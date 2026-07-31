# Examiner's report — `t1-switch-latch`

Independent audit of the discrimination profile at
`exam/runs/20260728T151000Z-V7-exam-stress-fanout/worlds/t1-switch-latch.json`.
Everything below was recomputed locally from `spec.json` + `raw_trace.jsonl` +
`ground_truth.json`; no file outside this report was written and no source was
edited. Paper: `v2-heldout-t1-switch-latch`, 12 items, `per_class=2`,
`rubric_digest e06bdf52…1cb091`.

**Headline.** The instrument is correct — every label it assigns is true of the
world's actual mechanics, and the marker is fair on every probe that matters.
But the profile's `effective_size: 4` is an overstatement, and the honest number
is **0**. A 20-line strategy that reads nothing but the sheet scores **12/12**,
including all four items the instrument calls `theory`. The reason is
structural, not accidental, and it is stated in §3 and §4.

---

## 1. Is the classification true of this world's mechanics?

**Yes. All twelve items were hand-checked, not a sample** — the paper is small
enough that a sample would have been a false economy.

The world (`worldgen/out/worlds/t1-switch-latch/spec.json`): 6×7 grid, walls on
the border plus `(1,4) (2,4) (4,4)`; agent starts `(1,2)`; goal `(4,5)` (never
painted); one **latch** switch at `(4,1)` on net `a`; two doors at `(3,4)` and
`(4,2)`, both `open_when_on` on net `a`. Palette
`{floor:0, wall:1, switch:2, switch_on:3, door:4, agent:6}`. Net `a` is on iff
the latch bit is 1 (`worldgen/mechanisms/switch_door.py:76-87`); an open door is
**not drawn at all** and its cell renders as floor
(`worldgen/mechanisms/switch_door.py:173-180`, the `continue` at :177-178).

Each row below: I read the switch bit off cell `(4,1)` (2 = off, 3 = on),
located the agent, applied `shift`, and re-derived the outcome by
`GridWorld.explain` (`worldgen/core/world.py:188-219`) — bounds/wall first, then
the `switch_door` claim, then the default `walk`.

| item | split | agent | act | target | target content | rule I derive | recorded rule | frame changes | class | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| `-000` | heldout | (1,1) | DOWN | (2,1) | floor | `walk` | `walk` | yes | theory | ✅ |
| `-001` | heldout | (1,3) | RIGHT | (1,4) | wall | `blocked_by_wall` | `blocked_by_wall` | **no** | free | ✅ |
| `-002` | replay | (3,1) | LEFT | (3,0) | wall | `blocked_by_wall` | `blocked_by_wall` | **no** | free | ✅ |
| `-003` | replay | (2,1) | RIGHT | (2,2) | floor | `walk` | `walk` | yes | memorised | ✅ |
| `-004` | replay | (3,2) | DOWN | (4,2) | door, net on → open | `walk_through_door` | `walk_through_door` | yes | memorised | ✅ |
| `-005` | heldout | (3,5) | DOWN | (4,5) | floor (the goal) | `walk` | `walk` | yes | theory | ✅ |
| `-006` | heldout | (2,3) | RIGHT | (2,4) | wall | `blocked_by_wall` | `blocked_by_wall` | **no** | free | ✅ |
| `-007` | replay | (4,3) | DOWN | (5,3) | wall | `blocked_by_wall` | `blocked_by_wall` | **no** | free | ✅ |
| `-008` | replay | (2,2) | DOWN | (3,2) | floor | `walk` | `walk` | yes | memorised | ✅ |
| `-009` | heldout | (3,3) | RIGHT | (3,4) | door, net on → open | `walk_through_door` | `walk_through_door` | yes | theory | ✅ |
| `-010` | replay | (4,3) | LEFT | (4,2) | door, net on → open | `walk_through_door` | `walk_through_door` | yes | memorised | ✅ |
| `-011` | heldout | (3,5) | LEFT | (3,4) | door, net on → open | `walk_through_door` | `walk_through_door` | yes | theory | ✅ |

For every row the recorded `frame_after` is byte-identical to the frame I
derived. Two spot examples in full:

* `-009` before, row 3 = `1 0 0 6 0 0 1`; switch cell `(4,1)` = 3, so net `a` is
  on, so the `(3,4)` door is open and renders 0. `RIGHT` from `(3,3)` targets a
  door the net makes passable → `walk_through_door`, agent to `(3,4)`. Recorded
  after, row 3 = `1 0 0 0 6 0 1`. ✅
* `-006` before, row 4 = `1 2 4 0 1 0 1`; switch is 2 (off), so both doors are
  drawn 4 and closed. `RIGHT` from `(2,3)` targets `(2,4)`, a `#`. Bounds/wall
  test fires before any mechanism is offered the cell → `blocked_by_wall`,
  nothing changes. ✅

**The two defect conditions you asked me to look for are both absent.**

* Every `free` item (`-001 -002 -006 -007`) has `frame_after == frame_before`,
  cell for cell. None of them changes the frame.
* Every `theory` item (`-000 -005 -009 -011`) does change the frame.
* `dead: 0` and `anomalies: []` are confirmed — the oracle is `correct` on all
  twelve (§2), so no triple `(False,·,·)` is reachable here.
* The profile's `frame_changes` field agrees with my recomputation on all 12
  items, and `by_rule` / `by_split` / `by_class` counts reproduce exactly.

The four-way taxonomy in `exam/tools/discrimination.py:95-114` is therefore a
faithful report of what the three voters do. **The caveat is not that the
labels are wrong; it is what `theory` is taken to mean.** See §3.

## 2. Does the marker misjudge anything on this world?

`exam/grading/rubrics_heldout.py`, exercised by importing `grade_frame_exact`
directly on items `-000` (theory/`walk`), `-001` (free/`blocked_by_wall`),
`-004` (memorised/`walk_through_door`) and `-009` (theory/`walk_through_door`).
Identical verdicts on all four items for every probe, so the table is collapsed.

| probe | verdict | detail | fair? |
|---|---|---|---|
| exact grid, bare | `correct` | `cells_wrong 0` | ✅ |
| exact, `{"frame_after": …}` | `correct` | | ✅ |
| exact, `{"frame": …}` / `{"after": …}` | `correct` | | ✅ (undocumented bonus, see below) |
| exact, tuple-of-tuples | `correct` | | ✅ |
| **transposed** (7×6) | `wrong` | `shape_ok False, cells_wrong -1` | ✅ |
| one cell changed (legal colour) | `wrong` | `shape_ok True, cells_wrong 1` | ✅ |
| short grid (5 rows × 7) | `wrong` | `shape_ok False, cells_wrong -1` | ✅ |
| ragged row | `wrong` | `not a well-formed frame` | ✅ |
| colour `8` (outside this palette) | `wrong` | `not a well-formed frame` | ✅ |
| booleans instead of ints | `wrong` | `not a well-formed frame` | ✅ |
| `{"abstain": true}` | `abstained` | 0 points | ✅ |
| `"abstain"` (string) | `abstained` | | ✅ |
| `null` | `unanswered` | `why: null answer` | ✅ |
| **`{}` (empty dict)** | `wrong` | `not a well-formed frame` | ⚠️ arguable |
| **`[]` (empty list)** | `wrong` | `not a well-formed frame` | ⚠️ arguable |
| **`{"frame_after": null}`** | `wrong` | `not a well-formed frame` | ⚠️ arguable |
| **cells as strings `"6"`** | `wrong` | `not a well-formed frame` | ⚠️ arguable |
| **cells as floats `6.0`** | `wrong` | `not a well-formed frame` | ⚠️ arguable |
| JSON *string* of the correct grid | `wrong` | `not a well-formed frame` | ⚠️ arguable |
| `{"answer": {"frame_after": …}}` (nested) | `wrong` | `not a well-formed frame` | ⚠️ arguable |
| `{"abstain": true, "frame_after": <correct>}` | `abstained` | | ⚠️ arguable |

Four findings, in descending order of how much I would want them fixed. None is
a scoring error on this world for any of the four synthetic examinees; all are
about how a *real* examinee's near-miss would be reported.

**(a) `{}` and `[]` are marked `wrong`, but `null` is marked `unanswered`.**
`rubrics_heldout.py:138-142` catches `None` and returns `unanswered`;
`_as_frame` (`:75-112`) returns `None` for an empty dict (falls through the
field loop to `:91`) and for an empty list (`:94`), which then lands on the
malformed branch at `:149-154` and scores `wrong`. All three are the same act —
the examinee submitted nothing — and a fair examiner would call all three
`unanswered`. The consequence is not cosmetic: the module docstring of
`mark.py:9-13` says the distinction exists precisely because "an arm with no
deliverable … is a finding, not a failure to answer", and an arm whose harness
emits `{}` for a missing prediction is silently reclassified from *finding* to
*failure*. **This does not break the "silence is never paid" invariant** — all
three score 0.0 — it corrupts the diagnosis, not the mark.

**(b) `{"frame_after": null}` → `wrong`.** Same category as (a): an explicit
"I produced no frame" inside the promised wrapper. A fair examiner: `unanswered`.

**(c) Serialisation misses and prediction errors are the same verdict.** Cells
as `"6"` (strings), as `6.0` (floats), the whole grid as a JSON string, or the
grid nested one level deeper all return `wrong` with
`why: "answer is not a well-formed frame"`. The paper's instructions
(`heldout_worldgen.py:213-218`) do say "a list of rows of integers", so refusing
these is defensible and the `detail` string does distinguish them for anyone
reading item-level output. But `wrong` is the same verdict a substantively wrong
prediction gets, and the rubric's own docstring (`:5-14`) argues at length that
a nearly-right theory must not read as nearly right — the symmetric hazard is
that a *right* theory with a JSON habit reads as wrong. A fair examiner would
give these a distinct verdict (`malformed`), or at minimum the report would
surface the malformed count separately. The float case is the weakest of the
three to refuse: JSON `6.0` and `6` denote the same integer, and
`rubrics_heldout.py:104` rejects it under a comment written to catch `bool`, not
`float`. I would call the float case a genuine, if small, misjudgement.

**(d) Abstention outranks a correct answer.** `_is_abstention` is tested first
(`:144`), so `{"abstain": true, "frame_after": <the correct grid>}` scores 0 and
is recorded `abstained`. Defensible (an examinee that says it cannot tell should
be taken at its word) but it is a rule nobody has written down; the instructions
present abstention and a frame as alternatives, not as a precedence.

**Two things the marker gets right that are worth naming rather than assuming.**
The truth-side palette override works: `legal_cells` for this world is
`(0,1,2,3,4,6)`, and the correct frame — which contains `1`, `3` and `6`, none
of which is in the default `_LEGAL_CELLS = {0,2,4,8}` at `:56` — is accepted.
The A0 hazard documented at `:50-55` is genuinely closed on this world. And the
two wrapper forms promised in the instructions are both accepted (`:86-91`),
plus two that are not promised (`"frame"`, `"after"`) — extra generosity, not a
defect.

### Structural invariants — both hold

| examinee | verdict counts | score | replay | heldout | gap |
|---|---|---|---|---|---|
| `oracle` | `correct 12` | 1.0000 | 1.0 | 1.0 | 0.0 |
| `null` | `unanswered 12` | 0.0000 | 0.0 | 0.0 | 0.0 |
| `memoriser` | `correct 8, wrong 4` | 0.6667 | 1.0 | 0.3333 | 0.6667 |
| `bluffer` | `correct 4, wrong 8` | 0.3333 | 0.3333 | 0.3333 | 0.0 |

* **Silence is never paid.** `null` is `unanswered` on all 12 items and
  `correct` on none, awarded 0.0 throughout. It reaches that verdict through the
  missing-key branch at `mark.py:51-52`, and an examinee that submits explicit
  per-item `null`s lands on `rubrics_heldout.py:138-142` for the same result.
* **Ground truth is never marked wrong.** `oracle` produces zero `wrong` and
  zero `abstained`: 12 `correct`, full marks.

## 3. A cheap examinee that beats the bluffer floor

**The bluffer floor on this world is 4/12 = 0.3333** — the four
`blocked_by_wall` items whose frame does not change.

I wrote one strategy, `walker`. It reads `frame_before`, `action` and `legend`
from the sheet and nothing else — no `ground_truth.json`, no `Item.truth`, no
`raw_trace.jsonl`, no world object. Its whole content:

> Find the cell holding `legend["agent"]`. Step one cell in the direction of
> `action`. If that cell is off the grid, or holds anything other than
> `legend["floor"]`, return the input frame unchanged. Otherwise move the agent
> colour into it and repaint the vacated cell as floor.

That is the generic heuristic "things move into empty space and are stopped by
anything that is not empty space". It contains no fact about switches, doors,
nets, latches or polarity, and it would be written the same way for any grid
world.

**Score: 12 / 12 = 1.0000.** Replay 1.0, held-out 1.0,
`gap_replay_minus_heldout` 0.0. Per class:

| class | walker | bluffer | memoriser | oracle |
|---|---|---|---|---|
| `free` (4) | 4/4 | 4/4 | 4/4 | 4/4 |
| `memorised` (4) | 4/4 | 0/4 | 4/4 | 4/4 |
| `theory` (4) | **4/4** | 0/4 | 0/4 | 4/4 |
| **total** | **12/12** | 4/12 | 8/12 | 12/12 |

It captures **100% of the `theory` residue** — all of `-000 -005 -009 -011` —
and beats the floor by +0.6667. It ties the oracle exactly, on every item, on
every axis.

A second variant, `walker_no_legend`, which does not consult the legend at all
(wall = the border colour, floor = the most common interior colour, agent = the
highest-numbered singleton colour), also scores **12/12**. So the result does
not even depend on the legend being printed.

**Why this happens, and why it is not a fluke of the twelve sampled items.**
I ran `walker` over the world's *entire* reachable transition relation — 26
states × 4 actions = 104 transitions:

| rule | walker correct | transitions |
|---|---|---|
| `walk` | 62 | 62 |
| `blocked_by_wall` | 32 | 32 |
| `walk_through_door` | 4 | 4 |
| `blocked_by_door` | 3 | 3 |
| `latch_already_set` | 2 | 2 |
| **`press_latch`** | **0** | **1** |
| **total** | **103** | **104** |

The heuristic is exactly wrong about **one transition in the whole world**:
`press_latch`, the single moment the latch bit goes 0 → 1 and the switch cell
repaints 2 → 3. Everything else in this world is "move onto empty space, or
don't". And `press_latch` is precisely the rule the matched-quota gate
**excludes** from the paper (`plan()` blocks it: `in_trace 1, held_out 0`,
`heldout_worldgen.py:130-137`) because a latch has one witness ever — the A0′
failure mode this whole world was built to be the control condition for
(`worldgen/mechanisms/switch_door.py:11-19`).

So the fairness rule and the informativeness of the paper are in direct
opposition here: the only transition that requires a world model is the only one
that cannot be asked twice, so it is dropped, and what remains is solvable
without one. This is not a bug in `discrimination.py` — it is the finding the
instrument was built to surface, arriving one step later than the instrument
looks. The taxonomy's own limit is written at
`exam/tools/discrimination.py:60-67`: "a fourth strategy nobody has written
could settle it for free, and the taxonomy would not notice." On this world
that fourth strategy exists, is trivial, and settles everything.

## 4. This world's honest effective size

**Against the three synthetic voters: 4.** Against any examinee that has
noticed grids contain a movable thing: **0.**

Nothing on this paper requires a world model. Concretely, a world model for
`t1-switch-latch` is the answer to three questions — does the latch set on
contact and never clear, does the door mirror the net, and what does the OR
network do — and the paper asks none of them:

* **`press_latch` is not on the paper.** Blocked, `in_trace 1 / held_out 0`.
  It is the only transition in 104 that a movement heuristic gets wrong.
* **`latch_already_set` is not on the paper.** Blocked, `in_trace 2 /
  held_out 0` — every reachable instance is already in the published trace, so
  there is nothing to hold out.
* **`blocked_by_door` is not on the paper.** Blocked, `in_trace 1 /
  held_out 2` — one witness inside the trace, one short of the quota. This is
  the near miss: it is the only rule that would have forced an examinee to read
  the switch's colour before predicting, and it fell one replay witness short.
* **`blocked_toggle_would_shut_door` never fires at all** in this world
  (`GROUND_TRUTH.md` marks it "never fires"; it does not appear among the six
  rules the reachable relation produces).

That leaves three rules on the paper, and none of them is informative:

* **`blocked_by_wall` (4 items, all `free`) is dead weight, and the profile
  already names it barren.** Every one of its 32 reachable transitions leaves
  the frame identical, so the bluffer is correct on it by construction. It can
  never produce a `theory` or `memorised` item in any world; it is a
  4-item-wide free gift, one third of the paper.
* **`walk` (4 items) and `walk_through_door` (4 items) are the same question
  printed twice.** `walk_through_door` only ever fires when the door is open
  (`switch_door.py:156-157`), and an open door is deliberately **not drawn** —
  its cell renders as floor 0 (`switch_door.py:177-178`). So on `-004 -009 -010
  -011` the target cell shows the examinee colour `0`, exactly what a plain
  floor cell shows on `-000 -003 -005 -008`. There is no observable on the sheet
  that separates the two rules. The distinction is real in the ground truth and
  invisible in the frame, so any strategy that handles `walk` handles
  `walk_through_door` for free. This is structural to the mechanism, not to the
  sample.

**Is the residue large enough to rank two examinees apart?** No, on three
independent counts.

1. It is 4 items with no partial credit, so the achievable scores on the residue
   are 0, ¼, ½, ¾, 1. A one-item difference between two examinees is 0.083 of
   the paper and carries no statistical weight at n = 4.
2. The residue is not four independent questions. It is two instances each of
   two rules that are indistinguishable on the sheet, so it is closer to *one*
   question asked four times. An examinee gets 4/4 or 0/4; the intermediate
   scores are essentially unreachable.
3. It does not discriminate at all against the strategy in §3, which takes all
   four. Two examinees that both know "the agent moves into empty space" are
   tied at 12/12 regardless of whether either holds a world theory.

One more consequence worth carrying: `gap_replay_minus_heldout` — the headline
this question type exists for (`heldout_worldgen.py:303-309`) — is 0.0 for the
oracle, 0.0 for the bluffer *and* 0.0 for the walker, and 0.667 only for the
memoriser. The gap detects memorisation and nothing else; on this world it
cannot tell a theory-holder from a theory-free examinee. It must always be read
next to the raw score, never alone.

### Recommendations (not requested; take or leave)

* Quote **0**, not 4, as this world's effective size, and add the walker (or
  any cheap movement heuristic) as a fifth voter in `VOTERS`. A `theory` class
  defined against three voters that all lack the most obvious heuristic is
  measuring the voter set. A five-voter classifier would relabel `-000 -005
  -009 -011` from `theory` to `free` and report this world's residue as 0
  immediately, without a human hand-check.
* `blocked_by_wall` should probably not be allowed to consume a quota slot in
  any world: it is provably barren everywhere, by construction, since its
  `then` clause is "nothing changes".
* If `blocked_by_door` could be given a second in-trace witness (a longer or
  differently-seeded exploration trace — the trace holds 29 of 104
  transitions), this world would gain the only 4 items that force an examinee
  to read state off the frame before predicting. That is the single highest-
  value change available here, and it is a trace-length problem, not a world
  design problem.

### Incidental finding

`heldout_worldgen.py:332` names its local `unchanged` but counts every key
entry whose `truth.frame_after` is not `None`, then publishes it under the axis
key `"items"`. The published number is right for its key; the variable name is a
leftover from a different statistic and will mislead the next reader of
`axes()`. Cosmetic, no effect on any score.

---

*Method: `exam.papers.heldout_worldgen.build_for("t1-switch-latch")` and
`exam.grading.rubrics_heldout.grade_frame_exact` imported and called directly;
`GridWorld.transitions()` walked for the 104-transition sweep. No source file
edited, no test suite run, no network, no git. All numbers above are
reproducible from the repository as it stands.*
