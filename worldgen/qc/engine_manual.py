"""The mined rule set, applied as a frame predictor.

`cold-start-a0` scores a *manual* — a hand-written `theory.dsl` compiled to
`theory.py` whose `step` and `render` are then compared frame-for-frame against
the world (`certify/score_vs_truth.py`).  Twenty worlds cannot each be given a
hand-written manual, and `run_all.py` is explicit that the theorize step is the
one a script cannot do.

So this module builds the object that sits one step *before* a manual: the raw
mined rule set, given a `step` and a `render` mechanically, with no adjudication
anywhere.  Scoring it answers a narrower question than "is the manual right",
and it is the question the factory actually needs answered — **does this world's
trajectory carry its mechanisms**?  If the engines can already predict the world
from the shipped trace, the theorize step downstream is being handed evidence
that determines the answer.  If they cannot, no amount of adjudication invents
the missing witness.

The two halves, and the reason each is mechanical:

* **`render`** — the board (what never varies across the trace) plus each track
  painted at its anchor.  This is `pipeline/board.py`'s decomposition, unchanged;
  the only choice here is paint order, and it is the world's own: the mover last,
  so it wins every overlap, as `GridWorld.render` and `A0PWorld.render` both do.
* **`step`** — per track, the mined ground rules whose action matches and whose
  guard evaluates true on the current `Obs`.  Ties are broken by the miner's own
  sort order and *counted*, because a tie is a defect in the rule set and hiding
  it would flatter the score.  No rule firing means "nothing happens", which is
  the frame axiom `cold-start-a0`'s dialect makes explicit (`semantics:`, E-03).

Lifted (`?dir`) rules are deliberately **not** used.  They are alpha-equivalent
restatements of the ground rules and applying both would double-count every
firing; `MiningResult.rules` is the ground set and `.lifted` is the summary.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .bridge import atoms_a0, multi_miner

Cell = Tuple[int, int]
Frame = List[List[int]]

DELTA = atoms_a0.DELTA


@dataclass(frozen=True)
class TrackState:
    """Where one track is and what colour it shows, at one instant.

    `last_anchor` survives a `vanish`, which is what lets an `appear` be
    predicted at all — see `_apply`.
    """

    anchor: Optional[Cell]
    color: Optional[int]
    last_anchor: Optional[Cell] = None

    def seen_at(self) -> Optional[Cell]:
        return self.anchor if self.anchor is not None else self.last_anchor


def track_states_at(seg, t: int) -> Dict[str, TrackState]:
    """Read every track's anchor and colour out of the segmentation at frame `t`."""
    out: Dict[str, TrackState] = {}
    for track in seg.tracks:
        anchor = track.anchors[t] if t < len(track.anchors) else None
        out[track.track_id] = TrackState(
            anchor=tuple(anchor) if anchor is not None else None,
            color=track.color,
        )
    return out


def observed_colors_at(seg, layer, t: int) -> Dict[str, Optional[int]]:
    """The colour each track actually shows in frame `t`, off its own mask.

    `Track.color` is the colour the track was *declared* with; a recolouring
    track (a switch) shows something else later.  `multi_miner.seg_color` reads
    the live value and is reused verbatim so that the predictor and the miner
    cannot disagree about what a colour is.
    """
    return {t_.track_id: multi_miner.seg_color(seg, layer, t_.track_id, t)
            for t_ in seg.tracks}


class EngineManual:
    """`step` + `render` induced from a `MiningResult`, and nothing else."""

    def __init__(self, board, background: int, seg, result, mover: str):
        self.board = board
        self.background = background
        self.seg = seg
        self.result = result
        self.mover = mover
        self.track_ids: List[str] = [t.track_id for t in seg.tracks]
        self.rel_cells: Dict[str, Tuple[Cell, ...]] = {
            t.track_id: tuple(tuple(c) for c in t.rel_cells) for t in seg.tracks
        }
        # Ground rules only, grouped for lookup.  Order is the miner's.
        self.by_track_action: Dict[Tuple[str, str], List[Any]] = {}
        for rule in result.rules:
            self.by_track_action.setdefault((rule.track, rule.action), []).append(rule)

    # ------------------------------------------------------------- rendering

    def render(self, states: Dict[str, TrackState]) -> Frame:
        frame = self.board.render(self.background)
        order = sorted(tid for tid in self.track_ids if tid != self.mover)
        if self.mover in self.track_ids:
            order.append(self.mover)             # painted last, wins overlaps
        for tid in order:
            ts = states.get(tid)
            if ts is None or ts.anchor is None or ts.color is None:
                continue
            ar, ac = ts.anchor
            for dr, dc in self.rel_cells[tid]:
                r, c = ar + dr, ac + dc
                if 0 <= r < len(frame) and 0 <= c < len(frame[0]):
                    frame[r][c] = ts.color
        return frame

    # ------------------------------------------------------------------ step

    def fire(self, track: str, obs, action: str):
        """(rule, n_fired) — the rule this track's guards select, if any."""
        fired = [
            rule for rule in self.by_track_action.get((track, action), [])
            if all(atoms_a0.evaluate(atom, obs, action) for atom in rule.guard)
        ]
        return (fired[0] if fired else None), len(fired)

    def step(self, states: Dict[str, TrackState], obs, action: str):
        """Predicted next `TrackState` per track, plus the conflict count."""
        out: Dict[str, TrackState] = {}
        conflicts = 0
        for tid in self.track_ids:
            current = states.get(tid, TrackState(None, None))
            rule, n = self.fire(tid, obs, action)
            if n > 1:
                conflicts += 1
            out[tid] = current if rule is None else _apply(current, rule.effect, action)
        return out, conflicts

    def predict_frame(self, states: Dict[str, TrackState], obs, action: str):
        nxt, conflicts = self.step(states, obs, action)
        return self.render(nxt), nxt, conflicts


def _apply(state: TrackState, effect, action: str) -> TrackState:
    kind = effect.type
    if kind == "none":
        return state
    if kind == "move":
        if state.anchor is None:
            return state
        dy, dx = (DELTA[action] if effect.direction is not None
                  else (effect.dy, effect.dx))
        return TrackState(anchor=(state.anchor[0] + dy, state.anchor[1] + dx),
                          color=state.color, last_anchor=state.anchor)
    if kind == "recolor":
        return TrackState(anchor=state.anchor, color=effect.to_color,
                          last_anchor=state.last_anchor)
    if kind == "vanish":
        # The anchor is remembered, not discarded.  A door that closes is the
        # same door, and `pipeline/reidentify.py` exists upstream precisely so
        # that a track which vanishes and returns keeps one identity — A0′ found
        # its single Door segmented as five without it.
        return TrackState(anchor=None, color=state.color,
                          last_anchor=state.seen_at())
    if kind == "appear":
        # `Effect` carries no position for an appearance, so the *rule* does not
        # say where the object comes back.  The *segmentation* does: this is a
        # track, it has an identity across its absence, and the last place it was
        # seen is the only position the evidence offers.  Predicting there is
        # reconstruction from what the pipeline emitted, not a peek at the ground
        # truth — a human writing the manual from this narration would say "the
        # Door reappears at (3,4)" for exactly the same reason.  Where a world
        # makes objects reappear somewhere new, this will be wrong and will score
        # as a miss, which is the correct outcome.
        return TrackState(anchor=state.seen_at(), color=state.color,
                          last_anchor=state.last_anchor)
    return state
