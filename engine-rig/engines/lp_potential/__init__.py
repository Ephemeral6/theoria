"""lp_potential -- public entry points."""

from typing import Any, Dict, List, Optional, Sequence

from common.candidates import emit, make_candidate
from engines.lp_potential.potential import (  # noqa: F401
    Certificate,
    CertificateError,
    Heuristic,
    Move,
    admissibility_report,
    check_exactly,
    heuristic_from,
    moves_from_graph,
    solve_certificate,
)

ENGINE = "lp_potential"


def candidates(certificate: Certificate, heuristic: Heuristic,
               graph: Dict[str, Any], timestamp: Optional[str] = None
               ) -> List[Dict[str, Any]]:
    """One invariant (the certificate) and one heuristic, from the same weights."""
    n_moves = len(certificate.moves)
    n_edges = len(graph["edges"])
    invariant_payload = certificate.as_json()
    invariant_payload["move_instances"] = [m.name() for m in certificate.moves]

    heuristic_payload = heuristic.as_json()
    heuristic_payload["admissibility_check"] = admissibility_report(heuristic, graph)

    return [
        make_candidate(
            engine=ENGINE,
            kind="invariant",
            payload=invariant_payload,
            transitions=list(range(n_edges)),
            coverage="%d/%d" % (n_edges, n_edges),
            timestamp=timestamp,
        ),
        make_candidate(
            engine=ENGINE,
            kind="heuristic",
            payload=heuristic_payload,
            transitions=list(range(n_edges)),
            coverage="%d/%d" % (n_moves, n_moves),
            timestamp=timestamp,
        ),
    ]


def run(graph: Dict[str, Any], initial: str,
        goal_states: Optional[Sequence[str]] = None,
        out_path: Optional[str] = None,
        timestamp: Optional[str] = None):
    """Solve for a certificate on `initial`; return (certificate, heuristic).

    Returns (None, None) when no certificate exists -- which is the correct
    answer for a solvable configuration, not a failure.
    """
    certificate = solve_certificate(graph, initial, goal_states=goal_states)
    if certificate is None:
        return None, None
    heuristic = heuristic_from(certificate)
    if out_path:
        emit(out_path, candidates(certificate, heuristic, graph, timestamp=timestamp))
    return certificate, heuristic
