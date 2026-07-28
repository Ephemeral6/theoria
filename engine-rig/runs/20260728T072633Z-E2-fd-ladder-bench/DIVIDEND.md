# What a proved deadlock is worth

Claim under test — Theoria 1.9: every deadlock proved, the planner speeds up at the same time

## The bundled rung, which takes a pruner

`expansions` is the headline; `seconds` is the weaker number, because the pruner is a Python callable run per generated state and carving the theorems is a cost the blind search never pays. Both are here so neither can stand in for the other.

| instance | cells | theorems (1-atom/2-atom) | carve s | exp before | exp after | saved | states cut | blind s | pruned s | plan unchanged |
|---|---|---|---|---|---|---|---|---|---|---|
| `far4` | 16 | 16 (8/8) | 0.07 | 808 | 571 | 29% | 69 | 0.026 | 0.020 | yes |
| `far5` | 25 | 24 (8/16) | 0.26 | 988 | 869 | 12% | 35 | 0.055 | 0.051 | yes |
| `far6` | 36 | 32 (8/24) | 0.63 | 3152 | 2788 | 12% | 78 | 0.246 | 0.225 | yes |
| `far7` | 49 | 40 (8/32) | 1.44 | 8003 | 7041 | 12% | 100 | 0.878 | 0.797 | yes |
| `ringstuck4` | 12 | 2 (2/0) | 0.01 | 44 | 22 | 50% | 2 | 0.002 | 0.002 | yes |
| `ringstuck5` | 16 | 2 (2/0) | 0.02 | 75 | 45 | 40% | 2 | 0.003 | 0.003 | yes |
| `ringstuck6` | 20 | 2 (2/0) | 0.04 | 114 | 76 | 33% | 2 | 0.005 | 0.005 | yes |
| `ringstuck7` | 24 | 2 (2/0) | 0.08 | 161 | 115 | 29% | 2 | 0.008 | 0.007 | yes |
| `ringstuck8` | 28 | 2 (2/0) | 0.13 | 216 | 162 | 25% | 2 | 0.011 | 0.010 | yes |

## The Fast Downward rungs, which do not

No pruning hook, so the theorems are compiled into the task instead (`bench/compile_theorems.py`). `singleton` expresses the corner deadlocks and stays inside STRIPS; `full` adds the pair deadlocks and needs `:adl`. Every guarded plan below was replayed against the **original** domain by the rig's own validator.

`fd-optimal/blind` is a **control, not a rung** — `choose_tier` never selects it. A\* with a zero heuristic is the bundled BFS in different clothes, so it shows what the theorems are worth to a search that has no other way of knowing a region is dead. Read it against the two rows below it: that difference is the whole finding.

| instance | guard | theorems carried | rung | exp before | exp after | task size before | task size after | plan delta | honest |
|---|---|---|---|---|---|---|---|---|---|
| `far4` | singleton | 8/16 | fd-optimal/blind | 837 | 610 | 1029 | 869 | 0 | yes |
| `far4` | singleton | 8/16 | fd-optimal/lmcut | 23 | 22 | 1029 | 869 | 0 | yes |
| `far4` | singleton | 8/16 | fd-optimal/ipdb | 12 | 12 | 1029 | 869 | 0 | yes |
| `far4` | singleton | 8/16 | fd-satisficing | 95 | 108 | 1029 | 869 | 2 | **no** |
| `far4` | full | 16/16 | fd-optimal/blind | 837 | 574 | 1029 | 981 | 0 | yes |
| `far4` | full | 16/16 | fd-optimal/lmcut | 23 | *refused* | 1029 | -- | -- | -- |
| `far4` | full | 16/16 | fd-optimal/ipdb | 12 | *refused* | 1029 | -- | -- | -- |
| `far4` | full | 16/16 | fd-satisficing | 95 | 40 | 1029 | 981 | -26 | yes |
| `far5` | singleton | 8/24 | fd-optimal/blind | 958 | 872 | 1815 | 1655 | 0 | yes |
| `far5` | singleton | 8/24 | fd-optimal/lmcut | 30 | 30 | 1815 | 1655 | 0 | yes |
| `far5` | singleton | 8/24 | fd-optimal/ipdb | 14 | 14 | 1815 | 1655 | 0 | yes |
| `far5` | singleton | 8/24 | fd-satisficing | 59 | 26 | 1815 | 1655 | -8 | yes |
| `far5` | full | 24/24 | fd-optimal/blind | 958 | 839 | 1815 | 1847 | 0 | yes |
| `far5` | full | 24/24 | fd-optimal/lmcut | 30 | *refused* | 1815 | -- | -- | -- |
| `far5` | full | 24/24 | fd-optimal/ipdb | 14 | *refused* | 1815 | -- | -- | -- |
| `far5` | full | 24/24 | fd-satisficing | 59 | 75 | 1815 | 1847 | 0 | yes |
| `far6` | singleton | 8/32 | fd-optimal/blind | 3070 | 2762 | 2813 | 2653 | 0 | yes |
| `far6` | singleton | 8/32 | fd-optimal/lmcut | 47 | 47 | 2813 | 2653 | 0 | yes |
| `far6` | singleton | 8/32 | fd-optimal/ipdb | 18 | 18 | 2813 | 2653 | 0 | yes |
| `far6` | singleton | 8/32 | fd-satisficing | 111 | 111 | 2813 | 2653 | 0 | yes |
| `far6` | full | 32/32 | fd-optimal/blind | 3070 | 2706 | 2813 | 2925 | 0 | yes |
| `far6` | full | 32/32 | fd-optimal/lmcut | 47 | *refused* | 2813 | -- | -- | -- |
| `far6` | full | 32/32 | fd-optimal/ipdb | 18 | *refused* | 2813 | -- | -- | -- |
| `far6` | full | 32/32 | fd-satisficing | 111 | 36 | 2813 | 2925 | -8 | yes |
| `far7` | singleton | 8/40 | fd-optimal/blind | 7196 | 6365 | 4023 | 3863 | 0 | yes |
| `far7` | singleton | 8/40 | fd-optimal/lmcut | 69 | 68 | 4023 | 3863 | 0 | yes |
| `far7` | singleton | 8/40 | fd-optimal/ipdb | 21 | 21 | 4023 | 3863 | 0 | yes |
| `far7` | singleton | 8/40 | fd-satisficing | 134 | 134 | 4023 | 3863 | 0 | yes |
| `far7` | full | 40/40 | fd-optimal/blind | 7196 | 6272 | 4023 | 4215 | 0 | yes |
| `far7` | full | 40/40 | fd-optimal/lmcut | 69 | *refused* | 4023 | -- | -- | -- |
| `far7` | full | 40/40 | fd-optimal/ipdb | 21 | *refused* | 4023 | -- | -- | -- |
| `far7` | full | 40/40 | fd-satisficing | 134 | 56 | 4023 | 4215 | -10 | yes |
| `ringstuck4` | singleton | 2/2 | fd-optimal/blind | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck4` | singleton | 2/2 | fd-optimal/lmcut | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck4` | singleton | 2/2 | fd-optimal/ipdb | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck4` | singleton | 2/2 | fd-satisficing | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck4` | full | 2/2 | fd-optimal/blind | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck4` | full | 2/2 | fd-optimal/lmcut | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck4` | full | 2/2 | fd-optimal/ipdb | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck4` | full | 2/2 | fd-satisficing | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck5` | singleton | 2/2 | fd-optimal/blind | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck5` | singleton | 2/2 | fd-optimal/lmcut | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck5` | singleton | 2/2 | fd-optimal/ipdb | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck5` | singleton | 2/2 | fd-satisficing | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck5` | full | 2/2 | fd-optimal/blind | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck5` | full | 2/2 | fd-optimal/lmcut | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck5` | full | 2/2 | fd-optimal/ipdb | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck5` | full | 2/2 | fd-satisficing | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck6` | singleton | 2/2 | fd-optimal/blind | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck6` | singleton | 2/2 | fd-optimal/lmcut | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck6` | singleton | 2/2 | fd-optimal/ipdb | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck6` | singleton | 2/2 | fd-satisficing | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck6` | full | 2/2 | fd-optimal/blind | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck6` | full | 2/2 | fd-optimal/lmcut | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck6` | full | 2/2 | fd-optimal/ipdb | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck6` | full | 2/2 | fd-satisficing | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck7` | singleton | 2/2 | fd-optimal/blind | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck7` | singleton | 2/2 | fd-optimal/lmcut | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck7` | singleton | 2/2 | fd-optimal/ipdb | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck7` | singleton | 2/2 | fd-satisficing | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck7` | full | 2/2 | fd-optimal/blind | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck7` | full | 2/2 | fd-optimal/lmcut | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck7` | full | 2/2 | fd-optimal/ipdb | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck7` | full | 2/2 | fd-satisficing | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck8` | singleton | 2/2 | fd-optimal/blind | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck8` | singleton | 2/2 | fd-optimal/lmcut | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck8` | singleton | 2/2 | fd-optimal/ipdb | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck8` | singleton | 2/2 | fd-satisficing | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck8` | full | 2/2 | fd-optimal/blind | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck8` | full | 2/2 | fd-optimal/lmcut | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck8` | full | 2/2 | fd-optimal/ipdb | 0 | 0 | 4 | 4 | -- | n/a |
| `ringstuck8` | full | 2/2 | fd-satisficing | 0 | 0 | 4 | 4 | -- | n/a |

**Zero expansions before *and* after on `ringstuck4`, `ringstuck5`, `ringstuck6`, `ringstuck7`, `ringstuck8`.** Fast Downward's translator settles those instances during relaxed reachability and the search never starts, so there is no search for a deadlock theorem to shorten. The task size of 4 in those rows is the degenerate task the translator emits once it has decided.
