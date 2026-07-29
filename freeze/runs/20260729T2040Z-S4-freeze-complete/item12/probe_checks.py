"""Scratch probe: the remaining cross-checks the budget table depends on.

Read-only. Kept so every figure in BUDGET_TABLE.md can be re-derived.
"""
import collections
import json
import math

POOL = "../../../../../proxy/var/spend_gate.jsonl"  # resolved below


def pool_path():
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    repo = here
    for _ in range(6):
        repo = os.path.dirname(repo)
        cand = os.path.join(repo, "proxy", "var", "spend_gate.jsonl")
        if os.path.exists(cand):
            return cand
    raise SystemExit("pool not found")


recs = [json.loads(l) for l in open(pool_path(), encoding="utf-8") if l.strip()]

# --- 1. haiku $/call cross-check against BUDGET_REPORT 13.1 ($0.0392) -------
haiku = [r for r in recs if r.get("kind") == "spend"
         and (r.get("detail") or {}).get("model") == "claude-haiku-4-5-20251001"]
placeholder = [r for r in haiku if r.get("unpriced")]
desk = [r for r in haiku if (r.get("detail") or {}).get("beat") == "theorize"
        and not r.get("unpriced")]
bare = [r for r in haiku if not r.get("unpriced")
        and (r.get("detail") or {}).get("beat") != "theorize"]
s = lambda rows: sum(float(r.get("usd") or 0) for r in rows)
print("haiku spend lines            n=%d  $%.4f" % (len(haiku), s(haiku)))
print("  of which unpriced ceiling  n=%d  $%.4f" % (len(placeholder), s(placeholder)))
print("  of which theorize desk     n=%d  $%.4f  mean $%.6f"
      % (len(desk), s(desk), s(desk) / len(desk)))
print("  bare_cc-shaped calls       n=%d  $%.4f  mean $%.6f   (13.1 says 0.0392)"
      % (len(bare), s(bare), s(bare) / len(bare)))

# --- 2. action ceiling: how much of it went to offline/pytest traffic ------
by_campaign = collections.defaultdict(int)
for r in recs:
    if r.get("kind") == "spend":
        by_campaign[r.get("campaign") or "?"] += int(r.get("actions") or 0)
test_like = {c: a for c, a in by_campaign.items()
             if ("pytest" in c or "mock" in c or "smoke" in c or "canary" in c)}
print()
print("pool actions total      %d" % sum(by_campaign.values()))
print("pool actions test-like  %d  (%.1f%%)"
      % (sum(test_like.values()),
         100 * sum(test_like.values()) / sum(by_campaign.values())))
for c, a in sorted(test_like.items(), key=lambda kv: -kv[1])[:8]:
    print("   %6d  %s" % (a, c))

# --- 3. BUDGET_REPORT 12.3 "587 actions" cross-check ----------------------
# cumulative pool actions as of the last phase3-variance-envelope record
last = max(r["seq"] for r in recs
           if r.get("campaign") == "phase3-variance-envelope")
cum = sum(int(r.get("actions") or 0) for r in recs
          if r.get("kind") == "spend" and r["seq"] <= last)
cum_usd = sum(float(r.get("usd") or 0) for r in recs
              if r.get("kind") == "spend" and r["seq"] <= last)
print()
print("as of seq %d (last envelope record): pool actions %d, pool $%.4f"
      % (last, cum, cum_usd))
print("   BUDGET_REPORT.md:643 says 587 actions / $10.5564")

# --- 4. n-feasibility, checking RES-1's arithmetic ------------------------
print()
q = 47 / 48
for n in (1, 2, 3, 64):
    print("q=%.6f n=%d  cell survival %.6f  live of 19 = %.4f  live of 12 = %.4f"
          % (q, n, 1 - q ** n, 19 * (1 - q ** n), 12 * (1 - q ** n)))
print("q=0.889 n=2  live of 19 = %.4f" % (19 * (1 - 0.889 ** 2)))
floor = 14 / 19
print("n needed for 14/19 at q=%.6f: %.2f -> %d"
      % (q, math.log(1 - floor) / math.log(q), math.ceil(math.log(1 - floor) / math.log(q))))
print("n=2 reaches 14/19 iff q <= %.4f" % ((1 - floor) ** (1 / 2)))
print("n=3 reaches 14/19 iff q <= %.4f" % ((1 - floor) ** (1 / 3)))
try:
    from scipy.stats import beta
    print("Clopper-Pearson 95%% for 47/48: [%.4f, %.4f]"
          % (beta.ppf(0.025, 47, 2), beta.ppf(0.975, 48, 1)))
except Exception as exc:
    print("scipy unavailable:", exc)

# --- 5. costs of the retry structure -------------------------------------
print()
for label, per_action, budget in (("haiku 30-act", 0.0435, 30),
                                  ("haiku S1", 0.0435, 672.4285714285714),
                                  ("opus 30-act", 0.1460, 30),
                                  ("opus S1", 0.1460, 672.4285714285714)):
    per_ep = per_action * budget
    for n, tag in ((2, "nominal n=2"), (64, "n=64 to reach 14/19")):
        eps = 19 * 3 * n
        print("%-12s %-20s %5d episodes  $%12.2f  (+18%% $%12.2f)"
              % (label, tag, eps, eps * per_ep, eps * per_ep * 1.18))
print()
for label, per_action, budget in (("haiku 30-act", 0.0435, 30),
                                  ("haiku S1", 0.0435, 672.4285714285714)):
    per_ep = per_action * budget
    live = 19 * (1 - q ** 2)
    print("%-12s cost per *live* cell at n=2: $%.2f  (19x2 episodes = $%.2f buys %.3f cells)"
          % (label, 19 * 2 * per_ep / live, 19 * 2 * per_ep, live))
