<!--
The adversarial reviewer's report, verbatim. Not summarised, not trimmed, not
answered inline. The brief it was given is in ADVERSARIAL-BRIEF.md, committed
before it ran.

Two sessions tonight were right to refuse to paraphrase an adversarial report;
this follows them. The only thing removed is the harness's own trailing line
naming the subagent's internal id, which is not part of the report.

What was done about it is in RESULTS.md under "What the adversarial review
overturned", written after this file and referring to it.
-->

# ADVERSARIAL REVIEW — V11 handover, cohort 2

Run: `exam/runs/20260728T202540Z-V11-handover-auto-r2/`
Worktree: `C:\Users\user\Desktop\theoria\.worktrees\v11-handover-auto`, branch `agent/v11-handover-auto`, HEAD `bec7722`
Nothing in the worktree was modified. `git status --porcelain` was empty on entry and on exit.

## Verdicts

| Claim | Verdict |
|---|---|
| (a) the examinees really had no context | **DEAD** — three independent leaks, one of which destroys the tier contrast itself |
| (b) the marking rule was fixed before the answers existed | **STANDS** — with one stale-manifest defect and one false sub-claim inside `BLINDING.md` |
| (c) the tier difference is bigger than the instruments' noise | **DAMAGED** — the arithmetic is right and the null is honestly reported, but the run's diagnosis of *why* it is null is wrong, and it is wrong in the direction that flatters the sheet |

The single most important sentence in this report: **the sheet printed the playbook's two deadlock prunes, in English, on the tier-1 paper.** The treatment leaked into the control. This is not a saturation problem and cannot be fixed by a harder sheet.

---

## (a) "The examinees really had no context" — DEAD

### A1. The decisive leak: the sheet hands tier 1 the playbook

The paper's own design document states the discriminating construct of the entire run. `exam/papers/handover_auto.py:22-29`:

> `stile` is settled by arithmetic: the Box's column parity differs from the target's … `cairn` is not: every parity the manual states matches, and the board is dead because the Box stands where no direction admits a push, which is a fact about geometry that only the *playbook* writes down (`prune no_direction_admits_a_push(Box.pos) => dead`). If the playbook is worth anything on this sheet, `cairn` is where it shows.

The playbook (tier 2 only) carries exactly two prunes, visible at `prompts/tier2_manual_playbook.prompt.md` lines 226 and 233:

```
prune parity(Box.pos) != parity(target) => dead          [proof: lean]
prune no_direction_admits_a_push(Box.pos) => dead        [proof: none]
```

Both of them are restated verbatim, in English, as claims on the **tier-1** question sheet:

* `prompts/tier1_manual.prompt.md:1430` (item `v11-why-02`)
  > "On a board whose target cell has a different column parity from the cell the Box starts on, the game can never be won."
* `prompts/tier1_manual.prompt.md:1484` (item `v11-why-05`)
  > "If the Box stands where no direction admits a push -- for every direction either the cell the Box would cross or the cell it would land on is not free, or the cell the Player would have to stand on is off the board or a wall -- then the Box will never move again, whatever the Player does."

The second one is not an approximation of the prune. It is the prune plus the off-board case spelled out, which is the only part a reader might otherwise have missed on `cairn` (the Box sits at `(0,5)`, the top-right corner of a 6×6 board; three of the four pushes fail because the Player would have to stand off the board).

Both items are `kind = "rule_justification"`. Their prompt is *"Which of the listed clauses does this claim's truth depend on?"* — which **presupposes the claim is true**. The tier-1 reader is not asked to evaluate these criteria. It is told they hold.

I tested whether those two printed criteria alone settle the optimal-action family, using no manual, no playbook and no search:

```
item         level    why02_colparity_dead  why05_frozen_dead   predicted
v11-opt-01   stile    True                  False               none
v11-opt-02   flume    False                 False               solvable
v11-opt-03   warren   False                 False               solvable
v11-opt-04   cairn    False                 True                none
v11-opt-05   kiln     False                 False               solvable
v11-opt-06   warren   False                 False               solvable
v11-opt-07   flume    False                 False               solvable
v11-opt-08   kiln     False                 False               solvable
```

Exactly correct on all eight, dead exactly on the two dead boards, no false positives. The two criteria on the sheet are jointly a complete and sound classifier for this paper's deadness question.

**Consequence.** `PREREGISTRATION.json` line 138 registers `where_the_delta_should_land` as "optimal_action, and inside it on the two dead boards. `cairn` is the sharpest". That is the only place a delta was predicted, and the sheet gave the control arm the treatment for it. The manipulation did not happen. Tier 1 was not "manual only"; it was "manual, plus the two prunes of the playbook, asserted as true, in prose".

`RESULTS.md:94-98` reads this backwards:

> "The prediction said tier 2 should pull ahead on `cairn` and nowhere else. Tier 1 got `cairn` right unaided, so the prediction's premise — that the manual alone would struggle there — was simply false. That is a finding about the prediction, and it is recorded as a miss."

Tier 1 did not get `cairn` unaided. The premise was not false; it was falsified by the instrument. This is a finding about the sheet, recorded as a finding about the prediction. Likewise `RESULTS.md:79-81`, "the board is dead for a geometric reason the manual never writes down" — true of the manual, false of the paper the reader was actually holding.

This leak is the same shape as the one that voided cohort 1: the answer to the sharpest items, written elsewhere on the same sheet. It is invisible to every defence `BLINDING.md` lists, because all four of them (18 forbidden substrings; declared `leak_probes`; brief wording; `test_no_single_tag_token_predicts_an_answer`) operate on *metadata and prompt provenance*. Nothing in `exam/leakage.py` compares one item's **content** against another item's **answer**. `leakage.check_paper` runs `probe_hits` (verbatim probe strings), `structural_hits` (`truth` key names vs `paper` key names, `exam/leakage.py:83-87`), `metadata_hits` (`points`, `tags`, `kind` only — see `PREREGISTRATION.json:"metadata_fields_checked"`) and `positional_report`. Cross-item semantic leakage has no checker at all.

### A2. `PREREGISTRATION.json` is a 0.57 answer key, and it was on disk before the readers ran

`BLINDING.md:50` is headed **"The answer key was never on disk while the examinees ran."** The literal key was not. A serialisation of 28 of its 31 item→answer pairs was.

`run_handover_auto.build()` (`exam/tools/run_handover_auto.py:104-105`) calls

```python
leak = leakage.check_paper(paper, sheet, key_doc=key_doc,
                           answer_of=HA.answer_labels(paper, key_doc))
```

and then writes the whole `leak` dict into `PREREGISTRATION.json` in the run directory. That dict contains `positional.example_ids_by_answer`, which is a literal map from answer label to item ids. `PREREGISTRATION.json:67-70`:

```json
"none": [
  "v11-opt-01",
  "v11-opt-04"
],
```

That is the exact fact — those two boards are dead — for which the entire first cohort was voided, now living in a sibling file in the same directory, written by the same `build()` call, committed in the same commit (`2831247`) that voided cohort 1.

I marked a submission built only from that file, using the real rubric and the real key, in memory:

```
score from PREREGISTRATION.json alone: 33.000/58.000 = 0.5690
(items covered: 28 of 31)
```

`label_counts` (`PREREGISTRATION.json:88-103`) gives away the remaining two: `world_law: 6` against four listed examples forces `v11-name-09` and `v11-name-10` to `world_law`, taking it to **35/58 = 0.603**. A reader that opened one JSON file and never read the manual outscores the run's own "memoriser" calibration arm (0.553), which is presented at `RESULTS.md:58` as evidence the sheet discriminates.

**Why the defence missed it.** `BLINDING.md:59-61` cites `test_the_driver_freezes_the_key_without_writing_it` as walking the run directory and asserting no declared probe hits anything in it. `exam/tests/test_handover_auto.py:422-436` does exactly that, and only that: it concatenates every file into `blob` and checks `leakage.probe_hits(blob, item.leak_probes)`. The declared probes are built by `_probes()` (`exam/papers/handover_auto.py:428-431`) as `"v11-opt-01 => none"` and `canonical(truth)`. The pre-registration spells the same fact as `"none": ["v11-opt-01", ...]`. Measured: **61 declared probes, 0 hits in `PREREGISTRATION.json`.** The test passes over a file that scores 0.60.

This is D-EX-018 recurring one commit later: a checker that looks for a specific spelling, and a leak in a different spelling of the same fact.

### A3. The delivery mechanism described in `BLINDING.md` is not the one used

`BLINDING.md:13-22`:

> ## What the examinee receives
> One string. Nothing else.
> …
> It is **pasted into the subagent's prompt**, not pointed at. No path, no directory, no repository name, no branch, no run id, no mention of what is being measured.

The run's own answer files contradict this on all six readers. Every `meta.tools_self_report` describes reading a file:

* `answers/reader-a1.answers.json`: `"Read (only the TASK.md file named in the instructions)…"`
* `answers/reader-a3.answers.json`: `"Read - one call, on the TASK.md file named in the instructions…"`
* `answers/reader-b3.answers.json`: `"Read (only the one permitted file B3/TASK.md)…"`

and every one carries `"delivery": "one-file temp directory, prompt pasted nowhere else"`.

So the readers were **pointed at a path**, in a **per-reader directory**, and reader b3 records that directory as `B3`. Three things follow:

1. The claim "no path, no directory" is false as written.
2. A reader with a path has a working directory and therefore a place to look around from. "The file does not exist yet" (`BLINDING.md:53-56`) was the argument for why the key is safe from a subagent with a shell; that argument is weakened by handing the subagent a filesystem foothold.
3. `B3` is an arm label. `test_the_prompt_does_not_say_which_tier_the_reader_is_in_relative_terms` (`BLINDING.md:37-39`) exists precisely to stop a reader knowing it is in a lettered group being compared with another. The prompt string passes that test; the *directory name* reintroduces the signal outside the tested surface.

The general defect: **the artifact that was tested is not the artifact that was delivered.** The three pre-registered blinding tests all run against `prompts/*.prompt.md`. What each reader actually received was a wrapper message naming `TASK.md`, whose text is nowhere in the run directory and nowhere in git. There is no way to check what else that wrapper said.

### A4. Chain of custody: nothing binds an answer file to a reader

`exam/tools/run_handover_auto.py` has two subcommands, `build` and `score` (`main()`, line ~470). There is no spawn step. The docstring's "without a human in the middle" is true only of building and marking; the six examinee invocations were made by hand by the orchestrating agent — the one agent that could derive the key with a single `HA.build()` call, which `BLINDING.md:71-73` itself names as "the strongest available cheat".

The run directory contains no transcripts, no session ids, no per-reader timestamps, no raw model output — only six hand-assembled JSON files:

```
answers/reader-a1.answers.json  …  answers/reader-b3.answers.json
```

The evidence that six independent readers existed is six differently-worded English sentences in `meta.tools_self_report`. That is consistent with six agents and equally consistent with one author paraphrasing. I am not alleging fabrication — the answer content argues against it (see A5) — but the run has no artifact that would distinguish the two, and it should, because the run's whole value rests on the distinction.

Commit timestamps bound the window: `2831247` (r2 build) at 04:26:42 +0800, `5054cad` (r2 answers) at 04:32:21 +0800. Six readers, 31 items each, in 5m39s. Plausible in parallel; worth recording, since it is not recorded anywhere.

### A5. The suspicious number — the six exact plan lengths — is NOT a leak. That sub-claim stands.

`RESULTS.md:100-107` nominates this as the most suspicious number in the run, and the brief asks whether it is credible, whether a shortcut formula exists, or whether it is evidence of a leak. I attacked it three ways and it survived all three.

**It is correct.** I wrote an independent BFS transcribed by hand from `MANUAL.md`'s five rules, importing no `exam` and no `a0-spike` code, and ran it on `sheet.json`:

```
v11-opt-01  stile   len=None
v11-opt-02  flume   len=24   firsts=['DOWN','RIGHT']
v11-opt-03  warren  len=25   firsts=['LEFT','UP']
v11-opt-04  cairn   len=None
v11-opt-05  kiln    len=14   firsts=['LEFT','UP']
v11-opt-06  warren  len=16   firsts=['DOWN','RIGHT']
v11-opt-07  flume   len=22   firsts=['RIGHT']
v11-opt-08  kiln    len=21   firsts=['DOWN','LEFT']
```

This matches the key exactly and matches all six readers exactly. The key is not marking against a private simulator quirk.

**No shortcut formula exists.** Manhattan box→target distances are 5, 6, 6, 6, 4, 4, 2, 4. `v11-opt-07` has Manhattan distance **2** and a shortest plan of **22**; `v11-opt-05` has Manhattan distance **4** and a shortest plan of **14**. Any monotone function of the geometry is dead on arrival. (opt-07's box is two cells above the target but the crossing cell `(6,5)` is a wall, so the box must be routed the long way round.)

**The variation across readers is the signature of search, not of copying.** Where the true optimal set has two members, readers split across it and never outside it: `v11-opt-03` — a1 said `LEFT`, the other four said `UP`; truth `['UP','LEFT']`. `v11-opt-06` — a2 said `RIGHT`, others `DOWN`; truth `['DOWN','RIGHT']`. `v11-opt-08` — b2 said `DOWN`, others `LEFT`; truth `['DOWN','LEFT']`. Where the true set is a singleton (`v11-opt-07`, `['RIGHT']`), all six agree. A shared leak of a stored value produces correlated identical answers; independent optimal search produces exactly this pattern.

**And the search was small, for a reason that credits the manual.** The manual's two parity invariants (`box_row_parity`, `box_col_parity`) pin the Box to one parity class, i.e. a quarter of the board. I measured the true reachable state space:

```
item        level   free cells  box cells of matching parity  states reached
v11-opt-02  flume   56          15                            825
v11-opt-03  warren  58          15                            855
v11-opt-05  kiln    43           8                            294
v11-opt-07  flume   56          15                            825
v11-opt-04  cairn   29           7                             27
```

A 25-action optimal plan over an 855-state graph with 15 candidate box cells is a demanding but entirely tractable hand search. Six-for-six from six readers is credible. It is credible *because* the deliverable under test handed them the pruning law that made it tractable — which is a genuine, if accidental, point in the manual's favour and is not currently claimed anywhere.

**Prior Sokoban knowledge** is a floor under both arms, as `BLINDING.md:97-104` concedes, and cannot bias the difference. It is however worth noting that `cairn`'s deadness — a box in a board corner — is the single most elementary fact in Sokoban, so the residue is not evenly distributed: it lands hardest on precisely the item the run designated as its discriminator.

### A6. Two further tells on the sheet, one admitted, one not

**Admitted** (`RESULTS.md:115-119`): the two dead levels are exactly the two that appear **once** in the optimal-action family; the three solvable levels appear **twice** each. Deadness is readable off item counts. I confirm the counts: `stile` 1, `cairn` 1, `flume` 2, `warren` 2, `kiln` 2.

**Not admitted:** the counterexample item `v11-why-ce-01` prints its own answer. It offers five boards, each drawn with its start position, and asks for a situation where "the Box's row is always odd" fails. Three of the five printed boards have the Box drawn on an **even** row: `cairn` `(0,5)`, `stile` `(0,5)`, `warren` `(2,6)`. Four of the six readers (a1, a3, b1, b3) answered `level=cairn; player=(1,5); box=(0,5)` — which is the cairn start state, printed verbatim in the item, copied without modification.

This makes `RESULTS.md:84-91` an overclaim:

> "a legal counterexample to `invariant box_row_parity … [status: proven]` … Six readers, six valid refutations … the reader did not merely draw level with the author, it correctly refuted the author's own theorem."

Two readers (a2, b2) constructed novel positions and genuinely refuted it. Four transcribed a picture the item drew for them. This is the run's headline "what was actually learned" claim, and two-thirds of its evidence is a copy operation.

### Verdict on (a)

Dead. Independent of the voided `dead` tag, the sheet leaked the playbook's own deadlock prunes into the control arm (A1), the run directory held a 0.60-scoring answer key throughout (A2), and the delivery mechanism was not the one the blinding note describes or the one the blinding tests test (A3). The plan lengths — the thing the run itself flagged as most suspicious — are the one part of this that survives intact.

---

## (b) "The marking rule was fixed before the answers existed" — STANDS

I verified this by file history rather than by narrative, and it holds.

**Commit order.** No answer file for this run predates the rubric or the paper.

```
18a3941  04:23:00  rubrics_handover_auto.py (394 lines, new)
                   papers/handover_auto.py  (867 lines, new)
                   tools/run_handover_auto.py, tests, BLINDING, PREREGISTRATION
2831247  04:26:42  tags fix; r2 BLINDING/MANIFEST/PREREGISTRATION/prompts/sheet
8927cf7  04:30:22  cohort-1 (voided) answers + ADVERSARIAL-BRIEF
5054cad  04:32:21  the six r2 answers
bec7722  04:35:50  RESULTS.json, RESULTS.md, DECISIONS.md, run_handover_auto.py
```

**Nothing that determines a mark was touched after an answer existed.** Per-path history:

* `exam/grading/rubrics_handover_auto.py` — one commit only, `18a3941`. Never edited.
* `exam/papers/handover_auto.py` — `18a3941`, then `2831247`. The `2831247` diff is one hunk, in `_optimal_items()`, deleting `"solvable" if truth["solvable"] else "dead"` from `tags` and adding a nine-line comment. It touches no truth, no item, no board, no prediction.
* `PREREGISTRATION.json`, `sheet.json`, `prompts/` for r2 — one commit only, `2831247`, before the r2 readers ran.
* `answers/` — one commit only, `5054cad`. No amend, no rewrite.

**Verified by recomputation, not by reading.** Re-deriving from HEAD:

```
key    f21ee3d66ebc  vs pre-registered f21ee3d66ebc   OK
sheet  6444a1a0753f  vs pre-registered 6444a1a0753f   OK
rubric 63ce1eabcc32  vs pre-registered 63ce1eabcc32   OK
```

`score()` (`exam/tools/run_handover_auto.py:377-389`) genuinely refuses to mark on a mismatch, and `test_scoring_refuses_a_key_that_no_longer_matches` (`exam/tests/test_handover_auto.py:439-449`) exercises the refusal. Re-marking the six answer files in memory against the re-derived key reproduces `58.000/58.000` for all six and `delta 0.000000` — the reported numbers are what the committed code and committed answers produce.

**The admitted post-hoc edit is complete and could not have moved a number.** `bec7722` touched four paths; the only code path is `run_handover_auto.py`, one hunk, +3/−2:

```python
-    point = _frac(item_ids, "tier2") - _frac(item_ids, "tier1")
+    one, two = HA.TIER1, HA.TIER2
+    point = _frac(item_ids, two) - _frac(item_ids, one)
```

`HA.TIER1 == "tier1_manual"`, so the literals were `KeyError`s. The account in `RESULTS.md:130-139` is accurate: this is a crash fix, not a threshold move, and the function it fixes returns `[0.0, 0.0]` on this data whatever the keys are, because every score is at the ceiling.

**Two defects, neither fatal to (b):**

1. **The MANIFEST is stale.** `MANIFEST.json` declares `exam/tools/run_handover_auto.py` at `ed7badab095e…`. That was its content at `18a3941` (confirmed: `git show 18a3941:… | sha256sum` = `ed7badab095e…`). The file at HEAD is `940bbb435d56…`. Every other file in the manifest verifies. So the run's own provenance record does not cover the one file the run admits changing — the disclosure is in the prose but not in the manifest, which is the artifact `CLAUDE.md` designates canonical ("Human narrative goes in `RUN_STATE.md`, never in place of the manifest").
2. **`BLINDING.md`'s sub-claim "the answer key was never on disk while the examinees ran" is false**, per A2. The *key file* was never written; a 0.60-scoring re-encoding of it was. This is a leak finding, not a pre-registration finding, so I score it under (a) and leave (b) standing.

**Verdict on (b): stands.** The rubric, the paper, the sheet, the key digest and the written prediction were all committed before any r2 answer existed, and I can reproduce all three digests from HEAD. This part of the run was done properly and the commit trail is genuinely usable as evidence.

---

## (c) "The tier difference is bigger than the noise of the instruments" — DAMAGED

The run does not assert this claim; it reports `conclusive: false` and calls it a null. The arithmetic checks out. The damage is to the *diagnosis*.

### The arithmetic is right

Recomputed in memory from the committed answers and the re-derived key:

```
reader-a1  tier1  58.000/58.000  1.000000
reader-a2  tier1  58.000/58.000  1.000000
reader-a3  tier1  58.000/58.000  1.000000
reader-b1  tier2  58.000/58.000  1.000000
reader-b2  tier2  58.000/58.000  1.000000
reader-b3  tier2  58.000/58.000  1.000000
tier1 mean 1.000000   tier2 mean 1.000000   delta 0.000000
```

matching `RESULTS.json` exactly. `saturated: true` follows correctly from `max(1.0, 1.0) > 0.95` (`run_handover_auto.py:436`); `conclusive: false` follows correctly from `excludes_zero` being false on both bootstraps (`run_handover_auto.py:437-439`). `_pct` picks index 500 and 19499 of 20000 — a correct 2.5/97.5 percentile. `bootstrap_over_items` correctly reweights by `possible` rather than averaging per-item fractions. No error found.

### The intervals mean nothing, and the write-up half-admits it

`[0.0, 0.0]` on both bootstraps is not a narrow interval; it is the absence of an interval. With every one of 6 readers × 31 items at full marks, the resampling distribution is a point mass at 0 by construction — no resample of a constant can be anything but the constant. `RESULTS.md:44-47` says this plainly ("degenerate because there is no variance anywhere to resample … `excludes_zero` is `false` for both") and that is the honest reading. The `[0,0]` interval is **not** being used dishonestly: it is never quoted as precision, and `conclusive` is correctly false.

Two overstatements around it:

* The commit message for `bec7722` says "The instruments were measured rather than assumed." A degenerate instrument returning a point mass has not been measured; it has been shown to be uninformative on this data. "20 000 resamples, seed pinned" is stated as though it bought precision. At n=3 per arm there are 27 distinct resamples per tier and 729 in total; 20 000 draws add nothing but decimal places. Even on non-degenerate data, a percentile bootstrap from 3 observations has coverage nowhere near 95%. `BLINDING.md:120-124` concedes n=3 is "not enough to make it narrow" — the sharper statement is that at n=3 the interval's nominal level is fiction.
* `RESULTS.md:35-38` describes the grader-noise probe as rewriting answers with "case flipped, fields reordered, citations reversed, whitespace padded". Reading `_perturb` (`run_handover_auto.py:157-180`): it upper-cases **field names** (`k.strip().upper()`) and leaves **values untouched**. So `action=none; plan_len=none` becomes `PLAN_LEN = none ;  ACTION = none` — the parser's `action.lower() == NO_ACTION` and `raw_len.lower()` branches were never exercised. Minor, but it is a claim about a probe that the probe does not make.
* More substantively: with zero wrong answers in the cohort, the grader-noise probe cannot see the error mode that actually matters. It measured that the parser is deterministic on *correct* answers. Marker behaviour on partial citation sets, on illegal counterexamples, and on near-miss plan lengths — where `grade_rule_justification`'s subtraction and `grade_counterexample`'s legality check actually bite — is untested by this run's noise probe.

### The diagnosis is wrong, and wrong in the flattering direction

`RESULTS.md:8-10`:

> "The delta is 0.000, and it is 0.000 because there was nowhere left to go, not because the two tiers were measured and found equal."

There is a third possibility the run does not consider, and it is the true one: **the delta is 0.000 because the two tiers were not different.** Per A1, the sheet gave tier 1 both of the playbook's prunes. On the family where a delta was pre-registered to appear, the arms were not distinguishable.

The distinction matters for what to do next. "Saturated" is a power problem: the fix is a harder sheet, which is exactly what `RESULTS.md:141-148` prescribes ("Give the sheet a cost instrument… Run the same apparatus on a world where the manual is *known* to be incomplete"). "Contaminated control" is a validity problem: a harder sheet with `v11-why-02` and `v11-why-05` still on it would produce the same null again, on a world where the manual really is incomplete, and the run would again read it as saturation. The remedy is to move the justification family's claims off the paper that asks the optimal-action questions, or to stop stating deadness criteria as presupposed-true claims.

So: **underclaiming** on the damage (a validity failure reported as a ceiling effect), and **overclaiming** in two specific places downstream of it — `RESULTS.md:95` ("Tier 1 got `cairn` right unaided") and `RESULTS.md:84-91` (the counterexample "refutation", four of six of which were transcription, per A6).

### The "the instrument works" section is circular

`RESULTS.md:49-65` argues the sheet discriminates because oracle 1.000 / memoriser 0.553 / bluffer 0.231, and concludes "The sheet separates a reader from a memoriser by 45 points of fraction."

The memoriser is not an examinee; it is a function the paper's author wrote (`exam/papers/handover_auto.py:828-845`). It scores 0.553 because it was **defined** to answer `abstain` on all six solvable optimal-action items and on the counterexample — 19 of 58 points forfeited by construction. The 45-point gap is the author's choice of what the memoriser refuses to attempt, not a measured property of the sheet.

It is also internally inconsistent with the paper's own design. The memoriser is documented as "perfect on what the *bundle itself* states — the five rules and the parity laws — and nothing else", yet its code answers `none` correctly on **both** dead boards:

```python
out[item_id] = ("action=none; plan_len=none" if not truth["solvable"] else "abstain")
```

including `cairn`, whose deadness `handover_auto.py:26-28` says is written down *only in the playbook*. The calibration arm meant to represent bundle-only knowledge is given knowledge the module says the bundle does not contain.

For contrast, a genuinely adversarial fake — the PREREGISTRATION.json reader of A2, which sees no bundle at all — scores **0.569**, beating the memoriser. That is the discrimination number worth reporting, and it points the other way.

### Verdict on (c)

Damaged. The arithmetic is correct, the `[0,0]` intervals are handled honestly, and `conclusive: false` is the right call on the numbers. But the reason given for the null is wrong; the run diagnoses a ceiling where the real fault is a contaminated control arm, and the two "what was actually learned" claims that carry the write-up's weight (cairn unaided, six independent refutations) do not survive inspection.

---

## Anything else that would make this result not worth having

1. **The prompts are 43 KB and 51 KB of single-shot input.** `PREREGISTRATION.json:"prompts"` records 43 279 and 50 753 bytes. Every reader answered 31 items in one pass with one `Read`. There is no record of reasoning, no intermediate state, no way to distinguish a reader that searched from a reader that recalled. `RESULTS.md:120-126` correctly names the missing cost instrument as residue 3; I would rank it first rather than third, because with accuracy at the ceiling it is now the *only* channel through which the tier question could ever have been answered on this world.

2. **`BLINDING.md` residue 4 is a real and unquantified confound.** The tier-1 bundle is built live from `a0-spike/theory/theory.dsl`, which has migrated to grammar v0.2 and gained a `semantics:` section since P-15. `render_manual` predates that section and omits it from `MANUAL.md`. So `MANUAL.dsl` is strictly more informative than `MANUAL.md`, and the extra material is dense Chinese-language reasoning about frame/conflict/cascade semantics with citations to `../THEORIZE_LOG.md`, `CONTRACTS/dsl_grammar_v0.2.md`, `probes/semantics_probe.py` and `runs/20260728T040057Z-c2/RUN_STATE.md`. Four live repository paths shipped inside the tier-1 prompt, to readers who had a filesystem foothold (A3). `BLINDING.md:106-113` names this as the most likely accidental route out of the bundle and then rests the whole matter on the `TOOLS:` self-reports, which no artifact corroborates.

3. **The two runs are one sheet.** The r2 sheet is byte-identical to the voided cohort-1 sheet apart from the eight `dead`/`solvable` tag tokens (verified by diff of the two `sheet.json` files: 8 hunks, all tag lines, nothing else). That is the right call for comparability, but it means the cohort-1 answers kept "as evidence about the leak" are evidence about a sheet that differs from the scored one only in the leak — a useful property nobody exploits. Comparing cohort 1's optimal-action answers against cohort 2's would directly measure what the `dead` tag was worth. Both sets are committed; the analysis is one script away and was not done.

4. **`exam/leakage.py`'s token-vs-value defect is knowingly left live in three other papers.** `BLINDING.md:160-166` and `DECISIONS.md` D-EX-018 record that `metadata_hits` buckets on whole `tags` values and that the fix belongs in the shared checker, deferred "because changing a shared checker in the middle of a run is how the next run gets voided". Correct call for this run. It means `p15-adaptation-a0`, `p15-heldout-a0` and `p15-verdict-a2` are currently unaudited against a leak class that has demonstrably shipped once.

5. **`abstain` is unpriced** (`BLINDING.md:126-131`, `RESULTS.md:127-128`). At a ceiling with zero abstentions it changes nothing here, but it is load-bearing for the memoriser calibration in (c), which scores what it scores because of how much it abstains.

---

## What would have to be true for this run to be worth having

The pre-registration machinery is sound and I could not break it: digests reproduce, the commit order is real, the rubric never moved, and the one post-hoc edit is a genuine crash fix that could not have altered a number. That part is better than most of what it is auditing.

What it is wrapped around is a sheet that told the control arm the answer to the only question the run was designed to ask. Before this apparatus is pointed at a `worldgen` world, three things need fixing, in this order:

1. Take `v11-why-02` and `v11-why-05` off any sheet that also asks an optimal-action question, or stop phrasing deadness criteria as claims whose truth is presupposed. Add a leakage check that compares each item's rendered text against every *other* item's answer — no such check exists.
2. Stop writing `leakage.positional` into the run directory at build time, or strip `example_ids_by_answer` and `label_counts` from what `build()` persists. Write the leakage report at `score` time, where it costs nothing.
3. Make the delivered message an artifact. Whatever wrapper text names `TASK.md` should be written into the run directory and hashed, and the blinding tests should run against *that*, not against a prompt file no reader received as its whole input. As it stands, `BLINDING.md`'s central factual claim about delivery is contradicted by the run's own answer files.

The three numbers I would carry forward from this run: the plan lengths are real and independently verified (24, 25, 14, 16, 22, 21, plus two genuine deads); the pre-registration held under recomputation; and a reader with nothing but `PREREGISTRATION.json` scores 0.603 on a paper it never saw.
