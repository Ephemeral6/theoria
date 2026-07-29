# V11 — the layered handover, automated. What it measured, and what it did not.

> **READ THIS FIRST. The adversarial review overturned this document's central
> diagnosis and two of its claims.** The corrections are at the bottom under
> "What the adversarial review overturned", and the review is verbatim in
> `ADVERSARIAL-VERBATIM.md`. The original text is left standing rather than
> quietly rewritten, so that what was claimed and what survived can both be
> read. Overturned passages are marked **[OVERTURNED]**.
>
> The one-line correction: the delta is 0.000 **because the sheet handed the
> control arm the treatment**, not because the sheet saturated. The tier
> comparison is not a null result. It is not a result.

Numbers: `RESULTS.json`. Blinding and residue: `BLINDING.md`. Frozen sheet, key
digest and prediction: `PREREGISTRATION.json`.

## The headline, stated the way it should be stated

**No conclusion about the value of the playbook.** Both tiers scored 1.000.

**[OVERTURNED]** The sentence that stood here read: *"The delta is 0.000, and it
is 0.000 because there was nowhere left to go, not because the two tiers were
measured and found equal."* Both halves are wrong. The tiers were not different:
two items on the tier-1 sheet restate the playbook's two `prune` entries in
English, so the control arm held the treatment. Saturation is a power problem and
a harder sheet fixes it; this is a validity problem and a harder sheet would not.

| | tier 1 (manual) | tier 2 (manual + playbook) |
|---|---|---|
| readers | 3 | 3 |
| mean fraction | **1.000** | **1.000** |
| per-family delta | step 0.000 · names 0.000 · optimal 0.000 · why 0.000 | |

Every one of the six readers scored 58/58 — 31 items correct, none wrong, none
abstained, none unanswered.

The pre-registered saturation rule also fired, and it is now the *second* reason this number means nothing rather than the first:

> if either tier scores above 0.95 overall the sheet has saturated again and the
> delta carries no information, whatever its sign.

That rule was written into `PREREGISTRATION.json` before the first reader ran,
which is the only reason it can be quoted now without it looking like an excuse
invented afterwards. `RESULTS.json` reports `saturated: true`,
`conclusive: false`.

## The error bars, and why they are not the reason for the null

Three instruments were measured, not assumed:

* **Grader noise** — every submission marked twice, and once more after every
  answer was cosmetically rewritten (case flipped, fields reordered, citations
  reversed, whitespace padded). Maximum movement: **0.0 points** on both probes.
  The marker contributes nothing to the spread.
* **Bootstrap over readers** (20 000 resamples, seed pinned): point 0.0, 95%
  interval **[0.0, 0.0]**.
* **Bootstrap over items** (20 000 resamples): point 0.0, interval
  **[0.0, 0.0]**.

Both intervals are degenerate because there is no variance anywhere to resample:
every reader gave a correct answer to every item. An interval of [0, 0] does not
exclude zero and `excludes_zero` is `false` for both. This is the V17 trap
avoided from the other side — there is no point estimate here to over-read.

## [OVERTURNED IN PART] The instrument works. The examinees are above its ceiling.

The reviewer showed this section is circular where it matters. The memoriser is
not an examinee; it is a function this paper's author wrote, and it scores 0.553
because it was *defined* to abstain on 19 points' worth of items. The 45-point
gap is the author's choice of what the fake refuses to attempt, not a measured
property of the sheet. Worse, the memoriser answers `none` correctly on `cairn`,
whose deadness this module's own docstring says only the playbook states — the
arm meant to represent bundle-only knowledge was handed knowledge the bundle does
not contain.

The number that does measure discrimination points the other way: a fake built
from `PREREGISTRATION.json` alone, having never seen the bundle, scores 0.603.

The table below is left as it was written.

It would be wrong to conclude the sheet is undiscriminating in general. Marked
against the same rubric, in the same run:

| fake examinee | fraction |
|---|---|
| oracle (answers from the key) | 1.000 |
| null (submits nothing) | 0.000 |
| memoriser (perfect on what the bundle states, nothing else) | 0.553 |
| bluffer (one confident answer per family, cites every clause) | 0.231 |

The sheet separates a reader from a memoriser by 45 points of fraction and from a
bluffer by 77. The citation family in particular punishes shotgunning exactly as
designed: the bluffer, which names every clause on every justification item,
scores under half of that family. What the sheet cannot do is separate one good
reader from another good reader, because on this world all six were good.

## What was actually learned

The tier question got no answer. A different question got a strong one.

**A fresh instance handed nothing but `a0-spike/theory/theory.dsl` and its
mechanical English rendering reproduced this world perfectly** — with no
repository, no history, no conversation, and one tool call each. That included:

* all five rules, on transitions covering every one of them, including two
  distinct ways a push fails and two distinct ways a move is blocked;
* exact shortest-plan lengths of 14, 16, 21, 22, 24 and 25 actions on boards up
  to 8×8, all six correct, from all six readers;
* **[OVERTURNED]** both boards with no solution, including `cairn`, "dead for a
  geometric reason the manual never writes down". True of the manual; false of
  the paper the reader was holding, which stated that reason as `v11-why-05`.
  Getting `cairn` right is not evidence about the manual;
* the citation family, including the one item whose support set is all five
  rules and the one whose set is two clauses and not one;
* **[PARTLY OVERTURNED]** a legal counterexample to `invariant box_row_parity …
  mod 2 = 1 [status: proven]`. Six valid refutations, but the item prints five
  boards *with their start positions drawn* and three of those pictures show the
  Box on an even row. Four readers copied the `cairn` start state out of the
  picture; two (a2, b2) constructed positions of their own. Two independent
  refutations, not six.

In 1.11's terms 新读者打平作者 is satisfied: the reader drew level with the
author and, in two cases out of six, refuted the author's own theorem unprompted.
Whatever this manual's limits are, this sheet is not where they are. That claim
survives the review; the tier claim does not.

The plan lengths in particular survive an independent attack. The reviewer wrote
its own BFS from `MANUAL.md`'s five rules, importing nothing from this
repository, and reproduced all six lengths and both deads. It showed no monotone
function of the geometry can produce them — `v11-opt-07` has a Manhattan
box→target distance of 2 and a shortest plan of 22 — and that where the optimal
set has two members the readers split across it and never outside it, which is
the signature of independent search rather than of a shared leak. Its explanation
for why the search was tractable is a point in the manual's favour this document
did not think to claim: the manual's two parity invariants pin the Box to a
quarter of the board, cutting `warren` to 855 reachable states.

**[OVERTURNED] And the pre-registered prediction about where the delta would
land is untested.** The text that stood here read: *"Tier 1 got `cairn` right
unaided, so the prediction's premise — that the manual alone would struggle
there — was simply false."* Tier 1 did not get `cairn` unaided; it had
`v11-why-05`. The premise was not falsified by the world, it was falsified by the
instrument. This was a finding about the sheet, recorded as a finding about the
prediction — the error running in the direction that flattered the sheet.

## The most suspicious number in this run

Six readers independently returned the exact shortest-plan length on six search
problems of 14 to 25 actions. That is either genuine competence at a scale worth
noting, or a shortcut this paper did not anticipate, or a leak invisible from
here. It is the first thing the adversarial review was pointed at
(`ADVERSARIAL-BRIEF.md`, claim (a)) and its verdict is in
`ADVERSARIAL-VERBATIM.md`.

Every reader's `TOOLS:` self-report says a single `Read` of the one file it was
given. Six honest self-reports are evidence, not proof, and `BLINDING.md` §2
lists what a dishonest one could have reached.

## Residues found in this run and not repaired

1. **A structural tell in the optimal-action family.** The two dead boards are
   exactly the two levels that appear *once* in that family; the three solvable
   levels appear twice each. A reader looking for sheet structure rather than
   world structure could read deadness off item counts. The fix is a third
   occurrence of each dead level; it needs a new sheet and a new cohort.
2. **Board size correlates with the answer.** `stile` (6×7) and `cairn` (6×6)
   are the two smallest boards on the paper and the two dead ones.
3. **No cost instrument.** 1.11 predicts the manual-only reader draws level *and
   pays for it in search* — 多付的搜索成本 ≈ 玩法书缓存的计算量. `plan_len` shows
   the search was completed; it does not show what completing it cost. This is
   P-15's open weakness 2 and it is still open. It is now the *only* place a
   tier difference could show on this world, since accuracy has no room left.
4. **`abstain` is unpriced.** It scores zero like a wrong answer; nothing here
   distinguishes an honest reader from a reckless one by score.

## One change was made to code after the answers arrived

`bootstrap_over_items` crashed with `KeyError: 'tier2'` on first use — it
indexed the per-item table with the literals `"tier1"`/`"tier2"` instead of the
tier ids. It is a crash, not a threshold: the function could not produce a
number at all, so there was no number to tune. The rubric, the sheet, the key
and the prediction are untouched — `rubric_digest` is `63ce1eabcc32…` in
`PREREGISTRATION.json` and in `RESULTS.json` alike, and `score` refuses to mark
unless the re-derived key still hashes to `f21ee3d66ebc…`. The fix is in its own
commit, after the answers commit, where anyone can see it.

## What to do next, in order

1. Give the sheet a cost instrument, or stop expecting the handover item to test
   1.11's actual prediction. Accuracy on A0 is exhausted.
2. Run the same apparatus on a world where the manual is *known* to be
   incomplete — `worldgen` builds them — so that there is a gap for a playbook
   to fill. A ceiling test on a world nobody fails measures the world.
3. Fix the two structural tells above before either.


---

# What the adversarial review overturned

`ADVERSARIAL-VERBATIM.md`, stored whole and unedited. Its brief was committed
before it ran (`ADVERSARIAL-BRIEF.md`). Its verdicts:

| claim | verdict |
|---|---|
| (a) the examinees really had no context | **DEAD** |
| (b) the marking rule was fixed before the answers existed | **STANDS** |
| (c) the delta is bigger than the instruments' noise | **DAMAGED** |

## (a) — dead. Three leaks, one of them fatal.

1. **The sheet gave tier 1 the playbook's two prunes.** `v11-why-02` restates
   `prune parity(Box.pos) != parity(target) => dead`; `v11-why-05` restates
   `prune no_direction_admits_a_push(Box.pos) => dead` with the off-board case —
   the part that decides `cairn` — spelled out. Both are `rule_justification`
   items, whose prompt presupposes the claim is true, so the tier-1 reader was
   not asked to evaluate them; it was told they hold. The reviewer showed the two
   printed criteria are jointly a complete and sound classifier for all eight
   optimal-action items with no manual, no playbook and no search. That is
   exactly the family, and exactly the board, where `PREREGISTRATION.json`
   pre-registered the difference. **The manipulation did not happen.**
2. **`PREREGISTRATION.json` was a 0.603 answer key** in the examinees' own run
   directory for the whole run: `build()` persisted
   `leakage.positional.example_ids_by_answer`, which spells `"none":
   ["v11-opt-01", "v11-opt-04"]`. The probe-based test walked that directory and
   reported 61 probes, 0 hits — it was looking for a different spelling of the
   same fact. D-EX-018 recurring one commit later.
3. **The delivery mechanism was not the one `BLINDING.md` described.** Readers
   were pointed at a per-reader `TASK.md` rather than handed a pasted string; the
   directories were named by arm (`A1`…`B3`); and the wrapper message they
   actually received was tested by nothing, because it existed nowhere.

It also recorded, correctly, that nothing binds an answer file to a reader: no
transcripts, no session ids, no per-reader timestamps, only six hand-assembled
JSON files whose independence rests on six differently-worded self-reports. It
says the answer *content* argues against fabrication — the split across tied
optimal actions — and that the run should still carry the artefact that would
settle it. It should.

## (b) — stands, verified by recomputation

The reviewer re-derived all three digests from HEAD (`key f21ee3d66ebc`, `sheet
6444a1a0753f`, `rubric 63ce1eabcc32`), confirmed the rubric module was committed
once and never edited, confirmed the only edit to the paper between build and
answers was the `dead`-tag deletion, and re-marked the six answer files in memory
to reproduce 58/58 and delta 0.000000. It confirmed the admitted post-hoc
`bootstrap_over_items` edit is a crash fix that could not have moved a number.

One defect it found and this run accepts: **`MANIFEST.json` was stale**, still
recording `run_handover_auto.py` at its pre-fix hash. Refreshed.

## (c) — damaged. The arithmetic is right; the diagnosis was not.

It checked the percentile indices, the reweighting in `bootstrap_over_items`, and
the saturation and conclusiveness logic, and found no error; it agrees
`[0.0, 0.0]` is handled honestly and never quoted as precision. Three
corrections it is right about:

* "the instruments were measured rather than assumed" (commit `bec7722`)
  overstates it. A point mass is not a measurement, and 20 000 resamples of 3
  observations buy decimal places, not coverage. At n=3 the nominal 95% is
  fiction.
* The grader-noise probe upper-cases *field names* and leaves values alone, so
  the parser's `none`-token branches were never exercised. This document's
  description of it ("case flipped") was wrong.
* With zero wrong answers in the cohort the probe could only show the marker is
  deterministic on correct answers. The partial-credit path, the
  illegal-counterexample path and the near-miss plan length — where the rubric
  actually bites — were exercised by unit tests only, never by this run.

## What was changed in response, and what was not

Changed:

* `build()` no longer persists the positional leakage block, and says why.
* `cross_item_leak_report` and
  `test_no_new_sheet_claim_restates_a_playbook_entry` — the check that did not
  exist. It measures containment of the playbook entry rather than Jaccard,
  because an entry is six words and a claim is thirty and Jaccard scores a
  perfect restatement at 0.2; the first version used Jaccard and found nothing.
  It flags exactly the two known offenders, pinned so a third fails the suite.
* `prompts/DELIVERY_WRAPPER.md`: the delivered message, written down and hashed.
* `BLINDING.md`: three corrections, with the superseded wording quoted in place.
* `MANIFEST.json`: refreshed.

Not changed, deliberately:

* `v11-why-02` and `v11-why-05` stay on the sheet. Six readers answered this
  paper; editing it now would leave a run whose artefacts describe a paper that
  never existed. They must come off the *next* sheet.
* The answers, the scores and `RESULTS.json` stand as produced.
* Nothing in this document was deleted. Overturned passages are marked.

## What this run is worth, stated plainly

The tier question — 两档之差 = 战略知识的价值 — got no answer, and this is the
second consecutive attempt that got no answer. What the run leaves behind:

* **an automated apparatus** — build, freeze, deliver, mark, bootstrap — whose
  pre-registration machinery survived a determined attack;
* **two leak classes found and pinned**, one by inspection during the run and one
  by adversarial review after it, both now with tests;
* **the fourth question family of 1.11 implemented and calibrated** for the first
  time;
* **an independently verified finding about the A0 manual**: a fresh reader with
  nothing else gets 14-to-25-action optimal plans exactly right, and the reason
  it is tractable is a law the manual states.

The next run of this apparatus must not be on A0. Accuracy there is exhausted,
and the only channel left for the tier question is cost, which nothing here
measures.

---

## Annulled on the `optimal_action` family (V26, 2026-07-29)

A second leak into the same two items was found after this run was sat, by V25's
pooled private-marker cut: among the eight `optimal_action` items, `stile` and
`cairn` carried their `level:` tag exactly once and were exactly the two dead
boards, so family-scoped level-name multiplicity predicts `action=none;
plan_len=none` 8 of 8 at an exact false-positive rate of 1/28 = 0.035714 against
alpha 0.05. All six examinees answered `none` on exactly `v11-opt-01` and
`v11-opt-04` and nowhere else, which is what both search and counting predict, so
those marks carry no information about reasoning and **no number here may be cited
as evidence about the dead boards.**

**The 36 shortest-plan integers are not annulled** (six solvable items x six
readers, unanimous: 24, 25, 14, 16, 22, 21). No channel on this sheet carries
plan-length information.

This run is **not** voided, and the ruling says why -- including why the sentence
V25 filed for it ("cannot distinguish reasoning from tag-reading") is too strong,
and why the reader disagreements on `v11-opt-03`/`-06`/`-08` are evidence that the
readers *did* reason. Full ruling, with the five-channel census:
`exam/runs/20260729T2215Z-V26-handover-leak-ruling/RULING.md`.
