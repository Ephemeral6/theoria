# RUN_STATE — 20260731T1723Z-ITERATION-PRACTICE

Territory `fleet-study`. Branch `p12/iteration-practice`, base commit `73760dc8`.
Document + measurement only. No code changed, nothing run against the API, no spend.

## What this run produced

- `fleet-study/ITERATION_PROTOCOL.md` — a field survey of thirteen comparable
  systems' improvement loops, a concrete Phase 3 iteration protocol built from
  them, and a diagnosis of the g50t level-1 theory against the failure taxonomy
  at `Theoria.md:340-349`.
- `probe_yield.py` / `probe_yield.json` — a read-only recomputation over
  `theoria-arm/runs/*/surprises.jsonl` producing two statistics the current
  scoreboard does not carry: `frontier_width` and `probe_yield`.

## The finding

Pooled over the four live carried legs (`20260731T1240Z`, `T1310Z-r2`,
`T1430Z-r3`, `T1500Z-sk48-carried-l1`): **47 probes, frontier width exactly 2 on
every single one, and the observed outcome inside the candidate set 0 times out
of 47.**

The candidate sets are large (9–24 hypotheses) and degenerate: `manual`, `inert`,
and 10–23 `without_<rule>` ablations that each reproduce one of those two answers.
So the split entropy that `Theoria.md:208` defines the probe's value as is capped
at one bit by construction, and because the ablation family is closed downward it
cannot contain a mechanism the manual lacks — which is what every failure so far
has been. `theoria-arm/inner/probe.py:10` documents the choice in its own words:
"The frontier here is built by ablation".

`Theoria.md:202` rules that out in advance: the frontier is 全体一致假设的前沿,
不交点猜测 — all hypotheses consistent with the ledger, not a point guess.

Cost of the degeneracy: 28 of r3's 33 successful actions (85% of the action
budget) bought no discrimination, and `levels_completed` is 0 in every leg.

## Failure class

**戳探设计差** (`Theoria.md:348`), fix at 前沿分裂准则. Not 机制归纳错 — r3 has one
replay mismatch against 28 probe refutations, so the manual replays history and
fails only on counterfactuals. The naive mapping (probe_refutation → wrong
induction) would send the next round to a theorize-prompt fix that cannot work.

Highest-leverage change for the next round: build the probe frontier by
generation, not ablation — K ≥ 3 mutually incompatible *successor* hypotheses
containing mechanisms the manual lacks. One knob, one file, zero extra actions.
Bound prediction and the reclassification rule are in `ITERATION_PROTOCOL.md` §3.4.

## Cross-territory asks (NOT dropped — see note)

Two items belong to other territories and must be dropped into `monitor/inbox/`
**from the main tree**. They are recorded here rather than written, because
`monitor/` is tracked and a message posted from a worktree is never read:

1. `theoria-arm` — leg `MANIFEST.json` carries no account identifier (r3 has
   `prompt_id` but `branch` and `base_commit` are `null`). The two-account
   crossover of `ITERATION_PROTOCOL.md` §2.7 is unauditable until one exists.
2. Design baseline — `Theoria.md:340-349` has no row whose symptom column
   cleanly receives a mass of `probe_refutation`; 戳探设计差's stated symptom is a
   non-event (probes skipped for zero entropy), not a refutation. The taxonomy
   probably needs a row, or the two instruments in §2.4 folded into `:351`.

## Honest limits

Nothing here was executed against the environment; every number is recomputed
from artefacts that already existed. The protocol is untested. Four of the
thirteen surveyed systems were read at abstract depth only, and that is disclosed
in the document head. No leg has ever completed a level, so the U-ladder and
transfer claims remain unmeasurable at the current leg length regardless of
protocol.
