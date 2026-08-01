"""The IR: a `TheoryAST` plus a `ProblemSpec`, ground and checked.

Everything a backend needs and nothing it has to re-derive. Three jobs:

1. **Grounding over instances.** A rule may quantify over a declared object
   *type* — `forall ?a in Peg` — and the instances live in the problem, not the
   manual, so this grounding cannot happen in `expand.py` (which handles value
   domains at the manual level). Both passes run here in order, and after them
   no `VarRef` survives. This is what lifts `gen_python`'s old restriction of one
   instance per declared type, which is why the peg world's rules used to
   compile to `pass`.

2. **State axes.** One axis per (instance, observation) pair that can vary.
   Backends that enumerate need them; backends that do algebra need the same
   list to know what they are quantifying over.

3. **Checking the manual against the level.** Undeclared landmarks, missing
   weight vectors, instances of undeclared types, and rules that mention names
   nothing supplies — all caught once, here, rather than three times as three
   different `KeyError`s inside three backends.
"""

from dataclasses import dataclass, field, replace
from typing import Dict, List, Optional, Sequence, Set

from .parser.ast_nodes import (
    ActionMatch, BinOp, Comparison, Expr, FieldAccess, FuncCall, Guard,
    GuardAction, GuardPredicate, NameRef, NumberLit, RuleDecl, TheoryAST,
    TupleLit, VarRef,
)
from .parser.expand import expand_theory
from .problem import Instance, ProblemSpec, check_against_theory
from .writes import WriteSets, WritesError, written_names


class IRError(Exception):
    """The manual and the level disagree, or the manual is outside the subset."""


@dataclass
class Axis:
    """One varying component of the state."""
    instance: str          # "Peg_0"
    observation: str       # "pos" | "alive" | "color" | "present"
    field: str             # "Peg_0_pos" — the attribute in generated Python
    type_name: str         # the declared object type, "Peg"


@dataclass
class WorldIR:
    ast: TheoryAST
    problem: ProblemSpec
    rules: List[RuleDecl]
    axes: List[Axis]
    fields_by_type: Dict[str, List[str]]
    actions: List[tuple]                    # (name, arity) seen in guards
    landmarks: Dict[str, tuple] = field(default_factory=dict)
    weights: Dict[str, List[int]] = field(default_factory=dict)
    # Where each vector in `weights` came from, by declared name: `"problem
    # <name>"` or `"certificate <repo-relative path>"`. Every form that prints
    # a weight prints this beside it, so "who solved for these numbers" is a
    # property of the artefact and not of the reader's memory (E-05).
    weight_sources: Dict[str, str] = field(default_factory=dict)
    # Legibility complaints, not errors. See `problem.check_against_theory`.
    warnings: List[str] = field(default_factory=list)
    # v0.3, ledger X-1. The manual's own answer to "which objects does this rule
    # write" — the definition `frame persist` and `conflict` both range over.
    # Carried on the IR so that every backend reads one resolved source instead
    # of each holding a private effect dictionary, which is the defect X-1 filed.
    writes: "WriteSets" = None                          # type: ignore[assignment]

    @property
    def semantics(self):
        return self.ast.semantics

    def instance_names(self) -> List[str]:
        return [i.name for i in self.problem.instances]


# --------------------------------------------------------------- substitution

def _subst_instances(expr: Expr, env: Dict[str, str]) -> Expr:
    if isinstance(expr, VarRef):
        if expr.name not in env:
            raise IRError(f"?{expr.name} is not bound by its rule header")
        return NameRef(env[expr.name])
    if isinstance(expr, FieldAccess):
        # `?a.pos` parses as a FieldAccess whose object is the raw text "?a".
        obj = expr.obj
        if obj.startswith("?"):
            if obj[1:] not in env:
                raise IRError(f"{obj} is not bound by its rule header")
            obj = env[obj[1:]]
        return FieldAccess(obj, expr.field_name)
    if isinstance(expr, FuncCall):
        return FuncCall(expr.name, [_subst_instances(a, env) for a in expr.args])
    if isinstance(expr, Comparison):
        return Comparison(expr.op, _subst_instances(expr.left, env),
                          _subst_instances(expr.right, env))
    if isinstance(expr, BinOp):
        return BinOp(expr.op, _subst_instances(expr.left, env),
                     _subst_instances(expr.right, env))
    if isinstance(expr, TupleLit):
        return TupleLit([_subst_instances(e, env) for e in expr.elements])
    return expr


def _subst_guard(guard: Guard, env: Dict[str, str]) -> Guard:
    out = []
    for clause in guard.clauses:
        if isinstance(clause, GuardAction):
            out.append(GuardAction(ActionMatch(
                clause.action.action_name,
                [_subst_instances(a, env) for a in clause.action.args])))
        else:
            out.append(GuardPredicate(_subst_instances(clause.expr, env),
                                      clause.negated))
    return Guard(out)


def _free_vars(expr: Expr, into: Set[str]) -> None:
    if isinstance(expr, VarRef):
        into.add(expr.name)
    elif isinstance(expr, FieldAccess):
        if expr.obj.startswith("?"):
            into.add(expr.obj[1:])
    elif isinstance(expr, FuncCall):
        for a in expr.args:
            _free_vars(a, into)
    elif isinstance(expr, (Comparison, BinOp)):
        _free_vars(expr.left, into)
        _free_vars(expr.right, into)
    elif isinstance(expr, TupleLit):
        for e in expr.elements:
            _free_vars(e, into)


def rule_variables(rule: RuleDecl) -> Set[str]:
    found: Set[str] = set()
    for clause in rule.guard.clauses:
        if isinstance(clause, GuardAction):
            for a in clause.action.args:
                _free_vars(a, found)
        else:
            _free_vars(clause.expr, found)
    _free_vars(rule.event, found)
    return found


# ------------------------------------------------------------------ grounding

def ground_over_instances(rule: RuleDecl, problem: ProblemSpec,
                          types: Set[str]) -> List[RuleDecl]:
    """Ground `forall ?a in <ObjectType>` over the level's instances.

    Distinct variables get distinct instances: a peg cannot jump over itself,
    and admitting the diagonal would generate a guard that no state satisfies
    plus a spurious mutual-exclusion obligation for `certify` to discharge.
    """
    obj_bindings = {v: d for v, d in rule.bindings.items() if d in types}
    if not obj_bindings:
        return [rule]

    order = list(obj_bindings)
    out: List[RuleDecl] = []

    def walk(i: int, env: Dict[str, str], used: Set[str]):
        if i == len(order):
            out.append(RuleDecl(
                name=rule.name + "__" + "_".join(env[v] for v in order),
                meta=rule.meta,
                guard=_subst_guard(rule.guard, env),
                event=_subst_instances(rule.event, env),
                bindings={},
            ))
            return
        var = order[i]
        for inst in problem.instances_of(obj_bindings[var]):
            if inst.name in used:
                continue
            walk(i + 1, dict(env, **{var: inst.name}), used | {inst.name})

    walk(0, {}, set())
    return out


def _collect_actions(rules: Sequence[RuleDecl]) -> List[tuple]:
    seen = []
    for rule in rules:
        for clause in rule.guard.clauses:
            if isinstance(clause, GuardAction):
                key = (clause.action.action_name, len(clause.action.args))
                if key not in seen:
                    seen.append(key)
    return seen


VARYING = ("pos", "alive", "present", "color", "colour")


def _resolve_weights(ast: TheoryAST, problem: ProblemSpec, certificate):
    """One place where a `weights <name>` declaration acquires its numbers.

    Ledger entry E-05 gave the potential a name; this is the other half — the
    numbers arrive from whoever solved for them, and **never** by being copied
    by hand into a level file. Before this, `gen_lean` read the certificate and
    the other three backends read only the problem, so a manual whose weights
    lived in a certificate rendered a `theory.md` that named a potential it
    could not show, and `check_against_theory` warned about a hole that was in
    fact filled.

    Precedence and the checks, in order:

    * the level may supply a vector; a certificate may supply one; **if both do
      they must be equal.** A stale copy is exactly how a proof comes to rest on
      weights nobody solved for, so disagreement is an error and not a
      preference.
    * a certificate whose vector has no declaration to land on is an error: the
      backend would have to guess which potential the manual meant.
    * more than one *unfilled* declaration and one certificate is an error too.
      One vector cannot fill two names, and picking the alphabetically-first is
      the kind of silent guess this compiler exists not to make.

    Returns `(weights, sources)`. Neither dict is ever partially written.
    """
    weights = dict(problem.weights)
    sources = {name: "problem %s" % problem.name for name in weights}
    declared = [d.name for d in ast.word_table.weights]

    if certificate is None:
        return weights, sources

    if not declared:
        raise IRError(
            "a certificate was supplied (%s) but theory.dsl declares no "
            "`weights <name> over <field>`, so its vector has no name to land "
            "on. Declare the potential (E-05) or drop the certificate."
            % (certificate.path or certificate.produced_by,))

    provenance = "certificate %s" % _provenance(certificate.path)
    vector = list(certificate.weights)

    for name in declared:
        if name in weights and list(weights[name]) != vector:
            raise IRError(
                "the level supplies %s = %s and %s carries %s. One of them is "
                "stale; they must agree before either becomes a theorem."
                % (name, list(weights[name]), provenance, vector))

    unfilled = [name for name in declared if name not in weights]
    if len(unfilled) > 1:
        raise IRError(
            "theory.dsl declares %d weight functions with no level vector (%s) "
            "and one certificate was supplied. One vector cannot fill two "
            "names; supply the others in the problem instance, or compile with "
            "one certificate per potential." % (len(unfilled), sorted(unfilled)))
    if unfilled:
        weights[unfilled[0]] = vector
        sources[unfilled[0]] = provenance
    else:
        # Every declaration already had a vector and all of them matched. Record
        # the certificate as the corroborating source, not as a second one.
        for name in declared:
            sources[name] = "%s (agrees with %s)" % (sources[name], provenance)
    return weights, sources


def _provenance(path: str) -> str:
    """A certificate path as a repo-relative one, so the record travels."""
    if not path:
        return "<in-memory certificate>"
    parts = path.replace("\\", "/").split("/")
    for anchor in ("engine-rig", "interop", "certificates"):
        if anchor in parts:
            return "/".join(parts[parts.index(anchor):])
    return parts[-1]


def _check_write_targets(rules: Sequence[RuleDecl], problem: ProblemSpec,
                         ast: TheoryAST, writes: WriteSets) -> List[str]:
    """What a rule's event writes must be a thing this manual can own.

    GAP R2-2. `theoria-arm` filed *"a cell that never varies gets no instance,
    so no rule can name it"* as a grammar hole. It is not one — the grammar
    states the law fine as soon as an instance is seated
    (`runs/20260801T1200Z-R2-2-board-cell-expressivity/SEATING.json`, levels L2
    and L3, same manual byte for byte). What made it *look* like a grammar hole
    is this compiler, and this is the check that was missing.

    Three cases, and they are not the same defect wearing three hats.

    **A cell term — error.** `recolored(leftof(?s), 1)` denotes a location, and
    a location is not a thing a manual owns. `gen_python` and `gen_lean` already
    refuse it; `gen_markdown` renders it as fluent prose (*"then leftof(?s)'s
    colour becomes 1"*) because nothing on that path ever asks what the rule
    writes. Raising here is what puts the fourth form under the same rule as the
    other three.

    **A declared landmark — error, and this is R2-2's trap.** A landmark is a
    `NameRef`, so `WriteSets.of_rule` accepted it; the declaration and
    `gen_python`'s compiled effect both said `{edge}`, so
    `check_backend_agreement` accepted it too. The emitted effect was
    `state.edge_color = 1`: an assignment onto a plain dataclass with no such
    field, which therefore **succeeds**, is absent from `State.key()`, and is
    read by nothing. `render` rebuilds the frame from `BOARD`, a compile-time
    constant, so the cell never moves. Measured — the rule is in `RULES`,
    `fired()` reports it firing, and `s0.key() == s1.key()`. Strictly worse than
    a refusal: a refusal sends the author to the repair, this sent them away
    believing the language could not say it. No level can make it right, because
    a landmark is *declared* to be a cell, so it is an error and not a warning.

    **An instance this level does not seat — warning.** Different situation,
    same symptom, and conflating them would be the easy mistake.
    `theory.dsl` is the **domain**: it travels between levels (`problem.py`).
    `a0-cart`'s `press_left` writes `Button`, and the `no-button` level is
    entitled to have no button — the rule simply cannot fire there. Erroring
    would delete a legitimate level from a checked-in handover package. It is
    still compiled to the same do-nothing assignment, so it is reported rather
    than tolerated, and `tests/test_writes.py` pins the count: v0.3 §5's own
    precedent is that a shortfall is carried as a measured number, because a
    declaration nobody verifies reads exactly like a verified one.

    Ranges only over rules whose write set **resolves**. An event in neither the
    manual's `writes { ... }` nor v0.3's default table stays a warning here and
    a refusal at the point of use, exactly as v0.3 §7 describes; widening that
    would replace a good diagnostic with a worse one, which is why it was
    written that way.
    """
    seated = {i.name for i in problem.instances}
    declared_landmarks = {lm.name for lm in ast.word_table.landmarks}
    out: List[str] = []
    for rule in rules:
        try:
            names = written_names(rule, writes)
        except WritesError as exc:
            raise IRError(str(exc)) from exc
        if names is None:
            continue
        for name in names:
            if name.startswith("?"):
                # Unreachable today: `build_ir` grounds first and already
                # refuses a rule with a variable left in it. Skipped explicitly
                # so that reordering those two passes produces no check at all
                # rather than a warning naming `?a` as an unseated instance.
                continue
            if name in seated:
                continue
            if name in declared_landmarks or name in problem.landmarks:
                raise IRError(
                    "rule %r writes %r, which this manual declares as a "
                    "`landmark` — a *cell*, not an object. An event writes "
                    "objects. The frame is drawn by painting instances onto "
                    "the level's board, so a cell no instance stands on renders "
                    "the board's colour on every step and an event aimed at it "
                    "compiles to an assignment nothing reads: before this check "
                    "the rule fired and the frame never changed. Repair: have "
                    "the level seat an instance on that cell and write the rule "
                    "over the instance. If the cell has never varied and the "
                    "level therefore seats nothing there, that is a "
                    "segmentation question and not a grammar one — see "
                    "theory-compiler/runs/"
                    "20260801T1200Z-R2-2-board-cell-expressivity/FINDING.md."
                    % (rule.name, name))
            out.append(
                "rule %r writes %r, which problem %r seats no instance of. The "
                "manual is the domain and travels between levels, so this is "
                "legal and the rule cannot fire here; but its effect still "
                "compiles to an assignment nothing reads. Reported rather than "
                "refused (R2-2)." % (rule.name, name, problem.name))
    return out


def build_ir(ast: TheoryAST, problem: ProblemSpec, certificate=None,
             check_conflicts: bool = True) -> WorldIR:
    """`certificate` is optional and is the **only** way weights enter without
    being written down twice. See `_resolve_weights`.

    `check_conflicts` discharges the `conflict` policy the manual declares
    (`conflict.check_conflict`) and **raises** if it cannot. It defaults to on
    because the alternative is what v0.2 shipped with: a manual that states
    which of constraint 9's two routes it claims, and nothing anywhere that
    checks either. Pass `False` only with a written reason — the one manual in
    this repo that needs it is the peg fixture, for ledger entry **E-07**.
    """
    if ast.semantics is None:
        raise IRError("theory.dsl has no `semantics:` section (E-03)")
    if ast.word_table is None:
        raise IRError("theory.dsl has no `word_table:` section")

    warnings = check_against_theory(problem, ast)

    ast = expand_theory(ast)                      # value domains (E-02)
    types = {o.name for o in ast.word_table.objects}
    fields_by_type = {o.name: [f.name for f in o.fields]
                      for o in ast.word_table.objects}

    rules: List[RuleDecl] = []
    for rule in (ast.rules.rules if ast.rules else []):
        for var in rule.bindings:
            if rule.bindings[var] not in types and not any(
                    d.name == rule.bindings[var]
                    for d in ast.word_table.domains):
                raise IRError(
                    f"rule {rule.name} binds ?{var} over {rule.bindings[var]!r}, "
                    f"which is neither a declared object type nor a declared "
                    f"value domain")
        rules.extend(ground_over_instances(rule, problem, types))

    for rule in rules:
        left = rule_variables(rule)
        if left:
            raise IRError(
                f"rule {rule.name} still mentions {sorted('?' + v for v in left)} "
                f"after grounding; add `forall` bindings for them")

    axes = []
    for inst in problem.instances:
        for obs in fields_by_type.get(inst.type, []):
            if obs in VARYING:
                axes.append(Axis(instance=inst.name, observation=obs,
                                 field=f"{inst.name}_{obs}", type_name=inst.type))

    weights, weight_sources = _resolve_weights(ast, problem, certificate)

    # `check_against_theory` runs before the certificate is in hand, so it warns
    # about every declaration the level does not fill. Once one of them has been
    # filled from a certificate the warning is describing a hole that is not
    # there, and a warning that is not true is how a log stops being read.
    filled = [name for name, src in weight_sources.items()
              if src.startswith("certificate")]
    if filled:
        warnings = [w for w in warnings
                    if not (w.startswith("theory.dsl declares `weights ")
                            and any("`weights %s " % n in w for n in filled))]

    writes = WriteSets(ast)
    warnings.extend(_check_write_targets(rules, problem, ast, writes))

    # v0.3, ledger X-1. A write set that arrived from the published default
    # table rather than from this manual is a per-world fact taken from a
    # cross-world table. That is the trade v0.3 makes for backward
    # compatibility, and it is a warning rather than an error for the same
    # reason a missing `landmark` is: it compiles to the same world when the
    # table is right. It is not silent, because a silent default is E-03.
    inherited = writes.inherited_from_table(rules)
    if inherited:
        warnings.append(
            "theory.dsl declares no `writes { ... }` for %s, so their write "
            "sets come from v0.3's default table. The table is keyed by name "
            "and arity across all worlds; what a rule writes is a fact about "
            "this one. Declare them if the table is not what this manual means."
            % (", ".join("%s/%d" % k for k in inherited),))

    if check_conflicts:
        from .conflict import Uniqueness, check_conflict
        report = check_conflict(rules, ast.semantics, problem.background,
                                strict=False,
                                uniq=Uniqueness(ast, problem),
                                writes=writes)
        warnings.extend(report.warnings())

    return WorldIR(
        warnings=warnings,
        writes=writes,
        ast=ast,
        problem=problem,
        rules=rules,
        axes=axes,
        fields_by_type=fields_by_type,
        actions=_collect_actions(rules),
        landmarks=dict(problem.landmarks),
        weights=weights,
        weight_sources=weight_sources,
    )
