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

---

# v2 — the CC vs Schema contrast, pre-registered 2026-07-28

Appended, never edited. Everything above stands as written, including where it
was wrong.

This batch registers **no new metrics**. It registers directional predictions
for the 38 existing metrics on a gradient that has never been run: `bare_cc`
against `schema_repro`, paired by game. That is the contrast `Theoria.md`
Phase 2 process 1 names, and v0 and v1 both reported it as impossible.

## Seal declaration — and this one is materially stronger than v1's

v1's seal was weak for one avoidable reason: the recon passes that preceded it
quoted values. `REPORT_V1.md` made fixing that item 1 on the v2 list. It was
fixed, and here is the accounting.

**The procedure actually followed.** The two reconnaissance passes over
`baseline-arms/schema_traces/` and `baseline-arms/out/campaign/` were
commissioned under a written instruction to return **field names, nesting
paths, value types and closed label sets only**, with an explicit prohibition
on scores, counts, durations, token totals, sample records, ranges, and
magnitude comparisons between runs. This table was written **before either
report was read**, and before the adapter that reads the material existed.

**Seen anyway, and it must be declared.** Two leaks, both from tracked files
this author had already read for other reasons:

1. **The upstream per-game outcome scores are encoded in directory names** —
   `claude_fable_opus/` names its four run directories with a trailing score,
   and `gpt_5_6_sol/` does not. Reading a directory listing therefore disclosed
   four numbers. They are *outcome* scores, not behavioural values, and every
   metric below is behavioural; more to the point, the direction of this
   gradient was fixed by `Theoria.md` long before this session — Schema is the
   published 98.98 state of the art and `bare_cc` is a one-shot CLI baseline.
   Nothing about which arm is stronger was learned here.
2. **File counts and byte sizes per game**, from `SCHEMA_PATH_A.md` section 2.1.

**Not seen, and this is the part that matters.** Not one step, action,
observation, token count, cost, duration, retry, session length or turn count
from any trace file in `schema_traces/`. No metric value on the Schema side of
any of the 38 rows below. The author does not know, at the time of writing,
**which of these metrics the Schema material can even be computed on** — the
recon reports that would say so were not read until this section had been
written to disk in full.

That last point is the strongest form available here and it was chosen on
purpose. Writing the predictions before knowing what is computable makes it
impossible to quietly drop the rows that were going to look bad, because the
set of rows was fixed before their computability was known.

## The prediction that matters most, stated separately

**Adding the Schema arm does not rescue the epistemic family.**

`REPORT_V1.md` recorded that 21 of 38 metrics had never been computed on a
control arm — the whole epistemic family, the whole mechanism family, and P4 —
and named the missing Schema arm as the cause. **That diagnosis is predicted
here to be wrong**, and the prediction is cheap to check.

`PREDICTIONS.md` v0 assumed `schema_repro` would carry a replay-level world
model and therefore light up K1 and K2. The material that actually arrived is
**upstream trajectories, not an upstream model**. A ledger of what an agent did
contains no manual, no concepts, no clauses, no probes and no compression
account, so:

* **K1–K14 stay `not-applicable` on both control arms.** The epistemic family
  remains entirely unvalidated after this round.
* **M1–M6 stay `not-applicable` on both**, for the different reason that they
  need per-game hand-annotated mechanism ground truth, which no ARC game has.
* **P4 stays `not-applicable` on both**, needing an optimal plan length that
  only a self-built world has.

If that holds, the Schema arm closes the validation gap for exploration,
planning and economy and closes **none** of it for the two families where
Theoria's distinctive claims live. The honest headline would then be that the
battery's unvalidated fraction improves from 21/38 to roughly 20/38, not to
zero — and that no amount of further baseline material can fix the rest,
because the missing ingredient is a *theory-bearing control arm*, which does
not exist and cannot be constructed from a baseline.

## Exploration

| id | dir | prediction | reasoning |
|---|---|---|---|
| X1 | lower | **wrong-direction**: `schema > bare_cc` | the length confound v1 found on the Theoria arms, now on the control side. A run that wins revisits a hub; a run that dies on step three cannot revisit anything. X1 as defined rewards dying early |
| X2 | higher | **wrong-direction**: `bare_cc > schema` | same mechanism from the other end. A three-step run takes three first-time transitions and scores 1.000 by construction |
| X3 | higher | **agrees** | the family's signature and its one real hope. A capable agent's novelty is concentrated early and collapses once it has the level's measure. Expect many `bare_cc` runs to be `insufficient-data` — too short to have quarters — which is itself the finding |
| X4 | lower | **no-effect** | normalised by run length, so the early-exit effect it cannot remove roughly cancels the thrashing effect it can |
| X5 | neutral | not ranked | `schema` far above `bare_cc` trivially; it is the support X1 and X4 must be read beside |
| X6 | higher | **no-effect** | already falsified on `bare_cc` in v1 (1.000, measuring the prompt builder). Nothing about the Schema side is expected to rescue it |

## Planning

| id | dir | prediction | reasoning |
|---|---|---|---|
| P1 | higher | **agrees, for the wrong reason** | v1 established P1 ~ P5 at rho = -0.837: actions-per-call is mostly an API-failure readout. The Schema side ran on upstream infrastructure and should fail less, so P1 will separate — as a plumbing gradient wearing a capability gradient's clothes. **A `discriminating` verdict here should not be believed** |
| P2 | higher | **no-effect** | neither control arm plans across turns; both re-decide each step |
| P3 | lower | **wrong-direction**: `schema > bare_cc` | backtracking needs a state to return to, and the length confound again |
| P4 | lower | **no-data on both sides** | needs an optimal plan length; no ARC game has one |
| P5 | neutral | not ranked | `bare_cc` far above `schema`; this is the confound, not a result |

## Economy

Every row here is conditional on upstream logging token usage at all, which is
**not known at the time of writing**. If it does not, the economy family is
one-sided again and the whole conditional block below resolves to `no-data` —
which would be a finding, not a failure of the prediction.

| id | dir | prediction | reasoning |
|---|---|---|---|
| E1 | neutral | not ranked | total spend; a diagnostic |
| E2 | higher | **no-effect** | **the sharpest prediction in this batch.** E2 is a `Theoria.md` Phase 4 *primary endpoint* and claim C2's signature. But C2 is about a theory-bearing arm paying up front; **both control arms are transcript-memory agents**, so neither should front-load. Predicting no separation on the primary endpoint is predicting that E2 measures the thing it claims to and not general competence. **If E2 separates CC from Schema cleanly, E2 is measuring capability rather than front-loading, and its status as C2's signature is in trouble** |
| E3 | lower | **no-effect** | E2 restated from the other end; it should agree with E2 whatever E2 does |
| E4 | lower | **wrong-direction**: `bare_cc` scores better | `bare_cc` is a fresh one-shot CLI per turn, so its context is constant by construction and it scores a perfect flat curve while understanding nothing. The Schema side runs multi-turn sessions whose context genuinely grows. E4 will crown the arm with no memory at all |
| E5 | lower | **agrees** | cost per *successful* action, and `bare_cc`'s denominator is savaged by the failure rate |
| E6 | neutral | not ranked | prices the infrastructure; registered `neutral` in v1 precisely so nobody ranks an arm on it |
| E7 | lower | **wrong-direction**, same as E4 | E4's defect moved one layer out, as v1 already recorded. Predicting they fail together is predicting rho(E4,E7) stays near 1 |

## Mechanism and Epistemic

| id | prediction |
|---|---|
| M1, M2, M3, M4, M5, M6 | **`not-applicable` on both control arms** — no per-game mechanism annotation exists for any ARC game, and no repair loop can exist on an arm with no manual |
| K1 ... K14 (all 14) | **`not-applicable` on both control arms** — the Schema material is a trajectory ledger, not a published world model. See the separate section above; this is the prediction this batch is really for |

## Three named ways this batch could be wrong

1. **The Schema side may not be one arm.** `schema_traces/` holds two upstream
   collections built by different agents on different scaffolding. If they do
   not share a schema they are two arms, and pooling them into `schema_repro`
   would manufacture within-arm variance that belongs between arms. The adapter
   must check; if they differ, the pre-registered pairing is against a pooled
   construct this table did not describe, and that has to be said in the report
   rather than absorbed.
2. **Every prediction here is confounded by harness.** `bare_cc` is this
   project's CLI against the live API; the Schema side is somebody else's agent
   on somebody else's infrastructure. There is no version of this contrast that
   separates arm from plumbing, and several rows above (P1, P5, E4, E7)
   predict that the plumbing will win. A `discriminating` verdict on this
   gradient is weaker evidence than the same verdict on the model ladder, which
   at least holds the harness fixed.
3. **Four paired games still cannot reach p<0.05.** Unchanged since v0. Every
   verdict below will read `underpowered`, and the effect sizes are the only
   thing anyone should read. Six non-tied paired games remains the floor, and
   this material does not supply them — it supplies a second arm on the same
   four games, which buys pairing quality, not power.

---

# v2.1 — four defences, pre-registered 2026-07-28, before any were written

Appended, never edited.

`REPORT_V2.md` closes with a numbered list of what v3 needs. Items 1 and 2 are
four small changes inside `battery/metrics/`, each closing a hole that an
executed exploit demonstrated. **Changing a metric after seeing its numbers is
exactly the move process 1 and process 4 exist to catch**, so the predictions
go down first, in the same file and under the same rule as every other batch.

## What is being changed, and the discipline that applies

These are **defences, not redefinitions toward a hoped-for result**. Each was
named in `gaming.py`'s register as the defence *before* any number existed;
each reads a field `battery/model.py` already carries and no metric ever read.
That is a narrower thing than tuning a metric, but it is not nothing, and the
test is stated in advance: **a defence that moves a published value has changed
the measurement, not protected it.** For three of the four, the prediction is
that no published value moves at all.

## The four

| id | defence | field it reads |
|---|---|---|
| P4 | refuse to score a run that never reached the goal | `Step.won` |
| K2 | refuse to score a held-out set whose sampling frame is undeclared | `Theory.held_out_frame` |
| K12 | a closed beat requires the episode to show evidence it happened | `Repair.repair_actions` / `changed_clause` |
| E2 | interpolate the cost at the 25% mark instead of `ceil`-ing to a whole turn | — |

## Predictions

**P4 — `not-applicable` unless the run won.** P4 is currently monotone in
failure: 1.0 is not a floor and one action against a 12-step plan scores 0.083.
The battery has produced exactly one P4 value in its history — `a2-refutation`,
18 actions against an 18-step optimal plan — and **that run won**.

* Prediction: `a2-refutation` keeps **P4 = 1.000, unchanged**. No published
  number moves.
* Prediction: `exploit_P4` stops landing, and P4 returns to the main table.
* Named risk: this makes P4 unscoreable on every losing run forever, which on
  current material means P4 is a one-value metric guarded by a second guard.
  That is a real cost and it is accepted — a metric that rewards giving up is
  worse than a metric that rarely fires.

**K2 — `not-applicable` unless the frame is declared.** K2 scores 1.000 over a
held-out set of one pair, indistinguishable from an exhaustive enumeration.
`model.py` documents at length that `held_out_frame` exists to prevent exactly
this comparison, and no metric reads it.

* This requires an **adapter change as well**, and that is worth flagging
  rather than burying: `REPORT_V1.md` claimed the field "now carries a one-line
  description of the sampling frame on every theory-bearing run". **That claim
  is false.** `a0-base` carries no frame, and neither does `a2-refutation`. So
  `adapters/a0.py` must declare A0's frame — the fact is already documented
  (the 3 state-action pairs its trace never covered) — before the metric can
  require one.
* Prediction: `a0-base` keeps **K2 = 0.000** and `a0-spike` keeps **K2 =
  1.000**, both unchanged, both now carrying a frame a reader can compare. The
  DC22 shape survives intact; it would have been destroyed by the more obvious
  fix of a denominator floor, which is why a floor is not the fix.
* Prediction: `exploit_K2` stops landing, and K2 returns to the main table.

**K12 — a closed beat needs evidence the beat happened.** K12 currently reads
six self-reported booleans from a file the producer wrote.

* The defence is deliberately *not* "every beat must spend environment
  actions": `model.py` is explicit that localisation and re-proof are offline
  work and honestly cost zero. The requirement is at the **episode** level — an
  episode may not report closed beats while showing neither environment cost
  nor a changed clause.
* Prediction: `a2-probed` keeps **K12 = 1.000** (48 actions, `teleport_down`
  changed) and `a0-spike` keeps **K12 = 0.000** (four episodes, real work, no
  beat closed). No published number moves.
* Prediction: `exploit_K12` stops landing, and K12 returns to the main table.

**E2 — interpolate, and only half the hole closes.** E2's head is
`ceil(n × 0.25)`, so a perfectly flat-cost run scores 0.333 at 9 turns and
0.250 at 12, and run length is set by the crash rather than by the arm.

* Prediction: **every published E2 value moves.** This is the one defence that
  changes the measurement, and it is a correction rather than a protection: the
  current numbers contain a length artefact of the same magnitude as their
  entire spread (observed range 0.162–0.321 across every real run). Direction:
  values pull toward 0.25, and the short runs move most. `sk48` at 9 turns
  (0.311) and `tn36` at 10 (0.321) should fall furthest.
* Prediction: a synthetic flat-cost run scores **exactly 0.250 at every
  length**, which is the property the current definition lacks.
* **Prediction: E2 does NOT return to the main table.** Interpolation fixes the
  length artefact and does nothing about the concentration attack — a run that
  dumps its whole bill on turn one still scores ~0.99 over 20 turns. Predicting
  that E2 stays in `reference` after its own fix is predicting that the second
  hole is the real one, and that a Phase 4 primary endpoint is still not safe.
* Prediction: E2's process-1 verdict stays `no-data`. The Schema corpus records
  no cost, so no E2 pair can form however the head is computed.

## Aggregate predictions, so this cannot be scored loosely

1. **Main table 6 → 9.** P4, K2 and K12 return; E2 does not.
2. **Exactly one of the four published-value sets moves: E2's.** P4, K2 and K12
   keep every value they currently report.
3. **No process-1 verdict changes**, on either gradient. None of these four
   metrics has a cross-arm pair now and none gains one.
4. **The unvalidated count stays 21.** These are defences, not new material.
5. The four exploits flip `succeeded` to `False` and their tests invert — the
   exploit suite becomes the regression test for the defences.

## The way this batch could be wrong

The honest failure mode is **defence theatre**: each change makes a metric
harder to game *in the exact way that was demonstrated*, and an exploit is one
adversary's imagination rather than a proof of safety. `exploit_P4` attacked
via early exit; requiring a win closes that and says nothing about a run that
wins by a lucky path. The four demonstrations that flip to `False` below are
evidence that four specific holes closed, and are **not** evidence that these
metrics are now sound. Nothing here licenses moving any of them out of the
reference tier on any ground other than the one demonstrated.
