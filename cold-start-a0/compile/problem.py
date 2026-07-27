"""The **problem** half of the domain/problem split.

`theory.dsl` is the domain: it travels between levels.  Everything that is true
of *this* grid and no other lives here — the board map, where the objects start,
what `portal_exit` names, which cell wins.

Every field is derived from `artifacts/raw_trace.jsonl` and the engines' output.
Nothing is read from the referee's copy of the truth:

| field | derived from |
|---|---|
| `board` | cells whose value is constant across the trace |
| `objects` | the segmenter's tracks, frame 0 |
| `goal_cell` | the Cart's position in the frames where the trace's `win` flag is set |
| `portal_exit` | where the Cart landed on the two teleport transitions |
| `arena` | floor cells plus the cells the board cannot explain |
"""

import json
import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from pipeline.board import Board, extract_board, object_layer  # noqa: E402
from pipeline.engines_stage import background_color  # noqa: E402
from pipeline import segment_operators  # noqa: E402
from world.ground_truth import read_trace  # noqa: E402

Cell = Tuple[int, int]


@dataclass
class ObjectInstance:
    name: str
    pos: Cell
    color: int
    present: bool = True


@dataclass
class Problem:
    name: str
    height: int
    width: int
    background: int
    board: List[List[int]]                 # background where the board is silent
    objects: List[ObjectInstance]
    goal_cell: Optional[Cell]
    landmarks: Dict[str, Cell] = field(default_factory=dict)
    arena: List[Cell] = field(default_factory=list)

    def as_json(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "grid": [self.height, self.width],
            "background": self.background,
            "board": self.board,
            "objects": [
                {"name": o.name, "pos": list(o.pos), "color": o.color,
                 "present": o.present}
                for o in self.objects
            ],
            "goal_cell": list(self.goal_cell) if self.goal_cell else None,
            "landmarks": {k: list(v) for k, v in sorted(self.landmarks.items())},
            "arena": [list(c) for c in self.arena],
        }


# The names the theorize step gave the tracks (THEORIZE_LOG O-01..O-03).  The
# mapping is by colour, which is the only stable handle the engine emits.
NAME_BY_COLOR = {7: "Button", 5: "Door", 6: "Cart"}


def derive(trace_path: str, name: str,
           name_by_color: Optional[Dict[int, str]] = None) -> Problem:
    frames, actions, wins = read_trace(trace_path)
    board = extract_board(frames)
    background = background_color(board, frames)
    layer = object_layer(frames, board, background=background)
    _operator, seg, _cmp = segment_operators.choose_operator(
        layer, background=background
    )

    objects: List[ObjectInstance] = []
    for track in seg.tracks:
        mask = track.masks[0]
        if mask is None:
            continue
        color = layer[0][mask[0][0]][mask[0][1]]
        objects.append(
            ObjectInstance(
                name=(name_by_color or NAME_BY_COLOR).get(
                    color, "obj_%d" % color),
                pos=tuple(track.anchors[0]),
                color=color,
            )
        )
    objects.sort(key=lambda o: o.name)

    cart = next((o for o in objects if o.name == "Cart"), None)

    goal_cell = None
    if any(wins):
        cart_track = next(t for t in seg.tracks if t.color == 6)
        winning = {tuple(cart_track.anchors[t]) for t, w in enumerate(wins) if w}
        if len(winning) == 1:
            goal_cell = winning.pop()

    # portal_exit: where the Cart landed whenever it moved further than one cell
    landmarks: Dict[str, Cell] = {}
    cart_track = next((t for t in seg.tracks if t.color == 6), None)
    if cart_track is not None:
        jumps = set()
        for t in range(len(frames) - 1):
            a, b = cart_track.anchors[t], cart_track.anchors[t + 1]
            if a is None or b is None:
                continue
            if abs(a[0] - b[0]) + abs(a[1] - b[1]) > 1:
                jumps.add(tuple(b))
        if len(jumps) == 1:
            landmarks["portal_exit"] = jumps.pop()

    arena = [
        (r, c)
        for r in range(board.height)
        for c in range(board.width)
        if board.values[r][c] is None or board.values[r][c] == background
    ]

    return Problem(
        name=name,
        height=board.height,
        width=board.width,
        background=background,
        board=board.render(background),
        objects=objects,
        goal_cell=goal_cell,
        landmarks=landmarks,
        arena=sorted(arena),
    )


def main() -> int:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    artifacts = os.path.join(root, "artifacts")
    for trace, name in (("raw_trace.jsonl", "a0-base"),
                        ("raw_trace_no_button.jsonl", "a0-no-button")):
        problem = derive(os.path.join(artifacts, trace), name)
        out = os.path.join(artifacts, "problem_%s.json" % name)
        with open(out, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(problem.as_json(), indent=2, sort_keys=True) + "\n")
        print(name, "objects=", [(o.name, o.pos, o.color) for o in problem.objects],
              "goal=", problem.goal_cell, "landmarks=", problem.landmarks,
              "arena=", len(problem.arena))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
