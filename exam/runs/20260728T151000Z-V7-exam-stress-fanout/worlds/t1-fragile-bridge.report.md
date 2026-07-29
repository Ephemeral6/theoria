# Independent examination — `t1-fragile-bridge`

Examiner report against `exam/runs/20260728T151000Z-V7-exam-stress-fanout/worlds/t1-fragile-bridge.json`.
Paper `v2-heldout-t1-fragile-bridge`, `per_class=2`, 8 items, rubric digest
`e06bdf52…1cb091` (recomputed live — matches the profile).

Everything below is local python against the built world. No files were edited, no
`git`, no network, no pytest suite.

---

## Verdict in one line

**The instrument's classification is correct on every item, and the marker never
misjudges a prediction — but the profile's `effective_size: 2` does not survive
contact with a 20-line theory-free examinee, which scores 8/8. The honest
effective size of this paper is 0.**

---

## 1. Is the classification true of this world's mechanics?

I re-implemented the transition myself from `worldgen/out/worlds/t1-fragile-bridge/spec.json`
and the rule table in `GROUND_TRUTH.md` (layout `#######/#.....#/#.#.#.#/#.....#/#######`,
fragile tiles at `(1,3)` and `(3,3)`, agent start `(1,1)`), decoding each frame back to
(agent cell, per-tile state) and re-rendering. **All 8 items reproduce exactly** — frame
and rule tag both — and every assigned class is consistent.

| item | action | agent | target | my rule | recorded rule | frame changes | class | checked |
|---|---|---|---|---|---|---|---|---|
| `t1-fragile-bridge-000` | RIGHT | (2,1) | (2,2)=wall | `blocked_by_wall` | `blocked_by_wall` | no | free | ✔ |
| `t1-fragile-bridge-001` | RIGHT | (3,1) | (3,2)=floor | `walk` | `walk` | yes | theory | ✔ |
| `t1-fragile-bridge-002` | LEFT | (3,2) | (3,1)=floor | `walk` | `walk` | yes | theory | ✔ |
| `t1-fragile-bridge-003` | RIGHT | (3,5) | (3,6)=wall | `blocked_by_wall` | `blocked_by_wall` | no | free | ✔ |
| `t1-fragile-bridge-004` | UP | (3,1) | (2,1)=floor | `walk` | `walk` | yes | memorised | ✔ |
| `t1-fragile-bridge-005` | LEFT | (3,2) | (3,1)=floor | `walk` | `walk` | yes | memorised | ✔ |
| `t1-fragile-bridge-006` | DOWN | (3,2) | (4,2)=wall | `blocked_by_wall` | `blocked_by_wall` | no | free | ✔ |
| `t1-fragile-bridge-007` | RIGHT | (2,1) | (2,2)=wall | `blocked_by_wall` | `blocked_by_wall` | no | free | ✔ |

Specifically as asked:

* **No `free` item changes the frame.** All four (`-000`, `-003`, `-006`, `-007`) are
  wall bumps; I recomputed each and the output frame is bit-identical to the input.
* **Both `theory` items do change the frame** (`-001` agent (3,1)→(3,2); `-002` agent
  (3,2)→(3,1)), and neither is in the published trace. Cross-checked the `replay` tags
  by hand against `raw_trace.jsonl`: `-004` is trace `t=7` (UP from (3,1)), `-005` is
  `t=6` (LEFT from (3,2)), `-006` is `t=5` (DOWN from (3,2)), `-000` is `t=9` (RIGHT
  from (2,1)). All four `replay` tags are honest; all four `heldout` keys are genuinely
  absent from the trace.
* **No defect in the instrument.** Zero anomalies, zero `dead`.

### Does the frame show enough state to predict the break?

Yes, but only positionally, and this is worth stating because it is not obvious.

The palette has **no `armed` colour**. A tile is `2` when intact, `3` when collapsed,
and while armed it is *invisible* — the agent (`6`) is standing on it. So "armed" is
readable only as "the agent is on a cell that is known to hold a fragile tile". That
knowledge is recoverable from the published trace: in all 11 trace frames, `(1,3)` and
`(3,3)` are `2`, so a diligent examinee can learn which two cells are tiles.
`ground_truth.json.frame_determines_state` confirms the encoding is lossless —
42 states, 42 distinct frames, `injective: true`. **Not a defect**, but it means
predicting the break requires cross-frame memory of tile locations, not just the frame
in front of you. On this paper the point is moot: no item touches a tile (see §4).

---

## 2. Does the marker misjudge anything?

I stressed `grade_frame_exact` (`exam/grading/rubrics_heldout.py:135`) on both a
frame-changing item (`-001`) and a static one (`-000`), 23 answer shapes each, by
importing the rubric — no edits.

### Structural invariants — both hold

* **Silence is never paid.** `null` (`reference_answers(..., "null")` returns `{}`)
  scores `unanswered` on all 8 items, `0.0/8.0`, verdict set `{unanswered}`. No
  `correct`, ever.
* **Ground truth is never marked wrong.** `oracle` scores `8.0/8.0`, verdict set
  `{correct}`. Zero `wrong`.
* **Stasis is never accepted where the frame moves.** I fed `frame_before` as the answer
  to every item whose truth differs from it: zero accepted.

### Correct behaviour (no complaint)

| answer shape | verdict | fair? |
|---|---|---|
| exact grid, bare | `correct` | ✔ |
| exact grid, `{"frame_after": …}` | `correct` | ✔ |
| exact grid, rows as tuples | `correct` | ✔ |
| exact grid, `{"abstain": false, "frame_after": …}` | `correct` | ✔ |
| correct grid **transposed** (7×5) | `wrong`, `shape_ok:false` | ✔ |
| correct grid, **one cell changed** | `wrong`, `cells_wrong:1` | ✔ |
| **ragged** grid (one short row) | `wrong`, malformed | ✔ |
| **short** grid (4 rows) | `wrong`, `shape_ok:false` | ✔ |
| correct grid with a cell = `8` or `4` (outside this world's `{0,1,2,3,6}`) | `wrong`, malformed | ✔ — and this is the fix that `legal_cells` exists for; `4`/`8` are the *A0 default* palette and are correctly refused here |
| `{"abstain": true}` | `abstained` | ✔ |
| `"abstain"` (bare string) | `abstained` | ✔ |
| booleans in place of 0/1 | `wrong`, malformed | ✔ (documented at `:104`) |
| `null` | `unanswered` | ✔ |

### Four cases where I think the verdict is arguably wrong

None of them changes a single point — all four already score 0. All four corrupt the
**verdict label**, which is exactly what `axes()` reads to report `abstained` and
`unanswered` (`heldout_worldgen.py:342-343`). The rubric's own docstring
(`rubrics_heldout.py:18-21`) says the abstention/wrong distinction exists "so a report
can say whether an examinee knew it did not know" — so mislabelling it defeats the
stated purpose of the category.

| # | answer | verdict now | what a fair examiner would say | why |
|---|---|---|---|---|
| **M1** | `{}` (empty dict) | `wrong` — "answer is not a well-formed frame" | `unanswered` | An empty object is nothing submitted. `None` gets `unanswered` at `:138-142`; `{}` falls through `_as_frame` (`:86-90`, no `abstain`, no `frame_after`/`frame`/`after`) and lands on `:151` as an incorrect *prediction*. An examinee that submitted `{}` for all 8 items reports as "8 wrong predictions" rather than "8 non-submissions". |
| **M2** | `[]` (empty list) | `wrong` — malformed | `unanswered` | Same argument: `_as_frame` rejects at `:94` (`not value`). An empty list is a non-answer, not a bad frame. |
| **M3** | `{"abstain": "true"}` | `wrong` — malformed | `abstained` | `_is_abstention` (`:115`) tests `value.get("abstain") is True`, so the string `"true"` misses. A model emitting stringified JSON booleans is a realistic examinee, and this reads its abstention as a failed prediction. |
| **M4** | `"I do not know"` | `wrong` — malformed | `abstained` | `_is_abstention` (`:119-120`) whitelists exactly four strings: `abstain`, `abstained`, `unknown`, `i cannot tell`. "I don't know" / "I do not know" / "cannot determine" all fall through. The whitelist is narrower than the intent. |

One softer note, not a defect: a **correct** prediction rendered with string cells
(`"1"`) or float cells (`6.0`) is scored `wrong` and is indistinguishable in the score
from a wildly incorrect grid. The detail dict does say `"answer is not a well-formed
frame"`, so a diagnostician can tell them apart; the *score* cannot. Given the
module's stated stance that it does not want to mark JSON conventions (`:79-83`), a
`malformed` verdict distinct from `wrong` would be more honest than either accepting
or silently conflating. I would not call this an error — it is a documented judgement
call — but it is the same class of thing as M1–M4.

Also observed, generous rather than unfair: `{"frame": …}` and `{"after": …}` are
accepted (`:88`) although the paper's instructions promise only `frame_after`; and
nesting recurses, so `{"frame_after": {"frame_after": grid}}` is `correct`.

---

## 3. A cheap examinee that beats the bluffer floor — it beats the *oracle's* margin too

**Bluffer floor on this world: 4/8 = 0.500** (`notes.unchanged_frame_share` = 0.5,
confirmed).

I wrote `cheap-walker`. It reads **only** `frame_before`, `action`, `legend` and `grid`
off the sheet. It never opens `ground_truth.json`, never touches `item.truth`, never
reads the trace, and knows nothing about this world:

```
1. the legend names a colour `agent` — find the unique cell holding it
2. the legend names a colour `floor` — that is what an agent may stand on
3. step one cell in the action's direction if the target cell is `floor`,
   vacating the old cell to `floor`; otherwise return the input frame unchanged
```

That is a generic gridworld prior — "things move onto empty space, and bounce off
anything else". It contains no fragile tile, no collapse, no notion of arming.

### Result: **8.0 / 8.0 = 1.000**

| class | cheap-walker | bluffer | memoriser | oracle |
|---|---|---|---|---|
| `free` (4) | 4 | 4 | 4 | 4 |
| `memorised` (2) | **2** | 0 | 2 | 2 |
| `theory` (2) | **2** | 0 | 0 | 2 |
| **total** | **8/8** | 4/8 | 6/8 | 8/8 |

`axes`: `replay 1.0`, `heldout 1.0`, **`gap_replay_minus_heldout 0.0`** — the headline
statistic this question type exists to produce reads *identical to a perfect
rule-learner*, produced by a strategy with no rule at all.

* Beats the bluffer floor by **+4 items (+0.500)**.
* Captures **2 of 2 = 100% of the `theory` residue**.
* Is **indistinguishable from the oracle** on this paper.

### The honest caveat, and it is the interesting part

The cheap walker is not correct about this world — it is correct about the eight
questions that were asked. Over the world's **168 reachable transitions** it scores
**148 = 88.1%**:

| rule | cheap-walker | of |
|---|---|---|
| `blocked_by_wall` | 80 | 80 |
| `blocked_by_collapsed` | 12 | 12 |
| `walk` | 56 | 68 |
| `cross_fragile` | **0** | 8 |

The 20 transitions it fails are exactly this world's mechanism: the 8 `cross_fragile`
steps (agent onto an intact tile) and the 12 `walk` steps that carry the delayed
collapse (agent leaves an armed tile, and the vacated cell renders `3` instead of `0`
— the "one frame later" behaviour that `spec.json.notes` calls "the inductively
interesting bit"). **The paper samples none of the 20.**

---

## 4. Honest effective size

**The instrument says `effective_size: 2`. The defensible number is `0`.**
`theory` on this world means "not settled by oracle/memoriser/bluffer", and both
`theory` items are settled by a fourth strategy that took twenty lines and no world
model. This is precisely the limit `discrimination.py:60-67` names in its own
docstring; `t1-fragile-bridge` is a worked instance of it.

### Which rules are dead weight, and why

| rule | items | why it is dead weight here |
|---|---|---|
| `blocked_by_wall` | 4 of 8 (all `free`) | Already flagged `barren` in the profile. Its truth *is* the input frame, so the bluffer has it for free. 50% of the paper. |
| `walk` | 4 of 8 (2 `memorised`, 2 `theory`) | Not barren by the instrument's test, but every one of the four drawn instances is an ordinary move across open floor. Predicted by the generic prior. Contributes 0 items requiring this world's theory. |
| `cross_fragile` | **0 items** | Excluded before sampling. `in_trace: 0`, `held_out: 8` — the published `raw_trace.jsonl` (11 frames, 10 actions) walks `DOWN DOWN DOWN … UP …` around the left column and **never steps on a fragile tile**, so the rule has no replay witness and the matched-quota rule refuses it (`heldout_worldgen.py:127-137`). |
| `blocked_by_collapsed` | **0 items** | Same cause: `in_trace: 0`, `held_out: 12`. No tile ever collapses in the trace, so no frame in the trace contains a `3`. |

So the world's *named* mechanism — the fragile bridge — is 100% absent from the paper
it generates, for a reason that has nothing to do with the world and everything to do
with a 10-action trace that avoided it.

### It was a near miss, not a structural impossibility

The 12 collapse-carrying `walk` transitions are all in the `heldout` `walk` pool, and
`walk` **is** a usable rule — the sampler could have drawn one. Under the sampling salt
(`_pick`, `heldout_worldgen.py:113-116`) the heldout `walk` pool has 63 candidates; the
paper takes ranks 0 and 1, and the 12 collapse-carrying candidates sit at ranks
**13, 14, 16, 22, 24, 42, 50, 54, 55, 58, 60, 61**. At `per_class=2` the chance of
drawing at least one is ≈ 1 − C(51,2)/C(63,2) ≈ **35%**; this world drew none.
Raising `per_class` to ~4–5 on this world would make a genuine collapse item likely,
and `per_class=2` × 63 candidates is why it did not happen.

### Can it rank two examinees apart?

**On theory, no.** Zero items separate a world-model examinee from a generic
gridworld heuristic, so the paper cannot rank the two things the framework exists to
distinguish. It *can* still separate a bluffer (4/8) from a memoriser (6/8) from
anything competent (8/8) — three levels at ±1/8 resolution — but that is a test of
"do you know an agent moves", not of "do you have a theory of this world". Any report
quoting `theory_share: 0.25` for `t1-fragile-bridge` should carry the correction.

---

## Findings not asked for

1. **`axes()` reports a miscounted field.** `heldout_worldgen.py:332-334` computes
   `unchanged = sum(1 for entry … if entry["truth"]["frame_after"] is not None)` and
   publishes it at `:344` as `"items"`. Every item has a `frame_after`, so this is
   always the item count — it is a correct item count under a variable named
   `unchanged`, which reads like a half-finished rename of the
   `unchanged_frame_share` statistic computed at `:207`/`:249`. Harmless today,
   but the name will mislead the next reader. Observed value here: `8`.
2. **The sheet's `legend` names mechanisms the paper never examines.** Items carry
   `{"agent":6,"collapsed":3,"floor":0,"fragile":2,"wall":1}` — so the examinee is told
   there is a `fragile` and a `collapsed` colour, while zero items exercise either
   rule. Not a leak of any answer, but it is an invitation to theorise about a
   mechanism the paper does not score.
3. **`cheap-walker` uses `legend` as a semantic hint.** It keys on the *names*
   `agent` and `floor`. That is a legitimate part of the sheet, but it means the legend
   is doing more work than "here is what the colours look like" — it hands a
   theory-free strategy the two roles it needs. A paper wanting a harder floor could
   publish the legend as opaque labels (`c0`…`c4`).
4. **`blocked_by_collapsed` is a `clause: true` rule** (`ground_truth.json:181`) that
   fires 12 times and is nonetheless silently excluded — worth confirming that a
   clause-rule with zero trace witnesses is meant to be reported the same way as a
   full rule with zero trace witnesses. Both currently land in `blocked_rules` with the
   same `why` string, and that string ("the trace witnessed it fewer than 2 times") is
   accurate but understates the case: it was witnessed **zero** times, which is a
   different situation from "once".
