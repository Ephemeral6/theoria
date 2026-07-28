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

`pagoda_differential`
    `lp_potential`'s exported documents in `engine-rig/interop/certificates/`,
    against the pagoda cases `build_cases` transcribes from them.  Four numbers
    are transcribed -- the weights, the bound, and by name the rule set -- and
    everything else in those documents is re-derived here: the start state, the
    goal states, and the move set.

    **This is the one place the producer's own `obligations` block is read, and
    reading it is the point of the check.**  The document lists every move
    instance with its delta already evaluated; `certificate_export.py::verify`
    iterates that list, so a document that drops an inconvenient instance
    verifies. The rechecker refuses the block as input (`certificate.py`,
    `_FORBIDDEN`) and grounds the moves from the rules instead. Here the two are
    compared -- every listed move replayed through the derived relation, and the
    derived action set compared against the list both ways -- so that an
    omission or a mislabelled move is *reported*, as a transcription finding,
    rather than silently believed or silently ignored.

    It reads files under `interop/`; it imports nothing from there. That
    distinction is the same one this package makes about `cold-start-a2`, and it
    is what `test_recheck_never_imports_the_engines` enforces.
"""

import hashlib
import json
import os
import re
from typing import Dict, List, Optional, Sequence, Tuple

from recheck.ruleset import RuleSet

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENGINE_RIG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A2_ROOT = os.path.join(REPO_ROOT, "cold-start-a2")
A2_EPISODE = os.path.join(A2_ROOT, "artifacts", "solved_episode.jsonl")
A2_HOLED_LEAN = os.path.join(A2_ROOT, "theory", "generated_holed", "theory.lean")
PAGODA_DOCUMENTS = os.path.join(ENGINE_RIG, "interop", "certificates")

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


# ------------------------------------------- lp_potential's exported documents

def pagoda_document(filename: str, directory: str = PAGODA_DOCUMENTS
                    ) -> Tuple[Dict[str, object], str]:
    """One producer document and the digest of the bytes it was read from."""
    path = os.path.join(directory, filename)
    if not os.path.exists(path):
        raise AnchorUnavailable(path)
    with open(path, "rb") as handle:
        payload = handle.read()
    return json.loads(payload.decode("utf-8")), hashlib.sha256(payload).hexdigest()


def _bitstring(ruleset: RuleSet, state: tuple, occupied: object) -> str:
    return "".join("1" if value == occupied else "0" for value in state)


def _vacant(ruleset: RuleSet, occupied: object) -> Optional[tuple]:
    """The "not occupied" value of each variable, when there is exactly one.

    The producer's documents are strings of `0` and `1`, so replaying one of
    their move instances means naming the empty value -- and naming it from the
    rule set's declared domain rather than assuming `0`.  A variable with three
    values has no single empty state and the replay says so instead of guessing.
    """
    out = []
    for variable in ruleset.variables:
        others = [value for value in variable.domain if value != occupied]
        if len(others) != 1:
            return None
        out.append(others[0])
    return tuple(out)


def _goal_states(ruleset: RuleSet, occupied: object) -> List[str]:
    return sorted(_bitstring(ruleset, state, occupied)
                  for state in ruleset.states() if ruleset.goal(state))


def pagoda_differential(ruleset: RuleSet, certificate, filename: str,
                        directory: str = PAGODA_DOCUMENTS) -> Dict[str, object]:
    """Compare a transcribed pagoda case against the document it came from.

    Every field is compared in the direction that matters: the transcription is
    checked against the producer, and the producer's move list is checked
    against the relation this package grounds from the rules.  A disagreement is
    reported, never resolved -- this function has no opinion about which side is
    wrong, and that is what makes it an anchor rather than a second checker.
    """
    document, digest = pagoda_document(filename, directory)
    occupied = certificate.occupied
    weights = [certificate.weights.get("pos%d" % i)
               for i in range(len(document.get("weights_integer") or ()))]
    init = [_bitstring(ruleset, state, occupied) for state in ruleset.init]
    goals = _goal_states(ruleset, occupied)

    # The rule set's own moves: an action that changes some state is a move the
    # geometry admits, and its label is the rule set's, not the document's.
    rows = ruleset.transitions()
    states = ruleset.states()
    derived_actions = sorted(
        action for a, action in enumerate(ruleset.actions)
        if any(rows[i][a] != i for i in range(len(states)))
    )

    listed = (((document.get("obligations") or {}).get("inv_closed") or {})
              .get("witnesses") or [])
    listed_actions = sorted({str(entry.get("move")) for entry in listed
                             if isinstance(entry, dict)})

    vacant = _vacant(ruleset, occupied)
    replay_mismatches: List[str] = []
    for entry in listed:
        if not isinstance(entry, dict):
            continue
        positions = entry.get("positions")
        move = str(entry.get("move"))
        if not isinstance(positions, list) or len(positions) != 3:
            replay_mismatches.append("%s: no (src, over, dst) to replay" % move)
            continue
        if vacant is None:
            replay_mismatches.append(
                "%s: %s has a variable with more than two values, so `0` in the "
                "document names no single state" % (move, ruleset.name))
            continue
        src, over, dst = positions
        n = len(ruleset.variables)
        before = tuple(occupied if i in (src, over) else vacant[i] for i in range(n))
        after = tuple(occupied if i == dst else vacant[i] for i in range(n))
        if move not in ruleset.actions:
            replay_mismatches.append("%s is not an action of %s" % (move, ruleset.name))
            continue
        got = ruleset.step(before, move)
        if got != after:
            replay_mismatches.append(
                "%s: document says %s -> %s, the rules make %s"
                % (move, _bitstring(ruleset, before, occupied),
                   _bitstring(ruleset, after, occupied),
                   _bitstring(ruleset, got, occupied)))

    checks = {
        "weights_agree": weights == list(document.get("weights_integer") or ()),
        "bound_agrees": certificate.bound == document.get("initial_potential"),
        "initial_state_agrees": init == [document.get("initial_state")],
        "goal_states_agree": goals == sorted(document.get("goal_states") or ()),
        "move_set_agrees": derived_actions == listed_actions,
        "listed_moves_replay": not replay_mismatches,
    }
    return {
        "document": filename,
        "document_sha256": digest,
        "ruleset": ruleset.name,
        "certificate": certificate.name,
        "transcribed_weights": dict(sorted(certificate.weights.items())),
        "document_weights": list(document.get("weights_integer") or ()),
        "derived_initial_state": init,
        "document_initial_state": document.get("initial_state"),
        "derived_goal_states": goals,
        "document_goal_states": sorted(document.get("goal_states") or ()),
        "n_moves_derived": len(derived_actions),
        "n_moves_listed": len(listed_actions),
        "replay_mismatches": replay_mismatches[:4],
        "checks": dict(sorted(checks.items())),
        "agrees": all(checks.values()),
    }
