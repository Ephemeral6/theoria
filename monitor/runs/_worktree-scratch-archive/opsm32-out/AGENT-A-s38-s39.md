# OPS-M cycle 32 — Agent A: are s38 and s39 guilty of the monitor verify red?

Measured 2026-07-30 by a measurement subagent. Nothing in the main checkout was
modified; all work happened in three fresh detached worktrees under
`.worktrees/opsm32-*` and all output under `.worktrees/opsm32-out/`.
No `git fetch` was run — remote-tracking refs as they already stood were used.

## Shas

| ref | sha |
|---|---|
| master HEAD (main checkout) | `cc7e414eb3bfde3325a50f9ce0e8dc896bda2b84` |
| `origin/master` | `cc7e414eb3bfde3325a50f9ce0e8dc896bda2b84` (identical — matters for s38, see below) |
| `origin/agent/s38-append-only-probe-branch-blind` | `9f8d94e3754d40be773fe05563f9b7e572bd6c13` |
| `origin/agent/s39-writes-into-the-live-master-tree` | `a03fde2fa1ef5a023ebd6005988bea91b398b709` |
| arm `ctl` HEAD | `cc7e414e` (detached, no merge) |
| arm `s38-mrg` HEAD | `0beefcc449f6f2e085cef18ba96a693828688804` |
| arm `s39-mrg` HEAD | `7670ceb5fabea98c1aa285d02dc7ca067ae5e11e` |

## Merge cleanliness

Both merges are clean. No conflicts, no conflict files, working tree empty
after each (`git status --porcelain` silent).

**s38** — `Merge made by the 'ort' strategy`, auto-merged `PARTNER_SYNC.md`.
`git diff --stat cc7e414e..HEAD | tail -1`:

```
 7 files changed, 619 insertions(+), 4 deletions(-)
```

Files: `PARTNER_SYNC.md`, `monitor/scan.py` (+51/-4),
`monitor/tests/test_append_only_probe_anchor.py` (new, 154 lines),
`monitor/runs/20260730T0410Z-S38/{MANIFEST.json,RUN_STATE.md,measure.json,measure.py}`.

**s39** — `Merge made by the 'ort' strategy`, auto-merged `PARTNER_SYNC.md`.
`git diff --stat cc7e414e..HEAD | tail -1`:

```
 8 files changed, 2310 insertions(+)
```

Files: `PARTNER_SYNC.md`, `monitor/master_tree_guard.py` (new, 816 lines),
`monitor/scan.py` (+74, new `probe_master_tree` registered in `PROBES`),
`monitor/tests/test_master_tree_guard.py` (new, 808 lines),
`monitor/runs/20260730T0440Z-S39/*`.

## New-test provenance (the "third category" check)

Both branches introduce a test file that does not exist on master:

```
git cat-file -p cc7e414e:monitor/tests/test_append_only_probe_anchor.py  -> ABSENT
git cat-file -p cc7e414e:monitor/tests/test_master_tree_guard.py         -> ABSENT
git cat-file -p cc7e414e:monitor/master_tree_guard.py                    -> ABSENT
```

So if either arm shows an ADDED failing id inside one of those files, the
correct reading is *not* "the branch broke the gate" — it is "the branch
shipped a new test". Whether that is a defect in the branch or a pre-existing
defect in master that the new test correctly catches has to be read off the
failure text, and is recorded per-id below.

## Method

`.worktrees/opsm32_arms.py` (a copy of last cycle's `opsm31_arms.py` with the
worktree prefix changed to `opsm32-`) invokes the gate exactly as
`monitor/ci_merge.py` does: command from `gates.gate_for(wt, "monitor")`,
env = `os.environ` + `PYTHONIOENCODING=utf-8`/`PYTHONUTF8=1` + `gates.gate_env(wt)`,
cwd `<wt>/monitor`, timeout 1800. It then re-runs the same pytest invocation the
gate's `tests` stage runs, with `-rf` added so every failing id is named
(the gate truncates its per-stage detail to the last 2000 chars).

**Standing confound, not removable:** `monitor/verify.sh` has stages that read
the *live* board under `monitor/board/`, and the three arms run sequentially
over ~20 minutes. A difference between arms can in principle be board drift
rather than branch effect. This is why the control is re-measured in the same
sitting rather than reusing last cycle's six ids. Where a set difference is
reported below, the note says whether it is board-sensitive.

## Arm `ctl` — the control (master alone, no branch)

`.worktrees/opsm32-out/ctl.gate.txt`. Gate rc **1**. Gate command as invoked:

```
['C:\\Program Files\\Git\\bin\\bash.exe',
 'C:/Users/user/Desktop/theoria/.worktrees/opsm32-ctl/monitor/verify.sh']
cwd: C:\Users\user\Desktop\theoria\.worktrees\opsm32-ctl\monitor
```

Stage lines:

```
== tests              FAILED(1)
== board states disjoint ok
== real run           ok
== artifact fields    ok
RED: tests
```

**`tests` is the only red stage** — the three board/artifact-reading stages are
green, so the board's live state is not what is failing here.

Control failing-id set (6), verbatim from the gate's own summary:

```
tests/test_scan_failure_exit.py::test_a_blinded_conflict_probe_does_not_report_green
tests/test_scan_no_third_value.py::test_a_deleted_append_only_file_is_a_risk
tests/test_scan_no_third_value.py::test_all_files_present_still_reads_green
tests/test_standing_reflex_no_third_value.py::test_reflex_reads_the_return_code_of_every_child_it_scrapes
tests/test_standing_reflex_no_third_value.py::test_a_failed_git_query_skips_revival_instead_of_reviving_everyone
tests/test_standing_reflex_no_third_value.py::test_supply_unknown_is_distinct_from_supply_low_zero
```

This is **identical** to the set OPS-M measured last cycle. Master's own monitor
gate is red on its own, at the current tip, with no branch merged in. Anything
the queue rejects with "verify gate red in monitor (verify.sh)" inherits at least
these six.

### What the control's red actually is (matters for reading s38)

Two of the six are `probe_append_only` returning `risk` against the live repo.
The failure text names the cause:

```
E  AssertionError: probe_append_only is risk on a checkout that should be clean:
   追加式文件出现删除：PARTNER_SYNC.md（删除 3 行，超出已裁决豁免 1 行）…
```

and its positive twin fails for the same reason — it constructs a *different*
violation (`battery/PREDICTIONS.md` absent) and then finds the detail string
talking about `PARTNER_SYNC.md` instead:

```
E  AssertionError: assert 'battery/PREDICTIONS.md' in '追加式文件出现删除：
   PARTNER_SYNC.md（删除 3 行，超出已裁决豁免 1 行）…'
```

So on master, `PARTNER_SYNC.md` carries **3 deleted lines on the first-parent
mainline against a `BASELINE` exemption of 1**. That is a live append-only
finding on master itself, not a flake and not a branch's doing. It is worth
noting that this is the *published-lines* half of the rule — the half s38
explicitly keeps ("一条净删除了已发布行的分支仍然红") — so s38 is not expected to
clear it, and if s38 *did* clear it that would be evidence the fix removed the
gate's teeth rather than its blindness.

## Side finding on s39, independent of the verdict

`probe_master_tree` deliberately judges the **main** worktree, not the worktree
`scan.py` happens to sit in:

```python
main = mtg.main_worktree(ROOT)
result = mtg.report(main)
hooked = mtg.hook_installed(main)
```

`master_tree_guard._run` (line ~216 of `monitor/master_tree_guard.py` on the
branch) shells out as `git status --porcelain -z` with **no
`--no-optional-locks`**. `git status` refreshes the index, so every run of this
probe from any worktree takes `.git/index.lock` in the *shared main checkout*.
It changes no file content and no tracked file, so it is not a correctness bug —
but it means the probe writes a lock into the live tree it is auditing, on every
`scan.build`, concurrently with the `ci_merge.py` queue. `--no-optional-locks`
(or `-c core.fsmonitor=false` plus it) would remove the race for free. Worth
raising with S39 regardless of the merge verdict.

The branch's own test suite is safe to run: every `install_hook`,
`precommit` and `main_worktree` test operates on a `tmp_path` repo fixture, not
on the live tree.

## STATUS: s38-mrg and s39-mrg still in flight

Merges are done and clean (above); the control is measured. The two merged arms
are running and are appended below as they land. Do not read the absence of a
verdict section as a verdict.
