"""Generate the rule sets and certificates under `recheck/cases/`.

Written rather than hand-typed because a 148-entry neighbour table typed by
hand is a transcription bug waiting to be blamed on the rechecker.  The
generator is data-driven: the boards are literals, everything else follows from
them.  Output is byte-stable -- `python -m recheck.build_cases --check` fails if
a committed case has drifted from what the generator says it should be.

Six worlds:

* **peg4** -- Fixture C, four starts.  `0111` is the unsolvable configuration
  `ic3_pdr` returns an invariant for (STATUS.md, M9); `1101` is the solvable one
  it correctly refuses, and is here so a forged invariant has somewhere to fail;
  `1110` is the one `lp_potential` found a pagoda for.
* **peg5 .. peg13** -- the same world widened, which is axis A of the E8
  boundary measurement: 32 up to 8192 states, each with the invariant `ic3_pdr`
  converges on for it.  The rule sets are built here from the geometry; the
  invariants are transcribed literals.  That split is deliberate and is the
  two-transcriptions rule -- see `PEG_IC3_INVARIANTS`.
* **peg5** -- the 5-cell board theory-compiler's fixture uses, from `11011`,
  once per target cell.  Two rule sets rather than one because the two pagoda
  certificates differ only in the goal, and `interop/README.md`'s finding is
  precisely that the two targets are separately provable and their disjunction
  is not.
* **keyed-gate** -- three flags and one guarded rule, written for this package
  rather than transcribed.  It is the exhibit for the pagoda obligation being
  quantified over moves *legal from the region*: its only potential-raising move
  cannot fire below the bound, so a checker that reads deltas straight off the
  geometry rejects a sound certificate.
* **a2-holed** -- the A2 exhibit's manual: the 9x9 pushing world with the
  teleport rule deleted.  This is the rule set the Lean file
  `cold-start-a2/theory/generated_holed/theory.lean` proves `unsolvable` over,
  axiom-free.
* **a2-world** -- the same world *with* the teleport rule, i.e. A2's control
  manual, which its 18-action refutation established is the world's own rule
  set.  The two files differ by one rule and one event, exactly as
  `theory.dsl` and `theory_holed.dsl` do.
* **sokoban** -- Fixture D's `ringstuck` and `open4far`, multi-valued rather
  than grounded-STRIPS, so the deadlock patterns `deadlock_carver` emits can be
  rechecked against rules nobody grounded for them.

The boards are transcribed from the fixtures and from
`cold-start-a2/theory/generated_holed/theory.py`.  Transcription is the risk, so
it is checked twice and neither check is this file: `tests/test_recheck_a2.py`
replays A2's own recorded 18-action refutation episode through the generated
`a2-world` rules frame by frame, and compares the generated `a2-holed`
transition relation against the 592-line `step` table inside the Lean file Lean
itself accepted.
"""

import argparse
import hashlib
import json
import os
import sys
from typing import Dict, List, Optional, Sequence, Tuple

from recheck.ruleset import canonical_text

CASES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cases")

RULESET_SCHEMA = "engine-rig/recheck/ruleset-v1"
CERTIFICATE_SCHEMA = "engine-rig/recheck/certificate-v1"

Cell = Tuple[int, int]


def cell_name(cell: Cell) -> str:
    return "%d,%d" % cell


def lit(value) -> list:
    return ["lit", value]


def var(name: str) -> list:
    return ["var", name]


def eq(left, right) -> list:
    return ["=", left, right]


def dump(path: str, payload: dict) -> str:
    text = serialise(payload)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return text


# ============================================================== peg solitaire

PEG_N = 4
PEG_GOAL = "0100"

# The board size only ever appears in prose, and prose is what the committed
# bytes are made of, so it is a table rather than an f-string.  A gradient step
# whose size has no word here falls back to the digits, which reads fine.
PEG_SIZE_WORD = {
    4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
}
_NUMBER_WORDS = PEG_SIZE_WORD

# One anchor per board: a number somebody else published about that world,
# outside this package and before it.
PEG_HAND_VERIFIED = {
    4: "peg4.py's docstring: 1110, 0111 and 1011 are unsolvable; 1101 solves "
       "in 2 moves",
    5: "interop/README.md: 11011 reaches only {00111, 11100, 01001, 10010}, "
       "bottoming out at two pegs, so no single-peg goal is reachable from it",
}

PEG_WORLD = {
    4: "engine-rig/fixtures/peg4.py",
    5: "engine-rig/interop/peg1d.py, whose 4-cell board is tested against the "
       "frozen fixtures/peg4",
}


def peg_moves(n: int = PEG_N) -> List[Tuple[int, int, int]]:
    """Every jump the geometry allows, as (src, over, dst)."""
    out = []
    for i in range(n):
        for step in (1, -1):
            over, dst = i + step, i + 2 * step
            if 0 <= dst < n:
                out.append((i, over, dst))
    return sorted(out, key=lambda m: (m[0], m[2]))


def peg_name(start: str, n: int = PEG_N) -> str:
    return "peg%d-%s" % (n, start)


def _peg_goal_prose(goal: str) -> str:
    pegs = [i for i, cell in enumerate(goal) if cell == "1"]
    if len(pegs) == 1:
        return "exactly one peg, at position %d (state %s)" % (pegs[0], goal)
    return "state %s" % goal


def peg_ruleset(start: str, n: Optional[int] = None, goal: str = PEG_GOAL,
                name: Optional[str] = None) -> dict:
    """1D peg solitaire on `n` positions, as rules rather than as an edge list.

    Parameterised over `n` and `goal` because axis A of the E8 boundary
    measurement is a *gradient* in state-space size, and a gradient whose steps
    have no rule set has no independent checker either -- the point of the axis
    is to carry the "an independent checker accepts this" column all the way up
    it, not only at the M9 anchor.

    `n = 4` reproduces Fixture C exactly, bytes included; that case is the
    anchor and its wording is its own.

    A `name` overrides the start-derived one, because the 5-cell board carries
    two rule sets from one start: the pagoda certificates `lp_potential`
    produced for it differ only in which cell the last peg has to land on, and
    that difference is the whole finding in `interop/README.md`, so the two
    goals must not be allowed to share a file.  A named board is one of those
    hand-anchored cases and takes its provenance from the tables; an unnamed
    board wider than the anchor is a gradient step and takes the anchor prose.
    """
    if n is None:
        n = len(start)
    moves = peg_moves(n)
    if len(start) != n or len(goal) != n:
        raise ValueError("start %r and goal %r must both be %d positions"
                         % (start, goal, n))
    hand_anchored = n == PEG_N or name is not None
    provenance = {
        # peg4 is the frozen M1 fixture; every wider board comes from the
        # generic builder, which was written for lp_potential and knows nothing
        # about this package.
        "world": PEG_WORLD[n] if hand_anchored
                 else "engine-rig/interop/peg1d.py",
        "goal": _peg_goal_prose(goal),
    }
    if hand_anchored:
        provenance["hand_verified"] = PEG_HAND_VERIFIED[n]
    else:
        provenance["anchor"] = (
            "interop.peg1d -- an independent transcription of the same geometry, "
            "written for lp_potential before this gradient existed. verify_all "
            "compares its edge relation and its distance_to(%s, [%s]) against "
            "the relation derived here." % (start, goal)
        )
    return {
        "schema": RULESET_SCHEMA,
        "name": name or peg_name(start, n),
        "comment": "Fixture C, 1D peg solitaire on %s positions, started at "
                   "%s. A move jumps a peg over a neighbouring peg into an "
                   "empty hole and removes the jumped peg."
                   % (_NUMBER_WORDS.get(n, str(n)), start),
        "provenance": provenance,
        "variables": [
            {"name": "pos%d" % i, "domain": [0, 1],
             "comment": "1 if position %d holds a peg" % i}
            for i in range(n)
        ],
        "actions": ["jump(%d,%d,%d)" % move for move in moves],
        "init": {"pos%d" % i: int(start[i]) for i in range(n)},
        "goal": ["and"] + [
            eq(var("pos%d" % i), lit(int(goal[i]))) for i in range(n)
        ],
        "rules": [
            {
                "name": "jump_%d_%d_%d" % move,
                "action": "jump(%d,%d,%d)" % move,
                "guard": ["and",
                          eq(var("pos%d" % move[0]), lit(1)),
                          eq(var("pos%d" % move[1]), lit(1)),
                          eq(var("pos%d" % move[2]), lit(0))],
                "effects": {
                    "pos%d" % move[0]: lit(0),
                    "pos%d" % move[1]: lit(0),
                    "pos%d" % move[2]: lit(1),
                },
            }
            for move in moves
        ],
    }


# --------------------------------------------------------- the size gradient
#
# Axis A of E8: the M9 configuration widened.  Every step is the same shape --
# position 0 empty, every other position filled, goal a single peg at position 1
# -- so what changes along the axis is the size of the state space (16 up to
# 8192) and nothing else.  Every one of them is unsolvable, which
# `interop.peg1d.distance_to` says independently.
#
# 4..8 came first, one position at a time.  10, 12 and 13 were added afterwards
# because `ic3bounds.axis_size.LADDER` is (4, 6, 8, 10, 12, 13, 14) and the
# ladder's recheck column can only be filled at a size that has a rule set here:
# a gradient step with no independent transcription has no independent checker,
# and the column would have had to read "not available" at exactly the sizes the
# measurement is about.  n=14 is absent because IC3 does not finish it inside the
# 300s budget -- there is no invariant at that rung to check, and inventing a
# case for it would put a rule set in the tree that nothing certifies.
PEG_GRADIENT: Tuple[Tuple[int, str, str], ...] = (
    (4, "0111", "0100"),
    (5, "01111", "01000"),
    (6, "011111", "010000"),
    (7, "0111111", "0100000"),
    (8, "01111111", "01000000"),
    (10, "0111111111", "0100000000"),
    (12, "011111111111", "010000000000"),
    (13, "0111111111111", "0100000000000"),
)

# `ic3_pdr`'s answers, transcribed clause by clause, in the order
# `ic3bounds.emit.ordered_clauses` writes them.
#
# **Transcribed, not computed.**  This file is inside `recheck/`, which imports
# nothing from `engines/` -- a test enforces it -- so the invariants arrive here
# as literals, exactly as M9's did.  `tests/test_ic3bounds_emit.py` re-runs the
# engine and fails if what it converges on is no longer what is written below,
# which is the check that keeps a literal honest.
#
# Each clause is a tuple of `(variable, the value that satisfies it)`; a clause
# is a disjunction, the clause list a conjunction.
PEG_IC3_INVARIANTS: Dict[Tuple[int, str, str], dict] = {
    (4, "0111", "0100"): {
        "produced_by": "engines/ic3_pdr (M9)",
        "comment": "(!pos1 | pos2) & (pos1 | !pos2) -- positions 1 and 2 always "
                   "hold the same thing.",
        "clauses": (
            (("pos1", 0), ("pos2", 1)),
            (("pos1", 1), ("pos2", 0)),
        ),
    },
    (5, "01111", "01000"): {
        "clauses": (
            (("pos1", 0), ("pos2", 1), ("pos4", 1)),
            (("pos2", 0), ("pos3", 0), ("pos4", 1)),
        ),
    },
    (6, "011111", "010000"): {
        "clauses": (
            (("pos0", 0), ("pos1", 0), ("pos5", 1)),
            (("pos0", 0), ("pos2", 0), ("pos4", 0)),
            (("pos0", 0), ("pos3", 1), ("pos4", 0)),
            (("pos2", 0), ("pos3", 0), ("pos4", 1)),
            (("pos2", 0), ("pos3", 0), ("pos5", 1)),
            (("pos2", 0), ("pos3", 1), ("pos4", 0)),
            (("pos1", 0), ("pos2", 1), ("pos3", 1), ("pos5", 1)),
            (("pos1", 0), ("pos3", 0), ("pos4", 1), ("pos5", 0)),
        ),
    },
    (7, "0111111", "0100000"): {
        "clauses": (
            (("pos4", 0), ("pos5", 0), ("pos6", 1)),
            (("pos1", 0), ("pos3", 0), ("pos4", 1), ("pos6", 1)),
            (("pos2", 0), ("pos3", 0), ("pos4", 1), ("pos6", 1)),
            (("pos1", 0), ("pos2", 1), ("pos3", 1), ("pos4", 1), ("pos5", 1),
             ("pos6", 1)),
        ),
    },
    (8, "01111111", "01000000"): {
        "clauses": (
            (("pos1", 0), ("pos2", 0), ("pos3", 0), ("pos7", 1)),
            (("pos1", 0), ("pos4", 0), ("pos5", 0), ("pos7", 1)),
            (("pos1", 0), ("pos4", 0), ("pos5", 1), ("pos6", 0)),
            (("pos2", 0), ("pos4", 0), ("pos5", 0), ("pos7", 1)),
            (("pos2", 0), ("pos4", 0), ("pos5", 1), ("pos6", 0)),
            (("pos1", 0), ("pos2", 0), ("pos3", 0), ("pos5", 1), ("pos6", 0)),
            (("pos1", 0), ("pos2", 0), ("pos3", 1), ("pos4", 0), ("pos6", 0)),
            (("pos1", 0), ("pos3", 0), ("pos4", 1), ("pos5", 1), ("pos7", 1)),
            (("pos1", 0), ("pos3", 0), ("pos5", 0), ("pos6", 1), ("pos7", 0)),
            (("pos2", 0), ("pos3", 0), ("pos4", 1), ("pos5", 1), ("pos7", 1)),
            (("pos1", 0), ("pos2", 1), ("pos3", 1), ("pos4", 1), ("pos5", 1),
             ("pos6", 1), ("pos7", 1)),
        ),
    },
    (10, "0111111111", "0100000000"): {
        "clauses": (
            (("pos4", 0), ("pos6", 0), ("pos7", 0), ("pos9", 1)),
            (("pos4", 0), ("pos6", 0), ("pos7", 1), ("pos8", 0)),
            (("pos1", 0), ("pos3", 0), ("pos6", 0), ("pos7", 0), ("pos9", 1)),
            (("pos1", 0), ("pos3", 0), ("pos6", 0), ("pos7", 1), ("pos8", 0)),
            (("pos2", 0), ("pos3", 0), ("pos6", 0), ("pos7", 0), ("pos9", 1)),
            (("pos2", 0), ("pos3", 0), ("pos6", 0), ("pos7", 1), ("pos8", 0)),
            (("pos1", 0), ("pos3", 0), ("pos4", 0), ("pos5", 0), ("pos7", 0),
             ("pos9", 1)),
            (("pos1", 0), ("pos3", 0), ("pos4", 0), ("pos5", 0), ("pos7", 1),
             ("pos8", 0)),
            (("pos1", 0), ("pos3", 0), ("pos4", 0), ("pos5", 1), ("pos6", 0),
             ("pos8", 0)),
            (("pos1", 0), ("pos3", 0), ("pos5", 0), ("pos6", 1), ("pos7", 1),
             ("pos9", 1)),
            (("pos1", 0), ("pos3", 0), ("pos5", 0), ("pos7", 0), ("pos8", 1),
             ("pos9", 0)),
            (("pos1", 0), ("pos4", 0), ("pos5", 0), ("pos6", 1), ("pos7", 1),
             ("pos9", 1)),
            (("pos2", 0), ("pos3", 0), ("pos4", 0), ("pos5", 0), ("pos7", 0),
             ("pos9", 1)),
            (("pos2", 0), ("pos3", 0), ("pos4", 0), ("pos5", 0), ("pos7", 1),
             ("pos8", 0)),
            (("pos2", 0), ("pos3", 0), ("pos4", 0), ("pos5", 1), ("pos6", 0),
             ("pos8", 0)),
            (("pos2", 0), ("pos4", 0), ("pos5", 0), ("pos6", 1), ("pos7", 1),
             ("pos9", 1)),
            (("pos2", 0), ("pos3", 0), ("pos4", 0), ("pos5", 0), ("pos6", 0),
             ("pos7", 0), ("pos8", 1)),
            (("pos1", 0), ("pos3", 0), ("pos4", 1), ("pos5", 1), ("pos6", 1),
             ("pos7", 1), ("pos8", 1), ("pos9", 1)),
            (("pos2", 0), ("pos3", 0), ("pos4", 1), ("pos5", 1), ("pos6", 1),
             ("pos7", 1), ("pos8", 1), ("pos9", 1)),
            (("pos1", 0), ("pos2", 1), ("pos3", 1), ("pos4", 1), ("pos5", 1),
             ("pos6", 1), ("pos7", 1), ("pos8", 1), ("pos9", 1)),
        ),
    },
    (12, "011111111111", "010000000000"): {
        "clauses": (
            (("pos4", 0), ("pos6", 0), ("pos8", 0), ("pos9", 0), ("pos11", 1)),
            (("pos4", 0), ("pos6", 0), ("pos8", 0), ("pos9", 1), ("pos10", 0)),
            (("pos1", 0), ("pos3", 0), ("pos5", 0), ("pos8", 0), ("pos9", 0),
             ("pos11", 1)),
            (("pos1", 0), ("pos3", 0), ("pos5", 0), ("pos8", 0), ("pos9", 1),
             ("pos10", 0)),
            (("pos1", 0), ("pos3", 0), ("pos6", 0), ("pos8", 0), ("pos9", 0),
             ("pos11", 1)),
            (("pos1", 0), ("pos3", 0), ("pos6", 0), ("pos8", 0), ("pos9", 1),
             ("pos10", 0)),
            (("pos2", 0), ("pos3", 0), ("pos6", 0), ("pos8", 0), ("pos9", 0),
             ("pos11", 1)),
            (("pos2", 0), ("pos3", 0), ("pos6", 0), ("pos8", 0), ("pos9", 1),
             ("pos10", 0)),
            (("pos4", 0), ("pos6", 0), ("pos7", 0), ("pos8", 1), ("pos9", 1),
             ("pos11", 1)),
            (("pos1", 0), ("pos3", 0), ("pos5", 0), ("pos6", 0), ("pos7", 0),
             ("pos9", 0), ("pos11", 1)),
            (("pos1", 0), ("pos3", 0), ("pos5", 0), ("pos6", 0), ("pos7", 0),
             ("pos9", 1), ("pos10", 0)),
            (("pos1", 0), ("pos3", 0), ("pos5", 0), ("pos6", 0), ("pos7", 1),
             ("pos8", 0), ("pos10", 0)),
            (("pos1", 0), ("pos3", 0), ("pos5", 0), ("pos7", 0), ("pos9", 0),
             ("pos10", 1), ("pos11", 0)),
            (("pos1", 0), ("pos3", 0), ("pos6", 0), ("pos7", 0), ("pos8", 1),
             ("pos9", 1), ("pos11", 1)),
            (("pos2", 0), ("pos3", 0), ("pos4", 0), ("pos5", 0), ("pos8", 0),
             ("pos9", 0), ("pos11", 1)),
            (("pos2", 0), ("pos3", 0), ("pos4", 0), ("pos5", 0), ("pos8", 0),
             ("pos9", 1), ("pos10", 0)),
            (("pos2", 0), ("pos3", 0), ("pos6", 0), ("pos7", 0), ("pos8", 1),
             ("pos9", 1), ("pos11", 1)),
            (("pos1", 0), ("pos3", 0), ("pos4", 0), ("pos5", 0), ("pos7", 0),
             ("pos8", 1), ("pos9", 1), ("pos11", 1)),
            (("pos2", 0), ("pos3", 0), ("pos4", 0), ("pos5", 0), ("pos6", 0),
             ("pos7", 0), ("pos9", 0), ("pos11", 1)),
            (("pos2", 0), ("pos3", 0), ("pos4", 0), ("pos5", 0), ("pos6", 0),
             ("pos7", 0), ("pos9", 1), ("pos10", 0)),
            (("pos2", 0), ("pos3", 0), ("pos4", 0), ("pos5", 0), ("pos6", 0),
             ("pos7", 1), ("pos8", 0), ("pos10", 0)),
            (("pos2", 0), ("pos3", 0), ("pos4", 0), ("pos5", 0), ("pos7", 0),
             ("pos8", 1), ("pos9", 1), ("pos11", 1)),
            (("pos1", 0), ("pos3", 0), ("pos5", 0), ("pos6", 1), ("pos7", 1),
             ("pos8", 1), ("pos9", 1), ("pos10", 1), ("pos11", 1)),
            (("pos1", 0), ("pos4", 0), ("pos5", 0), ("pos6", 1), ("pos7", 1),
             ("pos8", 1), ("pos9", 1), ("pos10", 1), ("pos11", 1)),
            (("pos2", 0), ("pos3", 0), ("pos4", 0), ("pos5", 0), ("pos6", 0),
             ("pos7", 0), ("pos8", 0), ("pos9", 0), ("pos10", 1)),
            (("pos2", 0), ("pos4", 0), ("pos5", 0), ("pos6", 1), ("pos7", 1),
             ("pos8", 1), ("pos9", 1), ("pos10", 1), ("pos11", 1)),
            (("pos1", 0), ("pos3", 0), ("pos4", 1), ("pos5", 1), ("pos6", 1),
             ("pos7", 1), ("pos8", 1), ("pos9", 1), ("pos10", 1), ("pos11", 1)),
            (("pos2", 0), ("pos3", 0), ("pos4", 1), ("pos5", 1), ("pos6", 1),
             ("pos7", 1), ("pos8", 1), ("pos9", 1), ("pos10", 1), ("pos11", 1)),
            (("pos1", 0), ("pos2", 1), ("pos3", 1), ("pos4", 1), ("pos5", 1),
             ("pos6", 1), ("pos7", 1), ("pos8", 1), ("pos9", 1), ("pos10", 1),
             ("pos11", 1)),
        ),
    },
    (13, "0111111111111", "0100000000000"): {
        "clauses": (
            (("pos1", 0), ("pos3", 0), ("pos5", 0), ("pos8", 0), ("pos9", 0),
             ("pos10", 1), ("pos12", 1)),
            (("pos1", 0), ("pos3", 0), ("pos5", 0), ("pos8", 0), ("pos10", 0),
             ("pos11", 0), ("pos12", 1)),
            (("pos1", 0), ("pos3", 0), ("pos6", 0), ("pos8", 0), ("pos9", 0),
             ("pos10", 1), ("pos12", 1)),
            (("pos1", 0), ("pos3", 0), ("pos6", 0), ("pos8", 0), ("pos10", 0),
             ("pos11", 0), ("pos12", 1)),
            (("pos1", 0), ("pos4", 0), ("pos6", 0), ("pos8", 0), ("pos9", 0),
             ("pos10", 1), ("pos12", 1)),
            (("pos1", 0), ("pos4", 0), ("pos6", 0), ("pos8", 0), ("pos10", 0),
             ("pos11", 0), ("pos12", 1)),
            (("pos2", 0), ("pos4", 0), ("pos6", 0), ("pos8", 0), ("pos9", 0),
             ("pos10", 1), ("pos12", 1)),
            (("pos2", 0), ("pos4", 0), ("pos6", 0), ("pos8", 0), ("pos10", 0),
             ("pos11", 0), ("pos12", 1)),
            (("pos1", 0), ("pos3", 0), ("pos5", 0), ("pos6", 0), ("pos7", 0),
             ("pos9", 0), ("pos10", 1), ("pos12", 1)),
            (("pos1", 0), ("pos3", 0), ("pos5", 0), ("pos6", 0), ("pos7", 0),
             ("pos10", 0), ("pos11", 0), ("pos12", 1)),
            (("pos1", 0), ("pos3", 0), ("pos6", 0), ("pos7", 0), ("pos8", 1),
             ("pos9", 1), ("pos10", 1), ("pos11", 1), ("pos12", 1)),
            (("pos1", 0), ("pos4", 0), ("pos6", 0), ("pos7", 0), ("pos8", 1),
             ("pos9", 1), ("pos10", 1), ("pos11", 1), ("pos12", 1)),
            (("pos2", 0), ("pos4", 0), ("pos6", 0), ("pos7", 0), ("pos8", 1),
             ("pos9", 1), ("pos10", 1), ("pos11", 1), ("pos12", 1)),
            (("pos1", 0), ("pos3", 0), ("pos4", 0), ("pos5", 0), ("pos7", 0),
             ("pos8", 1), ("pos9", 1), ("pos10", 1), ("pos11", 1), ("pos12", 1)),
            (("pos1", 0), ("pos3", 0), ("pos5", 0), ("pos6", 1), ("pos7", 1),
             ("pos8", 1), ("pos9", 1), ("pos10", 1), ("pos11", 1), ("pos12", 1)),
            (("pos1", 0), ("pos4", 0), ("pos5", 0), ("pos6", 1), ("pos7", 1),
             ("pos8", 1), ("pos9", 1), ("pos10", 1), ("pos11", 1), ("pos12", 1)),
            (("pos2", 0), ("pos4", 0), ("pos5", 0), ("pos6", 1), ("pos7", 1),
             ("pos8", 1), ("pos9", 1), ("pos10", 1), ("pos11", 1), ("pos12", 1)),
            (("pos1", 0), ("pos3", 0), ("pos4", 1), ("pos5", 1), ("pos6", 1),
             ("pos7", 1), ("pos8", 1), ("pos9", 1), ("pos10", 1), ("pos11", 1),
             ("pos12", 1)),
            (("pos2", 0), ("pos3", 0), ("pos4", 1), ("pos5", 1), ("pos6", 1),
             ("pos7", 1), ("pos8", 1), ("pos9", 1), ("pos10", 1), ("pos11", 1),
             ("pos12", 1)),
            (("pos1", 0), ("pos2", 1), ("pos3", 1), ("pos4", 1), ("pos5", 1),
             ("pos6", 1), ("pos7", 1), ("pos8", 1), ("pos9", 1), ("pos10", 1),
             ("pos11", 1), ("pos12", 1)),
        ),
    },
}


def render_peg_cnf(clauses: Sequence[Sequence[Tuple[str, int]]]) -> str:
    """`(!pos1 | pos2) & (pos1 | !pos2)` -- the engine's own rendering.

    Written here rather than imported from `engines.ic3_pdr.system` for the one
    reason everything in this package is written twice: this file may not import
    the engine it is transcribing.
    """
    return " & ".join(
        "(%s)" % " | ".join(name if value else "!" + name for name, value in clause)
        for clause in clauses
    )


def peg_ic3_certificate(start: str = "0111", n: int = PEG_N,
                        goal: str = PEG_GOAL) -> dict:
    """`ic3_pdr`'s answer on `start`, transcribed clause by clause.

    STATUS.md, M9: `I(s) = (!pos1 | pos2) & (pos1 | !pos2)` on `0111`.  Written
    as the clauses rather than as `pos1 == pos2`, so that what is rechecked is
    the shape the engine actually emitted -- and so that the emitted shape and
    this transcription can be compared literal by literal.
    """
    entry = PEG_IC3_INVARIANTS[(n, start, goal)]
    clauses = entry["clauses"]
    comment = entry.get("comment") or (
        "%s -- %d clause(s) over %d positions, the invariant ic3_pdr converges "
        "on for %s. Its size in states is pinned in recheck/verify_all.py and "
        "cross-checked against the engine's own count in "
        "tests/test_ic3bounds_emit.py."
        % (render_peg_cnf(clauses), len(clauses), n, start)
    )
    return {
        "schema": CERTIFICATE_SCHEMA,
        "name": "%s-ic3-invariant" % peg_name(start, n),
        "kind": "inductive_invariant",
        "claim": "unsolvable",
        "produced_by": entry.get(
            "produced_by",
            "engines/ic3_pdr, emitted through ic3bounds/emit.py (E8 axis A)"),
        "comment": comment,
        "ruleset": {"name": peg_name(start, n)},
        "predicate": ["and"] + [
            ["or"] + [eq(var(name), lit(value)) for name, value in clause]
            for clause in clauses
        ],
    }


# =================================================== pagoda (lp_potential)

# Transcribed from `engine-rig/interop/certificates/*.json`, which
# `interop/certificate_export.py` wrote out of `lp_potential`'s LP solution.
# Four numbers each: the weights, the bound, the start and the target cell.
#
# Nothing else is transcribed.  The move set, the state space and the goal come
# from the rule set named alongside, and are grounded here; the producer's own
# `obligations` block -- which lists every move instance with its delta already
# evaluated -- is not read by this package at all.  `anchors.py` compares that
# block against the derived relation once, as a differential, where a
# disagreement is a finding rather than a rejection.
#
#  (case, rule set, weights, bound, producer document)
PAGODA_CLAIMS: Tuple[Tuple[str, str, Tuple[int, ...], int, str], ...] = (
    ("peg4-1110-pagoda", "peg4-1110", (-1, 1, 0, 1), 0,
     "pagoda_4_1110_to_0100.json"),
    ("peg5-11011-to-01000-pagoda", "peg5-11011-to-01000", (-1, 1, 0, 1, -1), 0,
     "pagoda_5_11011_to_01000.json"),
    ("peg5-11011-to-00010-pagoda", "peg5-11011-to-00010", (-1, 1, 0, 1, -1), 0,
     "pagoda_5_11011_to_00010.json"),
)


def pagoda_certificate(name: str, ruleset_name: str, weights: Sequence[int],
                       bound: int, document: str) -> dict:
    """A pagoda as this package states one: weights, a bound, and no more.

    There is no `predicate` and no `obligations`.  The set of states is
    `potential(s) <= bound`, derived; the obligations are the rechecker's to
    discharge, from the rule set's own geometry.
    """
    return {
        "schema": CERTIFICATE_SCHEMA,
        "name": name,
        "kind": "potential_bound",
        "claim": "unsolvable",
        "produced_by": "engines/lp_potential (M6), exported by "
                       "interop/certificate_export.py",
        "comment": "I(s) := potential(s) <= %d, where potential sums w over the "
                   "occupied positions. The pagoda obligation is that no legal "
                   "move raises the potential and that every goal state exceeds "
                   "the bound." % bound,
        "provenance": {
            "document": "engine-rig/interop/certificates/%s" % document,
            "solved_by": "engines/lp_potential, exact rationals scaled to "
                         "integers by the LCM of their denominators",
            "transcribed": "weights and bound only; the move set, the state "
                           "space and the goal are re-derived from the rule set",
        },
        "ruleset": {"name": ruleset_name},
        "occupied": 1,
        "bound": bound,
        "weights": {"pos%d" % i: int(w) for i, w in enumerate(weights)},
    }


# ------------------------------------------------------------- keyed-gate

def keyed_gate_ruleset() -> dict:
    """A world where the only potential-raising move cannot fire below the bound.

    This is not a world anybody plays; it is the smallest exhibit of a
    distinction the pagoda obligation turns on.  `open_gate` raises the
    potential by 5, and its guard needs both keys held -- but any state holding
    both keys already has potential 2, over the bound of 0, so the move is not
    legal from anywhere the invariant admits.  The certificate is therefore
    genuinely inductive, and a checker that reads `delta > 0` off the geometry
    without asking where the move can fire from rejects it.

    The earlier draft of this rechecker did exactly that, so the exhibit is
    carried as a case and asserted as a test rather than described in a comment.
    Nothing sets either key, so the world is unsolvable for a reason the second
    opinion can confirm on its own.
    """
    return {
        "schema": RULESET_SCHEMA,
        "name": "keyed-gate",
        "comment": "Three 0/1 flags and one guarded rule. The prize is behind a "
                   "gate needing both keys, and no rule ever grants a key.",
        "provenance": {
            "world": "written for this package, not transcribed from one",
            "purpose": "the pagoda obligation is `no *legal* move raises the "
                       "potential`; here the only raising move is legal from no "
                       "state under the bound, so checking the geometry instead "
                       "of the region false-rejects a sound certificate",
            "unsolvable_because": "no rule writes keyA or keyB, so the gate's "
                                  "guard never holds on any reachable state",
        },
        "variables": [
            {"name": "keyA", "domain": [0, 1], "comment": "1 if the first key is held"},
            {"name": "keyB", "domain": [0, 1], "comment": "1 if the second key is held"},
            {"name": "prize", "domain": [0, 1], "comment": "1 once the gate is open"},
        ],
        "actions": ["open"],
        "init": {"keyA": 0, "keyB": 0, "prize": 0},
        "goal": eq(var("prize"), lit(1)),
        "rules": [
            {
                "name": "open_gate",
                "action": "open",
                "guard": ["and", eq(var("keyA"), lit(1)), eq(var("keyB"), lit(1))],
                "effects": {"prize": lit(1)},
                "owns": ["prize"],
            },
        ],
    }


def keyed_gate_certificate() -> dict:
    return {
        "schema": CERTIFICATE_SCHEMA,
        "name": "keyed-gate-pagoda",
        "kind": "potential_bound",
        "claim": "unsolvable",
        "produced_by": "written by hand for this package",
        "comment": "w = {keyA: 1, keyB: 1, prize: 5}, bound 0. The region is the "
                   "single state {0,0,0}; `open` does not fire there, so the "
                   "potential never rises from it. Over the whole product it "
                   "does -- {1,1,0} -open-> {1,1,1} gains 5 -- and that state is "
                   "over the bound, which is exactly why the obligation is "
                   "quantified over legal moves from the region.",
        "ruleset": {"name": "keyed-gate"},
        "occupied": 1,
        "bound": 0,
        "weights": {"keyA": 1, "keyB": 1, "prize": 5},
    }


# ==================================================================== A2

# Transcribed from cold-start-a2/theory/generated_holed/theory.py (BOARD).
A2_BOARD: Tuple[Tuple[int, ...], ...] = (
    (1, 1, 1, 1, 1, 1, 1, 1, 1),
    (1, 0, 1, 0, 0, 1, 0, 0, 1),
    (1, 0, 0, 0, 0, 1, 0, 0, 1),
    (1, 0, 0, 0, 0, 1, 0, 0, 1),
    (1, 0, 0, 0, 0, 1, 0, 0, 1),
    (1, 0, 0, 0, 0, 1, 0, 0, 1),
    (1, 1, 0, 0, 0, 1, 0, 0, 1),
    (1, 0, 1, 1, 3, 1, 0, 0, 1),
    (1, 1, 1, 1, 1, 1, 1, 1, 1),
)

A2_DIRECTIONS: Dict[str, Cell] = {
    "up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1),
}
A2_BUTTON = (1, 1)
A2_BUTTON_COLOUR = 7
A2_BUTTON_PRESSED = 8
A2_CART_COLOUR = 6
A2_CART_START = (5, 1)
A2_DOOR = (6, 4)
A2_DOOR_COLOUR = 5
A2_GOAL = (2, 7)
A2_PORTAL_EXIT = (7, 6)
A2_PORTAL_COLOUR = 3
A2_BACKGROUND = 0


def a2_arena() -> List[Cell]:
    return [(r, c) for r in range(9) for c in range(9) if A2_BOARD[r][c] == A2_BACKGROUND]


def a2_ruleset(with_teleport: bool) -> dict:
    arena = a2_arena()
    neighbours = []
    for cell in arena:
        for name in sorted(A2_DIRECTIONS):
            dr, dc = A2_DIRECTIONS[name]
            neighbours.append([cell_name(cell), name, cell_name((cell[0] + dr, cell[1] + dc))])

    board_entries = [[cell_name(cell), 0] for cell in arena]
    board_entries += [
        [cell_name((r, c)), A2_BOARD[r][c]]
        for r in range(9) for c in range(9)
        if A2_BOARD[r][c] not in (0, 1)
    ]

    # `rendered` is `theory.py`'s render() read back off the frame, in the same
    # draw order: board, then Button, then Cart, then Door, so the later drawing
    # wins.  The guards below read colours and never the state directly, which
    # is what the manual's own `colored(...)` / `free(...)` mean.
    rendered = ["if",
                ["and", eq(["param", "x"], lit(cell_name(A2_DOOR))),
                 eq(var("door"), lit("yes"))],
                lit(A2_DOOR_COLOUR),
                ["if", eq(["param", "x"], var("cart")),
                 lit(A2_CART_COLOUR),
                 ["if", eq(["param", "x"], lit(cell_name(A2_BUTTON))),
                  var("button"),
                  ["table", "board", ["param", "x"]]]]]

    def push(direction: str) -> dict:
        target = ["table", "nb", var("cart"), lit(direction)]
        return {
            "name": "push_%s" % direction,
            "action": direction,
            "guard": ["call", "free", target],
            "effects": {"cart": target},
            "owns": ["cart"],
        }

    rules = [push(d) for d in ("up", "down", "left", "right")]
    if with_teleport:
        rules.append({
            "name": "teleport_down",
            "action": "down",
            "comment": "when act=push(Cart, down) and colored(below(Cart), 3) "
                       "then jumped(Cart, portal_exit)",
            "guard": eq(["call", "rendered",
                         ["table", "nb", var("cart"), lit("down")]],
                        lit(A2_PORTAL_COLOUR)),
            "effects": {"cart": lit(cell_name(A2_PORTAL_EXIT))},
            "owns": ["cart"],
        })
    rules.append({
        "name": "press_up",
        "action": "up",
        "guard": eq(["call", "rendered", ["table", "nb", var("cart"), lit("up")]],
                    lit(A2_BUTTON_COLOUR)),
        "effects": {"button": lit(A2_BUTTON_PRESSED)},
        "owns": ["button"],
    })
    rules.append({
        "name": "door_opens_up",
        "action": "up",
        "guard": eq(["call", "rendered", ["table", "nb", var("cart"), lit("up")]],
                    lit(A2_BUTTON_COLOUR)),
        "effects": {"door": lit("no")},
        "owns": ["door"],
    })

    name = "a2-world" if with_teleport else "a2-holed"
    return {
        "schema": RULESET_SCHEMA,
        "name": name,
        "comment": (
            "A2's 9x9 pushing world, %s the teleport rule. %s"
            % ("with" if with_teleport else "WITHOUT",
               "This is the control manual, which A2's 18-action refutation "
               "established is the world's own rule set."
               if with_teleport else
               "This is the exhibit: the manual whose `unsolvable` theorem is "
               "true of itself and false of the world.")
        ),
        "provenance": {
            "manual": "cold-start-a2/theory/%s"
                      % ("theory.dsl" if with_teleport else "theory_holed.dsl"),
            "compiled_form": "cold-start-a2/theory/%s/theory.py"
                             % ("generated" if with_teleport else "generated_holed"),
            "board": "transcribed from that file's BOARD literal",
            "difference": "a2-world adds exactly the rule `teleport_down`",
        },
        "variables": [
            {"name": "button", "domain": [A2_BUTTON_COLOUR, A2_BUTTON_PRESSED],
             "comment": "the Button's colour; 8 once pressed"},
            {"name": "cart", "domain": [cell_name(cell) for cell in arena],
             "comment": "the Cart's cell, over the %d background cells" % len(arena)},
            {"name": "door", "domain": ["no", "yes"],
             "comment": "whether the Door is still present at %s" % cell_name(A2_DOOR)},
        ],
        "actions": ["down", "left", "right", "up"],
        "tables": {
            "board": {
                "arity": 1,
                "comment": "the board's own colours; every cell not listed is "
                           "wall (1), which is what the BOARD literal says",
                "default": 1,
                "entries": sorted(board_entries),
            },
            "nb": {
                "arity": 2,
                "comment": "the neighbour of a Cart cell in a direction",
                "entries": sorted(neighbours),
            },
        },
        "defs": [
            {
                "name": "rendered",
                "params": ["x"],
                "comment": "the colour a frame shows at cell x -- board, then "
                           "Button, then Cart, then Door, last drawn wins",
                "body": rendered,
            },
            {
                "name": "free",
                "params": ["x"],
                "body": eq(["call", "rendered", ["param", "x"]], lit(A2_BACKGROUND)),
            },
        ],
        "init": {
            "button": A2_BUTTON_COLOUR,
            "cart": cell_name(A2_CART_START),
            "door": "yes",
        },
        "goal": eq(var("cart"), lit(cell_name(A2_GOAL))),
        "rules": rules,
    }


# Pagoda weight, transcribed from generated_holed/theory.lean, `def w`.
A2_WEIGHT_ZERO_CELLS: Tuple[Cell, ...] = (
    (1, 3), (1, 4),
    (2, 1), (2, 2), (2, 3), (2, 4),
    (3, 1), (3, 2), (3, 3), (3, 4),
    (4, 1), (4, 2), (4, 3), (4, 4),
    (5, 1), (5, 2), (5, 3), (5, 4),
    (6, 2), (6, 3), (6, 4),
)


def a2_certificate() -> dict:
    arena = a2_arena()
    zero = set(A2_WEIGHT_ZERO_CELLS)
    assert zero <= set(arena) and len(zero) == 21
    return {
        "schema": CERTIFICATE_SCHEMA,
        "name": "a2-right-room-locked",
        "kind": "inductive_invariant",
        "claim": "unsolvable",
        "produced_by": "zero_space -> a GF(2) occupancy law, adjudicated into a "
                       "0/1 pagoda weight (cold-start-a2 THEORIZE_LOG L-03)",
        "comment": "I(s) := w(cart) = 0, the invariant Lean proves closed in "
                   "cold-start-a2/theory/generated_holed/theory.lean, axiom-free. "
                   "It is TRUE of the holed manual and FALSE of the world; "
                   "rechecking it against a2-world must reject it. This is the "
                   "one certificate here that carries no `ruleset` binding, and "
                   "the omission is the point: it is meant to be checked "
                   "against both manuals, and a binding would refuse the second "
                   "run before the invariant was ever evaluated.",
        "provenance": {
            "lean": "cold-start-a2/theory/generated_holed/theory.lean, `def w` "
                    "and `def I`",
            "lean_status": "GREEN, #print axioms unsolvable = []",
            "refuted_by": "cold-start-a2/artifacts/refutation.json -- an "
                          "18-action episode ends with win: true",
        },
        "tables": {
            "w": {
                "arity": 1,
                "comment": "0 on the 21 cells the Cart was ever observed on, 1 "
                           "everywhere else, including the goal cell",
                "default": 1,
                "entries": sorted([cell_name(cell), 0] for cell in arena if cell in zero),
            },
        },
        "predicate": eq(["table", "w", var("cart")], lit(0)),
    }


# ================================================================ sokoban

SOKOBAN_DELTA: Dict[str, Cell] = {
    "down": (1, 0), "left": (0, -1), "right": (0, 1), "up": (-1, 0),
}
SOKOBAN_DIRECTIONS = tuple(sorted(SOKOBAN_DELTA))

OPEN4_GRID = ("######", "#....#", "#....#", "#....#", "#....#", "######")
RING_GRID = ("######", "#....#", "#.##.#", "#.##.#", "#....#", "######")


def floors(grid: Sequence[str]) -> List[Cell]:
    return sorted((r, c) for r, row in enumerate(grid)
                  for c, char in enumerate(row) if char == ".")


def sokoban_ruleset(name: str, grid: Sequence[str], player: Cell,
                    boxes: Sequence[Tuple[str, Cell]],
                    goals: Sequence[Tuple[str, Cell]]) -> dict:
    cells = floors(grid)
    names = [cell_name(cell) for cell in cells]
    box_names = [box for box, _ in boxes]

    neighbours = []
    for cell in cells:
        for direction in SOKOBAN_DIRECTIONS:
            dr, dc = SOKOBAN_DELTA[direction]
            target = (cell[0] + dr, cell[1] + dc)
            if target in set(cells):
                neighbours.append([cell_name(cell), direction, cell_name(target)])

    clear_body = ["and", ["!=", ["param", "x"], lit("none")]]
    clear_body += [["!=", ["param", "x"], var(v)] for v in ["player"] + box_names]

    rules = []
    for direction in SOKOBAN_DIRECTIONS:
        target = ["table", "nb", var("player"), lit(direction)]
        rules.append({
            "name": "move_%s" % direction,
            "action": "move-%s" % direction,
            "comment": "PDDL `move`: at-player ?from, clear ?to, adj ?from ?to ?d",
            "guard": ["call", "clear", target],
            "effects": {"player": target},
            "owns": ["player"],
        })
    for direction in SOKOBAN_DIRECTIONS:
        front = ["table", "nb", var("player"), lit(direction)]
        beyond = ["table", "nb", front, lit(direction)]
        effects: Dict[str, object] = {"player": front}
        for box in box_names:
            effects[box] = ["if", eq(front, var(box)), beyond, var(box)]
        rules.append({
            "name": "push_%s" % direction,
            "action": "push-%s" % direction,
            "comment": "PDDL `push`: at-player ?p, at ?b ?from, clear ?to, "
                       "adj ?p ?from ?d, adj ?from ?to ?d",
            "guard": ["and",
                      ["or"] + [eq(front, var(box)) for box in box_names],
                      ["call", "clear", beyond]],
            "effects": effects,
            "owns": sorted(effects),
        })

    occupants = ["player"] + box_names
    distinct = ["and"]
    for i, left in enumerate(occupants):
        for right in occupants[i + 1:]:
            distinct.append(["!=", var(left), var(right)])

    return {
        "schema": RULESET_SCHEMA,
        "name": name,
        "comment": "Fixture D's sokoban level %s, as finite-domain variables "
                   "rather than grounded STRIPS." % name,
        "provenance": {
            "world": "engine-rig/fixtures/sokoban.py",
            "grid": list(grid),
            "encoding": "one variable per movable thing; the PDDL's `clear` "
                        "fluent becomes the derived predicate `clear`, and the "
                        "at-most-one-thing-per-cell fact the grounded task gets "
                        "from its mutexes becomes the declared constraint, "
                        "which this rechecker proves inductive rather than "
                        "assuming.",
        },
        "variables": (
            [{"name": "player", "domain": names}]
            + [{"name": box, "domain": names} for box in box_names]
        ),
        "actions": (
            ["move-%s" % d for d in SOKOBAN_DIRECTIONS]
            + ["push-%s" % d for d in SOKOBAN_DIRECTIONS]
        ),
        "tables": {
            "nb": {
                "arity": 2,
                "comment": "the floor neighbour, or `none` at a wall",
                "default": "none",
                "entries": sorted(neighbours),
            },
        },
        "defs": [
            {
                "name": "clear",
                "params": ["x"],
                "comment": "a real floor cell holding neither the player nor a box",
                "body": clear_body,
            },
        ],
        "constraint": distinct,
        "init": dict(
            [("player", cell_name(player))]
            + [(box, cell_name(cell)) for box, cell in boxes]
        ),
        "goal": ["and"] + [eq(var(box), lit(cell_name(cell))) for box, cell in goals],
        "rules": rules,
    }


def deadlock_certificate(level: str, pattern: Sequence[Tuple[str, Cell]],
                         closure: str) -> dict:
    text = " AND ".join("at(%s,c%d%d)" % (box, cell[0], cell[1])
                        for box, cell in pattern)
    slug = "-".join("%s-%d%d" % (box, cell[0], cell[1]) for box, cell in pattern)
    return {
        "schema": CERTIFICATE_SCHEMA,
        "name": "%s-dead-%s" % (level, slug),
        "kind": "dead_region",
        "claim": "conditional_unsolvability",
        "produced_by": "engines/deadlock_carver (M9)",
        "comment": "%s AND not-goal => dead (closure: %s)" % (text, closure),
        "ruleset": {"name": level},
        "predicate": ["and"] + [
            eq(var(box), lit(cell_name(cell))) for box, cell in pattern
        ],
    }


RINGSTUCK_THEOREMS = (
    (("b1", (1, 1)),),
    (("b1", (1, 4)),),
)

OPEN4FAR_THEOREMS = (
    (("b1", (1, 1)),), (("b1", (1, 4)),), (("b1", (4, 1)),), (("b1", (4, 4)),),
    (("b2", (1, 1)),), (("b2", (1, 4)),), (("b2", (4, 1)),), (("b2", (4, 4)),),
    (("b1", (1, 2)), ("b2", (1, 3))),
    (("b1", (1, 3)), ("b2", (1, 2))),
    (("b1", (2, 1)), ("b2", (3, 1))),
    (("b1", (2, 4)), ("b2", (3, 4))),
    (("b1", (3, 1)), ("b2", (2, 1))),
    (("b1", (3, 4)), ("b2", (2, 4))),
    (("b1", (4, 2)), ("b2", (4, 3))),
    (("b1", (4, 3)), ("b2", (4, 2))),
)


# ================================================================== driver

def serialise(payload: dict) -> str:
    """The exact bytes `dump` writes, so a digest taken here is the file's."""
    return canonical_text(payload)


def bind(cases: Dict[str, dict]) -> Dict[str, dict]:
    """Fill in each certificate's `ruleset.sha256` from the rule set it names.

    A binding by name alone is weak: two rule sets may share a name, and the
    rechecker would pass `ruleset_binding` on either.  The digest makes the
    binding mean the file.  Certificates deliberately meant to be checked
    against more than one rule set carry no binding at all, which is a
    different statement and is left alone here.
    """
    digests = {
        payload["name"]: hashlib.sha256(serialise(payload).encode("utf-8")).hexdigest()
        for payload in cases.values()
        if payload.get("schema") == RULESET_SCHEMA
    }
    for payload in cases.values():
        binding = payload.get("ruleset")
        if payload.get("schema") != CERTIFICATE_SCHEMA or not binding:
            continue
        digest = digests.get(binding.get("name"))
        if digest is None:
            raise KeyError("certificate %r binds to an unknown rule set %r"
                           % (payload.get("name"), binding.get("name")))
        binding["sha256"] = digest
    return cases


def all_cases() -> Dict[str, dict]:
    cases: Dict[str, dict] = {
        # All four starts peg4.py hand-verifies, so all four literals in its
        # docstring are anchors on this encoding rather than only the two the
        # certificate needs.
        "peg4-0111.rules.json": peg_ruleset("0111"),
        "peg4-1011.rules.json": peg_ruleset("1011"),
        "peg4-1101.rules.json": peg_ruleset("1101"),
        "peg4-1110.rules.json": peg_ruleset("1110"),
        "peg4-0111-ic3.cert.json": peg_ic3_certificate(),
        # The 5-cell board theory-compiler's fixture uses. Two rule sets, one
        # start, two targets: `interop/README.md`'s finding is that the pagoda
        # exists for cells 1 and 3 and for no disjunction of them.
        "peg5-11011-to-01000.rules.json": peg_ruleset(
            "11011", goal="01000", name="peg5-11011-to-01000"),
        "peg5-11011-to-00010.rules.json": peg_ruleset(
            "11011", goal="00010", name="peg5-11011-to-00010"),
        "keyed-gate.rules.json": keyed_gate_ruleset(),
        "keyed-gate-pagoda.cert.json": keyed_gate_certificate(),
    }
    # The E8 size gradient. n=4 is already above -- it is the M9 anchor and
    # keeps its own filenames and wording -- so the loop starts at the next
    # step and adds one rule set and one certificate per size.
    for n, start, goal in PEG_GRADIENT:
        if n == PEG_N:
            continue
        cases["%s.rules.json" % peg_name(start, n)] = peg_ruleset(start, n, goal)
        cases["%s-ic3.cert.json" % peg_name(start, n)] = peg_ic3_certificate(
            start, n, goal)
    cases.update({
        "a2-holed.rules.json": a2_ruleset(with_teleport=False),
        "a2-world.rules.json": a2_ruleset(with_teleport=True),
        "a2-right-room-locked.cert.json": a2_certificate(),
        # `ring` and `open4` carry no certificate. They are here as anchors: the
        # fixture states their optima (1 and 6) on grounds this encoding shares
        # nothing with, so a transcription error in the sokoban rules shows up
        # as a wrong plan length rather than as a quietly wrong verdict.
        "sokoban-ring.rules.json": sokoban_ruleset(
            "sokoban-ring", RING_GRID, (1, 1), (("b1", (1, 2)),),
            (("b1", (1, 3)),)),
        "sokoban-open4.rules.json": sokoban_ruleset(
            "sokoban-open4", OPEN4_GRID, (4, 4),
            (("b1", (2, 2)), ("b2", (3, 3))),
            (("b1", (1, 2)), ("b2", (4, 3)))),
        "sokoban-ringstuck.rules.json": sokoban_ruleset(
            "sokoban-ringstuck", RING_GRID, (1, 1), (("b1", (1, 2)),),
            (("b1", (3, 1)),)),
        "sokoban-open4far.rules.json": sokoban_ruleset(
            "sokoban-open4far", OPEN4_GRID, (4, 4),
            (("b1", (2, 2)), ("b2", (3, 3))),
            (("b1", (4, 2)), ("b2", (1, 3)))),
    })
    for name, ruleset_name, weights, bound, document in PAGODA_CLAIMS:
        cases["%s.cert.json" % name] = pagoda_certificate(
            name, ruleset_name, weights, bound, document)
    for pattern in RINGSTUCK_THEOREMS:
        cert = deadlock_certificate("sokoban-ringstuck", pattern, "no_deleting_action")
        cases["%s.cert.json" % cert["name"]] = cert
    for pattern in OPEN4FAR_THEOREMS:
        closure = "no_deleting_action" if len(pattern) == 1 else "deleting_actions_blocked"
        cert = deadlock_certificate("sokoban-open4far", pattern, closure)
        cases["%s.cert.json" % cert["name"]] = cert
    return bind(cases)


def write(directory: str = CASES_DIR) -> Dict[str, str]:
    os.makedirs(directory, exist_ok=True)
    out = {}
    for filename, payload in sorted(all_cases().items()):
        out[filename] = dump(os.path.join(directory, filename), payload)
    return out


def check(directory: str = CASES_DIR) -> List[str]:
    """Filenames whose committed bytes differ from what the generator makes."""
    drifted = []
    for filename, payload in sorted(all_cases().items()):
        path = os.path.join(directory, filename)
        expected = serialise(payload)
        if not os.path.exists(path):
            drifted.append(filename + " (missing)")
            continue
        with open(path, "r", encoding="utf-8", newline="") as handle:
            if handle.read().replace("\r\n", "\n") != expected:
                drifted.append(filename)
    return drifted


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m recheck.build_cases")
    parser.add_argument("--check", action="store_true",
                        help="verify the committed cases match, write nothing")
    parser.add_argument("--dir", default=CASES_DIR)
    args = parser.parse_args(argv)

    if args.check:
        drifted = check(args.dir)
        for filename in drifted:
            print("DRIFTED %s" % filename, file=sys.stderr)
        print("%d cases, %d drifted" % (len(all_cases()), len(drifted)))
        return 1 if drifted else 0

    written = write(args.dir)
    print("%d cases written to %s" % (len(written), args.dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
