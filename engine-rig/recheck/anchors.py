"""Checks that the rule sets say what their sources say.

The rechecker's own correctness is one risk; the other, and the larger one, is
that a rule set under `cases/` is a *mis*transcription -- in which case every
verdict it produces is about a world nobody has.  Nothing inside this package
can detect that, so the checks live here and each one is against something
written by someone else, for another purpose, before this package existed:

`a2_replay_episode`
    A2's recorded refutation -- 19 frames, 18 actions, ending in `win: true` --
    replayed through the generated `a2-world` rules.  The comparison is on the
    *rendered frame*, cell by cell, using the rule set's own `rendered`
    definition, so the board, the draw order, the Door's occupancy and the
    teleport destination are all under test at once.  If the transcription were
    wrong anywhere the world can reach, the frames diverge.

`a2_lean_step_table`
    The 592-line `step` table inside
    `cold-start-a2/theory/generated_holed/theory.lean` -- the file Lean itself
    compiled, axiom-free -- against the transition relation this package derives
    from `a2-holed.rules.json`.  Two independent compilations of one manual,
    148 states by 4 directions, compared edge by edge.

Both take their inputs from another track's directory and write nothing to it.
Both are skipped, loudly, if that directory is not present: they are
cross-checks, so an absent counterpart is a missing check, never a pass.
"""

import json
import os
import re
from typing import Dict, List, Optional, Sequence, Tuple

from recheck.ruleset import RuleSet

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
A2_ROOT = os.path.join(REPO_ROOT, "cold-start-a2")
A2_EPISODE = os.path.join(A2_ROOT, "artifacts", "solved_episode.jsonl")
A2_HOLED_LEAN = os.path.join(A2_ROOT, "theory", "generated_holed", "theory.lean")

A2_BUTTON_CELL = (1, 1)
A2_DOOR_CELL = (6, 4)
A2_CART_COLOUR = 6
A2_DOOR_COLOUR = 5


class AnchorUnavailable(RuntimeError):
    """The counterpart artefact is not on this machine."""


# ------------------------------------------------------------------- A2 replay

def a2_state_from_frame(ruleset: RuleSet, frame: Sequence[Sequence[int]]) -> tuple:
    """Read a world frame back into a rule-set state."""
    cart: Optional[str] = None
    for r, row in enumerate(frame):
        for c, colour in enumerate(row):
            if colour == A2_CART_COLOUR:
                cart = "%d,%d" % (r, c)
    if cart is None:
        raise ValueError("no cart in this frame")
    assignment = {
        "cart": cart,
        "button": frame[A2_BUTTON_CELL[0]][A2_BUTTON_CELL[1]],
        "door": "yes" if frame[A2_DOOR_CELL[0]][A2_DOOR_CELL[1]] == A2_DOOR_COLOUR else "no",
    }
    return tuple(assignment[variable.name] for variable in ruleset.variables)


def a2_render(ruleset: RuleSet, state: tuple) -> List[List[int]]:
    """Draw a state back onto a frame, using the rule set's own `rendered`."""
    rendered = ruleset.scope.macros.get("rendered")
    if rendered is None:                              # pragma: no cover
        raise ValueError("this rule set declares no `rendered`")
    return [
        [rendered(state, None, ("%d,%d" % (r, c),)) for c in range(9)]
        for r in range(9)
    ]


def a2_replay_episode(ruleset: RuleSet, path: str = A2_EPISODE) -> Dict[str, object]:
    """Replay A2's recorded 18-action refutation and compare every frame."""
    if not os.path.exists(path):
        raise AnchorUnavailable(path)
    with open(path, "r", encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    if len(rows) < 2:
        raise ValueError("episode too short to replay")

    state = a2_state_from_frame(ruleset, rows[0]["frame"])
    mismatches: List[str] = []
    if a2_render(ruleset, state) != [list(row) for row in rows[0]["frame"]]:
        mismatches.append("frame 0 does not render back to itself")

    for index in range(len(rows) - 1):
        action = str(rows[index]["action"]).lower()
        state = ruleset.step(state, action)
        expected = [list(row) for row in rows[index + 1]["frame"]]
        got = a2_render(ruleset, state)
        if got != expected:
            differing = [
                "(%d,%d) world=%s rules=%s" % (r, c, expected[r][c], got[r][c])
                for r in range(9) for c in range(9)
                if expected[r][c] != got[r][c]
            ]
            mismatches.append(
                "frame %d after %s: %s" % (index + 1, action, ", ".join(differing[:4]))
            )

    final = rows[-1]
    return {
        "episode": os.path.relpath(path, REPO_ROOT).replace("\\", "/"),
        "n_frames": len(rows),
        "n_actions": len(rows) - 1,
        "world_reports_win": bool(final.get("win")),
        "rules_reach_goal": bool(ruleset.goal(state)),
        "mismatches": mismatches,
        "agrees": not mismatches and bool(final.get("win")) and bool(ruleset.goal(state)),
    }


# ------------------------------------------------------------ A2 vs Lean's step

_CELL_COMMENT = re.compile(r"^\s*(c\d+)\s*=\s*\((\d+),\s*(\d+)\)\s*$")
_STEP_ROW = re.compile(
    r"\|\s*⟨Cell\.(c\d+),\s*ButtonColour\.v(\d),\s*DoorPresent\.(yes|no)⟩"
    r",\s*\.(up|down|left|right)\s*=>\s*"
    r"⟨Cell\.(c\d+),\s*ButtonColour\.v(\d),\s*DoorPresent\.(yes|no)⟩"
)


def parse_lean_step_table(path: str = A2_HOLED_LEAN) -> Tuple[Dict[str, str], List[tuple]]:
    """(cell name -> "r,c", [(from, action, to), ...]) out of the Lean source."""
    if not os.path.exists(path):
        raise AnchorUnavailable(path)
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read()

    cells: Dict[str, str] = {}
    for line in text.splitlines():
        match = _CELL_COMMENT.match(line)
        if match:
            cells[match.group(1)] = "%s,%s" % (match.group(2), match.group(3))

    rows: List[tuple] = []
    for match in _STEP_ROW.finditer(text):
        rows.append((
            (cells[match.group(1)], int(match.group(2)), match.group(3)),
            match.group(4),
            (cells[match.group(5)], int(match.group(6)), match.group(7)),
        ))
    return cells, rows


def a2_lean_step_table(ruleset: RuleSet, path: str = A2_HOLED_LEAN) -> Dict[str, object]:
    """Compare Lean's explicit `step` table with the relation derived here."""
    cells, rows = parse_lean_step_table(path)
    order = [variable.name for variable in ruleset.variables]

    def to_state(triple) -> tuple:
        cart, button, door = triple
        assignment = {"cart": cart, "button": button, "door": door}
        return tuple(assignment[name] for name in order)

    mismatches: List[str] = []
    for source, action, target in rows:
        got = ruleset.step(to_state(source), action)
        want = to_state(target)
        if got != want:
            mismatches.append(
                "%s -%s-> lean %s, rules %s"
                % (ruleset.render_state(to_state(source)), action,
                   ruleset.render_state(want), ruleset.render_state(got))
            )

    expected = len(cells) * 2 * 2 * 4
    return {
        "lean_file": os.path.relpath(path, REPO_ROOT).replace("\\", "/"),
        "n_cells": len(cells),
        "n_rows": len(rows),
        "n_expected_rows": expected,
        "complete": len(rows) == expected,
        "mismatches": mismatches[:8],
        "n_mismatches": len(mismatches),
        "agrees": not mismatches and len(rows) == expected,
    }
