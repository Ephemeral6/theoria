"""Between raw ARC frames and the engines' input shapes.

The engines were validated offline against synthetic fixtures: 12x12 frames,
one mover, a hand-built peg graph. A real ARC game is 64x64, may narrate a
dozen simultaneous changes in one command, and has no state graph at all. This
module is the whole of the distance between those two facts, and it is written
so the distance is *visible*: every narrowing it applies -- a crop, a cap, a
dropped engine -- is recorded in the report it returns, with the number that
motivated it.

`Theoria.md`'s division of labour is the rule this module obeys. It performs
no adjudication: it does not name an object, does not accept a rule, does not
decide what the board is. It computes, it dispatches, and it records what came
back. The single write-point into the two books is `inner/theorize.py`.
"""

import os
import time
import traceback
from typing import Any, Dict, List, Optional, Sequence, Tuple

import _bootstrap                                     # noqa: F401  (sys.path)

from .frames import FrameStore, cells_of_interest

#: A full 64x64 frame is 4096 cells. `mdl_segmenter` does connected components
#: plus a bipartite match per transition; the fixtures it was validated on are
#: 144 cells. Above this many cells the arena crop is used instead of the whole
#: frame, and the report says so.
CROP_ABOVE_CELLS = 1200

#: `zero_space` builds one GF(2) feature per (cell, colour). This bounds the
#: elimination and is a declared narrowing (see `frames.cells_of_interest`).
LAW_CELL_CAP = 240

#: Colour codes are 0..15; the engine wants strings.
def colour_name(v: int) -> str:
    return "c%X" % (v & 0xF)


class EngineReport(dict):
    """A plain dict, so it serialises straight into the run archive."""


def _timed(fn, *args, **kwargs):
    started = time.time()
    try:
        value = fn(*args, **kwargs)
        return value, int((time.time() - started) * 1000), None
    except Exception as exc:                          # noqa: BLE001
        return None, int((time.time() - started) * 1000), {
            "error": "%s: %s" % (type(exc).__name__, exc),
            "traceback": traceback.format_exc(limit=6),
        }


# ---------------------------------------------------------------- geometry
def choose_window(store: FrameStore) -> Dict[str, Any]:
    """Whole frame, or the arena?

    A0 read its world on a 9x9 board where every cell mattered. Here most of a
    64x64 frame may never change, and handing 4096 static cells to a segmenter
    buys nothing but one enormous track. The arena is the bounding box of the
    cells that have ever changed, padded by one so an object's neighbourhood is
    visible.

    This is a *narrowing of evidence* and it is declared: `full_frame` says
    whether it fired, and `covered` says what fraction of the dynamic cells the
    window holds (it is always 1.0 by construction -- recorded anyway, so a
    later change to this function cannot silently drop cells).
    """
    dynamic = store.dynamic_cells()
    shape = store.shape or (0, 0)
    total = shape[0] * shape[1]
    box = store.bounding_box(dynamic, pad=1)
    area = 0 if box is None else (box[2] - box[0] + 1) * (box[3] - box[1] + 1)

    use_crop = bool(box) and total > CROP_ABOVE_CELLS and area < total
    inside = dynamic if box is None else [
        (r, c) for r, c in dynamic if box[0] <= r <= box[2] and box[1] <= c <= box[3]]
    return {
        "full_frame": not use_crop,
        "box": list(box) if (box and use_crop) else None,
        "frame_cells": total,
        "window_cells": area if use_crop else total,
        "dynamic_cells": len(dynamic),
        "covered": (len(inside) / len(dynamic)) if dynamic else 1.0,
        "reason": ("frame is %d cells (> %d), arena is %d"
                   % (total, CROP_ABOVE_CELLS, area)) if use_crop else
                  ("frame is %d cells, no crop needed" % total),
    }


def windowed_grids(store: FrameStore, window: Dict[str, Any]) -> List[List[List[int]]]:
    box = window.get("box")
    grids = store.grids
    if not box:
        return grids
    return [store.crop(g, tuple(box)) for g in grids]


# ---------------------------------------------------------------- engines
def segment(store: FrameStore, window: Dict[str, Any], *,
            out_path: Optional[str] = None) -> EngineReport:
    """`mdl_segmenter`, run twice.

    A0's D-A0-007 accepted the uniform-colour operator over the colour-agnostic
    one *by the framework's own criterion* -- the shorter script -- after the
    colour-agnostic operator merged the Cart into the Button whenever they
    touched. That comparison is not a one-off finding about A0; it is the
    choice every world poses. So both operators are run here and the shorter
    script wins, with both accounts kept.
    """
    from engines import mdl_segmenter                 # noqa: PLC0415

    grids = windowed_grids(store, window)
    background = store.background()
    report = EngineReport(engine="mdl_segmenter", background=background,
                          n_frames=len(grids), window=window, variants=[])
    if len(grids) < 2:
        report["skipped"] = "fewer than two states; nothing to segment"
        return report

    best = None
    for split in (False, True):
        seg, ms, err = _timed(mdl_segmenter.run, grids, background=background,
                              split_by_color=split)
        entry = {"split_by_color": split, "ms": ms}
        if err:
            entry.update(err)
        else:
            entry.update({"tracks": len(seg.tracks), "events": len(seg.events),
                          "script_bits": seg.script_bits,
                          "baseline_bits": seg.baseline_bits,
                          "gain_bits": seg.gain_bits,
                          "compression_ratio": round(seg.compression_ratio, 6)})
            if best is None or seg.script_bits < best[1].script_bits:
                best = (split, seg)
        report["variants"].append(entry)

    if best is None:
        report["error"] = "both segmentation operators failed"
        return report

    split, seg = best
    report["chosen_operator"] = ("connected_components(4)+uniform_color" if split
                                else "connected_components(4)")
    report["chosen_split_by_color"] = split
    report["tracks"] = [
        {"track_id": t.track_id, "color": t.color, "shape": list(t.shape),
         "n_cells": len(t.rel_cells), "first_frame": t.first_frame,
         "frames_present": sum(1 for a in t.anchors if a is not None)}
        for t in seg.tracks]
    report["event_types"] = _histogram(e.type for e in seg.events)

    if out_path:
        rows, _, err = _timed(_append_candidates, mdl_segmenter, "candidates",
                              out_path, seg)
        report["candidates"] = rows if rows is not None else 0
        if err:
            report["candidate_error"] = err
    report["_segmentation"] = seg                     # in-memory only; stripped on save
    return report


def mine(store: FrameStore, seg_report: EngineReport, window: Dict[str, Any], *,
         out_path: Optional[str] = None) -> EngineReport:
    """`cegis_miner`, and the honest handling of its precondition.

    `transitions_from_segmentation` raises `ValueError` unless every transition
    narrates *exactly one* `move` event or none at all. That precondition is
    true of the fixtures and is a real claim about a world: it says the world
    has one mover and that nothing else changes when it moves. A real game may
    simply not be like that, and the right output then is the refusal, recorded
    -- not a quietly reshaped input that makes the engine answer a question it
    was not asked.
    """
    from engines import cegis_miner                   # noqa: PLC0415

    report = EngineReport(engine="cegis_miner")
    seg = seg_report.get("_segmentation")
    if seg is None:
        report["skipped"] = "no segmentation"
        return report

    grids = windowed_grids(store, window)
    actions = store.actions
    report["n_states"] = len(grids)
    report["n_actions"] = sum(1 for a in actions if a)

    per_track = []
    mined = None
    for track in seg.tracks:
        transitions, ms, err = _timed(
            cegis_miner.transitions_from_segmentation, grids, actions, seg,
            track, store.background())
        entry = {"track_id": track.track_id, "ms": ms}
        if err:
            # The precondition failed. Which precondition is the finding.
            entry["refused"] = err["error"]
            per_track.append(entry)
            continue
        entry["transitions"] = len(transitions)
        result, ms2, err2 = _timed(cegis_miner.run, transitions,
                                   out_path=out_path if mined is None else None)
        entry["mine_ms"] = ms2
        if err2:
            entry.update(err2)
        else:
            entry["rules"] = [
                {"name": r.name, "action": r.action,
                 "guard": [a.name for a in r.guard],
                 "effect": _effect_json(r.effect),
                 "coverage": r.coverage,
                 "frontier_size": len(r.frontier),
                 "frontier": [[a.name for a in alt] for alt in r.frontier]}
                for r in result.all_rules]
            entry["guards_mutually_exclusive"] = result.guards_are_mutually_exclusive()
            entry["explains_every_transition"] = result.explains_every_transition()
            if mined is None:
                mined = result
        per_track.append(entry)

    report["tracks"] = per_track
    report["refusals"] = [t["refused"] for t in per_track if "refused" in t]
    report["_result"] = mined
    if mined is None:
        report["verdict"] = (
            "no track satisfies the miner's precondition (exactly one move "
            "event per transition). The world does not narrate as one mover.")
    return report


def laws(store: FrameStore, *, out_path: Optional[str] = None,
         cap: int = LAW_CELL_CAP) -> EngineReport:
    """`zero_space` over the cells that actually move.

    The engine takes states as lists of per-cell colour *strings*; a 64x64
    frame over the colours seen would be tens of thousands of GF(2) features.
    The cells handed over are the ones that have ever changed, most-active
    first, capped -- and both numbers are in the report, because a law found
    over 240 of 900 dynamic cells is a law about those 240 and about nothing
    else.
    """
    from engines import zero_space                    # noqa: PLC0415

    report = EngineReport(engine="zero_space")
    cells = cells_of_interest(store, cap=cap)
    dynamic = store.dynamic_cells()
    report.update({"cells_used": len(cells), "cells_dynamic": len(dynamic),
                   "cap": cap,
                   "narrowed": len(cells) < len(dynamic),
                   "cells": [list(c) for c in cells[:64]]})
    grids = store.grids
    if len(grids) < 2 or not cells:
        report["skipped"] = "fewer than two states, or nothing ever changed"
        return report

    colours = sorted({g[r][c] for g in grids for r, c in cells})
    states = [[colour_name(g[r][c]) for r, c in cells] for g in grids]
    report["colours"] = [colour_name(v) for v in colours]
    report["features"] = len(cells) * len(colours)

    result, ms, err = _timed(zero_space.run, states,
                             [colour_name(v) for v in colours],
                             out_path=out_path)
    report["ms"] = ms
    if err:
        report.update(err)
        return report

    globals_ = result.global_laws()
    # Evidence adequacy, computed rather than left to a reader. A GF(2) null
    # space over m features constrained by only r independent differences has
    # dimension m - r, so with a handful of transitions against hundreds of
    # features almost every vector is a "law": each one is numerically true
    # over the observed states and says nothing about the world. A0 read its
    # laws off 275 transitions. This ratio is what tells the desk which
    # regime it is in, and it is put in front of it rather than inferred.
    n_transitions = max(0, len(grids) - 1)
    adequacy = {
        "transitions": n_transitions,
        "features": len(cells) * len(colours),
        "difference_rank": result.difference_rank,
        "space_dimension": result.dimension,
        "constrained_fraction": (round(result.difference_rank /
                                       max(1, result.n_features), 6)),
        "verdict": None,
    }
    adequacy["verdict"] = (
        "ADEQUATE: the observed differences constrain most of the feature "
        "space" if adequacy["constrained_fraction"] > 0.5 else
        "THIN: %d transitions constrain rank %d of %d features, so the null "
        "space has dimension %d and nearly every vector in it is a 'law' that "
        "is true over these states and unfalsified rather than confirmed. "
        "Treat every law below as a correlation awaiting a transition that "
        "could break it, not as a conservation law."
        % (n_transitions, result.difference_rank, result.n_features,
           result.dimension))

    report.update({
        "n_features": result.n_features,
        "space_dimension": result.dimension,
        "difference_rank": result.difference_rank,
        "evidence_adequacy": adequacy,
        "n_laws": len(result.laws),
        "n_global_laws": len(globals_),
        "n_cell_local_laws": len(result.cell_local_laws()),
        "global_laws": [{"support": [f.name() for f in law.features],
                         "value": law.value,
                         "cells": sorted({cells[f.cell] for f in law.features})}
                        for law in globals_[:40]],
    })
    report["_result"] = result
    return report


# ---------------------------------------------------------------- plumbing
def _effect_json(effect: Any) -> Dict[str, Any]:
    out = {"type": getattr(effect, "type", None)}
    for name in ("dy", "dx", "to", "direction"):
        value = getattr(effect, name, None)
        if value is not None:
            out[name] = list(value) if isinstance(value, tuple) else value
    return out


def _histogram(values) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for v in values:
        out[str(v)] = out.get(str(v), 0) + 1
    return out


def _append_candidates(module, attr: str, out_path: str, *args) -> int:
    """Engines write their own rows when handed `out_path`; a few build them
    separately. Either way the single writer is `common.candidates`."""
    from common.candidates import emit                 # noqa: PLC0415
    rows = getattr(module, attr)(*args)
    emit(out_path, rows)
    return len(rows)


def strip_internals(report: Any) -> Any:
    """Remove the in-memory engine objects before a report is serialised."""
    if isinstance(report, dict):
        return {k: strip_internals(v) for k, v in report.items()
                if not k.startswith("_")}
    if isinstance(report, list):
        return [strip_internals(v) for v in report]
    return report


def run_engines(store: FrameStore, out_path: str) -> Dict[str, Any]:
    """The dispatch step of theorize: choose engines, run them, collect.

    Theoria.md 1.10(b) rule 3: engine calls are not model calls. Nothing in
    this function can reach a model, and the whole of it is deterministic given
    the same frames.
    """
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    window = choose_window(store)
    seg = segment(store, window, out_path=out_path)
    mined = mine(store, seg, window, out_path=out_path)
    law = laws(store, out_path=out_path)

    dispatched = ["mdl_segmenter", "cegis_miner", "zero_space"]
    not_dispatched = {
        "lp_potential": "needs an explicit state graph with enumerated moves; "
                        "none exists for a 64x64 world whose dynamics are unknown",
        "ic3_pdr": "same graph requirement as lp_potential",
        "fd_adapter": "needs theory.pddl, which needs a manual; runs at plan, "
                      "not at dispatch",
        "deadlock_carver": "needs a grounded PDDL task; same gate as fd_adapter",
        "probe_frontier": "needs a hypothesis frontier, which is theorize's "
                          "output rather than its input; runs at probe",
    }
    return {"window": window, "mdl_segmenter": seg, "cegis_miner": mined,
            "zero_space": law, "dispatched": dispatched,
            "not_dispatched": not_dispatched,
            "store": store.summary()}
