# arm-s42 — `origin/agent/s42-fleetkit-three-lies` (cycle 33, base pinned `ea4f6af6`)

Pure measurement. No adjudication, no fixes, no commits.

Standing flag under measurement: **"verify gate red in monitor (verify.sh)"**
(`monitor/ci/CONFLICT-origin_agent_s42-fleetkit-three-lies.md`).

## 1. Identity

| item | value |
|---|---|
| base (pinned) | `ea4f6af68611df19c6657ba553e72e61d9cdb84a` |
| branch tip | `835e864ef388f0f358ba3b95bc3631f342d031d7` |
| worktree | `.worktrees/opsm33-s42` (detached) |
| merge commit | `5f74addf8de1368c41299b705ada9756e58f7bef` |

## 2. Merge — CLEAN

`git merge --no-ff --no-edit origin/agent/s42-fleetkit-three-lies` → rc 0,
"Merge made by the 'ort' strategy." No conflicted paths.

Note: the first attempt was killed by a 120 s tool timeout mid-checkout and left
the worktree at `ea4f6af6` with a clean index (no partial merge). Re-run with a
600 s budget completed. Checkout of 6649 files is slow on this machine; that is a
harness artefact, not a branch property.

Diffstat, 14 files, +1891 / −91:

```
 PARTNER_SYNC.md                                    |   6 +
 fleetkit/README.md                                 |  46 +-
 fleetkit/fleetkit/__init__.py                      |   5 +-
 fleetkit/fleetkit/__main__.py                      | 106 +++++
 fleetkit/fleetkit/board.py                         | 213 +++++++---
 fleetkit/fleetkit/bus.py                           |  17 +-
 fleetkit/runs/20260730T101232Z-S42/FINDINGS.md     | 158 +++++++
 fleetkit/runs/20260730T101232Z-S42/MANIFEST.json   |  28 ++
 fleetkit/runs/20260730T101232Z-S42/RUN_STATE.md    | 205 +++++++++
 fleetkit/tests/test_documented_entry_point.py      | 173 ++++++++
 fleetkit/tests/test_lane_items_are_reachable.py    | 236 +++++++++++
 fleetkit/tests/test_sweep_does_not_free_live_claims.py | 233 ++++++++++
 fleetkit/verify.py                                 |  87 +++-
 monitor/tests/test_fleetkit_drift.py               | 469 +++++++++++++++++++++
```

The branch touches **two territories**: `fleetkit/` (code + its own tests +
verify.py) and `monitor/` (one added test file). The flag under measurement is
the `monitor` gate.

## 3. s40/s42 collision — the four cycle-32 claims, re-verified

All four **VERIFIED**. Commands and raw output:

| # | claim | result |
|---|---|---|
| 1 | both add the same path `monitor/tests/test_fleetkit_drift.py`; s40 blob `ef73603f`, s42 blob `e3c8c25e` | **VERIFIED** |
| 2 | s40 = 387 lines, s42 = 469 lines | **VERIFIED** |
| 3 | merge-base is `60def5cb` and lacks the file; neither branch is an ancestor of the other | **VERIFIED** |
| 4 | they assert opposite things about `LANE_OWNER` / `_PREFIX` | **VERIFIED**, and more sharply than stated |

```
$ git ls-tree origin/agent/s40-fleetkit-fork-has-drifted -- monitor/tests/test_fleetkit_drift.py
100644 blob ef73603fcf05edaa84d5f8957f80026fbb748afc	monitor/tests/test_fleetkit_drift.py
$ git ls-tree origin/agent/s42-fleetkit-three-lies -- monitor/tests/test_fleetkit_drift.py
100644 blob e3c8c25eada1675dd8c119a3da5627c7f819d513	monitor/tests/test_fleetkit_drift.py
$ git merge-base s40 s42
60def5cbeb97ba51ad54098e3d0306e3be79b282
$ git ls-tree 60def5cb -- monitor/tests/test_fleetkit_drift.py     # empty → absent
$ git ls-tree ea4f6af6 -- monitor/tests/test_fleetkit_drift.py     # empty → absent on the pinned base too
$ git merge-base --is-ancestor s40 s42  → false
$ git merge-base --is-ancestor s42 s40  → false
line counts: s40 387, s42 469
```

Claim 4, verbatim opposition. s40's added test asserts the defect is **still
present**:

```python
# s40 blob ef73603f, line 299
assert "LANE_OWNER = {}" in kit_src, (
    "fleetkit's LANE_OWNER is no longer the empty literal -- ...")
```

s42's added test at the same path asserts it is **gone**:

```python
# s42 blob e3c8c25e, line 372
assert "LANE_OWNER" not in bound, (
    "LANE_OWNER is back in fleetkit. If it is real this time, it needs a ...")
```

and s42's `fleetkit/fleetkit/board.py` diff makes that true by deleting the
lines (`git diff 60def5cb s42 -- fleetkit/fleetkit/board.py`):

```
-_PREFIX = ""
-LANE_OWNER = {}
-    for lane, owner in LANE_OWNER.items():
-    for lane in sorted(LANE_OWNER):
-                reserved.append((pri, iid, lane, LANE_OWNER[lane], m))
-        if len(cols) >= 3 and _PREFIX and _PREFIX in cols[0]:
```

`git show s42:fleetkit/fleetkit/board.py | grep LANE_OWNER` finds only two hits,
both inside prose comments (lines 118, 369) — no binding survives. So the two
branches are not merely an add/add conflict on a path; the surviving file
determines which assertion about `fleetkit/board.py` the monitor suite makes,
and only one of the two can be true of any single tree.

## 4. Monitor gate (as `ci_merge.py:539-544` invokes it)

Invoked through the merged tree's own `monitor/gates.py`, so the command and env
are the runner's, not a reconstruction:

```
GATE ROW: {"kind": "verify", "name": "verify.sh", "canonical": true, "decorative": false,
           "cmd": ["C:\\Program Files\\Git\\bin\\bash.exe",
                   "<wt>/monitor/verify.sh"],
           "why": "the territory ships its own completion gate"}
PYTHONPATH: C:\Users\user\Desktop\theoria\.worktrees\opsm33-s42
cwd: <wt>/monitor        timeout: 1800
```

**rc = 1. Dying stage = `tests`, but NOT by a red suite.** `verify.py` never
printed a single stage line — stdout was **empty** — and stderr is an unhandled
traceback:

```
  File "<wt>/monitor/verify.py", line 276, in verify
    label, code, detail = _tests()
  File "<wt>/monitor/verify.py", line 141, in _tests
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
         os.path.join(HERE, "tests")],
        cwd=HERE, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=900)
subprocess.TimeoutExpired: Command '[... '-m', 'pytest', '-q', '-p',
  'no:cacheprovider', '<wt>\\monitor\\tests']' timed out after 900 seconds
```

So on this run the gate did not reach a verdict at all: `_tests()`'s inner
900 s `subprocess.run` timeout fired, `TimeoutExpired` propagated out of
`verify()` → `main()` → module scope, and the process died with rc 1 and no
stdout. `ci_merge.py:545` sees rc != 0 on a `verify`-kind gate and writes
exactly the standing flag text, "verify gate red in monitor (verify.sh)".

**This differs from what the standing flag file records.** The flag
(`monitor/ci/CONFLICT-origin_agent_s42-fleetkit-three-lies.md`, base
`d1da2c9c`, 2 attempts, last 2026-07-30T13:58:23Z) carries a transcript with
`== tests FAILED(1)`, `RED: tests`, and six named failures:

```
tests/test_scan_failure_exit.py::test_a_blinded_conflict_probe_does_not_report_green
tests/test_scan_no_third_value.py::test_a_deleted_append_only_file_is_a_risk
tests/test_scan_no_third_value.py::test_all_files_present_still_reads_green
tests/test_standing_reflex_no_third_value.py::test_reflex_reads_the_return_code_of_every_child_it_scrapes
tests/test_standing_reflex_no_third_value.py::test_a_failed_git_query_skips_revival_instead_of_reviving_everyone
tests/test_standing_reflex_no_third_value.py::test_supply_unknown_is_distinct_from_supply_low_zero
```

i.e. the queue's own two attempts got a *completed* suite with six failures,
and this measurement got a 900 s timeout instead. Load is the obvious
confound — `ci_merge.py` (pid 32352) and five other cycle-33 arm agents were
running concurrently on this machine — but it is recorded here as measured, not
explained away. Whether the added `test_fleetkit_drift.py` itself is slow is
resolved in §5/§6 below.

## 4b. Note on `_tests()`'s unguarded timeout

`verify.py:141` passes `timeout=900` and does not catch `TimeoutExpired`. The
consequence is that a slow-but-passing suite and a red suite are reported
identically by `ci_merge` (rc != 0 → "verify gate red"), with the only
distinguishing evidence being an empty stdout plus a stderr traceback. Recorded
as an observation about the instrument; not adjudicated here.

## 5. `pytest -q -rf` in `<wt>/monitor`

_pending_

## 6. Third category — do s42's added tests pass against s42's own edited code?

_pending_
