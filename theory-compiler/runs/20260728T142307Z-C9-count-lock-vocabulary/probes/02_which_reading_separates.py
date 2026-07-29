"""Which candidate atom family actually separates the 276 pairs?  Measure, don't guess."""
import os, sys
sys.path.insert(0, ".")
from worldgen.qc.bridge import (atoms_a0, engines_stage, extract_board,
                                multi_miner, object_layer, segment_operators)
from worldgen.core.trace import read_trace
from worldgen.qc.run_qc import WORLDS_OUT

DELTA = atoms_a0.DELTA
world_id = "t2-lock-fragile"
frames, actions, _ = read_trace(os.path.join(WORLDS_OUT, world_id, "raw_trace.jsonl"))
board = extract_board(frames)
bg = engines_stage.background_color(board, frames)
layer = object_layer(frames, board, background=bg)
_op, seg, _ = segment_operators.choose_operator(layer, background=bg)
transitions = multi_miner.build_transitions(frames, layer, actions, seg, background=bg)
track_ids = [t.track_id for t in seg.tracks]
vocab = multi_miner.build_vocabulary([t.obs for t in transitions], list(track_ids))

# candidate readings, all computed from Obs alone
def anchor_of(obs, t):
    a = obs.anchors.get(t)
    return tuple(a) if a is not None else None

def f_abs(obs, t):                      # (a) absolute anchor of track t
    return ("abs", t, anchor_of(obs, t))

def f_delta(obs, t):                    # (b) t's anchor minus the mover's
    a, m = anchor_of(obs, t), (tuple(obs.mover_anchor) if obs.mover_anchor else None)
    if a is None or m is None:
        return ("delta", t, None)
    return ("delta", t, (a[0] - m[0], a[1] - m[1]))

def f_adj(obs, t):                      # (c) t sits one step in direction D from the mover
    a, m = anchor_of(obs, t), (tuple(obs.mover_anchor) if obs.mover_anchor else None)
    if a is None or m is None:
        return ("adj", t, None)
    for d, (dr, dc) in DELTA.items():
        if (m[0] + dr, m[1] + dc) == a:
            return ("adj", t, d)
    return ("adj", t, "far")

pairs = []
groups = {}
for tr in transitions:
    for track in track_ids:
        groups.setdefault((track, tr.action, tr.effects[track].key()), []).append(tr)
for (track, action, eff), members in groups.items():
    others = [tr for tr in transitions
              if tr.action == action and tr.effects[track].key() != eff]
    for pos in members:
        for neg in others:
            if all(atoms_a0.evaluate(a, pos.obs, pos.action)
                   == atoms_a0.evaluate(a, neg.obs, neg.action) for a in vocab):
                pairs.append((track, pos, neg))
print("inseparable pairs: %d" % len(pairs))

for label, fn in (("(a) at(T) absolute", f_abs),
                  ("(b) delta(T) relative to the tracked object", f_delta),
                  ("(c) adj(T,D) one step away", f_adj)):
    sep = 0
    for track, pos, neg in pairs:
        if any(fn(pos.obs, t) != fn(neg.obs, t) for t in track_ids):
            sep += 1
    print("%-46s separates %3d / %d" % (label, sep, len(pairs)))
