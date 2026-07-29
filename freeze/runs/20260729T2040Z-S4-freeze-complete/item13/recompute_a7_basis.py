"""Item #13, second basis: the A7 variance envelope.

freeze/STATS_RULES.md section 5 cites ONLY the campaign_*.json batch. But the
tree holds a SECOND, tracked, purpose-built variance envelope --
baseline-arms/runs/20260728T103135Z-a7/envelope.json -- whose RUN_STATE.md:19
says it exists to produce "the variance estimate Phase 4 needs to fix its
per-cell repeat count". That is item #13's own job. Section 5 does not cite it.

This script recomputes it from tracked blobs and runs the ar25 sensitivity that
section 5.3 could not run on the campaign batch (there, all four games shared one
contended window, so no clean contrast existed). Here a contrast DOES exist:
A7 formally excludes 3 ar25 cells as `degraded`, and those 3 cells are recorded
in the tracked append-only baseline-arms/out/campaign_cells.jsonl under
campaign="phase3-variance-envelope".

Run: python freeze/runs/20260729T2040Z-S4-freeze-complete/item13/recompute_a7_basis.py
"""
import hashlib
import json
import statistics as st
import subprocess

ENV = "baseline-arms/runs/20260728T103135Z-a7/envelope.json"
CELLS = "baseline-arms/out/campaign_cells.jsonl"


def blob(p):
    return subprocess.run(["git", "show", f"HEAD:{p}"],
                          capture_output=True, check=True).stdout


print("=" * 78)
print("0. PROVENANCE")
print("=" * 78)
head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                      text=True, check=True).stdout.strip()
print(f"HEAD = {head}")
be, bc = blob(ENV), blob(CELLS)
for p, b in [(ENV, be), (CELLS, bc)]:
    print(f"  {p}\n    sha256={hashlib.sha256(b).hexdigest()}  bytes={len(b)}")

env = json.loads(be.decode("utf-8"))
cells = [json.loads(l) for l in bc.decode("utf-8").splitlines() if l.strip()]

print()
print("=" * 78)
print("1. WHAT A7 EXCLUDED, AND WHY -- the tree's definition of `degraded`")
print("=" * 78)
print(json.dumps(env["excluded"], indent=2, ensure_ascii=False))
print(f"degrees_of_freedom = {env['degrees_of_freedom']}  "
      f"(= 9 cells - 3 games, ar25 already out)")

print()
print("=" * 78)
print("2. A7's WITHIN-CELL DISPERSION, AS RECORDED (ar25 EXCLUDED)")
print("=" * 78)
print(f"{'game':16} {'metric':22} {'n':>2} {'mean':>10} {'sd':>9} {'cv':>8}")
for g, gv in sorted(env["games"].items()):
    for m in ["actions_ok", "action_success_rate", "levels_completed",
              "usd_per_action"]:
        s = gv["stats"][m]
        cv = "null" if s["cv"] is None else f"{s['cv']:.4f}"
        print(f"{g:16} {m:22} {s['n']:2d} {s['mean']:10.4f} {s['sd']:9.4f} {cv:>8}")
print()
print("pooled within-cell CV (envelope.json:pooled_cv):")
for m, v in sorted(env["pooled_cv"].items()):
    print(f"  {m:22} {'null' if v is None else f'{v:.6f}'}")
print()
print("A7's own sizing recommendation (envelope.json:sizing):")
for m, s in sorted(env["sizing"].items()):
    print(f"  {m:22} " + "  ".join(f"{k}={s[k]}" for k in sorted(s)))

print()
print("=" * 78)
print("3. THE ar25 SENSITIVITY -- include vs exclude the 3 degraded cells")
print("=" * 78)
ar25 = [c for c in cells if c["game_id"].startswith("ar25")
        and c.get("campaign") == "phase3-variance-envelope"]
print(f"ar25 degraded cells recovered from {CELLS}: {len(ar25)}")
for c in ar25:
    print(f"  repeat={c['repeat']} actions_ok={c['actions_ok']:3d} "
          f"actions_failed={c['actions_failed']:2d} budget={c['budget']} "
          f"levels_completed={c['levels_completed']} outcome={c['outcome']:14} "
          f"started={c['started']}")
print()
print("cross-check: A7's envelope cells started 18:21:28Z; the campaign_*.json")
print("batch of section 5.2 started 18:19:36Z. Two distinct batches, as 5.2 says.")

ar25_ok = [c["actions_ok"] for c in ar25]
ar25_asr = [c["actions_ok"] / (c["actions_ok"] + c["actions_failed"]) for c in ar25]


def stats(v):
    m = st.mean(v)
    sd = st.stdev(v) if len(v) > 1 else 0.0
    return m, sd, (sd / m if m else float("nan"))


print()
print("--- per-game actions_ok, both ways ---")
print(f"{'game':16} {'n':>2} {'mean':>8} {'sd':>8} {'cv':>8}  standing")
rows_ex = []
for g, gv in sorted(env["games"].items()):
    s = gv["stats"]["actions_ok"]
    rows_ex.append((g, s["n"], s["mean"], s["sd"], s["cv"]))
    print(f"{g:16} {s['n']:2d} {s['mean']:8.3f} {s['sd']:8.3f} {s['cv']:8.4f}  included")
m, sd, cv = stats(ar25_ok)
print(f"{'ar25-0c556536':16} {len(ar25_ok):2d} {m:8.3f} {sd:8.3f} {cv:8.4f}  "
      f"EXCLUDED by A7 (degraded)")

print()
print("--- the decision variable, computed both ways ---")


def pooled_cv(groups):
    """sqrt(pooled within-group variance)/grand mean, the envelope's definition."""
    num = sum((len(v) - 1) * st.variance(v) for v in groups if len(v) > 1)
    den = sum(len(v) - 1 for v in groups)
    allv = [x for v in groups for x in v]
    return (num / den) ** 0.5 / st.mean(allv), den


# rebuild the three included games' raw repeats from the envelope
inc_ok = [[r["actions_ok"] for r in gv["repeats"]]
          for g, gv in sorted(env["games"].items())]
inc_asr = [[r["action_success_rate"] for r in gv["repeats"]]
           for g, gv in sorted(env["games"].items())]

for lab, groups_ok, groups_asr in [
        ("EXCLUDING ar25 (A7 main analysis, 9 cells, 3 games)", inc_ok, inc_asr),
        ("INCLUDING ar25 (pre-registered sensitivity, 12 cells, 4 games)",
         inc_ok + [ar25_ok], inc_asr + [ar25_asr])]:
    p_ok, df = pooled_cv(groups_ok)
    p_asr, _ = pooled_cv(groups_asr)
    wcvs = [st.stdev(v) / st.mean(v) for v in groups_ok if len(v) > 1]
    grand = [x for v in groups_ok for x in v]
    between = st.stdev([st.mean(v) for v in groups_ok]) / st.mean(grand)
    print(f"\n  {lab}")
    print(f"    cells                          : {len(grand)}   df={df}")
    print(f"    pooled within-cell CV actions_ok: {p_ok:.4f}")
    print(f"    pooled within-cell CV succ.rate : {p_asr:.4f}")
    print(f"    max within-game CV              : {max(wcvs):.4f}")
    print(f"    between-game CV of means        : {between:.4f}")
    print(f"    levels_completed (U3) variance  : 0.0  (floor: 0 in every cell)")
    print(f"    primary endpoints measured      : 0 of 3")
    print(f"    small-variance threshold 0.10   : "
          f"{'PASS (max wcv < 0.10)' if max(wcvs) < 0.10 else 'FAIL (max wcv >= 0.10)'}"
          f"   -- see STATS_RULES.s4draft.md:265-266 for where 0.10 comes from")

print()
print("=" * 78)
print("4. THE TWO TRACKED BASES DISAGREE -- and that is the finding")
print("=" * 78)
print(f"{'basis':44} {'cells':>6} {'pooled CV':>10} {'reads as':>12}")
print(f"{'campaign_*.json (section 5.2, 10-fail abort)':44} "
      f"{'48':>6} {'0.4915':>10} {'LARGE':>12}")
p_ok, _ = pooled_cv(inc_ok)
print(f"{'A7 envelope excl ar25 (30-action budget)':44} "
      f"{'9':>6} {p_ok:10.4f} {'SMALL':>12}")
p_ok2, _ = pooled_cv(inc_ok + [ar25_ok])
print(f"{'A7 envelope incl ar25 (sensitivity)':44} "
      f"{'12':>6} {p_ok2:10.4f} {'MIXED':>12}")
print()
print("Ratio between the two tracked estimates of the SAME quantity")
print(f"(within-cell dispersion of bare_cc on the dev pile): "
      f"0.4915 / {p_ok:.4f} = {0.4915/p_ok:.1f}x")
print()
print("Neither basis measures ANY of the three primary endpoints. On the one")
print("endpoint both do record -- levels_completed -- both are identically 0")
print("(48/48 and 9/9, and 12/12 with ar25 in). Sample variance 0 is a floor,")
print("not a small variance.")
print()
print("Theoria.md:368: 'variance small => n=1 defensible, otherwise n=2'.")
print(f"A {0.4915/p_ok:.0f}x disagreement between two tracked measurements of the")
print("same quantity is not 'variance small'. It is 'variance unknown'.")
print("'Otherwise' covers unknown. => n = 2, with and without ar25.")
print()
print("BUT NOTE WHAT DID FLIP, in section 3 above: on the A7 basis the SURROGATE")
print("dispersion test flips on ar25's inclusion --")
print("  excl ar25: max within-game CV 0.0370 < 0.10  => 'small' => n=1 defensible")
print("  incl ar25: max within-game CV 0.2756 >= 0.10 => 'not small' => n=2")
print("So any n argument resting on the CV number is FRAGILE: one game's standing")
print("decides it. The argument that does NOT flip is the endpoint argument --")
print("0 of 3 primary endpoints measured, levels_completed identically 0, in every")
print("subset of every basis. n=2 survives on that, and only on that.")
print()
print("Note also A7's own sizing says n_to_detect_25pct_difference = 3 for every")
print("metric it could size. No tracked basis anywhere argues for n=1.")
