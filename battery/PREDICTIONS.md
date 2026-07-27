# PREDICTIONS — directional pre-registration, battery v0

`Theoria.md` Phase 2, process 2: *每个入册指标先写下三臂的方向性预测，预测先于回算.*

**This file is append-only from the commit that introduces it.** A prediction
that can be edited after the fact is not a prediction. Corrections go in a new
dated section at the bottom, with the original left standing and wrong.

Written **before** `run_battery.py` was executed for the first time. The
adapters existed and had been smoke-tested against raw inputs; no metric
function had been written or run when the table below was fixed.

---

## Seal declaration — what the author had already seen

Pre-registration is worth exactly as much as the predictor's ignorance, so the
holes are named here rather than left to be discovered.

**Not seen (genuinely blind).** Every value of every exploration, planning and
economy metric, on every run. Those come from `baseline-arms/ledger.jsonl` and
the A0 traces, neither of which had been reduced to a metric at writing time.
The correlation structure and every effect size are likewise unseen.

**Seen (not blind).** The A0 epistemic inputs. `cold-start-a0/THEORIZE_LOG.md`
and `artifacts/score_vs_truth.json` were read while building the adapter, so at
writing time the author already knew that A0's full-history replay agrees on
233 of 236 pairs, that its held-out accuracy is 0 of 3, that two admitted
concepts carry negative compression accounts, and that zero executable probes
were emitted. **K1, K2, K7 and K8 on A0 are therefore post-dictions, and are
marked `[seen]` in the table.** They are recorded anyway because the *arm
ordering* they predict is still prospective — A0 is one arm, and nothing about
`bare_cc` or `schema_repro` on those metrics was visible.

**Structurally impossible to blind.** The author built the metric definitions.
A definition can be tuned toward a hoped-for result even without seeing data,
which is what process 1 (discriminative power on control arms only) and process
4 (anti-gaming audit) exist to catch. Neither is a substitute for a second
pair of eyes and `STATUS.md` records that as an open weakness of v0.

---

## The three arms

| arm | world model | expected shape |
|---|---|---|
| `bare_cc` | in weights, in the transcript | acts, then reconsiders; the transcript is the memory |
| `schema_repro` | `world_model.py`, replay-level | a fitted simulator, no theorems |
| `theoria` | two books, four forms | pays up front to build a theory, then plans against it |

`>` means "scores higher on this metric". The prediction is the **ordering**,
not the magnitude; magnitudes are not pre-registrable from zero prior runs.

---

## Exploration

| id | metric | prediction | reasoning |
|---|---|---|---|
| X1 | `state_revisit_rate` | `bare_cc > schema > theoria` | revisiting is what you do when you cannot tell whether you have been here; a manual with object identity can tell |
| X2 | `novel_transition_rate` | `theoria > schema > bare_cc` | the theorising arm is deliberately covering the transition space early; the others sample it incidentally |
| X3 | `novelty_frontload` | `theoria > schema ≈ bare_cc` | **the signature prediction of the family.** Theoria's novelty should be concentrated in the first quartile and then collapse, because once the manual closes there is nothing left to be surprised by. A flat novelty curve means the theory never closed |
| X4 | `max_no_progress_streak` | `bare_cc > schema > theoria` | the failure mode this catches is thrashing, and thrashing is what an arm does when it has no model to consult |

## Planning

| id | metric | prediction | reasoning |
|---|---|---|---|
| P1 | `actions_per_model_call` | `theoria > schema > bare_cc` | a plan is many actions per decision; `bare_cc` re-decides every step by construction |
| P2 | `actions_per_call_trend` | `theoria > 0`, `schema ≈ 0`, `bare_cc ≈ 0` | **this is the one that tests "planning gets longer as the theory closes".** A positive trend for Theoria and flat elsewhere is the shape; a flat Theoria trend falsifies the internal story even if P1 is high |
| P3 | `backtrack_rate` | `bare_cc > schema > theoria` | returning to a state within two steps is an undo, and you undo what you did not foresee |
| P4 | `solution_redundancy` | `bare_cc > schema > theoria`, Theoria within 1.5× optimal | a planner with a correct manual walks the plan; the ratio is the cost of not having one |

## Economy

| id | metric | prediction | reasoning |
|---|---|---|---|
| E2 | `frontload_index_25` | `theoria > schema ≈ bare_cc` | **claim C2's signature, and a Phase 4 primary endpoint.** Understanding is bought early and spent late; ignorance pays by the turn forever |
| E3 | `convergence_turn_90` | `theoria < schema ≈ bare_cc` | the same fact from the other end: Theoria should reach 90% of its bill early |
| E4 | `context_growth_quadratic_gain` | `bare_cc > schema > theoria ≈ 0` | a transcript-memory arm re-reads a growing transcript every turn, which is quadratic in tokens. An arm whose memory is a manual re-reads a manual of roughly fixed size. **If Theoria's context also grows quadratically, the two books are not doing the job the design claims** |
| E5 | `cost_per_action` | `bare_cc > schema > theoria` overall; reversed over the first quartile | the crossover *is* the claim; a Theoria arm that is cheaper from turn one is winning on engineering, not on understanding, which is what the ablation arm exists to separate |

## Mechanism

| id | metric | prediction | reasoning |
|---|---|---|---|
| M1 | `mean_first_use_delay` | `bare_cc > schema > theoria` | the delay between seeing a mechanism and exploiting it is the most direct behavioural read of "understood it" |
| M2 | `mechanism_uptake` | `theoria > schema > bare_cc` | fraction of annotated mechanisms ever used at all |
| M3 | `cross_level_first_use_delay` | `theoria ≪ others`, and near zero on level 2+ | this is claim C3 (transfer). Conditional on levels sharing mechanics, which Phase 1 must confirm |

## Epistemic

Only an arm with books has most of these. `bare_cc` is structurally
`not-applicable` on all of them — predicted here as a *structural* claim, not a
score of zero. `schema_repro` has a replay-level model, so K1/K2 apply to it.

| id | metric | prediction | reasoning |
|---|---|---|---|
| K1 | `replay_accuracy` | `schema ≈ theoria`, both `> 0.95`; `bare_cc` N/A | **[seen for A0: 0.987]** replay is the metric the field already optimises, so it should *not* separate the two model-bearing arms. A metric that cannot separate them is doing its job here: it is the control |
| K2 | `held_out_accuracy` | `theoria > schema`, both `< K1` | **[seen for A0: 0.000]** the DC22 shape — a missing rule is invisible to replay and fatal off-trace. The gap `K1 − K2` is the real instrument, and A0 already shows it can be total |
| K3 | `theorem_count` | `theoria > 0`, others 0 | structural |
| K4 | `evidence_coverage` | `theoria > 0.9` | mean coverage over clauses the manual annotates |
| K5 | `vocabulary_size` | `theoria > schema` | the manual names objects; a fitted simulator need not |
| K6 | `mean_compression_gain` | `theoria > 0` | the framework's own admission criterion, applied to itself |
| K7 | `negative_gain_concepts` | `theoria > 0`, and **this is expected, not a defect** | **[seen for A0: 2 of 3]** the O-04 conflict: full-frame responsibility admits concepts that compression alone would reject. Predicting a nonzero count is predicting that the conflict is structural rather than an A0 accident |
| K8 | `probe_executable_rate` | `theoria > 0` on any world larger than A0 | **[seen for A0: 0.000]** A0 emitted zero executable probes. The prediction is that this is a property of a 59-state world, not of the probe machinery — and if it stays zero on ARC, the probe design is broken |
| K9 | `playbook_entries` | `theoria > 0`, others 0 | structural |
| K10 | `deadlock_theorems` | `theoria > 0`, others 0 | structural; the machine-checked "this cannot be won" that no baseline can produce |

---

## Two named ways this could all be wrong

Recorded now so they cannot be discovered later and called limitations.

1. **The control arms may never produce the contrast.** `schema_repro` does not
   exist and may never — `baseline-arms/SCHEMA_LOCATE.md` finds the official
   harness was never released. Every prediction above involving `schema` is
   then untestable, and the battery's discriminative validation loses the
   gradient `Theoria.md` specified for it. v0 substitutes the model ladder
   within `bare_cc`; `DECISIONS.md` D-B-004 argues why that is weaker.
2. **The economy predictions may be confounded by caching.** Prompt caching
   makes cost a function of how a harness batches, not only of how much it
   needs to read. If the three arms cache differently, E2/E3/E5 measure the
   harness. The defence is the shared-shell discipline; the check is that
   `cache_read_input_tokens` and raw `input_tokens` move together across arms,
   and it is not yet implemented.
