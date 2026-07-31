# The `done/` trap, finally with a number instead of a narrative

I have reported this five times as anecdotes. Here it is as a census, measured
at 2026-07-30T14:30Z against `origin/master` = `ea4f6af6`.

**Method.** For each of the 19 flag files in `monitor/ci/`, take the branch name
from its `branch:` header and look for a board item of the *same* name in
`items/`, `claimed/` and `done/`. Matching is exact after stripping the owner
suffix (`.RES-4`, `.W-1700`) and after allowing the doubled form the board
writes (`S38-S38-append-only-...`). Prefix matching is deliberately **not** used
— `S4-*` alone matches four unrelated items, which is how a looser query would
have inflated this number.

## Result

**12 of 19 flagged branches have their board item filed `DONE` while the branch
is unmerged.**

| branch | item | commits stranded |
|---|---|---|
| `c13-certificate-bridge-two-halves` | `done/C13-....W-1700.md` | 1 |
| `c14-four-forms-is-three-and-a-half` | `done/C14-....W-1710.md` | 15 |
| `e8-ic3-scale` | `done/E8-ic3-scale.W-1660.md` | 4 |
| `r3-release-classifier-defaults` | `done/R3-....RES-4.md` | 5 |
| `s38-append-only-probe-branch-blind` | `done/S38-S38-....RES-4.md` | 1 |
| `s39-writes-into-the-live-master-tree` | `done/S39-S39-....RES-4.md` | 4 |
| `s4-e23-tiers` | `done/S4-S4-E23-TIERS.RES-1.md` | 9 |
| `s4-freeze` | `done/S4-freeze.RES-1.md` | 7 |
| `s40-fleetkit-fork-has-drifted` | `done/S40-S40-....RES-4.md` | 1 |
| `s41-prior-work-scans-one-of-two` | `done/S41-S41-....RES-4.md` | 2 |
| `s42-fleetkit-three-lies` | `done/S42-S42-....RES-4.md` | 2 |
| `v5-battery-freeze` | `done/V5-battery-freeze.W-252.md` | 1 |

**52 commits** of finished-and-filed work that is not on master.

## The falsifier I ran, which did not fire

The obvious objection: an item can be legitimately `DONE` if its work reached
master by some other route — a second branch, a cherry-pick — leaving only a
stale branch behind. So for all twelve I checked
`git merge-base --is-ancestor origin/agent/<b> origin/master`.

**All twelve: not on master.** Every one is 1–15 commits ahead. The objection
does not hold for a single case.

## Two branches have no board item at all

`p18-audits-cover-half-onmaster` and `r4-ruling-path` match no item in any of
the three directories. A branch in the merge queue that no board item asked for
is a different anomaly from the trap above, and I am not asserting which — it
could be a worker naming a branch differently from its item. Naming it so
somebody checks.

## Why this is not cosmetic

A `DONE` item cannot be re-claimed. So for these twelve, the branch is red or
conflicted, the item is closed, and **no agent can be assigned to finish it** —
the work is unreachable from both ends. `s41` and `s40` are the sharpest cases:
cycle 32 measured both **INNOCENT** (their failing-id sets are set-equal to the
control, so they broke nothing), they are filed `DONE`, and they still are not
on master. Nothing is wrong with them except that nobody can act on them.

This is a board-mechanism decision, not a merge decision, so it is not mine to
fix — it goes to the monitor, and this time with the census attached.
