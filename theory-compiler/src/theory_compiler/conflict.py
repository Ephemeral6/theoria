"""Discharging the `conflict` obligation the manual declares.

`CONTRACTS/dsl_grammar_v0.2.md` gives `semantics:` two routes to constraint 9's
"exactly one successor", and makes the manual say which it claims:

| declared | what the manual is claiming | what has to be proved |
|---|---|---|
| `conflict exclusive` | at most one rule fires per object per transition | the guards of any two rules that claim a common object are **disjoint** |
| `conflict priority: r1 > r2 > ...` | if several fire, the earliest listed wins | the declared order is **total over the rules that can collide** |

Until this module existed, v0.2 made the manual *state* which route it took and
nothing checked either one. That is worse than not asking: a declaration nobody
verifies reads exactly like a verified one. (`gen_python` emits a runtime
`AmbiguousTransition`, but that fires only on a state some replay happens to
visit — it is a smoke alarm, not a proof.)

## "Per object" is the whole difficulty

The naive reading — "all guards pairwise disjoint" — is wrong, and rejecting
A0's manual is how you find out. `press_left` and `door_opens_left` have
**identical** guards, deliberately: pressing the button opens the door in the
same transition. They do not violate `exclusive`, because one claims the Button
and the other claims the Door, and the declaration is about *an object* being
claimed twice. So the obligation is discharged pairwise over rules whose
**claimed-object sets intersect**, and only those.

## Two routes, and the report says which one paid

**Guard analysis** (`check_conflict`) is syntactic, sound, and incomplete. Six
decidable reasons two guards cannot both hold:

1. **Different action.** A transition carries exactly one action, so guards
   matching different actions are disjoint. After grounding there are no
   variables left, distinct object names denote distinct objects, and distinct
   direction names denote distinct directions — so a syntactic difference is a
   semantic one.
2. **A predicate and its negation** on the same term (E-01's `not`).
3. **Two `colored(t, ...)` clauses on one term with different colours** — a
   cell has one colour.
4. **`free(t)` against `colored(t, c)` for a non-background `c`** — the
   predictor *defines* `_free(cell)` as `colour(cell) == BACKGROUND`. This is
   what separates A0's `push_down` from `teleport_down`.
5. **`free(t)` against `t = wall`** — `wall` compiles to `not _in_bounds(t)`,
   and a cell that is not on the board is not free. The cart manual's own
   comment asserts exactly this; rule 5 is what turns the comment into a
   discharge.
6. **Two different live instances pinned to one value of a `unique` field**
   (E-07). This is the reason a schema quantified over a second instance — the
   peg jump's `?b` — can entail `exclusive` at all.

**Exhaustive sweep** (`certify_conflict`) settles what analysis could not, by
running the predictor over every state the level can represent. This is the
layer the contract means by "`certify` must prove it", and when the answer is
no it hands back a state and an action rather than a complaint.

Anything guard analysis cannot settle is reported as *undischarged*, never as
proved. A pair that is in fact disjoint for a reason not on the list above will
be refused, and that is the correct direction to be wrong in: the alternative
is a compiler that says "proved" when it means "I could not find a
counterexample". Widening the list is a change to this file; **assuming** a
pair is fine is not available.

## What this found, and how it was closed: E-07

The peg manual declared `conflict exclusive` and **did not entail it**. Two
groundings of one schema — `jump_right(?a=Peg_0, ?b=Peg_1)` and
`jump_right(?a=Peg_0, ?b=Peg_3)` — both claim `Peg_0`, and both guards hold
whenever `Peg_1` and `Peg_3` sit on the same cell. The sweep was unambiguous:
over the 80,000 representable (state, action) pairs there were **600** such
collisions; over the 59,560 where no two live pegs share a cell, **none**.

The fact — pegs cannot stack — was always true of the world and had nowhere to
be written down. So the manual gained a place to write it: **`pos: Int unique`**
in the word table, reason 6 above. With it, guard analysis discharges all 228
overlapping pairs and the conditional route is not needed.

`unique` is a **claim, not a hint**, and `certify_uniqueness` discharges it in
turn: true of the initial state, and preserved by `step` over all 59,560
well-formed transitions. Skipping the second half would have been the same
mistake one level down — the declaration could hold at the start, rot one move
later, and void every disjointness proof resting on it.

**The conditional route stays.** A manual that needs the condition and does not
declare it still gets a named conditional discharge with a witness, rather than
a silent pass. E-07 is closed for peg because peg can now say the thing; it is
not closed by deciding the question no longer matters.
"""

from typing import Dict, List, Optional, Sequence, Set, Tuple

from .parser.ast_nodes import (
    ActionMatch, Comparison, Expr, FieldAccess, FuncCall, GuardAction,
    GuardPredicate, NameRef, NumberLit, RuleDecl, TupleLit, VarRef,
)


class ConflictError(Exception):
    """The manual declares a conflict policy it does not satisfy."""


# Which event names claim which of their arguments. Kept here rather than
# imported from a backend because the obligation is a property of the manual,
# not of one compilation of it — but it must not drift from what the backends
# actually mutate, so `test_conflict.py` pins the two tables against each other.
#
# **Unknown events fail closed.** Guessing "one object, the first argument"
# would under-approximate the claimed set for any future two-object event, and
# an under-approximated claim set silently skips the pair that needed checking.
CLAIMED_ARGS: Dict[Tuple[str, int], Tuple[int, ...]] = {
    ("moved", 2): (0,),
    ("jumped", 2): (0,),
    ("teleported", 2): (0,),
    ("jumped", 3): (0, 1),          # the mover and the peg it jumps over
    ("recolored", 2): (0,),
    ("vanished", 1): (0,),
    ("appeared", 1): (0,),
    ("removed", 1): (0,),
    ("stayed", 1): (0,),
}


def claimed_objects(rule: RuleDecl) -> Set[str]:
    """The instances this rule's event mutates."""
    event = rule.event
    if not isinstance(event, FuncCall) or not event.args:
        raise ConflictError(
            "rule %r has no object-shaped event, so which object it claims "
            "cannot be determined and `conflict` cannot be discharged for it"
            % (rule.name,))
    key = (event.name, len(event.args))
    if key not in CLAIMED_ARGS:
        raise ConflictError(
            "rule %r fires %s/%d, which this checker has no claim table for. "
            "Add it to `CLAIMED_ARGS`: assuming it claims only its first "
            "argument would skip exactly the pairs a two-object event creates."
            % (rule.name, event.name, len(event.args)))
    out = set()
    for index in CLAIMED_ARGS[key]:
        arg = event.args[index]
        if not isinstance(arg, NameRef):
            raise ConflictError(
                "rule %r claims a non-object at argument %d of %s"
                % (rule.name, index, event.name))
        out.add(arg.name)
    return out


# ------------------------------------------------------------- guard analysis

# `above(x)` and `toward(x, up)` are the same cell written two ways, and two
# guards that disagree about one of them must still be comparable. Normalising
# to the `toward` form is what lets A0's `free(below(Cart))` line up with a
# `colored(below(Cart), 3)` written either way.
SPATIAL_AS_TOWARD = {"above": "up", "below": "down",
                     "leftof": "left", "rightof": "right"}


def _key(expr: Expr) -> str:
    """A syntactic key for an expression, stable across equal trees.

    Normalises the spatial shorthands so that two spellings of one cell get one
    key; everything else is structural.
    """
    if isinstance(expr, NameRef):
        return "n:%s" % expr.name
    if isinstance(expr, VarRef):                       # should not survive grounding
        return "v:%s" % expr.name
    if isinstance(expr, NumberLit):
        return "i:%d" % expr.value
    if isinstance(expr, FieldAccess):
        return "f:%s.%s" % (expr.obj, expr.field_name)
    if isinstance(expr, FuncCall):
        if expr.name in SPATIAL_AS_TOWARD and len(expr.args) == 1:
            return "c:toward(%s,n:%s)" % (_key(expr.args[0]),
                                          SPATIAL_AS_TOWARD[expr.name])
        return "c:%s(%s)" % (expr.name, ",".join(_key(a) for a in expr.args))
    if isinstance(expr, TupleLit):
        return "t:(%s)" % ",".join(_key(e) for e in expr.elements)
    if isinstance(expr, Comparison):
        return "p:%s%s%s" % (_key(expr.left), expr.op, _key(expr.right))
    return "?:%r" % (expr,)


def _action_of(rule: RuleDecl) -> Optional[ActionMatch]:
    for clause in rule.guard.clauses:
        if isinstance(clause, GuardAction):
            return clause.action
    return None


def _predicates(rule: RuleDecl) -> Tuple[Set[str], Set[str]]:
    """(positive keys, negated keys) over the guard's predicate clauses."""
    positive, negative = set(), set()
    for clause in rule.guard.clauses:
        if isinstance(clause, GuardPredicate):
            (negative if clause.negated else positive).add(_key(clause.expr))
    return positive, negative


def _colours(rule: RuleDecl) -> Dict[str, Set[int]]:
    """term key -> the colours a positive `colored(term, c)` clause demands."""
    out: Dict[str, Set[int]] = {}
    for clause in rule.guard.clauses:
        if not isinstance(clause, GuardPredicate) or clause.negated:
            continue
        expr = clause.expr
        if (isinstance(expr, FuncCall) and expr.name == "colored"
                and len(expr.args) == 2 and isinstance(expr.args[1], NumberLit)):
            out.setdefault(_key(expr.args[0]), set()).add(expr.args[1].value)
    return out


def _offboard_terms(rule: RuleDecl) -> Set[str]:
    """Terms a positive `t = wall` clause demands be off the board.

    `wall` is the one reserved cell value and it means "not a cell at all" —
    the predictor compiles `above(Cart) = wall` to `not _in_bounds(...)`.
    """
    out = set()
    for clause in rule.guard.clauses:
        if not isinstance(clause, GuardPredicate) or clause.negated:
            continue
        expr = clause.expr
        if isinstance(expr, Comparison) and expr.op == "=":
            for side, other in ((expr.right, expr.left), (expr.left, expr.right)):
                if isinstance(side, NameRef) and side.name == "wall":
                    out.add(_key(other))
    return out


class Uniqueness:
    """The `unique` field declarations, resolved against the level's instances.

    Passed explicitly rather than kept in module state: this decides whether a
    pair is *proved* disjoint, and a checker whose verdict depends on hidden
    globals is not one anybody should believe.
    """

    def __init__(self, ast=None, problem=None):
        self.unique_field: Dict[str, str] = {}       # type -> field name
        self.has_aliveness: Dict[str, bool] = {}     # type -> can be absent
        self.instance_type: Dict[str, str] = {}      # instance -> type
        if ast is None or ast.word_table is None:
            return
        for obj in ast.word_table.objects:
            names = [f.name for f in obj.fields]
            self.has_aliveness[obj.name] = bool(
                {"alive", "present"} & set(names))
            for field in obj.fields:
                if field.unique:
                    self.unique_field[obj.name] = field.name
        if problem is not None:
            self.instance_type = {i.name: i.type for i in problem.instances}

    def __bool__(self) -> bool:
        return bool(self.unique_field)


def _placements(rule: RuleDecl, uniq: "Uniqueness") -> Dict[str, Set[str]]:
    """value-key -> the instances this guard pins to that value, on a unique field.

    Collects `X.f = <expr>` where `f` is declared `unique` for `X`'s type, and
    `X` is required alive if the type has an aliveness field — `unique` is
    about *live* instances, and a dead peg is off the board.
    """
    alive: Set[str] = set()
    for clause in rule.guard.clauses:
        if not isinstance(clause, GuardPredicate) or clause.negated:
            continue
        expr = clause.expr
        if (isinstance(expr, Comparison) and expr.op == "="
                and isinstance(expr.left, FieldAccess)
                and expr.left.field_name in ("alive", "present")
                and isinstance(expr.right, NameRef)
                and expr.right.name == "true"):
            alive.add(expr.left.obj)

    out: Dict[str, Set[str]] = {}
    for clause in rule.guard.clauses:
        if not isinstance(clause, GuardPredicate) or clause.negated:
            continue
        expr = clause.expr
        if not (isinstance(expr, Comparison) and expr.op == "="
                and isinstance(expr.left, FieldAccess)):
            continue
        holder = expr.left.obj
        type_name = uniq.instance_type.get(holder)
        if type_name is None:
            continue
        if uniq.unique_field.get(type_name) != expr.left.field_name:
            continue
        if uniq.has_aliveness.get(type_name) and holder not in alive:
            continue           # not required live, so uniqueness says nothing
        out.setdefault(_key(expr.right), set()).add(holder)
    return out


def _free_terms(rule: RuleDecl) -> Set[str]:
    """Terms a positive `free(t)` clause demands be background-coloured."""
    out = set()
    for clause in rule.guard.clauses:
        if not isinstance(clause, GuardPredicate) or clause.negated:
            continue
        expr = clause.expr
        if isinstance(expr, FuncCall) and expr.name == "free" and len(expr.args) == 1:
            out.add(_key(expr.args[0]))
    return out


def disjointness_reason(a: RuleDecl, b: RuleDecl, background: int = 0,
                        uniq: Optional["Uniqueness"] = None) -> Optional[str]:
    """Why `a` and `b` can never both fire, or `None` if this cannot be shown.

    Sound in one direction only: a non-`None` answer is a proof, a `None`
    answer is "not proved here" and never "they can collide".
    """
    act_a, act_b = _action_of(a), _action_of(b)
    if act_a is not None and act_b is not None:
        if act_a.action_name != act_b.action_name:
            return ("they match different actions (%s vs %s), and a transition "
                    "carries exactly one" % (act_a.action_name, act_b.action_name))
        if len(act_a.args) != len(act_b.args):
            return ("they match %s at different arities (%d vs %d)"
                    % (act_a.action_name, len(act_a.args), len(act_b.args)))
        for index, (x, y) in enumerate(zip(act_a.args, act_b.args)):
            if _key(x) != _key(y):
                return ("their action arguments differ at position %d (%s vs "
                        "%s), and after grounding distinct names denote "
                        "distinct things"
                        % (index, _key(x), _key(y)))

    pos_a, neg_a = _predicates(a)
    pos_b, neg_b = _predicates(b)
    contradiction = (pos_a & neg_b) | (pos_b & neg_a)
    if contradiction:
        return ("one requires %s and the other requires its negation"
                % sorted(contradiction)[0])

    col_a, col_b = _colours(a), _colours(b)
    for term in sorted(set(col_a) & set(col_b)):
        if col_a[term].isdisjoint(col_b[term]):
            return ("they demand different colours of %s (%s vs %s), and a "
                    "cell has one colour"
                    % (term, sorted(col_a[term]), sorted(col_b[term])))

    # `free(t)` is *defined* as "t is the background colour" — the predictor
    # emits `_free(state, cell) := _cell_colour(state, cell) == BACKGROUND` —
    # so demanding `free(t)` and `colored(t, c)` for any other colour is a
    # contradiction. This is what separates A0's `push_down` from
    # `teleport_down`: one wants the cell below empty, the other wants it to be
    # the Portal.
    for free_side, col_side, order in ((a, col_b, ("first", "second")),
                                       (b, col_a, ("second", "first"))):
        for term in sorted(_free_terms(free_side) & set(col_side)):
            demanded = sorted(c for c in col_side[term] if c != background)
            if demanded and background not in col_side[term]:
                return ("the %s requires free(%s) — i.e. colour %d — and the "
                        "%s requires colour(s) %s of the same cell"
                        % (order[0], term, background, order[1], demanded))

    # `free(t)` needs `t` to be a cell at all: the predictor's `_cell_colour`
    # returns `None` off the board, which is never the background colour. So
    # `free(t)` and `t = wall` cannot both hold. The cart manual's own comment
    # claims exactly this ("push_up and teleport are disjoint: a wall is not
    # free"); this is what turns that comment into a discharged obligation.
    for free_side, wall_side, order in ((a, b, ("first", "second")),
                                        (b, a, ("second", "first"))):
        shared = _free_terms(free_side) & _offboard_terms(wall_side)
        for term in sorted(shared):
            return ("the %s requires free(%s) and the %s requires the same "
                    "cell to be `wall`, i.e. off the board — a cell that is "
                    "not on the board is not free" % (order[0], term, order[1]))

    # E-07. Two guards that each pin a *different* live instance of one type to
    # the same value of a `unique` field cannot both hold. This is what lets a
    # schema quantified over a second instance — the peg jump's `?b` — entail
    # `conflict exclusive` at all: without it, `(?a=Peg_0, ?b=Peg_1)` and
    # `(?a=Peg_0, ?b=Peg_3)` both claim Peg_0 whenever Peg_1 and Peg_3 sit on
    # one cell, and nothing in the manual said they cannot.
    if uniq:
        place_a, place_b = _placements(a, uniq), _placements(b, uniq)
        for value in sorted(set(place_a) & set(place_b)):
            others = place_b[value] - place_a[value]
            mine = place_a[value] - place_b[value]
            if mine and others:
                type_name = uniq.instance_type[sorted(mine)[0]]
                return ("the first puts %s and the second puts %s at the same "
                        "%s, and %s.%s is declared `unique` — no two live %s "
                        "share it (E-07)"
                        % (sorted(mine)[0], sorted(others)[0], value,
                           type_name, uniq.unique_field[type_name], type_name))
    return None


# --------------------------------------------------------------- the discharge

class ConflictReport:
    """What was proved, over which pairs, and by what reason.

    Kept as an artefact rather than a bool because "the obligation holds" is a
    claim a reader should be able to audit: which pairs shared an object at
    all, which of those were discharged, and by which of the three rules.
    """

    def __init__(self, policy: str):
        self.policy = policy
        self.overlapping: List[Tuple[str, str, List[str]]] = []
        self.disjoint: List[Tuple[str, str, str]] = []
        self.ordered: List[Tuple[str, str]] = []
        self.undischarged: List[Tuple[str, str, List[str]]] = []
        # Rules whose event has no claim table: which objects they
        # touch is unknown, so no pair involving them can be judged.
        self.unclaimable: List[Tuple[str, str]] = []
        self.swept: Optional[dict] = None

    @property
    def green(self) -> bool:
        return not self.undischarged

    def warnings(self) -> List[str]:
        """Undischarged pairs, as compile-time warnings rather than errors.

        `build_ir` cannot raise on these: `gen_python` builds the predictor
        *through* `build_ir`, so refusing here would deny the exhaustive route
        the very predictor it needs. The obligation is fatal one layer up, in
        `certify_conflict`, which is where `CONTRACTS/dsl_grammar_v0.2.md` puts
        it ("`certify` must prove it").
        """
        out = ["rule %s: %s" % (name, why) for name, why in self.unclaimable]
        if not self.undischarged:
            return out
        pairs = ", ".join("%s/%s" % (a, b) for a, b, _ in self.undischarged[:3])
        more = "" if len(self.undischarged) <= 3 else (
            " (and %d more)" % (len(self.undischarged) - 3))
        return out + ["`conflict %s` is not discharged by guard analysis for %d rule "
                "pair(s): %s%s. Run `certify_conflict` to settle it against the "
                "predictor; if it survives there too, the manual claims "
                "something it does not entail (ledger E-07)."
                % (self.policy, len(self.undischarged), pairs, more)]

    def as_json(self) -> dict:
        return {
            "policy": self.policy,
            "pairs_sharing_an_object": len(self.overlapping),
            "discharged_by_disjointness": [
                {"rules": [x, y], "reason": why} for x, y, why in self.disjoint],
            "discharged_by_priority": [list(p) for p in self.ordered],
            "undischarged": [
                {"rules": [x, y], "shared_objects": objs}
                for x, y, objs in self.undischarged],
            "green": self.green,
        }

    def summary(self) -> str:
        return ("conflict %s: %d rule pair(s) share an object; %d discharged by "
                "disjointness, %d by the declared order, %d undischarged"
                % (self.policy, len(self.overlapping), len(self.disjoint),
                   len(self.ordered), len(self.undischarged)))


def check_conflict(rules: Sequence[RuleDecl], semantics,
                   background: int = 0, strict: bool = True,
                   uniq: Optional["Uniqueness"] = None) -> ConflictReport:
    """Discharge the declared `conflict` policy, or raise `ConflictError`.

    `rules` must be **ground** — the IR's rules, after `forall` expansion. A
    schema's guards mention variables, and two groundings of one schema are
    exactly the pairs most likely to collide, so checking before grounding
    would check the wrong thing.
    """
    report = ConflictReport(semantics.conflict)

    if semantics.conflict == "priority":
        known = {r.name for r in rules}
        unknown = [n for n in semantics.priority if n not in known]
        if unknown:
            raise ConflictError(
                "`conflict priority:` orders %s, which the manual has no ground "
                "rule for. After `forall` expansion a schema becomes one rule "
                "per value (`<rule>_<value>`), and the order has to name the "
                "ground rules it actually ranks." % (sorted(unknown),))
        rank = {name: i for i, name in enumerate(semantics.priority)}
    else:
        rank = {}

    # An event with no claim table is fatal in strict mode — guessing "the
    # first argument" would silently skip the pairs a two-object event creates.
    # In non-strict mode it is recorded and the pass continues: `build_ir` runs
    # non-strict, and a manual with an unrecognised event is going to be
    # refused by the backend with a message about *that*, which is the more
    # useful error. Preempting it here would replace a good diagnostic with a
    # worse one.
    claims: Dict[str, Set[str]] = {}
    unclaimable: List[Tuple[str, str]] = []
    for rule in rules:
        try:
            claims[rule.name] = claimed_objects(rule)
        except ConflictError as exc:
            if strict:
                raise
            claims[rule.name] = set()
            unclaimable.append((rule.name, str(exc)))
    for name, why in unclaimable:
        report.unclaimable.append((name, why))

    for i, a in enumerate(rules):
        for b in rules[i + 1:]:
            shared = sorted(claims[a.name] & claims[b.name])
            if not shared:
                # Different objects: this pair cannot violate a policy about
                # one object being claimed twice. A0's press_left /
                # door_opens_left are exactly here — identical guards, and a
                # cascade rather than a conflict.
                continue
            report.overlapping.append((a.name, b.name, shared))

            reason = disjointness_reason(a, b, background, uniq)
            if reason is not None:
                report.disjoint.append((a.name, b.name, reason))
                continue

            if semantics.conflict == "priority" and a.name in rank and b.name in rank:
                report.ordered.append((a.name, b.name))
                continue

            report.undischarged.append((a.name, b.name, shared))

    if report.undischarged and strict:
        raise ConflictError(_explain(report, semantics))
    return report


# ------------------------------------------------- the exhaustive route

#: The well-formedness condition a world may need for `exclusive` to hold, and
#: which no v0.2 guard can state. Named rather than anonymous so a report can
#: say *which* assumption a conditional discharge rests on.
DISTINCT_POSITIONS = "distinct_positions"
CONDITIONS = {
    DISTINCT_POSITIONS:
        "no two live instances of one declared type occupy the same cell",
}


def cell_universe(problem) -> list:
    """Cells in the *predictor's* representation, not the ProblemSpec's.

    `ProblemSpec.cells()` returns 1-tuples for a line world, because a cell is
    a coordinate there too. The generated predictor stores a line position as a
    bare `int` — `_neighbour(pos, d)` does `pos + 1`. Sweeping with tuples
    produces `TypeError: can only concatenate tuple (not "int") to tuple`,
    which is a loud failure and therefore a lucky one; a representation
    mismatch that happened to be silent would have swept a state space no rule
    could ever match and reported a clean green.
    """
    if problem.is_line:
        return list(range(problem.n_pos))
    return [tuple(c) for c in problem.arena]


def _distinct_live_positions(state) -> bool:
    """The fallback well-formedness notion, for manuals that declare no
    `unique` field: no two live instances share a position."""
    live = [getattr(state, f) for f in vars(state) if f.endswith("_pos")
            and getattr(state, f[:-4] + "_alive", True)]
    return len(live) == len(set(live))


def _states(ns, cells, wellformed=None):
    """Every state the predictor can represent, from the level's own axes.

    Not the reachable set. Reachability is a property of one starting
    configuration; `conflict` is a claim about the *domain*, and D-TC-012 is
    the standing lesson that a rule can be right as a problem solution and
    wrong as a domain. So the sweep runs over what the state type admits.
    """
    import itertools
    start = ns["initial_state"]()
    names = [f[:-4] for f in vars(start) if f.endswith("_pos")]
    per = []
    for name in names:
        has_alive = hasattr(start, name + "_alive")
        flags = (True, False) if has_alive else (True,)
        per.append([(c, a) for c in cells for a in flags])
    if not per:
        return None, None

    def generate():
        for combo in itertools.product(*per):
            state = start.copy()
            for name, (cell, alive) in zip(names, combo):
                setattr(state, name + "_pos", cell)
                if hasattr(state, name + "_alive"):
                    setattr(state, name + "_alive", alive)
            # The filter is a predicate on the built state, not a rule about
            # positions: `unique` may name any field, and hardcoding "distinct
            # live positions" would silently sweep the wrong space for a manual
            # that declares uniqueness of a colour.
            if wellformed is not None and not wellformed(state):
                continue
            yield state
    return generate, names


def _sweep(ns, cells, wellformed=None, limit: int = 400_000):
    """(pairs examined, first ambiguous witness or None). None,None if too big."""
    generate, _names = _states(ns, cells, wellformed)
    if generate is None:
        return None, None
    ambiguous = ns["AmbiguousTransition"]
    actions = list(ns["ACTIONS"])
    seen = 0
    witness = None
    for state in generate():
        for action in actions:
            seen += 1
            if seen > limit:
                return None, None
            try:
                ns["step"](state, action)
            except ambiguous as exc:
                if witness is None:
                    witness = (ns["occupancy"](state) if "occupancy" in ns
                               else repr(vars(state)), repr(action), str(exc))
    return seen, witness


def _violations(state, ns, uniq: "Uniqueness") -> Optional[Tuple[str, str, str]]:
    """(type, instance, instance) if two live instances share a unique value."""
    for type_name, field in sorted(uniq.unique_field.items()):
        holders = [n for n, t in uniq.instance_type.items() if t == type_name]
        seen: Dict[object, str] = {}
        for name in sorted(holders):
            if uniq.has_aliveness.get(type_name):
                alive = getattr(state, name + "_alive",
                                getattr(state, name + "_present", True))
                if not alive:
                    continue
            value = getattr(state, "%s_%s" % (name, field), None)
            if value in seen:
                return (type_name, seen[value], name)
            seen[value] = name
    return None


def certify_uniqueness(ns: dict, uniq: "Uniqueness", cells) -> dict:
    """Prove that `unique` is true of the world, not merely asserted about it.

    A `unique` declaration restricts which states are well formed, and a
    restriction nobody checks is how a manual comes to describe a world it does
    not have — the same failure `semantics:` exists to close, one level down.
    Two obligations, both discharged by running the predictor:

    * **initial** — the level's own starting state satisfies it;
    * **preserved** — from every well-formed state, every action leads to a
      well-formed state. This is `inv_closed` in miniature, and it is the half
      that matters: without it the declaration would hold at the start and rot
      one move later, and every disjointness proof resting on it would be void.

    Sweeping *well-formed* states only is correct here rather than convenient:
    the claim being proved is inductive, so states that already violate the
    property are not in its scope. That is exactly why the preservation half
    cannot be skipped.
    """
    if not uniq:
        return {"status": "not declared"}

    start = ns["initial_state"]()
    bad = _violations(start, ns, uniq)
    if bad is not None:
        raise ConflictError(
            "`%s.%s` is declared `unique`, but the level's initial state has "
            "%s and %s sharing a value. The declaration is a claim about the "
            "world and this level is a counterexample to it."
            % (bad[0], uniq.unique_field[bad[0]], bad[1], bad[2]))

    generate, _names = _states(
        ns, cells, wellformed=lambda st: _violations(st, ns, uniq) is None)
    if generate is None:
        return {"status": "not swept",
                "why": "the well-formed state space is too large to sweep"}

    examined = 0
    for state in generate():
        for action in ns["ACTIONS"]:
            examined += 1
            try:
                after = ns["step"](state, action)
            except ns["AmbiguousTransition"]:
                # Not this check's business: `certify_conflict` owns it, and it
                # reports a far better message than a uniqueness violation would.
                continue
            bad = _violations(after, ns, uniq)
            if bad is not None:
                raise ConflictError(
                    "`%s.%s` is declared `unique` and `step` does not preserve "
                    "it: from a well-formed state, action %r leaves %s and %s "
                    "sharing a value. Every disjointness proof that rests on "
                    "the declaration is void until this is fixed."
                    % (bad[0], uniq.unique_field[bad[0]], action, bad[1], bad[2]))
    return {"status": "proved", "obligations": ["initial", "preserved"],
            "well_formed_transitions_examined": examined,
            "fields": {t: f for t, f in sorted(uniq.unique_field.items())}}


def certify_conflict(report: ConflictReport, ns: dict, semantics,
                     cells) -> ConflictReport:
    """Settle what guard analysis could not, against the predictor itself.

    This is the layer `CONTRACTS/dsl_grammar_v0.2.md` names when it says
    "`certify` must prove it". Guard analysis is syntactic and incomplete; the
    predictor is the world the manual actually compiles to, so sweeping it
    decides the question — and when the answer is no, it hands back a concrete
    state and action rather than a complaint.

    Three outcomes:

    * **green** — no state the level can represent lets two rules claim one
      object. The obligation holds outright.
    * **conditional** — it holds under a *named* condition (see `CONDITIONS`)
      and fails without one, with a witness for the failure. This is a real
      result, not a shrug: the sweep proves both halves. It is also a defect
      report, because the manual does not state the condition and the v0.2
      guard language cannot state it — ledger **E-07**.
    * **raise** — it fails even under the condition. The manual is wrong.
    """
    if not report.undischarged:
        report.swept = {"status": "green", "route": "guard analysis"}
        return report

    seen, witness = _sweep(ns, cells)
    if seen is None:
        report.swept = {"status": "not swept",
                        "why": "the representable state space is too large to sweep"}
        raise ConflictError(_explain(report, semantics))

    if witness is None:
        report.swept = {"status": "green", "route": "exhaustive",
                        "pairs_examined": seen}
        report.undischarged = []
        return report

    seen2, witness2 = _sweep(ns, cells, wellformed=_distinct_live_positions)
    if seen2 is not None and witness2 is None:
        report.swept = {
            "status": "conditional",
            "route": "exhaustive",
            "condition": DISTINCT_POSITIONS,
            "condition_means": CONDITIONS[DISTINCT_POSITIONS],
            "pairs_examined_unrestricted": seen,
            "pairs_examined_restricted": seen2,
            "witness_without_the_condition": witness,
            "ledger": "E-07",
        }
        return report

    report.swept = {"status": "failed", "route": "exhaustive",
                    "pairs_examined": seen, "witness": witness}
    raise ConflictError(
        _explain(report, semantics)
        + "\n\nThe exhaustive sweep agrees: in state %s under action %s, %s"
        % (witness[0], witness[1], witness[2]))


def _explain(report: ConflictReport, semantics) -> str:
    lines = []
    if semantics.conflict == "exclusive":
        lines.append(
            "the manual declares `conflict exclusive`, which claims that at "
            "most one rule fires per object per transition. These rule pairs "
            "claim a common object and were not shown to be mutually "
            "exclusive:")
    else:
        lines.append(
            "the manual declares `conflict priority:`, which claims the order "
            "is total over the rules that can collide. These pairs can collide "
            "and the order does not rank both members:")
    for a, b, shared in report.undischarged:
        lines.append("  - %s and %s both claim %s" % (a, b, ", ".join(shared)))
    lines.append("")
    lines.append(
        "This checker is sound and incomplete: it proves disjointness from a "
        "different action, a predicate and its negation, or conflicting colour "
        "demands, and reports everything else as undischarged rather than "
        "guessing. So this is either a real ambiguity in the manual or a "
        "reason outside that list.")
    lines.append(
        "Either make the guards distinguishable by one of those three, or "
        "declare `conflict priority: ...` and rank the pair — which states "
        "that they *can* both fire and says which wins, instead of claiming "
        "they cannot.")
    return "\n".join(lines)
