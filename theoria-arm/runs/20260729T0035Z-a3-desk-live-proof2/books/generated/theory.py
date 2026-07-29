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
LANDMARKS = {}
BACKGROUND = 1
N_POS = None
GRID = (8, 8)
BOARD = [
    [1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 0, 1],
    [1, 1, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 0, 1],
    [1, 1, 0, 4, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 3, 1],
    [1, 1, 1, 1, 1, 1, 1, 1],
]
ACTIONS = [('key', 2)]


@dataclass
class State:
    """One field per instance per observation the word table names."""
    Floor_r2c1_pos: object = (2, 1)
    Floor_r2c1_color: object = 0
    Floor_r3c1_pos: object = (3, 1)
    Floor_r3c1_color: object = 0
    Floor_r4c1_pos: object = (4, 1)
    Floor_r4c1_color: object = 0
    Floor_r5c1_pos: object = (5, 1)
    Floor_r5c1_color: object = 0
    Cart_pos: object = (1, 1)
    Cart_color: object = 2
    Landmark_3_pos: object = (6, 6)
    Landmark_3_color: object = 3
    Landmark_4_pos: object = (5, 3)
    Landmark_4_color: object = 4

    def copy(self):
        return replace(self)

    def key(self):
        return (self.Floor_r2c1_pos, self.Floor_r2c1_color, self.Floor_r3c1_pos, self.Floor_r3c1_color, self.Floor_r4c1_pos, self.Floor_r4c1_color, self.Floor_r5c1_pos, self.Floor_r5c1_color, self.Cart_pos, self.Cart_color, self.Landmark_3_pos, self.Landmark_3_color, self.Landmark_4_pos, self.Landmark_4_color,)


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
    if 'Floor_r2c1' not in _exclude:
        r, c = state.Floor_r2c1_pos
        grid[r][c] = state.Floor_r2c1_color
    if 'Floor_r3c1' not in _exclude:
        r, c = state.Floor_r3c1_pos
        grid[r][c] = state.Floor_r3c1_color
    if 'Floor_r4c1' not in _exclude:
        r, c = state.Floor_r4c1_pos
        grid[r][c] = state.Floor_r4c1_color
    if 'Floor_r5c1' not in _exclude:
        r, c = state.Floor_r5c1_pos
        grid[r][c] = state.Floor_r5c1_color
    if 'Cart' not in _exclude:
        r, c = state.Cart_pos
        grid[r][c] = state.Cart_color
    if 'Landmark_3' not in _exclude:
        r, c = state.Landmark_3_pos
        grid[r][c] = state.Landmark_3_color
    if 'Landmark_4' not in _exclude:
        r, c = state.Landmark_4_pos
        grid[r][c] = state.Landmark_4_color
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


def _guard_move_down(state, action):
    """move_down  [ev: t2,t6,t7,t8  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(state.Cart_pos, 'down')) == 0): return False
    return True


def _effect_move_down(state):
    state.Cart_pos = _neighbour(state.Cart_pos, 'down')


RULES = [
    ('move_down', _guard_move_down, _effect_move_down, ['Cart']),
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
    return False


def simulate(initial, actions):
    states = [initial]
    current = initial
    for action in actions:
        current = step(current, action)
        states.append(current)
    return states


def initial_state():
    return State(
        Floor_r2c1_pos=(2, 1),
        Floor_r2c1_color=0,
        Floor_r3c1_pos=(3, 1),
        Floor_r3c1_color=0,
        Floor_r4c1_pos=(4, 1),
        Floor_r4c1_color=0,
        Floor_r5c1_pos=(5, 1),
        Floor_r5c1_color=0,
        Cart_pos=(1, 1),
        Cart_color=2,
        Landmark_3_pos=(6, 6),
        Landmark_3_color=3,
        Landmark_4_pos=(5, 3),
        Landmark_4_color=4,
    )
