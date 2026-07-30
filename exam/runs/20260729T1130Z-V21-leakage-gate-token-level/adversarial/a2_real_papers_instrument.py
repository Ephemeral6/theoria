"""A2 -- does the A1 `continue` bug fire on the five shipped papers, and is the
`floor` contaminated across fields?

Re-implements `_metadata_hits_within`'s control flow with tracing, without
touching exam/leakage.py.  Reports, per paper / per derived label set / per
kind-group / per field:

  * whether `len(scored) < 2` fired -> token check SKIPPED for that field
  * the group floor vs the floor actually used by the token check
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

PAPERS = sorted(BUILDERS) + ["<handover_auto>"]


def build(qt):
    if qt == "<handover_auto>":
        from exam.papers import handover_auto
        return handover_auto.build()
    return module_for(qt).build()


def trace(labelled, answer_of, tolerance=0.90):
    """Mirror of _metadata_hits_within, instrumented."""
    out = []
    if len(labelled) < 4:
        return out
    alphabet = {answer_of[i.item_id] for i in labelled}
    if len(alphabet) < 2:
        return out
    majority = Counter(answer_of[i.item_id] for i in labelled).most_common(1)[0][1]
    group_floor = majority / len(labelled)
    floor = group_floor
    for field_name in leakage.METADATA_FIELDS:
        buckets = {}
        for item in labelled:
            value = item.sheet_side().get(field_name)
            if value is None:
                continue
            buckets.setdefault(canonical(value), Counter())[answer_of[item.item_id]] += 1
        if len(buckets) < 2:
            out.append((field_name, "constant-field", group_floor, floor, "token-check SKIPPED"))
            continue
        usable = {k: c for k, c in buckets.items() if sum(c.values()) > 1}
        skipped = False
        if len(usable) >= 2:
            seen = sum(sum(c.values()) for c in usable.values())
            scored = Counter()
            for counter in usable.values():
                scored.update(counter)
            if len(scored) < 2:
                out.append((field_name, "degenerate-subset", group_floor, floor,
                            "token-check SKIPPED (the A1 bug, since fixed)"))
                continue
            floor_here = scored.most_common(1)[0][1] / seen if seen else 0.0
            floor = max(floor, floor_here)
        out.append((field_name, "scored", group_floor, floor,
                    "token-check ran with floor=%.4f (group floor %.4f)"
                    % (floor, group_floor)))
    return out


for qt in PAPERS:
    paper = build(qt)
    key = paper.key(digest())
    sets = leakage.derive_label_sets(paper, key)
    print("=" * 78)
    print(paper.paper_id, "n_items=%d" % len(paper.items),
          "derived label fields:", sorted(sets))
    for source, labels in sorted(sets.items()):
        for group in leakage._by_answer_alphabet(paper, labels):
            kind = canonical(group[0].sheet_side().get("kind")) if group else "?"
            rows = trace(group, labels)
            for field_name, why, gf, fl, note in rows:
                flag = "  <<<" if "SKIPPED (the A1 bug, since fixed)" in note else ""
                contam = "  <<< FLOOR RAISED" if fl > gf + 1e-12 else ""
                print("  [%-22s] kind=%-28s n=%-3d %-7s %-18s %s%s%s"
                      % (source, kind[:28], len(group), field_name, why, note,
                         flag, contam))
