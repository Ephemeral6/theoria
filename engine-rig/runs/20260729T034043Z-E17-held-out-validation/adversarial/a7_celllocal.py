"""Is the 92.9 % `cell_local` "surprise" a fact about `scope`, or about the
corpus's boundary?

`operations_for` builds CONTIGUOUS windows on a line, so cell 0 is touched by
exactly one operation and cell n-1 by exactly one operation.  Withhold either of
those two and the corresponding cell is constant in the training data.  Rebuild
the same family with WRAP-AROUND windows -- every cell then touched by k
operations -- and re-measure.
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from common.rng import SplitMix64
from engines.zero_space import gf2, zerospace
from heldout import parityworld
from heldout.parityworld import COLORS, ParityWorld, apply
from heldout import split as hsplit


def cyclic_ops(n_cells, width):
    return [tuple(sorted((i + j) % n_cells for j in range(width)))
            for i in range(n_cells)]


def build(ops, n_cells, seed, n_transitions=60, tag="cyc"):
    rng = SplitMix64(seed)
    initial = tuple(COLORS[rng.below(2)] for _ in range(n_cells))
    actions = list(range(len(ops)))
    while len(actions) < n_transitions:
        actions.append(rng.below(len(ops)))
    actions = actions[:n_transitions]
    state = initial
    states = [state]
    for a in actions:
        state = apply(state, ops[a])
        states.append(state)
    return ParityWorld(world_id="%s-n%d-s%08x" % (tag, n_cells, seed),
                       n_cells=n_cells, width=len(ops[0]), seed=seed,
                       operations=ops, actions=actions, states=states)


def score(world, train, heldout):
    feats = zerospace.build_features(world.n_cells, sorted(COLORS))
    enc = [zerospace.encode(s, feats) for s in world.states]
    basis = gf2.null_space([enc[t] ^ enc[t + 1] for t in train], len(feats))
    locals_, _ = zerospace.local_laws(basis, feats)
    globals_ = [gf2.reduce_modulo(v, locals_)
                for v in gf2.quotient_basis(sorted(basis), locals_)]
    c = Counter()
    misses = []
    for scope, vecs in (("cell_local", locals_), ("global", globals_)):
        for v in vecs:
            ok = all(gf2.dot(v, enc[t] ^ enc[t + 1]) == 0 for t in heldout)
            c[scope + "/laws"] += 1
            c[scope + "/hit"] += int(ok)
            if not ok and scope == "cell_local":
                sup = [feats[i].name() for i in gf2.support(v, len(feats))]
                misses.append(sup)
    return c, misses


def sweep(make_ops, label):
    tally = Counter()
    miss_cells = Counter()
    boundary_ops = 0
    for n_cells in parityworld.N_CELLS:
        for width in parityworld.WIDTHS:
            for i in range(20):
                seed = parityworld.SEED_BASE + 1000 * n_cells + 100 * width + i
                ops = make_ops(n_cells, width)
                w = build(ops, n_cells, seed, tag=label)
                for j in range(len(ops)):
                    tr, ho = hsplit.leave_one_operation_out(w.actions, j)
                    if not tr or not ho:
                        continue
                    c, misses = score(w, tr, ho)
                    tally.update(c)
                    if misses:
                        boundary_ops += 1
                    for sup in misses:
                        for name in sup:
                            miss_cells[name.split("@")[1]] += 1
    print("  %-28s cell_local laws=%-6d hit=%.1f %%   global laws=%-6d hit=%.1f %%"
          % (label, tally["cell_local/laws"],
             100.0 * tally["cell_local/hit"] / tally["cell_local/laws"],
             tally["global/laws"],
             100.0 * tally["global/hit"] / tally["global/laws"]))
    print("      leave-one-out variants producing a cell_local miss: %d" % boundary_ops)
    print("      miss支持 by cell index:", dict(sorted(miss_cells.items(),
                                                       key=lambda kv: int(kv[0]))))


def main():
    print("== Z-S2 cell_local, contiguous windows (the delivered corpus) ==")
    sweep(lambda n, k: parityworld.operations_for(n, k), "contiguous (delivered)")
    print()
    print("== Z-S2 cell_local, the same family with WRAP-AROUND windows ==")
    sweep(cyclic_ops, "cyclic")


if __name__ == "__main__":
    main()
