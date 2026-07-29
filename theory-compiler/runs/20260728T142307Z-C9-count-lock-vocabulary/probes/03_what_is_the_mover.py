import os, sys
sys.path.insert(0, ".")
from worldgen.qc.bridge import (atoms_a0, engines_stage, extract_board,
                                multi_miner, object_layer, segment_operators)
from worldgen.core.trace import read_trace
from worldgen.qc.run_qc import WORLDS_OUT
for world_id in ("t2-lock-fragile", "t1-tokens-lock"):
    frames, actions, _ = read_trace(os.path.join(WORLDS_OUT, world_id, "raw_trace.jsonl"))
    board = extract_board(frames)
    bg = engines_stage.background_color(board, frames)
    layer = object_layer(frames, board, background=bg)
    _op, seg, _ = segment_operators.choose_operator(layer, background=bg)
    trs = multi_miner.build_transitions(frames, layer, actions, seg, background=bg)
    tracks = [t.track_id for t in seg.tracks]
    o = trs[0].obs
    print("== %s: %d tracks %s" % (world_id, len(tracks), tracks))
    print("   mover_anchor over first 5 transitions:",
          [t.obs.mover_anchor for t in trs[:5]])
    print("   distinct mover_anchors:", len({str(t.obs.mover_anchor) for t in trs}))
    print("   anchors dict (t0):", o.anchors)
    v = multi_miner.build_vocabulary([t.obs for t in trs], list(tracks))
    print("   atoms=%d, at-atoms=%d, count-atoms=%d"
          % (len(v), sum(1 for a in v if a.kind == "at"),
             sum(1 for a in v if a.kind == "count")))
