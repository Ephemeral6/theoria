"""The 'row shift' question: E11's 0.0617 / 0.0584 vs E18's 0.0669 / 0.0617.

Builds the fires/silent matrix once per rule and computes the max entropy delta
between 'one vote per guard' and 'one vote per distinguishable world' under
several defensible readings of what 'max entropy delta' means.  If some reading
reproduces E11's pair, the 'row shift' story is wrong.  Scratch; run from
engine-rig/.
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RIG = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, RIG)
sys.path.insert(0, os.path.dirname(RIG))

from tools.survey_numbers import pf_infinity as PF   # noqa: E402
from engines.cegis_miner.atoms import evaluate       # noqa: E402
from engines.probe_frontier import hypotheses_from_guards  # noqa: E402

ACTS = PF.PROBE_ACTIONS


def H(counts_fire, n):
    """Binary partition entropy in bits, all guards weight 1.0."""
    out = np.zeros_like(counts_fire, dtype=float)
    p = counts_fire / float(n)
    mask = (p > 0) & (p < 1)
    pp = p[mask]
    out[mask] = -(pp * np.log2(pp) + (1 - pp) * np.log2(1 - pp))
    return out


states = PF._enumerate_states()
rules = PF._mined_rules()
print("states=%d rules=%d" % (len(states), len(rules)))

for rule in sorted(rules, key=lambda r: r.name):
    hyps = hypotheses_from_guards(rule.frontier, evaluate, label=rule.name)
    g = len(hyps)
    # fires[k, s, a]
    fires = np.zeros((g, len(states), len(ACTS)), dtype=bool)
    for k, h in enumerate(hyps):
        for si, s in enumerate(states):
            for ai, a in enumerate(ACTS):
                fires[k, si, ai] = (h.predict(s, a) == "fires")
    vecs = [fires[k].tobytes() for k in range(g)]
    seen, reps = {}, []
    for k, v in enumerate(vecs):
        if v not in seen:
            seen[v] = k
            reps.append(k)
    if len(reps) == g:
        print("%-14s guards=%2d worlds=%2d  (no collapse)" % (rule.name, g, len(reps)))
        continue

    n_all = fires.sum(axis=0).astype(float)                 # (S, A)
    n_rep = fires[reps].sum(axis=0).astype(float)
    Ha = H(n_all, g)
    Hb = H(n_rep, len(reps))
    d = np.abs(Ha - Hb)

    am_a = np.lexsort((np.array([str(x) for x in ACTS])[None, :].repeat(len(states), 0).argsort(1),
                       -Ha), axis=1)[:, 0]
    # engine order: (-value,-entropy,cost,str(action)); cost is uniform 1.0 here
    order_a = np.lexsort((np.tile(np.arange(len(ACTS)), (len(states), 1)), -Ha), axis=1)
    order_b = np.lexsort((np.tile(np.arange(len(ACTS)), (len(states), 1)), -Hb), axis=1)
    moved = order_a[:, 0] != order_b[:, 0]
    top_a = Ha.max(axis=1)
    top_b = Hb.max(axis=1)
    at_argmax = np.abs(Ha[np.arange(len(states)), order_a[:, 0]]
                       - Hb[np.arange(len(states)), order_a[:, 0]])
    splittable = (Ha > 0).any(axis=1)

    print("%-14s guards=%2d worlds=%2d  argmax_moved=%d" %
          (rule.name, g, len(reps), int(moved.sum())))
    print("      (1) max over all states x all actions      = %.6f" % d.max())
    print("      (2) max |H_all - H_rep| at engine argmax   = %.6f" % at_argmax.max())
    print("      (3) max |max_a H_all - max_a H_rep|        = %.6f" % np.abs(top_a - top_b).max())
    print("      (4) (1) restricted to states argmax moved  = %.6f"
          % (d[moved].max() if moved.any() else 0.0))
    print("      (5) (1) restricted to splittable states    = %.6f" % d[splittable].max())
    print("      (6) max over distinct (n_all,n_rep) pairs  = %.6f  pairs=%s"
          % (d.max(), sorted({(int(x), int(y)) for x, y in
                              zip(n_all.ravel(), n_rep.ravel())})[:12]))
    # every attainable delta value, so we can see whether 0.0617/0.0584 is on the menu
    vals = sorted({round(float(x), 6) for x in d.ravel()})
    print("      attainable deltas (top 8): %s" % vals[-8:])
