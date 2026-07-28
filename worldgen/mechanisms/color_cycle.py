"""Color cycle — a coloured gate whose colour advances when you push against it.

One cycler is one cell with a phase in `range(k)` and an `open_phase`.  Walk into
it while `phase == open_phase` and you walk through and the phase does not move;
walk into it while it is shut and you do not move but the phase advances by one.
So the agent opens a gate by bumping it until its colour comes round, and the
advance is a cyclic group action of order `k`: it destroys no information, since
`k` applications are the identity.

That is what makes the family **reversible**, and the reversibility is the point
rather than a side effect.  A0′ (`cold-start-a0/prime/A0P_REPORT.md` §1) is the
measured version of the argument: its toggle world saw 47 % of the state-action
pairs and shipped a manual that was 228/228 correct, while A0's latch world saw
99 % and shipped three errors, because a latch gives a rule exactly one witness
and no way to obtain a second.  A cycler hands `advance_cycler` a fresh witness
at every shut phase, so a reader can enumerate the phase table as evidence
instead of inferring it by analogy from one sighting.

**One configuration is a latch and a generator should not emit it.**  Passing
through does not advance the phase, so `open_phase` is absorbing: a cycler that
starts exactly one step short of its open phase fires `advance_cycler` once and
never again, which `core/reversibility.py` scores as `max_witnesses == 1` and
reports as disagreeing with the `True` claim below.  `(open_phase - phase0) % k`
is the number of witnesses available, and worlds want it at 2 or more — with
`k = 2` that means starting the cycler already open.

The phases are drawn in different colours — `cycler`, `cycler_1`, `cycler_2`, … —
which is what makes the state visible at all: the phase is the only thing in this
family that a reader can read straight off a frame, and every rule about a cycler
is a rule about that colour.
"""

from typing import Any, Dict, FrozenSet, List, Optional, Tuple

from ..core.spec import Entity, WorldSpec
from ..core.types import Cell, State, shift
from .base import Ctx, Mechanism, Outcome, View, register

_LENGTHS: Tuple[int, ...] = (2, 3, 4)


class ColorCycle(Mechanism):
    name = "color_cycle"
    kinds = ("cycler",)
    priority = 35

    # ----------------------------------------------------------------- state
    def n_vars(self, spec: WorldSpec, mine: Tuple[Entity, ...]) -> int:
        self._params(spec, mine)          # construction-time validation, see below
        return len(mine)

    def initial_vars(self, spec: WorldSpec, mine: Tuple[Entity, ...]) -> Tuple[int, ...]:
        return tuple(phase0 for _k, _open, phase0 in self._params(spec, mine))

    def _params(self, spec: WorldSpec,
                mine: Tuple[Entity, ...]) -> Tuple[Tuple[int, int, int], ...]:
        """`(k, open_phase, phase0)` per cycler in spec order.

        Read out of the spec on every call: one `ColorCycle()` instance serves
        every world in the registry, so it must not remember one of them.  The
        checks live here because `n_vars` runs it at construction, and a cycler
        whose `open_phase` is outside `range(k)` is a gate that never opens —
        a world worth rejecting loudly rather than shipping.
        """
        out: List[Tuple[int, int, int]] = []
        for entity in mine:
            k = int(entity.prop("k", 3))
            if k not in _LENGTHS:
                raise ValueError("cycler at %r has k=%d, expected one of %s"
                                 % (entity.cell, k,
                                    ", ".join(str(n) for n in _LENGTHS)))
            open_phase = int(entity.prop("open_phase", 0))
            if not 0 <= open_phase < k:
                raise ValueError("cycler at %r has open_phase=%d outside range(%d)"
                                 % (entity.cell, open_phase, k))
            phase0 = int(entity.prop("phase0", 0))
            if not 0 <= phase0 < k:
                raise ValueError("cycler at %r has phase0=%d outside range(%d)"
                                 % (entity.cell, phase0, k))
            out.append((k, open_phase, phase0))
        return tuple(out)

    # --------------------------------------------------------------- queries
    def occupied(self, spec: WorldSpec, mine: Tuple[Entity, ...],
                 view: View) -> FrozenSet[Cell]:
        params = self._params(spec, mine)
        return frozenset(entity.cell for i, entity in enumerate(mine)
                         if view.get(i) != params[i][1])

    def reserved(self, spec: WorldSpec, mine: Tuple[Entity, ...],
                 view: View) -> FrozenSet[Cell]:
        # Empty.  A cycler is either shut — and then it is in `occupied`, so
        # nothing can be put there by any route — or open, and walking through an
        # open cycler deliberately leaves the phase alone (see `interact`).  An
        # agent deposited on an open cycler therefore skips no effect and lands in
        # a state indistinguishable from having walked in, which is the whole
        # question this predicate asks.
        return frozenset()

    # ------------------------------------------------------------- behaviour
    def interact(self, ctx: Ctx) -> Optional[Outcome]:
        index = ctx.index_at(ctx.target)
        if index is None:
            return None
        k, open_phase, _phase0 = self._params(ctx.spec, ctx.mine)[index]
        phase = ctx.view.get(index)
        if phase == open_phase:
            # Passing through deliberately leaves the phase alone: if walking
            # through also advanced it, the gate's state would depend on the
            # agent's whole route and no reader could read it off a single frame.
            return Outcome(agent=ctx.target, rule="walk_through_cycler")
        return Outcome(
            agent=None,
            writes=((ctx.view.abs(index), (phase + 1) % k),),
            rule="advance_cycler",
        )

    # --------------------------------------------------------------- drawing
    def render(self, spec: WorldSpec, mine: Tuple[Entity, ...], view: View,
               frame: List[List[int]]) -> None:
        for i, entity in enumerate(mine):
            phase = view.get(i)
            color = spec.color("cycler" if phase == 0 else "cycler_%d" % phase)
            r, c = entity.cell
            frame[r][c] = color

    # -------------------------------------------------------------- the truth
    def truth_rules(self, spec: WorldSpec, mine: Tuple[Entity, ...]) -> List[Dict[str, Any]]:
        if not mine:
            return []
        return [
            {"name": "walk_through_cycler",
             "when": "act=D and the target cell holds a cycler whose phase equals "
                     "its open phase",
             "then": "the agent enters the cell and the phase does not change",
             "reversible": True},
            {"name": "advance_cycler",
             "when": "act=D and the target cell holds a cycler whose phase is not "
                     "its open phase",
             "then": "the agent does not move and the cycler's phase becomes "
                     "(phase + 1) mod k",
             # A0′ §1: the advance has order k and so destroys nothing, and every
             # shut phase supplies its own witness — the phase table becomes
             # enumerated evidence rather than an analogy drawn from one
             # unrepeatable sighting, which is what lets a manual be right.
             "reversible": True,
             # But re-witnessability is a property of the *geometry*, not of the
             # group, and here the difference is measurable rather than
             # hypothetical: this rule measures 2 in `t1-cycler-gate` and 1 in
             # both `t2-cycler-lock` and `t3-cycler-portal-lock`.  Reversible
             # effect, single witness — the combination the library previously
             # could not express, and the one worth having a catalogue for.  The
             # advance only fires from a *shut* phase, so once the cycler is open
             # the agent has to come round through k-1 more advances to get
             # another, and where the geometry does not allow that, it does not.
             "re_witnessable": "conditional — the advance fires only from a shut "
                               "phase, so a second witness needs a route that "
                               "returns the agent to one; measured per world"},
        ]

    def invariants(self, spec: WorldSpec, mine: Tuple[Entity, ...]) -> List[Dict[str, Any]]:
        if not mine:
            return []
        params = self._params(spec, mine)
        cells = tuple(entity.cell for entity in mine)
        lengths = tuple(k for k, _open, _phase0 in params)

        def in_range(world, state, _lengths=lengths) -> bool:
            phases = world.view(self, state).all()
            return all(0 <= phase < k for phase, k in zip(phases, _lengths))

        def color_reads_phase(world, state, _cells=cells) -> bool:
            # The rendered colour is the only channel the phase has to a reader,
            # so if it ever failed to determine the phase the whole family would
            # be unlearnable from frames.  The agent is painted last and wins the
            # overlap, hence the cell it stands on is exempt.
            frame = world.render(state)
            phases = world.view(self, state).all()
            for (r, c), phase in zip(_cells, phases):
                if (r, c) == state.agent:
                    continue
                want = world.spec.color("cycler" if phase == 0
                                        else "cycler_%d" % phase)
                if frame[r][c] != want:
                    return False
            return True

        return [
            {"name": "phase_in_range",
             "statement": "every cycler's phase stays in range(k)",
             "check": in_range},
            {"name": "color_reads_phase",
             "statement": "the colour of a cycler cell determines its phase, "
                          "except where the agent covers it",
             "check": color_reads_phase},
        ]


register(ColorCycle())
