"""Precision on the reproduced entropy deltas + a large closed-form cross-check."""
import math
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RIG = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, RIG)
sys.path.insert(0, os.path.dirname(RIG))

from tools.survey_numbers import pf_infinity as PF        # noqa: E402
from engines.cegis_miner.atoms import evaluate            # noqa: E402
from engines.probe_frontier import hypotheses_from_guards  # noqa: E402

ACTS = PF.PROBE_ACTIONS


def H(cf, n):
    out = np.zeros_like(cf, dtype=float)
    p = cf / float(n)
    m = (p > 0) & (p < 1)
    pp = p[m]
    out[m] = -(pp * np.log2(pp) + (1 - pp) * np.log2(1 - pp))
    return out


print("=== reading (3): max over states of |best-action entropy| difference ===")
states = PF._enumerate_states()
for rule in sorted(PF._mined_rules(), key=lambda r: r.name):
    if rule.name not in ("teleport", "blocked_UP"):
        continue
    hyps = hypotheses_from_guards(rule.frontier, evaluate, label=rule.name)
    g = len(hyps)
    fires = np.zeros((g, len(states), len(ACTS)), dtype=bool)
    for k, h in enumerate(hyps):
        for si, s in enumerate(states):
            for ai, a in enumerate(ACTS):
                fires[k, si, ai] = (h.predict(s, a) == "fires")
    seen, reps = {}, []
    for k in range(g):
        v = fires[k].tobytes()
        if v not in seen:
            seen[v] = k
            reps.append(k)
    Ha = H(fires.sum(0).astype(float), g)
    Hb = H(fires[reps].sum(0).astype(float), len(reps))
    delta_top = np.abs(Ha.max(1) - Hb.max(1))
    i = int(delta_top.argmax())
    print("%-12s guards=%d worlds=%d  max|topH_all - topH_rep| = %.10f  -> %.4f"
          % (rule.name, g, len(reps), delta_top.max(), round(float(delta_top.max()), 4)))
    print("             (all-actions max, what E18 used)      = %.10f  -> %.4f"
          % (np.abs(Ha - Hb).max(), round(float(np.abs(Ha - Hb).max()), 4)))

print()
print("=== closed form vs 4,000,000-world Monte Carlo, literal reading ===")
rng = random.Random(12345)
p = 2 / 9
N = 4_000_000
inf = bug = 0
for _ in range(N):
    h = rng.randint(1, 9)
    a = rng.randint(1, 7)
    o = rng.randint(1, 5)
    cols = [len({rng.randrange(o) for _ in range(h)}) > 1 for _ in range(a)]
    # regenerate properly: the set trick above already draws h cells per column
    zs = [rng.randrange(9) < 2 for _ in range(a)]
    zsplit = any(z and c for z, c in zip(zs, cols))
    if zsplit:
        inf += 1
    elif any(zs) and any(cols):
        bug += 1
print("MC per 4000: infinity=%.1f  zero_cost_bug=%.1f"
      % (4000 * inf / N, 4000 * bug / N))
