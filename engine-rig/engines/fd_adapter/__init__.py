"""fd_adapter -- public entry points.

One interface, three rungs.  `solve()` returns the same Plan object whether the
bundled BFS, Fast Downward's optimal rung or its satisficing one produced it, so
the acceptance criterion ("plan length equals the hand-verified optimum") is
backend-agnostic -- and the Plan names the rung, so a length that came from a
satisficing planner cannot be mistaken for an optimum.  The rule that picks the
rung lives in `backends.choose_tier`.
"""

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from common.candidates import emit, make_candidate
from engines.fd_adapter import backends, search, validate
from engines.fd_adapter.pddl import (  # noqa: F401
    Domain,
    GroundAction,
    PddlError,
    Problem,
    ground_actions,
    parse_domain,
    parse_problem,
)
from engines.fd_adapter.search import Pruner, SearchResult  # noqa: F401
from engines.fd_adapter.validate import InvalidPlan, validate_plan  # noqa: F401

ENGINE = "fd_adapter"

HERE = os.path.dirname(os.path.abspath(__file__))
DOMAIN_PATH = os.path.join(HERE, "domain.pddl")
PROBLEM_PATH = os.path.join(HERE, "problem.pddl")

# The rung `run()` records artifacts on.  Pinned, not discovered: see `run()`.
ARTIFACT_TIER = backends.STUB


class NoPlanExists(RuntimeError):
    """The planner *proved* the instance has no plan.

    A RuntimeError subclass on purpose.  `solve()` has always raised a bare
    RuntimeError here and callers written against that keep working unchanged;
    what is new is that they can now tell a proof from a crash, which they could
    not while the Fast Downward path raised the same thing for both.
    """


@dataclass
class Plan:
    actions: List[str]
    backend: str                       # a tier id: one of backends.TIERS
    optimal: bool                      # is the backend's answer length-optimal?
    domain: str
    problem: str
    search: str = "bfs"                # the configuration that rung ran, verbatim

    @property
    def length(self) -> int:
        return len(self.actions)

    def as_json(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "problem": self.problem,
            "backend": self.backend,
            "search": self.search,
            "optimal": self.optimal,
            "length": self.length,
            "actions": list(self.actions),
        }


def read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def solve_parsed(domain: Domain, problem: Problem,
                 domain_path: Optional[str] = None,
                 problem_path: Optional[str] = None,
                 prefer: Optional[str] = None,
                 prune: Optional[search.Pruner] = None,
                 heuristic: Optional[str] = None
                 ) -> Tuple[Optional[Plan], search.SearchResult]:
    """Plan for an already-parsed instance; `None` when no plan exists.

    Unsolvable is a *result* here, not an exception -- the probe layer asks
    "can this configuration be reached?" and needs to be told no, and the
    deadlock carver measures the search on instances it expects to be pruned to
    nothing.  `solve()` keeps its raising behaviour for existing callers.

    That promise now holds on **every** rung.  It used to hold on the bundled
    one only: Fast Downward reports "no plan exists" by exiting with no plan
    file, this adapter could not tell that from "the planner fell over", and so
    raised on both.  It can now -- see `backends.proves_unsolvable`, which had to
    be decided by measuring the planner rather than by reading its exit codes,
    because a complete search that exhausts the state space and an incomplete one
    that gives up leave FD with the *same* exit code.  A run that only failed to
    find a plan stays a hard error on purpose: it has not proved there is none,
    and a caller that read it as unsolvable would close a question the planner
    never answered.

    Fast Downward reads files and has no pruning hook, so an instance
    synthesised in memory or a call with `prune=` always takes the bundled
    search.  `backends.choose_tier` is where that rule is written down; the
    returned Plan names the rung that answered and the configuration it ran.
    """
    tier, executable = backends.choose_tier(
        prefer=prefer,
        on_disk=bool(domain_path and problem_path),
        prune=prune,
    )
    if tier == backends.STUB:
        result = search.search(domain, problem, prune=prune)
        if result.plan is None:
            return None, result
        actions = [action.text() for action in result.plan]
        config = backends.fd_search_config(tier)
    else:
        config = backends.fd_search_config(tier, heuristic, executable)
        actions = backends.run_fast_downward(
            executable, domain_path, problem_path, tier=tier, heuristic=heuristic,
        )
        # FD keeps its node account to itself; the plan is in `actions`.
        result = search.SearchResult(None, 0, 0, 0, 0)
        if actions is None:
            return None, result

    plan = Plan(
        actions=actions,
        backend=tier,
        # BFS and A* are both length-optimal for unit costs; LAMA is not, and
        # says so rather than letting its length be read as an optimum.
        optimal=tier != backends.FD_SATISFICING,
        domain=domain.name,
        problem=problem.name,
        search=config,
    )
    validate_plan(domain, problem, plan.actions)   # never emit an unchecked plan
    return plan, result


def solve(domain_path: str = DOMAIN_PATH, problem_path: str = PROBLEM_PATH,
          prefer: Optional[str] = None, heuristic: Optional[str] = None) -> Plan:
    """Plan for a PDDL instance, climbing as far up the ladder as it can.

    `prefer="stub"` forces the bundled search, which is what the tests use so
    that they exercise the same path on every machine; `prefer="fd-optimal"` or
    `prefer="fd-satisficing"` names a rung and fails loudly rather than dropping
    to another one.  `heuristic=` selects the optimal rung's heuristic
    (`"lmcut"`, the default, or `"ipdb"`) and is ignored elsewhere.

    Raises `NoPlanExists` -- a RuntimeError, so callers written against the old
    behaviour still catch it -- when the planner proved there is no plan.
    """
    domain = parse_domain(read(domain_path))
    problem = parse_problem(read(problem_path))
    plan, _ = solve_parsed(
        domain, problem,
        domain_path=domain_path, problem_path=problem_path, prefer=prefer,
        heuristic=heuristic,
    )
    if plan is None:
        raise NoPlanExists("no plan exists for %s" % problem.name)
    return plan


def to_payload(plan: Plan) -> Dict[str, Any]:
    """The plan payload shape; frozen in this engine's README."""
    return plan.as_json()


def candidates(plan: Plan, timestamp: Optional[str] = None) -> List[Dict[str, Any]]:
    return [
        make_candidate(
            engine=ENGINE,
            kind="plan",
            payload=to_payload(plan),
            transitions=list(range(plan.length)),
            coverage="%d/%d" % (plan.length, plan.length),
            timestamp=timestamp,
        )
    ]


def run(domain_path: str = DOMAIN_PATH, problem_path: str = PROBLEM_PATH,
        out_path: Optional[str] = None, prefer: Optional[str] = None,
        timestamp: Optional[str] = None) -> Plan:
    """Emit the plan candidate.  Pinned to the bundled rung unless told otherwise.

    `solve()` climbs to Fast Downward when it can find one; this deliberately
    does not, because this is the path that writes `artifacts/candidates.jsonl`
    and that file has to be byte-identical on a machine with a planner installed
    and one without.  Determinism is a repo requirement, not a nicety, so the
    higher rungs are opt-in here: pass `prefer="fd-optimal"` to record an FD
    plan instead.
    """
    plan = solve(domain_path, problem_path, prefer=prefer or ARTIFACT_TIER)
    if out_path:
        emit(out_path, candidates(plan, timestamp=timestamp))
    return plan
