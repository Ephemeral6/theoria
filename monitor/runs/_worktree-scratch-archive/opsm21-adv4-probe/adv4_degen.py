"""For every sheet where master fires and v25 is silent, is master's finding
the degenerate one -- a scored subset containing only ONE answer class?

Replays the sheets by id from the sweep JSONL (no re-randomisation), rebuilds
them, and reports master's raw finding plus whether the subset it scored was
single-class.
"""
import json
import os
import sys

TREE = os.path.abspath(sys.argv[1])
sys.path.insert(0, TREE)
IDS = [int(x) for x in sys.argv[2].split(",")]

from exam.model import Item, Paper, LeakageError  # noqa: E402
from exam import leakage as L                     # noqa: E402

SRC = "C:/Users/user/AppData/Local/Temp/adv4_master.jsonl"
rows = {}
with open(SRC) as fh:
    for line in fh:
        d = json.loads(line)
        rows[d["id"]] = d

single_class = 0
multi_class = 0
for i in IDS:
    d = rows[i]
    items = [Item(item_id="q%02d" % (j + 1), rubric_id="r", points=3.0,
                  paper={"kind": "verdict", "question": "solvable?"},
                  truth={"claim": a}, leak_probes=["zzp%d" % j], tags=t)
             for j, (a, t) in enumerate(zip(d["ans"], d["tags"]))]
    items = [Item(item_id="q%02d" % (j + 1), rubric_id="r", points=3.0,
                  paper={"kind": "verdict", "question": "solvable?"},
                  truth={"claim": d["ans"][j]}, leak_probes=["zzp%d" % j],
                  tags=d["tags"][j]) for j in range(len(d["ans"]))]
    paper = Paper(paper_id="sw%05d" % i, question_type="verdict",
                  instructions="x", items=items)
    answer_of = {it.item_id: d["ans"][j] for j, it in enumerate(items)}
    hits = L.metadata_hits(paper, answer_of)
    for h in hits:
        vals = h.get("values", {})
        classes = set()
        for counter in vals.values():
            classes |= set(counter)
        deg = len(classes) < 2
        single_class += deg
        multi_class += not deg
        print("id=%-5d leaky=%-5s loo=%.3f base=%.3f | field=%s n=%s "
              "predicts=%s floor=%s | scored classes=%s %s"
              % (i, d["leaky"], d["loo"], d["base"], h.get("field"),
                 h.get("n"), h.get("predicts"), h.get("majority_floor"),
                 sorted(classes), "<-- DEGENERATE" if deg else ""))
print()
print("findings with a single-class scored subset : %d" % single_class)
print("findings with >=2 classes in the subset    : %d" % multi_class)
