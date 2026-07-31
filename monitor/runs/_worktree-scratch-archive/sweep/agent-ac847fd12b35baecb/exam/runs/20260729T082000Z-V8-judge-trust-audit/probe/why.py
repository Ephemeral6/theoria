"""Why is each bluffer-scoring item bluffer-scoring? Re-derive the cause per
paper from the truth, rather than asserting it."""
import importlib
import json
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, REPO)
HERE = os.path.dirname(__file__)
doc = json.load(open(os.path.join(HERE, "handbuilt_discrimination.json"),
                     encoding="utf-8"))

# ---- heldout: bluffer answers frame_before. Free iff nothing changes.
hp = importlib.import_module("exam.papers.heldout").build()
before = {i.item_id: i.paper["frame_before"] for i in hp.items}
split = {i.item_id: i.truth["split"] for i in hp.items}
event = {i.item_id: i.truth["event"] for i in hp.items}
rows = []
for it in doc["heldout"]["items"]:
    iid = it["item_id"]
    static = it["truth"]["frame_after"] == before[iid]
    rows.append((iid, it["class"], static, split[iid], event[iid]))
print("### heldout: class x (frame unchanged?)")
tab = {}
for _, c, s, sp, ev in rows:
    tab.setdefault((c, s), 0)
    tab[(c, s)] += 1
for k in sorted(tab, key=str):
    print("   %-52s unchanged=%-6s n=%d" % (k[0], k[1], tab[k]))
print("   bluffer-scoring == frame-unchanged? ",
      all((r[1] in ("free",) or r[1].startswith("anomaly")) == r[2] for r in rows))
print("   class x split:")
tab2 = {}
for _, c, s, sp, ev in rows:
    tab2.setdefault((c, sp), 0)
    tab2[(c, sp)] += 1
for k in sorted(tab2, key=str):
    print("      %-52s %-8s n=%d" % (k[0], k[1], tab2[k]))
print("   events on bluffer-scoring items:")
ev_tab = {}
for iid, c, s, sp, ev in rows:
    if s:
        ev_tab[ev] = ev_tab.get(ev, 0) + 1
print("     ", ev_tab)
print("   the 36 bluffer-scoring heldout item ids:")
print("     ", " ".join(sorted(r[0] for r in rows if r[2])))

# ---- handover: bluffer plays the modal answer per family.
hh = importlib.import_module("exam.papers.handover")
hpp = hh.build()
key = hpp.key(importlib.import_module("exam.grading.registry").digest())
bl = hh.reference_answers(hpp, key, "bluffer")
orc = hh.reference_answers(hpp, key, "oracle")
print()
print("### handover: bluffer's modal answer per family, and what it takes")
modal = {}
for i in hpp.items:
    modal.setdefault(i.paper["kind"], set()).add(bl[i.item_id])
print("   modal answers:", {k: sorted(v) for k, v in modal.items()})
hit = [i.item_id for i in hpp.items if bl[i.item_id] == orc[i.item_id]]
print("   items where modal == truth (%d):" % len(hit), " ".join(sorted(hit)))

# ---- handover_auto
ha = importlib.import_module("exam.papers.handover_auto")
hap = ha.build()
key2 = hap.key(importlib.import_module("exam.grading.registry").digest())
bl2 = ha.reference_answers(hap, key2, "bluffer")
orc2 = ha.reference_answers(hap, key2, "oracle")
print()
print("### handover_auto: fixed bluff string per kind")
print("   ", json.dumps(ha._BLUFF, indent=6, sort_keys=True))
hit2 = [i.item_id for i in hap.items if bl2[i.item_id] == orc2[i.item_id]]
print("   items where the fixed bluff == truth (%d):" % len(hit2),
      " ".join(sorted(hit2)))
