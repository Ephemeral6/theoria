# RUN_STATE — C1-worldgen

Worker `W-1610`, 2026-07-28. Branch `agent/c1-worldgen`, base commit
`1e7002d`. Provenance: `worldgen/runs/20260728T081713Z-C1-worldgen/`.

## What the item asked for, and what is here

| goal | state |
|---|---|
| parameterised mechanism library, 7 families, complexity tiers | **done** — `worldgen/mechanisms/`, composable, tier 1/2/3 |
| 20 worlds, each with ground truth, solvability decision, systematic trajectory, `raw_trace.jsonl` in cold-start-a0 format, reversibility annotation | **done** — `worldgen/out/worlds/`, six build gates green, byte-reproducible across interpreters |
| QC: three worlds through the cold-start-a0 pipeline, manual accuracy at the bar | **run, and the bar was missed.** See §the miss |
| registered uses | **done** — `worldgen/README.md` §registered uses |

## The inherited remnant, and why it was kept

The board item said the predecessor branch was 可读可弃. It was read. The
architecture was kept and the artefacts were not: two independent adversarial
audits (`runs/…/AUDIT.md`) plus one measurement run found **fourteen defects**,
of which three were critical and two falsified the properties the library is
sold on. The shipped `out/` was also stale — built from an older code state, so
its numbers described a catalogue that no longer existed.

Kept because they are genuinely good: `State = (agent, vars)` with disjoint
per-mechanism slices (complete, hashable, JSON-serialisable, no per-mechanism
state class to merge); the exact uncapped reachability decision in
`solvability.py`, which raises rather than truncating; structural determinism
(sorted reachable sets, mechanisms ordered by `(priority, name)`, `sort_keys` and
`newline="\n"` on every write); and a trace writer byte-faithful to
`cold-start-a0/prime/world/ground_truth.py`.

## The three that mattered

**The reversibility stamp did not exist.** `reversibility.py` computed
`any(can_reach(t, s) for t in targets for s in sources)` — the cross product of
all firing targets against all firing sources — where the docstring specifies a
firing transition reaching **its own** source. Two consequences: every
finite-but-repeatable rule read `UNBOUNDED`, and the graded branch was
unreachable dead code (no cross-product edge ⇒ no chain edges ⇒ longest chain
always 1). Across 20 worlds, 94 rules read `-1`, 8 read `1`, and **nothing read
anything else**. This is the A0′ criterion the item names as the framework
finding, and it was a one-line quantifier error. Fixed, with the longest-chain
descent rewritten iteratively (the recursive version sat behind a
`setrecursionlimit` bump — past the C stack that is a hard interpreter crash, not
an exception — and memoised before exploring children). `collect_token` on
`t1-tokens-lock` now reads **3**, `cross_fragile` on `t1-fragile-bridge` **2**,
`toggle_switch` on `t1-switch-toggle` **-1**.

**Two-way portals were dead code in every world.** `portal.interact` tested the
landing cell with `world.is_free`, which excludes `no_rest`, which contains both
mouths — so for `twoway` the landing cell *is* always excluded. `t2-portal-pair`
collapsed to 5 reachable states and shipped unsolvable; the `portal-pair` /
`portal-paired` contrast pair was confounded because one half never ran. And
`reversibility.json` recorded `teleport_twoway` as `unreachable` with a clean
`reversibility_score: 1.0` — a dead mechanic passing as a clean world.

The naive repair — swap `is_free` for `can_stand` — would have been worse.
`consumable` renders ARMED identically to INTACT, justified by the agent always
covering an armed tile, and that holds *only* while `interact` is the sole route
onto a tile. `can_stand` would let gravity drop the agent onto an intact tile and
make two distinct states render identically: a frame-does-not-determine-state
bug, traded for a dead-code one. So the library gained the third predicate it was
missing — **`can_rest`**, "may the agent be *deposited* here without skipping
somebody's `interact`" — and `reserved` per mechanism. `t2-portal-pair` now has
24 reachable states.

**The catalogue's solvability labels were inverted.**
`t2-unsolvable-nodoor` — the world whose entire purpose is to ship an
unsolvability certificate — was **solvable in five steps**, because the door sat
in an open room with floor above and below it. The same geometry meant
`t1-switch-toggle` and `t1-switch-latch` were winnable **without ever touching
the switch**, so the headline mechanic was decorative in three worlds, and
`t3-full-house`'s block was walled on two opposite sides so `push` could never
fire. Nothing compared measurement to intent. Now `spec.intended_solvable` is a
build gate, the divider is real, and exactly one world is unsolvable.

## The other repairs

A door could **close under the agent** (agent inside a solid cell, the door's own
invariant violated, and the agent painted last erasing the closed door's colour —
two states rendering alike). Now refused, as a witnessable rule
`blocked_toggle_would_shut_door`, and `t1-switch-toggle` carries a second door
next to the switch specifically so the catalogue witnesses that branch.

Gravity used `is_free` for the **agent**, so it would not drop the agent onto a
collected token's cell — which renders as bare floor — leaving the agent hovering
with visible floor beneath it. Its self-check `nothing_rests_on_a_free_cell`
evaluated the *same wrong predicate*, so it returned True on exactly the states
it existed to reject. Both now use the predicate that governs the fall.

`up_is_inert` was published as a true rule with `reversible: True` and is false:
`UP` into a fragile tile returns the agent to where it started and leaves the
tile permanently collapsed. Scoped to plain floor, with the reason recorded.

**The rule table was prose with nothing checking it.** Only `name` was tied to
`Outcome.rule`, by convention. 12 of 20 worlds declared rules that never fired,
and `GROUND_TRUTH.md` printed `unreachable` for three (`fall`, `up_is_inert`,
`door_mirrors_net`) that are not tags at all — they fire inside `settle`. A
reader could not tell "impossible by design" from "impossible by bug", and one of
those entries, `teleport_twoway`, *was* the bug. Now `rule_correspondence` closes
both directions and gates the build, with two declared exemptions
(`cascade`, `clause`) that are claims rather than escape hatches.

**Every gate was already computed, printed, and then exited 0.** Seven worlds
shipped `claim_disagreements` and one a violated invariant. A constant false
alarm is indistinguishable from the real one it exists to raise.

And the disagreements themselves were a **conceptual conflation**, not defects:
the library had one word for two properties. `collect_token`'s effect is one-way
*and* the rule is re-witnessable three times in a three-token world;
`advance_cycler` has order k and destroys nothing *and* measures a single witness
in two worlds. Mechanisms now declare `re_witnessable` where the axes come apart,
which is what the graph measures, and `reversible` stays as prose.

Also: `worldgen/.gitattributes` (the directory had none, `core.autocrlf` is true
here, and the first commit would have normalised every artefact); the determinism
gate now rebuilds in a **separate interpreter** at a different `PYTHONHASHSEED`
rather than in-process where the seed was shared; and the unsolvability
diagnostic deletes a portal pair as one unit instead of one mouth at a time,
which used to produce `invalid: portal pair 'p' has 1 mouth(s)` twice and name no
blocker.

## The catalogue

20 worlds, 9/7/4 across tiers 1/2/3, 6 to 2654 reachable states, mean
reversibility score 0.949, 4 variant pairs, 1 unsolvable. Six build gates green,
byte-identical across interpreters.

Six worlds carry a single-witness rule — the A0 failure mode, on purpose and
labelled: `push` in `t1-push-corridor`, `press_latch` in `t1-switch-latch` and
`t3-latch-maze`, `cross_fragile` in `t2-lock-fragile` and `t3-latch-maze`,
`advance_cycler` in `t2-cycler-lock` and `t3-cycler-portal-lock`. The last of
those is the interesting one: a rule whose effect is fully reversible and which a
single trajectory can still witness only once.

## The miss

`worldgen/qc/PREREGISTERED.md` fixed the bar — sample, layers, and a held-out
threshold of **0.90** — before the harness was run, and names the substitution it
makes: `cold-start-a0/run_all.py` says M3 (theorize) is missing "because a script
cannot do it", so what is graded is the **engine manual**, the raw mined rule set
before any adjudication, which the file states is a *lower bound*.

Measured (`worldgen/qc/QC_REPORT.md`, raw in `out/qc/QC.json`):

| world | L1 | L2 | L3a replay | L3b held-out |
|---|---|---|---|---|
| `t1-switch-toggle` | ✅ | ✅ | **1.000** | ❌ 0.773 |
| `t1-switch-latch` | ✅ | ✅ | **1.000** | ❌ 0.896 |
| `t2-lock-fragile` | ❌ raises | ❌ | — | — |

**The family misses the bar and the bar was not moved.** What the miss is made
of was traced to individual transitions:

* `t1-switch-latch`'s misses are *all* `blocked_by_wall` on `UP` from row 1, one
  guard matching, i.e. an under-constrained rule on a negative the trace never
  showed. A0's hand-written manual has no `blocked` clause either —
  `score_vs_truth.py` records it as *"entailed by the frame axiom, not a
  clause"*. The frame axiom is a semantic decision; mining does not produce one;
* `t1-switch-toggle`'s are frontier ambiguity — 51 guard conflicts held-out, 0 in
  replay — in the same run that designed 17 probes and could execute none. The
  trace leaves ambiguity it also cannot resolve;
* `t2-lock-fragile` makes the miner raise `NoSeparatingGuard`. Localised rather
  than guessed (`qc/diagnose_miner.py`): the two transitions have **different
  frames** and all 98 atoms agree on both, and `frame_determines_state` is 0
  collisions on all 20 worlds. So the world is learnable and `a0_relational_v1`
  cannot express the difference — 表达力不够, caught offline for free instead of
  in Phase 3 at API cost. Reported upstream in `monitor/inbox/`; not worked
  around, since `cold-start-a0` is the other track's.

So the bar's premise — that the engine manual gets close to an adjudicated one —
is now measured and wrong. That is more useful than a threshold that was met.

## Gaps — what is not done

1. **The adjudicated half of the QC.** Nobody hand-wrote a `theory.dsl` for a
   worldgen world, compiled it, and scored it on the same held-out set. That is
   the missing measurement and it is the one that would price adjudication: if a
   written manual clears 0.90 where the mined set sits at 0.77, the gap *is* the
   value of the theorize step, in a number. Scoped, not done.
2. **`t2-lock-fragile` does not run the upstream pipeline.** Out of my hands —
   the fix is an atom in `cold-start-a0/pipeline/atoms_a0.py`, another track's
   file. Filed.
3. **Four worlds have very thin traces** (`t1-portal-oneway` 10/104,
   `t1-fragile-bridge` 10/168, `t2-gravity-push` 9/140, `t2-portal-paired`
   10/24). This is honest — the 40 % budget is a stated policy and an irreversible
   world's greedy walk genuinely stalls, which is the A0′ point — but 6 % coverage
   is thin evidence. A multi-episode trace (reset and walk again) would fix it and
   would need a second file, since a reset marker cannot go in `raw_trace.jsonl`
   without breaking the zero-downstream-change contract. Not built.
4. **`t2-portal-paired` is nearly degenerate** — 6 reachable states, solvable in
   2. It works and it is a legitimate minimal contrast to `t2-portal-pair`, but it
   carries little evidence.
5. **`push` in `t3-full-house`** fires but the world is solvable in 6 steps
   without it; the block is exercised, not load-bearing.
6. **The seal has A0's hole**: one instance built these worlds, repaired them,
   and graded them. The adversarial audits were separate agents with no stake in
   the code, which is better than A0 had, and it is not independence.

## Reproduce

```bash
cd .worktrees/c1-worldgen
python -m worldgen.verify        # build gates + determinism + tests + QC
```
