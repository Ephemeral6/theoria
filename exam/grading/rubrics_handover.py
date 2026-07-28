"""Marking rules for the layered handover paper (Theoria.md 1.11, 题型 2).

Three rubrics, one per question family, and one parser shared between them.

**Why the grammar is written down here and not inferred.**  A handover paper is
answered by a *fresh reader* -- a person or an agent that has never seen this
repository -- so the answers arrive as text.  The temptation is to read them
charitably: "(2,3) box moved left" obviously means the same as
`player=(2,3); box=(3,1); rule=push2`, so why not accept it?  Because a rubric
that guesses is a rubric that can be re-guessed after the answers are in, and
the whole point of `registry.digest()` is that it cannot.  So: one grammar,
published in every bundle's `READER_BRIEF.md`, and an answer outside it scores
zero with the parse failure recorded in `detail`.  The reader was told exactly
what to write; failing to write it is a fact about the reader, not noise to be
smoothed away.

**Where the grammar is deliberately loose.**  Case, surrounding whitespace, the
space after a comma inside a cell, and the order of the three fields of a
step-semantics answer.  None of those carry information, so insisting on them
would measure typing rather than understanding.  Every looseness here is a
normalisation applied *before* comparison and applied identically to every
answer -- never a judgement about what one particular answer probably meant.

**One rubric is set-valued on purpose.**  `optimal_action` accepts any action
that lies on *some* shortest solution, not the one the BFS oracle happened to
return.  Ties in a shortest-path search are broken by the order the successor
loop happens to run in; marking against that order would fail a reader for
agreeing with the world and disagreeing with an implementation detail.  The
truth therefore carries the whole accepted set, and `exam/tests/test_handover.py`
re-derives that set by brute force so the set itself cannot quietly narrow.

`abstain` is accepted by all three rubrics and scores zero with verdict
`abstained`.  It is not generosity: a reader who cannot decide and says so is
telling us something different from a reader who guesses, and Theoria 1.11 grades
sensitivity and specificity as a pair everywhere else too.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ..model import Item, ItemScore, Rubric

#: The five rules of the A0 manual, in the manual's own spelling.  Frozen: an
#: answer naming a rule outside this set is unparseable, not wrong-but-close.
RULE_NAMES: Tuple[str, ...] = (
    "walk", "push2", "blocked_wall", "blocked_box_crossing",
    "blocked_box_landing",
)

#: The four actions of the A0 world.
ACTIONS: Tuple[str, ...] = ("UP", "DOWN", "LEFT", "RIGHT")

#: The two classes of the vocabulary question.
NAME_CLASSES: Tuple[str, ...] = ("level_data", "world_law")

#: The one thing every rubric accepts outside its own alphabet.
ABSTAIN = "abstain"

_CELL = re.compile(r"^\(\s*(-?\d+)\s*,\s*(-?\d+)\s*\)$")
_FIELD = re.compile(r"^([A-Za-z_]+)\s*=\s*(.+)$")


class ParseFailure(Exception):
    """The answer is not a sentence of the published grammar."""


# ------------------------------------------------------------------- parsing

def normalise(answer: Any) -> str:
    """Collapse the differences that carry no information, and only those.

    A non-string answer is stringified rather than refused, because a reader
    that emitted a JSON number where a string was asked for has still said
    something checkable; the grammar below will reject it if it is not a
    sentence.  What is *not* done here is any rewriting of content.
    """
    return " ".join(str(answer).split()).strip()


def parse_cell(text: str) -> Tuple[int, int]:
    match = _CELL.match(text.strip())
    if not match:
        raise ParseFailure(
            "expected a cell written (row,col) with integer row and col, got %r"
            % text)
    return int(match.group(1)), int(match.group(2))


def parse_step_answer(answer: Any) -> Dict[str, Any]:
    """`player=(r,c); box=(r,c); rule=<name>` -- all three, order free.

    Semicolons separate; `=` binds.  Exactly the three keys, no more and no
    fewer: a missing field is not an omission the marker may fill in, and an
    extra field means the reader answered a question that was not asked.
    """
    text = normalise(answer)
    if text.lower() == ABSTAIN:
        return {"abstain": True}
    parts = [p for p in text.split(";") if p.strip()]
    fields: Dict[str, str] = {}
    for part in parts:
        match = _FIELD.match(part.strip())
        if not match:
            raise ParseFailure(
                "%r is not a `key=value` field; the grammar is "
                "`player=(r,c); box=(r,c); rule=<name>`" % part.strip())
        key = match.group(1).strip().lower()
        if key in fields:
            raise ParseFailure("field %r given twice" % key)
        fields[key] = match.group(2).strip()
    expected = {"player", "box", "rule"}
    if set(fields) != expected:
        raise ParseFailure(
            "expected exactly the fields %s, got %s"
            % (sorted(expected), sorted(fields)))
    rule = fields["rule"].strip()
    if rule not in RULE_NAMES:
        raise ParseFailure(
            "%r is not one of the manual's rule names %s"
            % (rule, list(RULE_NAMES)))
    return {"abstain": False,
            "player": parse_cell(fields["player"]),
            "box": parse_cell(fields["box"]),
            "rule": rule}


def parse_class_answer(answer: Any) -> Dict[str, Any]:
    """`level_data` | `world_law` | `abstain`.  Nothing else, in any case."""
    text = normalise(answer).lower()
    if text == ABSTAIN:
        return {"abstain": True}
    if text not in NAME_CLASSES:
        raise ParseFailure(
            "%r is not one of %s (or %r)"
            % (normalise(answer), list(NAME_CLASSES), ABSTAIN))
    return {"abstain": False, "class": text}


def parse_action_answer(answer: Any) -> Dict[str, Any]:
    """`UP` | `DOWN` | `LEFT` | `RIGHT` | `abstain`, case-insensitive."""
    text = normalise(answer)
    if text.lower() == ABSTAIN:
        return {"abstain": True}
    upper = text.upper()
    if upper not in ACTIONS:
        raise ParseFailure(
            "%r is not one of %s (or %r)" % (text, list(ACTIONS), ABSTAIN))
    return {"abstain": False, "action": upper}


# -------------------------------------------------------------------- marking

def _parse_failed(item: Item, exc: ParseFailure, said: Any) -> ItemScore:
    return ItemScore(item.item_id, item.rubric_id, 0.0, item.points, "wrong",
                     {"parse_error": str(exc), "raw": str(said)[:200],
                      "said": None})


def _abstained(item: Item) -> ItemScore:
    return ItemScore(item.item_id, item.rubric_id, 0.0, item.points,
                     "abstained", {"said": ABSTAIN})


def grade_step(answer: Any, truth: Dict[str, Any], item: Item) -> ItemScore:
    """All three fields or nothing.

    No partial credit, and the reason is the same one `a0-spike/README.md` gives
    for comparing rendered frames rather than internal state: a theory that puts
    the box in the right place and the player in the wrong one has predicted the
    wrong situation.  Half marks would let a reader who never worked out that a
    push also moves the pusher look like a reader who did.
    """
    try:
        got = parse_step_answer(answer)
    except ParseFailure as exc:
        return _parse_failed(item, exc, answer)
    if got["abstain"]:
        return _abstained(item)

    want_player = tuple(truth["next_player"])
    want_box = tuple(truth["next_box"])
    want_rule = truth["rule"]
    said = "player=(%d,%d); box=(%d,%d); rule=%s" % (
        got["player"][0], got["player"][1], got["box"][0], got["box"][1],
        got["rule"])
    correct = (got["player"] == want_player and got["box"] == want_box
               and got["rule"] == want_rule)
    detail = {
        "said": said,
        "player_ok": got["player"] == want_player,
        "box_ok": got["box"] == want_box,
        "rule_ok": got["rule"] == want_rule,
    }
    return ItemScore(item.item_id, item.rubric_id,
                     item.points if correct else 0.0, item.points,
                     "correct" if correct else "wrong", detail)


def grade_name_class(answer: Any, truth: Dict[str, Any],
                     item: Item) -> ItemScore:
    """Two classes, one right.  The cheapest rubric and the sharpest question."""
    try:
        got = parse_class_answer(answer)
    except ParseFailure as exc:
        return _parse_failed(item, exc, answer)
    if got["abstain"]:
        return _abstained(item)
    correct = got["class"] == truth["class"]
    return ItemScore(item.item_id, item.rubric_id,
                     item.points if correct else 0.0, item.points,
                     "correct" if correct else "wrong",
                     {"said": got["class"]})


def grade_optimal_action(answer: Any, truth: Dict[str, Any],
                         item: Item) -> ItemScore:
    """Correct iff the action lies on *some* shortest solution.

    `truth["optimal_actions"]` is the whole accepted set, computed by the world's
    own BFS oracle over every action out of the state, not the first plan the
    oracle returned.  Marking against a single tie-break would fail a reader for
    disagreeing with an iteration order.
    """
    try:
        got = parse_action_answer(answer)
    except ParseFailure as exc:
        return _parse_failed(item, exc, answer)
    if got["abstain"]:
        return _abstained(item)
    accepted = [str(a).upper() for a in truth["optimal_actions"]]
    correct = got["action"] in accepted
    return ItemScore(item.item_id, item.rubric_id,
                     item.points if correct else 0.0, item.points,
                     "correct" if correct else "wrong",
                     {"said": got["action"], "n_accepted": len(accepted)})


RUBRICS: Tuple[Rubric, ...] = (
    Rubric("handover.step_semantics",
           "One transition of the A0 manual: the next Player cell, the next Box "
           "cell and the rule that fired, all three or nothing.",
           grade_step),
    Rubric("handover.name_class",
           "Is this name something the level supplies (level_data) or something "
           "the world fixes across every level (world_law)?",
           grade_name_class),
    Rubric("handover.optimal_action",
           "An action lying on some shortest solution from the given state; the "
           "whole optimal set is accepted, not one tie-break.",
           grade_optimal_action),
)
