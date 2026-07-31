"""Adversarial recheck of E18's corpus-A story.  Scratch; run from engine-rig/.

    python runs/20260730T120000Z-E18/adversarial/adv_corpus_a.py
"""
import itertools
import math
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RIG = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
ROOT = os.path.dirname(RIG)
sys.path.insert(0, RIG)
sys.path.insert(0, ROOT)

from tools.survey_numbers import pf_infinity as PF  # noqa: E402


# --------------------------------------------------------------------------
# 1. Closed form for the two defect predicates.
#
# ranked is sorted by (-value, -entropy, cost, str(action)); value = H/cost, or
# inf at cost 0.  splits <=> n_classes > 1 <=> H > 0.  Hence:
#   * emit happens iff ranked[0].splits
#   * a zero-cost action is always ranked ahead of every priced one, and the
#     zero-cost actions are ordered among themselves by entropy
#   => infinity_row  <=>  some zero-cost action splits
#   => zero_cost_bug <=>  some action has cost 0, none of those splits, and
#                         some priced action does split
# Column j splits iff the j-th column of the table has >= 2 distinct symbols.
# Cells are i.i.d. uniform over o symbols, so P(column splits) = 1 - o^(1-h),
# independently across columns; costs are independent of the table.
# --------------------------------------------------------------------------
def probs(h, a, o, p):
    q = 1.0 - o ** (1 - h)                       # P(one column splits)
    p_inf = 1.0 - (1.0 - p * q) ** a
    p_bug = ((1.0 - p * q) ** a - (1.0 - p) ** a
             - (1.0 - q) ** a + ((1.0 - p) * (1.0 - q)) ** a)
    return p_inf, p_bug


def expected(hyp_rng, act_rng, obs_rng, p, n=4000):
    hs = range(hyp_rng[0], hyp_rng[1] + 1)
    as_ = range(act_rng[0], act_rng[1] + 1)
    os_ = range(obs_rng[0], obs_rng[1] + 1)
    combos = list(itertools.product(hs, as_, os_))
    ei = math.fsum(probs(h, a, o, p)[0] for h, a, o in combos) / len(combos)
    eb = math.fsum(probs(h, a, o, p)[1] for h, a, o in combos) / len(combos)
    return n * ei, n * eb


def sd_binom(mean, n=4000):
    pr = mean / n
    return math.sqrt(n * pr * (1 - pr))


print("=" * 78)
print("1. CLOSED FORM vs the module's own claimed closed-form numbers")
print("=" * 78)
readings = [
    ("literal 1-9 x 1-7 x 1-5, p=2/9", (1, 9), (1, 7), (1, 5), 2 / 9),
    ("h 1..8, a 2..6, o 1-5, p=2/9", (1, 8), (2, 6), (1, 5), 2 / 9),
    ("a 2..7, p=1/6", (1, 9), (2, 7), (1, 5), 1 / 6),
    ("hypset-like h1..8 a2..6 o2..4 p=1/11", (1, 8), (2, 6), (2, 4), 1 / 11),
    ("literal but o 2..5", (1, 9), (1, 7), (2, 5), 2 / 9),
    ("literal but h 2..9", (2, 9), (1, 7), (1, 5), 2 / 9),
    ("literal but a 2..7", (1, 9), (2, 7), (1, 5), 2 / 9),
    ("literal but h 1..8", (1, 8), (1, 7), (1, 5), 2 / 9),
    ("literal but o 1..4", (1, 9), (1, 7), (1, 4), 2 / 9),
    ("literal p=1/4", (1, 9), (1, 7), (1, 5), 0.25),
    ("literal p=1/11", (1, 9), (1, 7), (1, 5), 1 / 11),
]
print("%-42s %8s %8s   %6s %6s" % ("reading", "E[inf]", "E[bug]", "z_1633", "z_82"))
for name, hr, ar, orn, p in readings:
    ei, eb = expected(hr, ar, orn, p)
    print("%-42s %8.1f %8.1f   %+6.2f %+6.2f"
          % (name, ei, eb, (1633 - ei) / sd_binom(ei), (82 - eb) / sd_binom(eb)))

# --------------------------------------------------------------------------
print()
print("=" * 78)
print("2. Does the closed form agree with the engine?  (primary corpus, full=True)")
print("=" * 78)
os.environ["THEORIA_FIXED_TIME"] = "2026-07-29T00:00:00Z"
os.environ["THEORIA_DETERMINISTIC_IDS"] = "1"
prim = PF.sweep_corpus_a(PF.BASE_SEED, PF.N_WORLDS, full=True)
for k in sorted(prim):
    print("   %-34s %s" % (k, prim[k]))
ei, eb = expected((1, PF.MAX_HYP), (1, PF.MAX_ACTIONS), (1, PF.MAX_OBS),
                  PF.ZERO_COST_NUMERATOR / PF.ZERO_COST_DENOMINATOR)
print("   closed-form expectation for THIS recipe: inf=%.1f  bug=%.1f" % (ei, eb))
print("   primary draw z vs its own recipe:  inf %+0.2f   bug %+0.2f"
      % ((prim["infinity_rows"] - ei) / sd_binom(ei),
         (prim["zero_cost_bug"] - eb) / sd_binom(eb)))

# --------------------------------------------------------------------------
print()
print("=" * 78)
print("3. Replicate band -- 200 corpora, and where the primary + E11 sit")
print("=" * 78)
N_REP = 200
inf_vals, bug_vals = [], []
for r in range(N_REP):
    s = PF.sweep_corpus_a(PF.BASE_SEED + (r + 1) * PF.N_WORLDS, PF.N_WORLDS,
                          full=False)
    inf_vals.append(s["infinity_rows"])
    bug_vals.append(s["zero_cost_bug"])

for label, vals, prim_v, e11 in (
        ("infinity_rows", inf_vals, prim["infinity_rows"], 1633),
        ("zero_cost_bug", bug_vals, prim["zero_cost_bug"], 82)):
    m = statistics.mean(vals)
    sd = statistics.stdev(vals)
    print("%s: n=%d mean=%.1f sd=%.1f min=%d max=%d" %
          (label, N_REP, m, sd, min(vals), max(vals)))
    print("    primary(seed %d) = %d   z=%+0.2f   inside[min,max]=%s   pct_ge=%.1f%%"
          % (PF.BASE_SEED, prim_v, (prim_v - m) / sd,
             min(vals) <= prim_v <= max(vals),
             100.0 * sum(v >= prim_v for v in vals) / N_REP))
    print("    E11          = %d   z=%+0.2f   inside[min,max]=%s   pct_ge=%.1f%%"
          % (e11, (e11 - m) / sd, min(vals) <= e11 <= max(vals),
             100.0 * sum(v >= e11 for v in vals) / N_REP))
    print("    first 32 replicates: mean=%.1f sd=%.1f min=%d max=%d"
          % (statistics.mean(vals[:32]), statistics.stdev(vals[:32]),
             min(vals[:32]), max(vals[:32])))

# --------------------------------------------------------------------------
print()
print("=" * 78)
print("4. fuzzlab.worlds.hypset itself, 4000 worlds, via the same predicates")
print("=" * 78)
try:
    from fuzzlab.worlds import hypset
    from fuzzlab import prng
    from engines.probe_frontier.frontier import rank_probes

    def hypset_counts(seeds):
        inf = bug = 0
        for sd_ in seeds:
            w = hypset.generate(sd_)
            hyps = w.hypotheses()
            costs = w.cost_map()
            ranked = rank_probes(hyps, w.state, w.actions, costs=costs)
            some = any(v.splits for v in ranked)
            zero_splits = any(
                costs[a] == 0.0 and len({row[j] for row in w.spec.table}) > 1
                for j, a in enumerate(w.spec.actions))
            best = ranked[0] if ranked and ranked[0].splits else None
            if best is None and some:
                bug += 1
            if zero_splits:
                inf += 1
        return inf, bug

    for label, seeds in (
            ("seeds 0..3999", range(4000)),
            ("seeds 1..4000", range(1, 4001)),
            ("derive(0,'hypset',i) i<4000",
             [prng.derive(0, "hypset", i) for i in range(4000)]),
            ("BASE_SEED+i", [PF.BASE_SEED + i for i in range(4000)]),
    ):
        print("   %-32s -> inf=%4d  bug=%3d" % (label, *hypset_counts(seeds)))
except Exception as exc:                                        # pragma: no cover
    print("   hypset run failed: %r" % (exc,))
