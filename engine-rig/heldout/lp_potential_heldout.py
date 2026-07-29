"""Held-out validation for `lp_potential`.

What the engine fits on is the **move list**: `solve_certificate` builds one LP
row per move geometry, and `check_exactly`'s `inv_closed` then quantifies over
`certificate.moves` -- the same list.  So the honest hold-out is a move geometry:
fit without it, then ask whether the weights still satisfy `inv_closed` on it,
and whether the unreachability claim is true against BFS over the *complete*
move set.

Two things this deliberately measures on the engine's side of the ledger:

* `solve_certificate` returning `None` is **silence**, not a miss.  The engine is
  sound but incomplete (D-014); refusing to certify is an answer.
* `lp_potential.candidates(...)` already gates on `premises_against_graph`, which
  re-derives the move list from the graph.  Whether that gate catches each unsound
  certificate is recorded per case, so the result credits the guard that exists
  instead of implying the emit path is unprotected.
"""

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from engines import lp_potential
from engines.lp_potential.potential import (
    Certificate, CertificateError, LpUnavailable, Move, heuristic_from,
    solve_certificate,
)
from heldout import peg

N_POSITIONS = (4, 5, 6, 7)


@dataclass
class Instance:
    instance_id: str
    n: int
    goal: str
    initial: str
    truly_reachable: bool


@dataclass
class HeldOutCase:
    instance_id: str
    withheld: List[int]
    outcome: str                    # certificate | silent | error
    detail: str = ""
    heldout_inv_closed: Optional[bool] = None
    claim_true: Optional[bool] = None
    gate_withholds: Optional[bool] = None
    # Kept apart on purpose.  `premises_against_graph` fails a certificate for
    # two different reasons and only the second is evidence that the *weights*
    # are wrong: a shorter move list is caught by counting, a raised potential is
    # caught by arithmetic.  Pooling them would let the completeness check take
    # credit for detection power the soundness check does not have.
    gate_missing_moves: List[str] = field(default_factory=list)
    gate_raising_moves: List[str] = field(default_factory=list)
    weights: List[str] = field(default_factory=list)
    admissibility_violations: Optional[int] = None
    admissibility_tested: Optional[int] = None
    first_violation: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BaselineCase:
    instance_id: str
    outcome: str
    claim_true: Optional[bool] = None
    admissibility_violations: Optional[int] = None
    admissibility_tested: Optional[int] = None
    first_violation: Dict[str, Any] = field(default_factory=dict)


def instances(n: int, graph: Dict[str, Any], goal: str) -> List[Instance]:
    out = []
    for state in graph["states"]:
        pegs = state.count("1")
        if pegs not in (n - 1, n - 2):
            continue
        if state == goal:
            continue
        out.append(
            Instance(
                instance_id="peg%d-g%s-i%s" % (n, goal, state),
                n=n, goal=goal, initial=state,
                truly_reachable=graph["distance_to_goal"][state] is not None,
            )
        )
    return out


def _admissibility_on_heldout(certificate: Certificate, graph: Dict[str, Any]
                              ) -> Tuple[int, int, Dict[str, Any]]:
    """L-L2.  Every state with a finite true distance that the LP never saw.

    The LP's constraints touch exactly two state sets -- `initial` and the goal
    states -- so everything else is held out.  Ground truth is the graph's BFS
    distance, which is computed over the complete move set even when the fit was
    not.
    """
    heuristic = heuristic_from(certificate)
    excluded = {certificate.initial, *certificate.goal_states}
    tested = 0
    violations = 0
    first: Dict[str, Any] = {}
    for state in sorted(graph["distance_to_goal"]):
        distance = graph["distance_to_goal"][state]
        if distance is None or state in excluded:
            continue
        tested += 1
        h = heuristic.value(state)
        if h > distance:
            violations += 1
            if not first:
                first = {"state": state, "h": ("inf" if math.isinf(h) else h),
                         "true_distance": distance}
    return violations, tested, first


def baseline(instance: Instance, graph: Dict[str, Any]) -> BaselineCase:
    """The engine as it ships: fitted on the complete move set."""
    try:
        certificate = solve_certificate(graph, instance.initial,
                                        goal_states=[instance.goal])
    except (LpUnavailable, CertificateError) as exc:
        return BaselineCase(instance.instance_id, "error", None, None, None,
                            {"exception": type(exc).__name__})
    if certificate is None:
        return BaselineCase(instance.instance_id, "silent")
    violations, tested, first = _admissibility_on_heldout(certificate, graph)
    return BaselineCase(
        instance_id=instance.instance_id,
        outcome="certificate",
        claim_true=not instance.truly_reachable,
        admissibility_violations=violations,
        admissibility_tested=tested,
        first_violation=first,
    )


def held_out_case(instance: Instance, graph: Dict[str, Any],
                  withheld: Tuple[int, int, int]) -> HeldOutCase:
    reduced = peg.graph_minus_geometry(graph, withheld)
    try:
        certificate = solve_certificate(reduced, instance.initial,
                                        goal_states=[instance.goal])
    except (LpUnavailable, CertificateError) as exc:
        return HeldOutCase(instance.instance_id, list(withheld), "error",
                           detail=type(exc).__name__)
    if certificate is None:
        return HeldOutCase(instance.instance_id, list(withheld), "silent")

    move = Move(*withheld)
    inv_closed = move.delta(certificate.weights) <= 0

    heuristic = heuristic_from(certificate)
    emitted = lp_potential.candidates(certificate, heuristic, graph)
    premises = lp_potential.premises_against_graph(certificate, graph)

    violations, tested, first = _admissibility_on_heldout(certificate, graph)
    return HeldOutCase(
        instance_id=instance.instance_id,
        withheld=list(withheld),
        outcome="certificate",
        heldout_inv_closed=inv_closed,
        claim_true=not instance.truly_reachable,
        gate_withholds=(emitted == []),
        gate_missing_moves=sorted(premises["missing_moves"]),
        gate_raising_moves=sorted(premises["moves_raising_potential"]),
        weights=[str(w) for w in certificate.weights],
        admissibility_violations=violations,
        admissibility_tested=tested,
        first_violation=first,
    )
