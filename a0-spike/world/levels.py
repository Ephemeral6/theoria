"""A0 levels, and the scripted trajectory the pipeline perceives.

Two levels, differing only in the target square:

  `match`     the target has the same parity as the box -- solvable
  `mismatch`  the target has the opposite parity -- unsolvable, and unsolvable
              for a *reason the theory can state*: the box never leaves its own
              checkerboard colour

The pair is the point. A framework that can only say "I searched and found
nothing" cannot tell them apart from the inside; one that has the conservation
law answers the second in one line and keeps looking on the first.

The trajectory is scripted rather than random so that every rule the miner has to
find has witnesses: moves in all four directions, at least one push, and at least
one blocked attempt against a wall and against the board edge.
"""

from typing import Dict, List, Tuple

from world.sokoban2 import (
    BLOCKED,
    DIRECTIONS,
    MOVE,
    PUSH,
    Level,
    rollout,
    solve_bfs,
)

HEIGHT = 7
WIDTH = 7

# A few interior walls: enough to give `blocked` witnesses and to stop the level
# being a bare open field, without cutting the box off from its target.
WALLS: Tuple[Tuple[int, int], ...] = ((1, 5), (4, 4), (5, 5))

PLAYER_START = (3, 5)
BOX_START = (3, 3)          # parity (3+3) % 2 = 0

MATCH_TARGET = (3, 1)       # parity 0 -- same colour as the box
MISMATCH_TARGET = (3, 2)    # parity 1 -- the other colour

MATCH = Level(
    name="match",
    height=HEIGHT,
    width=WIDTH,
    walls=WALLS,
    player=PLAYER_START,
    box=BOX_START,
    target=MATCH_TARGET,
)

MISMATCH = Level(
    name="mismatch",
    height=HEIGHT,
    width=WIDTH,
    walls=WALLS,
    player=PLAYER_START,
    box=BOX_START,
    target=MISMATCH_TARGET,
)

# A third level, for evidence only. Its wall at (3,4) sits on an ODD-parity cell,
# which is the whole point: the box's crossed cell always has odd parity, every
# wall in `match` has even parity, so "the box is blocked by the cell it would
# cross" is unreachable there. The domain rule cannot be pinned down from `match`
# alone -- the manual is meant to be domain-level and travel between levels, so
# the evidence has to as well (THEORIZE_LOG T-9).
# One per direction: a wall on the cell the box would CROSS when pushed that way,
# and a player start from which that push is reachable. Four levels, because a
# single one only makes the case reachable in one direction.
_CROSSING_SPEC = {
    "UP":    {"wall": (2, 3), "player": (5, 3)},
    "DOWN":  {"wall": (4, 3), "player": (1, 3)},
    "LEFT":  {"wall": (3, 2), "player": (3, 5)},
    "RIGHT": {"wall": (3, 4), "player": (3, 1)},
}

CROSSING_LEVELS = tuple(
    Level(
        name="crossing_%s" % direction,
        height=HEIGHT,
        width=WIDTH,
        walls=WALLS + (spec["wall"],),
        player=spec["player"],
        box=BOX_START,
        target=BOX_START,
    )
    for direction, spec in sorted(_CROSSING_SPEC.items())
)

LEVELS = {"match": MATCH, "mismatch": MISMATCH}
EVIDENCE_LEVELS = (MATCH,) + CROSSING_LEVELS


# The observation trajectory. Deliberately explores rather than solves: the
# pipeline must induce the rules from it, not be handed the solution.
TRAJECTORY: List[str] = [
    "LEFT",      # push the box: (3,3) slides two cells to (3,1)
    "UP",        # walk
    "UP",
    "RIGHT",     # walk toward the wall at (1,5)
    "RIGHT",     # blocked by the wall
    "DOWN",
    "DOWN",
    "DOWN",
    "DOWN",
    "LEFT",
    "LEFT",
    "UP",
    "LEFT",
    "LEFT",
    "DOWN",
    "DOWN",
    "DOWN",      # walk to the bottom edge
    "DOWN",      # blocked by the board edge
    "RIGHT",
    "RIGHT",
    "UP",
    "UP",
    "LEFT",
    "UP",
    "RIGHT",
    "RIGHT",
    "DOWN",
    "LEFT",
]


def observations(level: Level = MATCH) -> Dict[str, object]:
    """Frames plus actions -- the only thing the pipeline is allowed to see."""
    return rollout(level, TRAJECTORY)


def trajectory_covers_every_event(level: Level = MATCH) -> Dict[str, int]:
    events = rollout(level, TRAJECTORY)["events"]        # type: ignore[index]
    return {
        event: sum(1 for e in events if e == event)
        for event in (MOVE, PUSH, BLOCKED)
    }


def ground_truth() -> Dict[str, object]:
    """What we know because we built the world. Used only to grade the run."""
    out: Dict[str, object] = {}
    for name, level in LEVELS.items():
        plan = solve_bfs(level)
        out[name] = {
            "box_parity": level.box_parity,
            "target_parity": level.target_parity,
            "parity_matches": level.parity_matches,
            "solvable": plan is not None,
            "optimal_plan_length": len(plan) if plan is not None else None,
            "optimal_plan": plan,
        }
    return out
