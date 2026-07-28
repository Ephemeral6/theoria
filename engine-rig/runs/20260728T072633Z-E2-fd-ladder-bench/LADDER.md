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
| `gripper-01` | 0.1 | 0.1 | 146.5 | 148.9 | 149.7 |
| `gripper-02` | 0.3 | 0.1 | 147.3 | 154.1 | 152.5 |
| `gripper-03` | 1.1 | 0.4 | 150.6 | 156.3 | 150.9 |
| `gripper-04` | 3.6 | 0.8 | 149.9 | 155.5 | 149.6 |
| `gripper-05` | 11.7 | 2.9 | 152.2 | 159.3 | 151.4 |
| `gripper-06` | 35.3 | 7.4 | 158.6 | 162.9 | 151.5 |
| `gripper-07` | 100.8 | 24.2 | 175.2 | 170.4 | 153.4 |
| `gripper-08` | 280.2 | 65.8 | 227.6 | 191.8 | 165.0 |
| `gripper-09` | 743.1 | 192.1 | 353.9 | 213.1 | 164.3 |
| `gripper-10` | 1926.5 | 502.9 | 666.2 | 262.9 | 161.9 |
| `sokoban-open4` | 4.3 | 0.3 | 166.4 | 264.6 | 167.3 |
| `sokoban-open4far` | 26.3 | 0.9 | 168.7 | 536.2 | 169.4 |
| `sokoban-ring` | 1.3 | 0.1 | 157.7 | 163.3 | 157.5 |
| `sokoban-ringstuck` | 2.0 | 0.1 | 149.3 | 149.0 | 146.7 |
| `sokoban-far4` | 26.7 | 0.8 | 168.2 | 541.6 | 171.6 |
| `sokoban-far5` | 56.0 | 2.0 | 179.9 | 989.4 | 179.2 |
| `sokoban-far6` | 253.9 | 4.1 | 187.3 | 1796.8 | 185.4 |
