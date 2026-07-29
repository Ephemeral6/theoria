"""Apply the frozen rubrics to a submission.

The marker is deliberately dumb.  It looks up each item's rubric by id, hands it
(answer, truth, item), and collects the result.  It does not know which
question type it is marking, it does not see the examinee's identity beyond
copying it into the report, and it cannot reach the paper's world.  Everything
interesting lives in the rubrics, where it is hashed.

An item with no answer is `unanswered` and scores zero -- distinct from `wrong`,
because the difference matters: an arm with no deliverable scores zero on
handover by *having nothing to submit*, and that is a finding, not a failure to
answer.  An arm that answers "I cannot tell" is `abstained`, which some rubrics
pay for (a framework willing to say "unsolvable" must be able to shut up) and
others do not.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from ..model import (ExamError, Item, ItemScore, Report, Submission, VERDICTS,
                     unanswered)
from .registry import digest, rubric


def _items_from_key(key_doc: Dict[str, Any]) -> List[Item]:
    items = []
    for entry in key_doc["items"]:
        items.append(Item(item_id=entry["item_id"], rubric_id=entry["rubric_id"],
                          points=float(entry["points"]), paper={},
                          truth=entry["truth"], tags=tuple(entry.get("tags", ()))))
    return items


def mark(key_doc: Dict[str, Any], submission: Submission, *,
         axes_fn: Optional[Any] = None,
         meta: Optional[Dict[str, Any]] = None) -> Report:
    """Mark one submission against one answer key."""
    if submission.paper_id != key_doc["paper_id"]:
        raise ExamError(
            "submission is for paper %r but the key is for %r -- marking across "
            "papers would produce a number with no meaning"
            % (submission.paper_id, key_doc["paper_id"]))

    key_digest = key_doc.get("rubric_digest")
    now_digest = digest()
    items = _items_from_key(key_doc)

    scores: List[ItemScore] = []
    for item in items:
        if item.item_id not in submission.answers:
            scores.append(unanswered(item))
            continue
        answer = submission.answers[item.item_id]
        score = rubric(item.rubric_id).grade(answer, item.truth, item)
        if score.verdict not in VERDICTS:
            raise ExamError("rubric %r returned verdict %r, outside %s"
                            % (item.rubric_id, score.verdict, list(VERDICTS)))
        if score.awarded > score.possible + 1e-9:
            raise ExamError("rubric %r awarded %s of %s possible on %s"
                            % (item.rubric_id, score.awarded, score.possible,
                               item.item_id))
        scores.append(score)

    report_meta: Dict[str, Any] = {
        "capabilities": list(submission.capabilities),
        "submission_meta": dict(submission.meta),
        "rubric_digest_at_build": key_digest,
        "rubric_digest_at_marking": now_digest,
        "rubric_digest_matches": key_digest == now_digest,
    }
    if key_digest != now_digest:
        report_meta["warning"] = (
            "the rubric changed between building this paper and marking it. "
            "The mark may not be the mark that was promised; re-build the paper "
            "or explain the change before quoting this number.")
    if meta:
        report_meta.update(meta)

    report = Report(paper_id=key_doc["paper_id"],
                    examinee_id=submission.examinee_id,
                    question_type=key_doc["question_type"],
                    rubric_digest=now_digest,
                    scores=scores,
                    meta=report_meta)
    tag_of = {i.item_id: i.tags for i in items}
    report.axes = {"by_tag": report.by_tag(tag_of)}
    if axes_fn is not None:
        extra = axes_fn(report, key_doc, submission)
        if extra:
            report.axes.update(extra)
    return report


def confusion(report: Report, key_doc: Dict[str, Any], *,
              positive: str) -> Dict[str, Any]:
    """Sensitivity and specificity together, for any two-class question type.

    Theoria.md 1.11 insists these are scored as a pair: a framework that answers
    "unsolvable" to everything has perfect sensitivity and is worthless.  Both
    numbers, always, or neither.
    """
    truth_of = {e["item_id"]: e["truth"] for e in key_doc["items"]}
    tp = fp = tn = fn = 0
    abstain_pos = abstain_neg = 0
    illegible_pos = illegible_neg = 0
    for score in report.scores:
        truth = truth_of.get(score.item_id, {})
        actual = truth.get("claim") or truth.get("label")
        is_positive = (actual == positive)
        said = score.detail.get("said")
        if score.verdict == "abstained" or said in ("abstain", "unknown"):
            if is_positive:
                abstain_pos += 1
            else:
                abstain_neg += 1
            continue
        if said is None:
            # Not an abstention. `unanswered` lands here too, and so does a
            # `wrong` verdict whose answer the rubric could not parse -- and
            # folding the second into the abstention count let a submission of
            # garbage print the row of a submission that honestly declined.
            # Counted separately for the reason D-EX-006 gave for counting
            # abstentions separately: the difference is the finding.
            if is_positive:
                illegible_pos += 1
            else:
                illegible_neg += 1
            continue
        said_positive = (said == positive)
        if is_positive and said_positive:
            tp += 1
        elif is_positive:
            fn += 1
        elif said_positive:
            fp += 1
        else:
            tn += 1

    def _rate(num: int, den: int) -> Optional[float]:
        return round(num / den, 6) if den else None

    return {
        "positive_class": positive,
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "abstained_on_positive": abstain_pos,
        "abstained_on_negative": abstain_neg,
        "unclassified_on_positive": illegible_pos,
        "unclassified_on_negative": illegible_neg,
        "sensitivity": _rate(tp, tp + fn),
        "specificity": _rate(tn, tn + fp),
        "note": ("Sensitivity counts abstentions as neither -- an abstention is "
                 "not a wrong answer, but it is not a right one either, so it is "
                 "reported separately rather than folded into a rate. An answer "
                 "that was never submitted, or that the rubric could not read a "
                 "claim out of, is `unclassified` and is neither an abstention "
                 "nor a classification."),
    }
