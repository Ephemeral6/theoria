"""Gravity — a global modifier: everything falls until something holds it up.

Gravity owns no entity kinds and no state.  It is bound into a world by naming
it in `spec.families` and switched on by `spec.flag("gravity")`, and everything
it moves belongs to somebody else: the agent, and whatever `world.movables`
reports — a push block, in practice, though gravity has never heard of one.
That is what the `movables` channel in `base.py` is for; a family written later
that exposes its entities there falls correctly on the day it is written, with
no edit here.

Semantics, deliberately the plain ones:

* a thing falls when the cell directly below it is free.  `world.is_free` is
  the test, so walls, bounds, the agent and every other mechanism's occupied
  cells all count without gravity knowing what any of them are;
* one `settle` call performs exactly one descent and returns.  `core/world.py`
  runs `settle` to a fixpoint, so looping to convergence here would duplicate
  that and hide a non-terminating world from `SETTLE_LIMIT`;
* the lowest candidate falls first, which is what stops a vertical stack from
  dropping through itself: the thing underneath has already vacated its cell by
  the time the thing above it is considered.

**`UP` is inert, and that is the design.**  Gravity claims no target cell in
`interact`, so an upward move resolves normally — the agent rises, then falls
straight back in the settle that ends the same step.  A climb rule would paper
over this; leaving it alone makes "up does nothing here" a rule a reader can
witness and induce, which is the kind of rule this library exists to produce.

**A fall is one-way.**  Stepping off a ledge cannot be undone from below unless
some other route climbs back, so `fall` is a directed edge in the reachable
graph and a rule that can only be witnessed above a ledge gets exactly one
witness ever.  A0′ (`cold-start-a0/prime/A0P_REPORT.md`) is where that stopped
being hypothetical; `core/reversibility.py` settles it per world by searching
the graph, and the claim below is only the designer's expectation.

One consequence worth stating because it shapes every trace: a fall carries no
`Outcome.rule` tag of its own.  It happens in `settle`, after the rule that
caused it, so the reader sees `walk` or `push` and a state that moved further
than that rule alone would explain.
"""

from typing import Any, Dict, List, Optional, Tuple

from ..core.spec import Entity, WorldSpec
from ..core.types import Cell, State, encode_cell, shift
from .base import Mechanism, register


class Gravity(Mechanism):
    name = "gravity"
    kinds = ()          # a modifier: no entity kind in any spec belongs to it
    priority = 10       # first in dispatch order; it claims nothing, so this only fixes the reading order

    # ----------------------------------------------------------------- state
    def n_vars(self, spec: WorldSpec, mine: Tuple[Entity, ...]) -> int:
        return 0        # where things are already lives in their owners' slices

    def _enabled(self, spec: WorldSpec) -> bool:
        return bool(spec.flag("gravity"))

    # ------------------------------------------------------------- behaviour
    def settle(self, world: Any, state: State) -> Optional[State]:
        if not self._enabled(world.spec):
            return None

        # (row, col, rank, var index); rank 0 is the agent, 1 a movable, and the
        # var index is -1 for the agent, which moves through `State.agent`
        # rather than through the state vector.
        candidates: List[Tuple[int, int, int, int]] = []
        if world.is_free(state, shift(state.agent, "DOWN")):
            candidates.append((state.agent[0], state.agent[1], 0, -1))
        for index, cell in world.movables(state):
            if world.is_free(state, shift(cell, "DOWN")):
                candidates.append((cell[0], cell[1], 1, index))
        if not candidates:
            return None

        # Largest row first, then largest column; the rank only breaks a tie
        # that `spec.validate` already forbids, and is here so that the order is
        # fixed on paper rather than by accident.
        row, col, rank, index = max(candidates, key=lambda t: (t[0], t[1], -t[2]))
        target: Cell = shift((row, col), "DOWN")
        if rank == 0:
            return state.with_agent(target)
        return state.written(((index, encode_cell(target, world.spec.width)),))

    # -------------------------------------------------------------- the truth
    def truth_rules(self, spec: WorldSpec, mine: Tuple[Entity, ...]) -> List[Dict[str, Any]]:
        if not self._enabled(spec):
            return []
        return [
            {"name": "fall",
             "when": "the cell directly below the agent, or below a movable entity, "
                     "is free",
             "then": "that thing descends one cell, and this repeats to a fixpoint — "
                     "a post-step settlement, appended to whatever rule ended the "
                     "step, never tagged as a rule of its own",
             "reversible": False,
             "why": "descending a ledge cannot be undone from below, so a fall is a "
                    "one-way edge in the reachable graph and any rule witnessed only "
                    "above a ledge gets exactly one witness"},
            {"name": "up_is_inert",
             "when": "act=UP",
             "then": "the agent enters the cell above if that cell is free, then falls "
                     "back into the cell it left during the same step's settlement, so "
                     "the state after the step equals the state before it",
             "reversible": True},
        ]

    def invariants(self, spec: WorldSpec, mine: Tuple[Entity, ...]) -> List[Dict[str, Any]]:
        if not self._enabled(spec):
            return []

        def resting(world, state) -> bool:
            cells: List[Cell] = [state.agent]
            cells.extend(cell for _index, cell in world.movables(state))
            return all(not world.is_free(state, shift(cell, "DOWN")) for cell in cells)

        return [
            {"name": "nothing_rests_on_a_free_cell",
             "statement": "the cell below the agent and below every movable is never "
                          "free — every state a reader can observe is a settle "
                          "fixpoint, so there is nowhere left to fall",
             "check": resting},
        ]


register(Gravity())
