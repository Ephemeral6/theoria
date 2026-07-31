"""E18: recompute the `mdl_segmenter` numbers the E11 cross-check published as prose.

The headline is **D1**, the object-id field that is too narrow to name the objects
it indexes:

    costs.py:50   b_objid    = bits_for(max(2, max_objects))
    segmenter.py  max_objects = max(len(comps) for comps in per_frame)

`max_objects` is the most components in any *single frame*, but tracks accumulate
across the whole trajectory through appear/vanish churn, and every event pays
exactly one `b_objid` field to say which track it is about.  So in 126 of 300
worlds the script is priced as if it could name its objects and it cannot.

E11 (`engine-rig/runs/20260729T000000Z-E11-engine-crosscheck-deep/partials/
mdl_segmenter-via-reconstruction.md`) reported this and thirteen sibling figures
as prose only -- no script, no data, nobody could recompute them.  This module is
the executable form.  It shares one corpus and one loop with all of them, because
they were all read off the same sweep.

Everything is recomputed from the world generator and the engine's published
payload.  The cost table is **transcribed here, not imported from `costs.py`**,
so the bit checks stay independent of the code they are checking -- the same
choice E11 made, and the same limitation: independent of the code, not of the
README the code and this module both descend from (see caveats).

Run:

    cd engine-rig
    python -m tools.survey_numbers.mdl_objid
    python -m tools.survey_numbers.mdl_objid \
        --jsonl runs/20260730T120000Z-E18/raw/mdl_objid.jsonl

Takes about 3 s: 300 worlds for the corpus and 2x800 for the section-7 operator
A/B.  The committed counts are `runs/20260730T120000Z-E18/counts/mdl.objid.json`,
written by `tools.survey_numbers.run_all`.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from tools.survey_numbers import _common

_common.add_repo_root()

from engines import mdl_segmenter as M                      # noqa: E402
from fuzzlab.prng import derive                             # noqa: E402
from fuzzlab.worlds import gridworld                        # noqa: E402

# ------------------------------------------------------------------ the corpus
# Stated verbatim in the partial, section 3: "300 gridworld worlds, seeds
# derive(0xE11C5EC, "gridworld", i), i in [0,300); grids 5x5 to 12x12 [...].
# The operator A/B in section 7 was additionally swept over 800 worlds."
CAMPAIGN_SEED = 0xE11C5EC
FAMILY = "gridworld"
N_WORLDS = 300
N_OPERATOR_WORLDS = 800

BACKGROUND = 0
N_COLORS = 10          # costs.py:21, the ARC palette
UNKNOWN = -1           # reconstruction sentinel for a cell whose colour was lost

INPUTS = [
    "engine-rig/common/rng.py",
    "engine-rig/engines/mdl_segmenter/README.md",
    "engine-rig/engines/mdl_segmenter/__init__.py",
    "engine-rig/engines/mdl_segmenter/costs.py",
    "engine-rig/engines/mdl_segmenter/segmenter.py",
    "engine-rig/runs/20260729T000000Z-E11-engine-crosscheck-deep/partials/"
    "mdl_segmenter-via-reconstruction.md",
    "fuzzlab/prng.py",
    "fuzzlab/worlds/common.py",
    "fuzzlab/worlds/gridworld.py",
]


# --------------------------------------------------- the cost table, transcribed
# From engines/mdl_segmenter/README.md's "The cost model" table.  Two readings had
# to be resolved against costs.py; both are recorded in the caveats.

def bits_for(n: int) -> int:
    """`ceil(log2 n)` as the engine means it (`costs.py:24-26`)."""
    return max(1, int(math.ceil(math.log2(max(2, n)))))


def gamma_bits(x: int) -> int:
    return 2 * int(math.floor(math.log2(x + 1))) + 1


def offset_bits(d: int) -> int:
    return 1 + gamma_bits(abs(d))


class Cost:
    """The published scheme, re-derived rather than imported."""

    def __init__(self, height: int, width: int, max_objects: int):
        self.b_dim = bits_for(max(height, width))
        self.b_pos = bits_for(height) + bits_for(width)
        self.b_color = bits_for(N_COLORS)
        self.b_evtype = 2
        self.b_objid = bits_for(max(2, max_objects))
        self.b_header = 8

    def declaration_bits(self, n_cells: int, box_h: int, box_w: int) -> int:
        return 2 * self.b_dim + self.b_pos + box_h * box_w + n_cells * self.b_color

    def move_bits(self, dy: int, dx: int) -> int:
        return self.b_evtype + self.b_objid + offset_bits(dy) + offset_bits(dx)

    def recolor_bits(self, n_changed: int) -> int:
        return self.b_evtype + self.b_objid + n_changed * self.b_color

    def vanish_bits(self) -> int:
        return self.b_evtype + self.b_objid

    def appear_bits(self, n_cells: int, box_h: int, box_w: int) -> int:
        return self.b_evtype + self.b_objid + self.declaration_bits(n_cells, box_h, box_w)


def own_components(frame: Sequence[Sequence[int]]) -> int:
    """Count 4-connected non-background blobs, without asking the engine.

    `b_objid` is derived from this count, so taking the engine's own component
    finder for it would make D1 self-referential.  Iterative flood fill, cells
    visited in row-major order: the count does not depend on the order anyway.
    """
    height = len(frame)
    width = len(frame[0]) if height else 0
    seen = [[False] * width for _ in range(height)]
    n = 0
    for r0 in range(height):
        for c0 in range(width):
            if seen[r0][c0] or frame[r0][c0] == BACKGROUND:
                continue
            n += 1
            stack = [(r0, c0)]
            seen[r0][c0] = True
            while stack:
                r, c = stack.pop()
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < height and 0 <= nc < width):
                        continue
                    if seen[nr][nc] or frame[nr][nc] == BACKGROUND:
                        continue
                    seen[nr][nc] = True
                    stack.append((nr, nc))
    return n


# ------------------------------------------------------------------- one world

def _survey_world(index: int) -> Dict[str, Any]:
    """Everything the fourteen figures need from one world, in one pass."""
    seed = derive(CAMPAIGN_SEED, FAMILY, index)
    world = gridworld.generate(seed)
    frames = world.frames
    height, width = world.spec.height, world.spec.width

    seg = M.segment_trajectory(frames, background=BACKGROUND)
    payloads = [M.to_payload(seg, track) for track in seg.tracks]
    by_id = {t.track_id: t for t in seg.tracks}

    max_objects = max(own_components(f) for f in frames)
    cost = Cost(height, width, max_objects)

    n_tracks = len(seg.tracks)
    n_events = len(seg.events)

    # -- D1: the id field against the track list ------------------------------
    # "at ceil(log2 n_tracks) per event".  Every event type pays exactly one
    # b_objid (costs.py:64-74), so the shortfall is per-event and uniform.
    honest_objid = int(math.ceil(math.log2(n_tracks))) if n_tracks > 0 else 0
    shortfall = max(0, honest_objid - cost.b_objid)
    undercharge = n_events * shortfall
    honest_script = seg.script_bits + undercharge

    # -- reconstruction from the published payload only -----------------------
    # Section 3's rule: all-background canvas, paint each track's `cells`
    # translated to `anchors[t]` in `color`, UNKNOWN where `color` is null.
    # Never `Track.masks` -- that is the engine's own per-frame answer and is
    # not published.
    cells_total = 0
    cells_wrong = 0
    cells_unrecoverable = 0
    frames_exact = 0
    truth = world.truth_masks()
    gt_frames_match = 0

    for t, original in enumerate(frames):
        canvas = [[BACKGROUND] * width for _ in range(height)]
        for payload in payloads:
            anchor = payload["anchors"][t]
            if anchor is None:
                continue
            color = payload["color"]
            paint = UNKNOWN if color is None else color
            for dr, dc in payload["cells"]:
                canvas[anchor[0] + dr][anchor[1] + dc] = paint
        exact = True
        for r in range(height):
            row_c, row_o = canvas[r], original[r]
            for c in range(width):
                cells_total += 1
                got = row_c[c]
                if got == UNKNOWN:
                    cells_unrecoverable += 1
                    exact = False
                elif got != row_o[c]:
                    cells_wrong += 1
                    exact = False
        frames_exact += exact

        engine_masks = {
            tuple(sorted((payload["anchors"][t][0] + dr, payload["anchors"][t][1] + dc)
                         for dr, dc in payload["cells"]))
            for payload in payloads
            if payload["anchors"][t] is not None
        }
        truth_masks = {tuple(sorted(mask)) for mask in truth[t]}
        gt_frames_match += engine_masks == truth_masks

    # -- every event re-priced from its own parameters ------------------------
    events_mispriced = 0
    for event in seg.events:
        if event.type == "move":
            expect = cost.move_bits(int(event.params["dy"]), int(event.params["dx"]))
        elif event.type == "vanish":
            expect = cost.vanish_bits()
        elif event.type == "appear":
            track = by_id[event.track]
            expect = cost.appear_bits(len(track.rel_cells), track.shape[0], track.shape[1])
        elif event.type == "recolor":
            expect = cost.recolor_bits(len(event.params["cells"]))
        else:                                                # pragma: no cover
            raise AssertionError("unknown event type %r" % (event.type,))
        events_mispriced += expect != event.bits

    n_recolor = sum(1 for e in seg.events if e.type == "recolor")

    return {
        "i": index,
        "seed": seed,
        "n_frames": len(frames),
        "n_tracks": n_tracks,
        "b_objid": cost.b_objid,
        "objid_overflow": n_tracks > 2 ** cost.b_objid,
        "script_bits": seg.script_bits,
        "baseline_bits": seg.baseline_bits,
        "beats_baseline": seg.script_bits < seg.baseline_bits,
        "beats_baseline_honest": honest_script < seg.baseline_bits,
        # not part of the jsonl contract, dropped before it is written
        "_extra": {
            "height": height,
            "width": width,
            "max_objects": max_objects,
            "engine_max_objects": max(len(M.connected_components(f)) for f in frames),
            "n_events": n_events,
            "n_objects": world.n_objects(),
            "undercharge": undercharge,
            "cells_total": cells_total,
            "cells_wrong": cells_wrong,
            "cells_unrecoverable": cells_unrecoverable,
            "frames_exact": frames_exact,
            "world_exact": frames_exact == len(frames),
            "gt_frames_match": gt_frames_match,
            "gt_world_match": gt_frames_match == len(frames),
            "inflated": n_tracks > world.n_objects(),
            "events_mispriced": events_mispriced,
            "n_recolor": n_recolor,
        },
    }


def _operator_pair(index: int) -> Tuple[bool, bool]:
    """(track counts differ, `segment_operator` strings differ) for one world."""
    world = gridworld.generate(derive(CAMPAIGN_SEED, FAMILY, index))
    agnostic = M.segment_trajectory(world.frames, background=BACKGROUND,
                                    split_by_color=False)
    by_color = M.segment_trajectory(world.frames, background=BACKGROUND,
                                    split_by_color=True)
    label_a = (M.to_payload(agnostic, agnostic.tracks[0])["segment_operator"]
               if agnostic.tracks else None)
    label_b = (M.to_payload(by_color, by_color.tracks[0])["segment_operator"]
               if by_color.tracks else None)
    return (len(agnostic.tracks) != len(by_color.tracks), label_a != label_b)


# ------------------------------------------------------------------ assembling

def _ratio(numerator: int, denominator: int) -> Dict[str, Any]:
    pct = round(100.0 * numerator / denominator, 4) if denominator else 0.0
    return {"numerator": numerator, "denominator": denominator, "pct": pct}


def _row(recomputed: Any, prose: Any) -> Dict[str, Any]:
    return {"recomputed": recomputed, "e11_prose": prose, "agrees": recomputed == prose}


def compute(jsonl_path: Optional[str | Path] = None) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = [_survey_world(i) for i in range(N_WORLDS)]
    rows.sort(key=lambda r: r["i"])
    extra = [r["_extra"] for r in rows]

    def total(field: str) -> int:
        return sum(int(e[field]) for e in extra)

    n_frames = sum(r["n_frames"] for r in rows)
    n_tracks = sum(r["n_tracks"] for r in rows)
    n_events = total("n_events")
    cells_total = total("cells_total")
    script_total = sum(r["script_bits"] for r in rows)
    undercharge = total("undercharge")

    objid_worlds = sum(1 for r in rows if r["objid_overflow"])
    beats = sum(1 for r in rows if r["beats_baseline"])
    beats_honest = sum(1 for r in rows if r["beats_baseline_honest"])
    flips = sum(1 for r in rows if r["beats_baseline"] and not r["beats_baseline_honest"])

    # Ties broken by the lowest index, so the witness is stable.
    worst = max(rows, key=lambda r: (r["n_tracks"], -r["i"]))
    worst_extra = worst["_extra"]

    operator = [_operator_pair(i) for i in range(N_OPERATOR_WORLDS)]
    operator_differs = sum(1 for differs, _ in operator if differs)
    operator_label_differs = sum(1 for _, label in operator if label)

    value = _ratio(objid_worlds, N_WORLDS)

    counts = {
        # --- the fourteen the ticket names ----------------------------------
        "mdl.objid_worlds": _row(value, _ratio(126, 300)),
        "mdl.worst_tracks": _row(worst["n_tracks"], 40),
        "mdl.objid_undercharge": _row(_ratio(undercharge, script_total),
                                      _ratio(9675, 168843)),
        "mdl.verdict_flips": _row(flips, 10),
        "mdl.worlds": _row(len(rows), 300),
        "mdl.frames": _row(n_frames, 6993),
        "mdl.cells": _row(cells_total, 506302),
        "mdl.cells_wrong": _row(total("cells_wrong"), 0),
        "mdl.unrecoverable": _row(_ratio(total("cells_unrecoverable"), cells_total),
                                  _ratio(18118, 506302)),
        "mdl.events_repriced": _row(n_events, 6939),
        "mdl.groundtruth_worlds": _row(_ratio(sum(1 for e in extra if e["gt_world_match"]),
                                              N_WORLDS),
                                       _ratio(173, 300)),
        "mdl.inflated_worlds": _row(sum(1 for e in extra if e["inflated"]), 127),
        "mdl.operator_differs": _row(_ratio(operator_differs, N_OPERATOR_WORLDS),
                                     _ratio(479, 800)),
        "mdl.operator_same": _row(_ratio(operator_label_differs, N_OPERATOR_WORLDS),
                                  _ratio(0, 800)),
        # --- supporting figures from the same loop, also prose-only in E11 ---
        "mdl.events_mispriced": _row(total("events_mispriced"), 0),
        "mdl.tracks": _row(n_tracks, 1807),
        "mdl.script_bits_total": _row(script_total, 168843),
        "mdl.beats_baseline": _row(beats, 242),
        "mdl.beats_baseline_honest": _row(beats_honest, 232),
        "mdl.worlds_replayed_exact": _row(_ratio(sum(1 for e in extra if e["world_exact"]),
                                                 N_WORLDS),
                                          _ratio(121, 300)),
        "mdl.frames_replayed_exact": _row(_ratio(total("frames_exact"), n_frames),
                                          _ratio(3275, 6993)),
        "mdl.groundtruth_frames": _row(_ratio(total("gt_frames_match"), n_frames),
                                       _ratio(5979, 6993)),
    }

    disagreements = sorted(k for k, v in counts.items() if not v["agrees"])

    caveats = [
        "Prose percentages are re-rendered from the prose's own fraction at 4 dp, so "
        "`agrees` turns on the fraction and never on E11's rounding (E11 wrote "
        "'40.3 %', this writes 40.3333).",
        "AMBIGUITY RESOLVED -- `b_objid`. README.md's cost table says "
        "`ceil(log2 max_objects)`; `costs.py:24-26,50` computes "
        "`max(1, ceil(log2(max(2, max_objects))))`. These differ for "
        "`max_objects <= 2`, which is the common case in `gridworld`. Took the "
        "code reading: it is what the engine actually charges, and it is the only "
        "reading under which E11's 'every individual event's bits: 0 mismatches' "
        "can hold.",
        "AMBIGUITY RESOLVED -- honest id width. Prose says 'at ceil(log2 n_tracks) "
        "per event'. Took it literally and clamped the per-event shortfall at zero "
        "(`max(0, honest - b_objid)`), since a field that is already wide enough is "
        "not an under-charge. Checked against the three neighbouring readings: "
        "`bits_for(n_tracks)` clamped and unclamped both also give 9675 bits; only "
        "unclamped `ceil(log2 n_tracks)` differs, at 7462 (4.42 %), and it is the "
        "reading the word 'under-charge' rules out. The choice is not load-bearing "
        "for the published figure.",
        "AMBIGUITY RESOLVED -- the 800-world operator sweep. Section 7 says only "
        "'additionally swept over 800 worlds' without restating the seeds. Took the "
        "same stream extended, `derive(0xE11C5EC, 'gridworld', i)` for i in [0,800). "
        "Confirmed by witness: section 7's example seed 12147563315917480426 is in "
        "this sweep and gives 4 tracks vs 10 with script_bits 313 vs 421, exactly as "
        "published.",
        "AMBIGUITY RESOLVED -- 'matching ground truth in every frame'. Compared the "
        "engine's per-frame mask *set* (from `anchors[t]` + `cells`, payload only) "
        "against `GridWorld.truth_masks()[t]` as sets of sorted cell tuples. Equality "
        "of sets, not of order or of track identity across frames.",
        "The cost table is transcribed from README.md, not imported from `costs.py`, "
        "so the bit checks are code-independent but not doc-independent -- an error "
        "shared by README and `costs.py` passes. E11 recorded the same limitation "
        "(section 9) and this module inherits it rather than closing it.",
        "`b_objid` is derived from `own_components()`, a local flood fill, not from "
        "the engine's `connected_components`: D1 is a claim about the engine's own "
        "component count, so importing it would be circular. The two are compared "
        "anyway and the agreement is reported below rather than asserted.",
        "GAP -- `recolor` is unexercised: `gridworld` emits %d recolor events in %d, "
        "so the re-pricing and reconstruction paths for it are written and never "
        "executed here, exactly as in E11 (section 9). Nothing in this module "
        "measures them." % (total("n_recolor"), n_events),
        "own_components() agrees with engines.mdl_segmenter.connected_components on "
        "max-objects-per-frame in %d/%d worlds."
        % (sum(1 for e in extra if e["max_objects"] == e["engine_max_objects"]), N_WORLDS),
        "Commit 2a1c30d (C11) added `SegmentationError` and the IMPOSSIBLE-pair guard "
        "to `segmenter.py` after E11's base commit ed592a6, so these figures are "
        "recomputed on code E11 never ran. It moves nothing: the guard adds no "
        "arithmetic and raises rather than returns, and it fired zero times across "
        "the %d segmentations here (%d corpus + %d operator sweep) -- any firing "
        "would have aborted this run."
        % (N_WORLDS + 2 * N_OPERATOR_WORLDS, N_WORLDS, 2 * N_OPERATOR_WORLDS),
        "Worst-case witness (D1 and the ground-truth inflation are the same world): "
        "seed %d, %d tracks addressed by a %d-bit id (capacity %d), for %d real "
        "objects." % (worst["seed"], worst["n_tracks"], worst["b_objid"],
                      2 ** worst["b_objid"], worst_extra["n_objects"]),
        ("Every figure agrees with E11." if not disagreements
         else "Disagrees with E11 on: " + ", ".join(disagreements)),
    ]

    if jsonl_path is not None:
        _write_jsonl(Path(jsonl_path), rows)

    return _common.result(
        key="mdl.objid",
        question=(
            "In how many of the 300 gridworld worlds does mdl_segmenter's script "
            "carry more tracks than its object-id field can address "
            "(n_tracks > 2**b_objid)?"
        ),
        value=value,
        e11_prose=_ratio(126, 300),
        counts=counts,
        inputs=_common.input_digests(INPUTS),
        method=(
            "Corpus: %d gridworld worlds, seeds derive(0x%X, %r, i) for i in [0,%d); "
            "the section-7 operator A/B additionally over i in [0,%d). For each world: "
            "segment with engines.mdl_segmenter.segment_trajectory (background=0, "
            "split_by_color=False); recompute max_objects with a local flood fill and "
            "b_objid = max(1, ceil(log2(max(2, max_objects)))); compare against "
            "len(seg.tracks). Reconstruct every frame from the published payload alone "
            "(anchors + cells + color, never Track.masks) onto an all-background canvas "
            "of the world's dimensions, painting UNKNOWN where color is null, and diff "
            "against the original. Re-price every event from its own parameters using a "
            "cost table transcribed from the engine README. Compare per-frame mask sets "
            "against GridWorld.truth_masks(). No network, no API, no RNG beyond the "
            "seed stream."
            % (N_WORLDS, CAMPAIGN_SEED, FAMILY, N_WORLDS, N_OPERATOR_WORLDS)
        ),
        caveats=caveats,
    )


JSONL_FIELDS = ("i", "seed", "n_frames", "n_tracks", "b_objid", "objid_overflow",
                "script_bits", "baseline_bits", "beats_baseline",
                "beats_baseline_honest")


def _write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    """One raw row per world, sorted by index, LF-terminated, keys sorted."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps({k: row[k] for k in JSONL_FIELDS},
                                    sort_keys=True) + "\n")


def _main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--jsonl", metavar="PATH", default=None,
                        help="write one raw row per world to PATH")
    args = parser.parse_args()
    _common.main(lambda: compute(jsonl_path=args.jsonl))


if __name__ == "__main__":
    _main()
