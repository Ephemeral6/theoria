# What a proved deadlock is worth

Claim under test — Theoria 1.9: every deadlock proved, the planner speeds up at the same time

## What a later audit moved, before you read any column

These are not this run's conclusions. They are findings from **engine-rig/DEADLOCK_CLAIM.md, branch agent/e7-deadlock-claim-audit** (run `runs/20260728T150713Z-E7-deadlock-claim-audit`) that this artifact is answerable to, carried in `dividend.json` under `prior_audit` so the JSON says them too.

| finding | section | applies to | what it says |
|---|---|---|---|
| `E7-ipdb-withdrawn` | §6, §7b | `fd-optimal/ipdb` | The whole astar(ipdb()) column is measured, not evidence. Its expansion counts move with iPDB's pattern generation and with pdb_max_size by more than the effect under study: far9 78 -> 30 vanishes under two of nine seeds, and swap-passage 454 -> 0 is the guard shrinking the abstraction under the default 2,000,000-entry cap rather than a deadlock dividend. |
| `E7-blind-band` | §1, §7c | `fd-optimal/blind` | The blind band on the far{N} family is -8.7% to -27.1% across far4..far10, not the '10-27%' E2 published; and that band is itself one open list's. Across instances generally the blind dividend runs 0% to 100%. |
| `E7-lmcut-range` | §3c, §4 | `fd-optimal/lmcut` | On lmcut the saving is 0 to -153 expansions (0% to -7.8%), and where the theorems are contained in FD's own delete relaxation it is not pruning at all: the states removed were already evaluated as dead ends and never expanded. The one isolated mechanism is a tightened relaxation raising h on live states. |
| `E7-tiebreak-invariant` | §3c | `tiebreak_sensitivity` | E7 already answered the tie-break objection with a stronger instrument than this one: the count of distinct states with f < C*, which A* must expand under any tie-break rule. This module measures absolute counts under three rules, which establishes the dependence and not its absence. |

## The bundled rung, which takes a pruner

`expansions` is the headline; `seconds` is the weaker number, because the pruner is a Python callable run per generated state and carving the theorems is a cost the blind search never pays. Both are here so neither can stand in for the other.

`net s` is the carve minus what the pruned search saved, on one invoice: **positive means the theorems cost more time than they bought**. It is a wall clock, so it is this machine's afternoon and not a reproducible number — `verify.py` checks orderings and never equality, and neither should a reader.

| instance | family | cells | theorems (1-atom/2-atom) | carve s | exp before | exp after | saved | states cut | blind s | pruned s | saved s | net s | repaid | plan unchanged |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `open4` | committed | 16 | 16 (8/8) | 0.07 | 47 | 47 | 0% | 0 | 0.004 | 0.004 | -0.000 | +0.075 | **no** | yes |
| `open4far` | committed | 16 | 16 (8/8) | 0.07 | 808 | 571 | 29% | 69 | 0.027 | 0.021 | +0.006 | +0.068 | **no** | yes |
| `far4` | solvable | 16 | 16 (8/8) | 0.07 | 808 | 571 | 29% | 69 | 0.027 | 0.021 | +0.006 | +0.068 | **no** | yes |
| `far5` | solvable | 25 | 24 (8/16) | 0.24 | 988 | 869 | 12% | 35 | 0.054 | 0.051 | +0.003 | +0.237 | **no** | yes |
| `far6` | solvable | 36 | 32 (8/24) | 0.64 | 3152 | 2788 | 12% | 78 | 0.248 | 0.232 | +0.016 | +0.625 | **no** | yes |
| `far7` | solvable | 49 | 40 (8/32) | 1.46 | 8003 | 7041 | 12% | 100 | 0.866 | 0.797 | +0.069 | +1.395 | **no** | yes |
| `ringstuck4` | unsolvable | 12 | 2 (2/0) | 0.01 | 44 | 22 | 50% | 2 | 0.002 | 0.002 | +0.000 | +0.011 | **no** | yes |
| `ringstuck5` | unsolvable | 16 | 2 (2/0) | 0.02 | 75 | 45 | 40% | 2 | 0.003 | 0.003 | +0.000 | +0.022 | **no** | yes |
| `ringstuck6` | unsolvable | 20 | 2 (2/0) | 0.04 | 114 | 76 | 33% | 2 | 0.005 | 0.005 | +0.001 | +0.044 | **no** | yes |
| `ringstuck7` | unsolvable | 24 | 2 (2/0) | 0.08 | 161 | 115 | 29% | 2 | 0.008 | 0.007 | +0.001 | +0.081 | **no** | yes |
| `ringstuck8` | unsolvable | 28 | 2 (2/0) | 0.13 | 216 | 162 | 25% | 2 | 0.013 | 0.011 | +0.002 | +0.130 | **no** | yes |

### The zero row — where true theorems buy nothing

DECISIONS **D-020**: the zero row is the informative one. Reporting only the instances where pruning pays would make a conditional result look unconditional, so these rows are in the table above and are named again here.

* **`open4`: 47 → 47 expansions** — 16 true theorems, zero expansions saved, plan unchanged. The search finds its plan before it wanders into a single dead region; pruning pays where the search would otherwise go.

The same instances on Fast Downward's blind control, which is a different search and therefore a second witness rather than a restatement: `open4` under `singleton`, 49 → 49; `open4` under `full`, 49 → 49; `open4` under `indexed`, 49 → 49.

And the zero survives changing Fast Downward's open list: `open4` expands exactly as many states guarded as unguarded under **every** tie-break rule measured below, so the zero is not one ordering's accident.

### The committed fixture against its generated copy

`open4far` ≡ `far4`. The committed fixture and the generated ladder's bottom rung are supposed to be one board. tests/test_bench.py asserts that about the dataclasses; these rows assert it about the measurements, from two different files on disk. Structural columns only -- theorem counts, expansions, task sizes, plan-length deltas. Never a clock.

**Every structural column agrees.** Two files on disk, one written by `fixtures.generate_all` and one by `instances.far_level(4)`, measured through the same pipeline and answering identically — so the ladder above `far4` is standing on the board the deadlock carver's README reasons about, and not on a lookalike.

## The Fast Downward rungs, which do not

No pruning hook, so the theorems are compiled into the task instead (`bench/compile_theorems.py`). `singleton` expresses the corner deadlocks and stays inside STRIPS. `full` adds the pair deadlocks as a `forall`, which FD turns into an axiom -- the two admissible heuristics refuse it. `indexed` is the same pair guard with the quantifier removed for static selectors: pure STRIPS, and they accept it. Every guarded plan below was replayed against the **original** domain by the rig's own validator.

Read `indexed` against `singleton` on the two admissible rows: that is what the pair theorems cost once they can be delivered at all. FD compiles a negative precondition on a fluent into one operator copy per other value of that variable, which is the task-size column blowing up and the reason `lmcut` expands *more* with the pair theorems than without them.

`fd-optimal/blind` is a **control, not a rung** — `choose_tier` never selects it. A\* with a zero heuristic is the bundled BFS in different clothes, so it shows what the theorems are worth to a search that has no other way of knowing a region is dead. Read it against the two rows below it: that difference is the whole finding.

> **Do not read the `fd-optimal/ipdb` rows below as a dividend in either direction.** The whole astar(ipdb()) column is measured, not evidence. Its expansion counts move with iPDB's pattern generation and with pdb_max_size by more than the effect under study: far9 78 -> 30 vanishes under two of nine seeds, and swap-passage 454 -> 0 is the guard shrinking the abstraction under the default 2,000,000-entry cap rather than a deadlock dividend. They are printed because deleting them would hide the artefact rather than label it.

> **And the `fd-optimal/lmcut` rows are smaller than they look.** On lmcut the saving is 0 to -153 expansions (0% to -7.8%), and where the theorems are contained in FD's own delete relaxation it is not pruning at all: the states removed were already evaluated as dead ends and never expanded. The one isolated mechanism is a tightened relaxation raising h on live states.

| instance | guard | theorems carried | rung | exp before | exp after | task size before | task size after | plan delta | honest |
|---|---|---|---|---|---|---|---|---|---|
| `open4` | singleton | 8/16 | fd-optimal/blind | 49 | 49 | 1029 | 869 | 0 | yes |
| `open4` | singleton | 8/16 | fd-optimal/lmcut | 7 | 7 | 1029 | 869 | 0 | yes |
| `open4` | singleton | 8/16 | fd-optimal/ipdb | 7 | 7 | 1029 | 869 | 0 | yes |
| `open4` | singleton | 8/16 | fd-satisficing | 6 | 6 | 1029 | 869 | 0 | yes |
| `open4` | full | 16/16 | fd-optimal/blind | 49 | 49 | 1029 | 981 | 0 | yes |
| `open4` | full | 16/16 | fd-optimal/lmcut | 7 | *refused* | 1029 | -- | -- | -- |
| `open4` | full | 16/16 | fd-optimal/ipdb | 7 | *refused* | 1029 | -- | -- | -- |
| `open4` | full | 16/16 | fd-satisficing | 6 | 7 | 1029 | 981 | 0 | yes |
| `open4` | indexed | 16/16 | fd-optimal/blind | 49 | 49 | 1029 | 4101 | 0 | yes |
| `open4` | indexed | 16/16 | fd-optimal/lmcut | 7 | 8 | 1029 | 4101 | 0 | yes |
| `open4` | indexed | 16/16 | fd-optimal/ipdb | 7 | 7 | 1029 | 4101 | 0 | yes |
| `open4` | indexed | 16/16 | fd-satisficing | 6 | 6 | 1029 | 4101 | 0 | yes |
| `open4far` | singleton | 8/16 | fd-optimal/blind | 837 | 610 | 1029 | 869 | 0 | yes |
| `open4far` | singleton | 8/16 | fd-optimal/lmcut | 23 | 22 | 1029 | 869 | 0 | yes |
| `open4far` | singleton | 8/16 | fd-optimal/ipdb | 12 | 12 | 1029 | 869 | 0 | yes |
| `open4far` | singleton | 8/16 | fd-satisficing | 95 | 108 | 1029 | 869 | 2 | **no** |
| `open4far` | full | 16/16 | fd-optimal/blind | 837 | 574 | 1029 | 981 | 0 | yes |
| `open4far` | full | 16/16 | fd-optimal/lmcut | 23 | *refused* | 1029 | -- | -- | -- |
| `open4far` | full | 16/16 | fd-optimal/ipdb | 12 | *refused* | 1029 | -- | -- | -- |
| `open4far` | full | 16/16 | fd-satisficing | 95 | 40 | 1029 | 981 | -26 | yes |
| `open4far` | indexed | 16/16 | fd-optimal/blind | 837 | 574 | 1029 | 4101 | 0 | yes |
| `open4far` | indexed | 16/16 | fd-optimal/lmcut | 23 | 34 | 1029 | 4101 | 0 | yes |
| `open4far` | indexed | 16/16 | fd-optimal/ipdb | 12 | 12 | 1029 | 4101 | 0 | yes |
| `open4far` | indexed | 16/16 | fd-satisficing | 95 | 111 | 1029 | 4101 | 0 | yes |
| `far4` | singleton | 8/16 | fd-optimal/blind | 837 | 610 | 1029 | 869 | 0 | yes |
| `far4` | singleton | 8/16 | fd-optimal/lmcut | 23 | 22 | 1029 | 869 | 0 | yes |
| `far4` | singleton | 8/16 | fd-optimal/ipdb | 12 | 12 | 1029 | 869 | 0 | yes |
| `far4` | singleton | 8/16 | fd-satisficing | 95 | 108 | 1029 | 869 | 2 | **no** |
| `far4` | full | 16/16 | fd-optimal/blind | 837 | 574 | 1029 | 981 | 0 | yes |
| `far4` | full | 16/16 | fd-optimal/lmcut | 23 | *refused* | 1029 | -- | -- | -- |
| `far4` | full | 16/16 | fd-optimal/ipdb | 12 | *refused* | 1029 | -- | -- | -- |
| `far4` | full | 16/16 | fd-satisficing | 95 | 40 | 1029 | 981 | -26 | yes |
| `far4` | indexed | 16/16 | fd-optimal/blind | 837 | 574 | 1029 | 4101 | 0 | yes |
| `far4` | indexed | 16/16 | fd-optimal/lmcut | 23 | 34 | 1029 | 4101 | 0 | yes |
| `far4` | indexed | 16/16 | fd-optimal/ipdb | 12 | 12 | 1029 | 4101 | 0 | yes |
| `far4` | indexed | 16/16 | fd-satisficing | 95 | 111 | 1029 | 4101 | 0 | yes |
| `far5` | singleton | 8/24 | fd-optimal/blind | 958 | 872 | 1815 | 1655 | 0 | yes |
| `far5` | singleton | 8/24 | fd-optimal/lmcut | 30 | 30 | 1815 | 1655 | 0 | yes |
| `far5` | singleton | 8/24 | fd-optimal/ipdb | 14 | 14 | 1815 | 1655 | 0 | yes |
| `far5` | singleton | 8/24 | fd-satisficing | 59 | 26 | 1815 | 1655 | -8 | yes |
| `far5` | full | 24/24 | fd-optimal/blind | 958 | 839 | 1815 | 1847 | 0 | yes |
| `far5` | full | 24/24 | fd-optimal/lmcut | 30 | *refused* | 1815 | -- | -- | -- |
| `far5` | full | 24/24 | fd-optimal/ipdb | 14 | *refused* | 1815 | -- | -- | -- |
| `far5` | full | 24/24 | fd-satisficing | 59 | 75 | 1815 | 1847 | 0 | yes |
| `far5` | indexed | 24/24 | fd-optimal/blind | 958 | 1159 | 1815 | 12111 | 0 | yes |
| `far5` | indexed | 24/24 | fd-optimal/lmcut | 30 | 37 | 1815 | 12111 | 0 | yes |
| `far5` | indexed | 24/24 | fd-optimal/ipdb | 14 | 14 | 1815 | 12111 | 0 | yes |
| `far5` | indexed | 24/24 | fd-satisficing | 59 | 29 | 1815 | 12111 | -6 | yes |
| `far6` | singleton | 8/32 | fd-optimal/blind | 3070 | 2762 | 2813 | 2653 | 0 | yes |
| `far6` | singleton | 8/32 | fd-optimal/lmcut | 47 | 47 | 2813 | 2653 | 0 | yes |
| `far6` | singleton | 8/32 | fd-optimal/ipdb | 18 | 18 | 2813 | 2653 | 0 | yes |
| `far6` | singleton | 8/32 | fd-satisficing | 111 | 111 | 2813 | 2653 | 0 | yes |
| `far6` | full | 32/32 | fd-optimal/blind | 3070 | 2706 | 2813 | 2925 | 0 | yes |
| `far6` | full | 32/32 | fd-optimal/lmcut | 47 | *refused* | 2813 | -- | -- | -- |
| `far6` | full | 32/32 | fd-optimal/ipdb | 18 | *refused* | 2813 | -- | -- | -- |
| `far6` | full | 32/32 | fd-satisficing | 111 | 36 | 2813 | 2925 | -8 | yes |
| `far6` | indexed | 32/32 | fd-optimal/blind | 3070 | 3034 | 2813 | 26253 | 0 | yes |
| `far6` | indexed | 32/32 | fd-optimal/lmcut | 47 | 66 | 2813 | 26253 | 0 | yes |
| `far6` | indexed | 32/32 | fd-optimal/ipdb | 18 | 18 | 2813 | 26253 | 0 | yes |
| `far6` | indexed | 32/32 | fd-satisficing | 111 | 40 | 2813 | 26253 | -10 | yes |
| `far7` | singleton | 8/40 | fd-optimal/blind | 7196 | 6365 | 4023 | 3863 | 0 | yes |
| `far7` | singleton | 8/40 | fd-optimal/lmcut | 69 | 68 | 4023 | 3863 | 0 | yes |
| `far7` | singleton | 8/40 | fd-optimal/ipdb | 21 | 21 | 4023 | 3863 | 0 | yes |
| `far7` | singleton | 8/40 | fd-satisficing | 134 | 134 | 4023 | 3863 | 0 | yes |
| `far7` | full | 40/40 | fd-optimal/blind | 7196 | 6272 | 4023 | 4215 | 0 | yes |
| `far7` | full | 40/40 | fd-optimal/lmcut | 69 | *refused* | 4023 | -- | -- | -- |
| `far7` | full | 40/40 | fd-optimal/ipdb | 21 | *refused* | 4023 | -- | -- | -- |
| `far7` | full | 40/40 | fd-satisficing | 134 | 56 | 4023 | 4215 | -10 | yes |
| `far7` | indexed | 40/40 | fd-optimal/blind | 7196 | 7033 | 4023 | 47967 | 0 | yes |
| `far7` | indexed | 40/40 | fd-optimal/lmcut | 69 | 111 | 4023 | 47967 | 0 | yes |
| `far7` | indexed | 40/40 | fd-optimal/ipdb | 21 | 21 | 4023 | 47967 | 0 | yes |
| `far7` | indexed | 40/40 | fd-satisficing | 134 | 43 | 4023 | 47967 | -10 | yes |
| `ringstuck4` | singleton | 2/2 | fd-optimal/blind | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck4` | singleton | 2/2 | fd-optimal/lmcut | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck4` | singleton | 2/2 | fd-optimal/ipdb | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck4` | singleton | 2/2 | fd-satisficing | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck5` | singleton | 2/2 | fd-optimal/blind | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck5` | singleton | 2/2 | fd-optimal/lmcut | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck5` | singleton | 2/2 | fd-optimal/ipdb | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck5` | singleton | 2/2 | fd-satisficing | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck6` | singleton | 2/2 | fd-optimal/blind | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck6` | singleton | 2/2 | fd-optimal/lmcut | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck6` | singleton | 2/2 | fd-optimal/ipdb | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck6` | singleton | 2/2 | fd-satisficing | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck7` | singleton | 2/2 | fd-optimal/blind | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck7` | singleton | 2/2 | fd-optimal/lmcut | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck7` | singleton | 2/2 | fd-optimal/ipdb | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck7` | singleton | 2/2 | fd-satisficing | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck8` | singleton | 2/2 | fd-optimal/blind | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck8` | singleton | 2/2 | fd-optimal/lmcut | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck8` | singleton | 2/2 | fd-optimal/ipdb | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck8` | singleton | 2/2 | fd-satisficing | 0 | 0 | 4 | 4 | -- | n/a |

**Zero expansions before *and* after on `ringstuck4`, `ringstuck5`, `ringstuck6`, `ringstuck7`, `ringstuck8`.** Fast Downward's translator settles those instances during relaxed reachability and the search never starts, so there is no search for a deadlock theorem to shorten. The task size of 4 in those rows is the degenerate task the translator emits once it has decided.

## The Fast Downward wall clock, with carving on the invoice

The three raw clocks per row are in `dividend.json` under `timing`; this is the subtraction, charged against **`search_seconds`**.

`search s` is what Fast Downward's search cost — the only clock a deadlock theorem can move, because a theorem removes transitions from the search and nothing else. `end-to-end` is ~150 ms of driver startup on every row of this batch; not a clock any theorem can move, and not the invoice.

`net s` = carve − search saved. **Positive means the carve was not repaid.** `solves to repay` is how many times this exact instance would have to be re-solved from the same theorems before it was; `--` where the guard saved nothing or cost time, because no number of repeats repays a carve out of a saving that is zero or negative.

**Where `search ms saved` is under a millisecond, `solves to repay` is arithmetic on clock noise.** FD prints its search time to four decimal places and these searches take tenths of a millisecond, so a four- or five-figure repayment count on such a row means "not in any number of solves anybody would run", not a schedule. It is printed rather than blanked because the threshold at which it stops being noise is a judgement, and hiding the number would make that judgement for the reader.

Every figure in this table is a wall clock and therefore this machine's afternoon. `verify.py` checks that clocks are present and correctly nested and never compares one for equality; read the signs and the orders of magnitude, not the digits.

| instance | guard | rung | search ms before | search ms after | search ms saved | carve s | net s | repaid | solves to repay | end-to-end ms before | end-to-end ms after |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `open4` | singleton | fd-optimal/blind | 0.2 | 0.2 | -0.0 | 0.07 | +0.075 | **no** | -- | 163.4 | 163.8 |
| `open4` | singleton | fd-optimal/lmcut | 0.3 | 0.3 | 0.0 | 0.07 | +0.075 | **no** | 2197 | 167.2 | 167.1 |
| `open4` | singleton | fd-optimal/ipdb | 0.1 | 0.1 | 0.0 | 0.07 | +0.075 | **no** | -- | 261.8 | 253.3 |
| `open4` | singleton | fd-satisficing | 0.1 | 0.2 | -0.0 | 0.07 | +0.075 | **no** | -- | 166.6 | 165.6 |
| `open4` | full | fd-optimal/blind | 0.2 | 0.2 | -0.0 | 0.07 | +0.075 | **no** | -- | 163.4 | 168.9 |
| `open4` | full | fd-optimal/lmcut | 0.3 | *refused* | -- | 0.07 | -- | -- | -- | 167.2 | 162.8 |
| `open4` | full | fd-optimal/ipdb | 0.1 | *refused* | -- | 0.07 | -- | -- | -- | 261.8 | 161.0 |
| `open4` | full | fd-satisficing | 0.1 | 0.2 | -0.0 | 0.07 | +0.075 | **no** | -- | 166.6 | 167.4 |
| `open4` | indexed | fd-optimal/blind | 0.2 | 0.2 | 0.0 | 0.07 | +0.075 | **no** | 12449 | 163.4 | 188.4 |
| `open4` | indexed | fd-optimal/lmcut | 0.3 | 0.5 | -0.2 | 0.07 | +0.075 | **no** | -- | 167.2 | 191.4 |
| `open4` | indexed | fd-optimal/ipdb | 0.1 | 0.1 | 0.0 | 0.07 | +0.075 | **no** | 8300 | 261.8 | 296.4 |
| `open4` | indexed | fd-satisficing | 0.1 | 0.1 | -0.0 | 0.07 | +0.075 | **no** | -- | 166.6 | 193.8 |
| `open4far` | singleton | fd-optimal/blind | 1.3 | 0.9 | 0.4 | 0.07 | +0.073 | **no** | 186 | 171.9 | 167.5 |
| `open4far` | singleton | fd-optimal/lmcut | 0.8 | 0.7 | 0.1 | 0.07 | +0.073 | **no** | 591 | 168.8 | 166.2 |
| `open4far` | singleton | fd-optimal/ipdb | 0.2 | 0.1 | 0.0 | 0.07 | +0.073 | **no** | 3053 | 533.5 | 427.8 |
| `open4far` | singleton | fd-satisficing | 0.7 | 0.7 | -0.0 | 0.07 | +0.073 | **no** | -- | 168.6 | 172.8 |
| `open4far` | full | fd-optimal/blind | 1.3 | 1.1 | 0.1 | 0.07 | +0.073 | **no** | 528 | 171.9 | 171.0 |
| `open4far` | full | fd-optimal/lmcut | 0.8 | *refused* | -- | 0.07 | -- | -- | -- | 168.8 | 170.7 |
| `open4far` | full | fd-optimal/ipdb | 0.2 | *refused* | -- | 0.07 | -- | -- | -- | 533.5 | 164.1 |
| `open4far` | full | fd-satisficing | 0.7 | 0.3 | 0.3 | 0.07 | +0.073 | **no** | 216 | 168.6 | 167.6 |
| `open4far` | indexed | fd-optimal/blind | 1.3 | 0.8 | 0.4 | 0.07 | +0.073 | **no** | 177 | 171.9 | 190.6 |
| `open4far` | indexed | fd-optimal/lmcut | 0.8 | 2.1 | -1.3 | 0.07 | +0.075 | **no** | -- | 168.8 | 191.9 |
| `open4far` | indexed | fd-optimal/ipdb | 0.2 | 0.1 | 0.0 | 0.07 | +0.073 | **no** | 1787 | 533.5 | 473.4 |
| `open4far` | indexed | fd-satisficing | 0.7 | 1.2 | -0.5 | 0.07 | +0.074 | **no** | -- | 168.6 | 191.9 |
| `far4` | singleton | fd-optimal/blind | 1.2 | 0.9 | 0.2 | 0.07 | +0.074 | **no** | 299 | 166.4 | 165.0 |
| `far4` | singleton | fd-optimal/lmcut | 0.8 | 0.7 | 0.1 | 0.07 | +0.074 | **no** | 675 | 163.8 | 163.9 |
| `far4` | singleton | fd-optimal/ipdb | 0.1 | 0.2 | -0.0 | 0.07 | +0.074 | **no** | -- | 526.1 | 422.8 |
| `far4` | singleton | fd-satisficing | 0.7 | 0.7 | -0.0 | 0.07 | +0.074 | **no** | -- | 167.9 | 168.4 |
| `far4` | full | fd-optimal/blind | 1.2 | 1.2 | 0.0 | 0.07 | +0.074 | **no** | 3093 | 166.4 | 164.2 |
| `far4` | full | fd-optimal/lmcut | 0.8 | *refused* | -- | 0.07 | -- | -- | -- | 163.8 | 160.9 |
| `far4` | full | fd-optimal/ipdb | 0.1 | *refused* | -- | 0.07 | -- | -- | -- | 526.1 | 167.0 |
| `far4` | full | fd-satisficing | 0.7 | 0.3 | 0.3 | 0.07 | +0.074 | **no** | 218 | 167.9 | 173.7 |
| `far4` | indexed | fd-optimal/blind | 1.2 | 0.8 | 0.4 | 0.07 | +0.074 | **no** | 194 | 166.4 | 187.5 |
| `far4` | indexed | fd-optimal/lmcut | 0.8 | 2.1 | -1.3 | 0.07 | +0.076 | **no** | -- | 163.8 | 187.8 |
| `far4` | indexed | fd-optimal/ipdb | 0.1 | 0.1 | -0.0 | 0.07 | +0.074 | **no** | -- | 526.1 | 464.8 |
| `far4` | indexed | fd-satisficing | 0.7 | 1.3 | -0.6 | 0.07 | +0.075 | **no** | -- | 167.9 | 189.1 |
| `far5` | singleton | fd-optimal/blind | 1.4 | 1.3 | 0.1 | 0.24 | +0.239 | **no** | 3107 | 172.0 | 171.3 |
| `far5` | singleton | fd-optimal/lmcut | 1.9 | 1.8 | 0.2 | 0.24 | +0.239 | **no** | 1408 | 172.4 | 171.7 |
| `far5` | singleton | fd-optimal/ipdb | 0.2 | 0.2 | -0.0 | 0.24 | +0.239 | **no** | -- | 978.9 | 924.9 |
| `far5` | singleton | fd-satisficing | 0.6 | 0.3 | 0.3 | 0.24 | +0.239 | **no** | 828 | 173.4 | 172.2 |
| `far5` | full | fd-optimal/blind | 1.4 | 2.0 | -0.6 | 0.24 | +0.240 | **no** | -- | 172.0 | 175.8 |
| `far5` | full | fd-optimal/lmcut | 1.9 | *refused* | -- | 0.24 | -- | -- | -- | 172.4 | 168.5 |
| `far5` | full | fd-optimal/ipdb | 0.2 | *refused* | -- | 0.24 | -- | -- | -- | 978.9 | 167.1 |
| `far5` | full | fd-satisficing | 0.6 | 0.8 | -0.2 | 0.24 | +0.239 | **no** | -- | 173.4 | 175.2 |
| `far5` | indexed | fd-optimal/blind | 1.4 | 1.7 | -0.3 | 0.24 | +0.239 | **no** | -- | 172.0 | 238.3 |
| `far5` | indexed | fd-optimal/lmcut | 1.9 | 7.3 | -5.3 | 0.24 | +0.245 | **no** | -- | 172.4 | 241.3 |
| `far5` | indexed | fd-optimal/ipdb | 0.2 | 0.2 | -0.0 | 0.24 | +0.239 | **no** | -- | 978.9 | 1104.1 |
| `far5` | indexed | fd-satisficing | 0.6 | 0.8 | -0.2 | 0.24 | +0.239 | **no** | -- | 173.4 | 250.6 |
| `far6` | singleton | fd-optimal/blind | 4.8 | 4.1 | 0.7 | 0.64 | +0.640 | **no** | 937 | 186.5 | 182.5 |
| `far6` | singleton | fd-optimal/lmcut | 4.1 | 3.9 | 0.2 | 0.64 | +0.640 | **no** | 2993 | 184.5 | 184.1 |
| `far6` | singleton | fd-optimal/ipdb | 0.3 | 0.2 | 0.0 | 0.64 | +0.640 | **no** | 14895 | 1772.5 | 1718.7 |
| `far6` | singleton | fd-satisficing | 1.2 | 1.2 | 0.0 | 0.64 | +0.640 | **no** | 20660 | 183.0 | 184.4 |
| `far6` | full | fd-optimal/blind | 4.8 | 7.1 | -2.3 | 0.64 | +0.643 | **no** | -- | 186.5 | 193.9 |
| `far6` | full | fd-optimal/lmcut | 4.1 | *refused* | -- | 0.64 | -- | -- | -- | 184.5 | 176.7 |
| `far6` | full | fd-optimal/ipdb | 0.3 | *refused* | -- | 0.64 | -- | -- | -- | 1772.5 | 179.6 |
| `far6` | full | fd-satisficing | 1.2 | 0.6 | 0.6 | 0.64 | +0.640 | **no** | 1070 | 183.0 | 187.9 |
| `far6` | indexed | fd-optimal/blind | 4.8 | 4.8 | 0.0 | 0.64 | +0.640 | **no** | 25619 | 186.5 | 325.0 |
| `far6` | indexed | fd-optimal/lmcut | 4.1 | 28.7 | -24.6 | 0.64 | +0.665 | **no** | -- | 184.5 | 353.1 |
| `far6` | indexed | fd-optimal/ipdb | 0.3 | 0.2 | 0.1 | 0.64 | +0.640 | **no** | 10856 | 1772.5 | 2143.0 |
| `far6` | indexed | fd-satisficing | 1.2 | 2.1 | -0.8 | 0.64 | +0.641 | **no** | -- | 183.0 | 330.4 |
| `far7` | singleton | fd-optimal/blind | 12.5 | 10.3 | 2.1 | 1.46 | +1.463 | **no** | 683 | 207.5 | 205.9 |
| `far7` | singleton | fd-optimal/lmcut | 8.6 | 8.2 | 0.4 | 1.46 | +1.464 | **no** | 3795 | 212.8 | 205.2 |
| `far7` | singleton | fd-optimal/ipdb | 0.2 | 0.2 | 0.0 | 1.46 | +1.465 | **no** | 162747 | 6449.4 | 6133.6 |
| `far7` | singleton | fd-satisficing | 1.8 | 1.7 | 0.0 | 1.46 | +1.465 | **no** | 30515 | 202.5 | 203.9 |
| `far7` | full | fd-optimal/blind | 12.5 | 18.7 | -6.3 | 1.46 | +1.471 | **no** | -- | 207.5 | 219.3 |
| `far7` | full | fd-optimal/lmcut | 8.6 | *refused* | -- | 1.46 | -- | -- | -- | 212.8 | 231.5 |
| `far7` | full | fd-optimal/ipdb | 0.2 | *refused* | -- | 1.46 | -- | -- | -- | 6449.4 | 199.6 |
| `far7` | full | fd-satisficing | 1.8 | 1.2 | 0.6 | 1.46 | +1.464 | **no** | 2348 | 202.5 | 207.1 |
| `far7` | indexed | fd-optimal/blind | 12.5 | 11.5 | 0.9 | 1.46 | +1.464 | **no** | 1565 | 207.5 | 470.2 |
| `far7` | indexed | fd-optimal/lmcut | 8.6 | 93.0 | -84.5 | 1.46 | +1.549 | **no** | -- | 212.8 | 547.8 |
| `far7` | indexed | fd-optimal/ipdb | 0.2 | 0.3 | -0.0 | 1.46 | +1.465 | **no** | -- | 6449.4 | 7377.6 |
| `far7` | indexed | fd-satisficing | 1.8 | 3.3 | -1.5 | 1.46 | +1.466 | **no** | -- | 202.5 | 477.3 |
| `ringstuck4` | singleton | fd-optimal/blind | 0.0 | 0.0 | -0.0 | 0.01 | +0.011 | **no** | -- | 146.4 | 145.4 |
| `ringstuck4` | singleton | fd-optimal/lmcut | 0.0 | 0.0 | 0.0 | 0.01 | +0.011 | **no** | 1012 | 145.2 | 147.4 |
| `ringstuck4` | singleton | fd-optimal/ipdb | 0.0 | 0.0 | 0.0 | 0.01 | +0.011 | **no** | 3711 | 144.3 | 149.5 |
| `ringstuck4` | singleton | fd-satisficing | 0.0 | 0.1 | -0.0 | 0.01 | +0.011 | **no** | -- | 148.2 | 145.8 |
| `ringstuck5` | singleton | fd-optimal/blind | 0.0 | 0.0 | 0.0 | 0.02 | +0.022 | **no** | 5483 | 144.9 | 146.9 |
| `ringstuck5` | singleton | fd-optimal/lmcut | 0.0 | 0.0 | -0.0 | 0.02 | +0.022 | **no** | -- | 146.5 | 147.9 |
| `ringstuck5` | singleton | fd-optimal/ipdb | 0.0 | 0.0 | -0.0 | 0.02 | +0.022 | **no** | -- | 144.9 | 145.8 |
| `ringstuck5` | singleton | fd-satisficing | 0.0 | 0.1 | -0.0 | 0.02 | +0.022 | **no** | -- | 147.1 | 148.5 |
| `ringstuck6` | singleton | fd-optimal/blind | 0.0 | 0.0 | -0.0 | 0.04 | +0.045 | **no** | -- | 147.4 | 149.5 |
| `ringstuck6` | singleton | fd-optimal/lmcut | 0.0 | 0.0 | -0.0 | 0.04 | +0.045 | **no** | -- | 146.8 | 149.1 |
| `ringstuck6` | singleton | fd-optimal/ipdb | 0.0 | 0.0 | 0.0 | 0.04 | +0.045 | **no** | 44893 | 147.3 | 146.1 |
| `ringstuck6` | singleton | fd-satisficing | 0.1 | 0.1 | 0.0 | 0.04 | +0.045 | **no** | 4082 | 147.3 | 144.7 |
| `ringstuck7` | singleton | fd-optimal/blind | 0.0 | 0.0 | 0.0 | 0.08 | +0.081 | **no** | -- | 149.7 | 151.3 |
| `ringstuck7` | singleton | fd-optimal/lmcut | 0.0 | 0.0 | 0.0 | 0.08 | +0.081 | **no** | 81421 | 155.2 | 149.4 |
| `ringstuck7` | singleton | fd-optimal/ipdb | 0.0 | 0.0 | -0.0 | 0.08 | +0.081 | **no** | -- | 149.1 | 149.7 |
| `ringstuck7` | singleton | fd-satisficing | 0.0 | 0.0 | 0.0 | 0.08 | +0.081 | **no** | 27141 | 153.3 | 149.3 |
| `ringstuck8` | singleton | fd-optimal/blind | 0.0 | 0.0 | -0.0 | 0.13 | +0.132 | **no** | -- | 152.9 | 149.7 |
| `ringstuck8` | singleton | fd-optimal/lmcut | 0.0 | 0.1 | -0.1 | 0.13 | +0.132 | **no** | -- | 156.0 | 154.4 |
| `ringstuck8` | singleton | fd-optimal/ipdb | 0.0 | 0.0 | 0.0 | 0.13 | +0.132 | **no** | 32946 | 151.9 | 157.2 |
| `ringstuck8` | singleton | fd-satisficing | 0.0 | 0.0 | 0.0 | 0.13 | +0.132 | **no** | 43928 | 149.5 | 151.3 |

**No row repaid the carve out of the search it shortened.** That is the same verdict the bundled rung reaches by its own clock, and it is the second-side number §1.9's speed clause never had.

## Tie-break sensitivity — E2's gap G7, measured

**Gap closed** — E2 G7 -- absolute blind-search expansion counts carry a tie-break dependence that the bench did not measure

**Question** — Is the dividend a property of the instance, or of the order Fast Downward happens to pop states off an f-layer?

> **All three configurations are f = g + blind(). Nothing in this block is an lmcut or ipdb measurement, so no tie-break spread here bears on the astar(ipdb()) column E7 §7b withdrew.**

> **This is the weaker of the two instruments.** E7 already answered the tie-break objection with a stronger instrument than this one: the count of distinct states with f < C*, which A* must expand under any tie-break rule. This module measures absolute counts under three rules, which establishes the dependence and not its absence.

This block shows the absolute count depends on the tie-break. It cannot show a saving is more than tie-breaking -- that needs the count of distinct states with f < C*, which A* must expand under any rule and which E7 §3c measures. Stated so the ratio column is not read as doing work it does not do.

Excluded — The unsolvable family: Fast Downward's translator settles every `ringstuck*` instance during relaxed reachability, the search never starts, and 0 expansions has no tie-break.

Not measured here — Structural only, one run per cell. The question is whether a ratio survives a change of open list; a wall clock answers neither half of it.

| tie-break | `--search` | what it changes |
|---|---|---|
| `astar` | `astar(blind())` | FD's own `astar()` shorthand: a tie-breaking open list keyed on (f, h), FIFO inside a bucket. Every other blind number in this file is this one. |
| `single` | `eager(single(sum([g(),blind()])),reopen_closed=true)` | The same f, ordered by a single-key open list. Same f-layers, different order inside them -- this is the configuration E2's review found. |
| `goalcount` | `eager(tiebreaking([sum([g(),blind()]),goalcount()]),reopen_closed=true)` | The same f, ties inside a layer broken by unsatisfied goal count. A third point, so the spread is a range rather than a difference of two. |

| instance | tie-break | exp before | plan before | singleton after | singleton ratio | full after | full ratio |
|---|---|---|---|---|---|---|---|
| `open4` | astar | 49 | 6 | 49 | 1.0000 | 49 | 1.0000 |
| `open4` | single | 82 | 6 | 82 | 1.0000 | 82 | 1.0000 |
| `open4` | goalcount | 45 | 6 | 45 | 1.0000 | 45 | 1.0000 |
| `open4far` | astar | 837 | 11 | 610 | 0.7288 | 574 | 0.6858 |
| `open4far` | single | 874 | 11 | 635 | 0.7265 | 599 | 0.6854 |
| `open4far` | goalcount | 607 | 11 | 476 | 0.7842 | 447 | 0.7364 |
| `far4` | astar | 837 | 11 | 610 | 0.7288 | 574 | 0.6858 |
| `far4` | single | 874 | 11 | 635 | 0.7265 | 599 | 0.6854 |
| `far4` | goalcount | 607 | 11 | 476 | 0.7842 | 447 | 0.7364 |
| `far5` | astar | 958 | 13 | 872 | 0.9102 | 839 | 0.8758 |
| `far5` | single | 1479 | 13 | 1294 | 0.8749 | 1254 | 0.8479 |
| `far5` | goalcount | 982 | 13 | 887 | 0.9033 | 852 | 0.8676 |
| `far6` | astar | 3070 | 17 | 2762 | 0.8997 | 2706 | 0.8814 |
| `far6` | single | 4519 | 17 | 3950 | 0.8741 | 3884 | 0.8595 |
| `far6` | goalcount | 3030 | 17 | 2712 | 0.8950 | 2653 | 0.8756 |
| `far7` | astar | 7196 | 20 | 6365 | 0.8845 | 6272 | 0.8716 |
| `far7` | single | 8172 | 20 | 7278 | 0.8906 | 7178 | 0.8784 |
| `far7` | goalcount | 5508 | 20 | 4985 | 0.9050 | 4903 | 0.8902 |

### The two spreads the claim is about

`baseline spread` is how far the **absolute** blind count moves when only the open list changes — the quantity G7 warned about. `ratio spread` is how far the **dividend** moves under the same change, in percentage points. "The ratios are stable" is true exactly when the second is small while the first is not, and both are numbers here rather than an assurance.

| instance | guard | baseline min | baseline max | baseline spread | dividend min | dividend max | ratio spread (pts) |
|---|---|---|---|---|---|---|---|
| `open4` | singleton | 45 | 82 | 82.2% | 0.0% | 0.0% | 0.0 |
| `open4` | full | 45 | 82 | 82.2% | 0.0% | 0.0% | 0.0 |
| `open4far` | singleton | 607 | 874 | 44.0% | 21.6% | 27.3% | 5.8 |
| `open4far` | full | 607 | 874 | 44.0% | 26.4% | 31.5% | 5.1 |
| `far4` | singleton | 607 | 874 | 44.0% | 21.6% | 27.3% | 5.8 |
| `far4` | full | 607 | 874 | 44.0% | 26.4% | 31.5% | 5.1 |
| `far5` | singleton | 958 | 1479 | 54.4% | 9.0% | 12.5% | 3.5 |
| `far5` | full | 958 | 1479 | 54.4% | 12.4% | 15.2% | 2.8 |
| `far6` | singleton | 3030 | 4519 | 49.1% | 10.0% | 12.6% | 2.6 |
| `far6` | full | 3030 | 4519 | 49.1% | 11.9% | 14.0% | 2.2 |
| `far7` | singleton | 5508 | 8172 | 48.4% | 9.5% | 11.6% | 2.1 |
| `far7` | full | 5508 | 8172 | 48.4% | 11.0% | 12.8% | 1.9 |

**Read the dividend columns against E7's band, not against E2's.** The blind band on the far{N} family is -8.7% to -27.1% across far4..far10, not the '10-27%' E2 published; and that band is itself one open list's. Across instances generally the blind dividend runs 0% to 100%. The table above is why the qualifier is needed: the band was measured under `astar()`'s open list, and these rows show what the same instances do under two others.
