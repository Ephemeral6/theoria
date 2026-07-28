"""Marking for 题型 1 — held-out prediction.  One rubric, and it is all-or-nothing.

**Why there is no partial credit.**  The obvious alternative is cells-correct:
award the fraction of grid cells the answer got right.  It is rejected here, and
the reason is not austerity.  On a 7x7 A0 board a typical transition changes two
cells, so an examinee that returns the *input frame unchanged* already scores
47/49 = 96% under a cells-correct rubric — on every item, including the ones it
has no theory for.  The rubric would then be measuring board size.  Worse, it
would pay best exactly where the framework claims to be different: a theory that
tracks the right positions and draws them wrong (a0-spike README, "certify runs
through the compiled manual") would score 90-something and read as nearly right,
when the whole point of comparing rendered frames is that it is simply wrong.

So: the frame matches, or it does not.  `detail` carries the cell-level diff for
whoever is diagnosing the failure, and carries no weight at all.

**Abstention is a third thing.**  `{"abstain": true}` scores zero, like a wrong
answer, but is recorded as `abstained`.  The distinction earns nothing and is not
meant to: it exists so a report can say whether an examinee knew it did not know.
A framework that must be able to say "unsolvable" must also be able to say
nothing, and the two are only distinguishable if the marker keeps them apart.

**Pure function of (answer, truth, item).**  No world, no examinee id, no disk.
The rubric cannot tell whether it is marking a `replay` or a `heldout` item
except through `item.tags`, and it does not look — the split matters to `axes`,
which reads the report, not to the mark.

One consequence worth naming, because it looks like an omission: `detail` does
*not* say whether the examinee predicted any change.  It cannot.  The marker
rebuilds items from the answer key, so `item.paper` is empty by the time a rubric
sees it, and the frame *before* is on the paper side only.  Recovering it from
the truth would mean the rubric reading something the paper never showed the
examinee.  That statistic belongs in `axes()`, which holds the key document, and
it is left there rather than smuggled here.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

from ..model import Item, ItemScore, Rubric

RUBRIC_ID = "heldout.frame_exact"

#: Every value the A0 renderer can emit.  An answer containing anything else is
#: not a frame; refusing it here is cheaper than letting it compare unequal and
#: be reported as a near miss.
#:
#: It is the **default**, not the law, and the difference arrived with the world
#: factory.  A generated world's palette is its own -- `{floor:0, wall:1,
#: block:2, agent:6}` plus whatever its mechanisms add -- so a rubric that
#: hardcodes A0's four values rejects every frame from every generated world as
#: "not a frame", which reads on the report as an examinee that cannot format an
#: answer.  A paper therefore publishes its own alphabet on the truth side, and
#: this constant is what a paper that does not gets.
_LEGAL_CELLS = frozenset({0, 2, 4, 8})


def _legal_cells(truth: Dict[str, Any]) -> frozenset:
    """The palette this item's world can emit.

    On the truth side rather than the paper side on purpose: it is derivable
    from the expected frame anyway, so publishing it to the examinee would give
    away nothing, but the rubric's contract is that it is a pure function of
    (answer, truth, item) and the palette is a fact about the answer key.
    """
    declared = truth.get("legal_cells")
    if not declared:
        return _LEGAL_CELLS
    return frozenset(int(value) for value in declared)

_ABSTAIN = "__abstain__"


def _as_frame(value: Any,
              legal: Optional[frozenset] = None) -> Optional[List[List[int]]]:
    """Coerce an answer to a grid, or return None if it is not one.

    Two shapes are accepted, both promised in the paper's instructions: a bare
    list of rows, and `{"frame_after": [...]}`.  Accepting both is a decision
    about what is being measured -- an examinee that predicts the world correctly
    and wraps it differently has not made a prediction error, and a rubric that
    scored it as one would be marking JSON conventions.
    """
    if isinstance(value, dict):
        if value.get("abstain") is True:
            return None
        for field in ("frame_after", "frame", "after"):
            if field in value:
                return _as_frame(value[field], legal)
        return None
    if isinstance(value, str):
        return None
    if not isinstance(value, (list, tuple)) or not value:
        return None
    rows: List[List[int]] = []
    for row in value:
        if not isinstance(row, (list, tuple)) or not row:
            return None
        cells: List[int] = []
        for cell in row:
            # bool is an int in Python and would silently compare equal to 0/1;
            # a frame of booleans is a malformed answer, not a frame of zeros.
            if isinstance(cell, bool) or not isinstance(cell, int):
                return None
            if cell not in (legal if legal is not None else _LEGAL_CELLS):
                return None
            cells.append(cell)
        rows.append(cells)
    if len({len(r) for r in rows}) != 1:
        return None
    return rows


def _is_abstention(value: Any) -> bool:
    if isinstance(value, dict):
        return value.get("abstain") is True
    if isinstance(value, str):
        return value.strip().lower() in ("abstain", "abstained", "unknown",
                                         "i cannot tell")
    return False


def _diff(answer: Sequence[Sequence[int]],
          truth: Sequence[Sequence[int]]) -> Tuple[bool, int]:
    """(same shape, number of cells that differ).  Diagnostic only."""
    if len(answer) != len(truth) or any(len(a) != len(t)
                                        for a, t in zip(answer, truth)):
        return False, -1
    wrong = sum(1 for a_row, t_row in zip(answer, truth)
                for a, t in zip(a_row, t_row) if a != t)
    return True, wrong


def grade_frame_exact(answer: Any, truth: Dict[str, Any], item: Item) -> ItemScore:
    expected = truth.get("frame_after")

    if answer is None:
        # An explicit null is not an abstention and not a frame.  It is treated as
        # nothing submitted, which is what it is.
        return ItemScore(item.item_id, item.rubric_id, 0.0, item.points,
                         "unanswered", {"why": "null answer"})

    if _is_abstention(answer):
        return ItemScore(item.item_id, item.rubric_id, 0.0, item.points,
                         "abstained",
                         {"why": "the examinee declined to predict this frame"})

    frame = _as_frame(answer, _legal_cells(truth))
    if frame is None:
        return ItemScore(item.item_id, item.rubric_id, 0.0, item.points, "wrong",
                         {"why": "answer is not a well-formed frame",
                          "expected_shape": [len(expected), len(expected[0])]
                          if expected else None})

    shape_ok, cells_wrong = _diff(frame, expected)
    correct = shape_ok and cells_wrong == 0
    detail: Dict[str, Any] = {
        "shape_ok": shape_ok,
        # Reported, never rewarded.  See the module docstring: a cells-correct
        # score on a 7x7 board is ~96% for doing nothing at all.
        "cells_wrong": cells_wrong,
    }
    return ItemScore(item.item_id, item.rubric_id,
                     item.points if correct else 0.0, item.points,
                     "correct" if correct else "wrong", detail)


FRAME_EXACT = Rubric(
    rubric_id=RUBRIC_ID,
    description=("held-out prediction: the predicted frame must equal the true "
                 "frame cell for cell. No partial credit -- a cells-correct score "
                 "on a 7x7 board is ~96% for returning the input unchanged, so it "
                 "would measure board size rather than theory. Abstention is "
                 "recorded and scores zero."),
    grade=grade_frame_exact,
)

RUBRICS: Tuple[Rubric, ...] = (FRAME_EXACT,)
