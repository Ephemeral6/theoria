"""Regression: gravity may not drop the agent onto a live entity.

This is the *other* failure mode of the landing predicate, and the reason the
library grew a third one rather than swapping between the two it had.  Fixing
the two-way portal (see `test_portal_landing.py`) by reaching for `can_stand`
would have been too lax in exactly the place that costs most: `consumable`
renders ARMED identically to INTACT, and defends that with "the agent is standing
on it and paints over it".  That argument is sound only while `interact` is the
sole route onto a tile.  An agent *dropped* onto an intact tile sits on a tile
that is still INTACT and produces a frame pixel-identical to the ARMED one — a
dead mechanic traded for a frame-does-not-determine-state bug, which is worse.

The same applies to an uncollected token: an agent deposited on one stands there
without collecting it, so the global count disagrees with the grid and the lock
stays shut with a token apparently already taken.

So gravity falls the agent on `can_rest` (which consults `reserved`) and falls
objects on `is_free`.  Both halves are pinned below, including the negative one:
once the token is collected its cell is plain floor and the agent *must* descend
into it — an over-broad predicate that reserved the cell forever would pass the
first assertion and fail this one.
"""

from worldgen.core.types import State
from worldgen.core.world import GridWorld
from worldgen.generate import from_art

TOKEN = GridWorld(from_art("regression-gravity-token", [
    "#######",
    "#A....#",
    "#T....#",
    "#....G#",
    "#######",
], {"A": "agent", "G": "goal", "T": ("token", {})}, gravity=True))

FRAGILE = GridWorld(from_art("regression-gravity-fragile", [
    "#######",
    "#A....#",
    "#F....#",
    "#....G#",
    "#######",
], {"A": "agent", "G": "goal", "F": ("fragile", {})}, gravity=True))


def _slot(grid: GridWorld, family: str) -> int:
    base, _length = grid.slices[family]
    return base


def test_agent_hovers_above_an_uncollected_token():
    start = TOKEN.initial()
    assert start.agent == (1, 1), (
        "gravity dropped the agent onto the uncollected token at (2, 1); it "
        "landed at %r" % (start.agent,))


def test_agent_hovers_above_an_intact_fragile_tile():
    start = FRAGILE.initial()
    assert start.agent == (1, 1), (
        "gravity dropped the agent onto the intact fragile tile at (2, 1); it "
        "landed at %r" % (start.agent,))


def test_agent_does_fall_once_the_token_below_is_collected():
    """The negative half: a collected token's cell is plain floor and must not
    keep hovering the agent."""
    collected = State(agent=(1, 1), vars=(1,))
    assert _slot(TOKEN, "count_lock") == 0        # the single token's slot
    landed = TOKEN.settle(collected)
    assert landed.agent == (3, 1), (
        "with the token collected the agent should fall to the floor at (3, 1); "
        "it came to rest at %r" % (landed.agent,))


def test_no_reachable_state_has_the_agent_on_an_untouched_entity():
    """Both entities start at 0 — uncollected, intact — and the only route onto
    their cell is `interact`, which raises that value in the same step."""
    for grid, family in ((TOKEN, "count_lock"), (FRAGILE, "consumable")):
        base = _slot(grid, family)
        cell = grid.spec.entities[0].cell
        for state in grid.reachable():
            if state.agent != cell:
                continue
            assert state.vars[base] != 0, (
                "%s: the agent stands on %r while it is still untouched"
                % (grid.spec.world_id, cell))
