"""Probe 06 -- the exact frames at which the agent's identity is handed over.

Prints every non-`move` event with its bits, plus the two frames around it, so
the swap is readable rather than inferred.  Then prices the alternative reading
(the agent moved, the token vanished) in the segmenter's own cost model.

Read-only.
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "cold-start-a0"))
sys.path.insert(0, os.path.join(ROOT, "engine-rig"))

import _bootstrap  # noqa: F401,E402

from engines.mdl_segmenter.costs import CostModel  # noqa: E402
from pipeline import segment_operators  # noqa: E402
from pipeline.board import extract_board, object_layer  # noqa: E402
from pipeline.engines_stage import background_color  # noqa: E402
from world.ground_truth import read_trace  # noqa: E402

WORLD = sys.argv[1] if len(sys.argv) > 1 else "t2-lock-fragile"
PATH = os.path.join(ROOT, "worldgen", "out", "worlds", WORLD, "raw_trace.jsonl")

frames, actions, _wins = read_trace(PATH)
board = extract_board(frames)
background = background_color(board, frames)
layer = object_layer(frames, board, background=background)
operator, seg, _rep = segment_operators.choose_operator(layer, background=background)

print("== %s operator=%s tracks=%d script_bits=%d" %
      (WORLD, operator, len(seg.tracks), seg.script_bits))

anchors = {t.track_id: t.anchors for t in seg.tracks}
colors = {t.track_id: t.color for t in seg.tracks}

interesting = sorted({e.t for e in seg.events if e.type != "move"})
for t in interesting:
    print("\n-- t=%d action=%s" % (t, actions[t - 1] if 0 < t <= len(actions) else "?"))
    for e in seg.events_at(t):
        print("     %-8s track=%-6s params=%s bits=%s" %
              (e.type, e.track, dict(e.params), e.bits))
    for tid in sorted(anchors):
        a_prev = anchors[tid][t - 1] if t > 0 else None
        a_now = anchors[tid][t]
        print("       %-6s (c=%s) %s -> %s" % (tid, colors[tid], a_prev, a_now))

cost = CostModel(len(layer[0]), len(layer[0][0]), max_objects=max(len(seg.tracks), 1))
print("\ncost model: b_evtype=%d b_objid=%d b_pos=%d vanish=%d appear=%d move=%d recolor=%d"
      % (cost.b_evtype, cost.b_objid, cost.b_pos,
         cost.vanish_bits, cost.appear_bits, cost.move_bits, cost.recolor_bits))

kinds = {}
for e in seg.events:
    kinds[e.type] = kinds.get(e.type, 0) + 1
print("events: %s   total_bits=%d" % (kinds, sum(e.bits for e in seg.events)))
