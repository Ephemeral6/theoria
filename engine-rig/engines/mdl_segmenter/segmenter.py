"""mdl_segmenter -- segmentation, tracking and event narration as one problem.

Three jobs collapse into a single compression problem: an object is whatever
decomposition makes the total edit script (move / appear / vanish / recolor) over
the diff sequence shortest.  Concretely:

  1. propose objects per frame as connected components of non-background cells;
  2. match frame t against frame t+1 with a bipartite assignment whose costs are
     *code lengths in bits*, padded with vanish/appear lanes so that "this object
     died and another was born" competes on the same scale as "it moved";
  3. read the chosen assignment off as events, and chain the matches into tracks.

Because the assignment is scored in bits, step 2 minimises description length
rather than some ad-hoc distance -- the tracker and the MDL objective are the
same object, which is the whole point of the engine.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
from scipy.optimize import linear_sum_assignment

from engines.mdl_segmenter.costs import CostModel, changed_pixels

Cell = Tuple[int, int]
Frame = Sequence[Sequence[int]]

IMPOSSIBLE = 10 ** 6  # a cost no real encoding can reach; keeps the matrix square


@dataclass(frozen=True)
class Component:
    """One connected blob in one frame."""

    cells: Tuple[Cell, ...]            # sorted absolute cells
    colors: Tuple[int, ...]            # aligned with `cells`

    @property
    def anchor(self) -> Cell:
        return (min(r for r, _ in self.cells), min(c for _, c in self.cells))

    @property
    def box(self) -> Tuple[int, int]:
        rs = [r for r, _ in self.cells]
        cs = [c for _, c in self.cells]
        return (max(rs) - min(rs) + 1, max(cs) - min(cs) + 1)

    @property
    def shape_key(self) -> Tuple[Tuple[Cell, ...], Tuple[int, ...]]:
        """Translation-invariant identity: relative cells plus their colours."""
        ar, ac = self.anchor
        return (tuple((r - ar, c - ac) for r, c in self.cells), self.colors)

    @property
    def uniform_color(self) -> Optional[int]:
        return self.colors[0] if len(set(self.colors)) == 1 else None


@dataclass
class Event:
    t: int                             # transition index (frame t -> t+1)
    type: str                          # move | appear | vanish | recolor
    track: str
    params: Dict[str, object] = field(default_factory=dict)
    bits: int = 0

    def as_json(self) -> Dict[str, object]:
        out = {"t": self.t, "type": self.type, "track": self.track, "bits": self.bits}
        out.update(self.params)
        return out


@dataclass
class Track:
    """One object followed through the trajectory."""

    track_id: str
    first_frame: int
    color: Optional[int]
    shape: Tuple[int, int]
    rel_cells: Tuple[Cell, ...]
    anchors: List[Optional[Cell]] = field(default_factory=list)
    masks: List[Optional[Tuple[Cell, ...]]] = field(default_factory=list)

    def mask_at(self, t: int) -> Optional[Tuple[Cell, ...]]:
        return self.masks[t] if 0 <= t < len(self.masks) else None


@dataclass
class Segmentation:
    tracks: List[Track]
    events: List[Event]
    script_bits: int
    baseline_bits: int
    declaration_bits: int
    n_frames: int

    @property
    def compression_ratio(self) -> float:
        return self.script_bits / float(self.baseline_bits) if self.baseline_bits else 1.0

    @property
    def gain_bits(self) -> int:
        return self.baseline_bits - self.script_bits

    def events_at(self, t: int) -> List[Event]:
        return [e for e in self.events if e.t == t]


# ---------------------------------------------------------------- proposals

def connected_components(frame: Frame, background: int = 0) -> List[Component]:
    """4-connected blobs of non-background cells, colour-agnostic.

    Colour-agnostic on purpose: splitting by colour shatters multi-coloured
    objects, which is the known failure mode of naive connectivity (Theoria
    1.8).  Colour differences are carried inside the component and used by the
    matcher instead.
    """
    height = len(frame)
    width = len(frame[0]) if height else 0
    seen = [[False] * width for _ in range(height)]
    out: List[Component] = []
    for r0 in range(height):
        for c0 in range(width):
            if seen[r0][c0] or frame[r0][c0] == background:
                continue
            stack = [(r0, c0)]
            seen[r0][c0] = True
            blob: List[Cell] = []
            while stack:
                r, c = stack.pop()
                blob.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and not seen[nr][nc]
                        and frame[nr][nc] != background
                    ):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            cells = tuple(sorted(blob))
            out.append(Component(cells=cells, colors=tuple(frame[r][c] for r, c in cells)))
    return sorted(out, key=lambda comp: comp.cells)


# ------------------------------------------------------------------ matching

def _match_cost(a: Component, b: Component, cost: CostModel) -> Tuple[int, Optional[str], Dict]:
    """Cost in bits of explaining `a` becoming `b` as a single event."""
    if a.cells == b.cells and a.colors == b.colors:
        return 0, None, {}
    if a.shape_key == b.shape_key:
        (ar, ac), (br, bc) = a.anchor, b.anchor
        dy, dx = br - ar, bc - ac
        return cost.move_bits(dy, dx), "move", {"dy": dy, "dx": dx}
    if a.cells == b.cells:
        changed = [i for i in range(len(a.cells)) if a.colors[i] != b.colors[i]]
        return (
            cost.recolor_bits(len(changed)),
            "recolor",
            {"cells": [list(a.cells[i]) for i in changed],
             "to": [b.colors[i] for i in changed]},
        )
    return IMPOSSIBLE, None, {}


def _assign(prev: List[Component], cur: List[Component], cost: CostModel):
    """Bipartite assignment with vanish/appear lanes; returns (pairs, gone, born)."""
    n, m = len(prev), len(cur)
    if n == 0 and m == 0:
        return [], [], []
    size = n + m
    matrix = np.full((size, size), float(IMPOSSIBLE))
    meta: Dict[Tuple[int, int], Tuple[Optional[str], Dict]] = {}
    for i, a in enumerate(prev):
        for j, b in enumerate(cur):
            bits, kind, params = _match_cost(a, b, cost)
            matrix[i, j] = float(bits)
            meta[(i, j)] = (kind, params)
    for i, a in enumerate(prev):                       # vanish lane
        matrix[i, m + i] = float(cost.vanish_bits())
    for j, b in enumerate(cur):                        # appear lane
        box_h, box_w = b.box
        matrix[n + j, j] = float(cost.appear_bits(len(b.cells), box_h, box_w))
    matrix[n:, m:] = 0.0                               # padding vs padding is free

    rows, cols = linear_sum_assignment(matrix)
    pairs, gone, born = [], [], []
    for i, j in zip(rows.tolist(), cols.tolist()):
        if i < n and j < m:
            kind, params = meta[(i, j)]
            pairs.append((i, j, int(matrix[i, j]), kind, params))
        elif i < n:
            gone.append(i)
        elif j < m:
            born.append(j)
    return pairs, sorted(gone), sorted(born)


# ------------------------------------------------------------------- driver

def segment_trajectory(frames: Sequence[Frame], background: int = 0) -> Segmentation:
    per_frame = [connected_components(frame, background) for frame in frames]
    height = len(frames[0])
    width = len(frames[0][0])
    max_objects = max((len(comps) for comps in per_frame), default=1)
    cost = CostModel(height, width, max_objects=max_objects)

    tracks: Dict[str, Track] = {}
    order: List[str] = []
    next_id = [0]

    def new_track(t: int, comp: Component) -> str:
        tid = "obj%d" % next_id[0]
        next_id[0] += 1
        track = Track(
            track_id=tid,
            first_frame=t,
            color=comp.uniform_color,
            shape=comp.box,
            rel_cells=comp.shape_key[0],
            anchors=[None] * len(frames),
            masks=[None] * len(frames),
        )
        track.anchors[t] = comp.anchor
        track.masks[t] = comp.cells
        tracks[tid] = track
        order.append(tid)
        return tid

    # frame 0: every component is born; its declaration is the script's prologue
    declaration_bits = 0
    live: Dict[int, str] = {}
    for idx, comp in enumerate(per_frame[0]):
        tid = new_track(0, comp)
        live[idx] = tid
        box_h, box_w = comp.box
        declaration_bits += cost.declaration_bits(len(comp.cells), box_h, box_w)

    events: List[Event] = []
    script_bits = declaration_bits
    baseline_bits = 0

    for t in range(len(frames) - 1):
        prev, cur = per_frame[t], per_frame[t + 1]
        pairs, gone, born = _assign(prev, cur, cost)

        transition_bits = cost.b_header
        new_live: Dict[int, str] = {}
        for i, j, bits, kind, params in sorted(pairs):
            tid = live[i]
            track = tracks[tid]
            track.anchors[t + 1] = cur[j].anchor
            track.masks[t + 1] = cur[j].cells
            new_live[j] = tid
            if kind is not None:
                events.append(Event(t=t, type=kind, track=tid, params=params, bits=bits))
                transition_bits += bits
        for i in gone:
            tid = live[i]
            bits = cost.vanish_bits()
            events.append(Event(t=t, type="vanish", track=tid, bits=bits))
            transition_bits += bits
        for j in born:
            comp = cur[j]
            tid = new_track(t + 1, comp)
            new_live[j] = tid
            box_h, box_w = comp.box
            bits = cost.appear_bits(len(comp.cells), box_h, box_w)
            events.append(
                Event(t=t, type="appear", track=tid,
                      params={"at": list(comp.anchor)}, bits=bits)
            )
            transition_bits += bits

        live = new_live
        script_bits += transition_bits
        baseline_bits += cost.baseline_transition_bits(
            len(changed_pixels(frames[t], frames[t + 1]))
        )

    return Segmentation(
        tracks=[tracks[tid] for tid in order],
        events=events,
        script_bits=script_bits,
        baseline_bits=baseline_bits,
        declaration_bits=declaration_bits,
        n_frames=len(frames),
    )
