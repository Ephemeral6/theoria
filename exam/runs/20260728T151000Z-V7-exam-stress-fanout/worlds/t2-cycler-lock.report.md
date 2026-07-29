# Independent examination — `t2-cycler-lock`

Examiner: independent audit of `exam/tools/discrimination.py`'s profile at
`exam/runs/20260728T151000Z-V7-exam-stress-fanout/worlds/t2-cycler-lock.json`.
Read-only on every existing file. No network, no LLM, no `git`, no `pytest`.

**Headline.** The instrument's classification is *arithmetically correct* — I
re-derived every item from the spec and all twelve labels hold. But the class it
calls `theory` does not mean what the name promises on this world: a
twenty-line, frame-only answer strategy that holds no model of the cycler, the
lock or the token counter scores **12/12**, taking all four `theory` items and
all four `memorised` ones. The honest effective size of this paper is **0**, not
4.

---

## 1. Is the classification true of this world's actual mechanics?

### Method

I reimplemented the transition relation from `worldgen/out/worlds/t2-cycler-lock/spec.json`
plus the two mechanism docstrings (`worldgen/mechanisms/color_cycle.py:101-116`,
`worldgen/mechanisms/count_lock.py:102-122`) **without importing
`worldgen/core/world.py`**, then compared. The check is therefore independent of
the code that produced the artefacts.

Board (5×9), from `spec.json`:

```
#########      agent start (1,1)      cycler (3,2)  k=2 open_phase=1 phase0=0
#.......#      goal        (3,7)      lock   (3,4)  k=2
#.#####.#      tokens (1,4) (1,7)     palette: floor 0 wall 1 token 2
#.......#                                      lock 3 cycler 4 cycler_1 5 agent 6
#########
```

### Result — the world reproduces exactly

| quantity | shipped | my re-derivation |
|---|---|---|
| reachable states | 61 (`ground_truth.json:288`) | 61 |
| distinct frames | 61, injective (`ground_truth.json:8-13`) | 61, 0 collisions |
| `blocked_by_wall` transitions | 122 | 122 |
| `walk` | 102 | 102 |
| `walk_through_cycler` | 6 | 6 |
| `advance_cycler` | 4 | 4 |
| `collect_token` | 4 | 4 |
| `walk_through_lock` | 4 | 4 |
| `blocked_by_lock` | 2 | 2 |

All **12** items check out: recomputed `frame_after` equals the recorded
`frame_after`, the recomputed rule name equals the recorded `rule`, and the
recomputed `frame_changes` flag equals the profile's.

| item | action | rule | split | class | frame changes | verified |
|---|---|---|---|---|---|---|
| `t2-cycler-lock-000` | DOWN | `blocked_by_wall` | heldout | free | no | ✓ agent (3,5), target (4,5) is wall row |
| `t2-cycler-lock-001` | RIGHT | `walk_through_cycler` | replay | memorised | yes | ✓ agent (3,1)→(3,2), cycler shows 5 = open |
| `t2-cycler-lock-002` | UP | `walk` | replay | memorised | yes | ✓ agent (2,1)→(1,1) |
| `t2-cycler-lock-003` | RIGHT | `blocked_by_wall` | replay | free | no | ✓ agent (2,1), target (2,2) is wall |
| `t2-cycler-lock-004` | LEFT | `blocked_by_wall` | replay | free | no | ✓ agent (2,1), target (2,0) is wall |
| `t2-cycler-lock-005` | RIGHT | `walk_through_cycler` | replay | memorised | yes | ✓ agent (3,1)→(3,2) |
| `t2-cycler-lock-006` | LEFT | `walk_through_cycler` | heldout | **theory** | yes | ✓ agent (3,3)→(3,2), phase unchanged |
| `t2-cycler-lock-007` | RIGHT | `walk` | heldout | **theory** | yes | ✓ agent (1,1)→(1,2) |
| `t2-cycler-lock-008` | UP | `walk` | replay | memorised | yes | ✓ agent (2,1)→(1,1) |
| `t2-cycler-lock-009` | UP | `blocked_by_wall` | heldout | free | no | ✓ agent (1,1), target (0,1) is wall |
| `t2-cycler-lock-010` | LEFT | `walk` | heldout | **theory** | yes | ✓ agent (1,6)→(1,5) |
| `t2-cycler-lock-011` | LEFT | `walk_through_cycler` | heldout | **theory** | yes | ✓ agent (3,3)→(3,2) |

**No `free` item changes the frame** (000, 003, 004, 009 are all
`blocked_by_wall` and all frame-static) and **no `theory` item is static**
(006, 007, 010, 011 all move the agent). On that test the instrument is clean:
zero anomalies, zero dead items, zero disagreements with the world.

### Hidden state — the distinction you asked for, made explicitly

**No item on this paper depends on state the examinee cannot see. Every one is a
hard question, not an unanswerable one.** Three separate checks:

1. `(frame_before, action) → frame_after` is a **function** over the entire
   reachable relation: I enumerated all 61×4 = 244 transitions keyed by rendered
   frame and found **0 ambiguities**. Two states never disagree about what a
   given action does.
2. The one structural way this world could hide a phase — the agent standing on
   the cycler, where `render()` paints the agent last
   (`worldgen/core/world.py:238`) and the colour stops reading the phase
   (`ground_truth.json:41-46`, invariant `color_reads_phase`, which explicitly
   exempts the agent's cell) — **never produces an ambiguity here**. There are
   3 reachable states with the agent on (3,2) and in all 3 the phase is 1.
   States with the agent covering a *shut* cycler: **0**. The reason is
   mechanical: `advance_cycler` does not move the agent
   (`color_cycle.py:112-116`), so the only way onto the cell is
   `walk_through_cycler`, which requires phase == open_phase.
3. The lock's count is likewise never hidden. The agent is on (3,4) in 2 states,
   both with collected == 2; and an open lock renders as floor
   (`count_lock.py:133-139`), so a `0` at (3,4) is unambiguous given the fixed
   entity layout.

So the "time-varying cycler composed with a lock" is, on this paper, fully
observable. That is a property of *this* world, not of the composition: the
composition supplies the machinery for an unanswerable item and the geometry
happens to keep it out of reach.

**One latent case worth naming.** The six `walk` transitions that vacate the
cycler cell (3,2) require repainting it `5`, which is knowledge about what lies
*under* the agent — the only frame-only-hard transitions this world has. None of
them was drawn: no item's `frame_before` has the agent at (3,2). See §3.

### Verdict on Q1

The classification is true of the mechanics. **No defect in the instrument on
this world.** What is wrong is not the labelling but the meaning of the label —
§3.

---

## 2. Does the marker misjudge anything?

Stressed by importing `exam/grading/rubrics_heldout.py` and calling
`grade_frame_exact` directly on items 000 (free/static), 002 (memorised) and
011 (theory). The rubric was not edited. Every case below was run on all three
items and gave the same verdict on each.

| answer | verdict | pts | fair? |
|---|---|---|---|
| exact bare grid | `correct` | 1.0 | ✓ |
| `{"frame_after": grid}` | `correct` | 1.0 | ✓ |
| `{"frame": grid}` / `{"after": grid}` | `correct` | 1.0 | ✓ (lenient — see below) |
| rows as tuples | `correct` | 1.0 | ✓ |
| `{"abstain": false, "frame_after": grid}` | `correct` | 1.0 | ✓ |
| transposed (9×5) | `wrong` | 0.0 | ✓ (`shape_ok=False, cells_wrong=-1`) |
| one cell changed | `wrong` | 0.0 | ✓ (`cells_wrong=1`, reported, never paid) |
| ragged row | `wrong` | 0.0 | ✓ |
| short grid (4 rows) | `wrong` | 0.0 | ✓ |
| correct grid + extra `[0]*9` row | `wrong` | 0.0 | ✓ |
| colour `7` (off palette) | `wrong` | 0.0 | ✓ |
| colour `8` (A0's default palette, not this world's) | `wrong` | 0.0 | ✓ |
| nested one level too deep `[grid]` | `wrong` | 0.0 | ✓ |
| `{"abstain": true}` | `abstained` | 0.0 | ✓ |
| `{"abstain": true, "frame_after": grid}` | `abstained` | 0.0 | ✓ |
| `"abstain"` / `"abstained"` / `"unknown"` / `"I cannot tell"` | `abstained` | 0.0 | ✓ |
| `None` | `unanswered` | 0.0 | ✓ |
| item omitted from the submission | `unanswered` | 0.0 | ✓ (`mark.py:51-52`) |
| **`{}`** | **`wrong`** | 0.0 | **✗ arguably** |
| **`[]`** | **`wrong`** | 0.0 | **✗ arguably** |
| **strings not ints** `[["1",...]]` | **`wrong`** | 0.0 | **✗ arguably** |
| **floats not ints** `[[1.0,...]]` | **`wrong`** | 0.0 | **✗ arguably** |
| **booleans** | **`wrong`** | 0.0 | ✓ (documented, `rubrics_heldout.py:103-105`) |
| **`{"abstain": 1}`** | **`wrong`** | 0.0 | **✗ arguably** |
| **`{"abstain": "yes"}`** | **`wrong`** | 0.0 | **✗ arguably** |
| **`{"abstention": true}`** | **`wrong`** | 0.0 | **✗ arguably** |
| **`"I can't tell"`** | **`wrong`** | 0.0 | **✗ arguably** |
| **`"I do not know"`** | **`wrong`** | 0.0 | **✗ arguably** |
| `{"frame_after": null}` | `wrong` | 0.0 | borderline |
| grid as a text block `"111111111\n…"` | `wrong` | 0.0 | ✓ (instructions say list of rows of ints) |

**Nothing scores a point it should not, and ground truth is never rejected.**
The complaints are all about the *verdict vocabulary*, not the mark. Three of
them, stated concretely:

**(a) A perfect prediction in the wrong datatype reads as no theory at all.**
An examinee that predicts all twelve frames correctly and serialises cells as
`"6"` instead of `6` scores **0/12**, and every one of those zeros lands in the
`wrong` bucket, which flows into `axes["by_rule"][*]["gap"]`
(`heldout_worldgen.py:338-341`) as though the examinee mis-modelled the rule. A
fair examiner would say: *correct prediction, rejected on format* — a fourth
outcome distinguishable from a wrong one. The rubric's own docstring
(`rubrics_heldout.py:8-12`) argues that a near-miss must not read as "nearly
right"; the symmetric hazard, a right answer reading as "no idea", is not
guarded. `VERDICTS` has no `malformed` member, so the rubric has nowhere to put
it. Same argument for `[[1.0, …]]`.

**(b) Three ways of submitting nothing split across two verdicts.** `None` →
`unanswered`; `{}` → `wrong`; `[]` → `wrong`. `_as_frame`
(`rubrics_heldout.py:87-95`) returns `None` for a dict with no recognised field
and for an empty list, and `grade_frame_exact:149-154` turns every `None` frame
into `wrong`. A fair examiner would call all three "nothing submitted". This
directly corrupts `axes["unanswered"]` (`heldout_worldgen.py:343`), the
statistic that exists to prove silence is not being paid — an examinee that
submits `{}` for every item is recorded as having made twelve wrong predictions.

**(c) The apostrophe is load-bearing in abstention detection.**
`_is_abstention` (`rubrics_heldout.py:115-121`) matches exactly four spellings.
`"I cannot tell"` abstains; `"I can't tell"` is `wrong`. `"unknown"` abstains;
`"I do not know"` is `wrong`. `{"abstain": true}` abstains; `{"abstain": 1}`,
`{"abstain": "yes"}` and `{"abstention": true}` are `wrong`. A fair examiner
reads all of these as declining to predict. Zero points either way, but the
`abstained` count is exactly the evidence for "the framework knew it did not
know", and it is decided by string equality.

**Minor leniency, no harm on this world:** `_as_frame:88` accepts `{"frame":…}`
and `{"after":…}` although the printed instructions
(`heldout_worldgen.py:212-218`) promise only `frame_after`, and it recurses, so
`{"frame_after": {"frame_after": grid}}` scores `correct`. Undocumented on the
sheet; strictly generous, so it cannot depress a score.

### The two structural invariants

Confirmed on this world, by marking all four reference examinees:

| examinee | score | verdicts |
|---|---|---|
| `oracle` | **1.0000** | `correct` × 12, **`wrong` × 0** |
| `null` | 0.0000 | **`unanswered` × 12**, `correct` × 0 |
| `memoriser` | 0.6667 | correct 8, wrong 4 |
| `bluffer` | 0.3333 | correct 4, wrong 8 |

**Silence is never paid** and **ground truth is never marked wrong.** Both hold.

---

## 3. A cheap examinee that beats the bluffer floor — and beats everything else

The bluffer floor here is 4/12 = **0.3333** (the four `blocked_by_wall` items).

### The strategy

It may read `frame_before`, `action`, `legend`, `grid`. It may not read
`ground_truth.json`, `Item.truth`, or the key. It holds no rule table.

```
find the unique cell whose colour == legend["agent"]
target = that cell + direction(action)
if target is off the grid:                 predict frame unchanged
if frame[target] == legend["wall"]:        predict frame unchanged
otherwise:                                 paint the old cell legend["floor"]
                                           paint the target legend["agent"]
```

The direction map is **induced from the published `raw_trace.jsonl`**, not
assumed — comparing agent positions across consecutive trace frames yields
`{UP:(-1,0), DOWN:(1,0), LEFT:(0,-1), RIGHT:(0,1)}` uniquely, from an open file.
Nothing world-specific is used: only `agent`, `wall` and `floor`, which are
renderer constants across the whole factory (`worldgen_port.py:167-170`).

### Score

| strategy | score | free | memorised | theory | replay | heldout | gap |
|---|---|---|---|---|---|---|---|
| bluffer (the floor) | 4/12 = **0.3333** | 4/4 | 0/4 | 0/4 | 0.333 | 0.333 | 0.000 |
| move only onto `floor` | 8/12 = **0.6667** | 4/4 | 2/4 | 2/4 | 0.667 | 0.667 | 0.000 |
| **move onto anything not a wall** | 12/12 = **1.0000** | 4/4 | 4/4 | **4/4** | 1.000 | 1.000 | 0.000 |

The `not-a-wall` prior **captures 100 % of the `theory` residue** — items 006,
007, 010, 011 — and matches the oracle exactly on every item. Its
`gap_replay_minus_heldout` is 0.000, i.e. it looks like a perfect rule-learner
on the axis this question type exists to measure
(`heldout_worldgen.py:303-309`).

The intermediate `floor-only` variant already beats the floor at 0.6667 and
takes 2 of the 4 theory items (007, 010 — plain walks), so even a strategy that
refuses to guess about coloured cells doubles the floor.

### Proof that it is not a world model

Scored against the **full** reachable relation rather than the paper:

| rule | transitions | prior gets wrong |
|---|---|---|
| `blocked_by_wall` | 122 | 0 |
| `walk` | 102 | **6** |
| `walk_through_cycler` | 6 | 0 |
| `walk_through_lock` | 4 | 0 |
| `collect_token` | 4 | **2** |
| `advance_cycler` | 4 | **4** |
| `blocked_by_lock` | 2 | **2** |
| **total** | **244** | **14** (94.3 % correct) |

It has no notion of phase (it is wrong on 4/4 `advance_cycler`), no notion of the
counter (wrong on 2/2 `blocked_by_lock`, and on the 2 `collect_token`
transitions where taking the second token opens the lock and changes (3,4) from
`3` to `0`), and no notion of what lies under the agent (wrong on the 6 `walk`
transitions that vacate the cycler cell (3,2), which must be repainted `5`).

**The paper draws none of those 14.** The six hard walks all have the agent at
(3,2); every one of the paper's twelve items has the agent at (3,5), (3,1),
(2,1), (3,3), (1,1) or (1,6). That is hash accident, not design: `_pick`
(`heldout_worldgen.py:113-116`) takes the two lowest salted hashes from pools of
24 replay / 78 heldout `walk` candidates, and the 2/24 and 4/78 hard ones did not
come up.

### Corroboration already on disk

`exam/runs/20260728T151000Z-V7-exam-stress-fanout/prior_sweep.json` runs the
same "walk-or-wall" prior over all twenty worlds and independently records
`t2-cycler-lock` at `prior: 1.0`, one of 12 worlds of 20 scoring 1.000. My
result is the per-item version of that line.

---

## 4. The world's honest effective size

**Zero.** Not four.

`discrimination.py:208` publishes `effective_size = theory = 4`. That number is
correct under its own definition — the three voters do not settle those items —
but the module's own docstring anticipates the failure
(`discrimination.py:60-67`): *"a fourth strategy nobody has written could settle
it for free, and the taxonomy would not notice."* On this world that fourth
strategy is twenty lines long and settles all four.

### Which rules are dead weight, and why

**Examined (3 of 7):**

* **`blocked_by_wall`** — 4 items, all `free`. Already flagged
  `barren_rules: ["blocked_by_wall"]`. Nothing changes; the bluffer has it.
* **`walk`** — 4 items (2 memorised, 2 theory). Dead weight *against the prior*:
  the only `walk` transitions on this board that need a world model are the six
  that vacate the cycler cell, and none were drawn. The four drawn are
  agent-moves-onto-empty-floor.
* **`walk_through_cycler`** — 4 items (2 memorised, 2 theory). This is the
  world's headline mechanism and it contributes nothing. All four items
  (001, 005, 006, 011) show the cycler **already open**, colour `5`, and the
  correct answer is "the agent moves in". To an examinee that treats every
  non-wall cell as enterable, an open cycler is indistinguishable from floor.
  Not one item shows the cycler shut. `discrimination.py:195-196` does not flag
  this rule as barren, because barrenness is defined against the three voters
  only — the rule looks productive (2 memorised + 2 theory) while discriminating
  nobody.

**Excluded by the matched quota (4 of 7)** — `plan()` reports these as blocked
at `per_class=2` (`heldout_worldgen.py:130-137`):

| rule | in trace | held out | why excluded |
|---|---|---|---|
| `advance_cycler` | 1 | 3 | trace witnessed it once — the A0′ failure mode, and `reversibility.json` scores it `max_witnesses: 1` |
| `collect_token` | 1 | 3 | same |
| `walk_through_lock` | 0 | 4 | trace never witnessed it — no replay control |
| `blocked_by_lock` | 0 | 2 | same |

**These four are exactly the rules that carry the cycler and the lock.** The
paper is a matched-quota exam over three movement rules, in a world whose whole
reason to exist is "one reversible gate and one monotone one, side by side"
(`spec.json:68`). The mechanisms named in `families` — `color_cycle`,
`count_lock` — are represented in the exam only by their trivial passable case.

### Is the residue large enough to rank two examinees apart?

No, on two counts.

1. **Against the prior, the residue is empty.** Two examinees that both hold
   "the agent moves unless a wall stops it" both score 12/12 and are
   unrankable. That prior is the default hypothesis for any grid world; an
   examinee is far more likely to hold it than not.
2. **Even taking `theory = 4` at face value**, one item is 8.3 points of the
   twelve-item total and the theory band spans only 33.3 points. Nothing finer
   than "got 3 of 4 vs 4 of 4" is expressible, and with n = 4 binary items that
   difference is not distinguishable from noise by any test.

### The per_class trap (not asked, but it inverts the obvious fix)

Raising `per_class` makes this world **less** informative, because the quota rule
trades rule coverage for item count:

| `per_class` | usable rules | items | bluffer | cheap prior |
|---|---|---|---|---|
| 1 | 5 | 10 | 2/10 = 0.200 | **8/10 = 0.800** |
| 2 (default) | 3 | 12 | 4/12 = 0.333 | 12/12 = 1.000 |
| 3 | 2 | 12 | 6/12 = 0.500 | 12/12 = 1.000 |
| 4 | 2 | 16 | 8/16 = 0.500 | 16/16 = 1.000 |
| 5 | 2 | 20 | 10/20 = 0.500 | 20/20 = 1.000 |
| 6 | 2 | 24 | 12/24 = 0.500 | 24/24 = 1.000 |

`per_class=1` is the **only** setting at which this world examines anything: it
admits `advance_cycler` and `collect_token`, and the prior drops to 0.800. At
`per_class ≥ 3` even `walk_through_cycler` falls out (replay pool = 2) and the
paper is `blocked_by_wall` + `walk` alone. A bigger paper here is a strictly
emptier one.

---

## What I found that you did not ask about

1. **`walk_through_cycler` is a false positive for the `barren_rules` test.**
   `_world_summary` (`discrimination.py:194-196`) calls a rule barren only when
   it yields no `theory` and no `memorised` item. On this world the rule yields
   2 of each and is not flagged, while discriminating nobody against a
   theory-free prior. Suggest defining barrenness against the prior as well.

2. **A fourth voter would fix the taxonomy cheaply.** `VOTERS`
   (`discrimination.py:87`) is `(oracle, memoriser, bluffer)`. Adding the
   walk-or-wall prior already implemented in `prior_sweep.py` and requiring it to
   be *wrong* before an item may be called `theory` would reclassify all 12 items
   on this world as zero-discrimination and make `effective_size` mean what its
   comment (`discrimination.py:206-208`) says it means.

3. **Item selection could be stratified against the prior instead of by hash.**
   This world contains 14 prior-defeating transitions; 6 of them are `walk`
   transitions inside a pool the paper already samples (2 replay of 24, 4 heldout
   of 78). Preferring candidates the prior gets wrong would turn this paper from
   effective size 0 into effective size 4 without touching the quota rule, the
   split rule, or the rubric.

4. **Mislabelled statistic in `axes`.** `heldout_worldgen.py:332-334` binds a
   variable named `unchanged` to *"items whose truth has a non-null
   `frame_after`"* — which is every item — and publishes it as
   `axes["items"] = 12`. The key is right; the name has never counted anything
   unchanged, and there is no unchanged-count in `axes` at all (the share lives
   separately in `Paper.notes["unchanged_frame_share"]`, `:249`). Cosmetic, but
   it is the kind of name a later reader will trust.

5. **The one genuinely hard question this world can ask is never asked.**
   "What colour is under the agent when it steps off the cycler?" is the only
   frame-only-hard `walk` on the board (6 transitions, agent at (3,2), answer
   `5` not `0`). It needs the phase rule, it is answerable from the printed
   frame, and it defeats the prior. It is a better item than any of the four the
   paper calls `theory`.

---

## Files consulted

* `exam/runs/20260728T151000Z-V7-exam-stress-fanout/worlds/t2-cycler-lock.json`
* `exam/tools/discrimination.py`
* `exam/papers/heldout_worldgen.py`, `exam/papers/worldgen_port.py`
* `exam/grading/rubrics_heldout.py`, `exam/grading/mark.py`
* `worldgen/out/worlds/t2-cycler-lock/spec.json`, `ground_truth.json`,
  `raw_trace.jsonl`, `GROUND_TRUTH.md`
* `worldgen/core/world.py`, `worldgen/mechanisms/{color_cycle,count_lock}.py`
* `exam/runs/20260728T151000Z-V7-exam-stress-fanout/prior_sweep.json`

Nothing under `arc-recon/` was opened. No file outside this report was created
or modified.
