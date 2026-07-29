import os, sys
from collections import Counter
sys.path.insert(0, ".")
from worldgen.qc.bridge import (engines_stage, extract_board, multi_miner,
                                object_layer, segment_operators)
from worldgen.core.trace import read_trace
from worldgen.qc.run_qc import WORLDS_OUT
for world_id in ("t2-lock-fragile", "t1-tokens-lock", "t1-walk-maze"):
    frames, actions, _ = read_trace(os.path.join(WORLDS_OUT, world_id, "raw_trace.jsonl"))
    board = extract_board(frames)
    bg = engines_stage.background_color(board, frames)
    layer = object_layer(frames, board, background=bg)
    _op, seg, _ = segment_operators.choose_operator(layer, background=bg)
    moves = Counter(e.track for e in seg.events if e.type == "move")
    types = Counter(e.type for e in seg.events)
    anchors0 = {t.track_id: seg.tracks[i].__dict__.get("shape") for i, t in enumerate(seg.tracks)}
    print("== %s  mover=%s" % (world_id, multi_miner.mover_track(seg)))
    print("   move events per track:", dict(sorted(moves.items())))
    print("   event types:", dict(sorted(types.items())))
