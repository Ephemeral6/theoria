"""Marking rules for question type 3 — rule-change adaptation.

Theoria.md 1.11: 「改一条规则,多快适应回来」.  `a0-spike/pipeline/adapt.py` does
this once, by hand, in a script; this module marks the mechanised version of it.
Four families, four rubrics:

    adapt.detect.v1        at which observation did the old theory first mispredict?
    adapt.detect_cross.v1  the same question asked of every level at once
    adapt.describe.v1      what changed, from a closed alphabet
    adapt.collateral.v1    what does the change take down, and does the old verdict hold
    adapt.repair.v1        what did the repair cost, and is the repaired theory exact

**This module is public to the examinee.**  It has to be: `exam/model.py` puts a
`rubric_digest` on every sheet precisely so the marking is frozen and readable
before any answer exists.  That has a consequence this file obeys throughout —
*the answer alphabets live here, and nothing else does*.  There is no variant
table here, no worked example, no aside about which change breaks what.  The
sheet points at this file for the vocabulary an answer must be written in
(`CHANGE_LABELS`, `CLAIMS`, `MANUAL_RULES`, `VERDICTS`), and pointing at a file
that also contained the answers would be a leak with a digest on it.

The heaviest weight in the paper is on `collateral`, and the reason is the one
`adapt.py` states in its own docstring: detection and repair are engineering,
but a theorem that silently becomes false is the failure this whole architecture
exists to prevent.  `[depends: push2]` on the A0 theorem is not decoration —
under some variants the verdict on `mismatch` flips outright, and a framework
that skipped the dependency step would go on confidently declaring a now-winnable
level impossible.  So the collateral rubric does two things no other rubric here
does: it grades the *reason* (which rules and which claims) separately from the
*verdict*, and it raises a `silently_wrong` flag in `detail` whenever an examinee
keeps the old verdict on a variant where it has flipped.  `axes()` surfaces that
flag as its own integer rather than folding it into a percentage, because an
examinee can score a respectable fraction here while being silently wrong twice,
and the fraction is the number that would hide it.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

from ..model import Item, ItemScore, Rubric

# --------------------------------------------------------------- alphabets

#: The closed alphabet of rule-change labels.  An answer to a `describe` item is
#: a subset of these keys.  The descriptions are written in the world's *visible*
#: vocabulary rather than in the names of the fields that were flipped: naming
#: the fields here would put the changed-rule label in the examinee's hands the
#: moment the sheet points at this file.
CHANGE_LABELS: Dict[str, str] = {
    "chg-box-travel-1":
        "a pushed box comes to rest one cell from where it started",
    "chg-box-travel-3":
        "a pushed box comes to rest three cells from where it started",
    "chg-box-crosses-blocked":
        "a pushed box may pass through a cell that is not clear, provided the "
        "cell it comes to rest on is clear",
    "chg-actor-enters-blocked":
        "the moving figure is no longer stopped by the board's fixed "
        "obstructions",
}

#: The five rules of the A0 manual, by the manual's own names.  A `collateral`
#: answer names the subset that the change falsifies.
MANUAL_RULES: Tuple[str, ...] = (
    "blocked_box_crossing", "blocked_box_landing", "blocked_wall", "push2",
    "walk",
)

#: The four registered claims of the A0 manual: three invariants and one
#: theorem.  Two questions are asked about this set and they are not the same
#: question -- "must be re-examined" is a dependency fact, "is now false" is a
#: semantic one, and the distance between them is exactly the work a theory
#: framework is supposed to do.  An examinee that collapses them scores badly on
#: one of the two halves whichever way it collapses them.
CLAIMS: Tuple[str, ...] = (
    "box_col_parity", "box_parity", "box_row_parity", "unsolvable_mismatch",
)

#: The verdict alphabet for the standing claim about the level named `mismatch`.
VERDICTS: Tuple[str, ...] = ("solvable", "unsolvable", "abstain")

#: The verdict the old manual holds before any rule is changed.  Kept here
#: because the `silently_wrong` flag is defined against it, and a flag whose
#: definition lives in a different file drifts away from the flag.
OLD_VERDICT = "unsolvable"

ABSTAIN_TOKENS = frozenset({"abstain", "unknown", "cannot tell", "i cannot tell"})


# ------------------------------------------------------------ answer reading

def _is_abstain(answer: Any) -> bool:
    if isinstance(answer, str):
        return answer.strip().lower() in ABSTAIN_TOKENS
    if isinstance(answer, dict):
        if answer.get("abstain") is True:
            return True
        for key in ("verdict", "answer", "index", "detected"):
            value = answer.get(key)
            if isinstance(value, str) and value.strip().lower() in ABSTAIN_TOKENS:
                return True
    return False


#: What `_read_claim` returns when the answer says nothing it can read.  Kept as
#: a named constant because the whole point is that this outcome is *not* the
#: same as claiming "it never diverged here" -- see below.
UNREADABLE = (False, False, None)


def _read_claim(answer: Any) -> Tuple[bool, bool, Optional[int]]:
    """(legible, claims a detection, the claimed 1-based index).

    Deliberately forgiving about *shape* and strict about *content*.  Four
    spellings of "it never diverged here" are accepted -- the string "never",
    `False`, `{"detected": false}`, and `{"index": null}` -- because the shape
    of the answer is not what is being measured and a rubric that marks a right
    answer wrong for punctuation is measuring formatting.  Nothing about the
    number itself is forgiven; that is the measurement.

    **Legibility is the third outcome, and it used to be missing.**  Until
    V4-exam-selftest this function had two outcomes, and everything it could not
    parse -- an unparseable string, `""`, `{}`, a bare `null` -- fell through to
    "did not claim a detection", which the caller then wrote down as the
    substantive answer `never`.  On `v-a0-03`, the one variant that is genuinely
    undetectable on its base level, `never` **is** the truth, so a submission of
    pure nonsense collected that item in full: measured at 1.6 of 144 points on
    this paper for `"__V4_GARBAGE__"`, `""`, `{}` and `null` alike, all of it on
    the two `v-a0-03.detect` items.

    That is the failure this paper exists to catch, wearing the marker's
    uniform: the item asks whether an examinee can tell "the change is
    invisible from here" from "I did not look", and the marker could not tell
    those apart either.  A forgiving reader may not invent a claim the examinee
    did not make; an illegible answer is now `wrong` with `said` recorded as
    `unreadable`, worth nothing and distinguishable in the report from both a
    real "never" and an abstention.

    One asymmetry is deliberate.  A **bare** `None` is illegible, but a `None`
    *value under a key the examinee wrote down* is a legible "never": in
    `{"per_level": {"match": null}}` the examinee named the level and declined
    to give it an index, which is an assertion.  A bare `null` asserts nothing
    and is what a broken serialiser emits.  Presence of the key is the claim.
    """
    if answer is None:
        return UNREADABLE
    if isinstance(answer, bool):        # bool before int: True is not index 1
        return True, bool(answer), None
    if isinstance(answer, int):
        return True, True, int(answer)
    if isinstance(answer, str):
        text = answer.strip().lower()
        if text in ("never", "none", "not detected", "no divergence"):
            return True, False, None
        try:
            return True, True, int(text)
        except ValueError:
            return UNREADABLE
    if isinstance(answer, dict):
        if "index" in answer or "detected" in answer:
            detected = answer.get("detected")
            index = answer.get("index")
            if detected is False:
                return True, False, None
            if isinstance(index, bool):
                index = None
            if isinstance(index, str):
                try:
                    index = int(index.strip())
                except ValueError:
                    index = None
            if index is None:
                return True, bool(detected), None
            return True, True, int(index)
    return UNREADABLE


def _read_level_claim(said_map: Dict[str, Any], level: str
                      ) -> Tuple[bool, bool, Optional[int]]:
    """`_read_claim` for one level of a per-level map.

    A level the examinee did not mention is illegible: not answered, not
    "never".  A level they did mention with a `null` index is a legible "never",
    which is the spelling the reference answers use.
    """
    if level not in said_map:
        return UNREADABLE
    value = said_map[level]
    if value is None:
        return True, False, None
    return _read_claim(value)


def _read_set(answer: Any, key: str) -> Optional[List[str]]:
    if isinstance(answer, dict):
        value = answer.get(key)
    else:
        value = answer
    if value is None:
        return None
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, (list, tuple, set)):
        return None
    return sorted({str(v).strip() for v in value})


def _read_verdict(answer: Any) -> Optional[str]:
    if isinstance(answer, str):
        text = answer.strip().lower()
        return text if text in VERDICTS else None
    if isinstance(answer, dict):
        for key in ("verdict", "mismatch_verdict", "claim"):
            value = answer.get(key)
            if isinstance(value, str) and value.strip().lower() in VERDICTS:
                return value.strip().lower()
    return None


def _read_bool(answer: Any, key: str) -> Optional[bool]:
    if not isinstance(answer, dict):
        return None
    value = answer.get(key)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in ("true", "yes", "exact"):
            return True
        if text in ("false", "no", "inexact"):
            return False
    return None


def _read_int(answer: Any, key: str) -> Optional[int]:
    if not isinstance(answer, dict):
        return None
    value = answer.get(key)
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and float(value).is_integer():
        return int(value)
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return None
    return None


# ------------------------------------------------------------ partial credit

#: Detection-latency tolerance bands, as (max absolute error, fraction awarded).
#:
#: The bands are tied to the shape of the evidence, not chosen for feel.  The
#: streams are *episodes*: the deterministic explorer resets, replays a prefix,
#: and takes one witnessing action, so the base level's 60 episodes average 5.68
#: actions and the longest is 14.  Therefore:
#:
#:   |error| <= 2  the examinee named the same action, off by a boundary
#:                 convention -- 0- versus 1-based counting, or whether the
#:                 action that surprised the theory is counted before or after.
#:   |error| <= 8  the examinee named the adjacent episode: it found the same
#:                 kind of surprise but mis-counted one reset.
#:   beyond        a different event.  Nothing is owed.
#:
#: All-or-nothing was rejected here, and only here among the set-valued
#: questions, because this item's answer *is* a latency.  Saying 17 where the
#: truth is 18, on a stream of 921 actions, is a different act from saying 400,
#: and an exam that scores them the same cannot report the quantity Theoria.md
#: 1.11 asks for ("多快适应回来") -- it can only report a hit rate.  The bands are
#: coarse and few on purpose: a smooth decay would pay for answers that are
#: merely in the neighbourhood, and "within 40 actions" has no meaning here.
#:
#: Two failures are NOT on this curve and never earn anything: claiming a
#: detection on a level where the change is undetectable (a false alarm on the
#: item designed to separate a real diagnosis from a plausible one), and
#: claiming "never" where the theory was in fact caught out.  They are opposite
#: errors and `axes()` counts them separately.
DETECTION_BANDS: Tuple[Tuple[int, float], ...] = ((0, 1.0), (2, 0.6), (8, 0.25))

#: Repair-budget tolerance, as (max relative error, fraction awarded).
#:
#: The budget is a count of actions produced by a fully deterministic
#: enumeration: an examinee that actually ran the stated protocol gets it
#: exactly, so the bands are not a generosity, they are a way of telling two
#: different failures apart.  2% is about five episodes on the smallest
#: evidence set (1478 actions) -- an off-by-one in one corner of the
#: enumeration.  10% is "the same order of magnitude", which is what the number
#: is for: Theoria.md 1.11 wants the *shape* of the repair bill, not its last
#: digit.  Anything past that is a guess and scores nothing.
BUDGET_BANDS: Tuple[Tuple[float, float], ...] = ((0.0, 1.0), (0.02, 0.7), (0.10, 0.3))


def _index_fraction(said: Optional[int], truth: Optional[int]) -> float:
    """Fraction earned for a claimed first-divergence index against the truth."""
    if truth is None:
        return 1.0 if said is None else 0.0
    if said is None:
        return 0.0
    error = abs(int(said) - int(truth))
    for limit, fraction in DETECTION_BANDS:
        if error <= limit:
            return fraction
    return 0.0


def _budget_fraction(said: Optional[int], truth: int) -> float:
    if said is None:
        return 0.0
    if truth == 0:
        return 1.0 if said == 0 else 0.0
    relative = abs(int(said) - truth) / float(truth)
    for limit, fraction in BUDGET_BANDS:
        if relative <= limit:
            return fraction
    return 0.0


def _score(item: Item, fraction: float, said: Any, detail: Dict[str, Any],
           *, abstained: bool = False) -> ItemScore:
    fraction = max(0.0, min(1.0, float(fraction)))
    if abstained:
        verdict = "abstained"
    elif fraction >= 1.0:
        verdict = "correct"
    else:
        verdict = "wrong"
    payload = dict(detail)
    payload["said"] = said
    payload["fraction"] = round(fraction, 6)
    return ItemScore(item.item_id, item.rubric_id, round(item.points * fraction, 6),
                     item.points, verdict, payload)


# ------------------------------------------------------------------ rubrics

def grade_detect(answer: Any, truth: Dict[str, Any], item: Item) -> ItemScore:
    """One variant, one level: when was the old theory first caught out?

    Truth is `{"detected": bool, "index": int|None}` with a 1-based index,
    computed by replaying the old theory against the variant world along the
    deterministic exploration -- the same walk `adapt.py::detection_latency`
    takes, so the number is a property of the world and the theory rather than
    of a lucky action order.
    """
    if _is_abstain(answer):
        return _score(item, 0.0, "abstain", {"why": "abstained"}, abstained=True)

    legible, claimed, index = _read_claim(answer)
    if not legible:
        return _score(item, 0.0, "unreadable",
                      {"why": "the answer states neither an observation index "
                              "nor that the change was never detected; a "
                              "reader may not invent the claim it cannot read"})
    truth_index = truth.get("index")
    fraction = _index_fraction(index if claimed else None, truth_index)

    detail: Dict[str, Any] = {"claimed_index": index if claimed else None,
                              "truth_index": truth_index}
    if truth_index is None and claimed:
        detail["false_alarm"] = True
        detail["why"] = ("the change is undetectable on this level; a claimed "
                         "detection is a plausible answer, not a diagnosis")
    elif truth_index is not None and not claimed:
        detail["missed"] = True
    said = "detected" if claimed else "never"
    return _score(item, fraction, said, detail)


def grade_detect_cross(answer: Any, truth: Dict[str, Any], item: Item) -> ItemScore:
    """The same variant seen from every level at once.

    `adapt.py::detection_across_levels` is the reference: where you look changes
    whether you notice at all, so latency is reported per level rather than as
    one number.  The answer is the whole map, and the score is the mean of the
    per-level bands -- which is why a bluffer that claims an early detection
    everywhere cannot ride the majority answer to a good mark here, as it can on
    any single level taken alone.
    """
    if _is_abstain(answer):
        return _score(item, 0.0, "abstain", {"why": "abstained"}, abstained=True)

    truth_map: Dict[str, Any] = truth.get("per_level", {})
    said_map: Dict[str, Any] = {}
    if isinstance(answer, dict):
        candidate = answer.get("per_level", answer)
        if isinstance(candidate, dict):
            said_map = candidate

    per_level: Dict[str, float] = {}
    unreadable: List[str] = []
    said_never: List[str] = []
    for level in sorted(truth_map):
        legible, claimed, index = _read_level_claim(said_map, level)
        if not legible:
            # A level the examinee never mentioned is not a claim that nothing
            # happened there. Scoring it as one paid an empty submission for the
            # levels whose truth is `None` -- see `_read_claim`.
            unreadable.append(level)
            per_level[level] = 0.0
            continue
        if not claimed:
            said_never.append(level)
        per_level[level] = _index_fraction(index if claimed else None,
                                           truth_map[level])
    fraction = (sum(per_level.values()) / len(per_level)) if per_level else 0.0

    detail = {"per_level_fraction": {k: round(v, 6) for k, v in per_level.items()},
              "claimed_never_on": sorted(said_never),
              "unreadable_on": sorted(unreadable),
              "truth_never_on": sorted(k for k, v in truth_map.items() if v is None)}
    if len(unreadable) == len(truth_map):
        said = "unreadable"
    elif len(said_never) == len(truth_map):
        said = "never"
    else:
        said = "detected"
    return _score(item, fraction, said, detail)


def grade_describe(answer: Any, truth: Dict[str, Any], item: Item) -> ItemScore:
    """What changed, as a subset of `CHANGE_LABELS`.

    Set equality, all or nothing.  Partial credit was rejected because the
    over-claiming half of the error is the point of one of the items: a variant
    can flip two fields of the world and still be *observationally* a one-label
    change, because at a travel distance of one cell there are no crossed cells
    for the crossing rule to govern.  Truth for such a variant is the minimal
    label set consistent with every observation, and an answer that names the
    unidentifiable second change is asserting something the evidence cannot
    support.  A Jaccard-style score would pay for exactly that, and would also
    pay a bluffer for naming the whole alphabet.
    """
    if _is_abstain(answer):
        return _score(item, 0.0, "abstain", {"why": "abstained"}, abstained=True)

    said = _read_set(answer, "labels")
    expected = sorted(truth.get("labels", []))
    unknown = sorted(set(said or []) - set(CHANGE_LABELS))
    exact = said is not None and said == expected and not unknown
    detail: Dict[str, Any] = {"claimed_labels": said, "n_expected": len(expected)}
    if unknown:
        detail["outside_alphabet"] = unknown
    return _score(item, 1.0 if exact else 0.0, "described" if said else "silent",
                  detail)


#: Weights inside a collateral item.  They add to 1.0 and every one of them is
#: an argument.
#:
#:   rules 0.30      which of the manual's five rules the change falsifies.  This
#:                   is where the repair has to be aimed; a wrong set is a repair
#:                   aimed at the wrong rule.
#:   reexamine 0.15  which registered claims the dependency edges force back onto
#:                   the bench.  Cheapest of the four -- on the A0 manual all
#:                   four claims hang off one rule, so the honest answer is
#:                   nearly always "all of them or none", and the item is worth
#:                   little precisely because it is nearly free.
#:   false 0.25      which claims are now actually false.  This is the one that
#:                   separates doing the re-examination from skipping it: on
#:                   several variants every claim must be re-examined and none of
#:                   them turns out to be false, and only an examinee that did
#:                   the work can say so.
#:   verdict 0.30    the standing verdict on `mismatch`.  Graded alone, and
#:                   reported alone, because it is the one an arm acts on.
COLLATERAL_WEIGHTS: Dict[str, float] = {
    "rules": 0.30, "reexamine": 0.15, "false": 0.25, "verdict": 0.30,
}


def grade_collateral(answer: Any, truth: Dict[str, Any], item: Item) -> ItemScore:
    """What the change takes down, and whether the old verdict survives.

    Three set-equality questions and one two-class verdict.  Sets are graded all
    or nothing: a half-right answer to "which rules broke" is a repair pointed
    half at the wrong rule, and set-overlap credit would pay an examinee for
    naming everything, which is precisely the arm this exam is built to catch.

    The `silently_wrong` flag in `detail` fires when the examinee keeps the old
    verdict on a variant where the verdict has flipped.  It is not a deduction
    -- the verdict weight already handles the deduction -- it is a *label*, so
    that `axes()` can report it as a count.  A framework can lose thirty percent
    of one item and look fine; a framework that declares a winnable level
    impossible has failed at the one thing the dependency annotation exists for.
    """
    if _is_abstain(answer):
        return _score(item, 0.0, "abstain", {"why": "abstained"}, abstained=True)

    said_rules = _read_set(answer, "rules_falsified")
    said_reexamine = _read_set(answer, "claims_to_reexamine")
    said_false = _read_set(answer, "claims_now_false")
    said_verdict = _read_verdict(answer)

    parts = {
        "rules": said_rules is not None
                 and said_rules == sorted(truth.get("rules_falsified", [])),
        "reexamine": said_reexamine is not None
                     and said_reexamine == sorted(truth.get("claims_to_reexamine", [])),
        "false": said_false is not None
                 and said_false == sorted(truth.get("claims_now_false", [])),
        "verdict": said_verdict is not None and said_verdict == truth.get("verdict"),
    }
    fraction = sum(COLLATERAL_WEIGHTS[k] for k, ok in parts.items() if ok)

    flipped = truth.get("verdict") != OLD_VERDICT
    silently_wrong = bool(flipped and said_verdict == OLD_VERDICT)
    detail: Dict[str, Any] = {
        "parts": {k: bool(v) for k, v in sorted(parts.items())},
        "claimed_rules": said_rules,
        "claimed_reexamine": said_reexamine,
        "claimed_false": said_false,
        "verdict_flipped": bool(flipped),
        "silently_wrong": silently_wrong,
    }
    if silently_wrong:
        detail["why"] = ("kept the old verdict on a variant where it flipped -- "
                         "the level is now winnable and the answer still calls it "
                         "impossible")
    return _score(item, fraction, said_verdict or "silent", detail)


#: Inside a repair item: what it cost, and whether it worked.  Exactness carries
#: the larger share because a cheap repair that is still wrong on unseen states
#: is not a repair -- Theoria.md 1.11 is explicit that replay is prediction about
#: the past and that a theory has to be scored on what it has not seen.
REPAIR_WEIGHTS: Dict[str, float] = {"budget": 0.4, "exact": 0.6}


def grade_repair(answer: Any, truth: Dict[str, Any], item: Item) -> ItemScore:
    """What the repair cost, and whether the repaired theory is exact off-history.

    `adapt.py::repair` is the reference implementation of the measurement, with
    one thing added that it does not do: exactness is checked on a held-out
    board the evidence never visited, not on the transitions that were replayed.
    Replay exactness is the thing a memoriser also has, so it cannot be the
    thing that is scored.
    """
    if _is_abstain(answer):
        return _score(item, 0.0, "abstain", {"why": "abstained"}, abstained=True)

    said_budget = _read_int(answer, "budget_actions")
    said_exact = _read_bool(answer, "exact_on_heldout")
    truth_budget = int(truth.get("budget_actions", 0))
    truth_exact = bool(truth.get("exact_on_heldout"))

    budget_fraction = _budget_fraction(said_budget, truth_budget)
    exact_ok = said_exact is not None and said_exact == truth_exact
    fraction = (REPAIR_WEIGHTS["budget"] * budget_fraction
                + REPAIR_WEIGHTS["exact"] * (1.0 if exact_ok else 0.0))

    detail = {"claimed_budget": said_budget, "truth_budget": truth_budget,
              "budget_fraction": round(budget_fraction, 6),
              "exactness_correct": bool(exact_ok)}
    said = ("exact" if said_exact else "inexact") if said_exact is not None else "silent"
    return _score(item, fraction, said, detail)


RUBRICS: Tuple[Rubric, ...] = (
    Rubric("adapt.detect.v1",
           "first observation at which the old theory mispredicts on one level; "
           "graded with episode-sized tolerance bands, no credit for a false "
           "alarm on a level where the change is undetectable",
           grade_detect),
    Rubric("adapt.detect_cross.v1",
           "the per-level map of first divergences for one variant; mean of the "
           "per-level bands, so a uniform guess cannot ride the majority answer",
           grade_detect_cross),
    Rubric("adapt.describe.v1",
           "the minimal set of rule-change labels consistent with the "
           "observations; set equality against CHANGE_LABELS",
           grade_describe),
    Rubric("adapt.collateral.v1",
           "falsified manual rules, claims to re-examine, claims now false, and "
           "the standing verdict on `mismatch`; raises silently_wrong when the "
           "old verdict is kept on a variant where it flipped",
           grade_collateral),
    Rubric("adapt.repair.v1",
           "the action budget a stated re-mining protocol spends and whether the "
           "re-mined theory is exact on a held-out board",
           grade_repair),
)
