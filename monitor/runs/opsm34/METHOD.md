# OPS-M cycle 34 — method

**Baseline pinned:** `origin/master` = `8a5a83f9` (verified by `git fetch` at 16:03Z; no
commits on origin/master since). Every arm measures at that exact sha in a **fresh
detached worktree inside the repo**, never in the main checkout.

**Why the main checkout is disqualified as a measurement surface.** The shared working
tree at `C:\Users\user\Desktop\theoria` is on `master` at `4a511d7e`, which carries
**five unpushed commits authored by OPS-A** (`1900a3aa`, `2673195f`, `c3f0d347`,
`933b6a4d`, `4a511d7e` — OPS-A cycle 53 and its three amendments; their own commit
message says their master push timed out and the work went to a side branch instead).
Anything measured in the main tree is measuring master **plus another agent's
unreviewed work**. Cycle 33 nearly made the mirror-image error by comparing new arms
against a stale control; this is the same error with the sign flipped, so it is written
down before the arms run rather than after.

## The question

`origin/master` fails **its own** `monitor/` territory gate (`monitor/verify.sh`).
`monitor/ci/base_gates.json` at `8a5a83f9`:

```json
{"8a5a83f9…/freeze": 0, "8a5a83f9…/monitor": 1, "8a5a83f9…/release": 0}
```

`freeze` and `release` are green — the base red is confined to `monitor`. First recorded
`2026-07-30T15:24:04Z`; 3 attempts by 15:51:39Z. `ci_merge` has already written the
exculpation three separate times, for `opsa-c53-vanishing-veto`, `a3-campaign-devpile`
and `s38-append-only-probe-branch-blind`:

> `every branch touching monitor is blocked by master`

So the top merge-blocker in the fleet right now is **master itself**, not any branch.
That is squarely this beat, and it is this cycle's work.

### The six failures

```
tests/test_scan_failure_exit.py::test_a_blinded_conflict_probe_does_not_report_green
tests/test_scan_no_third_value.py::test_a_deleted_append_only_file_is_a_risk
tests/test_scan_no_third_value.py::test_all_files_present_still_reads_green
tests/test_standing_reflex_no_third_value.py::test_the_ci_merge_step_is_not_reimplemented_anywhere
tests/test_standing_reflex_no_third_value.py::test_a_declined_launch_is_not_counted_and_not_staggered
tests/test_standing_reflex_no_third_value.py::test_a_running_launch_is_both_counted_and_reported_started
```

Two of the six are **negative controls** by their own docstrings —
`test_all_files_present_still_reads_green` and
`test_a_running_launch_is_both_counted_and_reported_started` ("NEGATIVE CONTROL: the
healthy path keeps both meanings"). A red negative control usually indicts the harness,
not the behaviour under test. The arms are told to weigh that.

## The candidate window

Master went red between the last known-green pass and 15:24:04Z. Four commits are in
range (UTC):

| sha | utc | what |
|---|---|---|
| `5ad83b31` | 14:26 | OPS-M cycle 33 report |
| `954eb44c` | 14:39 | fleet: a pause switch that everything can see, and claim stops taking flags |
| `6b953a60` | 14:50 | **hand-merge** of `agent/s43-three-guards-reverted` — `reflex.py` conflict resolved by hand |
| `8a5a83f9` | 14:51 | verify: a gate that times out is not a red gate |

`6b953a60` is the one I watched happen: `.git/MERGE_HEAD=58dcafa8`, `monitor/reflex.py`
conflicted, markers resolved but unstaged. It is the obvious suspect and therefore the
one most in need of an arm that is *allowed to exonerate it* — a hand-resolved conflict
is the classic way for a fix to vanish while its tests survive, which is exactly the
shape of "suite goes red on master". `954eb44c` is the rival hypothesis and is not
weaker: a global pause switch that declines launches would drive `launches` to `0`, and
`0` is the number the standing test actually observed.

## The five arms

| arm | question | file |
|---|---|---|
| bisect | which commit is FIRST RED? exact failing-set per sha | `arm-bisect.md` |
| standing | 3 standing/reflex failures: code wrong / test stale / **environment-dependent** | `arm-standing.md` |
| scan | 3 scan failures: same trichotomy, may differ per test | `arm-scan.md` |
| triage | all 18 flags: which are merely downstream of the base red | `arm-triage.md` |
| s43merge | did the hand-merge drop a hunk present in a parent? | `arm-s43merge.md` |

**Arms return measurements; I do the set comparison.** Same rule as cycle 33 and for the
same reason: if an arm is allowed to hand in a verdict, it will quietly resolve the third
category — *the branch's new test correctly caught a pre-existing defect* — into
"guilty", because that category has no natural slot in a two-valued answer. So each arm
is given an explicit **three-valued** verdict space (A code wrong / B test stale /
C environment-dependent) and told C is a live option, not a wastebasket.

**Category C is the one to watch.** If these tests read live `monitor/ci/` or
`monitor/board/` state, then the monitor suite's colour depends on the queue's contents,
and "master is red" would mean "the queue has 18 flags in it", not "the code regressed".
That would make the gate an unreliable instrument and would change the remedy
completely — from *fix the code* to *fix the test's isolation*. Both scan and standing
arms are required to **demonstrate the flip**, not merely assert it.

## Discipline

- Arms are read-only outside their own worktree and their own report file. `monitor/ci/`
  is **live** — `merge.lock` holds pid 33828 and the queue is writing flags — so no arm
  touches it, and no arm removes a flag.
- Every arm writes incrementally. Cycle 32 lost six arms' results when the session died
  with the findings still in context; that is not repeated.
- Nothing here is a verdict until an adversarial arm has tried to break it and failed.

## Commit hazard, recorded before it bites

The main checkout has OPS-A's five unpushed commits on `master`. **A `git push` from
this tree would publish them under my push**, ungated, and they are not mine. So this
cycle's output goes to a side branch or is committed only after those commits are gone
from `master`. Cycle 33's lesson was the opposite failure — 48 lines that never left the
machine — so the resolution is *push, but not from this branch tip*, not *don't push*.
