"""The frame store: everything the arm has observed, and the arithmetic over it.

An ARC command answers with a *cascade* -- between 1 and 113 grids for one
action; the precheck saw 7 from a single `g50t` ACTION2. Two different things
live in that list and both are kept:

* the **transition**: (grid before, action, grid after), where "after" is the
  last grid of the cascade. This is what a rule is mined from and what
  `theory.py` is asked to predict.
* the **cascade** itself: the intermediate grids. They are evidence about the
  world's internal steps, and `Theoria.md`'s `cascade single_frame |
  multi_frame` semantics is a claim *about* them. Collapsing them at intake
  would decide that question by accident, so nothing here collapses them.

The derived quantities are arithmetic, not judgement: which cells have ever
changed, which colour is the background, what a step's diff was. Naming any of
it -- Cart, Door, wall -- happens in `inner/theorize.py` and nowhere else.
"""

import hashlib
import json
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Cell = Tuple[int, int]

HEX = "0123456789abcdef"


def grid_hash(grid: Optional[Grid]) -> Optional[str]:
    if grid is None:
        return None
    blob = json.dumps(grid, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


def render(grid: Grid) -> str:
    """64 rows of 64 hex digits. baseline-arms' rendering, kept identical so
    the two arms' prompts differ in content and not in encoding."""
    return "\n".join("".join(HEX[v & 0xF] for v in row) for row in grid)


def render_window(grid: Grid, box: Optional[Tuple[int, int, int, int]],
                  with_ruler: bool = True) -> str:
    """A crop, with row/column numbers, so the desk can name a cell it sees."""
    if box is None:
        return render(grid)
    r0, c0, r1, c1 = box
    lines = []
    if with_ruler:
        tens = "    " + "".join(str((c // 10) % 10) for c in range(c0, c1 + 1))
        ones = "    " + "".join(str(c % 10) for c in range(c0, c1 + 1))
        lines.append(tens)
        lines.append(ones)
    for r in range(r0, r1 + 1):
        row = "".join(HEX[grid[r][c] & 0xF] for c in range(c0, c1 + 1))
        lines.append("%3d %s" % (r, row))
    return "\n".join(lines)


def diff_cells(a: Optional[Grid], b: Optional[Grid]) -> List[Tuple[int, int, int, int]]:
    """(row, col, before, after) for every cell that changed."""
    if a is None or b is None:
        return []
    out = []
    for r in range(min(len(a), len(b))):
        ra, rb = a[r], b[r]
        for c in range(min(len(ra), len(rb))):
            if ra[c] != rb[c]:
                out.append((r, c, ra[c], rb[c]))
    return out


def describe_diff(a: Optional[Grid], b: Optional[Grid], limit: int = 16) -> str:
    changed = diff_cells(a, b)
    if a is None:
        return "(first frame)"
    if not changed:
        return "no cells changed"
    if len(changed) <= limit:
        return "; ".join("(%d,%d) %x->%x" % t for t in changed)
    rows = sorted({r for r, _, _, _ in changed})
    cols = sorted({c for _, c, _, _ in changed})
    colours_before = sorted({x for _, _, x, _ in changed})
    colours_after = sorted({y for _, _, _, y in changed})
    return ("%d cells changed, rows %d-%d, cols %d-%d, %s -> %s"
            % (len(changed), rows[0], rows[-1], cols[0], cols[-1],
               colours_before, colours_after))


class Step:
    """One command and everything it returned."""

    __slots__ = ("step_idx", "action", "data", "status", "frames", "state",
                 "levels_completed", "available_actions", "probe", "note",
                 "before_hash")

    def __init__(self, step_idx: int, action: str, frames: List[Grid], *,
                 data: Optional[Dict[str, Any]] = None, status: int = 200,
                 state: Optional[str] = None,
                 levels_completed: Optional[int] = None,
                 available_actions: Optional[List[int]] = None,
                 probe: bool = False, note: str = "",
                 before_hash: Optional[str] = None):
        self.step_idx = step_idx
        self.action = action
        self.data = data
        self.status = status
        self.frames = frames
        self.state = state
        self.levels_completed = levels_completed
        self.available_actions = available_actions or []
        self.probe = probe
        self.note = note
        self.before_hash = before_hash

    @property
    def n_frames(self) -> int:
        return len(self.frames)

    @property
    def grid(self) -> Optional[Grid]:
        """The state after the command: the last grid of the cascade."""
        return self.frames[-1] if self.frames else None

    def as_json(self) -> Dict[str, Any]:
        return {"step_idx": self.step_idx, "action": self.action,
                "data": self.data, "status": self.status,
                "n_frames": self.n_frames, "state": self.state,
                "levels_completed": self.levels_completed,
                "available_actions": self.available_actions,
                "probe": self.probe, "note": self.note,
                "grid_hash": grid_hash(self.grid),
                "before_hash": self.before_hash}


class FrameStore:
    """Every successful command, in order. Failed commands are not states."""

    def __init__(self) -> None:
        self.steps: List[Step] = []

    # -- intake ------------------------------------------------------------
    def add(self, step: Step) -> Step:
        step.before_hash = grid_hash(self.current)
        self.steps.append(step)
        return step

    def since(self, start_idx: int) -> "FrameStore":
        """A view of the trace from `start_idx` on, sharing the same `Step`s.

        Every derived property here -- `grids`, `actions`, `constant_cells`,
        `background` -- is a statement about *one continuous trajectory*. A
        level boundary is not a transition the manual's `step` function
        produces: the world is replaced wholesale by the server, no action
        caused it, and cells that were constant for the whole of level 1 carry
        no information about level 2's board. Replaying or segmenting across
        one is a category error that shows up as `replay_mismatch` -- surprise
        the manual is then charged, at model prices, to "repair".

        So the beats that reason over a trajectory take this view rather than
        the whole store. The whole store is still what gets written to
        `trace.jsonl`: the boundary is a fact about the run and is kept.

        The `Step`s are shared, not copied -- `before_hash` and `step_idx` stay
        as they were recorded, so a step's identity is the same in both views.
        """
        view = FrameStore()
        view.steps = self.steps[start_idx:]
        return view

    # -- the sequence ------------------------------------------------------
    @property
    def current(self) -> Optional[Grid]:
        for step in reversed(self.steps):
            if step.grid is not None:
                return step.grid
        return None

    @property
    def grids(self) -> List[Grid]:
        """One grid per step: the canonical state sequence."""
        return [s.grid for s in self.steps if s.grid is not None]

    @property
    def actions(self) -> List[Optional[str]]:
        """Aligned with `grids`: element t is the action taken *at* grid t.

        `cegis_miner.transitions_from_segmentation` reads this list and stops
        at the first `None`, so the last element must be `None` -- there is no
        action after the final observed frame.
        """
        labelled = [s for s in self.steps if s.grid is not None]
        out: List[Optional[str]] = []
        for i in range(len(labelled)):
            out.append(labelled[i + 1].action if i + 1 < len(labelled) else None)
        return out

    @property
    def shape(self) -> Optional[Tuple[int, int]]:
        grid = self.current
        return (len(grid), len(grid[0])) if grid else None

    def __len__(self) -> int:
        return len(self.steps)

    # -- arithmetic over what was seen -------------------------------------
    def colour_histogram(self) -> Dict[int, int]:
        counts: Dict[int, int] = {}
        for grid in self.grids:
            for row in grid:
                for v in row:
                    counts[v] = counts.get(v, 0) + 1
        return counts

    def background(self) -> int:
        """The most common colour over everything seen.

        A *choice*, and the cheapest defensible one: `mdl_segmenter` needs a
        background to call non-background pixels objects, and Theoria's
        full-frame responsibility (constraint 2) needs the leftovers to be the
        board. If the modal colour turns out to be a wall rather than a floor
        the segmentation degrades loudly (one enormous track), which is a
        visible failure rather than a silent one.
        """
        hist = self.colour_histogram()
        if not hist:
            return 0
        return max(sorted(hist), key=lambda c: hist[c])

    def constant_cells(self) -> List[Cell]:
        """Cells that have shown one colour for the whole history: the board."""
        grids = self.grids
        if not grids:
            return []
        first = grids[0]
        h, w = len(first), len(first[0])
        out = []
        for r in range(h):
            for c in range(w):
                v = first[r][c]
                if all(g[r][c] == v for g in grids):
                    out.append((r, c))
        return out

    def dynamic_cells(self) -> List[Cell]:
        """Cells the board cannot explain. These are what an object hypothesis
        has to account for, and what constraint 2 says may not be ignored."""
        grids = self.grids
        if not grids:
            return []
        first = grids[0]
        h, w = len(first), len(first[0])
        out = []
        for r in range(h):
            for c in range(w):
                v = first[r][c]
                if any(g[r][c] != v for g in grids):
                    out.append((r, c))
        return out

    def bounding_box(self, cells: Sequence[Cell],
                     pad: int = 1) -> Optional[Tuple[int, int, int, int]]:
        if not cells:
            return None
        grid = self.current
        h, w = (len(grid), len(grid[0])) if grid else (64, 64)
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        return (max(0, min(rows) - pad), max(0, min(cols) - pad),
                min(h - 1, max(rows) + pad), min(w - 1, max(cols) + pad))

    def crop(self, grid: Grid, box: Tuple[int, int, int, int]) -> Grid:
        r0, c0, r1, c1 = box
        return [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]

    # -- reporting ---------------------------------------------------------
    def summary(self) -> Dict[str, Any]:
        grids = self.grids
        dynamic = self.dynamic_cells()
        hist = self.colour_histogram()
        return {
            "steps": len(self.steps),
            "states": len(grids),
            "shape": list(self.shape) if self.shape else None,
            "background": self.background(),
            "colours_seen": sorted(hist),
            "constant_cells": len(self.constant_cells()),
            "dynamic_cells": len(dynamic),
            # The number the manual's objects actually have to cover: a dynamic
            # cell showing the background colour in frame 0 is already drawn
            # correctly by the board, so only the rest need an owner. This is
            # the figure certify's responsibility pass will report against.
            "cells_needing_an_owner": sum(
                1 for r, c in dynamic
                if grids and grids[0][r][c] != self.background()),
            "dynamic_box": list(self.bounding_box(dynamic) or []) or None,
            "cascade_lengths": sorted({s.n_frames for s in self.steps}),
            "max_frames_in_one_command": max((s.n_frames for s in self.steps),
                                             default=0),
            "distinct_states": len({grid_hash(g) for g in grids}),
            "actions_used": sorted({s.action for s in self.steps}),
        }

    def to_jsonl(self, path: str, *, with_frames: bool = True) -> str:
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            for step in self.steps:
                row: Dict[str, Any] = step.as_json()
                if with_frames:
                    row["frames"] = step.frames
                fh.write(json.dumps(row, sort_keys=True, separators=(",", ":")))
                fh.write("\n")
        return path


def load_store(path: str) -> FrameStore:
    store = FrameStore()
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            step = Step(row["step_idx"], row["action"], row.get("frames") or [],
                        data=row.get("data"), status=row.get("status", 200),
                        state=row.get("state"),
                        levels_completed=row.get("levels_completed"),
                        available_actions=row.get("available_actions"),
                        probe=row.get("probe", False), note=row.get("note", ""))
            store.add(step)
    return store


def cells_of_interest(store: FrameStore, cap: int = 240) -> List[Cell]:
    """The cells a conservation law is looked for over.

    `zero_space` builds one GF(2) feature per (cell, colour); 4096 cells times
    the colours seen is tens of thousands of features and an elimination that
    says nothing useful. A0's answer was the arena -- the cells the world
    actually uses -- and this is the same answer computed rather than known:
    the cells that have ever changed, most-active first, capped.

    The cap is a *declared* narrowing, not a silent one: `adapt.py` records how
    many dynamic cells there were and how many were handed over, so a law found
    here is known to be a law about those cells only.
    """
    grids = store.grids
    if not grids:
        return []
    first = grids[0]
    h, w = len(first), len(first[0])
    churn: Dict[Cell, int] = {}
    for r in range(h):
        for c in range(w):
            distinct = len({g[r][c] for g in grids})
            if distinct > 1:
                churn[(r, c)] = distinct
    ordered = sorted(churn, key=lambda cell: (-churn[cell], cell))
    return sorted(ordered[:cap])
