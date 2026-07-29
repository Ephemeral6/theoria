# E17 · pre-registration — held-out validation for `zero_space` and `lp_potential`

**Written and committed BEFORE any measurement was taken.** The commit that adds
this file contains no results, no harness output and no table edit citing a
number. `git merge-base --is-ancestor <this commit> <results commit>` must hold;
if it does not, this document is worthless and the numbers below it should be
read as post-hoc.

Nothing in the split rules or the pass criteria may be changed after a hit rate
has been seen. If a rule turns out to be unworkable, the correct action is to
record that fact, stop, and say the number was not obtained — not to re-cut.

---

## 0. What is being measured, and what is not

Every "已测 / verified" cell in `engine-rig` today is verified **on the evidence
that produced the claim**. For `zero_space` this is close to a tautology: the
laws are the GF(2) null space of the observed difference vectors, so
`verify(result, states)` re-checks `a·d = 0` on exactly the `d` that were fed
into the elimination. The `AssertionError` in `zero_space/__init__.py:run` is
therefore near-unfireable by construction. `grep -ril "held_out\|held-out"
engine-rig/engines engine-rig/tools` returns nothing.

This run measures **one** thing: *does a law/certificate fitted on part of the
evidence still hold on the part that was withheld?*

**It does not measure engine correctness, and a miss is not a defect.**

* `zero_space` — `DECISIONS.md` **D-003** states the engine's quantifier is the
  *observed* difference space: fewer observed differences ⇒ a **larger**
  recovered invariant space, still sound with respect to what was seen, weaker
  than ground truth. A held-out miss is that mechanism becoming visible. It says
  "this law does not extrapolate to unseen transitions", not "the engine is
  wrong". Every number below carries that sentence next to it.
* `lp_potential` — the engine is **sound but incomplete** (CLAUDE.md, D-008):
  it never certifies a solvable configuration, but some genuinely unsolvable
  ones admit no linear pagoda. A refusal is silence, not an error, and silence
  is never counted as a miss.

---

## 1. Corpora

Both corpora are generated inside the harness with the rig's own
`common.rng.SplitMix64`; no committed fixture is modified, and no committed
artifact is rewritten. Sealed-pile contact: none. Network: none. API: none.

### Z — `parityworld` (for `zero_space`)

`n` cells, palette `("B", "R")`, each cell always holds exactly one colour. An
*operation* is a fixed subset of cell indices of size `k`; applying it flips
every cell in the subset. The operation set for a world is the `n - k + 1`
contiguous windows of width `k`. `pair_flip` (Fixture B) is the case
`n = 8, k = 2`.

| parameter | values |
|---|---|
| `n` (cells) | 6, 8, 10 |
| `k` (operation width) | 2, 3 |
| `T` (transitions per world) | 60 |
| worlds | 20 per `(n, k)` pair ⇒ **120 worlds** |
| world seed | `0xE17A0000 + 1000*n + 100*k + i`, `i` in `0..19` |

Trajectory construction, per world: the first `len(ops)` actions walk every
operation once in index order (D-003's own fixture rule, kept so that a
*random* split is not silently a *coverage* split), then the remaining actions
are `SplitMix64(seed).below(len(ops))`. The initial state is drawn from the same
generator.

### L — `pegN` (for `lp_potential`)

The `jumpgraph` family `fixtures/peg4.py` already defines, generalised in `n`:
positions `0..n-1`, a move is `(src, over, dst)` with `over = src ± 1`,
`dst = src ± 2`, legal when `src` and `over` hold pegs and `dst` is empty;
applying it clears `src` and `over` and fills `dst`. The full `2^n` state space
is enumerated; BFS from every state gives ground-truth distance to the goal.

| parameter | values |
|---|---|
| `n` (positions) | 4, 5, 6, 7 |
| goal | every single-peg state `g` with `1 <= index(g) <= n-2` |
| initial | every state with `n - 1` pegs, and every state with `n - 2` pegs |
| instances | the full cross product, de-duplicated on `(n, goal, initial)` |

**Harness sanity gate (pre-registered):** for `n = 4`, `goal = "0100"`, the
harness's generated graph must equal `fixtures/peg4.generate()` on `states`,
`move_instances`, `edges`, `distance_to_goal` and `solvable`. If it does not,
the harness is wrong and the run is void.

---

## 2. Splits — the exact cut, fixed here

### Z-S1 · random transition hold-out (70 / 30)

Per world: the `T` transition indices are permuted by a Fisher–Yates shuffle
driven by `SplitMix64(world_seed ^ 0x5115)`. The first `floor(0.7 * T) = 42`
indices are **train**; the remaining 18 are **held out**. Train and test are
disjoint by construction and every transition is in exactly one side.

Fit: `basis = gf2.null_space(train_differences, n_features)`, then the engine's
own `local_laws` / `quotient_basis` / `reduce_modulo` presentation, then the
engine's own `Law` objects. Only the *selection of differences* differs from
`zerospace.analyse`; every other line is the engine's.

**Harness sanity gate (pre-registered):** with train = all `T` transitions, the
harness's basis must equal `zerospace.analyse(states, colors).basis` in all 120
worlds. If it does not, the harness has drifted from the engine and the run is
void.

### Z-S2 · leave-one-operation-out

Per world, per operation `j`: **train** = every transition whose action is not
`j`; **held out** = every transition whose action is `j`. If either side is
empty the `(world, j)` pair is skipped and counted as skipped, not as a hit.

Z-S1 and Z-S2 are **both** pre-registered and **both** will be reported,
whatever they say. They are two equally defensible cuts of the same evidence and
the expectation (§4) is that they disagree sharply. Reporting only the flattering
one would be the exact failure mode this ticket exists to stop.

### L-L1 · leave-one-move-geometry-out

Per instance, per move geometry `m` present in the instance's graph: build
`graph_minus_m` by deleting every edge whose geometry is `m`; run
`solve_certificate(graph_minus_m, initial, goal_states=[goal])`. `None` (HiGHS
proved infeasible) is **silence**, recorded separately and never counted as a
miss. `LpUnavailable` / `CertificateError` are recorded as errors, also not
misses.

### L-L2 · held-out states for the heuristic

For every certificate produced in L-L1, and for every certificate produced on
the **complete** graph, evaluate `h(s)` against ground-truth BFS distance for
every state `s` with a finite distance that is **not** in the fitting
constraints. The fitting constraints touch exactly two state sets: `initial`
(one state) and `goal_states`. Every other state with a finite distance is
held out. That set is the test set.

---

## 3. Metrics and what counts as a hit — fixed here

**`zero_space`, per recovered law:**

* `delta_hit` — `a · d = 0` for **every** held-out difference `d`. This is the
  law's actual content (conservation across a transition) and is the **primary
  reported number**.
* `value_hit` — `a · x = law.value` for **every** state incident to a held-out
  transition. Strictly stronger than `delta_hit`: it also asks whether the
  constant survives, which it need not when the held-out transitions are the
  only path from `x_0` to `x_t`. Reported second.

Rate = hits / laws recovered on the train side. Reported per split, and split
out by `scope` (`cell_local` vs `global`), because a cell-local law is a law
about the encoding and is expected to hold trivially; pooling the two would let
encoding laws inflate the headline.

**`lp_potential`, per certificate produced on a reduced graph:**

* `heldout_inv_closed` — `m.delta(weights) <= 0` for the withheld geometry `m`.
  **Primary reported number.**
* `claim_true` — the certificate's claim ("goal unreachable from `initial`")
  checked against BFS ground truth over the **complete** move set. A certificate
  that survives `check_exactly` on its truncated move list but whose claim is
  false is a **false certificate**, and is reported by name.
* `gate_withholds` — whether `lp_potential.candidates(cert, h, full_graph)`
  returns `[]`, i.e. whether the existing `premises_against_graph` emit gate
  catches it. This is measured so the result credits the guard that already
  exists instead of implying there is none.
* L-L2: `admissibility_violations` — count of held-out states with
  `h(s) > true_distance`.

**Silence is never a miss.** `solve_certificate` returning `None` is tallied in
its own column.

---

## 4. Predictions — recorded so the run can falsify me

1. **Z-S1 `delta_hit` ≈ 100 %.** A 70 % random slice of 60 transitions almost
   certainly still witnesses every operation, so the train difference space has
   the same span as the full one and the recovered laws are identical.
2. **Z-S2 `delta_hit` well below 100 %, and lower for small `|ops|`.** Removing
   an operation entirely shrinks the observed difference space, D-003's
   mechanism; the extra laws that appear are exactly the ones that fail on the
   withheld operation.
3. **Z: `cell_local` laws hit at 100 % under both splits**, because they are
   facts about the encoding, not about the dynamics.
4. **L-L1 `heldout_inv_closed` well below 100 %**, and at least one **false
   certificate**: `check_exactly` iterates `certificate.moves`, so a geometry
   absent from the list is unconstrained in the LP *and* unexamined in the
   re-check at once.
5. **L-L1 `gate_withholds` = 100 % of the unsound cases.**
   `premises_against_graph` re-derives the move list from the graph, so it
   should catch every one — the hole is in `check_exactly`, not at the emit
   boundary, and the report must say so.
6. **L-L2 on complete-graph certificates: 0 violations.** `h`'s admissibility
   follows from `inv_closed` over the complete move set, so held-out states
   should be clean, which would make `lp_potential` the one engine that already
   had a (partial, unlabelled) held-out check.

If prediction 6 holds it is a point *in the engine's favour* and must be
reported as such.

---

## 5. Pass criteria — what makes this run valid, not what makes the engines look good

The run is **valid** iff all of:

1. Both harness sanity gates in §1 and §2 pass.
2. The harness is byte-reproducible: two consecutive runs produce identical
   `results.json` (modulo nothing — the file has no timestamp).
3. Every miss is emitted with a concrete witness (world/instance id, the law's
   support or the certificate's weights, the offending transition index or move
   geometry) so a reader can reproduce it by hand.
4. `python -m pytest engine-rig -q` is run and its real output and exit code are
   recorded, pass or fail.

**There is no hit-rate threshold, and no hit rate can make this run fail.**
Setting one would convert a boundary (D-003, D-008) into a defect, which is the
misreading this pre-registration exists to prevent. The deliverable is the
number and its witnesses.

---

## 6. Sequence

1. Commit this file alone. *(no results exist yet)*
2. Commit the harness.
3. Run it; commit `results.json`, `RESULTS.md`, measured console output.
4. Only then edit `tools/engine_table.py` so `ENGINE_TABLE.md` carries the
   numbers, and regenerate.
5. Adversarial subagent; record its verdict verbatim; correct or record being
   overturned.
