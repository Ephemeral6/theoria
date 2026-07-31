# OPS-M cycle 32 — Agent C: arms `s42-mrg` and `v6-mrg`

Measurement subagent for OPS-M. Nothing here was committed; both arms are
detached worktrees under `.worktrees/`. No `git fetch` was run — remote-tracking
refs as they stood in the main checkout at start of cycle.

## Shas used

| thing | sha |
|---|---|
| master HEAD (base of both arms) | `cc7e414eb3bfde3325a50f9ce0e8dc896bda2b84` |
| `origin/agent/s42-fleetkit-three-lies` | `835e864ef388f0f358ba3b95bc3631f342d031d7` |
| `origin/agent/v6-v23-large-space-verdict-gap` | `e4b25676386423e9604d3a443fcabb4e824483e3` |
| merge-base(master, s42) | `7972a075778a367f6260adfa6f0a4691999b4f5b` |
| merged arm `opsm32-s42-mrg` HEAD | `26c960773a5e4671baca14ad87ace45279520963` |
| merged arm `opsm32-v6-mrg` HEAD | `f0db2ea5d1d93a564ba893919019a9fa71c7df9a` |

## Control (measured by a sibling agent last cycle, on clean cc7e414e) — 6 failures

```
tests/test_scan_failure_exit.py::test_a_blinded_conflict_probe_does_not_report_green
tests/test_scan_no_third_value.py::test_a_deleted_append_only_file_is_a_risk
tests/test_scan_no_third_value.py::test_all_files_present_still_reads_green
tests/test_standing_reflex_no_third_value.py::test_reflex_reads_the_return_code_of_every_child_it_scrapes
tests/test_standing_reflex_no_third_value.py::test_a_failed_git_query_skips_revival_instead_of_reviving_everyone
tests/test_standing_reflex_no_third_value.py::test_supply_unknown_is_distinct_from_supply_low_zero
```

Master's own monitor gate is red independent of any branch. Any branch verdict
below is a **set difference against this control**, not "is the gate green".

---

## Arm 1 — `s42-mrg` (`agent/s42-fleetkit-three-lies`)

### Merge

**CLEAN.** `Merge made by the 'ort' strategy.` No conflicted paths
(`git diff --name-only --diff-filter=U` empty).

`git diff --stat cc7e414e..HEAD | tail -1`:
```
 14 files changed, 1891 insertions(+), 91 deletions(-)
```

Touched top-level paths: `PARTNER_SYNC.md`, `fleetkit/`, `monitor/`.

**Only one file under `monitor/`:**
```
monitor/tests/test_fleetkit_drift.py          (new, 469 lines, +469)
```
Everything else is `fleetkit/` (README, `__init__.py`, new `__main__.py`,
`board.py` +213/-?, `bus.py`, `verify.py`, three new fleetkit tests, and a
`fleetkit/runs/20260730T101232Z-S42/` provenance triple).

### Pre-facts established before the gate ran

* `monitor/tests/test_fleetkit_drift.py` **does not exist on master**:
  `git cat-file -p cc7e414e:monitor/tests/test_fleetkit_drift.py` →
  `fatal: path ... does not exist in 'cc7e414e'`. So every failing id in that
  file is category (b) or (c) by construction — it cannot be (a), the branch
  cannot have broken a test that did not exist.
* `monitor/board.py` is **byte-identical** between `cc7e414e` and the branch tip
  (`git diff --stat origin/agent/s42-... cc7e414e -- monitor/board.py` empty).
  This matters because the new test compares `monitor/board.py` against
  `fleetkit/fleetkit/board.py` and pins counts. The merge therefore cannot have
  desynchronised the pinned numbers from the monitor side.

### What the new test asserts (read in full)

`monitor/tests/test_fleetkit_drift.py` is a **drift tracker**, not a behaviour
test of monitor. It AST-parses both `monitor/board.py` and
`fleetkit/fleetkit/board.py`, normalises line endings + dedents, and compares
top-level functions. Its contract is "a divergence must be DECLARED, or it is
red" — a hand-maintained `DECLARED` dict maps function name →
(`extraction`|`stale`|`defect`, reason). Tests:

1. `test_every_divergence_is_declared` — differ ⇒ must be in DECLARED.
2. `test_declared_entries_still_describe_a_real_divergence` — a DECLARED entry
   that is now identical must be deleted (minus `GLOBAL_ONLY`).
3. `test_declared_names_all_exist_in_both_files`
4. `test_every_declared_entry_has_a_verdict_and_a_reason`
5. `test_the_measured_divergence_count_is_pinned` — asserts `len(shared) == 17`,
   `len(divergent) == 8`, `len(divergent | GLOBAL_ONLY) == 9`, and
   `set(DECLARED) == divergent | GLOBAL_ONLY`.
6. `test_the_function_that_diverges_without_any_source_difference` —
   `territories_busy` source identical, `meta` source different.
7. `test_lane_ownership_is_gone_from_fleetkit` — no `LANE_OWNER` binding, no
   `def stale_lanes`, no `"Filled from fleet.json at import"` docstring.
8. `test_fleetkits_sweep_reads_a_prefix_instead_of_shipping_an_empty_one` — no
   module-level `_PREFIX` binding, `def task_prefix` present, `SWEEP-REFUSED`
   present.
9. Six synthetic-source unit tests of the comparison predicate itself
   (`_undeclared`) — self-contained, no file reads.

`_both()` calls `pytest.skip("fleetkit is not on this tree")` if
`fleetkit/fleetkit/board.py` is absent, so on a tree without fleetkit these skip
rather than fail.

**Fragility note (bears on (c) if it fires):** tests 5 and 6 are *pinned
numbers* and *pinned identities*. They are green only for the exact pair of
files (monitor `board.py` at cc7e414e × fleetkit `board.py` at the s42 tip). Any
later commit to `monitor/board.py` by anyone can flip 5 red without fleetkit
changing at all. That is by design per the docstring ("re-run the measurement
rather than edit the number"), but it makes this test a **standing merge-order
hazard** for the queue, not just for this branch.

### Independent early read: the new test file alone

Run in the arm before the full gate, `PYTHONPATH=<wt>`, cwd `<wt>/monitor`:

```
python -m pytest -q -p no:cacheprovider -rf tests/test_fleetkit_drift.py
.............                                                            [100%]
```

**13 passed, 0 failed.** The new file is green in the merged tree, including the
pinned-count test.

### Gate result — `s42-mrg.gate.txt`, rc 1

Command exactly as `ci_merge.py` issues it:
`bash <wt>/monitor/verify.sh`, cwd `<wt>/monitor`, env = `gate_env(<wt>)` +
`PYTHONIOENCODING/PYTHONUTF8`.

Stage lines:
```
== tests              FAILED(1)
== board states disjoint ok
== real run           ok
== artifact fields    ok
RED: tests
```
`tests` is the ONLY red stage. `board states disjoint` ok (137 delivered, 7
claimed). `real run` ok — `gates: 24 gated, 1 tests-only, 0 UNGATED`,
`board.py list: 161 line(s)`. `artifact fields` ok (13 required fields).

Failing ids, verbatim:
```
tests/test_scan_failure_exit.py::test_a_blinded_conflict_probe_does_not_report_green
tests/test_scan_no_third_value.py::test_a_deleted_append_only_file_is_a_risk
tests/test_scan_no_third_value.py::test_all_files_present_still_reads_green
tests/test_standing_reflex_no_third_value.py::test_reflex_reads_the_return_code_of_every_child_it_scrapes
tests/test_standing_reflex_no_third_value.py::test_a_failed_git_query_skips_revival_instead_of_reviving_everyone
tests/test_standing_reflex_no_third_value.py::test_supply_unknown_is_distinct_from_supply_low_zero
```

Cross-checked against the sibling's **same-cycle** control arm
(`.worktrees/opsm32-out/ctl.gate.txt`, clean `cc7e414e`, `RED: tests`, same four
stage lines): byte-identical list of six.

### Set diff

```
ADDED   (branch-caused): (none)
REMOVED (branch repairs): (none)
```

**SET EQUAL to the control.**

### Verdict — `s42-mrg`: **INNOCENT**

The queue's "verify gate red in monitor (verify.sh)" for
`agent/s42-fleetkit-three-lies` is master's own pre-existing red. The branch's
only monitor-side change is a new 469-line test file that is fully green in the
merged tree, and it neither adds nor removes a single failing id.

No added id, so the (a)/(b)/(c) question has **no instances** to classify for
this branch. Recorded for the record: had `test_fleetkit_drift.py` failed, it
would have been (b)-or-(c) by construction (absent from `cc7e414e`), never (a).

**What would falsify this verdict**

* A control arm on `cc7e414e` producing a failing set that is *not* these six —
  the set diff is only meaningful against a correct control. Two independent
  controls (last cycle, and `ctl.gate.txt` this cycle) agree, so this is now
  well-pinned.
* Any later commit that changes `monitor/board.py` while `fleetkit/board.py`
  stays put. `test_the_measured_divergence_count_is_pinned` asserts
  `len(shared) == 17` / `len(divergent) == 8` / `set(DECLARED) == divergent |
  GLOBAL_ONLY` against the *live* pair of files. This arm is green because
  `monitor/board.py` is byte-identical between `cc7e414e` and the s42 tip. **If
  another branch touching `monitor/board.py` lands before s42, s42 will go red
  in the merged arm through no fault of its own** — this is a real merge-order
  interaction, and the honest disposition is "land s42 before any
  `monitor/board.py` change, or expect one DECLARED-table update".
* A `fleetkit` gate (not the monitor gate) failing on this branch. Not measured
  here — this arm only ran monitor's `verify.sh`, which is what the queue's
  complaint named. `fleetkit/verify.py` is modified by +87 lines and three new
  fleetkit tests are added; those were **not** exercised by this measurement.

---

## Arm 2 — `v6-mrg` (`agent/v6-v23-large-space-verdict-gap`)

### Merge

**CLEAN.** No conflicted paths.

`git diff --stat cc7e414e..HEAD | tail -1`:
```
 27 files changed, 3854 insertions(+), 495 deletions(-)
```

Touched top-level dirs: `exam/`, `monitor/`.

Full changed-file list:
```
exam/DECISIONS.md
exam/STATUS.md
exam/papers/verdict.py
exam/runs/20260730T021500Z-V23-large-space/BASELINE-cycle94.md
exam/runs/20260730T021500Z-V23-large-space/CRITERION.md
exam/runs/20260730T021500Z-V23-large-space/MANIFEST.json
exam/runs/20260730T021500Z-V23-large-space/RUN_STATE.md
exam/runs/20260730T021500Z-V23-large-space/adversarial/round5-findings.md
exam/runs/20260730T021500Z-V23-large-space/enumeration_probe.json
exam/runs/20260730T021500Z-V23-large-space/enumeration_probe.py
exam/runs/20260730T021500Z-V23-large-space/probe_lp_interface.json
exam/runs/20260730T021500Z-V23-large-space/probe_lp_interface.py
exam/runs/20260730T021500Z-V23-large-space/repro_duplicate_switch.json
exam/runs/20260730T021500Z-V23-large-space/repro_duplicate_switch.py
monitor/inbox/20260729T091000Z-RES-3-handoff.md
monitor/inbox/20260729T1120Z-RES-3-proposal-V24-exam-verify-repairs-staleness.md
monitor/inbox/20260729T1145Z-RES-3-two-findings-outside-my-territory.md
monitor/inbox/20260729T1150Z-RES-3-handoff.md
monitor/inbox/20260729T153000Z-RES-3-e15-and-e17-merge-clean-but-do-not-run.md
monitor/inbox/20260729T1556Z-RES-3-board-worker-id-accepts-flags.md
monitor/inbox/20260729T235719Z-RES-3-board-claim-eats-option-flags.md
monitor/inbox/20260730T0300Z-RES-3-worldgen-cannot-host-a-large-space-world.md
monitor/inbox/20260730T0301Z-RES-3-lp-potential-certifies-a-solvable-level.md
monitor/inbox/20260730T0625Z-RES-3-adversarial-checks-need-a-stated-predicate.md
monitor/inbox/20260730T070500Z-RES-3-name-the-evidence-class-of-every-number.md
monitor/inbox/20260730T071500Z-RES-3-two-findings-that-say-filed-but-are-not-on-the-board.md
monitor/inbox/20260730T095500Z-RES-3-claim-help-takes-a-p1-off-the-board-forever.md
```

**Its entire `monitor/` footprint is 13 new inbox `.md` files.** It adds no
monitor python, no monitor test, and modifies no existing monitor file. A priori
this branch cannot cause a monitor `tests` failure; the only way it could turn
the monitor gate red is via a non-`tests` stage that reads `monitor/inbox/`.

### Gate result

_(pending)_
