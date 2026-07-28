"""Probe 05 -- what the segmenter actually returns on a consumable world.

W-1252 measured the symptom (`mover_track` picks a token) but not the shape of
the segmentation that produces it.  This dumps, per track: colour, lifetime,
the anchor sequence, and the events credited to it -- for the three worlds whose
move attribution differs.

Read-only.  No network, no API.
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "cold-start-a0"))
sys.path.insert(0, os.path.join(ROOT, "engine-rig"))

import _bootstrap  # noqa: F401,E402

from pipeline import multi_miner, segment_operators  # noqa: E402
from pipeline.board import extract_board, object_layer  # noqa: E402
from pipeline.engines_stage import background_color  # noqa: E402
from world.ground_truth import read_trace  # noqa: E402

WORLDS = ["t2-lock-fragile", "t1-tokens-lock", "t1-walk-maze"]


def trace_path(world):
    return os.path.join(ROOT, "worldgen", "out", "worlds", world, "raw_trace.jsonl")


def run(k, world):
    frames, actions, _wins = read_trace(trace_path(world))
    board = extract_board(frames)
    background = background_color(board, frames)
    layer = object_layer(frames, board, background=background)
    operator, seg, _rep = segment_operators.choose_operator(layer, background=background)
    mover = multi_miner.mover_track(seg)

    print("== %s  frames=%d operator=%s mover=%s" % (world, len(frames), operator, mover))
    for track in seg.tracks:
        present = [i for i, m in enumerate(track.masks) if m is not None]
        anchors = [track.anchors[i] for i in present]
        distinct = sorted({tuple(a) for a in anchors if a is not None})
        moves = sum(1 for e in seg.events if e.track == track.track_id and e.type == "move")
        others = sorted({e.type for e in seg.events
                         if e.track == track.track_id and e.type != "move"})
        print("   %-6s colour=%-3s life=[%s..%s]/%d  distinct_anchors=%-3d moves=%-3d other=%s"
              % (track.track_id, track.color,
                 present[0] if present else "-", present[-1] if present else "-",
                 len(track.masks), len(distinct), moves, ",".join(others) or "-"))
        if len(distinct) <= 6:
            print("          anchors: %s" % (distinct,))
        else:
            print("          anchors: %s ... (%d total)" % (distinct[:6], len(distinct)))
    print()


if __name__ == "__main__":
    for k, w in enumerate(WORLDS):
        run(k, w)
