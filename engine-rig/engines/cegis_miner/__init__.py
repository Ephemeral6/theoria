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
    while_present: bool = False,
) -> List[Transition]:
    """Turn frames + the segmenter's object trajectory into mineable transitions.

    The miner never reads pixels to decide *what happened* -- that is the
    segmenter's narration.  It reads pixels only to evaluate guards.

    `while_present` bounds the window to the frames where the object exists.
    The default `False` is the original scope: the walk starts at frame 0 and a
    track that is not there yet raises.  That is right for a fixture where every
    object is born in the prologue and wrong for a trajectory where objects
    appear -- on the recorded `g50t` r3 leg it discarded 14 of 18 tracks for
    being absent at a frame that has nothing to do with their evidence.  With
    `while_present=True` the walk runs over `[first_frame, last_present]`, which
    is where the track's evidence actually is; an object that vanishes and
    returns still raises, because a gap is a claim about identity that the
    miner is not entitled to make.  See DECISIONS.md D-E20-003.
    """
    track = track or seg.tracks[0]
    out: List[Transition] = []
    present = [i for i, a in enumerate(track.anchors) if a is not None]
    if while_present and not present:
        return out
    start = present[0] if while_present else 0
    stop = present[-1] if while_present else len(frames) - 1
    for t in range(start, min(stop, len(frames) - 1)):
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
        timestamp: Optional[str] = None, on_unseparable: str = "raise",
        action_alphabet: Optional[Sequence[str]] = None) -> MiningResult:
    result = mine(transitions, on_unseparable=on_unseparable,
                  action_alphabet=action_alphabet)
    if out_path:
        emit(out_path, candidates(result, timestamp=timestamp))
    return result
