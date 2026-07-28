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
LANDMARKS = {'target': (3, 3)}
BACKGROUND = 0
N_POS = None
GRID = (7, 7)
BOARD = [
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 8, 0],
    [0, 0, 0, 8, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 8, 0, 0],
    [0, 0, 0, 0, 0, 8, 0],
    [0, 0, 0, 0, 0, 0, 0],
]
ACTIONS = [('move', 'Player', 'up'), ('move', 'Player', 'down'), ('move', 'Player', 'left'), ('move', 'Player', 'right')]


@dataclass
class State:
    """One field per instance per observation the word table names."""
    Box_pos: object = (3, 3)
    Player_pos: object = (5, 3)

    def copy(self):
        return replace(self)

    def key(self):
        return (self.Box_pos, self.Player_pos,)


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
    if 'Box' not in _exclude:
        r, c = state.Box_pos
        grid[r][c] = 1
    if 'Player' not in _exclude:
        r, c = state.Player_pos
        grid[r][c] = 1
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


def _guard_walk_up(state, action):
    """walk_up  [ev: t0,t1,t2  cov: 262/262]"""
    if action != ('move', 'Player', 'up'): return False
    if not (_free(state, _neighbour(state.Player_pos, 'up'))): return False
    return True


def _effect_walk_up(state):
    state.Player_pos = _neighbour(state.Player_pos, 'up')


def _guard_walk_down(state, action):
    """walk_down  [ev: t0,t1,t2  cov: 262/262]"""
    if action != ('move', 'Player', 'down'): return False
    if not (_free(state, _neighbour(state.Player_pos, 'down'))): return False
    return True


def _effect_walk_down(state):
    state.Player_pos = _neighbour(state.Player_pos, 'down')


def _guard_walk_left(state, action):
    """walk_left  [ev: t0,t1,t2  cov: 262/262]"""
    if action != ('move', 'Player', 'left'): return False
    if not (_free(state, _neighbour(state.Player_pos, 'left'))): return False
    return True


def _effect_walk_left(state):
    state.Player_pos = _neighbour(state.Player_pos, 'left')


def _guard_walk_right(state, action):
    """walk_right  [ev: t0,t1,t2  cov: 262/262]"""
    if action != ('move', 'Player', 'right'): return False
    if not (_free(state, _neighbour(state.Player_pos, 'right'))): return False
    return True


def _effect_walk_right(state):
    state.Player_pos = _neighbour(state.Player_pos, 'right')


def _guard_push2_up(state, action):
    """push2_up  [ev: t3,t9,t27  cov: None]"""
    if action != ('move', 'Player', 'up'): return False
    if not ((state.Box_pos == _neighbour(state.Player_pos, 'up'))): return False
    if not (_free_except(state, state.Box_pos, ('Box',))): return False
    if not (_free(state, _neighbour(state.Box_pos, 'up'))): return False
    if not (_free(state, _neighbour(_neighbour(state.Box_pos, 'up'), 'up'))): return False
    return True


def _effect_push2_up(state):
    state.Box_pos = _neighbour(_neighbour(state.Box_pos, 'up'), 'up')
    state.Player_pos = _neighbour(state.Player_pos, 'up')


def _guard_push2_down(state, action):
    """push2_down  [ev: t3,t9,t27  cov: None]"""
    if action != ('move', 'Player', 'down'): return False
    if not ((state.Box_pos == _neighbour(state.Player_pos, 'down'))): return False
    if not (_free_except(state, state.Box_pos, ('Box',))): return False
    if not (_free(state, _neighbour(state.Box_pos, 'down'))): return False
    if not (_free(state, _neighbour(_neighbour(state.Box_pos, 'down'), 'down'))): return False
    return True


def _effect_push2_down(state):
    state.Box_pos = _neighbour(_neighbour(state.Box_pos, 'down'), 'down')
    state.Player_pos = _neighbour(state.Player_pos, 'down')


def _guard_push2_left(state, action):
    """push2_left  [ev: t3,t9,t27  cov: None]"""
    if action != ('move', 'Player', 'left'): return False
    if not ((state.Box_pos == _neighbour(state.Player_pos, 'left'))): return False
    if not (_free_except(state, state.Box_pos, ('Box',))): return False
    if not (_free(state, _neighbour(state.Box_pos, 'left'))): return False
    if not (_free(state, _neighbour(_neighbour(state.Box_pos, 'left'), 'left'))): return False
    return True


def _effect_push2_left(state):
    state.Box_pos = _neighbour(_neighbour(state.Box_pos, 'left'), 'left')
    state.Player_pos = _neighbour(state.Player_pos, 'left')


def _guard_push2_right(state, action):
    """push2_right  [ev: t3,t9,t27  cov: None]"""
    if action != ('move', 'Player', 'right'): return False
    if not ((state.Box_pos == _neighbour(state.Player_pos, 'right'))): return False
    if not (_free_except(state, state.Box_pos, ('Box',))): return False
    if not (_free(state, _neighbour(state.Box_pos, 'right'))): return False
    if not (_free(state, _neighbour(_neighbour(state.Box_pos, 'right'), 'right'))): return False
    return True


def _effect_push2_right(state):
    state.Box_pos = _neighbour(_neighbour(state.Box_pos, 'right'), 'right')
    state.Player_pos = _neighbour(state.Player_pos, 'right')


def _guard_blocked_wall_up(state, action):
    """blocked_wall_up  [ev: t5,t11  cov: 16/16]"""
    if action != ('move', 'Player', 'up'): return False
    if (_free(state, _neighbour(state.Player_pos, 'up'))): return False
    if ((state.Box_pos == _neighbour(state.Player_pos, 'up'))): return False
    return True


def _effect_blocked_wall_up(state):
    pass  # writes {} — nothing happens


def _guard_blocked_wall_down(state, action):
    """blocked_wall_down  [ev: t5,t11  cov: 16/16]"""
    if action != ('move', 'Player', 'down'): return False
    if (_free(state, _neighbour(state.Player_pos, 'down'))): return False
    if ((state.Box_pos == _neighbour(state.Player_pos, 'down'))): return False
    return True


def _effect_blocked_wall_down(state):
    pass  # writes {} — nothing happens


def _guard_blocked_wall_left(state, action):
    """blocked_wall_left  [ev: t5,t11  cov: 16/16]"""
    if action != ('move', 'Player', 'left'): return False
    if (_free(state, _neighbour(state.Player_pos, 'left'))): return False
    if ((state.Box_pos == _neighbour(state.Player_pos, 'left'))): return False
    return True


def _effect_blocked_wall_left(state):
    pass  # writes {} — nothing happens


def _guard_blocked_wall_right(state, action):
    """blocked_wall_right  [ev: t5,t11  cov: 16/16]"""
    if action != ('move', 'Player', 'right'): return False
    if (_free(state, _neighbour(state.Player_pos, 'right'))): return False
    if ((state.Box_pos == _neighbour(state.Player_pos, 'right'))): return False
    return True


def _effect_blocked_wall_right(state):
    pass  # writes {} — nothing happens


def _guard_blocked_box_on_wall_up(state, action):
    """blocked_box_on_wall_up  [ev: -  cov: -]"""
    if action != ('move', 'Player', 'up'): return False
    if not ((state.Box_pos == _neighbour(state.Player_pos, 'up'))): return False
    if (_free_except(state, state.Box_pos, ('Box',))): return False
    return True


def _effect_blocked_box_on_wall_up(state):
    pass  # writes {} — nothing happens


def _guard_blocked_box_on_wall_down(state, action):
    """blocked_box_on_wall_down  [ev: -  cov: -]"""
    if action != ('move', 'Player', 'down'): return False
    if not ((state.Box_pos == _neighbour(state.Player_pos, 'down'))): return False
    if (_free_except(state, state.Box_pos, ('Box',))): return False
    return True


def _effect_blocked_box_on_wall_down(state):
    pass  # writes {} — nothing happens


def _guard_blocked_box_on_wall_left(state, action):
    """blocked_box_on_wall_left  [ev: -  cov: -]"""
    if action != ('move', 'Player', 'left'): return False
    if not ((state.Box_pos == _neighbour(state.Player_pos, 'left'))): return False
    if (_free_except(state, state.Box_pos, ('Box',))): return False
    return True


def _effect_blocked_box_on_wall_left(state):
    pass  # writes {} — nothing happens


def _guard_blocked_box_on_wall_right(state, action):
    """blocked_box_on_wall_right  [ev: -  cov: -]"""
    if action != ('move', 'Player', 'right'): return False
    if not ((state.Box_pos == _neighbour(state.Player_pos, 'right'))): return False
    if (_free_except(state, state.Box_pos, ('Box',))): return False
    return True


def _effect_blocked_box_on_wall_right(state):
    pass  # writes {} — nothing happens


def _guard_blocked_box_crossing_up(state, action):
    """blocked_box_crossing_up  [ev: t7,t19  cov: None]"""
    if action != ('move', 'Player', 'up'): return False
    if not ((state.Box_pos == _neighbour(state.Player_pos, 'up'))): return False
    if not (_free_except(state, state.Box_pos, ('Box',))): return False
    if (_free(state, _neighbour(state.Box_pos, 'up'))): return False
    return True


def _effect_blocked_box_crossing_up(state):
    pass  # writes {} — nothing happens


def _guard_blocked_box_crossing_down(state, action):
    """blocked_box_crossing_down  [ev: t7,t19  cov: None]"""
    if action != ('move', 'Player', 'down'): return False
    if not ((state.Box_pos == _neighbour(state.Player_pos, 'down'))): return False
    if not (_free_except(state, state.Box_pos, ('Box',))): return False
    if (_free(state, _neighbour(state.Box_pos, 'down'))): return False
    return True


def _effect_blocked_box_crossing_down(state):
    pass  # writes {} — nothing happens


def _guard_blocked_box_crossing_left(state, action):
    """blocked_box_crossing_left  [ev: t7,t19  cov: None]"""
    if action != ('move', 'Player', 'left'): return False
    if not ((state.Box_pos == _neighbour(state.Player_pos, 'left'))): return False
    if not (_free_except(state, state.Box_pos, ('Box',))): return False
    if (_free(state, _neighbour(state.Box_pos, 'left'))): return False
    return True


def _effect_blocked_box_crossing_left(state):
    pass  # writes {} — nothing happens


def _guard_blocked_box_crossing_right(state, action):
    """blocked_box_crossing_right  [ev: t7,t19  cov: None]"""
    if action != ('move', 'Player', 'right'): return False
    if not ((state.Box_pos == _neighbour(state.Player_pos, 'right'))): return False
    if not (_free_except(state, state.Box_pos, ('Box',))): return False
    if (_free(state, _neighbour(state.Box_pos, 'right'))): return False
    return True


def _effect_blocked_box_crossing_right(state):
    pass  # writes {} — nothing happens


def _guard_blocked_box_landing_up(state, action):
    """blocked_box_landing_up  [ev: t31,t44  cov: None]"""
    if action != ('move', 'Player', 'up'): return False
    if not ((state.Box_pos == _neighbour(state.Player_pos, 'up'))): return False
    if not (_free_except(state, state.Box_pos, ('Box',))): return False
    if not (_free(state, _neighbour(state.Box_pos, 'up'))): return False
    if (_free(state, _neighbour(_neighbour(state.Box_pos, 'up'), 'up'))): return False
    return True


def _effect_blocked_box_landing_up(state):
    pass  # writes {} — nothing happens


def _guard_blocked_box_landing_down(state, action):
    """blocked_box_landing_down  [ev: t31,t44  cov: None]"""
    if action != ('move', 'Player', 'down'): return False
    if not ((state.Box_pos == _neighbour(state.Player_pos, 'down'))): return False
    if not (_free_except(state, state.Box_pos, ('Box',))): return False
    if not (_free(state, _neighbour(state.Box_pos, 'down'))): return False
    if (_free(state, _neighbour(_neighbour(state.Box_pos, 'down'), 'down'))): return False
    return True


def _effect_blocked_box_landing_down(state):
    pass  # writes {} — nothing happens


def _guard_blocked_box_landing_left(state, action):
    """blocked_box_landing_left  [ev: t31,t44  cov: None]"""
    if action != ('move', 'Player', 'left'): return False
    if not ((state.Box_pos == _neighbour(state.Player_pos, 'left'))): return False
    if not (_free_except(state, state.Box_pos, ('Box',))): return False
    if not (_free(state, _neighbour(state.Box_pos, 'left'))): return False
    if (_free(state, _neighbour(_neighbour(state.Box_pos, 'left'), 'left'))): return False
    return True


def _effect_blocked_box_landing_left(state):
    pass  # writes {} — nothing happens


def _guard_blocked_box_landing_right(state, action):
    """blocked_box_landing_right  [ev: t31,t44  cov: None]"""
    if action != ('move', 'Player', 'right'): return False
    if not ((state.Box_pos == _neighbour(state.Player_pos, 'right'))): return False
    if not (_free_except(state, state.Box_pos, ('Box',))): return False
    if not (_free(state, _neighbour(state.Box_pos, 'right'))): return False
    if (_free(state, _neighbour(_neighbour(state.Box_pos, 'right'), 'right'))): return False
    return True


def _effect_blocked_box_landing_right(state):
    pass  # writes {} — nothing happens


RULES = [
    ('walk_up', _guard_walk_up, _effect_walk_up, ['Player']),
    ('walk_down', _guard_walk_down, _effect_walk_down, ['Player']),
    ('walk_left', _guard_walk_left, _effect_walk_left, ['Player']),
    ('walk_right', _guard_walk_right, _effect_walk_right, ['Player']),
    ('push2_up', _guard_push2_up, _effect_push2_up, ['Box', 'Player']),
    ('push2_down', _guard_push2_down, _effect_push2_down, ['Box', 'Player']),
    ('push2_left', _guard_push2_left, _effect_push2_left, ['Box', 'Player']),
    ('push2_right', _guard_push2_right, _effect_push2_right, ['Box', 'Player']),
    ('blocked_wall_up', _guard_blocked_wall_up, _effect_blocked_wall_up, []),
    ('blocked_wall_down', _guard_blocked_wall_down, _effect_blocked_wall_down, []),
    ('blocked_wall_left', _guard_blocked_wall_left, _effect_blocked_wall_left, []),
    ('blocked_wall_right', _guard_blocked_wall_right, _effect_blocked_wall_right, []),
    ('blocked_box_on_wall_up', _guard_blocked_box_on_wall_up, _effect_blocked_box_on_wall_up, []),
    ('blocked_box_on_wall_down', _guard_blocked_box_on_wall_down, _effect_blocked_box_on_wall_down, []),
    ('blocked_box_on_wall_left', _guard_blocked_box_on_wall_left, _effect_blocked_box_on_wall_left, []),
    ('blocked_box_on_wall_right', _guard_blocked_box_on_wall_right, _effect_blocked_box_on_wall_right, []),
    ('blocked_box_crossing_up', _guard_blocked_box_crossing_up, _effect_blocked_box_crossing_up, []),
    ('blocked_box_crossing_down', _guard_blocked_box_crossing_down, _effect_blocked_box_crossing_down, []),
    ('blocked_box_crossing_left', _guard_blocked_box_crossing_left, _effect_blocked_box_crossing_left, []),
    ('blocked_box_crossing_right', _guard_blocked_box_crossing_right, _effect_blocked_box_crossing_right, []),
    ('blocked_box_landing_up', _guard_blocked_box_landing_up, _effect_blocked_box_landing_up, []),
    ('blocked_box_landing_down', _guard_blocked_box_landing_down, _effect_blocked_box_landing_down, []),
    ('blocked_box_landing_left', _guard_blocked_box_landing_left, _effect_blocked_box_landing_left, []),
    ('blocked_box_landing_right', _guard_blocked_box_landing_right, _effect_blocked_box_landing_right, []),
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
    return (state.Box_pos == LANDMARKS['target'])


def simulate(initial, actions):
    states = [initial]
    current = initial
    for action in actions:
        current = step(current, action)
        states.append(current)
    return states


def initial_state():
    return State(
        Box_pos=(3, 3),
        Player_pos=(5, 3),
    )
