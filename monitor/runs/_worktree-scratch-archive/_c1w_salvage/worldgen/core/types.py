"""Ground vocabulary shared by every world and every mechanism.

Two decisions here are load-bearing and everything else follows from them.

**State is `(agent, vars)` and nothing else.** `vars` is a flat tuple of
non-negative integers; the world hands each mechanism a disjoint slice of it at
construction time and the mechanism never sees the rest. That is what lets a
mechanism be written, tested and reviewed in isolation while still composing
with six others in the same grid: there is no per-mechanism state class to
merge, no dictionary whose key set drifts, and the whole state is hashable,
orderable and JSON-serialisable for free. A position stored in `vars` is encoded
as `r * width + c` (`encode_cell`).

**Colours are assigned per world, not per mechanism.** ARC's palette is ten
colours and this library has seven mechanism families, so a fixed global
assignment is not available. Each world draws colours for the entity kinds it
actually contains out of `POOL`, records the mapping in its ground truth, and a
downstream reader must therefore learn the mapping from the trace rather than
memorise it across worlds. That is the honest situation on ARC and it is
cheaper to build in now than to retrofit.
"""

from dataclasses import dataclass
from typing import Dict, Tuple

Cell = Tuple[int, int]

ACTIONS: Tuple[str, ...] = ("UP", "DOWN", "LEFT", "RIGHT")
DELTA: Dict[str, Cell] = {
    "UP": (-1, 0),
    "DOWN": (1, 0),
    "LEFT": (0, -1),
    "RIGHT": (0, 1),
}
OPPOSITE: Dict[str, str] = {"UP": "DOWN", "DOWN": "UP",
                            "LEFT": "RIGHT", "RIGHT": "LEFT"}

# Reserved across every world, so that the three things every world has always
# read the same: the empty cell, the boundary, and the thing the player drives.
FLOOR = 0
WALL = 1
AGENT = 6
RESERVED: Tuple[int, ...] = (FLOOR, WALL, AGENT)

# Everything else is drawn from here, per world, in the order kinds first appear.
POOL: Tuple[int, ...] = (2, 3, 4, 5, 7, 8, 9)


def encode_cell(cell: Cell, width: int) -> int:
    return cell[0] * width + cell[1]


def decode_cell(value: int, width: int) -> Cell:
    return (value // width, value % width)


def shift(cell: Cell, action: str) -> Cell:
    dr, dc = DELTA[action]
    return (cell[0] + dr, cell[1] + dc)


@dataclass(frozen=True, order=True)
class State:
    """The complete configuration of a world at one instant.

    `vars` carries every mechanism's mutable data, concatenated in mechanism
    order.  Frozen and tuple-valued, so it is hashable and sorts deterministically
    — the reachability search, the explorer and the trace writer all depend on a
    stable order and none of them has to define one.
    """

    agent: Cell
    vars: Tuple[int, ...] = ()

    def key(self) -> Tuple[int, int, Tuple[int, ...]]:
        return (self.agent[0], self.agent[1], self.vars)

    def with_agent(self, cell: Cell) -> "State":
        return State(agent=cell, vars=self.vars)

    def written(self, writes) -> "State":
        """Return a copy with `writes` — an iterable of `(index, value)` — applied."""
        if not writes:
            return self
        buf = list(self.vars)
        for index, value in writes:
            buf[index] = value
        return State(agent=self.agent, vars=tuple(buf))
