"""lp_potential -- public entry points."""

from typing import Any, Dict, List, Optional, Sequence

from common.candidates import emit, make_candidate
from engines.lp_potential.potential import (  # noqa: F401
    Certificate,
    CertificateError,
    Heuristic,
    LpUnavailable,
    Move,
    admissibility_report,
    check_exactly,
    heuristic_from,
    moves_from_graph,
    premises_against_graph,
    solve_certificate,
)

ENGINE = "lp_potential"


WITHHOLD = "withhold"
MARK = "mark"
ON_UNSOUND = (WITHHOLD, MARK)


def candidates(certificate: Certificate, heuristic: Heuristic,
               graph: Dict[str, Any], timestamp: Optional[str] = None,
               on_unsound: str = WITHHOLD) -> List[Dict[str, Any]]:
    """One invariant (the certificate) and one heuristic, from the same weights.

    Both rows are gated on `premises_against_graph`, which re-derives the
    certificate's premises from the graph rather than from the certificate.  The
    first cut of this fix gated only the heuristic row, and that was the same
    defect one row over: the invariant went out saying `goal unreachable from X`
    with all three conditions `true`, beside a heuristic row whose counterexamples
    were a proof that `inv_closed` is false over the real move set.  Two rows from
    one weight vector, contradicting each other, nothing saying which wins.

    `on_unsound="withhold"` (default) emits nothing when the premises fail;
    `"mark"` emits both rows carrying `unsound: true` and the `premise_check`.
    Production cannot reach either branch -- `solve_certificate` builds the move
    list *from* the graph -- which is exactly why it needs a test rather than an
    argument.
    """
    if on_unsound not in ON_UNSOUND:
        raise ValueError(
            "on_unsound must be one of %r, got %r" % (list(ON_UNSOUND), on_unsound)
        )
    premise_check = premises_against_graph(certificate, graph)
    if not premise_check["sound_over_graph"] and on_unsound == WITHHOLD:
        return []

    n_moves = len(certificate.moves)
    n_edges = len(graph["edges"])
    invariant_payload = certificate.as_json()
    invariant_payload["move_instances"] = [m.name() for m in certificate.moves]
    invariant_payload["premise_check"] = dict(premise_check)

    # The empirical check scores h against `graph["distance_to_goal"]`, which is
    # the distance to the *graph's* goals.  When the certificate is about a
    # different set (a supported call), those distances answer another question
    # and every row of the report is a fabricated counterexample -- so the check
    # is not run rather than run and mis-scored.  The incomplete-move-list hazard
    # it used to be the only guard against is now caught directly by
    # `premise_check`, so declining to sample costs nothing.
    if premise_check["goal_states_match_graph"]:
        heuristic_payload = heuristic.as_json(admissibility_report(heuristic, graph))
    else:
        heuristic_payload = heuristic.as_json()
        heuristic_payload["admissible_basis"]["empirical_check"] = (
            "not comparable -- certificate goals %r, graph goals %r"
            % (premise_check["certificate_goal_states"],
               premise_check["graph_goal_states"])
        )
    heuristic_payload["premise_check"] = dict(premise_check)

    if not premise_check["sound_over_graph"]:            # only reachable under MARK
        for payload in (invariant_payload, heuristic_payload):
            payload["unsound"] = True
        invariant_payload["holds"] = False
        heuristic_payload["admissible"] = False
        heuristic_payload["admissible_basis"]["admissible"] = False

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
    answer for a solvable configuration, not a failure.  A solver that stopped
    without deciding raises `LpUnavailable` instead of arriving here, so
    `(None, None)` cannot be manufactured by a resource limit.
    """
    certificate = solve_certificate(graph, initial, goal_states=goal_states)
    if certificate is None:
        return None, None
    heuristic = heuristic_from(certificate)
    if out_path:
        emit(out_path, candidates(certificate, heuristic, graph, timestamp=timestamp))
    return certificate, heuristic
