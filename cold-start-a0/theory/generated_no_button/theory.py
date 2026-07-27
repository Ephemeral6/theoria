"""Auto-generated from theory.dsl by compile/gen_python_a0.py — DO NOT EDIT.

Constraint 4: generated forms are never hand-edited.  Change theory.dsl and
recompile.

This module is the only predictor in the system.  `step` implements the manual's
rules plus the frame axiom the manual declares in its header: *if no rule fires
for an object, that object is unchanged*.
"""

from dataclasses import dataclass, replace
from typing import Dict, List, Optional, Tuple

Cell = Tuple[int, int]

DIRECTIONS: Dict[str, Cell] = {
    "up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1),
}
ACTIONS = [("push", "Cart", d) for d in ("up", "down", "left", "right")]

GRID = (9, 9)
BACKGROUND = 0
LANDMARKS: Dict[str, Cell] = {'portal_exit': (1, 1)}
BOARD: List[List[int]] = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 0, 0, 0, 5, 0, 0, 1],
    [1, 0, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 0, 0, 1, 1, 0, 0, 1],
    [1, 1, 1, 3, 1, 1, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1],
]


@dataclass
class State:
    """One state.  Field per object per observation in the word table."""
    Cart_pos: Cell = (0, 0)
    Cart_colour: int = 0

    def copy(self) -> 'State':
        return replace(self)

    def key(self):
        return (self.Cart_pos, self.Cart_colour)


def render(state: State) -> List[List[int]]:
    """The manual drawn back onto a frame (constraint 2, cheap layer)."""
    grid = [list(row) for row in BOARD]
    if True:
        r, c = state.Cart_pos
        grid[r][c] = state.Cart_colour
    return grid


def responsibility(state: State):
    """Which object owns each pixel; `None` means the board owns it.

    Returns (owner_grid, contested).  `contested` is non-empty exactly
    when two objects claim the same pixel, which the manual forbids.
    """
    owner: List[List[Optional[str]]] = [[None] * GRID[1] for _ in range(GRID[0])]
    contested = []
    if True:
        r, c = state.Cart_pos
        if owner[r][c] is not None:
            contested.append(((r, c), owner[r][c], 'Cart'))
        owner[r][c] = 'Cart'
    return owner, contested


def _neighbour(cell: Cell, direction: str) -> Cell:
    dr, dc = DIRECTIONS[direction]
    return (cell[0] + dr, cell[1] + dc)


def _in_bounds(cell: Cell) -> bool:
    return 0 <= cell[0] < GRID[0] and 0 <= cell[1] < GRID[1]


def _cell_colour(state: State, cell: Cell) -> Optional[int]:
    """Read the colour off the rendered frame — no side door."""
    if not _in_bounds(cell):
        return None
    return render(state)[cell[0]][cell[1]]


def _free(state: State, cell: Cell) -> bool:
    return _cell_colour(state, cell) == BACKGROUND


def _guard_push_up(state: State, action) -> bool:
    """push_up  [ev: t2,t8,t15  cov: 23/23]"""
    if action != ('push', 'Cart', 'up'): return False
    if not _free(state, _neighbour(state.Cart_pos, 'up')): return False
    return True


def _effect_push_up(state: State) -> None:
    state.Cart_pos = _neighbour(state.Cart_pos, 'up')


def _guard_push_down(state: State, action) -> bool:
    """push_down  [ev: t0,t5,t9  cov: 28/28]"""
    if action != ('push', 'Cart', 'down'): return False
    if not _free(state, _neighbour(state.Cart_pos, 'down')): return False
    return True


def _effect_push_down(state: State) -> None:
    state.Cart_pos = _neighbour(state.Cart_pos, 'down')


def _guard_push_left(state: State, action) -> bool:
    """push_left  [ev: t3,t12,t19  cov: 18/18]"""
    if action != ('push', 'Cart', 'left'): return False
    if not _free(state, _neighbour(state.Cart_pos, 'left')): return False
    return True


def _effect_push_left(state: State) -> None:
    state.Cart_pos = _neighbour(state.Cart_pos, 'left')


def _guard_push_right(state: State, action) -> bool:
    """push_right  [ev: t1,t6,t10  cov: 22/22]"""
    if action != ('push', 'Cart', 'right'): return False
    if not _free(state, _neighbour(state.Cart_pos, 'right')): return False
    return True


def _effect_push_right(state: State) -> None:
    state.Cart_pos = _neighbour(state.Cart_pos, 'right')


def _guard_teleport_down(state: State, action) -> bool:
    """teleport_down  [ev: t11  cov: 1/1]"""
    if action != ('push', 'Cart', 'down'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'down')) != 3: return False
    return True


def _effect_teleport_down(state: State) -> None:
    state.Cart_pos = LANDMARKS['portal_exit']


RULES = [
    ('push_up', _guard_push_up, _effect_push_up, 'Cart'),
    ('push_down', _guard_push_down, _effect_push_down, 'Cart'),
    ('push_left', _guard_push_left, _effect_push_left, 'Cart'),
    ('push_right', _guard_push_right, _effect_push_right, 'Cart'),
    ('teleport_down', _guard_teleport_down, _effect_teleport_down, 'Cart'),
]


class AmbiguousTransition(Exception):
    """Two rules claimed the same object: constraint 9 is violated."""


def step(state: State, action) -> State:
    """One action, one successor.  Total: the frame axiom closes it.

    Every guard is read against `state`, never against the partially
    updated result: rules fire simultaneously, not in file order.
    """
    result = state.copy()
    claimed = {}
    for name, guard, effect, obj in RULES:
        if not guard(state, action):
            continue
        if obj in claimed:
            raise AmbiguousTransition(
                '%s and %s both fire on %s for %s'
                % (claimed[obj], name, action, obj))
        claimed[obj] = name
        effect(result)
    return result


def fired(state: State, action) -> List[str]:
    return [name for name, guard, _e, _o in RULES if guard(state, action)]


def is_goal(state: State) -> bool:
    return state.Cart_pos == (2, 7)


def simulate(initial: State, actions) -> List[State]:
    states = [initial]
    current = initial
    for action in actions:
        current = step(current, action)
        states.append(current)
    return states


def initial_state() -> State:
    return State(
        Cart_pos=(5, 1),
        Cart_colour=6,
    )
