"""The factory's acceptance gate: three worlds through cold-start-a0's engines.

The bar was written down first, in `worldgen/qc/PREREGISTERED.md`, and this
module does not restate it — it measures against it and reports misses as misses.
Four layers, in order of how much they can go wrong:

    L1 liveness  -- run_stage() completes on the shipped trace; candidates
                    validate against the frozen schema
    L2 structure -- mover-track guards mutually exclusive and total
    L3a replay   -- the mined rules reproduce the trace they were mined from
    L3b held-out -- ...and the reachable pairs the trace never contained

L1 and L2 run the upstream pipeline exactly as `cold-start-a0/run_all.py` does,
on the shipped `raw_trace.jsonl`, so they are the literal reading of the gate.
L3 needs an `Obs` at unvisited states and therefore uses the shared-segmentation
protocol fixed in advance in PREREGISTERED.md §protocol.

```bash
cd .worktrees/c1-worldgen && python -m worldgen.qc.run_qc
```
"""

import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple

from . import bridge
from .bridge import extract_board, engines_stage, multi_miner, object_layer, segment_operators
from .engine_manual import EngineManual, TrackState
from ..core.explorer import _walk
from ..core.trace import read_trace, rows
from ..core.world import GridWorld
from ..generate import BY_ID

HERE = os.path.dirname(os.path.abspath(__file__))
WORLDGEN = os.path.dirname(HERE)
CATALOG = os.path.join(WORLDGEN, "catalog")
WORLDS_OUT = os.path.join(WORLDGEN, "out", "worlds")
QC_OUT = os.path.join(WORLDGEN, "out", "qc")

# Fixed in PREREGISTERED.md before the harness was run.  Not a tunable.
SAMPLE: Tuple[str, ...] = ("t1-switch-toggle", "t1-switch-latch", "t2-lock-fragile")
HELD_OUT_BAR = 0.90


# ------------------------------------------------------------------- L1 / L2

def layer_one_two(world_id: str) -> Dict[str, Any]:
    """`engines_stage.run_stage` on the shipped trace, then the schema validator."""
    trace = os.path.join(WORLDS_OUT, world_id, "raw_trace.jsonl")
    out_dir = os.path.join(QC_OUT, world_id)
    os.makedirs(out_dir, exist_ok=True)
    candidates = os.path.join(out_dir, "candidates.jsonl")
    report_path = os.path.join(out_dir, "engines_report.json")
    if os.path.exists(candidates):
        os.remove(candidates)            # append-only within a run, not across

    result: Dict[str, Any] = {"trace": trace, "candidates": candidates}
    try:
        report = engines_stage.run_stage(trace, candidates, report_path)
    except Exception as exc:                                  # noqa: BLE001
        result.update(live=False, error="%s: %s" % (type(exc).__name__, exc))
        return result

    mining = report["mining"]
    mover = report["segmentation"]["mover"]
    result.update(
        live=True,
        frames=report["frames"],
        transitions=report["transitions"],
        tracks=len(report["segmentation"]["tracks"]),
        mover=mover,
        rules_mined=len(mining["rules"]),
        mutually_exclusive=mining["mutually_exclusive"],
        explains_every_transition=mining["explains_every_transition"],
        probes=len(report["probes"]),
        executable_probes=sum(1 for p in report["probes"] if p.get("tier") == "executable"),
        global_laws=len(report["zero_space"]["global_laws"]),
    )
    result["l2_pass"] = bool(mining["mutually_exclusive"].get(mover)
                             and mining["explains_every_transition"].get(mover))

    validate = subprocess.run(
        [sys.executable, "-m", "tools.validate_candidates", candidates],
        cwd=bridge.ENGINE_RIG, capture_output=True,
    )
    result["schema_valid"] = validate.returncode == 0
    result["schema_output"] = (validate.stdout or b"").decode("utf-8", "replace").strip()
    if validate.returncode != 0:
        result["schema_error"] = (validate.stderr or b"").decode("utf-8", "replace").strip()[-800:]
    result["l1_pass"] = bool(result["live"] and result["schema_valid"])
    return result


# ------------------------------------------------------------------- L3

def _states_at(seg, layer, t: int) -> Dict[str, TrackState]:
    """Anchor from the segmentation, colour from the live mask.

    `Track.color` is what the track was declared with; a switch shows something
    else after it toggles.  `multi_miner.seg_color` is the miner's own reader,
    reused so predictor and miner cannot disagree about what a colour is.
    """
    out: Dict[str, TrackState] = {}
    for track in seg.tracks:
        anchor = track.anchors[t] if t < len(track.anchors) else None
        # The most recent place this track was seen at or before `t`.  A track
        # that is currently absent still has one, and that is what makes an
        # `appear` predictable — see `engine_manual._apply`.
        last = next((tuple(track.anchors[i]) for i in range(min(t, len(track.anchors) - 1), -1, -1)
                     if track.anchors[i] is not None), None)
        # Same for the colour: an absent track has none in frame `t`, and a
        # predicted reappearance has to be painted something.  The last colour it
        # showed is what the trace offers; `Track.color` is the declared fallback.
        color = multi_miner.seg_color(seg, layer, track.track_id, t)
        if color is None:
            color = next(
                (c for c in (multi_miner.seg_color(seg, layer, track.track_id, i)
                             for i in range(min(t, len(track.anchors) - 1), -1, -1))
                 if c is not None), track.color)
        out[track.track_id] = TrackState(
            anchor=tuple(anchor) if anchor is not None else None,
            color=color,
            last_anchor=last,
        )
    return out


def layer_three(world_id: str) -> Dict[str, Any]:
    world = GridWorld(BY_ID[world_id])

    shipped_frames, shipped_actions, _wins = read_trace(
        os.path.join(WORLDS_OUT, world_id, "raw_trace.jsonl"))
    budget = len(shipped_actions) - 1                     # last action is null

    states, actions = _walk(world, budget=None)           # the exhaustive walk
    frames = [world.render(s) for s in states]
    actions_padded: List[Optional[str]] = list(actions) + [None]

    # The protocol's load-bearing assumption, asserted rather than assumed: the
    # exhaustive walk's first `budget` transitions ARE the shipped trace.  Both
    # come from the same greedy loop, which the budget only truncates.
    prefix_rows = rows(world, states[:budget + 1], actions[:budget] + [None])
    shipped_rows = [{"t": i, "frame": shipped_frames[i], "action": shipped_actions[i],
                     "win": _wins[i]} for i in range(len(shipped_frames))]
    prefix_matches = prefix_rows == shipped_rows

    board = extract_board(frames)
    background = engines_stage.background_color(board, frames)
    layer = object_layer(frames, board, background=background)
    _operator, seg, _cmp = segment_operators.choose_operator(layer, background=background)

    transitions = multi_miner.build_transitions(
        frames, layer, actions_padded, seg, background=background)
    mover = multi_miner.mover_track(seg)
    track_ids = [t.track_id for t in seg.tracks]

    mined_on = [t for t in transitions if t.index < budget]
    result = multi_miner.mine(mined_on, track_ids, mover=mover)
    manual = EngineManual(board, background, seg, result, mover)

    # Self-check: can the decomposition even reproduce an *observed* frame?  If
    # not, every number below is measuring the renderer, not the rules.
    render_ok = sum(1 for t in range(len(frames))
                    if manual.render(_states_at(seg, layer, t)) == frames[t])

    seen_pairs = {(states[i].key(), actions[i]) for i in range(budget)}
    buckets = {"replay": [0, 0], "held_out": [0, 0]}      # [agree, total]
    conflicts = {"replay": 0, "held_out": 0}
    misses: List[Dict[str, Any]] = []
    for tr in transitions:
        t = tr.index
        pair = (states[t].key(), actions[t])
        bucket = "replay" if t < budget else ("held_out" if pair not in seen_pairs else None)
        if bucket is None:
            continue                                      # a repeat, graded already
        predicted, _nxt, n_conflicts = manual.predict_frame(
            _states_at(seg, layer, t), tr.obs, tr.action)
        conflicts[bucket] += n_conflicts
        buckets[bucket][1] += 1
        if predicted == frames[t + 1]:
            buckets[bucket][0] += 1
        elif len(misses) < 8:
            fired = {tid: manual.fire(tid, tr.obs, tr.action) for tid in track_ids}
            misses.append({
                "t": t, "action": tr.action, "bucket": bucket,
                "agent": list(states[t].agent),
                "true_rule": world.explain(states[t], tr.action)[1],
                "fired": {tid: (None if r is None else r.name) for tid, (r, _n) in fired.items()},
                "n_matching_guards": {tid: n for tid, (_r, n) in fired.items()},
            })

    def acc(name: str) -> Optional[float]:
        agree, total = buckets[name]
        return round(agree / total, 6) if total else None

    return {
        "budget": budget,
        "prefix_matches_shipped_trace": prefix_matches,
        "exhaustive_transitions": len(actions),
        "reachable_states": len(world.reachable()),
        "tracks": len(track_ids),
        "mover": mover,
        "rules_mined": len(result.rules),
        "render_self_check": "%d/%d" % (render_ok, len(frames)),
        "render_self_check_ok": render_ok == len(frames),
        "guard_conflicts": conflicts,
        "replay": {"agree": buckets["replay"][0], "total": buckets["replay"][1],
                   "accuracy": acc("replay")},
        "held_out": {"agree": buckets["held_out"][0], "total": buckets["held_out"][1],
                     "accuracy": acc("held_out")},
        "misses": misses,
    }


# ------------------------------------------------------------------ verdicts

def _l3_failure(exc: BaseException) -> Dict[str, Any]:
    return {
        "error": "%s: %s" % (type(exc).__name__, exc),
        "render_self_check_ok": None,
        "guard_conflicts": {"replay": None, "held_out": None},
        "replay": {"agree": 0, "total": 0, "accuracy": None},
        "held_out": {"agree": 0, "total": 0, "accuracy": None},
        "misses": [],
    }


def verdict(l12: Dict[str, Any], l3: Dict[str, Any]) -> Dict[str, Any]:
    replay = l3["replay"]["accuracy"]
    held = l3["held_out"]["accuracy"]
    return {
        "L1_liveness": bool(l12.get("l1_pass")),
        "L2_structure": bool(l12.get("l2_pass")),
        "L3a_replay": replay == 1.0,
        "L3b_held_out": held is not None and held >= HELD_OUT_BAR,
        "L3b_value": held,
        "held_out_bar": HELD_OUT_BAR,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    worlds = list(argv or SAMPLE)
    os.makedirs(QC_OUT, exist_ok=True)
    report: Dict[str, Any] = {
        "prompt_id": "C1-worldgen",
        "sample": worlds,
        "bar": "worldgen/qc/PREREGISTERED.md",
        "held_out_bar": HELD_OUT_BAR,
        "worlds": {},
    }
    for world_id in worlds:
        print("== %s" % world_id, flush=True)
        l12 = layer_one_two(world_id)
        # A world whose rule set cannot be synthesised at all is a *result* — it
        # is the "机制归纳错" row of the failure taxonomy showing up in the
        # factory rather than in Phase 3 — so it is recorded, not raised.
        try:
            l3 = layer_three(world_id)
        except Exception as exc:                              # noqa: BLE001
            l3 = _l3_failure(exc)
        v = verdict(l12, l3)
        report["worlds"][world_id] = {"l1_l2": l12, "l3": l3, "verdict": v}
        print("   L1=%s L2=%s L3a=%s(%s) L3b=%s(%s)  conflicts=%s  render=%s%s"
              % (v["L1_liveness"], v["L2_structure"], v["L3a_replay"],
                 l3["replay"]["accuracy"], v["L3b_held_out"], v["L3b_value"],
                 json.dumps(l3["guard_conflicts"], sort_keys=True),
                 l3.get("render_self_check", "-"),
                 "  ERROR: " + l3["error"] if l3.get("error") else ""), flush=True)

    vs = [w["verdict"] for w in report["worlds"].values()]
    report["family_verdict"] = {
        "all_L1": all(v["L1_liveness"] for v in vs),
        "all_L2": all(v["L2_structure"] for v in vs),
        "all_L3a": all(v["L3a_replay"] for v in vs),
        "L3b_passed": sum(1 for v in vs if v["L3b_held_out"]),
        "L3b_required": 2,
    }
    fv = report["family_verdict"]
    report["family_verdict"]["pass"] = bool(
        fv["all_L1"] and fv["all_L2"] and fv["all_L3a"]
        and fv["L3b_passed"] >= fv["L3b_required"])

    out = os.path.join(QC_OUT, "QC.json")
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print()
    print("family verdict: %s" % json.dumps(report["family_verdict"], sort_keys=True))
    print("-> %s" % os.path.relpath(out, WORLDGEN))
    return 0 if report["family_verdict"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:] or None))
