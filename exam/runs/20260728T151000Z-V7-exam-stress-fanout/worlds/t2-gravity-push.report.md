# Independent examination — `t2-gravity-push`

Examiner: independent audit of `exam/tools/discrimination.py`'s profile at
`exam/runs/20260728T151000Z-V7-exam-stress-fanout/worlds/t2-gravity-push.json`.
Everything below is local python against the worktree
`C:\Users\user\Desktop\theoria\.worktrees\v7-exam-stress-fanout`. No file was
edited, no network, no `git`, no `pytest` run, no contact with `arc-recon/`.

Paper under examination: `v2-heldout-t2-gravity-push`, 8 items, `per_class=2`,
rubric digest `e06bdf52…1cb091`.

## Verdict in one line

The instrument's classification is **correct on all 8 items** — every recorded
`frame_after` and every assigned `class` survives an independent re-derivation
from `spec.json`. But `effective_size: 1` is still an **overstatement**: a
14-line strategy that reads only the printed sheet scores **8/8**, so under a
voter pool that includes it the world has **0** informative items. Separately,
this paper's sheet **leaks the ground-truth rule name of every item**, and the
exam's own leakage gate catches it — it is simply never run on this paper type.

---

## 1. Is the classification true of this world's actual mechanics?

### 1.1 The hand check — all 8 items, re-derived from the layout

I re-implemented the rule table of `GROUND_TRUTH.md` from scratch (walls from
`spec.json["layout"]`, `walk` / `blocked_by_wall` / `push` / `blocked_by_block`
dispatch, then a `settle` fixpoint for gravity) and compared against
`Item.truth["frame_after"]` for every item. Grid is 7×9; the layout is

```
row0  #########
row1  #.......#
row2  ###.#####      <- the only hole in row 2 is col 3 (the shaft)
row3  #.......#
row4  #.#######      <- the only hole in row 4 is col 1 (the second shaft)
row5  #.......#
row6  #########
```

| item | action | agent | block | rule (recorded / mine) | frame changes | class | re-derivation |
|---|---|---|---|---|---|---|---|
| `-000` | RIGHT | (5,7)→(5,7) | (3,5) | `blocked_by_wall` / same | no | `free` | target (5,8) is the right wall — **match** |
| `-001` | LEFT | (3,3)→(3,2) | (3,5) | `walk` / same | yes | `memorised` | (3,2) floor; (4,2) wall so no fall — **match** |
| `-002` | LEFT | (1,2)→(1,1) | (3,5) | `walk` / same | yes | `memorised` | (1,1) floor; (2,1) wall so no fall — **match** |
| `-003` | RIGHT | (5,2)→(5,3) | (3,7) | `walk` / same | yes | **`theory`** | (5,3) floor; (6,3) wall — **match** |
| `-004` | LEFT | (5,1)→(5,1) | (3,6) | `blocked_by_wall` / same | no | `free` | target (5,0) is the left wall — **match** |
| `-005` | DOWN | (3,3)→(3,3) | (3,5) | `blocked_by_wall` / same | no | `free` | target (4,3) is wall (row 4's hole is col 1) — **match** |
| `-006` | UP | (3,3)→(3,3) | (3,6) | `walk` / same | no | `free` | target (2,3) **is** floor, so the agent rises; gravity then drops it straight back to (3,3). Net identity — **match** |
| `-007` | UP | (1,1)→(1,1) | (3,5) | `blocked_by_wall` / same | no | `free` | target (0,1) is the top wall — **match** |

All 8 frames re-derived independently: **MATCH**. All 8 rule tags: **MATCH**.
Replay provenance also checks out by hand against `raw_trace.jsonl`: `-001` is
line 10 (`t=9`), `-002` is line 5 (`t=4`), `-005` is line 9 (`t=8`), `-007` is
line 6 (`t=5`).

**No `free` item changes the frame and no `theory`/`memorised` item fails to.**
The instrument (`exam/tools/discrimination.py:95` `_classify`,
`:149` `frame_changes`) is not defective on this world. `-006` is the item most
likely to be a bug and is not one: it is tagged `walk` and does not change the
frame, which is correct, because `up_is_inert` is declared a **cascade** rule
(`ground_truth.json` rules[4], `cascade: true`) and cascades carry no rule tag
of their own by construction.

### 1.2 Why this world produces only one informative item — the cause

Three things compound, and only the third is bad luck.

**(a) The paper examines two rules, and one of them is a no-op by definition.**
`heldout_worldgen.plan` (`exam/papers/heldout_worldgen.py:119-145`) admits a
rule only if it has ≥`per_class` transitions **inside** the published trace and
≥`per_class` **outside** it. Measured over the full reachable relation:

| rule | reachable transitions | distinct keys in trace | held out | admitted? |
|---|---|---|---|---|
| `blocked_by_wall` | 71 | 5 | 66 | yes |
| `walk` | 66 | 4 | 62 | yes |
| `push` | **2** | **0** | 2 | no — 0 in trace |
| `blocked_by_block` | **1** | **0** | 1 | no — 0 in trace |

`blocked_by_wall`'s `then` clause is literally "nothing changes", and I measured
it: **0 of its 71 reachable transitions alter the frame.** So its 4 items
(2 replay + 2 heldout) are `free` *a priori* — the bluffer cannot lose them.
That is half the paper, guaranteed, before any sampling happens. This is not
specific to `t2-gravity-push`: any world that admits `blocked_by_wall` donates
`2 × per_class` structurally free items.

**(b) The `walk` half is capped at `per_class` informative items.** Of the 4
`walk` items, 2 are `replay` — and `walk`'s 4 in-trace transitions are 4/4
frame-changing, so both replay items land in `memorised` with certainty. Only
the 2 held-out `walk` items can ever be `theory`. **The structural ceiling on
this paper is 2 theory items out of 8 (0.25), reachable only on a perfect draw.**

**(c) The draw was unlucky by one.** 6 of the 62 held-out `walk` transitions are
`up_is_inert` cases (UP into open floor, settled straight back — 56/62 change,
0.903). The salted sample (`heldout_worldgen.py:113-116`) drew one of those six
as `-006`, converting a would-be `theory` item into a `free` one. Expected
number of such draws in a 2-of-62 sample is 2 × 6/62 = **0.194**; the paper got
1. So 1 of the 2 available informative slots was lost to sampling noise, and the
world landed at `theory_share = 0.125` instead of its own ceiling of 0.25.

**The root cause is the trace, and it is not fixable by budget.** The published
trace is 10 actions (`coverage.json`: `budget: 10`, `coverage: 9/140`,
`coverage_fraction: 0.0643`) and never touches the block. I checked whether a
longer trace would rescue `push`: it would not. `explorer.exhaustive_length` for
this world is **46**, and running `explorer._walk(world, budget=None)` — the
unbudgeted exhaustive walk — witnesses `blocked_by_wall` 21× and `walk` 25×, and
**`push` and `blocked_by_block` zero times, ever.** The reason is the world's own
selling point: the greedy nearest-uncovered explorer
(`worldgen/core/explorer.py:49-79`) descends the col-1 shaft to row 5, which is a
one-way sink, before it ever reaches (3,4) where a push is possible. Once in the
sink, `pool` goes empty and the walk terminates at 46 actions having covered a
few dozen of 140 state-action pairs. **No trace-budget setting can put a push in
this world's trace.** `BUDGET_FRACTION = 0.40` is irrelevant here — the world hit
the `max(10, …)` floor at `worldgen/core/explorer.py:92` anyway.

So the two rules that would produce a genuinely non-trivial prediction on this
world (a *two*-entity frame change, the block moving) are exactly the two the
paper cannot examine, and the two it does examine are the two that were already
in the trace because they are the two that fire everywhere.

### 1.3 The tag bias, quantified — it is worth exactly 0.000 marks

`run_matrix.tag_bias` (`exam/tools/run_matrix.py:103-127`) reports **0.25** here,
the catalogue's only non-zero value, and `test_worldgen_papers.py:110-123` bounds
it at ≤0.25 — i.e. this world sits exactly on the assertion.

Measured on the paper:

| split | items | frame changes | share |
|---|---|---|---|
| `replay` | 4 | 2 (`-001`, `-002`) | 0.500 |
| `heldout` | 4 | 1 (`-003`) | 0.250 |

`|0.500 − 0.250| = 0.25`.

**Two corrections to how this number should be read.**

*First, it is mostly a sampling artefact, not a structural asymmetry.* The
structural part is real and is what the docstring names: all 6 `up_is_inert`
transitions are held out, none is in the trace, so the pools genuinely differ.
But in the pools the gap is small — expected changed share on replay is
(0 + 2×1.000)/4 = 0.500, on heldout (0 + 2×0.903)/4 = 0.4516, so the **expected**
tag bias is **0.048**. The realised 0.25 is 5× that, and the excess is the `-006`
draw. Also: with 4 items per split, `tag_bias` is quantised to multiples of 0.25.
The metric **cannot report a value between 0 and 0.25 on an 8-item paper.** The
world is on the bound partly because the bound is the metric's resolution.

*Second, and more usefully: the exploit the docstring describes is worth nothing
here.* The docstring says "an examinee that noticed could bias toward 'nothing
happens' on held-out items". I enumerated every tag-conditional policy over
{stasis, move-if-floor} and marked each one:

| replay policy | heldout policy | score |
|---|---|---|
| stasis | stasis | 5/8 |
| stasis | move | 5/8 |
| **move** | **stasis** | **7/8** |
| **move** | **move** | **7/8** |

Best tag-conditional = 7/8. Best tag-*blind* = 7/8. **Marginal value of the tag:
0/8 = 0.000.** The arithmetic: on the 4 held-out items, stasis wins `-006` and
move wins `-003`, and they tie 3–3 against each other; on the 4 replay items,
stasis is 2 and move is 4, so no policy ever wants stasis on replay. Since stasis
is (weakly) the majority answer in *both* splits (0.75 heldout, 0.50 replay — a
tie), no tag-conditional stasis policy can beat the tag-blind bluffer floor
either. **The 0.25 tag bias on this world buys an examinee zero marks.** It is
worth publishing as an honest residual, but it should not be read as an
exploitable edge, and the report should say so.

---

## 2. Does the marker misjudge anything on this world?

I stressed `grade_frame_exact` (`exam/grading/rubrics_heldout.py:135`) directly
on `-000` (frame unchanged) and `-003` (frame changed, the sole `theory` item),
23 answer shapes each, by importing the module. The rubric was not edited.

Verdicts identical across both items except where the answer coincides with the
truth. The **fair** ones first, so the flags below are visible as exceptions:

| answer | verdict | fair? |
|---|---|---|
| exact bare grid | `correct` 1.0 | yes |
| `{"frame_after": grid}` / `{"frame": …}` / `{"after": …}` | `correct` 1.0 | yes — instructions promise the first, the other two are generous |
| tuple of tuples | `correct` 1.0 | yes |
| transposed 9×7 | `wrong`, `shape_ok:false`, `cells_wrong:-1` | yes |
| one cell changed | `wrong`, `shape_ok:true`, `cells_wrong:1` | yes — no partial credit is the design |
| short grid (6 rows) | `wrong`, `shape_ok:false` | yes |
| ragged (one short row) | `wrong`, "not a well-formed frame" | yes |
| `{"abstain": true}` | `abstained` 0.0 | yes |
| `null` | `unanswered` 0.0 | yes |
| the input frame (bluffer) | `correct` on `-000`, `wrong` (`cells_wrong:2`) on `-003` | yes |

### 2.1 Five verdicts I would argue are wrong

**(i) Malformed answers are indistinguishable from wrong predictions in the
verdict.** `_as_frame` returning `None` produces the verdict string `"wrong"`
(`rubrics_heldout.py:151`), the same string a genuine mis-prediction gets. Only
`detail.why` separates them, and `axes()`
(`exam/papers/heldout_worldgen.py:342-344`) counts verdicts, not details. The
project already knows this reads badly — `worldgen_port.py:174-180` says a
malformed-answer verdict "reads on the report as an examinee that cannot format
an answer" — but the fix went into the *palette* and not into the *verdict*.
`VERDICTS` (`exam/model.py:233`) has four slots and no `malformed`. On this world
that matters more than usual: an examinee that gets the physics right and the
JSON slightly wrong is reported identically to one with no theory.

**(ii) Integral floats are rejected.** `[[1.0, 1.0, …]]` → `wrong`.
`rubrics_heldout.py:104-105` checks `isinstance(cell, int)` strictly. `1.0` is an
unambiguous colour-1 cell, and a JSON round-trip through numpy, pandas, or a
model that emits `1.0` produces exactly this. This is the case most likely to
bite a real examinee and score it zero for a theory it holds correctly. The
`bool` exclusion on the same line is well-argued; the float exclusion is not
argued at all.

**(iii) `{}` and `[]` are `wrong`, not `unanswered`.** `mark.py:9-13` states the
principle: "An item with no answer is `unanswered` … because the difference
matters: an arm with no deliverable scores zero on handover by *having nothing to
submit*, and that is a finding". An empty dict and an empty list are having
nothing to submit. They score 0.0 either way, so no total moves, but they inflate
`wrong` and deflate `unanswered` in `axes()` — and `unanswered` is the axis that
carries the finding.

**(iv) `{"frame_after": null}` is `wrong`, not `unanswered`.** A bare `null` is
correctly `unanswered` (`rubrics_heldout.py:138-142`), but the same null wrapped
in the envelope the instructions ask for is `wrong`. The wrapping is explicitly
declared not to be part of what is measured (`rubrics_heldout.py:80-83`: "a rubric
that scored it as one would be marking JSON conventions"), yet here it changes
the verdict.

**(v) `"I do not know"` is `wrong`, `"abstain"` is `abstained`.**
`_is_abstention` (`rubrics_heldout.py:115-121`) matches a closed list of four
strings, one of which is the phrase `"i cannot tell"`. A near-miss phrasing falls
through to `wrong`. Given that the rubric's whole stated reason for keeping
abstention separate is "so a report can say whether an examinee knew it did not
know", a four-string whitelist is thin. Likewise `{"abstain": false}` → `wrong`.

**Two things I checked and would *not* flag.** A colour outside the palette
(`8`, which is legal in A0 but not here) is refused as "not a well-formed frame"
rather than compared — correct, though it loses the `cells_wrong` diagnostic on
what is really a near miss. And a 9×7 transpose is refused on shape rather than
compared cell-wise — correct.

### 2.2 One fragility worth naming: the whole paper hangs on `legal_cells`

This world's palette is `{floor:0, wall:1, block:2, agent:6}`. The rubric's
fallback `_LEGAL_CELLS` is `{0, 2, 4, 8}` (`rubrics_heldout.py:56`), which
intersects it in `{0, 2}` and contains neither the wall colour nor the agent
colour. I graded the **oracle's own answer** against a truth dict with
`legal_cells` removed:

```
_legal_cells(with)    = [0, 1, 2, 6]
_legal_cells(without) = [0, 2, 4, 8]
oracle answer -> wrong  {'why': 'answer is not a well-formed frame'}
```

So if a future builder ever stops populating `truth["legal_cells"]`
(`heldout_worldgen.py:201`), every answer on this world — including ground
truth — is marked `wrong` with a message that blames the **examinee**.
Calibration catches the *fact* (`run_matrix.py:153-155` asserts the oracle is
never `wrong`), but the failure message points the wrong way. This is not a live
defect; it is a single optional field standing between the paper and a 0.000
across the board.

### 2.3 The two structural invariants — both confirmed

Marked all four fakes against the real key:

| mode | fraction | verdicts |
|---|---|---|
| `oracle` | 1.000000 | `{correct: 8}` — **no `wrong` anywhere** ✓ |
| `null` | 0.000000 | `{unanswered: 8}`, total awarded 0.0 — **silence is never paid** ✓ |
| `memoriser` | 0.875000 | `{correct: 7, wrong: 1}` |
| `bluffer` | 0.625000 | `{correct: 5, wrong: 3}` |

Both match `expected_fraction` (`run_matrix.py:61-100`) exactly. The memoriser's
0.875 rather than 0.500 is the interaction the docstring at `run_matrix.py:77-83`
predicts: it is right on all 4 replay items *and* on the 3 held-out items where
nothing happens.

---

## 3. A cheap examinee that beats the bluffer floor

Bluffer floor on this world: **5/8 = 0.625** (`unchanged_frame_share: 0.625`,
published in the paper's own notes).

Every strategy below reads **only** the sheet: `frame_before`, `action`,
`legend`, `grid`, `tags`, and the paper-level `world` block. None opens
`ground_truth.json`; none is given any item's truth.

| strategy | score | items | got `-003` (the `theory` item)? |
|---|---|---|---|
| bluffer (floor) | 5/8 = 0.625 | `+...++++` | no |
| tag-exploit: stasis on heldout, move on replay | 7/8 = 0.875 | `+++.++++` | **no** |
| **`move-if-floor` (legend only, no gravity)** | **7/8 = 0.875** | `++++++.+` | **yes** |
| `move-if-floor` + UP inert | **8/8 = 1.000** | `++++++++` | **yes** |
| rule-tag: `blocked_*`→stasis, else move | 7/8 = 0.875 | `++++++.+` | yes |
| `move-if-floor` + generic gravity settle | **8/8 = 1.000** | `++++++++` | **yes** |

`move-if-floor` is the whole strategy:

> Read `legend` for which integer is the agent, which is the floor. Find the
> agent. Compute the target cell one step in the direction named by `action`.
> If the target is off the grid, or does not hold the floor colour, return the
> input frame. Otherwise write the floor colour into the agent's old cell and
> the agent colour into the target, and return that.

**It scores 0.875 — equal to the memoriser, +0.25 over the floor — and it takes
the single `theory` item.** It has no model of this world: no gravity, no push,
no ledges, nothing read from the trace, nothing learned. It knows only that
grids usually have walls you cannot walk into, which the printed `legend` hands
it for free by naming colour 1 `"wall"` and colour 0 `"floor"`.

The one item it misses is `-006`, the `up_is_inert` case. Two different one-line
additions repair it to **8/8 = 1.000**, and both are justified by text the sheet
itself prints: the paper-level `world` block is
`{"world_id": "t2-gravity-push", "tier": 2, "families": ["gravity", "push"], "grid": [7,9]}`,
so the examinee is *told* the world has gravity. Either "if the world says
gravity, UP does not stick" or the generic "after moving, fall while the cell
below is floor" gets every item. So a **sheet-only strategy ties the oracle on
this paper.**

**The tag-exploit strategy is the control, and it fails.** Biasing toward
"nothing happens" on held-out items scores 7/8 but **loses `-003`** — it buys its
marks entirely on the replay side, where the tag is not what helped. Combined
with the exhaustive policy table in §1.3, the conclusion is that the 0.25 tag
bias is not the vulnerability on this world. The **legend** is.

### 3.1 A leak I was not asked to look for: the sheet names the rule

`Item.sheet_side()` (`exam/model.py:108-110`) publishes `tags` verbatim, and
`heldout_worldgen.py:204` sets `tags=(split, "rule:%s" % cand["rule"])`. So the
sheet an examinee receives contains, for every item:

```
…"points":1.0,"tags":["heldout","rule:blocked_by_wall"]},{"action":"LEFT"…
```

The paper deliberately withholds rule names elsewhere — `heldout_worldgen.py:238-241`
explains at length that `notes["quota"]` carries "Counts, not names. The rule
names are the answer vocabulary of the `by_rule` axis, and a sheet that lists
them hands the examinee the alphabet it is being asked to discover." The tag
hands over the alphabet *and* the per-item label.

On this world the tag is decisive for 4 of 8 items: `rule:blocked_by_wall` is a
rule whose `then` clause is "nothing changes", and I measured 0/71 of its
reachable transitions changing the frame. An examinee who guesses what the name
means answers those four with certainty and no reasoning.

**The exam's own gate catches this. It is never pointed at these papers.**
Running `leakage.check_paper(paper, sheet, key_doc=key)` by hand raises
`LeakageError` on **all 8 items**:

```
v2-heldout-t2-gravity-push leaks its own answers:
 [{'item_id': 't2-gravity-push-000', 'check': 'probe', 'hits': ['blocked_by_wall']},
  {'item_id': 't2-gravity-push-001', 'check': 'probe', 'hits': ['walk']}, … all 8 …]
```

Each item declares its own rule name as its leak probe
(`heldout_worldgen.py:203`, `leak_probes=(cand["rule"],)`), and
`leakage.probe_hits` (`exam/leakage.py:53-70`) finds it. The gate is not run
because it lives in `build_papers.build_one` (`exam/tools/build_papers.py:72`),
which iterates `BUILDERS` (`exam/papers/__init__.py:34-39`) —
`{heldout, handover, adaptation, verdict}`. `heldout_worldgen` is not in it: it
exposes `build_for(world_id)`, not `build()`. **All twenty worldgen papers bypass
the leakage gate.**

The suite has a substitute check that misses it by one character.
`test_worldgen_papers.py:70-87` asserts `'"%s"' % rule not in sheet` — the rule
name *wrapped in JSON quotes*. In the sheet the string is `"rule:walk"`, so
`"walk"` (quote, w, a, l, k, quote) is genuinely absent while `walk` is present:

```
rule 'blocked_by_wall':  "blocked_by_wall" in sheet -> False   <- what the test checks
                          blocked_by_wall  in sheet -> True    <- what leakage.probe_hits checks
rule 'walk':             "walk"            in sheet -> False
                          walk             in sheet -> True
```

The test's own docstring is right about the subtlety it *did* catch (a family
name like `push` is legitimately open because `spec.json` names it), and neither
`walk` nor `blocked_by_wall` appears in this world's `spec.json` — I checked.
The prefix `rule:` is the only reason the assertion passes.

---

## 4. Honest effective size

**Can this world rank two examinees apart? No.**

`discrimination.py:208` sets `effective_size = theory = 1`. Even taking that at
face value, one binary item cannot rank: two examinees who differ only in world
knowledge differ by at most 1 mark = 0.125 of the paper, and the evidence for the
difference is a single Bernoulli trial. Nothing survives that.

But 1 is too generous, and the module says so itself
(`discrimination.py:60-67`): "An item this file calls `theory` is one that those
three strategies do not settle — a fourth strategy nobody has written could
settle it for free, and the taxonomy would not notice." I wrote the fourth
strategy. Adding `move-if-floor` and `move-if-floor + UP-inert` as voters:

| item | oracle | memoriser | bluffer | heuristic | heuristic+UP-inert | 3-voter class |
|---|---|---|---|---|---|---|
| `-000` | correct | correct | correct | correct | correct | `free` |
| `-001` | correct | correct | wrong | correct | correct | `memorised` |
| `-002` | correct | correct | wrong | correct | correct | `memorised` |
| `-003` | correct | wrong | wrong | **correct** | **correct** | `theory` |
| `-004` | correct | correct | correct | correct | correct | `free` |
| `-005` | correct | correct | correct | correct | correct | `free` |
| `-006` | correct | correct | correct | wrong | correct | `free` |
| `-007` | correct | correct | correct | correct | correct | `free` |

**Theory items under the 5-voter taxonomy: 0 of 8.** One sheet-only examinee gets
all eight. **The honest effective size of `t2-gravity-push` is 0.**

### Should it be in the matrix?

**Not as a paper. Yes as a diagnostic.** Its `heldout` column cannot separate a
world-modeller from a legend-reader, and reporting it beside worlds that can will
drag any catalogue-level mean toward "the exam is easy" for the wrong reason. But
it is the world that makes two failures visible — the `up_is_inert`/`walk`
tagging collapse and the one-way-sink explorer strand — so deleting it would
delete the evidence. Keep the row, quote `effective_size: 0`, and stop quoting
`n_items: 8`.

### Rules that are dead weight

* **`blocked_by_wall` — dead weight, and not only here.** 0/71 reachable
  transitions change the frame. It cannot produce an informative item on *any*
  world, and it consumes `2 × per_class` = 4 of this paper's 8 slots. The
  instrument already names it (`summary.barren_rules: ["blocked_by_wall"]`) but
  its own `_world_summary` (`discrimination.py:194-196`) derives barrenness
  *empirically* from the sampled items rather than *a priori* from the rule's
  `then` clause. It should be excluded at `plan()` time, or given a separate quota
  so it cannot eat half a small paper.
* **`up_is_inert` masquerading as `walk` — worse than dead weight.** 6 of the 62
  held-out `walk` transitions are settle-back identities. They are tagged `walk`,
  counted toward `walk`'s quota, and then classify as `free`. They also produce
  the tag bias and the `axes()["by_rule"]["walk"]` gap. The rule table's own
  reasoning for making cascades untagged (`GROUND_TRUTH.md` line 20) is sound for
  the *trace*; it is wrong for the *quota*, where it silently mixes a
  frame-changing class with an identity class under one name.
* **`push` and `blocked_by_block` — the two rules that matter, unexaminable.**
  Not dead weight; excluded weight. Together they are the only mechanism on this
  world whose prediction requires modelling anything beyond "walls stop you".

### What would have to change in `worldgen/` for this world to carry a real paper

In rough order of how much it fixes:

1. **The explorer must not strand itself.** `worldgen/core/explorer.py:49-79`
   greedily walks to the *nearest* uncovered `(state, action)` pair. On a layered
   world with one-way falls that is exactly the wrong heuristic: it takes the
   cheap descent and permanently forfeits everything above it. I confirmed the
   consequence at `budget=None`: the exhaustive walk is 46 actions, witnesses only
   `walk` and `blocked_by_wall`, and never once pushes the block. Cost the
   candidate pair by *reachability lost* (pairs that become unreachable if you
   take this action) as well as by distance, or run the walk over the DAG of
   strongly-connected components top-down. Until this changes, **no budget setting
   gives this world a push in its trace**, which is a much stronger statement than
   "the trace is short".
2. **`push` needs more than 2 reachable transitions.** Even a perfect explorer
   would find only 2, and the matched quota needs `per_class` inside *and*
   `per_class` outside — so at `per_class=2`, `push` is unqualifiable in principle
   here. The spec has one block at (3,5) on a corridor with two free cells to its
   right. A second block, or a block on the row-5 corridor (7 free cells), would
   raise the count into double digits.
3. **`up_is_inert` should carry its own tag.** Splitting it out of `walk` would
   drop `walk`'s frame-changing share from 0.909 to 1.000, take the realised tag
   bias to 0.000, and stop the quota mixing two classes under one name. It would
   also give the cascade a rule row that `by_rule` can report, which is what a
   reader of the axes actually wants.
4. **Publish the rule's `then` clause on the truth side** so `plan()` can refuse
   no-op rules (`then == "nothing changes"`) instead of the exam discovering their
   barrenness after the fact.

Items 1 and 3 are the ones that would move this world's effective size off zero;
item 2 is what would make it a *tier-2* paper rather than a tier-1 one.

---

## Appendix — what I found that was not asked for

1. **The sheet leaks the ground-truth rule name on every item of every worldgen
   paper** (`exam/model.py:108-110` + `heldout_worldgen.py:204`), the leakage gate
   catches it and raises on all 8 items here, and the gate is never run on this
   paper type because `heldout_worldgen` is absent from `BUILDERS`
   (`exam/papers/__init__.py:34-39`). §3.1.
2. **The substitute test misses it by one character.**
   `test_worldgen_papers.py:70-87` searches for the JSON-quoted `"walk"`; the tag
   is `"rule:walk"`. §3.1. This affects all twenty worlds, not just this one.
3. **`tag_bias` cannot resolve below 0.25 on an 8-item paper.** The world is
   pinned exactly on the ≤0.25 assertion at `test_worldgen_papers.py:123` partly
   because 0.25 is the metric's quantisation step at 4 items per split. Expected
   bias from the pools is 0.048. §1.3.
4. **The advertised tag exploit is worth 0.000 marks.** Exhaustive policy search;
   stasis is the majority answer in both splits, so the tag can never pay. §1.3.
5. **No trace budget can fix this world.** The exhaustive 46-action walk witnesses
   `push` zero times. §1.2. This is a property of the greedy explorer meeting a
   one-way world, and it will recur on every gravity/ledge world in the catalogue.
6. **Integral floats (`1.0`) are graded `wrong`**, and malformed answers share the
   `wrong` verdict with genuine mis-predictions. §2.1(i)–(ii).
7. **`theory_share` peaks at `per_class=1`, not at larger quotas**: 0.250 / 0.125 /
   0.167 / 0.188 for `per_class` 1 / 2 / 3 / 4. Growing the paper dilutes it,
   because `blocked_by_wall` grows at exactly the same rate as `walk` while
   contributing nothing.
