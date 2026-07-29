"""Pairwise separation: which voter pairs each item actually tells apart,
on awarded points rather than on the binary `correct` label."""
import json
import os

HERE = os.path.dirname(__file__)
doc = json.load(open(os.path.join(HERE, "handbuilt_discrimination.json"),
                     encoding="utf-8"))
ORDER = ["heldout", "handover", "adaptation", "verdict", "handover_auto"]
PAIRS = [("oracle", "bluffer"), ("oracle", "memoriser"), ("memoriser", "bluffer")]

for name in ORDER:
    p = doc[name]
    print("== %s  (n=%d, %s pts)" % (name, p["n_items"], p["total_points"]))
    for a, b in PAIRS:
        sep = [i for i in p["items"]
               if abs(i["awarded"][a] - i["awarded"][b]) > 1e-9]
        print("   %-22s separated on %2d/%2d items, %.1f/%.1f points"
              % ("%s vs %s" % (a, b), len(sep), p["n_items"],
                 sum(i["points"] for i in sep), p["total_points"]))
    both_eq = [i for i in p["items"]
               if abs(i["awarded"]["memoriser"] - i["awarded"]["bluffer"]) < 1e-9]
    print("   memoriser==bluffer on %d items (%.1f pts)"
          % (len(both_eq), sum(i["points"] for i in both_eq)))

print()
print("### adaptation, item by item (partial credit)")
for i in sorted(doc["adaptation"]["items"], key=lambda x: x["item_id"]):
    print("  %-26s %-22s pts=%-5s O=%-5s M=%-6s B=%-6s cls=%s"
          % (i["item_id"], i["rubric_id"], i["points"], i["awarded"]["oracle"],
             i["awarded"]["memoriser"], i["awarded"]["bluffer"], i["class"]))

print()
print("### verdict, item by item")
for i in sorted(doc["verdict"]["items"], key=lambda x: x["item_id"]):
    t = i["truth"]
    print("  %-16s pts=%-4s O=%-4s M=%-5s B=%-5s cls=%-38s claim=%-11s "
          "size=%-6s cert=%s"
          % (i["item_id"], i["points"], i["awarded"]["oracle"],
             i["awarded"]["memoriser"], i["awarded"]["bluffer"], i["class"],
             t.get("claim"), t.get("board_size_class"),
             bool(t.get("certificate_blob"))))
