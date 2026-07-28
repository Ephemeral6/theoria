# Battery v1 — what eating three new sources found

Recomputed over every trajectory in the repository: **31 runs, 4 arms, 38
metrics, 417 computed values**. Artefacts in [`artifacts/`](artifacts/),
regenerable with `python -m battery.run_battery` and byte-identical on a re-run.

Zero new game spend, zero model calls, zero network. Still a passive
instrument.

v0 read 26 runs from 2 arms. v1 adds `a0-spike` (an injected-rule-change
experiment), `cold-start-a2` (the only 打脸→修复 loop in the repository), and
the labelling that separates the variance-envelope cells from the M4 pilot
inside a ledger that had been pooling them.

---

## The headline: the contrast this phase exists to draw is 82% empty

`Theoria.md` Phase 2 process 1 specifies the discriminative gradient as **CC vs
Schema**. The Schema arm does not exist. v0 substituted the model ladder inside
`bare_cc` and recorded that as a weakness. v1 finally has real Theoria-arm
material, so the obvious move is to contrast `bare_cc` against it directly.

**That contrast has data on both sides for 7 of 38 metrics.**

The other 31 are structurally one-sided, and not for want of runs:

* `bare_cc` has no books, so the **entire epistemic family** (11 metrics) cannot
  be scored on it — not badly, at all.
* The offline Theoria arms have no model calls, so the **entire economy family**
  (7 metrics) cannot be scored on them.
* The mechanism family needs hand-annotated ground truth, which only the
  self-built worlds have.

The two arms are close to complementary, which means the effect sizes below are
computed on the thin overlap where both happen to be measurable:

| id | family | δ | n (Θ vs CC) | medians | verdict |
|---|---|---|---|---|---|
| X5 | exploration | +0.986 | 6 vs 24 | 41.5 vs 2.5 states | not ranked (neutral) |
| X2 | exploration | −0.765 | 6 vs 17 | 0.869 vs 1.000 | separates **against** |
| P5 | planning | −0.708 | 6 vs 24 | 0.000 vs 0.286 | not ranked (neutral) |
| X1 | exploration | +0.637 | 6 vs 17 | 0.781 vs 0.143 | separates **against** |
| X3 | exploration | +0.621 | 6 vs 11 | 0.140 vs 0.000 | separates, as declared |
| P3 | planning | +0.333 | 6 vs 15 | 0.095 vs 0.000 | separates **against** |
| X4 | exploration | +0.069 | 6 vs 17 | 0.074 vs 0.067 | no effect |

Of the five rankable metrics, **three separate backwards, one not at all, and
one separates as declared**. And the one that separates — X3, the exploration
family's signature — separates because a systematic coverage sweep front-loads
novelty by construction, which is a property of what the trace was *for*, not of
the arm that produced it.

**The whole table is confounded by world.** Every Theoria run here is on a
self-built world; every `bare_cc` run is on an ARC game whose API refused 29% of
its actions. X1 says the Theoria arms revisit states five times more often —
because a coverage walk deliberately revisits, and a `bare_cc` run that dies
after three steps cannot. P5 says the Theoria arms never fail — because a
self-built world cannot return HTTP 500.

Two consequences worth stating plainly:

1. **This is not process 1 and is not filed as process 1.** `Theoria.md` is
   explicit — 验证只用对照两臂，与 Theoria 无关 — so validation stays
   control-only in `discrimination.json`, and this contrast goes to a separate
   `arm_contrast.json` whose every entry carries `confounded_by_world: true`.
   Nothing here licenses a metric.
2. **This is the argument for the Schema arm, quantified.** A replay-level
   model is the only arm that would have books *and* model calls, i.e. the only
   one that overlaps both sides. `Theoria.md` did not pick CC vs Schema
   arbitrarily; it picked the one pair that can actually be compared.

A note on the p-values in `arm_contrast.json`, several of which are below 0.05:
the unpaired design attains p = 0.0117 at 2 vs 17 where four paired games could
not beat 0.125. **That power was bought by discarding the pairing**, which is
the only thing that was controlling for the world. They are reported with
`min_attainable_p` beside them and should persuade nobody.

## 21 of 38 metrics have never been computed on a control arm

This is what the new 验证材料 column in [`METRICS.md`](METRICS.md) is for, and
it is generated from the recompute rather than asserted.

| | metrics |
|---|---|
| validated on control arms | 17 — all of exploration, planning (except P4), economy |
| **zero control-arm runs** | **21 — the whole epistemic family, the whole mechanism family, and P4** |

`Theoria.md`: 分不开已知差异的指标，没资格测未知差异 — a metric that cannot
separate a known difference has no business measuring an unknown one. Twenty-one
metrics have never been given the chance, because the material that would give
it to them does not exist. That is not a defect in those metrics and it is not
fixable by writing more code; it is the same hole as the missing Schema arm,
seen from the other end.

It does mean something concrete for Phase 4: **the epistemic family, which is
where Theoria's distinctive claims live, is entirely unvalidated as an
instrument.** Every number it produces is currently a description of one arm
with nothing to compare it against.

## Three defects in v0, found by feeding it new material

None of these were found by inspecting the battery. All three surfaced because
a new source had a field the old one did not.

**1. v0 pooled two campaigns and could not know it.** `baseline-arms/ledger.jsonl`
holds the M4 pilot and the phase-3 variance envelope in one file with nothing on
a row to tell them apart. They are not interchangeable: all three envelope cells
stop at exactly 10 cumulative failures because `bare_cc.py` says so, so they are
right-censored by a harness rule rather than by anything the arm did. v1 joins
`out/campaign_cells.jsonl` and `out/pilot_*.json` to label every run; 3 are
envelope, 14 pilot, 7 unlabelled. The envelope is visibly the more degraded
material — P5 median 0.40 against the pilot's 0.286.

**2. The turn axis counted retries as deliberation.** `bare_cc` writes one
`model_call` row per *attempt*, and one pilot run bills three attempts at a
single step with three different token counts and three different prices. v0's
economy metrics used call order as the turn axis, so a run whose model call
failed twice looked like a run that thought three times. v1 separates the two
axes: E1 stays on the billing axis because the money was really spent, E2/E3
move to the decision axis. This changed four values on pre-existing runs, and
one of them changed status — `sk48-sonnet-9022a076` drops below the eight-turn
floor and now correctly reports `insufficient-data` where v0 reported 0.315.

**3. `parse_dsl` silently missed every annotation on a continuation line.**
Every theorem in the repository writes its bracket on the line *after* the
clause, so `proven` and `probe_pending` were `False` for precisely the clauses
that carry a proof or a pending probe — on all three arms at once. Fixed; no
metric currently reads those flags, so no published number moves, which is
exactly why it survived v0 unnoticed.

## The pre-registration scoreboard

`PREDICTIONS.md` registered nine metrics before any of them was implemented.
The seal declaration is honest that most are post-dictions, because the recon
passes quoted values. Here is what happened anyway.

**X6 — falsified, in the manner the registration predicted.** The prediction
was `bare_cc < 0.5`, with an explicit escape clause: *a value near 1.0 would
falsify the reasoning, not confirm the arm — it would mean the harness, not the
arm, is varying the action*. X6 is **1.000 on all three envelope runs** and has
a median of 1.000 across the pilot. The arm essentially never re-emits a refused
action. The ladder makes it worse: δ = −0.500, so the *more* capable models
change action less. X6 as defined measures the prompt builder. It sits in the
reference tier, where its own gaming register put it before the numbers existed.

**E7 — refuted by the de-redundancy pass, in the same recompute that
introduced it.** E7 was built on the claim that E4 reads nothing because context
tokens are constant by construction on a one-shot-CLI arm. The token fields *are*
constant — `input_tokens` is 10 and `cache_read_input_tokens` is 24405 on every
envelope call — but `cache_creation_input_tokens` tracks the prompt body after
all. **E4 ~ E7 correlate at ρ = +0.991 over 14 shared runs**, and the clustering
merges them with E4 as representative. E7 did not rescue a blind metric; it
restated a metric that could see. Both are kept so the discrepancy stays
visible, and the claim in E7's docstring has been left standing and wrong.

**K14 — falsified on one arm, by its own registered gaming mode.** The
prediction was `theoria < 0` on every arm with a compression account. It holds
at −5 bits on A0-base and on all three A2 manuals. It fails on `a0-no-button`,
which scores **+1001** — because that manual admits exactly one concept, so its
minimum *is* its maximum. K14's gaming register says: *admit no small concepts;
a vocabulary of one has a minimum equal to its maximum.* The register predicted
the failure and the data produced it in the same run.

**K13 — confirmed, and only just.** Predicted `theoria_a2 < theoria_a0_spike`
and `a2 < 0.3`. Result: **A2 0.262, a0-spike 1.095**. Localised repair costs a
quarter of what the theory cost; rebuilding costs slightly more than the theory
cost. The margin matters: the adapter faced a genuine choice about whether L6's
verification replay is billed, worth 0.164 unbilled against 0.262 billed. Both
clear 0.3, but **the unbilled reading is the one that flatters this project's
own prediction**, so the billed reading was taken and the alternative kept in
the artefact (`DECISIONS.md` D-B-015). Under the flattering convention this
prediction would have looked comfortable; under the conservative one it barely
survives, and that difference is the honest report.

**E6, M4, M5, M6, K12 — as registered.** E6 5.9 (envelope) and 5.3 (pilot),
inside the predicted 5–10. M5 = 0.75 on a0-spike: the predicted *ceiling* below
1.0 held, and the mechanism is the one named — `nocross` changes a rule that the
`match` evidence never exercises differently, so a manual replaying that
evidence perfectly stays silently wrong. K12: A2 closes 6 of 6 beats, a0-spike 0
of 6, which is the fraction doing its job — a0-spike detects and rebuilds, real
work that closes none of the six named beats.

## P4 was computed for the first time

REPORT_V0 listed solution redundancy as *"never computed once — entirely
notional in v0"*: it needs ground truth **and** a run that was trying to win,
and no run had both. A2's `solved_episode.jsonl` is an 18-action episode against
an 18-action optimal plan.

**P4 = 1.000.** The first path-efficiency number the battery has ever produced,
and it is exactly optimal — which also means it discriminates nothing yet. It
is one run, on a self-built world, by a planner with the ground truth in hand.

## K2 now means two different things and the report says which

A0 scores held-out accuracy **0.000**. a0-spike scores **1.000**. Both are
`K2`, and comparing them directly would be wrong.

* A0's denominator is **3** state-action pairs its trace happened never to
  cover. It is a handful of adversarial gaps, and the manual gets all three
  wrong for a reason `THEORIZE_LOG` R-05 predicted by name.
* a0-spike's denominator is **39960** — an exhaustive enumeration of every
  well-formed (state, direction) pair across five levels, most unreachable from
  the start state. Nothing was withheld; the world is simply small enough to
  enumerate.

`Theory.held_out_frame` now carries a one-line description of the sampling frame
on every theory-bearing run, and K2's support fields carry the counts. The DC22
shape that v0 reported — 98.7% on replay, 0% off-trace — remains real and
remains A0's. It is not a property of the framework that a later, better-evidenced
manual reproduced; a0-spike's exhaustive check finds zero mismatches.

## De-redundancy, first run with enough data to bite

257 of 703 metric pairs now share enough runs to correlate, against a matrix
that was almost entirely empty in v0. Six pairs exceed |ρ| ≥ 0.9 and the
clustering merges 38 metrics into 33:

| cluster | ρ | representative | reading |
|---|---|---|---|
| E4 ~ E7 | +0.991 | E4 | E7 is redundant — see above |
| K14 ~ K5 ~ K7 | ±1.000 | K5 | on 5 near-identical manuals; thin, not yet a merge |
| K10 ~ K8 | −0.968 | K10 | across the probe/theorem boundary; suspect |
| K6 ~ X1 | +0.900 | X1 | across families with no mechanism; treat as noise |

Two below the threshold are worth reading anyway: **E6 ~ P5 at +0.857** (retry
amplification is largely the failure rate restated, since every failed step
burns the full eight retries) and **P1 ~ P5 at −0.837**, which reproduces v0's
finding that actions-per-model-call is mostly an API failure readout.

The K-family cluster is the one to distrust: five manuals, four of them variants
of two worlds, is not a sample from which ρ = 1.000 means anything.

## What v1 still cannot see

| gap | why |
|---|---|
| **The specified CC vs Schema gradient** | still no Schema arm; `SCHEMA_LOCATE.md` says there may never be one. This now has a number attached: it is why 31 of 38 metrics have no cross-arm contrast |
| **Any Theoria arm on an ARC game** | every Theoria run is a self-built world, so arm and world are perfectly confounded in every comparison |
| **The economy family on any theory-bearing arm** | A0, a0-spike and A2 all ran engines and hand adjudication with zero LLM in the loop. Claim C2's signature has still never been computed on an arm with a theory |
| **M3 cross-level transfer (claim C3)** | still no multi-level run |
| **Repair with a control** | K12/K13 rest on one A2 loop and four a0-spike variants, authored by the project that defined the metrics, in worlds it built. An arm without a manual cannot have a repair loop at all, so no control is constructible |
| **Statistical power** | unchanged. 4 paired games; 6 non-tied pairs is the floor for p<0.05. Every process-1 verdict is still `underpowered` |

## What v2 needs, in order

1. **Seal the recon.** v1's pre-registration is materially weaker than v0's for
   one avoidable reason: the surveys that preceded it quoted values, not just
   schemas. v2's surveys must return field names only, with values held until
   the predictions are committed. This is the cheapest fix on the list and the
   one that most affects whether anything here is believable.
2. **Retire or rebuild X6.** It measures the prompt builder. Either give the arm
   the failure in its context and re-measure, or drop it.
3. **Fold E7 into E4 or drop it.** ρ = +0.991 is not a second finding.
4. **K14 needs a floor on vocabulary size**, or it rewards a one-word manual.
   K5 and K7 are the companions; nothing pairs them automatically.
5. **A repair loop on a world the project did not build.** Everything in the U4
   family is currently self-graded homework, and `Theoria.md` already says U4 is
   排座次 and 不当证据 — an ordering, not evidence. The battery should keep
   refusing to cite it until that changes.
6. **Six paired games.** Unchanged from v0 and still upstream of everything
   else.
