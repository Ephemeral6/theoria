# Examiner's report — `t1-tokens-lock`

Independent audit of `exam/tools/discrimination.py`'s profile of one world.
Profile audited: `exam/runs/20260728T151000Z-V7-exam-stress-fanout/worlds/t1-tokens-lock.json`
(paper `v2-heldout-t1-tokens-lock`, per_class=2, 12 items, rubric digest
`e06bdf52…1cb091`).

Everything below is recomputed locally: no network, no LLM, no `git`, no `pytest`,
no file written except this one. No source file was edited.

**Headline.** The classification is *true* — all 12 items check out, zero
anomalies, zero defects in the labels. But the instrument's `effective_size = 4`
is not the number to quote. A theory-free examinee that knows nothing about
tokens, locks or counting scores **11/12** on this paper. The honest effective
size is **1 item**, and that item is answerable only from a fact
(`props.k = 3`) that the world's published trace never once witnesses.

---

## 1. Is the classification true of this world's actual mechanics?

### 1.1 Method

I re-derived every transition from `worldgen/out/worlds/t1-tokens-lock/spec.json`
and the prose in `GROUND_TRUTH.md`, with a hand-written simulator that does **not**
call `GridWorld.explain`, `GridWorld.step` or `GridWorld.render`
(`worldgen/core/world.py:188`, `:221`, `:226`). It recovers state from
`frame_before` (agent = the cell showing 6; token *i* uncollected iff its spec
cell shows 2; lock closed iff `(3,4)` shows 3), re-renders it to confirm the
round trip, applies the five rules by hand in the documented priority order, and
re-renders the result.

The world: 5×9, layout `#########/#.......#/#.#####.#/#.......#/#########`,
agent start `(1,1)`, tokens `(1,3) (1,5) (3,1)`, one lock at `(3,4)` with `k = 3`,
goal `(3,7)` (never painted). Palette `{floor 0, wall 1, token 2, lock 3, agent 6}`.

### 1.2 Result — all twelve items, hand-checked

| item | action | rule (mine / recorded) | class | frame changes | my `frame_after` == recorded |
|---|---|---|---|---|---|
| `t1-tokens-lock-000` | DOWN | collect_token / collect_token | theory | yes | **yes** |
| `t1-tokens-lock-001` | LEFT | blocked_by_wall / blocked_by_wall | free | no | **yes** |
| `t1-tokens-lock-002` | RIGHT | walk / walk | theory | yes | **yes** |
| `t1-tokens-lock-003` | RIGHT | walk / walk | theory | yes | **yes** |
| `t1-tokens-lock-004` | UP | walk / walk | memorised | yes | **yes** |
| `t1-tokens-lock-005` | RIGHT | collect_token / collect_token | theory | yes | **yes** |
| `t1-tokens-lock-006` | DOWN | collect_token / collect_token | memorised | yes | **yes** |
| `t1-tokens-lock-007` | LEFT | blocked_by_wall / blocked_by_wall | free | no | **yes** |
| `t1-tokens-lock-008` | LEFT | walk / walk | memorised | yes | **yes** |
| `t1-tokens-lock-009` | RIGHT | collect_token / collect_token | memorised | yes | **yes** |
| `t1-tokens-lock-010` | LEFT | blocked_by_wall / blocked_by_wall | free | no | **yes** |
| `t1-tokens-lock-011` | UP | blocked_by_wall / blocked_by_wall | free | no | **yes** |

12/12 exact, 12/12 rule labels agree, 12/12 state round-trips.
**No `free` item changes the frame. No `theory` item leaves it unchanged. No
`dead` item. No anomaly.** The instrument's labels are sound on this world.

Worked examples, in full, so the check is reproducible by eye:

* **`t1-tokens-lock-000`** (the only item on the paper that touches the
  mechanism). Before: agent at `(2,1)`; `(1,3)` and `(1,5)` show `0`, so two
  tokens are collected; `(3,1)` shows `2`; `(3,4)` shows `3`, so the lock is shut
  and the count is `2 < 3`. Action DOWN targets `(3,1)`, an uncollected token →
  `collect_token`. Count rises to 3, so `3 ≥ k` and the lock stops being drawn
  (`worldgen/mechanisms/count_lock.py:134-140`). After: `(2,1)→0`, `(3,1)→6`,
  **`(3,4)→0`**. Recorded `frame_after` matches. Three cells move, and the third
  is the one no theory-free examinee predicts.
* **`t1-tokens-lock-003`** (`walk`, held out). Agent `(1,2)`, RIGHT into `(1,3)`.
  `(1,3)` is a token *cell* but the token there is already collected, so it is
  plain floor and the transition is an ordinary `walk`
  (`count_lock.py:107-108`, "already collected: floor, let it walk"). Recorded
  `frame_after` agrees, and the frame shows `0` at `(1,3)` — the examinee is not
  asked to remember anything.
* **`t1-tokens-lock-001` / `-007`** — both are agent at `(2,1)`, action LEFT,
  target `(2,0)` = wall. Same question, two different token configurations, both
  correctly `blocked_by_wall`, both frame-identical.

### 1.3 Is the count visible in the frame?

Yes, but only as a **complement, and only against the total**, and the total is
not on the sheet.

* The renderer draws *uncollected* tokens (`count_lock.py:126-132`). The frame
  therefore shows `3 − collected`, never `collected`.
* The lock is drawn iff `collected < k`, so it is a **one-bit readout** of the
  count. `count_lock.py:133-140` is explicit: an open lock renders as floor and
  "nothing else in the frame announces that the count reached `k`".
* Per item, `visible_tokens + collected = 3` holds on all 12 (verified).
  `ground_truth.json:8-13` confirms `frame_determines_state.injective = true`,
  50 states → 50 distinct frames, so nothing is aliased away.

So the world is not one with a hidden quantity — the state is legible. But two
constants are needed to read it, and neither is printed on the sheet
(`heldout_worldgen.py:187-192` puts only `frame_before`, `action`, `legend`,
`grid` there):

1. **the total, 3** — recoverable from `raw_trace.jsonl` frame 0, which shows all
   three tokens;
2. **the threshold, `k = 3`** — present in `spec.json` `entities[3].props.k`, and
   **nowhere in the trace**.

I checked (2) exhaustively: across all 51 published frames, cell `(3,4)` is `3`
in every one; the fewest tokens ever visible in the trace is **1**, never 0. The
lock **never opens in the published evidence**. The two transitions in the entire
reachable graph that open it are both held out (`in_trace = False`). An examinee
working from the trace alone can establish `k ≥ 3` and cannot establish `k ≤ 3`;
it cannot fall back on solvability either, because the goal `(3,7)` is never
painted (`world.py:235-237`) and the optimal plan `RIGHT×6, DOWN×2` routes along
row 1 and never touches the lock.

**Not a defect in your instrument, but a finding about the item**: whether
`t1-tokens-lock-000` is answerable at all depends on whether the examinee is
handed `spec.json`. `worldgen_port.OPEN_FILES` (`:65`) licenses it, so formally
yes. If an arm in practice receives only the trace as its "discovery input", then
`-000` is a mark nobody can earn from evidence, and this paper's *entire*
informative residue evaporates.

---

## 2. Does the marker misjudge anything on this world?

Twenty-seven near-truth answers pushed through `rubrics_heldout.grade_frame_exact`
(`:135`) directly, on items `-000`, `-002`, `-006`, `-010`. The rubric was not
edited. `_legal_cells(truth)` correctly resolves to `{0,1,2,3,6}` for this world,
so no legitimate frame is rejected as malformed — the A0 hardcoding hazard named
at `rubrics_heldout.py:56` does not bite here.

### 2.1 Cases the marker gets right

| answer | verdict | fair? |
|---|---|---|
| bare correct grid | `correct` | yes |
| `{"frame_after": grid}` | `correct` | yes |
| `{"frame_after": grid, "why": …, "confidence": 0.9}` | `correct` | yes |
| rows as tuples | `correct` | yes — serialisation must not cost a mark |
| `json.loads(json.dumps(grid))` | `correct` | yes |
| transposed 9×5 | `wrong`, `shape_ok=False` | yes (grid is 5×9, so no aliasing) |
| one cell changed | `wrong`, `cells_wrong=1` | yes — no partial credit, by design |
| rows reversed | `wrong`, `cells_wrong=2` | yes |
| short grid (4 rows) | `wrong`, `shape_ok=False` | yes |
| grid with one extra column | `wrong`, `shape_ok=False` | yes |
| ragged (one short row) | `wrong` | yes |
| `{"abstain": true}` | `abstained` | yes |
| `"abstain"` (string) | `abstained` | yes |
| `null` | `unanswered` | yes |
| `frame_before` (bluffer) | `correct` on the 4 unchanged items, `wrong` on 8 | yes |

### 2.2 Cases where I think the verdict is arguably wrong

**R-1 — an empty container is scored as a wrong prediction, not as silence.**
`{}` → `wrong` ("answer is not a well-formed frame"); `[]` → `wrong`; but `None` →
`unanswered`. Path: `grade_frame_exact:138` fires only on `answer is None`;
`_is_abstention:115` returns False for `{}`; `_as_frame:86-91` finds no
`frame_after`/`frame`/`after` key and returns `None`, so control reaches the
malformed branch at `:151`.
*What a fair examiner would say:* an empty object and an empty list are blank
paper. They are `unanswered`, exactly like `None`. No mark moves (both award 0.0),
but `axes()["unanswered"]` (`heldout_worldgen.py:343`) and any confusion matrix
will record a blank as an attempted-and-failed prediction. An LLM examinee that
emits `{}` when it has nothing is the realistic trigger.

**R-2 — integer-valued floats and `numpy` integers are rejected as malformed.**
`[[6.0, 0.0, …]]` → `wrong`; `[[numpy.int64(6), …]]` → `wrong`; a bare
`numpy.ndarray` → `wrong`. Cause: `_as_frame:104` demands
`isinstance(cell, int)`.
*What a fair examiner would say:* `6.0` is the number six. JSON does not
distinguish, and every examinee whose pipeline passes through numpy/pandas emits
either `float` or `numpy.int64`. This costs a **full mark per item** for a
prediction that is exactly right, and it does so silently — the report reads
"cannot format an answer", which is precisely the misreading the module's own
docstring warns about at `rubrics_heldout.py:50-55`. `int(cell) == cell` would
close it without weakening the bool guard at `:104`
(`isinstance(cell, bool)` must stay first). `np.array(grid).tolist()` is
accepted, so the failure is confined to examinees that skip that call.

**R-3 — there is no `malformed` verdict, so nine distinct defects read as
"wrong".** `VERDICTS = ('correct','wrong','abstained','unanswered')`
(`exam/model.py`). On this world, all of {cells as strings, cells as floats,
cells as bools, ragged grid, out-of-palette colour, JSON string of the grid, bare
`0`, `{}`, `[]`, `{"answer": grid}`, `{"frame_after": null}`, a list of row-strings}
land on `wrong`, alongside a genuinely mistaken prediction.
*What a fair examiner would say:* "you predicted the wrong world" and "you could
not serialise a grid" are different failures and a report that cannot tell them
apart will be misread. `detail["why"]` distinguishes them; nothing counts them.
This is the same conflation the docstring rejects for cells-correct
(`rubrics_heldout.py:1-14`), applied one level up.

**R-4 — an out-of-palette colour loses the diagnostic diff (mild).**
The correct frame with one cell set to `4` returns `wrong` /
"answer is not a well-formed frame" with no `cells_wrong`, indistinguishable in
the report from an answer that is not a grid at all. The verdict is right; the
`detail` is less useful than it could be.

**R-5 — accepted shapes exceed documented shapes; abstention outranks a supplied
answer (leniency, flagged not condemned).** `{"frame": …}` and `{"after": …}` are
accepted (`_as_frame:88`) though the instructions promise only a bare grid or
`{"frame_after": …}` (`heldout_worldgen.py:213-218`). And
`{"abstain": true, "frame_after": <correct grid>}` scores `abstained`, because
`:144` is checked before `:149` — defensible (the examinee said it declined) but
worth knowing.

### 2.3 The two structural invariants

Both hold, verified through the real `mark()` path with `axes_fn=heldout_wg.axes`:

| examinee | verdicts | score | replay | heldout | gap |
|---|---|---|---|---|---|
| `oracle` | **correct 12**, wrong 0 | 12/12 | 1.000 | 1.000 | 0.000 |
| `null` | **unanswered 12**, correct 0 | 0/12 | 0.000 | 0.000 | 0.000 |
| `memoriser` | correct 8, wrong 4 | 8/12 | 1.000 | 0.333 | 0.667 |
| `bluffer` | correct 4, wrong 8 | 4/12 | 0.333 | 0.333 | 0.000 |

**Silence is never paid** — `null` is `unanswered` on all 12 and `correct` on none.
**Ground truth is never marked wrong** — `oracle` produces zero `wrong`, so the
`dead` count of 0 in the profile is real, not a coincidence of counting.

---

## 3. A cheap examinee that beats the bluffer floor without a world model

Bluffer floor on this paper: **4/12 = 0.333** (= `notes.unchanged_frame_share`,
`heldout_worldgen.py:249`).

I wrote two strategies. Neither opens `ground_truth.json`; neither touches
`Item.truth`, `paper.key(...)`, or the profile artefact. Inputs are the sheet
(`frame_before`, `action`, `legend`, grid dims) and, for S3 only, the world's
published `raw_trace.jsonl`.

**S2 — "agent-mover" (legend + the generic grid prior).**
Locate the cell showing `legend["agent"]`; step one cell in the named direction;
if the target is off-board or shows `legend["wall"]`, return the input frame
unchanged; otherwise paint the vacated cell `legend["floor"]` and the target
`legend["agent"]`. Nothing about tokens, locks, counts or thresholds.

**S3 — "trace-fitted" (S2 with the direction semantics learned, not written).**
Same shape, but the map `action → (dr, dc)` and the answer to "what colour does
the vacated cell become" are fitted by majority vote over agent displacements in
`raw_trace.jsonl`. It recovers `{DOWN:(1,0), RIGHT:(0,1), LEFT:(0,-1),
UP:(-1,0)}` and `vacated → 0`, so it does not even assume English.

### Scores

| examinee | score | replay | heldout | gap | `theory` items captured |
|---|---|---|---|---|---|
| bluffer (floor) | 4/12 = **0.333** | 0.333 | 0.333 | 0.000 | 0 of 4 |
| memoriser | 8/12 = 0.667 | 1.000 | 0.333 | 0.667 | 0 of 4 |
| **S2 agent-mover** | **11/12 = 0.917** | 1.000 | 0.833 | 0.167 | **3 of 4** |
| **S3 trace-fitted** | **11/12 = 0.917** | 1.000 | 0.833 | 0.167 | **3 of 4** |
| oracle | 12/12 = 1.000 | 1.000 | 1.000 | 0.000 | 4 of 4 |

Both beat the floor by **+0.583** and beat the memoriser by **+0.250**. Both
capture **4/4 free, 4/4 memorised, and 3 of the 4 `theory` items**
(`-002`, `-003`, `-005`). The single miss, for both, is
**`t1-tokens-lock-000`** — the third-token collect, where the lock also vanishes.

Why `collect_token` falls to a strategy with no concept of collection: the agent
is painted last and wins every overlap (`world.py:238`), so a collected token is
simply overpainted. **The frame delta of a `collect_token` is identical to the
frame delta of a `walk`** unless the collection crosses the threshold. The
mechanism is invisible in the observable except at the one boundary.

Honesty statement: S2/S3 are not literally assumption-free — they encode "the
frame changes by translating one agent-coloured cell, and walls block". That is
the generic grid prior the brief sanctioned ("the most common single-cell delta"),
it is world-independent, and it contains no fact about tokens, locks or counting.
I did not read the truths, and the misses are consistent with that: the strategy
fails exactly where a counter is required and nowhere else.

---

## 4. This world's honest effective size

### 4.1 The numbers

| measure | value |
|---|---|
| items on the paper | 12 |
| instrument's `effective_size` (`theory`) | 4 |
| items requiring a world model, measured against S2/S3 | **1** (`t1-tokens-lock-000`) |
| zero-discrimination share (instrument) | 0.333 |
| zero-discrimination share against a kinematic baseline | **0.917** (11 of 12) |

### 4.2 The rules, named, with why each is dead weight

* **`blocked_by_wall` — 4 items (33% of the paper), wholly barren.** The
  instrument already names it (`summary.barren_rules`). 100 of the world's 200
  reachable transitions fire it; the answer is "copy the input", which is the
  bluffer's entire strategy. It cannot rank anyone, ever, in any world.
* **`walk` — 4 items, dead weight above the bluffer.** The kinematic baseline
  predicts **88 of 88** reachable `walk` transitions. Items `-002`, `-003`, `-004`
  and `-008` separate a memoriser from a bluffer and nothing beyond that.
  `-002` is the sharpest illustration: it is labelled `theory` and it is a plain
  step onto open floor.
* **`collect_token` — 4 items, 3 of them dead weight.** The baseline predicts
  **5 of 7** reachable `collect_token` transitions, for the overpainting reason
  above. Only `-000` survives.
* **`walk_through_lock` and `blocked_by_lock` — not dead weight but absent.**
  Both have `in_trace = 0` (2 and 3 held-out witnesses respectively), so the
  matched-quota rule at `heldout_worldgen.py:126-137` excludes them. **The paper
  examines a counting world without examining either of its two lock rules.**
  This matters more than it looks: `blocked_by_lock` is the one rule the
  kinematic baseline gets **0 of 3** right — it would happily walk into a shut
  lock. The only rule in the world that would expose the cheap strategy is the
  one the quota cannot carry.

### 4.3 The world's ceiling, not just this paper's

Running S2 over the **entire reachable relation** (200 transitions, 50 states):

| rule | n | kinematic baseline | bluffer |
|---|---|---|---|
| `blocked_by_wall` | 100 | 100 (1.000) | 100 (1.000) |
| `walk` | 88 | 88 (1.000) | 0 |
| `collect_token` | 7 | 5 (0.714) | 0 |
| `walk_through_lock` | 2 | 2 (1.000) | 0 |
| `blocked_by_lock` | 3 | **0 (0.000)** | 3 (1.000) |
| **total** | **200** | **195 (0.975)** | 103 (0.515) |

By split: replay 43/43 = 1.000, held out 152/157 = 0.968.

**Five transitions in the whole world defeat a theory-free examinee**: 2
`collect_token` threshold crossings and 3 `blocked_by_lock`. Three of those five
can never appear on a matched-quota paper (`in_trace = 0`). So the world's
absolute ceiling as a held-out-prediction exam is **2 informative items**, and
this paper realises **1** of them.

### 4.4 The quota makes it worse at any other setting

| per_class | feasible | usable rules | items |
|---|---|---|---|
| 2 | yes | `blocked_by_wall`, `collect_token`, `walk` | 12 |
| 3 | yes | `blocked_by_wall`, `walk` | 12 |
| 4 | yes | `blocked_by_wall`, `walk` | 16 |

`collect_token` has only **2** in-trace witnesses, so at `per_class ≥ 3` it is
dropped and the paper contains **zero** mechanism items — a 16-item paper on a
count-lock world consisting entirely of walking and bumping into walls, whose
informative residue against a kinematic baseline is **0**. `per_class = 2` is the
only setting at which this world examines its own mechanism at all, and it is a
happy accident of the trace, not a property the builder checks.

### 4.5 Can the residue rank two examinees apart?

**No.** One binary item. A full world theory and a hand-written kinematic
heuristic differ by exactly one mark out of twelve (1.000 vs 0.917). Two
examinees that both hold the grid prior and differ only in whether they induced
the counter are separated by a single Bernoulli trial — no confidence interval
worth printing survives that. The `gap_replay_minus_heldout` axis does separate
them (memoriser 0.667, baseline 0.167, oracle 0.000), and it is the number to
quote in preference to the score; but it too rests on that one item.

---

## 5. Things I found that were not asked about

**F-1 — the taxonomy is algebraically equivalent to `frame_changes × split`, on
every world, not just this one.** With the three voters as defined
(`heldout_worldgen.reference_answers:288-295`), the memoriser answers the truth
on `replay` and `frame_before` on `heldout`, and the bluffer answers
`frame_before` everywhere. Therefore, whenever the oracle is correct:

| split | frame changes? | memoriser | bluffer | `_classify` |
|---|---|---|---|---|
| replay | no | correct | correct | **free** |
| replay | yes | correct | wrong | **memorised** |
| heldout | no | correct | correct | **free** |
| heldout | yes | wrong | wrong | **theory** |

All 12 items obey this exactly. So `theory` means precisely *"the frame changes
and the item was held out"*, `memorised` means *"the frame changes and it was
not"*, `free` means *"the frame does not change"*. `dead` and `anomaly:*` are
reachable **only** if the oracle fails — i.e. only if the marker rejects ground
truth, which `run_matrix`'s calibration already tests, as the module docstring
concedes at `discrimination.py:41-44`.

The consequence is that `summary.free` is a re-derivation of
`notes.unchanged_frame_share`, which `build_for` already computes at
`heldout_worldgen.py:249` — and on this world the two agree to the digit
(0.333333 each). The instrument's per-rule and per-split cross-tabs are genuinely
new and genuinely useful; the *class* column is not a difficulty measure and the
docstring's caveat at `discrimination.py:59-67` ("a fourth strategy nobody has
written could settle it for free") is, on this world, not hypothetical — I wrote
it in section 3 and it settled 3 of the 4. Suggestion: either add a fourth voter
(a kinematic baseline is 30 lines and world-independent), or rename the class to
something like `held_out_change` and let `effective_size` carry an explicit
"against these voters" qualifier.

**F-2 — the `theory` label is unstable under a rename of the split, but the
underlying items are not.** Items `-002` and `-003` are plain floor walks that
happen to be held out. They are labelled `theory` and cost nothing to answer.
Conversely `-006` and `-009` are `collect_token` transitions labelled
`memorised` purely because the trace happened to contain them. Nothing about the
mechanics distinguishes `-005` (`theory`) from `-009` (`memorised`) — both are
first/second-token collections; only trace membership differs.

**F-3 — this world's `collect_token` is *observationally* a `walk`.** Because the
agent paints last (`world.py:238`), collection has no frame signature of its own.
The rule's entire observable content is the threshold crossing at `k`, of which
the world contains 2 instances. A world-factory reviewer may want to know that a
mechanism can be present, correctly implemented, fully invariant-checked, and
still contribute almost nothing that a frame-comparison exam can see.

**F-4 — the counting mechanism's discriminating rule is exactly the one the trace
starves.** `blocked_by_lock` is the only rule in the world the kinematic baseline
gets 0% right, and it has `in_trace = 0`. The explorer that produced
`raw_trace.jsonl` never bumped into the shut lock even once in 50 steps, despite
the lock being shut for the entire trace. If the trace generator were nudged to
touch each declared rule at least twice, this world would carry a genuinely
informative paper instead of a nearly-free one — the transitions exist, the
sampler just never visited them.

**F-5 — no leak.** The sheet carries `world.families = ["count_lock"]`
(`heldout_worldgen.py:220-227`), which names the mechanism family but not the
rule names, not `k`, and not the token total. Consistent with the module's stated
discipline at `:240-246`. I found nothing on the sheet that answers an item.

---

### Reproduction

All figures above come from six throwaway scripts in the session scratchpad
(`…/scratchpad/q1.py`, `q1b.py`, `q2.py`, `q2b.py`, `q3.py`, `q4.py`), run as
plain `python` against this worktree. They import
`exam.papers.heldout_worldgen`, `exam.papers.worldgen_port`,
`exam.grading.rubrics_heldout`, `exam.grading.mark` and read
`worldgen/out/worlds/t1-tokens-lock/`. Nothing under `arc-recon/` was touched;
no test suite was run; no repository file was modified.
