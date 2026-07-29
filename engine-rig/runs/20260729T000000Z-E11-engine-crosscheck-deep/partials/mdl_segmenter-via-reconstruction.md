# mdl_segmenter, cross-checked by rebuilding the original frames

**Work order** E11-engine-crosscheck-deep, lane: `mdl_segmenter` via reconstruction.
**Tree** `.worktrees/e11-engine-crosscheck-deep`, base commit `ed592a6`.
**Nothing under `engine-rig/` or `fuzzlab/` was modified.** The harness lives outside
the repo, in the session scratchpad (`scratchpad/e11/xcheck.py`, `xcheck2.py`).

---

## 1. What the engine actually promises

This matters more than the measurement, because the obvious report here — "the
description does not replay the frames" — would be a false positive. The engine
declines the promise twice, in writing, before any test is run:

* `fuzzlab/props/mdl_segmenter.py:5-18` — "**no frame round-trip.** There is no
  replay function anywhere in the rig, and a `Segmentation` could not support
  one… The 'script' is a bit-accounting scheme, not a decodable encoding." It
  also declines any compression guarantee: `script_bits < baseline_bits` is a
  Fixture A result, not a contract.
* `fuzzlab/BUGS.md`, section *What was deliberately not asserted*, repeats both
  in the same terms.
* `engine-rig/engines/mdl_segmenter/README.md:64-82` publishes the payload as
  **stable**, with `"color": null` explicitly documented for non-uniform objects.

So: **a failed round-trip is not a defect of this engine and is not reported as
one below.** What is reported is (a) *how much* is lost, which nobody had
measured, and (b) three places where the engine's own internal accounts disagree
with each other — those are defects, because they are promises the engine does
make.

---

## 2. The chain, and who wrote each link

| Step | Code | Whose |
|---|---|---|
| world generation | `fuzzlab/worlds/gridworld.py` `generate(seed)` | **shared** (unavoidable) |
| seed derivation | `fuzzlab/prng.py` `derive()` → `common.rng.SplitMix64` | **shared** |
| segmentation | `engines.mdl_segmenter.segment_trajectory` | **subject under test** |
| publication | `engines.mdl_segmenter.candidates` / `to_payload` | **subject under test** |
| frame reconstruction | `scratchpad/e11/xcheck.py::reconstruct` | **mine, written here** |
| cost model re-derivation | `xcheck.py::MyCost`, `m_bits_for`, `m_gamma`, `m_offset` | **mine**, transcribed from README.md's cost table, not imported from `costs.py` |
| connected components | `xcheck.py::my_components` | **mine** |
| changed-pixel diff | `xcheck.py::my_changed` | **mine** |
| ground-truth masks | `GridWorld.truth_masks()` | **shared** (the generator's own answer) |

No engine reconstruction or validation helper was called — there is none to call.
Critically, the reconstructor reads **only the published payload**
(`color`, `cells`, `anchors`, `events`), never `Track.masks`, which is the
engine's own per-frame answer and is not published anyway.

### Shared dependencies — full list

1. `fuzzlab/worlds/gridworld.py` — world generator. Unavoidable: I need frames
   with known ground truth. Mitigation: it is not the engine, and its `Rules`
   class is a standalone transition function (its own docstring says so).
2. `fuzzlab/prng.py` + `common.rng.SplitMix64` — seed stream. Shared with the
   engine's own fixtures. A biased stream could hide cases; it cannot manufacture
   the disagreements found below.
3. `GridWorld.truth_masks()` — used in §6 only.
4. Python 3.13, numpy, scipy (`linear_sum_assignment`, inside the engine only).
5. `engine-rig/engines/mdl_segmenter/README.md` — I transcribed the cost table
   from it. If the README is wrong in the same direction as `costs.py`, my bit
   check is circular. It is *not* independent of the docs, only of the code.
   Stated plainly rather than papered over.

---

## 3. Method and scale

300 `gridworld` worlds, seeds `derive(0xE11C5EC, "gridworld", i)`, `i` in
`[0,300)`; grids 5x5 to 12x12, 6993 frames, 506 302 cells, 1807 tracks, 6939
events. The operator A/B in §7 was additionally swept over 800 worlds.
Re-running reproduces every figure byte-for-byte.

**Reconstruction rule.** Start from an all-background canvas of the right size.
For each published track and each frame where `anchors[t]` is not null, paint
`cells` translated to the anchor, in colour `color`; if `color` is null the cell
is painted `UNKNOWN`. `recolor` events are replayed onto the per-cell colour map
(gridworld emits none, so this path is untested here — say so).

**Note before the table:** the payload does **not** carry the grid height, width,
or the background value. I supplied all three from the world spec. A consumer
holding only `candidates.jsonl` cannot even allocate the canvas. Consistent with
"not a decodable encoding", but worth stating since the payload is the published
interface.

---

## 4. Reconstruction fidelity — the numbers

| Measure | Result |
|---|---|
| worlds replayed **pixel-exact on every frame** | **121 / 300 (40.3 %)** |
| frames replayed pixel-exact | 3275 / 6993 (46.8 %) |
| cells total | 506 302 |
| cells **wrong** (painted the wrong colour) | **0 (0.0000 %)** |
| cells **unrecoverable** (`color: null`) | **18 118 (3.5785 %)** |
| worlds with all tracks uniformly coloured | 121 — **all 121 replay exactly** |
| worlds with ≥1 non-uniform track | 179 — **0 replay exactly** |
| non-uniform tracks | 1008 / 1807 (55.8 %) |
| per-world loss among affected worlds | min 0.09 %, median 5.45 %, mean 7.30 %, **max 35.00 %** |

The split is total and clean, and this is the finding:

> **The published description is losslessly correct about geometry and silent
> about colour on exactly the non-uniform objects.** Every cell the engine claims
> is occupied *is* occupied, in every frame, in all 300 worlds — zero wrong
> pixels. The only information that does not survive is the per-cell colour of
> multi-coloured objects, and it is lost completely rather than approximately.

So the loss is one-dimensional and predictable: **`color == null` is a perfect
predictor of failure to replay.** A consumer can tell in advance, from the
payload alone, whether the description will replay. That is a much better
position than "40 % of worlds fail" suggests, and nobody had established it.

---

## 5. Is the bit account self-consistent? — yes, completely

Recomputed from my own transcription of the cost table, against my own component
finder and my own pixel diff, on all 300 worlds:

| Check | Result |
|---|---|
| `declaration_bits` (frame 0, from my components) | **300 / 300 agree** |
| `script_bits` (my full recomputation) | **300 / 300 agree** |
| `baseline_bits` (my own changed-pixel count) | **300 / 300 agree** |
| the identity `script = decl + (n-1)*8 + Σ event.bits` | **300 / 300 hold** |
| **every individual event's `bits` field** (6939 events) | **0 mismatches** |

The last row is new. `fuzzlab`'s `script_bits_identity` sums `e.bits` as given, so
a systematically mispriced `move_bits` would still satisfy it. Recomputing each
event from its own parameters closes that hole. It is clean.

`baseline_bits` is confirmed correct here for the first time — §8 notes that no
invariant reads it.

---

## 6. Three internal disagreements (defects, not missing promises)

### D1 — the object-id field is too narrow to name the objects it indexes

`costs.py:48`: `b_objid = bits_for(max(2, max_objects))`, where
`segmenter.py:220` sets `max_objects = max(len(comps) for comps in per_frame)` —
the most components in **any single frame**. But tracks accumulate across the
whole trajectory through appear/vanish churn, and every event pays exactly one
`b_objid` field to say *which track it is about*.

| | |
|---|---|
| worlds where `n_tracks > 2**b_objid` | **126 / 300 (42 %)** |
| worst case | seed 9374841901514197509: **40 tracks addressed by a 2-bit id** (capacity 4) |
| total under-charge, at `ceil(log2 n_tracks)` per event | **9675 bits over 168 843 bits of script (5.7 %)** |
| worlds that stop beating the baseline once the id is honest | **10** (242 → 232 of 300) |

This is a genuine MDL error, not a nitpick: the script is priced as if it could
name its objects, and it cannot. Ten worlds change verdict on the engine's own
headline comparison. **Only crossing the cost model against the track list shows
it** — every existing test takes `max_objects` as given.

### D2 — colour bits are charged for information the representation throws away

`costs.py:55-62`: every declaration (and every `appear`, which contains one)
charges `n_cells * b_color` — one colour **per occupied cell**. But `Track`
(`segmenter.py:80`) stores a single `Optional[int] color`, and `to_payload`
publishes that one field.

| | |
|---|---|
| colour bits charged in declarations/appears | 30 084 |
| colour bits actually retained in the payload | **3196 (10.6 %)** |
| cells charged for a colour that was then discarded | **5090** |

Nearly 90 % of the colour budget prices an encoding the engine does not emit.
This is the mirror image of D1 — over-charged here, under-charged there — and it
is the mechanical cause of §4: the engine **paid in full** for exactly the
per-cell colours whose loss makes 179 worlds unreplayable. Whether the fix is to
store the colours or to stop charging for them is an adjudication call, not
mine; but as it stands `script_bits` describes a richer encoding than exists.

### D3 — `CostModel.b_off` is dead

`costs.py:52` assigns `self.b_off = 1 + self.b_dim`, the fixed-width offset the
module docstring argues *against* using. Never read anywhere in the repo
(`grep b_off` → one hit, the assignment). Harmless, but it is a fixed-width
offset sitting in a cost model whose central design claim is that offsets are
gamma-coded.

---

## 7. `segment_operator` — the hardwiring is real. Confirmed.

`engine-rig/engines/mdl_segmenter/__init__.py:23`:

```python
"segment_operator": "connected_components(4)+bipartite_common_fate",
```

A literal. `run()` and `segment_trajectory()` both take `split_by_color`
(`__init__.py:62`, `segmenter.py:216`), and `connected_components`' own docstring
(`segmenter.py:115-129`) calls the choice "the segmentation operator hypothesis
space of Theoria 1.8" and says the A0 world *needs* the second one. The payload
never records which was used.

Swept over **800 worlds**, both operators on each:

| | |
|---|---|
| worlds where the `segment_operator` string differs | **0 / 800** |
| worlds where the two operators produce **different track counts** | **479 / 800 (59.9 %)** |
| example | seed 12147563315917480426: **4 tracks vs 10**, `script_bits` 313 vs 421, byte-identical `segment_operator` |
| largest counts seen | 28 vs 26, 23 vs 26, 25 vs 25 (same count, different cut) |

**Confirmed as a defect.** Two provenance-incompatible segmentations are
published under one label, into an append-only candidate stream whose whole
purpose is that the LLM can adjudicate what an engine proposed. I did not
reproduce the specific "23 vs 6" figure from the earlier report — that ratio does
not occur in `gridworld`, whose object counts are small; my worst ratio is 4 vs
10. The substance is confirmed and the magnitude is larger than 23-vs-6 suggests,
because it is 60 % of worlds, not one anecdote.

Note `cold-start-a0/pipeline/engines_stage.py:104` passes
`segment_operator=operator + "+bipartite_common_fate"` — a downstream consumer
has already worked around this by recomputing the field itself, which is evidence
the field is load-bearing and known-broken at the source.

## `Track.color` — correct

Independently recomputed for all **1807** tracks: gather the colours the original
frames show on the track's occupied cells across every frame it is present; the
truth is that colour if the set is a singleton, else `None`.
**0 disagreements in 1807.** `Track.color` is right. It is, however, read by no
invariant in the rig (§8) — correct by luck of nobody having broken it, not by
test.

---

## 8. What only the cross-check exposes

1. **The size of the loss, and its shape.** 3.58 % of cells, 0 % wrong,
   `color: null` a perfect predictor. No single-engine test could produce this
   because the rig has no reconstructor by design.
2. **D1, the object-id under-pricing** — needs the cost model and the track list
   in the same frame. 42 % of worlds; flips 10 worlds' compression verdict.
3. **D2, colour bits charged and discarded** — needs `costs.py` and `to_payload`
   compared. 89.4 % of the colour budget.
4. **Per-event bit correctness** (6939 events) — `script_bits_identity` sums
   `e.bits` as given and cannot see a mispriced formula.
5. **`baseline_bits` is correct but unchecked.** No invariant in `fuzzlab/props/`
   reads it (`grep baseline_bits` hits only two prose lines). It is published in
   every candidate's `mdl` block, including `gain_bits` and `ratio` derived from
   it. Now verified: 300 / 300.
6. **Ground truth exists and is never consumed.** `GridWorld.truth_masks()`
   (`gridworld.py:231`) returns the generator's own object decomposition and no
   property calls it. Comparing it to the engine's tracks:
   **173 / 300 worlds match ground truth in every frame; 5979 / 6993 frames
   (85.5 %) match; 127 worlds report more tracks than the world contains, worst
   case 40 tracks for 4 real objects.** `masks_partition_the_foreground` passes on
   all of these — a merged mover-plus-obstacle blob is still a valid partition of
   the foreground. Partition-correct and object-wrong are different things, and
   only ground truth separates them.
7. **The payload cannot name its own canvas** (§3): no height, width, or
   background.

---

## 9. Where I could not reach a conclusion

* **My bit check is code-independent, not doc-independent.** I transcribed the
  cost table from `README.md`. A shared error between README and `costs.py` would
  pass my check. Genuinely closing this needs a second derivation from
  `Theoria.md`, which I did not do.
* **`recolor` is untested by reconstruction.** `gridworld` never recolours, so
  zero `recolor` events occurred in 6939. My replay path for them is written and
  unexercised. `recolor` params *do* carry `cells` and `to`, so that path may well
  reconstruct — unmeasured either way.
* **Item 6 is not a defect claim.** The 127 inflated-track worlds are dominated by
  the mover becoming 4-adjacent to an obstacle, at which point colour-agnostic
  components genuinely merge. `gridworld.py:23-26` claims "no reachable placement
  ever touches an obstacle", but `_place_obstacles`' own docstring
  (`gridworld.py:266-284`) says the criterion was **inverted** to require the
  obstacle be *witnessed* — i.e. the mover must get adjacent. Those two docstrings
  contradict each other, and it is a **`fuzzlab` generator** question, not an
  engine one. I did not chase it; flagging it for whoever owns `fuzzlab`.
* **Whether D1/D2 should be fixed, and how,** is an adjudication call. Storing
  per-cell colours would make the round-trip lossless and justify the charge;
  dropping the charge would make the MDL number honest and keep the engine
  lossy. Both are coherent. Not my call — the work order says report, not fix.
* **One world in 300 shipped with `obstacles_dropped: true`**, i.e. the generator
  gave up on the requested obstacles. Not enough to affect any figure above, but
  the sample is not quite the drawn distribution.
