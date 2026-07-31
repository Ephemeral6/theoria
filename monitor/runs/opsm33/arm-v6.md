# arm-v6 — `origin/agent/v6-v23-large-space-verdict-gap`

Method: `monitor/runs/opsm33/METHOD.md`. Base pinned `ea4f6af6`.
Worktree: `.worktrees/opsm33-v6` (detached at base, then merged).

## 1. Branch identity

* tip (measured): `e4b25676386423e9604d3a443fcabb4e824483e3`
* tip (flag file): `e4b25676386423e9604d3a443fcabb4e824483e3` — same, flag is current
* flag base: `d1da2c9c` (one commit behind our pinned `ea4f6af6`)
* flag reason: `verify gate red in monitor (verify.sh)`, attempts 3,
  first_seen 2026-07-30T10:26:34Z, last_seen 2026-07-30T13:48:26Z

## 2. Merge

**CLEAN.** `Merge made by the 'ort' strategy.` rc=0, no conflicted paths.

```
 exam/DECISIONS.md                                  | 106 +++-
 exam/STATUS.md                                     |  31 +-
 exam/papers/verdict.py                             |  47 +-
 .../BASELINE-cycle94.md                            |  51 ++
 .../20260730T021500Z-V23-large-space/CRITERION.md  | 314 +++++++++--
 .../20260730T021500Z-V23-large-space/MANIFEST.json | 210 +++----
 .../20260730T021500Z-V23-large-space/RUN_STATE.md  | 384 ++++++++++++-
 .../adversarial/round5-findings.md                 | 559 +++++++++++++++++++
 .../enumeration_probe.json                         | 604 +++++++++++++++++----
 .../enumeration_probe.py                           | 386 +++++++++----
 .../probe_lp_interface.json                        | 389 +++++++++++--
 .../probe_lp_interface.py                          | 370 +++++++++++--
 .../repro_duplicate_switch.json                    |   2 +-
 .../repro_duplicate_switch.py                      |  39 +-
 ...-claim-help-takes-a-p1-off-the-board-forever.md | 137 +++++
 15 files changed, 3134 insertions(+), 495 deletions(-)
```

(The diffstat above is the merge's own — i.e. only what the merge added on top
of `ea4f6af6`. The three-dot diff below is the branch's full delta from base.)

## 3. Territories actually touched (`git diff --name-only ea4f6af6...`)

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

Two territories: **`exam/`** (14 files, all the substance) and **`monitor/`**
(13 files, *all* of them new `monitor/inbox/*.md` notes — inert Markdown
messages addressed to OPS-M).

**Territory/flag mismatch, recorded up front:** the flag says the branch failed
`monitor`'s `verify.sh`, but the branch touches **zero lines of monitor code,
tests, board state, ops-status or CI config**. Its entire monitor footprint is
inbox correspondence. Nothing under `monitor/inbox/` is imported or asserted on
by the reflex/scan/standing modules named in the recorded stderr
(`reflex.py`, `scan.py`). Strong prior for innocence before the gate is run.

## 4. THIRD CATEGORY — checked explicitly, does NOT fire

The branch adds **zero test files** and modifies **zero test files**:

```
$ git diff --name-only ea4f6af6...origin/agent/v6-v23-large-space-verdict-gap -- '*test_*'
(empty)
```

Files *added* by the branch are 2 exam Markdown artefacts and 13
`monitor/inbox/*.md` notes (`--diff-filter=A`, full list in the run log). No
`.py` file outside `exam/` is added or changed. So the collected count cannot
move and no new test can be catching a master defect. **Third category: NO.**

Related, and it belongs to the control rather than to this branch: the failing
`monitor` tests named in the flag assert on strings inside `monitor/reflex.py`
that do not exist at the pinned base —

```
$ grep -c "SUPPLY-UNKNOWN:" monitor/reflex.py     # at ea4f6af6
0
```

Those tests are already on master and already red at master; they are a
pre-existing master defect being caught by pre-existing tests. That is control
territory, not an arm finding.

## 5. Gate runs

### 5a. `monitor` gate — run exactly as `ci_merge.py:539-544`

```
cwd        = <wt>/monitor
cmd        = "C:/Program Files/Git/bin/bash.exe" <wt>/monitor/verify.sh   # gates._runner
PYTHONPATH = <wt>  prepended                                             # gates.gate_env
timeout    = 1800
```

**rc = 1. Dying stage: `tests` — but NOT the way the flag says.**

The gate did not reach a verdict. It raised out of stage 1 and printed no
stage banner at all; the entire captured output is a traceback:

```
  File "...\monitor\verify.py", line 141, in _tests
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
         os.path.join(HERE, "tests")],
        cwd=HERE, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=900)
...
subprocess.TimeoutExpired: Command '[...'-m', 'pytest', ... 'monitor\tests']'
  timed out after 900 seconds
GATE_RC=1
```

Wall clock: started 22:37, raised 22:52 (900 s inner timeout), well inside the
outer 1800 s. Six OPS-M measurement agents plus `ci_merge.py` were on the box
concurrently, so the 900 s is plausibly load, not the tree.

Two things follow, and they are about the instrument, not the branch:

1. **`verify.py:_tests()` does not catch `subprocess.TimeoutExpired`.** A slow
   suite therefore does not become `FAILED(n)` on the `tests` stage with a
   detail — it takes the whole gate down as an uncaught exception. `ci_merge`
   sees rc != 0 on a `kind == "verify"` gate and writes exactly the same
   `verify gate red in monitor (verify.sh)` flag it would write for a genuine
   red. **A timeout and a failing suite are the same flag text.** This is the
   same unguarded-timeout shape as commit `886441a1`.
2. The flag file for *this* branch records the other outcome — a completed
   run with `RED: tests` and 6 named ids — so at 10:26/13:48 the suite did
   finish. The flag's transcript is a real red, not a timeout.

### 5b. `monitor` pytest — full failing-id recovery

(running)
