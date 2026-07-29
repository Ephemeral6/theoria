"""`fd_adapter` mutants — four defects, and one of them is a probe of the seam.

Read this before the table: three facts about `props/fd_adapter.py` decide what a
mutant here *can* be, and all three change how a survivor must be read.

**1. The rung is `stub-bfs`, always, and not because this machine lacks a
planner.** `props/fd_adapter.py` calls `engine.solve_parsed(domain, problem)`
without `domain_path=`/`problem_path=`, so `backends.choose_tier` takes clause 3
(`backends.py:184` — "or an instance that exists only in memory forces
`stub-bfs`"; Fast Downward reads files) and returns `("stub-bfs", None)` on every
machine, planner installed or not. So every number this catalogue produces is
about the bundled BFS. `stub-bfs` *is* documented length-optimal for unit costs
(`backends.py:9` table, `search.py:4`), and `Plan.optimal` is `True` on it
(`__init__.py:135`, `optimal = tier != FD_SATISFICING`) — so a "not optimal"
mutant is a real defect *here*. It would not be on `fd-satisficing`, which
declines that promise outright; nothing in this file may be read as a statement
about that rung.

**2. `props/fd_adapter.py:_solve` is dead code.** It is defined at line 84 and
called nowhere: all three invariants call `engine.solve_parsed(...)` directly
(lines 104, 131, 165). Compare `props/lp_potential.py`, where `_solve` is the
live seam on four call sites. So the seam the framework's design assumes — "every
property module funnels its engine call through one private helper"
(`mutants/__init__.py`) — does not exist for this engine, and the whole class of
*forged answer* defects (truncate the plan, flip `Plan.optimal`, shorten
`plan.actions` by one) cannot be injected at all. `fd-solve-seam-is-dead` is
registered to make that measurable rather than asserted: it is expected to report
`eval=0`, `inert=<all worlds>`.

**3. The only live seam is `_parsed`, and a naive mutant on it is invisible by
construction.** Every invariant does `domain, problem = _parsed(world)` and then
hands *the same two objects* to the engine (`solve_parsed`) and to the oracle
(`_model`). Corrupting the tuple therefore corrupts both sides equally, they
agree about the corrupted instance, and nothing fires. That is not a weak
battery: `props/fd_adapter.py:7-10` states it as the module's residual risk —
"if the parser is wrong, these properties inherit the error and will report a
pass".

So the mutants below fork the parse instead. `_EngineView` hands the **engine** a
modified instance and the **oracle** the untouched one, deciding which by looking
for the innermost `fuzzlab.props.fd_adapter` frame on the stack: `_model` is the
oracle's entry point and gets the truth; anything else on that module (the three
invariant functions, which is what `solve_parsed` is called from) is the engine's
path and gets the lie. The direction matters and is the opposite of cheating: the
judge always sees the real world, the engine is the one that is wrong. What is
being simulated is "the engine planned as if the instance were slightly
different" — a wrong *answer*, arrived at honestly — which is the closest
reachable stand-in for the forged-answer mutants fact 2 rules out.

`_model` itself is never touched. Injecting there would corrupt the oracle's
ground truth, which measures nothing except whether the judge can be lied to.
"""

import copy
import sys
from typing import Any, Dict, List, Optional, Tuple

from fuzzlab import mutants as mut
from fuzzlab import rig  # noqa: F401  (path bootstrap: puts engine-rig on sys.path)

from engines.fd_adapter.pddl import ground_actions, static_predicates  # noqa: E402

ENGINE = "fd_adapter"
SEAM = "_parsed"

#: The property module whose stack frames decide which view is asked for.
PROPS_MODULE = "fuzzlab.props.fd_adapter"

#: The one function on that module that is the *oracle*'s reader. Everything
#: else on it (the three invariants) reaches the engine.
ORACLE_ENTRY = "_model"


def _oracle_is_asking() -> bool:
    """Is this attribute read on its way to the oracle rather than the engine?

    Walk outwards to the innermost frame belonging to `props/fd_adapter.py` and
    read its function name. Both paths pass through `engines.fd_adapter.*` frames
    — `_model` calls the engine's `ground_actions` — so "is there an engine frame
    on the stack" does not separate them, but which *property* function is
    underneath does:

        oracle:  __getattr__ <- pddl.ground_actions <- props._model <- invariant
        engine:  __getattr__ <- search.search <- solve_parsed <- invariant

    Defaults to the truth when neither is found, so a read from anywhere else
    (the driver's `repr`, a debugger) cannot be served a lie by accident.
    """
    frame = sys._getframe(1)
    while frame is not None:
        if frame.f_globals.get("__name__") == PROPS_MODULE:
            return frame.f_code.co_name == ORACLE_ENTRY
        frame = frame.f_back
    return True


class _EngineView:
    """One parsed object with two faces: the world's, and the engine's.

    `__slots__` so that every other attribute misses and lands in `__getattr__`;
    `__repr__` is distinct so the driver's `repr(mutated) != repr(real)` inert
    check sees the change without needing `mut.touched()` (which cannot mark the
    tuple `_parsed` returns anyway — tuples reject `setattr`).
    """

    __slots__ = ("_true", "_lie", "_note")

    def __init__(self, true_obj: Any, lie_obj: Any, note: str) -> None:
        self._true = true_obj
        self._lie = lie_obj
        self._note = note

    def __getattr__(self, name: str) -> Any:
        return getattr(self._true if _oracle_is_asking() else self._lie, name)

    def __repr__(self) -> str:
        return "<_EngineView %s: %s>" % (self._note, self._lie)


def _busiest_static_atom(domain: Any, problem: Any) -> Optional[Tuple[str, ...]]:
    """The static initial atom the most ground actions depend on, or None.

    A static predicate is one no action adds or deletes (`pddl.static_predicates`),
    so grounding discards every action instance whose static preconditions are
    false in the initial state. Deleting one such atom from the engine's view
    therefore deletes exactly the ground actions that used it and nothing else —
    the narrowest way to take operators away from the planner without touching
    the plan. Picking the busiest one rather than the first is only about power:
    a far-corner adjacency is on no shortest path and the mutant would be a
    no-op in effect while still counting as applied.
    """
    static = static_predicates(domain)
    in_init = {atom for atom in problem.init if atom[0] in static}
    if not in_init:
        return None
    counts: Dict[Tuple[str, ...], int] = {}
    for action in ground_actions(domain, problem):
        for atom in action.pre_positive:
            if atom in in_init:
                counts[atom] = counts.get(atom, 0) + 1
    if not counts:
        return sorted(in_init)[0]
    return max(sorted(counts), key=lambda atom: counts[atom])


# ------------------------------------------------------------------- corruptions

def _weaken_goal(result: Any, args: Tuple[Any, ...],
                 kwargs: Dict[str, Any]) -> Any:
    domain, problem = result
    if not problem.goal_positive:
        raise mut.inert("problem states no positive goal atom; none to drop")
    lie = copy.deepcopy(problem)
    dropped = sorted(lie.goal_positive)[-1]
    lie.goal_positive = [a for a in lie.goal_positive if a != dropped]
    return (domain, _EngineView(problem, lie, "problem/goal"))


def _hide_operators(result: Any, args: Tuple[Any, ...],
                    kwargs: Dict[str, Any]) -> Any:
    domain, problem = result
    atom = _busiest_static_atom(domain, problem)
    if atom is None:
        raise mut.inert("no static atom in the initial state; no operator to hide")
    lie = copy.deepcopy(problem)
    lie.init = [a for a in lie.init if a != atom]
    if len(lie.init) == len(problem.init):
        raise mut.inert("the chosen static atom is not in init after all")
    return (domain, _EngineView(problem, lie, "problem/init-static"))


def _overachieve_goal(result: Any, args: Tuple[Any, ...],
                      kwargs: Dict[str, Any]) -> Any:
    """Add a non-static initial atom to the engine's goal.

    Chosen so the result is a *valid but wasteful* plan rather than a wrong one:
    any plan for `goal ∪ {extra}` from the real initial state is a plan for
    `goal`, built from real operators, so it replays and reaches the real goal —
    it is only longer, because the engine spends steps restoring `extra`. Atoms
    whose predicate already appears anywhere in the goal are skipped: in sokoban
    the first such atom is the box's *initial* cell, and demanding that together
    with the box's goal cell is a contradiction, which would turn this into a
    second false-unsolvability mutant instead of a degradation one.
    """
    domain, problem = result
    static = static_predicates(domain)
    constrained = {atom[0] for atom in problem.goal_positive}
    constrained |= {atom[0] for atom in problem.goal_negative}
    extra = sorted(atom for atom in problem.init
                   if atom[0] not in static and atom[0] not in constrained)
    if not extra:
        raise mut.inert("no non-static initial atom outside the goal's predicates")
    lie = copy.deepcopy(problem)
    lie.goal_positive = list(lie.goal_positive) + [extra[0]]
    return (domain, _EngineView(problem, lie, "problem/goal+"))


def _ground_nothing(result: Any, args: Tuple[Any, ...],
                    kwargs: Dict[str, Any]) -> Any:
    domain, problem = result
    if not domain.actions:
        raise mut.inert("domain declares no action schemas; nothing to lose")
    lie = copy.deepcopy(domain)
    lie.actions = []
    return (_EngineView(domain, lie, "domain/actions"), problem)


def _ground_nothing_for_both(result: Any, args: Tuple[Any, ...],
                             kwargs: Dict[str, Any]) -> Any:
    """`_ground_nothing` without the fork: the *shared* grounder loses them.

    The negative control for the whole seam design. `props/fd_adapter.py:7-10`
    declares the parser and grounder a shared dependency and the properties'
    residual risk; this makes that risk concrete and measurable instead of
    stated. Same defect as `fd-false-unsolvable`, injected one layer lower.
    """
    domain, problem = result
    if not domain.actions:
        raise mut.inert("domain declares no action schemas; nothing to lose")
    domain.actions = []
    return (domain, problem)


def _truncate_plan(result: Any, args: Tuple[Any, ...],
                   kwargs: Dict[str, Any]) -> Any:
    """Never runs. See `fd-solve-seam-is-dead` and fact 2 in the module docstring."""
    plan, search_result = result
    if plan is None or not plan.actions:
        raise mut.inert("no plan to truncate")
    plan.actions = plan.actions[:-1]
    return (plan, search_result)


mut.register(
    mut.Mutant(
        id="fd-solve-seam-is-dead",
        engine=ENGINE, seam="_solve", kind=mut.UNSOUND,
        claim="`Plan.actions` is a plan that reaches the goal -- "
              "engines/fd_adapter/__init__.py:140 runs validate.validate_plan on "
              "it before returning ('never emit an unchecked plan'), and "
              "props/fd_adapter.py names plan_replays_to_the_goal as the check "
              "of exactly that.",
        description="drop the last action of the returned plan. THIS MUTANT IS "
                    "A SEAM PROBE, and the pre-registered prediction is not the "
                    "kill: props/fd_adapter.py:84 defines `_solve` and never "
                    "calls it (the invariants call engine.solve_parsed directly "
                    "at lines 104/131/165), so the prediction written before the "
                    "run is `worlds_evaluated == 0` and `worlds_inert == "
                    "worlds_offered`. expect_kill records what it *would* kill "
                    "if the seam were live, because the field cannot be empty.",
        corrupt=_truncate_plan,
        expect_kill=("plan_replays_to_the_goal",),
    ),
    mut.Mutant(
        id="fd-engine-plans-for-a-weaker-goal",
        engine=ENGINE, seam=SEAM, kind=mut.UNSOUND,
        claim="the returned plan reaches the goal *of the problem it was given* "
              "-- engines/fd_adapter/search.py:is_goal tests every atom of "
              "problem.goal_positive, and __init__.py:140 validates the plan "
              "against that same problem before returning it.",
        description="the engine sees a problem with one positive goal atom "
                    "removed; the oracle sees the real one. The engine's answer "
                    "is a genuine plan for a strictly weaker goal -- often "
                    "shorter, and on an instance that is only unsolvable because "
                    "of the dropped atom, a plan where the truth admits none.",
        corrupt=_weaken_goal,
        expect_kill=("plan_replays_to_the_goal", "optimal_rungs_are_optimal"),
    ),
    mut.Mutant(
        id="fd-engine-loses-operators",
        engine=ENGINE, seam=SEAM, kind=mut.DEGRADED,
        claim="stub-bfs is length-optimal for unit costs -- backends.py:9 rules "
              "it `length-optimal: yes`, search.py:4 says 'BFS is optimal for "
              "unit costs', and __init__.py:135 sets Plan.optimal True on every "
              "rung but fd-satisficing. On this campaign the rung is always "
              "stub-bfs (choose_tier clause 3, in-memory instance), so the "
              "promise is live on every world here.",
        description="one static initial atom is hidden from the engine, deleting "
                    "the ground actions whose static preconditions needed it. "
                    "The engine returns a plan built from a subset of the real "
                    "operators: still executable, still reaching the real goal, "
                    "but no longer the shortest -- and it still says optimal. "
                    "This is the DEGRADED case: if optimal_rungs_are_optimal "
                    "cannot kill it, that invariant is decoration. Where the "
                    "hidden operators were the only route, the engine reports "
                    "unsolvable instead, which is the second prediction.",
        corrupt=_hide_operators,
        expect_kill=("optimal_rungs_are_optimal", "no_plan_means_unsolvable"),
    ),
    mut.Mutant(
        id="fd-engine-overshoots-the-goal",
        engine=ENGINE, seam=SEAM, kind=mut.DEGRADED,
        claim="same promise as fd-engine-loses-operators: stub-bfs is "
              "length-optimal for unit costs (backends.py:9, search.py:4) and "
              "Plan.optimal is True on it (__init__.py:135). This campaign never "
              "leaves that rung, so 'the plan is longer than the optimum' is a "
              "broken promise here and would not be on fd-satisficing.",
        description="the engine's goal gains one non-static initial atom, so it "
                    "returns a plan that also puts that atom back. The plan is "
                    "VALID -- real operators, real initial state, and it "
                    "achieves the real goal on the way -- so "
                    "plan_replays_to_the_goal should stay silent; it is only "
                    "longer than the optimum while still flagged optimal. "
                    "Written after fd-engine-loses-operators turned out never to "
                    "produce a longer plan on any world (it either disconnected "
                    "the instance or changed nothing), which left the DEGRADED "
                    "shape unmeasured; expect_kill below was fixed before this "
                    "mutant was run. A no_plan_means_unsolvable kill would be an "
                    "unpredicted side effect (the strengthened goal turning out "
                    "unreachable), not the target.",
        corrupt=_overachieve_goal,
        expect_kill=("optimal_rungs_are_optimal",),
    ),
    mut.Mutant(
        id="fd-false-unsolvable",
        engine=ENGINE, seam=SEAM, kind=mut.UNSOUND,
        claim="`None` from solve_parsed is a *proof* that no plan exists, not a "
              "give-up -- engines/fd_adapter/__init__.py:86-102 ('Unsolvable is "
              "a result here, not an exception ... a run that only failed to "
              "find a plan stays a hard error on purpose'), and search.py's BFS "
              "is exhaustive, so an empty queue is the proof.",
        description="the engine grounds no actions at all (its view of the "
                    "domain has an empty action list) and so reports every "
                    "instance whose goal is not already true as unsolvable. On a "
                    "world the oracle's BFS solves, that is an unsolvability "
                    "claim about a solvable instance.",
        corrupt=_ground_nothing,
        expect_kill=("no_plan_means_unsolvable",),
    ),
    mut.Mutant(
        id="fd-shared-grounder-blind-spot",
        engine=ENGINE, seam=SEAM, kind=mut.INCOMPLETE,
        claim="pddl.ground_actions returns 'every ground instance that could "
              "ever fire' (engines/fd_adapter/pddl.py:305). A grounder that "
              "returns fewer makes solve_parsed's `None` a false proof of "
              "unsolvability, contradicting __init__.py:86-102.",
        description="the same defect as fd-false-unsolvable, one layer lower: "
                    "the action schemas vanish for BOTH the engine and the "
                    "oracle, because props/fd_adapter.py builds its ground truth "
                    "with the engine's own ground_actions (line 66) rather than "
                    "from world.problem_text. THE PRE-REGISTERED PREDICTION IS "
                    "THAT THIS KILLS NOTHING -- it is the negative control that "
                    "shows why the other mutants fork the parse, and it turns "
                    "the residual risk stated in props/fd_adapter.py:7-10 into a "
                    "measured blind spot. expect_kill names what it would kill "
                    "if the oracle's model were independent of the grounder, "
                    "because the field cannot be empty.",
        corrupt=_ground_nothing_for_both,
        expect_kill=("no_plan_means_unsolvable",),
    ),
)
