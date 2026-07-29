"""Auto-generated from theory.dsl — DO NOT EDIT.

Change the manual and recompile. This module is the only predictor
in the system: certify's replay, the Lean generator's transition
table and the plan validator all read the world through `step`.

`step` implements the semantics the manual *declares*; nothing
about the frame axiom, the conflict policy or the cascade shape is
assumed here, and a manual that does not say is refused.
"""

from dataclasses import dataclass, replace

SEMANTICS = {'frame': 'persist', 'conflict': 'exclusive', 'cascade': 'single_frame'}
GEOMETRY = 'grid'
DIRECTIONS = {'up': (-1, 0), 'down': (1, 0), 'left': (0, -1), 'right': (0, 1)}
LANDMARKS = {'portal_exit': (1, 1)}
BACKGROUND = 0
N_POS = None
GRID = (9, 9)
BOARD = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 0, 0, 1, 1, 0, 0, 1],
    [1, 1, 1, 3, 1, 1, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1],
]
ACTIONS = [('push', 'Cart', 'up'), ('push', 'Cart', 'down'), ('push', 'Cart', 'left'), ('push', 'Cart', 'right')]


@dataclass
class State:
    """One field per instance per observation the word table names."""
    Button_pos: object = (3, 2)
    Button_color: object = 7
    Cart_pos: object = (5, 1)
    Cart_color: object = 6
    Door_pos: object = (4, 5)
    Door_color: object = 5
    Door_present: object = True

    def copy(self):
        return replace(self)

    def key(self):
        return (self.Button_pos, self.Button_color, self.Cart_pos, self.Cart_color, self.Door_pos, self.Door_color, self.Door_present,)


def _neighbour(cell, direction):
    dr, dc = DIRECTIONS[direction]
    return (cell[0] + dr, cell[1] + dc)


def _in_bounds(cell):
    return 0 <= cell[0] < GRID[0] and 0 <= cell[1] < GRID[1]


def _adjacent(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1


def render(state, _exclude=()):
    """The manual drawn back onto a frame.

    `_exclude` leaves the named instances off the frame. It exists
    for `_free_except` and ledger X-5: asking whether an object's
    own cell is free is a question about the board and the *other*
    objects, and painting the asker onto the frame first makes the
    answer unconditionally False.
    """
    grid = [list(row) for row in BOARD]
    if 'Button' not in _exclude:
        r, c = state.Button_pos
        grid[r][c] = state.Button_color
    if 'Cart' not in _exclude:
        r, c = state.Cart_pos
        grid[r][c] = state.Cart_color
    if 'Door' not in _exclude and state.Door_present:
        r, c = state.Door_pos
        grid[r][c] = state.Door_color
    return grid


def _cell_colour(state, cell, _exclude=()):
    if not _in_bounds(cell):
        return None
    return render(state, _exclude)[cell[0]][cell[1]]


def _free(state, cell):
    return _cell_colour(state, cell) == BACKGROUND


def _free_except(state, cell, exclude):
    """`free(<obj>.pos)` — is the asker's own cell a legal empty one?

    Ledger X-5. On the board, not a wall, and nobody *else* on it.
    False exactly when the object stands off the board, on a wall,
    or on top of another object.
    """
    return _cell_colour(state, cell, exclude) == BACKGROUND


def occupancy(state):
    """The frame as a bitstring — the view a pagoda weight sees."""
    return ''.join('0' if v == BACKGROUND else '1'
                   for row in render(state) for v in row)


def _guard_push_up(state, action):
    """push_up  [ev: t6,t16,t21  cov: 52/52]"""
    if action != ('push', 'Cart', 'up'): return False
    if not (_free(state, _neighbour(state.Cart_pos, 'up'))): return False
    return True


def _effect_push_up(state):
    state.Cart_pos = _neighbour(state.Cart_pos, 'up')


def _guard_push_down(state, action):
    """push_down  [ev: t0,t9,t12  cov: 62/62]"""
    if action != ('push', 'Cart', 'down'): return False
    if not (_free(state, _neighbour(state.Cart_pos, 'down'))): return False
    return True


def _effect_push_down(state):
    state.Cart_pos = _neighbour(state.Cart_pos, 'down')


def _guard_push_left(state, action):
    """push_left  [ev: t5,t20,t27  cov: 46/46]"""
    if action != ('push', 'Cart', 'left'): return False
    if not (_free(state, _neighbour(state.Cart_pos, 'left'))): return False
    return True


def _effect_push_left(state):
    state.Cart_pos = _neighbour(state.Cart_pos, 'left')


def _guard_push_right(state, action):
    """push_right  [ev: t3,t8,t10  cov: 52/52]"""
    if action != ('push', 'Cart', 'right'): return False
    if not (_free(state, _neighbour(state.Cart_pos, 'right'))): return False
    return True


def _effect_push_right(state):
    state.Cart_pos = _neighbour(state.Cart_pos, 'right')


def _guard_teleport_down(state, action):
    """teleport_down  [ev: t11,t103  cov: 2/2]"""
    if action != ('push', 'Cart', 'down'): return False
    if not (_cell_colour(state, _neighbour(state.Cart_pos, 'down')) == 3): return False
    return True


def _effect_teleport_down(state):
    state.Cart_pos = LANDMARKS['portal_exit']


def _guard_press_left(state, action):
    """press_left  [ev: t99  cov: 1/1]"""
    if action != ('push', 'Cart', 'left'): return False
    if not (_cell_colour(state, _neighbour(state.Cart_pos, 'left')) == 7): return False
    return True


def _effect_press_left(state):
    state.Button_color = 8


def _guard_door_opens_left(state, action):
    """door_opens_left  [ev: t99  cov: 1/1]"""
    if action != ('push', 'Cart', 'left'): return False
    if not (_cell_colour(state, _neighbour(state.Cart_pos, 'left')) == 7): return False
    return True


def _effect_door_opens_left(state):
    state.Door_present = False


RULES = [
    ('push_up', _guard_push_up, _effect_push_up, ['Cart']),
    ('push_down', _guard_push_down, _effect_push_down, ['Cart']),
    ('push_left', _guard_push_left, _effect_push_left, ['Cart']),
    ('push_right', _guard_push_right, _effect_push_right, ['Cart']),
    ('teleport_down', _guard_teleport_down, _effect_teleport_down, ['Cart']),
    ('press_left', _guard_press_left, _effect_press_left, ['Button']),
    ('door_opens_left', _guard_door_opens_left, _effect_door_opens_left, ['Door']),
]


class AmbiguousTransition(Exception):
    """Two rules claimed one object: `conflict exclusive` is violated."""


def step(state, action):
    """One action, one successor, per the manual's `semantics:`.

    frame persist        -- an object no firing rule touches is
                            unchanged, which is what makes this total.
    conflict exclusive   -- two rules claiming one object is an error,
                            not a precedence question.
    cascade single_frame -- every guard reads `state`, never the
                            partially updated result.
    """
    result = state.copy()
    claimed = {}
    for name, guard, effect, objs in RULES:
        if not guard(state, action):
            continue
        for obj in objs:
            if obj in claimed:
                raise AmbiguousTransition(
                    '%s and %s both fire on %s for %s'
                    % (claimed[obj], name, action, obj))
            claimed[obj] = name
        effect(result)
    return result


def fired(state, action):
    return [n for n, g, _e, _o in RULES if g(state, action)]


def is_goal(state):
    return (state.Cart_pos == (2, 7))


def simulate(initial, actions):
    states = [initial]
    current = initial
    for action in actions:
        current = step(current, action)
        states.append(current)
    return states


def initial_state():
    return State(
        Button_pos=(3, 2),
        Button_color=7,
        Cart_pos=(5, 1),
        Cart_color=6,
        Door_pos=(4, 5),
        Door_color=5,
        Door_present=True,
    )
