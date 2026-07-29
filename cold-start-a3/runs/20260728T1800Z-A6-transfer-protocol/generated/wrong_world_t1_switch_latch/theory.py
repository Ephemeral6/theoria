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
GRID = (6, 7)
BACKGROUND = 0
LANDMARKS: Dict[str, Cell] = {}
BOARD: List[List[int]] = [
    [1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 1, 0, 1],
    [1, 0, 0, 0, 1, 0, 1],
    [1, 0, 0, 0, 4, 0, 1],
    [1, 0, 4, 0, 1, 0, 1],
    [1, 1, 1, 1, 1, 1, 1],
]


@dataclass
class State:
    """One state.  Field per object per observation in the word table."""
    Block_pos: Cell = (0, 0)
    Block_colour: int = 0
    Cart_pos: Cell = (0, 0)
    Cart_colour: int = 0

    def copy(self) -> 'State':
        return replace(self)

    def key(self):
        return (self.Block_pos, self.Block_colour, self.Cart_pos, self.Cart_colour)


def render(state: State) -> List[List[int]]:
    """The manual drawn back onto a frame (constraint 2, cheap layer)."""
    grid = [list(row) for row in BOARD]
    if True:
        r, c = state.Block_pos
        grid[r][c] = state.Block_colour
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
        r, c = state.Block_pos
        if owner[r][c] is not None:
            contested.append(((r, c), owner[r][c], 'Block'))
        owner[r][c] = 'Block'
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


def _guard_step_up(state: State, action) -> bool:
    """step_up  [ev: t7,t10,t23,t26  cov: 5/5]"""
    if action != ('push', 'Cart', 'up'): return False
    if not _free(state, _neighbour(state.Cart_pos, 'up')): return False
    return True


def _effect_step_up(state: State) -> None:
    state.Cart_pos = _neighbour(state.Cart_pos, 'up')


def _guard_step_down(state: State, action) -> bool:
    """step_down  [ev: t0,t9,t16,t25  cov: 5/5]"""
    if action != ('push', 'Cart', 'down'): return False
    if not _free(state, _neighbour(state.Cart_pos, 'down')): return False
    return True


def _effect_step_down(state: State) -> None:
    state.Cart_pos = _neighbour(state.Cart_pos, 'down')


def _guard_step_left(state: State, action) -> bool:
    """step_left  [ev: t2,t8,t15,t18  cov: 7/7]"""
    if action != ('push', 'Cart', 'left'): return False
    if not _free(state, _neighbour(state.Cart_pos, 'left')): return False
    return True


def _effect_step_left(state: State) -> None:
    state.Cart_pos = _neighbour(state.Cart_pos, 'left')


def _guard_step_right(state: State, action) -> bool:
    """step_right  [ev: t5,t12,t21,t28  cov: 6/6]"""
    if action != ('push', 'Cart', 'right'): return False
    if not _free(state, _neighbour(state.Cart_pos, 'right')): return False
    return True


def _effect_step_right(state: State) -> None:
    state.Cart_pos = _neighbour(state.Cart_pos, 'right')


def _guard_shove_up(state: State, action) -> bool:
    """shove_up  [ev: symmetry  cov: 0/0]"""
    if action != ('push', 'Cart', 'up'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'up')) != 2: return False
    if not _free(state, _neighbour(state.Block_pos, 'up')): return False
    return True


def _effect_shove_up(state: State) -> None:
    state.Cart_pos = _neighbour(state.Cart_pos, 'up')


def _guard_shove_down(state: State, action) -> bool:
    """shove_down  [ev: symmetry  cov: 0/0]"""
    if action != ('push', 'Cart', 'down'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'down')) != 2: return False
    if not _free(state, _neighbour(state.Block_pos, 'down')): return False
    return True


def _effect_shove_down(state: State) -> None:
    state.Cart_pos = _neighbour(state.Cart_pos, 'down')


def _guard_shove_left(state: State, action) -> bool:
    """shove_left  [ev: symmetry  cov: 0/0]"""
    if action != ('push', 'Cart', 'left'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'left')) != 2: return False
    if not _free(state, _neighbour(state.Block_pos, 'left')): return False
    return True


def _effect_shove_left(state: State) -> None:
    state.Cart_pos = _neighbour(state.Cart_pos, 'left')


def _guard_shove_right(state: State, action) -> bool:
    """shove_right  [ev: t13,t30  cov: 2/2]"""
    if action != ('push', 'Cart', 'right'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'right')) != 2: return False
    if not _free(state, _neighbour(state.Block_pos, 'right')): return False
    return True


def _effect_shove_right(state: State) -> None:
    state.Cart_pos = _neighbour(state.Cart_pos, 'right')


def _guard_block_up(state: State, action) -> bool:
    """block_up  [ev: symmetry  cov: 0/0]"""
    if action != ('push', 'Cart', 'up'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'up')) != 2: return False
    if not _free(state, _neighbour(state.Block_pos, 'up')): return False
    return True


def _effect_block_up(state: State) -> None:
    state.Block_pos = _neighbour(state.Block_pos, 'up')


def _guard_block_down(state: State, action) -> bool:
    """block_down  [ev: symmetry  cov: 0/0]"""
    if action != ('push', 'Cart', 'down'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'down')) != 2: return False
    if not _free(state, _neighbour(state.Block_pos, 'down')): return False
    return True


def _effect_block_down(state: State) -> None:
    state.Block_pos = _neighbour(state.Block_pos, 'down')


def _guard_block_left(state: State, action) -> bool:
    """block_left  [ev: symmetry  cov: 0/0]"""
    if action != ('push', 'Cart', 'left'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'left')) != 2: return False
    if not _free(state, _neighbour(state.Block_pos, 'left')): return False
    return True


def _effect_block_left(state: State) -> None:
    state.Block_pos = _neighbour(state.Block_pos, 'left')


def _guard_block_right(state: State, action) -> bool:
    """block_right  [ev: t13,t30  cov: 2/2]"""
    if action != ('push', 'Cart', 'right'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'right')) != 2: return False
    if not _free(state, _neighbour(state.Block_pos, 'right')): return False
    return True


def _effect_block_right(state: State) -> None:
    state.Block_pos = _neighbour(state.Block_pos, 'right')


RULES = [
    ('step_up', _guard_step_up, _effect_step_up, 'Cart'),
    ('step_down', _guard_step_down, _effect_step_down, 'Cart'),
    ('step_left', _guard_step_left, _effect_step_left, 'Cart'),
    ('step_right', _guard_step_right, _effect_step_right, 'Cart'),
    ('shove_up', _guard_shove_up, _effect_shove_up, 'Cart'),
    ('shove_down', _guard_shove_down, _effect_shove_down, 'Cart'),
    ('shove_left', _guard_shove_left, _effect_shove_left, 'Cart'),
    ('shove_right', _guard_shove_right, _effect_shove_right, 'Cart'),
    ('block_up', _guard_block_up, _effect_block_up, 'Block'),
    ('block_down', _guard_block_down, _effect_block_down, 'Block'),
    ('block_left', _guard_block_left, _effect_block_left, 'Block'),
    ('block_right', _guard_block_right, _effect_block_right, 'Block'),
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
    return state.Cart_pos == (4, 5)


def simulate(initial: State, actions) -> List[State]:
    states = [initial]
    current = initial
    for action in actions:
        current = step(current, action)
        states.append(current)
    return states


def initial_state() -> State:
    return State(
        Block_pos=(4, 1),
        Block_colour=2,
        Cart_pos=(1, 2),
        Cart_colour=6,
    )
