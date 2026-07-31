"""Random grid worlds -- the fuzz generalisation of Fixture A (the Cart world).

One rectangular *mover* under the push rule, zero or more static obstacles, and
an optional teleport.  The dynamics are exactly the ones `cegis_miner`'s guard
vocabulary can express, so a world outside the vocabulary never masquerades as
an engine bug:

    teleport  anchor == portal_a          -> anchor := portal_b   (any action)
    push      strip(D) in bounds and clear -> anchor += delta(D)
    otherwise                              -> nothing happens

Two things are enforced at generation time, both so that "the ground truth
segmentation" is a well-defined object rather than a matter of opinion:

* **the mover is a rectangle.**  `cegis_miner` reads `strip(D)` off an anchor and
  a bounding box; a non-rectangular mover would make the vocabulary's guard and
  the world's rule different statements, and every miner "failure" would be that
  mismatch rather than a defect.

* **no reachable placement ever touches an obstacle.**  Components are
  4-connected and colour-agnostic, so a mover that parks beside an obstacle *is*
  one object as far as any segmenter is concerned.  The generator BFSes the
  mover's whole reachable set (teleport included) and rejects placements that
  come within one cell of an obstacle, so "how many objects are on this board"
  has one answer.  Worlds that cannot satisfy it fall back to zero obstacles --
  recorded in the spec as `obstacles_dropped`, never silently.

Non-rectangular and multi-coloured obstacles *are* generated: they stress the
segmenter's component finder and its colour handling, and they cost nothing
elsewhere because they never move.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from fuzzlab.prng import Rng
from fuzzlab.worlds.common import World

Cell = Tuple[int, int]
Frame = List[List[int]]

DIRECTIONS: Tuple[str, ...] = ("UP", "DOWN", "LEFT", "RIGHT")
DELTA: Dict[str, Cell] = {
    "UP": (-1, 0),
    "DOWN": (1, 0),
    "LEFT": (0, -1),
    "RIGHT": (0, 1),
}

BACKGROUND = 0
PALETTE = tuple(range(1, 10))          # 9 non-background colours

MAX_OBSTACLE_ATTEMPTS = 24


# --------------------------------------------------------------------- shapes

def grow_polyomino(rng: Rng, n_cells: int) -> Tuple[Cell, ...]:
    """A random 4-connected shape of `n_cells` cells, normalised to origin."""
    cells: Set[Cell] = {(0, 0)}
    while len(cells) < n_cells:
        frontier = sorted(
            {
                (r + dr, c + dc)
                for (r, c) in cells
                for (dr, dc) in DELTA.values()
            }
            - cells
        )
        if not frontier:                                  # pragma: no cover
            break
        cells.add(rng.choice(frontier))
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def rect_cells(height: int, width: int) -> Tuple[Cell, ...]:
    return tuple((r, c) for r in range(height) for c in range(width))


# ---------------------------------------------------------------------- spec

@dataclass(frozen=True)
class Obstacle:
    cells: Tuple[Cell, ...]                # absolute
    colors: Tuple[int, ...]                # aligned with `cells`

    def json(self) -> Dict[str, Any]:
        return {
            "cells": [list(c) for c in self.cells],
            "colors": list(self.colors),
        }


@dataclass(frozen=True)
class GridSpec:
    seed: int
    height: int
    width: int
    mover_shape: Tuple[int, int]           # (h, w) of the rectangle
    mover_color: int
    start_anchor: Cell
    obstacles: Tuple[Obstacle, ...]
    portal: Optional[Tuple[Cell, Cell]]    # (portal_a anchor, portal_b anchor)
    n_frames: int
    obstacles_dropped: bool

    def json(self) -> Dict[str, Any]:
        return {
            "seed": self.seed,
            "height": self.height,
            "width": self.width,
            "mover_shape": list(self.mover_shape),
            "mover_color": self.mover_color,
            "start_anchor": list(self.start_anchor),
            "obstacles": [o.json() for o in self.obstacles],
            "portal": None if self.portal is None
                      else [list(self.portal[0]), list(self.portal[1])],
            "n_frames": self.n_frames,
            "obstacles_dropped": self.obstacles_dropped,
        }


# ------------------------------------------------------------------ dynamics

class Rules:
    """The world's transition function, standing alone from any engine."""

    def __init__(self, spec: GridSpec):
        self.spec = spec
        self.blocked: Set[Cell] = set()
        for obstacle in spec.obstacles:
            self.blocked.update(obstacle.cells)

    def mover_cells(self, anchor: Cell) -> List[Cell]:
        h, w = self.spec.mover_shape
        return [(anchor[0] + dr, anchor[1] + dc) for dr in range(h) for dc in range(w)]

    def in_bounds(self, cell: Cell) -> bool:
        r, c = cell
        return 0 <= r < self.spec.height and 0 <= c < self.spec.width

    def strip_cells(self, anchor: Cell, direction: str) -> List[Cell]:
        """The cells the mover sweeps into on a one-step move in `direction`."""
        r, c = anchor
        h, w = self.spec.mover_shape
        if direction == "UP":
            return [(r - 1, c + dc) for dc in range(w)]
        if direction == "DOWN":
            return [(r + h, c + dc) for dc in range(w)]
        if direction == "LEFT":
            return [(r + dr, c - 1) for dr in range(h)]
        if direction == "RIGHT":
            return [(r + dr, c + w) for dr in range(h)]
        raise ValueError(direction)

    def strip_free(self, anchor: Cell, direction: str) -> bool:
        cells = self.strip_cells(anchor, direction)
        if not all(self.in_bounds(cell) for cell in cells):
            return False
        return all(cell not in self.blocked for cell in cells)

    def anchor_fits(self, anchor: Cell) -> bool:
        cells = self.mover_cells(anchor)
        return all(self.in_bounds(c) for c in cells) and not any(
            c in self.blocked for c in cells
        )

    def step(self, anchor: Cell, action: str) -> Tuple[Cell, str]:
        """Ground-truth transition: (next anchor, event label)."""
        portal = self.spec.portal
        if portal is not None and anchor == portal[0]:
            return portal[1], "teleport"
        if self.strip_free(anchor, action):
            dr, dc = DELTA[action]
            return (anchor[0] + dr, anchor[1] + dc), "move:" + action
        return anchor, "noop"

    def reachable_anchors(self, start: Cell) -> Set[Cell]:
        seen = {start}
        stack = [start]
        while stack:
            anchor = stack.pop()
            for direction in DIRECTIONS:
                nxt = self.step(anchor, direction)[0]
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        return seen

    def render(self, anchor: Cell) -> Frame:
        grid = [[BACKGROUND] * self.spec.width for _ in range(self.spec.height)]
        for obstacle in self.spec.obstacles:
            for cell, color in zip(obstacle.cells, obstacle.colors):
                grid[cell[0]][cell[1]] = color
        for (r, c) in self.mover_cells(anchor):
            grid[r][c] = self.spec.mover_color
        return grid


# ----------------------------------------------------------------- the world

@dataclass
class GridWorld(World):
    spec: GridSpec
    rules: Rules
    frames: List[Frame]
    actions: List[Optional[str]]           # len == n_frames, last is None
    anchors: List[Cell]
    events: List[str]                      # len == n_frames - 1

    family = "gridworld"

    @property
    def seed(self) -> int:
        return self.spec.seed

    def spec_json(self) -> Dict[str, Any]:
        return self.spec.json()

    @property
    def action_list(self) -> List[str]:
        """The n_frames-1 real actions, without the trailing None."""
        return [a for a in self.actions if a is not None]

    def truth_masks(self) -> List[List[Tuple[Cell, ...]]]:
        """Ground-truth object masks per frame: mover first, then obstacles.

        Well defined precisely because the generator forbids the mover from ever
        touching an obstacle -- see the module docstring.
        """
        out = []
        for anchor in self.anchors:
            masks = [tuple(sorted(self.rules.mover_cells(anchor)))]
            masks += [tuple(sorted(o.cells)) for o in self.spec.obstacles]
            out.append(masks)
        return out

    def n_objects(self) -> int:
        return 1 + len(self.spec.obstacles)

    def moved(self) -> int:
        return sum(1 for e in self.events if e != "noop")


# ------------------------------------------------------------------ generator

def _place_obstacles(rng: Rng, height: int, width: int,
                     mover_shape: Tuple[int, int],
                     start_anchor: Cell,
                     portal: Optional[Tuple[Cell, Cell]],
                     n_wanted: int) -> Tuple[Tuple[Obstacle, ...], bool]:
    """Obstacles that no reachable mover placement ever touches.

    Returns (obstacles, dropped).  `dropped` is True when the rejection loop
    gave up and the world ships with none -- which is a legitimate world, just
    not the one the draw asked for, and the spec says so.
    """
    if n_wanted == 0:
        return (), False

    all_cells = [(r, c) for r in range(height) for c in range(width)]

    for _ in range(MAX_OBSTACLE_ATTEMPTS):
        obstacles: List[Obstacle] = []
        taken: Set[Cell] = set()
        ok = True
        for _ in range(n_wanted):
            size = rng.between(1, 4)
            shape = grow_polyomino(rng, size)
            span_r = max(r for r, _ in shape) + 1
            span_c = max(c for _, c in shape) + 1
            if span_r > height or span_c > width:
                ok = False
                break
            origin = (rng.below(height - span_r + 1), rng.below(width - span_c + 1))
            cells = tuple(sorted((origin[0] + r, origin[1] + c) for r, c in shape))
            if any(cell in taken for cell in cells):
                ok = False
                break
            colors = tuple(rng.choice(PALETTE) for _ in cells)
            obstacles.append(Obstacle(cells=cells, colors=colors))
            taken.update(cells)
        if not ok:
            continue

        # Obstacles must not touch each other either, or two of them are one
        # component and the object count is again a matter of opinion.
        if _any_touching(obstacles):
            continue

        candidate = GridSpec(
            seed=0, height=height, width=width, mover_shape=mover_shape,
            mover_color=1, start_anchor=start_anchor, obstacles=tuple(obstacles),
            portal=portal, n_frames=0, obstacles_dropped=False,
        )
        rules = Rules(candidate)
        if not rules.anchor_fits(start_anchor):
            continue
        if portal is not None and not rules.anchor_fits(portal[1]):
            continue

        halo = {
            (cell[0] + dr, cell[1] + dc)
            for o in obstacles for cell in o.cells
            for (dr, dc) in list(DELTA.values()) + [(0, 0)]
        }
        reachable = rules.reachable_anchors(start_anchor)
        if any(
            cell in halo
            for anchor in reachable
            for cell in rules.mover_cells(anchor)
        ):
            continue
        if any(not rules.anchor_fits(a) for a in reachable):
            continue
        _ = all_cells
        return tuple(obstacles), False

    return (), True


def _any_touching(obstacles: Sequence[Obstacle]) -> bool:
    for i, a in enumerate(obstacles):
        halo = {
            (cell[0] + dr, cell[1] + dc)
            for cell in a.cells
            for (dr, dc) in list(DELTA.values()) + [(0, 0)]
        }
        for b in obstacles[i + 1:]:
            if halo & set(b.cells):
                return True
    return False


def generate(seed: int) -> GridWorld:
    """A grid world, a pure function of `seed`."""
    rng = Rng(seed)

    height = rng.between(5, 12)
    width = rng.between(5, 12)
    mover_h = rng.between(1, min(3, height - 1))
    mover_w = rng.between(1, min(3, width - 1))
    mover_color = rng.choice(PALETTE)
    start_anchor = (rng.below(height - mover_h + 1), rng.below(width - mover_w + 1))

    portal = None
    if rng.chance(1, 3):
        a = (rng.below(height - mover_h + 1), rng.below(width - mover_w + 1))
        b = (rng.below(height - mover_h + 1), rng.below(width - mover_w + 1))
        if a != b:
            portal = (a, b)

    n_obstacles = rng.weighted([(0, 3), (1, 3), (2, 2), (3, 1)])
    obstacles, dropped = _place_obstacles(
        rng, height, width, (mover_h, mover_w), start_anchor, portal, n_obstacles
    )

    n_frames = rng.between(6, 40)

    spec = GridSpec(
        seed=seed, height=height, width=width,
        mover_shape=(mover_h, mover_w), mover_color=mover_color,
        start_anchor=start_anchor, obstacles=obstacles, portal=portal,
        n_frames=n_frames, obstacles_dropped=dropped,
    )
    rules = Rules(spec)

    anchor = start_anchor
    anchors = [anchor]
    events: List[str] = []
    actions: List[Optional[str]] = []
    for _ in range(n_frames - 1):
        action = rng.choice(DIRECTIONS)
        actions.append(action)
        anchor, event = rules.step(anchor, action)
        anchors.append(anchor)
        events.append(event)
    actions.append(None)

    frames = [rules.render(a) for a in anchors]

    return GridWorld(
        spec=spec, rules=rules, frames=frames, actions=actions,
        anchors=anchors, events=events,
    )
