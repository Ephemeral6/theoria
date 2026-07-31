"""Which reading of the E11 prose fits ALL of E11's corpus-A numbers, not just two?

E11 published, from one 4000-world corpus:
    infinity_rows 1633, zero_cost_bug 82, ranking differences 35
    (of which 10 exact ties + 25 float near-ties, 0 real reorderings),
    max entropy deviation 1.11e-15.

The E18 module only scored itself against the first two.  `ranking_diff_worlds`
is a third, independent handle on the same draw and is sensitive to n_actions
and n_obs in a different way, so it discriminates between readings that the
first two cannot separate.  Scratch; run from engine-rig/.
"""
import math
import os
import random
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RIG = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, RIG)
sys.path.insert(0, os.path.dirname(RIG))

from tools.survey_numbers import pf_infinity as PF  # noqa: E402
from engines.probe_frontier.frontier import rank_probes  # noqa: E402
from engines.probe_frontier import Hypothesis  # noqa: E402

TIE_TOL = PF.TIE_TOL


class W:
    def __init__(self, seed, hr, ar, orr, p):
        rng = random.Random(seed)
        h = rng.randint(*hr)
        a = rng.randint(*ar)
        o = rng.randint(*orr)
        self.ids = tuple("h%d" % i for i in range(h))
        self.actions = PF.ACTION_NAMES[:a]
        self.obs = PF.OBSERVATIONS[:o]
        self.table = tuple(tuple(rng.choice(self.obs) for _ in self.actions)
                           for _ in self.ids)
        self.weights = tuple(rng.choice(PF.WEIGHT_POOL) for _ in self.ids)
        self.costs = tuple(0.0 if rng.random() < p else rng.choice(PF.COST_NONZERO)
                           for _ in self.actions)
        self.state = "s%08d" % seed

    def hypotheses(self):
        out = []
        for i, hid in enumerate(self.ids):
            lk = {a: self.table[i][j] for j, a in enumerate(self.actions)}
            out.append(Hypothesis(id=hid, predict=lambda s, a, lk=lk: lk[a],
                                  weight=self.weights[i], description=hid))
        return out

    def part(self, j):
        d = {}
        for i, hid in enumerate(self.ids):
            d.setdefault(self.table[i][j], []).append(hid)
        return d


def sweep(base, n, hr, ar, orr, p, with_ranking=True):
    inf = bug = rank_diff = exact = 0
    for i in range(n):
        w = W(base + i, hr, ar, orr, p)
        costs = {a: c for a, c in zip(w.actions, w.costs)}
        hyps = w.hypotheses()
        ranked = rank_probes(hyps, w.state, w.actions, costs=costs)
        splits = [len(w.part(j)) > 1 for j in range(len(w.actions))]
        some = any(splits)
        zsplit = any(c == 0.0 and s for c, s in zip(w.costs, splits))
        zpresent = any(c == 0.0 for c in w.costs)
        if zsplit:
            inf += 1
        if zpresent and not zsplit and some:
            bug += 1
        if not with_ranking:
            continue
        # independent truth ranking, same discipline as the module
        wt = {h.id: h.weight for h in hyps}
        tv = {}
        for j, a in enumerate(w.actions):
            cw = [math.fsum(wt[x] for x in ids)
                  for _, ids in sorted(w.part(j).items())]
            tot = math.fsum(cw)
            ent = (math.log2(tot)
                   - math.fsum(x * math.log2(x) for x in cw if x > 0) / tot) if tot > 0 else 0.0
            c = costs[a]
            tv[a] = (ent, c, ent / c if c else math.inf)
        oe = [v.action for v in ranked]
        ot = [a for a, _ in sorted(tv.items(),
                                   key=lambda kv: (-kv[1][2], -kv[1][0], kv[1][1], str(kv[0])))]
        if oe != ot:
            rank_diff += 1
            # would a key WITHOUT the str() fallback have differed here too?
        # E11's 10 "exact tie decided by str()" cases: pairs exactly equal on
        # (-value,-entropy,cost).  Count worlds that contain such a pair at all.
        ev = {v.action: (v.value, v.entropy, v.cost) for v in ranked}
        acts = list(ev)
        if any(ev[acts[x]] == ev[acts[y]]
               for x in range(len(acts)) for y in range(x + 1, len(acts))):
            exact += 1
    return inf, bug, rank_diff, exact


READINGS = [
    ("literal   h1-9 a1-7 o1-5 p=2/9", (1, 9), (1, 7), (1, 5), 2 / 9),
    ("E18 alt   h1-8 a2-6 o1-5 p=2/9", (1, 8), (2, 6), (1, 5), 2 / 9),
    ("E18 alt2  h1-9 a2-7 o1-5 p=1/6", (1, 9), (2, 7), (1, 5), 1 / 6),
    ("h2-9 a1-7 o1-5 p=2/9", (2, 9), (1, 7), (1, 5), 2 / 9),
    ("h1-9 a1-7 o2-5 p=2/9", (1, 9), (1, 7), (2, 5), 2 / 9),
    ("h1-8 a2-6 o2-5 p=2/9", (1, 8), (2, 6), (2, 5), 2 / 9),
    ("h2-9 a2-7 o2-5 p=2/9", (2, 9), (2, 7), (2, 5), 2 / 9),
]

N = 4000
REPS = 12
print("%-34s %-18s %-14s %-16s" %
      ("reading", "infinity(1633)", "bug(82)", "rank_diff(35)"))
for name, hr, ar, orr, p in READINGS:
    infs, bugs, rds, exs = [], [], [], []
    for r in range(REPS):
        i_, b_, rd_, ex_ = sweep(PF.BASE_SEED + r * N, N, hr, ar, orr, p)
        infs.append(i_); bugs.append(b_); rds.append(rd_); exs.append(ex_)
    def f(v, target):
        m, s = statistics.mean(v), statistics.stdev(v)
        return "%6.0f+-%-4.0f z%+.1f" % (m, s, (target - m) / s if s else 0)
    print("%-34s %s  %s  %s   exact_tie_worlds=%.0f"
          % (name, f(infs, 1633), f(bugs, 82), f(rds, 35), statistics.mean(exs)))
