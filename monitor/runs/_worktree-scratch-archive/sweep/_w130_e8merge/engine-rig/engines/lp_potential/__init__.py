"""lp_potential -- public entry points."""

import json
import os
from typing import Any, Dict, List, Optional, Sequence

from common.candidates import emit, make_candidate
from engines.lp_potential.potential import (  # noqa: F401
    BUDGET,
    CERTIFIED,
    Certificate,
    CertificateError,
    DECIDED_STATUSES,
    Heuristic,
    LpOutcome,
    LpUnavailable,
    Move,
    NO_LINEAR_PAGODA,
    NUMERICAL,
    STATUS_MEANINGS,
    STATUS_WORDS,
    UNBOUNDED,
    UNDECIDED,
    admissibility_report,
    check_exactly,
    heuristic_from,
    moves_from_graph,
    premises_against_graph,
    solve,
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


def decide(graph: Dict[str, Any], initial: str,
           goal_states: Optional[Sequence[str]] = None,
           margin: int = 1, bound: int = 10,
           solver_options: Optional[Dict[str, Any]] = None,
           outcome_path: Optional[str] = None) -> LpOutcome:
    """The structured entry point: what the LP said, including that it said nothing.

    This is the one to call when the *rate* of silence matters, or when silence
    has to be attributable.  `run` is `decide` narrowed to the pair the rest of
    the rig consumes.

    `outcome_path`, when given, writes `LpOutcome.as_json()` there.  It is a
    sidecar and deliberately not a row in `candidates.jsonl`: the candidate
    schema is frozen (`CONTRACTS/candidates_schema.md`) and the ids are
    content-addressed, so widening the payload would re-hash a stream pinned in
    `release/MANIFEST.jsonl`.  A declined LP is also not a candidate -- there is
    nothing for the LLM to adjudicate -- but it is still a measurement, and the
    measurement is what nobody could read off an artifact before E15.
    """
    outcome = solve(graph, initial, goal_states=goal_states, margin=margin,
                    bound=bound, solver_options=solver_options)
    if outcome_path:
        directory = os.path.dirname(os.path.abspath(outcome_path))
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(outcome_path, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(outcome.as_json(), handle, indent=2, sort_keys=True)
            handle.write("\n")
    return outcome


def run(graph: Dict[str, Any], initial: str,
        goal_states: Optional[Sequence[str]] = None,
        out_path: Optional[str] = None,
        timestamp: Optional[str] = None,
        solver_options: Optional[Dict[str, Any]] = None,
        outcome_path: Optional[str] = None):
    """Solve for a certificate on `initial`; return (certificate, heuristic).

    Returns (None, None) on `no_linear_pagoda` -- HiGHS proved the LP infeasible,
    which is the correct answer for a solvable configuration and for an
    unsolvable one this method cannot reach, not a failure.

    The branch below is on `outcome.status`, **by name**.  It is not
    `if certificate is None`, and the difference is the whole item: that
    expression is equally true when HiGHS hit its iteration limit, and the pair
    `(None, None)` is read downstream as "no linear pagoda separates the goal
    from the start".  An undecided outcome raises `LpUnavailable` carrying the
    status word, so a resource limit cannot arrive at a caller wearing the
    costume of a geometric fact.
    """
    outcome = decide(graph, initial, goal_states=goal_states,
                     solver_options=solver_options, outcome_path=outcome_path)

    if outcome.status == NO_LINEAR_PAGODA:
        return None, None
    if outcome.status != CERTIFIED:
        raise LpUnavailable(
            "lp_potential declines to answer: %s (%s). HiGHS status %r; %s. "
            "No claim about %s follows."
            % (outcome.status, outcome.meaning, outcome.solver_status,
               outcome.solver_message, initial),
            outcome,
        )

    certificate = outcome.certificate
    heuristic = heuristic_from(certificate)
    if out_path:
        emit(out_path, candidates(certificate, heuristic, graph, timestamp=timestamp))
    return certificate, heuristic
