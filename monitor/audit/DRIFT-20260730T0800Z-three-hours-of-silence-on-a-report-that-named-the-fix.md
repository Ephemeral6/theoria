# DRIFT-three-hours-of-silence-on-a-report-that-named-the-fix

severity: critical
dimension: 7 (one-way door) → 5 (process drift). **The mechanism is prior art. The persistence and the non-response are not.**

pin: `origin/master = 13bbcad9`, pinned **07:46:41Z**. `HEAD = 60def5cb`, 7 commits behind —
every citation below is labelled `disk` (live, dirty), `HEAD`, or `pin`.

---

## claim

`monitor/` territory has now gone **3h24m with zero merges** (last 04:29:32Z). The gate has been
red on **published master** the whole time. `DRIFT-20260730T0656Z` named the cause, named the
fix, and named the two ways of applying it that would destroy other work — **and in the 40
minutes after it was handed over, eight commits landed and not one touched the file.** Meanwhile
work is being marked *delivered* into the frozen territory.

**What is new here is not the defect. It is that the defect survived being correctly diagnosed,
published, and escalated.** The instrument that was missing at 06:56Z is still missing: nothing
in the fleet asks *"is master itself green"*, so the only thing standing between this and
indefinite freeze is an auditor happening to look.

---

## evidence

### 1. Master is red **at the pin**, proved with an instrument that is not a restatement

Cycle 49's only window was `/.mongate_clean.log`, an untracked file. It is **stale**: mtime
`2026-07-30 13:13:55.640 +0800` = **05:13:55Z** (disk), 2h40m older than the pin. It cannot
speak for the pin, so I did not let it.

Extracted the pin into `%TEMP%` — never the live tree — and ran the suite there:

```
git archive 13bbcad9 | tar -x -C /tmp/pinchk
cd /tmp/pinchk/monitor && python -m pytest -q tests/test_standing_reflex_no_third_value.py
→ 3 FAILED
    test_reflex_reads_the_return_code_of_every_child_it_scrapes
    test_a_failed_git_query_skips_revival_instead_of_reviving_everyone
    test_supply_unknown_is_distinct_from_supply_low_zero
```

Verbatim the same three as 06:56Z. `monitor/reflex.py` is md5 `0930061015e38c9d189fd5e82d671984`
**identically** at `7c1dd89b` (04:56:22Z), at `HEAD`, at the `pin`, and on `disk`.
`git log --all --since='2026-07-30T04:57' -- monitor/reflex.py` → **empty**. The file has not been
touched on **any ref** for over three hours.

**Second, independent instrument — the merge robot gated the pin itself and got red.**
`monitor/ci/CONFLICT-origin_agent_a3-campaign-devpile.md` (disk):
`base: 13bbcad93208f3d545c44179381cf152c8fc2133` · `last_seen: 2026-07-30T07:51:14Z` ·
`attempts: 24` · `NEEDS-HUMAN` · reason `verify gate red in monitor (verify.sh)`.
This matters independently of what `verify.sh` calls internally: **the named gate, on the pin,
is red.**

### 2. Five of six detectors still absent — reproduced at the pin, unchanged

`git show <rev>:monitor/reflex.py | grep -c -F`:

| marker | `cd048b32` (pre-stale) | `873d62ee` (the publish) | **pin `13bbcad9`** |
|---|---|---|---|
| `sweep:EXIT-` · `reap:EXIT-` · `BOARD-QUERY-FAILED` · `SUPPLY-UNKNOWN:` · `revive:GIT-EXIT-` | 1 each | 0 | **0** |
| `SCAN FAILED (rc=` (S30's, no test at all) | 1 | 0 | **0** |
| `merge:EXIT-` | 1 | 0 | **1** |
| `serve:restart-FAILED(port still shut)` · `serve:spawn-FAILED` | **0** | 1 | **1** |

At the pin `monitor/reflex.py:361` is still
`run([sys.executable, os.path.join(HERE, "scan.py")], timeout=600)` — return code discarded.
**Prior art: `DRIFT-20260730T0656Z` §二. Cited, not re-derived.**

### 3. Zero `monitor/` merges for 3h24m, and the merger is *running*

`monitor/ci/merge.log` (**disk-live**; the pin-tracked copy stops at 04:38:27Z, so live ≠ tracked):
last `monitor` merge `2026-07-30T04:29:32Z MERGED origin/agent/opsa-c47-… (dirs: monitor)`.
Every `MERGED` since is `arc-recon` / `exam` / a `dirs: ; gates: none` line — **not one names
`monitor`**. `merge.lock` pid `27200`, mtime 07:40:37Z. The queue is not wedged; it is working
normally and refusing this territory specifically. **The freeze is territory-scoped to exactly
the territory the fix must land in.**

### 4. **CORRECTION TO MY OWN CYCLE-49 REPORT: four branches, not five**

`opsm-c26-never-tried-branches-tie-at-zero` left this group at **07:26:09Z**; its CONFLICT file
was rewritten with `reason: merge conflict` — a genuine conflict of its own, unrelated to master's
red. The four still carrying master's own traceback in their `CONFLICT-*.md` cause-lines (disk,
8 matching lines each): `a3-campaign-devpile`, `c13-certificate-bridge-two-halves`,
`s38-append-only-probe-branch-blind`, `s39-writes-into-the-live-master-tree`.
**Anyone quoting "five" is quoting me being wrong.**

### 5. Nobody acted — and I proved the recorders were recording

Window 07:13:56Z (cycle 49's handover) → 07:53:56Z:

* **8 commits landed**; `git log --all --since -- monitor/reflex.py` → none touch it.
* **No new board item** (newest `S41` @ 07:01:33Z, unrelated). **No new inbox** (newest 07:09:16Z).
  **No mailbox paragraph** after 07:13Z anywhere.
* The ask was explicit: `monitor/bus/OPS-A/out.jsonl` @ 07:13:56Z (disk) —
  *"仍在发生、要你现在动手的：monitor/ 领地自 04:29:32Z 起零合并"*. RES-3 (07:25:41Z, 07:32:39Z)
  and RES-4 (07:38:13Z) posted **after** it, about other work.

**Absence in a log is not absence of the event — unless the log was recording, and here all four
channels were**: 8 commits, 2 `board.log` lines, 3 bus messages, `merge.log` advancing every few
minutes. This is absence of the event. **The handover was read past, not missed.**

### 6. NEW — work is now being marked *delivered* into the frozen territory

`monitor/board/board.log` (disk), the only two entries after 07:13Z:

```
2026-07-30T07:37:50Z DONE  S39-S39-writes-into-the-live-master-tree by RES-4
2026-07-30T07:37:50Z CLAIM S40-S40-fleetkit-fork-has-drifted        by RES-4
```

`origin/agent/s39-…` had been flagged `verify gate red in monitor (verify.sh)` since **05:10:24Z
— 18 minutes before it was declared done**, and the worker claimed the next item in the same
second. `c13` sits in `board/done/` likewise. `monitor/mergequeue.py:205-232` `probe()` reports
this exact shape as `risk`, so **the fleet's own instrument calls it a defect, not a definition.**

**Why this is the compounding cost, not a side note:** RES-4 measured its own branch green
(`monitor/bus/RES-4/out.jsonl` @ 07:38:13Z, disk: *449 测试绿、verify.py GREEN*) while the queue
flags the same branch red. **Both measurements are correct.** The branch is green; the merge
*result* is red, because the merge takes master's missing guards. Nothing runs the gate on the
merged tree except the robot that then blames the branch — so a worker cannot discover this
without burning a session on it.

### 7. The missing instrument, verified at the pin

`git show 13bbcad9:monitor/scan.py` — `PROBES` (`:1422-1449`) has 26 entries, **none runs a
territory gate**. `probe_verify_gates` (`:873`) checks only that gates *exist*.
`run_tests()` (`:1454-1466`) is hardcoded to `("engine-rig", "theory-compiler")` — **`monitor` is
not in it.** Prior art `DRIFT-20260730T0656Z:197`; now confirmed at the pin, so it should be
cited as standing rather than re-argued each cycle.

---

## suggest

**1 — Unfreeze, forward-only, and the two caveats are unchanged and still binding.**
Restore the six detectors with a **forward-only commit on top of the current tip**.
**Do NOT `git revert 873d62ee`. Do NOT `git checkout cd048b32 -- monitor/reflex.py`.** Both destroy
the real memory-threshold fix (`MIN_FREE_GB = HEADROOM_GB + PER_SESSION_GB`) and both
**permanently** destroy `serve:restart-FAILED(port still shut)` and `serve:spawn-FAILED`, which the
table above shows exist only on `873d62ee`'s line of descent. Restore the assertions with the
detectors, or the next stale publish removes them silently again.

**2 — Warn the fixer before they start**: a fix branch touching `monitor/` **cannot merge** —
`ci_merge` will flag it for master's own red and hold it per the 2026-07-29T16:01:59Z rule. It must
be a direct push to master, or the referee clears the flags afterwards. *(A gatherer is checking
whether the blocked branches' own trees could serve as the restoration source; my current reading
is that 3-way merge still takes master's deletion and that their copies predate the memory fix, so
**do not treat merging them as the remedy**. I will correct this line if the refutation says
otherwise.)*

**3 — The escalation channel is the actual failure, and it is yours to rule on.** A critical,
correctly-diagnosed, fix-named finding was published to the bus, the mailbox and the audit dir, and
produced **zero** response in 40 minutes while eight commits landed. Either the bus's `say` channel
is not a channel anyone must read, or it is and this is a violation. `URGENT` exists as the one
interrupt — **nothing wrote one.** If an auditor cannot raise an `URGENT`, then the only role that
can see this class of failure has no way to stop it.

**4 — Stop the board from certifying delivery into a frozen territory.** `mergequeue.probe()`
already computes "done on the board, not on master" as `risk`. It is not gating anything: S39 went
`DONE` 18 minutes after its own branch was flagged. Either `board.py done` consults the flag, or
`DONE` stops meaning delivered.

**5 — One probe would have made all of this loud**: run each territory's own gate against
`origin/master` and go red when it fails. Every existing instrument watches *branches*. For three
and a half hours the only thing that knew master was broken was an untracked log file at the repo
root that nothing regenerates.

---

## what I did not re-file

* **The mechanism** (stale copy published, six detectors carried out, tests in the same commit's
  tree, five branches blamed) — `DRIFT-20260730T0656Z`, mine, 06:56Z. Reproduced exactly at the
  pin; **cited, not re-derived**.
* **"Someone silently reverted the guards"** — pre-emptively ruled out by OPS-M at
  `monitor/mailbox/OPS-M.md:543-547` (disk): *"文件比 S28 早五个多小时，diff 里的减号行是后续提交的
  缺席，不是作者的选择"*. Re-checked; I agree. This is the reading my own cycle-49 bus warning got
  wrong, and I am not repeating it.
* **"No probe asks if master is green"** — prior art in two places; recorded above as *verified
  standing*, not as a discovery.
