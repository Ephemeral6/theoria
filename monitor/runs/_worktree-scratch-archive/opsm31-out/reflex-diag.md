# Reflex-layer diagnosis (read-only), 2026-07-30 ~11:55Z

## OBSERVED

* `monitor/reflex.py` writes to `reflex.log` in exactly 3 places:
  - L363 `rlog(" | ".join(events) if events else "quiet")` — end of cycle, always
  - L171 mid-cycle: `standing session released a claim: ...`
  - L234 mid-cycle: `quota: window reopened on its own -> automatic resume ...`
  Early return at L118-120 (lock held, age < 1500s) writes NOTHING.
* The last FIVE lines of reflex.log (01:55:14Z, 02:23:47Z, 06:40:15Z, 07:40:23Z,
  08:32:21Z) are all the L234 mid-cycle form. The last END-OF-CYCLE line is
  **2026-07-30T01:33:34Z** — 10h20m ago, not 3h.
* Task `TheoriaReflex`: State=Running, MultipleInstances=**IgnoreNew**,
  ExecutionTimeLimit=PT72H, repetition PT5M, LastRunTime 19:47:01 local,
  LastTaskResult **2147946720 = 0x800710E0** = "The operator or administrator has
  refused the request" (= start refused, an instance was already running).
* Live processes (local time = UTC+8):
  - pid 42104 `reflex.py`, started 19:17:01 (11:17:01Z), parent 2360 (svchost/sched)
  - pid 2220 `ci_merge.py`, started 19:19:10 (11:19:10Z), **parent 42104**
  - pid 4576 `monitor\scan.py`, started 19:50:01, parent 9492 = `cmd /c refresh.cmd`
    → belongs to **TheoriaDashboard** (PT10M), NOT to reflex.
* `monitor/reflex.lock`: content `42104`, CreationTime = LastWriteTime = 19:17:01.
* `monitor/ci/merge.lock`: content `2220`, LastWriteTime 19:19:13,
  CreationTime **18:14:15 (10:14:15Z)** — NTFS tunneling of the lock created by the
  PREVIOUS ci_merge at 10:14:15Z, i.e. that ci_merge never ran its
  `finally: release_lock()` → it was killed, and pid 2220 removed it as stale
  (`take_lock()` ci_merge.py:431-435, threshold 3600s).
* merge.log is alive (11:51:13Z) — written by pid 2220. Previous run's last line
  was 11:09:04Z; nothing between 11:09:04Z and 11:25:26Z.
* Microsoft-Windows-TaskScheduler/Operational is **IsEnabled=False** — no
  per-start event evidence available.
* index.html/state.json mtime 19:41:32/33; refresh.log mtime 19:41 → the 19:40
  dashboard scan exited ~92 s after start. pid 4576 (19:50 scan) still running at
  19:56 → >6 min under current load.

## Timeline reconstruction (INFERRED, arithmetic exact)

10:12:0x trigger → reflex starts → ci_merge spawned 10:14:15Z (lock ctime)
→ 3600 s later = **11:14:15Z** reflex's `subprocess.run(timeout=3600)` raises
TimeoutExpired, kills ci_merge, escapes `main()` before L363 → no log line;
`finally` removes reflex.lock → next 5-min trigger **11:17:01** = pid 42104,
ci_merge at 11:19:10. Every timestamp matches to the second.

## Unguarded child calls in the live file

| line | child | timeout | guarded? |
|---|---|---|---|
| 160 | board.py sweep | 2400 (default) | no |
| 209 | dispatch.py --reap | 2400 | no |
| 215/237 | quota.py check | 2400 | no |
| 232 | quota.py resume | 1800 | no |
| 268 | schtasks (per worker) | 2400 | no |
| 299 | dispatch.py --worker | 2400 | no |
| 331 | dispatch.py --only | 2400 | no |
| **345-346** | **ci_merge.py** | **3600** | **no — this is the one that fires** |
| 361 | scan.py | 600 | no (guard deleted by 873d62ee) |

## 873d62ee guard count

7 guards removed, not 4 "except" guards:
returncode checks (4): sweep EXIT, reap EXIT, revive GIT-EXIT, merge EXIT
  (merge EXIT restored later by c8061d7b via `merge_events()`)
except bodies silenced (2): BOARD-QUERY-FAILED, SUPPLY-UNKNOWN
try/except deleted outright (1 block, 2 handlers): scan.py TimeoutExpired/Exception
Commit message speaks only of MIN_FREE_GB; the 115 deletions are unmentioned.
