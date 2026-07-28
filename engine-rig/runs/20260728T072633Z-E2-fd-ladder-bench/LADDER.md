# The three-rung ladder, measured

Fastest of 3 runs per cell. `stub-bfs` gives up past 200,000 expansions.

> **Node counts do not compare across rungs.** stub-bfs expands grounded STRIPS states; Fast Downward expands SAS+ states after translation. No ratio between the two appears here.

## Plan length, against an oracle that is not a planner

| instance | oracle | stub-bfs | fd/lmcut | fd/ipdb | fd/lama | optimum ok | rungs agree | lama >= optimum |
|---|---|---|---|---|---|---|---|---|
| `gripper-01` | 3 | 3 | 3 | 3 | 3 | yes | yes | yes |
| `gripper-02` | 5 | 5 | 5 | 5 | 5 | yes | yes | yes |
| `gripper-03` | 9 | 9 | 9 | 9 | 9 | yes | yes | yes |
| `gripper-04` | 11 | 11 | 11 | 11 | 11 | yes | yes | yes |
| `gripper-05` | 15 | 15 | 15 | 15 | 15 | yes | yes | yes |
| `gripper-06` | 17 | 17 | 17 | 17 | 17 | yes | yes | yes |
| `gripper-07` | 21 | 21 | 21 | 21 | 21 | yes | yes | yes |
| `gripper-08` | 23 | 23 | 23 | 23 | 23 | yes | yes | yes |
| `gripper-09` | 27 | 27 | 27 | 27 | 27 | yes | yes | yes |
| `gripper-10` | 29 | 29 | 29 | 29 | 29 | yes | yes | yes |
| `sokoban-open4` | 6 | 6 | 6 | 6 | 6 | yes | yes | yes |
| `sokoban-open4far` | -- | 11 | 11 | 11 | 37 | n/a | yes | yes |
| `sokoban-ring` | 1 | 1 | 1 | 1 | 1 | yes | yes | yes |
| `sokoban-ringstuck` | -- | *unsolvable* | *unsolvable* | *unsolvable* | *not entitled* | n/a | n/a | n/a |
| `sokoban-far4` | -- | 11 | 11 | 11 | 37 | n/a | yes | yes |
| `sokoban-far5` | -- | 13 | 13 | 13 | 21 | n/a | yes | yes |
| `sokoban-far6` | -- | 17 | 17 | 17 | 27 | n/a | yes | yes |

## Nodes expanded — read down a column, never across a row

| instance | stub-bfs (STRIPS states) | fd/lmcut (SAS+) | fd/ipdb (SAS+) | fd/lama (SAS+) |
|---|---|---|---|---|
| `gripper-01` | 5 | 4 | 4 | 4 |
| `gripper-02` | 18 | 8 | 6 | 7 |
| `gripper-03` | 81 | 54 | 66 | 13 |
| `gripper-04` | 238 | 107 | 217 | 16 |
| `gripper-05` | 693 | 611 | 656 | 22 |
| `gripper-06` | 1830 | 1338 | 1783 | 25 |
| `gripper-07` | 4721 | 4556 | 4654 | 31 |
| `gripper-08` | 11742 | 10537 | 11661 | 34 |
| `gripper-09` | 28653 | 28377 | 28548 | 40 |
| `gripper-10` | 68566 | 66176 | 68443 | 43 |
| `sokoban-open4` | 47 | 7 | 7 | 6 |
| `sokoban-open4far` | 808 | 23 | 12 | 95 |
| `sokoban-ring` | 1 | 2 | 2 | 2 |
| `sokoban-ringstuck` | 44 | 0 | 0 | 0 |
| `sokoban-far4` | 808 | 23 | 12 | 95 |
| `sokoban-far5` | 988 | 30 | 14 | 59 |
| `sokoban-far6` | 3152 | 47 | 18 | 111 |

## Wall clock, in milliseconds — the column that decides which rung to call

`search` is what Fast Downward's search cost; `end-to-end` is what the caller waited for, driver startup and translation included. On this batch they differ by three orders of magnitude, and only the second one is a cost anybody pays.

| instance | stub-bfs | fd/lmcut search | fd/lmcut end-to-end | fd/ipdb end-to-end | fd/lama end-to-end |
|---|---|---|---|---|---|
| `gripper-01` | 0.2 | 0.1 | 148.2 | 150.9 | 151.3 |
| `gripper-02` | 0.3 | 0.1 | 148.7 | 152.1 | 147.2 |
| `gripper-03` | 1.1 | 0.4 | 150.0 | 159.2 | 152.9 |
| `gripper-04` | 3.5 | 0.7 | 151.7 | 157.1 | 150.3 |
| `gripper-05` | 11.6 | 2.9 | 153.1 | 160.0 | 152.5 |
| `gripper-06` | 34.8 | 7.6 | 161.3 | 167.8 | 152.6 |
| `gripper-07` | 100.8 | 24.1 | 175.2 | 170.1 | 150.0 |
| `gripper-08` | 270.4 | 64.5 | 218.5 | 181.8 | 158.3 |
| `gripper-09` | 746.0 | 188.2 | 352.6 | 209.6 | 162.8 |
| `gripper-10` | 1953.9 | 507.2 | 692.5 | 263.1 | 161.9 |
| `sokoban-open4` | 4.2 | 0.3 | 165.9 | 258.7 | 164.2 |
| `sokoban-open4far` | 27.0 | 0.8 | 163.3 | 534.6 | 166.1 |
| `sokoban-ring` | 1.4 | 0.1 | 154.1 | 152.4 | 153.0 |
| `sokoban-ringstuck` | 1.8 | 0.0 | 144.7 | 146.2 | 146.2 |
| `sokoban-far4` | 26.5 | 0.8 | 166.1 | 539.3 | 172.7 |
| `sokoban-far5` | 53.7 | 1.9 | 177.1 | 983.9 | 170.9 |
| `sokoban-far6` | 246.7 | 4.1 | 183.2 | 1774.1 | 182.9 |
