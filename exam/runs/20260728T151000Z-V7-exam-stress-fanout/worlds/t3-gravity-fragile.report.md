# Examiner's report — `t3-gravity-fragile`

Independent audit of the discrimination profile at
`exam/runs/20260728T151000Z-V7-exam-stress-fanout/worlds/t3-gravity-fragile.json`.
Everything below was recomputed locally from `worldgen/out/worlds/t3-gravity-fragile/`
and from the exam modules imported in-process. No source file was edited, no
network call made, no `pytest` run, no `git` command issued.

**Headline.** The instrument's classification is correct on every item — but the
paper it is describing does not examine this world. All 8 items are drawn from
`walk` and `blocked_by_wall`; the three families the world is named for
(`gravity`, `consumable`, `push`) contribute **zero** items. A four-line
sheet-only heuristic that knows nothing about this world scores **8/8**,
capturing both items the instrument calls `theory`. The honest effective size of
the shipped paper is **0**, not 2.

---

## 1. Is the classification true of this world's actual mechanics?

**Yes — all 8 items verified, zero defects in the instrument.**

I re-derived every transition by hand from `spec.json`'s layout and the rule
table in `GROUND_TRUTH.md`, in a scratch reimplementation that does not import
`worldgen.core.world` (it re-parses the frame, applies the rule table, then runs
settle). All 8 recomputed `frame_after` values and all 8 recomputed rule tags
match the recorded ones exactly.

The board (`spec.json:50-58`) is three horizontal corridors — rows 1, 3, 5 — with
row 2 solid except `(2,3)` and row 4 solid except `(4,5)`. Both gaps hold fragile
tiles (`spec.json:11-36`). One block starts at `(3,4)`. Agent starts `(1,1)`,
goal `(5,7)`.

| item | action | rule | split | class | my recomputation | cells changed |
|---|---|---|---|---|---|---|
| `t3-gravity-fragile-000` | UP | `blocked_by_wall` | heldout | free | agent `(5,1)`, `(4,1)` is wall → no change | 0 |
| `t3-gravity-fragile-001` | LEFT | `walk` | replay | memorised | agent `(3,3)`→`(3,2)`; `(4,2)` wall so no fall | 2 |
| `t3-gravity-fragile-002` | RIGHT | `walk` | replay | memorised | agent `(3,1)`→`(3,2)` | 2 |
| `t3-gravity-fragile-003` | DOWN | `blocked_by_wall` | replay | free | agent `(3,1)`, `(4,1)` is wall → no change | 0 |
| `t3-gravity-fragile-004` | RIGHT | `walk` | heldout | theory | agent `(3,3)`→`(3,4)`, block at `(3,5)` untouched | 2 |
| `t3-gravity-fragile-005` | DOWN | `blocked_by_wall` | replay | free | agent `(1,2)`, `(2,2)` is wall → no change | 0 |
| `t3-gravity-fragile-006` | RIGHT | `walk` | heldout | theory | agent `(3,1)`→`(3,2)`, block at `(3,5)` untouched | 2 |
| `t3-gravity-fragile-007` | UP | `blocked_by_wall` | heldout | free | agent `(3,4)`, `(2,4)` is wall → no change | 0 |

The `replay` tags are independently confirmed against `raw_trace.jsonl`:
`-001` is trace `t=10→11`, `-002` is `t=15→16`, `-003` is `t=13→14`,
`-005` is `t=3→4`. The `heldout` tags are confirmed too — `-004` and `-006`
require the block at `(3,5)`, a configuration the trace only reaches at `t=20`,
its terminal frame with `action: null`, so no transition out of it was published.

Every `free` item changes 0 cells and every `theory`/`memorised` item changes 2.
**No `free` item changes the frame and no `theory` item leaves it unchanged.**
No defect found in `exam/tools/discrimination.py`.

### The cascade question — and the finding that matters

You asked whether any item's answer involves more than one cell moving, and
whether the frame carries enough state to predict the cascade. Census over all
156 reachable transitions, by cells changed:

| rule | reachable transitions | cells changed |
|---|---|---|
| `walk` | 64 | always exactly 2 |
| `blocked_by_wall` | 79 | 0 |
| `blocked_by_collapsed` | 6 | 0 |
| `blocked_by_block` | 1 | 0 |
| `cross_fragile` | 3 | **3** |
| `push` | 3 | **3** |

Only **6 of 156** transitions change more than 2 cells, and **all six are
excluded from the paper**. So:

* **No item on this paper has a cascading answer.** Not one. The 2-cell items are
  a single agent step: one cell vacated, one occupied. The multi-cell physics —
  agent leaves, tile flips `3→4`, agent lands one row down — appears only in
  `cross_fragile`, and every `cross_fragile` transition is quota-blocked.
* Gravity is not merely under-examined, it is **structurally fused to
  `cross_fragile`**. All 64 `walk` transitions change exactly 2 cells, meaning a
  walk never triggers a fall: rows 2 and 4 are solid except at the two tile
  cells, so the only descent in the whole world is *through* a fragile tile.
  Removing the `consumable` family would remove gravity's only observable effect.
* **The frame is sufficient** where it is used. `ground_truth.json:8-13` records
  `frame_determines_state.injective: true` over all 39 states, with zero
  collisions. The reason is worth stating because it is not obvious: the fragile
  tile's *armed* state (1) is never observable, both because
  `consumable.py:121-130` paints armed as the collapsed colour and because the
  `armed_tile_under_agent` invariant puts the agent's colour 6 over it anyway.
  And an armed state never survives a step here — both tiles have free floor
  directly beneath (`(3,3)` under `(2,3)`, `(5,5)` under `(4,5)`), so gravity
  carries the agent straight off in the same settle and the tile collapses
  immediately. Confirmed empirically: across all 39 reachable states, tile cells
  only ever show 3 or 4, never an intermediate.

---

## 2. Does the marker misjudge anything on this world?

### Structural invariants — both hold

| examinee | verdicts over the 8 items | score |
|---|---|---|
| `null` | `unanswered` × 8 | 0/8 |
| `oracle` | `correct` × 8 | 8/8 |
| `bluffer` | `correct` × 4, `wrong` × 4 | 4/8 |
| `memoriser` | `correct` × 6, `wrong` × 2 | 6/8 |

**Silence is never paid** — `null` scores zero, and `unanswered` on every item;
never `correct`. **Ground truth is never marked wrong** — `oracle` produces no
`wrong` and no `abstained`. Both confirmed.

### Stress cases (26 variants × 4 items — `-000`, `-001`, `-004`, `-006`)

Behaviour is identical across all four items except where the answer coincides
with the truth (the bluffer answer is `correct` on the static item `-000`, as it
should be). Verdicts a fair examiner would agree with:

| answer shape | verdict | fair? |
|---|---|---|
| exact grid, bare | `correct` | yes |
| `{"frame_after": grid}` / `{"frame": …}` / `{"after": …}` | `correct` | yes |
| `{"frame_after": grid, "note": "…"}` | `correct` | yes — extra keys tolerated |
| `{"abstain": false, "frame_after": grid}` | `correct` | yes |
| tuple of tuples | `correct` | yes |
| transposed (9×7) | `wrong`, `shape_ok: False` | yes |
| one cell changed | `wrong`, `cells_wrong: 1` | yes |
| short grid (6 rows) | `wrong`, `shape_ok: False` | yes |
| row padded to width 10 | `wrong`, `shape_ok: False` | yes |
| ragged (one row width 8) | `wrong` (malformed) | yes |
| colour 7 (outside palette) | `wrong` (malformed) | yes |
| colour 8 (legal in A0, not here) | `wrong` (malformed) | yes — palette is per-world |
| negative colour | `wrong` (malformed) | yes |
| bool-bearing grid | `wrong` (malformed) | yes — deliberate, `rubrics_heldout.py:104-105` |
| `{"abstain": true}` | `abstained` | yes |
| `"abstain"` (string) | `abstained` | yes |
| `null` | `unanswered` | yes |
| single string of digit rows | `wrong` (malformed) | yes |
| `[[ [1],[1],… ]]` nested extra dim | `wrong` (malformed) | yes |
| `{"grid": …}`, `{"answer": …}` | `wrong` (malformed) | defensible — instructions promise `frame_after` |

### Four verdicts I would argue are wrong

**(a) `{}` scores `wrong`; bare `null` scores `unanswered`.**
`rubrics_heldout.py:138-142` treats `None` as "nothing submitted". An empty dict
is equally nothing submitted, but falls through `_as_frame` (`:75-95`, returns
`None` because no recognised field is present) and lands on the malformed branch
at `:151-154` as `wrong`. Same for `{"frame_after": null}` and
`{"frame_after": []}`. A fair examiner would call all three *unanswered* — an
examinee that submitted an empty envelope made no prediction, and grading it
identically to a wrong prediction inflates the `wrong` count in every report.
This is not hypothetical: `mark.py:51-52` already routes a *missing* item id to
`unanswered`, so the rubric and the marker disagree about what "nothing" means
depending on whether the key is absent or present-and-empty.

**(b) A grid of digit strings scores `wrong`.**
`[["1","1",…],…]` is rejected at `rubrics_heldout.py:104-105` and marked
`wrong`. The module's own stated principle contradicts this: `:80-84` says
accepting two envelope shapes is "a decision about what is being measured — an
examinee that predicts the world correctly and wraps it differently has not made
a prediction error, and a rubric that scored it as one would be marking JSON
conventions." `"1"` versus `1` is exactly a JSON convention, and it is the single
most likely formatting slip from any examinee that renders a grid as text. A fair
examiner would either coerce it or give it a distinct verdict — zero points is
defensible, `wrong` is not, because the report cannot tell it from a failed
prediction.

**(c) A grid of floats scores `wrong`.**
`[[1.0, 1.0, …], …]` is rejected by the same `isinstance(cell, int)` check.
`6.0 == 6` in Python, and any answer that has been through numpy, pandas, or a
JSON round-trip in a language without an integer type arrives this way. Note the
rubric explicitly reasons about `bool` at `:103-105` and rejects it on purpose
(correct — `True == 1` would silently pass), but says nothing about `float`,
which suggests the rejection is incidental rather than intended. A fair examiner
would accept a float that is integral.

**(d) `{"abstain": "true"}` and `{"Abstain": true}` score `wrong`.**
`_is_abstention` (`:115-121`) requires the literal key `abstain` mapped to the
literal `True`. A string `"true"` or a capitalised key falls through to
malformed → `wrong`. Since `_is_abstention` already accepts four free-text string
forms (`"abstain"`, `"abstained"`, `"unknown"`, `"i cannot tell"`), the strictness
on the dict path is inconsistent with the leniency on the string path. A fair
examiner would record these as `abstained`. The stake is real: the whole point of
the abstained/wrong split (`rubrics_heldout.py:17-21`) is to say whether an
examinee knew it did not know, and a near-miss abstention silently becomes a
wrong prediction.

### One latent hazard, not currently firing

`_LEGAL_CELLS = frozenset({0, 2, 4, 8})` (`rubrics_heldout.py:56`) is the fallback
when truth carries no `legal_cells`. It contains neither `1` (wall) nor `6`
(agent), so *every* frame of this world would be rejected as malformed. Verified:
grading the exact correct answer for `-004` against a truth dict with
`legal_cells` removed yields `wrong` — "answer is not a well-formed frame". The
paper does supply `legal_cells` (`heldout_worldgen.py:201`; the value for this
world is `(0,1,2,3,4,6)`), so nothing is broken today. But the failure mode is
silent and total, and it reads on a report as an examinee that cannot format
JSON — exactly the misdiagnosis `:50-55` was written to prevent.

---

## 3. Can a cheap examinee beat the bluffer floor?

**Yes — comprehensively. It does not merely beat the floor, it ties the oracle.**

Bluffer floor on this paper: **4/8 = 0.500** (`unchanged_frame_share: 0.5` in the
paper notes, confirmed by marking).

The strategy, **S1**, reads only `frame_before`, `action`, `legend`, `grid`. It
never opens `ground_truth.json` and never sees any `Item.truth`:

1. locate the cell whose colour equals `legend["agent"]`;
2. compute the target cell one step in the action's direction;
3. if the target is off-grid or its colour equals `legend["wall"]`, return the
   input frame unchanged;
4. otherwise if its colour equals `legend["floor"]`, write `floor` into the old
   agent cell and `agent` into the target, and return that.

That is the entire theory: *walls stop you, floor lets you through, one step at a
time.* It contains no gravity, no push, no fragile handling, and nothing specific
to this world.

| examinee | score | of the 2 `theory` items | of the 2 `memorised` items |
|---|---|---|---|
| bluffer (the floor) | 4/8 = 0.500 | 0/2 | 0/2 |
| **S1 (walk-only, sheet-only)** | **8/8 = 1.000** | **2/2** | **2/2** |
| S2 (S1 + generic gravity) | 8/8 = 1.000 | 2/2 | 2/2 |
| S3 (S1 + gravity + push + fragile) | 8/8 = 1.000 | 2/2 | 2/2 |
| memoriser | 6/8 = 0.750 | 0/2 | 2/2 |
| oracle | 8/8 = 1.000 | 2/2 | 2/2 |

**S1 captures 100% of the `theory` residue** — +0.500 over the floor, and it is
indistinguishable from the oracle on this paper. Adding gravity buys nothing,
because no item on the paper involves a fall.

Why this happens is visible in the item table: `-004` and `-006` are labelled
`theory` only because the memoriser has not seen those exact frames. Mechanically
`-006` is the *same transition* as the `memorised` item `-002` — agent `(3,1)`
walks right to `(3,2)` — differing only in where the block sits three cells away,
a cell that plays no part in the transition. The "world model" being asked for is
"a walk is still a walk when an irrelevant object moved."

For calibration on how much S1 does *not* know: run against the full reachable
relation it scores **150/156**, missing exactly the 3 `cross_fragile` and 3 `push`
transitions — the six multi-cell ones. S3, which adds push and one-shot-tile
handling, scores **156/156**. So a genuine world model is worth 6 transitions out
of 156 in this world, and the shipped paper samples none of them.

---

## 4. What is this world's honest effective size?

**Zero.** The profile's `effective_size: 2` is the count of items the *oracle
alone* settles among three fixed strategies. Add a fourth strategy that any
examinee could write from the sheet alone (S1 above) and the residue is 0/8.
Nothing on this paper ranks an examinee with a world model above one with a
generic grid prior. `exam/tools/discrimination.py:60-67` already warns that a
fourth strategy could settle a `theory` item for free; **this world is a concrete
instance of that warning, and both of its `theory` items fall to it.**

### Dead weight, named

Four of six rules never reach the paper. `heldout_worldgen.py:126-137` requires
`per_class` transitions **inside** the trace and `per_class` **outside** it:

| rule | reachable | in trace | held out | why it is dead weight |
|---|---|---|---|---|
| `cross_fragile` | 3 | 1 | 2 | **structurally impossible.** Needs 4 total at `per_class=2`; the world contains 3, and cannot contain more — `tile_state_is_monotone` caps it at one witness per tile, and there are two tiles. No exploration budget fixes this. |
| `push` | 3 | 1 | 2 | **structurally impossible.** Needs 4; the world contains 3. The agent enters row 3 at `(3,3)`, always left of the block, and can never reach its right side, so the block is monotone rightward over 4 cells = exactly 3 pushes, ever. |
| `blocked_by_block` | 1 | 0 | 1 | **structurally impossible.** One reachable transition in the entire world. |
| `blocked_by_collapsed` | 6 | 0 | 6 | fixable — 6 transitions exist, but the 20-step trace witnessed none. A longer or better-targeted trace would unblock this one. |
| `blocked_by_wall` | 79 | — | — | examined, but **barren**: all 4 of its items are `free`. A no-op prediction is exactly what the bluffer submits. |
| `walk` | 64 | — | — | the only rule producing an informative item — and S1 answers all of them. |

So the world's three headline families are quota-eliminated *by their own
irreversibility*. The mechanism that makes the world interesting is the same one
that makes it unexaminable: a rule you can only witness twice cannot supply two
replay witnesses and two held-out witnesses.

### Is the residue large enough to rank two examinees apart?

No. Against the three built-in strategies the paper separates three tiers
(4/8, 6/8, 8/8). Against any examinee that reads the legend, it separates
nothing: bluffer 4/8, everyone else 8/8. Two examinees that both know "walls
block" are indistinguishable, and an examinee that knows the *fragile* mechanism
gains exactly 0 marks for it.

### Why 39 states, and is that weaker or stronger?

Tier-3 siblings, from `worldgen/out/worlds/INDEX.json`:

| world | reachable states |
|---|---|
| `t3-full-house` | 2654 |
| `t3-latch-maze` | 436 |
| `t3-cycler-portal-lock` | 262 |
| **`t3-gravity-fragile`** | **39** |

**Yes — the irreversible mechanism is collapsing the reachable set, and it is
doing so three times over.** The 39 states factor cleanly into three layers by
tile state:

| tiles `(2,3)`,`(4,5)` | states | agent confined to | block cells |
|---|---|---|---|
| intact, intact | 7 | row 1 | `(3,4)` |
| collapsed, intact | 18 | row 3 | `(3,4)`…`(3,7)` |
| collapsed, collapsed | 14 | row 5 | `(3,6)`, `(3,7)` |

Three compounding one-way ratchets: tile `(2,3)` collapses on first use and seals
row 1 forever (rows 2 is otherwise solid wall), tile `(4,5)` does the same for
row 3, and the block is monotone rightward because the agent can never get behind
it. A naive product of the visible degrees of freedom — 23 open cells × 4 block
positions × 4 tile-state pairs — is 368; the reachable set is 39, about 11%.
The reachable graph is 7 SCCs of sizes 7, 7, 7, 6, 5, 4, 3, arranged in a DAG:
within a layer the agent shuffles freely along its corridor, but every edge
between layers is one-way. `spec.json:59` says exactly this ("the reachable graph
is close to a DAG"), and the measurement confirms it. A further consequence:
**86 of 156 state-action pairs (55.1%) are self-loops** — 79 `blocked_by_wall`,
6 `blocked_by_collapsed`, 1 `blocked_by_block` — which is the direct source of
the paper's `free` class.

**Weaker as an exam world, in its current configuration.** A world model is worth
6 of 156 transitions here, and the quota rule excludes all 6. Small is not the
problem per se — the problem is that irreversibility puts the *interesting*
transitions permanently below the sampling threshold while leaving 143 boring ones
above it. In principle this shape could make a *stronger* exam: a one-way world
punishes a wrong prediction harder because the state is unrecoverable. The exam
does not currently ask that question — it asks for single-step frames, and
single-step frames in a one-way world are dominated by no-ops.

---

## Things you did not ask about

**1. The default quota is strictly the wrong choice for this world.**
`plan()` at `per_class=1` produces the *same 8 items of budget* but a materially
better paper:

| | `per_class=1` | `per_class=2` (shipped) |
|---|---|---|
| items | 8 | 8 |
| rules examined | `blocked_by_wall`, `cross_fragile`, `push`, `walk` | `blocked_by_wall`, `walk` |
| free / memorised / theory | 2 / 3 / 3 | 4 / 2 / 2 |
| theory share | 0.375 | 0.250 |
| bluffer floor | 2/8 = 0.250 | 4/8 = 0.500 |
| S1 (cheap sheet-only) | **4/8 = 0.500** | **8/8 = 1.000** |
| S3 (push + fragile) | 8/8 | 8/8 |
| memoriser | 5/8 | 6/8 |

At `per_class=1` the paper actually ranks: bluffer 0.250 < S1 0.500 < memoriser
0.625 < S3/oracle 1.000, four distinguishable tiers, and the cheap heuristic
captures only 1 of 3 `theory` items. The matched-quota argument
(`heldout_worldgen.py:24-36`) still holds at `per_class=1` — both splits still
get identical rule mixes, so the tag still carries no information. `per_class=2`
is defended as "the smallest number that can distinguish a rule an examinee has
learned from one it got right once" (`:65-67`), which is a sound argument in
general and the wrong trade here: it buys a second witness of `walk` at the price
of the world's entire mechanism set. **Recommendation: make `per_class` a
per-world choice driven by rule scarcity, or fall back to 1 for any rule whose
total reachable transition count is below `2 × per_class`.**

**2. `blocked_by_collapsed` is the one genuinely fixable exclusion.** Six
reachable transitions, none witnessed by the 20-step trace
(`coverage.json:8-15`). Trace coverage is 19/156 = 12.2% of state-action pairs.
A trace that spends a few steps walking back into a collapsed tile would unblock
a rule that is *not* structurally capped, adding a real class at `per_class=2`
without touching the quota rule.

**3. The `theory` label is doing less work here than the name implies.** Items
`-004` and `-006` are `theory` only because the memoriser is frame-keyed:
`-006` is mechanically identical to the `memorised` item `-002`, differing solely
in a block position three cells away that does not participate. The instrument is
measuring "this exact frame was not published", not "this transition needs a
model". That is a fair reading of what `discrimination.py` claims to measure, but
worth flagging because the reading note at `:255-259` invites `theory` to be
"quoted as the paper's real size", and on this world that number is an
overstatement by a factor of 2 relative to the honest value of 0. Consider adding
a fourth voter — a generic legend-reading walker like S1 — to the `VOTERS` tuple.
It would reclassify both items here and cost nothing to compute.

**4. Gravity is unobservable except through `consumable` in this world.**
All 64 `walk` transitions change exactly 2 cells, so no walk ever ends in a fall.
The only descents in the world are the 3 `cross_fragile` transitions. An examinee
could hold a completely wrong theory of gravity and never be caught — including
on the full 156-transition relation, where S2 (with gravity) and S1 (without)
score identically at 150/156. If the `gravity` family is meant to be tested, this
world's layout does not test it.

---

*Recomputed 2026-07-28 from `worldgen/out/worlds/t3-gravity-fragile/` (`spec.json`,
`raw_trace.jsonl`, `ground_truth.json`, `coverage.json`, `GROUND_TRUTH.md`),
`worldgen/out/worlds/INDEX.json`, and in-process imports of
`exam.papers.heldout_worldgen`, `exam.papers.worldgen_port`,
`exam.grading.rubrics_heldout`, `exam.grading.mark`, `exam.tools.discrimination`.
Rubric digest `e06bdf52…1cb091`, matching the profile under audit. Read-only
throughout.*
