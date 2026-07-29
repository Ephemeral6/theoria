"""How big a multiplicity lift does an innocent field produce?

F-2c is a new leak class and it needs a threshold. D-EX-011 records that three
exclusions were added to `metadata_hits` in response to false positives found
while wiring it up, because "a checker that cries wolf gets switched off, which
is the same failure as a checker that never runs". So the threshold here is
chosen against measurement rather than taste: this script prints the lift every
sheet-visible field of every paper produces, so the separation between the real
leak and the noise floor is visible before a number is written into the module.

Run from the repo root:
    PYTHONPATH=. python exam/runs/<this run>/probe_multiplicity_threshold.py
"""

from collections import Counter

from exam.grading.registry import digest
from exam.model import canonical
from exam.papers import BUILDERS, module_for


def flatten(node, prefix="", depth=0, out=None):
    """Every sheet-visible field, as path -> canonical value."""
    out = {} if out is None else out
    if depth > 4:
        return out
    if isinstance(node, dict):
        for key, value in node.items():
            path = "%s.%s" % (prefix, key) if prefix else str(key)
            out[path] = canonical(value)
            flatten(value, path, depth + 1, out)
    elif isinstance(node, list):
        out[prefix + "(len)"] = canonical(len(node))
    return out


def multiplicity_lift(fields, answer_of, field_name):
    """Accuracy of predicting the answer from `is this value unique on the sheet`."""
    values = {i: fields[i].get(field_name) for i in answer_of}
    if any(v is None for v in values.values()):
        return None
    counts = Counter(values.values())
    groups = {}
    for iid, answer in answer_of.items():
        groups.setdefault(counts[values[iid]] == 1, Counter())[answer] += 1
    if len(groups) < 2 or any(sum(c.values()) < 2 for c in groups.values()):
        return None            # one side empty or a single item: no rule to test
    hits = sum(c.most_common(1)[0][1] for c in groups.values())
    return hits / len(answer_of), {k: dict(v) for k, v in groups.items()}


def main():
    for question_type in BUILDERS:
        module = module_for(question_type)
        paper = module.build()
        key_doc = paper.key(digest())
        truth_of = {e["item_id"]: e["truth"] for e in key_doc["items"]}

        # Answer label: the two-valued verdict claim where there is one, else the
        # smallest-alphabet scalar truth field, which is the closest analogue.
        candidates = {}
        for iid, truth in truth_of.items():
            for name, value in truth.items():
                if isinstance(value, (str, bool, int)) and not isinstance(value, float):
                    candidates.setdefault(name, {})[iid] = canonical(value)
        usable = {n: v for n, v in candidates.items()
                  if len(v) == len(truth_of) and 2 <= len(set(v.values())) <= 6}
        if not usable:
            print("\n=== %s: no small-alphabet truth field ===" % question_type)
            continue

        for label_name, answer_of in sorted(usable.items()):
            floor = Counter(answer_of.values()).most_common(1)[0][1] / len(answer_of)
            fields = {i.item_id: flatten(i.sheet_side()) for i in paper.items}
            rows = []
            for field_name in sorted({f for d in fields.values() for f in d}):
                result = multiplicity_lift(fields, answer_of, field_name)
                if result is None:
                    continue
                accuracy, groups = result
                rows.append((accuracy - floor, accuracy, field_name, groups))
            rows.sort(reverse=True)
            print("\n=== %s / label=%s  n=%d floor=%.4f ==="
                  % (question_type, label_name, len(answer_of), floor))
            for lift, accuracy, field_name, groups in rows[:8]:
                print("  lift=%+.4f acc=%.4f  %-34s unique=%s repeated=%s"
                      % (lift, accuracy, field_name,
                         groups.get(True), groups.get(False)))
            if len(rows) > 8:
                print("  ... %d more fields, max remaining lift %+.4f"
                      % (len(rows) - 8, rows[8][0]))


if __name__ == "__main__":
    main()
