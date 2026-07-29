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

  * track `a` **vanishes** at *t*, and never comes back;
  * track `b` **recolours** at *t* — its whole body, exactly its own cells, into
    `a`'s colour *as of t* (not `a.color`, which is the colour `a` was declared
    with and goes stale the moment `a` recolours);
  * `a` and `b` have the same shape, so a move between them is representable;
  * their anchors at *t* are 4-adjacent (L1 distance 1);
  * `b`'s body from *t+1* on is one contiguous run — a track that vanishes and
    *returns* was not consumed, and handing its whole suffix to `a` would hand
    `a` an un-narrated teleport. Return-after-absence belongs to `reidentify`.

Then `a` moved onto `b` and `b` was consumed: `a` takes `b`'s future, `b` ends.
Everything else is refused with its own reason and counted into the report as a
near miss, so the next rung has a forcing case rather than a guess.

**An ambiguous transition is refused whole.** If two vanishing tracks could each
have eaten the same object, or one could have eaten either of two, the pass takes
*none* of those pairings. Both matchings are equally supported by the pixels, and
picking one by track id would make the answer an artefact of which raster cell
the segmenter happened to number first. The entire justification for overruling
the matcher here is that this pass reads a signature the matcher's per-transition
scoring cannot; where the signature is ambiguous it has nothing to say, and says
so in the report rather than guessing. A world that needs those transitions
repaired is the forcing case for the next rung.

**Standing on something is not eating it, and that is why this pass needs the
pixels.** An adversarial review found the decisive case in a shipped world:
`worldgen`'s `t2-cycler-lock` lets the agent walk *over* a cycler tile, and the
frames produce vanish + total recolour + same shape + adjacent — the signature,
exactly. Repairing it hands the agent's identity to the tile it is standing on,
and the mover gets *worse*: 46/61 frames tracking the agent before the repair,
33/61 after. Nothing in the `Segmentation` distinguishes the two stories, because
at that transition they are the same picture. The pixels distinguish them, but
only **later**: an occluded body shows itself again the moment the mover steps
off, and a consumed one never does. So the pass takes the object layer and
refuses any candidate whose cells go back to showing something other than floor.
Measured over all 35 worldgen worlds through `choose_operator`: **7 improved, 0
regressed** (`probes/11_mover_tracks_the_agent.py`).

Two limits worth stating rather than discovering. First: without `frames` the
occlusion test cannot run and the pass is strictly more permissive — the report
carries `occlusion_test_ran` so that is visible rather than assumed. Second, like
`reidentify`, when nothing fires it returns the *input* object rather than a
copy.

The price is real and is not hidden: `+2` bits per repaired swap for a one-cell
mover (the delta is `6 - 4k` for a *k*-cell mover, so a larger body actually
makes the honest reading cheaper), and it is charged in the same currency the
script was written in — `segment_operators._max_objects` reproduces upstream's
`b_objid` width rather than deriving one from the track count, or `script_bits`
would stop being the length of any single code.

This is the one place in the pipeline where a
segmentation decision is *not* made by script length.  The reason it is taken
anyway is that description length here is the segmentation script **plus** the
rule script, and the mis-anchored reading has no rule script at all — the miner
raises `NoSeparatingGuard` rather than paying more bits.  Two bits of frame
narration against a theory that exists is not a close call, but it is a
different criterion from the one `choose_operator` uses, and callers get the
number so they can disagree.

Upstream is untouched: this consumes a `Segmentation` and returns a new one.
"""

from collections import Counter
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
    saw_pixels: bool = False

    def as_json(self) -> Dict[str, object]:
        return {
            "operator": "identity_swap_repair(adjacent,full_recolor,same_shape,"
                        "not_occlusion)",
            "occlusion_test_ran": self.saw_pixels,
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


def _recolor_is_total(event: Event, track: Track, t: int,
                      to_color: Optional[int]) -> bool:
    """The recolour turned *all* of `track`'s own cells into `to_color`.

    Comparing the count alone is not enough: a recolour of *n* cells somewhere
    else on the board would pass that. The cells must be this track's body.
    """
    cells = event.params.get("cells") or []
    to = event.params.get("to") or []
    if not to or to_color is None:
        return False
    body = track.masks[t] if 0 <= t < len(track.masks) else None
    if body is None:
        return False
    if sorted(tuple(c) for c in cells) != sorted(tuple(c) for c in body):
        return False
    return all(int(c) == int(to_color) for c in to)


def _color_now(track: Track, t: int, events: Sequence[Event]) -> Optional[int]:
    """`track.color` is its colour when it was declared, not its colour now.

    A track that has already recoloured -- including one that recoloured because
    an earlier swap was repaired around it -- carries a stale `color`, and
    adjudicating the next hop against it refuses a genuine step-onto.  Replay the
    recolours instead.
    """
    color = track.color
    for event in sorted((e for e in events
                         if e.track == track.track_id
                         and e.type == "recolor" and e.t < t),
                        key=lambda e: e.t):
        to = event.params.get("to") or []
        if to:
            color = int(to[0])
    return color


def _absent_from(track: Track, t: int) -> bool:
    """The track has no body at or after `t`."""
    return all(m is None for m in track.masks[t:])


def _leaves_and_never_returns(track: Track, t: int) -> bool:
    """From `t` on, the track is present for a while and then gone for good.

    A track that vanishes and *comes back* is not a track that was consumed, and
    handing its whole suffix to the mover would hand the mover an un-narrated
    teleport across the board.  `reidentify` owns return-after-absence; this pass
    must not eat its cases.
    """
    tail = track.masks[t:]
    seen_gap = False
    for mask in tail:
        if mask is None:
            seen_gap = True
        elif seen_gap:
            return False
    return True


def _comes_back_into_view(frames, background: int, cells, mover_color, t: int):
    """Did the body under the mover show itself again after the mover left?

    This is the occlusion test, and it is the one check the `Segmentation` alone
    cannot make.  Standing **on** something and destroying it produce the same
    two events at the same transition; the pixels tell them apart, but only
    *later* — a consumed object's cells go to the mover and then to floor, while
    an occluded one shows itself again the moment the mover steps off.

    Returns the frame index where it reappeared, or `None`.
    """
    if frames is None:
        return None
    for i in range(t + 1, len(frames)):
        values = {frames[i][r][c] for r, c in cells}
        if len(values) != 1:
            continue
        value = values.pop()
        if value != background and value != mover_color:
            return i
    return None


def _well_formed(seg: Segmentation) -> bool:
    """Every track carries one mask and one anchor per frame.

    A ragged `Segmentation` is not something `mdl_segmenter` produces, and
    re-threading one silently produces a worse-formed one.  Refuse instead.
    """
    return all(len(t.masks) == seg.n_frames and len(t.anchors) == seg.n_frames
               for t in seg.tracks)


def repair_identity_swaps(seg: Segmentation, cost: CostModel,
                          frames=None,
                          background: int = 0) -> Tuple[Segmentation, SwapReport]:
    """Re-thread identities the matcher handed to the object that was consumed.

    `frames` is the object layer the segmentation was built on.  It is optional
    only so that a caller can price the pass without it; **without it the
    occlusion test cannot run** and the pass is strictly more permissive, which
    is recorded in the report rather than left to be inferred.
    """
    tracks: List[Track] = [deepcopy(t) for t in seg.tracks]
    by_id: Dict[str, Track] = {t.track_id: t for t in tracks}
    events: List[Event] = [
        Event(t=e.t, type=e.type, track=e.track, params=dict(e.params), bits=e.bits)
        for e in seg.events
    ]

    report = SwapReport(script_bits_before=seg.script_bits,
                        script_bits_after=seg.script_bits,
                        saw_pixels=frames is not None)

    if not _well_formed(seg):
        report.near_misses.append(
            {"t": None, "mover": None, "eaten": None,
             "why": "the segmentation is ragged -- some track does not carry one "
                    "mask and one anchor per frame; refusing to re-thread it"})
        return seg, report

    horizon = max((e.t for e in events), default=-1)
    for t in range(horizon + 1):
        at_t = [e for e in events if e.t == t]
        vanished = [e for e in at_t if e.type == "vanish"]
        recolored = [e for e in at_t if e.type == "recolor"]
        if not vanished or not recolored:
            continue

        # --- propose, then check that the evidence names one answer ---------
        proposals = []
        for v_event in sorted(vanished, key=lambda e: e.track):
            mover = by_id.get(v_event.track)
            if mover is None or not _present(mover, t) or _present(mover, t + 1):
                continue
            if not _absent_from(mover, t + 1):
                report.near_misses.append(
                    {"t": t, "mover": mover.track_id, "eaten": None,
                     "why": "the vanishing track comes back later; that is "
                            "return-after-absence and belongs to reidentify"})
                continue
            mover_color = _color_now(mover, t, events)
            for r_event in sorted(recolored, key=lambda e: e.track):
                eaten = by_id.get(r_event.track)
                if eaten is None or eaten.track_id == mover.track_id:
                    continue
                if not (_present(eaten, t) and _present(eaten, t + 1)):
                    continue
                if not _recolor_is_total(r_event, eaten, t, mover_color):
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
                if not _leaves_and_never_returns(eaten, t + 1):
                    report.near_misses.append(
                        {"t": t, "mover": mover.track_id, "eaten": eaten.track_id,
                         "why": "the eaten track returns after a gap, so its "
                                "suffix is not the mover's body"})
                    continue
                back = _comes_back_into_view(
                    frames, background, eaten.masks[t], mover_color, t)
                if back is not None:
                    report.near_misses.append(
                        {"t": t, "mover": mover.track_id, "eaten": eaten.track_id,
                         "reappears_at": back,
                         "why": "those cells show something other than floor "
                                "again at frame %d, so the mover stood on it "
                                "rather than consuming it" % back})
                    continue
                proposals.append((mover, eaten, v_event, r_event, dy, dx))

        # An ambiguous transition is refused whole.  Choosing between two equally
        # supported pairings by track id would be an artefact of which raster
        # cell the segmenter numbered first, dressed up as physics -- and this
        # pass's whole justification is that it reads a signature the matcher
        # cannot.  Where the signature is ambiguous it has nothing to say.
        movers = Counter(p[0].track_id for p in proposals)
        eatens = Counter(p[1].track_id for p in proposals)
        contested = {i for i, p in enumerate(proposals)
                     if movers[p[0].track_id] > 1 or eatens[p[1].track_id] > 1}
        for i in sorted(contested,
                        key=lambda i: (proposals[i][0].track_id,
                                       proposals[i][1].track_id)):
            mover, eaten, _v, _r, dy, dx = proposals[i]
            report.near_misses.append(
                {"t": t, "mover": mover.track_id, "eaten": eaten.track_id,
                 "displacement": [dy, dx],
                 "why": "more than one pairing is equally supported at this "
                        "transition; the evidence does not choose one, so none "
                        "is taken"})

        for i, (mover, eaten, v_event, r_event, dy, dx) in enumerate(proposals):
            if i in contested:
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

            for i in range(t + 1, seg.n_frames):
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
