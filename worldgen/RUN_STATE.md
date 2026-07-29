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

---

# RUN_STATE — C6-worldgen-mutate

Worker `W-1251`, 2026-07-28. Branch `agent/c6-worldgen-mutate`, base commit
`0d28e99`. Provenance: `worldgen/runs/20260728T134933Z-C6-worldgen-mutate/`.
Nothing above this line was edited; C1's record stands as written.

## What the item asked for, and what is here

| goal | state |
|---|---|
| `worldgen/mutate.py`: a built world + one rule-level edit → new world + new truth | **done** — 15 mutants in `out/worlds/v-*/`, six files each, all six build gates plus two new ones green |
| a machine-readable description of the edit, for 检测延迟 / 修复成本 / 连带作废 | **done for two of three, partial for the third and it says so** — `out/worlds/MUTATIONS.json`; repair cost is blocked on another territory's miner, see §gaps |
| four edit families, ≥2 instances each | **done** — 3/6/3/3 across `forbid_action` / `change_guard` / `reversible_to_irreversible` / `move_portal_exit` |
| factory inspection as in C1 (sampled through cold-start-a0) | **run, and it missed.** See §the second miss |
| interface written in RUN_STATE, `exam/` untouched | **done** — §the interface below; `git diff --stat` touches no file under `exam/` |

## The interface — what `exam/` may read, and where

Nothing in `exam/` changed. **One thing in `exam/` does need to**, and the first
version of this section said otherwise:

| surface | what it contains | licence |
|---|---|---|
| `worldgen/out/worlds/INDEX.json` | **unchanged — still exactly the twenty.** Zero rows added | open (roster) |
| `worldgen/out/worlds/<variant_id>/` | the same six files as any other world, so `exam/papers/worldgen_port.py`'s `open_world`, `trace`, `scoring_truth`, `coverage`, `reversibility` all work unchanged | `spec.json` + `raw_trace.jsonl` open; the other four scoring-only |
| `worldgen/out/worlds/MUTATIONS.json` | **new.** `roster` is the mutants' index in `INDEX.json`'s exact shape; `mutations[]` is the edit descriptors. Everything that *states* a mutant's base or its edit is here | **scoring-only** |

**The one change `exam/` has to make, and why I did not make it.**
`exam/guard.py:generated_worlds()` admits a generated id iff it is a row in
`INDEX.json`, so putting the mutants there was the obvious move and this section
originally claimed it as done and free. It is not free: it breaks **five tests
in `exam/`** —

```
FAILED test_the_factory_has_been_built                        assert 35 == 20
FAILED test_the_matrix_covers_every_world_and_says_so         assert 35 == 20
FAILED test_every_world_has_matched_rule_mixes[v-ce732813]
FAILED test_the_tag_is_close_to_uninformative...[v-ce732813]
FAILED test_the_marker_is_calibrated_on_every_world[v-ce732813]
```

— because `exam/` asserts the roster is exactly twenty, and offers every row to
`heldout_worldgen.build_for`, which raises on `v-ce732813`'s three reachable
states. Found by an adversarial review, not by me; `worldgen`'s own 412 tests
were green throughout, and the damage was entirely across the boundary the item
told me not to cross. So the mutants stay out of `INDEX.json`, their roster
ships beside them in the same shape, and admitting them is one line in
`exam/guard.py` plus a decision about which mutants a paper builder should be
offered — both of which are `exam/`'s to make. `exam/tests/test_worldgen_papers.py`
is back to 95 passed.

`MUTATIONS.json`, per mutation (`schema_version: worldgen/mutations/v0.2`):

```
variant_id            opaque handle, `v-<sha256(base|operators)[:8]>`
base_world_id         the catalogue world it was cut from
edit_family           forbid_action | change_guard
                      | reversible_to_irreversible | move_portal_exit
edit_family_agrees    the family label checked against operators + measurement
operators             [{op: set_prop|forbid_action|move_entity, ...}]
transparent_name      scoring-only; the phrase an item must never print
justification         scoring-only prose
leak_probes           every string whose appearance on a sheet gives it away
changes               {transition_function, initial_state} — both measured

detection             earliest_actions          int | null   ← 检测延迟
                      earliest_witness          the action sequence, replayable
                      observationally_equivalent
                      search_complete
                      first_divergent_rules     {base, mutant}
                      streams{base_raw_trace, base_optimal_plan}
                                                {index, n_actions, complete}

collateral            rules_falsified           [rule names]  ← 连带作废
                      rule_pairs_forward/backward
                      claims_now_false, claims_to_reexamine
                      claims_added, claims_removed
                      rule_witness_changes      {rule: {base, mutant}}
                      verdict, base_verdict, verdict_flipped
                      optimal_length, reachable_states, reversibility_score

repair                divergent_observations, divergent_share  ← 修复成本
                      greedy_witness_budget   int | null
                      greedy_actions_before_stall, stalled_on
                      classes_total, classes_witnessable_in_mutant,
                      classes_only_in_base
                      miner_measured  = null, with its blocker named
```

`greedy_witness_budget` is `null` when **no** walk in the mutated world
witnesses every class the edit created — `v-eb4c5810` forbids `UP` in a world
whose cycler phase is absorbing at `open_phase`, so two of its classes are
individually reachable and jointly not. That case used to break out of the
greedy loop and publish the truncated count as an upper bound on the optimal,
which bounded nothing.

Plus, once per base world, `claim_dependencies[<base>]` — the **claim→rule
dependency graph** `GAPS.md` names as missing and `ground_truth.json` does not
have. `exam/papers/adaptation.py` gets it from `[depends: …]` annotations a
human wrote into A0's manual; nothing generated has those, so this computes
them. Its method and its known over-approximation are in
`mutate.claim_dependencies.__doc__`.

Field names for the three metrics follow `battery/model.py`'s vocabulary where
one existed (`detection_actions`, `repair_actions`, `invalidated_theorems`) —
matching it costs nothing and the battery's M4/M5/M6 read the same shapes.

**Two properties `exam.papers.adaptation.build()` refuses to ship a paper
without, both present and both labelled:**

* an **undetectable** variant — `v-ab7a7d57`, `t2-switch-push` with a net
  relabelled at both ends. A genuine rule-table change with provably no
  observable consequence: `test_the_undetectable_variant_is_undetectable_on_the_whole_graph`
  checks it by walking both reachable sets rather than by trusting the number
  that claims it;
* a **verdict flip**, in both directions: `t2-unsolvable-nodoor` → solvable
  (`v-57cfb2b4`), and three solvable worlds → unsolvable (`v-707a64ad`,
  `v-ce732813`, `v-d2c2b1b9`).

`v-707a64ad` / `v-d2c2b1b9` are the shape GAPS.md asks for by name — *"near-twin
solvable/unsolvable pairs on the same board so that board identity carries no
signal"*. Their boards are byte-identical to `t1-switch-toggle`'s and
`t1-switch-latch`'s and nothing in any frame distinguishes them until the switch
is thrown.

## The knob layer, and what GAPS.md got right and wrong

GAPS.md diagnosed the blockage as *"semantics live in mechanism classes'
`interact()` bodies; push distance is one cell because `mechanisms/push.py` says
so in code, not because a parameter says so."* That is exactly right about push
and mostly wrong about everything else. `switch.mode`, `door.polarity`,
`door.net`, `switch.net`, `lock.k`, `cycler.open_phase`, `cycler.phase0`,
`portal.mode` and `portal.dest` are all read out of `Entity.props` at the
decision point on every call. What was missing was not a parameterisation but a
**declaration** of one: nothing said which props are semantic, what their
domains are, or which mechanism reads them, so nothing could enumerate the legal
edits.

`mutate.KNOBS` is that declaration and it is not prose:
`tests/test_mutate.py::test_every_declared_knob_is_read_by_its_mechanism`
perturbs each one on a world that carries it and requires the transition
function or the initial state to move. One knob is exempt — `portal.pair`,
because every catalogue world has exactly one pair, so the only edit the
validator admits is relabelling both mouths, which is a gauge transformation.
The exemption is itself a test rather than a note: `test_the_unexercisable_knobs_reason_is_itself_checked`
asserts the relabel changes nothing, and starts failing the day a four-mouth
world ships.

**Exactly one knob is genuinely new**: `flags["forbidden_action"]`, read by
`GridWorld.explain` before the grid is consulted, because forbidding a command
is the one edit in the item's list no entity prop can express. It is absent from
all twenty catalogue worlds, and their artefacts are byte-identical either side
of it — `git diff` touches no file under `out/worlds/t*/`.

Two details of it are load-bearing. The check comes **first**, ahead of the
bounds test, so `action_forbidden` and `blocked_by_wall` cannot fight over the
same transition and the tag a transition carries does not depend on where the
agent happens to stand. And the two are **observationally identical** — same
frame, different tag — which is what makes the detection latency of a forbidden
action non-trivial: `v-7048ee5e` is not detectable at action 1 from a start cell
whose UP is a wall, and measures 2.

`truth.base_rules` rewrites `walk` and `blocked_by_wall`'s `when` clauses for
such a world, because they stop being unconditional and `rule_correspondence`
compares names rather than prose — a referee's copy can go wrong in exactly the
direction nothing checks.

## Two gates added, and what they caught

`build.py` builds the mutants through the same `build_world` and judges them
with the same `build.gate_failures`, so four of the five existing gates apply
verbatim and the determinism check covers them. (Five, not six: `GATES` has five
entries and determinism is a sixth check outside it — an earlier draft of this
file wrote "all six build gates **and** the determinism gate", double-counting.)
Two more were needed:

* **the edit-family gate.** `edit_family` is a claim about what an edit *is*,
  and it is compared against what the operators touch and — for
  `reversible_to_irreversible` — against the two measured reversibility stamps.
  `test_the_edit_family_claim_is_checked_against_the_measurement` mislabels a
  real guard change and requires the gate to notice;
* **the mutant solvability gate.** `build.py`'s `solvability_intent_failures`
  reads `spec.intended_solvable`, which a mutant leaves `null` on purpose (see
  §the open spec) — so on a mutant that gate is vacuous, and the check moved
  rather than lapsed: the claim lives in `Edit.intended_solvable` and
  `mutate.mutation_gate_failures` compares it to the exhaustive decision.

The gates caught two of my own predictions in the first run, which is the only
evidence that they are gates. `t1-tokens-lock` with `LEFT` forbidden was
declared unsolvable and is not — the goal never needed the lock — and it also
made `walk_through_lock` dormant, a declared primary rule that never fires.
`t2-cycler-lock` with `open_phase=0` starts open, so `advance_cycler` never
fires at all. Both were replaced rather than exempted.

The family gate's first form was itself defective and an adversarial review
broke it: it counted a rule that merely **stopped existing** in the mutant as a
rule that had lost re-witnessability, so `v-57cfb2b4` — which opens two doors
permanently, retiring `blocked_by_door` and touching nothing about reversibility
— passed as `reversible_to_irreversible`. It now requires a rule that *survives*
into the mutant to lose the property, or a genuinely new single-witness rule;
`test_the_edit_family_claim_is_checked_against_the_measurement` mislabels that
exact variant and requires the gate to notice.

The determinism gate now also diffs `INDEX.json` and `MUTATIONS.json`, which
were outputs nothing compared. `MUTATIONS.json` is computed from two reachable
graphs and a product search and is exactly the shape of artefact where a `set`
reaching an output would hide.

A third hazard, not a gate but the same class: a variant id is a **digest of its
operators**, so revising an operator does not update a directory — it strands
the old one and builds a new one beside it. An orphan is a complete six-file
world published under an id nothing describes and no gate ever judged, and this
run produced two within an hour and would have committed both. `prune_orphans`
deletes them and a test asserts the directory listing equals the corpus.

## The open spec — how much the leak discipline actually buys

Less than the first version of this file claimed, and the difference is worth
stating exactly rather than reassuringly.

**What was fixed.** `spec.json` is classified **open**
(`exam/papers/worldgen_port.py:64`) and every catalogue world's copy carries
`"intended_solvable": true|false` — for `t2-unsolvable-nodoor`, the literal
answer to a verdict item. It has no functional role, so a mutant's is `null` and
the claim travels in `MUTATIONS.json` instead, with the gate that checks it
moved rather than dropped. `variant_of`, `variant_delta` and `notes` are blank
for the same reason. And **`seed`**, which was not: it is copied verbatim by
`_replace`'s defaults, it is unique across the twenty, and matching it against
the open catalogue specs identified the base of all fifteen mutants exactly.
Now `0`, with a test.

**What cannot be fixed, and what the docstring now says instead of denying it.**
A mutant may not move the layout, the start or the goal — that refusal is what
makes the detection latency mean anything — and the base's `spec.json` is open
too. So the geometry identifies the base, and a two-file diff *is* the edit, in
plaintext: `v-7048ee5e` differs from `t1-walk-maze` by
`flags: {} → {"forbidden_action": "UP"}`. `entities[].props` is the rule set in
words for the same reason: `open_world()` rebuilds the `GridWorld` from that
file. There is no version of it that both works and hides this. What the
discipline here buys is that the *id* and the *labels* do not leak, which is
what leaked before (W-1540's incident); it is not a claim that an examinee
handed both specs cannot read off the answer, and `mutate.py`'s docstring and
`test_a_mutants_open_files_carry_no_label_that_names_the_edit` both now say so
in as many words. An earlier draft of that test was named for a check it did not
perform — it opened one of the two open files and never applied its own answer
alphabet to either.

One more, unfixed and only half-verified: a forbidden action shrinks the
reachable set enough that `budget_for`'s 40 % clamps to its floor of 10, so
`v-eb4c5810`'s trace is 10 actions where its base's is 70. `raw_trace.jsonl` is
open and **its length correlates with the edit**. The budget policy is
pre-registered in `core/explorer.py` and moving it to hide a signal would be
worse; recorded here instead.

**The twenty were left alone.** Changing their published format is a decision
about a surface another territory reads, and it is not mine to make silently on
a branch about mutation. Filed to `monitor/inbox/`, along with the observation —
present in the artefacts, *not* verified as reaching a sheet — that
`INDEX.json` is loaded by `worldgen_port.roster()` and carries `solvable` and
`optimal_length` per world.

## The second miss

`worldgen/qc/PREREGISTERED_MUTANTS.md` fixed the sample and the bar before the
harness ran. Measured (`out/qc/QC_MUTANTS.json`):

| variant | family | base | L1/L2/L3a | held-out (mutant vs base) |
|---|---|---|---|---|
| `v-ce732813` | forbid_action | `t1-walk-maze` | ✅ | 0.667 vs **1.000** |
| `v-707a64ad` | change_guard | `t1-switch-toggle` | ✅ | 0.738 vs 0.773 |
| `v-efe43df1` | reversible_to_irreversible | `t2-switch-push` | ❌ raises | — |
| `v-a3446614` | move_portal_exit | `t1-portal-oneway` | ✅ | 0.586 vs 0.548 |

`v-efe43df1` makes the miner raise `NoSeparatingGuard`, and **so does
`t2-switch-push`, its base**, which no previous run had sampled.
`qc/diagnose_miner.py` localises both to the same cause as C1 found for
`t2-lock-fragile`: *"the VOCABULARY is short — the frames differ but no atom
sees the difference."* That is `a0_relational_v1`'s expressiveness, in another
track. Transcripts in the run directory.

The bar was not moved and the sample was not swapped; `pass` stays `false`. What
was added is `base_runs_the_pipeline`, measured and deliberately **not** an input
to the verdict, so a reader can tell the two cases apart without taking my word.
The postscript on `PREREGISTERED_MUTANTS.md` records that the bar's rule 1 was
written absolutely and contradicts the sentence above it, and that the bar is
what is wrong here rather than the mutant.

The interesting number is the one that passed: **`v-ce732813` drops held-out
accuracy from 1.000 to 0.667 on the world with no mechanisms in it at all.**
`t1-walk-maze` is the only world in the catalogue the engine manual gets
perfectly right, and forbidding one direction breaks it — the mined rules cannot
express "this command does nothing, everywhere", so a refusal that looks exactly
like a wall from a frame is unlearnable for that vocabulary. That is the
capability boundary the corpus exists to find, showing up at the cheapest
possible price.

## Gaps — what is not done

1. **修复成本 has no miner-measured number.** `repair.miner_measured` is `null`
   with its blocker named. GAPS.md is right that `engine-rig`'s miner represents
   a two-object sokoban percept and cannot express mechanism state; a repair
   score against a miner that cannot represent the state is not a measurement.
   What ships is the divergent-observation count, the divergent rule-pair
   classes, and a greedy witness budget with **both** its bounds stated — an
   upper bound on the optimal witness budget, a lower bound on a miner's repair
   budget. Not the number the exam grades on.
2. **Three unsolvable mutants, and the verdict paper wants nine.** GAPS.md
   §class-(ii) also needs worlds with ≥10^12 configurations; the largest thing
   here is 2654 states. Neither is closed. The near-twin *pairs* are, which was
   the other half of that blocker.
3. **`reversible_to_irreversible` has no end-to-end pipeline measurement**,
   because the base drawn for it in the pre-registered sample does not run. Not
   worked around; the sample was fixed in advance.
4. **The `move_portal_exit` pair is less discriminating than intended.**
   `v-a3446614` and `v-c52c42ed` move the same exit two and five cells and both
   measure `earliest_actions: 4` — the latency is the walk to the mouth and is
   the same either way. They differ in what happens *at* the divergence, which
   is in `divergence_examples`, not in when it happens.
5. **`cycler.phase0` is an initial-condition edit, not a guard edit.** It is
   filed under `reversible_to_irreversible` and the family check passes on the
   measured stamp (`advance_cycler` 2 → 1), but `changes.transition_function` is
   **false** for it: no rule moved, nothing is falsified, and there is nothing to
   repair. The field exists so a paper cannot conflate it with the two real
   irreversibility edits. Whether it belongs in that family at all is a judgement
   I made and flagged rather than hid.
6. **`v-a3446614` and `v-c52c42ed` are not the contrast they were chosen to
   be**, and neither is `v-379c937f` against `v-efe43df1`. The first pair agrees
   on *every* published field and differs only in where the agent lands, which
   the descriptor records in `divergence_examples` and summarises nowhere. The
   second pair has structurally identical collateral blocks and differs only in
   detection latency (8 against 5). Both are kept and both `justification`
   strings now say what the numbers say instead of what I expected.
7. **The seal still has A0's hole**, one turn further down. I wrote the
   mutation layer, chose the corpus, and computed the metrics that grade it. Two
   independent adversarial subagents audited the measurement code and the leak
   discipline; that is better than nothing and it is not independence.

## What the adversarial pass changed

Kept as a list because the number matters more than the prose: **nine** of the
findings below were defects in shipped artefacts or in claims this file made,
and every one was found by a reviewer with no stake in the code rather than by
the tests I had written for it.

| found | what it was |
|---|---|
| `INDEX.json` admission | five `exam/` tests broken across a boundary the item told me not to cross, while `worldgen`'s own suite stayed green |
| stale rule text | `ground_truth.json` for a forbidden-action world contradicted itself; `rule_correspondence` compares names and is blind to prose, so no gate saw it |
| stalled repair walk | a truncated greedy count published as an upper bound on an optimum that does not exist |
| family check | a rule that stopped existing counted as a rule that lost re-witnessability, so a guard change wore the reversibility label |
| divergence classes | enumerated over the base's reachable set only, so `classes_total` contradicted `rule_pairs_backward` in the same record |
| `seed` | copied from the base, unique across the twenty, and therefore naming the base of all fifteen |
| no-op edits | `_apply_one`'s docstring promised to refuse them and it did not; `move_entity` could relocate a token |
| dependency graph | no row for a claim the edit *created*, so `latch_monotone` could never be re-examined |
| five justifications | prose that overstated, contradicted, or simply misdescribed its own measured numbers |

Two things the same pass **refuted**, which is worth as much: the product-BFS
detection latency was cross-checked against two independent oracles over the
fifteen mutants and seventy fuzzed edits with zero disagreements, and the
claim→rule graph's cross-mechanism blind spot does not exist — no mechanism ever
paints over another's cells in any reachable state of any of the twenty.

## Reproduce

```bash
cd .worktrees/c6-worldgen-mutate
python -m worldgen.verify                    # everything, including both QC stages
python -m worldgen.mutate --knobs            # the declared semantic knobs
python -m worldgen.mutate --list             # the edit corpus
python -m worldgen.qc.run_qc --mutants       # the mutants against their bases
```

---

# RUN_STATE — V12-worldgen-gate-deaf

2026-07-28. Branch `agent/v12-worldgen-gate-deaf`, base commit `77e9216`.
Provenance: `worldgen/runs/20260728T153030Z-V12-worldgen-gate-deaf/`.
Nothing above this line was edited; C1's and C6's records stand as written.

## The complaint, and the part of it that survived checking

A repository-wide negative-control census measured this: `python -m
worldgen.verify` printed the bare token **`green`** and exited **0**, while
`out/qc/QC.json` and `out/qc/QC_MUTANTS.json` both said `pass: false`. The item
asked whether `gating=False` on the two QC stages was deliberate before asking
anyone to change it. **It was deliberate, and the evidence is not ambiguous:**

* `verify.py`'s own docstring said so in words — "Both QC stages are reported and
  neither gates, and that is deliberate rather than convenient" — with the
  reason: a missed pre-registered bar gets published, not lowered;
* it was there in the first commit. `git show 66493f6:worldgen/verify.py` carries
  the same paragraph in the singular; C6 (`9a37d8a`) added the mutants stage and
  deliberately rewrote it into the plural. Two sessions, same call, on purpose;
* `PREREGISTERED.md` fixes the disposition of a miss in advance: "recorded as a
  miss, not re-scored against a lower one";
* **and the red is not this territory's.** `t2-lock-fragile` and `t2-switch-push`
  both make the upstream miner raise `NoSeparatingGuard`; `qc/diagnose_miner.py`
  localised it to `a0_relational_v1`'s vocabulary — the frames differ and all 98
  atoms agree on both. The fix is an atom in `cold-start-a0/`, the other track's
  file. §gaps item 2 already said so and it is still true.

So gating on `pass` was refused. It would leave the world factory permanently red
for a file it is forbidden to edit, and a permanently red gate is one everybody
learns to route around — the census's own pathology, one level up. It would also
promote `PREREGISTERED_MUTANTS.md`'s rule 1 into a hard gate, a rule whose own
postscript says it was mis-specified and should have read "a pipeline **its base
survives**".

**Three things were nevertheless defective**, and they are where the complaint's
shape actually lives:

1. **the word `green`.** The docstring's honesty never reached the surface a
   reader or a CI log sees;
2. **a crash and a measured miss were the same signal.** Both stages were judged
   by `proc.returncode` alone, and `run_qc` returns 1 for an honest miss
   (`run_qc.py:371`, `:435`) exactly as Python returns 1 for an uncaught
   `ImportError`. **The entire QC layer could have stopped executing and this
   command would not have changed a character.** Non-gating was a decision about
   a *measured verdict*; it was never a decision to accept a stage that did not
   run;
3. **nothing pinned the miss**, so "neither stage gates" was implemented as "any
   QC outcome exits 0". A third world could start raising, replay could slide
   from 1.000 to 0.4, a passing mutant could start failing — all green.

## What was built

`worldgen/qc/KNOWN_MISS.json` — hand-written, checked in — transcribes the exact
verdict each QC stage produces today, per stage and per row, with `owner`,
`what_is_red` and `whose_work_it_is` beside each red. `worldgen/qc/gate.py`
compares a stage's artifact against it. `verify.py`'s QC stages now gate on
**deviation from the pin**, in either direction, and on a stage that failed to
rewrite its artifact during the run (mtime stamped before launch — `run_qc`
writes unconditionally on every completed run, so a stale mtime is a death).

Nothing was loosened. `PREREGISTERED.md` and `PREREGISTERED_MUTANTS.md` are
byte-untouched, the 0.90 threshold is still 0.90, both artifacts still say
`pass: false`. Before: every QC outcome exited 0. After: exactly one does, and it
is the one already published. An **improvement** gates too — it means the pin has
become a lie about what ships, and the repair is to re-run QC and transcribe,
never to widen the pin.

Two things are pinned and two are deliberately not. Pinned: the verdict dicts and
the per-world / per-pair L1 / L2 / L3a booleans, because those are what the bars
read. Not pinned: the L3b floats (0.773333, 0.895833, and the mutant/base pairs).
They are the upstream miner's score, this territory can act on neither direction,
and `PREREGISTERED_MUTANTS.md` rule 3 fixed in advance that mutant L3b carries
**no** threshold — pinning it would install the very threshold that file refused.
They are transcribed into `recorded_but_not_pinned` so a human diffing the file
against `QC.json` still sees a drift.

## Where it is red, and whose work that is

**`verify` exits 0 today** — the pin matches, which is what a correct pin does on
the run that produced it. The reds it pins are unchanged and belong upstream:

| stage | red | owner |
|---|---|---|
| `qc_family` | `t2-lock-fragile` raises `NoSeparatingGuard`, sinking all_L1/L2/L3a; no world reaches the pre-registered 0.90 held-out (0.773, 0.896), so `L3b_passed` is 0 of 2 | `cold-start-a0` — an atom in `pipeline/atoms_a0.py`. Filed, §gaps item 2 |
| `qc_mutants` | `v-efe43df1` fails rule 1: the pipeline raises on it | `cold-start-a0`, **not the mutation layer** |

The second row's attribution is the one that will be misread, so it is spelled
out here as well as in the pin: the pipeline **also raises on `t2-switch-push`,
`v-efe43df1`'s base**, measured in the same process by the same harness and
recorded in the artifact as `base_runs_the_pipeline: false`. Same vocabulary
shortfall as `t2-lock-fragile`'s
(`runs/…-C6-worldgen-mutate/diagnose_t2-switch-push.txt`). The mutant did not
break anything. Anyone reading that red as "the variant layer is broken" has read
it backwards. The real consequence is the one §gaps already carries: the
`reversible_to_irreversible` family has no end-to-end pipeline measurement,
because the base drawn for it does not run.

## The negative control, and the proof it is not vacuous

`worldgen/tests/test_verify_qc_gate.py`, modelled on
`figures/check_coverage.py --self-test`. It spawns `python -m worldgen.verify`
and asserts on **the process's exit code**, through the shipped `main()`, the
shipped mtime stamping and the shipped aggregation; only the stage table and the
pin file are substituted, via `--selftest-spec`. Six implanted reds — a world
that starts raising, a stage that reports success while writing a different
verdict, a red that quietly went green, a sample with the failing world deleted,
a stage that dies before writing, and a stage that dies while a *correct* stale
artifact sits on disk — each required to exit non-zero. Plus a **positive
control** requiring the pinned verdict (with the stub exiting 1, as `run_qc`
does) to exit 0, without which "it exits non-zero" would be evidence of nothing.
Plus three tests on the shipped table itself, so a future edit that sets
`stage_key=None` cannot restore the defect and stay green.

The control was then **mutation-tested**: `verify.py` was temporarily reverted to
the pre-V12 semantics and the same seven cases re-run.
`runs/…-V12-…/mutation_check.txt`: **1 of 7 behaved, 6 did not** — every
implanted red exited 0, and six tests failed. Restored, 13 pass. That transcript
is the evidence that the gate can fail, which is the only reason to trust it when
it does not.

The control never invokes the real QC stages and writes only into a temp
directory; `test_out_tree_untouched` hashes `QC.json` and `QC_MUTANTS.json`
before and after and asserts they are byte-identical.

## Measured

```
python -m pytest worldgen/ -q     412 passed, 13 skipped  ->  425 passed, 13 skipped   exit 0
python -m worldgen.verify         exit 0, last line no longer the bare token `green`
```

Full transcripts in `runs/20260728T153030Z-V12-worldgen-gate-deaf/`:
`verify_before.txt`, `verify_after.txt`, `pytest_before.txt`, `pytest_after.txt`,
`negative_control.txt`, `mutation_check.txt`, and the judgment in `JUDGMENT.md`.

## Gaps — what this item did not do

1. **`python -m worldgen.verify` dirties ten committed artifacts** under
   `out/qc/*/` (`candidates.jsonl`, `engines_report.json` — `frontier_size`
   32 → 57 and similar), identically on every run, so it is drift between the
   `cold-start-a0` code state that produced the committed copies and the one on
   disk now, not nondeterminism. `QC.json` and `QC_MUTANTS.json` are byte-stable,
   which is why the pin holds. Diff kept as
   `runs/…-V12-…/out_dirtied_by_verify.diff`; the tree was restored with `git
   checkout`. Not this territory's to fix, and it is *why* the negative control
   must never invoke the real QC stages.
2. **`exam/verify.py:25` says it is "Same shape as `worldgen/verify.py`, and for
   the same reason stated there"**, so defects (1)–(3) above very likely
   replicate in `exam/`. Outside this item's boundary; raised in
   `monitor/inbox/20260728T153030Z-RES-3-worldgen-qc-gate-pinned.md`.
3. **The pin is a transcription made by the same session that wrote the gate.**
   `test_pin_matches_what_the_committed_artifacts_say` keeps it honest against
   the artifacts on disk, which is a consistency check and not independence —
   A0's hole again, one level down.

---

# V16 — the determinism gate had never been shown to go red

`worldgen/build.py`'s `check_determinism` is the strongest determinism claim in
this repository: it rebuilds the catalogue in a **fresh interpreter** at
`PYTHONHASHSEED=271828` and diffs every byte. Two independent censuses (V11,
V14) had flagged it as having no negative control. V14 nonetheless scored
`build.py` as *covered*, because the verdict was **file-level** and other things
in the same file are tested — a function-level blank hidden by a file-level
present. This item is that blank, filled.

Run directory: `worldgen/runs/20260728T172500Z-V16-determinism-has-no-caller/`.

## 1. The premise, measured rather than scanned

Both censuses said "zero test callers" from a static scan. Measured with a
tripwire that raises on entry to `check_determinism`:

* `worldgen/` — 412 passed, 13 skipped, **green**, sentinel file never created.
* `exam/tests/test_worldgen_papers.py` + `theory-compiler/tests/test_count_guard.py`
  (the only other tests that mention `worldgen`) — 110 passed, **green**.
* The tripwire itself was verified live: a direct call raised and wrote the
  sentinel. Without that check the green above would mean nothing, which is the
  failure mode this whole item is about.

**The premise holds.** One correction the scans had missed: the function is not
dead code in *production*. `worldgen/verify.py:42` runs
`python -m worldgen.build --check` as its first, gating stage. Nothing runs
`verify.py` automatically. `test_determinism_gate.py` now pins that wiring, so
dropping `--check` from `verify.STAGES` cannot silently orphan the gate.

## 2. The negative control

`worldgen/tests/determinism_sandbox.py` copies the package source to a temp
root, patches a defect into a generator, and runs the **real command line**
there — `python -m worldgen.build --check <world>` — asserting the process exit
code and the gate's own banner. A sandbox rather than the real tree because the
gate diffs against `build.OUT` and `main` rebuilds it on the way in; running
`--check` in place would rewrite ten committed artefacts, which is a separate
ledger entry. Same move `figures/check_coverage.py --self-test` makes with the
pre-P8 tree.

Twenty tests, `worldgen/tests/test_determinism_gate.py`. Suite is **428 passed,
13 skipped** (was 412/13); `git status worldgen/` clean apart from the new
files; `out/` untouched.

## 3. Two classes of defect, and they are not the same claim

This is the correction that changed what V16 demonstrates, and it came from the
adversarial reviewer rather than from me. `CLAUDE.md` states the requirement as
*"byte-reproducible for a **fixed seed**"*. Measured by building twice at one
seed (`determinism_sandbox.classify`):

| class | injections | at a fixed seed | violates |
|---|---|---|---|
| A | `unseeded_rng`, `wall_clock` | bytes **move** | `CLAUDE.md` as written |
| B | `mechanism_order`, `hash_order_wide` | bytes **do not move** | only the stronger rule the gate enforces |

`mechanism_order` is the shape `build.py`'s own docstring names — `GridWorld`
taking its mechanism order from `set` iteration. **By the charter's literal
wording it is not a violation.** It violates cross-seed stability, which
`CLAUDE.md` never asks for and `check_determinism` demands anyway.

Class B is kept and is the more interesting half — the `shared_hashseed` column
below is the evidence that catching it is worth something. But the first version
of this work asserted all four were "nondeterministic", which is **false** for
class B, and a reader who took `mechanism_order` for a charter violation would
have been told something this repository does not promise. Both halves are now
labelled in the table and pinned by tests. A note proposing `CLAUDE.md` say
which of the two it means has gone to `monitor/inbox/`; changing the charter is
not this item's call.

## 4. The gate is awake — the weakening table

Leave the injection in place, weaken `check_determinism` instead. Every cell is
a **rate over distinct parent seeds**, not a verdict, because two of them are
genuinely probabilistic and the first version of this table published both as
settled facts.

| injection | class | none | shared_hashseed | size_only | no_diff |
|---|---|---|---|---|---|
| `mechanism_order` | B | **RED (25/30 seeds)** | MISSED (0/10) | MISSED (0/10) | MISSED (0/10) |
| `hash_order_wide` | B | **RED** (30/30) | MISSED (0/10) | MISSED (0/10) | MISSED (0/10) |
| `unseeded_rng` | A | **RED** (30/30) | **RED** (10/10) | **RED (5/10 seeds)** | MISSED (0/10) |
| `wall_clock` | A | **RED** (30/30) | **RED** (10/10) | MISSED (0/10) | MISSED (0/10) |

`shared_hashseed` is the gate exactly as it stood before C1's audit finding F7,
and it misses **both** class-B defects: that column is what the fresh-interpreter
rebuild actually buys. Three of these cells are kept as permanent tests.

Two cells are rates and must be read as such. `mechanism_order` on
`t3-latch-maze` binds three mechanisms, so set iteration has six orders and
**one parent seed in six agrees with the gate's hardcoded 271828 and cannot see
the defect at all** — 25 of 30 seeds catch it. `unseeded_rng` under `size_only`
turns on whether two random floats happen to have the same `repr` length —
5 of 10. Prose saying "reproducible rather than guaranteed" is not enough here;
the table is the part that gets copied.

## 5. What this does **not** establish — read this before citing the above

* **The real `check_determinism` still runs against the real catalogue exactly
  zero times, automatically.** All twenty new tests exercise a *source copy in
  a temporary directory*. V16 demonstrated that the gate **can** go red. It did
  not make the gate **run**. Those are different things and the first reads like
  the second.
* **The production `--check` path with no world id has never been reached by any
  test** — the branch that builds the mutants, writes the rosters, runs
  `mutation_gate_failures`, and adds `INDEX.json` and `MUTATIONS.json` to the
  diff pairs. `build.py:266-268` says in its own comment that `MUTATIONS.json`
  is "exactly the shape of artefact where a `set` reaching an output would
  hide". That branch is still uncontrolled. Neither of these is fixed here;
  both are new items.
* The `divergent_artefacts` helper is **implementation-independent, not
  criterion-independent**. It reproduces the gate's five-line diff loop without
  calling it, but by default it is handed the same seed pair the gate hardcodes,
  so it cannot by itself distinguish nondeterminism from a deterministic
  function of the hash seed. That is what `classify` is for.

## 6. What the adversarial pass changed

Nine confirmed findings, every one acted on; the reviewer failed to land a
single bypass against the injections that are constructively bound to go red,
which is the hard evidence that the control is real. The corrections it forced:

| found | what it was |
|---|---|
| the definition | `mechanism_order` and `hash_order_wide` are **not** nondeterministic under `CLAUDE.md`'s written rule; the module docstring's central sentence was false |
| the oracle | `divergent_artefacts` was called "independent" while hardcoding the gate's own seed pair — implementation-independent at best |
| `25/30`, `5/10` | two probabilistic cells published as settled facts, with `PARENT_SEED = "1"` silently sitting in the visible 5/6 |
| `verdict()` | scored on exit code + banner with no `named` requirement, and `build.py:251-253` prints that banner for a *crashed* comparison build — the classifier could score a crash as a catch (measured: 0 crashes in 240 runs, so no published cell was wrong; the hole was real regardless) |
| a wrong fact | `mechanism_order`'s description claimed "the whole trace moves"; `raw_trace.jsonl` is byte-identical, only `ground_truth.json` / `GROUND_TRUTH.md` / `reversibility.json` move — and this run's own first console log had said so |
| a misattributed docstring | the red test credited the banner assertion for ruling out crashes; it is the third assertion that does it |
| the scoreboard | §5 above exists because the reviewer said the report read as if the gate were now running |
| `Elapsed 13.9 s` | a wall-clock number printed in an artefact about byte determinism |

The 25/30 and 5/10 rates above are this session's own re-measurement, not the
reviewer's numbers copied over; 25/30 reproduced its figure exactly and 5/10 is
an independent draw from the same coin.

**The reviewer's full report is not in this run directory.** The harness blocked
the subagent from writing it and its findings reached this session only as the
coordinator's summary; the coordinator holds the verbatim text. What is on disk
here is the reviewer's executable probes, under `adversarial/`. Every finding
above was re-verified against those probes or re-measured directly rather than
transcribed.

---

# Merge of master (64157c1c) into `agent/v12-worldgen-gate-deaf`

2026-07-29, W-1641, board item `S24-merge-conflict-drain`. The branch had sat
undelivered since 2026-07-28 23:59 because `ci_merge` re-flagged the same
conflict every five minutes. Recorded here because two of the three things this
merge touched are corrections to sections above, and those are append-only.

**The textual conflict was one file, `worldgen/RUN_STATE.md`** — V12 and V16 each
appended a top-level section at the same offset. Both kept, ordered by run
timestamp (V12 `20260728T153030Z`, then V16 `20260728T172500Z`). Nothing was
dropped from either side; the merge is a pure 147-line append.

**Two further conflicts were semantic, and git could not see either**, because in
both cases the two sides edited different files:

1. **`verify.STAGES` arity.** V12 widened `Stage` from `(label, command,
   gating)` to a 4-tuple with `stage_key`. V16's
   `test_determinism_gate.py::test_verify_still_runs_the_determinism_gate`
   unpacks three and died with `ValueError: too many values to unpack`. The two
   intents do not contradict — V16 pins that the `--check` wiring still gates,
   which says nothing about `stage_key` — so both are kept and the unpack is now
   `label, command, gating, *_`. `stage_key`'s own invariants stay pinned by
   `test_verify_qc_gate.py::test_every_shipped_qc_stage_is_pinned`, so nothing
   is left unguarded by widening the tuple here. No test was deleted.

2. **The pin went stale in the *improving* direction, which is the case V12
   built the gate to catch.** §gaps item 2 above named the fix for
   `t2-lock-fragile`'s `NoSeparatingGuard` as an atom in
   `cold-start-a0/pipeline/atoms_a0.py`, another track's file. Master contains
   it (`atoms_a0.py` +91 lines, and a new `identity_swap.py`). So
   `t2-lock-fragile` now runs clean — `all_L1`/`all_L2`/`all_L3a` all true, and
   it clears held-out at 0.98773. Eight pinned cells deviated and `verify`
   correctly went red.

   Repaired the way this file already specifies — **re-run QC and transcribe,
   never widen**: `qc_family`'s verdict, its `t2-lock-fragile` row, and the
   `recorded_but_not_pinned` float were re-transcribed from a fresh
   `python -m worldgen.qc.run_qc`, confirmed byte-stable across two consecutive
   runs (`QC.json` sha256 `d6aa04de…6acc0a15` both times). `PREREGISTERED.md` is
   byte-untouched and the 0.90 bar is still 0.90. **The stage is still a MISS**:
   `L3b_passed` is 1 of 2 required and `pass` is still `false`, because
   `t1-switch-toggle` (0.773) and `t1-switch-latch` (0.896) remain under the bar.
   `qc_mutants` did **not** move — `t2-switch-push`, `v-efe43df1`'s base, still
   raises, so that red and its attribution stand exactly as written above.

   The committed `out/qc/QC.json` was regenerated with the documented command
   rather than hand-edited, since
   `test_pin_matches_what_the_committed_artifacts_say` compares the pin against
   it. `QC_MUTANTS.json` was byte-identical and is untouched.

**§gaps item 1 is unchanged and still bites:** the same ten unpinned artefacts
under `out/qc/*/` dirty on every `verify` run, plus a new
`out/qc/t2-lock-fragile/engines_report.json` that only appears now that the
world gets far enough to produce one. Still upstream drift, still not this
territory's; restored with `git checkout` and left uncommitted, as before. Only
the two *pinned* artefacts are tracked against the pin.

Gate after the merge: `python worldgen/verify.py` → **exit 0**, stages
`[ok] [ok] [miss] [miss]`, suite **445 passed, 13 skipped** (V12's 425 and V16's
428 both present). One host note for whoever runs this next: do **not** set
`PYTHONIOENCODING=utf-8` for this suite. The negative-control tests round-trip a
subprocess's stdout, and forcing the child to UTF-8 while the parent still
decodes with this host's GBK default kills the reader thread — four tests fail
with `proc.stdout is None`, which looks like a gate failure and is not one.
