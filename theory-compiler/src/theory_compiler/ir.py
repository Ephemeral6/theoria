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
    # Legibility complaints, not errors. See `problem.check_against_theory`.
    warnings: List[str] = field(default_factory=list)

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


def build_ir(ast: TheoryAST, problem: ProblemSpec) -> WorldIR:
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

    return WorldIR(
        warnings=warnings,
        ast=ast,
        problem=problem,
        rules=rules,
        axes=axes,
        fields_by_type=fields_by_type,
        actions=_collect_actions(rules),
        landmarks=dict(problem.landmarks),
        weights=dict(problem.weights),
    )
