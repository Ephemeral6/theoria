"""Front (b): re-cut the same evidence every other defensible way.

If a hit rate is a property of the engine, re-cutting should move it a little.
If it is a property of the cut, re-cutting should move it a lot -- or, worse,
not move it at all because the cut never withheld anything.
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from common.rng import SplitMix64
from engines.zero_space import gf2, zerospace
from heldout import parityworld
from heldout.parityworld import COLORS, ParityWorld, apply, operations_for
from heldout import split as hsplit


def enc_world(world):
    feats = zerospace.build_features(world.n_cells, sorted(COLORS))
    return feats, [zerospace.encode(s, feats) for s in world.states]


def fit_score(world, train, heldout):
    feats, enc = enc_world(world)
    diffs = [enc[t] ^ enc[t + 1] for t in train]
    basis = gf2.null_space(diffs, len(feats))
    locals_, _ = zerospace.local_laws(basis, feats)
    globals_ = [gf2.reduce_modulo(v, locals_)
                for v in gf2.quotient_basis(sorted(basis), locals_)]
    c = Counter()
    for scope, vecs in (("cell_local", locals_), ("global", globals_)):
        for v in vecs:
            ok = all(gf2.dot(v, enc[t] ^ enc[t + 1]) == 0 for t in heldout)
            c[scope + "/laws"] += 1
            c[scope + "/hit"] += int(ok)
    # coverage: does train witness every operation?
    c["cover"] = int({world.actions[t] for t in train} == set(range(len(world.operations))))
    c["splits"] += 1
    return c


def report(name, tally):
    for scope in ("global", "cell_local"):
        laws = tally[scope + "/laws"]
        if not laws:
            continue
        print("  %-34s %-10s laws=%-6d hit=%5.1f %%"
              % (name, scope, laws, 100.0 * tally[scope + "/hit"] / laws))
    print("  %-34s train covers every op in %d / %d splits"
          % ("", tally["cover"], tally["splits"]))


def build_nocover(n_cells, width, seed, n_transitions):
    """parityworld.build WITHOUT the 'every operation first' guarantee."""
    ops = operations_for(n_cells, width)
    rng = SplitMix64(seed)
    initial = tuple(COLORS[rng.below(2)] for _ in range(n_cells))
    actions = [rng.below(len(ops)) for _ in range(n_transitions)]
    state = initial
    states = [state]
    for a in actions:
        state = apply(state, ops[a])
        states.append(state)
    return ParityWorld(world_id="nc-n%d-k%d-s%08x" % (n_cells, width, seed),
                       n_cells=n_cells, width=width, seed=seed, operations=ops,
                       actions=actions, states=states)


def frac_split(n, world_seed, num, den, salt=hsplit.SPLIT_SALT):
    order = hsplit.shuffled(range(n), world_seed ^ salt)
    cut = (n * num) // den
    return sorted(order[:cut]), sorted(order[cut:])


def main():
    worlds = parityworld.corpus()

    cuts = {
        "Z-S1 as registered (70/30, salt 5115)":
            lambda w: frac_split(len(w.actions), w.seed, 7, 10),
        "random 70/30, salt 0xBEEF":
            lambda w: frac_split(len(w.actions), w.seed, 7, 10, 0xBEEF),
        "random 50/50":
            lambda w: frac_split(len(w.actions), w.seed, 5, 10),
        "random 90/10":
            lambda w: frac_split(len(w.actions), w.seed, 9, 10),
        "random 20/80":
            lambda w: frac_split(len(w.actions), w.seed, 2, 10),
        "contiguous prefix 70 / suffix 30":
            lambda w: (list(range(42)), list(range(42, 60))),
        "contiguous suffix 70 (train = last 42)":
            lambda w: (list(range(18, 60)), list(range(18))),
        "parity of transition index (even train)":
            lambda w: ([t for t in range(60) if t % 2 == 0],
                       [t for t in range(60) if t % 2 == 1]),
    }
    print("== A. transition-level cuts of the delivered corpus ==")
    for name, fn in cuts.items():
        tally = Counter()
        for w in worlds:
            tr, ho = fn(w)
            tally.update(fit_score(w, tr, ho))
        report(name, tally)

    print()
    print("== B. leave-TWO-operations-out ==")
    tally = Counter()
    for w in worlds:
        n_ops = len(w.operations)
        for i in range(n_ops):
            for j in range(i + 1, n_ops):
                tr = [t for t, a in enumerate(w.actions) if a not in (i, j)]
                ho = [t for t, a in enumerate(w.actions) if a in (i, j)]
                if not tr or not ho:
                    continue
                tally.update(fit_score(w, tr, ho))
    report("leave-2-ops-out", tally)

    print()
    print("== C. leave-one-operation-out, as registered (control) ==")
    tally = Counter()
    for w in worlds:
        for j in range(len(w.operations)):
            tr, ho = hsplit.leave_one_operation_out(w.actions, j)
            if not tr or not ho:
                continue
            tally.update(fit_score(w, tr, ho))
    report("Z-S2", tally)

    print()
    print("== D. Z-S1 on a corpus WITHOUT parityworld.build's coverage guarantee ==")
    for T in (60, 20, 12, 8):
        tally = Counter()
        skipped = 0
        for n_cells in parityworld.N_CELLS:
            for width in parityworld.WIDTHS:
                for i in range(20):
                    seed = parityworld.SEED_BASE + 1000 * n_cells + 100 * width + i
                    w = build_nocover(n_cells, width, seed, T)
                    tr, ho = frac_split(T, seed, 7, 10)
                    if not tr or not ho:
                        skipped += 1
                        continue
                    tally.update(fit_score(w, tr, ho))
        print("  T=%d" % T)
        report("  no-coverage-guarantee 70/30", tally)


if __name__ == "__main__":
    main()
