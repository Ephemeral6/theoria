# Examiner's report — `t1-push-corridor`

Independent audit of the discrimination profile at
`exam/runs/20260728T151000Z-V7-exam-stress-fanout/worlds/t1-push-corridor.json`.

Read-only on every existing file; no source edited, no `git`, no network, no
pytest suite. All numbers below come from targeted in-process python against
`exam.papers.heldout_worldgen`, `exam.grading.*`, `exam.leakage` and
`worldgen/out/worlds/t1-push-corridor/`.

**Reproduction.** `discrimination.profile_world("t1-push-corridor", 2)` re-run in
this worktree is **byte-identical** to the published profile
(`canonical(mine) == canonical(published)`), and `registry.digest()` still equals
the profile's `rubric_digest` `e06bdf52…1cb091`. The artefact is current.

**Headline.** The classification is correct — every item, checked by hand and by
an independently written simulator. But the profile's `effective_size: 2` is an
**over-estimate**: on this world the two `theory` items, and in fact all eight,
are answered 8/8 by three separate strategies that hold no theory of this world,
one of which does nothing but read a field the sheet prints. The honest effective
size of `v2-heldout-t1-push-corridor` is **0**.

---

## The world, in one screen

`worldgen/out/worlds/t1-push-corridor/spec.json` — grid 5×6, seed 103, tier 1,
`variant_of: t1-push-open`, `variant_delta: "same mechanism, dead-end corridor
instead of an open room"`.

```
######      palette: floor 0, wall 1, block 2, agent 6
#....#      agent_start (1,1), block (1,3), goal (3,4)
#.####      9 free cells; the agent can reach 8 of them
#....#      15 reachable states, 60 reachable transitions
######
```

Four declared rules (`GROUND_TRUTH.md:22-27`), with reachable firing counts from
`ground_truth.json["reversibility"]["rules"]`:

| rule | firing transitions | on the paper? |
|---|---|---|
| `blocked_by_wall` | 32 | yes, 4 items |
| `walk` | 26 | yes, 4 items |
| `push` | 1 | **no** — `in_trace 1, held_out 0` |
| `blocked_by_block` | 1 | **no** — `in_trace 0, held_out 1` |

---

## Q1 — Is the classification true of this world's mechanics?

**Yes. All 8 of 8 items verified, no defect found.**

I wrote a simulator from `spec.json`'s `layout` and `colors` plus the four rules
as stated in `GROUND_TRUTH.md`, parsing agent and block positions out of the
rendered `frame_before` rather than out of any state object. It reproduces
`GridWorld` exactly: **60 of 60 reachable transitions match on both the next
frame and the rule name, 0 mismatches** (`blocked_by_wall` 32, `walk` 26, `push`
1, `blocked_by_block` 1).

Per item — every one of the eight was hand-checked, not a sample:

| item | action | agent → target | my rule | truth rule | frame match | class | changes |
|---|---|---|---|---|---|---|---|
| `t1-push-corridor-000` | UP | (3,1) → (2,1) floor | `walk` | `walk` | ✔ | theory | yes |
| `t1-push-corridor-001` | LEFT | (1,3) → (1,2) floor | `walk` | `walk` | ✔ | memorised | yes |
| `t1-push-corridor-002` | DOWN | (1,1) → (2,1) floor | `walk` | `walk` | ✔ | memorised | yes |
| `t1-push-corridor-003` | UP | (1,1) → (0,1) wall | `blocked_by_wall` | `blocked_by_wall` | ✔ | free | no |
| `t1-push-corridor-004` | LEFT | (2,1) → (2,0) wall | `blocked_by_wall` | `blocked_by_wall` | ✔ | free | no |
| `t1-push-corridor-005` | LEFT | (3,3) → (3,2) floor | `walk` | `walk` | ✔ | theory | yes |
| `t1-push-corridor-006` | UP | (3,4) → (2,4) wall | `blocked_by_wall` | `blocked_by_wall` | ✔ | free | no |
| `t1-push-corridor-007` | LEFT | (2,1) → (2,0) wall | `blocked_by_wall` | `blocked_by_wall` | ✔ | free | no |

* **No `free` item changes the frame.** All four (`-003`, `-004`, `-006`,
  `-007`) are genuinely fixed points; the bluffer is correct because the world
  really does nothing, not because the marker is lenient.
* **Both `theory` items change the frame** (`-000`, `-005`), and both are
  `heldout` — I confirmed independently against `raw_trace.jsonl` that neither
  `(frame_before, action)` key appears in the published trace, so the memoriser
  genuinely cannot have them.
* **Both `memorised` items** (`-001`, `-002`) are in the trace, and the trace's
  own published successor frame equals `truth.frame_after` in both cases. `-002`
  is trace line `t=0`; `-001` is trace line `t=19`; `-003` is `t=15`; `-007` is
  `t=8`.
* The `replay`/`heldout` tag agrees with the raw trace on **8 of 8** items.
  `run_matrix.tag_bias(paper) = 0.0` — the tag is outcome-neutral here.

**No instrument defect.** `discrimination._classify` (`discrimination.py:95-114`)
produced no `anomaly:` triple, `dead = 0`, and the profile's `frame_changes`
field matches my recomputation on all eight.

One structural fact worth naming, because it is what makes the rest of this
report possible: on this world **`class` is a pure function of `rule`**.
`blocked_by_wall` ⟺ `free` ⟺ frame unchanged; `walk` ⟺ frame changes ⟺
`theory` or `memorised` depending only on the split. There is no item where the
outcome is not read off the rule name.

---

## Q2 — Does the marker misjudge anything on this world?

### Structural invariants: both hold

Marked through `exam.grading.mark.mark` with `axes_fn=heldout_worldgen.axes`:

| examinee | score | verdicts | `gap_replay_minus_heldout` |
|---|---|---|---|
| `oracle` | 1.000 | `correct` × 8 | 0.0 |
| `null` | 0.000 | `unanswered` × 8 | 0.0 |
| `memoriser` | 0.750 | `correct` × 6, `wrong` × 2 | 0.5 |
| `bluffer` | 0.500 | `correct` × 4, `wrong` × 4 | 0.0 |

* **Silence is never paid.** `null` is `unanswered` on 8 of 8, `correct` on 0.
* **Ground truth is never marked wrong.** `oracle` produces 0 `wrong`, 8
  `correct`.
* The palette reaches the marker: all 8 items carry
  `truth.legal_cells = [0,1,2,6]`. Confirmed the fallback matters — strip
  `legal_cells` from an item's truth and the *correct* frame is rejected as "not
  a well-formed frame", because `_LEGAL_CELLS` defaults to `{0,2,4,8}`
  (`rubrics_heldout.py:56`) and this world's walls are `1` and its agent is `6`.
  The mechanism at `_legal_cells` (`rubrics_heldout.py:59-70`) is load-bearing
  and is working.

### Stress cases

Every case below was run through `grade_frame_exact` on both
`t1-push-corridor-000` (a `theory` item, frame changes) and
`t1-push-corridor-003` (a `free` item, frame does not). **The two items gave
identical verdicts on every case**, so one table serves.

| answer | verdict | pts | fair? |
|---|---|---|---|
| correct grid, bare | `correct` | 1.0 | ✔ |
| correct grid, `{"frame_after": …}` | `correct` | 1.0 | ✔ |
| correct grid, `{"frame": …}` | `correct` | 1.0 | undocumented, see F-3 |
| correct grid, `{"after": …}` | `correct` | 1.0 | undocumented, see F-3 |
| correct grid as tuple-of-tuples | `correct` | 1.0 | ✔ |
| correct grid **transposed** (6×5) | `wrong`, `shape_ok:false, cells_wrong:-1` | 0.0 | ✔ |
| correct grid, **one cell changed** to another legal colour | `wrong`, `cells_wrong:1` | 0.0 | ✔ |
| correct grid, **cells as strings** `"1"` | `wrong`, "not a well-formed frame" | 0.0 | see F-1 |
| **rows as strings** `["111111", …]` | `wrong`, "not a well-formed frame" | 0.0 | see F-1 |
| correct grid, **cells as floats** `1.0` | `wrong`, "not a well-formed frame" | 0.0 | see F-2 |
| ragged (row 2 one cell short) | `wrong`, "not a well-formed frame" | 0.0 | ✔ |
| short grid (4 rows of 6) | `wrong`, `shape_ok:false` | 0.0 | ✔ |
| colour `8`, **outside this world's palette** | `wrong`, "not a well-formed frame" | 0.0 | ✔ |
| `{"abstain": true}` | `abstained` | 0.0 | ✔ |
| `{}` (empty dict) | `wrong` | 0.0 | see F-4 |
| `null` | `unanswered` | 0.0 | ✔ |
| `[]` (empty list) | `wrong` | 0.0 | see F-4 |
| `"abstain"` (string) | `abstained` | 0.0 | ✔ |
| `"no idea"` (string) | `wrong` | 0.0 | see F-5 |
| `{"frame_after": null}` | `wrong` | 0.0 | see F-4 |
| `{"abstain": true, "frame_after": <the correct grid>}` | `abstained` | **0.0** | see F-6 |
| booleans in place of 0/1 | `wrong`, "not a well-formed frame" | 0.0 | ✔ (documented, `:104`) |
| correct grid + trailing `[]` row | `wrong` | 0.0 | ✔ |
| nested one level too deep | `wrong` | 0.0 | ✔ |

**No case was found where a wrong prediction scored, or where a correct
prediction was refused** — with the single exception of F-6 below. What follows
are the arguable calls, in descending order of how much a fair examiner would
object.

**F-6 — a correct frame submitted alongside `abstain` scores zero, and this
costs a real mark.** `grade_frame_exact:144` tests `_is_abstention(answer)`
*before* it ever calls `_as_frame`, so `{"abstain": true, "frame_after": <exactly
the true grid>}` short-circuits to `abstained`/0.0. This is the only case in the
table where a fully correct, well-formed prediction is present in the submission
and earns nothing. A fair examiner faced with a hedged-but-correct answer would
either mark it `correct` (the prediction is there and it is right) or flag the
self-contradiction explicitly; silently taking the abstention is the one reading
that is strictly worse for the examinee than either. Note the asymmetry with the
other verdicts: `abstained` and `wrong` both pay 0.0, so most of this table's
disagreements are labelling only — F-6 is the one that moves the score.

**F-1 — the spec's own grid dialect is marked as a wrong prediction.**
`spec.json` writes grids as a list of strings (`"######"`, `"#....#"`), and that
file is licensed open to the examinee. An examinee that answers in the dialect
the world publishes — `["111111","100021",…]` — is refused by `_as_frame:97`
(`row` is not a list/tuple) and reported as `wrong`. So is a cells-as-strings
answer. The instructions do say "a list of rows of integers"
(`heldout_worldgen.py:213-218`), so scoring 0 is defensible; what is not
defensible is that the *verdict vocabulary has no word for it*. `VERDICTS` is
`("correct","wrong","abstained","unanswered")` (`model.py:233`), so a stringly
serialised but perfectly correct world theory lands in the same bucket as a
confident false prediction. The only trace of the difference is `detail.why`,
which no axis aggregates. For an LLM examinee — the population this exam exists
to measure — rows-as-strings is one of the most likely output formats there is,
and this world's own open artefact models it. A fair examiner would give this a
distinguishable verdict (or a re-submit), not silently fold it into `wrong`.

**F-2 — integral floats are refused.** `[[1.0,1.0,…]]` is "not a well-formed
frame" (`_as_frame:104`, `not isinstance(cell, int)`). A frame written with float
syntax is still that frame; JSON does not distinguish `1` from `1.0` at the type
level for most producers. The `bool` exclusion on the same line is justified in a
comment and is right; the float exclusion is not justified anywhere. Cheap fix
would be to accept a float that is integral. Same consequence as F-1: it reads on
a report as a wrong theory.

**F-4 — "nothing submitted" splits three ways for no stated reason.** `null` →
`unanswered`; `{}` → `wrong`; `[]` → `wrong`; `{"frame_after": null}` → `wrong`.
The rubric's own comment at `:139-140` says an explicit null "is treated as
nothing submitted, which is what it is" — but `{}`, `[]` and `{"frame_after":
null}` are equally nothing submitted, and get the harsher label. No score
consequence (both 0.0), but `axes()` publishes an `unanswered` count
(`heldout_worldgen.py:343`), and an examinee whose harness emits `{}` on failure
will read as having answered wrongly eight times rather than as having answered
nothing.

**F-5 — the abstention vocabulary is a closed four-element list.**
`_is_abstention:119-120` accepts exactly `abstain`, `abstained`, `unknown`, `i
cannot tell`. `"no idea"`, `"I don't know"`, `"cannot determine"` all fall
through to `wrong`. The module docstring (`:17-21`) says the abstention verdict
exists "so a report can say whether an examinee knew it did not know" — a
four-phrase whitelist systematically converts natural-language declines into
wrongs and corrupts exactly the statistic the distinction was built for.

**F-3 — the marker accepts two wrappers the sheet never promises.** The
instructions promise the bare grid and `{"frame_after": …}`; `_as_frame:88` also
accepts `{"frame": …}` and `{"after": …}`. Harmless leniency, but it is an
undocumented tolerance that favours an examinee who has read the marker's source
over one who has read the sheet, and the module's stated contract is that the
rubric marks predictions, not JSON conventions.

---

## Q3 — Can a cheap examinee beat the bluffer floor without a world model?

**Yes — comprehensively. Three independent strategies score 8/8 = 1.000 and
capture 2 of 2 `theory` items, i.e. 100% of the informative residue.**

The bluffer floor here is 4/8 = **0.500** (the four `blocked_by_wall` items).
Each strategy below is a pure function of the *sheet* — `paper.sheet(digest())`,
i.e. `item_id`, `points`, `tags`, `frame_before`, `action`, `legend`, `grid` —
and, where stated, the world's **open** `raw_trace.jsonl`. None reads
`ground_truth.json`; none touches `Item.truth`; none was tuned against the
answers.

| strategy | score | free 4 | memorised 2 | theory 2 |
|---|---|---|---|---|
| **S0** bluffer — return `frame_before` (the floor) | 4/8 = 0.500 | 4/4 | 0/2 | 0/2 |
| **S1** read the rule name printed in `tags` | **8/8 = 1.000** | 4/4 | 2/2 | **2/2** |
| **S2** generic grid prior, using `legend` names | **8/8 = 1.000** | 4/4 | 2/2 | **2/2** |
| **S3a** legend-free, mover = higher singleton colour | **8/8 = 1.000** | 4/4 | 2/2 | **2/2** |
| S3b legend-free, mover = lower singleton colour | 2/8 = 0.250 | 2/4 | 0/2 | 0/2 |
| **S4** local rule learned from the open `raw_trace.jsonl` | **8/8 = 1.000** | 4/4 | 2/2 | **2/2** |

**S1 — the sheet prints the answer.** `Item.sheet_side()` (`model.py:108-111`)
splats `tags` onto the sheet, and `heldout_worldgen.py:204` sets
`tags=(split, "rule:%s" % rule)`. So every item on this paper carries
`"rule:walk"` or `"rule:blocked_by_wall"` in plain text. S1 is four lines: if the
tag starts `rule:blocked`, return the input; otherwise translate the agent one
cell. It holds no theory of pushing, of block interaction, of geometry, of
anything — it reads an English word off the question paper. 8/8.

**S2 — a universal grid prior, no world knowledge.** The legend on the sheet
names the colours: `{"agent":6,"wall":1,"floor":0,"block":2}`. S2 applies the
single most generic prior in the genre — *walls stop you, otherwise you advance
one cell* — with no knowledge of this world at all. 8/8, and it never once has to
decide what a block does, because **no item on this paper has a block in the
action direction**. The word "wall" in the legend is doing the work.

**S3a — even the legend is dispensable.** Infer the wall colour as the colour
tiling the border, the floor as the commonest interior colour, and guess that the
mover is the higher-valued of the two singleton colours. 8/8. (S3b, guessing the
lower singleton — i.e. mistaking the block for the agent — collapses to 2/8, so
the legend is worth 6 marks against a wrong guess but 0 against a right one. A
coin-flip examinee expects 5/8, still above the floor.)

**S4 — learn the rule from the published trace, no legend, no priors.** From
`raw_trace.jsonl` alone S4 identifies the mover as the singleton colour that most
often lands on a changed cell (recovers `6`), learns the colour it leaves behind
(recovers `0`), and builds a table keyed on the colour one step ahead of the
mover:

```
ahead=0 -> the mover advances      ahead=1 -> nothing happens
ahead=2 -> something changes  (learned from the trace's one push, never needed)
```

Then it generalises that table over the action. 8/8, both `theory` items
included. This is the most honest form of the finding: an examinee that does
nothing but tabulate a 1-cell neighbourhood from the licensed trace answers this
paper perfectly, including the items the profile calls "the only class that needs
a world model".

**Why this is not peeking.** The `theory` items are `walk` transitions in states
the trace never visited. But `walk` is *state-independent*: the local rule "floor
ahead ⇒ advance" transfers from any witnessed state to any unwitnessed one. The
held-out split holds out *states*, and this world's residue only ever required
*locality*. That is the gap the instrument does not see, and it is exactly the
limit `discrimination.py:59-67` names in its own "WHAT THIS IS NOT" section —
S4 is the fourth strategy that section says nobody wrote down.

---

## Q4 — What is this world's honest effective size?

**The profile says `effective_size: 2`. The honest answer is 0.**

`theory = 2` is correct as defined — two items that `oracle` alone, of the three
voters, gets right. But "requires a world model" is the claim the number is
quoted for, and on this world it is false: S1, S2, S3a and S4 each take 2/2 of
them while holding no theory of `t1-push-corridor`. There is no item on this
paper that separates an examinee with a theory of *this* world from one with a
generic grid reflex.

**The item budget, honestly accounted:**

| | items | ranks anybody? |
|---|---|---|
| `free` (`blocked_by_wall`) | 4 | no — bluffer has them |
| `memorised` (`walk`, replay) | 2 | separates trace-readers only |
| `theory` (`walk`, heldout) | 2 | not against S1/S2/S3a/S4 |
| **requires a theory of this world** | **0** | — |

**Dead weight, by name:**

* **`push` — dead, and it is the world's entire reason for existing.** 1 of 60
  reachable transitions; `in_trace 1, held_out 0`, so `plan()` blocks it
  (`heldout_worldgen.py:130-137`). `spec.json`'s own note says "The block can be
  shoved exactly once before it meets the wall, and the agent can never reach its
  far side… This is the A0 vs A0′ contrast with the mechanism held fixed and only
  the geometry moved." The matched-quota rule is *correct* to refuse it — a rule
  with one witness has no second witness to hold out, which is precisely the A0′
  failure mode. But the consequence is that the one mechanism this world was
  built to exhibit is the one mechanism the paper cannot ask about. `t1-push-open`
  and `t1-push-corridor` differ only in whether `push` is re-witnessable, and
  neither paper contains a `push` item, so the contrast the pair was constructed
  to make is invisible to this question type.
* **`blocked_by_block` — dead.** 1 reachable transition, `in_trace 0,
  held_out 1`. Blocked for the mirror reason (no replay control).
* **`blocked_by_wall` — on the paper and barren.** 4 items, all `free`. The
  profile already names it in `summary.barren_rules`, correctly. Its 32 reachable
  transitions are the world's most abundant, and every one of them is a fixed
  point, so `per_class=2` spends **half the paper** buying marks the bluffer
  already has.
* **`walk` — carries 100% of the discriminative content**, and is the most
  generic rule in the catalogue. Of the paper's 8 items, 4 are `walk`; of those,
  2 are replay (beaten by a memoriser) and 2 are held-out (beaten by S4).

**Is the residue large enough to rank two examinees apart?** No, on two counts.

1. *Statistically.* Even taking the profile's own `theory = 2` at face value, the
   resolution is three points (0, 1, 2 of 2). One item flipping moves the paper
   score by 0.125 and the residue by 0.5. Two examinees whose theories differ can
   tie at 2/2 or separate by a coin-flip; there is no confidence to be had from
   n = 2 with no partial credit.
2. *Substantively.* The residue is not about this world. Both `theory` items ask
   "does the agent step onto adjacent floor". Any examinee that has seen one grid
   world answers them, and the four strategies above prove it constructively.

**What would fix it.** Not more items of the same kind — `per_class=3` would add
one more `walk` pair and one more `blocked_by_wall` pair and change nothing. The
constraint is the world: 15 reachable states, 60 transitions, and the interesting
mechanism reachable exactly once. `t1-push-corridor` is a legitimate *world* — its
reversibility stamp (0.75, single-witness `push`) is the finding it was built to
carry — but it cannot carry a held-out prediction paper that measures anything.
The honest report line is "this world ranks nobody", the same line the
instrument already prints for a `theory_share == 0` world; it just does not print
it here, because the two `walk` items look informative and are not.

---

## Not asked for, but found

**X-1 (highest severity) — this paper fails the exam's own leak gate, and the
gate is never run on it.** Every item declares its rule name as a leak probe
(`heldout_worldgen.py:203`, `leak_probes=(cand["rule"],)`), and the sheet prints
that rule name in `tags`. Running the gate by hand:

```
leakage.check_paper(paper, paper.sheet(digest()), key_doc=paper.key(digest()))
-> LeakageError: v2-heldout-t1-push-corridor leaks its own answers:
   [{'item_id': 't1-push-corridor-000', 'check': 'probe', 'hits': ['walk']},
    … all 8 items …]
```

**8 of 8 items hit check 1.** The reason nobody has seen this: `exam/tools/build_papers.py:72`
is the only caller of `check_paper`, and it iterates `BUILDERS`
(`exam/papers/__init__.py:34-39`), which lists `heldout`, `handover`,
`adaptation`, `verdict` — **not** `heldout_worldgen`. The entire world-factory
paper family bypasses the leak gate. This is the same class of failure recorded
at `exam/DECISIONS.md:226` ("an optional check is a check that does not run"),
one layer up: the check is not optional, it is simply not wired to this builder.

**X-2 — the test that should have caught X-1 passes vacuously.**
`exam/tests/test_worldgen_papers.py:71` asserts no rule name appears on the
sheet, and it searches for `'"%s"' % rule` — the *quoted* token `"walk"`. The
sheet contains `"rule:walk"`, in which `walk` is preceded by `:` and not by a
quote, so the substring is absent and the assertion passes. Measured on this
world:

| rule | `"<rule>"` in `spec.json`? | `"<rule>"` in sheet? | `rule:<rule>` in sheet? |
|---|---|---|---|
| `walk` | False | **False** (test passes) | **True** |
| `blocked_by_wall` | False | **False** (test passes) | **True** |

The test's own docstring is about the `push`-is-also-a-family exemption, which is
sound reasoning; the quoting convention it uses to implement that reasoning is
what defeats it. Note that the exemption does not even apply here — neither
`walk` nor `blocked_by_wall` appears in `spec.json` — so the sheet is introducing
answer vocabulary the open files never gave the examinee, which is exactly what
the test was written to forbid.

**X-3 — `derive_label_sets` would excuse the leak even if the gate ran.**
`leakage.py:184-187` skips any truth field whose value already appears in the
sheet text, on the reasoning that "a field the sheet already publishes is a
stratum, not an answer". That reasoning was written for `split`, which is
deliberately printed and is provably uninformative here (`tag_bias = 0.0`). It
silently extends to `rule`, which is printed by accident and is a perfect answer
key. Confirmed: `derive_label_sets(paper, key_doc)` returns `{}` on this world —
both `split` and `rule` are excused, so checks 3 and the metadata check see
nothing. Only check 1 fires, and check 1 is not being run.

**X-4 — the discrimination instrument cannot see X-1, by construction.** Its
three voters are all defined in terms of the truth (`reference_answers`,
`heldout_worldgen.py:257-298`); none of them reads the sheet. So a paper that
prints its answers in a tag looks exactly like a paper that does not.
Adding a fifth calibration examinee that answers *only from the sheet* — the
S1 strategy above is ~10 lines — would turn X-1 into a number on the matrix
rather than an audit finding. The same voter would have caught this on every
world in the factory at once.

**X-5 — good news worth recording.** `paper.notes` carries
`unchanged_frame_share: 0.5` and `quota.classes: 2`, either of which would be a
calibration hint. `Paper.key()` holds `notes`; `Paper.sheet()` does not
(`model.py:144-179`). Verified: `"notes" in sheet` is `False` and
`"unchanged_frame_share"` does not occur in the sheet text. The roster is off the
sheet as well. That split is working.

---

## Method and provenance

* World: `worldgen/out/worlds/t1-push-corridor/` — `spec.json`, `raw_trace.jsonl`
  (21 lines, 19 usable transitions), `ground_truth.json`, `GROUND_TRUTH.md`.
* Paper: `heldout_worldgen.build_for("t1-push-corridor", 2)` →
  `v2-heldout-t1-push-corridor`, 8 items, `unchanged_frame_share 0.5`.
* Rubric: `exam/grading/rubrics_heldout.py`, digest
  `e06bdf52e6f5e100008960582dcd931f06d9242bb1fb02edc01b4e81d71cb091` (matches the
  profile's).
* Everything ran in-process from a scratchpad outside the repository. No file in
  the worktree was modified except this report; no `git` command was run; no
  network; no pytest suite; `arc-recon/` untouched.
