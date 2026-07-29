"""Partial-credit-aware view: what each voter actually earns, per item and per
rubric family, plus the reason each free item is free."""
import json
import os
import sys

HERE = os.path.dirname(__file__)
doc = json.load(open(os.path.join(HERE, "handbuilt_discrimination.json"),
                     encoding="utf-8"))
ORDER = ["heldout", "handover", "adaptation", "verdict", "handover_auto"]
VOTERS = ("oracle", "memoriser", "bluffer")

print("### voter totals (awarded / possible)")
for name in ORDER:
    p = doc[name]
    tot = {m: round(sum(i["awarded"][m] for i in p["items"]), 4) for m in VOTERS}
    print("  %-14s possible=%-7s %s   fractions=%s" % (
        name, p["total_points"], tot,
        {m: round(tot[m] / p["total_points"], 4) for m in VOTERS}))

print()
print("### items on which the theory-free bluffer earns FULL marks "
      "(free + the oracle=T/mem=F/bluff=T triple)")
for name in ORDER:
    p = doc[name]
    hit = [i for i in p["items"]
           if abs(i["awarded"]["bluffer"] - i["points"]) < 1e-9]
    print("  %-14s %d/%d items, %.1f/%.1f points (%.1f%%)"
          % (name, len(hit), p["n_items"],
             sum(i["points"] for i in hit), p["total_points"],
             100.0 * sum(i["points"] for i in hit) / p["total_points"]))

print()
print("### items on which the bluffer earns SOMETHING (partial credit counts)")
for name in ORDER:
    p = doc[name]
    hit = [i for i in p["items"] if i["awarded"]["bluffer"] > 1e-9]
    print("  %-14s %d/%d items, %.3f points earned of %.1f possible on them"
          % (name, len(hit), p["n_items"],
             sum(i["awarded"]["bluffer"] for i in hit),
             sum(i["points"] for i in hit)))

print()
print("### per-rubric breakdown: class counts and voter point totals")
for name in ORDER:
    p = doc[name]
    fams = {}
    for i in p["items"]:
        f = fams.setdefault(i["rubric_id"], {"n": 0, "pts": 0.0, "cls": {},
                                             "o": 0.0, "m": 0.0, "b": 0.0})
        f["n"] += 1
        f["pts"] += i["points"]
        c = i["class"].split(":")[0] if i["class"].startswith("anomaly") \
            else i["class"]
        c = "bluffer_free_memoriser_fails" if c == "anomaly" else c
        f["cls"][c] = f["cls"].get(c, 0) + 1
        f["o"] += i["awarded"]["oracle"]
        f["m"] += i["awarded"]["memoriser"]
        f["b"] += i["awarded"]["bluffer"]
    print("  %s" % name)
    for rid in sorted(fams):
        f = fams[rid]
        print("    %-36s n=%-3d pts=%-6s O=%-6.2f M=%-6.2f B=%-6.2f  %s"
              % (rid, f["n"], f["pts"], f["o"], f["m"], f["b"], f["cls"]))

print()
print("### heldout: is 'free' exactly 'frame does not change'?")
p = doc["heldout"]
mism = 0
for i in p["items"]:
    t = i["truth"]
    keys = sorted(t.keys())
    if "frame_after" not in t:
        print("   no frame_after; truth keys =", keys)
        break
else:
    pass
print("   truth keys sample:", sorted(p["items"][0]["truth"].keys()))
print("   tags sample:", p["items"][0]["tags"])
