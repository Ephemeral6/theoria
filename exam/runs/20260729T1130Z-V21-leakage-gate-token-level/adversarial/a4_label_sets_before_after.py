"""A4 -- verify STATUS.md's "3, 1, 2 and 4 ... against 0, 0, 2 and 3" and
"89 of 186 items", and judge every newly-derived label field.

Re-implements derive_label_sets with the *old* 60% floor and the *new*
MIN_LABELLED floor, without touching exam/leakage.py.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from exam import leakage
from exam.grading.registry import digest
from exam.model import canonical
from exam.papers import BUILDERS, module_for


def derive(paper, key_doc, mode):
    per_field, counts = {}, {}
    n_items = len(key_doc.get("items", ())) or 1
    for entry in key_doc.get("items", ()):
        truth = entry.get("truth")
        if not isinstance(truth, dict):
            continue
        for f, v in truth.items():
            if not isinstance(v, (str, bool, int, float)) or isinstance(v, float):
                continue
            per_field.setdefault(f, {})[entry["item_id"]] = canonical(v)
            counts.setdefault(f, set()).add(canonical(v))
    sheet_text_of = {i.item_id: canonical(i.sheet_side()) for i in paper.items}
    out, rejected = {}, {}
    for f, labels in per_field.items():
        alpha = counts[f]
        if len(alpha) < 2 or len(alpha) > leakage.MAX_LABEL_ALPHABET:
            rejected[f] = "alphabet=%d" % len(alpha)
            continue
        if mode == "old" and len(labels) < 0.6 * n_items:
            rejected[f] = "n_labelled=%d < 0.6*%d" % (len(labels), n_items)
            continue
        if mode == "new" and len(labels) < leakage.MIN_LABELLED:
            rejected[f] = "n_labelled=%d < 4" % len(labels)
            continue
        public = sum(1 for iid, lab in labels.items()
                     if lab.strip('"') in sheet_text_of.get(iid, ""))
        if public > 0.6 * len(labels):
            rejected[f] = "public on %d/%d" % (public, len(labels))
            continue
        out[f] = labels
    return out, rejected


def build(qt):
    if qt == "<handover_auto>":
        from exam.papers import handover_auto
        return handover_auto.build()
    return module_for(qt).build()


total = 0
for qt in sorted(BUILDERS) + ["<handover_auto>"]:
    paper = build(qt)
    key = paper.key(digest())
    old, _ = derive(paper, key, "old")
    new, rej = derive(paper, key, "new")
    total += len(paper.items) if qt != "<handover_auto>" else 0
    print("=" * 76)
    print("%-22s n_items=%d" % (paper.paper_id, len(paper.items)))
    print("  OLD (60%% floor): %d  %s" % (len(old), sorted(old)))
    print("  NEW (MIN_LABELLED=4): %d  %s" % (len(new), sorted(new)))
    added = sorted(set(new) - set(old))
    print("  ADDED: %s" % added)
    for f in added:
        labs = new[f]
        alpha = sorted({v for v in labs.values()})
        print("     + %-22s on %2d/%2d items, alphabet=%s"
              % (f, len(labs), len(paper.items), alpha))
    # what live library check_paper would actually derive
    live = leakage.derive_label_sets(paper, key)
    assert sorted(live) == sorted(new), (sorted(live), sorted(new))
print("=" * 76)
print("sum of the four BUILDERS papers' items:", total)
