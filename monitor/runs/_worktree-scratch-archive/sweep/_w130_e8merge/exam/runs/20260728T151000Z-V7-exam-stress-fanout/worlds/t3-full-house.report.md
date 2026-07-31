# `t3-full-house` — independent examiner's report

Scope: the world `worldgen/out/worlds/t3-full-house/`, its 24-item paper
`v2-heldout-t3-full-house`, and the discrimination profile at
`exam/runs/20260728T151000Z-V7-exam-stress-fanout/worlds/t3-full-house.json`.
Everything below was produced locally in python. No file was modified, no
network call made, no `git` command run, no test suite invoked.

Headline: **the instrument's classification is arithmetically correct and I found
no defect in it. But the number it reports — `effective_size: 8` — is an
overstatement on this world by a factor of at least two, and arguably by all of
it: a 60-line examinee that reads only the sheet scores 24/24.**

---

## 1. Is the classification true of this world's actual mechanics?

### 1.1 Method

I wrote an independent transition function from `spec.json` and the rule table in
`GROUND_TRUTH.md:26-38` — my own parser (rendered frame → agent / block / net
bit), my own `is_free` / `can_rest` predicates, my own renderer — and never
called `GridWorld`. I then re-derived every one of the 24 items and compared both
the frame and the rule name.

**Result: 24 of 24 frames reproduced cell-for-cell, 24 of 24 rule labels agreed.
Zero mismatches.** The frame→state parse also round-tripped on all 24
`frame_before` grids, independently confirming `frame_determines_state.injective`
(`worldgen_port.frame_ambiguous` returns `False`) on the items that matter.

Items checked — all of them, not a sample:

| class | item ids | frame changes |
|---|---|---|
| `free` (8) | `-002 -004 -012 -017 -018 -021 -022 -023` | **none** (0 cells differ on all 8) |
| `memorised` (8) | `-000 -005 -006 -007 -008 -014 -015 -019` | all 8 |
| `theory` (8) | `-001 -003 -009 -010 -011 -013 -016 -020` | all 8 |

So the two properties you asked me to falsify both hold: **no `free` item changes
the frame, and every `theory` item does.** `dead: 0` is correct — the oracle is
correct on 24/24. `anomalies: []` is correct. The `by_rule`, `by_split` and
`by_class` tables in the profile JSON all reproduce.

### 1.2 What the composition actually buys — one item, and it is a free mark

This world composes `portal`, `push` and `switch_door`. Only **one** item on the
paper is a transition that neither mechanism alone would produce:

* **`t3-full-house-002`** — agent at `(7,8)`, action `UP`, block at `(6,8)`. The
  cell beyond the block is `(5,8)`, which the layout marks `.` (open floor) —
  but it is a portal mouth. `GridWorld.is_free` (`worldgen/core/world.py:112-124`)
  excludes `no_rest` cells, so a block may not be parked on a portal mouth. The
  push therefore fails on a cell that looks passable. This is push × portal, and
  it is the only item on the sheet that is.

  It is classified **`free`**. Its frame does not change, so a bluffer scores it.
  The one genuinely compositional question on the largest world in the catalogue
  is worth zero discrimination.

The other three `blocked_by_block` items (`-004`, `-021`, `-022`) are all blocked
by an ordinary wall (`layout` char `#` at `(8,3)`, `(1,5)`, `(8,8)`) — push alone
would produce them.

### 1.3 The only non-local rule on the paper

`toggle_switch` is the one rule whose effect is not adjacent to the agent. All
four items (`-003 -005 -008 -010`) change exactly two cells: the switch at
`(6,1)` and the door at `(3,5)`, at Chebyshev distance 3–4 from the agent. That
cascade (`door_mirrors_net`, `GROUND_TRUTH.md:36`) is the only action-at-a-distance
the paper tests, and it is the only thing my cheap examinee's per-item variant
failed on (§3). Everything else on this paper is a 1–3 cell edit within one step
of the agent.

### 1.4 Trace thinness — and why "held out" is weaker than it sounds

| quantity | value |
|---|---|
| reachable states | 2 654 |
| reachable state-action pairs | 10 616 |
| pairs in the published trace | 217 (**2.04 %**) |
| distinct frames in the trace | 73 of 2 654 (**2.75 %**) |

That looks like a paper whose held-out half is a different world. It is not.
Keying the evidence index on the *full rendered frame* (`worldgen_port.transition_key`,
`worldgen_port.py:148-158`) means a state that differs from a traced state only in
where the single block is parked counts as unseen. Three of the eight `theory`
items are exactly that:

| theory item | replay twin | before-frames differ only at | effect footprint |
|---|---|---|---|
| `t3-full-house-016` | `t3-full-house-000` | `(1,1)` / `(3,3)` — block moved | **identical** |
| `t3-full-house-009` | `t3-full-house-006` | `(2,6)` / `(3,3)` — block moved | **identical** |
| `t3-full-house-010` | `t3-full-house-005` | `(3,3)` / `(7,3)` — block moved | **identical** |

Each pair is the same agent, the same action, the same two cells changing to the
same values. The block is on the other side of the map and plays no part. Under
the exact-key definition one is `replay` and the other is `theory`.

Measured, not asserted: I built a **positional memoriser** — the same trace the
`memoriser` gets, but indexed on `(agent cell, action) → cell deltas` instead of
`(full frame, action)`. It scores **17/24** against the published memoriser's
16/24, and it captures **4 of the 8 `theory` items** (`-009 -011 -013 -016`) with
no world model whatsoever. Its `gap_replay_minus_heldout` is 0.25, against the
published memoriser's 0.667.

This is not a defect in `discrimination.py` — the taxonomy is exactly as
documented, and the module's own closing paragraph (`exam/tools/discrimination.py:59-67`)
predicts precisely this ("a fourth strategy nobody has written could settle it
for free, and the taxonomy would not notice"). It is a fact about the world:
**half the theory residue on `t3-full-house` is held out only in the bookkeeping
sense.**

### 1.5 The mechanism the paper does not examine at all

`blocked_by_door` and `walk_through_door` each have **62 reachable transitions
and 0 in the trace**, so the matched-quota rule (`heldout_worldgen.py:119-145`)
blocks both. The published trace never once puts the agent on the door cell
`(3,5)` (0 of 221 frames). So the `switch_door` family is examined only through
`toggle_switch` — the paper tests that the switch flips and the door redraws, and
never tests what the door *does*. `classes_not_examined: 2` in the paper's notes
is the honest record of this, but it undersells it: those two rules are the only
place the door has semantic content rather than cosmetic content.

Quota margin is also thinner than the profile suggests. `teleport_twoway` has
**exactly 2** in-trace transitions — the minimum. At `per_class=3` it drops out
and the world falls to 5 rules; at `per_class=4`, `blocked_by_block` goes too
(3 in-trace) and only 4 rules survive.

---

## 2. Does the marker misjudge anything on this world?

I ran the battery directly against `grade_frame_exact`
(`exam/grading/rubrics_heldout.py:135`) on a changing item
(`t3-full-house-020`, push, held-out) and a non-changing item
(`t3-full-house-012`, blocked-by-wall, held-out). Both behaved identically.

### 2.1 Structural invariants — both hold

* **Silence is never paid.** `null` scores `unanswered` on 24/24, `0.0` points
  total. No `correct`, no `wrong`. `mark` also awards `unanswered` for an item id
  simply absent from the answers dict (`exam/grading/mark.py:51-52`).
* **Ground truth is never marked wrong.** `oracle` scores `correct` on 24/24,
  24.0 of 24.0 points, zero `wrong`.
* **No wrong frame is ever marked correct.** I mutated every cell of every item's
  true frame to every other legal colour — **15 120 single-cell mutants, 0 marked
  correct.**

### 2.2 Verdicts that are correct and unsurprising

| answer | verdict | fair? |
|---|---|---|
| bare correct grid | `correct` | yes |
| `{"frame_after": grid}` | `correct` | yes |
| tuple-of-tuples | `correct` | yes |
| transposed correct grid (10×9) | `wrong`, `shape_ok:false` | yes — the grid is 9×10, not square, so this is a real prediction error |
| correct grid, one cell changed | `wrong`, `cells_wrong:1` | yes — no partial credit is the documented design |
| short grid (5 of 9 rows) | `wrong`, `shape_ok:false` | yes |
| ragged grid | `wrong`, malformed | yes |
| `{"abstain": true}` | `abstained`, 0.0 | yes |
| `"abstain"` (string) | `abstained` | yes |
| `null` | `unanswered` | yes |

### 2.3 Verdicts I would argue with — four of them

**(a) A correct prediction with the wrong number type is scored as a wrong
prediction.** `[[6.0, 0.0, ...]]` — the correct frame with JSON floats — is
`wrong`. So is the correct frame with string cells `[["6", "0", ...]]`.
`_as_frame` rejects any cell that is not `isinstance(cell, int)`
(`rubrics_heldout.py:104-105`).

*What a fair examiner would say:* these are format errors, not prediction
errors. The examinee predicted the world exactly right. The rubric's own
docstring makes the case for accepting `{"frame_after": …}` alongside a bare
list — "a rubric that scored it as one would be marking JSON conventions"
(`rubrics_heldout.py:80-84`) — and then marks JSON conventions one line later.
`6.0` is not an ambiguous value; `float.is_integer()` settles it. This matters in
practice: `json.loads` of a model's output, or any numpy round-trip
(`numpy.int64` is not `isinstance` of `int` either), lands here. The verdict
`wrong` is then indistinguishable in `axes` from having no theory at all.

**(b) `{}` is `wrong`; `null` is `unanswered`.** An empty dict conveys exactly as
much prediction as `null` — none — but scores `wrong`
(`rubrics_heldout.py:88-91` falls through to `return None`, then :151). `[]` is
likewise `wrong`.

*What a fair examiner would say:* nothing was submitted, so `unanswered`. As it
stands an examinee that returns `{}` on every item reports 24 wrong answers,
while one that returns `null` reports 24 unanswered — the same behaviour, two
different findings. The rubric explicitly reasons that `null` "is treated as
nothing submitted, which is what it is" (:139-140); `{}` is also nothing
submitted.

**(c) Malformed answers and wrong answers share the verdict `wrong`.** There are
four verdicts (`correct`/`wrong`/`abstained`/`unanswered`) and no `malformed`.
The distinction survives only in `detail["why"]`, which `axes` does not read
(`heldout_worldgen.py:303-345`). This is the mechanism that makes (a) and (b)
consequential rather than cosmetic: the report's headline numbers cannot tell an
examinee that got the physics wrong from one that got the physics right and the
serialisation wrong. Given that the rubric already carved out `abstained` purely
so a report could say something a score cannot, a fifth verdict is in keeping
with its own design.

**(d) The palette check has almost no power on this world.**
`legal_cells` here is `(0,1,2,3,4,5,6,7)` — eight consecutive values, because the
world uses eight colours. So `_legal_cells` (`rubrics_heldout.py:59`) rejects only
`≥8` or negative. Any garbage grid drawn from 0–7 passes the well-formedness gate
and is scored on the diff. That is not wrong, but the profile should not be read
as though the palette gate is screening anything on `t3-full-house`.

**One asymmetry worth naming, which I would *not* call a misjudgement:**
`{"abstain": true, "frame_after": <correct grid>}` scores `abstained`, not
`correct` — `_is_abstention` is tested before `_as_frame` (:145 before :149). The
examinee did declare it could not tell, so honouring the declaration is
defensible. Flagged only so nobody discovers it in a live run.

**Undocumented generosity:** `{"frame": …}` and `{"after": …}` are accepted as
aliases (`rubrics_heldout.py:88`) although only `frame_after` is promised in the
paper's instructions (`heldout_worldgen.py:213-218`). Harmless, but it means the
instructions understate what the marker takes.

---

## 3. Can a cheap examinee beat the bluffer floor without a world model?

**Yes, decisively, and this is the finding I would act on first.**

The bluffer floor on this world is **8/24 = 0.333** (the eight `free` items).
The published memoriser scores 16/24 = 0.667.

I wrote a strategy that reads only `frame_before`, `action`, `legend` and `grid`
from the sheet. It never opens `ground_truth.json`, never touches `Item.truth`,
never calls `GridWorld`, never reads `raw_trace.jsonl`. It is generic: it looks
colours up **by legend name** (`agent`, `wall`, `floor`, `block`, `portal`,
`switch`/`switch_on`, `door`) and applies the obvious folk physics those names
suggest — walk into floor, stop at wall, shove a block if the cell beyond is
floor, step onto a portal and come out the other mouth, flip a switch in place.

| variant | score | theory items captured |
|---|---|---|
| bluffer (floor) | 8/24 = 0.333 | 0 / 8 |
| memoriser | 16/24 = 0.667 | 0 / 8 |
| **cheap, one sheet at a time** | **20/24 = 0.833** | **6 / 8** |
| **cheap, allowed to look at all 24 sheets' `frame_before` grids** | **24/24 = 1.000** | **8 / 8** |
| oracle | 24/24 = 1.000 | 8 / 8 |

`gap_replay_minus_heldout` is **0.000** for both variants — replay 0.833 /
heldout 0.833, and 1.000 / 1.000. The axis designed to catch a memoriser reads
this examinee as a perfect rule-learner, which in a narrow sense it is; it just
did not learn the rules from evidence, it read them off the legend.

**The single-sheet variant's only failures** are the four `toggle_switch` items
(`-003 -005 -008 -010`). It flips the switch correctly and cannot redraw the door,
because when the door is open it renders as colour `0` and a single sheet gives
no way to know cell `(3,5)` is special. That is the one place on this paper where
real world knowledge is required — and it is 4 items, 2 of them `theory`.

**Why the 24/24 variant is not cheating.** It uses no truth of any kind. It scans
the 24 published `frame_before` grids — the paper side, which every examinee
holds — and observes:

* colour 5 (`door`) is only ever seen at `(3,5)`; colour 7 (`portal`) only at
  `(5,1)` and `(5,8)`; colours 3/4 (`switch`/`switch_on`) only at `(6,1)`;
* across all 24 sheets exactly two (switch, door) readings occur: `(3, 5)` and
  `(4, 0)`. The invariant "the door is drawn iff the switch reads 3" is therefore
  legible from the sheets alone, with no held-out answer involved.

That is enough to place the door and to know which way it flips. The paper's own
question sheets leak the map of every mechanism in the world.

Two smaller leaks compound it: `paper.world` prints
`families: ["portal", "push", "switch_door"]` (`heldout_worldgen.py:220-227`) —
the mechanism vocabulary, handed over on the sheet, which is exactly the thing
the `quota` note takes care *not* to hand over ("counts, not names … a sheet that
lists them hands the examinee the alphabet it is being asked to discover",
:239-241). And the `legend` maps semantic English names to colours, so an
examinee never has to discover that colour 2 is shovable or that colour 7 is a
portal; it is told.

---

## 4. This world's honest effective size

**Somewhere between 2 and 4 items, not 8.**

| reading | items that require a world model | why |
|---|---|---|
| profile as published | 8 | oracle-only among the three synthetic voters |
| against a positional memoriser (§1.4) | 4 | `-009 -011 -013 -016` fall to `(agent, action)` keying |
| against the cheap legend examinee (§3) | 2 | only `-003` and `-010` (`toggle_switch`, held-out) survive |
| against the cross-sheet cheap examinee | **0** | nothing survives |

The residue that resists every theory-free strategy I could write is
**`t3-full-house-003` and `t3-full-house-010`** — both `toggle_switch`, both
held-out, both requiring the examinee to know that flipping `(6,1)` redraws
`(3,5)` four cells away. Two items out of twenty-four, and they are the same
question asked twice from adjacent agent positions.

### Dead weight, by name

* **`blocked_by_wall`** — 4 items (`-012 -017 -018 -023`), all `free`. Correctly
  listed in `barren_rules`. It is definitionally barren: "nothing changes" *is*
  the bluffer's answer. It can never discriminate under an exact-frame rubric,
  in any world. It costs 4 of the 24 item slots on the largest paper in the
  catalogue.
* **`blocked_by_block`** — 4 items (`-002 -004 -021 -022`), all `free`, same
  reason. Note the loss here is sharper: `-002` is the one push × portal
  composition on the sheet (§1.2), and the rubric cannot see the difference
  between an examinee that understood why the block will not move and one that
  copied the input.
* **`walk`** — nominally 2 memorised + 2 theory, but both held-out items
  (`-011`, `-013`) fall to the positional memoriser and both fall to the cheap
  examinee. Effectively barren against anything smarter than a bluffer.
* **`teleport_twoway`** — 4 items; the two `theory` ones (`-009`, `-016`) are
  block-displaced twins of the two `replay` ones (§1.4). Effectively barren.
* **`blocked_by_door` / `walk_through_door`** — dead weight in the strongest
  sense: 62 reachable transitions each, zero in the trace, so they carry **no
  items at all**. The only rules on this world with real semantic content that a
  legend cannot give away, and they are the two the quota rule excludes.

Only **`push`** and **`toggle_switch`** carry items that any of my theory-free
strategies actually miss, and `push` misses only because my positional memoriser
mis-fires, not because push is hard.

### Is the residue large enough to rank two examinees apart?

**No.** Two items — `-003` and `-010` — cannot separate two examinees at any
useful resolution. A single coin flip on one `toggle_switch` item moves the
"real" score by 50 %. Worse, the two are near-duplicates (same rule, same split,
agent at `(7,1)` and `(5,1)`), so they are one observation with a redundant
copy, not two independent ones. `t3-full-house` is the biggest world in the
catalogue and it distinguishes a world-modeller from a legend-reader on
effectively **one distinct question**.

---

## Things you did not ask about

1. **The paper's sheet is a map of the world.** The 24 `frame_before` grids
   between them localise the door, both portal mouths and the switch, and expose
   the door/switch rendering invariant. `worldgen_port` is careful to keep
   `ground_truth.json` off the sheet (`worldgen_port.py:26-42`), and it succeeds
   — but the open half leaks the same information by aggregation. This is a
   property of the *paper*, not of a bad examinee: any examinee holding all 24
   sheets holds it. If you want the `theory` class to mean what it says, the
   legend should be opaque (`c0 … c7`) and `families` should come off
   `paper.world`.

2. **The exact-frame evidence key is doing real work you may not want.**
   `transition_key` is defended (`worldgen_port.py:148-158`) on the grounds that
   two states rendering identically are the same question. True — but the
   converse does not follow: two states rendering *almost* identically, differing
   only outside the region the action touches, are also the same question, and
   the key calls them different. That is where 3 of this world's 8 `theory` items
   come from. A locality-aware split (hold out on the causal footprint, not the
   whole frame) would shrink the count and make it mean something.

3. **`discrimination.py` should probably carry a fourth voter.** Everything in §3
   was built in about sixty lines from the sheet alone. Adding a `legend-reader`
   to `VOTERS` would collapse `theory` to the residue that actually resists it,
   and would surface this on all twenty worlds at once rather than one examiner
   at a time. The module already anticipates the gap in prose
   (`discrimination.py:59-67`); the fix is a strategy, not a rewrite.

4. **`cells_wrong: -1` is a sentinel in a numeric field.** `_diff`
   (`rubrics_heldout.py:124-132`) returns `-1` for a shape mismatch. Anything
   that aggregates `cells_wrong` across items will silently subtract. Nothing in
   `exam/` does today.

5. **`unchanged_frame_share` and the bluffer floor are the same number, computed
   twice.** `heldout_worldgen.py:207` computes 0.333333; the profile's
   `zero_discrimination_share` is 0.333333. They agreed here, which is a useful
   cross-check, and it will keep agreeing exactly as long as no rule ever changes
   the frame back to itself.
