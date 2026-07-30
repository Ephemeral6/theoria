# Cycle 32 verdict table (written as results arrive — nothing lives only in context)

Control: clean worktree of `cc7e414e`, **6 failures**, `tests` the only red stage.
Measured twice concurrently by two independent agents, identical id sets, so the
"a fresh control might differ" falsifier was checked and did not fire.

Method per branch: worktree at `cc7e414e` → `git merge --no-edit <branch>` → the
monitor gate run exactly as `ci_merge.py` invokes it (env from `gates.gate_env`,
cwd `<wt>/monitor`, timeout 1800) → `pytest -q -rf` for the full failing-id set →
set comparison against control. INNOCENT = set-equal to control.

| branch | merge | gate | added | removed | verdict |
|---|---|---|---|---|---|
| `s41-prior-work-scans-one-of-two` | — | rc 1, tests only | none | none | **INNOCENT** (cycle 31) |
| `c13-certificate-bridge-two-halves` @ `21c88bc5` | clean, 20 files +2544/−9 | rc 1, tests only | none | none | **INNOCENT** |
| `s40-fleetkit-fork-has-drifted` @ `9ca9278a` | clean, 3 files +672 | rc 1, tests only | none | none | **INNOCENT** |
| `s38-append-only-probe-branch-blind` | | | | | pending |
| `s39-writes-into-the-live-master-tree` | | | | | pending |
| `s42-fleetkit-three-lies` | | | | | pending |
| `v6-v23-large-space-verdict-gap` | | | | | pending |
| `a3-campaign-devpile` | | | | | pending (X-vs-Y) |
| `s4-freeze` | clean | rc 1, freeze `[15]` | n/a | n/a | **RETIRE — contained in s4-e23-tiers** |
| `s4-e23-tiers` | clean, 22 files +4406 | rc 1, freeze `[15]` 15b | n/a | n/a | **HOLD, send back** (15b unsatisfiable) |

**Third category checked on s40 and it does not fire.** s40 adds
`monitor/tests/test_fleetkit_drift.py`, which does not exist on master; 409−397
= 12 collected = exactly its 12 tests, and standalone they are 12/12 green. So
the branch's new tests do not catch a master defect — they pass.

## Two findings outside what I asked for

**s40 and s42 collide, and not merely mechanically.** Both independently add the
same path `monitor/tests/test_fleetkit_drift.py` (s40 blob `ef73603f`, 387 lines;
s42 blob `e3c8c25e`, 469 lines); their merge-base `60def5cb` lacks the file and
neither branch is an ancestor of the other — an add/add conflict for whichever is
queued second. And they assert **opposite things**: s40's `DECLARED` dict says
fleetkit still carries the `LANE_OWNER = {}` / `_PREFIX = ''` defects, while s42
*edits* `fleetkit/board.py` to remove them. If s42 lands first, s40's pinned-count
tests should go red on the next tree. **Do not queue both.** Which one survives is
a content decision, not merge mechanics, so it is not mine.

**S40 is filed DONE and is not.** `board.log` has `2026-07-30T08:01:25Z DONE S40
by RES-4` and the item sits in `done/`, but the branch is unmerged and touches
nothing under `fleetkit/`, so the item's requirement 3 (make the false
`LANE_OWNER` docstring true or delete it) is provably not met by it — its own
docstring defers the fleetkit-side fixes to a follow-up. This is the `done/` trap
I have now reported five times: a DONE item cannot be reassigned, so the work
cannot be finished by anyone.
