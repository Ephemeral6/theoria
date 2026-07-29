# Independent examination — `t1-cycler-gate`

Examiner: independent, read-only. Paper `v2-heldout-t1-cycler-gate`, `per_class=2`,
8 items, rubric digest `e06bdf52…1cb091`. Everything below is local python against
`worldgen/out/worlds/t1-cycler-gate/` and `exam/`; no file was edited, no network,
no `git`.

**Headline.** The classification is arithmetically correct and I found no defect in
`discrimination.py` itself. But the world's honest effective size is **0**, not 2 —
and there is a **leak that the repo's own leakage gate fails this paper on, on all
eight items**, because the worldgen paper builder is not wired into that gate.

---

## 0. The world, in one paragraph

6×7 board, solid wall border, 4×5 open interior (rows 1–4, cols 1–5). Agent starts
(2,2), goal (4,5), one cycler at **(2,4)** with `k=3`, `open_phase=2`, `phase0=0`.
Palette `{floor:0, wall:1, cycler:2, cycler_1:3, cycler_2:4, agent:6}`. 58 reachable
states, 232 reachable transitions, `frame_determines_state.injective = true`.

Four declared rules (`GROUND_TRUTH.md`): `walk`, `blocked_by_wall`,
`walk_through_cycler`, `advance_cycler`. Firing counts over the reachable relation:

| rule | transitions | static (frame unchanged) | in trace | held out |
|---|---:|---:|---:|---:|
| `walk` | 166 | 0 | 54 | 112 |
| `blocked_by_wall` | 54 | **54** | 14 | 40 |
| `advance_cycler` | 8 | 0 | **1** | 7 |
| `walk_through_cycler` | 4 | 0 | **0** | 4 |

**Only two of the four rules reach the paper.** `advance_cycler` is blocked
(`heldout_worldgen.plan` → `in_trace: 1 < 2`) and `walk_through_cycler` is blocked
(`in_trace: 0`). The published `raw_trace.jsonl` pushes the gate exactly once
(line 51→52, `t=50` RIGHT from (2,3), colour 2→3) and never again; it never reaches
phase 2, so **colour 4 never appears in the trace at all**. The world's entire
defining mechanism — the cycler this world is named for — contributes **zero items**.

---

## 1. Is the classification true of the actual mechanics?

**Yes, on all eight items — verified, not spot-checked.** I re-implemented the
transition function from `spec.json` plus the `GROUND_TRUTH.md` rule table
(deliberately *not* calling `GridWorld`, so this is a second implementation, not a
tautology), read the cycler phase off the frame colour, and recomputed every item.

| item | class | rule | split | action | agent | phase | target | Δframe | recheck |
|---|---|---|---|---|---|---:|---|---|---|
| `t1-cycler-gate-000` | memorised | walk | replay | UP | (2,1) | 0 | floor (1,1) | yes | OK |
| `t1-cycler-gate-001` | **theory** | walk | heldout | LEFT | (4,3) | 2 | floor (4,2) | yes | OK |
| `t1-cycler-gate-002` | free | blocked_by_wall | heldout | UP | (1,5) | 0 | **wall (0,5)** | no | OK |
| `t1-cycler-gate-003` | **theory** | walk | heldout | LEFT | (1,3) | 0 | floor (1,2) | yes | OK |
| `t1-cycler-gate-004` | free | blocked_by_wall | replay | DOWN | (4,3) | 1 | **wall (5,3)** | no | OK |
| `t1-cycler-gate-005` | memorised | walk | replay | RIGHT | (4,1) | 0 | floor (4,2) | yes | OK |
| `t1-cycler-gate-006` | free | blocked_by_wall | heldout | DOWN | (4,2) | 2 | **wall (5,2)** | no | OK |
| `t1-cycler-gate-007` | free | blocked_by_wall | replay | DOWN | (4,1) | 0 | **wall (5,1)** | no | OK |

Every recomputed `frame_after` equals the recorded one, cell for cell. Every
recomputed rule name equals the recorded one. **Defects found: none.**

* No `free` item changes the frame. All four are the agent walking into the top or
  bottom wall row; `blocked_by_wall`'s `then` is literally "nothing changes", so this
  is structural, not luck.
* Both `theory` items change the frame.
* No `dead` item, and none is possible here: the oracle answers from `truth` and the
  marker accepts it (§2).

### The cycler question you flagged: the phase is never needed

**No item on this paper requires a hidden phase, and none could.** Look at the
`target` column: not one of the eight items has the cycler cell (2,4) as its target.
Every target is a border wall or plain interior floor. The cycler colour on the
sheet (2 on five items, 3 on one, 4 on two) is **pure decoration** — it distinguishes
the transition keys, and plays no part in any answer. Overwrite it with any legal
colour and all eight answers are unchanged.

Even if an item *did* touch the gate, the phase would still be readable: the
`color_reads_phase` invariant holds on all 58 states, and
`frame_determines_state.injective = true`. There is exactly one frame configuration
in the whole world where the phase is hidden — the agent standing **on** the open
cycler at (2,4), which renders as agent-6 — and even that is unambiguous, because
the agent can only stand there when `phase == open_phase == 2`.

So: this world's time-varying mechanism is not a source of hidden state on this
paper. It is not a source of anything on this paper.

---

## 2. Does the marker misjudge anything?

I graded 66 near-answers (22 constructions × 3 items: `-001` theory/walk,
`-002` free/blocked, `-005` memorised/walk) by calling
`rubrics_heldout.grade_frame_exact` directly. The rubric was not edited.

**Verdicts that are right, and worth recording as right:**

| construction | verdict | pts | detail |
|---|---|---:|---|
| bare correct grid | `correct` | 1.0 | `cells_wrong: 0` |
| `{"frame_after": …}`, `{"frame": …}`, `{"after": …}` | `correct` | 1.0 | all three wrappers accepted |
| tuple-of-tuples | `correct` | 1.0 | |
| transposed (6×7 → 7×6) | `wrong` | 0.0 | `shape_ok: false, cells_wrong: -1` |
| one cell changed | `wrong` | 0.0 | `cells_wrong: 1` — no partial credit, by design |
| colour 5 (outside palette `[0,1,2,3,4,6]`) | `wrong` | 0.0 | malformed |
| ragged row / short grid / extra row | `wrong` | 0.0 | |
| `{"abstain": true}`, `"abstain"` | `abstained` | 0.0 | |
| `null` | `unanswered` | 0.0 | |

`_legal_cells` (`rubrics_heldout.py:59`) correctly picks up this world's six-colour
palette from `truth["legal_cells"]` rather than A0's hardcoded `{0,2,4,8}`
(`:56`) — a correct answer to this paper is not rejected as malformed. Confirmed on
all three items.

### Three verdicts a fair examiner would give differently

**(a) `{"abstain": true, "frame_after": <the exactly correct grid>}` → `abstained`,
0.0.** This is the only case in my sweep where a **correct prediction earns zero**.
`_is_abstention` (`rubrics_heldout.py:115`, called at `:144`) fires before
`_as_frame` ever runs, and `_as_frame` short-circuits on the same key at `:86-87`,
so the correct grid sitting in the same object is never looked at. A fair examiner
reading "here is my predicted frame, and I am flagging that I am unsure" marks it
**correct** — the examinee predicted the world correctly. The rubric's own docstring
(`:19-21`) says abstention exists "so a report can say whether an examinee knew it
did not know"; it was not meant to be a way to discard an answer that is present and
right. Severity: low frequency, but it is a false negative on ground-truth-quality
output, which is the one class of error the module is otherwise built to avoid.

**(b) `{}`, `[]`, and `{"frame_after": null}` → `wrong`, while `null` → `unanswered`.**
All four are "the examinee submitted nothing usable". Three of them are recorded as
a *wrong prediction*. Nothing is paid (all 0.0), so the "silence is never paid"
invariant survives — but "silence is *reported* as silence" does not. An examinee
that emits `{}` on all eight items produces a report reading `wrong: 8`,
indistinguishable from an examinee with a bad world theory, and `axes()`
(`heldout_worldgen.py:342-343`) counts `abstained` and `unanswered` and will show 0
for both. A fair examiner calls an empty submission `unanswered`. The inconsistency
between bare `null` (`unanswered`) and `{"frame_after": null}` (`wrong`) has no
defensible reading at all — they are the same statement in two syntaxes.

**(c) A correct grid typed as strings, or with `true`/`false` for 1/0, collapses into
the same `wrong` bucket as a genuinely mispredicted frame.** `detail.why` says
`"answer is not a well-formed frame"`, but the verdict, the score, and every axis
are identical to a real prediction error. This is exactly the distinction the module
argues for in the abstention case at `:19-21` and then does not make for formatting.
There is no `malformed` member of `VERDICTS`. Not a scoring error — a reporting one,
and it is the reading `worldgen_port.legal_cells` (`:173-181`) explicitly warns
about: "a malformed-answer verdict reads on a report as an examinee that cannot
format JSON".

### The two structural invariants — both hold

Marked through `mark()` with `axes_fn=heldout_worldgen.axes`:

| examinee | score | verdicts | gap (replay − heldout) |
|---|---:|---|---:|
| `null` | 0/8 | `unanswered: 8` | 0.00 |
| `oracle` | 8/8 | `correct: 8` | 0.00 |
| `memoriser` | 6/8 | `correct: 6, wrong: 2` | 0.50 |
| `bluffer` | 4/8 | `correct: 4, wrong: 4` | 0.00 |

* **Silence is never paid** — `null` is `unanswered` on all 8, awarded 0.0 on all 8.
  Asserted, holds.
* **Ground truth is never marked wrong** — `oracle` produces `correct` on all 8, zero
  `wrong`. Asserted, holds.
* No two items share a `(frame_before, action)` pair, so no item is aliased to
  another.

---

## 3. A cheap examinee that beats the bluffer floor

Bluffer floor: **4/8 = 0.500** (the four `blocked_by_wall` items).

I wrote **`walker`**, which reads only `item.paper` — `frame_before`, `action`,
`legend`, `grid`. It never opens `ground_truth.json`, never touches `item.truth`,
never reads `raw_trace.jsonl`. Its entire theory is one sentence:

> Find the cell holding the legend's `agent` colour. Step one cell in the direction
> of `action`. If that lands outside the grid or on the legend's `wall` colour,
> return the input frame unchanged. Otherwise repaint the vacated cell as `floor` and
> the target cell as `agent`.

It knows nothing about cyclers, phases, `open_phase`, or `k`.

| examinee | score | free | memorised | theory |
|---|---:|---:|---:|---:|
| bluffer (floor) | 4/8 = 0.500 | 4/4 | 0/2 | 0/2 |
| memoriser | 6/8 = 0.750 | 4/4 | 2/2 | 0/2 |
| **`walker`** | **8/8 = 1.000** | 4/4 | 2/2 | **2/2** |
| oracle (ceiling) | 8/8 = 1.000 | 4/4 | 2/2 | 2/2 |

**It beats the floor by 4 items and captures 2 of 2 of the `theory` residue — the
whole of it. It ties the oracle. `replay = heldout = 1.00`, `gap = 0.00`.**

To pre-empt the objection that reading `legend` is a form of world knowledge, I also
ran **`walker_no_legend`**, which is handed no names at all: it induces the wall
colour as "the value filling the entire outer border", the floor colour as "the
commonest non-wall value", and the agent colour as "the rarest non-wall value". Same
result: **8/8**, `theory` 2/2.

This is not a peek and not a trick. It is the single most generic heuristic anyone
would write for a grid, and this paper cannot tell it apart from a correct world
theory.

**Where `walker` actually breaks.** Over the full 232-transition reachable relation
it is right on **220 (94.8%)**. Its 12 failures are:

* the **8 `advance_cycler`** transitions (agent bumps a shut gate: agent does not
  move, gate colour advances) — `walker` moves the agent and does not touch the
  colour;
* **4 `walk`** transitions, all from agent-at-(2,4), i.e. standing on the open gate
  and stepping off in each of the four directions. `walker` repaints the vacated cell
  as floor-0; the truth restores `cycler_2` = 4. These four are the *only* place in
  the world where the frame does not display the phase, and therefore the only
  `walk` transitions that genuinely need the rule "the agent can only be standing
  there if the gate is open".

**The paper samples none of these twelve.** That is the whole of the world's real
difficulty, and the sheet does not touch it.

---

## 4. Honest effective size

**Items that genuinely require a world model: 0 of 8.**

`discrimination.json` reports `effective_size: 2`. The number is a correct
application of the definition, but the definition rests on three voters, and none of
them is the obvious fourth. `discrimination.py`'s own docstring (`:59-67`) names this
limit — "a fourth strategy nobody has written could settle it for free, and the
taxonomy would not notice". On this world that strategy is thirty lines long and
scores full marks.

Why `theory` is 2 here has nothing to do with theory: items `-001` and `-003` are
`theory` **solely because they are `walk` items in the `heldout` split**, and the
memoriser is defined (`heldout_worldgen.py:290-295`) to predict stasis outside the
trace. Any examinee that moves the agent when the target is free gets them. The
label is measuring the memoriser's stipulated blind spot, not the item's difficulty.

### Dead weight, by name

**`blocked_by_wall` — 4 of 8 items (50%), and it is dead by construction, not by
accident.** Its `then` clause is "nothing changes", so *every one of its 54 reachable
transitions is static* — the bluffer scores 54/54. It cannot produce a `memorised` or
a `theory` item in this world at any `per_class`, and (since the clause is the same
everywhere) it cannot in any other world either. `discrimination.py` already names it
`barren`; the stronger statement is that it is **provably** barren from the rule
table alone, and could be excluded before an item is ever built. Half of this paper
is spent on it.

**`walk` — 4 of 8 items, of which 4 of 4 fall to `walker`.** Not dead in principle,
but on this board the only interesting `walk` transitions are the 4 that step off the
open gate, and the sampler picked none of them (all four `walk` items have the agent
on plain floor).

**`advance_cycler` and `walk_through_cycler` — excluded entirely**, by the
matched-quota rule, because the published trace pushes the gate once and opens it
never. This is the finding that matters: the world is called `t1-cycler-gate`, its
`spec.notes` calls it "the cheapest world in the catalogue for which the naive
'colour means state' reading is right", and **the exam set in it never once mentions
the gate.**

### Is the residue enough to rank two examinees apart?

**No.** With `theory = 2` nominal and `0` real, the paper's discriminating power
between two competent examinees is nil. Its only live signal is
`gap_replay_minus_heldout`, and even that is degenerate: the memoriser's 0.50 gap
comes entirely from two `walk` items that any grid heuristic answers, so an examinee
scoring gap ≈ 0 has demonstrated only that it can move a token one square.

Two examinees can be separated on this paper only if one of them is worse than a
thirty-line heuristic.

### One concrete fix, measured

`per_class` interacts non-monotonically with informativeness here, which is worth
knowing because the intuition runs the other way:

| `per_class` | items | usable rules | free | memorised | theory | `walker` score | theory captured by `walker` |
|---:|---:|---|---:|---:|---:|---|---|
| **1** | 6 | **`advance_cycler`**, `blocked_by_wall`, `walk` | 2 | 2 | 2 | **4/6** | **1/2** |
| 2 (shipped) | 8 | `blocked_by_wall`, `walk` | 4 | 2 | 2 | 8/8 | 2/2 |
| 3 | 12 | `blocked_by_wall`, `walk` | 6 | 3 | 3 | 12/12 | 3/3 |

**`per_class=1` produces a strictly more discriminating paper than `per_class=2` on
this world** — fewer items, but `advance_cycler` clears its quota and the cheap
walker drops to 4/6 with only half the theory residue. Growing `per_class` past 2
adds nothing but free marks: at 3 the paper is 50% larger and `walker` still ties the
oracle. The real fix is upstream — the published trace needs a second gate push and
one pass through the open gate, which would qualify both cycler rules at
`per_class=2` and put the world's actual mechanism on its own exam.

---

## 5. Things you did not ask about

### 5a. The rule name is printed on the sheet. The repo's own leak gate fails this paper on all 8 items.

`heldout_worldgen.py:204` sets `tags=(split, "rule:%s" % cand["rule"])`, and
`Item.sheet_side` (`exam/model.py:108-110`) puts `tags` on the sheet. So every
examinee is shown, per item:

```
"tags": ["replay", "rule:walk"]          "tags": ["heldout", "rule:blocked_by_wall"]
```

This contradicts the module's own stated discipline 35 lines further down
(`heldout_worldgen.py:239-246`), which explains why `notes.quota` publishes counts
and not names: *"a sheet that lists them hands the examinee the alphabet it is being
asked to discover. The mapping lives in the truth file only."* It also contradicts
the item's own declared leak probe: `:203` sets `leak_probes=(cand["rule"],)` — the
bare strings `"walk"` and `"blocked_by_wall"` — and those strings are then printed
verbatim in the sheet entry of the very item that declared them. All 8 of 8.

It is a regression introduced by the worldgen port, not an inherited flaw: the A0
paper at `exam/papers/heldout.py:508` uses `tags=(split,)`.

This is not my judgement call. `exam/leakage.py:300` `check_paper` is the project's
own gate, and run by hand on this paper it raises:

```
LeakageError : v2-heldout-t1-cycler-gate leaks its own answers:
  [{'item_id': 't1-cycler-gate-000', 'check': 'probe', 'hits': ['walk']},
   {'item_id': 't1-cycler-gate-001', 'check': 'probe', 'hits': ['walk']},
   {'item_id': 't1-cycler-gate-002', 'check': 'probe', 'hits': ['blocked_by_wall']},
   … all eight …]
```

**Why it was never caught:** `check_paper` has exactly one caller,
`exam/tools/build_papers.py:72`, which iterates `exam.papers.BUILDERS`
(`exam/papers/__init__.py:33-38`) — and that dict maps `"heldout"` to
`exam.papers.heldout`, the A0 paper. `heldout_worldgen` is not in it. **All twenty
worldgen papers bypass the leakage gate entirely.** `build_papers.py`'s own docstring
promises "Every sheet is checked for leakage before it is written"; for the twenty
generated papers that sentence is not true.

**How much it is worth on this world.** I wrote two examinees that read the tag:

* `tag_reader` — "if the tag says `rule:blocked_by_wall`, echo the frame; otherwise
  slide the agent." It never checks a bound, a wall, or a colour to *decide*
  anything. **8/8.**
* `tag_only_stasis` — answers only the items whose tag says `rule:blocked_by_wall`
  (by echoing the input) and abstains on everything else. Zero grid reasoning of any
  kind, not even finding the agent. **4/8 — exactly the bluffer floor, reached by
  reading four strings.**

On a world where one of two rules is "nothing changes", printing the rule name is
printing the answer. Note also that `SHARED_KEYS` in `leakage.py:77-80` whitelists
`"tags"` for the *structural* check, so even if the gate were wired in, only the
probe check would have caught this — which it does.

Recommendation: change `heldout_worldgen.py:204` to `tags=(split,)`, matching
`heldout.py:508`, and add the twenty worldgen papers to whatever calls
`leakage.check_paper`. The `rule:` tag is still available on the key side via
`Item.key_side` (`model.py:112-115`) and in `truth["rule"]`, which is where `axes`
already reads it from (`heldout_worldgen.py:313`) — so nothing downstream needs it
from the sheet.

**Effect on the discrimination instrument:** none, and that is the point. All three
voters in `VOTERS` (`discrimination.py:87`) answer from `paper["frame_before"]` and
`truth`; none reads `tags`. The instrument is structurally blind to this leak and
will keep reporting `theory: 2` on a paper whose answers are printed on it.

### 5b. Colour 4 appears on the sheet but never in the published trace

`cycler_2` = 4 appears in 2 of 8 sheets (`-001`, `-006`) and in **zero** of the 71
trace frames (trace colours: `{0,1,2,3,6}`; palette: `{0,1,2,3,4,6}`). Both items
carrying it are `heldout`. So "this frame shows a colour I have never seen ⟹ this is
a held-out item" is sound at 2/2 on this paper.

Harmless today, because the split tag is printed on the sheet anyway. Worth recording
because it becomes a live channel the moment anyone removes that tag as a fix for
5a — the splits are *rule*-matched by construction but they are not
*colour-distribution*-matched, and nothing measures that.

### 5c. `Paper.check_leakage` does not exist

`exam/model.py:95` tells a builder that `Paper.check_leakage` "treats an empty probe
list on an item with a non-trivial truth as a failure". There is no such method
(`hasattr(Paper, "check_leakage") is False`). The behaviour it describes does exist,
but as `leakage.check_paper(..., require_probes=True)` (`leakage.py:321-326`). A
builder author following the docstring looks for a method on the object they hold,
does not find it, and concludes there is no gate — which is, as it happens, the state
5a is in.

### 5d. The reversibility stamp is honest, and it is the trace that is thin

`ground_truth.json` records `advance_cycler.max_witnesses = 2` and scores the world
`reversibility_score: 1.0` — 4 of 4 rules re-witnessable. That is true of the *world*.
The exam is blocked on it anyway, because feasibility is measured against the
*published trace*, which witnessed it once. The A0′ criterion the factory stamps
("a rule witnessed exactly once has no second witness to hold out") is satisfied by
the world and violated by the artefact. Worth stating plainly, because a reader of
`GROUND_TRUTH.md` alone would conclude this world is exam-ready on all four rules.

---

## Reproduction

Read-only python, run from the worktree root; no pytest, no writes to the repo.

```python
from exam.papers import heldout_worldgen as hw, worldgen_port as port
from exam.grading.registry import digest
from exam import leakage
p = hw.build_for("t1-cycler-gate", 2)
hw.plan("t1-cycler-gate", 2)          # blocked: advance_cycler 1/7, walk_through 0/4
p.sheet(digest())["items"][0]["tags"] # ['replay', 'rule:walk']       <- 5a
leakage.check_paper(p, p.sheet(digest()), key_doc=p.key(digest()))  # raises  <- 5a
```
