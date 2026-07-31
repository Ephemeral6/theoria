"""Render the per-paper tables and the zero-discrimination item lists."""
import json
import os

HERE = os.path.dirname(__file__)
doc = json.load(open(os.path.join(HERE, "handbuilt_discrimination.json"),
                     encoding="utf-8"))

ORDER = ["heldout", "handover", "adaptation", "verdict", "handover_auto"]

for name in ORDER:
    p = doc[name]
    items = p["items"]
    n, tp = p["n_items"], p["total_points"]
    print("=" * 78)
    print("%s  (%s, %s)  n=%d  points=%s" % (name, p["paper_id"],
                                             p["question_type"], n, tp))
    classes = {}
    for it in items:
        c = it["class"]
        e = classes.setdefault(c, {"n": 0, "pts": 0.0})
        e["n"] += 1
        e["pts"] += it["points"]
    print("  %-52s %5s %7s %7s %7s" % ("class", "items", "item%", "points", "pt%"))
    for c in sorted(classes, key=lambda k: -classes[k]["pts"]):
        e = classes[c]
        print("  %-52s %5d %6.1f%% %7.1f %6.1f%%"
              % (c, e["n"], 100.0 * e["n"] / n, e["pts"], 100.0 * e["pts"] / tp))

    strict = [it for it in items if it["strict_zero"]]
    print("  --- strictly zero-discrimination (identical awarded points for all "
          "three voters): %d items, %.1f points (%.1f%% of paper) ---"
          % (len(strict), sum(i["points"] for i in strict),
             100.0 * sum(i["points"] for i in strict) / tp))
    for it in sorted(strict, key=lambda i: (-i["points"], i["item_id"])):
        print("      %-34s %-34s pts=%-5s cls=%-10s awarded=%s"
              % (it["item_id"], it["rubric_id"], it["points"], it["class"],
                 it["awarded"]["oracle"]))
    dead = [it for it in items if it["class"] == "dead"]
    if dead:
        print("  *** DEAD ITEMS: %d ***" % len(dead))
        for it in dead:
            print("      ", it["item_id"], it["rubric_id"], it["points"],
                  it["why"])
    anom = [it for it in items if it["class"].startswith("anomaly")]
    if anom:
        print("  --- anomaly triples: %d items, %.1f points ---"
              % (len(anom), sum(i["points"] for i in anom)))
        for it in sorted(anom, key=lambda i: i["item_id"]):
            print("      %-34s %-34s pts=%-5s %s"
                  % (it["item_id"], it["rubric_id"], it["points"],
                     it["class"].split(":")[1]))
    print()
