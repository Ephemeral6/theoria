# OPS-M cycle 30 — do s39 / s40 add any gate red of their own?

Written incrementally. Started 2026-07-30T10:32:58Z.

## Fixed points

| thing | value |
|---|---|
| `origin/master` (control base) | `46ba6e34f43a55e40b6acef3e2164b1ec878f302` |
| `origin/agent/s39-writes-into-the-live-master-tree` tip | `a03fde2fa1ef5a023ebd6005988bea91b398b709` |
| `origin/agent/s40-fleetkit-fork-has-drifted` tip | `9ca9278a1637ae6f41a3e02fc05637fc2f5ed870` |
| s39 merge-base with master | `3d59d0a63cffeb0e1f865c2bacc8508c5232087b` |
| s40 merge-base with master | `60def5cbeb97ba51ad54098e3d0306e3be79b282` |

Four worktrees, all created at `46ba6e34` (no shared control — each branch got
its own control arm, so a control run cannot be contaminated by the other
branch's merged arm):

```
.worktrees/opsm30-s39-ctl   46ba6e34 (detached)
.worktrees/opsm30-s39-mrg   46ba6e34 + git merge --no-ff --no-edit <s39>  -> f96ec35d0a6b4559d1181e3fabc5f5f471d82f27
.worktrees/opsm30-s40-ctl   46ba6e34 (detached)
.worktrees/opsm30-s40-mrg   46ba6e34 + git merge --no-ff --no-edit <s40>  -> 9b975784a43588d6c8843b497e90ae724d40566f
```

Both merges succeeded with rc 0. **No conflict on either branch**, so the gate
is measurable in all four arms.

## Territories each branch touches

```
$ git diff --name-only origin/master...<branch>
```

s39: `PARTNER_SYNC.md`, `monitor/master_tree_guard.py`, `monitor/scan.py`,
`monitor/tests/test_master_tree_guard.py`, `monitor/runs/20260730T0440Z-S39/*` (4 files)

s40: `monitor/tests/test_fleetkit_drift.py`, `monitor/runs/20260730T0625Z-S40/*` (2 files)

Both branches touch exactly one territory: `monitor`. So the monitor gate is
the whole question.

Note already visible statically and worth flagging up front: **s40 adds
`monitor/tests/test_fleetkit_drift.py`, a new test file inside the directory the
monitor gate runs pytest over.** "It does not touch reflex.py" does not imply
"it cannot add red" — the gate's first stage is
`python -m pytest -q -p no:cacheprovider monitor/tests`, which collects any new
file. The static reading last cycle did not account for this.

## How the gate was run — replicating ci_merge, not gates.run()

`monitor/ci_merge.py:526-544`:

```python
row = gate_for(wt, d)                      # -> gates.gate_for
r = sh(row["cmd"], cwd=os.path.join(wt, d), timeout=1800,
       extra_env=gates.gate_env(wt))
```

with `sh()` (`ci_merge.py:92`) building
`env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")` then
`env.update(extra_env)`; `gates.gate_env(wt)` adds `PYTHONPATH=<wt>`.
`gates.run()` omits the env entirely, which is the measured defect the brief
warns about — it was not used.

Driver: `C:\Users\user\AppData\Local\Temp\opsm30_gate.py` (outside the repo,
nothing under `monitor/` was modified). It asserts the territory dir exists and
that `gate_for` returned `kind == "verify"` before running, so a
"no verify script" answer cannot be confused with a missing path. Discovery used
each arm's own `monitor/gates.py`; the resolved gate is `monitor/verify.sh` ->
`bash monitor/verify.sh` -> `python monitor/verify.py` in every arm.

Each arm ran twice:
1. the gate exactly as ci_merge runs it (gives the rc ci_merge would flag on);
2. the gate's own `tests` stage verbatim (`verify.py::_tests`) plus `-rf`, same
   cwd and env, because `verify.py` truncates each stage's detail to the last
   2000 chars and that can cut the failing-id list.

Exact command per arm:

```
python C:\Users\user\AppData\Local\Temp\opsm30_gate.py \
  C:\Users\user\Desktop\theoria\.worktrees\opsm30-<arm> monitor \
  C:\Users\user\Desktop\theoria\.worktrees\opsm30-<arm>\monitor \
  <label> C:\Users\user\AppData\Local\Temp\opsm30-out
```

## Results

(filled in as arms complete)

### s39 CONTROL (46ba6e34, clean master) — gate rc 1, RED

Stage table: `tests FAILED(1)`, `board states disjoint ok`, `real run ok`,
`artifact fields ok`. Verdict line `RED: tests`.

Failing set (6) from the gate's own short summary:

```
tests/test_scan_failure_exit.py::test_a_blinded_conflict_probe_does_not_report_green
tests/test_scan_no_third_value.py::test_a_deleted_append_only_file_is_a_risk
tests/test_scan_no_third_value.py::test_all_files_present_still_reads_green
tests/test_standing_reflex_no_third_value.py::test_reflex_reads_the_return_code_of_every_child_it_scrapes
tests/test_standing_reflex_no_third_value.py::test_a_failed_git_query_skips_revival_instead_of_reviving_everyone
tests/test_standing_reflex_no_third_value.py::test_supply_unknown_is_distinct_from_supply_low_zero
```

Consistent with the known root cause: 873d62ee reverted three guards in
`monitor/reflex.py`; the reflex tests assert on the source text of the reverted
guards (`substring not found`, `'SUPPLY-UNKNOWN:' in src`).

## Condition of the machine during measurement (recorded, not excused)

`Get-Process python` at 2026-07-30T10:55Z shows the box saturated: the live
`ci_merge.py` plus at least five OTHER OPS-M cycle-30 gate measurements
(`opsm30-v6-mrg`, `opsm30-a3-mrg`, `opsm30-c13-ctl`, `opsm30-adv-7972`,
`advref29-m`) running the same monitor suite concurrently, plus `scan.py` and
three `_runner.py` workers. One monitor gate that should take ~2 min took ~8.
Because ambient load varies minute to minute, the s39 merged arm and both s40
arms were launched **concurrently** rather than one after another, so all arms
see comparable contention instead of the control getting a quiet box and the
merged arm a busy one. Any arm-to-arm difference is re-run before being called
a finding.

Master did not move during the measurement: `origin/master` was
`46ba6e34` at 2026-07-30T10:32:58Z and still `46ba6e34` at
2026-07-30T11:06:10Z.

### All four arms — the numbers

| arm | HEAD | gate rc | tests collected | failing ids |
|---|---|---|---|---|
| s39 CONTROL | `46ba6e34` | **1 (RED)** | 397 | 6 |
| s39 MERGED  | `f96ec35d` | **1 (RED)** | 446 (+49) | 6 |
| s40 CONTROL | `46ba6e34` | **1 (RED)** | 397 | 6 |
| s40 MERGED  | `9b975784` | **1 (RED)** | 409 (+12) | 6 |

Collected counts read off pytest's progress bar (72 chars per line; last line
partial). They matter: they are the proof the merged arms **actually collected
the branches' new test files** rather than the failure sets matching because
nothing new ran. s39 adds 49 passing tests (`test_master_tree_guard.py`,
808 lines); s40 adds 12 passing tests (`test_fleetkit_drift.py`, 387 lines).
Neither adds a single F.

The failing set is the same six in all four arms:

```
tests/test_scan_failure_exit.py::test_a_blinded_conflict_probe_does_not_report_green
tests/test_scan_no_third_value.py::test_a_deleted_append_only_file_is_a_risk
tests/test_scan_no_third_value.py::test_all_files_present_still_reads_green
tests/test_standing_reflex_no_third_value.py::test_a_failed_git_query_skips_revival_instead_of_reviving_everyone
tests/test_standing_reflex_no_third_value.py::test_reflex_reads_the_return_code_of_every_child_it_scrapes
tests/test_standing_reflex_no_third_value.py::test_supply_unknown_is_distinct_from_supply_low_zero
```

The four gate transcripts are **byte-identical** (`md5 e296e893054cb3035ff9354a0bf8e577`
on all of `s39-ctl.gate.txt`, `s39-mrg.gate.txt`, `s40-ctl.gate.txt`,
`s40-mrg.gate.txt`). Stage-by-stage in every arm: `tests FAILED(1)`,
`board states disjoint ok`, `real run ok`, `artifact fields ok`, verdict
`RED: tests`.

Caveat on that identity, stated so it is not over-read: `verify.py` truncates
each stage's detail to the last 2000 chars, and `pytest -q` here emits no
"N failed, M passed in Xs" line, so the transcript window contains only the
FAILURES tail and the short summary. Byte-identity therefore proves the same
failing set, not the same test total — the totals come from the separate `-rf`
runs above and they differ, correctly.

No arm left the tree dirty: `git status --porcelain --untracked-files=all --
monitor` is empty in all four worktrees after the run (ignoring `__pycache__`),
so `dirty`/`drift` does not enter either verdict.

## VERDICTS

### `origin/agent/s39-writes-into-the-live-master-tree` @ `a03fde2f`

* control (`46ba6e34`): rc 1, 6 failures listed above
* merged (`46ba6e34` + merge = `f96ec35d`): rc 1, the same 6
* merged − control = **∅**
* control − merged = **∅**
* **VERDICT: INNOCENT (identical failure sets).** The gate is red in the merged
  arm for exactly the reason it is red on clean master — the three guards
  873d62ee reverted in `monitor/reflex.py`, plus the three `scan` no-third-value
  tests. s39's own 49 tests all pass, its new `probe_master_tree` does not crash
  `scan.build` (`real run ok`), and the artifact-fields stage stays green.

### `origin/agent/s40-fleetkit-fork-has-drifted` @ `9ca9278a`

* control (`46ba6e34`): rc 1, the same 6 failures
* merged (`46ba6e34` + merge = `9b975784`): rc 1, the same 6
* merged − control = **∅**
* control − merged = **∅**
* **VERDICT: INNOCENT (identical failure sets).** Its 12 new tests were
  collected and all passed.

### Did the prior static "s40 is innocent" reading survive the run?

**Yes — but its reasoning did not, and should not be reused.** The conclusion
is confirmed by measurement. The argument given for it ("it only adds three new
files and touches neither `reflex.py` nor the guard tests") is not a valid one:
one of those three added files is `monitor/tests/test_fleetkit_drift.py`, which
lands inside the exact directory the monitor gate runs pytest over, and it
asserts against `monitor/board.py` vs `fleetkit/fleetkit/board.py` in the
*merged* tree. A file that adds 12 collected tests to the gated suite can add
red without touching one line of `reflex.py`; "touches no existing file" is not
"cannot fail the gate". It passed here for a checkable reason, not a structural
one: nothing on master has touched `monitor/board.py` or `fleetkit/` since
s40's merge-base (`git log 60def5cb..origin/master -- monitor/board.py
fleetkit/` is empty), so the branch's DECLARED-divergence table is still
accurate against the merged tree. If master later changes `board.py`, that
same file is a live candidate for new red and must be re-measured, not
re-reasoned.

## Reproduce

```
git worktree add --detach .worktrees/opsm30-s39-ctl 46ba6e34
git worktree add --detach .worktrees/opsm30-s39-mrg 46ba6e34
git -C .worktrees/opsm30-s39-mrg merge --no-ff --no-edit \
    origin/agent/s39-writes-into-the-live-master-tree
git worktree add --detach .worktrees/opsm30-s40-ctl 46ba6e34
git worktree add --detach .worktrees/opsm30-s40-mrg 46ba6e34
git -C .worktrees/opsm30-s40-mrg merge --no-ff --no-edit \
    origin/agent/s40-fleetkit-fork-has-drifted

python C:\Users\user\AppData\Local\Temp\opsm30_gate.py \
    C:\Users\user\Desktop\theoria\.worktrees\opsm30-<arm> monitor \
    C:\Users\user\Desktop\theoria\.worktrees\opsm30-<arm>\monitor \
    <label> C:\Users\user\AppData\Local\Temp\opsm30-out
```

Raw transcripts: `C:\Users\user\AppData\Local\Temp\opsm30-out\{s39,s40}-{ctl,mrg}.{gate.txt,pytest.txt,json}`.

Nothing was pushed, nothing under `monitor/` was modified except this new
findings file, no test was edited or skipped, and no network or API call was
made.

Finished 2026-07-30T11:06:10Z.
