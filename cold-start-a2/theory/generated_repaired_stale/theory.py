"""Auto-generated from theory.dsl by compile/gen_python_a0.py — DO NOT EDIT.

Constraint 4: generated forms are never hand-edited.  Change theory.dsl and
recompile.

This module is the only predictor in the system.  `step` implements the manual's
rules under the semantics the manual **declares** in its `semantics:` section --
see SEMANTICS below.  Nothing about the frame axiom, the conflict policy or the
cascade shape is assumed by this backend; a manual that does not say is rejected
at compile time.
"""

from dataclasses import dataclass, replace
from typing import Dict, List, Optional, Tuple

Cell = Tuple[int, int]

DIRECTIONS: Dict[str, Cell] = {
    "up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1),
}
ACTIONS = [("push", "Cart", d) for d in ("up", "down", "left", "right")]

SEMANTICS = {'frame': 'persist', 'conflict': 'exclusive', 'cascade': 'single_frame'}
GRID = (9, 9)
BACKGROUND = 0
LANDMARKS: Dict[str, Cell] = {'portal_exit': (7, 6)}
BOARD: List[List[int]] = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 1, 0, 0, 1, 0, 0, 1],
    [1, 0, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 0, 0, 0, 1, 0, 0, 1],
    [1, 1, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 1, 1, 3, 1, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1],
]


@dataclass
class State:
    """One state.  Field per object per observation in the word table."""
    Button_pos: Cell = (0, 0)
    Button_colour: int = 0
    Cart_pos: Cell = (0, 0)
    Cart_colour: int = 0
    Door_pos: Cell = (0, 0)
    Door_colour: int = 0
    Door_present: bool = True

    def copy(self) -> 'State':
        return replace(self)

    def key(self):
        return (self.Button_pos, self.Button_colour, self.Cart_pos, self.Cart_colour, self.Door_pos, self.Door_colour, self.Door_present)


def render(state: State) -> List[List[int]]:
    """The manual drawn back onto a frame (constraint 2, cheap layer)."""
    grid = [list(row) for row in BOARD]
    if True:
        r, c = state.Button_pos
        grid[r][c] = state.Button_colour
    if True:
        r, c = state.Cart_pos
        grid[r][c] = state.Cart_colour
    if state.Door_present:
        r, c = state.Door_pos
        grid[r][c] = state.Door_colour
    return grid


def responsibility(state: State):
    """Which object owns each pixel; `None` means the board owns it.

    Returns (owner_grid, contested).  `contested` is non-empty exactly
    when two objects claim the same pixel, which the manual forbids.
    """
    owner: List[List[Optional[str]]] = [[None] * GRID[1] for _ in range(GRID[0])]
    contested = []
    if True:
        r, c = state.Button_pos
        if owner[r][c] is not None:
            contested.append(((r, c), owner[r][c], 'Button'))
        owner[r][c] = 'Button'
    if True:
        r, c = state.Cart_pos
        if owner[r][c] is not None:
            contested.append(((r, c), owner[r][c], 'Cart'))
        owner[r][c] = 'Cart'
    if state.Door_present:
        r, c = state.Door_pos
        if owner[r][c] is not None:
            contested.append(((r, c), owner[r][c], 'Door'))
        owner[r][c] = 'Door'
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
    """push_up  [ev: t9,t11,t13  cov: 40/40]"""
    if action != ('push', 'Cart', 'up'): return False
    if not _free(state, _neighbour(state.Cart_pos, 'up')): return False
    return True


def _effect_push_up(state: State) -> None:
    state.Cart_pos = _neighbour(state.Cart_pos, 'up')


def _guard_push_down(state: State, action) -> bool:
    """push_down  [ev: t3,t12,t16  cov: 40/40]"""
    if action != ('push', 'Cart', 'down'): return False
    if not _free(state, _neighbour(state.Cart_pos, 'down')): return False
    return True


def _effect_push_down(state: State) -> None:
    state.Cart_pos = _neighbour(state.Cart_pos, 'down')


def _guard_push_left(state: State, action) -> bool:
    """push_left  [ev: t8,t10,t21  cov: 33/33]"""
    if action != ('push', 'Cart', 'left'): return False
    if not _free(state, _neighbour(state.Cart_pos, 'left')): return False
    return True


def _effect_push_left(state: State) -> None:
    state.Cart_pos = _neighbour(state.Cart_pos, 'left')


def _guard_push_right(state: State, action) -> bool:
    """push_right  [ev: t2,t6,t15  cov: 36/36]"""
    if action != ('push', 'Cart', 'right'): return False
    if not _free(state, _neighbour(state.Cart_pos, 'right')): return False
    return True


def _effect_push_right(state: State) -> None:
    state.Cart_pos = _neighbour(state.Cart_pos, 'right')


def _guard_teleport_down(state: State, action) -> bool:
    """teleport_down  [ev: t194  cov: 1/1]"""
    if action != ('push', 'Cart', 'down'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'down')) != 3: return False
    return True


def _effect_teleport_down(state: State) -> None:
    state.Cart_pos = LANDMARKS['portal_exit']


def _guard_press_up(state: State, action) -> bool:
    """press_up  [ev: t90  cov: 1/1]"""
    if action != ('push', 'Cart', 'up'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'up')) != 7: return False
    return True


def _effect_press_up(state: State) -> None:
    state.Button_colour = 8


def _guard_door_opens_up(state: State, action) -> bool:
    """door_opens_up  [ev: t90  cov: 1/1]"""
    if action != ('push', 'Cart', 'up'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'up')) != 7: return False
    return True


def _effect_door_opens_up(state: State) -> None:
    state.Door_present = False


RULES = [
    ('push_up', _guard_push_up, _effect_push_up, 'Cart'),
    ('push_down', _guard_push_down, _effect_push_down, 'Cart'),
    ('push_left', _guard_push_left, _effect_push_left, 'Cart'),
    ('push_right', _guard_push_right, _effect_push_right, 'Cart'),
    ('teleport_down', _guard_teleport_down, _effect_teleport_down, 'Cart'),
    ('press_up', _guard_press_up, _effect_press_up, 'Button'),
    ('door_opens_up', _guard_door_opens_up, _effect_door_opens_up, 'Door'),
]


class AmbiguousTransition(Exception):
    """Two rules claimed the same object: constraint 9 is violated."""


def step(state: State, action) -> State:
    """One action, one successor, per the manual's `semantics:`.

    frame persist     -- an object no firing rule touches is unchanged,
                         which is what makes this function total.
    conflict exclusive -- two rules claiming one object is an error,
                         not a precedence question.
    cascade single_frame -- every guard reads `state`, never the
                         partially updated result, and all effects
                         apply together.
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
        Button_pos=(1, 1),
        Button_colour=7,
        Cart_pos=(5, 1),
        Cart_colour=6,
        Door_pos=(6, 4),
        Door_colour=5,
        Door_present=True,
    )
