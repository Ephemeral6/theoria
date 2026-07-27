"""The bit-counting scheme both the object script and the pixel baseline pay in.

One scheme, published (see this engine's README.md), simple enough to re-derive
by hand.  Rigging the comparison by choosing units is the obvious failure mode
here, so the two models share their per-transition header and neither is charged
for the initial frame; they differ only in how a transition's *content* is
encoded.

Every field is fixed-width except a move's displacement, which is Elias-gamma
coded.  That is not a refinement for its own sake: with a fixed-width offset
every displacement costs the same, so the matcher has no reason to prefer "each
block moved one cell" over "the two blocks swapped identities", and tracking
becomes ill-posed whenever two look-alikes are on the board.  Charging by
magnitude also puts the right price on the teleport -- a long jump is expensive
to describe, which is precisely why it carries information.
"""

import math
from typing import Sequence, Tuple

N_COLORS = 10  # the ARC palette; fixed so the cost model does not drift per fixture


def bits_for(n: int) -> int:
    """Bits to index n distinct values (at least 1)."""
    return max(1, int(math.ceil(math.log2(max(2, n)))))


def gamma_bits(x: int) -> int:
    """Elias-gamma code length for the non-negative integer x (coding x+1)."""
    if x < 0:
        raise ValueError("gamma_bits takes a non-negative magnitude")
    return 2 * int(math.floor(math.log2(x + 1))) + 1


def offset_bits(d: int) -> int:
    """One signed displacement component: a sign bit plus its magnitude."""
    return 1 + gamma_bits(abs(d))


class CostModel:
    def __init__(self, height: int, width: int, max_objects: int = 1,
                 n_colors: int = N_COLORS):
        self.height = height
        self.width = width
        self.b_dim = bits_for(max(height, width))
        self.b_pos = bits_for(height) + bits_for(width)
        self.b_color = bits_for(n_colors)
        self.b_evtype = 2                       # move | appear | vanish | recolor
        self.b_objid = bits_for(max(2, max_objects))
        self.b_header = 8                       # item count, paid by both models
        self.b_off = 1 + self.b_dim             # one signed offset component

    # -- object script ----------------------------------------------------
    def declaration_bits(self, n_cells: int, box_h: int, box_w: int) -> int:
        """Cost of introducing an object: box, anchor, mask bitmap, cell colours."""
        return (
            2 * self.b_dim              # bounding box dimensions
            + self.b_pos                # anchor
            + box_h * box_w             # occupancy bitmap over the box
            + n_cells * self.b_color    # colour per occupied cell
        )

    def move_bits(self, dy: int, dx: int) -> int:
        return self.b_evtype + self.b_objid + offset_bits(dy) + offset_bits(dx)

    def recolor_bits(self, n_cells_changed: int) -> int:
        return self.b_evtype + self.b_objid + n_cells_changed * self.b_color

    def vanish_bits(self) -> int:
        return self.b_evtype + self.b_objid

    def appear_bits(self, n_cells: int, box_h: int, box_w: int) -> int:
        return self.b_evtype + self.b_objid + self.declaration_bits(n_cells, box_h, box_w)

    # -- per-pixel baseline ------------------------------------------------
    def pixel_edit_bits(self) -> int:
        """One changed pixel: where it is, what colour it became."""
        return self.b_pos + self.b_color

    def baseline_transition_bits(self, n_changed: int) -> int:
        return self.b_header + n_changed * self.pixel_edit_bits()


def changed_pixels(before: Sequence[Sequence[int]],
                   after: Sequence[Sequence[int]]) -> Tuple[Tuple[int, int], ...]:
    out = []
    for r, (row_b, row_a) in enumerate(zip(before, after)):
        for c, (vb, va) in enumerate(zip(row_b, row_a)):
            if vb != va:
                out.append((r, c))
    return tuple(out)
