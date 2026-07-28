# RUN_STATE — E4-property-fuzz

Worker `W-1610`, 2026-07-28. Branch `agent/e4-property-fuzz`, base commit
`0b01f29`. Provenance: `fuzzlab/runs/20260728T085448Z-E4-property-fuzz/`.

## What the item asked for, and what is here

| goal | state |
|---|---|
| parameterised deterministic random worlds, seeds all recorded | **done** — five families, pure functions of a 64-bit seed, `out/seeds.jsonl` |
| ≥3 invariants per engine, six engines | **done** — 23 invariants (4/4/4/4/3/4) |
| ≥500 worlds through the full battery | **done** — 500 per engine, **3000 worlds**, 0 violations, 0 unexplained raises, 80 skipped with reasons |
| failure cases minimised and archived | **done** — `minimize.py` + `archive/`; the honest limits of the method are stated in its docstring |
| do not modify `engine-rig`; report to `BUGS.md` and `PARTNER_SYNC` | **held** — `rig.py` only puts it on `sys.path`; zero bytes changed |

## The inherited remnant

`agent/e1-property-fuzz` carried an untracked `fuzzlab/` with the PRNG, the rig
bootstrap, the finding types and all five world generators. The infrastructure is
good and was kept — in particular the house rule in `oracles/__init__.py`, **an
oracle may not call the engine it judges**, which is the only thing that makes
this battery worth running. What was missing is everything that does the judging:
`oracles/` held nothing but that docstring, and `props/` nothing but `finding.py`.

## The finding that matters is about the corpus, not the engines

The first campaign was green. It was also worthless, and the two facts are
independent. An adversarial audit of the generators
(`runs/…/GENERATOR_AUDIT.md`) measured what the corpus contained:

* **`gridworld` could never produce an obstacle.** `_place_obstacles` demanded
  that no reachable mover placement land in the obstacle's halo — but the mover
  is stopped precisely when its strip contains an obstacle cell, i.e. when it is
  adjacent, so the condition reduced to "the obstacle is unreachable", which a
  ≤4-cell obstacle in a ≥5×5 grid cannot arrange. Measured: **0 obstacles in
  3200 worlds across five campaign seeds**, every request dropped after 24 doomed
  BFS sweeps. So `mdl_segmenter`'s component finder and bipartite track matcher
  were never exercised at all, and `cegis_miner`'s guard language collapsed —
  with no obstacles the `clear(strip(D))` conjunct is never load-bearing and only
  the bounds half of a guard is ever needed. The acceptance test is now the
  positive one it should always have been (the obstacle must be *witnessed* — some
  reachable anchor actually blocked by it) and the segmenter sees **1–23 tracks**;
* **`jumpgraph` was mostly degenerate.** `initial` and `goal_states` drawn
  uniformly from all 2ⁿ bit strings: 52.5 % of initial states had no legal move,
  87.5 % had ≤4 reachable states, only 3 % were genuinely solvable, and of 70
  certificates `lp_potential` issued **43 were over a one-state reachable set**.
  Now `initial` is drawn from states that can move and goals from states with
  strictly fewer pegs — but **not** conditioned on solvability, because
  unsolvable-but-non-trivial is the case the engine exists for;
* `blockworld` drew goals independently of the initial state (14.7 % already
  solved at step 0) and `hypset` spent 28.5 % of its budget on flavours where no
  action splits anything. Both retuned.

Ground truth, by contrast, was honest everywhere — independently recomputed with
0 mismatches across all five families, including `jumpgraph`'s
`distance_to_goal` table, which `lp_potential.admissibility_report` consumes and
which would otherwise have validated the engine against itself.

## Result

3000 worlds, 23 invariants, **0 violations, 0 unexplained raises**. All 80
`skipped` findings have one cause, recorded in `BUGS.md` as B1.

The one substantive thing the battery learned about the engines: **the
colour-agnostic segmentation operator cannot mine a world in which the mover ever
touches another object.** The merged component narrates as `vanish`+`appear`
rather than `move` and `transitions_from_segmentation` refuses it. That is the
touching-objects gap the A0 family has now reported upstream three times, and it
fired on **179 of 500 worlds** the moment the corpus contained obstacles.
`split_by_color=True` recovers all but 20 of them. It is invisible on any corpus
of single-object worlds — which is what the rig's own fixtures, and this battery
until the repair, both were.

## Two false accusations, recorded rather than quietly fixed

A fuzz battery's most likely output is a false accusation. This one produced two
before it produced anything else, both against engines that were right every
time, both caught by reading the first finding instead of the count:

* `probe_frontier.entropy_matches_bruteforce`, **120 violations in 120 worlds** —
  the oracle summed class *sizes*; the engine sums `Hypothesis.weight`, and
  `hypset` draws non-uniform weights;
* `fd_adapter.plan_replays_to_the_goal`, **13 plans "do not execute"** — the
  oracle keyed its action table on `GroundAction.text`, which is a bound method
  rather than a property, so it recognised no action at all.

`fuzzlab/tests/test_oracles.py` pins both against closed forms. A third
oracle bug — a size metric returning 0 for two of five families, which would have
made the minimiser rank them arbitrarily forever — was caught by
`test_size_metric_is_defined_for_every_family` rather than by inspection.

## Gaps

1. **No Fast Downward on this machine.** `fd_adapter` fell back to `stub-bfs` on
   every world, so two of its three rungs were never exercised and the cross-rung
   ladder invariant is untested here. Expected, not a defect — but `fd_adapter`'s
   coverage is one rung of three and should not be quoted as more.
2. **`blockworld` plans stay short** (deepest 8 before the goal repair). Short
   plans cannot distinguish an optimal planner from a satisficing one even where
   both rungs exist, so gap 1 would not fully close by installing FD.
3. **The PDDL parser is the engine's.** Re-implementing one would test a parser,
   not a planner, so it is shared and everything downstream of it is not. If the
   parser is wrong, `fd_adapter`'s three properties inherit the error and report
   a pass. Stated in `BUGS.md` rather than hidden.
4. **`blockworld`'s abstract domain cannot emit the two best grounder-fuzzing
   corners** — add/delete are constructed disjoint and pre_pos/pre_neg are
   constructed disjoint, so no action both adds and deletes an atom and no
   precondition is contradictory. Not repaired; it is a generator redesign, not a
   tuning.
5. **23 invariants over six engines is thin**, and a green campaign over one
   corpus is not a proof. What this run licenses is exactly: these claims held on
   these 3000 worlds.
6. **One instance wrote the generators, the oracles and the invariants.** The
   audits were independent agents with no stake in the code, which is better than
   nothing and is not independence.

## Reproduce

```bash
cd .worktrees/e4-property-fuzz
python -m fuzzlab.verify        # oracle tests + smoke campaign + engine-rig's own suite
python -m fuzzlab.campaign      # the standing 500-world campaign
```
