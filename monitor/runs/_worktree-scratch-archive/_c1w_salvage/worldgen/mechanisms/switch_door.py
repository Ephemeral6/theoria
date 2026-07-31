"""Switch and door — a bit the agent can set, and a wall that mirrors it.

This is the generalisation of `cold-start-a0/prime/world/a0p_world.py`'s central
mechanic: a switch the agent pushes into, and a door elsewhere in the grid that
is present or absent according to the switch.  Two things are generalised out of
that world.  A switch has a **mode** — `toggle` flips its bit both ways,
`latch` sets it to 1 and never releases it — and both switch and door carry a
**net** label, so one door can answer to several switches and one switch can
drive several doors.

**Both modes exist because A0′ measured the difference between them.**
`A0P_REPORT.md` §1: A0's Button was a latch, so `press` had exactly one witness
ever and the direction generalisation over it could never be enumerated
evidence; A0′'s toggle gave every direction its own witness, and half the
state-action coverage produced a *better* manual.  Reversibility beats coverage.
A latch here is therefore not an oversight to be fixed but the control condition
— the thing a generated world uses when it wants a mechanism that exploration
provably cannot pin down.

* push into a `toggle` switch, from any of the four directions → its bit flips
  (`toggle_switch`).  The agent does not move: a switch is furniture, not floor;
* push into a `latch` switch → its bit becomes 1 (`press_latch`), or, if it is
  already 1, nothing at all happens (`latch_already_set`);
* push into a door its net makes passable → the agent walks in
  (`walk_through_door`); otherwise nothing happens (`blocked_by_door`).

**A net with several switches is on iff *any* of them is on** — an OR network.
That is a design choice and not the only one (AND, parity and majority are all
defensible); it is stated in `truth_rules` so a reader of the ground truth is
told which one this world uses rather than left to induce it from the extension.

A door holds no state.  It is a function of its net, which is what makes its
disappearance an observable event rather than a state variable: an open door is
not drawn at all and the cell renders as floor, exactly as in `a0p_world.py`.
A0′ §2 is the reason that matters — `mdl_segmenter` matches frame *t* against
*t+1* only, so a door that closes and reopens comes back as a fresh track every
time, and re-identifying it is work the reader has to do.
"""

from typing import Any, Dict, FrozenSet, List, Optional, Tuple

from ..core.spec import Entity, WorldSpec
from ..core.types import Cell, State
from .base import Ctx, Mechanism, Outcome, View, register


class SwitchDoor(Mechanism):
    name = "switch_door"
    kinds = ("switch", "door")
    priority = 30

    # ----------------------------------------------------------------- state
    def _switches(self, mine: Tuple[Entity, ...]) -> Tuple[Tuple[int, Entity], ...]:
        """`(local var index, entity)` per switch, spec order.

        The slice is indexed by *switch*, not by entity: doors share this
        mechanism's entity list but hold no state, so the two indexings differ
        as soon as a spec interleaves them.
        """
        out: List[Tuple[int, Entity]] = []
        for entity in mine:
            if entity.kind == "switch":
                out.append((len(out), entity))
        return tuple(out)

    def _doors(self, mine: Tuple[Entity, ...]) -> Tuple[Entity, ...]:
        return tuple(e for e in mine if e.kind == "door")

    def n_vars(self, spec: WorldSpec, mine: Tuple[Entity, ...]) -> int:
        return len(self._switches(mine))

    def initial_vars(self, spec: WorldSpec, mine: Tuple[Entity, ...]) -> Tuple[int, ...]:
        return (0,) * len(self._switches(mine))

    # --------------------------------------------------------------- networks
    def _net_on(self, mine: Tuple[Entity, ...], view: View, net: str) -> bool:
        """The OR network: on iff at least one switch on `net` shows 1.

        A net with no switches at all is off, which is what gives a spec the
        unsolvable variant for free — A0′'s `a0p-no-switch`, where the door
        still mirrors a switch that is not there.
        """
        for index, entity in self._switches(mine):
            if entity.prop("net", "a") == net and view.get(index):
                return True
        return False

    def _is_open(self, door: Entity, mine: Tuple[Entity, ...], view: View) -> bool:
        on = self._net_on(mine, view, door.prop("net", "a"))
        if door.prop("polarity", "open_when_on") == "open_when_off":
            return not on
        return on

    # --------------------------------------------------------------- queries
    def occupied(self, spec: WorldSpec, mine: Tuple[Entity, ...],
                 view: View) -> FrozenSet[Cell]:
        return frozenset(d.cell for d in self._doors(mine)
                         if not self._is_open(d, mine, view))

    # ------------------------------------------------------------- behaviour
    def interact(self, ctx: Ctx) -> Optional[Outcome]:
        for index, entity in self._switches(ctx.mine):
            if entity.cell != ctx.target:
                continue
            bit = ctx.view.get(index)
            if entity.prop("mode", "toggle") == "latch":
                if bit:
                    return Outcome(agent=None, rule="latch_already_set")
                return Outcome(agent=None,
                               writes=((ctx.view.abs(index), 1),),
                               rule="press_latch")
            return Outcome(agent=None,
                           writes=((ctx.view.abs(index), 1 - bit),),
                           rule="toggle_switch")

        for door in self._doors(ctx.mine):
            if door.cell != ctx.target:
                continue
            if self._is_open(door, ctx.mine, ctx.view):
                return Outcome(agent=ctx.target, rule="walk_through_door")
            return Outcome(agent=None, rule="blocked_by_door")

        return None

    # --------------------------------------------------------------- drawing
    def render(self, spec: WorldSpec, mine: Tuple[Entity, ...], view: View,
               frame: List[List[int]]) -> None:
        switches = self._switches(mine)
        if switches:
            # Two palette entries for one entity kind: the bit has to be legible
            # off the frame alone, since nothing else in the render carries it.
            off, on = spec.color("switch"), spec.color("switch_on")
            for index, entity in switches:
                r, c = entity.cell
                frame[r][c] = on if view.get(index) else off

        doors = self._doors(mine)
        if doors:
            closed = spec.color("door")
            for door in doors:
                if self._is_open(door, mine, view):
                    continue          # an open door is absent, not a marked floor
                r, c = door.cell
                frame[r][c] = closed

    # -------------------------------------------------------------- the truth
    def truth_rules(self, spec: WorldSpec, mine: Tuple[Entity, ...]) -> List[Dict[str, Any]]:
        switches = self._switches(mine)
        doors = self._doors(mine)
        if not switches and not doors:
            return []
        modes = tuple(e.prop("mode", "toggle") for _, e in switches)
        rules: List[Dict[str, Any]] = []

        if "toggle" in modes:
            rules.append(
                {"name": "toggle_switch",
                 "when": "act=D and the target cell holds a switch in toggle mode",
                 "then": "that switch's bit flips 0↔1 and the agent stays where it is",
                 "reversible": True})
        if "latch" in modes:
            rules.append(
                {"name": "press_latch",
                 "when": "act=D and the target cell holds a switch in latch mode "
                         "whose bit is 0",
                 "then": "that switch's bit becomes 1, permanently, and the agent "
                         "stays where it is",
                 # A0′ §1: a latch fires exactly once in the life of a world, so a
                 # generalisation over it has one witness and can never be
                 # enumerated evidence — no amount of exploration buys a second.
                 "reversible": False})
            rules.append(
                {"name": "latch_already_set",
                 "when": "act=D and the target cell holds a switch in latch mode "
                         "whose bit is already 1",
                 "then": "nothing changes",
                 "reversible": True})
        if doors:
            rules.extend([
                {"name": "walk_through_door",
                 "when": "act=D and the target cell holds a door whose net's "
                         "aggregate bit matches its polarity",
                 "then": "the agent enters the door's cell",
                 "reversible": True},
                {"name": "blocked_by_door",
                 "when": "act=D and the target cell holds a door whose net's "
                         "aggregate bit does not match its polarity",
                 "then": "nothing changes",
                 "reversible": True},
                # Not an `Outcome.rule` — no transition carries this tag, because
                # the dependency is what makes the door a function rather than an
                # actor.  It is stated here anyway: it is the law a reader has to
                # induce (A0′'s `zero_space` found it as a global law), and the
                # ground truth would be incomplete without it.
                {"name": "door_mirrors_net",
                 "when": "at every instant, for a door on net N with polarity P",
                 "then": "N is on iff any switch on N shows 1 (an OR network); the "
                         "door is passable and undrawn iff N's aggregate bit "
                         "matches P, and impassable and drawn otherwise",
                 "reversible": True},
            ])
        return rules

    def invariants(self, spec: WorldSpec, mine: Tuple[Entity, ...]) -> List[Dict[str, Any]]:
        switches = self._switches(mine)
        doors = self._doors(mine)
        if not switches and not doors:
            return []
        out: List[Dict[str, Any]] = []

        if doors:
            color = spec.color("door")

            def drawn_iff_closed(world, state, _color=color) -> bool:
                frame = world.render(state)
                view = world.view(self, state)
                for door in self._doors(world.mine(self)):
                    r, c = door.cell
                    if self._is_open(door, world.mine(self), view):
                        if frame[r][c] == _color:
                            return False
                    elif frame[r][c] != _color:
                        return False
                return True

            out.append(
                {"name": "door_presence_tracks_net",
                 "statement": "a door shows colour %d exactly when its net's "
                              "aggregate bit does not match its polarity, and shows "
                              "nothing of its own otherwise" % color,
                 "check": drawn_iff_closed})

        if any(e.prop("mode", "toggle") == "latch" for _, e in switches):
            out.append(
                {"name": "latch_monotone",
                 "statement": "every latch switch's bit is monotone non-decreasing "
                              "along every trajectory, and so is the aggregate bit "
                              "of a net whose switches are all latches: once 1, "
                              "never 0 again",
                 # Monotonicity is a property of a transition, not of a state, so
                 # there is nothing honest to put here — a single-state predicate
                 # cannot distinguish a bit that rose from one that was always 1.
                 # `core/reversibility.py` settles it on the reachable graph.
                 "check": None})

        return out


register(SwitchDoor())
