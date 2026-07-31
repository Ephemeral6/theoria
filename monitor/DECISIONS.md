# monitor — design calls and the reasons for them

The other territories keep one of these (`engine-rig/DECISIONS.md` is the model).
`monitor/` did not, and its hardest-won conclusions were scattered across inbox
notes, run directories and probe docstrings — where they are readable only by
somebody who already knows to look. This file is where a call that survived an
argument gets written down once.

Newest first.

---

## S44-b — `IgnoreNew` + `PT72H` make reflex's own stale-lock takeover dead code

**Adjudicated 2026-07-31. Measured, not inferred.**

The question the board item asked: is `ExecutionTimeLimit: PT72H` in conflict
with the 1500-second stale-lock takeover at `reflex.py:150-153`? OPS-M (cycle 30)
suspected `IgnoreNew` forbids the very second instance that takeover depends on.

**Answer: yes, and the takeover is unreachable in the scenario it was written
for.** Re-measured on this box today with `Get-ScheduledTask TheoriaReflex`:

```
MultipleInstances  : IgnoreNew
ExecutionTimeLimit : PT72H
Trigger repetition : PT5M
```

The takeover reads:

```python
if os.path.exists(LOCK):
    if time.time() - os.path.getmtime(LOCK) < 1500:
        return 0            # previous reflex still at work
    os.remove(LOCK)
```

Executing `os.remove(LOCK)` requires a reflex process to be *running*. There are
exactly two ways one starts: the scheduler's 5-minute trigger, or a human. So
split by whether the previous process is still alive:

| the holder | can a second process start? | what the takeover does |
|---|---|---|
| **alive but stuck** (no progress, never reaches `finally`) | **No** — `IgnoreNew` refuses every tick while the first instance runs, and `PT72H` means Windows does not kill it for three days | **never runs**; the layer is silently down for up to 72 hours |
| **dead** (killed, host slept, `finally` skipped) | Yes — the task is no longer running, so the next tick starts | runs correctly: idles up to 25 minutes, then frees the lock and takes over |

So the two settings are not individually wrong. `IgnoreNew` is right (two
concurrent reflexes would each revive every session). `PT72H` is defensible on
its own (a legitimate cycle here takes 25–50 minutes, so a short limit would
kill healthy work). The 1500s takeover is right for the crash case. **The net
effect of all three together is that the one scenario with no other recovery
path — a live process that has stopped making progress — also has no takeover.**

**Two things follow, and only the second one is done here.**

1. *Not done, and deliberately not done:* lowering `ExecutionTimeLimit` to, say,
   `PT30M` so Windows kills a stuck cycle and the next tick takes over. It is
   the obvious fix and it is unsafe as things stand: measured cycle lengths on
   this machine are ~50 minutes (`2026-07-30T23:22:27Z`, `07-31T00:14:11Z`,
   `01:04:34Z`, `01:54:33Z`), because `ci_merge` runs a full territory gate for
   every flag in the queue. A 30-minute limit would kill *healthy* cycles
   mid-merge, and killing a process holding `merge.lock` is a worse failure than
   the one being fixed. The prerequisite is S44-a — get the gate back under
   control, then the cycle length comes down, and only then is a real
   `ExecutionTimeLimit` safe. **Written down rather than done, because a change
   to the scheduler is a change to the thing that recovers the fleet.**
2. *Done:* since the automatic path cannot fire, a human has to be told. That is
   `scan.probe_reflex_heartbeat`, which reports `risk` and **names the pid** when
   a live holder passes 1500 seconds. The probe is not a substitute for the
   self-heal; it is the admission that the self-heal is not there.

### The measurement that shaped the probe more than the threshold did

The item proposed "last line older than 15–20 minutes is risk". Taken alone that
is wrong on this machine, and wrong in the direction that gets probes deleted:
a reflex **tick** is 5 minutes but a reflex **cycle** is 25–50, `reflex.log` is
written only when a cycle *finishes* (`reflex.py:445`), and `IgnoreNew` means no
tick starts meanwhile. A healthy busy machine therefore shows a 40-minute-old
last line most of the day.

`reflex.lock` is what makes that silence explicable, so the probe crosses the two
signals and only calls silence a fault when no cycle is in flight. The negative
control for exactly this case is
`tests/test_reflex_heartbeat.py::test_a_busy_healthy_machine_reads_green`.

### And the log's mtime is not a clock

`reflex.log` is a **tracked** file. Any checkout, merge, reset or `git pull
--ff-only` restamps it, and `ci_merge.main()` ends with one in a live working
tree. OPS-M recommended an mtime probe twice and then retracted it after
measuring a 3h18m gap between the file's mtime and its last content line
(`inbox/20260729T152000Z-opsm-retraction-…`). The probe reads the timestamp
*inside* the last line, and two tests hold that: one restamps a stale log and
requires the verdict to stay red, one greps the source so the habit cannot grow
back.

---

## S44-a — a gate's own runtime has to be watched, because its cost is invisible until it starts lying

**2026-07-31.**

`monitor/tests` grew from tens of seconds to ~25 minutes without anything
saying a word. The consequence was not slowness. `verify.py`'s pytest stage had
a 900-second timeout; `subprocess.TimeoutExpired` propagated out of the stage,
the gate crashed, and `ci_merge` recorded it as `verify gate red in monitor` —
so nine delivered branches were held for a defect none of them had, one of them
being the branch carrying the fix.

Two emergency moves were made and **neither is a fix**: the ceiling went to 2400s,
and a timeout now returns exit 124 with "this is NOT a red suite" rather than
being read as a failure. A gate that takes half an hour gets bypassed eventually.

The lesson worth more than the repair: **the runtime of a check is itself a
measurement, and nothing in this repository was recording it.** A suite can
double in cost every week and every single run still says `passed`. The gate's
own duration is now bounded by a constant that the gate asserts against itself
(`verify.py`), so growth past the budget is a red gate rather than a slow
afternoon — and the constant is *lower* than the timeout, so the suite reports
its own obesity before the timeout gets a chance to misreport it as a failure.
