"""出题机 -- the four question types of Theoria.md 1.11, one module each.

Every module in `BUILDERS` exposes the same four names, and nothing else is
required of it:

    PAPER_ID : str
        Stable.  It names the paper file, the truth file, and every report.

    build() -> Paper
        Deterministic.  Two builds over unchanged sources produce byte-identical
        sheets; there is no wall clock and no RNG without a pinned seed.

    reference_answers(paper, key_doc, mode) -> dict[item_id, answer]
        The calibration examinees.  `mode` is one of CALIBRATION_MODES.  This is
        what lets the marker be tested before it marks anything real: a paper
        that cannot produce a known-full-marks and a known-zero submission
        cannot tell us whether its own marker works.

    axes(report, key_doc, submission) -> dict
        Question-type-specific summary numbers.  Optional; may return {}.

Keeping the four types behind one interface is what makes the exam a protocol
rather than four scripts.  The runner does not know what a held-out item is.
"""

from __future__ import annotations

import importlib
from typing import Any, Dict, Tuple

from ..model import QUESTION_TYPES

#: question type -> module path.  Frozen alongside QUESTION_TYPES.
BUILDERS: Dict[str, str] = {
    "heldout": "exam.papers.heldout",
    "handover": "exam.papers.handover",
    "adaptation": "exam.papers.adaptation",
    "verdict": "exam.papers.verdict",
}

#: The four fake examinees every paper must be able to produce.
#:
#:   oracle     answers from ground truth            -> full marks, by construction
#:   null       submits nothing                      -> zero, by construction
#:   memoriser  perfect on what it has seen, nothing else
#:   bluffer    always gives the same confident answer
#:
#: The last two are not padding.  `memoriser` is the arm Theoria.md 1.11 warns
#: about -- "重放是对过去的预测,背题也能满分" -- and a held-out paper that
#: cannot separate it from `oracle` is not testing rules.  `bluffer` is the arm
#: with perfect sensitivity and no specificity, and a verdict paper that scores
#: it well is scoring confidence.
CALIBRATION_MODES: Tuple[str, ...] = ("oracle", "null", "memoriser", "bluffer")


def module_for(question_type: str) -> Any:
    if question_type not in BUILDERS:
        raise KeyError("no builder for question type %r; the four types are %s"
                       % (question_type, list(QUESTION_TYPES)))
    return importlib.import_module(BUILDERS[question_type])


def all_modules() -> Dict[str, Any]:
    return {qt: module_for(qt) for qt in BUILDERS}
