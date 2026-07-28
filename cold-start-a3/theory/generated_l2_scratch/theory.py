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
LANDMARKS: Dict[str, Cell] = {'exit_a': (1, 5), 'exit_b': (4, 1)}
BOARD: List[List[int]] = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 1, 0, 4, 0, 1],
    [1, 0, 1, 1, 1, 0, 0, 0, 1],
    [1, 0, 1, 0, 1, 0, 0, 0, 1],
    [1, 0, 0, 0, 1, 0, 0, 0, 1],
    [1, 3, 0, 0, 1, 0, 0, 0, 1],
    [1, 0, 0, 0, 1, 0, 0, 0, 1],
    [1, 0, 0, 0, 1, 1, 0, 1, 1],
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


def _guard_step_up(state: State, action) -> bool:
    """step_up  [ev: t0,t1,t2,t3,t13  cov: 72/72]"""
    if action != ('push', 'Cart', 'up'): return False
    if not _free(state, _neighbour(state.Cart_pos, 'up')): return False
    return True


def _effect_step_up(state: State) -> None:
    state.Cart_pos = _neighbour(state.Cart_pos, 'up')


def _guard_step_down(state: State, action) -> bool:
    """step_down  [ev: t6,t7,t8,t9,t10  cov: 78/78]"""
    if action != ('push', 'Cart', 'down'): return False
    if not _free(state, _neighbour(state.Cart_pos, 'down')): return False
    return True


def _effect_step_down(state: State) -> None:
    state.Cart_pos = _neighbour(state.Cart_pos, 'down')


def _guard_step_left(state: State, action) -> bool:
    """step_left  [ev: t12,t30,t38,t48,t85  cov: 42/42]"""
    if action != ('push', 'Cart', 'left'): return False
    if not _free(state, _neighbour(state.Cart_pos, 'left')): return False
    return True


def _effect_step_left(state: State) -> None:
    state.Cart_pos = _neighbour(state.Cart_pos, 'left')


def _guard_step_right(state: State, action) -> bool:
    """step_right  [ev: t26,t31,t32,t39,t56  cov: 54/54]"""
    if action != ('push', 'Cart', 'right'): return False
    if not _free(state, _neighbour(state.Cart_pos, 'right')): return False
    return True


def _effect_step_right(state: State) -> None:
    state.Cart_pos = _neighbour(state.Cart_pos, 'right')


def _guard_warp_a_up(state: State, action) -> bool:
    """warp_a_up  [ev: t193,t293  cov: 2/2]"""
    if action != ('push', 'Cart', 'up'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'up')) != 3: return False
    return True


def _effect_warp_a_up(state: State) -> None:
    state.Cart_pos = LANDMARKS['exit_a']


def _guard_warp_a_down(state: State, action) -> bool:
    """warp_a_down  [ev: t19,t74  cov: 2/2]"""
    if action != ('push', 'Cart', 'down'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'down')) != 3: return False
    return True


def _effect_warp_a_down(state: State) -> None:
    state.Cart_pos = LANDMARKS['exit_a']


def _guard_warp_a_left(state: State, action) -> bool:
    """warp_a_left  [ev: t51,t130,t223  cov: 3/3]"""
    if action != ('push', 'Cart', 'left'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'left')) != 3: return False
    return True


def _effect_warp_a_left(state: State) -> None:
    state.Cart_pos = LANDMARKS['exit_a']


def _guard_warp_a_right(state: State, action) -> bool:
    """warp_a_right  [ev: none  cov: 0/0]"""
    if action != ('push', 'Cart', 'right'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'right')) != 3: return False
    return True


def _effect_warp_a_right(state: State) -> None:
    state.Cart_pos = LANDMARKS['exit_a']


def _guard_warp_b_up(state: State, action) -> bool:
    """warp_b_up  [ev: t17,t66  cov: 2/2]"""
    if action != ('push', 'Cart', 'up'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'up')) != 4: return False
    return True


def _effect_warp_b_up(state: State) -> None:
    state.Cart_pos = LANDMARKS['exit_b']


def _guard_warp_b_down(state: State, action) -> bool:
    """warp_b_down  [ev: none  cov: 0/0]"""
    if action != ('push', 'Cart', 'down'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'down')) != 4: return False
    return True


def _effect_warp_b_down(state: State) -> None:
    state.Cart_pos = LANDMARKS['exit_b']


def _guard_warp_b_left(state: State, action) -> bool:
    """warp_b_left  [ev: t181,t199,t281,t313  cov: 4/4]"""
    if action != ('push', 'Cart', 'left'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'left')) != 4: return False
    return True


def _effect_warp_b_left(state: State) -> None:
    state.Cart_pos = LANDMARKS['exit_b']


def _guard_warp_b_right(state: State, action) -> bool:
    """warp_b_right  [ev: t24,t79  cov: 2/2]"""
    if action != ('push', 'Cart', 'right'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'right')) != 4: return False
    return True


def _effect_warp_b_right(state: State) -> None:
    state.Cart_pos = LANDMARKS['exit_b']


def _guard_switch_press_up(state: State, action) -> bool:
    """switch_press_up  [ev: none  cov: 0/0]"""
    if action != ('push', 'Cart', 'up'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'up')) != 7: return False
    return True


def _effect_switch_press_up(state: State) -> None:
    state.Switch_colour = 8


def _guard_switch_press_down(state: State, action) -> bool:
    """switch_press_down  [ev: t61,t230  cov: 2/2]"""
    if action != ('push', 'Cart', 'down'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'down')) != 7: return False
    return True


def _effect_switch_press_down(state: State) -> None:
    state.Switch_colour = 8


def _guard_switch_press_left(state: State, action) -> bool:
    """switch_press_left  [ev: none  cov: 0/0]"""
    if action != ('push', 'Cart', 'left'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'left')) != 7: return False
    return True


def _effect_switch_press_left(state: State) -> None:
    state.Switch_colour = 8


def _guard_switch_press_right(state: State, action) -> bool:
    """switch_press_right  [ev: none  cov: 0/0]"""
    if action != ('push', 'Cart', 'right'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'right')) != 7: return False
    return True


def _effect_switch_press_right(state: State) -> None:
    state.Switch_colour = 8


def _guard_door_opens_up(state: State, action) -> bool:
    """door_opens_up  [ev: none  cov: 0/0]"""
    if action != ('push', 'Cart', 'up'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'up')) != 7: return False
    return True


def _effect_door_opens_up(state: State) -> None:
    state.Door_present = False


def _guard_door_opens_down(state: State, action) -> bool:
    """door_opens_down  [ev: t61,t230  cov: 2/2]"""
    if action != ('push', 'Cart', 'down'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'down')) != 7: return False
    return True


def _effect_door_opens_down(state: State) -> None:
    state.Door_present = False


def _guard_door_opens_left(state: State, action) -> bool:
    """door_opens_left  [ev: none  cov: 0/0]"""
    if action != ('push', 'Cart', 'left'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'left')) != 7: return False
    return True


def _effect_door_opens_left(state: State) -> None:
    state.Door_present = False


def _guard_door_opens_right(state: State, action) -> bool:
    """door_opens_right  [ev: none  cov: 0/0]"""
    if action != ('push', 'Cart', 'right'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'right')) != 7: return False
    return True


def _effect_door_opens_right(state: State) -> None:
    state.Door_present = False


def _guard_switch_release_up(state: State, action) -> bool:
    """switch_release_up  [ev: none  cov: 0/0]"""
    if action != ('push', 'Cart', 'up'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'up')) != 8: return False
    return True


def _effect_switch_release_up(state: State) -> None:
    state.Switch_colour = 7


def _guard_switch_release_down(state: State, action) -> bool:
    """switch_release_down  [ev: t140  cov: 1/1]"""
    if action != ('push', 'Cart', 'down'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'down')) != 8: return False
    return True


def _effect_switch_release_down(state: State) -> None:
    state.Switch_colour = 7


def _guard_switch_release_left(state: State, action) -> bool:
    """switch_release_left  [ev: none  cov: 0/0]"""
    if action != ('push', 'Cart', 'left'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'left')) != 8: return False
    return True


def _effect_switch_release_left(state: State) -> None:
    state.Switch_colour = 7


def _guard_switch_release_right(state: State, action) -> bool:
    """switch_release_right  [ev: none  cov: 0/0]"""
    if action != ('push', 'Cart', 'right'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'right')) != 8: return False
    return True


def _effect_switch_release_right(state: State) -> None:
    state.Switch_colour = 7


def _guard_door_closes_up(state: State, action) -> bool:
    """door_closes_up  [ev: none  cov: 0/0]"""
    if action != ('push', 'Cart', 'up'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'up')) != 8: return False
    return True


def _effect_door_closes_up(state: State) -> None:
    state.Door_present = True


def _guard_door_closes_down(state: State, action) -> bool:
    """door_closes_down  [ev: t140  cov: 1/1]"""
    if action != ('push', 'Cart', 'down'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'down')) != 8: return False
    return True


def _effect_door_closes_down(state: State) -> None:
    state.Door_present = True


def _guard_door_closes_left(state: State, action) -> bool:
    """door_closes_left  [ev: none  cov: 0/0]"""
    if action != ('push', 'Cart', 'left'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'left')) != 8: return False
    return True


def _effect_door_closes_left(state: State) -> None:
    state.Door_present = True


def _guard_door_closes_right(state: State, action) -> bool:
    """door_closes_right  [ev: none  cov: 0/0]"""
    if action != ('push', 'Cart', 'right'): return False
    if _cell_colour(state, _neighbour(state.Cart_pos, 'right')) != 8: return False
    return True


def _effect_door_closes_right(state: State) -> None:
    state.Door_present = True


RULES = [
    ('step_up', _guard_step_up, _effect_step_up, 'Cart'),
    ('step_down', _guard_step_down, _effect_step_down, 'Cart'),
    ('step_left', _guard_step_left, _effect_step_left, 'Cart'),
    ('step_right', _guard_step_right, _effect_step_right, 'Cart'),
    ('warp_a_up', _guard_warp_a_up, _effect_warp_a_up, 'Cart'),
    ('warp_a_down', _guard_warp_a_down, _effect_warp_a_down, 'Cart'),
    ('warp_a_left', _guard_warp_a_left, _effect_warp_a_left, 'Cart'),
    ('warp_a_right', _guard_warp_a_right, _effect_warp_a_right, 'Cart'),
    ('warp_b_up', _guard_warp_b_up, _effect_warp_b_up, 'Cart'),
    ('warp_b_down', _guard_warp_b_down, _effect_warp_b_down, 'Cart'),
    ('warp_b_left', _guard_warp_b_left, _effect_warp_b_left, 'Cart'),
    ('warp_b_right', _guard_warp_b_right, _effect_warp_b_right, 'Cart'),
    ('switch_press_up', _guard_switch_press_up, _effect_switch_press_up, 'Switch'),
    ('switch_press_down', _guard_switch_press_down, _effect_switch_press_down, 'Switch'),
    ('switch_press_left', _guard_switch_press_left, _effect_switch_press_left, 'Switch'),
    ('switch_press_right', _guard_switch_press_right, _effect_switch_press_right, 'Switch'),
    ('door_opens_up', _guard_door_opens_up, _effect_door_opens_up, 'Door'),
    ('door_opens_down', _guard_door_opens_down, _effect_door_opens_down, 'Door'),
    ('door_opens_left', _guard_door_opens_left, _effect_door_opens_left, 'Door'),
    ('door_opens_right', _guard_door_opens_right, _effect_door_opens_right, 'Door'),
    ('switch_release_up', _guard_switch_release_up, _effect_switch_release_up, 'Switch'),
    ('switch_release_down', _guard_switch_release_down, _effect_switch_release_down, 'Switch'),
    ('switch_release_left', _guard_switch_release_left, _effect_switch_release_left, 'Switch'),
    ('switch_release_right', _guard_switch_release_right, _effect_switch_release_right, 'Switch'),
    ('door_closes_up', _guard_door_closes_up, _effect_door_closes_up, 'Door'),
    ('door_closes_down', _guard_door_closes_down, _effect_door_closes_down, 'Door'),
    ('door_closes_left', _guard_door_closes_left, _effect_door_closes_left, 'Door'),
    ('door_closes_right', _guard_door_closes_right, _effect_door_closes_right, 'Door'),
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
    return state.Cart_pos == (1, 1)


def simulate(initial: State, actions) -> List[State]:
    states = [initial]
    current = initial
    for action in actions:
        current = step(current, action)
        states.append(current)
    return states


def initial_state() -> State:
    return State(
        Cart_pos=(6, 7),
        Cart_colour=6,
        Door_pos=(3, 1),
        Door_colour=5,
        Door_present=True,
        Switch_pos=(7, 6),
        Switch_colour=7,
    )
