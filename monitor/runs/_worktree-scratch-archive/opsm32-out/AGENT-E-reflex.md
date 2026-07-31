# AGENT-E — why reflex cycles die without a line, and the patch

OPS-M cycle 32. Written as the work happened; every claim is tagged
**OBSERVED** (I have the bytes) or **INFERRED** (it follows from observed
things plus source reading).

Verdict up front: **H1 survives, and it is no longer a hypothesis — I caught
the mechanism live, with reflex's own `scan.py` child in the process table.**

---

## 1. The mechanism

`monitor/reflex.py:361` (at master `cc7e414e`) is

```python
        # 5. light dashboard refresh
        run([sys.executable, os.path.join(HERE, "scan.py")], timeout=600)

        rlog(" | ".join(events) if events else "quiet")
```

`run()` is `subprocess.run(..., timeout=timeout)`. It is **not** inside a
`try`. When the 600 s deadline fires, `subprocess.run` kills the child and
raises `subprocess.TimeoutExpired`, which propagates out of `main()` past the
`rlog()` two lines below. The `finally:` at 365 removes the lock, so the next
tick is admitted normally — the cycle simply vanishes with **no line in
`reflex.log` at all**, which is byte-identical to a cycle the scheduler never
started. (OBSERVED: source. INFERRED: nothing — this is what the code says.)

`scan.py` under fleet load takes far longer than 600 s. **MEASURED**, three
independent ways, all on 2026-07-30:

| instance | started | ended | runtime |
|---|---|---|---|
| pid 35256, `TheoriaDashboard` → `refresh.cmd` (no timeout, ran to completion) | 12:20:01Z | between 12:46:10Z and 12:46:42Z | **1571–1602 s (~26 min)** |
| pid 39452, my own hand-timed run (`--out-dir` into `.worktrees/opsm32-out/scanprobe`) | 12:41:24Z | still running at 12:56:43Z | **> 920 s and counting** |
| pid 18472, **reflex 6328's own child** | ~12:42:15Z | between 12:51:58Z and 12:52:29Z | **~600 s — killed at the deadline** |

All three OBSERVED, from `.worktrees/opsm32-out/prediction2b.log` and
`.worktrees/opsm32-out/scan-timing.txt`.

Two honest caveats on the measurement. (i) My own hand-timed run is itself
extra load, so from 12:41 onwards there were up to three concurrent
`scan.py` processes; the ~26 min figure for pid 35256 covers 12:20–12:46, i.e.
only its last five minutes overlap mine. (ii) I ran `scan.py` with
`--out-dir .worktrees/opsm32-out/scanprobe` **from the main checkout**, not in
a worktree, after verifying every write site honours `out_dir`: `index.html`
and `state.json` (`scan.py:2716`, `2757`), `history.jsonl`
(`append_history`, `scan.py:1554`), `crashes.jsonl` (`record_crash`,
`scan.py:3015`) and the failure page (`write_failure`). Everything else it
does to the main tree is read-only (`git worktree list`, `git check-ignore`,
`board.py list`, `tasklist`); the pytest subprocess at `scan.py:1458` is behind
`--tests`, which I did not pass. No tracked file in the main checkout was
touched.

So: `scan.py` needs ~26 min, reflex grants it 600 s, and the timeout is fatal
and silent. **Every** cycle dies there. That is why `reflex.log`'s last
end-of-cycle line is `2026-07-30T01:33:34Z` (line 275) while the file's last
line is `08:32:21Z` — the later lines are the *mid-cycle* quota `rlog()` at
`reflex.py:234`, written by cycles that then died at the scan. OBSERVED.

### The live prediction, and it fired

I ran a 30 s poller (`.worktrees/opsm32-out/watch_prediction2.sh` →
`prediction2b.log`) over reflex pid 6328. Prediction recorded before the fact:
*ci_merge 2592 exits on its own well under its 3600 s timeout; ~600 s later
6328 dies with no new `reflex.log` line.*

OBSERVED, verbatim from the log:

```
12:41:58Z procs=[... reflex:6328(ppid2360,898s) ci_merge:2592(ppid6328,790s) ...] reflexlog=280
12:42:29Z procs=[... reflex:6328(ppid2360,929s) ... scan:18472(ppid6328,14s)]    reflexlog=280 mergelog=2170
...
12:51:58Z procs=[reflex:6328(ppid2360,1498s) ... scan:18472(ppid6328,583s) ...]  reflexlog=280
12:52:29Z procs=[scan:39452(...) scan:31304(...)]                               reflexlog=280
```

Read it line by line:

* ci_merge 2592 lived **790–820 s** — a fifth of its 3600 s timeout — and
  wrote two more `merge.log` lines on the way out (2168 → 2170). It exited on
  its own.
* At 12:42:29 a **new `scan.py`, pid 18472, whose parent is 6328**, is 14 s
  old. So reflex launched it at ~12:42:15Z, immediately after ci_merge
  returned. This is the smoking gun: the child is named, parented, and
  timestamped.
* 18472 reached 583 s at 12:51:58 and **both it and reflex 6328 were gone by
  12:52:29**. 12:42:15 + 600 = 12:52:15Z, inside the observation window.
* `reflex.log` stayed at **280 lines throughout**. The cycle left nothing.

The parent and the child dying inside the same 31 s window is what a
`subprocess.run` timeout looks like: `run()` kills the child, then raises into
an unguarded caller.

A third cycle was already in flight when I stopped: reflex pid **30148**
started 12:57:01Z (the first tick after 6328 died — the scheduler had been
refusing ticks at 12:32/12:37/12:42/12:47/12:52 under `IgnoreNew`), and
launched ci_merge pid 39280 at ~12:58:52Z. `reflex.log` was still at 280 lines
at 13:01:00Z. `prediction2b.log` keeps running to ~13:31Z; the same signature
(ci_merge exits → a `scan.py` child with ppid 30148 appears → both it and
30148 vanish ~600 s later, no new `reflex.log` line) is the standing prediction
and the log is the record.

### The earlier cycle, retro-fitted

The cycle before (reflex 42104 / ci_merge 2220, from
`.worktrees/opsm31-out/prediction-check.log`) fits the same arithmetic.
OBSERVED: `merge.log`'s last line of that pass is `12:14:21Z`; ci_merge 2220
was alive at 12:14:05 and gone by 12:14:36; reflex 42104 was alive at 12:23:56
and gone by 12:24:28. That is **560–607 s** of parent life after the child
returned, with `reflex.log` pinned at 280 lines. Same shape, same number.

---

## 2. Refutation attempts

I tried to break H1 before believing it. What each attempt found:

**H3 — "ci_merge was killed by its own 3600 s timeout and the arithmetic is
wrong." REFUTED, three ways.**

1. The decisive structural point: `run()` at 345 is **also** unguarded. If
   ci_merge had hit its deadline, `TimeoutExpired` would have propagated *at
   that instant* and reflex would have died within a second of its child, not
   ~600 s later. The gap alone refutes it. (INFERRED from source; the source is
   unambiguous.)
2. The cycle-32 repeat measured ci_merge 2592 directly at **790–820 s**, i.e.
   22 % of its timeout. OBSERVED.
3. `merge.log` shows the 11:25→12:14 pass ending cleanly rather than being cut
   mid-branch: `ci_merge.main()` walks the whole `todo` list and only breaks
   early after `--max` (default 2) *successful* merges. That pass produced 15
   `FLAG` lines and zero `MERGED`, so `done` stayed 0 and the loop ran to the
   end of the list; v6 was the last entry, flagged at 12:14:21Z, and the
   process was gone ~15 s later. OBSERVED (`merge.log:2152-2166`) + INFERRED
   (`ci_merge.py:663-700`).
   * Caveat, stated so nobody over-reads it: the absence of a trailing `HELD`
     line in that pass is **not** evidence of truncation. `HELD` is emitted
     only when `should_hold` actually held something, and master moved at
     11:09 (the p18 merge), which invalidates every memo's base check — so
     that pass legitimately re-verified everything and held nothing.
   * `merge.lock` cannot discriminate: `take_lock()` treats a lock older than
     3600 s as stale, and the gap from 2220's lock to 2592's start is ~3890 s,
     so "released cleanly" and "discarded as stale" predict the same outcome.
     The lock is a dead instrument here; I did not lean on it. (INFERRED,
     `ci_merge.py:429-438`.)

**H2 — "reflex died of something else after ci_merge returned." REFUTED for
every candidate I could name.**

* *Machine sleep / hibernate / resume.* No `Kernel-Power` 42/107 and no
  resume events in the System log for the last 24 h. OBSERVED
  (`Get-WinEvent -FilterHashtable @{LogName='System'; Id=42,107,...}` → empty).
* *Process crash.* Zero `Error`-level Application-log entries in 24 h. No
  WER/faulting-application record. OBSERVED.
* *The scheduler's own limits.* `TheoriaReflex` has
  `ExecutionTimeLimit=PT72H`, `MultipleInstances=IgnoreNew`, `RestartCount=0`.
  A 25-minute cycle is nowhere near 72 h. OBSERVED. (`StopIfGoingOnBatteries`
  is `True`, but there was no battery transition — see the sleep check.)
* *An external watchdog killing reflex on its own age.* REFUTED by the two
  cycles having very different total lifetimes but the **same** post-scan
  interval: 42104 lived 11:17:01→~12:24 (**~4020 s**), 6328 lived
  12:27:01→~12:52:15 (**~1514 s**), and both died ~600 s after their `scan.py`
  child was spawned. A watchdog keyed on reflex's age would give a constant
  total lifetime; a 600 s child deadline gives exactly what was seen.
  OBSERVED. Also, nothing in `monitor/*.py` kills reflex —
  `grep -rn reflex monitor/*.py | grep -iE 'kill|taskkill|terminate|Stop-Process'`
  is empty. OBSERVED.
* *An exception in `merge_events(r)` or the SUPPLY block.* Both would raise
  within milliseconds of ci_merge returning, not 600 s later; and the SUPPLY
  block is already inside `try/except Exception`, so it cannot propagate at
  all. INFERRED from source, and independently ruled out by cycle 32's
  observation of the `scan.py` child actually being spawned *after* those
  blocks ran.

**H4 — "scan.py is fast and something else is slow." REFUTED by measurement.**
See the table above: 1571–1602 s for a completed run. Also note the
`TheoriaDashboard` task's `LastTaskResult` at 20:40:01 local was
`2147946720` = `0x800710E0` — the scheduler refusing a new instance because
the 12:20 one was still going. Its own 10-minute cadence is being outrun by
its own scan. OBSERVED.

Corroborating, weaker, and worth having anyway: `monitor/refresh.log`'s
`index.html written` stamps (local time, UTC+8) for this afternoon run
15:59:01, 16:23:13, **17:54:32**, 18:33:30, **19:41:19**, 20:17:35, 20:45:42.
Consecutive gaps of 24, 91, 39, 68, 36 and 28 minutes against a **10-minute**
task cadence. These gaps are upper bounds on runtime rather than runtimes
(each includes the wait for the next tick), so they do not measure `scan.py`
— but any gap over 10 minutes is proof the previous instance overran. It has
been overrunning all afternoon. OBSERVED.

**Event-log / stderr sinks — checked, and there is nothing.**
`Microsoft-Windows-TaskScheduler/Operational` is `IsEnabled: False`
(OBSERVED via `Get-WinEvent -ListLog`, so this is verified, not assumed).
`Microsoft-Windows-TaskScheduler/Maintenance` is enabled but contains no
`Theoria*` records. The `TheoriaReflex` action is
`"D:\Miniforge3\python.exe" "…\monitor\reflex.py"` with **no redirect and no
`WorkingDirectory`** — so the traceback from the fatal `TimeoutExpired` is
written to a console that does not exist and is discarded. There is no sink
anywhere. (Contrast `TheoriaDashboard`, whose `refresh.cmd` does
`>> monitor\refresh.log 2>&1`; reflex has no equivalent.) OBSERVED.

**What survived:** H1, upgraded from inference to direct observation.

### Two side findings worth the monitor's attention

1. **`scan.py`'s docstring lies about reflex.** `scan.py:3134-3137` says
   *"Non-zero so a caller can tell. `reflex.py` now checks this; before S30 it
   discarded the return code."* Master `cc7e414e` line 361 discards it: the
   call's result is not assigned. A crashed scan is invisible to reflex today.
   OBSERVED. The patch fixes it (`scan:EXIT-%d`).
2. **An overrun tick leaves no trace anywhere.** The scheduler is the real
   mutual exclusion (`IgnoreNew`), so reflex's own 1500 s stale-lock path never
   fires; and the scheduler's refusals go only to the disabled Operational
   log. `LastTaskResult 2147946720` on `Get-ScheduledTaskInfo` is a *current*
   value, not a history. So during the outage there was no record of the
   refused ticks either. OBSERVED.

---

## 3. The patch — `REFLEX_PATCH.diff`

A real unified diff against `monitor/reflex.py` at master `cc7e414e`
(255 lines). **Not applied** — it is a file, the monitor applies it.

It is **not** "a revert of `873d62ee`". `873d62ee` did not delete a
ci_merge-timeout guard — that guard never existed — and one of the four
returncode checks it removed was already restored by `c8061d7b`. What the
patch *adds*, exactly:

**(a) No child call can kill a cycle silently.**
* New `class Unfinished` — a result stand-in with `returncode = -1`,
  `stdout = ""`, `stderr = <why>` — and `run_guarded(args, timeout, tag,
  events)`, which turns `TimeoutExpired` into `"<tag>:TIMEOUT(<n>s)"` and
  `OSError` into `"<tag>:SPAWN-FAILED:<type>"` and hands back a result instead
  of raising. Non-zero on purpose, so the existing `EXIT-` alarms also fire —
  a killed child must not read as a clean no-op (S28 finding 10).
* Applied to the ci_merge call (was 344-347) and the `scan.py` call (was 361),
  plus the board sweep, the reaper, and the git query.
* `MERGE_TIMEOUT_S = 3600` / `SCAN_TIMEOUT_S = 600` are hoisted to named
  constants with the measurement in the comment. **I did not change the 600.**
  Raising it is a real judgment (a cycle would then be able to exceed the
  5-minute tick interval by design) and it belongs to the monitor, not to a
  forensics agent. What the patch guarantees is that the timeout is now an
  *event*: post-patch, today's machine would log
  `… | scan:TIMEOUT(600s) | scan:EXIT--1 killed at the 600s deadline`
  every cycle instead of nothing. That line is the argument for raising it.
* A backstop `except BaseException` around the whole cycle body writes
  `CYCLE-DIED:<Type> <last traceback line>` to `reflex.log` and then
  re-raises. This is what makes silence impossible *by construction* rather
  than site by site — the named guards will always be one call behind the next
  person who adds a child.

**(b) "Did not finish" is now distinguishable from "did not run."**
* `rlog("cycle-start pid=%d")` immediately after the lock is taken. The
  end-of-cycle line is written by the **parent** after every child returns, so
  it is exactly the line that goes missing when the parent is the thing
  failing — and `merge.log`, the instrument OPS-M reached for twice, is
  written by the ci_merge **child**, so it is brightest precisely then.
* `stale-lock: removed a lock <n>s old …` when the previous cycle died without
  releasing it.
* `cycle-skip: previous reflex still holds the lock (<n>s old)` — but only
  above 900 s (three ticks), so routine overlap stays silent while a genuinely
  stuck cycle becomes loud.
* Cost, stated honestly: one extra short line per cycle. At the current
  ~25-minute cycle that is ~2-3 lines/hour.

**(c) The three red tests, greened by editing `reflex.py` alone.** Nothing else
needs to change.
* `test_reflex_reads_the_return_code_of_every_child_it_scrapes` — adds
  `sweep:EXIT-`, `reap:EXIT-`, `revive:GIT-EXIT-` (`merge:EXIT-` already
  existed in `merge_events`), and removes both banned shapes
  `"--reap"]).stdout` and `"--format=%(refname:short)"]).stdout`.
* `test_a_failed_git_query_skips_revival_instead_of_reviving_everyone` — the
  literal `events.append("revive:GIT-EXIT-%d(loop-skipped)"` is present and
  the whole revive loop now sits under the `else:` of the git guard, so a
  failed query **skips** the loop. The failure direction here spends money:
  an empty `remote` makes every delivered session look undelivered.
* `test_supply_unknown_is_distinct_from_supply_low_zero` — the
  `except Exception: pass` is replaced by
  `except Exception as exc: events.append("SUPPLY-UNKNOWN:%s" % …)` with the
  `SUPPLY-LOW:%d` case moved to an `else:`, so "measured zero" and "could not
  measure" are two different lines.

### Test results, run in `.worktrees/opsm32-reflexpatch` (detached at `cc7e414e`)

`python -m py_compile reflex.py` → **OK**.

`python -m pytest tests/test_standing_reflex_no_third_value.py -q` →
**18 passed, 0 failed** (all three target tests green).

Whole `monitor/tests` suite, failing-id sets:

*Before the patch (6 failures):*
```
tests/test_scan_failure_exit.py::test_a_blinded_conflict_probe_does_not_report_green
tests/test_scan_no_third_value.py::test_a_deleted_append_only_file_is_a_risk
tests/test_scan_no_third_value.py::test_all_files_present_still_reads_green
tests/test_standing_reflex_no_third_value.py::test_reflex_reads_the_return_code_of_every_child_it_scrapes
tests/test_standing_reflex_no_third_value.py::test_a_failed_git_query_skips_revival_instead_of_reviving_everyone
tests/test_standing_reflex_no_third_value.py::test_supply_unknown_is_distinct_from_supply_low_zero
```

*After the patch:* see §"post-patch suite" below (filled in when the run
finished; the pre-patch set minus the three reflex ones, with no additions, is
the pass condition).

The three remaining pre-existing failures are all in `scan.py`'s tests and are
untouched by this patch — they are somebody else's red, not this patch's.
