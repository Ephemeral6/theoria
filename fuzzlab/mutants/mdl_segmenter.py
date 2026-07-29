"""`mdl_segmenter` mutants — eleven defects across four invariants.

The seam is `props/mdl_segmenter.py:_segment`, the module's only call into
`engines.mdl_segmenter.segment_trajectory`; all four invariants go through it, so
one rebinding covers the whole battery. Each mutant is the `Segmentation` the
engine *would* have returned with a particular bug, and every `expect_kill` was
written before the driver was run once.

Two structural facts about `Segmentation` decide what a mutant here can be, and
both change what a kill means:

* **`masks` and `anchors` are independent fields, and `rel_cells` is a third.**
  So a mutant can move a track rigidly (anchors *and* masks together, leaving
  `rel_cells` alone) and hit `masks_partition_the_foreground` without touching
  `masks_follow_anchors` — or perturb `rel_cells` alone and hit
  `masks_follow_anchors` and nothing else. A mutant that trips every invariant
  says nothing about which one is load-bearing.
* **Four fields of the engine's own output are read by no invariant**:
  `Track.color`, `Track.shape`, `Track.first_frame` and
  `Segmentation.baseline_bits`, plus `Event.params` for every event type except
  `move`, and `Event.bits` only ever in aggregate. `mdl-flip-track-color`,
  `mdl-inflate-baseline-bits` and `mdl-misprice-event` are pre-registered
  *predicted survivors* aimed at exactly that gap: the point of running them is
  to put a measured number under a claim otherwise made by reading.

`Mutant.expect_kill` may not be empty (`mutants/__init__.py:__post_init__`), so
those three name the nearest invariant that reads anything in the same
neighbourhood rather than the one that actually covers them — there is none. The
`PREDICTED SURVIVOR` prefix in `description` is what carries the honest
prediction, and the partial report says so in the same words.
"""

import copy
from typing import Any, Dict, List, Tuple

from fuzzlab import mutants as mut

ENGINE = "mdl_segmenter"
SEAM = "_segment"

# costs.py:CostModel.b_header -- the per-transition header both the object script
# and the pixel baseline pay. Duplicated here (as in props) rather than imported,
# so a mutant does not quietly inherit the number it is testing.
HEADER_BITS = 8

# The rigid displacement used by `mdl-shift-track-rigidly`. Any non-zero offset
# works: a finite non-empty cell set is never equal to a translate of itself, so
# the union over tracks always stops matching the frame's foreground.
SHIFT = (0, 1)

NARRATED = ("move", "appear", "vanish")


# ------------------------------------------------------------------- helpers

def _present_frames(track: Any) -> List[int]:
    return [t for t, anchor in enumerate(track.anchors)
            if anchor is not None and track.masks[t] is not None]


def _first_present_track(result: Any) -> Tuple[Any, List[int]]:
    for track in result.tracks:
        present = _present_frames(track)
        if present:
            return track, present
    raise mut.inert("no track is present in any frame; nothing to corrupt")


def _events_by_track_t(result: Any) -> Dict[Tuple[str, int], List[Any]]:
    out: Dict[Tuple[str, int], List[Any]] = {}
    for event in result.events:
        out.setdefault((event.track, event.t), []).append(event)
    return out


# ------------------------------------------------------------------- mutants

def _shift_track_rigidly(result: Any, args: Tuple[Any, ...],
                         kwargs: Dict[str, Any]) -> Any:
    track, present = _first_present_track(result)
    dr, dc = SHIFT
    for t in present:
        anchor = track.anchors[t]
        track.anchors[t] = (anchor[0] + dr, anchor[1] + dc)
        track.masks[t] = tuple((r + dr, c + dc) for r, c in track.masks[t])
    return result


def _duplicate_track(result: Any, args: Tuple[Any, ...],
                     kwargs: Dict[str, Any]) -> Any:
    track, _ = _first_present_track(result)
    result.tracks = list(result.tracks) + [copy.deepcopy(track)]
    return result


def _perturb_rel_cells(result: Any, args: Tuple[Any, ...],
                       kwargs: Dict[str, Any]) -> Any:
    track, _ = _first_present_track(result)
    if not track.rel_cells:
        raise mut.inert("track %s has no relative cells" % track.track_id)
    track.rel_cells = tuple((r + 1, c) for r, c in track.rel_cells)
    return result


def _forget_anchor(result: Any, args: Tuple[Any, ...],
                   kwargs: Dict[str, Any]) -> Any:
    # A frame whose predecessor is also present, so the transition into it reads
    # as a vanish the script never narrates -- otherwise the anchor could be
    # dropped at a frame the track had just appeared in, where nothing is
    # expected of the narration either way.
    for track in result.tracks:
        present = set(_present_frames(track))
        for t in sorted(present):
            if t - 1 in present:
                track.anchors[t] = None
                return result
    raise mut.inert("no track is present on two consecutive frames")


def _flip_move_delta(result: Any, args: Tuple[Any, ...],
                     kwargs: Dict[str, Any]) -> Any:
    for event in result.events:
        if event.type == "move":
            params = dict(event.params)
            params["dy"] = int(params["dy"]) + 1
            event.params = params
            return result
    raise mut.inert("this world's script contains no move event")


def _drop_narration(result: Any, args: Tuple[Any, ...],
                    kwargs: Dict[str, Any]) -> Any:
    for i, event in enumerate(result.events):
        if event.type in NARRATED:
            del result.events[i]
            return result
    raise mut.inert("script narrates no move/appear/vanish to withhold")


def _skip_transition_header(result: Any, args: Tuple[Any, ...],
                            kwargs: Dict[str, Any]) -> Any:
    if result.n_frames < 2:
        raise mut.inert("single-frame trajectory pays no transition header")
    result.script_bits -= HEADER_BITS
    return result


def _spurious_free_move(result: Any, args: Tuple[Any, ...],
                        kwargs: Dict[str, Any]) -> Any:
    if not result.events:
        raise mut.inert("no event to clone into a spurious one")
    by = _events_by_track_t(result)
    for track in result.tracks:
        for t in range(len(track.anchors) - 1):
            here, there = track.anchors[t], track.anchors[t + 1]
            if here is None or there is None or tuple(here) != tuple(there):
                continue
            if by.get((track.track_id, t)):
                continue
            event = copy.deepcopy(result.events[0])
            event.t = t
            event.type = "move"
            event.track = track.track_id
            event.params = {"dy": 0, "dx": 0}
            event.bits = 0
            result.events.append(event)
            return result
    raise mut.inert("every still transition already carries an event")


def _misprice_event(result: Any, args: Tuple[Any, ...],
                    kwargs: Dict[str, Any]) -> Any:
    for event in result.events:
        if event.bits > 1:
            cut = event.bits // 2
            event.bits -= cut
            result.script_bits -= cut
            return result
    raise mut.inert("no event priced above one bit")


def _flip_track_color(result: Any, args: Tuple[Any, ...],
                      kwargs: Dict[str, Any]) -> Any:
    for track in result.tracks:
        if track.color is not None:
            track.color = (int(track.color) % 9) + 1   # another palette colour
            return result
    raise mut.inert("no track has a uniform colour to misreport")


def _inflate_baseline_bits(result: Any, args: Tuple[Any, ...],
                           kwargs: Dict[str, Any]) -> Any:
    if result.baseline_bits <= 0:
        raise mut.inert("baseline is zero; doubling it changes nothing")
    result.baseline_bits *= 2
    return result


mut.register(
    mut.Mutant(
        id="mdl-shift-track-rigidly",
        engine=ENGINE, seam=SEAM, kind=mut.UNSOUND,
        claim="a track's mask at frame t is the cells of the connected "
              "component actually found in that frame -- "
              "segmenter.py:segment_trajectory sets `track.masks[t+1] = "
              "cur[j].cells` where `cur` is `connected_components(frame)`, whose "
              "`seen` grid makes the components a partition of the "
              "non-background cells.",
        description="move one track's anchors *and* masks by (0,+1) on every "
                    "frame it is present. rel_cells is left alone, so the shape "
                    "is still rigid and the frame-to-frame displacements are "
                    "unchanged: the object is simply reported one column from "
                    "where it is.",
        corrupt=_shift_track_rigidly,
        expect_kill=("masks_partition_the_foreground",),
    ),
    mut.Mutant(
        id="mdl-duplicate-track",
        engine=ENGINE, seam=SEAM, kind=mut.INCONSISTENT,
        claim="the tracks' masks are pairwise disjoint -- components come from "
              "one `seen` grid (segmenter.py:connected_components) and each "
              "surviving component is claimed by exactly one track through the "
              "bipartite assignment, so no cell is under two objects.",
        description="list one track twice (the shape a bug in the `order` list "
                    "of segment_trajectory would take, since tracks are read "
                    "back as `[tracks[tid] for tid in order]`). track_id is kept, "
                    "so the narration still matches and only disjointness "
                    "breaks.",
        corrupt=_duplicate_track,
        expect_kill=("masks_partition_the_foreground",),
    ),
    mut.Mutant(
        id="mdl-perturb-rel-cells",
        engine=ENGINE, seam=SEAM, kind=mut.INCONSISTENT,
        claim="`Track.rel_cells` is the object's translation-invariant shape -- "
              "segment_trajectory sets `rel_cells=comp.shape_key[0]`, documented "
              "at Component.shape_key as 'Translation-invariant identity: "
              "relative cells plus their colours', so mask == rel_cells at "
              "anchor is the engine's own identity.",
        description="shift rel_cells by (+1,0), leaving anchors and masks "
                    "untouched: the declared shape no longer reconstructs the "
                    "mask, which is what a manual compiled from `to_payload`'s "
                    "`cells` field would replay.",
        corrupt=_perturb_rel_cells,
        expect_kill=("masks_follow_anchors",),
    ),
    mut.Mutant(
        id="mdl-forget-anchor",
        engine=ENGINE, seam=SEAM, kind=mut.INCONSISTENT,
        claim="anchors[t] and masks[t] are set together and mean the same "
              "presence -- segment_trajectory writes the pair on every branch "
              "(`track.anchors[t+1] = cur[j].anchor; track.masks[t+1] = "
              "cur[j].cells`), and `__init__.py:candidates` reports coverage "
              "from masks while `to_payload` publishes anchors.",
        description="drop one anchor while keeping its mask, at a frame whose "
                    "predecessor is also present: the object's pixels are still "
                    "reported and its position is not, and the transition into "
                    "that frame now reads as an unnarrated vanish.",
        corrupt=_forget_anchor,
        expect_kill=("masks_follow_anchors", "events_agree_with_tracks"),
    ),
    mut.Mutant(
        id="mdl-flip-move-delta",
        engine=ENGINE, seam=SEAM, kind=mut.UNSOUND,
        claim="a move event's (dy,dx) is the displacement the anchor actually "
              "took -- segmenter.py:_match_cost computes `dy, dx = br - ar, "
              "bc - ac` from the two components' anchors and hands exactly those "
              "params to the Event.",
        description="add 1 to the first move event's dy. The script now narrates "
                    "a displacement the object did not make, while its price and "
                    "the masks stay as they were.",
        corrupt=_flip_move_delta,
        expect_kill=("events_agree_with_tracks",),
    ),
    mut.Mutant(
        id="mdl-drop-narration",
        engine=ENGINE, seam=SEAM, kind=mut.INCOMPLETE,
        claim="every anchor change is narrated, and the script's price is the "
              "sum of what it narrates -- segment_trajectory appends an Event "
              "and adds its bits to `transition_bits` in the same breath, on all "
              "three branches (pairs / gone / born).",
        description="delete the first move/appear/vanish event. A state change "
                    "the caller is never told about, and -- because the bits went "
                    "with it -- a script that no longer adds up to its own "
                    "declared cost.",
        corrupt=_drop_narration,
        expect_kill=("events_agree_with_tracks", "script_bits_identity"),
    ),
    mut.Mutant(
        id="mdl-skip-transition-header",
        engine=ENGINE, seam=SEAM, kind=mut.DEGRADED,
        claim="every transition pays `cost.b_header` in the script exactly as it "
              "does in the baseline -- costs.py: 'the two models share their "
              "per-transition header'; segment_trajectory opens each transition "
              "with `transition_bits = cost.b_header`.",
        description="report script_bits 8 lower than the engine computed it: one "
                    "transition header never charged. The narration is untouched, "
                    "so only the accounting identity can see it -- and the "
                    "understated script is the number D-005's acceptance ratio "
                    "is read off.",
        corrupt=_skip_transition_header,
        expect_kill=("script_bits_identity",),
    ),
    mut.Mutant(
        id="mdl-spurious-free-move",
        engine=ENGINE, seam=SEAM, kind=mut.UNSOUND,
        claim="the engine narrates a move only when something moved, and never "
              "for free -- _match_cost returns `kind=None` when `a.cells == "
              "b.cells and a.colors == b.colors`, and costs.py:move_bits is "
              "b_evtype + b_objid + two offsets, so it is never below 6 bits.",
        description="PREDICTED SURVIVOR: add a `move` event with (dy,dx)=(0,0) "
                    "and bits=0 to a track at a transition where it did not "
                    "move. events_agree_with_tracks checks each move event "
                    "against the anchors, but a zero displacement is trivially "
                    "consistent with a still anchor, and zero bits leave the "
                    "identity intact -- so the script gains a sentence stating "
                    "something that did not happen. Registered against "
                    "events_agree_with_tracks because its docstring claims both "
                    "directions ('an event describing a motion that did not "
                    "happen is a false statement in the script').",
        corrupt=_spurious_free_move,
        expect_kill=("events_agree_with_tracks",),
    ),
    mut.Mutant(
        id="mdl-misprice-event",
        engine=ENGINE, seam=SEAM, kind=mut.DEGRADED,
        claim="an event's `bits` is its length under the published cost model -- "
              "costs.py move_bits / recolor_bits / vanish_bits / appear_bits, "
              "'One scheme, published (see this engine's README.md), simple "
              "enough to re-derive by hand'; segment_trajectory stores that "
              "number on the Event and adds the same number to script_bits.",
        description="PREDICTED SURVIVOR: halve one event's bits and take the "
                    "same amount off script_bits. The accounting identity is "
                    "closed under any change that moves both sides, so the "
                    "engine can misprice an event by any amount as long as it "
                    "misprices the total to match. Registered against "
                    "script_bits_identity because it is the only invariant that "
                    "reads bits at all.",
        corrupt=_misprice_event,
        expect_kill=("script_bits_identity",),
    ),
    mut.Mutant(
        id="mdl-flip-track-color",
        engine=ENGINE, seam=SEAM, kind=mut.UNSOUND,
        claim="`Track.color` is the object's uniform colour -- "
              "segment_trajectory sets `color=comp.uniform_color`, defined at "
              "Component.uniform_color as `colors[0] if len(set(colors)) == 1 "
              "else None`, and `__init__.py:to_payload` publishes it as the "
              "object_hypothesis payload's `color`.",
        description="PREDICTED SURVIVOR: report a different palette colour for "
                    "the first uniformly coloured track. The masks, the "
                    "narration and the bits are all untouched, and no invariant "
                    "reads `color` -- the manual would inherit a false fact of "
                    "exactly the right shape. Registered against "
                    "masks_partition_the_foreground as the only invariant that "
                    "looks at a track's per-frame content at all.",
        corrupt=_flip_track_color,
        expect_kill=("masks_partition_the_foreground",),
    ),
    mut.Mutant(
        id="mdl-inflate-baseline-bits",
        engine=ENGINE, seam=SEAM, kind=mut.UNSOUND,
        claim="`baseline_bits` is the pixel model's price of the same "
              "trajectory -- segment_trajectory accumulates "
              "`cost.baseline_transition_bits(len(changed_pixels(frames[t], "
              "frames[t+1])))`, and costs.py names the failure it guards: "
              "'Rigging the comparison by choosing units is the obvious failure "
              "mode here'.",
        description="PREDICTED SURVIVOR: double baseline_bits, so gain_bits and "
                    "compression_ratio -- the numbers D-005's acceptance "
                    "threshold is stated in -- overstate the engine's advantage "
                    "by a factor of two. props declines to assert that the "
                    "script *beats* the baseline, which is right; this is the "
                    "different claim that the baseline is the price of these "
                    "frames. Registered against script_bits_identity as the only "
                    "invariant that reads a bit count.",
        corrupt=_inflate_baseline_bits,
        expect_kill=("script_bits_identity",),
    ),
)
