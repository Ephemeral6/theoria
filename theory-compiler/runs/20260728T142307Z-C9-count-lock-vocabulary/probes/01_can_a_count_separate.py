"""Can a colour-cardinality atom separate these pairs at all?  Decisive check."""
import os, sys
from collections import Counter
sys.path.insert(0, ".")
from worldgen.qc.bridge import (atoms_a0, engines_stage, extract_board,
                                multi_miner, object_layer, segment_operators)
from worldgen.core.trace import read_trace
from worldgen.qc.run_qc import WORLDS_OUT

world_id = "t2-lock-fragile"
frames, actions, _ = read_trace(os.path.join(WORLDS_OUT, world_id, "raw_trace.jsonl"))
board = extract_board(frames)
bg = engines_stage.background_color(board, frames)
layer = object_layer(frames, board, background=bg)
_op, seg, _ = segment_operators.choose_operator(layer, background=bg)
transitions = multi_miner.build_transitions(frames, layer, actions, seg, background=bg)
track_ids = [t.track_id for t in seg.tracks]
vocab = multi_miner.build_vocabulary([t.obs for t in transitions], list(track_ids))
masks = multi_miner.atom_masks(vocab, [t.obs for t in transitions],
                               [t.action for t in transitions])

n_count = sum(1 for a in vocab if a.kind == "count")
print("atoms=%d  of which count=%d" % (len(vocab), n_count))
print("count atoms:", sorted({a.name for a in vocab if a.kind == "count" and not a.negated}))

groups = {}
for tr in transitions:
    for track in track_ids:
        groups.setdefault((track, tr.action, tr.effects[track].key()), []).append(tr)

def hist(obs):
    return Counter(v for row in obs.frame for v in row)

pairs_checked = 0
hist_differs = 0
examples = []
for (track, action, eff), members in sorted(groups.items(), key=lambda kv: str(kv[0])):
    others = [tr for tr in transitions
              if tr.action == action and tr.effects[track].key() != eff]
    for pos in members:
        for neg in others:
            same_atoms = all(
                atoms_a0.evaluate(a, pos.obs, pos.action)
                == atoms_a0.evaluate(a, neg.obs, neg.action) for a in vocab)
            if not same_atoms:
                continue
            pairs_checked += 1
            hp, hn = hist(pos.obs), hist(neg.obs)
            if hp != hn:
                hist_differs += 1
                if len(examples) < 3:
                    examples.append((track, action, hp, hn))
            elif len(examples) < 3 and pairs_checked <= 3:
                diff = [(r, c, pos.obs.frame[r][c], neg.obs.frame[r][c])
                        for r in range(len(pos.obs.frame))
                        for c in range(len(pos.obs.frame[0]))
                        if pos.obs.frame[r][c] != neg.obs.frame[r][c]]
                examples.append((track, action, "identical histogram", diff))

print("\ninseparable (pos,neg) pairs the whole vocabulary agrees on: %d" % pairs_checked)
print("of those, pairs whose colour histograms DIFFER: %d" % hist_differs)
print("  -> a colour-cardinality atom can separate at most those %d." % hist_differs)
for e in examples:
    print("  example:", e)
