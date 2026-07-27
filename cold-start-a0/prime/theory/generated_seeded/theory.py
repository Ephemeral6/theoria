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
LANDMARKS: Dict[str, Cell] = {'portal_exit': (1, 1)}
BOARD: List[List[int]] = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 0, 0, 4, 1, 0, 0, 1],
    [1, 0, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 1],
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
    Door_pos: Cell = (0, 0)
    Door_colour: int = 0
    Door_present: bool = True
    Switch_pos: Cell = (0, 0)
    Switch_colour: int = 0

    def copy(self) -> 'State':
        return replace(self)

    def key(self):
        return (self.Cart_pos, self.Cart_colour, self.Door_pos, self.Door_colour, self.Door_present, self.Switch_pos, self.Switch_colour)


def render(state: State) -> List[List[int]]:
    """The manual drawn back onto a frame (constraint 2, cheap layer)."""
    grid = [list(row) for row in BOARD]
    if True:
        r, c = state.Cart_pos
        grid[r][c] = state.Cart_colour
    if state.Door_present:
        r, c = state.Door_pos
        grid[r][c] = state.Door_colour
    if True:
        r, c = state.Switch_pos
        grid[r][c] = state.Switch_colour
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
    if state.Door_present:
        r, c = state.Door_pos
        if owner[r][c] is not None:
            contested.append(((r, c), owner[r][c], 'Door'))
        owner[r][c] = 'Door'
    if True:
        r, c = state.Switch_pos
        if owner[r][c] is not None:
            contested.append(((r, c), owner[r][c], 'Switch'))
        owner[r][c] = 'Switch'
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
    """push_up  [ev: t12,t39  cov: 17/17]"""
    if action != ('push', 'Cart', 'up'): return False
    if not _free(state, _neighbour(state.Cart_pos, 'up')): return False
    return True


def _effect_push_up(state: State) -> None:
    state.Cart_pos = _neighbour(state.Cart_pos, 'up')


def _guard_push_down(state: State, action) -> bool:
    """push_down  [ev: t0,t5,t9  cov: 26/26]"""
    if action != ('push', 'Cart', 'down'): return False
    if not _free(state, _neighbour(state.Cart_pos, 'down')): return False
    return True


def _effect_push_down(state: State) -> None:
    state.Cart_pos = _neighbour(state.Cart_pos, 'down')


def _guard_push_left(state: State, action) -> bool:
    """push_left  [ev: t3,t46  cov: 16/16]"""
    if action != ('push', 'Cart', 'left'): return False
    if not _free(state, _neighbour(state.Cart_pos, 'left')): return False
    return True


def _effect_push_left(state: State) -> None:
    state.Cart_pos = _neighbour(state.Cart_pos, 'left')


def _guard_push_right(state: State, action) -> bool:
    """push_right  [ev: t1,t38  cov: 23/23]"""
    if action != ('push', 'Cart', 'right'): return False
    if not _free(state, _neighbour(state.Cart_pos, 'right')): return False
    return True


def _effect_push_right(state: State) -> None:
    state.Cart_pos = _neighbour(state.Cart_pos, 'right')


def _guard_push_onto_crate(state: State, action) -> bool:
    """push_onto_crate  [ev: none  cov: 0/0]"""
    if action != ('push', 'Cart', 'right'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'right')) != 4: return False
    return True


def _effect_push_onto_crate(state: State) -> None:
    state.Cart_pos = _neighbour(state.Cart_pos, 'right')


def _guard_teleport_down(state: State, action) -> bool:
    """teleport_down  [ev: t11,t43  cov: 2/2]"""
    if action != ('push', 'Cart', 'down'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'down')) != 3: return False
    return True


def _effect_teleport_down(state: State) -> None:
    state.Cart_pos = LANDMARKS['portal_exit']


def _guard_switch_on_up(state: State, action) -> bool:
    """switch_on_up  [ev: t12  cov: 1/1]"""
    if action != ('push', 'Cart', 'up'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'up')) != 7: return False
    return True


def _effect_switch_on_up(state: State) -> None:
    state.Switch_colour = 8


def _guard_switch_on_down(state: State, action) -> bool:
    """switch_on_down  [ev: t43  cov: 1/1]"""
    if action != ('push', 'Cart', 'down'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'down')) != 7: return False
    return True


def _effect_switch_on_down(state: State) -> None:
    state.Switch_colour = 8


def _guard_switch_on_left(state: State, action) -> bool:
    """switch_on_left  [ev: t106  cov: 1/1]"""
    if action != ('push', 'Cart', 'left'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'left')) != 7: return False
    return True


def _effect_switch_on_left(state: State) -> None:
    state.Switch_colour = 8


def _guard_switch_on_right(state: State, action) -> bool:
    """switch_on_right  [ev: t11  cov: 1/1]"""
    if action != ('push', 'Cart', 'right'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'right')) != 7: return False
    return True


def _effect_switch_on_right(state: State) -> None:
    state.Switch_colour = 8


def _guard_door_opens_up(state: State, action) -> bool:
    """door_opens_up  [ev: t12  cov: 1/1]"""
    if action != ('push', 'Cart', 'up'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'up')) != 7: return False
    return True


def _effect_door_opens_up(state: State) -> None:
    state.Door_present = False


def _guard_door_opens_down(state: State, action) -> bool:
    """door_opens_down  [ev: t43  cov: 1/1]"""
    if action != ('push', 'Cart', 'down'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'down')) != 7: return False
    return True


def _effect_door_opens_down(state: State) -> None:
    state.Door_present = False


def _guard_door_opens_left(state: State, action) -> bool:
    """door_opens_left  [ev: t106  cov: 1/1]"""
    if action != ('push', 'Cart', 'left'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'left')) != 7: return False
    return True


def _effect_door_opens_left(state: State) -> None:
    state.Door_present = False


def _guard_door_opens_right(state: State, action) -> bool:
    """door_opens_right  [ev: t11  cov: 1/1]"""
    if action != ('push', 'Cart', 'right'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'right')) != 7: return False
    return True


def _effect_door_opens_right(state: State) -> None:
    state.Door_present = False


def _guard_switch_off_up(state: State, action) -> bool:
    """switch_off_up  [ev: t39  cov: 1/1]"""
    if action != ('push', 'Cart', 'up'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'up')) != 8: return False
    return True


def _effect_switch_off_up(state: State) -> None:
    state.Switch_colour = 7


def _guard_switch_off_down(state: State, action) -> bool:
    """switch_off_down  [ev: t46  cov: 1/1]"""
    if action != ('push', 'Cart', 'down'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'down')) != 8: return False
    return True


def _effect_switch_off_down(state: State) -> None:
    state.Switch_colour = 7


def _guard_switch_off_left(state: State, action) -> bool:
    """switch_off_left  [ev: t85  cov: 1/1]"""
    if action != ('push', 'Cart', 'left'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'left')) != 8: return False
    return True


def _effect_switch_off_left(state: State) -> None:
    state.Switch_colour = 7


def _guard_switch_off_right(state: State, action) -> bool:
    """switch_off_right  [ev: t38  cov: 1/1]"""
    if action != ('push', 'Cart', 'right'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'right')) != 8: return False
    return True


def _effect_switch_off_right(state: State) -> None:
    state.Switch_colour = 7


def _guard_door_shuts_up(state: State, action) -> bool:
    """door_shuts_up  [ev: t39  cov: 1/1]"""
    if action != ('push', 'Cart', 'up'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'up')) != 8: return False
    return True


def _effect_door_shuts_up(state: State) -> None:
    state.Door_present = True


def _guard_door_shuts_down(state: State, action) -> bool:
    """door_shuts_down  [ev: t46  cov: 1/1]"""
    if action != ('push', 'Cart', 'down'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'down')) != 8: return False
    return True


def _effect_door_shuts_down(state: State) -> None:
    state.Door_present = True


def _guard_door_shuts_left(state: State, action) -> bool:
    """door_shuts_left  [ev: t85  cov: 1/1]"""
    if action != ('push', 'Cart', 'left'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'left')) != 8: return False
    return True


def _effect_door_shuts_left(state: State) -> None:
    state.Door_present = True


def _guard_door_shuts_right(state: State, action) -> bool:
    """door_shuts_right  [ev: t38  cov: 1/1]"""
    if action != ('push', 'Cart', 'right'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'right')) != 8: return False
    return True


def _effect_door_shuts_right(state: State) -> None:
    state.Door_present = True


RULES = [
    ('push_up', _guard_push_up, _effect_push_up, 'Cart'),
    ('push_down', _guard_push_down, _effect_push_down, 'Cart'),
    ('push_left', _guard_push_left, _effect_push_left, 'Cart'),
    ('push_right', _guard_push_right, _effect_push_right, 'Cart'),
    ('push_onto_crate', _guard_push_onto_crate, _effect_push_onto_crate, 'Cart'),
    ('teleport_down', _guard_teleport_down, _effect_teleport_down, 'Cart'),
    ('switch_on_up', _guard_switch_on_up, _effect_switch_on_up, 'Switch'),
    ('switch_on_down', _guard_switch_on_down, _effect_switch_on_down, 'Switch'),
    ('switch_on_left', _guard_switch_on_left, _effect_switch_on_left, 'Switch'),
    ('switch_on_right', _guard_switch_on_right, _effect_switch_on_right, 'Switch'),
    ('door_opens_up', _guard_door_opens_up, _effect_door_opens_up, 'Door'),
    ('door_opens_down', _guard_door_opens_down, _effect_door_opens_down, 'Door'),
    ('door_opens_left', _guard_door_opens_left, _effect_door_opens_left, 'Door'),
    ('door_opens_right', _guard_door_opens_right, _effect_door_opens_right, 'Door'),
    ('switch_off_up', _guard_switch_off_up, _effect_switch_off_up, 'Switch'),
    ('switch_off_down', _guard_switch_off_down, _effect_switch_off_down, 'Switch'),
    ('switch_off_left', _guard_switch_off_left, _effect_switch_off_left, 'Switch'),
    ('switch_off_right', _guard_switch_off_right, _effect_switch_off_right, 'Switch'),
    ('door_shuts_up', _guard_door_shuts_up, _effect_door_shuts_up, 'Door'),
    ('door_shuts_down', _guard_door_shuts_down, _effect_door_shuts_down, 'Door'),
    ('door_shuts_left', _guard_door_shuts_left, _effect_door_shuts_left, 'Door'),
    ('door_shuts_right', _guard_door_shuts_right, _effect_door_shuts_right, 'Door'),
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
        Cart_pos=(5, 1),
        Cart_colour=6,
        Door_pos=(4, 5),
        Door_colour=5,
        Door_present=True,
        Switch_pos=(3, 2),
        Switch_colour=7,
    )
