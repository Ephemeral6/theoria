"""`can_stand` / `is_free` / `can_rest` are three predicates, not two plus an alias.

They were two, and the conflation is what killed two-way portals and what a naive
repair would have turned into a rendering bug.  Stated as a table over one world:

| cell | `can_stand` | `is_free` | `can_rest` |
|---|---|---|---|
| the agent's own cell | yes | **no** | **yes** |
| a portal mouth (in `no_rest`, not in `reserved`) | yes | **no** | **yes** |
| an uncollected token (in `no_rest` *and* `reserved`) | yes | no | **no** |
| plain floor | yes | yes | yes |
| a wall | no | no | no |

The two rows in bold are the whole argument.  `is_free` answers "may an *object*
be placed here" and correctly excludes both the agent's cell and every `no_rest`
cell; the agent has already left the cell it is moving out of, and a portal mouth
is precisely where a two-way pair is meant to deliver it.  `can_rest` therefore
ignores both — and still respects `reserved`, which is what stops a fall or a
teleport from depositing the agent somewhere `interact` would have had an effect.

A world with a portal pair and a token exhibits all five rows at once, so the
distinctions are read off a single state rather than argued.
"""

from worldgen.core.world import GridWorld
from worldgen.generate import from_art

# P (1, 3) and Q (3, 1) are a two-way pair; T (2, 3) is an uncollected token.
GRID = GridWorld(from_art("regression-predicates", [
    "#######",
    "#A.P..#",
    "#..T..#",
    "#Q...G#",
    "#######",
], {"A": "agent", "G": "goal", "T": ("token", {}),
    "P": ("portal", {"mode": "twoway", "pair": "p"}),
    "Q": ("portal", {"mode": "twoway", "pair": "p"})}))

AGENT_CELL = (1, 1)
MOUTH = (1, 3)
TOKEN = (2, 3)
FLOOR = (2, 2)
WALL = (0, 0)


def _row(state, cell):
    return (GRID.can_stand(state, cell), GRID.is_free(state, cell),
            GRID.can_rest(state, cell))


def test_the_three_predicates_disagree_exactly_where_they_should():
    state = GRID.initial()
    assert state.agent == AGENT_CELL

    expected = {
        AGENT_CELL: (True, False, True),   # can_rest ignores `cell == state.agent`
        MOUTH: (True, False, True),        # can_rest ignores `no_rest`
        TOKEN: (True, False, False),       # can_rest respects `reserved`
        FLOOR: (True, True, True),
        WALL: (False, False, False),
    }
    for cell, want in sorted(expected.items()):
        assert _row(state, cell) == want, (
            "%r: (can_stand, is_free, can_rest) = %r, expected %r"
            % (cell, _row(state, cell), want))


def test_membership_is_what_drives_the_difference():
    """Not a restatement of the table: it pins *why* each row differs, so a
    predicate that got the right answer from the wrong set still fails."""
    state = GRID.initial()
    assert MOUTH in GRID.no_rest(state) and MOUTH not in GRID.reserved(state)
    assert TOKEN in GRID.no_rest(state) and TOKEN in GRID.reserved(state)
    assert AGENT_CELL not in GRID.no_rest(state)
    assert AGENT_CELL not in GRID.reserved(state)


def test_can_rest_is_can_stand_minus_reserved():
    """The definition, checked over every cell of every reachable state."""
    for state in GRID.reachable():
        reserved = GRID.reserved(state)
        for r in range(GRID.spec.height):
            for c in range(GRID.spec.width):
                cell = (r, c)
                assert GRID.can_rest(state, cell) == (
                    GRID.can_stand(state, cell) and cell not in reserved), cell
