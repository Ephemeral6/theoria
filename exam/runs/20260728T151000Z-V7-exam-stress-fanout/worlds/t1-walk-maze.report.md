# Independent examination — `t1-walk-maze`

Paper `v2-heldout-t1-walk-maze`, `per_class=2`, 8 items, rubric digest
`e06bdf52…1cb091`. Profile under review:
`exam/runs/20260728T151000Z-V7-exam-stress-fanout/worlds/t1-walk-maze.json`.

Everything below is local python against the built world. No network, no LLM, no
`pytest` run, no file written except this one.

The world's whole mechanism is two rules
(`worldgen/out/worlds/t1-walk-maze/GROUND_TRUTH.md:23-24`):

| rule | when | then |
|---|---|---|
| `walk` | target cell is inside the grid and is not a wall | agent moves one cell |
| `blocked_by_wall` | target cell is outside the grid or is a wall | **nothing changes** |

Palette `{floor:0, wall:1, agent:6}`; grid 7x9; 24 reachable states; frames
injective on states (`ground_truth.json:8-13`), so the frame-keyed evidence index
cannot conflate two states.

---

## 1. Is the classification true of this world's mechanics? — **Yes, all 8 items, no defect**

I re-derived every transition from `spec.json`'s `layout` string with my own
9-line stepper (not `GridWorld`), and compared frame, rule name and class. This
is not a sample: the paper has 8 items and I checked all 8.

| item | agent (r,c) | action | target | layout at target | my rule | truth rule | frame_after matches | changes | class |
|---|---|---|---|---|---|---|---|---|---|
| `t1-walk-maze-000` | (3,1) | LEFT | (3,0) | `#` wall | `blocked_by_wall` | `blocked_by_wall` | yes | no | `free` |
| `t1-walk-maze-001` | (2,3) | LEFT | (2,2) | `#` wall | `blocked_by_wall` | `blocked_by_wall` | yes | no | `free` |
| `t1-walk-maze-002` | (2,7) | LEFT | (2,6) | `#` wall | `blocked_by_wall` | `blocked_by_wall` | yes | no | `free` |
| `t1-walk-maze-003` | (1,6) | RIGHT | (1,7) | `.` floor | `walk` | `walk` | yes | yes | `theory` |
| `t1-walk-maze-004` | (1,3) | LEFT | (1,2) | `.` floor | `walk` | `walk` | yes | yes | `memorised` |
| `t1-walk-maze-005` | (1,2) | LEFT | (1,1) | `.` floor | `walk` | `walk` | yes | yes | `memorised` |
| `t1-walk-maze-006` | (5,6) | LEFT | (5,5) | `.` floor | `walk` | `walk` | yes | yes | `theory` |
| `t1-walk-maze-007` | (5,7) | RIGHT | (5,8) | `#` wall | `blocked_by_wall` | `blocked_by_wall` | yes | no | `free` |

Also checked, and all clean:

* every `frame_before` is the layout with exactly one `6` painted on a `.` cell —
  no item shows an impossible board;
* the two invariants the marker never checks (`agent_unique`, `grid_shape`) hold
  on every before/after frame on the sheet;
* the `free` / `theory` invariants the instrument implies:
  **no `free` item changes the frame** (000/001/002/007 are byte-identical
  before and after) and **both `theory` items do change it** (003, 006);
  `frame_changes` in the profile agrees with recomputation on all 8;
* `replay` / `heldout` tags are honest against the published trace: for all four
  `replay` items the `(frame, action)` key is in `raw_trace.jsonl` **and** the
  trace's recorded successor equals `truth.frame_after`; for all four `heldout`
  items the key is absent;
* `anomalies: []` reproduces, `dead: 0` reproduces, and two builds of the paper
  are identical object-for-object.

**Verdict: no defect in the instrument on this world.** The classification is
true of the mechanics.

One remark on how the classes arise, because it is what makes the rest of this
report: on this world `free` and `blocked_by_wall` are the *same set*, and not by
sampling luck. `blocked_by_wall`'s consequent is literally "nothing changes", so
its `frame_after == frame_before` by definition, which is verbatim the bluffer's
answer. Every `blocked_by_wall` item on every world at every `per_class` is
`free`. The instrument reports the rule as `barren`; it is worth saying it is
*structurally* barren, not accidentally so.

---

## 2. Does the marker misjudge anything? — **Two structural invariants hold; six verdicts are arguably wrong, all in the same direction (they conflate "said nothing" with "predicted wrongly")**

Rubric: `exam/grading/rubrics_heldout.py`. 100 answers constructed near the truth
across items 000 (free), 003 and 006 (theory), 004 (memorised), each graded by
calling `grade_frame_exact` directly with the item rebuilt from the answer key —
the rubric was not edited.

### Structural invariants — both hold

| examinee | verdict counts | score |
|---|---|---|
| `oracle` | `{correct: 8}` — **no `wrong`, ever** | 1.000 |
| `null` | `{unanswered: 8}` — **never `correct`; silence is not paid** | 0.000 |
| `memoriser` | `{correct: 6, wrong: 2}` | 0.750 |
| `bluffer` | `{correct: 4, wrong: 4}` | 0.500 |

Across all 100 stress answers, `correct` was returned **only** for answers whose
cell content equals `frame_after` exactly. Nothing near-but-not-truth was paid.

### Verdicts that are right

`transposed correct grid` → `wrong` (7x9 vs 9x7; `_diff` at :124-132 returns
`shape_ok=False`). `one cell changed to another legal colour` → `wrong`.
`ragged (one short row)` → `wrong` (:110). `short grid (6 rows)` → `wrong`.
`colour 2 or 9, outside this world's palette {0,1,6}` → `wrong` (:106, palette
taken from `truth.legal_cells`, so a *correct* answer can never be rejected this
way). `bare grid` and `{"frame_after": grid}` → both `correct` (:88-90).
`{"abstain": true}` and the strings `"abstain"`, `"unknown"`, `"I cannot tell"`,
`"ABSTAIN"` → `abstained` (:115-121). Bool cell → `wrong` (:104, and the comment
there is correct — `True == 1` would otherwise silently pass as a wall).
`json null` → `unanswered` (:138-142). Correct-content-but-two-agents and
correct-but-agent-erased → `wrong`, so exactness covers the invariants the
rubric never checks.

### Verdicts that are arguably wrong

Ordered by how much I would push back. All score 0 either way; the damage is to
the **verdict class**, which is what `axes()` (`heldout_worldgen.py:342-343`) and
`discrimination._classify` (`discrimination.py:95-114`) read.

| # | answer | verdict | a fair examiner would say | why it matters |
|---|---|---|---|---|
| 1 | `{}` (empty dict) | `wrong` | `unanswered` | `mark.py:51-53` already calls a **missing key** `unanswered`, and `rubrics_heldout.py:138-142` calls `null` `unanswered` "which is what it is". `{}` is the third way of submitting nothing and is the only one scored as a *prediction*. An examinee that returns `{}` on every item is classified `dead` on every item by `discrimination.py` — i.e. reported as a **marker defect** ("nobody can score it, oracle included") when the truth is a silent examinee. |
| 2 | `{"frame_after": null}` | `wrong` | `unanswered` | The documented wrapper (the instructions on the sheet promise exactly this key) used to say "no prediction". Same conflation as #1, reached through the *encouraged* answer shape. |
| 3 | `[]` (empty list) | `wrong` | `unanswered` | `_as_frame` :94 rejects empty lists before any content check. Same conflation. |
| 4 | correct grid as strings `[["1","1",…]]` | `wrong` | `correct`, or at minimum not `wrong` | The rubric's own stated principle (:80-84) is that "an examinee that predicts the world correctly and wraps it differently has not made a prediction error, and a rubric that scored it as one would be marking JSON conventions." A cell-for-cell correct grid whose cells are numeric strings is precisely a different JSON convention. The rubric accepts two *wrappers* on that argument and then refuses the same argument one level down. |
| 5 | correct grid as floats `[[1.0,…]]` | `wrong` | `correct` | Sharper than #4 because it is reachable *without the examinee doing anything*: JSON has no int/float distinction, and `json.loads("[[6.0]]")` yields floats. Confirmed by round-tripping the true frame through `json.dumps/loads` — the int version stays `correct`, the float version becomes `wrong`. A correct world model plus one serialiser that writes `6.0` scores zero. |
| 6 | `{"frame_after": {"abstain": true}}` | `wrong` | `abstained` | `_as_frame` recurses into the wrapper, hits the abstain dict, returns `None`, and `None` from `_as_frame` means "malformed" (:149-154). A nested abstention is indistinguishable from a malformed grid. |
| 7 | prose other than the four accepted strings — `"I don't know"`, `"no prediction"`, `"unsolvable"` | `wrong` | `abstained` | :119-120 is a closed four-item allowlist. The module docstring (:19-21) argues abstention exists so a report can say whether an examinee knew it did not know; a four-string allowlist decides that by vocabulary. `"unsolvable"` is the specific word Theoria.md 1.11 cares about and it is marked as a wrong *frame*. |
| 8 | `{"abstain": true, "frame_after": <correct>}` | `abstained` | `correct` | `_is_abstention` (:145) fires before `_as_frame`, so a correct prediction accompanied by an abstain flag earns nothing. Low severity — the submission is self-contradictory — but the precedence is undocumented. |

Two smaller notes, not misjudgements:

* `{"frame": …}` and `{"after": …}` are accepted as wrappers (:88) but are not in
  the sheet's instructions, while `{"grid": …}`, `{"prediction": …}`,
  `{"answer": …}` are `wrong`. An undocumented, asymmetric allowlist.
* An out-of-palette colour and a wrong shape produce the *same* detail
  (`"answer is not a well-formed frame"` plus `expected_shape`), because the
  palette check at :106 runs before any shape check. Diagnostic only.

**Nothing here changes any score on this world**, since every arguable case is
worth 0 either way. What it changes is the `unanswered` / `abstained` / `wrong`
split, and therefore what `discrimination.py` would call a fifth examinee.

---

## 3. Cheap examinee vs the bluffer floor — **yes, decisively: 8/8, and the crude version exposes a worse problem**

Bluffer floor = 4/8 = **0.500** (= `notes.unchanged_frame_share`, 0.5). Four
strategies, each reading only `frame_before`, `action`, `legend` and the grid
dimensions from `item.paper`; none touches `ground_truth.json`, `item.truth`, or
`raw_trace.jsonl`. Scored through the real `mark()` with the real key.

| strategy | score | replay | heldout | gap | free | memorised | theory |
|---|---|---|---|---|---|---|---|
| `bluffer` (the floor) | 4/8 = **0.500** | 0.50 | 0.50 | 0.00 | 4/4 | 0/2 | **0/2** |
| `always-move` — move the agent one cell in the action's direction, no obstacle model at all | 4/8 = **0.500** | 0.50 | 0.50 | 0.00 | **0/4** | 2/2 | **2/2** |
| `legend-walker` — same, but do not move if the target is off-grid or holds the colour the legend calls `wall` | 8/8 = **1.000** | 1.00 | 1.00 | 0.00 | 4/4 | 2/2 | **2/2** |
| `blind-walker` — same, with the obstacle colour inferred as the value tiling the whole border and the mover as the rarest value; the legend is never read | 8/8 = **1.000** | 1.00 | 1.00 | 0.00 | 4/4 | 2/2 | **2/2** |

Three findings, in order of severity.

**(a) The paper is fully solved by ~25 lines with no world model.**
`legend-walker` ties the oracle at 8/8 and captures **2/2 of the theory
residue**. It contains no knowledge of this world: it applies the stock
gridworld prior "an action named for a direction moves the mover that way unless
a wall is in the way", reading the word `wall` off the legend that is printed on
the sheet. `blind-walker` removes even that, inferring the obstacle colour from
the border of the picture, and also scores 8/8. On this world "requires a world
model" means "requires the single most common prior about grids".

**(b) The total score is not monotone in theory.** `bluffer` and `always-move`
both score exactly **0.500**, and their correct-sets are **disjoint**:
bluffer gets {000, 001, 002, 007} and nothing else; always-move gets
{003, 004, 005, 006} and nothing else. One holds no theory at all; the other has
captured the entire informative residue (2/2 theory, 2/2 memorised). The paper's
headline number cannot tell them apart, and neither can `gap_replay_minus_heldout`
(0.00 for both). This is the failure mode `discrimination.py`'s docstring warns
about, realised: the free items are numerous enough to exactly offset the
informative ones.

**(c) The headline axis is capped.** `heldout` has a floor of 0.5 on this world
(two of its four items are `free`) and `replay` a ceiling of 1.0, so
`gap_replay_minus_heldout` ∈ [−0.5, +0.5], half its nominal range. The
calibration `memoriser` sits exactly at the ceiling (0.500), so the axis cannot
distinguish a memoriser from anything more memorising than a memoriser.

Honest caveat: (a) is a strong result *about this world only*. `t1-walk-maze` is
the catalogue's declared floor ("No mechanism at all", `spec.json:24`), so a
stock prior solving it is not a scandal — it is the control behaving like a
control. It becomes a scandal only if the same strategy scores well on tiers 2
and 3, which is outside my remit; I would run these four strategies across the
other nineteen worlds before drawing any conclusion.

---

## 4. Honest effective size — **2 items (25%), one rule, and too small to rank anybody**

**Items that genuinely require a world model: 2** — `t1-walk-maze-003` and
`t1-walk-maze-006`. Both are `walk`, both `heldout`. The paper's advertised size
is 8; quote 2.

**Dead weight, by name:**

* **`blocked_by_wall` — 4 of 8 items (50%), all `free`, zero discrimination.**
  Its consequent is "nothing changes" (`GROUND_TRUTH.md:24`), so its
  `frame_after` *is* the bluffer's answer. It cannot ever produce an informative
  item — not at another `per_class`, not on another world, not with a different
  sampler. Half this paper is a rule that is unfalsifiable-by-construction under
  a frame-exact rubric. (Structurally: any rule whose `then` is stasis is
  permanently `free`. On this world that is 1 of 2 rules; the catalogue-wide
  version of this observation is worth checking against the other nineteen.)
* **`walk` — 4 items, of which 2 are discounted to `memorised`** because the
  replay half is answerable from `raw_trace.jsonl` alone. That discount is
  deliberate and correct, but it means the informative yield of the world's only
  live rule is half its item count.

**The 25% is structural, not a small-sample artefact.** Profiling at
`per_class` ∈ {1, 2, 3, 6, 10, 18} gives `theory_share = 0.25` at *every* value,
with `effective_size == per_class` exactly and `free == 2·per_class`. The
composition is pinned by the rule count and the stasis rule, so no amount of
sampling changes the ratio — it only scales the residue. The feasibility ceiling
is `per_class = 18` (72 items, 18 theory items); `per_class = 19` refuses,
because `blocked_by_wall` has only 18 in-trace witnesses.

**Is the residue big enough to rank two examinees apart? No.** With 2 informative
items, the largest possible separation between two examinees on the residue is
2-0. Treated as a paired comparison (exact McNemar / sign test, 2 discordant
items all one way), that is p = 2·0.5² = **0.5** — a perfect sweep against a
total failure is indistinguishable from a coin. Even on all 8 items, the widest
real gap on this paper (oracle 8 vs bluffer 4, 4 discordant items) gives
p = 2·0.5⁴ = **0.125**. Six discordant items is the minimum for p < 0.05, so
**`per_class ≥ 6`** (24 items, 6 theory items) is the smallest build of this
world on which a clean sweep of the residue is a statistically defensible
ranking. As shipped, this world can *illustrate* a difference and cannot
*establish* one.

There is also a dependence problem the item count hides: both theory items
exercise the *same* rule under the *same* condition ("step onto open floor"), so
they are not two independent probes. Every strategy I wrote got both or neither.
The residue is better described as **one rule tested twice** than as two items.

---

## Found without being asked

1. **The `per_class=2` sheet never tests vertical movement.** Action histogram
   over the 8 items: `LEFT` 6, `RIGHT` 2, **`UP` 0, `DOWN` 0** — even though the
   candidate pools are full of both (`walk` heldout pool: RIGHT 8, LEFT 8, DOWN
   6, UP 6; `blocked_by_wall` heldout pool: UP 10, RIGHT 8, DOWN 7, LEFT 5). It
   is an accident of the sampling salt in `heldout_worldgen._pick`
   (:113-116), which sorts by `sha256(salt + key)` with no stratification over
   actions. Consequence: an examinee with a correct horizontal model and an
   inverted or broken vertical model scores 8/8. The gap closes on its own at
   `per_class ≥ 4` (UP 3, DOWN 2) and is comfortable at 6 (UP 5, DOWN 5) — a
   second reason to prefer `per_class = 6` for this world. A stratified pick,
   or simply reporting the per-action histogram alongside `by_rule`, would make
   this visible instead of latent.

2. **Two items chain.** `t1-walk-maze-005`'s `frame_before` is exactly
   `t1-walk-maze-004`'s `frame_after` (agent at (1,2) in both). An examinee that
   reads the whole sheet can infer that LEFT moved the agent one cell, from the
   sheet alone, without any theory — a small extra channel by which the
   `theory` label overstates what the items demand. Enumeration-plus-hash
   sampling has no de-adjacency constraint.

3. **`discrimination.py` cannot represent the "cheap prior" examinee.** Its
   three voters span "knows everything", "knows the trace", "knows nothing", and
   a fourth strategy that knows only a generic prior lands *outside* the lattice:
   `always-move` is correct on exactly the items the bluffer is wrong on. The
   module docstring already concedes this limit ("a fourth strategy nobody has
   written could settle it for free"); this world is a concrete instance, and
   `legend-walker` would be a cheap fourth voter to add — it costs ~25 lines and
   would reclassify all 8 items here as free.

4. **A silent examinee can be reported as a marker defect.** Combining §2 #1
   with `discrimination._classify`: an examinee submitting `{}` per item is
   `wrong` everywhere, so if it were ever used as a voter the classifier would
   emit `dead` — which the module documents as "a **marker defect**, not a
   difficulty… reported separately and loudly". The three current voters never
   do this, so nothing is broken today; the failure is latent in the
   `{}`→`wrong` mapping.

---

### Reproduction

All results above come from four throwaway scripts run against the worktree with
`sys.path` set to its root; nothing in the repo was modified. The load-bearing
calls are `heldout_worldgen.build_for("t1-walk-maze", pc)`,
`Paper.key(registry.digest())`, `rubrics_heldout.grade_frame_exact(answer, truth,
item)` on items rebuilt from the key, `grading.mark.mark(...)` with
`axes_fn=heldout_worldgen.axes`, and
`tools.discrimination.profile_world("t1-walk-maze", pc)`.
