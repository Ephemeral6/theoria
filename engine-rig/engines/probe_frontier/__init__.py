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
from engines.probe_frontier.reach import (  # noqa: F401
    EXECUTABLE,
    HYPOTHETICAL,
    REACHABLE,
    UNREACHABLE,
    Configuration,
    ExecutableProbe,
    Reachability,
    design,
    reach,
    reachability_problem,
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


def executable_payload(probe: ExecutableProbe,
                       hypotheses: Sequence[Hypothesis],
                       state_rendering: Optional[List[str]] = None) -> Dict[str, Any]:
    """The `probe_design` payload for a planner-backed probe.

    A superset of the hypothetical-tier shape above: same keys, same meanings,
    plus `tier`, `verdict` and `reach`.  A reader who only knows the old shape
    still reads this one correctly, which is the point of extending rather than
    replacing -- `cost` now carries the reaching plan's length instead of a
    placeholder 1.
    """
    best = probe.best
    payload: Dict[str, Any] = {
        "action": best.action if best else None,
        "entropy_bits": round(probe.entropy, 12),
        "value_bits_per_cost": round(probe.value, 12),
        "cost": None if probe.cost == float("inf") else probe.cost,
        "n_hypotheses": len(hypotheses),
        "hypotheses": [
            {"id": h.id, "description": h.description, "weight": h.weight}
            for h in hypotheses
        ],
        "partition": best.as_json()["partition"] if best else {},
        "ranking": [value.as_json() for value in probe.ranked],
        "state": state_rendering,
    }
    payload.update(probe.as_json())
    payload["rendering"] = _executable_rendering(probe, hypotheses)
    return payload


def _executable_rendering(probe: ExecutableProbe, hypotheses: Sequence[Hypothesis]) -> str:
    if probe.tier == HYPOTHETICAL and not probe.reach.reachable:
        return (
            "probe %s at %s would split %d hypotheses (%.3f bits), but the "
            "configuration is unreachable -- this experiment cannot be performed "
            "on this instance"
        ) % (
            probe.best.action if probe.best else "-",
            probe.configuration.name, len(hypotheses), probe.entropy,
        )
    if probe.best is None:
        return "no action at %s separates anything" % probe.configuration.name
    return (
        "probe %s at %s: %.3f bits for a path cost of %g (%d-action reach plan "
        "plus the probe itself), %.4f bits per unit cost"
    ) % (
        probe.best.action, probe.configuration.name, probe.entropy, probe.cost,
        probe.reach.length or 0, probe.value,
    )


def executable_candidates(probes: Sequence[ExecutableProbe],
                          hypotheses: Sequence[Hypothesis],
                          transitions: Sequence[int],
                          coverage: Optional[str] = None,
                          timestamp: Optional[str] = None) -> List[Dict[str, Any]]:
    """One `probe_design` per configuration -- including the unreachable ones.

    An unreachable configuration is emitted rather than dropped: "no experiment
    settles this here" is the answer, and silently proposing nothing looks
    identical to having nothing to propose.
    """
    rows = []
    for probe in probes:
        state = probe.configuration.state
        rendering = state.render() if hasattr(state, "render") else None
        rows.append(
            make_candidate(
                engine=ENGINE,
                kind="probe_design",
                payload=executable_payload(probe, hypotheses, rendering),
                transitions=list(transitions),
                coverage=coverage or "%d/%d" % (len(hypotheses), len(hypotheses)),
                timestamp=timestamp,
            )
        )
    return rows


def run_with_planner(hypotheses: Sequence[Hypothesis],
                     configurations: Sequence[Configuration],
                     domain: Any, base_problem: Any,
                     prune: Optional[Any] = None,
                     transitions: Optional[Sequence[int]] = None,
                     coverage: Optional[str] = None,
                     out_path: Optional[str] = None,
                     timestamp: Optional[str] = None) -> List[ExecutableProbe]:
    """Design probes, ask the planner whether each site is reachable, emit both tiers."""
    probes = design(hypotheses, configurations, domain, base_problem, prune=prune)
    if out_path:
        emit(
            out_path,
            executable_candidates(
                probes, hypotheses,
                transitions=list(transitions or []),
                coverage=coverage,
                timestamp=timestamp,
            ),
        )
    return probes


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
