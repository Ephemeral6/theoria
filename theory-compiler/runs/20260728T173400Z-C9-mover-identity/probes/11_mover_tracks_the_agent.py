"""Probe 11 -- does the mover track actually follow the agent, on every world?

The adversarial review of `identity_swap` measured this and found the pass made
three cycler worlds *worse*: standing on a cycler produces the same two events as
eating a token, so the repair fired on occlusion. That is answered by giving the
pass the pixels (an occluded body shows itself again once the mover steps off;
a consumed one never does), and this is the measurement that says whether the
answer worked.

Ground truth is cheap here: the agent is the only colour-6 cell in a worldgen
frame. Agreement is "the mover's anchor is the agent's cell", counted over every
frame of every world, with the repair on and off.

    python .../11_mover_tracks_the_agent.py

Read-only. Writes one JSON next to itself.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RUN = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(RUN, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "cold-start-a0"))
sys.path.insert(0, os.path.join(ROOT, "engine-rig"))

import _bootstrap  # noqa: F401,E402

from engines.mdl_segmenter.costs import CostModel  # noqa: E402

from pipeline import multi_miner, segment_operators  # noqa: E402
from pipeline.board import extract_board, object_layer  # noqa: E402
from pipeline.engines_stage import background_color  # noqa: E402
from pipeline.reidentify import reidentify  # noqa: E402
from world.ground_truth import read_trace  # noqa: E402

AGENT = 6
WORLDS = os.path.join(ROOT, "worldgen", "out", "worlds")


def agent_cells(frames):
    out = []
    for frame in frames:
        cells = [(r, c) for r, row in enumerate(frame)
                 for c, v in enumerate(row) if v == AGENT]
        out.append(cells[0] if len(cells) == 1 else None)
    return out


def agreement(seg, truth):
    mover = multi_miner.mover_track(seg)
    track = next(t for t in seg.tracks if t.track_id == mover)
    hit = sum(1 for i, want in enumerate(truth)
              if want is not None and i < len(track.anchors)
              and track.anchors[i] is not None
              and tuple(track.anchors[i]) == want)
    return mover, hit, sum(1 for w in truth if w is not None)


def without_repair(layer, background):
    """The same choice `choose_operator` makes, with the swap pass removed."""
    best = None
    height, width = len(layer[0]), len(layer[0][0])
    for name in sorted(segment_operators.OPERATORS):
        seg = segment_operators.segment_with(name, layer, background=background)
        cost = CostModel(height, width, max_objects=segment_operators._max_objects(seg))
        merged, report = reidentify(seg, cost)
        if report.applied:
            seg = merged
        if best is None or (seg.script_bits, name) < best[0]:
            best = ((seg.script_bits, name), seg)
    return best[1]


def main():
    rows = {}
    for world in sorted(os.listdir(WORLDS)):
        path = os.path.join(WORLDS, world, "raw_trace.jsonl")
        if not os.path.exists(path):
            continue
        frames, _actions, _wins = read_trace(path)
        board = extract_board(frames)
        background = background_color(board, frames)
        layer = object_layer(frames, board, background=background)
        truth = agent_cells(frames)

        _op, seg_on, report = segment_operators.choose_operator(
            layer, background=background)
        swaps = next(r for r in report if r["chosen"])["identity_repair"]
        seg_off = without_repair(layer, background)

        mover_on, hit_on, total = agreement(seg_on, truth)
        mover_off, hit_off, _ = agreement(seg_off, truth)
        rows[world] = {
            "swaps": swaps["n_swaps"], "delta_bits": swaps["delta_bits"],
            "refusals": len(swaps["near_misses"]),
            "occlusion_test_ran": swaps["occlusion_test_ran"],
            "mover_on": mover_on, "mover_off": mover_off,
            "agree_on": hit_on, "agree_off": hit_off, "frames": total,
        }
        flag = ""
        if hit_on < hit_off:
            flag = "  <-- WORSE"
        elif hit_on > hit_off:
            flag = "  <-- better"
        print("%-24s swaps=%-2d delta=%-3d refused=%-3d  agree %3d/%-3d -> %3d/%-3d%s"
              % (world, swaps["n_swaps"], swaps["delta_bits"],
                 len(swaps["near_misses"]), hit_off, total, hit_on, total, flag))

    better = [w for w, r in rows.items() if r["agree_on"] > r["agree_off"]]
    worse = [w for w, r in rows.items() if r["agree_on"] < r["agree_off"]]
    perfect = [w for w, r in rows.items() if r["agree_on"] == r["frames"]]
    print("\nworlds: %d   improved: %d   regressed: %d   mover exact everywhere: %d"
          % (len(rows), len(better), len(worse), len(perfect)))
    print("improved:", sorted(better))
    print("regressed:", sorted(worse))
    out = os.path.join(RUN, "mover_tracks_the_agent.json")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"worlds": rows, "improved": sorted(better),
                   "regressed": sorted(worse)}, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print("wrote", out)
    return 1 if worse else 0


if __name__ == "__main__":
    sys.exit(main())
