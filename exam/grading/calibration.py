"""Calibrate the marker before it marks anything real.

An exam is two instruments in a trenchcoat: a question-setter and a marker.  The
question-setter can be checked by reading it.  The marker cannot -- a marking
bug produces a plausible number, and a plausible number is indistinguishable
from a result.  So the marker is run first against examinees whose scores are
known *before* the run, and it has to reproduce them.

Four fakes, each pinning a different way the marker could be wrong:

    oracle      answers from ground truth.  Must score exactly 1.0.  Anything
                less means the rubric rejects a correct answer -- the marker is
                stricter than the truth, and every real score is depressed by an
                unknown amount.

    null        submits nothing.  Must score exactly 0.0, with every item
                `unanswered` rather than `wrong`.  Anything more means the
                marker pays for silence, and every real score is inflated.  It
                doubles as the bare-CC arm, which has no deliverable to submit
                (Theoria.md 1.11: "CC 无物可交记零") -- a zero the code derives
                rather than a zero someone wrote down.

    memoriser   perfect on what it has already seen, useless off it.  This is
                the arm 1.11 is built to catch: "重放是对过去的预测,背题也能
                满分".  A held-out paper that cannot separate it from `oracle`
                is not testing rules, it is testing recall, and the separation
                has to be *measured* rather than assumed.

    bluffer     one confident answer everywhere.  Perfect sensitivity, no
                specificity.  A verdict paper that scores it well is scoring
                confidence.

The expectations below are **pre-registered**: bands written down as part of the
protocol, not fitted to what the fakes turned out to score.  Where a band is
wide it is because the exact value depends on item mix and the protocol does not
want to pin item mix; where it is exact (`oracle`, `null`) it is because the
value follows from construction and any deviation is a bug.

**A failed calibration blocks real grading.**  `assert_calibrated` raises, and
`exam.tools.run_exam` calls it before it will mark a submitted answer file.  An
uncalibrated marker's output is not a low-confidence result, it is not a result.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ..model import ExamError, Paper, Submission, canonical
from ..papers import CALIBRATION_MODES, module_for
from .mark import mark
from .registry import digest


@dataclass(frozen=True)
class Band:
    """A pre-registered expectation for one (question type, fake) pair."""

    low: float
    high: float
    why: str

    def holds(self, value: float) -> bool:
        return self.low - 1e-9 <= value <= self.high + 1e-9

    def describe(self) -> str:
        if self.low == self.high:
            return "== %.4g" % self.low
        return "in [%.4g, %.4g]" % (self.low, self.high)


#: Pre-registered.  Edit only with a reason recorded in DECISIONS.md; the
#: rubric digest does not cover this file, so a quiet widening here would not
#: show up as a digest mismatch -- which is exactly why it is called out.
EXPECTED: Dict[Tuple[str, str], Band] = {
    # Exact, everywhere: these two follow from construction, not from item mix.
    ("heldout", "oracle"): Band(1.0, 1.0, "ground truth must be accepted in full"),
    ("heldout", "null"): Band(0.0, 0.0, "silence must pay nothing"),
    ("handover", "oracle"): Band(1.0, 1.0, "ground truth must be accepted in full"),
    ("handover", "null"): Band(0.0, 0.0, "an arm with no deliverable scores zero"),
    ("adaptation", "oracle"): Band(1.0, 1.0, "ground truth must be accepted in full"),
    ("adaptation", "null"): Band(0.0, 0.0, "silence must pay nothing"),
    ("verdict", "oracle"): Band(1.0, 1.0, "ground truth must be accepted in full"),
    ("verdict", "null"): Band(0.0, 0.0, "silence must pay nothing"),

    # Bands.  Wide on purpose: the exact value depends on how many items of each
    # class a paper happens to carry, and pinning that would freeze item mix as
    # a side effect of calibration.
    ("heldout", "memoriser"): Band(0.0, 0.75,
        "it replays what it saw, so its total is dragged up by the replay "
        "control and down by held-out. The number that matters is the gap, "
        "checked separately by `replay_gap`."),
    # WIDENED AFTER FIRST CONTACT -- see D-EX-010. The original band was
    # Band(0.0, 0.35, "returning the unchanged frame is right only where
    # nothing moved"), and the built paper scored 0.45. The premise was wrong,
    # not the paper: the paper over-samples the guard classes on purpose, and
    # every guard's answer *is* an unchanged frame. The absolute number is
    # retained only as a hard ceiling; the expectation that does the work is now
    # the mix-invariant pair in `_type_specific`, which is strictly stronger.
    ("heldout", "bluffer"): Band(0.0, 0.50,
        "an absolute band here encodes an assumption about item mix that the "
        "paper is entitled to refute. The real checks are `bluffer_hits_ceiling` "
        "and `oracle_minus_bluffer`; this is a backstop, not the measurement."),
    ("handover", "memoriser"): Band(0.0, 0.80,
        "the manual drills step semantics, so it can pass that family while "
        "failing to tell level data from world law"),
    ("handover", "bluffer"): Band(0.0, 0.55,
        "answering the modal label in each family beats zero and should not "
        "approach a reader who understood the document"),
    ("adaptation", "memoriser"): Band(0.0, 0.40,
        "it answers as though nothing changed, which is the whole failure"),
    ("adaptation", "bluffer"): Band(0.0, 0.45,
        "claiming everything is invalidated must not pay: recall without "
        "precision is the failure mode this item type exists to price"),
    ("verdict", "memoriser"): Band(0.0, 0.70,
        "competent on the small-space family it has seen, collapsing on the "
        "large-space one it cannot enumerate"),
    ("verdict", "bluffer"): Band(0.0, 0.50,
        "always answering `unsolvable` buys perfect sensitivity and zero "
        "specificity; the score must reflect the pair, not the sensitivity"),
}

#: Extra structural expectations that are not a score band.
STRUCTURAL = {
    "null_all_unanswered": "every item of a null submission is `unanswered`",
    "oracle_no_wrong": "an oracle submission contains no `wrong` verdict",
    "heldout_replay_gap": ("the memoriser's replay score must exceed its "
                           "held-out score by a wide margin, or the paper is "
                           "not testing rules"),
    "verdict_bluffer_pair": ("the bluffer must show sensitivity 1.0 and "
                             "specificity 0.0"),
}

#: How wide "wide" is for the memoriser gap.  Pre-registered with the bands.
MIN_REPLAY_GAP = 0.40

#: How far ground truth must beat a bluffer on the held-out paper.  Added after
#: first contact together with the ceiling check (D-EX-010): it says what the
#: original absolute band was trying to say, in a form that does not depend on
#: how many refusal items the paper happens to carry.
MIN_ORACLE_BLUFFER_MARGIN = 0.50


def _submission(examinee_id: str, paper: Paper, answers: Dict[str, Any],
                mode: str) -> Submission:
    caps = () if mode == "null" else ("answers",)
    return Submission(examinee_id="fake-%s" % mode, paper_id=paper.paper_id,
                      answers=answers, capabilities=caps,
                      meta={"fake": mode,
                            "note": "a calibration examinee, not a real arm"})


def calibrate_one(question_type: str) -> Dict[str, Any]:
    """Run the four fakes through one paper and check the pre-registered bands."""
    module = module_for(question_type)
    paper = module.build()
    rubric_digest = digest()
    key_doc = paper.key(rubric_digest)
    axes_fn = getattr(module, "axes", None)

    results: Dict[str, Any] = {}
    failures: List[str] = []

    for mode in CALIBRATION_MODES:
        answers = module.reference_answers(paper, key_doc, mode)
        submission = _submission(mode, paper, answers, mode)
        report = mark(key_doc, submission, axes_fn=axes_fn)
        fraction = report.fraction
        band = EXPECTED.get((question_type, mode))
        entry: Dict[str, Any] = {
            "fraction": fraction,
            "awarded": report.awarded,
            "possible": report.possible,
            "counts": {v: sum(1 for s in report.scores if s.verdict == v)
                       for v in ("correct", "wrong", "abstained", "unanswered")},
            "axes": report.axes,
        }
        if band is None:
            failures.append("%s/%s: no pre-registered band. A fake with no "
                            "expectation calibrates nothing." % (question_type, mode))
        else:
            entry["expected"] = band.describe()
            entry["why"] = band.why
            entry["holds"] = band.holds(fraction)
            if not band.holds(fraction):
                failures.append("%s/%s: scored %.4f, expected %s (%s)"
                                % (question_type, mode, fraction,
                                   band.describe(), band.why))

        # -- structural checks, which a band cannot express ------------------
        if mode == "null":
            n_unanswered = entry["counts"]["unanswered"]
            if n_unanswered != len(report.scores):
                failures.append(
                    "%s/null: %d of %d items are not `unanswered`. Silence must "
                    "be recorded as silence -- an arm with nothing to submit is "
                    "a finding, not a wrong answer."
                    % (question_type, len(report.scores) - n_unanswered,
                       len(report.scores)))
        if mode == "oracle" and entry["counts"]["wrong"]:
            failures.append("%s/oracle: %d item(s) marked wrong. The rubric "
                            "rejects ground truth."
                            % (question_type, entry["counts"]["wrong"]))
        results[mode] = entry

    # -- the two type-specific structural checks ---------------------------
    extra = _type_specific(question_type, results, paper=paper, key_doc=key_doc,
                           axes_fn=axes_fn)
    failures.extend(extra["failures"])
    results["structural"] = extra["checks"]

    return {
        "question_type": question_type,
        "paper_id": paper.paper_id,
        "rubric_digest": rubric_digest,
        "n_items": len(paper.items),
        "modes": results,
        "failures": failures,
        "calibrated": not failures,
    }


#: The verdict sheet's `INSTRUCTIONS` advertise five answer shapes.  The four
#: fakes submit three of them, and the seven mutants of `selftest.py` are all
#: derived from the oracle's answers, so they inherit the same three.  These are
#: the two the apparatus never sees, plus the two failure shapes that ride on
#: them.  Each expectation below is **arithmetic over the paper's own points and
#: the rubric's own constants** rather than a band -- D-EX-012's rule, and the
#: reason there is no number fitted to a first reading anywhere in here.
#:
#: Measured cost of not having these (D-EX-026): of fourteen faults injected into
#: the verdict rubric by an adversarial audit, thirteen passed `assert_calibrated`
#: and twelve passed all seven mutants.  Two -- "score the reason half even when
#: the claim is wrong" and "believe an invariant certificate's values instead of
#: re-deriving them, on large boards only" -- were caught by nothing at all:
#: not the gate, not the mutants, not 73 tests.  Both live on answer shapes no
#: fake submitted.
_VERDICT_PROBES = ("abstainer", "illegible", "searcher", "wrong_claim_with_reason",
                   "forged_certificate")


def _verdict_probe_answers(kind: str, key_doc: Dict[str, Any]) -> Dict[str, Any]:
    answers: Dict[str, Any] = {}
    for entry in key_doc["items"]:
        claim = entry["truth"]["claim"]
        if kind == "abstainer":
            answers[entry["item_id"]] = {"claim": "abstain"}
        elif kind == "illegible":
            # A well-formed object with no `claim` key: what a broken serialiser
            # emits.  Must be `wrong` and must pay nothing.
            answers[entry["item_id"]] = {"verdict": claim}
        elif kind == "searcher":
            answers[entry["item_id"]] = {"claim": claim,
                                         "reason": "exhaustive_search"}
        elif kind == "forged_certificate":
            # Right claim, fabricated reason. The module's thesis is that "the
            # examinee's arithmetic is checked, never believed"; this is the
            # submission that tests it, and no fake and no mutant makes it --
            # the mutants are all derived from the oracle's answers, which are
            # true.
            #
            # The witness matters. A first version sent only a certificate, and
            # on a *solvable* item `_score_unsolvable_reason` is never called --
            # the reason half was refused for lack of a witness rather than
            # because anything was re-derived, so the probe scored exactly right
            # on 8 of 17 items no matter what the checker did. An adversarial
            # review found it by making `check_certificate` a rubber stamp and
            # watching the award move by 9, not 17. A probe that passes for the
            # wrong reason on half the paper is half a probe. D-EX-027.
            answers[entry["item_id"]] = {
                "claim": claim,
                "certificate": {"kind": "invariant", "invariant": "cart_region",
                                "initial_value": [0, 0], "goal_value": [0, 1]},
                "witness": ["UP", "UP", "UP"]}
        else:                                   # wrong_claim_with_reason
            flipped = "solvable" if claim == "unsolvable" else "unsolvable"
            answers[entry["item_id"]] = {"claim": flipped,
                                         "reason": "exhaustive_search",
                                         "witness": ["UP"],
                                         "certificate": {"kind": "cut_set",
                                                         "cells": [[0, 0]]}}
    return answers


#: The verdict rubric's split, **pre-registered here rather than imported from
#: there**.  The first draft of `_verdict_probe_expectation` read
#: `rubrics_verdict.SEARCH_CREDIT`, and so the expectation moved with the
#: constant: injecting `SEARCH_CREDIT = 1.0` -- "I searched it all" paid in full,
#: which destroys the one ordering class (i) exists to create -- changed the
#: marker and the check together and the gate stayed green.  A check that reads
#: its expectation out of the code it is checking is not a check.  These are
#: protocol numbers; moving one is a deliberate edit a reviewer sees, which is
#: the same argument D-EX-016 makes for the protocol digest.
VERDICT_WEIGHTS = {"verdict": 0.5, "justification": 0.5, "search_credit": 0.4}


def _verdict_probe_expectation(kind: str, key_doc: Dict[str, Any]) -> float:
    """What the marker must award, computed rather than observed."""
    VERDICT_WEIGHT = VERDICT_WEIGHTS["verdict"]
    JUSTIFICATION_WEIGHT = VERDICT_WEIGHTS["justification"]
    SEARCH_CREDIT = VERDICT_WEIGHTS["search_credit"]

    if kind in ("abstainer", "illegible", "wrong_claim_with_reason"):
        return 0.0
    total = 0.0
    for entry in key_doc["items"]:
        points = float(entry["points"])
        truth = entry["truth"]
        awarded = points * VERDICT_WEIGHT           # the claim is right
        if kind == "forged_certificate":
            # On an unsolvable item the certificate's numbers are re-derived and
            # refused; on a solvable one the witness is replayed and loses. Both
            # halves of the reason channel are exercised and both pay nothing,
            # so the claim half is all there is -- on every item, for a reason
            # that is about the item.
            total += awarded
            continue
        if truth["claim"] == "unsolvable" and truth.get("search_credible"):
            awarded += points * JUSTIFICATION_WEIGHT * SEARCH_CREDIT
        # A right `solvable` with no witness earns the claim only, and a search
        # claim on a level too big to search earns the claim only.
        total += awarded
    return total


def _type_specific(question_type: str, results: Dict[str, Any], *,
                   paper: Optional[Paper] = None,
                   key_doc: Optional[Dict[str, Any]] = None,
                   axes_fn: Optional[Any] = None) -> Dict[str, Any]:
    checks: Dict[str, Any] = {}
    failures: List[str] = []

    if question_type == "heldout":
        axes = results.get("memoriser", {}).get("axes", {})
        # The builder names it `gap_replay_minus_heldout`; `replay_gap` is
        # accepted as an alias so a rename in either place is a failed lookup
        # rather than a silently absent measurement.
        gap = axes.get("gap_replay_minus_heldout", axes.get("replay_gap"))
        checks["replay_gap"] = gap
        checks["min_replay_gap"] = MIN_REPLAY_GAP
        if gap is None:
            failures.append(
                "heldout: the memoriser's report carries no `replay_gap` axis. "
                "The gap is the measurement; without it the paper reports a "
                "total that a memoriser can share with a rule-learner.")
        elif gap < MIN_REPLAY_GAP:
            failures.append(
                "heldout: the memoriser's replay-minus-held-out gap is %.4f, "
                "below the pre-registered %.2f. Either the held-out split is "
                "leaking evidence or the memoriser is not memorising."
                % (gap, MIN_REPLAY_GAP))

        # The two checks that replaced the absolute bluffer band (D-EX-010).
        # Both are invariant to item mix, which is what the absolute band was
        # not: the paper publishes the score an examinee gets for returning the
        # input frame unchanged, and the bluffer must land exactly on it and
        # remain far from a real theory.
        bluffer = results.get("bluffer", {})
        ceiling = bluffer.get("axes", {}).get("unchanged_frame_share")
        bluffer_fraction = bluffer.get("fraction")
        oracle_fraction = results.get("oracle", {}).get("fraction")
        checks["published_bluffer_ceiling"] = ceiling
        checks["bluffer_fraction"] = bluffer_fraction
        if ceiling is None:
            failures.append(
                "heldout: the paper does not publish `unchanged_frame_share`. "
                "A bluffer's ceiling is a property of the item mix, so it has to "
                "be published by the paper rather than assumed by the protocol.")
        elif bluffer_fraction is None or abs(bluffer_fraction - ceiling) > 1e-9:
            failures.append(
                "heldout: the bluffer scored %.4f against a published ceiling of "
                "%.4f. It should land exactly on the ceiling -- if it does not, "
                "either the ceiling is miscomputed or the bluffer is doing "
                "something other than returning the input frame."
                % (bluffer_fraction if bluffer_fraction is not None else -1.0,
                   ceiling))
        if oracle_fraction is not None and bluffer_fraction is not None:
            margin = round(oracle_fraction - bluffer_fraction, 6)
            checks["oracle_minus_bluffer"] = margin
            if margin < MIN_ORACLE_BLUFFER_MARGIN:
                failures.append(
                    "heldout: ground truth beats the bluffer by only %.4f, below "
                    "the pre-registered %.2f. A paper on which saying nothing "
                    "useful gets close to knowing the rules is not measuring the "
                    "rules." % (margin, MIN_ORACLE_BLUFFER_MARGIN))

    if question_type == "verdict":
        axes = results.get("bluffer", {}).get("axes", {})
        conf = axes.get("confusion", {})
        sens, spec = conf.get("sensitivity"), conf.get("specificity")
        checks["bluffer_sensitivity"] = sens
        checks["bluffer_specificity"] = spec
        if sens != 1.0 or spec != 0.0:
            failures.append(
                "verdict: the bluffer shows sensitivity=%s specificity=%s; the "
                "protocol expects 1.0 / 0.0. An arm that answers `unsolvable` "
                "to everything must catch every unsolvable case and no solvable "
                "one -- if it does not, the confusion matrix is not reading the "
                "answers it thinks it is." % (sens, spec))

        # The pair, per board-size stratum, and not only pooled. The class split
        # cannot state it -- the three classes partition the paper by answer, so
        # one denominator is empty in every class cell -- and pooled is where
        # D-EX-015 argues it means least. `board_size_class` cross-cuts the
        # answer, so the bluffer's signature must appear in each stratum on its
        # own. Strictly stronger than the pooled assertion above and independent
        # of how many items of each class the paper happens to carry. D-EX-024.
        strata = axes.get("confusion_by_board_size") or {}
        checks["bluffer_pair_by_board_size"] = {
            k: (v.get("sensitivity"), v.get("specificity"))
            for k, v in sorted(strata.items())}
        if not strata:
            failures.append(
                "verdict: the bluffer's report carries no per-stratum pair. The "
                "pooled pair is the one number D-EX-015 shows cannot separate "
                "ground truth from a reader who never saw a board.")
        for stratum, cell in sorted(strata.items()):
            if (cell.get("sensitivity"), cell.get("specificity")) != (1.0, 0.0):
                failures.append(
                    "verdict: on %s boards the bluffer shows %s / %s, not "
                    "1.0 / 0.0. 敢说不可解的框架必须在可解题上闭嘴 has to hold "
                    "inside each stratum, not only after pooling them."
                    % (stratum, cell.get("sensitivity"), cell.get("specificity")))

        # The weights the probes' arithmetic assumes, checked against the ones
        # the marker actually uses. Without this the two could drift apart
        # silently in the safe-looking direction: the probes would keep passing
        # while measuring a different rubric.
        from . import rubrics_verdict as _rv

        live = {"verdict": _rv.VERDICT_WEIGHT,
                "justification": _rv.JUSTIFICATION_WEIGHT,
                "search_credit": _rv.SEARCH_CREDIT}
        checks["verdict_weights"] = live
        for name, expected_weight in sorted(VERDICT_WEIGHTS.items()):
            if abs(live[name] - expected_weight) > 1e-9:
                failures.append(
                    "verdict: the rubric's %s weight is %g, and the protocol "
                    "pre-registers %g. Half the item is the claim and half is "
                    "the reason, and a search is worth %g of a reason -- those "
                    "three numbers are what makes a certificate beat 'I looked "
                    "everywhere', which is the whole of class (i)."
                    % (name, live[name], expected_weight,
                       VERDICT_WEIGHTS["search_credit"]))

        # The answer shapes no fake submits. D-EX-026.
        if key_doc is not None:
            probes: Dict[str, Any] = {}
            for kind in _VERDICT_PROBES:
                answers = _verdict_probe_answers(kind, key_doc)
                report = mark(key_doc, Submission(
                    examinee_id="probe-%s" % kind, paper_id=key_doc["paper_id"],
                    answers=answers, capabilities=("answers",),
                    meta={"probe": kind}), axes_fn=axes_fn)
                expected = _verdict_probe_expectation(kind, key_doc)
                counts = {v: sum(1 for s in report.scores if s.verdict == v)
                          for v in ("correct", "wrong", "abstained", "unanswered")}
                probes[kind] = {"awarded": report.awarded, "expected": expected,
                                "counts": counts}
                if abs(report.awarded - expected) > 1e-9:
                    failures.append(
                        "verdict/%s: the marker awarded %.4f where arithmetic "
                        "over the paper's points says %.4f. This probe exists "
                        "because no calibration fake submits this answer shape, "
                        "so nothing else in the protocol looks at the branch it "
                        "takes." % (kind, report.awarded, expected))
                if kind == "abstainer" and counts["abstained"] != len(report.scores):
                    failures.append(
                        "verdict/abstainer: %d of %d items are not `abstained`. "
                        "A framework that will say 'unsolvable' has to be able "
                        "to say nothing, and the marker has to record that it "
                        "did -- an abstention read as a claim is worth 9 of 34 "
                        "on this paper."
                        % (len(report.scores) - counts["abstained"],
                           len(report.scores)))
                if kind == "illegible" and counts["wrong"] != len(report.scores):
                    failures.append(
                        "verdict/illegible: %d of %d unreadable answers are not "
                        "`wrong`. An answer nobody can read is not an "
                        "abstention and not a missing submission; recording it "
                        "as either lets a broken serialiser look like restraint."
                        % (len(report.scores) - counts["wrong"], len(report.scores)))
                if kind == "wrong_claim_with_reason" and counts["wrong"] != len(report.scores):
                    failures.append(
                        "verdict/wrong_claim_with_reason: %d of %d items are "
                        "not `wrong`. The reason half must be unreachable when "
                        "the claim is wrong, or a confidently mistaken examinee "
                        "is paid for a well-formed argument for a falsehood."
                        % (len(report.scores) - counts["wrong"], len(report.scores)))
            checks["answer_shape_probes"] = probes

    if question_type == "adaptation":
        axes = results.get("memoriser", {}).get("axes", {})
        flag = axes.get("silently_wrong")
        checks["memoriser_silently_wrong"] = flag
        if not flag:
            failures.append(
                "adaptation: the memoriser did not trip `silently_wrong`. That "
                "flag is the demonstration -- a theory that keeps a verdict "
                "after the rule it depended on changed is the failure this "
                "architecture exists to prevent, and the paper has to be able "
                "to see it.")

    return {"checks": checks, "failures": failures}


def calibrate_all(question_types: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    from ..papers import BUILDERS
    types = list(question_types or BUILDERS)
    per_type = {qt: calibrate_one(qt) for qt in types}
    failures = [f for r in per_type.values() for f in r["failures"]]
    return {
        "rubric_digest": digest(),
        "pre_registered": {"%s/%s" % k: {"band": b.describe(), "why": b.why}
                           for k, b in sorted(EXPECTED.items())},
        "structural_expectations": STRUCTURAL,
        "min_replay_gap": MIN_REPLAY_GAP,
        "per_type": per_type,
        "failures": failures,
        "calibrated": not failures,
    }


def assert_calibrated(question_type: str) -> Dict[str, Any]:
    """Refuse to proceed on an uncalibrated marker."""
    result = calibrate_one(question_type)
    if not result["calibrated"]:
        raise ExamError(
            "the %s marker is not calibrated, so it will not mark a real "
            "submission:\n  %s" % (question_type, "\n  ".join(result["failures"])))
    return result
