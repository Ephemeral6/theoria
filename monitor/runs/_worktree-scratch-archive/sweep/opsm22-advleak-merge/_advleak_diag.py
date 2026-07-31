"""Classify each 'master fires, merge silent' case without trusting either tree.

For every field master flagged, recompute from the raw corpus:
  * usable  = whole-value buckets holding >1 item   (both trees score only these)
  * scored  = the answer multiset inside those buckets
  * rate    = sum(bucket majority) / seen           (both trees)
  * floor   = group majority / len(group)           (master's comparison)
  * floor_h = max(floor, scored majority / seen)    (merge's comparison)
  * lift    = rate - scored_majority/seen           (informativeness of the field)

A suppression with lift > 0 is a real leak going quiet.  A suppression with
lift == 0 is a field that predicts nothing beyond the base rate.
"""
import json
import sys
from collections import Counter


def canon(v):
    return json.dumps(v, sort_keys=True, ensure_ascii=False)


def sheet_side(spec):
    return {"item_id": spec["item_id"], "points": spec["points"],
            "tags": list(spec["tags"]), "kind": spec["kind"], "board": "b"}


def analyse(case, fields):
    groups = {}
    for spec in case["items"]:
        groups.setdefault(canon(spec["kind"]), []).append(spec)
    out = []
    for gkey, group in groups.items():
        if len(group) < 4:
            continue
        answers = Counter(s["answer"] for s in group)
        if len(answers) < 2:
            continue
        floor = answers.most_common(1)[0][1] / len(group)
        for field in fields:
            buckets = {}
            for spec in group:
                val = sheet_side(spec).get(field)
                if val is None:
                    continue
                buckets.setdefault(canon(val), Counter())[spec["answer"]] += 1
            usable = {k: c for k, c in buckets.items() if sum(c.values()) > 1}
            if len(usable) < 2:
                continue
            correct = sum(c.most_common(1)[0][1] for c in usable.values())
            seen = sum(sum(c.values()) for c in usable.values())
            rate = correct / seen
            scored = Counter()
            for c in usable.values():
                scored.update(c)
            sub_floor = scored.most_common(1)[0][1] / seen
            floor_h = max(floor, sub_floor)
            master_fires = rate > 0.90 and rate > floor + 1e-9
            merge_fires = (len(scored) >= 2 and rate > 0.90
                           and rate > floor_h + 1e-9)
            if master_fires and not merge_fires:
                out.append({
                    "group_kind": gkey, "group_n": len(group), "field": field,
                    "rate": round(rate, 6), "floor_group": round(floor, 6),
                    "sub_floor": round(sub_floor, 6),
                    "floor_here": round(floor_h, 6),
                    "n_answers_in_scored_subset": len(scored),
                    "scored": dict(scored), "seen": seen,
                    "lift_over_scored_baseline": round(rate - sub_floor, 9),
                    "class": ("single-category-subset" if len(scored) < 2
                              else "floor-denominator"),
                })
    return out


def main():
    corpus = {c["id"]: c for c in json.load(open(sys.argv[1], encoding="utf-8"))}
    ids = sys.argv[2:]
    fields = ("points", "tags", "kind")          # master's METADATA_FIELDS
    tally = Counter()
    maxlift = 0.0
    for cid in ids:
        rows = analyse(corpus[cid], fields)
        print("== %s" % cid)
        for r in rows:
            tally[r["class"]] += 1
            maxlift = max(maxlift, r["lift_over_scored_baseline"])
            print("   ", json.dumps(r, sort_keys=True))
        if not rows:
            print("    (no whole-value suppression found -- look elsewhere)")
            tally["UNEXPLAINED"] += 1
    print()
    print("CLASS TALLY:", dict(tally))
    print("MAX lift over scored-subset baseline among suppressions:", maxlift)


if __name__ == "__main__":
    main()
