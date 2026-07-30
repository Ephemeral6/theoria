# Second reflex death, observed with the child process named

The first death (pid 42104) established the 600 s signature by arithmetic. This
one has the child attached, and it happened on a **cheap** pass, which rules out
"the pass was too big" as a contributing cause.

| time (UTC) | fact | how observed |
|---|---|---|
| 12:27:01 | reflex pid **6328** starts (parent = scheduler) | `Get-CimInstance Win32_Process` |
| 12:28:49 | its child `ci_merge.py` pid **2592** starts | same, ParentProcessId 6328 |
| 12:42:13 | ci_merge writes its last line (`HELD 14 …`) and exits; `merge.lock` is **released** — a clean exit, 13.5 min, nowhere near its 3600 s | `monitor/ci/merge.log`, `lock=none` in `pass-watch.log` |
| 12:42:16 | reflex launches `monitor/scan.py` pid **18472**, parent 6328 — 3 s after ci_merge returned, i.e. `reflex.py:361` | `Get-CimInstance`, CreationDate 20:42:16 local |
| ~12:52:16 | 600 s later: `run(scan.py, timeout=600)` raises `TimeoutExpired` | inferred from the two facts either side |
| 12:52:16–12:53:52 | reflex 6328 **gone**, `monitor/reflex.log` still **280 lines** | `pass-watch.log`, `reflex6328=0` |

`reflex.py:361` is `run([sys.executable, HERE/scan.py], timeout=600)`; it is not
inside a `try`. Line 363 is the only end-of-cycle log line. So the exception
propagates out of `main()`, the process exits through its `finally` (which
removes `reflex.lock`, so no stale lock is left), and the cycle ends two lines
before its own heartbeat.

**Two instances, same signature, different pass sizes**: pid 42104 after a
55-minute full pass, pid 6328 after a 13.5-minute cheap pass. The pass is not
the variable. `scan.py` exceeding 600 s is.

**What this does NOT damage.** Everything in `reflex.py` before `:361` has
already run by then — session revival, the quota-window resume, standing-claim
release, the supply alarm, and the whole merge pass. So the fleet's reflexes are
firing every cycle; what is lost is the heartbeat line and `scan.py`'s
completion. That matters because the heartbeat is the fleet's only "is the reflex
layer alive" signal, and it has now read "dead" for 11 hours while the layer was
in fact working — the exact failure mode I documented in cycle 19 and then
recommended the wrong replacement instrument for.

**Load caveat, stated because it is mine**: I have had up to nine subagents
running pytest since ~12:35Z, which inflates `scan.py`'s runtime. But death #1
(pid 42104, ~12:24Z) preceded all of it, and a `scan.py` belonging to
`TheoriaDashboard` had already run 12+ minutes at 12:32Z. My load makes this
worse; it did not create it. What my load does not explain is why a 600 s
timeout has no `except` around it.
