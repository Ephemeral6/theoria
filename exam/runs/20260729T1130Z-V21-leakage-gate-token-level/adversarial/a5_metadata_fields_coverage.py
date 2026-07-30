"""A5 -- METADATA_FIELDS = ("points","tags","kind") is not the set of fields on
the sheet.  Enumerate every sheet_side key on every shipped paper and say which
the metadata/token check never looks at.
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from exam import leakage
from exam.grading.registry import digest
from exam.model import canonical
from exam.papers import BUILDERS, module_for


def build(qt):
    if qt == "<handover_auto>":
        from exam.papers import handover_auto
        return handover_auto.build()
    return module_for(qt).build()


checked = set(leakage.METADATA_FIELDS)
for qt in sorted(BUILDERS) + ["<handover_auto>"]:
    paper = build(qt)
    keys = Counter()
    for it in paper.items:
        keys.update(it.sheet_side().keys())
    print("=" * 76)
    print(paper.paper_id, " n_items =", len(paper.items))
    for k, c in sorted(keys.items()):
        mark = "CHECKED  " if k in checked else "unchecked"
        # how discriminating is the field: distinct values / distinct tokens
        vals = {canonical(it.sheet_side().get(k)) for it in paper.items
                if k in it.sheet_side()}
        toks = set()
        for it in paper.items:
            toks |= leakage.field_tokens(it.sheet_side().get(k))
        print("   %-9s %-22s on %2d/%2d  distinct_values=%-4d distinct_tokens=%d"
              % (mark, k, c, len(paper.items), len(vals), len(toks)))
