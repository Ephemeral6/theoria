"""What does the gate's REPORT say on construction B, tree by tree?

A silent gate that publishes "I declined to score 4 of 6 tag values" is a
different object from a silent gate that publishes nothing. This prints the
whole report so the difference is visible.
"""
import json
import os
import sys

TREE = os.path.abspath(sys.argv[1])
sys.path.insert(0, TREE)
from exam.model import Item, Paper, LeakageError  # noqa: E402
from exam import leakage as L                     # noqa: E402

S, U = "solvable", "unsolvable"
ROWS = [(S, ["gold"]), (U, ["red", "blue"]), (S, ["silver"]),
        (U, ["blue", "green"]), (S, ["gold"]), (U, ["green", "red"]),
        (S, ["silver"]), (U, ["red", "blue", "green"])]
items = [Item(item_id="q%02d" % (j + 1), rubric_id="r", points=3.0,
              paper={"kind": "verdict", "question": "solvable?"},
              truth={"claim": a}, leak_probes=["zzp%d" % j], tags=t)
         for j, (a, t) in enumerate(ROWS)]
paper = Paper(paper_id="adv4-B", question_type="verdict", instructions="x",
              items=items)
answer_of = {it.item_id: a for it, (a, _) in zip(items, ROWS)}
print("### tree=%s" % os.path.basename(TREE))
try:
    rep = L.check_paper(paper, paper.sheet("d0" * 32, "d1" * 32),
                        key_doc=paper.key("d0" * 32), answer_of=answer_of)
    print("GATE SILENT. report keys: %s" % sorted(rep))
    for k in sorted(rep):
        if k in ("positional", "positional_derived"):
            continue
        print("  %s = %s" % (k, json.dumps(rep[k], sort_keys=True)[:1400]))
except LeakageError as e:
    print("GATE FIRES: %s" % str(e)[:400])
