# QC — three worlds through cold-start-a0's engines

Bar: [`PREREGISTERED.md`](PREREGISTERED.md), written before the harness ran and
not edited since. Raw numbers: `worldgen/out/qc/QC.json`. Reproduce with

```bash
cd .worktrees/c1-worldgen && python -m worldgen.qc.run_qc
```

## Result: the family MISSES the pre-registered bar, on two of the four layers

| world | L1 liveness | L2 structure | L3a replay | L3b held-out (bar 0.90) |
|---|---|---|---|---|
| `t1-switch-toggle` | ✅ | ✅ | ✅ **1.000** | ❌ 0.773 |
| `t1-switch-latch` | ✅ | ✅ | ✅ **1.000** | ❌ 0.896 |
| `t2-lock-fragile` | ❌ **raises** | ❌ | — | — |

Family verdict from `PREREGISTERED.md` — all three clear L1/L2/L3a and at least
two clear L3b — is **not met**: one world does not run at all, and zero of the
two that do clear L3b. The bar is not being moved. What follows is what the
miss is made of, because a miss whose cause is measured is worth more than a
pass whose margin is not.

## L1/L2 — what did run

Both switch worlds ran the upstream stage clean:

| | `t1-switch-toggle` | `t1-switch-latch` |
|---|---|---|
| frames / transitions | 41 / 40 | 31 / 30 |
| tracks after re-identification | 4 | 4 |
| rules mined | 31 | 27 |
| guards mutually exclusive, all tracks | ✅ | ✅ |
| explains every transition, all tracks | ✅ | ✅ |
| `zero_space` global laws | 3 | 3 |
| probes designed / executable | 17 / **0** | 9 / **1** |
| candidates schema-valid | ✅ | ✅ |

The probe counts are worth a second look, because they are A0 against A0′ again
and this time the worlds differ only in one legend entry. The **latch** world
yields an executable probe; the **toggle** world yields seventeen designs and
none executable. That is the opposite of A0′'s result and it is not a defect —
A0′'s toggle produced 13 executable probes at 47 % coverage, and this toggle
world runs at 38 %, so the prober is being asked to split frontiers from a
thinner trace. It is recorded rather than explained away.

## L3a replay — 1.000 on both

The mined rules reproduce every transition they were mined from, with **zero
guard conflicts** inside the replay window. The render self-check passed exactly
(123/123 and 80/80 frames), so the board-plus-tracks decomposition reproduces
observed frames and these numbers grade rules rather than the renderer.

Getting here took one fix to the harness, not to the worlds: the predictor
originally treated a segmenter `appear` event as unpredictable, because
`Effect` carries no position for an appearance. But the *segmentation* carries
one — the track has an identity across its absence, which is what
`pipeline/reidentify.py` exists upstream to give it — so a returning door is
predicted at the last place it was seen. See `qc/engine_manual.py:_apply`.

## L3b held-out — 0.773 and 0.896, and what the misses are

Two distinct failure modes, and neither is a predictor bug — both were traced to
individual transitions.

**`t1-switch-latch`, 0.896 — the unwitnessed negative.** Every miss is
`blocked_by_wall` on `UP` from row 1, with exactly **one** guard matching. The
trace never contains an `UP` into the top wall, so the mined `obj0_step_UP`
guard is not constrained to exclude it and the engine manual walks the agent
into the wall. This is A0's own failure mode reproduced exactly: a rule that is
*under-constrained* rather than wrong, on a case the trajectory never presented.

It is also precisely the gap **adjudication closes and mining cannot**. A0's
hand-written manual has no `blocked` clause at all — `score_vs_truth.py`'s
structural table records `blocked` as *"entailed by the frame axiom, not a
clause"*. The frame axiom is a semantic decision about what a manual means when
it says nothing, and no amount of mining produces it. So the 0.104 shortfall
sits almost entirely on the one thing `PREREGISTERED.md` predicted the engine
manual would be a lower bound on.

**`t1-switch-toggle`, 0.773 — frontier ambiguity.** 51 guard conflicts in the
held-out window (0 in replay): two guards match the same unseen observation and
the predictor takes the miner's own cheapest-first ordering. The doors are the
tracks that split. This is a live frontier, which is the state a probe exists to
resolve — and the same run designed 17 probes and could execute none of them.
The two numbers are one finding: **this world's trace leaves ambiguity that its
trace also cannot resolve.** That is a property of the 38 % budget on this
geometry, and it is the single most useful thing the QC found about the
catalogue.

## `t2-lock-fragile` — the miner refuses the world, and the world is not at fault

`pipeline.engines_stage.run_stage` raises
`NoSeparatingGuard: no literal separates transition 1 from the positives`.

That error has two possible causes and they carry opposite verdicts, so the
harness localises it (`worldgen/qc/diagnose_miner.py`) rather than guessing:

* if the two transitions the miner cannot separate have **identical frames** and
  different effects, the world does not determine its own behaviour and the
  defect is in this library;
* if their **frames differ** and no atom in the vocabulary sees the difference,
  the defect is in the atom set.

Measured: the frames differ, and every atom in the 98-atom vocabulary agrees on
both. Independently, `frame_determines_state` is now a build gate and reports
**0 collisions on all 20 worlds** — 87/87 distinct frames on this world. So the
world is learnable and `a0_relational_v1` cannot express what separates these
two transitions.

This is the **表达力不够 / concept-not-formed** row of Theoria's failure taxonomy,
found offline by the factory instead of live in Phase 3 at API cost, which is
what the factory is for. It is reported upstream in
`monitor/inbox/20260728T093000Z-W-1610-a0-vocabulary-cannot-separate-a-count-lock-world.md`
rather than worked around here — `cold-start-a0` belongs to the other track and
`worldgen` may not edit it.

## What this says about the family

The catalogue is not disqualified by this and should not be read as if it were.
Three things are now measured that were not before:

1. two worlds differing in **one legend entry** produce 1.000 replay and a
   0.12 spread in held-out accuracy, with the difference traceable to named
   transitions. That is the discriminating instrument V2's exam and the ablation
   arm were asked for;
2. a world with two composed irreversible families is **outside the reach of the
   current engine vocabulary**, which is a capability boundary worth having a
   fixture for;
3. the shortfall against the bar is concentrated on the frame axiom and on live
   frontiers — the two things the *adjudication* step exists to supply. The bar
   was set for an engine manual on the assumption that the mined set would get
   closer to an adjudicated one than it does. That assumption is now measured
   and wrong, which is a more useful outcome than a threshold that was met.

The honest next move is **not** to lower L3b. It is to run the missing half:
hand-write a `theory.dsl` for one of these worlds, compile it, and score the
*adjudicated* manual on the same held-out set. If it clears 0.90 where the
engine manual sits at 0.77, the gap is the value of adjudication, stated in a
number. That is scoped in `RUN_STATE.md` §gaps and is not done here.
