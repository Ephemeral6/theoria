"""fd_adapter -- public entry points.

One interface, two possible backends.  `solve()` returns the same Plan object
whether Fast Downward or the bundled BFS produced it, so the acceptance
criterion ("plan length equals the hand-verified optimum") is backend-agnostic.
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


@dataclass
class Plan:
    actions: List[str]
    backend: str                       # "fast-downward" | "stub-bfs"
    optimal: bool                      # is the backend's answer length-optimal?
    domain: str
    problem: str

    @property
    def length(self) -> int:
        return len(self.actions)

    def as_json(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "problem": self.problem,
            "backend": self.backend,
            "search": backends.FD_SEARCH if self.backend == "fast-downward" else "bfs",
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
                 prune: Optional[search.Pruner] = None
                 ) -> Tuple[Optional[Plan], search.SearchResult]:
    """Plan for an already-parsed instance; `None` when no plan exists.

    Unsolvable is a *result* here, not an exception -- the probe layer asks
    "can this configuration be reached?" and needs to be told no, and the
    deadlock carver measures the search on instances it expects to be pruned to
    nothing.  `solve()` keeps its raising behaviour for existing callers.

    Fast Downward reads files and cannot be handed a pruner, so an instance
    synthesised in memory or a call with `prune=` always takes the bundled
    search.  That is the same substitution STATUS.md already records, not a new
    one -- but it does mean the "unsolvable is a result" promise holds on the
    bundled path only: FD raises on a missing plan file, since it cannot tell
    "no plan exists" from "the planner fell over".  Both callers who rely on the
    promise take the bundled path by construction.
    """
    can_use_fd = prefer != "stub" and domain_path and problem_path and prune is None
    executable = backends.find_fast_downward() if can_use_fd else None
    if executable is not None:
        actions = backends.run_fast_downward(executable, domain_path, problem_path)
        backend = "fast-downward"
        # FD keeps its node account to itself; the plan is in `actions`.
        result = search.SearchResult(None, 0, 0, 0, 0)
    else:
        result = search.search(domain, problem, prune=prune)
        if result.plan is None:
            return None, result
        actions = [action.text() for action in result.plan]
        backend = "stub-bfs"

    plan = Plan(
        actions=actions,
        backend=backend,
        optimal=True,                  # A*/blind and BFS are both optimal here
        domain=domain.name,
        problem=problem.name,
    )
    validate_plan(domain, problem, plan.actions)   # never emit an unchecked plan
    return plan, result


def solve(domain_path: str = DOMAIN_PATH, problem_path: str = PROBLEM_PATH,
          prefer: Optional[str] = None) -> Plan:
    """Plan for a PDDL instance, using Fast Downward when it is available.

    `prefer="stub"` forces the bundled search, which is what the tests use so
    that they exercise the same path on every machine.
    """
    domain = parse_domain(read(domain_path))
    problem = parse_problem(read(problem_path))
    plan, _ = solve_parsed(
        domain, problem,
        domain_path=domain_path, problem_path=problem_path, prefer=prefer,
    )
    if plan is None:
        raise RuntimeError("no plan exists for %s" % problem.name)
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
    plan = solve(domain_path, problem_path, prefer=prefer)
    if out_path:
        emit(out_path, candidates(plan, timestamp=timestamp))
    return plan
