# CITECHECK — 2026-08-04 delta: the zero, its three explanations, and four numbers this paper had been overstating

```audit-stamp
target: papers/phase1-workshop/PAPER.md
sha256: 8dff0bd318943f7d1b61502ea13aaec6033c258322333a014cd899e7782a25b9
lines: 4308
bytes: 277455
scope: delta audit of the 2026-08-04 edit (the abstract's new paragraph, §1.5's two closing notes, §7.10a, §11.2's ledger sentence, §11.3a's repair and closing paragraphs, new §11.3b, §11.5's closing note, §12.3); everything outside those sites is byte-unchanged from the state CITECHECK-2026-08-01.md pinned, and behind that the five-slice index in CITECHECK-2026-07-30.md remains the covering evidence
status: binding
date: 2026-08-04
```

**What this file is.** The successor `CITECHECK-2026-08-01.md`'s stamp now names.
A **delta audit, not a re-audit**, on the pattern the 07-31 and 08-01 files
established: the 2026-08-04 edit states the zero-completion fact as this paper's
central open question, carries three corrections into the body, and adds a live
result to a mechanism §11.3a had withdrawn. This file audits the paths, numbers
and quotes those edits introduced — nothing else. For the unchanged remainder the
covering audit is the chain behind it. That is a claim about byte-identity of the
untouched text, not a fresh reading of it.

**What is different about this delta.** The 08-01 delta withdrew a claim about a
mechanism. This one does three things at once, and only the first is routine:
it *carries* a live confirmation that arrived after the last audit closed, it
*corrects* four published numbers that were all wrong in the direction that
flattered the paper, and it *opens* a question rather than answering one. The
third is the load-bearing one, so the check below asks of §11.3b not "is this
number right" but "does this paragraph state the confound, or does it state a
conclusion and mention the confound".

## Every quantitative claim the delta introduced, checked against its artefact

The *how checked* column keeps the three grades the 08-01 audit defined:
**recomputed** — this run's own script recounted it from tracked files;
**read** — taken from a named artefact in another territory and not
independently recomputed; **derived** — arithmetic on a row above.

| claim (as edited) | where | artefact | how checked | verdict |
|---|---|---|---|---|
| 43 archived `bare_cc` run directories; 36 with a summary; 7 without | §7.10a, §11.3b | `baseline-arms/runs/MANIFEST.json` | **recomputed** — `runs/20260804T1500Z-P19b-.../census.py`, `baseline_archive`; AGREES | ok |
| 0 of 36 summaries carry a `score` key | §7.10a | `baseline-arms/runs/*/run.json` | **recomputed**; AGREES with `audit_zero.json` `question_1.run_dirs_persisting_a_score_field` | ok |
| 63 archived scorecard body rows, 58 distinct scorecard runs, 57 named run ids | §7.10a, §11.3b | `baseline-arms/probe_log.jsonl` + `baseline-arms/out/shards/probe_log.*.jsonl` | **recomputed** — deduplicated on `(card_id, environment, run guid)` keeping the largest action count; the 58th carries no run id, which is why 57 and 58 are both printed; AGREES | ok |
| 1,562 successful actions, 0 levels, 0.0 score | §7.10a, §11.3b, abstract, §1.5 | ibid. | **recomputed**; AGREES with A28 §4 to the action | ok |
| level-1 reference 78 / 61 / 32 / 32 for g50t / sk48 / ar25 / tn36 | §7.10a, §11.3b | scorecard `level_baseline_actions` in the same shards | **recomputed**; AGREES | ok |
| best run reached 73 / 38 / 67 / 32; 0 / 0 / 4 / 2 runs at or over the reference | §7.10a | ibid. | **recomputed**; AGREES with `audit_zero.json` `question_3_budget.per_game` | ok |
| the 67-action `ar25` run is 2.09× its reference and ends `GAME_OVER` | §7.10a | ibid. | **derived** from the row above (67/32 = 2.094); the terminal state is **recomputed** | ok |
| all six adequate-budget runs are `haiku-4.5`; no opus-5 or sonnet-5 run reached a reference | §7.10a | `baseline-arms/runs/20260802T2040Z-A28-baseline-zero-examined/RUN_STATE.md` §4 | **read**, and §7.10a says so in the sentence that cites it. The tier lives in the scorecard `tags`, which this run's census does not join; `unmeasurable_here` records that rather than reporting a zero | ok, with the grade stated |
| ledger 656 rows, 214 carrying `levels_completed`, 442 not | §7.10a, §11.2 | `baseline-arms/ledger.jsonl` | **recomputed**; the paper's previous "560 rows … 0 throughout" is corrected in both places | ok |
| 16 live Theoria legs, 15 carrying the upstream field | §11.3b, abstract | `theoria-arm/runs/*/run.json` | **recomputed**; both counts printed because they are different sets | ok |
| `levels_completed` 0 on twelve legs, **absent** on four; `summary.score` null on all sixteen; eleven scorecards at `score: 0.0` | §11.3b | ibid. | **recomputed**; the absent four are a bucket, never folded into the zero | ok |
| 22 level logs, all zero bytes | §11.3a, §11.3b | `theoria-arm/runs/*/levels.jsonl` | **recomputed** — reported as `never_written`, not as `0 rows` | ok |
| largest non-probe action count on any leg is 11; eight legs at exactly 5; longest leg 33 actions of which 28 probes | §11.3b | each leg's `probes.jsonl` against its `run.json` | **recomputed**; one leg's two instruments disagree by one probe and the census names it rather than reconciling it | ok |
| detector wired in `inner/loop.py`, never exercised on a real positive; 2,700 env-step rows, 547 carrying the counter, none `WIN` | §11.3b | `theoria-arm/runs/20260802T2100Z-A27-level-boundary-detector/MEASUREMENT.json` | **read** | ok, grade stated |
| R2b: 27 completed probes, 21 contained, 77.8 %; g50t 20 of 24 = 83.3 %; widths 6/8/9/10 | §11.3a, abstract, §12.3 | `theoria-arm/runs/20260801T044640Z-R2b-{g50t-a,sk48-b}/probes.jsonl` | **recomputed** — `survived` non-empty on a `result` row; AGREES with `R2b-VERDICT.md` | ok |
| ablation 5 of 52 = 9.6 %; replay-predicted 43 of 52 = 82.7 % | §11.3a, abstract | `theoria-arm/runs/20260801T0900Z-R2-frontier-by-generation/MANIFEST.json`, `replay` | **read** for the two counts, **derived** for the percentages | ok, grade stated |
| the R2b legs completed no level | §11.3a, §11.5 | `theoria-arm/runs/_rounds/20260801T044640Z-R2b/round.json` | **recomputed** — sum over `legs[*].levels_completed`; AGREES | ok |
| \$0.1147 per action for a bare-model run | §11.3b | `baseline-arms/runs/bare_cc-g50t-claude-opus-5-6a39afc2/run.json` | **derived** — 3.441054 / 30, both fields read from that file | ok |
| the §11.3a paragraph was committed at 04:07 UTC and R2b started at 04:46 UTC | §11.3a | `git log` on `papers/.../20260801T1200Z-P23-...` and the R2b run directory's UTC name | **recomputed** — commit `86fca692`, 2026-08-01 12:07:05 +0800; the round directory is `20260801T044640Z` | ok |

Twenty-seven quantities in the aggregate list run through `census.py --check`,
which prints AGREES/DIFFERS per row: **27 AGREES, 0 DIFFERS**, with three
quantities recorded as `unmeasurable-here`.

## Four claims this audit ruled against, and what happened to them

Each of these was in the brief this run was handed, and each is wrong in the
direction that would have made the paper's evidence look stronger.

1. **"46 baseline runs."** 46 is the manifest's count of *all* entries; three of
   them are an exclusion record, a fetch and a ledger migration and never played
   a game. 43 is the run count. The paper now names its denominators.
2. **"Highest score 0."** No `bare_cc` `run.json` has ever carried a `score`
   key; the field being read was `levels_completed`. The score is genuinely
   0.0 and it lives on the scorecard bodies, not in the run archive. Both facts
   are now stated, separately, because "score is 0" and "score was never
   recorded here" are different claims and only one of them was true of the file
   being cited.
3. **"Nothing ever exceeded 33 actions."** True of the Theoria arm and false of
   the baseline arm, whose best `g50t` observation is 73 actions — 93.6 % of the
   78 the level costs — and whose best `ar25` observation is 67 against a
   reference of 32. The corrected sentence separates the two arms.
4. **"The zero is a budget artefact."** True on `g50t` and `sk48`; **false on
   `ar25` and `tn36`**, where six runs reached or exceeded the reference cost
   and lost anyway. §7.10a now carries the four-game table rather than the
   uniform claim, which costs the paper a tidy sentence and buys it the only
   capability evidence on the pile it is entitled to cite.

## Two things this delta deliberately did not do

* **It did not touch `verify_paper.py`.** Nine new claim blocks and one elided
  path were flagged by checks E and B; every one was fixed by adding the real
  citation to the prose. No `ADJUDICATED_*` entry was added. A gate edited by
  the change that has to pass it is not a gate, and this paper has the precedent
  written down (P17: a green gate is not evidence).
* **It did not resolve the open question it opened.** §11.3b names three
  explanations, gives a decisive measurement for each, and states that the
  cheapest of the three is unpaid and unrun. The temptation was to write the
  first explanation as the answer, since it is the one with the tidiest
  arithmetic; §7.10a's own table refutes it on half the pile.

## What this audit did not do

It did not re-audit the unchanged text, did not open the figures, did not verify
anything about the exam, the transfer chapter or the adjudication census, and did
not read or write any run directory belonging to the long-leg experiment in
flight. Nothing here made an ARC call, a model call or a network request, and no
sealed-pile game id appears in any file it touched.
