# OPS-M cycle 30 — is `origin/agent/v6-v23-large-space-verdict-gap` red on its own?

Diagnostic only. Nothing under `monitor/` was modified except this report file.
No push, no commit, no network, no ARC contact.

## Subjects

| | SHA |
|---|---|
| `origin/master` (both arms' base) | `46ba6e34f43a55e40b6acef3e2164b1ec878f302` |
| `origin/agent/v6-v23-large-space-verdict-gap` (tip) | `a29e3dc04ba35168551c69593dd8c26ec0c8b7bc` |

Fetched and resolved at **2026-07-30T10:33:35Z** (`date -u`).

Branch touches two top-level dirs: `exam`, `monitor`.
Merge `--no-ff --no-edit` into a clean `origin/master` worktree: **clean, rc=0**,
27 files changed, 3017 insertions, 207 deletions. No conflicts — the gate IS
measurable.

## Method — replicating `ci_merge.py`, not `gates.run()`

`ci_merge.py:543` runs `sh(cmd, cwd=os.path.join(wt, d), timeout=1800,
extra_env=gates.gate_env(wt))`, and `ci_merge.sh` (line 92-102) builds
`env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")` then
`env.update(extra_env)`. `gates.gate_env(wt)` prepends `wt` to `PYTHONPATH`.
`gates.run()` omits all of that (it calls `gates.sh` with no `env=`), so it is
NOT what the flag came from and was deliberately not used.

`TEST_CMDS` is empty, so `ci_merge.gate_for` falls through to
`gates.gate_for` for both territories.

Driver: `.worktrees/opsm30_gate_driver.py` (gitignored dir), invoked with
Windows-native absolute worktree paths.

```
git worktree add --detach .worktrees/opsm30-v6-ctl 46ba6e34f43a55e40b6acef3e2164b1ec878f302
git worktree add --detach .worktrees/opsm30-v6-mrg 46ba6e34f43a55e40b6acef3e2164b1ec878f302
cd .worktrees/opsm30-v6-mrg && git merge --no-ff --no-edit a29e3dc04ba35168551c69593dd8c26ec0c8b7bc
python .worktrees/opsm30_gate_driver.py "C:\Users\user\Desktop\theoria\.worktrees\opsm30-v6-ctl" monitor
python .worktrees/opsm30_gate_driver.py "C:\Users\user\Desktop\theoria\.worktrees\opsm30-v6-mrg" monitor
python .worktrees/opsm30_gate_driver.py "C:\Users\user\Desktop\theoria\.worktrees\opsm30-v6-ctl" exam
python .worktrees/opsm30_gate_driver.py "C:\Users\user\Desktop\theoria\.worktrees\opsm30-v6-mrg" exam
```

Gate discovery, identical in both arms and path-existence proved before the run
(`PATH-EXISTS ...\monitor -> True`):

```
kind=verify name=verify.sh
cmd=['C:\Program Files\Git\bin\bash.exe', '<wt>/monitor/verify.sh']
PYTHONPATH=<wt>
```

## Results — monitor territory

| Arm | window (UTC) | rc | stages |
|---|---|---|---|
| CONTROL (clean master) | 10:34:48Z → 10:43:39Z | **1** | tests FAILED(1); board states disjoint ok; real run ok; artifact fields ok |
| MERGED (master + v6) | 10:43:49Z → 10:52:51Z | **1** | tests FAILED(1); board states disjoint ok; real run ok; artifact fields ok |

CONTROL failure set (6):

```
tests/test_scan_failure_exit.py::test_a_blinded_conflict_probe_does_not_report_green
tests/test_scan_no_third_value.py::test_a_deleted_append_only_file_is_a_risk
tests/test_scan_no_third_value.py::test_all_files_present_still_reads_green
tests/test_standing_reflex_no_third_value.py::test_reflex_reads_the_return_code_of_every_child_it_scrapes
tests/test_standing_reflex_no_third_value.py::test_a_failed_git_query_skips_revival_instead_of_reviving_everyone
tests/test_standing_reflex_no_third_value.py::test_supply_unknown_is_distinct_from_supply_low_zero
```

MERGED failure set (6): **byte-identical** (`diff` of the sorted sets is empty).

* MERGED \ CONTROL = ∅
* CONTROL \ MERGED = ∅

Note the flag's text said five; the measured count on clean master is **six**.

## Results — exam territory (the branch's other dir, and it runs first)

| Arm | window (UTC) | rc | verdict |
|---|---|---|---|
| CONTROL | 10:53:30Z → 10:59:18Z | **0** | GREEN (build_papers/pytest/run_exam --calibrate/run_selftest/determinism all ok) |
| MERGED | 10:59:25Z → 11:04:59Z | **0** | GREEN (same five stages) |

## VERDICT

**INNOCENT (identical failure sets).** The newest branch to be flagged inherits
the clean-master failure set exactly — same six ids, same rc, same stage
pattern — and adds nothing in either of the two territories it touches. Its own
territory (`exam`) is green in both arms. The red belongs to `origin/master`.

## Second question — is 873d62ee still the reason?

Tested tree = master `46ba6e34`. Latest commit touching `monitor/reflex.py` is
`7c1dd89b` (a merge); the last content change is **`873d62ee`** itself
(`reflex: the top-up threshold was a total, the crash was a concurrency`,
2026-07-30 12:55:40 +0800 = 04:55Z, 69 insertions / **115 deletions** for a
commit whose message describes moving one constant).

All three regressions are **STILL LIVE** as of `46ba6e34`. Quoted from
`.worktrees/opsm30-v6-ctl/monitor/reflex.py`:

**(a) unchecked git query — LIVE.** Lines 312-313:

```
312            remote = run(["git", "branch", "-r", "--list", "origin/agent/*",
313                          "--format=%(refname:short)"]).stdout.lower()
```

No `returncode` inspection; `run()` at 52-64 is a bare `subprocess.run` with no
`check=True`:

```
 63        return subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
 64                              encoding="utf-8", errors="replace", timeout=timeout)
```

A failed query yields empty stdout, so line 323 `if "agent/%s" % slug in remote`
never matches and every delivered-but-exited worker looks unrevived. `873d62ee`
deleted the guard that existed (`- if _remote.returncode != 0: events.append("revive:GIT-EXIT-%d(loop-skipped)" ...)`),
which is exactly the string
`test_a_failed_git_query_skips_revival_instead_of_reviving_everyone` searches
for and cannot find (`ValueError: substring not found`).

**(b) supply alarm swallowed — LIVE.** Lines 352-358:

```
352        try:
353            import board as board_mod
354            depth = len(board_mod.candidates())
355            if depth <= 2:
356                events.append("SUPPLY-LOW:%d" % depth)
357        except Exception:
358            pass
```

`873d62ee` deleted `+ except Exception as exc: events.append("SUPPLY-UNKNOWN:%s" ...)`
and put back `except Exception: pass`. That is the S28 defect verbatim: a broken
board is quieter than an empty one.

**(c) board headcount defaults to zero silently — LIVE.** Lines 254-259:

```
254        try:
255            import board as board_mod
256            avail = len(board_mod.candidates())
257            claimed = len(board_mod.claimed_map())
258        except Exception:
259            avail, claimed = 0, 0
```

`873d62ee`'s diff removes the S28 comment block and the reporting
`except Exception as exc:` handler, restoring the bare `except Exception:`.

**Nothing has been fixed since 10:00Z.** No commit touches `monitor/reflex.py`
after `873d62ee`'s content change.

**But 873d62ee is only 3 of the 6 failures.** The other three live in
`monitor/scan.py`, which `873d62ee` never touched. Measured directly on the
CONTROL arm, `test_a_blinded_conflict_probe_does_not_report_green` fails with:

```
E       AssertionError: and it is `missing`, not `risk`: no evidence is not evidence of a conflict
E       assert 'risk' == 'missing'
```

i.e. `scan.probe_conflicts()` with a blinded `git_or_none` returns `risk` where
the test demands `missing`. Last content commits on `monitor/scan.py`:
`5e245532` (S36) then `fad88ca3`; the tests were landed/extended by `c8061d7b`.
So master's red has **two** independent sources, and reverting `873d62ee` alone
would clear only the three `test_standing_reflex_no_third_value` failures.
