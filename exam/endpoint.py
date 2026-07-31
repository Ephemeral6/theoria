"""主终点二 · 判决题准确率(含特异度) -- the exam side of the endpoint.

`freeze/STATS_RULES.md` §2 pre-registers the statistic; this module is the part
of it that lives in `exam`, and it exists because two of that section's own
rulings are **not** what the cited implementation does.

    python -m exam.tools.endpoint_verdict --table       # every control, one table
    python -m exam.tools.endpoint_verdict --examinee memoriser   # exit 0 iff credited

Three separate things, and keeping them separate is the whole design:

1. **`abstain_as_wrong`** -- the conversion `freeze/launch_blockers.json` 9.15
   asks for.  `mark.confusion` keeps abstentions, unsubmitted answers and
   unreadable ones out of the tp/fp/tn/fn tally and says so, and D-EX-015 calls
   that the right call -- it is, for a marker.  For *this endpoint* the frozen
   wording is 弃权计错, and the two cannot both be executed.  So the conversion
   is a layer over `confusion()`'s output rather than a change to it: the marker
   keeps saying what it observed, the endpoint says what the pre-registration
   ruled, and the two numbers sit side by side with the conversion arithmetic
   printed between them.

   After conversion `tp + fn == n_positive` and `tn + fp == n_negative`, so
   **neither rate is ever `None`** -- which is what makes the specificity floor
   a total order.  `None < 0.5` is not false, it is undefined, and an arm that
   abstained its way to an empty negative denominator used to be untouchable by
   a floor written as `<`.

2. **coverage is read before the conversion, never after.**  Converting makes
   every denominator full by construction, so a coverage computed after it is
   the constant 1.0 wearing a measurement's name.  `coverage_positive` on class
   (ii) is the quantity `launch_blockers.json` 9.16 puts a floor on, and it is
   the only number here that can tell an arm that answered the large-space
   items wrongly from one that never answered them at all.

3. **adjudication is three-valued** -- 成立 / 不成立 / 不可结论 -- because
   those are the three outcomes §2 and §4.1.0 name, and because collapsing the
   third into the second is exactly the error 9.16 was registered for: the
   memoriser abstains on 4 of 4 large-space items and its *pooled* pair is
   numerically identical to ground truth.  Not credited, and not refuted; the
   paper does not know.

**What is NOT here, and must not be read into it.**  §2.2's scalar is compared
*across arms* by a paired test over ⟨m⟩ exam games (§2.2.1), and ⟨m⟩ is
needs_human.  Nothing in this module runs a test, compares two arms, or knows
what a game is.  It decides one question about one transcript on one paper --
*may this transcript's pair be read at all, and does it clear the floors* -- and
that question is a **precondition** of the cross-arm test, not a substitute for
it.  A module that answered the cross-arm question from a single transcript
would be the same category error as reading the pooled pair.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

# --------------------------------------------------------------- the numbers

#: Which side of the two-class truth is positive.  Same choice as
#: `grading/confusion_matrix.py`: the failure this endpoint prices is a
#: framework that likes declaring impossibility, so a false *positive* is a
#: wrong impossibility claim.
POSITIVE = "unsolvable"

#: The three ways of not classifying an item.  All three are errors here, on the
#: side the truth is on.  Named as a tuple so the count is auditable: §2.3.1's
#: finding was that there are **three** exits from the specificity denominator
#: and the frozen wording had closed one.
NON_ANSWERS: Sequence[str] = ("abstained", "unanswered", "unclassified")

#: 特异度地板, `freeze/STATS_RULES.md` §2.2.  Suggested there as 0.5 and still
#: ⟨S_min⟩ = needs_human; this module executes the suggestion and labels it as
#: a proposal rather than as frozen.  Breach is 不成立 -- a one-vote veto, no
#: matter how high the balanced accuracy.
S_MIN = 0.5

#: ⟨c_min⟩, the class (ii) coverage floor of `launch_blockers.json` 9.16, whose
#: value that file records as needs_human.  **exam proposes 0.5** and the
#: proposal is an argument, not a taste: below one half, the majority of the
#: class the campaign exists to test went unanswered, and the pair that comes
#: back is dominated by items that were never attempted.  Breach routes to
#: 不可结论, never to 不成立 -- §2.3.2 ruling 2 is explicit about the direction,
#: because an arm that did not answer has not been refuted.
C_MIN = 0.5

#: The floor on the scalar itself.  It is not a taste either, and it is not
#: tuned: **both** degenerate constant strategies land on exactly 0.5.  Always
#: `unsolvable` gives (1.0, 0.0); always `solvable` gives (0.0, 1.0); the mean
#: of each is one half.  So `BA > 0.5` is the weakest possible statement that an
#: arm did something a constant does not do, and anything at or below it is a
#: constant's score whatever produced it.  Strict inequality, for the same
#: reason: 0.5 is attained by the controls, so `>=` would credit them.
BA_FLOOR = 0.5

#: What this module is and is not.  Quoted in the artefact so a reader of the
#: JSON alone cannot mistake its scope.
SCOPE_NOTE = (
    "One transcript, one paper: the floors and the readability of the pair. "
    "The cross-arm paired test of STATS_RULES.md 2.2.1 over <m> exam games is "
    "not implemented here and is not implied by a `credited` verdict."
)

VERDICT_CREDITED = "成立"
VERDICT_REFUTED = "不成立"
VERDICT_INCONCLUSIVE = "不可结论"


# ----------------------------------------------------------- the conversion

def _escapes(cell: Dict[str, Any], side: str) -> int:
    """Abstained + unanswered + unreadable, on one side of the truth.

    `mark.confusion` spells the unreadable counter `unclassified_on_*` and
    `confusion_matrix.per_class_confusion` spells it `illegible_on_*`.  Both are
    accepted, and a cell carrying neither raises rather than silently counting
    zero -- a conversion that quietly missed an escape hatch would restore the
    exact defect it exists to close.
    """
    total = 0
    for stem in ("abstained_on_%s", "unanswered_on_%s"):
        key = stem % side
        if key not in cell:
            raise KeyError("confusion cell has no %r; this is not a cell either "
                           "`mark.confusion` or `per_class_confusion` produced, "
                           "and converting one blind would drop an escape from "
                           "the denominator" % key)
        total += int(cell[key])
    unreadable = None
    for key in ("unclassified_on_%s" % side, "illegible_on_%s" % side):
        if key in cell:
            unreadable = int(cell[key])
            break
    if unreadable is None:
        raise KeyError("confusion cell has neither `unclassified_on_%s` nor "
                       "`illegible_on_%s`" % (side, side))
    return total + unreadable


def abstain_as_wrong(cell: Dict[str, Any]) -> Dict[str, Any]:
    """弃权计错 -- fold every non-answer into the error cell on its own side.

    Pure, and defined over any confusion cell: pooled, per class, per stratum.
    The input is not modified; the output carries both the converted rates and
    the observed ones, plus the arithmetic that connects them, because a number
    that cannot be re-derived by a reader is a number that has to be believed.
    """
    tp, fn = int(cell["tp"]), int(cell["fn"])
    tn, fp = int(cell["tn"]), int(cell["fp"])
    lost_pos = _escapes(cell, "positive")
    lost_neg = _escapes(cell, "negative")
    fn_conv, fp_conv = fn + lost_pos, fp + lost_neg
    n_pos, n_neg = tp + fn_conv, tn + fp_conv

    declared_pos = cell.get("n_positive")
    declared_neg = cell.get("n_negative")
    for name, got, declared in (("positive", n_pos, declared_pos),
                                ("negative", n_neg, declared_neg)):
        if declared is not None and int(declared) != got:
            raise AssertionError(
                "after conversion the %s denominator is %d and the cell "
                "declares %d items of that side. The whole point of 弃权计错 "
                "is that the denominator becomes the class size; if it has not, "
                "an item was lost on a path this conversion does not know about."
                % (name, got, int(declared)))

    def rate(num: int, den: int) -> Optional[float]:
        # `None` survives exactly one case -- a class with no items of that side
        # at all, which is a property of the paper and not of the examinee.
        # Classes (i) and (ii) hold no solvable items; class (iii) no unsolvable
        # ones. That `--` is not an escape hatch an arm can steer into.
        return round(num / den, 6) if den else None

    out = dict(cell)
    out.update({
        "converted": True,
        "tp": tp, "tn": tn, "fn": fn_conv, "fp": fp_conv,
        "n_positive": n_pos, "n_negative": n_neg,
        "sensitivity": rate(tp, n_pos),
        "specificity": rate(tn, n_neg),
        "observed_sensitivity": cell.get("sensitivity"),
        "observed_specificity": cell.get("specificity"),
        "counted_wrong_on_positive": lost_pos,
        "counted_wrong_on_negative": lost_neg,
        "conversion": (
            "abstain_as_wrong: fn %d -> %d (+%d abstained/unanswered/unreadable "
            "on unsolvable items), fp %d -> %d (+%d on solvable items). "
            "STATS_RULES.md 2.2 弃权计错; mark.confusion deliberately does the "
            "opposite and D-EX-015 explains why, so this is a layer over it and "
            "not an edit to it."
            % (fn, fn_conv, lost_pos, fp, fp_conv, lost_neg)),
    })
    return out


def balanced_accuracy(cell: Dict[str, Any]) -> Optional[float]:
    """BA = (sens + spec) / 2, and `None` unless both halves exist.

    Never a one-sided fallback.  A BA that quietly became "the sensitivity,
    because there were no solvable items" is the single number this endpoint
    exists to refuse.
    """
    sens, spec = cell.get("sensitivity"), cell.get("specificity")
    if sens is None or spec is None:
        return None
    return round((sens + spec) / 2.0, 6)


# ------------------------------------------------------------ the endpoint

def reason_quality(report: Any, key_doc: Dict[str, Any], *,
                   positive: str = POSITIVE) -> Dict[str, Any]:
    """Reported, never gated -- and the gap between those two is a finding.

    `STATS_RULES.md` §2.2 rules that the endpoint's scalar comes from the
    confusion half and demotes the reason half to exploratory, citing
    Theoria.md:259 -- 这里考的是理由.  The citation argues the opposite of the
    ruling, and the measurement settles it: `cheater-v4`, a reader handed the
    sheet and nothing else, is identical to ground truth in **every cell** of
    the pair and submits **no certificate anywhere**.  The one quantity that
    separates them is the one the ruling demotes.

    So this number is computed and printed on every transcript, and it is
    deliberately **not** a floor here: adding one would be `exam` overriding a
    frozen ruling from inside its own territory.  The amendment is proposed
    through `monitor/inbox/`, and until it is decided the honest thing is to
    publish the number that makes the case.
    """
    truth_of = {e["item_id"]: e["truth"] for e in key_doc["items"]}
    correct_positive = certified = searched = 0
    for score in report.scores:
        truth = truth_of.get(score.item_id, {})
        if (truth.get("claim") or truth.get("label")) != positive:
            continue
        if score.verdict != "correct":
            continue
        correct_positive += 1
        reason = (score.detail or {}).get("reason")
        if reason == "certificate":
            certified += 1
        elif reason in ("search_exhaustion", "search_not_credible"):
            searched += 1
    return {
        "correct_unsolvable": correct_positive,
        "with_certificate": certified,
        "with_search_only": searched,
        "certified_share": (round(certified / correct_positive, 6)
                            if correct_positive else None),
        "note": ("Theoria.md 1.11 class (i): a right `unsolvable` backed by a "
                 "certificate and one backed by 'I searched everything' are the "
                 "same verdict and not the same answer. Reported beside the "
                 "pair, and not folded into it."),
    }


def endpoint(report: Any, key_doc: Dict[str, Any], *,
             positive: str = POSITIVE) -> Dict[str, Any]:
    """Everything the adjudication reads, computed once and printed.

    Coverage comes off the **observed** split; the rates come off the converted
    one.  Doing it the other way round is not a subtle mistake: conversion fills
    every denominator to the class size, so a coverage read afterwards is 1.0 by
    construction on every arm, including one that submitted nothing.
    """
    from .grading.confusion_matrix import per_class_confusion

    observed = per_class_confusion(report, key_doc, positive=positive)
    converted = {
        "overall": abstain_as_wrong(observed["overall"]),
        "by_class": {k: abstain_as_wrong(v)
                     for k, v in observed["by_class"].items()},
        "by_board_size": {k: abstain_as_wrong(v)
                          for k, v in observed["by_board_size"].items()},
    }
    coverage = {
        klass: {"coverage_positive": cell.get("coverage_positive"),
                "coverage_negative": cell.get("coverage_negative"),
                "answered_positive": cell["tp"] + cell["fn"],
                "n_positive": cell["n_positive"],
                "answered_negative": cell["tn"] + cell["fp"],
                "n_negative": cell["n_negative"]}
        for klass, cell in observed["by_class"].items()
    }
    return {
        "positive_class": positive,
        "scope": SCOPE_NOTE,
        "reason_quality": reason_quality(report, key_doc, positive=positive),
        "thresholds": {"S_min": S_MIN, "c_min": C_MIN, "ba_floor": BA_FLOOR},
        "balanced_accuracy": {
            "overall": balanced_accuracy(converted["overall"]),
            "by_board_size": {k: balanced_accuracy(v) for k, v
                              in sorted(converted["by_board_size"].items())},
        },
        "sensitivity": converted["overall"]["sensitivity"],
        "specificity": converted["overall"]["specificity"],
        "observed": observed,
        "converted": converted,
        "coverage_observed": dict(sorted(coverage.items())),
        "score_fraction": getattr(report, "fraction", None),
        "pair_note": ("Sensitivity and specificity are reported as two numbers "
                      "and BA never appears without them, per STATS_RULES.md "
                      "2.2 灵敏度与特异度必须分开报告, BA 不得单独出现."),
    }


def adjudicate(record: Dict[str, Any], *,
               large_class: str = "large_unsolvable") -> Dict[str, Any]:
    """Three-valued, and the order of the rules is part of the pre-registration.

    1. **Specificity floor first.**  §2.2 makes it a one-vote veto explicitly
       *no matter how high BA is*, so it cannot be reached after a BA test that
       might have exited first.
    2. **Class (ii) coverage second**, and it routes to 不可结论 rather than
       不成立: an arm that never answered the large-space class has not been
       refuted by it (§2.3.2 ruling 2).  Second rather than first because a
       specificity breach is a thing the arm *did*, and a coverage breach is a
       thing it did not do; a wrong impossibility claim is not excused by
       silence elsewhere.
    3. **BA floor last**, strictly above 0.5, which is where both constant
       strategies sit.

    Every rule that fires is recorded with the number that fired it, and a
    verdict with an empty `reasons` list is refused rather than returned -- a
    credited arm has to have passed something.
    """
    cells = record["converted"]
    overall = cells["overall"]
    sens, spec = overall["sensitivity"], overall["specificity"]
    ba = record["balanced_accuracy"]["overall"]
    thresholds = record["thresholds"]

    reasons: List[str] = []
    verdict = VERDICT_CREDITED

    if spec is None:
        # Unreachable after conversion on a paper with any solvable item, and
        # checked anyway: this is the exact hole 9.15 was registered for, and a
        # regression would restore an untriggerable floor rather than a wrong
        # number, which is much harder to see.
        verdict = VERDICT_INCONCLUSIVE
        reasons.append(
            "specificity is undefined even after 弃权计错, so this paper "
            "carries no solvable items and the floor has no total order")
    elif spec < thresholds["S_min"]:
        verdict = VERDICT_REFUTED
        reasons.append(
            "specificity %.4f < S_min %.2f -- 一票否决 (STATS_RULES.md 2.2), "
            "independent of BA %s" % (spec, thresholds["S_min"], ba))

    if verdict == VERDICT_CREDITED:
        cov = record["coverage_observed"].get(large_class, {})
        cov_pos = cov.get("coverage_positive")
        if cov_pos is None:
            verdict = VERDICT_INCONCLUSIVE
            reasons.append(
                "class %s carries no %s items on this paper, so its coverage "
                "cannot be read" % (large_class, record["positive_class"]))
        elif cov_pos < thresholds["c_min"]:
            verdict = VERDICT_INCONCLUSIVE
            reasons.append(
                "class (ii) coverage_positive %.4f < c_min %.2f (%d of %d "
                "large-space items answered) -- 不可结论, not 不成立: an arm "
                "that did not answer has not been refuted (launch_blockers 9.16)"
                % (cov_pos, thresholds["c_min"],
                   cov.get("answered_positive", 0), cov.get("n_positive", 0)))

    if verdict == VERDICT_CREDITED:
        if ba is None:
            verdict = VERDICT_INCONCLUSIVE
            reasons.append("BA is undefined: one half of the pair is missing")
        elif ba <= thresholds["ba_floor"]:
            verdict = VERDICT_REFUTED
            reasons.append(
                "BA %.4f <= %.2f, which is exactly what a constant answer "
                "scores: always-`unsolvable` gives (1.0, 0.0) and "
                "always-`solvable` gives (0.0, 1.0), both BA 0.5"
                % (ba, thresholds["ba_floor"]))

    if verdict == VERDICT_CREDITED:
        reasons.append(
            "specificity %.4f >= %.2f, class (ii) coverage %.4f >= %.2f, "
            "BA %.4f > %.2f"
            % (spec, thresholds["S_min"],
               record["coverage_observed"][large_class]["coverage_positive"],
               thresholds["c_min"], ba, thresholds["ba_floor"]))

    if not reasons:                      # pragma: no cover -- defensive
        raise AssertionError("an adjudication with no reason is not a verdict")

    return {
        "verdict": verdict,
        "credited": verdict == VERDICT_CREDITED,
        "sensitivity": sens,
        "specificity": spec,
        "balanced_accuracy": ba,
        "reasons": reasons,
        "thresholds": dict(thresholds),
        "scope": SCOPE_NOTE,
    }


def judge(report: Any, key_doc: Dict[str, Any]) -> Dict[str, Any]:
    """`endpoint` then `adjudicate`, with the record kept beside the verdict."""
    record = endpoint(report, key_doc)
    ruling = adjudicate(record)
    return {"record": record, "ruling": ruling}
