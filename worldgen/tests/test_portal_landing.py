"""Regression: the portal landing test used the wrong predicate, twice over.

`Portal.interact` asked `world.is_free(state, landing)`.  `is_free` answers "may
an *object* be placed here", and it excludes two things that have no business
governing where the *agent* comes to rest:

* **`no_rest`**, which by the base-class default holds every cell a mechanism
  owns — including both mouths of a pair.  So a `twoway` mouth could never
  deliver the agent to its partner: the mode was dead code in every world that
  contained it, `teleport_twoway` never fired, and `reversibility.json` recorded
  it as `unreachable` next to a clean `reversibility_score: 1.0`;
* **`cell == state.agent`**, correct for an object and wrong for the agent, which
  has already left the cell it is moving out of.  With `paired` mouths two apart
  and the agent between them, the landing *is* the cell being vacated, so that
  clause made the pair silently inert in both directions and returned
  `blocked_portal_exit` instead.

The repair is `world.can_rest`, a third predicate rather than a swap between the
two that already existed — swapping in `can_stand` would have been the other
failure mode (see `test_gravity_landing.py`).

Both worlds here are built inline rather than taken from the catalogue, so the
test states the geometry that exhibits the defect instead of depending on a
catalogue world continuing to contain it.
"""

from worldgen.core import truth
from worldgen.core.world import GridWorld
from worldgen.generate import from_art
from worldgen.tests import support

# Two mouths, nothing else in the way.  The agent reaches P at (1, 3) by walking
# and must be delivered to Q at (3, 1).
TWOWAY = GridWorld(from_art("regression-twoway", [
    "#####",
    "#A.P#",
    "#...#",
    "#Q.G#",
    "#####",
], {"A": "agent", "G": "goal",
    "P": ("portal", {"mode": "twoway", "pair": "p"}),
    "Q": ("portal", {"mode": "twoway", "pair": "p"})}))

# Mouths two apart with the agent between them: entering either mouth lands the
# agent back on (1, 2), the cell it is in the act of leaving.
PAIRED = GridWorld(from_art("regression-paired-vacated", [
    "#######",
    "#PAQ..#",
    "#....G#",
    "#######",
], {"A": "agent", "G": "goal",
    "P": ("portal", {"mode": "paired", "pair": "p"}),
    "Q": ("portal", {"mode": "paired", "pair": "p"})}))


def test_twoway_portals_fire_somewhere_on_the_reachable_graph():
    assert "teleport_twoway" in truth.fired_rules(TWOWAY), (
        "a world with a two-way pair never emits `teleport_twoway`; the landing "
        "test is excluding the partner mouth again")


def test_twoway_delivers_the_agent_to_the_partner_mouth():
    state, rules = support.drive(TWOWAY, ["RIGHT", "RIGHT"])
    assert rules == ["walk", "teleport_twoway"], rules
    assert state.agent == (3, 1), (
        "entering the mouth at (1, 3) left the agent at %r, not on its partner"
        % (state.agent,))


def test_paired_portal_may_land_on_the_cell_the_agent_is_vacating():
    start = PAIRED.initial()
    assert start.agent == (1, 2)
    for action in ("RIGHT", "LEFT"):
        nxt, rule = PAIRED.explain(start, action)
        assert rule == "teleport_paired", (
            "%s into a paired mouth returned %r; the landing cell is the one the "
            "agent is vacating and the test is still treating it as occupied"
            % (action, rule))
        assert nxt.agent == (1, 2)


def test_paired_world_still_frame_determines_state():
    """The repair must not buy the teleport at the cost of the property the whole
    catalogue rests on."""
    for grid in (TWOWAY, PAIRED):
        report = truth.frame_determines_state(grid)
        assert report["injective"], (grid.spec.world_id, report["collisions"])
