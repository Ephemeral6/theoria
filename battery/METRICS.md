# METRICS — battery v1

**Generated from the code by `python -m battery.docs`. Do not edit by hand;
edit the metric and regenerate.** `tests/test_docs.py` fails if this file and
the registry disagree.

Five families, per `Theoria.md` Phase 2. Each metric carries a declared
direction — whether higher or lower is the more capable reading — so that no
ordering can be flipped after the numbers are in.

**Tier** is decided mechanically by the anti-gaming audit
(`battery/audit/gaming.py`), not by opinion:

> a metric an arm could optimise **by accident**, with **no defence implemented
> in the battery**, is demoted to `reference`.

Demotion is not deletion. Reference metrics are computed, reported and
correlated; they are excluded from ordering claims and from the main table.
`neutral`-direction metrics are diagnostics: they describe a run without
ranking it, and are never used in an ordering at all.

**验证材料 / validation material** is new in v1, and it is the column to read
before believing any other. `Theoria.md` Phase 2 process 1 says validation uses
the **control arms only** — 验证只用对照两臂，与 Theoria 无关 — so a metric
computed on a Theoria arm is *computable*, not *validated*. This column reports
control-arm runs and the process-1 verdict, and is generated from the recompute
rather than asserted, so it cannot drift from what actually happened.

A metric reading `none — never computed on a control arm` has not been shown to
separate anything. `Theoria.md` is blunt about what that means:
分不开已知差异的指标，没资格测未知差异.

**Main table (19):** E1, E2, E3, E6, K10, K11, K12, K2, K7, M1, M3, M4, M6, P2, P3, P4, P5, X3, X5

**Reference (19):** E4, E5, E7, K1, K13, K14, K3, K4, K5, K6, K8, K9, M2, M5, P1, X1, X2, X4, X6

**Never validated on a control arm (21):** K1, K10, K11, K12, K13, K14, K2, K3, K4, K5, K6, K7, K8, K9, M1, M2, M3, M4, M5, M6, P4

---

## 探索 · Exploration — systematic, or circling?

| id | direction | tier | needs | 验证材料 | definition |
|---|---|---|---|---|---|
| `X1` | lower | reference | steps, observations | 81 control runs over 4 games (S1 baseline-parity, m4-pilot, phase3-variance-envelope, unlabelled, upstream-claude_fable_opus, upstream-gpt_5_6_sol); process 1: underpowered | Fraction of observed states that had been visited before. |
| `X2` | higher | reference | steps, observations | 81 control runs over 4 games (S1 baseline-parity, m4-pilot, phase3-variance-envelope, unlabelled, upstream-claude_fable_opus, upstream-gpt_5_6_sol); process 1: underpowered | Fraction of (state, action) transitions taken for the first time. |
| `X3` | higher | main | steps, observations | 73 control runs over 4 games (S1 baseline-parity, m4-pilot, phase3-variance-envelope, unlabelled, upstream-claude_fable_opus, upstream-gpt_5_6_sol); process 1: underpowered | Novelty in the first quarter of a run minus novelty in the last quarter; the curve's shape as one number. |
| `X4` | lower | reference | steps, observations | 81 control runs over 4 games (S1 baseline-parity, m4-pilot, phase3-variance-envelope, unlabelled, upstream-claude_fable_opus, upstream-gpt_5_6_sol); process 1: underpowered | Longest run of consecutive steps discovering no new state, as a fraction of the run's length. |
| `X5` | neutral | main | steps, observations | 88 control runs over 4 games (S1 baseline-parity, m4-pilot, phase3-variance-envelope, unlabelled, upstream-claude_fable_opus, upstream-gpt_5_6_sol); process 1: not-ranked | Distinct states observed. Support for X1/X4, not a ranking. |
| `X6` | higher | reference | steps, failed_steps | 71 control runs over 4 games (S1 baseline-parity, m4-pilot, phase3-variance-envelope, unlabelled); process 1: no-data | Fraction of failed steps after which the arm chose a different action. Does the arm read its own refusals? |

**How each would be gamed.**

* **`X1`** — Never revisit anything: flail through a large state space taking a fresh action every turn. A run that dies on turn three scores a perfect 0.
  *Accidental:* yes. *Defence:* Floor the run length and read it beside X5; a low revisit rate over 8 distinct states is not the same fact as a low revisit rate over 200. **(not implemented — demoted)**
* **`X2`** — Take a never-before-tried action every turn. Short runs score 1.0 automatically -- three of the pilot's runs do exactly that.
  *Accidental:* yes. *Defence:* Same floor as X1; X2 is really X3's input rather than a score of its own. **(not implemented — demoted)**
* **`X3`** — Repeat yourself deliberately in the last quarter to widen the gap.
  *Accidental:* no. *Defence:* Gaming it requires deliberately wasting late turns, which costs score on every other metric at once. (implemented)
* **`X4`** — End the run before a streak can form.
  *Accidental:* yes. *Defence:* Normalised by run length, which removes the length effect but not the early-exit effect. **(not implemented — demoted)**
* **`X5`** — Not a ranking.
  *Accidental:* no. *Defence:* Diagnostic. (implemented)
* **`X6`** — Vary the action after every failure on principle, without reading the failure. A harness that rotates its action list on retry scores 1.0 having modelled nothing at all.
  *Accidental:* yes. *Defence:* Would need the arm's action to be attributable to a decision rather than to a retry policy. The ledger collapses the harness's retry loop into one row, so a repeat across logged steps *is* an arm decision -- but nothing checks that the arm was shown the failure before choosing, and on the pilot harness it demonstrably was not. **(not implemented — demoted)**

## 计划 · Planning — is a decision buying more actions?

| id | direction | tier | needs | 验证材料 | definition |
|---|---|---|---|---|---|
| `P1` | higher | reference | steps, model_calls | 82 control runs over 4 games (S1 baseline-parity, m4-pilot, phase3-variance-envelope, unlabelled, upstream-claude_fable_opus); process 1: underpowered | Successful environment actions per model call. |
| `P2` | higher | main | steps, model_calls | 74 control runs over 4 games (S1 baseline-parity, m4-pilot, phase3-variance-envelope, unlabelled, upstream-claude_fable_opus); process 1: underpowered | Actions per model call in the run's second half minus the first half; is a decision buying more actions as the run goes on? |
| `P3` | lower | main | steps, observations | 79 control runs over 4 games (S1 baseline-parity, m4-pilot, phase3-variance-envelope, unlabelled, upstream-claude_fable_opus, upstream-gpt_5_6_sol); process 1: underpowered | Fraction of steps that returned to the state two steps earlier — an undo. |
| `P4` | lower | main | steps, truth, optimal, solve_attempt | none — never computed on a control arm | Actual successful steps divided by the shortest known plan. 1.0 is optimal; needs ground truth, so development pile and A0 only, and needs the run to have been trying to win. |
| `P5` | neutral | main | steps | 88 control runs over 4 games (S1 baseline-parity, m4-pilot, phase3-variance-envelope, unlabelled, upstream-claude_fable_opus, upstream-gpt_5_6_sol); process 1: not-ranked | Fraction of environment steps that failed outright. A diagnostic: it is the confound P1 and P2 are most exposed to. |

**How each would be gamed.**

* **`P1`** — Emit ten actions per model call. Any actions. The metric cannot tell a plan from a burst.
  *Accidental:* yes. *Defence:* Read against P4 (were those actions on the shortest path?) -- but P4 needs ground truth, so most runs have no check at all. **(not implemented — demoted)**
* **`P2`** — Batch more actions per call as the run goes on.
  *Accidental:* no. *Defence:* An *increasing* batch size is a deliberate schedule; a harness that batches does so at a constant rate, which cancels in the difference. (implemented)
* **`P3`** — Never undo -- easy in a game whose actions are irreversible, impossible in one where they are not.
  *Accidental:* yes. *Defence:* Compared only within a game, where every arm faces the same reversibility. The pairing is implemented. (implemented)
* **`P4`** — Nothing cheap: the ratio needs a real optimal plan and a real attempt to reach the goal.
  *Accidental:* no. *Defence:* Restricted to solve attempts with ground truth; coverage walks are refused outright. (implemented)
* **`P5`** — Not a ranking -- it measures the infrastructure, which is the point.
  *Accidental:* no. *Defence:* Diagnostic. Read it before believing P1 or P2. (implemented)

## 经济 · Economy — the shape of the bill

| id | direction | tier | needs | 验证材料 | definition |
|---|---|---|---|---|---|
| `E1` | neutral | main | model_calls, cost | 78 control runs over 4 games (S1 baseline-parity, m4-pilot, phase3-variance-envelope, unlabelled); process 1: not-ranked | Total model cost. Support for the shape metrics, not a ranking. |
| `E2` | higher | main | model_calls, cost | 67 control runs over 4 games (S1 baseline-parity, m4-pilot, phase3-variance-envelope, unlabelled); process 1: no-data | Share of total cost spent in the first 25% of turns. High means front-loaded: the arm paid to understand, then coasted. |
| `E3` | lower | main | model_calls, cost | 67 control runs over 4 games (S1 baseline-parity, m4-pilot, phase3-variance-envelope, unlabelled); process 1: no-data | Fraction of the run's turns needed to reach 90% of its total cost. Low means the bill settled early. |
| `E4` | lower | reference | model_calls | 74 control runs over 4 games (S1 baseline-parity, m4-pilot, phase3-variance-envelope, unlabelled, upstream-claude_fable_opus); process 1: underpowered | R^2 of a quadratic fit to context tokens per turn minus R^2 of a linear fit. Positive means context is accelerating. |
| `E5` | lower | reference | steps, model_calls, cost | 78 control runs over 4 games (S1 baseline-parity, m4-pilot, phase3-variance-envelope, unlabelled); process 1: no-data | Total cost divided by successful environment actions. |
| `E6` | neutral | main | steps, http_tries | 76 control runs over 4 games (S1 baseline-parity, m4-pilot, phase3-variance-envelope, unlabelled); process 1: not-ranked | Mean HTTP attempts the harness burned per logged environment step. A diagnostic: it prices the infrastructure the other economy metrics charge silently to the arm. |
| `E7` | lower | reference | model_calls, prompt_chars | 70 control runs over 4 games (S1 baseline-parity, m4-pilot, phase3-variance-envelope, unlabelled); process 1: no-data | R^2 of a quadratic fit to prompt size per turn minus R^2 of a linear fit. Positive means what the arm re-reads is accelerating. |

**How each would be gamed.**

* **`E1`** — Not a ranking.
  *Accidental:* no. *Defence:* Diagnostic. (implemented)
* **`E2`** — Die early -- a run that ends on turn four spent 100% of its cost in its first quarter. Or dump one enormous prompt on turn one.
  *Accidental:* yes. *Defence:* Requires at least eight turns, and pairs by game so two arms are compared over the same problem. (implemented)
* **`E3`** — As E2, from the other end.
  *Accidental:* yes. *Defence:* Same eight-turn floor and same pairing. (implemented)
* **`E4`** — Truncate or compact the context on a schedule and the quadratic term vanishes.
  *Accidental:* yes. *Defence:* None implemented. Prompt caching and context compaction do exactly this, for reasons that have nothing to do with understanding, and the battery cannot currently tell a compaction policy from a theory that closed. **(not implemented — demoted)**
* **`E5`** — Emit many cheap actions; the denominator grows faster than the numerator.
  *Accidental:* yes. *Defence:* Would need pairing against P4. Not implemented. **(not implemented — demoted)**
* **`E6`** — Not a ranking -- it measures the API and the retry policy, which is the point.
  *Accidental:* no. *Defence:* Diagnostic, and registered `neutral` so no ordering can use it. Read it before believing E1 or E5. (implemented)
* **`E7`** — Truncate or summarise the assembled prompt on a schedule and the quadratic term vanishes -- exactly E4's defect, one layer further out.
  *Accidental:* yes. *Defence:* None implemented. `prompt_chars` counts what the harness chose to assemble, so a compaction policy and a theory that closed produce the same flat curve. The improvement over E4 is only that the axis is no longer constant by construction, so the metric can now be wrong in an interesting way instead of silent. **(not implemented — demoted)**

## 机制 · Mechanism — seen it, then used it, how long between?

| id | direction | tier | needs | 验证材料 | definition |
|---|---|---|---|---|---|
| `M1` | lower | main | truth, mechanisms | none — never computed on a control arm | Mean steps between a mechanism becoming visible and the arm first using it, over annotated mechanisms it did use. |
| `M2` | higher | reference | truth, mechanisms | none — never computed on a control arm | Fraction of annotated mechanisms the arm ever used. |
| `M3` | lower | main | steps, truth, mechanisms | none — never computed on a control arm | Mean first-use delay for mechanisms met again on a later level — does understanding travel? (Claim C3.) |
| `M4` | lower | main | repairs | none — never computed on a control arm | Mean environment actions until a changed rule first contradicts the manual, over changes the manual noticed at all. |
| `M5` | higher | reference | repairs | none — never computed on a control arm | Fraction of injected rule changes the manual notices on the evidence it already holds. |
| `M6` | neutral | main | repairs | none — never computed on a control arm | Mean share of the manual's theorems invalidated by one repair. A diagnostic: a repair that invalidates nothing had nothing load-bearing downstream. |

**How each would be gamed.**

* **`M1`** — Flail at random and hit the mechanism early by luck.
  *Accidental:* yes. *Defence:* Luck does not repeat across games, and the pairing is cross-game. Read beside M2. (implemented)
* **`M2`** — Same flailing; uptake is a hit counter and random play eventually hits everything.
  *Accidental:* yes. *Defence:* None beyond reading it with M1 -- a mechanism used late is still used. **(not implemented — demoted)**
* **`M3`** — Unimplemented.
  *Accidental:* no. *Defence:* n/a (implemented)
* **`M4`** — Inject only changes that fire on the first action. The delay is a property of which rule was broken at least as much as of the manual that noticed.
  *Accidental:* no. *Defence:* The variants are authored before the metric reads them and are named in the artefact, so the choice of change is auditable rather than tunable after the fact. Gaming it requires choosing easy variants *and* publishing the list of variants chosen. (implemented)
* **`M5`** — Inject only changes you already know the evidence exercises, and the rate is 1.0 by construction.
  *Accidental:* yes. *Defence:* None implemented. Nothing in the battery checks that the injected variants were chosen independently of the evidence set, and the only producer in the repository authored both. **(not implemented — demoted)**
* **`M6`** — Not a ranking -- and both directions have a bad reading, which is why it does not rank.
  *Accidental:* no. *Defence:* Diagnostic. The unambiguous number is in the support field: how many repairs would have left a silently false theorem standing without dependency tracking. (implemented)

## 认识 · Epistemic — the quality of the books themselves

| id | direction | tier | needs | 验证材料 | definition |
|---|---|---|---|---|---|
| `K1` | higher | reference | theory | none — never computed on a control arm | Full-history exact replay accuracy: the fraction of observed state-action pairs on which the manual agrees with the world. |
| `K10` | higher | main | theory | none — never computed on a control arm | Deadlock theorems: machine-checked proofs that a region of the search space can never reach the goal. |
| `K11` | neutral | main | theory | none — never computed on a control arm | Manual revisions. The concept-birth timeline's coarse axis. |
| `K12` | higher | main | repairs | none — never computed on a control arm | Share of the six repair beats — 打脸→定位→戳探→修订→重证→解出 — that closed. |
| `K13` | lower | reference | repairs | none — never computed on a control arm | Environment actions spent repairing, over the actions the original theory cost. Low means the repair was localised. |
| `K14` | higher | reference | theory | none — never computed on a control arm | Minimum per-concept compression gain in bits. The statistic K6's mean hides. |
| `K2` | higher | main | theory | none — never computed on a control arm | Accuracy on state-action pairs the trace never covered. The metric replay cannot see. |
| `K3` | higher | reference | theory | none — never computed on a control arm | Invariants and theorems in the manual. |
| `K4` | higher | reference | theory | none — never computed on a control arm | Mean coverage over clauses the manual annotates with one; the count of unannotated clauses is reported alongside, not folded in. |
| `K5` | higher | reference | theory | none — never computed on a control arm | Concepts admitted to the manual's word table. |
| `K6` | higher | reference | theory | none — never computed on a control arm | Mean compression gain per admitted concept, in bits. Positive means the concept paid for itself. |
| `K7` | neutral | main | theory | none — never computed on a control arm | Concepts admitted despite a negative compression account. A diagnostic, not a score: it counts a live conflict between two of the framework's own admission criteria. |
| `K8` | higher | reference | theory | none — never computed on a control arm | Executable probes as a fraction of probe designs. Low means the probe machinery proposed experiments it could not run. |
| `K9` | higher | reference | theory | none — never computed on a control arm | Entries in the playbook — ordering, pruning, heuristics, preferences. |

**How each would be gamed.**

* **`K1`** — Overfit. A model with enough parameters replays its own history perfectly and knows nothing.
  *Accidental:* yes. *Defence:* None, and none is wanted. K1 is the battery's *control*: it is the number the field already optimises, and its job here is to be high for everyone so that K2 can be the thing that separates. Reporting K1 as an achievement is the error this whole phase exists to avoid. **(not implemented — demoted)**
* **`K10`** — Emit many trivial `prune ... => dead` entries.
  *Accidental:* no. *Defence:* A deadlock theorem carries a Lean proof obligation with zero axioms; a false one does not compile. The battery counts rather than checks, so the defence is external to it -- but it is a real one, and it is why this metric stays in the main table. (implemented)
* **`K11`** — Not a ranking.
  *Accidental:* no. *Defence:* Diagnostic; a low count is ambiguous between 'right first time' and 'never checked'. (implemented)
* **`K12`** — Declare fewer beats. The denominator is the arm's own claim about what a repair loop consists of.
  *Accidental:* no. *Defence:* `beats_required` is fixed at six by `Theoria.md`'s A2 acceptance, not by the arm, and the adapter sets it. An arm that closes four of six reports 0.67 and cannot redefine the six. (implemented)
* **`K13`** — Report the patch and not the re-derivation. An incremental repair that quietly re-mines the world afterwards looks five times cheaper than one that says so.
  *Accidental:* yes. *Defence:* None implemented, and the exposure is live rather than hypothetical: the two arms in hand used different repair strategies (`patch` vs `rebuild`) and the ratio cannot separate strategy from capability. `strategy` is carried into the support field so the confound is at least visible, which is not the same as defended. **(not implemented — demoted)**
* **`K14`** — Admit no small concepts. A vocabulary of one large concept has a minimum equal to its maximum.
  *Accidental:* yes. *Defence:* K5 counts the vocabulary and would show the shrinkage, but nothing pairs them automatically, and K5 is itself gameable in the opposite direction. The pair K7/K14 is the intended reading and it is a convention, not a mechanism. **(not implemented — demoted)**
* **`K2`** — Very little: the pairs are by construction the ones the trace never exercised.
  *Accidental:* no. *Defence:* Held-out by construction; the manual is frozen before the held-out pairs are scored, and A0's seal is stamped in THEORIZE_LOG.md. (implemented)
* **`K3`** — Write many trivial theorems. `0 = 0` is a theorem.
  *Accidental:* yes. *Defence:* An LLM asked for theorems will produce them in quantity. Needs a non-triviality filter that does not exist yet. **(not implemented — demoted)**
* **`K4`** — Only write down clauses you have complete evidence for. Omitting every hard rule scores 1.0.
  *Accidental:* yes. *Defence:* None implemented -- and A0 demonstrates the failure rather than merely predicting it. A0's manual scores K4 = 1.000 *because* it rejected the one generalisation it lacked evidence for (THEORIZE_LOG R-05), and that same omission is why its K2 is 0.000. Evidence coverage rewards exactly the caution that held-out accuracy punishes. K4 must never be reported without K2 beside it. **(not implemented — demoted)**
* **`K5`** — Name more things.
  *Accidental:* yes. *Defence:* K6 is meant to price each name, but see K6. **(not implemented — demoted)**
* **`K6`** — Admit one enormous concept and reject every small one. A0's mean is +706 bits, carried entirely by the Cart at +2125 while two of the three concepts are negative.
  *Accidental:* yes. *Defence:* The minimum would be the honest statistic; the mean is reported with min and max in its support fields, but the headline number is still a mean. Fix in v1. **(not implemented — demoted)**
* **`K7`** — Not a ranking -- a count of a framework conflict.
  *Accidental:* no. *Defence:* Diagnostic. (implemented)
* **`K8`** — Design only probes you already know you can run.
  *Accidental:* yes. *Defence:* None. And the denominator is tiny (9 on A0), so the ratio is noisy as well as gameable. **(not implemented — demoted)**
* **`K9`** — Write more playbook entries.
  *Accidental:* yes. *Defence:* None implemented. **(not implemented — demoted)**

---

## Deviations from `Theoria.md` Phase 2

* **X4** is normalised by run length. The runs in hand differ in
  length by a factor of twenty, and a raw streak would rank a long run
  above a short one for no reason but its length.
* **P4** additionally requires the run to have been *trying to win*.
  A0's 275-step coverage walk scores 22.9x optimal against its
  12-step plan, which measures the trace's purpose, not the arm.
* **E2 / E3** require at least eight turns. A run that ends on turn
  four spent all its money in its first quarter and looks maximally
  front-loaded while having understood nothing. This matters more
  here than elsewhere: the front-load index is a Phase 4 primary
  endpoint.
* **The turn axis is the decision, not the model call.** v0 used
  model-call order because the ledger carries no turn index. That
  counted a retried decision as several turns: one pilot run bills
  three model calls at one step, with three different prices. v1
  groups calls onto the step they were deciding for E2/E3, and leaves
  E1 on the billing axis, because the money was really spent.
  `INPUT_FORMAT.md` gap 5 is still open upstream.
* **E7 duplicates E4 on a different axis** rather than replacing it.
  E4 fits curvature to context *tokens*, which are constant by
  construction on a one-shot-CLI arm and therefore measure the
  harness. E7 fits the same curvature to prompt size, which is the
  axis that grows. Both are kept so the discrepancy stays visible.
* **K13's currency is environment actions**, because no producer in
  the repository records tokens, wall time or model calls for a
  repair. `Theoria.md` does not fix a unit for U4; this is the unit
  the artefacts can support, not the most informative one.
