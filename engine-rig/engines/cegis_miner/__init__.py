"""cegis_miner -- public entry points."""

from typing import Any, Dict, List, Optional, Sequence

from common.candidates import emit, make_candidate
from engines.cegis_miner.atoms import State  # noqa: F401
from engines.cegis_miner.miner import (  # noqa: F401
    Effect,
    MiningResult,
    NoSeparatingGuard,
    Rule,
    Transition,
    enumerate_frontier,
    lift,
    mine,
    structural_name,
    synthesize,
)
from engines.mdl_segmenter import Segmentation, Track

ENGINE = "cegis_miner"


def transitions_from_segmentation(
    frames: Sequence[Sequence[Sequence[int]]],
    actions: Sequence[Optional[str]],
    seg: Segmentation,
    track: Optional[Track] = None,
    background: int = 0,
) -> List[Transition]:
    """Turn frames + the segmenter's object trajectory into mineable transitions.

    The miner never reads pixels to decide *what happened* -- that is the
    segmenter's narration.  It reads pixels only to evaluate guards.
    """
    track = track or seg.tracks[0]
    out: List[Transition] = []
    for t in range(len(frames) - 1):
        action = actions[t]
        if action is None:
            break
        anchor = track.anchors[t]
        if anchor is None:
            raise ValueError("object absent at frame %d; unsupported on this fixture" % t)
        events = [e for e in seg.events_at(t) if e.track == track.track_id]
        if not events:
            effect = Effect(type="none")
        elif len(events) == 1 and events[0].type == "move":
            nxt = track.anchors[t + 1]
            effect = Effect(
                type="move",
                dy=int(events[0].params["dy"]),
                dx=int(events[0].params["dx"]),
                to=tuple(nxt) if nxt is not None else None,
            )
        else:
            raise ValueError(
                "transition %d narrates %r; only move/none are mined on this fixture"
                % (t, [e.type for e in events])
            )
        state = State(
            frame=tuple(tuple(row) for row in frames[t]),
            anchor=tuple(anchor),
            shape=tuple(track.shape),
            background=background,
        )
        out.append(Transition(index=t, state=state, action=action, effect=effect))
    return out


def to_payload(rule: Rule) -> Dict[str, Any]:
    """The rule_hypothesis payload shape; frozen in this engine's README."""
    return rule.as_json()


def candidates(result: MiningResult, timestamp: Optional[str] = None) -> List[Dict[str, Any]]:
    return [
        make_candidate(
            engine=ENGINE,
            kind="rule_hypothesis",
            payload=to_payload(rule),
            transitions=rule.support,
            coverage=rule.coverage,
            timestamp=timestamp,
        )
        for rule in result.all_rules
    ]


def run(transitions: Sequence[Transition], out_path: Optional[str] = None,
        timestamp: Optional[str] = None) -> MiningResult:
    result = mine(transitions)
    if out_path:
        emit(out_path, candidates(result, timestamp=timestamp))
    return result
