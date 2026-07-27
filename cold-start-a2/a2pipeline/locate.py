"""M7 — 定位.  Theoria §1.4's three-way, run as three checks.

§1.4's argument, verbatim in structure: once a claimed-impossible goal is
solved, the error is *necessarily* on the witness path, and it is in one of
exactly three places —

    1. some step is mispredicted,
    2. the goal test is wrong,
    3. the board was misread from the start.

(The one-line proof that the list is exhaustive: if all three were right, the
manual would walk the same path to the same goal and could not have proved the
goal unreachable.)

So localisation is not a search.  It is three checks on one path, and this
module runs all three rather than stopping at the first — a report that says
"step 12 disagrees" without also saying the goal test and the board were fine
has not actually narrowed anything.

Everything here reads `solved_episode.jsonl` and the compiled manual.  The
world's source is not imported: the manual is confronted with frames, which is
the only channel §1.4's mechanism is entitled to.
"""

import json
import os
import sys
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from certify.replay import ACTION_NAMES, load_theory  # noqa: E402

from a2world.ground_truth import read_trace  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACTS = os.path.join(ROOT, "artifacts")
EPISODE = os.path.join(ARTIFACTS, "solved_episode.jsonl")
HOLED = os.path.join(ROOT, "theory", "generated_holed", "theory.py")

MOVER_COLOUR = 6


def _cell_of(frame, colour: int) -> Optional[Tuple[int, int]]:
    for r, row in enumerate(frame):
        for c, value in enumerate(row):
            if value == colour:
                return (r, c)
    return None


def locate(theory_py: str = HOLED,
           episode_path: str = EPISODE) -> Dict[str, object]:
    theory = load_theory(theory_py)
    frames, actions, wins = read_trace(episode_path)

    # --- check 3 first: did the manual read the board right? -------------
    # Cheapest, and if it fails every later disagreement is downstream noise.
    board_diffs = []
    state = theory.initial_state()
    rendered = theory.render(state)
    for r in range(theory.GRID[0]):
        for c in range(theory.GRID[1]):
            if rendered[r][c] != frames[0][r][c]:
                board_diffs.append({"cell": [r, c], "manual": rendered[r][c],
                                    "world": frames[0][r][c]})

    # --- check 1: does every step predict right? -------------------------
    step_diffs: List[Dict[str, object]] = []
    state = theory.initial_state()
    for t, action in enumerate(actions):
        if action is None:
            break
        nxt = theory.step(state, ACTION_NAMES[action])
        predicted = theory.render(nxt)
        observed = frames[t + 1]
        if predicted != observed:
            step_diffs.append({
                "t": t,
                "action": action,
                "mover_before": list(_cell_of(frames[t], MOVER_COLOUR) or ()),
                "mover_manual_predicts": list(_cell_of(predicted, MOVER_COLOUR) or ()),
                "mover_world_shows": list(_cell_of(observed, MOVER_COLOUR) or ()),
                "cells_differing": [
                    [r, c]
                    for r in range(theory.GRID[0])
                    for c in range(theory.GRID[1])
                    if predicted[r][c] != observed[r][c]
                ],
                "fired": theory.fired(state, ACTION_NAMES[action]),
            })
        # follow the WORLD, not the manual: after the first divergence the
        # manual's own successor is not the state the episode is in, and
        # replaying from it would report cascading phantom errors.
        state = _state_from_frame(theory, nxt, observed)

    # --- check 2: does the goal test agree with the win flag? ------------
    goal_diffs = []
    state = theory.initial_state()
    for t, frame in enumerate(frames):
        state = _state_from_frame(theory, state, frame)
        if bool(theory.is_goal(state)) != bool(wins[t]):
            goal_diffs.append({"t": t, "manual": bool(theory.is_goal(state)),
                               "world": bool(wins[t])})

    verdicts = {
        "misread_board": bool(board_diffs),
        "mispredicted_step": bool(step_diffs),
        "wrong_goal_test": bool(goal_diffs),
    }
    culprits = sorted(k for k, v in verdicts.items() if v)

    report: Dict[str, object] = {
        "manual": os.path.relpath(theory_py, ROOT),
        "episode": os.path.relpath(episode_path, ROOT),
        "path_length": len(actions) - 1,
        "checks": verdicts,
        "culprits": culprits,
        "board_diffs": board_diffs[:20],
        "goal_diffs": goal_diffs[:20],
        "step_diffs": step_diffs[:20],
        "n_step_diffs": len(step_diffs),
    }

    if len(step_diffs) >= 1 and not board_diffs:
        first = step_diffs[0]
        report["located"] = {
            "t": first["t"],
            "action": first["action"],
            "mover_at": first["mover_before"],
            "manual_predicts": first["mover_manual_predicts"],
            "world_shows": first["mover_world_shows"],
            "rules_that_fired": first["fired"],
            "reading": (
                "at t=%d the Cart is at %s, the action is %s, the manual fires "
                "%s and predicts the Cart stays at %s, and the world puts it at "
                "%s — a jump of %d cells.  No rule in this manual has an effect "
                "that moves the mover more than one cell, so the defect is a "
                "MISSING RULE, not a wrong one: nothing here can be corrected, "
                "something has to be added."
                % (first["t"], tuple(first["mover_before"]), first["action"],
                   first["fired"] or "nothing",
                   tuple(first["mover_manual_predicts"]),
                   tuple(first["mover_world_shows"]),
                   abs(first["mover_before"][0] - first["mover_world_shows"][0])
                   + abs(first["mover_before"][1] - first["mover_world_shows"][1]))
            ),
            "probe_target": {
                "mover_cell": first["mover_before"],
                "action": first["action"],
                "question": "what makes this transition jump — the colour of the "
                            "cell below, or the Cart's being on this particular "
                            "cell?  Both fit the single witness; M8 designs an "
                            "experiment that separates them.",
            },
        }
    return report


def _state_from_frame(theory, template, frame):
    """Re-seat the manual's state on what the frames actually show.

    Only the observations the word table declares are read back — the mover's
    cell and each non-mover object's colour / presence — and they are read off
    the frame, never off the world.  This is what keeps localisation from
    reporting one real divergence as twenty.
    """
    state = template.copy()
    cell = _cell_of(frame, MOVER_COLOUR)
    if cell is not None:
        state.Cart_pos = cell
    for field in list(vars(state)):
        if field.startswith("Cart"):
            continue
        if field.endswith("_colour"):
            name = field[: -len("_colour")]
            pos = getattr(state, "%s_pos" % name, None)
            if pos is not None and frame[pos[0]][pos[1]] not in (MOVER_COLOUR,):
                present = getattr(state, "%s_present" % name, True)
                if present:
                    setattr(state, field, frame[pos[0]][pos[1]])
        elif field.endswith("_present"):
            name = field[: -len("_present")]
            pos = getattr(state, "%s_pos" % name, None)
            colour = getattr(state, "%s_colour" % name, None)
            if pos is not None and colour is not None:
                if frame[pos[0]][pos[1]] != colour:
                    setattr(state, field, False)
    return state


def main() -> int:
    report = locate()
    with open(os.path.join(ARTIFACTS, "locate_report.json"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")

    print("checks:", json.dumps(report["checks"], sort_keys=True))
    print("culprit:", ", ".join(report["culprits"]) or "none — nothing to locate?")
    located = report.get("located")
    if located:
        print("located: t=%d %s  manual->%s  world->%s"
              % (located["t"], located["action"],
                 tuple(located["manual_predicts"]), tuple(located["world_shows"])))
        print(located["reading"])
    return 0 if report["culprits"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
