"""The segmentation operator space, and the MDL adjudication between operators.

Theoria 1.8 does not say "objects are connected components"; it says objects come
from a **segmentation operator hypothesis space** (connected components, common
fate clustering, template matching, ...) that the model chooses from per world,
with the choice written into the manual and disciplined by rendering consistency
and the evidence rules.  `engine-rig/mdl_segmenter` implements one operator from
that space.  A0 needs a second one, for a reason that shows up the moment two
objects touch:

  the colour-agnostic 4-connected operator merges the Cart into the Button
  whenever the Cart is standing next to it.  On the A0 trajectory that produced
  **90 tracks, 88 vanishes and 87 appears** for a world with three objects.

The repair is not to patch the engine but to add the operator the world needs --
4-connected blobs of *uniform colour* -- and to let the engine's own objective
choose: run the segmenter under each operator and keep the shorter script.  That
is "concept = compression" doing the adjudicating, which is the criterion the
framework already commits to, rather than a preference smuggled in by hand.

Mechanically, the proposal step is the only thing swapped.  The cost model, the
bipartite matcher and the narration all stay upstream and unmodified: this module
rebinds `mdl_segmenter.segmenter.connected_components` for the duration of one
call and restores it afterwards.  No file in `engine-rig` is touched.
"""

import contextlib
import inspect
from typing import Callable, Dict, List, Sequence, Tuple

from engines.mdl_segmenter import segmenter as _seg
from engines.mdl_segmenter.costs import CostModel
from engines.mdl_segmenter.segmenter import Component, Segmentation

from pipeline.identity_swap import repair_identity_swaps
from pipeline.reidentify import reidentify

Cell = Tuple[int, int]
Frame = Sequence[Sequence[int]]

_UPSTREAM = _seg.connected_components

# `engine-rig` grew a `split_by_color` switch on `segment_trajectory` partway
# through this sprint — the same gap, closed upstream.  When it is there we use
# it and the rebinding below never happens; the local operator stays as the
# fallback so this directory still runs against the version of `engine-rig` that
# was tagged at `engine-rig-m8-integration`.
_NATIVE_SPLIT = "split_by_color" in inspect.signature(_seg.segment_trajectory).parameters


def components_connected(frame: Frame, background: int = 0) -> List[Component]:
    """The upstream operator: 4-connected, colour-agnostic."""
    return _UPSTREAM(frame, background)


def components_uniform_color(frame: Frame, background: int = 0) -> List[Component]:
    """4-connected blobs of a single colour.

    Splitting by colour is the failure mode upstream warns about on
    multi-coloured objects, and the honest trade is stated in the operator
    account: this operator cannot represent an object that carries two colours at
    once.  A0's objects are monochrome and they touch, so here it is the right
    half of the trade -- and which half is right is decided by script length, not
    by assertion.
    """
    height = len(frame)
    width = len(frame[0]) if height else 0
    seen = [[False] * width for _ in range(height)]
    out: List[Component] = []
    for r0 in range(height):
        for c0 in range(width):
            if seen[r0][c0] or frame[r0][c0] == background:
                continue
            color = frame[r0][c0]
            stack = [(r0, c0)]
            seen[r0][c0] = True
            blob: List[Cell] = []
            while stack:
                r, c = stack.pop()
                blob.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and not seen[nr][nc]
                        and frame[nr][nc] == color
                    ):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            cells = tuple(sorted(blob))
            out.append(Component(cells=cells,
                                 colors=tuple(frame[r][c] for r, c in cells)))
    return sorted(out, key=lambda comp: comp.cells)


OPERATORS: Dict[str, Callable] = {
    "connected_components(4)": components_connected,
    "connected_components(4)+uniform_color": components_uniform_color,
}


@contextlib.contextmanager
def _operator(fn: Callable):
    original = _seg.connected_components
    _seg.connected_components = fn
    try:
        yield
    finally:
        _seg.connected_components = original


def segment_with(name: str, frames: Sequence[Frame],
                 background: int = 0) -> Segmentation:
    uniform = name.endswith("uniform_color")
    if _NATIVE_SPLIT:
        return _seg.segment_trajectory(frames, background=background,
                                       split_by_color=uniform)
    if not uniform:
        return _seg.segment_trajectory(frames, background=background)
    with _operator(OPERATORS[name]):
        return _seg.segment_trajectory(frames, background=background)


def choose_operator(frames: Sequence[Frame], background: int = 0):
    """Run every operator, then repair identity, then re-identify; keep the
    shortest script.

    Three adjudications.  Two of them are by script length and are reported as
    such; the third is not, and says so:

    1. which component proposer (colour-agnostic vs uniform-colour) — by bits;
    2. whether the matcher handed a mover's identity to the object it stepped
       onto — **not** by bits.  That reading is 2 bits *cheaper* per swap under
       the published cost model, which is exactly why the matcher chooses it and
       exactly why script length cannot be the thing that overrules it.  See
       `pipeline.identity_swap`; the price is in the report;
    3. whether merging same-template, disjoint-lifetime tracks pays — an object
       that vanishes and comes back is otherwise a fresh track every time, which
       is how A0′'s single Door became five.

    The order matters: a swap repair turns a `recolor` into a `vanish`, which is
    what gives `reidentify` a disjoint lifetime to work with in the first place.

    Returns `(name, segmentation, report)`.  Ties break on the operator name so
    the choice is deterministic.
    """
    height = len(frames[0])
    width = len(frames[0][0])

    scored = []
    reports = {}
    swap_reports = {}
    for name in sorted(OPERATORS):
        seg = segment_with(name, frames, background=background)
        cost = CostModel(height, width, max_objects=max(len(seg.tracks), 1))
        repaired, swap_report = repair_identity_swaps(seg, cost)
        if swap_report.applied:
            seg = repaired
        swap_reports[name] = swap_report
        merged, merge_report = reidentify(seg, cost)
        if merge_report.applied:
            seg = merged
        reports[name] = merge_report
        scored.append((seg.script_bits, name, seg))
    scored.sort(key=lambda row: (row[0], row[1]))
    best_name = scored[0][1]
    best_seg = scored[0][2]
    report = [
        {
            "operator": name,
            "script_bits": seg.script_bits,
            "baseline_bits": seg.baseline_bits,
            "ratio": round(seg.compression_ratio, 4),
            "tracks": len(seg.tracks),
            "events": len(seg.events),
            "reidentification": reports[name].as_json(),
            "identity_repair": swap_reports[name].as_json(),
            "chosen": name == best_name,
        }
        for bits, name, seg in scored
    ]
    return best_name, best_seg, report
