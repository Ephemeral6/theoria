"""Consumable — a one-shot passage that collapses behind the agent.

A `fragile` tile can be crossed exactly once.  The agent walks onto it as if it
were floor; when the agent walks off, the tile turns to solid ground and the
route is gone.  Three states per tile — 0 intact, 1 armed, 2 collapsed — and the
middle one is the whole design:

* the agent moves into an intact tile — the agent takes the cell and the tile
  arms (`cross_fragile`).  The tile does **not** collapse on this step;
* settlement, on some later step, finds an armed tile that the agent is no
  longer standing on and collapses it.  There is no rule name for that, because
  no action caused it;
* the agent moves into a collapsed tile — it is in `occupied`, so this normally
  never reaches `interact` at all; if it ever does, nothing happens
  (`blocked_by_collapsed`).

**The one-step delay is the interesting inductive fact about this family.**  A
reader of the trace sees the agent enter a coloured tile and the colour survive
the frame; the change to `collapsed` lands in the frame where the agent departs,
never in the frame where it arrives.  Effect and cause are one frame apart, so a
miner that only pairs a write with the action taken in the same frame will
attribute the collapse to whatever the agent did next — a wrong rule that fits
every observation.  Getting it right requires noticing that the tile under the
agent is already committed.

**Irreversible by construction, like `count_lock` and unlike a toggle.**  Tile
state only ever rises, so `cross_fragile` has exactly one witness per tile in the
whole reachable graph.  A0′ (`cold-start-a0/prime/A0P_REPORT.md` §1) is the
measurement of what that costs: its latched Button gave `press_left` one witness
and no second, capping what any exploration could establish, against a toggle
that reached a perfect manual on 47 % coverage.
"""

from typing import Any, Dict, FrozenSet, List, Optional, Tuple

from ..core.spec import Entity, WorldSpec
from ..core.types import Cell, State
from .base import Ctx, Mechanism, Outcome, View, register

# Named because the three-way split is read in five places and `2` is not a fact
# a reader should have to carry.
INTACT, ARMED, COLLAPSED = 0, 1, 2


class Consumable(Mechanism):
    name = "consumable"
    kinds = ("fragile",)
    priority = 60

    # ----------------------------------------------------------------- state
    def n_vars(self, spec: WorldSpec, mine: Tuple[Entity, ...]) -> int:
        return len(mine)

    def initial_vars(self, spec: WorldSpec, mine: Tuple[Entity, ...]) -> Tuple[int, ...]:
        return (INTACT,) * len(mine)

    def _cells_in(self, mine: Tuple[Entity, ...], view: View,
                  value: int) -> Tuple[Cell, ...]:
        return tuple(e.cell for i, e in enumerate(mine) if view.get(i) == value)

    # --------------------------------------------------------------- queries
    def occupied(self, spec: WorldSpec, mine: Tuple[Entity, ...],
                 view: View) -> FrozenSet[Cell]:
        return frozenset(self._cells_in(mine, view, COLLAPSED))

    def reserved(self, spec: WorldSpec, mine: Tuple[Entity, ...],
                 view: View) -> FrozenSet[Cell]:
        """Every tile still INTACT.  This is what makes `render` below honest.

        ARMED draws as INTACT, and the justification for that — see `render` — is
        that the agent is standing on an armed tile and paints over it, so the
        two never render identically in a reachable state.  That argument holds
        only while `interact` is the *sole* route onto a tile: an agent dropped
        here by gravity, or delivered by a portal, would sit on a tile that is
        still INTACT and produce a frame pixel-identical to the ARMED one.  So
        the tile is reserved while it is INTACT, and the argument stays true by
        construction rather than by luck.

        COLLAPSED tiles are absent: they are in `occupied`, which already stops
        everything.  ARMED tiles are absent because an armed tile is by
        definition the one the agent is already standing on.
        """
        return frozenset(self._cells_in(mine, view, INTACT))

    # ------------------------------------------------------------- behaviour
    def interact(self, ctx: Ctx) -> Optional[Outcome]:
        index = ctx.index_at(ctx.target)
        if index is None:
            return None
        if ctx.view.get(index) == INTACT:
            return Outcome(
                agent=ctx.target,
                writes=((ctx.view.abs(index), ARMED),),
                rule="cross_fragile",
            )
        # COLLAPSED lands here for real: `occupied` governs where things may be
        # *placed*, and the agent's own move is decided by this method alone.
        # ARMED cannot — an armed tile is by definition the one under the agent's
        # feet and `target` is always a neighbour — but the answer would be the
        # same, so the branch is left total rather than assertive.
        return Outcome(agent=None, rule="blocked_by_collapsed")

    def settle(self, world: Any, state: State) -> Optional[State]:
        mine = world.mine(self)
        view = world.view(self, state)
        writes: List[Tuple[int, int]] = []
        for index, entity in enumerate(mine):
            if view.get(index) == ARMED and entity.cell != state.agent:
                writes.append((view.abs(index), COLLAPSED))
        if not writes:
            return None
        # One pass and out: `core/world.py` re-runs settle to a fixpoint, and a
        # loop here would only race it.
        return state.written(tuple(writes))

    # --------------------------------------------------------------- drawing
    def render(self, spec: WorldSpec, mine: Tuple[Entity, ...], view: View,
               frame: List[List[int]]) -> None:
        if not mine:
            return
        intact = spec.color("fragile")
        collapsed = spec.color("collapsed")
        for index, entity in enumerate(mine):
            r, c = entity.cell
            value = view.get(index)
            if value == COLLAPSED:
                frame[r][c] = collapsed
            else:
                # ARMED draws as intact.  The agent is painted last and stands on
                # it, so the choice is invisible; drawing it as collapsed early
                # would be, and would leak the pending event a frame ahead.
                frame[r][c] = intact

    # -------------------------------------------------------------- the truth
    def truth_rules(self, spec: WorldSpec, mine: Tuple[Entity, ...]) -> List[Dict[str, Any]]:
        if not mine:
            return []
        return [
            {"name": "cross_fragile",
             "when": "act=D and the target cell holds an intact fragile tile",
             "then": "the agent moves onto the tile and the tile arms.  The tile "
                     "does not collapse on this step: the collapse happens later, "
                     "in settlement, on the first step at which the agent is no "
                     "longer standing there — so in the trace the tile changes to "
                     "the collapsed colour one frame after the crossing, not in "
                     "the frame of the crossing itself",
             # As for `collect_token` in `count_lock`: the effect is one-way, the
             # rule is re-witnessable once there is more than one tile.  Each tile
             # is a fresh witness of the same rule, and A0′'s criterion is about
             # how many witnesses a trajectory can obtain, not about undo.
             "reversible": False,
             "re_witnessable": len(mine) >= 2,
             "why": "one witness per tile, so the count is the number of tiles — "
                    "%d here" % len(mine)},
            {"name": "blocked_by_collapsed",
             "clause": True,
             "when": "act=D and the target cell holds a collapsed fragile tile",
             "then": "nothing changes",
             "reversible": True},
        ]

    def invariants(self, spec: WorldSpec, mine: Tuple[Entity, ...]) -> List[Dict[str, Any]]:
        if not mine:
            return []

        def one_armed(world, state) -> bool:
            view = world.view(self, state)
            return sum(1 for v in view.all() if v == ARMED) <= 1

        def armed_under_agent(world, state) -> bool:
            view = world.view(self, state)
            return all(entity.cell == state.agent
                       for i, entity in enumerate(world.mine(self))
                       if view.get(i) == ARMED)

        return [
            {"name": "single_armed_tile",
             "statement": "at most one fragile tile is armed at any instant",
             "check": one_armed},
            {"name": "armed_tile_under_agent",
             "statement": "an armed fragile tile's cell is the agent's cell",
             "check": armed_under_agent},
            {"name": "tile_state_is_monotone",
             "statement": "a fragile tile's state only ever rises, 0 -> 1 -> 2, so a "
                          "collapsed tile is never crossed again",
             # Prose.  It relates two states and `check` sees one; the graph-side
             # form of the same claim is `cross_fragile` having one witness per tile.
             "check": None},
        ]

    def reversibility(self, spec: WorldSpec, mine: Tuple[Entity, ...]) -> List[Dict[str, Any]]:
        if not mine:
            return []
        return [
            {"note": "%d one-way frontiers, one per tile: the reachable graph is a "
                     "DAG in the vector of tile states and an explorer that crosses "
                     "a tile can never sample the other side of that crossing again"
                     % len(mine)},
            {"note": "the collapse is not attributable to an action — it is emitted "
                     "by settle, so no transition carries a rule name for it, and it "
                     "is visible only as the state difference one frame on"},
        ]


register(Consumable())
