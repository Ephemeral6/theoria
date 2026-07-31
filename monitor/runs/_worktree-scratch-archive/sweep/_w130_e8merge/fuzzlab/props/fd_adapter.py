"""`fd_adapter` — three invariants against an independent grounded-STRIPS BFS.

One honest dependency, stated rather than hidden: the PDDL **parser** is the
engine's. `blockworld` emits PDDL text and re-implementing a parser would test a
parser, not a planner. So `parse_domain`/`parse_problem`/`ground_actions` are
shared, and everything downstream of them — replaying the plan, deciding
optimality, deciding unsolvability — is `fuzzlab/oracles/search.py`, which shares
no code with `engines/fd_adapter/search.py`. If the parser is wrong, these
properties inherit the error and will report a pass; that is the residual risk
and it is why it is written down here.

What the rungs promise, from `DECISIONS.md` and the engine README:

* `stub-bfs` and `fd-optimal` are **length-optimal for unit costs**;
* `fd-satisficing` is **not**, and says so via `Plan.optimal is False`. So the
  optimality invariant is applied only where `plan.optimal` is true — asserting
  it on the satisficing rung would be a bug report against a documented
  non-guarantee;
* `NoPlanExists` means **proved unsolvable**, not "search gave up". A bare
  `RuntimeError` is the give-up path and is deliberately a different exception.

On a machine without a Fast Downward build the adapter falls back to `stub-bfs`.
That is expected, not a defect (README, CLAUDE.md), so the campaign records which
rung actually answered rather than requiring a particular one.

| invariant | claim under test |
|---|---|
| `plan_replays_to_the_goal` | the returned plan's preconditions all hold in sequence and the goal is met at the end |
| `optimal_rungs_are_optimal` | where the plan says `optimal`, its length equals the true BFS optimum |
| `no_plan_means_unsolvable` | `NoPlanExists` is only ever raised where exhaustive BFS confirms no plan exists |
"""

from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from fuzzlab import rig  # noqa: F401  (path bootstrap)
from fuzzlab.oracles import search
from fuzzlab.props import finding

from engines import fd_adapter as engine  # noqa: E402
from engines.fd_adapter.pddl import (  # noqa: E402
    PddlError, ground_actions, parse_domain, parse_problem,
)

FAMILY = "blockworld"
ENGINE = "fd_adapter"

# Ground STRIPS BFS is exponential; past this the oracle declines rather than
# guessing.  Quoted in the report beside the `skipped` count.
STATE_BUDGET = 60_000


def _parsed(world: Any):
    return (parse_domain(world.domain_text), parse_problem(world.problem_text))


def _model(domain, problem) -> Tuple[Set[str], Set[str], Dict[str, Dict[str, Set[str]]]]:
    """`(initial, goal, actions)` in the plain-set form the oracle works in.

    `GroundAction` is flattened to `{"pre", "add", "del"}` sets of stringified
    atoms — the oracle deliberately does not carry the engine's atom objects
    around, so a bug in their comparison semantics cannot propagate into the
    replay.
    """
    actions: Dict[str, Dict[str, Set[str]]] = {}
    for ground in ground_actions(domain, problem):
        # `Plan.actions` are PDDL surface strings, `"(name arg arg)"`, and
        # `GroundAction.text` is a bound method rather than a property — keying
        # on it silently produced an oracle that recognised no action at all and
        # reported thirteen "plan does not execute" violations against an engine
        # that was right. Rebuilt from `name` and `args` so the key is the thing
        # the plan actually names.
        actions["(%s)" % " ".join((ground.name,) + tuple(ground.args))] = {
            "pre_pos": {str(a) for a in ground.pre_positive},
            "pre_neg": {str(a) for a in ground.pre_negative},
            "del": {str(a) for a in ground.del_effects},
            "add": {str(a) for a in ground.add_effects},
        }
    initial = {str(a) for a in problem.init}
    goal = ({str(a) for a in problem.goal_positive},
            {str(a) for a in problem.goal_negative})
    return initial, goal, actions


def _solve(world: Any):
    domain, problem = _parsed(world)
    return engine.solve_parsed(domain, problem)


def _skip_pddl(world: Any, invariant: str, exc: Exception) -> List[finding.Finding]:
    return [finding.skipped(
        ENGINE, invariant, world,
        "PddlError — the generated instance is outside the supported STRIPS "
        "subset. Documented behaviour, not a defect.",
        cause="pddl_error", error=str(exc))]


# --------------------------------------------------------------- invariants

def plan_replays_to_the_goal(world: Any) -> List[finding.Finding]:
    """Applying the plan step by step from the initial state reaches the goal."""
    try:
        domain, problem = _parsed(world)
    except PddlError as exc:
        return _skip_pddl(world, "plan_replays_to_the_goal", exc)
    plan, _result = engine.solve_parsed(domain, problem)
    if plan is None:
        return []                       # no plan is the next invariant's business

    initial, goal, actions = _model(domain, problem)
    ok, why = search.validate_plan(initial, goal, actions, plan.actions)
    if not ok:
        return [finding.violated(
            ENGINE, "plan_replays_to_the_goal", world,
            "the returned %d-step plan does not execute: %s" % (len(plan.actions), why),
            backend=plan.backend, search=plan.search, plan=list(plan.actions),
            reason=why)]
    return []


def optimal_rungs_are_optimal(world: Any) -> List[finding.Finding]:
    """Where `Plan.optimal` is true, the length is the true BFS optimum.

    Not checked when the plan says it is not optimal: the satisficing rung is
    documented as returning a valid but possibly longer plan, and asserting
    otherwise would be a bug report against a promise the engine explicitly
    declines to make.
    """
    try:
        domain, problem = _parsed(world)
    except PddlError as exc:
        return _skip_pddl(world, "optimal_rungs_are_optimal", exc)
    plan, _result = engine.solve_parsed(domain, problem)
    if plan is None or not plan.optimal:
        return []

    initial, goal, actions = _model(domain, problem)
    best, exhausted = search.optimal_plan_length(initial, goal, actions,
                                                 budget=STATE_BUDGET)
    if not exhausted:
        return [finding.skipped(
            ENGINE, "optimal_rungs_are_optimal", world,
            "ground BFS hit the %d-state budget" % STATE_BUDGET,
            cause="ground_bfs_budget",
            plan_length=len(plan.actions), backend=plan.backend)]
    if best is None:
        return [finding.violated(
            ENGINE, "optimal_rungs_are_optimal", world,
            "the engine returned a %d-step plan on rung %s, but exhaustive BFS "
            "finds no plan at all" % (len(plan.actions), plan.backend),
            backend=plan.backend, plan=list(plan.actions))]
    if len(plan.actions) != best:
        return [finding.violated(
            ENGINE, "optimal_rungs_are_optimal", world,
            "rung %s claims optimality with %d steps, BFS optimum is %d"
            % (plan.backend, len(plan.actions), best),
            backend=plan.backend, search=plan.search,
            length=len(plan.actions), optimum=best, plan=list(plan.actions))]
    return []


def no_plan_means_unsolvable(world: Any) -> List[finding.Finding]:
    """`None` is a proof of unsolvability, so BFS must agree there is no plan."""
    try:
        domain, problem = _parsed(world)
    except PddlError as exc:
        return _skip_pddl(world, "no_plan_means_unsolvable", exc)
    plan, _result = engine.solve_parsed(domain, problem)
    if plan is not None:
        return []

    initial, goal, actions = _model(domain, problem)
    best, exhausted = search.optimal_plan_length(initial, goal, actions,
                                                 budget=STATE_BUDGET)
    if not exhausted:
        return [finding.skipped(
            ENGINE, "no_plan_means_unsolvable", world,
            "ground BFS hit the %d-state budget, so 'no plan' could not be "
            "confirmed either way" % STATE_BUDGET, cause="ground_bfs_budget")]
    if best is not None:
        return [finding.violated(
            ENGINE, "no_plan_means_unsolvable", world,
            "the engine reported the instance unsolvable, but BFS finds a "
            "%d-step plan" % best,
            optimum=best)]
    return []


INVARIANTS = {
    "plan_replays_to_the_goal": plan_replays_to_the_goal,
    "optimal_rungs_are_optimal": optimal_rungs_are_optimal,
    "no_plan_means_unsolvable": no_plan_means_unsolvable,
}


def check(world: Any) -> List[finding.Finding]:
    return finding.run_invariants(ENGINE, world, INVARIANTS)
