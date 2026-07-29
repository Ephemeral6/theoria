"""Write the five sokoban-2 problem instances from the ground-truth levels.

Run once; the JSON is checked in. The levels belong to `a0-spike` (the other
track), so they are *read* here and never imported at test time — the fixtures
are data, and `tools/probe_mentions.py` re-checks each one against the live
level before it grades anything, so a level that moves turns the probe red
rather than turning it silently into a different experiment.

    python theory-compiler/runs/20260728T102343Z-c7/make_sokoban2_problems.py
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(REPO, "theory-compiler", "tests", "fixtures")

sys.path.insert(0, os.path.join(REPO, "a0-spike"))
from world import levels, sokoban2                              # noqa: E402


def problem(level) -> dict:
    board = [[sokoban2.EMPTY] * level.width for _ in range(level.height)]
    for (r, c) in level.walls:
        board[r][c] = sokoban2.WALL
    return {
        "name": "sokoban2-%s" % level.name,
        "grid": [level.height, level.width],
        "background": sokoban2.EMPTY,
        "board": board,
        # Declaration order decides paint order in `render`; the ground truth
        # paints the box first and the player over it. The two never share a
        # cell in the swept set, so this only matters for reading the artefact.
        "objects": [
            {"name": "Box", "type": "Box", "pos": list(level.box)},
            {"name": "Player", "type": "Player", "pos": list(level.player)},
        ],
        "landmarks": {"target": list(level.target)},
        "arena": [[r, c] for r in range(level.height) for c in range(level.width)],
    }


def main() -> None:
    for level in (levels.MATCH,) + levels.CROSSING_LEVELS:
        path = os.path.join(OUT, "sokoban2_%s_problem.json" % level.name)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(problem(level), handle, indent=2, sort_keys=True)
            handle.write("\n")
        print("wrote", os.path.relpath(path, REPO))


if __name__ == "__main__":
    main()
