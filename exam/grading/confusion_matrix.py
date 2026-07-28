"""灵敏度与特异度分开打分 -- the pair, split by the class that produced it.

`mark.confusion()` already refuses to blend sensitivity and specificity, and
`calibration` already asserts that the verdict bluffer shows 1.0 / 0.0.  What
neither does is say **where** a sensitivity came from, and on this paper that is
most of the information:

    (i)  small_unsolvable   exhaustive search answers correctly here.  A
                            complete searcher scores full marks for a reason
                            that does not transfer to any larger board.
    (ii) large_unsolvable   2^60 to 2^120 configurations.  Enumeration is out
                            of reach, so only an invariant can answer.
    (iii) solvable_hard     the false-positive trap, each with a computed
                            witness plan.

An arm that aces (i) and scores zero on (ii) has the **same headline
sensitivity** as an arm that reasons -- 1.0 against 1.0 -- because sensitivity
pools all nine unsolvable items regardless of which class they came from.  The
distinction between "I enumerated it" and "I proved it" is the entire reason
classes (i) and (ii) are separate classes, and a single blended rate hides it.
So the matrix splits the rate by class, and the split is the point.

**A rate with an empty denominator is `null`, never `0.0`.**  Class (i) contains
no solvable items, so specificity is not zero there, it is undefined; writing it
as zero would make an arm look as though it had failed a test it was never
given.  Every undefined cell carries the reason it is undefined, in the cell.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Sequence

from ..model import ANSWERS_DIR, Submission, canonical, read_json
from ..papers import CALIBRATION_MODES, module_for
from .mark import confusion, mark
from .registry import digest

#: The question type whose truth is two-valued.  Named rather than inferred:
#: the other three papers have graded answers, not classifications, and a
#: confusion matrix over them would be a category error dressed as a number.
QUESTION_TYPE = "verdict"

#: Which side of the two-class truth counts as positive.  `unsolvable` is the
#: positive class because the failure this paper exists to price is a framework
#: that likes declaring impossibility -- so a false *positive* is a wrong
#: impossibility claim, which is the direction that matters.
POSITIVE = "unsolvable"


def _rate(num: int, den: int) -> Optional[float]:
    return round(num / den, 6) if den else None


def per_class_confusion(report: Any, key_doc: Dict[str, Any], *,
                        positive: str = POSITIVE) -> Dict[str, Any]:
    """The pair, once overall and once per truth class.

    The class lives in the truth side of the key and never on the sheet, so
    this is a referee-side reading of a paper the examinee saw unlabelled.
    """
    truth_of = {e["item_id"]: e["truth"] for e in key_doc["items"]}
    buckets: Dict[str, List[Any]] = {}
    for score in report.scores:
        klass = truth_of.get(score.item_id, {}).get("class", "unclassified")
        buckets.setdefault(klass, []).append(score)

    def tally(scores: Sequence[Any]) -> Dict[str, Any]:
        tp = fp = tn = fn = 0
        abstain_pos = abstain_neg = 0
        for score in scores:
            truth = truth_of.get(score.item_id, {})
            actual = truth.get("claim") or truth.get("label")
            is_positive = (actual == positive)
            said = score.detail.get("said")
            if score.verdict == "abstained" or said in (None, "abstain", "unknown"):
                if is_positive:
                    abstain_pos += 1
                else:
                    abstain_neg += 1
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
        n_pos, n_neg = tp + fn + abstain_pos, tn + fp + abstain_neg
        cell: Dict[str, Any] = {
            "n": len(scores), "n_positive": n_pos, "n_negative": n_neg,
            "tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "abstained_on_positive": abstain_pos,
            "abstained_on_negative": abstain_neg,
            "sensitivity": _rate(tp, tp + fn),
            "specificity": _rate(tn, tn + fp),
            # A rate computed over answered items only is inflated by
            # abstention: an arm that abstains on everything it does not know
            # scores 1.0 on what is left. `mark.confusion` keeps abstentions
            # out of the denominator on purpose and says so, which is the right
            # call -- an abstention is not a wrong answer -- but it makes the
            # rate uninterpretable on its own. Coverage is the missing half:
            # how much of the class the rate was computed over. The memoriser
            # is the live case (see the run's MATRIX.md): sensitivity 1.000,
            # coverage 5/9, and pooled it is numerically indistinguishable
            # from ground truth.
            "coverage_positive": _rate(tp + fn, n_pos),
            "coverage_negative": _rate(tn + fp, n_neg),
        }
        if not n_pos:
            cell["sensitivity_undefined_because"] = (
                "this class contains no %s items, so there is nothing to be "
                "sensitive to. The cell is empty, not zero." % positive)
        if not n_neg:
            cell["specificity_undefined_because"] = (
                "this class contains only %s items, so specificity has an "
                "empty denominator. The cell is empty, not zero -- an arm "
                "cannot fail a test it was never given." % positive)
        return cell

    return {
        "positive_class": positive,
        "overall": tally(report.scores),
        "by_class": {k: tally(v) for k, v in sorted(buckets.items())},
        "note": "Sensitivity and specificity are reported side by side and "
                "never combined. An abstention counts toward neither rate and "
                "is carried in its own column.",
    }


def _submission(mode: str, paper_id: str, answers: Dict[str, Any]) -> Submission:
    caps = () if mode == "null" else ("answers",)
    return Submission(examinee_id="fake-%s" % mode, paper_id=paper_id,
                      answers=answers, capabilities=caps,
                      meta={"fake": mode,
                            "note": "a calibration examinee, not a real arm"})


def _real_submissions(paper_id: str) -> Dict[str, Submission]:
    """Any real submission sitting in `artifacts/answers/` for this paper.

    The fakes are what the marker is calibrated on; a real submission is what
    the matrix is *for*.  The cheater subagent's sheet-only claims land here and
    become a row like any other, which is the only way its 1.000 / 1.000 sits
    next to the oracle's where a reader can see them together.
    """
    out: Dict[str, Submission] = {}
    if not os.path.isdir(ANSWERS_DIR):
        return out
    prefix = "%s." % paper_id
    for name in sorted(os.listdir(ANSWERS_DIR)):
        if not (name.startswith(prefix) and name.endswith(".answers.json")):
            continue
        doc = read_json(os.path.join(ANSWERS_DIR, name))
        submission = Submission.from_json(doc)
        out[submission.examinee_id] = submission
    return out


def verdict_matrix(modes: Optional[Sequence[str]] = None, *,
                   include_real: bool = True) -> Dict[str, Any]:
    """Every examinee against every verdict class, both rates in every cell."""
    module = module_for(QUESTION_TYPE)
    paper = module.build()
    key_doc = paper.key(digest())
    axes_fn = getattr(module, "axes", None)

    classes: Dict[str, int] = {}
    for entry in key_doc["items"]:
        klass = entry["truth"].get("class", "unclassified")
        classes[klass] = classes.get(klass, 0) + 1

    submissions: Dict[str, Submission] = {}
    for mode in (modes or CALIBRATION_MODES):
        answers = module.reference_answers(paper, key_doc, mode)
        submissions[mode] = _submission(mode, paper.paper_id, answers)
    if include_real:
        submissions.update(_real_submissions(paper.paper_id))

    rows: Dict[str, Any] = {}
    for name, submission in submissions.items():
        report = mark(key_doc, submission, axes_fn=axes_fn)
        rows[name] = {
            "fraction": report.fraction,
            "awarded": report.awarded,
            "possible": report.possible,
            "is_fake": name in CALIBRATION_MODES,
            "pooled": confusion(report, key_doc, positive=POSITIVE),
            "split": per_class_confusion(report, key_doc),
        }

    return {
        "paper_id": paper.paper_id,
        "question_type": QUESTION_TYPE,
        "rubric_digest": digest(),
        "positive_class": POSITIVE,
        "class_sizes": dict(sorted(classes.items())),
        "class_meaning": {
            "small_unsolvable": "(i) exhaustive search answers correctly here, "
                                "possibly for a reason that does not transfer",
            "large_unsolvable": "(ii) 2^60 to 2^120 configurations; only an "
                                "invariant can answer",
            "solvable_hard": "(iii) the false-positive trap, each with a "
                             "computed witness plan",
        },
        "examinees": rows,
    }


def render_matrix(matrix: Dict[str, Any]) -> str:
    """The matrix as a table, with `--` wherever a denominator is empty."""
    classes = list(matrix["class_sizes"])
    lines: List[str] = []
    lines.append("# verdict — sensitivity / specificity, split by class")
    lines.append("")
    lines.append("paper `%s`, positive class `%s`, rubric digest `%s`"
                 % (matrix["paper_id"], matrix["positive_class"],
                    matrix["rubric_digest"][:12]))
    lines.append("")
    lines.append("Sizes: " + ", ".join("`%s` %d" % (k, v)
                                       for k, v in matrix["class_sizes"].items()))
    lines.append("")
    header = ["examinee", "score", "sens (pooled)", "spec (pooled)"]
    for klass in classes:
        header.append("sens · %s" % klass)
        header.append("spec · %s" % klass)
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "---|" * len(header))

    def cell(entry: Dict[str, Any], which: str) -> str:
        """`rate (answered/total)`. The rate alone is not a reading."""
        value = entry.get(which)
        if which == "sensitivity":
            answered, total = entry.get("tp", 0) + entry.get("fn", 0), entry.get("n_positive", 0)
        else:
            answered, total = entry.get("tn", 0) + entry.get("fp", 0), entry.get("n_negative", 0)
        if not total:
            return "--"
        if value is None:
            return "-- (0/%d)" % total
        return "%.3f (%d/%d)" % (value, answered, total)

    for mode, row in matrix["examinees"].items():
        pooled = row["split"]["overall"]
        cells = [("`%s`" % mode), "%.4f" % row["fraction"],
                 cell(pooled, "sensitivity"), cell(pooled, "specificity")]
        for klass in classes:
            entry = row["split"]["by_class"].get(klass, {})
            cells.append(cell(entry, "sensitivity"))
            cells.append(cell(entry, "specificity"))
        lines.append("| " + " | ".join(cells) + " |")

    lines.append("")
    lines.append("Each cell is `rate (answered / class size)`. **The rate alone "
                 "is not a reading**: abstentions are kept out of the "
                 "denominator, so an arm that abstains on everything it cannot "
                 "do scores 1.000 on what is left.")
    lines.append("")
    lines.append("`--` is an empty denominator, not a zero. Classes (i) and "
                 "(ii) hold no solvable items, so specificity is undefined "
                 "there; class (iii) holds no unsolvable items, so sensitivity "
                 "is undefined there. An arm cannot fail a test it was never "
                 "given, and writing those cells as `0.000` would say it had.")

    twins = collisions(matrix)
    if twins:
        lines.append("")
        lines.append("## Examinees this matrix cannot tell apart")
        lines.append("")
        for group, scores in twins:
            lines.append("* **%s** — every cell identical, scores %s."
                         % (", ".join("`%s`" % g for g in group),
                            ", ".join("%.4f" % s for s in scores)))
        lines.append("")
        lines.append("A pair of rates is not an instrument on its own. Where "
                     "two examinees collide here, the thing that separates "
                     "them is the score — which on this paper means the "
                     "certificate half of the rubric, not the claim half.")
    return "\n".join(lines) + "\n"


def collisions(matrix: Dict[str, Any]) -> List[Any]:
    """Examinees whose every rate is identical, and their differing scores.

    Reported rather than assumed away.  On the first run this found the pair
    that matters: `oracle` and the sheet-only cheater agree in every cell of
    the split, 1.000 / 1.000 throughout, and differ only in the score.  A
    reader who never saw the world is indistinguishable from ground truth on
    the pair alone.
    """
    signatures: Dict[str, List[str]] = {}
    for name, row in matrix["examinees"].items():
        cells = [row["split"]["overall"]["sensitivity"],
                 row["split"]["overall"]["specificity"]]
        for klass in sorted(matrix["class_sizes"]):
            entry = row["split"]["by_class"].get(klass, {})
            cells.extend([entry.get("sensitivity"), entry.get("specificity"),
                          entry.get("coverage_positive"),
                          entry.get("coverage_negative")])
        signatures.setdefault(canonical(cells), []).append(name)
    out = []
    for _signature, group in sorted(signatures.items()):
        if len(group) < 2:
            continue
        out.append((sorted(group),
                    [matrix["examinees"][g]["fraction"] for g in sorted(group)]))
    return out
