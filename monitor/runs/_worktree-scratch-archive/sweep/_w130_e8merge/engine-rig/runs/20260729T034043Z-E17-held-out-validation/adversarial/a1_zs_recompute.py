"""Independent recomputation of the zero_space held-out numbers + leakage probes.

Nothing here imports heldout.zero_space_heldout for the scoring: the fit and the
score are re-implemented from engines.zero_space directly, so agreement with
results.json is evidence and not an echo.
"""
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from engines.zero_space import gf2, zerospace
from heldout import parityworld
from heldout.parityworld import COLORS
from heldout import split as hsplit


def encode_world(world):
    feats = zerospace.build_features(world.n_cells, sorted(COLORS))
    return feats, [zerospace.encode(s, feats) for s in world.states]


def my_fit(encoded, feats, train):
    diffs = [encoded[t] ^ encoded[t + 1] for t in train]
    basis = gf2.null_space(diffs, len(feats))
    locals_, trunc = zerospace.local_laws(basis, feats)
    globals_ = [gf2.reduce_modulo(v, locals_)
                for v in gf2.quotient_basis(sorted(basis), locals_)]
    return locals_, globals_


def score_split(world, train, heldout):
    feats, enc = encode_world(world)
    locals_, globals_ = my_fit(enc, feats, train)
    out = Counter()
    for scope, vecs in (("cell_local", locals_), ("global", globals_)):
        for v in vecs:
            delta_ok = all(gf2.dot(v, enc[t] ^ enc[t + 1]) == 0 for t in heldout)
            val = gf2.dot(v, enc[0])
            value_ok = all(gf2.dot(v, enc[e]) == val
                           for t in heldout for e in (t, t + 1))
            out[scope + "/laws"] += 1
            out[scope + "/delta"] += int(delta_ok)
            out[scope + "/value"] += int(value_ok)
            out[scope + "/agree"] += int(delta_ok == value_ok)
    return out


def main():
    worlds = parityworld.corpus()
    print("worlds:", len(worlds))

    # ---- leakage probe: how many DISTINCT difference vectors does a world have?
    distinct = Counter()
    heldout_all_seen_in_train = 0
    s1_total = 0
    for w in worlds:
        feats, enc = encode_world(w)
        diffs = [enc[t] ^ enc[t + 1] for t in range(len(enc) - 1)]
        distinct[len(set(diffs))] += 1
        tr, ho = hsplit.random_transition_split(len(w.actions), w.seed)
        train_set = {diffs[t] for t in tr}
        s1_total += 1
        if all(diffs[t] in train_set for t in ho):
            heldout_all_seen_in_train += 1
    print("distinct difference vectors per world (count -> #worlds):",
          dict(sorted(distinct.items())))
    print("ops per world:", sorted({len(w.operations) for w in worlds}))
    print("Z-S1 worlds where EVERY held-out difference vector also occurs in "
          "train (bit-identical): %d / %d" % (heldout_all_seen_in_train, s1_total))

    # ---- recompute the headline rates
    tally = Counter()
    for w in worlds:
        tr, ho = hsplit.random_transition_split(len(w.actions), w.seed)
        s = score_split(w, tr, ho)
        for k, v in s.items():
            tally["Z-S1/" + k] += v
        for j in range(len(w.operations)):
            tr2, ho2 = hsplit.leave_one_operation_out(w.actions, j)
            if not tr2 or not ho2:
                continue
            s = score_split(w, tr2, ho2)
            for k, v in s.items():
                tally["Z-S2/" + k] += v

    def rate(p):
        return "%.1f" % (100.0 * tally[p + "/delta"] / tally[p + "/laws"])

    for p in ("Z-S1/global", "Z-S1/cell_local", "Z-S2/global", "Z-S2/cell_local"):
        print("%-18s laws=%-6d delta=%s%%  value=%s%%  delta==value on %d/%d laws"
              % (p, tally[p + "/laws"], rate(p),
                 "%.1f" % (100.0 * tally[p + "/value"] / tally[p + "/laws"]),
                 tally[p + "/agree"], tally[p + "/laws"]))

    # ---- per-(n,k) global Z-S2
    per = Counter()
    for w in worlds:
        for j in range(len(w.operations)):
            tr2, ho2 = hsplit.leave_one_operation_out(w.actions, j)
            if not tr2 or not ho2:
                continue
            s = score_split(w, tr2, ho2)
            key = "n%d-k%d" % (w.n_cells, w.width)
            per[key + "/laws"] += s["global/laws"]
            per[key + "/delta"] += s["global/delta"]
    print("Z-S2 global by setting:")
    for key in sorted({k.rsplit("/", 1)[0] for k in per}):
        print("   %-8s %6d laws  %5.1f %%"
              % (key, per[key + "/laws"],
                 100.0 * per[key + "/delta"] / per[key + "/laws"]))

    # ---- against results.json
    with open("runs/20260729T034043Z-E17-held-out-validation/results.json",
              encoding="utf-8") as fh:
        d = json.load(fh)["zero_space"]["splits"]
    print("results.json says:")
    for p in ("Z-S1/global", "Z-S1/cell_local", "Z-S2/global", "Z-S2/cell_local"):
        r = d[p]
        print("   %-18s laws=%-6d delta=%.1f%%" % (p, r["laws"],
                                                   100.0 * r["delta_hit"] / r["laws"]))


if __name__ == "__main__":
    main()
