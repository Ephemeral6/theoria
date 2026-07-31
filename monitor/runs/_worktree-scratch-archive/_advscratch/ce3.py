"""CASE3: the *floor_here* narrowing path -- scored subset has TWO distinct
answers, so `len(scored) >= 2` passes, and master still fires while v21 does not.
This path is NOT covered by the author's 'rate is 1.0 by arithmetic' argument.
"""
import json
from exam.leakage import metadata_hits
from exam.model import Item, Paper
import exam.leakage as L
print("leakage.py =", L.__file__)

def mk(rows, pid="ce3"):
    items, ans = [], {}
    for iid, tags, a in rows:
        items.append(Item(item_id=iid, rubric_id="r1", points=1.0,
                          paper={"board": "same"}, truth={"x": a},
                          leak_probes=("zzz",), tags=tuple(tags)))
        ans[iid] = a
    return Paper(paper_id=pid, question_type="verdict", instructions="i",
                 items=items), ans

UNIQ = ["zephyr","kumquat","obsidian","marzipan","trellis",
        "walrus","flotsam","gherkin","pumice","yardarm"]
rows = []
# bucket alpha: 10 yes + 1 no   -> per-bucket max 10 (yes)
for k in range(10): rows.append((f"pa{k}", ["alpha"], "yes"))
rows.append(("pa9x", ["alpha"], "no"))
# bucket bravo: 10 yes         -> per-bucket max 10 (yes)
for k in range(10): rows.append((f"pb{k}", ["bravo"], "yes"))
# 10 singleton buckets, answer "maybe": dilute the GROUP floor only
for k, w in enumerate(UNIQ): rows.append((f"ps{k}", [w], "maybe"))

paper, ans = mk(rows)
f = metadata_hits(paper, ans)
print("N FINDINGS =", len(f))
print(json.dumps(f, indent=2, sort_keys=True))
