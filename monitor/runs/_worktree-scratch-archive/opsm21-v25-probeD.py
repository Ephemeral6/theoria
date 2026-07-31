"""CONSTRUCTION D: V21's genuine gain -- a shared token inside per-item-unique
values. Pure synthetic; no game data, no sealed pile, no network."""
import os, sys, json
sys.path.insert(0, os.getcwd())
from exam.model import Item, Paper, LeakageError
from exam import leakage as L
ANS = {0:"alive",1:"dead",2:"alive",3:"dead",4:"alive",5:"dead",6:"alive",7:"dead"}
items=[]
for i in range(8):
    tags=["slot%02d"%i]+(["dead"] if ANS[i]=="dead" else [])
    items.append(Item(item_id="q%02d"%i, rubric_id="r", points=3.0,
                      paper={"kind":"verdict","question":"alive or dead?"},
                      truth={"claim":ANS[i]}, leak_probes=["p%02d"%i], tags=tags))
paper=Paper(paper_id="ctor-token-d", question_type="verdict",
            instructions="alive or dead", items=items)
answer_of={it.item_id:ANS[i] for i,it in enumerate(items)}
print("TREE:", os.path.basename(os.getcwd()))
hits=L.metadata_hits(paper, answer_of)
print("metadata_hits fired  :", bool(hits))
for h in hits:
    print("   ", json.dumps({k:v for k,v in sorted(h.items()) if k!="values"}, sort_keys=True))
try:
    L.check_paper(paper, paper.sheet("d0"*16,"d1"*16), answer_of=answer_of, require_probes=False)
    print("check_paper          : CLEAN (gate silent)")
except LeakageError as e:
    print("check_paper          : RAISED LeakageError (gate fires)")
