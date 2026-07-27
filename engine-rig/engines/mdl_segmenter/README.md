# mdl_segmenter

Segmentation, tracking and event narration as **one** compression problem: an
object is whatever decomposition makes the total edit script over the diff
sequence shortest.

## What it does

1. **Propose** — connected components (4-neighbourhood) of non-background cells,
   colour-agnostic, so a multi-coloured object is not shattered by its own
   palette. Colour lives *inside* the component and is used by the matcher.
2. **Match** — frame t against frame t+1 by bipartite assignment
   (`scipy.optimize.linear_sum_assignment`) whose cost matrix is measured in
   **bits of description length**, padded with vanish/appear lanes so that
   "it died and another was born" competes against "it moved" on one scale.
3. **Narrate** — read the assignment off as `move` / `appear` / `vanish` /
   `recolor` events, and chain matches into tracks.

Because the assignment is scored in bits, the tracker *is* the MDL objective.

## The cost model

Both the object script and the per-pixel baseline are priced by the same scheme
(`costs.py`). Neither is charged for the initial frame, and both pay the same
8-bit per-transition header; they differ only in how a transition's content is
encoded. For a 12x12 grid and a 10-colour palette:

| Field | Bits | Value here |
|---|---|---|
| `b_pos` cell coordinate | `ceil(log2 H) + ceil(log2 W)` | 8 |
| `b_color` | `ceil(log2 n_colors)` | 4 |
| `b_evtype` | 2 | 2 |
| `b_objid` | `ceil(log2 max_objects)` | 1 |
| `b_header` per transition | 8 | 8 |
| offset component | `1 + gamma(abs d)`, `gamma(x) = 2*floor(log2(x+1))+1` | 2 (d=0), 4 (d=1), 8 (d=8) |

* object declaration = `2*b_dim` (box) + `b_pos` (anchor) + `box_h*box_w`
  (occupancy bitmap) + `n_cells*b_color` = **46 bits** for the 2x3 Cart
* `move` = `b_evtype + b_objid + offset(dy) + offset(dx)` — 9 bits for a unit
  step, 19 bits for the (8,8) teleport
* `recolor` = `b_evtype + b_objid + n_changed*b_color`
* `vanish` = `b_evtype + b_objid`; `appear` = that plus a declaration
* baseline transition = `b_header + n_changed_pixels * (b_pos + b_color)`

Displacement is Elias-gamma coded rather than fixed-width for a substantive
reason: under a fixed-width offset every displacement costs the same, the
matcher becomes indifferent between "each block moved one cell" and "the two
blocks swapped identities", and tracking is ill-posed as soon as two look-alikes
share a board. Charging by magnitude also prices the teleport correctly — a long
jump is expensive to describe, which is exactly why it is informative.

## Result on Fixture A (50 frames)

```
object script   826 bits  (46 declaration + 49*8 headers + 41*9 moves + 1*19 teleport)
pixel baseline 2888 bits  (49*8 headers + 12 bits per changed pixel)
ratio          0.286
```

The 6-cell mask is recovered identically to ground truth on all 50 frames, with
no spurious appear/vanish, and the teleport shows up as the single move whose
displacement is not a unit step.

## Payload shape — `kind: "object_hypothesis"` (stable)

```json
{
  "object_id": "obj0",
  "segment_operator": "connected_components(4)+bipartite_common_fate",
  "color": 6,                     // null if the object is not uniformly coloured
  "shape": [2, 3],                // bounding box [h, w]
  "cells": [[0,0],[0,1],...],     // occupied cells, relative to the anchor
  "first_frame": 0,
  "anchors": [[5,5], ...],        // per frame; null where the object is absent
  "events": [{"t":0,"type":"move","track":"obj0","bits":9,"dy":-1,"dx":0}, ...],
  "mdl": {"script_bits":826,"baseline_bits":2888,"gain_bits":2062,"ratio":0.286}
}
```

`evidence.transitions` lists the transitions where this object had an event;
`evidence.coverage` is `<frames present>/<frames total>`.

## API

```python
from engines import mdl_segmenter
seg = mdl_segmenter.run(frames, background=0, out_path="candidates.jsonl")
seg.tracks[0].masks[t]      # absolute cells at frame t, or None
seg.events_at(t)            # events narrating transition t -> t+1
seg.script_bits, seg.baseline_bits
```
