# OPS-M cycle 30 — adversarial test of the "monitor gate is RED on clean master" URGENT

Adversarial subagent. Nothing merged, committed, or pushed. Nothing under
`monitor/` modified outside throwaway worktrees. No test weakened or skipped.

Instrument: `monitor/runs/opsm30/control.py` — it **imports `ci_merge`** and calls
`ci_merge.gate_for` / `ci_merge.sh` / `gates.gate_env`, rather than reimplementing
them (cycle 29's control reimplemented; a reimplementation is a claim about the
runner that nothing checks against the runner).

Worktrees: `.worktrees/opsm30-adv-cur` (46ba6e34), `.worktrees/opsm30-adv-7972`
(7972a075), `.worktrees/opsm30-adv-revert` (46ba6e34 with reflex.py reverted).

---

## Attack 1 — the instrument. VERDICT: **SURVIVES**

The two named traps do not apply, because **`ci_merge` never calls `gates.run()`**.
It has its own call site at `ci_merge.py:543`:

```
            r = sh(cmd, cwd=os.path.join(wt, d), timeout=1800,
                   extra_env=gates.gate_env(wt))
```

and its own `sh` (`ci_merge.py:92-103`) which sets
`PYTHONIOENCODING=utf-8, PYTHONUTF8=1` plus `gate_env`'s `PYTHONPATH=<worktree>`.
So the env *is* passed on the production path. `gates.run()`'s missing-env bug is
real but is on a path `ci_merge` does not use (it is used by
`gates.py --run/--run-all` and by `scan.probe_verify_gates`) — worth its own
report, not a defect in this measurement.

`TEST_CMDS` is empty (`ci_merge.py:86-88` confirmed), so
`ci_merge.gate_for == gates.gate_for`. Gate resolved for `monitor` is
`verify.sh` (canonical, wins over `verify.py`), run via
`C:\Program Files\Git\bin\bash.exe` with the path forward-slashed — no
`/tmp/...`→`C:\tmp\...` confusion, and `gate_for` returned `kind=verify`, not
the ambiguous `none`. Trap 2 therefore did not fire either.

One faithfulness gap, disclosed: `ci_merge` builds its worktree with
`tempfile.mkdtemp()` in `%TEMP%`; cycle 30's rules require worktrees inside the
repo, so all runs here are in `.worktrees/`. Cycle 29 proved `freeze` is
location-sensitive; `monitor` is measured *inside* the repo, i.e. the location
that is **more favourable** to green. It is red anyway, so the gap cannot
manufacture the red.

## Attack 2 — staleness. VERDICT: **SURVIVES (with a correction to the count)**

Master moved 8 commits: `7972a075` → `46ba6e34`. `monitor/reflex.py` is
**unchanged** across that span (`git log 7972a075..origin/master -- monitor/reflex.py`
is empty), so the reflex half of the claim is not stale.

Re-run at CURRENT master, faithful invocation:

```
$ python monitor/runs/opsm30/control.py cur-46ba6e34 .worktrees/opsm30-adv-cur monitor freeze release papers
monitor    RED (verify gate red in monitor)         rc=1  507.4s
freeze     GREEN                                    rc=0  51.8s
release    GREEN                                    rc=0  60.8s
papers     GREEN                                    rc=0  9.5s
```

Re-run at the measured SHA:

```
$ python monitor/runs/opsm30/control.py old-7972a075 .worktrees/opsm30-adv-7972 monitor freeze release papers
monitor    RED (verify gate red in monitor)         rc=1  493.3s
freeze     GREEN                                    rc=0  34.7s
release    GREEN                                    rc=0  56.6s
papers     GREEN                                    rc=0  18.4s
```

The headline reproduces. **But the count changed: 5 → 6.** `46ba6e34` adds
`test_scan_failure_exit.py::test_a_blinded_conflict_probe_does_not_report_green`,
which arrived with `12034a02` ("the guard for this hole was written, committed,
and never deployed"). The URGENT's "5" is now wrong on master.

## Attack 3 — causation on 873d62ee. VERDICT: **REFUTED**

Controlled revert: current master with **only** reflex.py set back to its
pre-873d62ee blob (`git checkout cd048b32 -- monitor/reflex.py`, 118+/100-).

Baseline, unmodified `46ba6e34` (6 failures):

```
FAILED tests/test_scan_failure_exit.py::test_a_blinded_conflict_probe_does_not_report_green
FAILED tests/test_scan_no_third_value.py::test_a_deleted_append_only_file_is_a_risk
FAILED tests/test_scan_no_third_value.py::test_all_files_present_still_reads_green
FAILED tests/test_standing_reflex_no_third_value.py::test_reflex_reads_the_return_code_of_every_child_it_scrapes
FAILED tests/test_standing_reflex_no_third_value.py::test_a_failed_git_query_skips_revival_instead_of_reviving_everyone
FAILED tests/test_standing_reflex_no_third_value.py::test_supply_unknown_is_distinct_from_supply_low_zero
```

With reflex.py reverted (**still 6 failures, still RED**):

```
FAILED tests/test_scan_failure_exit.py::test_a_blinded_conflict_probe_does_not_report_green
FAILED tests/test_scan_no_third_value.py::test_a_deleted_append_only_file_is_a_risk
FAILED tests/test_scan_no_third_value.py::test_all_files_present_still_reads_green
FAILED tests/test_standing_reflex_no_third_value.py::test_a_crashed_merger_no_longer_reads_as_a_clean_no_op
FAILED tests/test_standing_reflex_no_third_value.py::test_a_successful_merge_is_unchanged
FAILED tests/test_standing_reflex_no_third_value.py::test_the_ci_merge_step_is_not_reimplemented_anywhere
```

Three consequences:

1. **Reverting 873d62ee does not turn the gate green.** Net failure count is
   unchanged at 6. Any remedy built on "revert the root cause" fails.
2. **873d62ee is a two-way clobber, not a deletion.** The pre-873d62ee
   reflex.py fails three *different* tests (`merge_events` inline-copy guards)
   that pass at current master — i.e. 873d62ee also *restored* work. This is
   the signature of a stale working copy being published, which is what OPS-A
   independently ruled at `monitor/mailbox/OPS-A.md:1122-1136` ("没有人删，是陈旧
   副本被发布" — a copy frozen on disk since 2026-07-29T17:15:46Z). The URGENT's
   framing ("deleting three guards ... ten minutes after the tests arrived")
   reads as authored removal; it was not.
3. **The three `test_scan_*` failures cannot be 873d62ee's.** 873d62ee is
   `1 file changed` — `monitor/reflex.py` only — and those tests read
   `scan.py` (`tests/test_scan_no_third_value.py:58,96,291`). They fail
   identically with reflex.py reverted.

### What the scan failures actually are

Not a source regression at all — they are **repository history**:

```
test_a_deleted_append_only_file_is_a_risk
E  assert 'battery/PREDICTIONS.md' in '追加式文件出现删除：PARTNER_SYNC.md（删除 3 行，
   超出已裁决豁免 1 行）...'
test_all_files_present_still_reads_green
E  probe_append_only is risk on a checkout that should be clean: ... PARTNER_SYNC.md（删除 3 行）
E  assert 'risk' == 'green'
```

`probe_append_only` is correctly reporting a **real append-only violation in
master's history** (PARTNER_SYNC.md lost 3 lines against a 1-line adjudicated
exemption). The tests assume a clean checkout reads green, so the probe being
*right* is what makes them red. This is a separate incident from 873d62ee and
is not mentioned anywhere in the URGENT.

### Timeline arithmetic in the URGENT is wrong

All commit stamps are `+08:00`; converted to UTC:

| commit | UTC | delta to 873d62ee |
|---|---|---|
| `1585dd04` | 2026-07-29T21:00:33Z | **7h55m** before (URGENT says "two hours") |
| `c8061d7b` | 2026-07-29T22:41:44Z | **6h14m** before (URGENT says "two hours") |
| `5c872888` | 2026-07-30T03:10:48Z | **1h45m** before (URGENT says "ten minutes") |
| `873d62ee` | 2026-07-30T04:55:40Z | — |

The "two hours" and "ten minutes" figures are both wrong, and both wrong in the
direction that makes the sequence look more damning than it was.

## Attack 4 — the green comparators. VERDICT: **freeze REFUTED as a comparator; release and papers SURVIVE**

All three were run in the same control invocation, so "same conditions" is true
as stated. But `freeze` is the hollow one, and it is hollow in the exact way
this repo has been burned before.

`freeze/verify.sh` on master has stages `[0]`…`[14]` and **no stage 15**:

```
$ grep -oE '\[[0-9]+\]' .worktrees/opsm30-adv-cur/freeze/verify.sh | sort -u -V
[0] [1] [2] [3] [4] [5] [6] [7] [8] [9] [10] [11] [12] [13] [14]
$ grep -rn "BUDGET_TABLE\|build_budget_table" .worktrees/opsm30-adv-cur/freeze/verify.sh
NOT PRESENT in master's freeze/verify.sh
```

The check that fails on `s4-freeze` / `s4-e23-tiers` is stage 15 /
`BUDGET_TABLE`, and it **does not exist in master's gate at all**. Master's
freeze GREEN therefore says nothing about the freeze branches — it is a gate
that never runs the failing check, the same shape as the cycle-29 finding
(which said "stops at stage 11"; the measured behaviour is that it runs to 14
and the stage is simply absent — same conclusion, more precise).

`release` (60.8s, classified 6479 tracked files, ran the S23 before/after
archive) and `papers` (9.5s but 184 tests + `verify_paper: PASS (6/6)`) did real
work and are honest comparators.

Structural caveat that the URGENT does not state: `monitor`'s gate hands its
**entire** `monitor/tests/` suite to pytest (`verify.py:142-146`), while
freeze/release/papers run curated staged checks. "monitor red, the others green"
is partly a statement about how much each gate looks at.

## Attack 5 — scope. VERDICT: **SURVIVES, and is stronger than published**

Six branches carry `verify gate red in monitor (verify.sh)` — one more than the
URGENT's five (`s40` and `v6-v23` are also flagged; `opsm-c26` has since merged).
Their `FAILED` sets, read out of `monitor/ci/CONFLICT-*.md`:

| branch | failures | novel (not on master) |
|---|---|---|
| `a3-campaign-devpile` | 6 | **0** |
| `c13-certificate-bridge-two-halves` | 5 | **0** |
| `s38-append-only-probe-branch-blind` | 6 | **0** |
| `s39-writes-into-the-live-master-tree` | 6 | **0** |
| `s40-fleetkit-fork-has-drifted` | 5 | **0** |
| `v6-v23-large-space-verdict-gap` | 6 | **0** |

Every set is exactly master's set at the moment that flag was written. The 5-vs-6
split is purely *when*: the sixth failure begins at `abc9d8ef` (commit date
2026-07-30T10:06:32Z), and `c13` (09:19:07Z) and `s40` (08:41:33Z) were flagged
before it. **No branch adds a single failure of its own.** The URGENT's core
inference is confirmed for all six.

### Two things scope-analysis turned up that the URGENT gets wrong

**(a) The a3 caveat is wrong — a3 is innocent, and should not be held.**
The URGENT says: *"especially a3 — its flag has been there since 07-29T04:14,
15 hours before this regression, so I lean toward it having another problem;
don't clear it on this basis."* That rests on `first_seen`, which is not what it
looks like. `ci_merge.flag()` carries `first_seen`/`attempts` forward from the
previous attempt **without comparing `reason`**:

```
    prev = last_attempt(branch)
    first_seen = prev.get("first_seen") or stamp
```

a3 has had three distinct reasons under that one counter:

```
$ grep -oE "FLAG origin/agent/a3-campaign-devpile: [^[]*" monitor/ci/merge.log | sort -u
  tests red in theoria-arm
  verify gate red in theoria-arm (verify.py)
  verify gate red in monitor (verify.sh)
```

So "27 attempts since 07-29T04:14" is three different failures summed. a3's
*theoria-arm* problem was real once — but a3 is also the **only** flagged branch
with a gate that ci_merge never reaches: `sorted(dirs)` is
`PARTNER_SYNC.md, monitor, theoria-arm`, and `ci_merge.py:548` returns on the
first red, so theoria-arm is never run. Tested directly on the merged tree:

```
$ python monitor/runs/opsm30/control.py a3-merged .worktrees/opsm30-adv-a3 theoria-arm
theoria-arm GREEN                                    rc=0  405.2s
```

**a3's hidden gate is green.** It adds zero failures and has no second problem.
The URGENT's hold on it should be lifted.

**(b) The sixth failure on master is OPS-M's own commit.**
Bisecting the single test across the eight new commits:

```
7972a075  ->  .            [100%]      (passes)
abc9d8ef  ->  short test summary info  (fails)
10709600 / 74e090e2 / 12034a02 / 46ba6e34  ->  fails
```

`abc9d8ef` is *"OPS-M cycle 29: the monitor gate is red on master itself…"* — the
commit that published this very URGENT. It changed **no source code**, only
markdown and JSON artifacts. The mechanism:
`monitor/runs/opsm29/conflicts-triage.md` quotes literal merge-conflict markers
as evidence, and `scan.probe_conflicts()` check (a) walks the tree for exactly
those (`scan.py:328`, `re.compile(r"^(<{7} |={7}$|>{7} )", re.M)`). The probe
finds them, returns `risk` instead of `missing`, and
`test_a_blinded_conflict_probe_does_not_report_green` goes red.

Writing the report about the red made the gate redder. Any agent who pastes a
conflict marker into a tracked file under `ROOT` will do it again — that is a
standing instrument defect, not a one-off. (This file deliberately contains no
seven-character conflict markers for that reason.)

### And the three `scan.py` failures belong to nobody named in the URGENT

They are `probe_append_only` correctly reporting a **real** append-only
violation in master's history — `PARTNER_SYNC.md` lost 3 lines against a 1-line
adjudicated exemption — against tests that assume a clean checkout reads green.
Untouched by 873d62ee, untouched by any branch, and unmentioned in the URGENT.

---

## Overall: **STANDS WITH CORRECTIONS — but the root-cause sentence must be retracted**

Stands:
* monitor's gate is RED on clean master, reproduced at the **current** master
  (`46ba6e34`) with an invocation that calls ci_merge's own functions.
* release and papers are green under the same invocation.
* every flagged branch's failures are a subset of master's, with zero novel
  failures. The branches are being blamed for master's red.

Must be corrected or retracted:
1. **RETRACT** "Root cause is 873d62ee." Reverting exactly its reflex.py hunks
   leaves the gate red with the same count (6), swaps three reflex failures for
   three others, and leaves all three scan failures untouched. 873d62ee is *a*
   cause of *three of six*, not *the* root cause.
2. **RETRACT** the deletion framing. 873d62ee is a stale working copy being
   published (it *restores* code as well as dropping it); OPS-A ruled this
   independently at `monitor/mailbox/OPS-A.md:1122-1136`. "Deleted three guards
   ten minutes after the tests arrived" reads as authorship of a removal.
3. **CORRECT** the arithmetic: 7h55m / 6h14m / 1h45m, not "two hours" / "ten
   minutes". All commit stamps are +08:00 and were not converted.
4. **CORRECT** the count: 5 → 6 on current master, and six flagged branches, not
   five (`s40`, `v6-v23` also).
5. **WITHDRAW the hold on a3.** Its hidden theoria-arm gate is green and its
   `first_seen` is an artifact of `flag()` summing three different reasons.
6. **WITHDRAW freeze as a comparator.** Master's freeze gate has no stage 15;
   it cannot speak to the freeze branches.
7. **ADD** the two causes the URGENT never names: the real `PARTNER_SYNC.md`
   append-only violation (3 of 6 failures), and `abc9d8ef`'s own
   conflict-marker artifact (1 of 6).

Net: three of master's six failures are 873d62ee's, three are not, and one of
those three was introduced by the report itself.

