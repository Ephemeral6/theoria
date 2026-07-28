"""Marking rules for the *automated* layered handover paper (V11).

Theoria.md 1.11 asks four things of a fresh reader who has been handed nothing
but a deliverable: what `step` means, which names are level data rather than
laws of the world, what the best action is from a given state, and **why a rule
holds**.  `rubrics_handover.py` (P-15) implements the first three.  The fourth
had no rubric at all, and the P-15 sheet saturated at 46/46 on both tiers, so
its tier difference measured nothing.  This module is the second attempt: the
missing family, plus two changes that give the other families somewhere to fail.

**What is new here, and why each change exists.**

1. `handover_auto.optimal_action` splits its two points.  One point for naming
   an action on a shortest solution -- the P-15 question -- and one for the
   *length* of that shortest solution.  A reader who guesses a plausible first
   move scores half; a reader who actually completed the search scores both.
   Length is the cheapest available proxy for "did you do the work", and doing
   the work is the quantity 1.11's pre-registered prediction is about.

2. The same rubric accepts `none`, and only `none`, on a board where the Box can
   never reach the target.  P-15 had no unsolvable board on the sheet, so a
   reader who had understood the parity law and a reader who had not answered
   identically.  `abstain` is still available and still scores zero: "I cannot
   tell" and "there is no such action" are different claims and the marker
   refuses to launder one into the other.

3. `handover_auto.rule_justification` is set-valued with a penalty.  The reader
   is given a claim and a fixed list of candidate clauses and must return the
   subset the claim's truth depends on.  Scoring is

       awarded = points * clamp01((|A n T| - |A \\ T|) / |T|)

   -- every clause that belongs is paid for, every clause that does not costs
   the same.  Without the subtraction the dominant strategy is to cite
   everything, and a rubric whose optimum is "say more" measures fluency.  Full
   marks require the exact set; partial credit is real but is recorded with
   verdict `wrong`, because `correct` in this exam means the answer was right,
   not that it was close.

4. `handover_auto.counterexample` is checked by executing the claim, not by
   comparing to a stored answer.  The A0 manual ships
   `invariant box_row_parity (Box.pos.row) mod 2 = 1` marked `proven`, and that
   sentence is false on most boards of its own world (`exam/STATUS.md`).  Asking
   a reader to *exhibit* a situation where a shipped theorem fails is the one
   question here whose marking cannot be argued with: the marker recomputes the
   claim at the situation the reader named.  The board geometry needed for the
   check travels in the item's `truth`, so the rubric stays a pure function of
   (answer, truth, item) and never reads the world off disk.

**The parsers are imported, not copied.**  `rubrics_handover` already publishes
a grammar for cells, rule names and classes, and two spellings of one grammar
drift apart.  The step and name-class rubrics here are the P-15 rubrics with new
ids; the digest of *this* module covers only what is new, and
`registry.module_digests()` reports both.

**Frozen before any answer existed.**  This file, the paper builder, and the
question sheet were committed before a single examinee was spawned; the commit
order is the evidence, and `exam/runs/<id>/BLINDING.md` names the commit.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Sequence, Set, Tuple

from ..model import Item, ItemScore, Rubric
from .rubrics_handover import (ABSTAIN, ACTIONS, NAME_CLASSES, RULE_NAMES,
                               ParseFailure, grade_name_class, grade_step,
                               normalise, parse_cell)

#: The token that says "no action begins a shortest solution, because there is
#: no solution".  Deliberately not `abstain`: one is a claim about the world,
#: the other is a claim about the reader.
NO_ACTION = "none"

#: Every clause of the A0 manual a justification item may ask about.  Frozen: a
#: citation outside this list is a parse failure, not a wrong answer, because
#: the reader was handed the list.
CITABLE: Tuple[str, ...] = (
    "walk", "push2", "blocked_wall", "blocked_box_crossing",
    "blocked_box_landing", "goal_box_on_target",
)

_FIELD = re.compile(r"^([A-Za-z_]+)\s*=\s*(.+)$")


def _fields(text: str, expected: Sequence[str]) -> Dict[str, str]:
    """`k=v; k=v` with exactly the expected keys, order free, case free."""
    out: Dict[str, str] = {}
    for part in [p for p in text.split(";") if p.strip()]:
        match = _FIELD.match(part.strip())
        if not match:
            raise ParseFailure(
                "%r is not a `key=value` field; the fields are %s"
                % (part.strip(), list(expected)))
        key = match.group(1).strip().lower()
        if key in out:
            raise ParseFailure("field %r given twice" % key)
        out[key] = match.group(2).strip()
    if set(out) != set(expected):
        raise ParseFailure("expected exactly the fields %s, got %s"
                           % (sorted(expected), sorted(out)))
    return out


def _parse_failed(item: Item, exc: ParseFailure, said: Any) -> ItemScore:
    return ItemScore(item.item_id, item.rubric_id, 0.0, item.points, "wrong",
                     {"parse_error": str(exc), "raw": str(said)[:200],
                      "said": None})


def _abstained(item: Item) -> ItemScore:
    return ItemScore(item.item_id, item.rubric_id, 0.0, item.points,
                     "abstained", {"said": ABSTAIN})


# ------------------------------------------------------- family 3, harder form

def parse_optimal_answer(answer: Any) -> Dict[str, Any]:
    """`action=<A|none>; plan_len=<n|none>` -- both fields, or `abstain`."""
    text = normalise(answer)
    if text.lower() == ABSTAIN:
        return {"abstain": True}
    fields = _fields(text, ("action", "plan_len"))
    action = fields["action"].strip()
    if action.lower() == NO_ACTION:
        action = NO_ACTION
    elif action.upper() in ACTIONS:
        action = action.upper()
    else:
        raise ParseFailure("%r is not one of %s (or %r, or %r)"
                           % (action, list(ACTIONS), NO_ACTION, ABSTAIN))
    raw_len = fields["plan_len"].strip()
    if raw_len.lower() == NO_ACTION:
        plan_len: Any = None
    else:
        try:
            plan_len = int(raw_len)
        except ValueError:
            raise ParseFailure(
                "plan_len must be a whole number of actions, or %r on a board "
                "with no solution; got %r" % (NO_ACTION, raw_len))
        if plan_len < 0:
            raise ParseFailure("plan_len cannot be negative; got %d" % plan_len)
    return {"abstain": False, "action": action, "plan_len": plan_len}


def grade_optimal_action(answer: Any, truth: Dict[str, Any],
                         item: Item) -> ItemScore:
    """Two independent halves: the move, and the length of the solution.

    They are scored separately on purpose.  A reader who names a good first move
    without finishing the search has understood the world and not yet paid the
    search cost, and that is precisely the state Theoria.md 1.11 predicts a
    manual-only reader to be in.  Folding the two into one all-or-nothing mark
    would erase the distinction the paper exists to measure.

    On a solvable board the accepted actions are the *whole* optimal set, for
    the reason `rubrics_handover.grade_optimal_action` gives: marking against one
    tie-break fails a reader for disagreeing with an iteration order.  On an
    unsolvable board the only accepted action is `none` and the only accepted
    length is `none`; a direction there is a wrong answer, not a near miss.
    """
    try:
        got = parse_optimal_answer(answer)
    except ParseFailure as exc:
        return _parse_failed(item, exc, answer)
    if got["abstain"]:
        return _abstained(item)

    solvable = bool(truth["solvable"])
    accepted = [str(a).upper() for a in truth.get("optimal_actions", ())]
    want_len = truth.get("plan_len")

    if solvable:
        action_ok = got["action"] in accepted
        len_ok = (got["plan_len"] is not None and got["plan_len"] == want_len)
    else:
        action_ok = got["action"] == NO_ACTION
        len_ok = got["plan_len"] is None

    half = item.points / 2.0
    awarded = (half if action_ok else 0.0) + (half if len_ok else 0.0)
    detail = {
        "said": "action=%s; plan_len=%s" % (
            got["action"], NO_ACTION if got["plan_len"] is None
            else got["plan_len"]),
        "action_ok": action_ok,
        "plan_len_ok": len_ok,
        "solvable": solvable,
        "n_accepted": len(accepted),
    }
    verdict = "correct" if (action_ok and len_ok) else "wrong"
    return ItemScore(item.item_id, item.rubric_id, awarded, item.points,
                     verdict, detail)


# ---------------------------------------------------- family 4, justification

def parse_justification_answer(answer: Any) -> Dict[str, Any]:
    """`rests_on=<name>+<name>+...`, or `rests_on=none`, or `abstain`."""
    text = normalise(answer)
    if text.lower() == ABSTAIN:
        return {"abstain": True}
    fields = _fields(text, ("rests_on",))
    body = fields["rests_on"].strip()
    if body.lower() == NO_ACTION:
        return {"abstain": False, "cited": frozenset()}
    names = [part.strip() for part in body.split("+") if part.strip()]
    if not names:
        raise ParseFailure(
            "rests_on must name at least one clause, or %r" % NO_ACTION)
    for name in names:
        if name not in CITABLE:
            raise ParseFailure("%r is not one of the clause names you were "
                               "given: %s" % (name, list(CITABLE)))
    return {"abstain": False, "cited": frozenset(names)}


def grade_rule_justification(answer: Any, truth: Dict[str, Any],
                             item: Item) -> ItemScore:
    """Set-valued, with a citation you should not have made costing what one you
    should have made earns.

        awarded = points * clamp01((|A n T| - |A \\ T|) / |T|)

    Full marks need the exact set.  Anything else is `wrong` with the partial
    credit recorded -- the verdict counts answers, the score measures them, and
    conflating the two would let a report of "8 correct" mean "8 nearly".

    A duplicate citation is collapsed rather than punished twice: `push2+push2`
    is one claim written clumsily, and the grammar is not the subject.
    """
    try:
        got = parse_justification_answer(answer)
    except ParseFailure as exc:
        return _parse_failed(item, exc, answer)
    if got["abstain"]:
        return _abstained(item)

    want: Set[str] = set(truth["rests_on"])
    cited: Set[str] = set(got["cited"])
    if not want:                     # never built; defended anyway
        raise ValueError("a justification item with an empty truth set cannot "
                         "be scored: division by zero, and no claim rests on "
                         "nothing")
    hit = len(cited & want)
    spurious = len(cited - want)
    ratio = (hit - spurious) / float(len(want))
    ratio = max(0.0, min(1.0, ratio))
    awarded = round(item.points * ratio, 6)
    exact = cited == want
    return ItemScore(item.item_id, item.rubric_id,
                     item.points if exact else awarded, item.points,
                     "correct" if exact else "wrong",
                     {"said": "+".join(sorted(cited)) if cited else NO_ACTION,
                      "hit": hit, "spurious": spurious,
                      "missing": sorted(want - cited),
                      "partial": (not exact) and awarded > 0.0})


# ----------------------------------------------------- family 4b, refutation

#: Claims this rubric knows how to recompute.  A claim id outside this table is
#: a build error, not a marking decision: the rubric will not guess what a
#: sentence means.
def _claim_box_row_mod2_eq_1(box: Tuple[int, int]) -> bool:
    return box[0] % 2 == 1


CLAIMS = {"box_row_mod2_eq_1": _claim_box_row_mod2_eq_1}


def parse_counterexample_answer(answer: Any) -> Dict[str, Any]:
    """`level=<id>; player=(r,c); box=(r,c)`, or `abstain`."""
    text = normalise(answer)
    if text.lower() == ABSTAIN:
        return {"abstain": True}
    fields = _fields(text, ("level", "player", "box"))
    return {"abstain": False,
            "level": fields["level"].strip(),
            "player": parse_cell(fields["player"]),
            "box": parse_cell(fields["box"])}


def grade_counterexample(answer: Any, truth: Dict[str, Any],
                         item: Item) -> ItemScore:
    """Recompute the claim where the reader says it fails.

    Three things have to hold and all three are checked here rather than assumed:
    the named board is one of the boards offered, the situation is legal on it
    (both cells on the board, neither a wall, and the two not the same cell),
    and the claim is genuinely false there.  A legal situation at which the claim
    happens to hold is a wrong answer, not a partial one -- the question asked
    for a refutation and a situation that satisfies the claim refutes nothing.

    All-or-nothing, and no credit for naming the right board with an illegal
    situation: a counterexample that is not a situation of the world is exactly
    the failure mode 1.11 wants certificates to rule out.
    """
    try:
        got = parse_counterexample_answer(answer)
    except ParseFailure as exc:
        return _parse_failed(item, exc, answer)
    if got["abstain"]:
        return _abstained(item)

    # A list of records rather than a dict keyed by board id, and deliberately
    # so: `leakage.structural_hits` compares *key names* across the two sides of
    # an item, and a truth keyed by board id shares every board id and every
    # geometry field with the sheet.  The check was right to refuse it -- the
    # fix is to stop putting answer-side data in key position, not to widen the
    # list of keys the check forgives.
    boards: Dict[str, Any] = {str(rec["id"]): rec
                              for rec in truth["legal_boards"]}
    claim_id = truth["claim"]
    if claim_id not in CLAIMS:
        raise ValueError("no checker for claim %r; the paper builder and this "
                         "rubric disagree about what was asked" % claim_id)

    said = "level=%s; player=(%d,%d); box=(%d,%d)" % (
        got["level"], got["player"][0], got["player"][1],
        got["box"][0], got["box"][1])
    detail: Dict[str, Any] = {"said": said}

    board = boards.get(got["level"])
    if board is None:
        detail["why"] = ("%r is not one of the boards you were given: %s"
                         % (got["level"], sorted(boards)))
        return ItemScore(item.item_id, item.rubric_id, 0.0, item.points,
                         "wrong", detail)

    walls = {tuple(w) for w in board["blocked"]}
    height, width = int(board["rows"]), int(board["cols"])

    def _legal(cell: Tuple[int, int]) -> bool:
        return (0 <= cell[0] < height and 0 <= cell[1] < width
                and cell not in walls)

    legal = (_legal(got["player"]) and _legal(got["box"])
             and got["player"] != got["box"])
    detail["situation_legal"] = legal
    if not legal:
        detail["why"] = ("the situation is not one this board can be in: both "
                         "cells must be on the board, neither a wall, and the "
                         "Player cannot stand on the Box")
        return ItemScore(item.item_id, item.rubric_id, 0.0, item.points,
                         "wrong", detail)

    holds = CLAIMS[claim_id](got["box"])
    detail["claim_holds_there"] = holds
    if holds:
        detail["why"] = ("the claim is true at this situation, so it is not a "
                         "counterexample")
    return ItemScore(item.item_id, item.rubric_id,
                     0.0 if holds else item.points, item.points,
                     "wrong" if holds else "correct", detail)


RUBRICS: Tuple[Rubric, ...] = (
    Rubric("handover_auto.step_semantics",
           "One transition of the A0 manual: next Player cell, next Box cell "
           "and the rule that fired, all three or nothing. Same marking as "
           "handover.step_semantics, new items.",
           grade_step),
    Rubric("handover_auto.name_class",
           "Is this name something the level supplies (level_data) or "
           "something the world fixes across every level (world_law)?",
           grade_name_class),
    Rubric("handover_auto.optimal_action",
           "Half the points for an action on some shortest solution (or `none` "
           "when there is no solution), half for the length of that shortest "
           "solution.",
           grade_optimal_action),
    Rubric("handover_auto.rule_justification",
           "The subset of the offered clauses the claim's truth depends on; "
           "hits pay, spurious citations cost the same, exact set for full "
           "marks.",
           grade_rule_justification),
    Rubric("handover_auto.counterexample",
           "A legal situation at which a claim the manual marks proven is "
           "false, checked by recomputing the claim there.",
           grade_counterexample),
)

#: Marking constants restated for the sheet, so the reader is told the alphabet
#: they will be marked against rather than left to infer it.
PUBLISHED = {
    "rule_names": list(RULE_NAMES),
    "name_classes": list(NAME_CLASSES),
    "actions": list(ACTIONS) + [NO_ACTION],
    "citable_clauses": list(CITABLE),
    "abstain": ABSTAIN,
}
