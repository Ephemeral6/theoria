# Audit of the inherited world generators — 2026-07-28

An adversarial read plus 200 generated worlds per family, measured. The verdict
that matters: **the generators are honest and easy, and easy is the failure mode
that makes a green campaign worthless.** Every carried ground truth was
independently recomputed and matched — 0 mismatches across all five families,
including `jumpgraph`'s `distance_to_goal` table, which `lp_potential`'s
admissibility report consumes and which would otherwise have validated the
engine against itself. Every engine accepts every generated world without an
exception. None of that is coverage.

| id | severity | what |
|---|---|---|
| **F1** | critical | **`gridworld` can never produce an obstacle.** `_place_obstacles`' acceptance test demands that no reachable mover placement lands in the obstacle's halo — but the mover is stopped precisely when its strip contains an obstacle cell, i.e. when it is adjacent. Obstacles are ≤4 cells in a grid ≥5×5 so they can never disconnect the free region, and the condition reduces to "the obstacle is unreachable", which this geometry cannot arrange. Measured: **0 obstacles in 3200 worlds across five campaign seeds**; 100 % of draws that asked for one were dropped after 24 doomed BFS retries. So `mdl_segmenter` sees only single-component frames — its component finder and bipartite track matcher are never exercised — and `cegis_miner`'s guard language collapses to its bounds half, because with no obstacles the `clear` conjunct is never load-bearing. |
| **F2** | critical | **`jumpgraph` is mostly degenerate.** `initial` and `goal_states` are drawn uniformly from all 2ⁿ bit strings with no conditioning on peg count or reachability. Measured over 200: **52.5 % have an initial state with no legal move**, 87.5 % have ≤4 reachable states, 36.5 % have goals with *more* pegs than the initial state (unsolvable by a one-line counting argument), and only **3 % are genuinely solvable in ≥1 move**. Of 70 certificates `lp_potential` issued, **43 were over a one-state reachable set** — it proved unsolvability of worlds with no moves. |
| **F3** | high | **`blockworld` never asks the planner to plan.** 14.7 % of worlds are already solved at step 0 (goals drawn independently of the initial state), 65 % have no plan, and the deepest plan in 150 draws was 8 actions — 3 for the abstract flavour. At depths 0–3 an optimal and a satisficing planner are indistinguishable, so the FD ladder distinction the engine stakes its acceptance on is untestable on this corpus. |
| **F4** | medium | `gridworld.spec.portal` is drawn without checking it lies in the mover's reachable set: 26.5 % of worlds carry a portal and in **74 % of those the teleport never fires**, so the spec asserts a rule the trace does not witness. |
| **F5** | medium | `hypset` spends 28.5 % of its budget on worlds where no action splits anything (the `agreeing` and `singleton` flavours). Legitimate as a negative control, indefensible as a quarter of the budget. Also: the `splitting` flavour always forces the split onto `actions[0]`, and 20.5 % of worlds declare observations that appear nowhere in the table. |
| **F6** | medium | `blockworld`'s abstract domain constructs add/delete disjoint and pre_pos/pre_neg disjoint, so it can never emit an action that both adds and deletes an atom, nor a contradictory precondition — the two highest-yield corners for fuzzing a STRIPS grounder are unreachable by construction. |
| **F7–F9** | low | Dead clamps in `parityworld` (`size` bounds that cannot bind; a "used ops" filter that always yields all ops); planted flavour is always k=2 though the palette has 8 symbols; `Rng.subset` silently drops `min_size` when it exceeds the sequence length (latent, no live call site); `hypset` declares two action names it never uses; `derive` is Θ(n²) in the index (0.04 s per family at 500, immaterial). |

**Determinism and stream independence: sound.** 0 collisions over 2500 draws;
per-family bit means all in [0.470, 0.527]; cross-family same-index correlation
|r| ≤ 0.036; lag-1 autocorrelation |r| ≤ 0.032. The families are shifted views of
one splitmix64 cycle, but the shifts are ≳10¹⁹ against a campaign length of 10³,
so overlap is impossible in practice.

**`parityworld` is trustworthy as shipped** — good flavour balance, planted laws
verified conserved on both colours, `breaks_parity` verified to really break
parity in all 31 cases where it is set.

## Consequence for this run

The first campaign passes recorded in this run — `mdl_segmenter` 80 worlds,
`cegis_miner` 40, `probe_frontier` 120, all zero violations — were taken
**before** these findings. Under F1 the first two are uninformative and are not
quoted as evidence of anything. They are re-run after the repair, and only the
post-repair numbers appear in `BUGS.md` and `RUN_STATE.md`.
