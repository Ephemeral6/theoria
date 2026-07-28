# QC bar — written before the harness was run

A0′'s explorer fixed its budget rule before looking at which gaps it produced,
"rather than tuning the cut until the interesting one shows up"
(`cold-start-a0/prime/world/explorer.py`). The same discipline applies to an
acceptance threshold: a bar chosen after seeing the numbers is not a bar.

So this file is written first, and it is not edited afterwards. What the run
found goes in `worldgen/qc/QC_REPORT.md`; if a world misses the bar it is
recorded as a miss, not re-scored against a lower one.

## What "跑 cold-start-a0 流水线" can and cannot mean here

`cold-start-a0/run_all.py` says it plainly: **M3 (theorize) is missing from the
driver because a script cannot do it.** `theory.dsl` is a hand-written artefact
and the driver consumes it. There is therefore no such thing as an automatic
"说明书准确率" for twenty worlds — a manual is the output of an adjudication, and
adjudication is the one step that is not mechanical.

What *is* mechanical is everything on either side of M3: the engines that
propose, and the scoring that grades. So the bar below grades the **engine
manual** — the raw mined rule set, before any LLM adjudicates it — applied as a
frame predictor. This is a **lower bound** on what an adjudicated manual can
reach, because adjudication exists precisely to improve on the mined set
(A0′ Run A: the engines proposed 35 hypotheses; the manual kept 21). A world
whose engine manual already predicts the world exactly is a world where the
theorize step has been handed a solved problem; a world whose engine manual is
far off is a world where the trace does not carry the mechanism.

This substitution is the honest one available, and it is a **stated gap**, not a
silent one: see `RUN_STATE.md` §gaps.

## Sample

Three worlds, chosen before running, one per complexity tier, each covering a
different mechanism family, and at least one irreversible:

| world | tier | why this one |
|---|---|---|
| `t1-switch-toggle` | 1 | the A0′ shape itself — reversible switch/door. The control: if the harness cannot score this, the harness is wrong, not the world. |
| `t1-switch-latch` | 1 | the A0 shape — same geometry, irreversible latch. Paired with the above it is the reversibility contrast the whole catalogue exists to supply. |
| `t2-lock-fragile` | 2 | two families composed (count-lock + consumable), both irreversible, tier 2. The hard case. |

## The bar

Per world, all four must hold:

* **L1 liveness** — `pipeline.engines_stage.run_stage` (imported read-only from
  `cold-start-a0`) runs to completion on the world's shipped `raw_trace.jsonl`,
  and every candidate it emits validates against the frozen
  `CONTRACTS/candidates_schema.md` via `engine-rig/tools/validate_candidates.py`.
  Binary. No partial credit.

* **L2 structure** — for the mover track, the mined guards are **mutually
  exclusive** and **explain every transition** in the trace. These are
  `MiningResult.guards_are_mutually_exclusive` and `.explains_every_transition`,
  computed by the upstream pipeline, not by anything in `worldgen/`. Binary.

* **L3a replay accuracy = 1.000** — the mined rule set, applied as a frame
  predictor, reproduces every transition of the trace it was mined from.
  Anything below 1.0 means the miner contradicts its own evidence; there is no
  tolerance band for that.

* **L3b held-out accuracy ≥ 0.90** — the same predictor, scored only on
  reachable `(state, action)` pairs the trace never contained. This is the
  number that matters and the reason the threshold is not 1.0: A0 itself scored
  **0.9873** with 99 % coverage and shipped three errors, and A0′ scored 1.0
  from 47 %. A family whose worlds sit at or above 0.90 held-out from a 40 %
  trace is supplying traces that carry their mechanisms. Below 0.90 the world is
  not disqualified from the catalogue — it is **flagged as thin evidence**, which
  is itself the product V2 and the ablation arm want.

**Family verdict:** the family passes if all three sampled worlds clear L1, L2
and L3a, and at least two of three clear L3b. Recording which world missed, and
by how much, is part of passing — a suppressed miss is a failed run.

## Protocol note, fixed in advance

L3b needs an `Obs` at states the shipped trace never visited, and an `Obs`
carries segmentation track identities. Segmenting the shipped trace and the
held-out states separately would produce two unrelated sets of track ids and the
comparison would be meaningless.

So: segmentation runs **once**, over the exhaustive walk; the rules are mined
**only** from the first `budget` transitions — byte-identical to the shipped
`raw_trace.jsonl` prefix, asserted in the harness — and are scored over all of
them. Mining sees exactly what the shipped trace contains and not one transition
more. This differs from `cold-start-a0`, which segments only its truncated
trace, and the difference is recorded here rather than discovered later.
