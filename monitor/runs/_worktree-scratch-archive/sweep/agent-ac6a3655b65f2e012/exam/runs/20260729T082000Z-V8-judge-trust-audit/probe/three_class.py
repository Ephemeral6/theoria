"""V8 item (3): sensitivity and specificity of the three verdict classes, apart.

Throwaway probe. Builds p15-verdict-a2, submits one constant-answer examinee per
verdict class, and reports the 3x3 (truth class, answered class) matrix in raw
counts and in awarded/possible. Nothing here writes into tracked exam paths.
"""

from __future__ import annotations

import json
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, REPO)

from exam.grading.mark import mark                     # noqa: E402
from exam.grading.registry import digest               # noqa: E402
from exam.model import Submission                      # noqa: E402
from exam.papers import verdict as V                   # noqa: E402
from exam.grading import rubrics_verdict as RV         # noqa: E402

# The three verdict classes, read off rubrics_verdict.py: the two claims the
# rubric compares against truth["claim"], plus the abstain family.
CLASSES = ("solvable", "unsolvable", "abstain")

paper = V.build()
key_doc = paper.key(digest())
truth_of = {e["item_id"]: e["truth"] for e in key_doc["items"]}
points_of = {e["item_id"]: float(e["points"]) for e in key_doc["items"]}
ids = [e["item_id"] for e in key_doc["items"]]

out = {
    "paper_id": paper.paper_id,
    "rubric_digest": digest(),
    "n_items": len(ids),
    "total_points": round(sum(points_of.values()), 6),
    "abstain_tokens": sorted(RV._ABSTAIN),
    "search_reasons": sorted(RV._SEARCH_REASONS),
    "verdict_weight": RV.VERDICT_WEIGHT,
    "justification_weight": RV.JUSTIFICATION_WEIGHT,
}

# ground-truth census over the three verdict classes
census = {c: 0 for c in CLASSES}
pts = {c: 0.0 for c in CLASSES}
for i in ids:
    census[truth_of[i]["claim"]] = census.get(truth_of[i]["claim"], 0) + 1
    pts[truth_of[i]["claim"]] += points_of[i]
out["truth_census"] = {c: {"n": census[c], "points": round(pts[c], 6)} for c in CLASSES}

# item-class (i)/(ii)/(iii) census, for the decomposition
item_class = {}
for i in ids:
    item_class.setdefault(truth_of[i]["class"], []).append(i)
out["item_class_census"] = {k: len(v) for k, v in sorted(item_class.items())}

# ------------------------------------------------- constant-answer examinees
reports = {}
for c in CLASSES:
    sub = Submission(examinee_id="const-%s" % c, paper_id=paper.paper_id,
                     answers={i: {"claim": c} for i in ids},
                     capabilities=("answers",), meta={"probe": "v8-item3"})
    reports[c] = mark(key_doc, sub, axes_fn=getattr(V, "axes", None))

out["constant_totals"] = {
    c: {"awarded": reports[c].awarded, "possible": reports[c].possible,
        "fraction": reports[c].fraction}
    for c in CLASSES
}

# --------------------------------------------------------------- 3x3 matrix
matrix = {}
for truth_c in CLASSES:
    row = {}
    for said_c in CLASSES:
        rep = reports[said_c]
        cells = [s for s in rep.scores if truth_of[s.item_id]["claim"] == truth_c]
        awarded = round(sum(s.awarded for s in cells), 6)
        possible = round(sum(s.possible for s in cells), 6)
        paid = [s.item_id for s in cells if s.awarded > 0]
        row[said_c] = {
            "n_items": len(cells),
            "n_paid": len(paid),
            "n_refused": len(cells) - len(paid),
            "awarded": awarded,
            "possible": possible,
            "awarded_over_possible": round(awarded / possible, 6) if possible else None,
            "verdicts": sorted({s.verdict for s in cells}),
            "paid_items": sorted(paid),
        }
    matrix[truth_c] = row
out["matrix_3x3"] = matrix

# ------------------------------------------------ per-class sens / spec
rates = {}
for c in CLASSES:
    rep = reports[c]
    pos = [s for s in rep.scores if truth_of[s.item_id]["claim"] == c]
    neg = [s for s in rep.scores if truth_of[s.item_id]["claim"] != c]
    sens_num = sum(1 for s in pos if s.awarded > 0)
    spec_num = sum(1 for s in neg if s.awarded == 0)
    pos_aw = round(sum(s.awarded for s in pos), 6)
    pos_po = round(sum(s.possible for s in pos), 6)
    neg_aw = round(sum(s.awarded for s in neg), 6)
    neg_po = round(sum(s.possible for s in neg), 6)
    rates[c] = {
        "sensitivity_items": {
            "num": sens_num, "den": len(pos),
            "rate": round(sens_num / len(pos), 6) if pos else None,
            "undefined_because": None if pos else
                "no item on this paper has ground truth %r; the denominator is "
                "empty, so the cell is null and not zero" % c,
        },
        "sensitivity_points": {
            "awarded": pos_aw, "possible": pos_po,
            "rate": round(pos_aw / pos_po, 6) if pos_po else None,
        },
        "specificity_items": {
            "num": spec_num, "den": len(neg),
            "rate": round(spec_num / len(neg), 6) if neg else None,
        },
        "specificity_points_leaked": {
            "awarded": neg_aw, "possible": neg_po,
            "leak_rate": round(neg_aw / neg_po, 6) if neg_po else None,
        },
    }
out["per_class_rates"] = rates

# ------------------------------------- decomposition of constant-"unsolvable"
rep = reports["unsolvable"]
decomp = []
for s in sorted(rep.scores, key=lambda s: s.item_id):
    t = truth_of[s.item_id]
    decomp.append({
        "item_id": s.item_id,
        "truth_claim": t["claim"],
        "item_class": t["class"],
        "level_id": json.loads(t["level_blob"])["level_id"],
        "variant_id": t["spec"]["variant_id"],
        "points": points_of[s.item_id],
        "awarded": s.awarded,
        "verdict": s.verdict,
        "reason": s.detail.get("reason"),
        "verdict_points": s.detail.get("verdict_points"),
        "reason_points": s.detail.get("reason_points"),
        "search_credible": t.get("search_credible"),
        "state_space_lower_bound": t.get("state_space", {}).get("lower_bound"),
    })
out["constant_unsolvable_items"] = decomp
out["constant_unsolvable_summary"] = {
    "awarded": rep.awarded, "possible": rep.possible,
    "paid_items": sum(1 for d in decomp if d["awarded"] > 0),
    "paid_all_are_genuinely_unsolvable": all(
        d["truth_claim"] == "unsolvable" for d in decomp if d["awarded"] > 0),
    "reason_points_total": round(sum(d["reason_points"] or 0.0 for d in decomp), 6),
    "by_item_class": {
        k: {"n": len(v),
            "awarded": round(sum(d["awarded"] for d in decomp
                                 if d["item_class"] == k), 6),
            "possible": round(sum(points_of[i] for i in v), 6)}
        for k, v in sorted(item_class.items())},
}

# ---------------------------------- cross-check against the shipped instrument
from exam.grading.confusion_matrix import per_class_confusion  # noqa: E402
out["shipped_per_class_confusion_for_bluffer"] = per_class_confusion(
    reports["unsolvable"], key_doc)
out["shipped_axes_confusion_for_bluffer"] = reports["unsolvable"].axes.get("confusion")

# also the reference bluffer, to confirm it is the same examinee
bluff = V.reference_answers(paper, key_doc, "bluffer")
bsub = Submission(examinee_id="ref-bluffer", paper_id=paper.paper_id,
                  answers=bluff, capabilities=("answers",), meta={})
brep = mark(key_doc, bsub, axes_fn=getattr(V, "axes", None))
out["reference_bluffer"] = {"awarded": brep.awarded, "possible": brep.possible,
                            "identical_to_const_unsolvable":
                                brep.awarded == reports["unsolvable"].awarded}

# oracle, as the ceiling
osub_answers = V.reference_answers(paper, key_doc, "oracle")
osub = Submission(examinee_id="ref-oracle", paper_id=paper.paper_id,
                  answers=osub_answers, capabilities=("answers",), meta={})
orep = mark(key_doc, osub, axes_fn=getattr(V, "axes", None))
out["reference_oracle"] = {"awarded": orep.awarded, "possible": orep.possible}

path = os.path.join(os.path.dirname(__file__), "three_class.json")
with open(path, "w", encoding="utf-8", newline="\n") as h:
    json.dump(out, h, indent=2, sort_keys=False)
    h.write("\n")
print(json.dumps(out, indent=2)[:200])
print("wrote", path)
