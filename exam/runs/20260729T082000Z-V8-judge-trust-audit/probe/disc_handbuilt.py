"""V8 item (2): per-item discrimination over the FIVE hand-built papers.

Reuses `exam/tools/discrimination.py`'s voter design (oracle / memoriser /
bluffer; `null` excluded) but drives the hand-built builders, which take no
world argument and are therefore unreachable from that tool.

Adds one thing the worldgen tool does not need: the hand-built rubrics award
partial credit, so `verdict == "correct"` (fraction >= 1.0) is not the whole
story. Every item also carries the three voters' *awarded points*, and an item
only counts as strictly zero-discrimination when the three are byte-identical
in points as well as in verdict.
"""

from __future__ import annotations

import importlib
import json
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, REPO)

from exam.grading.mark import mark                     # noqa: E402
from exam.grading.registry import digest               # noqa: E402
from exam.guard import no_network                      # noqa: E402
from exam.model import Submission                      # noqa: E402

VOTERS = ("oracle", "memoriser", "bluffer")

MODULES = {
    "heldout": "exam.papers.heldout",
    "handover": "exam.papers.handover",
    "adaptation": "exam.papers.adaptation",
    "verdict": "exam.papers.verdict",
    "handover_auto": "exam.papers.handover_auto",
}


def _classify(correct):
    o, m, b = correct["oracle"], correct["memoriser"], correct["bluffer"]
    if o and m and b:
        return "free"
    if not o and not m and not b:
        return "dead"
    if o and m and not b:
        return "memorised"
    if o and not m and not b:
        return "theory"
    return "anomaly:oracle=%s,memoriser=%s,bluffer=%s" % (o, m, b)


def profile(name, modpath):
    module = importlib.import_module(modpath)
    paper = module.build()
    key_doc = paper.key(digest())
    axes_fn = getattr(module, "axes", None)

    verdicts, awarded, why = {}, {}, {}
    for mode in VOTERS:
        answers = module.reference_answers(paper, key_doc, mode)
        report = mark(key_doc, Submission(
            examinee_id="fake-%s" % mode, paper_id=paper.paper_id,
            answers=answers, capabilities=("answers",)), axes_fn=axes_fn)
        for s in report.scores:
            verdicts.setdefault(s.item_id, {})[mode] = s.verdict
            awarded.setdefault(s.item_id, {})[mode] = round(s.awarded, 6)
            why.setdefault(s.item_id, {})[mode] = s.detail.get("why")

    items = []
    for it in paper.items:
        iid = it.item_id
        correct = {m: verdicts[iid][m] == "correct" for m in VOTERS}
        pts = [awarded[iid][m] for m in VOTERS]
        items.append({
            "item_id": iid,
            "rubric_id": it.rubric_id,
            "points": it.points,
            "kind": it.paper.get("kind"),
            "tags": list(it.tags),
            "class": _classify(correct),
            "verdicts": dict(verdicts[iid]),
            "awarded": dict(awarded[iid]),
            "points_spread": round(max(pts) - min(pts), 6),
            "strict_zero": max(pts) - min(pts) < 1e-9,
            "why": {m: why[iid][m] for m in VOTERS},
            "truth": it.truth,
        })
    return {"paper": name, "paper_id": paper.paper_id,
            "question_type": paper.question_type,
            "n_items": len(items),
            "total_points": round(sum(i["points"] for i in items), 6),
            "items": items}


def main():
    with no_network():
        out = {name: profile(name, path) for name, path in MODULES.items()}
    dest = os.path.join(os.path.dirname(__file__), "handbuilt_discrimination.json")
    with open(dest, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    print("wrote", dest)
    for name, doc in out.items():
        counts = {}
        pts = {}
        for it in doc["items"]:
            counts[it["class"]] = counts.get(it["class"], 0) + 1
            pts[it["class"]] = round(pts.get(it["class"], 0.0) + it["points"], 6)
        print("%-14s n=%-4d pts=%-7s %s" % (name, doc["n_items"],
                                            doc["total_points"], counts))
        print("%-14s %s" % ("", pts))


if __name__ == "__main__":
    main()
