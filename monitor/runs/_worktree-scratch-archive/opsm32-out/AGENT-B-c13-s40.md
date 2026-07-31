# OPS-M cycle 32 — Agent B: c13 and s40 merge arms

Measured by a subagent of OPS-M. Base of every arm: **master `cc7e414eb3bfde3325a50f9ce0e8dc896bda2b84`**.
No `git fetch` was run; remote-tracking refs as they already stood locally.

Nothing in the main checkout was written. Work lives in
`.worktrees/opsm32-c13-mrg`, `.worktrees/opsm32-s40-mrg`; outputs in
`.worktrees/opsm32-out/{c13,s40}/`.

## Shas

| what | sha |
|---|---|
| base master | `cc7e414eb3bfde3325a50f9ce0e8dc896bda2b84` |
| `origin/agent/c13-certificate-bridge-two-halves` | `21c88bc5ab5723164d1c051856dab6bef4e6a580` |
| c13 merge commit (arm HEAD) | `281afd2b378412231e8ebf85863ef5dab0c1f06a` |
| `origin/agent/s40-fleetkit-fork-has-drifted` | `9ca9278a1637ae6f41a3e02fc05637fc2f5ed870` |
| s40 merge commit (arm HEAD) | `cc7632864719e9687841fa4d0aa468971d42fe5a` |

## Control (from cycle 31, sibling agent re-measuring this cycle — theirs is authoritative if it differs)

6 failing ids on clean `cc7e414e`:

```
tests/test_scan_failure_exit.py::test_a_blinded_conflict_probe_does_not_report_green
tests/test_scan_no_third_value.py::test_a_deleted_append_only_file_is_a_risk
tests/test_scan_no_third_value.py::test_all_files_present_still_reads_green
tests/test_standing_reflex_no_third_value.py::test_reflex_reads_the_return_code_of_every_child_it_scrapes
tests/test_standing_reflex_no_third_value.py::test_a_failed_git_query_skips_revival_instead_of_reviving_everyone
tests/test_standing_reflex_no_third_value.py::test_supply_unknown_is_distinct_from_supply_low_zero
```

**Control CONFIRMED in this sitting, not merely inherited.** The sibling agent's
control arm `opsm32-ctl` (clean `cc7e414e`, run concurrently with these two arms)
produced the identical six ids in the identical order, with the identical single
red stage — `.worktrees/opsm32-out/ctl.pytest.txt` and `ctl.gate.txt`:

```
== tests              FAILED(1)
== board states disjoint ok
== real run           ok
== artifact fields    ok
RED: tests
```

So the "a fresh control might differ" falsifier named under each verdict below
has been checked, and it did not fire.

## Arm 1 — c13-mrg

**Merge: CLEAN** (`Merge made by the 'ort' strategy`, rc 0, no conflicts, working tree clean).

```
git diff --stat cc7e414e..HEAD | tail -1
 20 files changed, 2544 insertions(+), 9 deletions(-)
```

Top-level dirs touched: `CONTRACTS`, `PARTNER_SYNC.md`, `engine-rig`, `monitor`.

The **only** file it adds under `monitor/` is an inbox note:
`monitor/inbox/20260730T050500Z-W-1700-c13-premise-expired-and-two-contracts-unanswered.md`.
It adds **no test** and changes **no code** in `monitor/` — so any red the
monitor gate shows on this arm is inherited from master by construction.

### Gate result — c13-mrg

Gate resolved by `gates.gate_for(wt, "monitor")` to `kind=verify`, `name=verify.sh`,
`cmd = ['C:\Program Files\Git\bin\bash.exe', '<wt>/monitor/verify.sh']`,
cwd `<wt>\monitor`. **gate rc 1.** Stages:

```
== tests              FAILED(1)
== board states disjoint ok
== real run           ok
== artifact fields    ok
RED: tests
```

`tests` is the **only** red stage. The three non-test stages are green:
`scan.build wrote history.jsonl, index.html, state.json` /
`gates: 24 gated, 1 tests-only, 0 UNGATED` / `board.py list: 161 line(s)` /
`state.json carries all 13 required fields; the gate survey is consistent`.

Re-run with `-rf` (`pytest_rc 1`): **397 collected, 6 failed, 0 skipped**.
Failing ids, verbatim:

```
tests/test_scan_failure_exit.py::test_a_blinded_conflict_probe_does_not_report_green
tests/test_scan_no_third_value.py::test_a_deleted_append_only_file_is_a_risk
tests/test_scan_no_third_value.py::test_all_files_present_still_reads_green
tests/test_standing_reflex_no_third_value.py::test_reflex_reads_the_return_code_of_every_child_it_scrapes
tests/test_standing_reflex_no_third_value.py::test_a_failed_git_query_skips_revival_instead_of_reviving_everyone
tests/test_standing_reflex_no_third_value.py::test_supply_unknown_is_distinct_from_supply_low_zero
```

**Set equality with the control: YES.** ADDED: `{}` (none). REMOVED: `{}` (none).

### Verdict — c13: INNOCENT

Evidence: (1) identical failing-id set to the control, item for item, in the same
order; (2) `tests` is the only red stage, and the red tests live in
`test_scan_*` / `test_standing_reflex_*`, files the branch does not touch;
(3) the branch's whole `monitor/` footprint is one inbox `.md`, so there is no
mechanism by which it could reach `scan.py` or `reflex.py`.

**What would falsify it:** a sibling control measured in the same sitting on
clean `cc7e414e` that yields a *different* set (in particular a smaller one) —
then the equality above would be an artefact of both runs sharing a
board-drift-induced red, and the difference would have to be re-derived against
the fresh control. Also falsified if a later `-rf` re-run of this arm names any
id outside the six.

## Arm 2 — s40-mrg

**Merge: CLEAN** (`Merge made by the 'ort' strategy`, rc 0, no conflicts, working tree clean).

```
git diff --stat cc7e414e..HEAD | tail -1
 3 files changed, 672 insertions(+)
```

Top-level dirs touched: `monitor` only. Files:

```
monitor/runs/20260730T0625Z-S40/FINDINGS.md
monitor/runs/20260730T0625Z-S40/RUN_STATE.md
monitor/tests/test_fleetkit_drift.py
```

**Third-category flag, established before the run:** the branch adds a NEW test
file into the gated suite. `git cat-file -e cc7e414e:monitor/tests/test_fleetkit_drift.py`
→ `fatal: path 'monitor/tests/test_fleetkit_drift.py' does not exist in 'cc7e414e'`.
So **the file is ABSENT on master.** Any failing id from that file is a *new
instrument*, not a regression: it compares `monitor/board.py` against
`fleetkit/fleetkit/board.py` function-by-function on normalised source and is
red unless each divergence is DECLARED with a reason. If it is red, the
question to ask is "is the divergence it names real?", not "did s40 break the
build?".

Standalone pre-check of the new file on the merged arm (`cwd=<wt>/monitor`,
`PYTHONPATH=<wt>`, `python -m pytest -q -p no:cacheprovider -rf tests/test_fleetkit_drift.py`):

```
............                                                             [100%]
```

**12 passed, 0 failed.** So the new instrument is green on the arm; the third
category does not fire here. (Consistent with the fact that
`git diff --stat <merge-base> cc7e414e -- monitor/board.py fleetkit/fleetkit/board.py`
is empty: neither file moved between s40's base `60def5cb` and `cc7e414e`, so the
branch's DECLARED divergence list is still exactly current.)

### Gate result — s40-mrg

Same gate resolution (`verify` / `verify.sh`, cwd `<wt>\monitor`). **gate rc 1.**
Stages:

```
== tests              FAILED(1)
== board states disjoint ok
== real run           ok
== artifact fields    ok
RED: tests
```

`tests` is the **only** red stage; the other three carry the identical green
detail as the c13 arm (24 gated / 1 tests-only / 0 UNGATED, board.py list 161
lines, 13 required fields).

Re-run with `-rf` (`pytest_rc 1`): **409 collected, 6 failed, 0 skipped**.
Failing ids, verbatim:

```
tests/test_scan_failure_exit.py::test_a_blinded_conflict_probe_does_not_report_green
tests/test_scan_no_third_value.py::test_a_deleted_append_only_file_is_a_risk
tests/test_scan_no_third_value.py::test_all_files_present_still_reads_green
tests/test_standing_reflex_no_third_value.py::test_reflex_reads_the_return_code_of_every_child_it_scrapes
tests/test_standing_reflex_no_third_value.py::test_a_failed_git_query_skips_revival_instead_of_reviving_everyone
tests/test_standing_reflex_no_third_value.py::test_supply_unknown_is_distinct_from_supply_low_zero
```

**Set equality with the control: YES.** ADDED: `{}` (none). REMOVED: `{}` (none).

**409 − 397 = 12**, exactly the 12 tests in the new `test_fleetkit_drift.py`, and
all 12 are in the passing count. So the new instrument ran inside the gate and
was green — the third category is checked and does **not** fire.

### Verdict — s40: INNOCENT

Evidence: (1) failing-id set identical to the control; (2) `tests` the only red
stage; (3) the branch adds 12 tests and the gate's collected count rises by
exactly 12 with the failure count unchanged at 6, so the new file contributed
zero red; (4) standalone run of the new file on the arm: `............ [100%]`,
12/12 pass; (5) the branch touches no `monitor/*.py` module at all — its only
executable addition is the test file itself.

**What would falsify it:** a same-sitting control with a different set; or a
`monitor/board.py` or `fleetkit/fleetkit/board.py` commit landing on master
after `cc7e414e`, which would move the subject of the pinned-count assertions in
`test_fleetkit_drift.py` and could turn this INNOCENT into a real red on the
then-current tip. That is a merge-order hazard, not a defect in the branch as
measured here — see the s42 collision below.

### Collision with s42 — found while cross-reading Agent C's arm, matters for merge order

`origin/agent/s42-fleetkit-three-lies` **also adds `monitor/tests/test_fleetkit_drift.py`**,
independently, with different content:

| branch | blob | lines |
|---|---|---|
| `agent/s40-fleetkit-fork-has-drifted` | `ef73603fcf05edaa84d5f8957f80026fbb748afc` | 387 |
| `agent/s42-fleetkit-three-lies` | `e3c8c25eada1675dd8c119a3da5627c7f819d513` | 469 |

`git merge-base s40 s42` = `60def5cb`, and the file is **ABSENT** there
(`fatal: path ... does not exist in '60def5cb...'`); `git merge-base --is-ancestor`
says neither branch contains the other. So this is a genuine **add/add
collision**: each merges cleanly into `cc7e414e` on its own, but the *second* of
the two to be queued will conflict on that path.

Worse than a textual conflict: the two files make **opposite claims about
fleetkit**. s40's `DECLARED` dict asserts fleetkit still carries the defects
(`LANE_OWNER = {}`, `_PREFIX = ''`), while s42 *edits* `fleetkit/board.py` to
remove them and its test asserts `LANE_OWNER` is gone and `task_prefix` exists.
If s42 lands first, s40's `test_declared_entries_still_describe_a_real_divergence`
and `test_the_measured_divergence_count_is_pinned` should go red on the *next*
tree — not because s40 is wrong but because its subject moved. **Recommendation
for the referee: do not queue both; pick one, and the pick is a content decision,
not a merge-mechanics one.**

### Board note (S40 DONE claim)

`monitor/board/board.log` records
`2026-07-30T08:01:25Z DONE S40-S40-fleetkit-fork-has-drifted by RES-4`
and the item sits in `monitor/board/done/`. The branch is unmerged, and its own
diff touches **nothing under `fleetkit/`** — so item requirement 3 ("that false
`LANE_OWNER` docstring must either become true or be deleted") is
demonstrably not done by this branch; its own test docstring says the fleetkit-side
fixes "belong to whoever holds that territory, and are filed as a follow-up item
rather than done here". The DONE claim therefore overstates delivery on
requirement 3 in addition to being marked while nothing was on master.

---

## Bottom line

| arm | merge | gate rc | red stages | collected | failed | ADDED | REMOVED | verdict |
|---|---|---|---|---|---|---|---|---|
| `c13-mrg` | clean | 1 | `tests` only | 397 | 6 | none | none | **INNOCENT** |
| `s40-mrg` | clean | 1 | `tests` only | 409 | 6 | none | none | **INNOCENT** |

Both arms reproduce master's own six failures exactly and add nothing. The
`tests` stage is the only red stage on either arm; `board states disjoint`,
`real run` and `artifact fields` are green on both. The queue's
"verify gate red in monitor" flag against these two branches is a **false red** —
the same class the `gates.py` comment already names ("a gate that cannot start
is reported as the territory failing its own check, which is a lie in the
direction that looks like a verdict"), except here the gate starts fine and is
simply red on master.

The six failures are master's, and their text says so plainly — e.g.

```
E  AssertionError: probe_append_only is risk on a checkout that should be clean:
   追加式文件出现删除：PARTNER_SYNC.md（删除 3 行，超出已裁决豁免 1 行）...
E  assert 'risk' == 'green'
```

and three `reflex.py` source-marker assertions that fail because the markers
(`sweep:EXIT-`, `SUPPLY-UNKNOWN:`) are absent from `monitor/reflex.py` at
`cc7e414e`. Neither c13 nor s40 touches `scan.py` or `reflex.py`.

### Reproduction

```
.worktrees/opsm32b_arms.py                     # driver (copy of opsm31_arms.py, prefix opsm32-)
.worktrees/opsm32-out/c13/c13-mrg.gate.txt     # full gate transcript
.worktrees/opsm32-out/c13/c13-mrg.pytest.txt   # -rf re-run, every failing id named
.worktrees/opsm32-out/c13/summary.json
.worktrees/opsm32-out/s40/s40-mrg.gate.txt
.worktrees/opsm32-out/s40/s40-mrg.pytest.txt
.worktrees/opsm32-out/s40/summary.json
```

### Standing confound (not removable)

`monitor/verify.sh`'s `real run` and `board states disjoint` stages read a board,
and both arms ran concurrently with five other sibling gate runs and with the
live `ci_merge.py` queue. Both stages came back green on both arms, and the
red stage (`tests`) is the one least exposed to board state — but the honest
statement is that these are two ~13-minute windows starting 20:37 local
(12:37Z), not instantaneous snapshots. The sibling control run is authoritative
if its set differs from the six above.
