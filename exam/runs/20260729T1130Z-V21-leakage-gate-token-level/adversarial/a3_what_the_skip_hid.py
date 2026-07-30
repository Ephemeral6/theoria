"""A3 -- run the token check on the combination the A1 `continue` skips.

v11-handover-a0, label set `solvable`, kind-group `optimal_action`, field
`tags`.  `metadata_hits` never reaches `_token_hits_within` there.  Call it
directly and print what it would have said.
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from exam import leakage
from exam.grading.registry import digest
from exam.model import canonical
from exam.papers import handover_auto

paper = handover_auto.build()
sets = leakage.derive_label_sets(paper, paper.key(digest()))
labels = sets["solvable"]

for group in leakage._by_answer_alphabet(paper, labels):
    kind = canonical(group[0].sheet_side().get("kind"))
    if "optimal_action" not in kind:
        continue
    print("group kind =", kind, " n =", len(group))
    for it in group:
        print("   %-12s tags=%-46s -> %s"
              % (it.item_id, str(list(it.tags)), labels[it.item_id]))
    counts = Counter(labels[i.item_id] for i in group)
    floor = counts.most_common(1)[0][1] / len(group)
    print("   group floor =", floor, counts)
    print("   metadata_hits reports:",
          [h for h in leakage.metadata_hits(paper, labels)])
    print("   _token_hits_within (called directly, bypassing the skip):")
    for h in leakage._token_hits_within(group, labels, 0.90, "tags", floor):
        print("      ", h)
    print("   ...and with the *group* floor for every token, per field tags:")
    # show every token and its rate, scored or not
    carriers = {}
    for item in group:
        for tok in leakage.field_tokens(item.sheet_side().get("tags")):
            carriers.setdefault(tok, []).append(item)
    for tok, holders in sorted(carriers.items()):
        held = {i.item_id for i in holders}
        w = Counter(labels[i.item_id] for i in holders)
        wo = Counter(labels[i.item_id] for i in group if i.item_id not in held)
        if not w or not wo:
            rate = None
        else:
            rate = (w.most_common(1)[0][1] + wo.most_common(1)[0][1]) / len(group)
        print("      %-14s carried_by=%d rate=%s  with=%s without=%s"
              % (tok, len(holders), rate, dict(w), dict(wo)))
