"""Construction B again, but through the FULL check_paper path: derived label
sets from the answer key as well as the declared one. Rules out 'v25 would have
caught it via a derived stratum'."""
import os, sys, json
sys.path.insert(0, os.getcwd())
from exam.model import LeakageError
from exam import leakage as L
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
B = import_module("opsm21-v25-probeB".replace("-", "_")) if False else None
# inline rebuild (module name has dashes)
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "opsm21-v25-probeB.py")).read().split("def main(")[0])
paper, answer_of = build_paper()
sheet = paper.sheet("d0"*16, "d1"*16)
key_doc = paper.key("d0"*16)
print("TREE:", os.path.basename(os.getcwd()))
print("derived label sets:", sorted(L.derive_label_sets(paper, key_doc)))
try:
    rep = L.check_paper(paper, sheet, answer_of=answer_of, key_doc=key_doc,
                        require_probes=False)
    print("check_paper: CLEAN (gate silent)")
    print("label_sets_checked:", rep.get("label_sets_checked"))
    mm = rep.get("metadata_multiplicity")
    if mm:
        print("multiplicity:", json.dumps(mm, sort_keys=True)[:500])
except LeakageError as e:
    print("check_paper: RAISED (gate fires)")
    print("  ", str(e)[:400])
