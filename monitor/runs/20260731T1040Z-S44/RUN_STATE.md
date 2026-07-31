# S44 — the gate that outgrew its own patience, and the loop nobody was watching

branch `cleanup2/s44-monitor-gate` · base `6fabcc7e` · worker W-1800 · 2026-07-31

Two board items, one territory, one theme: **an instrument whose cost or whose
silence nobody was measuring.**

---

## Part 1 — `S44-monitor-suite-outgrew-its-gate`

### Measure first, and the measurement moved the answer

`pytest -q --durations=50` over `monitor/tests` on this box, before any change:

```
WALL_SECONDS=460.7675151
```

The board item expected the subprocess-heavy tests (running `scan`, gates,
`schtasks`, git) to dominate. **They do not.** Six tests took 338.7s of the
460.8s — 74% — and every one of them was doing the *same* thing: a real
`scan.build(False, out_dir=…)`, ~55 seconds each, then reading a different field
out of byte-identical output.

```
64.79s  test_scan_failure_exit.py::test_a_healthy_scan_says_so_and_stamps_an_epoch
59.84s  test_gate_enforcement.py::test_a_real_scan_can_run_without_touching_the_workspace
54.19s  test_scan_failure_exit.py::test_the_page_computes_its_own_age
53.78s  test_scan_failure_exit.py::test_a_healthy_scan_writes_the_same_three_files_as_before
53.59s  test_verdict_reconcile.py::test_the_build_counts_and_names_items_nothing_checks
52.50s  test_scan_failure_exit.py::test_a_clock_that_disagrees_reads_as_unknown_not_as_fresh
------
338.69s  (74% of the suite)
```

The 7th slowest test was **3.39s**. The gate-runner tests, the `schtasks` probes,
the git-repo fixtures — all of them together are a rounding error. Guessing would
have sent the work at `test_gate_outcomes.py` and bought about twelve seconds.

The item's own 30-minute figure is also explained rather than contradicted: it
was measured on 2026-07-30 with six concurrent pytest processes on this machine
(OPS-M names the confound in his own cycle-30 note). Same suite, ~4× wall under
contention. Both numbers are real; the one to optimise against is the structural
one.

### Disposition, per class, as the item required

| class | what was found | disposition | why |
|---|---|---|---|
| **genuinely-needed subprocess, run repeatedly** | six identical `scan.build()` runs, 338.7s | **one session-scoped fixture** (`conftest.real_scan`) | the run is necessary — S30 exists because a crashed scan and a healthy one wrote the same files — but it is necessary *once*. Zero assertions dropped; five redundant scans dropped. |
| **only checks that a command is composed correctly** | **none found** | nothing done | Looked, honestly, and did not find any. `test_gate_enforcement.py` already asserts composition by string (`test_the_merge_log_line_names_gated_and_ungated_separately` builds the line rather than merging a branch), and `test_ci_merge_still_refuses_a_red_verify_gate` is already a source-level check. Inventing work here would have been motion, not repair. |
| **truly slow and necessary → mark slow, split out of the gate** | **not applied** | nothing split out | After the fixture the gate's pytest stage is **183.5s against a 300s target**. Splitting checks out of a gate that already meets its budget is removing coverage for no gain, and the item says so itself: *分出去的必须仍然有人跑，否则这就是砍掉检查而不是加速*. If the suite grows past the budget again, the gate now says so on every run (below) and this is the row to revisit. |
| **cheap tests** | 52 files, nothing above 3.4s | untouched | |

### Result

```
before : WALL_SECONDS=460.7675151
after  : WALL_SECONDS=182.8012588        (-60.3%)
```

Post-change `--durations=20` has exactly one entry above 4.6s, and it is the
shared fixture's setup:

```
58.91s setup  tests/test_gate_budget.py::test_the_shared_fixture_really_is_a_real_scan
 4.52s call   tests/test_gate_budget.py::test_the_over_budget_line_appears_only_when_over_budget
 3.20s call   tests/test_gate_outcomes.py::test_hanging_gate_is_broken_not_green
```

**Hard target, measured on the gate itself** (`python monitor/verify.py`):

```
== tests              ok
pytest stage took 183.5s (budget 300s, ceiling 2400s)
...
GREEN
GATE_EXIT=0 GATE_WALL=236.914236
```

183.5s ≤ 300s. The ceiling was **not** raised; it was left at 2400 and the
reasoning is in `verify.py`'s comment — the suite now uses a small fraction of
it, and tightening it would save nothing while re-creating the false red on a
contended afternoon.

### Negative control (item point 4, not optional)

`tests/test_gate_budget.py` manufactures a test that must exceed the ceiling and
requires the gate to report **124 / TIMED OUT / "This is NOT a red suite"** —
not a failure. Its companion requires a genuinely failing suite to still be
**1**, because a `_tests()` hardwired to return 124 would satisfy the first half
while making every real failure unreportable. The pair is the check.

The whole cost of the incident was those two numbers being one observation.

### The harder lesson, made operational

`verify.py` now prints its pytest stage's elapsed seconds **on every run, green
or red**, against a declared `TESTS_BUDGET_S = 300`. Over budget prints a loud
line and is **not** red — deliberately, and written down in `DECISIONS.md`:
wall-clock here is contended, so a hard time assertion would hold branches for a
machine's mood, which is the exact harm this item repairs.

The teeth that *are* load-independent live in
`test_only_the_shared_fixture_runs_a_real_scan`, which reads the sources and
fails if a seventh real scan appears without a declared
`# real-scan-exempt: <reason>`. It has its own positive control, because a
source-reading guard that matches nothing passes forever and looks exactly like
compliance.

---

## Part 2 — `S44-reflex-heartbeat-unwatched`

### The probe

`scan.probe_reflex_heartbeat`, registered as `PROBES["reflex_heartbeat"]`,
modelled on `probe_standing` as the item asked — but **not** on the threshold the
item proposed, and the reason is a measurement.

Ticks are 5 minutes. **Cycles are 25–50 minutes**, measured from the live log:

```
2026-07-30T23:22:27Z / 07-31T00:14:11Z / 01:04:34Z / 01:54:33Z   (~50 min apart)
```

`reflex.log` is written only when a cycle *finishes* (`reflex.py:445`), and
`MultipleInstances: IgnoreNew` means no tick starts while one is in flight. So
"last line older than 20 minutes" is the **normal** reading of a perfectly
healthy busy machine, and a probe keyed on that alone would be red most of the
day — then switched off, which is the outcome the item explicitly warns about.

The probe therefore crosses two signals, with `reflex.lock` answering *is this
silence explained*:

```
lock absent, last line <= 20 min          green
lock absent, last line >  20 min          RISK  — nothing running, nothing finished
lock held, pid alive, age <  1500s        green — a cycle is in flight
lock held, pid alive, age >= 1500s        RISK  — stuck, and no takeover is coming
lock held, pid dead                       RISK  — crashed before `finally`
lock held, pid unreadable                 RISK  — "cannot tell" is not green
```

`REFLEX_LOCK_STALE_S = 1500` is copied from `reflex.py`, not chosen again.

### Negative controls (the point of the ticket)

* `test_a_quiet_healthy_machine_reads_green` — the ordinary case.
* `test_a_busy_healthy_machine_reads_green` — the case that sinks the naive
  probe: a 40-minute-old last line **with a live young lock** is green.
* `test_the_boundary_is_not_crossed_one_second_early` — green *at* the
  threshold, both thresholds.
* `test_the_probe_reads_content_not_mtime` — restamps a stale log the way a
  `git pull --ff-only` does and requires the verdict to stay red. This encodes
  OPS-M's own retraction (`inbox/20260729T152000Z-…`): `reflex.log` is a
  **tracked** file, he measured a 3h18m gap between its mtime and its last
  content line, and `ci_merge.main()` ends with a pull in a live working tree.
  A second test greps the source so the habit cannot grow back.

Not asserted: green against the live repository. `TheoriaReflex` is currently
`Disabled` on this box and the honest reading is `risk` —

```
上一轮跑完于 2026-07-31T01:54:33Z（530 分钟前…），而 reflex.lock 不存在
——没有一轮在跑，也没有一轮跑完。
```

A test that demanded green there would be a test demanding the machine lie. The
live-repo test asserts only that the probe runs and reaches a verdict.

### The PT72H / IgnoreNew adjudication — asked for, answered, written down

**The contradiction is real and the self-heal never fires.** Re-measured today
with `Get-ScheduledTask TheoriaReflex`: `MultipleInstances: IgnoreNew`,
`ExecutionTimeLimit: PT72H`, trigger repetition `PT5M`.

Executing `reflex.py:153`'s `os.remove(LOCK)` requires a *second* reflex process.
Split by whether the holder is alive:

* **holder alive but stuck** — `IgnoreNew` refuses every tick, `PT72H` means
  Windows will not kill it for three days, so the second process never exists
  and **the takeover never runs**. Silent, up to 72 hours, no recovery path.
* **holder dead** — the task is no longer running, the next tick starts, and the
  takeover works exactly as designed.

So the takeover is dead code in precisely the scenario with no other recovery.
Full reasoning, and the reason `ExecutionTimeLimit` was **not** lowered (a
30-minute limit would kill healthy 50-minute cycles mid-merge, and killing a
process holding `merge.lock` is worse than the fault being fixed), is in
`monitor/DECISIONS.md` §S44-b. It is a prerequisite chain: fix the gate cost
first, cycle length comes down, *then* a real `ExecutionTimeLimit` is safe.

Since the automatic path cannot fire, the probe names the pid and asks for a
human. That is the honest scope of what this ticket can deliver.

---

## Gate

```
GREEN   (tests / board states disjoint / real run / artifact fields all ok)
GATE_EXIT=0
pytest stage took 183.5s (budget 300s, ceiling 2400s)
```

Zero API calls, zero spend, zero sealed-pile contact, no credential values.
