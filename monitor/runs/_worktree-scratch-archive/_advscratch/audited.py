import json, os
from exam.model import read_json
import exam.leakage as L
print("leakage.py =", L.__file__)
root = os.path.dirname(os.path.dirname(L.__file__))
lk = read_json(os.path.join(root, "exam", "artifacts", "leakage.json"))
for rep in lk["papers"]:
    print("=" * 66)
    print(rep.get("paper_id"), " n_items=", rep.get("n_items"))
    print("  label_sets_checked      :", rep.get("label_sets_checked"))
    print("  metadata_fields_checked :", rep.get("metadata_fields_checked"))
    uns = rep.get("metadata_unscored")
    if uns is None:
        print("  metadata_unscored       : ABSENT")
        continue
    for src, rows in sorted(uns.items()):
        tot = sum(r.get("scored_values", 0) for r in rows)
        print("    [%-18s] scored_values_total=%d %s" % (src, tot,
              [(r.get("field"), r.get("declined"), r.get("scored_values"),
                r.get("singleton_values")) for r in rows]))
