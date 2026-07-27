# METRICS — battery v0

**Generated from the code by `python -m battery.docs`. Do not edit by hand;
edit the metric and regenerate.** `tests/test_docs.py` fails if this file and
the registry disagree.

Five families and twenty-eight metrics, per `Theoria.md` Phase 2. Each carries
a declared direction — whether higher or lower is the more capable reading —
so that no ordering can be flipped after the numbers are in.

**Tier** is decided mechanically by the anti-gaming audit
(`battery/audit/gaming.py`), not by opinion:

> a metric an arm could optimise **by accident**, with **no defence implemented
> in the battery**, is demoted to `reference`.

Demotion is not deletion. Reference metrics are computed, reported and
correlated; they are excluded from ordering claims and from the main table.
`neutral`-direction metrics are diagnostics: they describe a run without
ranking it, and are never used in an ordering at all.

**Main table (15):** E1, E2, E3, K10, K11, K2, K7, M1, M3, P2, P3, P4, P5, X3, X5

**Reference (14):** E4, E5, K1, K3, K4, K5, K6, K8, K9, M2, P1, X1, X2, X4

---

## 探索 · Exploration — systematic, or circling?

| id | direction | tier | needs | definition |
|---|---|---|---|---|
| `X1` | lower | reference | steps, observations | Fraction of observed states that had been visited before. |
| `X2` | higher | reference | steps, observations | Fraction of (state, action) transitions taken for the first time. |
| `X3` | higher | main | steps, observations | Novelty in the first quarter of a run minus novelty in the last quarter; the curve's shape as one number. |
| `X4` | lower | reference | steps, observations | Longest run of consecutive steps discovering no new state, as a fraction of the run's length. |
| `X5` | neutral | main | steps, observations | Distinct states observed. Support for X1/X4, not a ranking. |

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

## 计划 · Planning — is a decision buying more actions?

| id | direction | tier | needs | definition |
|---|---|---|---|---|
| `P1` | higher | reference | steps, model_calls | Successful environment actions per model call. |
| `P2` | higher | main | steps, model_calls | Actions per model call in the run's second half minus the first half; is a decision buying more actions as the run goes on? |
| `P3` | lower | main | steps, observations | Fraction of steps that returned to the state two steps earlier — an undo. |
| `P4` | lower | main | steps, truth, optimal, solve_attempt | Actual successful steps divided by the shortest known plan. 1.0 is optimal; needs ground truth, so development pile and A0 only, and needs the run to have been trying to win. |
| `P5` | neutral | main | steps | Fraction of environment steps that failed outright. A diagnostic: it is the confound P1 and P2 are most exposed to. |

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

| id | direction | tier | needs | definition |
|---|---|---|---|---|
| `E1` | neutral | main | model_calls, cost | Total model cost. Support for the shape metrics, not a ranking. |
| `E2` | higher | main | model_calls, cost | Share of total cost spent in the first 25% of turns. High means front-loaded: the arm paid to understand, then coasted. |
| `E3` | lower | main | model_calls, cost | Fraction of the run's turns needed to reach 90% of its total cost. Low means the bill settled early. |
| `E4` | lower | reference | model_calls | R^2 of a quadratic fit to context tokens per turn minus R^2 of a linear fit. Positive means context is accelerating. |
| `E5` | lower | reference | steps, model_calls, cost | Total cost divided by successful environment actions. |

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

## 机制 · Mechanism — seen it, then used it, how long between?

| id | direction | tier | needs | definition |
|---|---|---|---|---|
| `M1` | lower | main | truth, mechanisms | Mean steps between a mechanism becoming visible and the arm first using it, over annotated mechanisms it did use. |
| `M2` | higher | reference | truth, mechanisms | Fraction of annotated mechanisms the arm ever used. |
| `M3` | lower | main | steps, truth, mechanisms | Mean first-use delay for mechanisms met again on a later level — does understanding travel? (Claim C3.) |

**How each would be gamed.**

* **`M1`** — Flail at random and hit the mechanism early by luck.
  *Accidental:* yes. *Defence:* Luck does not repeat across games, and the pairing is cross-game. Read beside M2. (implemented)
* **`M2`** — Same flailing; uptake is a hit counter and random play eventually hits everything.
  *Accidental:* yes. *Defence:* None beyond reading it with M1 -- a mechanism used late is still used. **(not implemented — demoted)**
* **`M3`** — Unimplemented.
  *Accidental:* no. *Defence:* n/a (implemented)

## 认识 · Epistemic — the quality of the books themselves

| id | direction | tier | needs | definition |
|---|---|---|---|---|
| `K1` | higher | reference | theory | Full-history exact replay accuracy: the fraction of observed state-action pairs on which the manual agrees with the world. |
| `K10` | higher | main | theory | Deadlock theorems: machine-checked proofs that a region of the search space can never reach the goal. |
| `K11` | neutral | main | theory | Manual revisions. The concept-birth timeline's coarse axis. |
| `K2` | higher | main | theory | Accuracy on state-action pairs the trace never covered. The metric replay cannot see. |
| `K3` | higher | reference | theory | Invariants and theorems in the manual. |
| `K4` | higher | reference | theory | Mean coverage over clauses the manual annotates with one; the count of unannotated clauses is reported alongside, not folded in. |
| `K5` | higher | reference | theory | Concepts admitted to the manual's word table. |
| `K6` | higher | reference | theory | Mean compression gain per admitted concept, in bits. Positive means the concept paid for itself. |
| `K7` | neutral | main | theory | Concepts admitted despite a negative compression account. A diagnostic, not a score: it counts a live conflict between two of the framework's own admission criteria. |
| `K8` | higher | reference | theory | Executable probes as a fraction of probe designs. Low means the probe machinery proposed experiments it could not run. |
| `K9` | higher | reference | theory | Entries in the playbook — ordering, pruning, heuristics, preferences. |

**How each would be gamed.**

* **`K1`** — Overfit. A model with enough parameters replays its own history perfectly and knows nothing.
  *Accidental:* yes. *Defence:* None, and none is wanted. K1 is the battery's *control*: it is the number the field already optimises, and its job here is to be high for everyone so that K2 can be the thing that separates. Reporting K1 as an achievement is the error this whole phase exists to avoid. **(not implemented — demoted)**
* **`K10`** — Emit many trivial `prune ... => dead` entries.
  *Accidental:* no. *Defence:* A deadlock theorem carries a Lean proof obligation with zero axioms; a false one does not compile. The battery counts rather than checks, so the defence is external to it -- but it is a real one, and it is why this metric stays in the main table. (implemented)
* **`K11`** — Not a ranking.
  *Accidental:* no. *Defence:* Diagnostic; a low count is ambiguous between 'right first time' and 'never checked'. (implemented)
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
* **The turn axis is model-call order**, because the ledger carries no
  turn index. `INPUT_FORMAT.md` gap 5.
