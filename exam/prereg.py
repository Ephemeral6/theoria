"""判决题 pre-registration -- written before any arm sits the paper.

`freeze/STATS_RULES.md` §2 pre-registers the *statistic* and the gaming audit.
What it does not carry, and what a pre-registration of an endpoint has to carry
before the endpoint means anything, is three things:

1. the **scoring rule** as executed, tied to the code that executes it by digest
   rather than by citation -- §2 cites `mark.py:95` and `rubrics_verdict.py:121`
   by line number, and line numbers move;
2. the **arms' expected behaviour, per class**, with a refutation condition for
   each -- a directional prediction that cannot fail is not a prediction, and
   Theoria.md:379 requires 逐指标方向预测 for exactly this reason;
3. **sensitivity and specificity as separate numbers with separate floors**,
   plus the coverage that makes either readable.

This module is the machine-readable half.  `PREREG` is data, `check()` compares
it against the paper that is actually built, and `exam/PREREG_VERDICT.md` is the
same content as prose.  Where the two disagree, `check()` is right and the prose
is a defect -- which is the only arrangement under which prose stays true.

**Pre-registration means the numbers are fixed before the arms are seen, not
that they came from nowhere.**  Every threshold here has an argument attached
and two of them are `needs_human` in `freeze/`: this module executes exam's
proposal and labels it a proposal.  Changing one is a visible edit to a tracked
file with a digest over it, which is the whole mechanism.
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence

from . import endpoint as ep

#: The arms of `freeze/STATS_RULES.md` §0.  `schema_repro` is absent from the
#: repo and from this list: `baseline-arms/SCHEMA_LOCATE.md` records that the
#: official harness was never published, so a row for it here would be a
#: prediction about an arm that cannot sit the paper.
ARMS: Sequence[str] = ("bare_cc", "theoria", "ablation_no_theorem_obligation")

#: One row per (arm, class).  `predict` is the direction; `refuted_if` is the
#: observation that would make this row false.  Both are required -- a row with
#: no refutation condition is an expectation, not a prediction, and the fourth
#: field says which of the two the row is being used as.
ARM_EXPECTATIONS: Sequence[Dict[str, str]] = (
    # ---------------------------------------------------------- class (i)
    {"arm": "bare_cc", "class": "small_unsolvable",
     "predict": "verdict often correct -- the board is small enough to search "
                "by hand -- but `certified_share` = 0.0: no machine-checkable "
                "certificate, because the arm has no deliverable to write one "
                "in (Theoria.md 1.11, CC 无物可交记零)",
     "refuted_if": "bare_cc submits a certificate that `check_certificate` "
                   "accepts on any class (i) item",
     "role": "prediction"},
    {"arm": "ablation_no_theorem_obligation", "class": "small_unsolvable",
     "predict": "same verdict accuracy as theoria, `certified_share` "
                "materially lower -- this is the ablation's whole definition, "
                "and class (i) is where the two are otherwise hardest to tell "
                "apart",
     "refuted_if": "the ablation's `certified_share` on class (i) is within "
                   "0.1 of theoria's",
     "role": "prediction"},
    {"arm": "theoria", "class": "small_unsolvable",
     "predict": "sensitivity 1.0 with `certified_share` > 0.5 -- the class "
                "exists to score the reason, and a framework that only searches "
                "here has not used what it is supposed to have",
     "refuted_if": "theoria's class (i) `certified_share` <= bare_cc's",
     "role": "prediction"},
    # --------------------------------------------------------- class (ii)
    {"arm": "bare_cc", "class": "large_unsolvable",
     "predict": "`coverage_positive` below `c_min`: the arm abstains or does "
                "not answer, and under 弃权计错 those become `fn`",
     "refuted_if": "bare_cc answers >= c_min of class (ii) and is right on "
                   "them",
     "role": "prediction"},
    {"arm": "ablation_no_theorem_obligation", "class": "large_unsolvable",
     "predict": "answers, and is right about as often as theoria, with no "
                "certificate -- the ablation removes the obligation to prove, "
                "not the ability to notice",
     "refuted_if": "the ablation's class (ii) sensitivity is more than 0.25 "
                   "below theoria's",
     "role": "prediction"},
    {"arm": "theoria", "class": "large_unsolvable",
     "predict": "`coverage_positive` = 1.0 and sensitivity 1.0. This is the "
                "class the architecture is for; abstention here is a failure, "
                "not caution",
     "refuted_if": "theoria's class (ii) coverage < c_min, which routes the "
                   "whole endpoint to 不可结论 for that arm",
     "role": "prediction"},
    # -------------------------------------------------------- class (iii)
    {"arm": "bare_cc", "class": "solvable_hard",
     "predict": "specificity >= S_min. The bare arm is not expected to have a "
                "taste for impossibility proofs, so class (iii) is where it "
                "should look *best*",
     "refuted_if": "bare_cc's specificity < S_min",
     "role": "prediction"},
    {"arm": "ablation_no_theorem_obligation", "class": "solvable_hard",
     "predict": "specificity >= S_min, and no lower than theoria's -- removing "
                "the theorem obligation should not make an arm *more* willing "
                "to declare impossibility",
     "refuted_if": "the ablation's specificity is more than 0.25 below "
                   "theoria's",
     "role": "prediction"},
    {"arm": "theoria", "class": "solvable_hard",
     "predict": "specificity >= 0.75, above the floor with margin. 敢说不可解的"
                "框架必须在这里闭嘴 -- a framework that ships unsolvability "
                "certificates has to be measurably quiet here, or the "
                "certificates are worth nothing",
     "refuted_if": "theoria's specificity < S_min, which is 不成立 for this "
                   "endpoint on its own, whatever BA says",
     "role": "prediction"},
)

#: The controls that must run before any arm does, and the verdict each must
#: receive.  `launch_blockers.json` 9.16 requires two (`bluffer` 必须判为不成立,
#: `memoriser` 必须不能判为成立); this table carries six, and the four extra ones
#: are not padding: `denier` is the only one that exercises the BA floor alone,
#: `abstainer` and `null` are the two the pre-conversion marker could not score
#: at all, and `oracle` is the only evidence that the gate can say yes.
CONTROL_EXPECTATIONS: Dict[str, Dict[str, Any]] = {
    "oracle": {"verdict": ep.VERDICT_CREDITED,
               "why": "ground truth must be creditable, or the gate has never "
                      "been observed to accept anything"},
    "bluffer": {"verdict": ep.VERDICT_REFUTED,
                "why": "always `unsolvable`: sensitivity 1.0, specificity 0.0. "
                       "Killed by the specificity floor (STATS_RULES 2.3)"},
    "denier": {"verdict": ep.VERDICT_REFUTED,
               "why": "always `solvable`: sensitivity 0.0, specificity 1.0. "
                      "Passes the specificity floor and the coverage floor, and "
                      "is killed by the BA floor alone -- the mirror control "
                      "without which the specificity floor could be mistaken "
                      "for the whole instrument"},
    "overclaimer": {"verdict": ep.VERDICT_REFUTED,
                    "why": "`unsolvable` everywhere except three solvable items: "
                           "sensitivity 1.0, specificity 0.375, BA 0.6875, "
                           "class (ii) coverage 1.0. It clears the BA floor and "
                           "the coverage floor, and **only** the specificity "
                           "floor refuses it -- which is why it exists. Without "
                           "it, deleting `S_min` changed no verdict on this "
                           "control set and the one-vote veto was carried on "
                           "the strength of its name"},
    "abstainer": {"verdict": ep.VERDICT_REFUTED,
                  "why": "abstains everywhere. Before 弃权计错 both rates read "
                         "`None` and no floor had a total order over it"},
    "memoriser": {"verdict": ep.VERDICT_INCONCLUSIVE,
                  "why": "answers only what it has seen: pooled pair identical "
                         "to ground truth on the items it answered, 0 of 4 on "
                         "class (ii). 不可结论, never 不成立 -- silence is not "
                         "refutation (launch_blockers 9.16)"},
    "null": {"verdict": ep.VERDICT_REFUTED,
             "why": "submits nothing; under 弃权计错 every item is an error on "
                    "its own side"},
}

#: What each floor is for, and -- measured, not asserted -- which control walks
#: through if it is removed.  `floor_leave_one_out()` recomputes the right-hand
#: column by actually disabling each floor, and a test pins the two against each
#: other, because a claim that a check is load-bearing is exactly the kind of
#: claim that rots.
#:
#: **This table was wrong on its first run and the measurement is what said so.**
#: `S_min` was written down as catching `abstainer` and `null`; disabling it
#: changed no verdict, because both of those also fail the BA floor.  A floor
#: that has never been observed to cast a vote is a floor carried on the
#: strength of its name -- so `overclaimer` was constructed to be the case only
#: `S_min` refuses (sensitivity 1.0, specificity 0.375, BA 0.6875), and every
#: floor now catches exactly one control alone.
FLOOR_CLAIMS: Dict[str, Dict[str, Any]] = {
    "S_min": {"value": ep.S_MIN,
              "source": "STATS_RULES.md 2.2, suggested 0.5, ⟨S_min⟩ needs_human",
              "catches_alone": ["overclaimer"]},
    "c_min": {"value": ep.C_MIN,
              "source": "launch_blockers.json 9.16, ⟨c_min⟩ needs_human; exam "
                        "proposes 0.5",
              "catches_alone": ["memoriser"]},
    "ba_floor": {"value": ep.BA_FLOOR,
                 "source": "exam: both constant strategies score exactly 0.5, "
                           "so a strict inequality above it is the weakest "
                           "statement that an arm is not a constant",
                 "catches_alone": ["denier"]},
}

#: The scoring rule, restated here so that a reader of the pre-registration does
#: not have to read the rubric to know what was promised.  `check()` compares
#: every number against the live constants; a rubric edit that moves one turns
#: this file red rather than silently re-defining the endpoint.
SCORING_RULE: Dict[str, Any] = {
    "items": 17,
    "class_sizes": {"small_unsolvable": 5, "large_unsolvable": 4,
                    "solvable_hard": 8},
    "points_per_item": {"unsolvable": 2.0, "solvable": 2.0},
    "weights": {"verdict": 0.5, "justification": 0.5, "search_credit": 0.4},
    "answer_alphabet": ["unsolvable", "solvable", "abstain"],
    "non_answers_are_errors": list(ep.NON_ANSWERS),
    "certificate_grammar": ["invariant", "cut_set", "counting"],
    "endpoint_scalar": "BA = (sensitivity + specificity) / 2, from the "
                       "confusion half after 弃权计错; never reported without "
                       "both halves beside it",
    "score_is_not_the_scalar": "the marks total folds the reason half in and is "
                               "reported separately (STATS_RULES 2.2)",
}

PREREG: Dict[str, Any] = {
    "endpoint": "主终点二 · 判决题准确率(含特异度)",
    "endpoint_id": "endpoint-2-verdict",
    "paper_id": "p15-verdict-a2",
    "sources": ["Theoria.md:259", "Theoria.md:373",
                "freeze/STATS_RULES.md §2", "freeze/launch_blockers.json 9.15",
                "freeze/launch_blockers.json 9.16"],
    "written_before": "any arm sits this paper; the only transcripts on disk "
                      "when this was written are the four calibration fakes and "
                      "`cheater-v4`, an adversarial reader, none of which is an "
                      "arm",
    "scoring_rule": SCORING_RULE,
    "readouts": {
        "primary": ["sensitivity", "specificity"],
        "derived": ["balanced_accuracy"],
        "required_beside": ["coverage_positive per class",
                            "certified_share",
                            "abstained / unanswered / unreadable counts"],
        "forbidden": ["balanced_accuracy alone",
                      "a single accuracy over all 17 items",
                      "a rate whose denominator excluded abstentions"],
    },
    "floors": FLOOR_CLAIMS,
    "arms": list(ARMS),
    "arm_expectations": list(ARM_EXPECTATIONS),
    "controls": CONTROL_EXPECTATIONS,
    "scope": ep.SCOPE_NOTE,
    "known_blind_spot": (
        "The gated numbers cannot separate `cheater-v4` -- a reader handed the "
        "sheet and nothing else -- from ground truth: identical in every cell, "
        "both credited. The only quantity that separates them is "
        "`certified_share` (0.0 against 1.0), which STATS_RULES 2.2 demotes to "
        "exploratory. exam publishes it on every transcript and has proposed "
        "the amendment through monitor/inbox rather than legislating it here."),
}


# ------------------------------------------------------------------- checks

def check(paper: Any = None, key_doc: Any = None) -> List[str]:
    """Every number in `PREREG`, against the paper and rubric that exist.

    A pre-registration that drifts from the instrument it registers is worse
    than none: it reads as a commitment and describes something else.  Returns
    the failures rather than raising, so a caller can print all of them.
    """
    from .grading import rubrics_verdict as rv
    from .grading.registry import digest
    from .papers import module_for

    failures: List[str] = []
    module = module_for("verdict")
    if paper is None:
        paper = module.build()
    if key_doc is None:
        key_doc = paper.key(digest())

    if paper.paper_id != PREREG["paper_id"]:
        failures.append("paper_id is %r, pre-registered %r"
                        % (paper.paper_id, PREREG["paper_id"]))

    sizes: Dict[str, int] = {}
    points: Dict[str, float] = {}
    for entry in key_doc["items"]:
        klass = entry["truth"]["class"]
        sizes[klass] = sizes.get(klass, 0) + 1
        points.setdefault(entry["truth"]["claim"], float(entry["points"]))
        if float(entry["points"]) != points[entry["truth"]["claim"]]:
            failures.append("items of claim %r do not all carry the same points"
                            % entry["truth"]["claim"])
    if sizes != SCORING_RULE["class_sizes"]:
        failures.append(
            "class sizes are %s, pre-registered %s. The mix is frozen "
            "(STATS_RULES 2.3 事后挑题目组合); changing it is a protocol edit, "
            "not a build detail." % (sizes, SCORING_RULE["class_sizes"]))
    if sum(sizes.values()) != SCORING_RULE["items"]:
        failures.append("paper carries %d items, pre-registered %d"
                        % (sum(sizes.values()), SCORING_RULE["items"]))
    if points != SCORING_RULE["points_per_item"]:
        failures.append("points per claim are %s, pre-registered %s"
                        % (points, SCORING_RULE["points_per_item"]))

    live = {"verdict": rv.VERDICT_WEIGHT, "justification": rv.JUSTIFICATION_WEIGHT,
            "search_credit": rv.SEARCH_CREDIT}
    if live != SCORING_RULE["weights"]:
        failures.append("rubric weights are %s, pre-registered %s"
                        % (live, SCORING_RULE["weights"]))

    grammar = sorted(getattr(rv, "CERTIFICATE_KINDS", ()) or
                     SCORING_RULE["certificate_grammar"])
    if grammar != sorted(SCORING_RULE["certificate_grammar"]):
        failures.append("certificate grammar is %s, pre-registered %s"
                        % (grammar, SCORING_RULE["certificate_grammar"]))

    for name, claim in FLOOR_CLAIMS.items():
        live_value = {"S_min": ep.S_MIN, "c_min": ep.C_MIN,
                      "ba_floor": ep.BA_FLOOR}[name]
        if abs(float(claim["value"]) - live_value) > 1e-12:
            failures.append("floor %s is %g in endpoint.py and %g here"
                            % (name, live_value, claim["value"]))

    for arm in ARMS:
        for klass in SCORING_RULE["class_sizes"]:
            rows = [r for r in ARM_EXPECTATIONS
                    if r["arm"] == arm and r["class"] == klass]
            if len(rows) != 1:
                failures.append(
                    "%d expectations for (%s, %s); the pre-registration is a "
                    "prediction per arm per class, and a missing cell is a cell "
                    "that can be filled in after the fact"
                    % (len(rows), arm, klass))
        for row in ARM_EXPECTATIONS:
            if row["arm"] == arm and not row.get("refuted_if"):
                failures.append("(%s, %s) has no refutation condition"
                                % (arm, row["class"]))
    return failures


def control_verdicts() -> Dict[str, str]:
    """Run every control through the gate and return what it was judged."""
    from .tools.endpoint_verdict import (control_submission, judge_submission)
    return {name: judge_submission(control_submission(name))["ruling"]["verdict"]
            for name in CONTROL_EXPECTATIONS}


def check_controls() -> List[str]:
    got = control_verdicts()
    failures = []
    for name, expected in CONTROL_EXPECTATIONS.items():
        if got.get(name) != expected["verdict"]:
            failures.append("control %s was judged %r, pre-registered %r (%s)"
                            % (name, got.get(name), expected["verdict"],
                               expected["why"]))
    return failures


def floor_leave_one_out() -> Dict[str, List[str]]:
    """Disable each floor in turn; report which controls become credited.

    This is the acceptance test for the floors themselves.  A floor that changes
    no verdict when it is removed has never been observed to do anything, and
    the pre-registration would be carrying it on the strength of its name.
    """
    from .tools.endpoint_verdict import (CONTROLS, control_submission,
                                         judge_submission)

    def credited_with(**overrides: float) -> List[str]:
        saved = (ep.S_MIN, ep.C_MIN, ep.BA_FLOOR)
        try:
            ep.S_MIN = overrides.get("S_min", ep.S_MIN)
            ep.C_MIN = overrides.get("c_min", ep.C_MIN)
            ep.BA_FLOOR = overrides.get("ba_floor", ep.BA_FLOOR)
            out = []
            for name in CONTROLS:
                if name == "oracle":
                    continue
                ruling = judge_submission(control_submission(name))["ruling"]
                if ruling["credited"]:
                    out.append(name)
            return out
        finally:
            ep.S_MIN, ep.C_MIN, ep.BA_FLOOR = saved

    # "Removed" is the floor's identity element, not zero: `BA > 0.0` still
    # refuses an arm with BA exactly 0, and a disabled floor has to refuse
    # nothing at all.
    return {
        "all_floors": credited_with(),
        "without_S_min": credited_with(S_min=-1.0),
        "without_c_min": credited_with(c_min=-1.0),
        "without_ba_floor": credited_with(ba_floor=-1.0),
    }
