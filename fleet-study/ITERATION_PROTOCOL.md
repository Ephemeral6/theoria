# ITERATION_PROTOCOL — how comparable projects run their improvement loop, and what Theoria's Phase 3 loop should be

Territory: `fleet-study/`. Run: `fleet-study/runs/20260731T1723Z-ITERATION-PRACTICE/`.
Base commit `73760dc8`, branch `p12/iteration-practice`. Document only — no code changed.
Evidence recomputed by `runs/20260731T1723Z-ITERATION-PRACTICE/probe_yield.py` →
`probe_yield.json` (read-only over `theoria-arm/runs/*/surprises.jsonl`; offline; no API calls;
development-pile legs only).

Every recommendation below is anchored either in a source I read (URL given) or in a
`Theoria.md` line (number given). Where I am extrapolating rather than citing, the sentence
says so.

**Reading-depth disclosure.** Anchors differ in how much I actually read. *Full text fetched
and extracted*: Agentic Harness Engineering, Architectural Design Decisions in Agent Harnesses,
OPINE-World, the "Coding Benchmarks Are Misaligned" position paper, the MIPROv2 API reference,
GEPA (PDF; the extraction came back generic, so I only use its headline claims). *Abstract or
search-summary only*: Voyager, WorldCoder, Executable World Models for ARC-AGI-3, AlphaProof,
Scaling Test-Time Compute for Agentic Coding, the OpenHands harness docs. Claims sourced to the
second group are weaker and are flagged inline.

**Contamination hygiene.** The ARC-AGI-3 write-ups surveyed here (OPINE-World, Executable World
Models) report per-game results across the full public set. I fetched both with prompts that
explicitly forbade per-game mechanics and game identifiers, and I have written no game mechanics
into this document. Only development-pile ids (`g50t-5849a774`, `sk48-d8078629`) appear. This is
mitigation, not a guarantee: reading *about* a methodology paper that also touches sealed games is
a thinner shield than not reading it, and §5 records that honestly.

---

## 1. Field survey

Five questions asked of each system: **what unit changes per iteration**, **what is the
scoreboard**, **how do they avoid overfitting the dev set**, **how do they parallelise**, **what
failure modes do they report**.

| System | Unit changed per iteration | Scoreboard | Anti-overfit | Parallelism | Reported failure modes |
|---|---|---|---|---|---|
| **Voyager** ([arxiv 2305.16291](https://arxiv.org/abs/2305.16291), [site](https://voyager.minedojo.org/)) | one executable skill program, regenerated under environment feedback + execution errors + self-verification | tech-tree milestones, unique items, distance travelled — all *progress counters*, not a pass/fail | automatic curriculum proposes the next task from current state/inventory/failed tasks, so the target moves with capability | not reported at the level I read | catastrophic forgetting (claimed alleviated by the skill library); abstract-level read only |
| **WorldCoder** ([arxiv 2402.12275](https://arxiv.org/abs/2402.12275)) | one Python world-model program, refined against a *failed transition* | consistency with the whole replay buffer + optimism about achievable reward | the program must explain **all** past interactions, not the last one — the buffer is the guard | a bandit over candidate programs balances exploiting a promising program against exploring new ones | search-summary read only; the bandit exists precisely because single-program refinement gets stuck |
| **Executable World Models for ARC-AGI-3** ([arxiv 2605.05138](https://arxiv.org/abs/2605.05138)) | the executable Python world model; each playthrough starts from a fresh agent instance and clean workspace with no carry-over | mean per-game RHAE; games fully solved | *identical agent prompt across all games* — no per-game content, which is the same rule as `Theoria.md:353` channel 3 | per-playthrough isolation | refactoring toward simpler abstractions is used as an MDL proxy against overfitting observed patterns |
| **OPINE-World** ([arxiv 2607.01531](https://arxiv.org/pdf/2607.01531)) | a programmatic rule / symbolic constraint — revisions are *structural* (add predicates, add relational structure, refine rule conditions) | ontology-error frequency; prediction accuracy on held-out interactions; **expansion of explanatory scope** | held-out interactions; prioritising errors that resolve *multiple* failed predictions over isolated anomalies | batched/parallel candidate interactions | fails when errors stem from unmeasured latent variables; when the true ontology needs concepts the symbolic framework cannot express; and **when the exploration budget runs out before enough data accumulates to disambiguate competing model revisions** |
| **SWE-agent** ([arxiv 2405.15793](https://arxiv.org/abs/2405.15793)) | one agent-computer-interface component | resolve rate on a 300-instance subset | ACI developed for one model then shown to port to another (10.5% with a different model) — portability as the generalisation test | not reported at the level I read | the edit action with linting dominates; a 100-line viewer window and last-5-observations won — i.e. the *interface*, not the model, carried the gain |
| **Agentic Harness Engineering** ([arxiv 2604.25850](https://arxiv.org/html/2604.25850)) | one harness component-file (system prompt, tool, middleware, skill, memory, sub-agent), git-versioned; ~4 shipped edits over 10 rounds | `pass@1` = mean binary success over k rollouts/task, infra failures scored 0 | **none — no held-out split.** They evolve on the full 89-task set and only transfer to a second benchmark afterwards. The authors do not claim this is sufficient | 96 concurrent rollouts; k≥2 rollouts/task ⇒ ~178 rollouts/iteration; ~32 h wall clock | **regression blindness** (fix-precision 33.7%/recall 51.4% vs ~6.5% random, but regression-precision 11.8%/recall 11.1%); **non-additivity** — single-component ablations sum to +11.1 pp while the full stack yields +7.3 pp; **operating-point coupling** (gains non-monotone across reasoning tiers) |
| **Harness design-decision census** ([arxiv 2604.18071](https://arxiv.org/html/2604.18071v1)) | n/a (cross-sectional, 70 projects, frozen 2026-03-23) | n/a | n/a — explicitly *no seeds, no repeats*; a snapshot | n/a | names the confound directly: harness dimensions **co-occur** (execution isolation with structured governance, support 0.89/lift 3.4), so "one knob" is often not one knob |
| **Benchmarks-misaligned position paper** ([arxiv 2606.17799](https://arxiv.org/html/2606.17799v1)) | n/a | n/a | n/a | n/a | the variance result that governs everything below: harness swaps move TerminalBench success by **≥20 pp at fixed model**; across 200 000+ SWE-Bench runs "orchestration choices, container allocations, and evaluation seeds materially move the pass rate at fixed model and fixed harness"; 4–10 pt swings between standardised and custom scaffolds. Recommends submissions carry ≥1 ablation on a non-model axis against a fixed baseline |
| **OpenHands eval harness** ([repo](https://github.com/OpenHands/benchmarks), [docs](https://docs.openhands.dev/openhands/usage/developers/evaluation-harness)) | component swapped into a fixed baseline seed configuration | resolve rate in pinned Docker runtimes | reproducibility by pinning: submoduled SDK at a specific commit, official runtime containers | container-parallel | the harness itself is worth several points (77.6% vs "several points lower" under mini-SWE-Agent) — harness is a confound, not a constant |
| **DSPy MIPROv2** ([docs](https://dspy.ai/api/optimizers/MIPROv2/)) | an (instruction, demo-set) pair, chosen by Bayesian optimisation | metric on the valset | **trainset and valset have disjoint roles** — trainset only bootstraps demos and proposes instructions, valset only scores. Cheap minibatch (default 35) each trial, **full valset every 5 trials**, and the returned program is the best on the *full* valset, not the best minibatch | trials | overfitting to a minibatch is the acknowledged risk the periodic full evaluation exists to catch |
| **GEPA** ([arxiv 2507.19457](https://arxiv.org/abs/2507.19457)) | one module's prompt, mutated from a selected ancestor using **natural-language reflection on rollout traces** | per-instance score vectors, kept as a **Pareto frontier** — a candidate survives if it is best on *at least one* instance | Pareto pool prevents collapse onto a single dev-set optimum; separate feedback/validation sets | population of candidates | matched GRPO's best validation score in 300–400 rollouts vs 24 000 — i.e. *textual* feedback is worth ~35–78× the sample efficiency of a scalar reward |
| **AlphaProof / AlphaGeometry 2** ([DeepMind](https://deepmind.google/blog/ai-solves-imo-problems-at-silver-medal-level/), [Nature](https://www.nature.com/articles/s41586-025-09833-y)) | a proof attempt; **every verified proof is fed back as training signal**, including proofs of *self-generated variations* of the target problem | Lean verification — binary, non-negotiable, no reward model | the verifier cannot be gamed; the curriculum is generated, so there is no fixed dev set to overfit | search over proof steps | uneven by domain (strong algebra/geometry, weak combinatorics) — i.e. *encodability of the domain in the formal language* is the binding constraint, not search |
| **Test-time scaling for agentic coding** ([arxiv 2604.16529](https://arxiv.org/abs/2604.16529)) | n/a (inference-time, not framework-time) | pass@1 | n/a | Recursive Tournament Voting over parallel rollouts; Parallel-Distill-Refine sequentially | the framing worth stealing: long-horizon test-time scaling is "a problem of representation, selection, and reuse", not of generating more attempts — each rollout is compressed to a structured summary of *hypotheses, progress and failure modes* before comparison |

### 1.1 Seven readings that transfer

1. **The unit of change is one file-sized component, and it is version-controlled.** AHE stores
   prompt/tool/middleware/skill/memory as separate files and reverts *at file granularity*
   ([2604.25850](https://arxiv.org/html/2604.25850)). SWE-agent ablates one ACI element.
   This is the external form of `Theoria.md:336`'s 只改一件事.
2. **Bind a falsifiable prediction to every edit.** AHE's change manifest records evidence →
   root cause → fix → *predicted fixes and predicted at-risk regressions*, and scores itself
   against the next round's ground truth. They can predict fixes (33.7% precision vs 6.5% random)
   and cannot predict regressions (11.8%). Directly usable, and directly matches
   `Theoria.md:336`'s 变更日志:改了什么 / 为什么 / 预期效应.
3. **Progress counters beat pass/fail when n is small.** Voyager scores milestones and item
   counts; OPINE-World scores ontology-error frequency and explanatory scope. `Theoria.md:351`
   already commits to this (记分板 = 意外计数, "这比总分诚实"). The survey says it is also the only
   thing with statistical power at Theoria's n.
4. **Textual feedback is worth ~1–2 orders of magnitude of scalar feedback.** GEPA's 300–400
   rollouts vs GRPO's 24 000. Theoria's `surprises.jsonl` payloads are exactly that rich textual
   signal — so the theorize beat must receive the *payload*, not the tally.
5. **Do not collapse to one candidate.** GEPA keeps a Pareto pool; WorldCoder runs a bandit over
   programs. Both exist because refining a single committed artefact gets stuck.
6. **Run-to-run noise is large enough to fake a result.** ≥20 pp harness-attributable swings,
   and seeds/containers moving pass rate at fixed model *and* fixed harness
   ([2606.17799](https://arxiv.org/html/2606.17799v1)). Any single-leg decision is unsafe —
   which is `Theoria.md:336`'s 禁忌…对单局差分做决策(方差骗人) confirmed from outside.
7. **Knobs co-occur.** The 70-project census finds harness dimensions bundled at lift 1.8–3.4
   ([2604.18071](https://arxiv.org/html/2604.18071v1)), and AHE measured non-additivity directly
   (+11.1 pp of parts → +7.3 pp of whole). "Change one thing" needs an explicit check that the
   thing was actually one thing.

---

## 2. The protocol

### 2.1 The round

One round = one hypothesis, one knob, a bound prediction, a fixed number of legs, and a
keep-or-revert verdict. This is `Theoria.md:336` with the missing quantities filled in from §1.

```
R0  pick the failure class with the highest count on the scoreboard      (Theoria.md:351)
R1  write the change manifest BEFORE touching anything:
      evidence / root cause / the one knob / predicted effect on the
      primary endpoint / predicted at-risk regressions                    (AHE 2604.25850)
R2  develop on A0 / worldgen only — free, offline, unlimited legs         (Theoria.md:353 ch.3)
R3  freeze the diff; run the knob-was-one-knob check                      (§2.8)
R4  dev-pile confirmation: N legs, fixed assignment schedule              (§2.3, §2.7)
R5  score against R1's prediction; keep or revert at file granularity     (AHE)
R6  append the manifest + outcome to the change log whether it shipped or not
```

R1-before-R2 is not ceremony. AHE's fix-precision number is only meaningful because the
prediction was recorded before the round ran; a prediction written afterwards scores 100% and
measures nothing.

### 2.2 What may change

The movable set is fixed by `Theoria.md:355`: theorize prompts and dispatch policy, DSL
expressivity, probe strategy, segmentation operator space, engine roster. Immovable: the five
inner beats, the ten constraints, the three division-of-labour laws, co-derived multi-form, the
shell and the ledger.

Each round names **exactly one**. Concretely, for the current arm:

| Knob | Where it lives | Cost of a round |
|---|---|---|
| theorize prompt / dispatch policy | `theoria-arm/inner/theorize.py` + prompt files | A0-developable, then 1 dev-pile confirmation (`Theoria.md:353` forbids developing prompts against ARC) |
| probe strategy (前沿分裂准则) | `theoria-arm/inner/probe.py`, `engine-rig/engines/probe_frontier/` | A0-developable end to end; the frontier's shape is testable offline |
| DSL expressivity | `theory-compiler/`, `CONTRACTS/dsl_grammar_v0.*` | offline; must be entered in the 表达力台账 with the leg and rule that forced it (`Theoria.md:345`) |
| segmentation operator space | `mdl_segmenter` | offline, fixture-testable |
| engine roster | `engine-rig/tools/run_all` | offline |

Note the asymmetry: **five of the six knobs are fully developable offline**. Only the confirmation
leg costs money. The protocol should exploit that ruthlessly — see §2.10.

### 2.3 Legs per round

The honest constraint: the development pile is 4 games, and the current legs are 14–34 steps
long. A binary win/loss endpoint over 4 games has no power whatever; `Theoria.md:336`'s own ban on
deciding from a single leg is the same point.

**Rule: the primary endpoint is a per-event rate, not a per-leg outcome.** A single r3 leg emitted
29 surprises and 28 probes — so pooling over probes gives n ≈ 30–100 per round instead of n = 4.
This is the only way Theoria gets statistical power at its budget, and it is what `Theoria.md:351`
already selects for by making the scoreboard a set of counts.

**Legs: 2 games × 2 legs = 4 legs minimum per dev-pile confirmation.** Anchors: `Theoria.md:368`
sets n = 2 unless dev-pile variance is demonstrably small; `Theoria.md:356` sizes the control
arms' variance envelope at 2–3 legs per game; AHE uses k ≥ 2 rollouts per task
([2604.25850](https://arxiv.org/html/2604.25850)); the position paper
([2606.17799](https://arxiv.org/html/2606.17799v1)) shows seeds alone move outcomes at fixed model
and harness, so k = 1 cannot separate a treatment effect from container noise.

Two games, not one, because a knob that helps one game and hurts the other is the modal outcome
in AHE's regression data and must be visible. Two games, not four, because §2.9 needs the other
two held in reserve.

**A0/worldgen legs are unbounded** — zero API cost, so run ≥5 seeds there and only promote a
change to a dev-pile round if the A0 effect is already unambiguous. This is MIPROv2's
minibatch/full-eval split ([dspy.ai](https://dspy.ai/api/optimizers/MIPROv2/)) with A0 as the
cheap minibatch and the dev pile as the periodic full evaluation.

### 2.4 The scoreboard, plus two instruments it is missing

`Theoria.md:351` defines it: battery v0 recomputed per leg + the seven surprise counts in two
families + proof-obligation pass rate + theorize rounds per level.

The four live legs show that this scoreboard **cannot distinguish an informative refutation from
an uninformative one**, and that gap is what §3 diagnoses. Two additions, both free (computed
from `probes.jsonl`/`surprises.jsonl`, no API cost, no new beat):

- **`frontier_width`** — the number of *distinct* outcomes the probe's hypothesis set predicts for
  the chosen action. This is the ceiling on the split entropy that `Theoria.md:208` defines the
  probe's value as. Width 1 buys nothing; width 2 buys at most one bit.
- **`probe_yield`** — the fraction of probes whose observed outcome was among the candidate
  predictions. A refutation with the truth *inside* the hypothesis set narrows the frontier and is
  the loop working; a refutation with the truth *outside* it eliminates every candidate at once
  and selects nothing.

External anchor: OPINE-World's scoreboard is ontology-error frequency **plus explanatory scope** —
"ability to account for previously anomalous observations"
([2607.01531](https://arxiv.org/pdf/2607.01531)). `probe_yield` is explanatory scope measured at
the probe.

### 2.5 The keep/revert rule

Keep iff **(a)** the primary endpoint moved in the direction R1 predicted, **and** **(b)** no other
primary endpoint regressed beyond the pre-registered tolerance. Otherwise revert the files, and
record the manifest anyway.

Recording failed rounds is not bookkeeping piety: AHE's regression-precision of 11.8% is only
knowable because unshipped rounds were scored too, and it is the number that tells you how much to
trust your own predictions ([2604.25850](https://arxiv.org/html/2604.25850)).

### 2.6 Stopping rules — three of them

- **Per round.** After the 4 confirmation legs. No peeking-and-extending: `Theoria.md:371` bans
  batching results and then deciding what to run next, and the same logic applies to adding legs
  because the first two looked good.
- **Per knob (circuit breaker).** At most **3 consecutive rounds on the same knob**. Three failures
  means the failure class was misdiagnosed, not that the fix needs a fourth try — go back to the
  scoreboard and re-read the taxonomy. This number is a judgement call extrapolated from AHE's
  4-shipped-in-10 hit rate, not a cited constant; it is written down so it can be argued with.
- **Global.** Verbatim from `Theoria.md:357`: dev-pile U3 on ≥⟨k⟩ games + score within ⟨Δ⟩ + bill
  shape visible; or budget ⟨B⟩ exhausted — first to arrive wins. Nothing in this protocol may
  extend that.

### 2.7 Two accounts without confounding

The failure to avoid is **account aligned with condition**. If account A always runs the changed
config and account B the baseline, then rate limits, container allocation, model routing and
clock-time-of-day are all folded into the treatment effect — and
[2606.17799](https://arxiv.org/html/2606.17799v1) shows those move the number at fixed model and
fixed harness.

**Schedule: a 2×2 crossover, swapped every round.**

```
Round k      | game X            | game Y
-------------|-------------------|-------------------
account A    | baseline leg      | changed leg
account B    | changed leg       | baseline leg

Round k+1    -- swap A and B     (assignment alternates, condition does not)
```

Four legs, both accounts see both conditions, both games see both conditions. Then:

- **Report the account main effect as a measured nuisance term every round.** It is free — the
  crossover already estimates it.
- **Void rule: if |account main effect| ≥ |treatment effect|, the round is void**, not negative.
  Re-run or redesign; do not report it as evidence either way.
- **Never let one account run both legs of a paired comparison for the same game** — that pairs on
  the wrong axis.
- Both accounts write to the same `proxy/var/spend_gate.jsonl` pool and the same ledger format, so
  an `account` field must be present in the leg manifest. **It is not there today** — I grepped
  `theoria-arm/runs/20260731T1430Z-A3-level2-carried-r3/MANIFEST.json` and found `prompt_id`,
  `branch` and `base_commit` (the latter two `null`) but no account identifier. Until a leg
  manifest records which account ran it, the crossover of §2.7 is unauditable and the account main
  effect cannot be estimated. **Adding that field is a prerequisite of the first two-account
  round**, and it belongs to the `theoria-arm` territory, so it goes to `monitor/inbox/`.

Parallelism buys wall-clock, never sample size: 4 legs run on 2 accounts is still 4 legs.

### 2.8 Change-one-thing while running parallel legs

The two disciplines look contradictory and are not. Resolution, in three rules:

1. **Parallel legs differ in *assignment*, not in *configuration*.** Within a round, exactly two
   configurations exist: frozen baseline and baseline+one-knob. Legs are replicates and crossover
   cells, never a menu of variants.
2. **If two knobs must be explored at once, run two separate rounds from the *same frozen
   baseline*, never a stacked config.** This is GEPA's ancestor-mutation discipline
   ([2507.19457](https://arxiv.org/abs/2507.19457)): each candidate descends from a chosen ancestor
   by one mutation, and the pool keeps whichever is best on at least one instance rather than
   collapsing to a single winner. Two green single-knob rounds then require a **third,
   stacked-config confirmation round** before both ship together — because AHE measured
   single-component ablations summing to +11.1 pp while the stack delivered +7.3 pp.
3. **The knob-was-one-knob check (R3).** Before the confirmation legs, diff the change and confirm
   it touches one entry of the `Theoria.md:355` movable set. The 70-project census
   ([2604.18071](https://arxiv.org/html/2604.18071v1)) found harness dimensions co-occurring at
   lift up to 3.4, so "I only edited one file" is not the same claim as "I only changed one knob".
   A probe-strategy edit that also changes what theorize is shown has changed two.

### 2.9 The four overfitting channels, made operational

`Theoria.md:353` names them; here is what each costs per round.

| Channel | Guard already in the design | Operational form in a round |
|---|---|---|
| games selected | the pile cut, `arc-recon/data/piles.json`, digest `3feca53e…41bbc19a` | confirmation legs use **2 of 4** dev games; the schedule of which 2 is fixed in advance and rotated on a written cycle, not chosen after seeing a result |
| metrics selected | battery discriminative-power validation on the two control arms only; freeze | the primary endpoint for a round is named in R1 *before* the legs run; everything else in that round is exploratory and cannot carry the verdict — the same rule `Theoria.md:373` freezes for Phase 4 (三个主终点, rest marked exploratory) |
| games remembered by us | prompts developed only on A0/worldgen; no game-specific content; diff review each iteration | R2/R3 are this guard. Add a mechanical grep of the diff for game ids and game-specific vocabulary; a prompt round that cannot pass it does not reach R4. External corroboration: the ARC-AGI-3 executable-world-model agent uses an *identical prompt across all games* ([2605.05138](https://arxiv.org/abs/2605.05138)) |
| model priors | cannot be closed, only reduced: game ids never enter model context, anonymise throughout, discount "induction from zero" and report the caveat | unchanged; note that leg manifests currently carry the game id in the campaign string (`theoria-arm:A3-campaign-devpile:g50t-5849a774:…`) — that is the *ledger*, not the model context, and the distinction must stay auditable |

Note honestly that AHE — the closest external analogue to this whole protocol — has **no held-out
split at all** and evolves on its full 89-task set ([2604.25850](https://arxiv.org/html/2604.25850)).
Theoria's sealed pile is a stronger guard than anything in the surveyed literature. That is a real
advantage and should be stated as one in the paper.

### 2.10 Budget arithmetic

From the live legs (`RUN_STATE.json`): r3 spent **$13.44 of a $19 reservation across 8 model
calls** and 33 successful actions in 5 735 s; r2 spent **$9.56 of $16 across 5 calls**. So a
4-leg dev-pile confirmation round costs roughly **$40–55 of model spend plus ~130 actions**, before
any control-arm re-run.

Two consequences.

1. `Theoria.md:356` is load-bearing, not an optimisation: freeze the two control arms' variance
   envelope once at 2–3 legs per game, then burn only the Theoria arm, and reuse overlap with the
   replay-bucket data rather than re-running it.
2. At ~$50/round, the offline-developable knobs (§2.2) must absorb most of the iteration. A round
   that reaches R4 without an unambiguous A0 result is spending confirmation budget on
   exploration.

**I have no spend authority and this document authorises nothing.** The numbers above are planning
arithmetic read off manifests that already exist; every figure in this document was produced
offline.

---

## 3. Diagnosis: which failure class is g50t level-1 stuck in

### 3.1 What the legs actually show

`probe_yield.json`, recomputed from `surprises.jsonl`:

| Leg | steps | surprises | probe_refutation | replay_mismatch | probes | frontier width | **observed ∈ candidate set** | outcome |
|---|---|---|---|---|---|---|---|---|
| `20260731T1240Z` (r1) | 6 | 1 | 0 | 1 | 0 | — | — | `spend_gate_tripped` (UNPRICED_SPEND, $0 charged) |
| `20260731T1310Z-r2` | 14 | 12 | 8 | 4 | 8 | 2–2 | **0 / 8** | `spend_gate_tripped` ($9.56/$16) |
| `20260731T1430Z-r3` | 34 | 29 | **28** | **1** | 28 | 2–2 | **0 / 28** | `spend_gate_tripped` ($13.44/$19) |
| `20260731T1500Z-sk48-l1` | — | 20 | 11 | 9 | 11 | 2–2 | **0 / 11** | — |
| **pooled** | | **62** | **47** | **15** | **47** | **2–2** | **0 / 47** | |

Three facts, none of which the current scoreboard reports:

1. **Every probe in every leg offered exactly two distinct predicted outcomes.** The candidate sets
   are large — 9 to 24 hypotheses — but they collapse: `manual`, `inert`, and 10–23
   `without_<rule>` ablations that each reproduce either the manual's answer or the inert one. The
   split entropy of `Theoria.md:208` is therefore capped at one bit, no matter how many rules the
   manual has.
2. **In 0 of 47 probes was the observed outcome among the predictions.** The world answered with a
   third hash every single time. Realised information gain toward *selecting* a successor theory:
   zero. A refutation that kills all candidates simultaneously leaves the posterior empty.
3. **The manual's state space does not contain the world's states.** In r3, P-25 and P-26 were
   consecutive `ACTION5` probes; the arm's belief toggled between two states
   (`65612ce2…`/`70eb49bb…`, manual and inert simply swapping places) while both probes observed
   the same new hash `132f0bf4…`. P-27/P-28 repeat the pattern onto `121cbbc9…`. The manual models
   that action as a 2-cycle; the world is not in a 2-cycle.

And the cost: **28 of r3's 33 successful actions — 85% of the action budget — went into probes that
selected nothing**, and `levels_completed` is 0 in every leg.

### 3.2 The taxonomy reading, including the wrong one

`Theoria.md:340-349`, row by row:

- **概念不成形** — symptoms are vocabulary thrash, negative compression gain, render mismatch.
  `render_mismatch = 0` in all four legs. Not indicated *by its stated symptom*, though §3.1 fact 3
  is suggestive; see §5.
- **机制归纳错** — symptom is 重放失配反复出现, recurring replay mismatch. In r3 there is exactly
  **one** replay mismatch, at t=4, and 28 probe refutations. The manual replays the recorded history
  almost perfectly and is wrong about everything counterfactual. That is not recurring replay
  mismatch.
- **调度失误** — symptom is the LLM doing engine work by hand, arithmetic/enumeration errors bounced
  by certify. `proof_failure = 0`, `execution_mismatch = 0`. Not indicated.
- **表达力不够** — symptom is a true rule that cannot be written into the DSL. Live candidate, but
  **not currently measurable**: nothing in the instrumentation reports a rule that theorize wanted
  and could not express. See §3.4.
- **证明打不动 / 搜索爆炸** — `proof_failure = 0`, `search_timeout = 0`, `heuristic_miss = 0`. Not
  indicated.
- **修订抖动** — symptom is theorize rounds per level out of control. Real and visible (r3: 8
  theorize calls, $13.44, level 1 never cleared, 4 refutations left `handled_by: null` when the
  gate tripped) — but this is a *consequence*: theorize is being re-invoked because each probe
  refutes everything and hands back no discrimination.
- **戳探设计差** — "探针不判别、命中率低", fix at 前沿分裂准则 / 戳探策略. **This is the class.**

**The naive mapping is wrong and it matters.** A reader who maps `probe_refutation` → 机制归纳错
(the manual was refuted, therefore induction was wrong) sends the next round to 证据呈现方式 and
CEGIS-frontier adjudication prompts — a theorize-prompt round that cannot possibly work, because
the frontier the probe is splitting was never the CEGIS frontier. The seven surprise kinds do not
disambiguate this; `frontier_width` and `probe_yield` (§2.4) do, and they are the reason those two
instruments are proposed. **`probe_refutation` is a genuinely ambiguous counter**, and that is a
defect in `Theoria.md:340-349` worth recording: its symptom column has no row that a mass of
probe refutations lands on cleanly, because 戳探设计差's stated symptom is a *non-event* (probes
skipped for zero entropy), not a refutation.

### 3.3 Why the frontier is degenerate — the design line that was not followed

The design specifies the probe's hypothesis set twice, and both times it is the version space:

- `Theoria.md:202` — CEGIS / version space hands over **全体一致假设的前沿,不交点猜测**: the frontier
  of *all* hypotheses consistent with the ledger, not a point guess. "前沿正是戳探的原料."
- `Theoria.md:229` — probe designs the discriminating experiment on the thinnest-evidenced clause
  and the most-dividing action; **戳探与规则挖掘共享同一份前沿数据结构** — probe and rule-mining share
  *the same* frontier data structure.
- `Theoria.md:208` — probe value = the partition entropy the action's outcome induces over that
  frontier, greedily maximised.

What the arm built instead is documented in its own docstring, `theoria-arm/inner/probe.py:10-19`:

> "The frontier here is built by ablation, which is the form a frontier takes once a manual exists.
> The hypotheses are: `manual` …; `manual_without_<rule>` …; `inert` — nothing changes."

That set is the committed manual plus its own downward closure under single-clause deletion. It is
a point guess and its ablations — exactly the 点猜测 that `Theoria.md:202` rules out — and it is
closed downward, so it **cannot contain any mechanism the manual lacks**. Since every failure so
far is a missing or mis-shaped mechanism rather than a spurious one, the truth is structurally
outside the set on every probe. The measured 0/47 is not bad luck; it is what this construction
guarantees.

OPINE-World names both halves of this independently: revisions must be **structural** — adding
predicates and relational structure, not just refining conditions — and its stated failure mode is
"exploration budget is exhausted before sufficient data accumulates to disambiguate competing model
revisions" ([2607.01531](https://arxiv.org/pdf/2607.01531)). Theoria's budget is being exhausted
because there are no competing model revisions to disambiguate: there is one revision and its
shadows.

### 3.4 The single highest-leverage framework change for the next round

**Knob: probe strategy (前沿分裂准则). Change: build the probe's frontier by *generation*, not by
*ablation*.**

The probe beat asks for K ≥ 3 mutually incompatible *successor* hypotheses — candidate mechanisms
the manual does **not** currently contain, generated from the thinnest-evidenced region and from
the states the manual failed to predict — and scores actions by partition entropy over
{manual} ∪ {inert} ∪ {K successors}. One knob, one entry of `Theoria.md:355`, one file
(`theoria-arm/inner/probe.py::_hypotheses` plus its `probe_frontier` call); the five beats,
the ten constraints and the ledger are untouched.

Why this one, over the alternatives:

- It is the *only* change that raises `frontier_width` above 2. Every other knob operates
  downstream of a hypothesis set that currently cannot represent the answer.
- It restores the design as written (`Theoria.md:202`/`208`/`229`) rather than extending it —
  the cheapest possible justification.
- It converts 85% of the action budget from waste into evidence at **zero additional action cost**:
  same number of probes, same actions, a hypothesis set that can actually be split.
- Corroborated three ways: WorldCoder's bandit over *candidate programs*
  ([2402.12275](https://arxiv.org/abs/2402.12275)); GEPA's refusal to collapse a candidate pool to
  one ([2507.19457](https://arxiv.org/abs/2507.19457)); OPINE-World's structural, ontology-expanding
  revisions ([2607.01531](https://arxiv.org/pdf/2607.01531)).
- One honest wrinkle: `Theoria.md:208` explicitly rejects bandits (拒 bandit(无随机性,错的框架)).
  That rejection is about the *environment* being deterministic, so the split is exactly
  computable rather than estimated. WorldCoder's bandit is over which *program* to refine, where
  the uncertainty is in synthesis, not in the world. Keeping K theories alive therefore does not
  contradict line 208 — but the selection among them must remain exact entropy over the frontier,
  never a stochastic bandit, or it does.

**Bound prediction, per §2.1/R1** (written before the round runs, scored after):

| Endpoint | now | predicted after |
|---|---|---|
| `frontier_width` (median over probes) | 2 | **≥ 3** |
| `probe_yield` (observed ∈ candidates) | 0 / 47 | **≥ 0.30** |
| actions spent on probes | 28 / 33 in r3 | unchanged (this is not an efficiency change) |
| at-risk regression | — | theorize cost per probe rises (K hypotheses to generate); `Theoria.md:344` 调度失误 counters may rise if the model hand-computes the successors |

**Reclassification rule — the part that makes this diagnostic rather than a guess.** Score after
the 4 confirmation legs of §2.3:

- width ≥ 3 **and** yield ≥ 0.30 → 戳探设计差 confirmed and repaired; next round moves to the next
  class on the scoreboard.
- width ≥ 3 **but** yield still ≈ 0 → the hypothesis set now varies and still cannot reach the
  truth. Reclassify to **表达力不够** (`Theoria.md:345`) or **概念不成形** (`:342`); next knob is DSL
  expressivity or the segmentation operator space, and the forcing rule goes in the 表达力台账.
  This is OPINE-World's "the true ontology requires concepts not naturally expressible in the
  symbolic framework" and AlphaProof's domain-encodability ceiling, arriving as a measurement
  instead of an opinion.
- width still 2 → the generator did not generate; the defect is implementation, not criterion, and
  the round does not count against the knob's 3-round circuit breaker.

Note the second branch is a live possibility, not a formality: §3.1 fact 3 (a believed 2-cycle
against a world that is not in one) is what a state space too coarse to represent the world looks
like. The round is designed so that a null result *names the next class* instead of costing a round.

---

## 4. Residual gaps — stated honestly

1. **No leg has ever completed a level.** All four ended `spend_gate_tripped` at 6–34 steps, and
   `levels_completed = 0` throughout. Every endpoint in §2 is therefore a rate over within-leg
   events; 每关 theorize 轮数 (`Theoria.md:351`), transfer (C3) and the U-ladder (C1) are **not
   measurable at this leg length**, and no amount of protocol fixes that. Raising the per-leg
   reservation is a separate decision with spend implications that I have no authority over and
   have not taken.
2. **I did not run anything.** Every number here is recomputed from artefacts that already existed
   on disk. The protocol in §2 is untested; its first real test is the round in §3.4.
3. **The 3-round circuit breaker (§2.6) is extrapolated, not cited.** Nothing in the surveyed
   literature fixes that constant; it is written down so it can be argued with rather than drifting.
4. **`Theoria.md:340-349` has a hole.** No row's symptom column cleanly receives a mass of
   `probe_refutation`. §2.4's two instruments patch it from outside; the taxonomy itself should
   probably grow a row, and that is a change to `Theoria.md` — which is not my territory, so it goes
   to `monitor/inbox/`, not into the baseline.
5. **Reading depth is uneven** (see the disclosure at the head). Voyager, WorldCoder, AlphaProof and
   the ARC-AGI-3 executable-world-model paper were read at abstract/summary depth only; their rows
   in §1 are correspondingly thinner and I have not leaned a recommendation on any detail I could
   not verify.
6. **Contamination is mitigated, not eliminated.** §0's note stands: two surveyed papers report over
   the full public ARC-AGI-3 set. I constrained the fetches to methodology and wrote no mechanics
   down, but a stricter reading of `CLAUDE.md`'s sealed-pile rule would have skipped them entirely.
   Flagging rather than burying it.
7. **The account-crossover schedule (§2.7) has an unmet prerequisite.** Leg manifests carry no
   account identifier — checked against r3's `MANIFEST.json`, which has `prompt_id` but `branch`
   and `base_commit` both `null` and no account field. §2.7 cannot be audited until
   `theoria-arm` adds one. That is another territory's file, so it is a `monitor/inbox/` ask, not
   an edit.

---

## Sources

- Voyager — https://arxiv.org/abs/2305.16291 · https://voyager.minedojo.org/
- WorldCoder — https://arxiv.org/abs/2402.12275
- Executable World Models for ARC-AGI-3 — https://arxiv.org/abs/2605.05138
- OPINE-World — https://arxiv.org/pdf/2607.01531
- SWE-agent — https://arxiv.org/abs/2405.15793
- Agentic Harness Engineering — https://arxiv.org/html/2604.25850
- Architectural Design Decisions in AI Agent Harnesses — https://arxiv.org/html/2604.18071v1
- Coding Benchmarks Are Misaligned with Agentic Software Engineering — https://arxiv.org/html/2606.17799v1
- OpenHands evaluation harness — https://github.com/OpenHands/benchmarks · https://docs.openhands.dev/openhands/usage/developers/evaluation-harness
- DSPy MIPROv2 — https://dspy.ai/api/optimizers/MIPROv2/
- GEPA — https://arxiv.org/abs/2507.19457
- AlphaProof / AlphaGeometry 2 — https://deepmind.google/blog/ai-solves-imo-problems-at-silver-medal-level/ · https://www.nature.com/articles/s41586-025-09833-y
- Scaling Test-Time Compute for Agentic Coding — https://arxiv.org/abs/2604.16529
- Theoria.md — `:202`, `:208`, `:229`, `:336`, `:340-349`, `:351`, `:353`, `:355`, `:356`, `:357`, `:368`, `:371`, `:373`
- `theoria-arm/inner/probe.py:1-23`; `theoria-arm/runs/{20260731T1240Z-A3-level2-carried, 20260731T1310Z-A3-level2-carried-r2, 20260731T1430Z-A3-level2-carried-r3, 20260731T1500Z-A3-sk48-carried-l1}/{RUN_STATE.json, surprises.jsonl}`
