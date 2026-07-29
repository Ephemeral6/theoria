"""Q1/Q2: independent re-derivation of the minimal detection depth.

Two independent oracles:
  (A) full synchronised-product BFS that does NOT stop at the first divergence
      -- it explores every pair reachable by a common action sequence, and only
      afterwards reports the minimum depth at which any frame pair differs.
  (B) brute-force IDDFS over literal action sequences up to depth D (exponential,
      so only for small D), which makes no product/dedup argument at all.
"""
import itertools
from collections import deque
from worldgen.core.world import GridWorld
from worldgen.core.types import ACTIONS
from worldgen import mutate
from worldgen.mutate import _frame_key, earliest_detection


def full_product_min_depth(base, mutant, cap=400000):
    """Min depth of a divergent (pair, action); explores the WHOLE product,
    diverged pairs included, so no pruning argument is relied on."""
    s = (base.initial(), mutant.initial())
    if _frame_key(base, s[0]) != _frame_key(mutant, s[1]):
        return 0, [], True
    seen = {(s[0].key(), s[1].key()): 0}
    q = deque([(s[0], s[1], ())])
    best = None
    best_w = None
    while q:
        sb, sm, path = q.popleft()
        d = len(path)
        if best is not None and d >= best:
            continue
        for a in ACTIONS:
            nb = base.step(sb, a)
            nm = mutant.step(sm, a)
            if _frame_key(base, nb) != _frame_key(mutant, nm):
                if best is None or d + 1 < best:
                    best, best_w = d + 1, list(path) + [a]
                continue          # do not expand past a divergence either way
            k = (nb.key(), nm.key())
            if k in seen:
                continue
            if len(seen) >= cap:
                return None, None, False
            seen[k] = d + 1
            q.append((nb, nm, path + (a,)))
    return best, best_w, True


def brute_force(base, mutant, maxd):
    """No product, no dedup: literal enumeration of action sequences."""
    for d in range(0, maxd + 1):
        for seq in itertools.product(ACTIONS, repeat=d):
            sb, sm = base.initial(), mutant.initial()
            if _frame_key(base, sb) != _frame_key(mutant, sm):
                return 0, []
            ok = True
            for i, a in enumerate(seq):
                sb = base.step(sb, a)
                sm = mutant.step(sm, a)
                if _frame_key(base, sb) != _frame_key(mutant, sm):
                    if i + 1 == d:
                        return d, list(seq)
                    ok = False
                    break
            if not ok:
                continue
    return None, None


print("%-12s %-8s %-8s %-8s %s" % ("id", "shipped", "oracleA", "oracleB", "verdict"))
for eid, edit in sorted(mutate.MUTANT_BY_ID.items()):
    b = GridWorld(mutate.BY_ID[edit.base])
    m = GridWorld(edit.spec())
    got = earliest_detection(b, m)
    a_d, a_w, a_complete = full_product_min_depth(b, m)
    maxd = 6 if (got["actions"] is None or got["actions"] > 6) else got["actions"] + 1
    bf_d, bf_w = brute_force(b, m, min(maxd, 7))
    agree = (got["actions"] == a_d) and (bf_d is None or bf_d == got["actions"])
    print("%-12s %-8s %-8s %-8s %s" % (
        eid, got["actions"], a_d, bf_d,
        "ok" if agree else "*** DISAGREE ***"))
    if got["actions"] is not None:
        # verify the witness actually diverges and is of the stated length
        sb, sm = b.initial(), m.initial()
        for a in got["witness"]:
            sb, sm = b.step(sb, a), m.step(sm, a)
        assert len(got["witness"]) == got["actions"]
        assert _frame_key(b, sb) != _frame_key(m, sm), "%s witness does not diverge" % eid
