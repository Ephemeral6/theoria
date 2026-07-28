"""Regression: a toggle reachable from a door cell used to shut the door on the agent.

`SwitchDoor.interact` flipped the bit unconditionally.  Where the geometry lets
the agent stand on an open door with the driving switch adjacent, that put the
agent *inside* a solid cell, and two separate things then broke at once:

* `door_presence_tracks_net` — the door's own invariant — failed, because the
  renderer paints the agent last and the closed door's colour was erased;
* with the colour erased the frame stopped determining the state, so the world
  became unlearnable from its own trace at exactly the states where the mechanic
  is most informative.

The repair refuses the toggle and names the refusal `blocked_toggle_would_shut_door`,
so the reader witnesses a switch that is visibly right there and visibly does not
flip, rather than an unexplained exception.  `t1-switch-toggle` carries a second
door next to its switch for the same reason — without it the branch is dormant
across the whole catalogue — but the world below states the geometry directly.
"""

from worldgen.core import truth
from worldgen.core.world import GridWorld
from worldgen.generate import from_art
from worldgen.mechanisms.switch_door import SwitchDoor
from worldgen.tests import support

# Switch at (1, 3), the door it drives directly below it at (2, 3).  The agent
# can throw the switch from (1, 2), walk round to the door via (2, 2), and then
# stand on the open door with the switch one step UP.
GRID = GridWorld(from_art("regression-shut-under-agent", [
    "#######",
    "#A.S..#",
    "#..D..#",
    "#....G#",
    "#######",
], {"A": "agent", "G": "goal",
    "S": ("switch", {"mode": "toggle", "net": "a"}),
    "D": ("door", {"net": "a", "polarity": "open_when_on"})}))

ONTO_THE_DOOR = ["RIGHT", "RIGHT", "DOWN", "RIGHT"]


def test_toggling_from_the_door_is_refused_and_named():
    state, rules = support.drive(GRID, ONTO_THE_DOOR)
    assert rules == ["walk", "toggle_switch", "walk", "walk_through_door"], rules
    assert state.agent == (2, 3), state.agent

    after, rule = GRID.explain(state, "UP")
    assert rule == "blocked_toggle_would_shut_door", (
        "pressing the switch from the door it drives returned %r" % rule)
    assert after == state, "the refused toggle changed the state"


def test_the_agent_is_never_inside_a_solid_cell():
    for state in GRID.reachable():
        assert state.agent not in GRID.occupied(state), (
            "reachable state %r has the agent standing in an occupied cell"
            % (state.key(),))


def test_door_presence_tracks_net_holds_everywhere():
    """The invariant the unguarded toggle violated, run over the whole reachable set."""
    mechanism = next(m for m in GRID.mechanisms if isinstance(m, SwitchDoor))
    declared = mechanism.invariants(GRID.spec, GRID.mine(mechanism))
    check = next(inv["check"] for inv in declared
                 if inv["name"] == "door_presence_tracks_net")
    for state in GRID.reachable():
        assert check(GRID, state), (
            "door_presence_tracks_net fails at %r" % (state.key(),))


def test_the_refusal_is_witnessable_in_the_catalogue():
    """`t1-switch-toggle` is built to reach this branch; if it stops, the rule is
    dormant everywhere and the family never witnesses it."""
    assert "blocked_toggle_would_shut_door" in truth.fired_rules(
        support.world("t1-switch-toggle"))
