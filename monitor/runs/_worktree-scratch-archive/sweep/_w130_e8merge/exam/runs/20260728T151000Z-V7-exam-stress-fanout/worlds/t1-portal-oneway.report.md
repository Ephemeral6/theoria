# Examiner's report — `t1-portal-oneway`

Independent audit of the discrimination profile at
`exam/runs/20260728T151000Z-V7-exam-stress-fanout/worlds/t1-portal-oneway.json`.

Read-only on every existing file. No network, no LLM, no `git`, no full `pytest`.
Everything below was produced by importing `exam.*` and `worldgen.*` in-process.

**Bottom line.** The instrument's classification of this world is correct on all
eight items — no defect. The marker is sound on the two invariants that matter and
has no verdict that pays for a wrong answer, but it collapses *format* failure into
`wrong`, which is arguably unfair. The world's honest effective size is **zero**, not
the reported two: a theory-free "move the agent one cell unless a wall is in the way"
strategy scores **8/8** against a bluffer floor of **4/8**, capturing 2/2 of the
`theory` residue. Separately, and not asked about: **the sheet prints the answer's
rule name on every item**, and the exam's own leakage gate rejects this paper — it has
simply never been run against it.

---

## 1. Is the classification true of this world's actual mechanics?

**Yes. All eight items check out, frame and rule tag.**

Method: I wrote an independent transition function directly from `spec.json`
(`worldgen/out/worlds/t1-portal-oneway/spec.json`) — bounds test → wall test →
portal test → walk — and an independent renderer (walls from `layout`, portal mouth
at `[5,1]` painted `2`, agent painted `6` last). I did **not** call
`GridWorld.explain`. For each item I recomputed `frame_after` from
`item.paper["frame_before"]` and `item.paper["action"]` and compared it to
`item.truth["frame_after"]` and `item.truth["rule"]`.

| item_id | action | agent before | agent after (mine) | rule (mine) | rule (recorded) | split | class | frame changes | frame matches |
|---|---|---|---|---|---|---|---|---|---|
| `t1-portal-oneway-000` | UP | (4,1) | (3,1) | `walk` | `walk` | heldout | theory | yes | ✔ |
| `t1-portal-oneway-001` | DOWN | (6,7) | (6,7) | `blocked_by_wall` | `blocked_by_wall` | heldout | free | no | ✔ |
| `t1-portal-oneway-002` | DOWN | (2,1) | (3,1) | `walk` | `walk` | replay | memorised | yes | ✔ |
| `t1-portal-oneway-003` | DOWN | (3,3) | (4,3) | `walk` | `walk` | replay | memorised | yes | ✔ |
| `t1-portal-oneway-004` | DOWN | (6,3) | (6,3) | `blocked_by_wall` | `blocked_by_wall` | replay | free | no | ✔ |
| `t1-portal-oneway-005` | DOWN | (1,5) | (1,5) | `blocked_by_wall` | `blocked_by_wall` | heldout | free | no | ✔ |
| `t1-portal-oneway-006` | DOWN | (6,2) | (6,2) | `blocked_by_wall` | `blocked_by_wall` | replay | free | no | ✔ |
| `t1-portal-oneway-007` | LEFT | (6,7) | (6,6) | `walk` | `walk` | heldout | theory | yes | ✔ |

Checks that answer the two failure modes named in the brief:

* **Every `free` item is genuinely static.** 001, 004, 005, 006 all have
  `frame_after == frame_before`; each is an agent adjacent to a `#` in the action's
  direction — (7,7), (7,3), (2,5), (7,2) respectively. No `free` item changes the
  frame.
* **Both `theory` items genuinely change it.** 000 moves (4,1)→(3,1); 007 moves
  (6,7)→(6,6). Neither is in the trace.

Split tags check out against `raw_trace.jsonl` independently: the four `replay`
items reproduce trace steps t=1 (002), t=4 (003), t=7 (004), t=9 (006). The four
`heldout` items have no `(frame, action)` key in the trace — 000 is the same frame
as trace t=3 but with `UP` where the trace played `DOWN`, which is the strictest
case and it is filed correctly.

Re-running `exam.tools.discrimination.profile_world("t1-portal-oneway", 2)` in
process reproduces the published artefact **byte-identically** (canonical JSON
compare). No defect in the instrument on this world.

---

## 2. Does the marker misjudge anything on this world?

### 2a. The two structural invariants — both hold

Marked through the real `exam.grading.mark.mark` with `axes_fn=heldout_wg.axes`:

| examinee | verdicts | score |
|---|---|---|
| `null` | `{"unanswered": 8}` | 0.000 |
| `oracle` | `{"correct": 8}` | 1.000 |
| `memoriser` | `{"correct": 6, "wrong": 2}` | 0.750 |
| `bluffer` | `{"correct": 4, "wrong": 4}` | 0.500 |

* **Silence is never paid.** `null` is `unanswered` on all 8 and scores 0.000. Never
  `correct`, never `abstained`. ✔
* **Ground truth is never marked wrong.** `oracle` produces 8 `correct`, zero
  `wrong`, zero `abstained`. ✔
* Abstention awards 0.0 and is recorded as `abstained`
  (`exam/grading/rubrics_heldout.py:146`) — it does not pay. ✔

### 2b. The stress battery — 32 probes

All against `t1-portal-oneway-000` (a `theory` item) unless noted, via
`grade_frame_exact(answer, truth, item)` directly. `legal_cells` for this world is
`(0, 1, 2, 6)`; the grid is 8×9.

| answer | verdict | detail | fair? |
|---|---|---|---|
| exact truth, bare list | `correct` | `cells_wrong: 0` | ✔ |
| `{"frame_after": truth}` | `correct` | — | ✔ |
| `{"frame": truth}` / `{"after": truth}` | `correct` | — | ✔ |
| tuple of tuples | `correct` | — | ✔ |
| truth + an extra key in the dict | `correct` | — | ✔ |
| `{"abstain": false, "frame_after": truth}` | `correct` | — | ✔ |
| **transposed (9×8)** | `wrong` | `shape_ok: false, cells_wrong: -1` | ✔ |
| **one cell changed** (`[0][0]` 1→0) | `wrong` | `shape_ok: true, cells_wrong: 1` | ✔ by design (no partial credit) |
| rows reversed | `wrong` | `cells_wrong: 14` | ✔ |
| short grid (7 rows) | `wrong` | `shape_ok: false` | ✔ |
| truth padded with a 10th column | `wrong` | `shape_ok: false` | ✔ |
| **ragged** (row 3 one short) | `wrong` | `not a well-formed frame` | ✔ verdict, see 2c |
| **`"6"`/`"0"` strings not ints** | `wrong` | `not a well-formed frame` | **arguable — see 2c** |
| `6.0`/`0.0` floats | `wrong` | `not a well-formed frame` | **arguable — see 2c** |
| booleans | `wrong` | `not a well-formed frame` | ✔ (explicitly reasoned at `rubrics_heldout.py:104`) |
| **colour 7 (outside palette)** | `wrong` | `not a well-formed frame` | ✔ |
| **colour 4** (A0's default palette, not this world's) | `wrong` | `not a well-formed frame` | ✔ — the per-world palette works |
| colour −1 | `wrong` | `not a well-formed frame` | ✔ |
| **`{"abstain": true}`** | `abstained` | 0.0 | ✔ |
| string `"abstain"` | `abstained` | 0.0 | ✔ |
| `{"abstain": 1}` | `wrong` | `not a well-formed frame` | **arguable — see 2c** |
| `{"abstain": "yes"}` | `wrong` | `not a well-formed frame` | **arguable — see 2c** |
| **`null`** | `unanswered` | 0.0 | ✔ |
| **`{}` (empty dict)** | `wrong` | `not a well-formed frame` | **arguable — see 2c** |
| `[]` (empty list) | `wrong` | `not a well-formed frame` | **arguable — see 2c** |
| `{"frame_after": null}` | `wrong` | `not a well-formed frame` | **arguable — see 2c** |
| `{"frame_after": []}` | `wrong` | `not a well-formed frame` | arguable |
| dict of rows `{"0": row, …}` | `wrong` | `not a well-formed frame` | ✔ |
| JSON string of the grid | `wrong` | `not a well-formed frame` | ✔ (`rubrics_heldout.py:92`) |
| `{"frame_after": {"frame_after": truth}}` | `correct` | — | **loose — see 2c** |
| free item 001, exact | `correct` | — | ✔ |
| free item 001, transposed | `wrong` | `shape_ok: false` | ✔ |

**Nothing in the battery pays for a wrong answer.** No answer that differs from the
truth was ever marked `correct`, and no answer that equals the truth cell-for-cell
in a legal representation was ever marked `wrong`. On the two headline near-misses
the brief singled out — transposed, and one cell changed — the verdict is `wrong`
and a fair examiner would agree; the rubric's no-partial-credit design is argued at
length in `exam/grading/rubrics_heldout.py:1-35` and I do not dispute it.

### 2c. Where I think the verdict is arguably wrong

**(i) Format failure is indistinguishable from theory failure — the one that
matters.** `exam/grading/rubrics_heldout.py:149-154`: when `_as_frame` returns
`None`, the verdict is `wrong`. An examinee that *predicted this world perfectly*
and serialised `"6"` instead of `6`, or `6.0` instead of `6`, receives the identical
verdict to the bluffer that predicted stasis. A fair examiner would say: "your world
model is right, your notation is wrong" — a distinct outcome, at minimum a distinct
verdict (`malformed`), even if it still scores zero. The information is not lost —
`detail.why` says `"answer is not a well-formed frame"` — but the verdict field
that every aggregate reads (`report.by_tag`, `axes.by_rule`, and
`discrimination._classify` at `exam/tools/discrimination.py:105`) sees only `wrong`.

This is precisely the hazard `exam/papers/worldgen_port.py:173-180` names for the
palette — *"a malformed-answer verdict reads on a report as an examinee that cannot
format JSON, not as a rubric that was pointed at the wrong world"* — solved at the
palette level and left unsolved one level up, at the verdict. `float` is the sharp
case: JSON round-trips through many serialisers as `6.0`, and no reasonable examinee
would regard that as a prediction error.

**(ii) `{}`, `[]`, `{"frame_after": null}` → `wrong`, but bare `null` →
`unanswered`.** Four ways of submitting nothing, three of which are called a wrong
prediction. `rubrics_heldout.py:138-142` reasons carefully that an explicit `null`
"is treated as nothing submitted, which is what it is" — the same reasoning applies
to `{}` and to `{"frame_after": null}` and is not applied. A fair examiner would
call all four `unanswered`. Scoring impact: none (all award 0.0). Reporting impact:
an examinee that emits `{}` on items it cannot answer is reported as having made
eight wrong *predictions* rather than eight non-submissions, which is the difference
the `unanswered`/`wrong` split exists to record (`exam/grading/mark.py:9-14`).

**(iii) `{"abstain": 1}` and `{"abstain": "yes"}` → `wrong`, not `abstained`.**
`_is_abstention` (`rubrics_heldout.py:115-121`) uses `value.get("abstain") is True`,
an identity test. The bare *string* `"abstain"` is honoured, and `{"abstain":
"yes"}` — strictly more explicit — is not. A fair examiner reading `{"abstain":
"yes"}` would record an abstention. Again zero scoring impact, but the abstention
count is the number that lets a report say whether an examinee knew it did not know
(`rubrics_heldout.py:17-21`), and it silently under-counts.

**(iv) The `frame_after` unwrap recurses without a depth bound.**
`{"frame_after": {"frame_after": truth}}` is marked `correct`
(`rubrics_heldout.py:88-90` recurses through `_as_frame`). Harmless here, but it
means the accepted answer shape is looser than the instructions promise; a
double-wrapped answer is not "the grid itself or `{"frame_after": [[...]]}`".

**(v) `cells_wrong: -1` is a sentinel sharing a field with real counts.**
`_diff` (`rubrics_heldout.py:124-132`) returns `-1` for a shape mismatch, so on this
world `detail.cells_wrong` takes the values `0`, `1`, `14` and `-1` with the last
meaning "not comparable". Diagnostic-only, but anything that averages the field gets
a number below zero.

None of (i)–(v) changes a single score on this world. (i) is the one I would fix.

---

## 3. A cheap examinee that beats the bluffer floor

**Yes — decisively. 8/8 (100%) against a floor of 4/8 (50%), capturing 2/2 of the
`theory` residue and 2/2 of the `memorised` residue.**

The strategies below read only `frame_before`, `action`, `legend` and `grid` from
`item.paper`. They do not open `ground_truth.json`, do not touch `item.truth`, and
do not look at the trace. They were marked through the real
`exam.grading.mark.mark` against `paper.key(digest())`.

### Strategy A — "walk-or-wall", using the printed legend

> Find the single cell whose colour is `legend["agent"]`. Take one step in the
> action's direction. If that cell is out of bounds or has colour `legend["wall"]`,
> return the input frame unchanged. Otherwise repaint the vacated cell
> `legend["floor"]` and the target cell `legend["agent"]`.

This is the most generic grid prior there is — "things move one step unless a wall
stops them". It contains no knowledge of portals, of this world's layout, or of
anything the exam is supposedly testing.

| | score |
|---|---|
| overall | **8 / 8 = 1.000** |
| `free` items (001, 004, 005, 006) | 4 / 4 |
| `memorised` items (002, 003) | 2 / 2 |
| `theory` items (000, 007) | **2 / 2** |
| `replay` axis | 1.000 |
| `heldout` axis | 1.000 |
| `gap_replay_minus_heldout` | 0.000 |

It posts the oracle's exact score card, including the zero gap that
`heldout_worldgen.reference_answers`'s docstring (`:266-272`) treats as the signature
of a rule-learner rather than a memoriser.

### Strategy B — the same thing without the legend

Same rule, but the palette is inferred from the frame: wall = the colour at `[0][0]`
(the border), agent = the highest colour value present, floor = the most common
remaining colour. **8 / 8.** So even a sheet with no legend at all does not protect
this paper.

(A third variant that identified the agent as "the colour appearing exactly once"
scored only 4/8 — colour `2`, the portal mouth, is also a singleton, so the tie-break
failed and it degenerated to the bluffer. That is a defect in that variant's colour
heuristic, not evidence that the paper is hard; two other tie-breaks both reach 8/8.)

### How much of a world model this is: none

Run Strategy A over the **entire reachable transition relation** of this world — all
104 transitions, not just the eight on the paper:

| rule | correct / total |
|---|---|
| `blocked_by_wall` | 54 / 54 |
| `walk` | 48 / 48 |
| **`teleport_oneway`** | **0 / 2** |
| total | 102 / 104 (0.981) |

The heuristic is wrong about exactly one thing — the portal, which is the entire
reason this world exists — and the paper never asks about it. The examinee is not
smart; the paper is not asking.

---

## 4. Honest effective size

**The instrument says `effective_size: 2`. The honest number is `0`.**

`effective_size` is defined as the `theory` count
(`exam/tools/discrimination.py:206-208`), i.e. items the three synthetic voters do
not settle. That is a sound definition and it is correctly computed. But the module's
own caveat (`discrimination.py:59-67`) is exactly what bites here: *"a fourth
strategy nobody has written could settle it for free, and the taxonomy would not
notice."* Section 3 is that fourth strategy. Both `theory` items fall to a heuristic
with no world model, so the number of items on this paper that genuinely require one
is **zero**.

### The rules, and which are dead weight

| rule | reachable transitions | in trace | held out | on the paper | verdict |
|---|---|---|---|---|---|
| `blocked_by_wall` | 54 | 2 | 52 | 4 items, all `free` | **dead weight** — barren by the instrument's own test |
| `walk` | 48 | 7 | 41 | 4 items (2 `memorised`, 2 `theory`) | **carries the paper, but is the universal grid prior** |
| `teleport_oneway` | 2 | 1 | 1 | **0 items — excluded** | **the only rule that could have discriminated, and it is not examined** |
| `blocked_portal_exit` | 0 | — | — | 0 | never fires; declared as a dormant clause in `ground_truth.json["rule_correspondence"]["dormant_clauses"]` |

* **`blocked_by_wall` is dead weight and the profile says so** (`barren_rules:
  ["blocked_by_wall"]`). Its answer is "the frame you were given", which is the
  bluffer's answer by definition. It cannot ever discriminate under this rubric.
  It contributes exactly half the paper.
* **`walk` is not dead weight in the instrument's terms** — it produces all four
  discriminating items — but it is dead weight in the terms that matter. "The agent
  moves one cell in the direction of the action" is the prior any examinee brings to
  a grid before it has seen anything, so an item that only tests `walk` tests
  nothing this framework claims to be about.
* **`teleport_oneway` is the world.** It is the only rule that distinguishes
  `t1-portal-oneway` from a bare maze, and it is excluded by the matched-quota gate:
  it has **1** witness inside the published trace and **1** outside, against
  `per_class = 2` on both sides (`exam/papers/heldout_worldgen.py:127-137`,
  `exam/papers/worldgen_port.py:236-280`). The refusal is *correct* — the design
  argument for it (`heldout_worldgen.py:24-36`) is right that dropping a rule from
  one side turns the printed `replay`/`heldout` tag into a hint. But the consequence
  is a paper about a portal world in which the portal cannot appear.

  The root cause is upstream, in the world, not in the exam: the portal has one
  mouth at `[5,1]` and only two reachable states from which stepping into it is
  possible (`ground_truth.json["reversibility"]["rules"]["teleport_oneway"]:
  firing_states 2, firing_transitions 2`). At `per_class = 1` the rule would qualify
  — but `per_class = 1` cannot distinguish a rule learned from a rule guessed once,
  which is why the default is 2. This world cannot carry a matched-quota question
  about its own mechanism at any honest quota.

### Is the residue large enough to rank two examinees apart?

**No, on three independent counts.**

1. **Size.** Two items. Even taking the instrument's `theory` count at face value, a
   two-item residue on 8 items gives a 0.5-point resolution and no confidence
   interval worth quoting. Two examinees differing by one item differ by 12.5% of
   the headline score.
2. **Content.** Both residue items are `walk`, and `walk` is answered by a
   theory-free heuristic (§3). The residue does not separate a world-modeller from a
   non-modeller; it separates an examinee that moves the agent from one that does
   not.
3. **Leakage.** See below — the sheet prints the rule name, so the residue does not
   separate anybody at all.

The paper's honest description is: eight items, four of which pay for copying the
input, four of which pay for knowing that grids let you walk. `bluffer_floor = 0.500`
is the number to quote as the ceiling on how meaningless the score can get; `1.000`
is what a theory-free strategy actually gets.

---

## Not asked about, but found

### A. The sheet prints the answer's rule name on every item — and the exam's own leakage gate rejects this paper

`exam/papers/heldout_worldgen.py:204` sets `tags=(split, "rule:%s" % cand["rule"])`,
and `exam/model.py:108-110` (`Item.sheet_side`) copies `tags` straight onto the
sheet. `paper.sheet(digest())` for this world contains:

```
t1-portal-oneway-000 ['heldout', 'rule:walk']              UP
t1-portal-oneway-001 ['heldout', 'rule:blocked_by_wall']   DOWN
t1-portal-oneway-002 ['replay',  'rule:walk']              DOWN
...
```

This directly contradicts the module's own stated discipline, twelve lines above the
offending assignment (`heldout_worldgen.py:239-246`):

> *"Counts, not names. The rule names are the answer vocabulary of the `by_rule`
> axis, and a sheet that lists them hands the examinee the alphabet it is being
> asked to discover."*

The counts are withheld from `notes` (which is key-side only, `model.py:169-178` —
correctly, so `unchanged_frame_share: 0.5` does not leak the bluffer floor). The
names are printed on every item.

On this world the tag *is* the answer. A strategy that reads nothing but the tag —
`rule:blocked_by_wall` → return the input; `rule:walk` → move the agent one cell —
scores **8/8**, with no wall lookup and no legend. The two-item `theory` residue is
not merely capturable by a heuristic; it is printed on the sheet.

The exam already has the machinery to catch this, and it catches it immediately:

```python
leakage.check_paper(paper, paper.sheet(digest()), key_doc=paper.key(digest()))
# LeakageError: v2-heldout-t1-portal-oneway leaks its own answers:
#   [{'item_id': 't1-portal-oneway-000', 'check': 'probe', 'hits': ['walk']},
#    {'item_id': 't1-portal-oneway-001', 'check': 'probe', 'hits': ['blocked_by_wall']},
#    ... all 8 items ...]
```

Every item's own declared probe (`heldout_worldgen.py:203`, `leak_probes=(rule,)`)
fires against its own sheet. The gate is not broken and the probes are not missing —
the gate has simply never been pointed at this paper. `heldout_worldgen` is absent
from `exam/papers/__init__.py:34-39` (`BUILDERS`), so
`exam/tools/build_papers.build_one` — the only caller of `leakage.check_paper`
(`build_papers.py:72`) — cannot reach it; and `run_matrix.py:181` and
`discrimination.py:125` build the `Paper` object and read `.items` directly, never
calling `.sheet()`. Twenty worlds' worth of papers are outside the leakage gate.

This does not affect anything in §1–§4 above, because all four synthetic examinees
answer from `Paper.items` rather than from a rendered sheet. It affects every real
examinee that would ever be handed one.

### B. On this world, `class` carries no information beyond two already-published fields

Verified on all 8 items: `class == "free" if not frame_changes else ("memorised" if
split == "replay" else "theory")`. The `_classify` triple
(`discrimination.py:95-114`) collapses exactly, because the memoriser is defined as
"truth on replay, `frame_before` elsewhere" (`heldout_worldgen.py:290-296`) and the
bluffer as "`frame_before` always". The taxonomy is therefore a relabelling of
`(split, frame_changes)`, both of which the profile already prints per item — and
`split` is printed on the sheet. This is not wrong; it is worth knowing that on a
world with no state beyond the agent's position, the classifier has no independent
evidence to add. It would only diverge on a world where the bluffer can be right
where the memoriser is wrong, which requires a held-out static transition the
memoriser mispredicts — impossible under the current memoriser definition.

### C. Reproducibility

`profile_world("t1-portal-oneway", 2)` re-run in-process is byte-identical to the
published artefact under canonical JSON compare. `rubric_digest` in the artefact
(`e06bdf52…1cb091`) matches `exam.grading.registry.digest()` at the time of this
audit, so the profile was not computed against a different rubric.

### D. `blocked_portal_exit` is correctly reported as dormant

`ground_truth.json["rule_correspondence"]["dormant_clauses"] ==
["blocked_portal_exit"]` and `GROUND_TRUTH.md` marks it **never fires**. My
independent transition function agrees: the portal's destination `[3,3]` is floor and
is never occupied by anything but the agent, and the agent has just left the mouth,
so the exit is never blocked. It is a declared clause with no reachable witness, not a
missing item. No defect.

---

## Reproduction

```python
# all read-only, no writes, no network
from exam.papers import heldout_worldgen as hw, worldgen_port as port
from exam.grading.registry import digest
from exam.grading.mark import mark
from exam.model import Submission
from exam.tools.discrimination import profile_world

paper = hw.build_for("t1-portal-oneway", 2)
key   = paper.key(digest())
sheet = paper.sheet(digest())          # <- carries 'rule:walk' etc.
hw.plan("t1-portal-oneway", 2)         # blocked_rules -> teleport_oneway 1/1
port.firing_counts(port.open_world("t1-portal-oneway"))
profile_world("t1-portal-oneway", 2)
```
