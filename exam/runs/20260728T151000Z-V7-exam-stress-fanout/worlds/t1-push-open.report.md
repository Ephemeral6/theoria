# Independent examination — `t1-push-open`

Examiner: independent audit of `exam/tools/discrimination.py`'s profile at
`exam/runs/20260728T151000Z-V7-exam-stress-fanout/worlds/t1-push-open.json`.
Everything below is local python against the worktree
`C:\Users\user\Desktop\theoria\.worktrees\v7-exam-stress-fanout`. No file was
edited, no network, no `git`, no `pytest` run.

Paper under examination: `v2-heldout-t1-push-open`, 12 items, `per_class=2`,
rubric digest `e06bdf52…1cb091`.

## Verdict in one line

The instrument's classification is **correct on every one of the 12 items** —
and the number it reports as the paper's real size, `effective_size: 4`, is
**still an overstatement**. A 25-line answer strategy that reads only the
printed sheet scores **12/12**, capturing all four `theory` items.

---

## 1. Is the classification true of this world's actual mechanics?

**Yes. All 12 items check out, by hand and by independent re-derivation.**

The world (`worldgen/out/worlds/t1-push-open/spec.json`) is a 5x7 board

```
#######      walls: row 0, row 4, col 0, col 6, plus (1,3) and (3,3)
#..#..#      13 floor cells; one block, colour 2; agent colour 6
#.....#      agent_start (2,2), block (2,3), goal (2,5), families ["push"]
#..#..#
#######
```

I re-derived every item's transition from the layout and the four rules in
`GROUND_TRUTH.md` **before** comparing to the recorded `frame_after`, then
re-checked mechanically against `GridWorld.transitions()` and against the
`(frame, action)` keys of the 41-line `raw_trace.jsonl`.

| item | action | agent → target | my derivation | recorded rule | recorded split | agrees |
|---|---|---|---|---|---|---|
| `t1-push-open-000` | LEFT | (1,1) → (1,0) wall | no change | `blocked_by_wall` | heldout | ✓ |
| `t1-push-open-001` | UP | (3,2) → (2,2) floor | agent to (2,2) | `walk` | replay | ✓ |
| `t1-push-open-002` | UP | (3,1) → (2,1) floor | agent to (2,1) | `walk` | replay | ✓ |
| `t1-push-open-003` | RIGHT | (2,3) → (2,4) block, (2,5) free | block→(2,5), agent→(2,4) | `push` | replay | ✓ |
| `t1-push-open-004` | UP | (3,5) → (2,5) block, (1,5) free | block→(1,5), agent→(2,5) | `push` | heldout | ✓ |
| `t1-push-open-005` | DOWN | (1,1) → (2,1) floor | agent to (2,1) | `walk` | heldout | ✓ |
| `t1-push-open-006` | DOWN | (3,1) → (4,1) wall | no change | `blocked_by_wall` | heldout | ✓ |
| `t1-push-open-007` | DOWN | (1,5) → (2,5) block, (3,5) free | block→(3,5), agent→(2,5) | `push` | heldout | ✓ |
| `t1-push-open-008` | DOWN | (2,3) → (3,3) wall | no change | `blocked_by_wall` | replay | ✓ |
| `t1-push-open-009` | UP | (3,1) → (2,1) floor | agent to (2,1) | `walk` | heldout | ✓ |
| `t1-push-open-010` | RIGHT | (2,2) → (2,3) block, (2,4) free | block→(2,4), agent→(2,3) | `push` | replay | ✓ |
| `t1-push-open-011` | LEFT | (3,4) → (3,3) wall | no change | `blocked_by_wall` | replay | ✓ |

Mechanical cross-check: 12/12 on `frame_after`, 12/12 on `rule`, 12/12 on
`split` (recomputed as `transition_key ∈ evidence_index`). Zero mismatches.

**The two properties you specifically asked me to falsify both hold:**

* Every `free` item — `-000`, `-006`, `-008`, `-011` — has
  `frame_after == frame_before`. Confirmed cell-for-cell. All four are
  `blocked_by_wall` where the target is a genuine wall. **No `free` item
  changes the frame.**
* Every `theory` item — `-004`, `-005`, `-007`, `-009` — changes the frame,
  and all four are `heldout`. **No `theory` item is static.**

Calibration matches the profile exactly: `dead = 0`, `anomalies = []`,
`free = memorised = theory = 4`. Scores are

| examinee | score | replay | heldout | gap | verdict counts |
|---|---|---|---|---|---|
| `oracle` | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 12 correct |
| `memoriser` | 0.6667 | 1.0000 | 0.3333 | 0.6667 | 8 correct, 4 wrong |
| `bluffer` | 0.3333 | 0.3333 | 0.3333 | 0.0000 | 4 correct, 8 wrong |
| `null` | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 12 unanswered |

**No defect found in `discrimination.py` on this world.**

One structural observation, not a defect: on `t1-push-open` the class is a
**deterministic function of `(split, frame_changes)`** — I confirmed all four
cells are single-valued. `heldout ∧ static → free`, `replay ∧ static → free`,
`replay ∧ changing → memorised`, `heldout ∧ changing → theory`. So on *this*
world the instrument reports nothing that
`paper.notes["unchanged_frame_share"]` (already `0.333333`) crossed with the
split tag printed on the sheet does not already say. That collapse is a
property of the world — a world with a rule that changes the frame in a way a
memoriser could still guess would break it — but it means the profile's
information content here is one number, not twelve.

---

## 2. Does the marker misjudge anything?

Rubric: `exam/grading/rubrics_heldout.py`. I ran ~30 near-truth answers through
`grade_frame_exact` directly, on the `theory` item `t1-push-open-007` and the
`free` item `t1-push-open-000`. **The rubric was not modified.**

### Structural invariants — both hold

* **Silence is never paid.** `null` is `unanswered` on all 12 items and
  `correct` on 0. No abstention form scores above zero: `{"abstain": true}`,
  `"abstain"`, `"I cannot tell"` all → `abstained`, 0.0.
* **Ground truth is never marked wrong.** `oracle` produces 0 `wrong`, on all
  12 items, in every accepted wrapping.

### Fair verdicts (no complaint)

| answer | verdict | detail |
|---|---|---|
| bare truth grid | `correct` | `cells_wrong: 0` |
| `{"frame_after": truth}` | `correct` | — |
| `{"frame": …}`, `{"after": …}` | `correct` | lenient beyond the printed instructions, in the examinee's favour |
| tuple-of-tuples | `correct` | — |
| truth + extra key | `correct` | — |
| one cell changed (legal colour) | `wrong` | `cells_wrong: 1` — right call, no partial credit by design |
| transposed 7x5 | `wrong` | `shape_ok: false` |
| short grid (4 rows) | `wrong` | `shape_ok: false` |
| ragged row | `wrong` | not a well-formed frame |
| input frame unchanged | `wrong` | `cells_wrong: 3` |
| one cell `True` (bool) | `wrong` | `rubrics_heldout.py:104` catches it deliberately |
| prose / integer `0` | `wrong` | — |
| `null` | `unanswered` | — |

### Two places the verdict is arguably wrong

**M1 — empty submissions are punished as wrong predictions.**

| answer | rubric says | a fair examiner would say |
|---|---|---|
| `{}` | `wrong` | `unanswered` — nothing was submitted |
| `[]` | `wrong` | `unanswered` |
| `{"frame_after": null}` | `wrong` | `unanswered` |
| `{"abstain": false}` | `wrong` | `unanswered` |

`grade_frame_exact` (`:138`) treats *only* Python `None` as "nothing
submitted". Everything else empty falls through `_as_frame` (`:75`) → `None`
→ the `wrong` branch at `:150`. The **score is unaffected** (all are 0.0), so
no ranking moves; what moves is the report. An examinee that returns `{}` on
every item reads as *twelve wrong predictions* rather than twelve blanks, and
`axes()["unanswered"]` (`heldout_worldgen.py:343`) counts 0 for it. That is
the same distinction the module docstring says it is keeping — "so a report can
say whether an examinee knew it did not know" — applied inconsistently to the
empty-object case. Confirmed on both a `theory` and a `free` item.

**M2 — a malformed answer is indistinguishable from a wrong prediction in the
`verdict` field.**

| answer | rubric says | a fair examiner would say |
|---|---|---|
| correct grid, cells as strings `"0"` | `wrong` | `malformed` — the prediction is right, the encoding is not |
| **correct grid, cells as floats `1.0`** | `wrong` | `malformed` |
| correct grid, rows as strings `"1111111"` | `wrong` | `malformed` |
| correct grid, one cell colour `8` | `wrong` | `malformed` (8 ∉ `{0,1,2,6}`) |
| correct grid, one cell colour `4` | `wrong` | `malformed` (4 is legal under the A0 default, not here) |

The `detail` dict does separate them (`"why": "answer is not a well-formed
frame"` vs `cells_wrong: N`), and the docstring at `:8-14` is explicit that
refusing a malformed frame is cheaper than reporting it as a near miss — so
this is a *deliberate* choice about the payload. But the choice stops one level
short: the `verdict` string is the field `discrimination.py:136` and
`run_matrix` read, and both are `"wrong"`. **An examinee that predicts all 12
frames exactly and JSON-encodes cells as floats scores 0.0000 with a report
identical to an examinee with no theory at all.** The float case is not
hypothetical — a JSON round-trip through most numeric layers produces `1.0`,
and `:104` rejects any non-`int`. The machinery for a third verdict already
exists (`abstained` is one); adding `malformed` would cost nothing and would
stop a formatting failure from being published as an epistemic one.

Neither M1 nor M2 changes any score on this paper. Both change how a report
reads, and M2 changes it in the direction that flatters the marker and
libels the examinee.

**M3 — not a marker fault, but note it:** `t1-push-open-008` and
`t1-push-open-010` have *identical* `frame_after`. A cross-product of all 12
answers against all 12 items produces exactly those two false accepts and no
others. It is genuine — `-010`'s push lands on `-008`'s static frame — so the
paper has 11 distinct answers for 12 items, not 12.

---

## 3. A cheap examinee for this world

Bluffer floor: **4/12 = 0.3333** (the four static `blocked_by_wall` items).

I wrote two strategies. Both are pure functions of a dict built from
`item.paper` alone — `frame_before`, `action`, `legend`, `grid` — handed in as
a deep copy. `ground_truth.json` is never opened; `Item.truth` is never in
scope inside either function. Neither uses `raw_trace.jsonl`, so neither has
even the memoriser's evidence.

**S1 `walk-only`** — legend-only generic grid prior, no notion of pushing:

> Find the single cell holding the colour the legend calls `agent`. Step one
> cell toward `action`. If that cell holds the colour the legend calls `floor`,
> move the agent there. Otherwise return the input frame.

**S2 `walk+shove`** — S1 plus the single most common prior in grid-world land:

> …and if the target cell holds anything that is neither `floor`, `wall` nor
> `agent`, and the cell **beyond** it is `floor`, that thing slides one cell and
> the agent takes its place; otherwise nothing happens.

S2 does not know that colour 2 is a block or that this world pushes. It knows
"not floor, not wall, not agent".

| strategy | score | replay | heldout | free 4 | memorised 4 | **theory 4** |
|---|---|---|---|---|---|---|
| bluffer (floor) | 0.3333 | 0.3333 | 0.3333 | 4 | 0 | **0** |
| S1 `walk-only` | **0.6667** | 0.6667 | 0.6667 | 4 | 2 | **2** |
| S2 `walk+shove` | **1.0000** | 1.0000 | 1.0000 | 4 | 4 | **4** |

**S2 achieves oracle parity — 12/12 — and captures 100% of the `theory`
residue.** The four items the instrument certifies as "the only class that
needs a world model" (`-004`, `-005`, `-007`, `-009`) are all taken by a
strategy that has never seen this world.

S1 is worth its own line. It ties the memoriser's total (0.6667) while scoring
**0.6667 on `heldout` against the memoriser's 0.3333**, and its
`gap_replay_minus_heldout` is **0.0000** — the signature the paper publishes as
"a rule-learner, not a memoriser" (`heldout_worldgen.py:305-308`). S1 has
learned no rule. It brought one.

**The honest framing.** You asked for an examinee that beats the floor *without
a world model*. S2 plainly *is* a world model — it is just not one derived from
this world's evidence. That is the finding, and it is the sharper version of
the caveat `discrimination.py:60-67` already writes about itself ("a fourth
strategy nobody has written could settle it for free"). The paper cannot
distinguish a theory *learned* from a theory *imported*, and on a tier-1 push
world the correct import is the default guess of anyone who has seen Sokoban.

**S2 is not tuned to this world.** I ran the identical function, unchanged,
across all 20 catalogue worlds:

| result | worlds |
|---|---|
| **1.0000 (oracle parity)** | `t1-walk-maze`, `t1-push-open`, `t1-push-corridor`, `t1-switch-toggle`, `t1-switch-latch`, `t1-portal-oneway`, `t1-cycler-gate`, `t1-fragile-bridge`, `t2-portal-pair`, `t2-portal-paired`, `t3-gravity-fragile` (11) |
| 0.60–0.88 | `t2-switch-push` 0.8333, `t2-gravity-push` 0.8750, `t2-unsolvable-nodoor` 0.7500, `t1-tokens-lock` / `t2-lock-fragile` / `t2-cycler-lock` / `t3-full-house` 0.6667, `t3-latch-maze` 0.6000, `t3-cycler-portal-lock` 0.5000 |

It beats the bluffer floor on **20 of 20** worlds. This is outside my remit —
I audited only `t1-push-open` in detail and did not verify the other papers'
items — but the totals are reproducible and I am reporting them because the
eleven oracle-parity worlds are a catalogue-level result, not a quirk of mine.

---

## 4. This world's honest effective size

**The instrument says 4. The defensible number depends on the examinee you are
guarding against, and none of the answers is 12.**

| baseline the residue is measured against | items genuinely requiring a *learned* model |
|---|---|
| a bluffer (returns input) | 8 |
| the profile's `effective_size` (oracle-only items) | **4** — `-004`, `-005`, `-007`, `-009` |
| a legend-only walker (S1, zero evidence) | **2** — `-004`, `-007` (both `push`/`heldout`) |
| a generic shove prior (S2, zero evidence) | **0** |

### Dead weight, by name

* **`blocked_by_wall` — 4 of 12 items, all free, dead by construction.** 75
  reachable transitions and **all 75 leave the frame unchanged**. Not "these
  four happened to be easy": *no* item this rule can ever carry is informative
  under a frame-exact rubric, because its `then` clause is literally "nothing
  changes" and the bluffer's answer is "nothing changes". The profile calls it
  `barren`; the stronger statement is that it is unfixable at `per_class` — it
  would still be barren at 2, 10 or 75 items. A third of the paper is spent on
  it.
* **`blocked_by_block` — 0 items, excluded, and would have been free too.** All
  5 of its reachable transitions are outside the published trace, so
  `plan()` blocks it ("every reachable transition of this rule is already in
  the trace" is *not* the reason; the reason is `in_trace: 0`, no replay
  control) and `paper.notes["classes_not_examined"] = 1`. All 5 leave the frame
  unchanged, so its exclusion costs the paper nothing it would have wanted.
  **Both of this world's stasis rules are structurally incapable of producing
  an informative item.**
* **`push` — 2 memorised + 2 theory, and completely exhausted.** The world has
  only **4 reachable `push` transitions in total**; the paper uses all four (2
  in trace, 2 held out). There is no headroom: at `per_class=3` `push` drops
  out of `usable_rules` entirely and the paper degenerates to `walk` +
  `blocked_by_wall` — i.e. to something S1 alone answers perfectly. `push` is
  the only rule on this paper that S1 cannot do, so the entire
  evidence-requiring content of `t1-push-open` rests on **two held-out items
  drawn from a pool of two**.
* **`walk` — 2 memorised + 2 theory, 112 reachable transitions, all changing.**
  The only rule with real headroom, and the only one where held-out items are
  drawn from a genuinely large pool. It is also the rule S1 captures for free.

### Is 4 enough to rank two examinees apart?

No, except at the extremes. All-or-nothing marking on 4 binary items gives a
score granularity of 1/12 = **0.0833** on the paper total and 0.25 on the
residue. Fisher exact, two-sided, on the theory subset:

| comparison | p |
|---|---|
| 4/4 vs 0/4 | **0.0286** |
| 4/4 vs 1/4 | 0.1429 |
| 4/4 vs 2/4 | 0.4286 |
| 4/4 vs 3/4 | **1.0000** |
| 3/4 vs 1/4 | 0.4857 |

Clopper-Pearson 95% CI on 4/4 of n=4 is **[0.398, 1.000]**; on 2/4 it is
[0.068, 0.932] — the two intervals overlap across most of the unit interval.
So the residue separates *has the push prior* from *has nothing*, and nothing
finer. It cannot tell a theory that is right three times in four from one that
is right four times in four. And because S2 takes all four, even that single
separable comparison does not measure what the paper claims to measure.

---

## Findings you did not ask for

**F1 — the sheet names the mechanic.** `heldout_worldgen.py:236-241` is
explicit that rule names are withheld because "a sheet that lists them hands
the examinee the alphabet it is being asked to discover", and dutifully
publishes counts instead. But two lines up, `heldout_worldgen.py:222` puts
`"families": ["push"]` on the sheet, and `worldgen_port.palette()` puts
`"block": 2` in the printed `legend`. Between them the examinee is told, before
seeing a single item, *this is a push world and colour 2 is a block*. That is
the entire content of the prior S2 used to score 12/12. The discipline applied
to rule names is not applied to family names or legend keys, and on a tier-1
world the family name **is** the rule.

**F2 — four items' answers are printed elsewhere on the same sheet.** Because
the paper is drawn from a chained trace, some items' `frame_after` appears
verbatim as another item's `frame_before`:

| item | class | its answer is printed as `frame_before` of |
|---|---|---|
| `t1-push-open-000` | free | `-005` |
| `t1-push-open-001` | memorised | `-010` |
| `t1-push-open-008` | free | `-003` |
| `t1-push-open-010` | memorised | `-003`, `-008` |

**None of the four `theory` items leaks this way**, so the residue itself is
clean and this is a caveat rather than a defect. It does mean an examinee with
the generic heuristic "the answer is probably one of the twelve frames printed
on this sheet" gets a materially narrowed search on a third of the paper, for
free. Worth a check in the builder, since it is a property of chained-trace
sampling and will recur on every world.

**F3 — `per_class` has no headroom here.** `plan("t1-push-open", 3)` drops
`push`. The paper is at its maximum informative size at `per_class=2`; growing
it makes it *less* informative, not more.

---

## Reproduction

All work was read-only. The strategies and probes were run from a scratchpad
outside the repository:

* item dump and hand-check: `heldout_worldgen.build_for("t1-push-open", 2)`,
  compared against `GridWorld.transitions()` and
  `worldgen_port.evidence_index("t1-push-open")`.
* marker stress: `rubrics_heldout.grade_frame_exact(answer, item.truth, item)`
  called directly, ~30 answers, on `-007` and `-000`.
* cheap examinees: strategies fed a deep copy of `item.paper` only; scored via
  `exam.grading.mark.mark` with `axes_fn=heldout_worldgen.axes`.
* catalogue sweep: the same S2 function over `worldgen_port.world_ids()`.

`exam/tools/discrimination.py` was not run in write mode; the published
per-world JSON was read, not regenerated.
