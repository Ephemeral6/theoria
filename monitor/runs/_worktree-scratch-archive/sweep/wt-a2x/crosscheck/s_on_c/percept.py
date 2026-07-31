"""Perception for World C — the rewrite of `a0-spike/pipeline/stages.py`'s front half.

The original hard-coded three palette entries (`PLAYER = 2`, `BOX = 4`,
`WALL = 8`) and a `Percept` with exactly two movable objects. Neither survives
contact with a world that has five colours and one mover. So the palette is
*derived* here — from what the colours do across the observed frames — and the
percept is a generic colour grid plus whichever cell holds the mover.

Nothing in this file names a role. `7` is not called "button" here; it is called
"a colour that recolours in place". Roles are adjudicated in the manual, on the
strength of the mined effect classes, and the reasoning is in THEORIZE_LOG.md.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

Cell = Tuple[int, int]
Frame = List[List[int]]

DELTA = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}


@dataclass(frozen=True)
class Percept:
    """One frame, read as a colour grid with the mover located."""

    grid: Tuple[Tuple[int, ...], ...]
    player: Cell
    height: int
    width: int
    background: int

    def on_board(self, cell: Cell) -> bool:
        return 0 <= cell[0] < self.height and 0 <= cell[1] < self.width

    def colour_at(self, cell: Cell) -> str:
        """A colour name usable in a guard literal. Off-board is its own value."""
        if not self.on_board(cell):
            return "offboard"
        return "c%d" % self.grid[cell[0]][cell[1]]

    def raw_at(self, cell: Cell) -> Optional[int]:
        if not self.on_board(cell):
            return None
        return self.grid[cell[0]][cell[1]]

    def ahead(self, direction: str, times: int = 1) -> Cell:
        dr, dc = DELTA[direction]
        return (self.player[0] + dr * times, self.player[1] + dc * times)

    def cells_of(self, colour: int) -> Tuple[Cell, ...]:
        return tuple((r, c) for r in range(self.height) for c in range(self.width)
                     if self.grid[r][c] == colour)


# --------------------------------------------------------------- stage 1: perceive

def palette_report(frames: Sequence[Frame], background: int) -> Dict[str, Any]:
    """Classify every colour by what it does across the observed frames.

    Four disjoint behaviours are enough to describe World C, and each is a fact
    about the trajectories rather than a guess about meaning:

    * **mover** — occupies exactly one cell in every frame, and that cell changes;
    * **fixed** — its cell set is identical in every frame;
    * **appears** / **disappears** — its cell set grows or shrinks.

    A colour that is both fixed-count and moving would be a second mover; the
    caller asserts there is exactly one, and the assertion is part of the record.
    """
    colours = sorted({v for f in frames for row in f for v in row})
    report: Dict[int, Dict[str, Any]] = {}
    for colour in colours:
        sets = [frozenset((r, c) for r, row in enumerate(f)
                          for c, v in enumerate(row) if v == colour)
                for f in frames]
        sizes = sorted({len(s) for s in sets})
        distinct = len({s for s in sets})
        first, last = sets[0], sets[-1]
        if colour == background:
            behaviour = "background"
        elif distinct == 1:
            behaviour = "fixed"
        elif sizes == [1] and all(len(s) == 1 for s in sets):
            behaviour = "mover"
        elif len(first) > len(last):
            behaviour = "disappears"
        elif len(first) < len(last):
            behaviour = "appears"
        else:
            behaviour = "varies"
        report[colour] = {
            "colour": colour,
            "behaviour": behaviour,
            "cell_counts": sizes,
            "distinct_cell_sets": distinct,
            "cells_first_frame": sorted(first),
        }
    return {"colours": colours, "by_colour": report}


def infer_palette(report: Dict[str, Any], background: int) -> Dict[str, int]:
    """Name the two roles perception alone can settle: background and mover."""
    movers = [c for c, d in report["by_colour"].items() if d["behaviour"] == "mover"]
    if len(movers) != 1:
        raise ValueError("expected exactly one mover colour, found %r" % (movers,))
    return {"background": background, "player": movers[0]}


def read_frame(frame: Sequence[Sequence[int]], palette: Dict[str, int]) -> Percept:
    grid = tuple(tuple(int(v) for v in row) for row in frame)
    player_colour = palette["player"]
    player = None
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v == player_colour:
                if player is not None:
                    raise ValueError("two cells hold the mover colour %d" % player_colour)
                player = (r, c)
    if player is None:
        raise ValueError("no cell holds the mover colour %d" % player_colour)
    return Percept(grid=grid, player=player, height=len(grid), width=len(grid[0]),
                   background=palette["background"])
