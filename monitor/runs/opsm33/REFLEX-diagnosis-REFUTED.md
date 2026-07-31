# My cycle-32 root cause for the dead reflex heartbeat does not survive its own window

I have reported twice that the reflex layer dies at `scan.py`'s unguarded
`timeout=600`, and that the `except` which would have caught it was one of the
guards deleted by `873d62ee`. This cycle I set out to observe it happening live.
It did not happen, and following that up refuted the diagnosis.

## The prediction, and why the test was void rather than merely failed

Filed at 14:26Z, before observing: `scan.py` pid 33764 started 14:20:01Z, so its
600 s deadline was 14:30:01Z; if it was still alive then, reflex (pid 9944) would
die within seconds and `reflex.log` would gain no line.

At 14:38Z scan had run 18.5 minutes — long past the deadline — and **reflex was
still alive**.

But the test was not a fair test, and the reason matters more than the result:

```
ProcessId 33764  ParentProcessId 40848
parent 40848: cmd.exe /c "C:\Users\user\Desktop\theoria\monitor\refresh.cmd"
```

**That `scan.py` is not reflex's child at all.** It belongs to the `refresh.cmd`
scheduled task, which runs `scan.py` with no timeout in the picture. I had
assumed the only `scan.py` on the box was reflex's, and never checked the parent
before predicting. So the watch tested a process pair that the diagnosis says
nothing about. Void, not falsified.

## What reflex is actually doing right now

```
children of 9944:  32352 = monitor/ci_merge.py, started 14:04:24Z
reflex 9944 CPU: 0.36 s
```

Reflex is **alive and idle, blocked on a `ci_merge` pass that has been running
36 minutes**, against the `timeout=3600` it is given. It has not reached the
`scan.py` step of this cycle at all. `reflex.log` gains its line when a cycle
*completes*, so the current silence is a long merge pass, not a death.

## The refutation proper

The silence being explained runs from **08:32:21Z**. Here is when the guard
actually existed, by `git log -S 'timeout(600s)' -- monitor/reflex.py`:

| commit | UTC | guard |
|---|---|---|
| `88d93400` | 02:11:37Z | **added** (S30) |
| `873d62ee` | 12:55:40Z | **deleted** |
| `954eb44c` | 14:39:29Z | **restored** |

Cross-checked by counting `TimeoutExpired` in each blob: `873d62ee~1` → 1,
`873d62ee` → 0, `7c1dd89b` → 0, `ea4f6af6` → 0, `954eb44c` → 1.

So **the guard was present for the first 4 hours 23 minutes of the silence**
(08:32:21Z → 12:55:40Z). A missing guard cannot explain a silence that began
four hours before the guard went missing. My root cause is refuted for the
window it was invoked to explain.

What remains true, and I do not want to over-correct it away: `873d62ee` really
did delete the guard, the deletion really was live from 12:55:40Z to 14:39:29Z,
and my cycle-32 report was accurate *about the tree as it stood when I wrote it*
(`ea4f6af6` has zero occurrences). What was wrong was the causal claim — that
this deletion was what killed the heartbeat "EVERY cycle regardless of the
queue". The two deaths I observed in cycle 32 may still have that cause; the
long silence does not, and I generalised from two observations to a standing
explanation without checking that the timeline permitted it.

## Status of the fix, which arrived mid-cycle

`954eb44c` (14:39:29Z) restored the guard on master. The monitor is at this
moment merging `origin/agent/s43-three-guards-reverted` **by hand in the live
master checkout** — `.git/MERGE_HEAD` = `58dcafa8`, conflicted in
`monitor/reflex.py`, markers resolved but not yet staged as I write this.

s43 does more than restore: it extracts the step into a testable
`scan_events(run_scan)` seam, on the stated grounds that inline in `main()` it
is unreachable from a test and `main()` cannot be driven in a test because that
tick launches paid sessions. Its docstring also says `873d62ee` deleted this
guard "along with five siblings" — **six**, where I said four and the branch
name says three. Three different counts of the same deletion; my s43 agent is
resolving which is right.

## Two operational consequences for me

1. **I must not run `git commit` until `.git/MERGE_HEAD` is gone.** A commit now
   would finish somebody else's conflicted merge under my authorship. My
   commit-as-you-go discipline is actively unsafe in this window.
2. The running reflex (pid 9944, started 14:02Z) predates the restore at
   14:39Z, so **it is still executing the unguarded code**. The fix is on disk
   but not in the process.

## The watch, run to completion

`monitor/runs/opsm33/reflex-watch.log`, 14:27:48Z → 14:47:30Z, 20 s sampling:

* **60 of 60 samples: reflex (9944) alive. Zero samples dead.**
* `scan.py` (33764) alive in all 60 — by the end it had run 27 minutes, 2.7x
  the 600 s deadline my prediction turned on.
* `reflex.log` last line unchanged at `08:32:21Z` throughout.

The prediction said reflex would die within seconds of 14:30:01Z. It did not
die at all, across the whole window. As established above this is not a fair
test of the diagnosis — that `scan.py` was never reflex's child — but it is a
clean measurement of the thing the alarm was actually about: **the heartbeat
being stale is not the same event as the process being dead**, and for these
twenty minutes it was stale and alive simultaneously, which is precisely the
distinction my own cycle-19 recommendation failed to make and which I then
failed to make again from the other direction.
