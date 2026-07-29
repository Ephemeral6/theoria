# Examiner's report — `t3-cycler-portal-lock`

Independent audit of the discrimination profile at
`exam/runs/20260728T151000Z-V7-exam-stress-fanout/worlds/t3-cycler-portal-lock.json`.
Read-only on every existing file; no network, no LLM, no `git`, no `pytest`.

Method: I re-implemented this world's transition function and renderer from
`spec.json` plus the prose of `GROUND_TRUTH.md` alone, without calling
`GridWorld.explain`, and used it to recompute every item. `GridWorld` was used
only to build the paper (the instrument under test) and, at the end, as the
thing my model was checked *against*.

**Headline.** The classification is exactly right, and it is also nearly
vacuous. All 16 items reproduce; the six `theory` items are genuinely
answerable — none depends on hidden state. But a 40-line answer strategy that
reads nothing but the printed frame, the printed legend and four generic
grid-game priors scores **16/16**, including 6/6 on the `theory` residue, with
`gap_replay_minus_heldout = 0.0`. The paper's honest effective size against a
theory-free-but-not-stupid examinee is **0 items**, not 6.

---

## 1. Is the classification true of this world's mechanics?

### 1.1 Independent recomputation

I decoded each `frame_before` into `(agent cell, cycler phase, token bits)`,
applied my own transition function, re-rendered, and compared.

* **All 16/16 items**: my `frame_after` equals the recorded `truth.frame_after`,
  and my rule tag equals the recorded `truth.rule`. Zero mismatches.
* **All 16/16 items**: my class (derived from `frame_changes` and `split`)
  equals the recorded `class`. Zero mismatches.

Hand-checked items, by class (every item in the paper, since there are only 16):

| item | agent | action | phase | tokens | rule I derived | recorded class | frame changes |
|---|---|---|---|---|---|---|---|
| `-001` | (1,6) | LEFT | 1 | (1,0) | `blocked_by_wall` | free | no |
| `-006` | (1,1) | LEFT | 1 | (0,0) | `blocked_by_wall` | free | no |
| `-007` | (4,8) | LEFT | 0 | (1,0) | `blocked_by_wall` | free | no |
| `-009` | (4,1) | LEFT | 0 | (0,0) | `blocked_by_wall` | free | no |
| `-000` | (6,4) | RIGHT | 1 | (0,0) | `walk` | memorised | yes |
| `-004` | (6,1) | RIGHT | 0 | (0,0) | `walk` | memorised | yes |
| `-003` | (6,1) | UP | 0 | (0,0) | `teleport_twoway` | memorised | yes |
| `-010` | (6,1) | UP | 1 | (0,0) | `teleport_twoway` | memorised | yes |
| `-013` | (3,1) | RIGHT | 1 | (0,0) | `walk_through_cycler` | memorised | yes |
| `-015` | (3,3) | LEFT | 1 | (1,0) | `walk_through_cycler` | memorised | yes |
| `-005` | (4,1) | UP | 1 | (1,1) | `walk` | theory | yes |
| `-008` | (4,6) | DOWN | 1 | (0,0) | `walk` | theory | yes |
| `-002` | (3,3) | LEFT | 1 | (0,1) | `walk_through_cycler` | theory | yes |
| `-011` | (3,1) | RIGHT | 1 | (1,0) | `walk_through_cycler` | theory | yes |
| `-012` | (4,8) | DOWN | 0 | (1,1) | `teleport_twoway` | theory | yes |
| `-014` | (6,8) | UP | 1 | (0,1) | `teleport_twoway` | theory | yes |

No `free` item changes the frame; every `theory` item does. **No defect in the
instrument on this world.**

### 1.2 Whole-graph cross-check

Not content with 16 items, I ran my independent model against `GridWorld` over
the entire reachable relation:

* 262 reachable states × 4 actions = **1 048 transitions**; my rendered
  successor and my rule tag agree with `worldgen/core/world.py:188 explain()`
  on **all 1 048**. Zero disagreements.
* My renderer round-trips through my frame decoder on all 262 states.

### 1.3 The hidden-phase question — answered no, three ways

You asked whether any of the six informative items is informative only because
its answer turns on a phase the examinee cannot see. **It does not, and the
margin is not thin.**

1. **The frame determines the state, measured.** `ground_truth.json`
   `frame_determines_state` reports `{states: 262, distinct_frames: 262,
   injective: true, collisions: []}`. I recomputed it independently: 262
   distinct rendered frames from 262 states, **0 collisions**. Since the
   transition is a function of (state, action) and the state is a function of
   the frame, every item's answer is a deterministic function of what is
   printed on the sheet. There is no hidden variable to be unlucky about.

2. **The one channel that could hide the phase is closed by the geometry.**
   The `color_reads_phase` invariant exempts the cell the agent stands on
   (`worldgen/mechanisms/color_cycle.py:172`), so an agent standing on the
   cycler would in principle hide the phase. Four reachable states have the
   agent on the cycler cell (3,2) — and **all four have phase 1**, which is the
   `open_phase`. That is forced, not lucky: `interact`
   (`color_cycle.py:101`) only admits the agent when `phase == open_phase`, and
   `reserved()` is empty (`color_cycle.py:90`) only because a shut cycler is in
   `occupied`. So agent-on-cycler implies phase 1, and nothing is concealed.
   Separately, **no item's `frame_before` puts the agent on the cycler, on a
   portal mouth, on a token or on the lock** — all 16 start on plain floor.

3. **The phase is not merely visible, it is not even needed.** All four cycler
   items in the paper are `walk_through_cycler`, i.e. phase already open. The
   rule where the phase actually matters, `advance_cycler`, is excluded from
   the paper by the matched quota (§4). A strategy that never looks at the
   cycler's colour answers all four correctly — see §3.

The lock's global count is likewise fully readable: the number of colour-3
cells is the uncollected count (`count_lock.py` `token_count` invariant), and
the lock at (5,4) shows colour 4 iff `collected < 2`. An agent can only reach a
token cell by collecting it, because `count_lock.py:88 reserved()` blocks any
teleport landing on an uncollected token — so "agent on token cell" is
unambiguously "collected".

**Verdict on Q1: the profile is correct, and none of the six informative items
is unanswerable-in-disguise.** This world is the good case in exactly the sense
you hoped: hard-looking without being unfair.

---

## 2. Does the marker misjudge anything?

Stressed by importing `exam.grading.rubrics_heldout` and calling
`grade_frame_exact` directly on items `-000` (memorised/walk), `-001`
(free/wall), `-002` (theory/cycler) and `-012` (theory/portal). **Every case
below behaved identically on all four items**, so the verdicts are properties
of the rubric, not of an item.

### 2.1 Structural invariants — both hold

| examinee | verdicts | score |
|---|---|---|
| `oracle` | 16 correct, **0 wrong** | 1.000 |
| `null` | **16 unanswered**, 0 correct | 0.000 |
| `memoriser` | 10 correct, 6 wrong | 0.625 |
| `bluffer` | 4 correct, 12 wrong | 0.250 |

Silence is never paid; ground truth is never marked wrong. `null` reaches
`unanswered` through `exam/grading/mark.py:51` (item absent from the answers
dict), not through the rubric.

### 2.2 The stress table (verdicts identical on all four probe items)

| answer | verdict | fair? |
|---|---|---|
| exact grid, bare | correct | yes |
| exact grid, `{"frame_after": …}` | correct | yes |
| exact grid, `{"frame": …}` / `{"after": …}` | correct | yes (undocumented but harmless) |
| exact grid as tuples of tuples | correct | yes |
| transposed (10×8) | wrong, `shape_ok=false, cells_wrong=-1` | yes |
| one cell changed | wrong, `cells_wrong=1` | yes |
| last row dropped | wrong, `shape_ok=false` | yes |
| ragged (row 0 truncated) | wrong, "not a well-formed frame" | yes |
| one cell out of palette (9) | wrong, "not a well-formed frame" | yes |
| `{"abstain": true}` | abstained | yes |
| `{"abstain": false}` + correct frame | correct | yes |
| bare string `"abstain"` | abstained | yes |
| `None` | unanswered | yes |
| cells as strings `"0"` | wrong | **arguable — see A** |
| whole grid as a JSON string | wrong | **arguable — see A** |
| `numpy.int64` cells / `numpy.ndarray` | wrong | **arguable — see A** |
| booleans in place of 0/1 | wrong | yes (documented, `rubrics_heldout.py:104`) |
| `{}` (empty dict) | **wrong** | **no — see B** |
| `[]` (empty list) | wrong | borderline (see B) |
| `{"abstain": true}` + correct frame | abstained | yes (see C) |

### A. Formatting failures are reported as `wrong`, not as their own verdict

`_as_frame` (`rubrics_heldout.py:75`) returns `None` for a correct prediction
encoded as strings, as a JSON string, or with `numpy` integers, and
`grade_frame_exact:151` turns that into `verdict="wrong"`. The `detail` carries
`"answer is not a well-formed frame"`, so a careful reader can tell — but the
verdict field cannot, and every aggregate in `axes()` and in
`discrimination.py` reads the verdict.

A fair examiner would say: *this examinee predicted the world correctly and
serialised it badly.* That is a different failure from predicting the wrong
frame, and this rubric's own docstring (`rubrics_heldout.py:50-55`) makes
exactly that argument in the other direction — it explains that A0's hardcoded
palette made every generated frame read "as an examinee that cannot format an
answer". The fix there was to widen the palette; the same reasoning says a
`malformed` verdict belongs alongside `abstained`. **Severity: moderate**, and
it matters more for LLM examinees than for the four synthetic ones, which never
mis-serialise. The `numpy` case is the likeliest to bite in practice: `numpy`
is a listed dependency of this repo and `np.int64` is not a Python `int`.

### B. `{}` is graded `wrong`; `None` is graded `unanswered`

This is the one I would call a genuine misjudgement. Both are "nothing was
submitted". `grade_frame_exact:138` catches `None` and returns `unanswered`
with `"why": "null answer"`; an empty dict falls through `_is_abstention`
(`:115`, no `abstain` key), then through `_as_frame`'s dict branch (`:88-91`,
no `frame_after`/`frame`/`after` key) to `return None` at `:91`, and is scored
`wrong`.

A fair examiner would return `unanswered` for `{}`. The consequence is not
cosmetic: `discrimination.py:144` classifies on `verdict == "correct"`, and
`heldout_worldgen.axes()` counts `unanswered` separately from wrong, so an
examinee that emits `{}` when it has nothing to say is recorded as having
guessed and missed on every such item — precisely the confusion the marker's
docstring (`mark.py:9-14`) says it exists to prevent. `[]` is the same path and
the same argument, though "empty grid" is a slightly more defensible reading of
a malformed answer.

### C. Abstention outranks a submitted frame

`{"abstain": true, "frame_after": <correct grid>}` scores `abstained`, because
`_is_abstention` (`:115`) is tested before `_as_frame` (`:149`). This is
defensible — an examinee that declares it cannot tell should be taken at its
word — but it is worth naming, because the *opposite* ordering inside
`_as_frame:86` (`abstain` checked first, then the frame fields) means the two
functions agree only by coincidence rather than by a shared rule. **Severity:
low.**

Nothing I could construct produced a *false `correct`*: I found no answer that
a fair examiner would call wrong and that this rubric pays for.

---

## 3. A cheap examinee for this world — it beats the floor, and then some

The bluffer floor is `unchanged_frame_share = 0.25` (4/16), reported by
`heldout_worldgen.py:249` and confirmed by the calibration run above.

I wrote a strategy that reads **only** `frame_before`, `action`, `legend` and
`grid` from `item.paper`. It never opens `ground_truth.json`, never touches
`item.truth`, never reads `raw_trace.jsonl`, and contains no world-specific
coordinate, phase or threshold. Its entire content is four generic grid-game
priors:

1. locate the agent by the legend's `agent` colour; the target is one step in
   the action's direction;
2. off-grid or `wall`-coloured target → the frame does not change;
3. `lock`-coloured target → the frame does not change (a colour named "lock"
   is a barrier); *never fires on this paper*;
4. `portal`-coloured target → the agent appears on the **other** cell of that
   colour, and its old cell becomes floor;
5. otherwise the agent walks in: old cell → floor, target cell → agent.

### Result: 16/16 = 1.000, including 6/6 on the `theory` residue

| class | cheap examinee | bluffer | memoriser | oracle |
|---|---|---|---|---|
| free (4) | 4/4 | 4/4 | 4/4 | 4/4 |
| memorised (6) | 6/6 | 0/6 | 6/6 | 6/6 |
| **theory (6)** | **6/6** | 0/6 | 0/6 | 6/6 |
| total | **16/16** | 4/16 | 10/16 | 16/16 |

`gap_replay_minus_heldout = 0.0`, `replay = 1.0`, `heldout = 1.0` — which
`heldout_worldgen.py:309` names as the signature of a rule-learner rather than
a memoriser. It captured **100 % of the theory residue** and beat the floor by
+0.75 absolute.

### Where the 12 marks above the floor come from — an ablation ladder

| strategy | score | free | memorised | theory |
|---|---|---|---|---|
| A. never move (bluffer) | 4/16 | 4/4 | 0/6 | 0/6 |
| B. + walk onto plain-floor targets only | 8/16 | 4/4 | 2/6 | 2/6 |
| C. + treat *every* non-wall colour as walkable | 12/16 | 4/4 | 4/6 | 4/6 |
| D. + legend name `portal` ⇒ swap to the other mouth | **16/16** | 4/4 | 6/6 | 6/6 |
| E. as D but with **no legend names at all**: "target colour appears exactly twice in the frame ⇒ swap to its twin" | **16/16** | 4/4 | 6/6 | 6/6 |

Three things are worth pulling out of that ladder.

* **Rung C is the expensive one.** "Anything that is not a wall can be walked
  into" is the single laziest possible prior, and it is worth +4 marks, 2 of
  them `theory`. It works because the only rule in this paper that punishes it
  (`advance_cycler`, where the cycler is shut and the agent bounces) was
  excluded by the quota. The paper contains four cycler items and every one of
  them is a *pass-through*, so the cycler is indistinguishable from floor.
* **Rung D does not need the legend.** Rung E shows the portal can be inferred
  purely structurally — "a non-floor, non-wall colour occupying exactly two
  cells is a paired teleport" — and gets the same 16/16. It works here only
  because the tokens (the other twice-occurring colour) are never a move target
  in this paper: `collect_token` is quota-excluded too.
* **The legend is nonetheless a real leak.** `worldgen_port.py:161 palette()`
  puts the spec's own mechanism names on the sheet: `portal`, `lock`, `token`,
  `cycler`, `cycler_1`, `cycler_2`. `heldout_worldgen.py:238-241` is explicit
  that rule *names* are withheld because "a sheet that lists them hands the
  examinee the alphabet it is being asked to discover" — but the legend hands
  over the same alphabet in the mechanism vocabulary. An examinee that knows
  what the English word "portal" means has been given `teleport_twoway` for
  free.

**Honest caveat.** This strategy is not a general theory of the world: it is
wrong on `advance_cycler` (16 reachable firings), on `blocked_by_lock` (16) and
on `walk_through_lock` (6). It scores 16/16 because *the paper does not contain
a single item from any rule that would refute it* — see §4. That is a fact
about the paper, not about the strategy's insight, and it is the finding.

---

## 4. Honest effective size, dead weight, and why this world leads the catalogue

### 4.1 Effective size

| measure | value |
|---|---|
| items on the paper | 16 |
| items the bluffer already has (`free`) | 4 |
| items separating only a trace-reader (`memorised`) | 6 |
| items the profile calls `theory` | 6 |
| **items surviving a cheap theory-free strategy (§3)** | **0** |

The profile's `effective_size: 6` is correct as defined — six items that
oracle-alone settles among *those three* voters. The instrument's own docstring
(`discrimination.py:60-67`) warns that a fourth strategy nobody wrote could
settle them for free. §3 is that fourth strategy, and it settles all six.
**Against a non-lazy theory-free examinee the effective size of this paper is
zero.**

### 4.2 Dead weight

`blocked_by_wall` is the only rule the profile names barren, and that is
generous: it accounts for 4 of 16 items (25 %) and 420 of the world's 1 048
reachable transitions, and it can never be anything but barren, because a rule
whose `then` is "nothing changes" makes `frame_after == frame_before`, which is
exactly the bluffer's answer.

The larger dead weight is invisible to the profile: **half of this world's
mechanics never reach the paper at all.** Per-rule witness counts (my
recomputation, matching `worldgen_port.feasibility`):

| rule | in trace | held out | changes frame | on the paper? |
|---|---|---|---|---|
| `walk` | 86 | 444 | yes | yes |
| `blocked_by_wall` | 52 | 368 | no | yes |
| `teleport_twoway` | 13 | 35 | yes | yes |
| `walk_through_cycler` | **2** | 6 | yes | yes (by one witness) |
| `advance_cycler` | 1 | 5 | yes | **no** |
| `blocked_by_lock` | 1 | 15 | no | **no** |
| `collect_token` | 1 | 13 | yes | **no** |
| `walk_through_lock` | 0 | 6 | yes | **no** |
| `blocked_portal_exit` | never fires | — | no | **no** |

So the world named `cycler-portal-lock` ships a paper in which:

* the **entire `count_lock` family is absent** — no token, no lock, no item in
  which the global collected count matters;
* the **cycler appears only in its open phase**, i.e. as floor with an unusual
  colour; the one rule that reads the phase is excluded;
* only the **portal** survives with its mechanics intact.

The composition that gives the world its name does not survive the quota
filter. What survives is walls, walk, a teleport, and a decorative tile.

### 4.3 Why this world leads — and the formula worldgen should target

I checked the arithmetic across all twenty per-world profiles in this run
directory (236 items). Two exact identities fall out.

**(i) The class is fully determined by two fields already in the truth.** On
all 236 items of all 20 worlds, without exception:

```
class = free       if not frame_changes
      = memorised  if frame_changes and split == "replay"
      = theory     if frame_changes and split == "heldout"
```

This follows from the definitions of the fakes at
`heldout_worldgen.py:286-295`: the bluffer is right iff the frame does not
change, and the memoriser is right iff the frame does not change *or* the split
is replay. On this question type `discrimination.py:95 _classify()` is
therefore a consistency check on the marker rather than a measurement — which
is a good thing to know about the instrument: its value is that `dead` and
`anomaly:` stay empty (they do here), not that the four-way split carries
information the truth file lacked.

**(ii) The theory share is `C / 2U`** where `U` = rules that pass the matched
quota and `C` = those of them that change the frame. Verified on 19 of 20
worlds:

```
t3-cycler-portal-lock  U=4  C=3  ->  3/8  = 0.375   (highest in the catalogue)
t2-switch-push         U=6  C=4  ->  4/12 = 0.333
t3-full-house          U=6  C=4  ->  4/12 = 0.333
t3-latch-maze          U=5  C=3  ->  3/10 = 0.300
eleven t1/t2/t3 worlds U=2  C=1  ->  1/4  = 0.250
t2-unsolvable-nodoor   U=3  C=1  ->  1/6  = 0.167
```

(The single exception is `t2-gravity-push`, reported 0.125 against a predicted
0.250 — one of its `walk` items has `frame_changes: false`, presumably a walk
that gravity settles back. Not my world, but the instrument should probably
flag a frame-changing rule that produced a non-changing item, since that is how
a `free` item smuggles itself in under a live rule's name.)

**So the answer to "what makes it best" is not the composition, and not the
tier.** `t3-full-house` is also tier 3, also composes three families, has 2 654
reachable states to this world's 262, and scores *lower*. The property is
arithmetic:

> Theory share is maximised by having **many frame-changing rules** and **as
> few no-op rules as possible** clear the ≥2-in-trace / ≥2-held-out bar.

`t3-cycler-portal-lock` wins because it is the only world in the catalogue
where exactly **one** no-op rule survives the quota while **three**
frame-changing rules do. Its other two no-op rules are eliminated by accident
of the published trace, not by design: `blocked_by_lock` fires 16 times in the
reachable graph but only **once** in the 161-frame trace, and
`blocked_portal_exit` never fires at all because the two mouths are eight
columns apart on open floor. Meanwhile `walk_through_cycler` scraped onto the
paper with **exactly 2** in-trace witnesses — the minimum. Had the explorer
bumped a wall next to the lock one more time, or crossed the cycler one time
fewer, this world would have tied at 0.333.

### 4.4 What `worldgen/` can do deliberately

1. **Cap the no-op rules that qualify, or stop paying for them.** Every no-op
   rule that clears the quota contributes exactly 4 free items and 0
   informative ones. `blocked_by_wall` clears it in every world, in every
   world, forever — it is a 4-item tax on every paper. Either exclude no-op
   rules from the quota (they are `frame_before == frame_after` by
   construction, so the paper module can detect them at
   `heldout_worldgen.py:127` without touching the truth), or pair each one with
   an item whose answer is *not* stasis. This alone would move every world from
   `C/2U` to `C/2C = 0.5`.
2. **Aim for `C ≥ 4` frame-changing rules with ≥2 trace witnesses each.** The
   binding constraint is the *trace*, not the world: this world has 8 firing
   rules and 4 of them fail on in-trace counts of 0 or 1. A longer or
   rule-directed exploration trace would qualify `collect_token`,
   `advance_cycler` and `walk_through_lock` and push `C` to 6 — and, far more
   importantly, would put on the paper the three rules that actually refute the
   cheap strategy of §3.
3. **The single highest-value change is to require that each paper contains at
   least one item that punishes "everything is walkable".** That is
   `advance_cycler` or `blocked_by_lock` here. Both exist in the world; both
   were filtered out; and their absence is why a 40-line heuristic scores
   1.000. A world's informative share should be measured against a
   *walk-in-anyway* baseline, not only against the bluffer.
4. **Vary the token bits less, or stop counting them as novelty** — see §5.1.

---

## 5. Things you did not ask about

### 5.1 Two of the six `theory` items are twins of `memorised` items, differing only in a causally irrelevant bit

| pair | agent | action | difference | classes |
|---|---|---|---|---|
| `-011` / `-013` | (3,1) | RIGHT | token bit at (1,4) | theory / memorised |
| `-002` / `-015` | (3,3) | LEFT | token bit at (1,8) | theory / memorised |

In both pairs the two items are the same move at the same cell with the same
cycler phase, and the *only* difference in the state is whether a token twelve
cells away has been collected — a variable that **no rule on this paper reads**.
An examinee that had memorised `-013` and applied the completely unjustified
heuristic "the token colour is irrelevant" answers `-011` correctly.

The `heldout` split is defined by `transition_key` (`worldgen_port.py:148`) as
the *rendered frame* plus the action, which is the right definition in general —
but a mechanism that multiplies the state space without affecting the
transition manufactures held-out keys for free. `count_lock` is doing exactly
that here: with 2 tokens it quadruples the reachable set (262 states over 36
agent cells) while contributing zero rules to the paper. **The lock's whole
contribution to this world's leading score is that it makes copies of frames.**

### 5.2 Five of the six `theory` items reuse an (agent cell, action) pair the trace already demonstrated

The published trace has 161 frames, 156 tagged transitions and 81 distinct
`(agent cell, action)` pairs. Of the six `theory` items, **five** — `-002`,
`-005`, `-011`, `-012`, `-014` — sit on an `(agent cell, action)` pair the
trace already shows in some token/phase configuration. Only `-008` (agent
(4,6), DOWN) is at a position/action the trace never exercised, and it is an
ordinary `walk` on open floor.

"Held out" here therefore means "the trace never showed this exact frame", not
"the trace never showed this situation". That is a defensible definition and it
is documented, but the report should not let a reader infer positional novelty
from it. A `heldout` split keyed on agent cell (or on rule × agent cell) would
be much harder, and this world could support it: it has 892 held-out
transitions against 156 in-trace ones.

### 5.3 A dead local in `axes()`

`heldout_worldgen.py:332` binds `unchanged = sum(1 for entry in ... if
entry.get("truth", {}).get("frame_after") is not None)` — the count of items
that *have* a truth frame, i.e. all of them — and reports it at `:344` as
`"items"`. The reported number is right (16); the variable name is a leftover
from something that counted unchanged frames and no longer does. Harmless, but
it reads as a bug to anyone auditing the axes, and the genuinely useful
statistic (unchanged share) lives elsewhere, at `:249`.

### 5.4 The `free` items are worse than free

All four `free` items are `blocked_by_wall` with the agent moving LEFT (`-001`,
`-006`, `-007`, `-009`). Not just one rule — one *direction*. The sampling hash
at `heldout_worldgen.py:113 _pick()` has no diversity term, so a rule with 420
candidate transitions can contribute four items that are near-identical in
form. It costs nothing here because the items are worthless anyway, but the
same mechanism selects the informative items too, and it is why §5.1's twin
pairs slipped through.

---

## Files consulted

* `worldgen/out/worlds/t3-cycler-portal-lock/{spec.json, raw_trace.jsonl, ground_truth.json, GROUND_TRUTH.md, coverage.json, reversibility.json}` — read only
* `worldgen/core/world.py`, `worldgen/mechanisms/{base,color_cycle,portal,count_lock}.py` — read only
* `exam/papers/{heldout_worldgen,worldgen_port}.py`, `exam/grading/{rubrics_heldout,mark}.py`, `exam/tools/discrimination.py` — read only, imported, never modified
* All 20 per-world profiles in this run directory, for the catalogue arithmetic in §4.3

No file in the repository was modified. This report is the only file created.
