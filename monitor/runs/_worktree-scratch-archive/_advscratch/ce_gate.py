"""Full-gate version of CASE1: does check_paper() RAISE LeakageError?"""
import json
from exam.leakage import check_paper
from exam.model import Item, Paper, LeakageError
import exam.leakage as L
print("leakage.py =", L.__file__)

UNIQ = ["zephyr","kumquat","obsidian","marzipan","trellis",
        "walrus","flotsam","gherkin","pumice","yardarm"]
rows  = [(f"ya{k}", ["alpha"], "yes") for k in range(5)]
rows += [(f"yb{k}", ["bravo"], "yes") for k in range(5)]
rows += [(f"nz{k}", [w], "no") for k, w in enumerate(UNIQ)]

items, ans = [], {}
for iid, tags, a in rows:
    items.append(Item(item_id=iid, rubric_id="r1", points=1.0,
                      paper={"board": "same-for-all-items"},
                      truth={"solvable": a == "yes"},
                      leak_probes=("nonexistent-probe-string",),
                      tags=tuple(tags)))
    ans[iid] = a
paper = Paper(paper_id="ce-gate", question_type="verdict",
              instructions="answer solvable yes/no", items=items)
sheet = paper.sheet("deadbeef", "deadbeef")
key_doc = paper.key("deadbeef")

try:
    rep = check_paper(paper, sheet, answer_of=ans, key_doc=key_doc)
    print("RESULT: GREEN (no LeakageError)")
    print("label_sets_checked:", rep.get("label_sets_checked"))
    print("metadata_unscored:", json.dumps(rep.get("metadata_unscored"), sort_keys=True))
except LeakageError as e:
    print("RESULT: RED -- LeakageError raised")
    print(str(e)[:600])
