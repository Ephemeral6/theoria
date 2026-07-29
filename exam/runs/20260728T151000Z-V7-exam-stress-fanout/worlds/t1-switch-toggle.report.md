# Independent examination — `t1-switch-toggle`

Examiner: independent audit of `exam/tools/discrimination.py`'s profile at
`exam/runs/20260728T151000Z-V7-exam-stress-fanout/worlds/t1-switch-toggle.json`.
Read-only on every existing file. No network, no LLM, no `pytest` run, no `git`.
Paper: `v2-heldout-t1-switch-toggle`, 8 items at `per_class=2`, rubric digest
`e06bdf52…1cb091`.

**Verdict in one line.** The instrument's classification is *arithmetically
correct and semantically hollow*: all eight labels are true of the world's
mechanics, but the two items it calls `theory` are answered perfectly by a
28-line grid prior that has never heard of a switch. This world's honest
effective size is **0**, not 2.

---

## 1. Is the classification true of this world's actual mechanics?

**Yes — no defect in the instrument.** I re-derived every one of the 8 items
from `worldgen/out/worlds/t1-switch-toggle/spec.json` with an independent
simulator (my own transition function and renderer, written from the rule table
in `GROUND_TRUTH.md:24-32`, not from `worldgen/core/world.py`), and compared
against `Item.truth["frame_after"]`, `Item.truth["rule"]`, and
`Item.truth["split"]`.

Items checked: **all eight** — `t1-switch-toggle-000` … `-007`. Every one
matched on all three fields. The `before` frames also round-trip through my
renderer, so my state inversion is not papering over a rendering difference.

| item | action | rule | split | frame changes | class | re-derived |
|---|---|---|---|---|---|---|
| `-000` | DOWN | `walk` | heldout | yes | `theory` | ✔ |
| `-001` | LEFT | `walk` | replay | yes | `memorised` | ✔ |
| `-002` | RIGHT | `blocked_by_wall` | heldout | no | `free` | ✔ |
| `-003` | RIGHT | `blocked_by_wall` | replay | no | `free` | ✔ |
| `-004` | UP | `blocked_by_wall` | replay | no | `free` | ✔ |
| `-005` | UP | `blocked_by_wall` | heldout | no | `free` | ✔ |
| `-006` | UP | `walk` | replay | yes | `memorised` | ✔ |
| `-007` | DOWN | `walk` | heldout | yes | `theory` | ✔ |

Worked examples, by hand:

* **`-000`** (`theory`). Agent at (1,1); switch (4,1) renders `3` = on, so net
  `a` is on, so both doors — (3,4) and (4,2) — are passable and undrawn (`0`).
  DOWN targets (2,1), which is `.` in `layout` row 2 and claimed by no
  mechanism ⇒ `walk`. Truth moves the agent to (2,1). Frame changes in exactly
  2 cells. Correct.
* **`-002`** (`free`). Agent at (1,3); RIGHT targets (1,4), which is `#` in
  `layout` row 1 ⇒ `blocked_by_wall`, nothing changes. Truth frame is
  byte-identical to `frame_before`. Correct.
* **`-007`** (`theory`). Agent at (3,5), switch on. DOWN targets (4,5) — floor,
  and the goal cell. `walk`. Truth moves the agent there; `win` is not part of
  the frame, so the only change is the two cells. Correct.

**Split membership independently confirmed.** For each item I recomputed
`port.transition_key(frame_before, action)` and checked it against
`port.evidence_index()` built from `raw_trace.jsonl`. All four `replay` tags are
in the trace and all four `heldout` tags are not; for every `replay` item the
trace's own successor frame equals `Item.truth["frame_after"]` byte for byte.

**The two defect conditions you named do not occur.** No `free` item changes the
frame (all four are byte-identical before/after); both `theory` items do change
it. `dead = 0`, `anomalies = []`, confirmed by re-running the three voters
through `mark()`.

On this world the taxonomy collapses to a one-line rule, which is worth stating
because it is what makes §3 possible: `free ⟺ frame unchanged`,
`memorised ⟺ changed ∧ replay`, `theory ⟺ changed ∧ heldout`. Nothing about
*difficulty* enters the label at all.

---

## 2. Does the marker misjudge anything on this world?

**Structural invariants — both hold.**

* Silence is never paid: `null` (`reference_answers(..., "null")` returns `{}`)
  scores `unanswered` on 8/8 items, fraction `0.000`, zero `correct`. The path is
  `exam/grading/mark.py:51-52`.
* Ground truth is never marked wrong: `oracle` scores `correct` on 8/8,
  fraction `1.000`, zero `wrong`.

For the record, the calibration triple on this paper: oracle `1.000`,
memoriser `0.750` (gap replay−heldout `0.500`), bluffer `0.500` (gap `0.000`).

**Stress battery.** 25 near-truth answers, applied to `-000` (`walk`, heldout),
`-002` (`blocked_by_wall`, heldout) and `-007` (`walk`, heldout). Identical
results on all three items. `grade_frame_exact` is `rubrics_heldout.py:135`.

| answer shape | verdict | fair? |
|---|---|---|
| correct grid, bare | `correct` 1.0 | ✔ |
| correct grid, `{"frame_after": …}` | `correct` 1.0 | ✔ |
| correct grid, `{"frame": …}` / `{"after": …}` | `correct` 1.0 | ✔ generous, undocumented |
| correct grid as tuples | `correct` 1.0 | ✔ |
| correct grid, transposed (6×7 → 7×6) | `wrong` (`shape_ok:false`) | ✔ |
| correct grid, one cell changed | `wrong` (`cells_wrong:1`) | ✔ |
| correct grid, one cell → colour `3` (in palette, absent from this frame) | `wrong` (`cells_wrong:1`) | ✔ |
| correct grid as **strings** | `wrong` ("not a well-formed frame") | ⚠ see D1 |
| correct grid as **floats** (`1.0`) | `wrong` ("not a well-formed frame") | ⚠ see D1 |
| correct grid as **booleans** | `wrong` ("not a well-formed frame") | ✔ (deliberate, `:104`) |
| ragged (one short row) | `wrong` ("not a well-formed frame") | ✔ |
| short grid (5 of 6 rows) | `wrong` (`shape_ok:false`) | ✔ |
| colour `9` (outside this world's palette `{0,1,2,3,4,6}`) | `wrong` ("not a well-formed frame") | ✔ |
| `{"abstain": true}` | `abstained` 0.0 | ✔ |
| `"abstain"` (string) | `abstained` 0.0 | ✔ |
| `{"abstain": true, "frame_after": <correct>}` | `abstained` 0.0 | ⚠ see D3 |
| `{"abstain": false, "frame_after": <correct>}` | `correct` 1.0 | ✔ |
| `{"abstain": 1}` | **`wrong`** | ✘ see D2 |
| `{}` | **`wrong`** | ✘ see D2 |
| `[]` | **`wrong`** | ✘ see D2 |
| `null` | `unanswered` 0.0 | ✔ |
| JSON *string* of the correct grid | `wrong` | ⚠ see D1 |
| `{"frame_after": {"frame_after": <correct>}}` | **`correct` 1.0** | ⚠ see D4 |
| bluffer (input frame) on `-002` | `correct` 1.0 | ✔ (the item is genuinely stasis) |
| bluffer (input frame) on `-000` / `-007` | `wrong` (`cells_wrong:2`) | ✔ |

`_legal_cells` (`rubrics_heldout.py:59`) correctly picks up this world's
declared palette `(0,1,2,3,4,6)` from `Item.truth["legal_cells"]` rather than the
A0 default `{0,2,4,8}` at `:56` — the A0 hardcoding hazard the docstring warns
about is genuinely fixed here; a frame containing `1`, `3` or `6` is accepted.

**No case awards a mark it should not.** Every misjudgement below is a
*reporting* defect — the arithmetic is right, the label on the report is not.

**D1 — format failure is reported as `wrong`, indistinguishable from a wrong
prediction.** `["1","1",…]`, `[1.0, 1.0, …]` and a JSON string of the grid all
land on `rubrics_heldout.py:151` with verdict `wrong`. A fair examiner would
say: *the prediction is right and the encoding is wrong* — zero marks is
defensible, but calling it `wrong` puts a correct world model in the same bucket
as a broken one. The rubric's own docstring (`rubrics_heldout.py:12`, and
`worldgen_port.py:177-179`) identifies exactly this confusion as the thing to
avoid, and then reproduces it one layer up: the distinction survives only in
`detail["why"]`, which no aggregate reads. `VERDICTS` would need a
`malformed` member for this to be fixable, so I am recording it rather than
proposing a patch.

**D2 — the empty answer is treated three different ways.** `null` →
`unanswered`; `{}` → `wrong`; `[]` → `wrong`; and `{"abstain": 1}` → `wrong`.
A fair examiner would call all four "nothing usable was submitted": `{}` and
`[]` are the JSON-serialisation of an examinee that produced no answer, and
`{"abstain": 1}` is an abstention written by someone whose serialiser emits `1`
for `true`. Marks are unaffected (all zero), but `axes()["unanswered"]` and
`["abstained"]` (`heldout_worldgen.py:342-343`) undercount, and a report would
claim an examinee guessed wrong when it in fact said nothing. Cause:
`_is_abstention` tests `value.get("abstain") is True` (`:116`, identity, not
truthiness) and `_as_frame` falls through to `return None` for a dict with no
recognised key (`:91`) and for any empty container (`:94`).

**D3 — a self-contradictory answer resolves in favour of abstention.**
`{"abstain": true, "frame_after": <correct grid>}` is `abstained`, because
`_is_abstention` runs first (`:144`) and `_as_frame` also short-circuits on
`abstain is True` (`:79-80`). Defensible, but it is a policy choice nothing
documents; a fair examiner could equally rule that a submitted prediction
overrides the flag. Low impact.

**D4 — `_as_frame` recurses without a depth bound** (`:88-90`), so
`{"frame_after": {"frame_after": {…: grid}}}` is accepted as `correct`. Harmless
on any real submission, and unbounded nesting is bounded by Python's recursion
limit rather than by the rubric.

**D5 (not a marker fault, but adjacent) — a dead variable in `axes()`.**
`heldout_worldgen.py:332-333` computes `unchanged = sum(1 for entry … if
entry["truth"]["frame_after"] is not None)` and publishes it as `"items"`. The
*name* says "unchanged frame count"; the *expression* counts every item with a
truth (here: 8, the item count). The published number is correct for the key it
is filed under, so nothing downstream is wrong — but the name is a trap, and the
statistic the name promises (which is the bluffer floor, and the single most
important number about this world) is not computed anywhere in `axes`. It exists
only as `Paper.notes["unchanged_frame_share"]` (`:249`, = `0.5` here).

---

## 3. A cheap examinee that beats the bluffer floor without a world model

**Yes, and it does not merely beat the floor — it ties the oracle.**

The bluffer floor on this paper is **0.500** (4 of 8 items are stasis;
`Paper.notes["unchanged_frame_share"] = 0.5`).

### Strategy `legend-prior`

Inputs: `item.paper` only — `frame_before`, `action`, `legend`, `grid`. It never
opens `ground_truth.json`, never touches `Item.truth`, and is not tuned to this
world: the three legend entries it uses (`agent`, `wall`, `floor`) are renderer
constants injected for every world by `worldgen_port.palette()` (`:167-168`), so
the same function runs unmodified on any of the twenty worlds.

```
find the unique cell whose colour == legend["agent"]
target := that cell + the unit step for `action`
if target is off-grid            -> return frame_before unchanged
if frame[target] != legend["floor"] -> return frame_before unchanged
else move: old cell := floor, target := agent
```

That is the whole theory: *the agent takes one step onto empty-looking ground,
and otherwise nothing happens.* It contains no notion of switch, door, net or
polarity.

### Score

| examinee | overall | replay | heldout | `free` | `memorised` | `theory` |
|---|---|---|---|---|---|---|
| bluffer (floor) | 0.500 | 0.500 | 0.500 | 4/4 | 0/2 | 0/2 |
| memoriser | 0.750 | 1.000 | 0.500 | 4/4 | 2/2 | 0/2 |
| **`legend-prior`** | **1.000** | **1.000** | **1.000** | 4/4 | 2/2 | **2/2** |
| oracle | 1.000 | 1.000 | 1.000 | 4/4 | 2/2 | 2/2 |

`legend-prior` is `correct` on all eight items — `-000` … `-007`. It captures
**100% of the theory residue (2 of 2)**, +0.500 over the bluffer floor and
+0.250 over the memoriser, and its `gap_replay_minus_heldout` is `0.000`, i.e.
on this paper it is indistinguishable from a genuine rule-learner on every axis
the exam reports.

This is not a sampling accident. Re-run at `per_class` = 1, 2, 3, 4 and 6
(4 to 24 items): `legend-prior` scores `1.000` at every quota, because at every
quota the paper's only two rules are `walk` and `blocked_by_wall`.

### The honest control, so this is not a claim about legend-reading being magic

A strictly weaker sibling, `blind-modal`, which is given no legend at all and
must infer floor as the modal colour and the agent as the unique
non-floor/non-border singleton, scores exactly **0.500** — it ties the bluffer
floor and captures 0 of 2 theory items. It fails because in this world's frames
the switch colour (`2` or `3`) is *also* a singleton, so the agent is not
identifiable, and the strategy degrades to stasis. The legend is doing real
work; the legend is also printed on the sheet.

### Proof that `legend-prior` is not a world model

Run over the world's **entire** reachable transition relation — 104 transitions
across 26 states, not just the 8 examined:

| rule | transitions | `legend-prior` correct |
|---|---|---|
| `walk` | 62 | 62 (100%) |
| `blocked_by_wall` | 32 | 32 (100%) |
| `walk_through_door` | 4 | 4 (100%) |
| `blocked_by_door` | 3 | 3 (100%) |
| `blocked_toggle_would_shut_door` | 1 | 1 (100%) |
| **`toggle_switch`** | **2** | **0 (0%)** |
| total | 104 | 102 (**98.1%**) |

The strategy is wrong about exactly one mechanism — the one the world is named
after — and right about everything else. Two observations follow, and they are
the substance of this report:

1. **The door rules are free by construction, not by luck.** The invariant
   `door_presence_tracks_net` (`GROUND_TRUTH.md:38`) says a door renders as
   colour `4` exactly when it is impassable and renders as *nothing* otherwise.
   So "a passable door looks like floor" is literally true of the pixels. An
   examinee that walks onto anything floor-coloured gets `walk_through_door`
   right without knowing doors exist, and one that stops at anything else gets
   `blocked_by_door` right without knowing nets exist. The mechanism is
   *visually transparent* in the rendered frame. Any exam over rendered frames
   in this world can never ask about it.
2. **`blocked_toggle_would_shut_door` is free for a different reason**: its
   consequent is "nothing changes", so a stasis-biased guesser is right by
   default.

`toggle_switch` — the agent bumps the switch, the agent does *not* move, and two
distant door cells change colour — is the only transition in the world whose
frame a theory-free examinee cannot produce. It is **2 of 104 transitions
(1.9%)**, and both are inside the published trace.

---

## 4. This world's honest effective size

**Effective size: 0 items.** The profile's `effective_size: 2` is the count of
items the three synthetic voters do not settle; the count of items that
*genuinely require a world model* is zero, because a fourth strategy that
`discrimination.py`'s own docstring anticipates (`:59-67`, "a fourth strategy
nobody has written could settle it for free, and the taxonomy would not notice")
settles both `-000` and `-007` from the sheet alone.

Restating the paper honestly:

| | count | share |
|---|---|---|
| items | 8 | |
| free (settled by the bluffer) | 4 | 0.500 |
| settled by a theory-free legend prior | **8** | **1.000** |
| requiring any knowledge of this world's mechanism | **0** | **0.000** |

### Dead weight, named

* **`blocked_by_wall` — 4 items, all `free`.** Already named as `barren` by the
  instrument. Its consequent is "nothing changes", so it is identical to the
  bluffer's standing answer. It can never produce a discriminating item under a
  frame-exact rubric, in this world or any other, and 50% of the paper is spent
  on it.
* **`walk` — 4 items, 2 `memorised` + 2 `theory`.** *Not* named as barren, and
  this is where the instrument overstates. `walk` is the universal grid-world
  rule; predicting it requires a direction convention and the ability to see a
  wall, both of which are given on the sheet. It is dead weight for measuring
  *this* world's theory even though it is live for measuring the memoriser.

### Rules that never reach the paper, and why

All four rules of this world's declared family `switch_door` are structurally
excluded by the matched-quota gate at `heldout_worldgen.py:127-129`, at **every**
value of `per_class` (verified at 1, 2, 3, 4):

| rule | in trace | held out | why excluded |
|---|---|---|---|
| `toggle_switch` | 2 | 0 | every reachable firing is already published in `raw_trace.jsonl` — no held-out half exists at any quota |
| `blocked_by_door` | 3 | 0 | same |
| `walk_through_door` | 0 | 4 | the trace never witnessed it — no replay control |
| `blocked_toggle_would_shut_door` | 0 | 1 | one reachable firing in the whole world; the A0′ single-witness failure |
| `door_mirrors_net` | — | — | cascade; untagged by construction, can never carry an item |

`toggle_switch` fires in only 2 of 104 reachable transitions and the 41-line
`raw_trace.jsonl` covers both of them (trace steps t=4→5 and t=5→6). The exam is
therefore not *choosing* to skip the world's mechanic — it *cannot* set a
held-out question about it, and no quota setting changes that. `t1-switch-toggle`
ships a paper that examines the two rules it shares with `t1-walk-maze` and
never once examines the thing that distinguishes it.

### Is the residue large enough to rank two examinees apart?

**No, on two independent grounds.**

1. *Statistically.* Even taking the profile's `theory = 2` at face value, two
   binary items admit exactly three distinguishable scores (0, ½, 1). A pure
   coin-flipper scores 2/2 with probability 0.25; separating two examinees at
   any conventional confidence needs an order of magnitude more items. Raising
   `per_class` to 6 gives 24 items but still `theory = 12` of the *same two
   generic rules*, so it buys precision on a quantity that is not theory.
2. *Substantively.* The residue is 0 after §3. Two examinees that differ only in
   whether they hold a world model of the switch score identically here —
   both 1.000 — because no item asks. What this paper can still rank is
   memorisation: the `gap_replay_minus_heldout` axis separates the memoriser
   (0.500) from everyone else (0.000), and that measurement is sound. It is just
   not a measurement of theory.

**Recommendation for the instrument, not for this world.** `discrimination.py`
should carry a fourth voter — a `prior` fake in
`heldout_worldgen.reference_answers` implementing the ten lines in §3 — and
report a fifth class for items that oracle *and* prior get but memoriser and
bluffer do not. On this world that class would absorb both current `theory`
items and `effective_size` would read `0`, which is the true number. Whatever
the taxonomy costs elsewhere, on `t1-switch-toggle` it converts a paper that
currently reads "25% theory" into one that reads "ranks nobody", and the second
statement is the one a question-setter needs.

---

### Reproduction

Everything above is local Python against the worktree, read-only, no network.
The re-derivation (§1) uses a hand-written simulator from `spec.json` and the
rule table, independent of `worldgen/core/world.py`; the rubric battery (§2)
calls `grade_frame_exact` directly without editing it; the strategies (§3) are
passed `item.paper` and nothing else and are scored through the ordinary
`mark()` path against `paper.key(digest())`.
