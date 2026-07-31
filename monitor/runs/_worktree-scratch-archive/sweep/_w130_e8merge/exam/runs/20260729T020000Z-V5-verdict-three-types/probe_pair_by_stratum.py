"""F-1's evidence: the same four fakes, split by class and split by board size.

Run from the repo root:  python exam/runs/<this run>/probe_pair_by_stratum.py

Kept as an artefact rather than a scratch file because it is the measurement F-1
rests on, and a measurement whose script was thrown away is an assertion.
"""

from exam.grading.mark import mark
from exam.grading.registry import digest
from exam.model import Submission
from exam.papers import CALIBRATION_MODES, module_for


def pair_by(truth_of, scores, bucket_key):
    """(sensitivity, specificity, positive coverage, negative coverage) per bucket."""
    groups = {}
    for score in scores:
        key = truth_of.get(score.item_id, {}).get(bucket_key, "?")
        groups.setdefault(key, []).append(score)

    out = {}
    for key, group in sorted(groups.items()):
        tp = fp = tn = fn = abstain_pos = abstain_neg = 0
        for score in group:
            positive = truth_of[score.item_id]["claim"] == "unsolvable"
            said = score.detail.get("said")
            if score.verdict == "abstained" or said in (None, "abstain", "unknown"):
                abstain_pos += positive
                abstain_neg += not positive
                continue
            said_positive = (said == "unsolvable")
            if positive and said_positive:
                tp += 1
            elif positive:
                fn += 1
            elif said_positive:
                fp += 1
            else:
                tn += 1
        sens = round(tp / (tp + fn), 3) if (tp + fn) else None
        spec = round(tn / (tn + fp), 3) if (tn + fp) else None
        out[key] = (sens, spec,
                    "%d/%d" % (tp + fn, tp + fn + abstain_pos),
                    "%d/%d" % (tn + fp, tn + fp + abstain_neg))
    return out


def main():
    module = module_for("verdict")
    paper = module.build()
    key_doc = paper.key(digest())
    truth_of = {e["item_id"]: e["truth"] for e in key_doc["items"]}
    axes_fn = getattr(module, "axes", None)

    for mode in CALIBRATION_MODES:
        answers = module.reference_answers(paper, key_doc, mode)
        submission = Submission(
            examinee_id="fake-%s" % mode, paper_id=paper.paper_id,
            answers=answers, capabilities=() if mode == "null" else ("answers",))
        report = mark(key_doc, submission, axes_fn=axes_fn)
        print("%-10s score=%.4f" % (mode, report.fraction))
        print("   by class      :", pair_by(truth_of, report.scores, "class"))
        print("   by board size :", pair_by(truth_of, report.scores, "board_size_class"))


if __name__ == "__main__":
    main()
