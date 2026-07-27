"""probe_frontier -- public entry points."""

from typing import Any, Dict, List, Optional, Sequence

from common.candidates import emit, make_candidate
from engines.probe_frontier import scenario  # noqa: F401
from engines.probe_frontier.frontier import (  # noqa: F401
    Hypothesis,
    ProbeValue,
    best_probe,
    entropy_of,
    partition_for,
    probe_value,
    rank_probes,
    surviving,
)

ENGINE = "probe_frontier"


def hypotheses_from_guards(guards: Sequence[Sequence[Any]],
                           evaluate: Any,
                           label: str = "guard") -> List[Hypothesis]:
    """Turn a cegis_miner frontier into probe hypotheses.

    Each guard from the frontier becomes a hypothesis predicting whether the
    rule's effect fires.  This is the shared data structure the framework asks
    for: the miner's leftover ambiguity is exactly the probe's input.
    """
    out = []
    for index, guard in enumerate(guards):
        names = sorted(getattr(atom, "name", str(atom)) for atom in guard)

        def predict(state, action, guard=guard):
            return "fires" if all(evaluate(atom, state, action) for atom in guard) else "silent"

        out.append(
            Hypothesis(
                id="%s_%d" % (label, index),
                predict=predict,
                description=" AND ".join(names),
            )
        )
    return out


def to_payload(best: ProbeValue, ranked: Sequence[ProbeValue],
               hypotheses: Sequence[Hypothesis],
               state_rendering: Optional[List[str]] = None) -> Dict[str, Any]:
    """The probe_design payload shape; frozen in this engine's README."""
    return {
        "action": best.action,
        "entropy_bits": round(best.entropy, 12),
        "value_bits_per_cost": round(best.value, 12),
        "cost": best.cost,
        "n_hypotheses": len(hypotheses),
        "hypotheses": [
            {"id": h.id, "description": h.description, "weight": h.weight}
            for h in hypotheses
        ],
        "partition": best.as_json()["partition"],
        "ranking": [value.as_json() for value in ranked],
        "state": state_rendering,
        "rendering": "probe %s: it splits %d hypotheses into %d outcome classes "
                     "(%.3f bits)" % (
                         best.action, len(hypotheses), best.n_classes, best.entropy
                     ),
    }


def candidates(best: ProbeValue, ranked: Sequence[ProbeValue],
               hypotheses: Sequence[Hypothesis],
               transitions: Sequence[int],
               coverage: str,
               state_rendering: Optional[List[str]] = None,
               timestamp: Optional[str] = None) -> List[Dict[str, Any]]:
    return [
        make_candidate(
            engine=ENGINE,
            kind="probe_design",
            payload=to_payload(best, ranked, hypotheses, state_rendering),
            transitions=transitions,
            coverage=coverage,
            timestamp=timestamp,
        )
    ]


def run(hypotheses: Sequence[Hypothesis], state: Any, actions: Sequence[Any],
        costs: Optional[Dict[Any, float]] = None,
        transitions: Optional[Sequence[int]] = None,
        coverage: Optional[str] = None,
        state_rendering: Optional[List[str]] = None,
        out_path: Optional[str] = None,
        timestamp: Optional[str] = None):
    """Rank the candidate actions; emit the best splitter as a probe design.

    Returns (best, ranked). `best` is None when no action separates anything --
    a real answer, meaning this state cannot advance the frontier.
    """
    ranked = rank_probes(hypotheses, state, actions, costs=costs)
    best = ranked[0] if ranked and ranked[0].splits else None
    if best is not None and out_path:
        emit(
            out_path,
            candidates(
                best,
                ranked,
                hypotheses,
                transitions=list(transitions or []),
                coverage=coverage or "%d/%d" % (len(hypotheses), len(hypotheses)),
                state_rendering=state_rendering,
                timestamp=timestamp,
            ),
        )
    return best, ranked
