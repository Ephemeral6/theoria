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

---

# v1 — nine further metrics, pre-registered 2026-07-28

Appended, never edited. The v0 table above stands exactly as it was written,
including where it was wrong.

`Theoria.md` Phase 2 process 2 again: *每个入册指标先写下三臂的方向性预测，预测先
于回算.* These nine were fixed before `run_battery` was executed over any of the
three new sources, and before a single new metric body was written.

## Seal declaration — and it is weaker than v0's, materially

v0 could say it was blind to every exploration, planning and economy value.
**v1 cannot say anything so clean, and pretending otherwise would be the exact
failure this file exists to prevent.**

Before writing this table the author commissioned three read-only surveys of
`cold-start-a2/`, `a0-spike/` and `baseline-arms/`, and read their reports.
Those reports quoted **actual values**, not only schemas. At writing time the
author already knew:

* a0-spike's held-out enumeration is **39960 cases, 0 mismatches**;
* a0-spike's four injected variants are detected at **18 / 18 / never / 6**
  actions, cost **3661 / 1478 / 1753 / 1721** evidence actions to repair
  against a 1966-action baseline, and invalidate **1 / 1 / 1 / 0** theorems;
* A2's repair loop closed **8 of 8** ledger beats and consumed **30**
  environment actions (18 refute + 12 probe) against a 183-transition play
  record;
* A2's concept accounts are **Cart +1433 → +1521, Button −5, Door −1**;
* the envelope's three cells failed **exactly 10 actions each**, spent
  **$2.5275**, and carry a constant `input_tokens: 10` and
  `cache_read_input_tokens: 24405` on every model call.

**Every v1 metric whose input appears in that list is a post-diction on the arm
it was read from, and is marked `[seen]` below.** What stays genuinely
prospective is narrower, and is stated rather than implied: the *ordering
between arms*, the behaviour of these metrics on any arm not listed above, and
every value on `bare_cc` for the three repair-shaped metrics — `bare_cc` has no
manual, so it cannot be surprised by a rule change.

**The procedural fix, recorded now so it cannot be discovered later and called
a limitation.** A recon pass that quotes values is the wrong instrument to put
in front of a pre-registration. v2 must commission surveys that return
**schemas and field names only**, with values held behind a seal opened after
the predictions are committed. That was not done here, and the discount applies
to all nine rows below.

## The arms, extended

v0 named three. The offline Theoria arms are now three distinct things, and
collapsing them would hide the only contrast the repair metrics have.

| arm | what it is | repair material |
|---|---|---|
| `bare_cc` | in weights, in the transcript | none, structurally |
| `schema_repro` | still does not exist | — |
| `theoria_a0` | `cold-start-a0`, self-built world, hand adjudication | none |
| `theoria_a0_spike` | `a0-spike`, sokoban-2 | 4 injected rule changes, re-mined from scratch |
| `theoria_a2` | `cold-start-a2`, the DC22 replay | 1 refutation, repaired incrementally |

## Exploration

| id | metric | prediction | reasoning |
|---|---|---|---|
| X6 | `post_failure_action_change` | `theoria > bare_cc`, and `bare_cc < 0.5` | after an action is refused, an arm that models the refusal tries something else; an arm that does not, re-emits it. `bare_cc` re-decides from a fresh prompt every turn and cannot remember that this action just failed, so it should repeat itself more often than chance. **A value near 1.0 on `bare_cc` would falsify the reasoning rather than flatter the arm** — it would mean the harness, not the arm, is varying the action |

## Economy

| id | metric | prediction | reasoning |
|---|---|---|---|
| E6 | `retry_amplification` | `≈ 5–10` on every ARC arm; **no ordering between arms** | **[seen]** this measures the API, not the agent. It is registered `neutral` exactly so that nobody ranks an arm on it. Its job is to stand beside P5 and E1 and price the infrastructure that the economy family otherwise charges silently to the arm |
| E7 | `prompt_growth_quadratic_gain` | `bare_cc > 0`; `theoria ≈ 0` | **the replacement for E4, and the reason E4 has been reading nothing.** `bare_cc` invokes a fresh one-shot CLI per turn, so its *token* context is constant by construction and E4 measures the harness's cache rather than the arm's memory. The history it re-reads rides in the prompt body instead. E7 fits the same curvature to `prompt_chars`, the axis that actually grows. The prediction is that the curvature E4 could not see is visible here |

## Mechanism

| id | metric | prediction | reasoning |
|---|---|---|---|
| M4 | `change_detection_delay` | `theoria ≪ bare_cc`; `theoria` under ~20 actions | **[seen for a0-spike: 18/18/6/6]** a manual is a standing prediction, so a changed rule contradicts it the first time it fires. An arm with no manual has nothing to contradict, and can only notice a change by failing to win — which is unbounded |
| M5 | `change_detection_rate` | `theoria > 0.5` but **`< 1.0`**; `bare_cc` N/A | **[seen for a0-spike: 0.75]** the interesting half of this prediction is the ceiling, not the floor. A rule can change in a way the evidence you happen to hold never exercises, which is precisely a0-spike's `nocross`. **Predicting < 1.0 is predicting that detection is a property of the evidence set rather than of the manual** — that a theory can be silently wrong while replaying perfectly |
| M6 | `repair_collateral_share` | `theoria > 0`, and **this is the point, not a defect** | **[seen for a0-spike: 3 of 4 variants invalidate 1 of 1 theorem]** registered `neutral`. A repair that invalidates nothing downstream is a theory whose theorems were not load-bearing. The number worth watching is its companion in the support field: how often a repair would leave a **silently false theorem standing** if dependencies were not tracked. On a0-spike that is 1 of 4, and a framework unable to count it would ship the false theorem |

## Epistemic

| id | metric | prediction | reasoning |
|---|---|---|---|
| K12 | `repair_loop_closure` | `theoria_a2 = 1.0`; `theoria_a0` and `bare_cc` N/A | **[seen: 8/8 beats]** structural, and registered mainly so that a *future* incomplete loop shows up as a fraction rather than as an absence. U4 is 被打脸后修得好吗; this is the yes-or-no half of it |
| K13 | `repair_cost_ratio` | `theoria_a2 < theoria_a0_spike`, and `a2 < 0.3` | **[seen for both]** **the sharpest prediction in this batch, and it is a prediction about repair *strategy*, not about arms.** A2 localises — refute, locate, probe, patch one rule — and should cost a fraction of the evidence the original theory cost. a0-spike re-mines the whole world and should cost order 1.0×. If localised repair does not come in far cheaper, the practical case for an explicit dependency-tracked manual loses its main argument |
| K14 | `min_compression_gain` | `theoria < 0` on every arm that has an account | **[seen for A0 and A2]** the honest statistic that K6's mean hides. K6 reports A0 at +706 bits, carried entirely by one concept while two of three are negative. Predicting the minimum is negative on *every* theory-bearing arm is predicting that the O-04 conflict — full-frame responsibility admitting concepts that compression would reject — is structural rather than an A0 accident. K7 counts that conflict; K14 prices it |

## Three named ways this batch could be wrong

1. **The repair metrics have one episode each and no control.** K12 and K13 rest
   on a single A2 loop and four a0-spike variants, all produced by the same
   project that defined the metrics, in worlds that project built. There is no
   arm without a manual to compare against, because an arm without a manual
   cannot have a repair loop at all. That is not a gap the battery can close —
   it is what `Theoria.md` means when it makes U4 排座次 (an ordering) and
   explicitly 不当证据 (not evidence). **No K12 or K13 number may be cited as
   evidence for claim C1.**
2. **K13 compares two repair strategies across two different worlds.** A2
   patches, a0-spike rebuilds; A2's world is 9×9 with 55 reachable states,
   a0-spike's is 7×7 with an exhaustive 39960-case enumeration. A ratio that
   comes out several-fold apart is at least as likely to be measuring "patch
   versus rebuild" as "which arm repairs better", and the two cannot be
   separated on this material. Registered anyway, with the confound named.
3. **E7 may measure the prompt builder rather than the arm.** `prompt_chars`
   counts what the harness assembled, and a harness that truncates history on a
   schedule flattens the curve for reasons having nothing to do with a theory
   closing. This is E4's defect moved one layer outward, not cured. It is
   registered because a measurable confounded axis beats an unmeasurable clean
   one, and because the confound now lives in a field a reader can check.
