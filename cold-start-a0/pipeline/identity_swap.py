"""Identity repair: the mover stepped onto it, it did not become the mover.

`reidentify` fixes the object that *comes back*.  This fixes the object that
*gets eaten* — and unlike that one, this repair costs bits, which is the whole
reason it has to be written down rather than assumed.

## What goes wrong

`mdl_segmenter` matches frame *t* against frame *t+1* with a bipartite
assignment scored in bits.  When a one-cell mover steps onto a one-cell
stationary object of a different colour, two explanations cover exactly the same
changed pixels:

| reading | events | bits |
|---|---|---|
| the stationary object **recoloured in place**, the mover **vanished** | recolor + vanish | 9 + 5 = **14** |
| the mover **moved** onto it, the stationary object **vanished** | move + vanish | 11 + 5 = **16** |

A one-cell recolour is `b_evtype + b_objid + b_color` = 9.  A one-step move is
`b_evtype + b_objid + offset(1) + offset(0)` = 11.  So the first reading is
**strictly cheaper**, and the assignment is per-transition and independent, so
the matcher is not failing to search — it is finding the optimum of the
published objective.  The objective prefers teleporting an identity to moving a
body.

## What it costs downstream

A0's cart world has nothing that gets consumed, which is why this sat undetected
through eight milestones.  On any world with a consumable it is fatal:
`worldgen`'s `t2-lock-fragile` has three tokens, so the agent's identity is
handed to a token three times, and `multi_miner.mover_track` — "the track that
moves most" — then names a *token* as the mover.  Every positional atom in
`a0_relational_v1` (`at`, `free(strip(D))`, `in_bounds`, `clear`, `tcolor`) is
anchored on the mover, so the whole vocabulary ends up aimed at an object that
never moved.  Measured attribution before this pass, over 110 transitions: the
agent is credited with **1** move, three stationary tokens with **61**.

## The one rung this pass claims, and its price

It fires on exactly one pattern, at one transition *t*:

  * track `a` **vanishes** at *t*;
  * track `b` **recolours** at *t*, all of its cells, to `a`'s colour;
  * `a` and `b` have the same shape, so a move between them is representable;
  * their anchors at *t* are 4-adjacent (L1 distance 1).

Then `a` moved onto `b` and `b` was consumed: `a` takes `b`'s future, `b` ends.
Anything wider — a non-adjacent swap, a partial recolour, a shape change — is
**not** repaired and is counted into the report as a near miss, so the next rung
has a forcing case rather than a guess.

The price is real and is not hidden: `+2` bits per repaired swap under the
published cost model, so this is the one place in the pipeline where a
segmentation decision is *not* made by script length.  The reason it is taken
anyway is that description length here is the segmentation script **plus** the
rule script, and the mis-anchored reading has no rule script at all — the miner
raises `NoSeparatingGuard` rather than paying more bits.  Two bits of frame
narration against a theory that exists is not a close call, but it is a
different criterion from the one `choose_operator` uses, and callers get the
number so they can disagree.

Upstream is untouched: this consumes a `Segmentation` and returns a new one.
"""

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from engines.mdl_segmenter.costs import CostModel
from engines.mdl_segmenter.segmenter import Event, Segmentation, Track


@dataclass
class Swap:
    """One repaired hand-over: `mover` stepped onto `eaten` at transition `t`."""

    t: int
    mover: str
    eaten: str
    dy: int
    dx: int
    bits_before: int
    bits_after: int

    def as_json(self) -> Dict[str, object]:
        return {
            "t": self.t,
            "mover": self.mover,
            "eaten": self.eaten,
            "displacement": [self.dy, self.dx],
            "bits_before": self.bits_before,
            "bits_after": self.bits_after,
            "delta_bits": self.bits_after - self.bits_before,
        }


@dataclass
class SwapReport:
    swaps: List[Swap] = field(default_factory=list)
    near_misses: List[Dict[str, object]] = field(default_factory=list)
    script_bits_before: int = 0
    script_bits_after: int = 0
    applied: bool = False

    def as_json(self) -> Dict[str, object]:
        return {
            "operator": "identity_swap_repair(adjacent,full_recolor,same_shape)",
            "swaps": [s.as_json() for s in self.swaps],
            "n_swaps": len(self.swaps),
            "near_misses": self.near_misses,
            "script_bits_before": self.script_bits_before,
            "script_bits_after": self.script_bits_after,
            "delta_bits": self.script_bits_after - self.script_bits_before,
            "priced_by": "not script length -- see module docstring",
            "applied": self.applied,
        }


def _anchor(track: Track, t: int) -> Optional[Tuple[int, int]]:
    if 0 <= t < len(track.anchors) and track.anchors[t] is not None:
        return tuple(track.anchors[t])
    return None


def _present(track: Track, t: int) -> bool:
    return 0 <= t < len(track.masks) and track.masks[t] is not None


def _recolor_is_total(event: Event, track: Track, to_color: Optional[int]) -> bool:
    """The recolour turned *all* of `track`'s cells into `to_color`."""
    cells = event.params.get("cells") or []
    to = event.params.get("to") or []
    if len(cells) != len(track.rel_cells):
        return False
    if not to or to_color is None:
        return False
    return all(int(c) == int(to_color) for c in to)


def repair_identity_swaps(seg: Segmentation,
                          cost: CostModel) -> Tuple[Segmentation, SwapReport]:
    """Re-thread identities the matcher handed to the object that was consumed."""
    tracks: List[Track] = [deepcopy(t) for t in seg.tracks]
    by_id: Dict[str, Track] = {t.track_id: t for t in tracks}
    events: List[Event] = [
        Event(t=e.t, type=e.type, track=e.track, params=dict(e.params), bits=e.bits)
        for e in seg.events
    ]

    report = SwapReport(script_bits_before=seg.script_bits,
                        script_bits_after=seg.script_bits)

    horizon = max((e.t for e in events), default=-1)
    for t in range(horizon + 1):
        at_t = [e for e in events if e.t == t]
        vanished = [e for e in at_t if e.type == "vanish"]
        recolored = [e for e in at_t if e.type == "recolor"]
        if not vanished or not recolored:
            continue
        taken_eaten: set = set()
        for v_event in sorted(vanished, key=lambda e: e.track):
            mover = by_id.get(v_event.track)
            if mover is None or not _present(mover, t) or _present(mover, t + 1):
                continue
            for r_event in sorted(recolored, key=lambda e: e.track):
                eaten = by_id.get(r_event.track)
                if eaten is None or eaten.track_id in taken_eaten:
                    continue
                if eaten.track_id == mover.track_id:
                    continue
                if not (_present(eaten, t) and _present(eaten, t + 1)):
                    continue
                if not _recolor_is_total(r_event, eaten, mover.color):
                    report.near_misses.append(
                        {"t": t, "mover": mover.track_id, "eaten": eaten.track_id,
                         "why": "recolour is not this track's whole body in the "
                                "vanishing track's colour"})
                    continue
                if tuple(mover.rel_cells) != tuple(eaten.rel_cells):
                    report.near_misses.append(
                        {"t": t, "mover": mover.track_id, "eaten": eaten.track_id,
                         "why": "shapes differ, a move between them is not "
                                "representable"})
                    continue
                a_mover, a_eaten = _anchor(mover, t), _anchor(eaten, t)
                if a_mover is None or a_eaten is None:
                    continue
                dy, dx = a_eaten[0] - a_mover[0], a_eaten[1] - a_mover[1]
                if abs(dy) + abs(dx) != 1:
                    report.near_misses.append(
                        {"t": t, "mover": mover.track_id, "eaten": eaten.track_id,
                         "displacement": [dy, dx],
                         "why": "not 4-adjacent; this pass claims one rung only"})
                    continue

                bits_before = v_event.bits + r_event.bits
                v_event.type = "move"
                v_event.track = mover.track_id
                v_event.params = {"dy": dy, "dx": dx}
                v_event.bits = cost.move_bits(dy, dx)
                r_event.type = "vanish"
                r_event.track = eaten.track_id
                r_event.params = {"consumed_by": mover.track_id}
                r_event.bits = cost.vanish_bits()
                bits_after = v_event.bits + r_event.bits

                for i in range(t + 1, len(mover.masks)):
                    mover.masks[i] = eaten.masks[i]
                    mover.anchors[i] = eaten.anchors[i]
                    eaten.masks[i] = None
                    eaten.anchors[i] = None
                for e in events:
                    if e.t > t and e.track == eaten.track_id:
                        e.track = mover.track_id

                report.swaps.append(Swap(t=t, mover=mover.track_id,
                                         eaten=eaten.track_id, dy=dy, dx=dx,
                                         bits_before=bits_before,
                                         bits_after=bits_after))
                report.script_bits_after += bits_after - bits_before
                taken_eaten.add(eaten.track_id)
                break

    if not report.swaps:
        return seg, report

    report.applied = True
    return Segmentation(
        tracks=tracks,
        events=events,
        script_bits=report.script_bits_after,
        baseline_bits=seg.baseline_bits,
        declaration_bits=seg.declaration_bits,
        n_frames=seg.n_frames,
    ), report
