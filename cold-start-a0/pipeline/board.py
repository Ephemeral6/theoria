"""Board extraction: what never varies sinks to the board.

Theoria 1.8, verbatim: *"一起变的就是一个东西 ... 从不变的沉淀为棋盘"*.  This is the
first thing the pipeline does and it is not an optimisation -- `mdl_segmenter`
proposes objects as connected components of non-background cells, and in a world
with walls that would hand back the whole wall structure as one object and glue
the Door onto it.  Separating the static layer first is what makes the
segmenter's own principle applicable.

Two frame sequences come out and both are used, for different jobs:

  * the **object layer** (board cells forced to background) goes to
    `mdl_segmenter`, which narrates *what happened*;
  * the **full frames** go to the guard vocabulary, which needs the walls to
    evaluate `free(strip(D))` at all.

That split is the engine's own contract: "the miner never re-derives what
happened from pixels -- it reads pixels only to evaluate guards."
"""

from typing import List, Optional, Sequence, Tuple

Cell = Tuple[int, int]
Frame = Sequence[Sequence[int]]


class Board:
    """The static layer of a trajectory."""

    def __init__(self, values: List[List[Optional[int]]]):
        self.values = values
        self.height = len(values)
        self.width = len(values[0]) if values else 0

    @property
    def static_cells(self) -> List[Cell]:
        return [
            (r, c)
            for r in range(self.height)
            for c in range(self.width)
            if self.values[r][c] is not None
        ]

    @property
    def dynamic_cells(self) -> List[Cell]:
        return [
            (r, c)
            for r in range(self.height)
            for c in range(self.width)
            if self.values[r][c] is None
        ]

    def cells_with(self, value: int) -> List[Cell]:
        return [
            (r, c)
            for r in range(self.height)
            for c in range(self.width)
            if self.values[r][c] == value
        ]

    def render(self, background: int = 0) -> List[List[int]]:
        """The board as a frame; dynamic cells show as background."""
        return [
            [background if v is None else v for v in row]
            for row in self.values
        ]

    def as_json(self) -> dict:
        return {
            "grid": [self.height, self.width],
            "static_cells": len(self.static_cells),
            "dynamic_cells": [list(c) for c in self.dynamic_cells],
            "map": self.render(),
        }


def extract_board(frames: Sequence[Frame]) -> Board:
    """A cell is board iff it holds the same value in every frame."""
    height = len(frames[0])
    width = len(frames[0][0])
    values: List[List[Optional[int]]] = []
    for r in range(height):
        row: List[Optional[int]] = []
        for c in range(width):
            first = frames[0][r][c]
            row.append(first if all(f[r][c] == first for f in frames) else None)
        values.append(row)
    return Board(values)


def object_layer(frames: Sequence[Frame], board: Board,
                 background: int = 0) -> List[List[List[int]]]:
    """Frames with every board cell forced to background."""
    out = []
    for frame in frames:
        out.append([
            [
                background if board.values[r][c] is not None else frame[r][c]
                for c in range(board.width)
            ]
            for r in range(board.height)
        ])
    return out
