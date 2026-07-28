# P-13 -- what the real planner bought

Fast Downward: `C:/Users/user/Desktop/theoria-p13/engine-rig/.toolchain/downward/fast-downward.py`
Search configuration: `astar(blind())` (blind A*, the stub's twin)

## A. The deadlock dividend, taken by Fast Downward

| Instance | Theorems (encoded) | FD before -> after | FD saved | Stub before -> after (M9) | Same answer |
|---|---|---|---|---|---|
| `open4` | 16 (16) | 49 -> 49 | 0 (0.0%) | 47 -> 47 | yes |
| `open4far` | 16 (16) | 837 -> 574 | 263 (31.4%) | 808 -> 571 | yes |
| `ringstuck` | 2 (2) | 0 -> 0 | n/a | 44 -> 22 | yes |

### What the numbers say

* `open4` -- **zero, on both engines** (49 -> 49 here, 47 -> 47 in M9).  D-020's negative result replicates: true theorems buy nothing when the answer lies shallower than any deadlock.
* `open4far` -- **the dividend survives the change of engine**: 31.4% fewer expansions on Fast Downward against 29.3% on the bundled search, and the plan is 11 steps either way.  The saving was not an artefact of the stub's node ordering.
* `ringstuck` -- **the theorems had nothing to buy**: Fast Downward's translator settles this instance by relaxed reachability before the search starts (`No relaxed solution! Generating unsolvable task...`), so it expands 0 states either way.  M9's 44 -> 22 is therefore a fact about the bundled search, which has no such check, and not a dividend a real planner would collect.

## B. Stub versus Fast Downward on the cold-start domains

| Instance | Stub | FD | Agree |
|---|---|---|---|
| `a0-spike/match` | 2 steps | 2 steps | yes |
| `a0-spike/mismatch` | UNSAT | UNSAT | yes |
| `cold-start-a0` | 12 steps | 12 steps | yes |
| `cold-start-a0/no-button` | UNSAT | UNSAT | yes |
| `cold-start-a2` | 18 steps | 18 steps | yes |
| `cold-start-a2/holed` | UNSAT | UNSAT | yes |
| `cold-start-a2/repaired` | 18 steps | 18 steps | yes |
