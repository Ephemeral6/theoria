# Examiner's report — `t2-lock-fragile`

Independent audit of `exam/tools/discrimination.py`'s profile of one world.
Profile audited: `exam/runs/20260728T151000Z-V7-exam-stress-fanout/worlds/t2-lock-fragile.json`
(12 items, `per_class=2`, rubric digest `e06bdf52…1cb091`, paper `v2-heldout-t2-lock-fragile`).

Everything below is local python against `worldgen/out/worlds/t2-lock-fragile/`
and the `exam` package. No files were edited, no network, no `git`.

**Headline.** The instrument's labels are *true* — every class assignment is
correct against the world's own transition function. But the label `theory` is
not doing the work its name claims. A 20-line sheet-only heuristic that has no
world model, never opens `ground_truth.json`, and knows nothing about locks,
tokens, counters or fragile tiles scores **12/12** on this paper — capturing
**4 of 4** of the `theory` residue. The honest effective size of this paper is
**0**, not 4.

---

## 1. Is the classification true of this world's mechanics?

**Yes. All 12 items hand-checked, all 12 correct.** No `free` item changes the
frame; no `theory` item fails to. Zero defects in the instrument's labelling.

I recomputed each transition from `spec.json` (layout, `entities`, `colors`) and
the two mechanism modules that own this world — `worldgen/mechanisms/count_lock.py`
and `worldgen/mechanisms/consumable.py` — then compared to the recorded
`frame_after`.

World: 7×9, agent start (1,1), goal (1,7). Tokens (1,3) (1,5) (3,1); fragile
tile (3,7); lock (5,6) with `k=3`. Palette `{floor:0, wall:1, token:2, lock:3,
fragile:4, collapsed:5, agent:6}`.

| item | action | rule | split | class | agent before → after | check |
|---|---|---|---|---|---|---|
| `-000` | DOWN | `walk` | replay | memorised | (1,5)→(2,5) | layout row2 col5 = `.`, unclaimed → walk ✓ |
| `-001` | RIGHT | `collect_token` | heldout | theory | (1,4)→(1,5) | (1,5) holds uncollected token 2 → collect; lock stays `3` (count 1→2 < k=3) ✓ |
| `-002` | DOWN | `collect_token` | replay | memorised | (2,1)→(3,1) | (3,1) token → collect; lock stays `3` ✓ |
| `-003` | DOWN | `blocked_by_wall` | replay | free | (1,2) fixed | (2,2) = `#` → no-op, frame identical ✓ |
| `-004` | RIGHT | `collect_token` | replay | memorised | (1,2)→(1,3) | (1,3) token → collect ✓ |
| `-005` | RIGHT | `walk` | heldout | theory | (1,1)→(1,2) | (1,2) floor ✓ |
| `-006` | LEFT | `blocked_by_wall` | heldout | free | (2,1) fixed | (2,0) = `#` ✓ |
| `-007` | RIGHT | `walk` | heldout | theory | (1,3)→(1,4) | (1,4) floor; tile already `5`, lock already open (drawn as 0) ✓ |
| `-008` | UP | `blocked_by_wall` | heldout | free | (1,1) fixed | (0,1) = `#` ✓ |
| `-009` | DOWN | `walk` | replay | memorised | (1,1)→(2,1) | (2,1) floor ✓ |
| `-010` | DOWN | `collect_token` | heldout | theory | (2,1)→(3,1) | (3,1) token → collect; lock stays `3` (count 1→2) ✓ |
| `-011` | DOWN | `blocked_by_wall` | replay | free | (5,2) fixed | (6,2) = `#` ✓ |

### Does the frame show enough state to predict the lock and the fragile tile?

For the lock: **yes, but only by absence.** `count_lock.render`
(`worldgen/mechanisms/count_lock.py:125-139`) draws a *closed* lock as colour 3
and an *open* lock not at all — it renders as floor. The number of colour-2
cells encodes `3 − collected` exactly (invariant `token_count`, checked on all 87
reachable states), so `collected = 3 − count(colour 2)` is readable off any
frame. An examinee can compute the counter from the sheet. Confirmed by
`ground_truth.json["frame_determines_state"]`: `injective: true`, 87 distinct
frames for 87 states.

For the fragile tile: **the pending collapse is invisible in the frame, and that
is the world's one genuinely hard fact.** `Consumable.render`
(`worldgen/mechanisms/consumable.py:117-132`) draws ARMED identically to INTACT,
and the agent is painted last, so a frame showing the agent on (3,7) shows
nothing about the tile underneath. The collapse is emitted by `settle`, one step
later, when the agent departs. It carries **no rule name at all**
(`consumable.py:103-114` writes COLLAPSED outside `interact`), so the transition
in which the tile turns to colour 5 is tagged `walk`.

**Neither mechanism is examined.** All four of this world's lock/fragile rules
are blocked out of the paper by the matched-quota gate
(`heldout_worldgen.plan`, `notes.classes_not_examined = 4`):

| blocked rule | in trace | held out | why blocked |
|---|---|---|---|
| `cross_fragile` | 0 | 1 | one witness in the whole reachable graph |
| `blocked_by_collapsed` | 0 | 2 | never witnessed by the trace |
| `blocked_by_lock` | 0 | 1 | never witnessed by the trace |
| `walk_through_lock` | 1 | 3 | one witness in the trace, `per_class=2` needed |

So the paper titled "lock + fragile" examines `walk`, `blocked_by_wall` and
`collect_token` only. It is, in item content, a walking maze with pickups.

### The classes are analytically determined, which is a fact about the instrument

On this question type the class of an item is a function of two things already
on the sheet or already in the profile:

```
free       <=> not frame_changes
memorised  <=> frame_changes and split == "replay"
theory     <=> frame_changes and split == "heldout"
```

Verified: 0 of 12 items deviate. This follows from `reference_answers`
(`exam/papers/heldout_worldgen.py:286-296`) — the bluffer is a stasis predictor
and the memoriser is a stasis predictor off-trace, so `bluffer correct <=> frame
unchanged` and `memoriser correct <=> unchanged or replay` by construction, on
every world, not just this one.

The consequence is not that the instrument is wrong; it is that on this question
type the three-voter panel produces **no information the pair (split tag,
frame_changes) does not already carry**. The `dead` detector is genuinely
load-bearing (it is an independent oracle check, and it correctly reports 0
here). The free/memorised/theory split is a re-labelling of "does the frame
change" × "is the tag printed on the sheet `replay`". `discrimination.py`'s own
docstring (lines 59-67) anticipates exactly this limit; this world is a worked
example of it.

Also worth naming: because the fragile collapse carries no rule tag, the
`by_rule` axis **cannot see the fragile mechanism at all**. The two transitions
that test it are filed under `walk`. Any per-rule reading of this world's
discrimination is blind to its headline mechanic by construction.

---

## 2. Does the marker misjudge anything on this world?

### Structural invariants — both hold

| examinee | verdict counts | score |
|---|---|---|
| `null` | `{unanswered: 12}` | 0/12 — **silence is never paid, 0 `correct`** ✓ |
| `oracle` | `{correct: 12}` | 12/12 — **ground truth is never marked wrong, 0 `wrong`** ✓ |
| `memoriser` | `{correct: 8, wrong: 4}` | 8/12, gap `replay−heldout` = 0.667 |
| `bluffer` | `{wrong: 8, correct: 4}` | 4/12 = the bluffer floor |

### Near-miss stress matrix

40 answer shapes were constructed against items `-000`, `-001`, `-003`, `-007`,
`-010` by importing `exam.grading.rubrics_heldout` directly. The rubric was not
modified. Verdicts were identical across all five probe items.

| answer shape | verdict | fair? |
|---|---|---|
| bare correct grid | `correct` | ✓ |
| `{"frame_after": grid}` / `{"frame": …}` / `{"after": …}` | `correct` | ✓ |
| wrapped + extra keys (`{"frame_after": g, "reason": "walk"}`) | `correct` | ✓ |
| tuple-of-tuples; `np.array(g).tolist()` | `correct` | ✓ |
| transposed 9×7 | `wrong`, `shape_ok:false, cells_wrong:-1` | ✓ (grid is non-square, so detectable) |
| one cell changed | `wrong`, `cells_wrong:1` | ✓ |
| short grid (5 rows) / extra 8th row | `wrong`, `shape_ok:false` | ✓ |
| ragged (one short row) | `wrong`, malformed | ✓ |
| rows reversed | `wrong`, `cells_wrong:8` | ✓ |
| colour 7 / 9 / −1 outside palette | `wrong`, malformed | ✓ verdict, ✗ diagnostic (see (d)) |
| `{"abstain": true}` | `abstained` | ✓ |
| `"abstain"` / `"  ABSTAIN  "` / `"I cannot tell"` | `abstained` | ✓ |
| `null` | `unanswered` | ✓ |
| `{}` , `[]` , `{"frame_after": null}` | `wrong` | **✗ arguably** |
| cells as `"0"`/`"1"` strings | `wrong` | **✗ arguably** |
| cells as floats `0.0`/`1.0` | `wrong` | **✗ arguably** |
| cells as `numpy.int64` | `wrong` | **✗ arguably** |
| cells as `bool` | `wrong` | ✓ (documented at `rubrics_heldout.py:104`) |
| rows as digit strings `"111111111"` | `wrong` | borderline |
| `{"abstain": true, "frame_after": <correct grid>}` | `abstained` (0 pts) | borderline, undocumented |
| `{"abstain": false, "frame_after": <correct grid>}` | `correct` | ✓ |
| `{"answer": g}` / `{"grid": g}` / `[g]` / `0` / `true` | `wrong` | ✓ |
| all-floor 7×9 | `wrong`, `cells_wrong:43` | ✓ |
| two agents (legal palette, illegal world state) | `wrong`, `cells_wrong:1` | ✓ |

### The verdicts I would argue are unfair

None of these *awards* a mark that should not be awarded — everything below
scores 0 either way, and no invariant is broken. The damage is that a
**formatting failure is recorded as a prediction failure**, and every downstream
aggregate reads it as one.

**(a) Numeric-type strictness — `numpy.int64` and `float` are marked `wrong`.**
`rubrics_heldout.py:104` is
`if isinstance(cell, bool) or not isinstance(cell, int): return None`.
`np.int64(6)` is not a python `int`; `6.0` is not either. Both compare equal to
the truth cell. An examinee that predicted this world's frames *perfectly* and
serialised through numpy, or through a JSON layer that widened ints to floats,
is told it was wrong about the world. Note the split hair: `np.array(g).tolist()`
→ `correct`, `[[np.int64(c) …]]` → `wrong`. A fair examiner would say **correct**
in both cases (value equality holds cell for cell), or at minimum would not
report the two differently. The rubric's own docstring (`:80-84`) states the
governing principle — that an examinee who predicts correctly and wraps
differently has not made a prediction error, and that scoring it as one would be
marking JSON conventions — and these three cases are that principle's own
counter-examples.

**(b) Empty submissions are split between two verdicts.** `None` → `unanswered`
(`:138-142`, with the comment that it is "treated as nothing submitted, which is
what it is"), but `{}` → `wrong`, `[]` → `wrong`, `{"frame_after": null}` →
`wrong`. These are the same event. A fair examiner would call all four
`unanswered`. Concrete downstream cost: `axes["unanswered"]` undercounts, and —
more importantly for this instrument — an examinee that emits `{}` where it has
no theory is classified by `discrimination.py` as having *tried and failed*
rather than as having said nothing, which is exactly the distinction the module
docstring says it keeps `null` out of the voter panel to preserve.

**(c) There is no `malformed` verdict.** `exam/model.py:233` freezes
`VERDICTS = ("correct", "wrong", "abstained", "unanswered")`. `_as_frame`
returning `None` therefore collapses into `wrong`, which is the structural root
of (a) and (b): the marker has the information (`detail["why"] = "answer is not
a well-formed frame"` is right there) and no verdict slot to put it in. Every
aggregate in `discrimination.py`, `axes()` and `run_matrix` reads
`verdict == "correct"` and cannot tell the two apart. This is the single change
that would fix the most of this list.

**(d) Off-palette answers lose their diagnostic.** A grid that is correct except
for one cell holding colour 7 returns `{"why": "answer is not a well-formed
frame"}` with **no `cells_wrong`**, while the same grid with an in-palette wrong
cell returns `cells_wrong: 1`. Two answers one cell apart get diagnostics of
different kinds. The verdict is defensible (`wrong` either way); the loss of the
diff is not, and `detail` is explicitly the diagnostic channel.

**(e) Abstention beats a submitted correct frame.** `_is_abstention` runs at
`:144`, before `_as_frame` at `:149`, so `{"abstain": true, "frame_after": <the
correct grid>}` scores 0 as `abstained`. Defensible precedence — the examinee
did declare it could not tell — but it is undocumented, and it is the one case
where a *correct* frame reaches the marker and earns nothing. Worth one line in
the docstring either way.

---

## 3. A cheap examinee that beats the bluffer floor

**Bluffer floor: 4/12 = 0.3333** (the four `blocked_by_wall` items; confirmed by
running the bluffer, and by `notes["unchanged_frame_share"] = 0.333333`).

### The strategy

Reads `frame_before`, `action`, `legend`, `grid` from the sheet. Nothing else.
No `ground_truth.json`, no `Item.truth`, no world module, no per-item table.

```
1. locate the agent: the unique cell equal to legend["agent"]
2. target = agent + delta(action)
3. if target is off-grid, or frame_before[target] == legend["wall"]:
       predict frame_before unchanged
4. else: predict frame_before with legend["floor"] written at the agent's old
       cell and legend["agent"] written at the target
```

Three generic grid priors, and no world-specific knowledge: *walls block*, *the
agent moves one cell*, *the agent leaves floor behind and paints over whatever
it steps onto*. The two colour names it uses (`wall`, `floor`) are printed on the
sheet in `legend`.

### Result

| examinee | score | replay | heldout | gap |
|---|---|---|---|---|
| bluffer (floor) | **4/12 = 0.3333** | 0.333 | 0.333 | 0.000 |
| memoriser | 8/12 = 0.6667 | 1.000 | 0.333 | 0.667 |
| **cheap heuristic** | **12/12 = 1.0000** | 1.000 | 1.000 | 0.000 |
| oracle | 12/12 = 1.0000 | 1.000 | 1.000 | 0.000 |

Per discrimination class: `free` 4/4, `memorised` 4/4, **`theory` 4/4**.
Per rule: `walk` 1.00, `blocked_by_wall` 1.00, `collect_token` 1.00, on both
splits.

**It captures 100% of the `theory` residue and ties the oracle.** It is exactly
the "fourth strategy nobody has written" that `discrimination.py`'s docstring
(lines 59-67) names as the taxonomy's blind spot. On this world the blind spot
is total: there is no item the panel calls `theory` that the fourth strategy
does not settle for free.

Why it works: the `collect_token` items look identical to `walk` items under
this heuristic, because a collected token stops being drawn and the agent paints
over its cell anyway. The token mechanic is invisible in a one-step prediction
unless the collection is the one that opens the lock — and none of the four
`collect_token` items is.

### Where it does break — and none of it is on the paper

Swept over all 348 reachable transitions of the world:

| rule | transitions | cheap correct | bluffer correct |
|---|---|---|---|
| `blocked_by_wall` | 171 | 171 | 171 |
| `walk` | 162 | **160** | 0 |
| `collect_token` | 7 | **5** | 0 |
| `walk_through_lock` | 4 | 4 | 0 |
| `blocked_by_collapsed` | 2 | **0** | 2 |
| `cross_fragile` | 1 | 1 | 0 |
| `blocked_by_lock` | 1 | **0** | 1 |
| **total** | **348** | **341 (97.99%)** | 174 (50.00%) |

The seven transitions a sheet-only heuristic cannot get are precisely this
world's signature:

* **2 × `walk` from (3,7)** (UP and DOWN out of the armed fragile tile) — the
  departed cell must become colour 5, not 0. This is `consumable.py`'s
  one-frame-delayed collapse, and it is the only place in the world where the
  current frame does not contain the information needed to predict the next one.
  Filed under `walk`.
* **2 × `blocked_by_collapsed`** — colour 5 is impassable; the heuristic walks in.
* **1 × `blocked_by_lock`** — colour 3 with `collected < 3`; the heuristic walks in.
* **2 × `collect_token`** — the third collection also erases the lock at (5,6)
  in the same frame (3→0). Requires having induced the counter and `k=3`.

Note that `cross_fragile` itself is **not** discriminating: walking onto an
intact tile looks exactly like walking onto floor, because the agent paints over
it. The fragile family's whole difficulty lives in the departure, which the rule
taxonomy calls `walk`.

---

## 4. Honest effective size

**Items requiring a world model: 0 of 12.** Not the 4 the profile's
`effective_size` field reports.

The profile's own numbers are internally consistent (`theory_share = 0.333`,
`zero_discrimination_share = 0.333`, `barren_rules = ["blocked_by_wall"]`), and
all four of its `theory` items really are items the published three-voter panel
does not settle. They are also all four settled by a heuristic with no theory,
so the number that should be quoted as "how many questions ask for a world
model" is zero.

### Dead weight, by name

* **`blocked_by_wall` — 4 items, ranks nobody.** Correctly flagged `barren` by
  the instrument. Every one of its 171 reachable transitions leaves the frame
  identical, so the bluffer, the memoriser, the cheap heuristic and the oracle
  all score them. A third of the paper.
* **`walk` — 4 items, ranks nobody in practice.** 160 of its 162 transitions are
  a one-cell agent move that any grid prior predicts. Only 2 (departure from the
  armed tile) discriminate, and neither was drawn.
* **`collect_token` — 4 items, ranks nobody in practice.** 5 of 7 transitions
  are indistinguishable from `walk` on a single step. Only the 2 that trip the
  lock discriminate, and neither was drawn.

### Rules that are dead weight because they are *absent*

The four rules that carry this world's identity are not on the paper at all:
`cross_fragile`, `blocked_by_collapsed`, `blocked_by_lock`, `walk_through_lock`.
All four are excluded by the matched-quota gate for the same reason the world
exists — they are irreversible or near-irreversible and the 110-step trace
(`coverage.json`: 102/348 pairs, 29.3%) witnessed each at most once. The world's
own `spec.json` note says it: *"Nearly every rule here has a single witness."*
The quota rule that makes the `replay`/`heldout` tag safe is, on exactly this
world, the rule that deletes everything the world was built to test.

### Why the selection missed the needle

Per candidate pool, how many members the cheap heuristic gets wrong, and what
`_pick`'s salted hash actually drew:

| rule | split | pool | discriminating | drawn | P(a uniform 2-draw hits one) |
|---|---|---|---|---|---|
| `blocked_by_wall` | replay | 45 | 0 | 0 | 0.000 |
| `blocked_by_wall` | heldout | 126 | 0 | 0 | 0.000 |
| `walk` | replay | 53 | 0 | 0 | 0.000 |
| `walk` | heldout | 109 | **2** | **0** | 0.037 |
| `collect_token` | replay | 3 | **1** | **0** | 0.667 |
| `collect_token` | heldout | 4 | **1** | **0** | 0.500 |

Expected discriminating items under a uniform draw: **≈ 1.20 of 12**. The
deterministic salted-hash draw got 0. So this is not bad luck so much as a
structural mismatch: the discriminating transitions are a 7-in-348 needle (2.0%
of the relation) and the sampler is uniform over a pool that is 98% generic
grid-walking. Even the best case on offer is one or two items.

### Can it rank two examinees apart?

**Against the published panel, yes but weakly: it separates a memoriser (8/12)
from a bluffer (4/12), gap 0.667 — which is a recall test, not a theory test.**

**Against any examinee that has a generic grid prior, no.** Two such examinees
both score 12/12 and the paper cannot order them, however different their world
theories are. The paper's discriminating power against the class of examinee
Theoria actually cares about is zero items, and a zero-item instrument cannot
rank anything.

### What would fix it

Nothing in `discrimination.py` — it reported this world correctly. The fix is in
item selection: the paper needs the seven transitions listed in §3 to be
*reachable as items*, which means either (i) relaxing the matched quota for
single-witness rules and accepting a `heldout`-only class with the tag
suppressed from the sheet, or (ii) selecting within a pool by "how many of the
published fakes disagree" rather than by a uniform salted hash. Option (ii) is
cheap: the pool table above was computed in seconds, and it would have found all
four of `collect_token`'s and `walk`'s discriminating candidates. Adding the
cheap heuristic of §3 as a fifth calibration fake would make the whole failure
visible in `run_matrix` without any new instrument.

---

## Things not asked about

1. **`discrimination.py`'s `by_rule` axis is blind to the world's headline
   mechanic.** The fragile collapse is emitted by `settle` and carries no rule
   tag, so the only two transitions that test it are filed under `walk`. Any
   report that says "which mechanism to fix" by reading `by_rule` will name
   `walk` here, which is not actionable. `GROUND_TRUTH.md` documents *cascade*
   rules as untagged; this collapse is not even listed as a cascade
   (`ground_truth.json["rule_correspondence"]["cascade"] = []`), so there is no
   trace of it in the rule axis at all.

2. **The roster row's `rules_never_witnessed` field lists all seven rules**
   (`worldgen/out/worlds/INDEX.json`, surfaced by
   `worldgen_port.summary("t2-lock-fragile")`), including `blocked_by_wall`,
   which fires 45 times inside the trace. It is copying
   `coverage.json["rules_never_witnessed"]`, which is a per-rule count of
   *uncovered state-action pairs* (`blocked_by_wall: 126`), not a list of
   unwitnessed rules. The name reads as an alarm and is not one; anything that
   renders that field will report a healthy world as having seven dead rules.
   The same content is duplicated under the accurate name
   `rules_with_uncovered_pairs`. `declared_never_fires` is correctly `[]`.

3. **`axes()["items"]` is not what it says.**
   `exam/papers/heldout_worldgen.py:332-334` binds
   `unchanged = sum(1 for entry in key_doc["items"] if
   entry["truth"]["frame_after"] is not None)` — the variable is named
   `unchanged` but counts items *with a truth frame at all*, which is every item.
   It reports 12 here and would report the item count on every world. The
   docstring at `rubrics_heldout.py:29-34` says the unchanged-frame statistic
   "belongs in `axes()`", so the intended computation appears to be missing
   rather than merely misnamed. `Paper.notes["unchanged_frame_share"]` carries
   the real number (0.333333).

4. **`transitions_in_trace` (102) < the trace's 110 transitions.** Expected —
   `evidence_index` is keyed on rendered frame + action, and the trace revisits 8
   `(frame, action)` pairs. Recorded because it means the `replay` pool is
   slightly smaller than a reader of `coverage.json` would assume.
