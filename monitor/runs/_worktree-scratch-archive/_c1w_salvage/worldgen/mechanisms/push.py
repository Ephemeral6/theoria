"""Push — a Sokoban block the agent can shove one cell at a time.

This is the reference implementation of the `Mechanism` contract; the other six
families follow its shape.  It exercises every part of the protocol: it holds
state (one encoded cell per block), it makes cells impassable, it exposes its
blocks as `movables` so that *other* mechanisms — gravity, in practice — can
relocate them without knowing what a block is, it claims the target cell in
`interact`, and it names the two rules it can fire.

Semantics, deliberately the plain Sokoban ones:

* the agent moves into a block, and the cell beyond it in the same direction is
  free — the block slides one cell and the agent takes its place (`push`);
* the cell beyond is not free — nothing happens at all (`blocked_by_block`).

**Reversibility is conditional and the module says so rather than guessing.**  A
block in open floor can be walked around and pushed back, so `push` is
re-witnessable; the same block in a one-wide corridor can only ever be pushed
away from the agent, and no amount of exploration will produce a second witness
of pushing it back.  A0′ (`cold-start-a0/prime/A0P_REPORT.md`) is the reason
this matters, and `core/reversibility.py` settles it per world by searching the
reachable graph — the claim here is only the designer's expectation, and the
factory check compares the two.
"""

from typing import Any, Dict, FrozenSet, List, Optional, Tuple

from ..core.spec import Entity, WorldSpec
from ..core.types import Cell, State, decode_cell, encode_cell, shift
from .base import Ctx, Mechanism, Outcome, View, register


class Push(Mechanism):
    name = "push"
    kinds = ("block",)
    priority = 20

    # ----------------------------------------------------------------- state
    def n_vars(self, spec: WorldSpec, mine: Tuple[Entity, ...]) -> int:
        return len(mine)

    def initial_vars(self, spec: WorldSpec, mine: Tuple[Entity, ...]) -> Tuple[int, ...]:
        return tuple(encode_cell(e.cell, spec.width) for e in mine)

    def _cells(self, spec: WorldSpec, mine: Tuple[Entity, ...], view: View) -> Tuple[Cell, ...]:
        return tuple(decode_cell(view.get(i), spec.width) for i in range(len(mine)))

    # --------------------------------------------------------------- queries
    def occupied(self, spec: WorldSpec, mine: Tuple[Entity, ...],
                 view: View) -> FrozenSet[Cell]:
        return frozenset(self._cells(spec, mine, view))

    def movables(self, spec: WorldSpec, mine: Tuple[Entity, ...],
                 view: View) -> Tuple[Tuple[int, Cell], ...]:
        return tuple((view.abs(i), cell)
                     for i, cell in enumerate(self._cells(spec, mine, view)))

    def no_rest(self, spec: WorldSpec, mine: Tuple[Entity, ...],
                view: View) -> FrozenSet[Cell]:
        # The base default would return each block's *starting* cell, which goes
        # stale the moment one is shoved.  A block's live cell is already in
        # `occupied`, so there is nothing left to add.
        return frozenset()

    # ------------------------------------------------------------- behaviour
    def interact(self, ctx: Ctx) -> Optional[Outcome]:
        cells = self._cells(ctx.spec, ctx.mine, ctx.view)
        if ctx.target not in cells:
            return None
        index = cells.index(ctx.target)
        beyond = shift(ctx.target, ctx.action)
        if not ctx.world.is_free(ctx.state, beyond):
            return Outcome(agent=None, rule="blocked_by_block")
        return Outcome(
            agent=ctx.target,
            writes=((ctx.view.abs(index), encode_cell(beyond, ctx.spec.width)),),
            rule="push",
        )

    # --------------------------------------------------------------- drawing
    def render(self, spec: WorldSpec, mine: Tuple[Entity, ...], view: View,
               frame: List[List[int]]) -> None:
        color = spec.color("block")
        for r, c in self._cells(spec, mine, view):
            frame[r][c] = color

    # -------------------------------------------------------------- the truth
    def truth_rules(self, spec: WorldSpec, mine: Tuple[Entity, ...]) -> List[Dict[str, Any]]:
        if not mine:
            return []
        return [
            {"name": "push",
             "when": "act=D and the target cell holds a block and the cell beyond "
                     "it in direction D is free",
             "then": "the block moves one cell in direction D and the agent takes "
                     "the block's old cell",
             "reversible": "conditional — only where the agent can reach the far "
                           "side of the block"},
            {"name": "blocked_by_block",
             "when": "act=D and the target cell holds a block and the cell beyond "
                     "it is not free",
             "then": "nothing changes",
             "reversible": True},
        ]

    def invariants(self, spec: WorldSpec, mine: Tuple[Entity, ...]) -> List[Dict[str, Any]]:
        if not mine:
            return []
        count = len(mine)
        color = spec.color("block")

        def check(world, state, _count=count, _color=color) -> bool:
            frame = world.render(state)
            return sum(row.count(_color) for row in frame) == _count

        return [
            {"name": "block_count",
             "statement": "exactly %d cell(s) show colour %d at all times" % (count, color),
             "check": check},
            {"name": "blocks_disjoint",
             "statement": "no two blocks ever occupy the same cell",
             "check": lambda world, state, _n=count: len({
                 decode_cell(v, world.spec.width)
                 for v in world.view(self, state).all()
             }) == _n},
        ]


register(Push())
