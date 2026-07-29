"""P-22: does the dev-pile envelope measure the ARM's variance or the ABORT RULE's?

Reads baseline-arms/out/campaign/campaign_*.json (48 episodes, 4 dev games x 12 reps,
arm=bare_cc, model=claude-haiku-4-5-20251001).  Untracked at time of writing.
"""
import json, glob, math, statistics as st
from collections import Counter

SRC = r"C:/Users/user/Desktop/theoria/baseline-arms/out/campaign"

rows = {}
for f in sorted(glob.glob(SRC + "/campaign_*.json")):
    g = f.split("campaign_")[-1][:-5]
    rows[g] = json.load(open(f, encoding="utf-8"))["episodes"]

print("=" * 78)
print("1. PER-GAME ENVELOPE")
print("=" * 78)
allok = []
for g, eps in rows.items():
    ok = [e["actions_ok"] for e in eps]; fa = [e["actions_failed"] for e in eps]
    cost = [e["cost_usd"] for e in eps]; lv = [e["levels_completed"] for e in eps]
    allok += ok
    print(f"{g}: n={len(eps)}  ok mean={st.mean(ok):6.2f} sd={st.stdev(ok):5.2f} "
          f"cv={st.stdev(ok)/st.mean(ok):.3f} | failed={sorted(set(fa))} "
          f"| levels={sorted(set(lv))} | cost cv={st.stdev(cost)/st.mean(cost):.3f}")
    print(f"       outcomes={dict(Counter(e['outcome'] for e in eps))}")

print()
print("=" * 78)
print("2. IS THE VARIANCE THE ABORT RULE? -- negative-binomial null")
print("=" * 78)
print("Abort rule: bare_cc.play() stops at actions_failed >= 10 (CUMULATIVE).")
print("If each action independently succeeds w.p. p, then #successes before the")
print("10th failure ~ NegBinom(r=10,p):  mean=10p/(1-p),  var=10p/(1-p)^2.")
print("Fit p from the observed MEAN only, then PREDICT the sd and compare.\n")
print(f"{'game':6} {'obs mean':>9} {'p_hat':>7} {'pred sd':>8} {'obs sd':>7} {'obs/pred':>9}")
ratios = []
for g, eps in rows.items():
    ok = [e["actions_ok"] for e in eps]
    m = st.mean(ok); sd = st.stdev(ok)
    p = m / (10.0 + m)                 # m = 10p/(1-p)  =>  p = m/(10+m)
    pred = math.sqrt(10 * p / (1 - p) ** 2)
    ratios.append(sd / pred)
    print(f"{g:6} {m:9.2f} {p:7.3f} {pred:8.2f} {sd:7.2f} {sd/pred:9.3f}")
print(f"\nmean obs/pred ratio = {st.mean(ratios):.3f}  (1.000 = variance FULLY explained")
print("by the stopping rule; >>1 = genuine excess arm variance)")

print()
print("=" * 78)
print("3. THE PRIMARY ENDPOINT (U3 = level completed) HAS NO VARIANCE TO MEASURE")
print("=" * 78)
lv = [e["levels_completed"] for eps in rows.values() for e in eps]
n = len(lv); wins = sum(1 for x in lv if x > 0)
print(f"levels_completed over all {n} episodes: {dict(Counter(lv))}")
print(f"U3 achieved in {wins}/{n} episodes.  Sample variance = 0 -- but this is a")
print("FLOOR effect, not low variance.")
print(f"Rule of three 95% upper bound on p(U3) for bare_cc: p <= 3/{n} = {3/n:.4f}")
print("Coverage of the official baseline action count actually reached:")
BASE = {"ar25": 748, "g50t": 879, "sk48": 1070, "tn36": 317}
for g, eps in rows.items():
    m = st.mean(e["actions_ok"] for e in eps)
    print(f"  {g}: mean {m:5.1f} actions of {BASE[g]:4d} baseline = {100*m/BASE[g]:4.1f}%")

print()
print("=" * 78)
print("4. LEAVE-ONE-GAME-OUT  (ar25 = the contention-degraded game, INC-BA-003)")
print("=" * 78)
for drop in [None] + list(rows):
    vals = [e["actions_ok"] for g, eps in rows.items() if g != drop for e in eps]
    cvs = [st.stdev([e["actions_ok"] for e in eps]) / st.mean(e["actions_ok"] for e in eps)
           for g, eps in rows.items() if g != drop]
    lab = "ALL 4 games" if drop is None else f"drop {drop}"
    print(f"{lab:14} N={len(vals):2d}  pooled cv={st.stdev(vals)/st.mean(vals):.3f}  "
          f"mean within-game cv={st.mean(cvs):.3f}  max={max(cvs):.3f}")

print()
print("=" * 78)
print("5. WHAT n BUYS: the pairing unit is the GAME, not the episode")
print("=" * 78)
print("Sealed pile = 21 games => 21 paired observations REGARDLESS of n.")
print("n only shrinks within-cell noise by sqrt(n); it adds no degrees of freedom.\n")
print("Exact two-sided sign test, k discordant pairs all favouring one arm:")
for k in range(3, 12):
    print(f"  k={k:2d}  p = 2*0.5^{k} = {2*0.5**k:.5f}" + ("   <- first k with p<0.05" if k == 6 else ""))
print("\n=> U3 endpoint needs Theoria to win >= 6 sealed games that bare_cc loses.")

print()
print("=" * 78)
print("6. INFRASTRUCTURE MORTALITY -- the real argument for n>=2")
print("=" * 78)
alleps = [e for eps in rows.values() for e in eps]
c = Counter(e["outcome"] for e in alleps)
dead = sum(v for k, v in c.items() if k in
           {"api_unusable", "model_error", "harness_error", "no_reset_window"})
print(f"outcomes over {len(alleps)} episodes: {dict(c)}")
print(f"infrastructure-terminated: {dead}/{len(alleps)} = {dead/len(alleps):.3f}")
print(f"P(a single episode survives to a substantive outcome) = {1-dead/len(alleps):.3f}")
print(f"With n=1, expected sealed cells lost to infrastructure = "
      f"21 * {dead/len(alleps):.3f} = {21*dead/len(alleps):.1f} of 21 per arm.")
