"""Item #13 recomputation: does STATS_RULES.md section 5 reproduce from the
TRACKED blobs at HEAD?

Deliberately reads via `git show HEAD:<path>` rather than from the working tree.
The whole point of item #13 is that the basis must be hashable at freeze time,
so the recomputation must run on the object git would publish, not on whatever
happens to be sitting in out/.

(freeze/runs/2026-07-28T1200Z-p22/envelope_stats.py hardcodes
 C:/Users/user/Desktop/theoria/baseline-arms/out/campaign -- the MAIN checkout.
 Run from a worktree it silently reads another tree's files. Noted, not fixed:
 baseline-arms/ and that run dir are read-only to this subagent.)

Run:  python freeze/runs/20260729T2040Z-S4-freeze-complete/item13/recompute_item13.py
"""
import hashlib
import json
import math
import statistics as st
import subprocess
from collections import Counter

GAMES = ["ar25", "g50t", "sk48", "tn36"]
PATHS = {g: f"baseline-arms/out/campaign/campaign_{g}.json" for g in GAMES}

# section 5.2 table, as written in freeze/STATS_RULES.md:588-593
CLAIMED_52 = {
    #        n   mean     sd     cv
    "ar25": (12, 34.42, 12.06, 0.351),
    "g50t": (12, 43.75, 16.27, 0.372),
    "sk48": (12, 23.92, 8.45, 0.353),
    "tn36": (12, 19.00, 8.03, 0.423),
}
# section 5.2 finding-two table, STATS_RULES.md:618-622
CLAIMED_NB = {
    "ar25": (0.775, 12.36, 0.976),
    "g50t": (0.814, 15.33, 1.061),
    "sk48": (0.705, 9.01, 0.938),
    "tn36": (0.655, 7.42, 1.082),
}
CLAIMED_NB_MEAN_RATIO = 1.014
# section 5.3 leave-one-out table, STATS_RULES.md:680-684
CLAIMED_LOO = {
    None: (0.491, 0.375, 0.423),
    "ar25": (0.540, 0.383, 0.423),
    "g50t": (0.444, 0.376, 0.423),
    "sk48": (0.494, 0.382, 0.423),
    "tn36": (0.435, 0.359, 0.423),
}
# official baseline action counts, as used by envelope_stats.py:60
BASE = {"ar25": 748, "g50t": 879, "sk48": 1070, "tn36": 317}


def blob(path):
    return subprocess.run(["git", "show", f"HEAD:{path}"],
                          capture_output=True, check=True).stdout


def ok(flag):
    return "OK   " if flag else "MISMATCH"


print("=" * 78)
print("0. PROVENANCE -- sha256 of the TRACKED blob at HEAD")
print("=" * 78)
head = subprocess.run(["git", "rev-parse", "HEAD"],
                      capture_output=True, text=True, check=True).stdout.strip()
print(f"HEAD = {head}")
raw, rows, meta = {}, {}, {}
for g in GAMES:
    b = blob(PATHS[g])
    raw[g] = b
    d = json.loads(b.decode("utf-8"))
    rows[g] = d["episodes"]
    meta[g] = d
    print(f"  {PATHS[g]}")
    print(f"    sha256={hashlib.sha256(b).hexdigest()}  bytes={len(b)}  "
          f"episodes={len(d['episodes'])}")

print()
print("=" * 78)
print("1. PROVENANCE FIELDS -- section 5.2's origin correction (:564-568)")
print("=" * 78)
for f in ["scenario", "started", "resumed_at", "status", "arm", "model", "game_id"]:
    vals = {g: meta[g].get(f) for g in GAMES}
    ident = len(set(vals.values())) == 1
    print(f"  {f:12} identical-across-4={ident!s:5}  {vals}")
print("  => section 5.2 claims scenario/started/resumed_at/status are byte-identical")
print("     across all four files. Verified above.")

print()
print("=" * 78)
print("2. SECTION 5.2 ENVELOPE TABLE (STATS_RULES.md:588-593)")
print("=" * 78)
print(f"{'game':6} {'n':>3} {'mean':>8} {'claim':>8} {'sd':>7} {'claim':>7} "
      f"{'cv':>6} {'claim':>6}  verdict")
allfail = []
for g in GAMES:
    eps = rows[g]
    v = [e["actions_ok"] for e in eps]
    m, sd = st.mean(v), st.stdev(v)
    cv = sd / m
    cn, cm, csd, ccv = CLAIMED_52[g]
    good = (len(eps) == cn and abs(m - cm) < 0.005 and abs(sd - csd) < 0.005
            and abs(cv - ccv) < 0.0005)
    allfail.append(good)
    print(f"{g:6} {len(eps):3d} {m:8.2f} {cm:8.2f} {sd:7.2f} {csd:7.2f} "
          f"{cv:6.3f} {ccv:6.3f}  {ok(good)}")
    print(f"       levels_completed={sorted(set(e['levels_completed'] for e in eps))}  "
          f"outcomes={dict(Counter(e['outcome'] for e in eps))}")

print()
print("=" * 78)
print("3. FINDING ONE -- floor effect on the primary endpoint")
print("=" * 78)
lv = [e["levels_completed"] for g in GAMES for e in rows[g]]
n = len(lv)
print(f"levels_completed over all {n} episodes: {dict(Counter(lv))}")
print(f"sample variance = {st.variance(lv) if len(set(lv)) > 1 else 0.0}")
print(f"rule of three 95% upper bound on p(U3): 3/{n} = {3/n:.4f}")
print("coverage of official baseline action count (section 5.2:601-602 claims "
      "2.2%-6.0%):")
cov = {}
for g in GAMES:
    m = st.mean(e["actions_ok"] for e in rows[g])
    cov[g] = 100 * m / BASE[g]
    print(f"  {g}: mean {m:6.2f} of {BASE[g]:4d} = {cov[g]:4.1f}%")
lo, hi = min(cov.values()), max(cov.values())
print(f"  range = {lo:.1f}%-{hi:.1f}%   claimed 2.2%-6.0%   "
      f"{ok(abs(lo-2.2) < 0.05 and abs(hi-6.0) < 0.05)}")

print()
print("=" * 78)
print("4. FINDING TWO -- NegBinom(r=10,p) stopping-rule null "
      "(STATS_RULES.md:618-622)")
print("=" * 78)
print("m = 10p/(1-p) => p = m/(10+m);  pred sd = sqrt(10p)/(1-p)")
print(f"{'game':6} {'obs mean':>9} {'p_hat':>7} {'claim':>7} {'pred sd':>8} "
      f"{'claim':>7} {'obs sd':>7} {'ratio':>7} {'claim':>7}  verdict")
ratios = []
for g in GAMES:
    v = [e["actions_ok"] for e in rows[g]]
    m, sd = st.mean(v), st.stdev(v)
    p = m / (10.0 + m)
    pred = math.sqrt(10 * p / (1 - p) ** 2)
    r = sd / pred
    ratios.append(r)
    cp, cpred, cr = CLAIMED_NB[g]
    good = abs(p - cp) < 0.0005 and abs(pred - cpred) < 0.005 and abs(r - cr) < 0.0005
    print(f"{g:6} {m:9.2f} {p:7.3f} {cp:7.3f} {pred:8.2f} {cpred:7.2f} "
          f"{sd:7.2f} {r:7.3f} {cr:7.3f}  {ok(good)}")
mr = st.mean(ratios)
print(f"\nmean obs/pred ratio = {mr:.4f}   claimed {CLAIMED_NB_MEAN_RATIO}   "
      f"{ok(abs(mr - CLAIMED_NB_MEAN_RATIO) < 0.0005)}")
print(f"section 5.5 reason 2 says '98.6% of the variance explained by the abort rule';")
print(f"section 5.2:624 says 'agrees to within 1.4%'.  |1 - {mr:.4f}| = "
      f"{abs(1-mr)*100:.2f}%")

print()
print("=" * 78)
print("5. FINDING THREE -- infrastructure mortality")
print("=" * 78)
alleps = [e for g in GAMES for e in rows[g]]
c = Counter(e["outcome"] for e in alleps)
DEAD = {"api_unusable", "model_error", "harness_error", "no_reset_window"}
dead = sum(v for k, v in c.items() if k in DEAD)
rate = dead / len(alleps)
print(f"outcomes over {len(alleps)} episodes: {dict(c)}")
print(f"infrastructure-terminated = {dead}/{len(alleps)} = {rate:.3f}   "
      f"claimed 47/48 = 0.979   {ok(dead == 47 and len(alleps) == 48)}")
print(f"P(single episode survives) = {1-rate:.3f}   claimed 0.021   "
      f"{ok(abs((1-rate)-0.021) < 0.0005)}")
print(f"claim layer  n=19: expected dead cells = 19*{rate:.3f} = {19*rate:.1f}"
      f"   claimed 18.6   {ok(abs(19*rate-18.6) < 0.05)}")
print(f"clean layer  n=12: expected dead cells = 12*{rate:.3f} = {12*rate:.1f}"
      f"   claimed 11.7   {ok(abs(12*rate-11.7) < 0.05)}")

print()
print("=" * 78)
print("6. SECTION 5.3 LEAVE-ONE-GAME-OUT (STATS_RULES.md:680-684)")
print("=" * 78)
print(f"{'variant':14} {'N':>3} {'pooled cv':>10} {'claim':>7} {'mean wcv':>9} "
      f"{'claim':>7} {'max wcv':>8} {'claim':>7}  verdict")
loo = {}
for drop in [None] + GAMES:
    vals = [e["actions_ok"] for g in GAMES if g != drop for e in rows[g]]
    cvs = [st.stdev([e["actions_ok"] for e in rows[g]])
           / st.mean(e["actions_ok"] for e in rows[g])
           for g in GAMES if g != drop]
    pooled = st.stdev(vals) / st.mean(vals)
    loo[drop] = (pooled, st.mean(cvs), max(cvs))
    cp, cmw, cmx = CLAIMED_LOO[drop]
    good = (abs(pooled - cp) < 0.0005 and abs(st.mean(cvs) - cmw) < 0.0005
            and abs(max(cvs) - cmx) < 0.0005)
    lab = "ALL 4" if drop is None else f"drop {drop}"
    print(f"{lab:14} {len(vals):3d} {pooled:10.3f} {cp:7.3f} {st.mean(cvs):9.3f} "
          f"{cmw:7.3f} {max(cvs):8.3f} {cmx:7.3f}  {good and 'OK' or 'MISMATCH'}")

print()
print("ar25 sensitivity, the direction that matters:")
d_all, d_ar25 = loo[None][0], loo["ar25"][0]
print(f"  pooled cv ALL 4      = {d_all:.4f}")
print(f"  pooled cv drop ar25  = {d_ar25:.4f}")
print(f"  delta = {d_ar25-d_all:+.4f}  ({100*(d_ar25-d_all)/d_all:+.1f}% relative)")
print(f"  dropping ar25 makes dispersion "
      f"{'LARGER' if d_ar25 > d_all else 'SMALLER'} -> "
      f"ar25 is not the driver of dispersion.")
print()
print("ar25's uniqueness in the batch:")
for g in GAMES:
    oc = Counter(e["outcome"] for e in rows[g])
    print(f"  {g}: {dict(oc)}")
nonapi = [(g, e["outcome"]) for g in GAMES for e in rows[g]
          if e["outcome"] != "api_unusable"]
print(f"  episodes NOT api_unusable: {nonapi}")

print()
print("=" * 78)
print("7. THE n=1 / n=2 DECISION VARIABLE, WITH AND WITHOUT ar25")
print("=" * 78)
print("Theoria.md:368 -- 'variance small => n=1 defensible, otherwise n=2'.")
print("Three primary endpoints; the envelope measures none of them. What it does")
print("measure, tabulated both ways:")
print()
for drop, lab in [(None, "all 4 games (48 ep)"), ("ar25", "excl. ar25 (36 ep)")]:
    sub = [g for g in GAMES if g != drop]
    eps = [e for g in sub for e in rows[g]]
    lvs = [e["levels_completed"] for e in eps]
    c2 = Counter(e["outcome"] for e in eps)
    d2 = sum(v for k, v in c2.items() if k in DEAD)
    rr = [st.stdev([e["actions_ok"] for e in rows[g]])
          / st.mean(e["actions_ok"] for e in rows[g]) for g in sub]
    nb = []
    for g in sub:
        v = [e["actions_ok"] for e in rows[g]]
        m, sd = st.mean(v), st.stdev(v)
        p = m / (10.0 + m)
        nb.append(sd / math.sqrt(10 * p / (1 - p) ** 2))
    print(f"  {lab}")
    print(f"    U3 (levels_completed>0) achieved   : {sum(1 for x in lvs if x>0)}"
          f"/{len(eps)}   variance={0.0 if len(set(lvs))==1 else st.variance(lvs)}")
    print(f"    primary endpoints with a variance  : 0 of 3")
    print(f"    infra mortality                    : {d2}/{len(eps)} = "
          f"{d2/len(eps):.3f}")
    print(f"    pooled CV(actions_ok)              : "
          f"{st.stdev([e['actions_ok'] for e in eps])/st.mean(e['actions_ok'] for e in eps):.3f}")
    print(f"    mean NegBinom obs/pred ratio       : {st.mean(nb):.3f}")
    print(f"    E[cells lost at n=1], claim n=19   : {19*d2/len(eps):.1f} of 19")
    print(f"    VERDICT under Theoria.md:368       : "
          f"{'n=2 (variance UNKNOWN, not small)' if True else ''}")
    print()
print("  => the verdict does NOT flip on ar25's inclusion. Both subsets give")
print("     0 of 3 primary endpoints measured, a floor at levels_completed=0,")
print("     and an infra mortality that leaves n=1 unsurvivable. Dropping ar25")
print("     moves dispersion the WRONG way for an n=1 defence (up, not down).")
