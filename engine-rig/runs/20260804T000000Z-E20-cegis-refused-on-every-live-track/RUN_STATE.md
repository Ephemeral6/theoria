# E20 — `cegis_miner` refused on every live track, and the recorded reason was wrong

**Territory:** engine-rig. **Offline throughout:** no API call, no model call, no
network, no sealed-pile contact. The only external input is a *recorded* arm
ledger, read for its frames; the fixture the regression tests run on is synthetic.

## What the board item asked, and what the evidence said

The item's premise was that `cegis_miner` refused on every live track because the
mover is a 24-pixel ring that `connected_components(4)` merges into the floor,
and that the fix therefore lives in the `mdl_segmenter`'s row of `Theoria.md`'s
engine table — common-fate clustering instead of connected components.

**The premise about the ring is exactly right. The conclusion drawn from it is
not, and the fix it proposes would not have worked.**

## 1. The refusal, reproduced

`verify_e20.py` replays both segmentation operators and the miner over the 34
recorded frames of `theoria-arm/runs/20260731T1430Z-A3-level2-carried-r3`
(`g50t-5849a774`, development pile). It reproduces the leg's **final dispatch
exactly**: 18 tracks, 16 refusals, and the same three refusal strings that
`engines_online.jsonl` recorded.

The ring is real. Under `split_by_color=True` it is a 24-cell, 5×5, colour-9
annulus with a colour-5 centre, sitting on an 880-cell colour-5 floor, so it is
4-adjacent to the floor on every side. Under `connected_components(4)` — the
operator the leg ran — floor and ring merge into one **1006-cell, multi-coloured
blob**, and the ring's motion is narrated as a `recolor` of that blob. Confirmed.

## 2. Three things the recorded verdict welded together

The verdict was:

> `no track satisfies the miner's precondition (exactly one move event per transition). The world does not narrate as one mover.`

| refusal reason | count (of 16) | what it is about |
|---|---|---|
| `object absent at frame 0` | **13** | the miner's walk starting at frame 0 for a track born later — nothing to do with the world's narration |
| `transition 1 narrates ['recolor']` | 2 | the merged blob — the item's premise, and correct |
| `transition 4 narrates ['vanish']` | 1 | ditto |

And the arithmetic was in the record all along: `n_tracks: 18`, `n_refusals: 16`.
**Two tracks satisfied the precondition** and died somewhere else — inside
`mine()`, with `NoSeparatingGuard`, whose reason `adapt.mine` discards. The
verdict fires on `mined is None`, which conflates "refused at the precondition"
with "raised during mining", so a universal claim was printed over a 16/18 count.

## 3. The world does narrate as one mover

The operator that isolates the ring is **already in the segmenter's box**.
`split_by_color=True` gives track `obj4`: 24 cells, first frame 0, 33
transitions, 26 `move` events, and `transitions_from_segmentation` **accepts it
without refusing**. The mover was always there; the engine never saw it.

It was never chosen because the MDL objective prefers the merge, and not by a
little: **13,332 bits vs 158,012**. This is not a selector bug — the merged
script really is shorter, because splitting by colour forces the 879-cell floor
to be re-declared every time the ring's hole crosses it (70 `vanish` + 71
`appear`). The objective charges for redescribing the floor, which is an artefact
of treating the floor as an object at all.

## 4. Negative control — common-fate clustering would not have fixed this

Measured, not assumed. Over the 34 recorded frames there are **18 co-variation
classes**, and the largest is **48 cells active in all 26 transitions**: the
*union of the ring's two berths*. The ring oscillates between two disjoint
positions, so every cell of berth A changes exactly when every cell of berth B
changes. They co-vary perfectly and common fate cannot separate them.

The operator the item asked for returns a 48-cell phantom, not the 24-cell ring.
It is still a legitimate gap in the operator space (`Theoria.md:90` names 连通域、
共变聚类、模板匹配 and the repo implements only the first, in two flavours) — but
it is not this world's fix, and building it would not have moved this leg.

## 5. What actually blocked it: the guard vocabulary

Once the segmentation is right, `cegis_miner` **still** fails, with a different
error. `build_vocabulary` hardcoded the `act` atoms to UP/DOWN/LEFT/RIGHT. The
world's alphabet is `RESET, ACTION1..ACTION5`.

    36 atoms | 16 identically false | 16 identically true | 4 discriminating
    the 4: at(8,14), !at(8,14), at(14,14), !at(14,14)
    every act== literal: mask 0b0

The miner was blind to which action had been taken, and said so correctly:
`no literal separates transition 2 from the positives`. A true report about a
vocabulary that was never given the words.

## 6. The fix, measured on the same recorded evidence

Three changes, all opt-in or no-op by default (D-E20-001/002/003):

* `build_vocabulary(states, actions)` — the alphabet comes from the evidence;
* `mine(..., on_unseparable="record")` — an unseparable effect class is filed
  with its reason instead of destroying the track's whole frontier;
* `transitions_from_segmentation(..., while_present=True)` — a track born late
  keeps the frames where it exists.

| | recorded live | after |
|---|---|---|
| cegis_miner candidate rows on the r3 leg | **0** | — |
| rules, under the operator the leg ran (`cc(4)`) | 0 | **12** over the 2 tracks that had passed |
| rules, under `cc(4)+uniform_color` | 0 | **38** over 7 tracks, incl. the 24-cell mover |
| the mover's own track (`obj4`, 24 cells) | refused | **4 rules + 4 recorded gaps** |

The mover's frontier, in full:

    move_ACTION1     ACTION1 -> move dy=+6 to (14,14)   guard [act==ACTION1]   frontier 1
    move_ACTION4     ACTION4 -> move dy=-6 to  (8,14)   guard [act==ACTION4]   frontier 1
    blocked_ACTION3  ACTION3 -> none                    guard [act==ACTION3]   frontier 1
    blocked_RESET    RESET   -> none                    guard [act==RESET]     frontier 1
    UNSEPARABLE      ACTION2 -> move dy=-6   support 12 transitions
    UNSEPARABLE      ACTION2 -> none         support  1 transition
    UNSEPARABLE      ACTION5 -> move dy=+6   support 12 transitions
    UNSEPARABLE      ACTION5 -> none         support  4 transitions (the last four)

Four rules **certified at frontier width 1** — not heuristics, and not point
guesses either: width 1 is the engine stating that this is the *only* guard
consistent with 33 transitions of evidence. And four gaps named precisely: the
two actions whose effect the anchor does not determine. That is a probe target of
exactly the kind `Theoria.md:208` prices, and it is the honest residual — this
world has state the guard vocabulary still cannot name.

`explains_every_transition()` returns **False** on those tracks, deliberately.

## 7. Frontier width behaves as `Theoria.md:202` specifies

On the synthetic `ring_world` fixture, holding evidence as the variable:

| transitions of evidence | frontier width of `move_ACTION1` |
|---|---|
| 2 | **4** — `act==ACTION1`, `!act==ACTION2`, `at(3,5)`, `!at(8,5)` |
| 3 | 1, with `move_ACTION2` still at 3 |
| 12 | 1 — every class pinned |

Wide when the evidence under-determines, narrowing as it arrives. The arm's
generated frontier cannot do this: its widths are a property of the generator,
not of the evidence, and it has no notion of a class being pinned.

## Residual gaps, stated honestly

* **`_POS_BITS = 8` is still calibrated for a 12×12 board** while the live world
  is 64×64. It mis-prices `at()` against the predicates in `guard_order_key`,
  which can pick the wrong *representative* of a frontier. It cannot change a
  frontier's membership, so it is a separate ticket, not folded in here.
* **The MDL operator choice is still wrong on this world class, and the fix is
  not mine to make.** `theoria-arm/world/adapt.py` runs both variants and keeps
  the one with fewer bits; it already has the good segmentation and discards it.
  Filed to `monitor/inbox/`. engine-rig cannot fix it without crossing territory.
* **Common-fate clustering is genuinely absent** from the operator space
  `Theoria.md:90` specifies. Measured here as *not* the fix for this world, but
  the gap is real and unclosed.
* **The hidden state on `ACTION2`/`ACTION5` is not explained**, only located. The
  deciding variable is plausibly the colour-1/2 tally that advances through the
  run, but no atom reads it and none was added — inventing one to make the
  numbers close is the thing this ticket exists to argue against.
* The reproduction is of **one leg of one development-pile game**. Whether the
  other legs share the shape is untested; `verify_e20.py` takes any ledger path
  and refuses non-development-pile games, so it is one command per leg.
