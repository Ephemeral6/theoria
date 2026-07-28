# BUGS — what the battery found, and what it did not

`fuzzlab` may not modify `engine-rig`. Everything here is a report; nothing here
was fixed in place. Reproduce any row with the command beside it.

## Verdict: no engine defect found

500 worlds per engine, six engines, **3000 worlds, 23 invariants, 0 violations,
0 unexplained raises, 80 skipped** (all one documented cause, B1 below).
Campaign seed `0x00005eedc1e4f002`, engine-rig at `0b01f29`. That is a real
result and it is also a weak one, and both halves need saying.

It is real because the invariants are judged by independent oracles, not by the
engines' own checkers — `fuzzlab/oracles/gf2.py` is a separate GF(2) elimination,
`fuzzlab/oracles/search.py` a separate BFS and STRIPS replay — and because the
house rule in `oracles/__init__.py` is that **an oracle may not call the engine
it judges**. Checking `zero_space` with `zero_space.verify` would establish that
the module agrees with itself and nothing more.

It is weak because absence of evidence over one corpus is not a proof, because
three of five generators had to be repaired before the corpus was worth anything
at all (below), and because 23 invariants over six engines is thin. What the run
licenses is: *these particular claims held on these 3000 worlds*.

## The findings are about the generators, not the engines

The first campaign was green too — and it was worthless. An adversarial audit of
the inherited generators (full text in
`runs/20260728T085448Z-E4-property-fuzz/GENERATOR_AUDIT.md`) measured what the
corpus actually contained:

| id | what was wrong | measured before | after repair |
|---|---|---|---|
| **G1** | **`gridworld` could never produce an obstacle.** `_place_obstacles` required that no reachable mover placement land in the obstacle's halo — but the mover is stopped exactly when it is adjacent, so the condition reduced to "the obstacle is unreachable", which a ≤4-cell obstacle in a ≥5×5 grid cannot arrange. | **0 obstacles in 3200 worlds** across five campaign seeds; `mdl_segmenter` saw only single-component frames; `cegis_miner`'s `clear(strip(D))` conjunct was never load-bearing, so only the bounds half of any guard was ever needed | 136/200 worlds carry obstacles, 0 dropped; the segmenter now sees **1–23 tracks** |
| **G2** | **`jumpgraph` was mostly degenerate.** `initial` and `goal_states` were drawn uniformly from all 2ⁿ bit strings with no conditioning on peg count or reachability. | 52.5 % of initial states had **no legal move**; 87.5 % had ≤4 reachable states; only 3 % genuinely solvable; of 70 certificates `lp_potential` issued, **43 were over a one-state reachable set** | 0 single-state worlds, 44/200 solvable, median 4 and mean 7.4 reachable states with a tail past 32 |
| **G3** | `blockworld` drew goals independently of the initial state | 14.7 % of worlds already satisfied at step 0 | goals drawn from unmet literals / unoccupied floors |
| **G4** | `hypset` spent a quarter of the budget on flavours where no action splits anything | 28.5 % undiscriminating, 11 % single-action | reweighted to ~10 %; minimum two actions |

**So the honest reading of the first green run is that it certified nothing**,
and it is recorded that way rather than quietly superseded. The numbers quoted
above are from after the repair.

Ground truth, by contrast, was **honest everywhere** — every carried truth was
independently recomputed with 0 mismatches across all five families, including
`jumpgraph`'s `distance_to_goal` table, which `lp_potential.admissibility_report`
consumes and which would otherwise have validated the engine against itself.

## Capability boundaries observed — reported, not filed as defects

Neither of these is a bug. Both are documented behaviour meeting a corpus that
now actually exercises it, and both are worth the other tracks knowing.

### B1 · the mover merges with an obstacle it touches

`transitions_from_segmentation` raises `ValueError: transition N narrates
['vanish']; only move/none are mined on this fixture`. Cause: the colour-agnostic
component operator merges the mover with an obstacle the instant they are
adjacent, so the merged component narrates as `vanish`+`appear` rather than
`move`. This is the **touching-objects gap** the A0 family has now reported
upstream three times.

Once `gridworld` started producing reachable obstacles this stopped being rare:
it fired on **179 of 500 worlds** (716 raises across four invariants). Retrying
with `split_by_color=True` — the operator that exists for exactly this — recovers
almost all of them, leaving **20 of 500 (4 %)** that neither operator can narrate
as move/none. `fuzzlab/props/cegis_miner.py` therefore tries both operators and
records which one worked, and the residue is the campaign's entire `skipped`
count (80 = 20 worlds × 4 invariants), carrying its reason rather than appearing
as an unexplained raise.

Worth stating plainly: **the default operator cannot mine a world in which the
mover ever touches another object.** For a segmenter aimed at ARC that is a
sharp limit, and it is invisible on any corpus of single-object worlds — which
is what the rig's own fixtures and, until this run, this battery both were.

```bash
python -m fuzzlab.minimize --engine cegis_miner --invariant frontier_guards_are_consistent --kind skipped
```

### B2 · `NoSeparatingGuard` on a coarse vocabulary

Documented and deliberate (`test_contradictory_evidence_is_reported_not_papered_over`):
the fixed five-predicate vocabulary cannot always separate a positive from a
negative. Recorded as `skipped`, never as a violation.

## Two false accusations the battery made about itself

Recorded because a fuzz battery's most likely output is a **false accusation**,
and the only defence is checking the oracle before filing. Both were caught by
reading the first finding rather than the count.

| | reported | actually |
|---|---|---|
| `probe_frontier.entropy_matches_bruteforce` | 120 violations in 120 worlds | the oracle summed class **sizes**; the engine sums `Hypothesis.weight`, and `hypset` draws non-uniform weights. The engine was right every time. |
| `fd_adapter.plan_replays_to_the_goal` | 13 plans "do not execute" | the oracle keyed its action table on `GroundAction.text`, which is a bound method, not a property — so it recognised no action at all. The engine was right every time. |

`fuzzlab/tests/test_oracles.py` now pins both against closed forms.

## What was deliberately not asserted

Writing an invariant against a guarantee nobody made produces a confident, wrong
bug report. These were considered and rejected, each with its source:

* **no frame round-trip from a `Segmentation`.** There is no replay function in
  the rig and a `Segmentation` could not support one — `Track` carries a single
  `color` and no per-frame per-cell colours, and an `appear` event carries only
  `{"at": [r,c]}`. The script is a bit-accounting scheme, not a decodable
  encoding. The strongest true statement is about **occupancy**, and that is
  `masks_partition_the_foreground`;
* **no `script_bits < baseline_bits`.** D-005's threshold is stated against
  Fixture A specifically; on random worlds the script is routinely longer. The
  structural claim is the bit *identity*, and that is what is checked;
* **no completeness for `lp_potential`.** The engine is sound and *explicitly*
  incomplete — D-014 makes the incompleteness a test so it cannot be quietly
  "fixed". The invariant is one-directional: a certificate implies unreachable,
  never the converse. Nor is sharpness asserted: D-008 says `M` is a worst case
  and "admissibility is the requirement, sharpness is not";
* **no optimality for `fd-satisficing`**, which documents itself as
  non-optimal via `Plan.optimal is False`; the check runs only where the plan
  claims optimality;
* **no cegis frontier completeness beyond `rule.frontier_max_size`**, which is
  `min(max(len(cegis_guard), 1), max_frontier_size)` and often 1 — two-literal
  minimal guards are then legitimately absent;
* **no global optimality for `probe_frontier`'s greedy argmax**, which is
  documented as greedy, one bit at a time.

## Standing caveats on this run

1. **Fast Downward is not installed on this machine.** `fd_adapter` fell back to
   `stub-bfs` on every world, so `fd-optimal` and `fd-satisficing` were never
   exercised and the ladder's cross-rung invariant is untested here. Expected,
   not a defect — but it means `fd_adapter`'s coverage is one rung of three.
2. **`blockworld` plans stay short.** The deepest plan seen before the G3 repair
   was 8 actions. Short plans cannot distinguish an optimal planner from a
   satisficing one even when both rungs are available.
3. **`fuzzlab`'s STRIPS parser is the engine's.** Re-implementing a PDDL parser
   would test a parser, not a planner, so `parse_domain`/`parse_problem`/
   `ground_actions` are shared and everything downstream of them is not. If the
   parser is wrong, these three properties inherit the error and report a pass.
4. **One instance wrote the generators, the oracles and the invariants.** The
   adversarial audits were independent agents with no stake in the code, which
   is better than nothing and is not independence.
