"""Portal — a mouth that moves the agent somewhere else the instant it steps in.

Three modes, and the reason there are three is that they differ in exactly the
two properties a rule miner has to get right:

* `oneway` — the mouth carries a `dest` cell and puts the agent there.  Nothing
  sends the agent back, so as a *route* it is irreversible; the rule itself is
  still re-witnessable whenever the agent can walk back round to the mouth, and
  `truth_rules` says precisely that rather than flattening it to True or False.
* `twoway` — two mouths share a `pair` label and each lands the agent on the
  other.  Re-witnessable, and the effect does not mention the direction of
  travel.
* `paired` — the same pairing, but the agent keeps its momentum through the
  mouth and lands on `shift(partner, act)`.  This is the only mode whose effect
  depends on `?dir`, and it exists so that a world can pose that question to a
  miner instead of letting every portal rule quantify the direction away.  If
  the cell it would land on is not free the move is refused outright, which is
  the one place a portal can fail.

Portals hold no state (`n_vars` is 0) and occupy nothing: a mouth is enterable
floor, and the agent simply never comes to rest on the mouth it entered.  Both
mouths of a pair are painted the same colour on purpose — the pairing is
something a reader has to infer from behaviour, because on ARC a palette that
gave the answer away would be a property of this generator and not of the task.
"""

from typing import Any, Dict, FrozenSet, List, Optional, Tuple

from ..core.spec import Entity, WorldSpec
from ..core.types import AGENT, Cell, State, shift
from .base import Ctx, Mechanism, Outcome, View, register

_MODES: Tuple[str, ...] = ("oneway", "twoway", "paired")
_RULE: Dict[str, str] = {
    "oneway": "teleport_oneway",
    "twoway": "teleport_twoway",
    "paired": "teleport_paired",
}


class Portal(Mechanism):
    name = "portal"
    kinds = ("portal",)
    priority = 40

    # ----------------------------------------------------------------- state
    def n_vars(self, spec: WorldSpec, mine: Tuple[Entity, ...]) -> int:
        # Nothing to store — but this is the one method GridWorld calls for every
        # mechanism at construction, so it is where a malformed pairing has to be
        # rejected.  A pair that is wrong is silently a different world otherwise.
        self._links(spec, mine)
        return 0

    def _links(self, spec: WorldSpec,
               mine: Tuple[Entity, ...]) -> Tuple[Tuple[str, Cell], ...]:
        """`(mode, anchor)` per entity in spec order, with the pairing resolved.

        The anchor is the destination for `oneway` and the partner's own cell for
        the two paired modes; `interact` turns it into a landing cell.  Rebuilt
        from the spec on every call rather than cached, because one `Portal()`
        instance is shared by every world in the registry and anything it
        remembered between worlds would be a leak across them.
        """
        members: Dict[str, List[int]] = {}
        for index, entity in enumerate(mine):
            mode = entity.prop("mode")
            if mode not in _MODES:
                raise ValueError("portal at %r has mode %r, expected one of %s"
                                 % (entity.cell, mode, ", ".join(_MODES)))
            if mode == "oneway":
                continue
            label = entity.prop("pair")
            if label is None:
                raise ValueError("%s portal at %r carries no pair label"
                                 % (mode, entity.cell))
            members.setdefault(str(label), []).append(index)

        for label in sorted(members):        # sorted, so the complaint a broken
            group = members[label]           # spec draws never depends on dict order
            if len(group) != 2:
                raise ValueError(
                    "portal pair %r has %d mouth(s) (%s), expected exactly 2"
                    % (label, len(group),
                       ", ".join(repr(mine[i].cell) for i in group)))
            first, second = mine[group[0]], mine[group[1]]
            if first.prop("mode") != second.prop("mode"):
                raise ValueError("portal pair %r mixes modes %r and %r"
                                 % (label, first.prop("mode"), second.prop("mode")))

        partner: Dict[int, Cell] = {}
        for label in sorted(members):
            left, right = members[label]
            partner[left] = mine[right].cell
            partner[right] = mine[left].cell

        out: List[Tuple[str, Cell]] = []
        for index, entity in enumerate(mine):
            mode = entity.prop("mode")
            if mode == "oneway":
                dest = entity.prop("dest")
                if dest is None:
                    raise ValueError("one-way portal at %r carries no dest"
                                     % (entity.cell,))
                anchor = (int(dest[0]), int(dest[1]))
                if not spec.in_bounds(anchor) or spec.is_wall(anchor):
                    raise ValueError("one-way portal at %r sends the agent to %r, "
                                     "which is not a floor cell"
                                     % (entity.cell, anchor))
            else:
                anchor = partner[index]
            out.append((mode, anchor))
        return tuple(out)

    # --------------------------------------------------------------- queries
    def occupied(self, spec: WorldSpec, mine: Tuple[Entity, ...],
                 view: View) -> FrozenSet[Cell]:
        # Stated rather than inherited: a mouth being *enterable* is the whole
        # mechanism, and a reader checking why push can shove a block onto one
        # should find the answer here instead of in the base class.
        return frozenset()

    def reserved(self, spec: WorldSpec, mine: Tuple[Entity, ...],
                 view: View) -> FrozenSet[Cell]:
        # Empty, and this is the whole of the two-way mode.  A portal holds no
        # state, so an agent that appears on a mouth without having walked into
        # it skips nothing — and for `twoway` and `paired` the partner mouth is
        # precisely where the agent is supposed to land.  The inherited default
        # (every owned cell) is what made `teleport_twoway` unreachable in every
        # world that contained it.
        return frozenset()

    # ------------------------------------------------------------- behaviour
    def interact(self, ctx: Ctx) -> Optional[Outcome]:
        index = ctx.index_at(ctx.target)
        if index is None:
            return None
        mode, anchor = self._links(ctx.spec, ctx.mine)[index]
        # `paired` is the only mode that reads the action, which is exactly what
        # it is for: a miner watching this world cannot drop `?dir` from the
        # effect, where for the other two modes it can.
        landing = shift(anchor, ctx.action) if mode == "paired" else anchor
        # `can_rest`, not `is_free`: the agent is being placed, not an object.
        # `is_free` excludes `no_rest` (which holds both mouths) and the agent's
        # own cell (which it has already left), and each of those on its own was
        # enough to make a mode of this mechanism dead code.
        if not ctx.world.can_rest(ctx.state, landing):
            return Outcome(agent=None, rule="blocked_portal_exit")
        return Outcome(agent=landing, rule=_RULE[mode])

    # --------------------------------------------------------------- drawing
    def render(self, spec: WorldSpec, mine: Tuple[Entity, ...], view: View,
               frame: List[List[int]]) -> None:
        color = spec.color("portal")
        for entity in mine:
            r, c = entity.cell
            frame[r][c] = color

    # -------------------------------------------------------------- the truth
    def truth_rules(self, spec: WorldSpec, mine: Tuple[Entity, ...]) -> List[Dict[str, Any]]:
        if not mine:
            return []
        modes = tuple(mode for mode, _ in self._links(spec, mine))
        rules: List[Dict[str, Any]] = []
        if "oneway" in modes:
            rules.append(
                {"name": "teleport_oneway",
                 "when": "act=D and the target cell holds a one-way portal whose "
                         "dest cell is free",
                 "then": "the agent is placed on the dest cell; nothing else changes",
                 "reversible": "conditional — the rule is re-witnessable iff the "
                               "agent can walk back to the mouth"})
        if "twoway" in modes:
            rules.append(
                {"name": "teleport_twoway",
                 "when": "act=D and the target cell holds one mouth of a two-way "
                         "pair and the other mouth is free",
                 "then": "the agent is placed on the other mouth, independently of D",
                 "reversible": True})
        if "paired" in modes:
            rules.append(
                {"name": "teleport_paired",
                 "when": "act=D and the target cell holds one mouth of a linked "
                         "pair and the cell one step in direction D beyond the "
                         "other mouth is free",
                 "then": "the agent is placed on that cell — the agent keeps "
                         "travelling in direction D through the pair",
                 "reversible": True})
        rules.append(
            {"name": "blocked_portal_exit",
             "clause": True,
             "when": "act=D and the target cell holds a portal whose landing cell "
                     "is a wall, out of bounds, or occupied",
             "then": "nothing changes",
             "reversible": True})
        return rules

    def invariants(self, spec: WorldSpec, mine: Tuple[Entity, ...]) -> List[Dict[str, Any]]:
        if not mine:
            return []
        color = spec.color("portal")
        cells = tuple(entity.cell for entity in mine)

        def one_agent(world, state) -> bool:
            frame = world.render(state)
            return sum(row.count(AGENT) for row in frame) == 1

        def mouths_static(world, state, _cells=cells, _color=color) -> bool:
            # The agent is painted last and wins the overlap, so a mouth it is
            # standing on shows AGENT; every other mouth must still show its
            # colour, since a portal never moves and never disappears.
            frame = world.render(state)
            return all(frame[r][c] == (AGENT if (r, c) == state.agent else _color)
                       for r, c in _cells)

        return [
            {"name": "agent_conserved",
             "statement": "exactly one cell shows the agent at all times — a "
                          "portal moves the agent, it never copies or deletes it",
             "check": one_agent},
            {"name": "mouths_static",
             "statement": "each of the %d portal mouth(s) shows colour %d unless "
                          "the agent is standing on it" % (len(cells), color),
             "check": mouths_static},
        ]


register(Portal())
