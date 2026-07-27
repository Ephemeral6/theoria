"""Auto-generated from theory.dsl by a0-spike/pipeline/gen_exec.py.

Do not edit. The manual is the source; this is one of its forms.
"""

from dataclasses import dataclass, replace
from typing import List, Optional, Tuple

GRID_HEIGHT = 7
GRID_WIDTH = 7
WALLS = frozenset([(1, 5), (4, 4), (5, 5)])

DELTA = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}

PLAYER_COLOR = 2
BOX_COLOR = 4
WALL_COLOR = 8


@dataclass
class State:
    player: Tuple[int, int]
    box: Tuple[int, int]

    def render(self) -> List[List[int]]:
        """Full-frame responsibility: every cell is accounted for."""
        grid = [[0] * GRID_WIDTH for _ in range(GRID_HEIGHT)]
        for (r, c) in WALLS:
            grid[r][c] = WALL_COLOR
        grid[self.box[0]][self.box[1]] = BOX_COLOR
        grid[self.player[0]][self.player[1]] = PLAYER_COLOR
        return grid


def _step_from(cell, direction, times):
    dr, dc = DELTA[direction]
    return (cell[0] + dr * times, cell[1] + dc * times)


def _on_board(cell):
    return 0 <= cell[0] < GRID_HEIGHT and 0 <= cell[1] < GRID_WIDTH


def _free(state, cell):
    return _on_board(cell) and cell not in WALLS and cell != state.box

def _rule_walk(state, direction):
    """walk -- compiled from theory.dsl"""
    if not (_free(state, _step_from(state.player, direction, 1))):
        return False
    state.player = _step_from(state.player, direction, 1)
    return True

def _rule_push2(state, direction):
    """push2 -- compiled from theory.dsl"""
    if not ((state.box == _step_from(state.player, direction, 1)) and _free(state, _step_from(state.box, direction, 2))):
        return False
    pusher = state.player
    state.box = _step_from(state.box, direction, 2)
    state.player = _step_from(pusher, direction, 1)
    return True

def _rule_blocked_wall(state, direction):
    """blocked_wall -- compiled from theory.dsl"""
    if not ((not _free(state, _step_from(state.player, direction, 1))) and (not (state.box == _step_from(state.player, direction, 1)))):
        return False
    pass  # nothing happens
    return True

def _rule_blocked_box(state, direction):
    """blocked_box -- compiled from theory.dsl"""
    if not ((state.box == _step_from(state.player, direction, 1)) and (not _free(state, _step_from(state.box, direction, 2)))):
        return False
    pass  # nothing happens
    return True

RULES = [("walk", _rule_walk), ("push2", _rule_push2), ("blocked_wall", _rule_blocked_wall), ("blocked_box", _rule_blocked_box)]


def step(state, direction):
    """Apply one action. Exactly one rule must fire (constraint 9)."""
    fired = []
    for name, rule in RULES:
        trial = replace(state)
        if rule(trial, direction):
            fired.append((name, trial))
    if len(fired) != 1:
        outcomes = {(s.player, s.box) for _, s in fired}
        if len(outcomes) != 1:
            raise RuntimeError(
                "ambiguous successor for %s: %r" % (direction, [n for n, _ in fired])
            )
    return fired[0][1]


def simulate(initial, actions):
    states = [initial]
    current = initial
    for action in actions:
        current = step(current, action)
        states.append(current)
    return states
