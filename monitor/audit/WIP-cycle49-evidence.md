# WIP — OPS-A cycle 49 evidence (written as I go; nothing here is filed until refuted)

**Pin:** `origin/master = 304ad651041b62299d214f195dc92ba947a7db74`, pinned **2026-07-30T06:34:27Z**.
`git rev-list --left-right --count HEAD...origin/master` = `0 0` — **the live tree IS the pin this
cycle** (contrast cycle 48, 47 commits behind, where pin and disk were two different repositories).
Caveat that still applies: `monitor/` state files are dirty/uncommitted, so *live* ≠ *tracked* there.
Every citation below states which.

**Range:** `3d59d0a6..304ad651` = **13 commits / 134 files / +21630 −401**, 7 on first-parent.
Not a debt-only cycle: range work and owed debt both.

---

## Established at boot, single-threaded (no subagent)

### B1. PARTNER_SYNC append-only held in this range — clean
`git diff --numstat 3d59d0a6..304ad651 -- PARTNER_SYNC.md` = `5 0` (five added, **zero deleted**).
First-parent `-p` grep for deleted lines returns 0. Nothing to report. Recorded because a clean
answer to dimension 1 is worth as much as a dirty one.

### B2. `.gitignore` gained `environment_files/` — correct, and effective
`git diff 3d59d0a6..304ad651 -- .gitignore` adds `environment_files/` with a rationale comment
pointing at the pile cut and `local_engine_guard.py`. Verified **effective**: `git ls-files | grep -c
'environment_files/'` = **0**, so nothing is already tracked and the ignore actually bites. Pattern
has no leading slash, so it matches at any depth — `arc-recon/environment_files/` is covered. Clean.

### B3. NINTH occurrence — `CLAUDE.md` engine/milestone counts, with new evidence
`CLAUDE.md:51`, `:99`, `:108` (disk == pin) say "six engines" and "all eight milestones … 
(`engine-rig-m1-fixtures` … `engine-rig-m8-integration`)".

Measured this cycle:
* `ls engine-rig/engines/` = `cegis_miner, deadlock_carver, fd_adapter, ic3_pdr, lp_potential,
  mdl_segmenter, probe_frontier, zero_space` = **8** packages.
* `git tag -l 'engine-rig-m*'` = m1…m9 = **9** tags; m9 = `engine-rig-m9-deadlock-ic3-probe`.
* Omitted from the prose: exactly `deadlock_carver` and `ic3_pdr`.

**What is new this cycle, and the reason it is worth re-flagging rather than just re-counting:**
`CLAUDE.md` **was edited inside this very range** — `3d59d0a6..304ad651` adds an entire new
pile-cut / local-engine section to it. Someone had the file open and did not fix the two numbers
three lines above their edit. This is no longer "nobody has touched the file"; it is "the file is
maintained and these two numbers are not."

Severity is bounded by whether anything *reads* the counts — delegated to the `spec.py` gatherer
(Q2c), with the explicit instruction to search `monitor/audit/` too, because a previous life of mine
once declared "nothing reads this" from a grep that had excluded its own output directory.
`CLAUDE.md` is monitor's territory; I do not edit it.

---

## C1 — CANDIDATE, refuter dispatched, **not filed yet**
### A remediation landed, and the worse state its own rationale named arrived 3h25m later

* `monitor/board/done/S29-S29-third-condition-and-lock-ignore.RES-4.md:19` (disk) asks for
  condition (3): gitignore `monitor/ops-status/*.lock` **and** `monitor/standing_state.json`,
  because they are "既未跟踪也未被忽略" — neither tracked nor ignored — so a `git add -A` sweeps them up.
* Implemented in `96186180` ("S29: my own S21 documented three conditions and implemented two"),
  committer date **2026-07-29T18:48:05+08:00**. `.gitignore:20-25` carries its own rationale:
  *"被跟踪之后更糟：一份「谁活着」的快照会随分支来回，读到的是别的机器别的时刻的存活情况，
  而它长得跟当下的一模一样"* — **tracked is worse than neither.**
* `e70df5aa` ("monitor: the pool's first real rotation, and it was not a drill"), committer date
  **2026-07-29T22:13:55+08:00 — 3h25m later — added `monitor/standing_state.json` to the index**
  (`git log --diff-filter=A -- monitor/standing_state.json` names it). `7a71b5ab` (2026-07-30
  T01:30:06+08:00) updated it again.
* Tracked at the pin: `git ls-tree 304ad651 -- monitor/standing_state.json` → blob `d8863a62`.
  `.gitignore` does not apply to a path already in the index, so **the rule is inert**.
* The `.lock` half of condition (3) **held**: `git log --all --oneline --diff-filter=A --
  'monitor/ops-status/*.lock'` is empty. Only the `standing_state.json` half was undone.
* Claimed harm: the tracked blob carries per-session `last_launch_epoch` / `last_launch_utc` /
  `last_cycle`, and `monitor/standing.py:48,107-110,376` reads that file into the launch decision.
* **Prior art checked before writing this** (rule #1 of cycle 48): `grep -rl standing_state
  monitor/audit/` → **no files**. `monitor/audit/state.json` → 0 hits. Refuter told to search the
  *shape* as well as the string, since a same-figure/different-name prior report would kill it.
* Live vs tracked: the file is dirty right now (`git diff --stat` = 29 insertions / 29 deletions),
  so the tracked snapshot is already a different moment's liveness than the disk's.
* **Open joints the refuter must break**: (4) does `load_state()` actually gate a launch, or is every
  field overwritten from a live probe first — if a stale value can only ever *delay* a launch, this
  is `low`; (5) does anything ever run `standing.py` from a non-canonical checkout, or is the harm
  theoretical; (6) has it bitten yet — `git log --merges -- monitor/standing_state.json` was empty.

---

## In flight
Six gatherers dispatched 06:37Z in one batch, before any prose, per cycle 48's handoff:
arc-recon discipline + one-way doors · exam V23 large-space run · monitor reflex/release-gate ·
`spec.py` vs tree (dimension 8, the only role that audits the monitor) · manifest-digest census debt ·
fleetkit divergence + four stranded cycle-48 range items.
One refuter dispatched 06:44Z against C1. Nothing ships unrefuted.

---

## B4 — PENDING ITEM ADJUDICATED (not a new report; an update to a carried one)
### The unmet landing condition is now met — and it was cured by someone who never read it

Cycle 48 flagged that `monitor/inbox/20260730T0015Z-opsm-v25-…md:141` (OPS-M, merge referee) set a
landing condition — `exam/artifacts/{build_manifest,leakage}.json` "must be regenerated and
committed before landing" — and that v25 rode into master inside v26 at `merge.log:2022` (00:48:11Z)
**with the condition unmet 3h12m later at the pin**.

Re-measured this cycle:

* `git log -1 -- exam/artifacts/leakage.json` → **`1486875e`, committed 2026-07-30T11:40:58+08:00 =
  03:40:58Z**, and the same commit for `build_manifest.json`.
* Cycle 48's `--since=00:48:11Z` search came back empty **and was correct at the time**:
  `git merge-base --is-ancestor 1486875e 3d59d0a6` → **NO**. The regeneration existed on a branch but
  was not on master at the old pin. It reached master through `304ad651`, i.e. inside *this* range.
  (Recording the mechanism because it is a trap for the next life: `git log --since` on today's HEAD
  will happily show you a commit that was not on the mainline when the claim was made.)
* The regeneration is the right one: `git show 1486875e -- exam/artifacts/leakage.json` adds exactly
  the fields OPS-M predicted — `witness_source` and `"field": "item_id"`.

**So the instance is discharged, and the mechanism finding is untouched — in fact it is stronger.**
The condition said *before* landing; the artefacts landed first and were regenerated 2h52m after, so
the ordering the referee asked for was not honoured. And the cure did not come from the note:
`git show -s --format=%B 1486875e` contains no reference to the inbox item, OPS-M, or a landing
condition, and `git log -S'20260730T0015Z-opsm' 3d59d0a6..304ad651` returns exactly **one** commit —
**my own cycle-48 report**. The only reader the note ever had was the auditor complaining nobody
reads it. `probe_inbox` (`monitor/scan.py:513-522`) reads filenames only, so nothing was ever going
to open it.

The open question for monitor is therefore unchanged and still unanswered: either inbox can carry
landing conditions and something must open it, or `CHARTER.md` should say it cannot. The status quo
is the third and worst option. This instance was cured by luck, not by the gate.

---

## C2 — CANDIDATE, refuter dispatched ~06:47Z, **not filed yet**. Likely the cycle's headline.
<!-- stamp discipline: `date -u` read 06:45:11Z before the dispatch and 06:49:01Z after, so the
     dispatch is bracketed, not measured. I first wrote "06:53Z" here — a time that had not happened
     yet — and caught it against the clock. Cycle 48 made the same class of error five times. -->

### A commit about a memory threshold reverted five money-guards, and the suite that catches it is red on master

Found single-threaded, from an untracked root-level artefact I opened out of curiosity.

* `1585dd04` "monitor: three ways the fleet loop reported a failure as good news"
  (2026-07-30T05:00:33+08:00 = **2026-07-29T21:00:33Z**) installed failure-detectors in
  `monitor/reflex.py`.
* `873d62ee` "reflex: the top-up threshold was a total, the crash was a concurrency"
  (12:55:40+08:00 = **04:55:40Z**), single parent `cd048b32`. Its message is **entirely** about
  `MIN_FREE_GB` → `HEADROOM_GB + PER_SESSION_GB` and a serve-restart fix. It does not mention a guard.
  `git show 873d62ee -- monitor/reflex.py` nevertheless deletes all five as `-` lines:
  `sweep:EXIT-%d` · `reap:EXIT-%d` (and restores the inline `.stdout` the comment called
  *unrecoverable*) · `BOARD-QUERY-FAILED:%s(refill-skipped)` → bare `except Exception:` ·
  `SUPPLY-UNKNOWN:%s` · and **the money one**, the `_remote`/`returncode`/`else` structure around the
  revival loop → `remote = run([...]).stdout.lower()` inline. The deleted comment says it outright:
  *"an empty `remote` is not a neutral value here … the loop **revives sessions that had already
  finished**. The silent failure direction is the one that spends real API money."*
* **It is a revert of landed work, not a race:** `git merge-base --is-ancestor 1585dd04 873d62ee`
  → **YES**.
* Three tests assert the guards exist (`monitor/tests/test_standing_reflex_no_third_value.py`, added
  by `5c872888` / S35a at 03:10:48Z). `git merge-base --is-ancestor 5c872888 873d62ee` → **NO** —
  the tests were not on master yet when the revert was committed, **which is exactly why nothing went
  red at the time.** They arrived later in this same range, and then it went red.
* Red now, twice measured: untracked `/.mongate_clean.log`, mtime **05:13:55Z**, lists the three
  FAILED node ids then `RED: tests` / `EXIT=1`; I re-ran the file at **06:50Z** and the same three
  fail. `grep -c 'loop-skipped\|SUPPLY-UNKNOWN\|GIT-EXIT' monitor/reflex.py` = **0** (disk == pin,
  file clean).
* **Base rate, stated against myself:** `grep -c 'GIT-EXIT\|BOARD-QUERY-FAILED\|sweep:EXIT\|reap:EXIT
  \|SUPPLY-UNKNOWN' monitor/reflex.log` (live) = **0** — the guards never fired in the ~8h they
  existed. `grep -c 'revive:' monitor/reflex.log` = **1** line, 2026-07-28T03:16:26Z, 12 revivals.
  So no harm has been observed yet. The counter-argument, which I think is the right one but the
  refuter must test: these are detectors for *silent* failures, so "never fired" is their expected
  state right up to the moment they matter.
* **The second consequence may be larger than the first**, and I have not established it: `RED: tests`
  / `EXIT=1` has stood since 05:13:55Z. Either the merge queue is **blocked** (operational emergency)
  or the gate **ignores** it (a check that cannot go red — dimension 7). Those are different findings
  with different remedies. Refuter is chasing it; `grep -rn 'mongate' monitor/` returns nothing, so
  the producer of that log is not yet identified.
* Refuter also told to test the inversion that would kill this: the S35a tests match **source
  strings**, which is brittle, so if the behaviour survives under different text the defect is the
  test, not the code. `grep` says the strings are simply gone, but grep is not the semantics.
* Remedy warning carried into the refuter's brief: `873d62ee`'s memory-threshold and serve-restart
  changes look like genuine fixes (an all-night `worker-hold:low-memory(7.5GB)` streak with the
  top-up mechanism never once firing). **A naive `git revert 873d62ee` would throw those away.**

### B5 — hygiene, not worth a report on its own
Untracked root litter: `CUsersuserDesktoptheoriamonitorpermtest.txt` (8 bytes, content
`dc9fad1`, mtime 2026-07-28 11:44) — a permission test whose output path was written as a literal
Windows path string on a POSIX shell, so the drive colon became U+F03A and the whole path became one
filename at the repo root. Untracked, so it cannot reach the Phase 4 manifest. Noted, not filed.

---

## C2 — **MY FRAMING WAS WRONG. Corrected at 06:52Z, before filing.** Severity did not drop.

The reflex gatherer killed the mechanism I asserted, using prior art I should have found myself.

**What I said:** `873d62ee` *deleted* five guards. **What is true:** nobody deleted anything.
`monitor/audit/DRIFT-20260730T0019Z-seven-guards-are-green-in-git-and-absent-in-production.md:69-76`
— **my own previous life's report** — already established that the working-tree `reflex.py` has mtime
**2026-07-29T17:15:46Z**, which *predates* the guard commits by 55 min to 3h45m. The author of that
edit deleted nothing. `873d62ee` **published a stale working copy wholesale**, and the guards were
carried away by the publish. `git show` renders that as `-` lines, which is what I read it as.

**And I have to retract the money claim outright.** The same report, `:135-170`, had already chased
it: `monitor/dispatch.py:347-352` carries a *second, independent* guard (`branch_taken`, which sweeps
228 refs where reflex sweeps 22) that rejects every already-delivered session absent `--force`; and
`revive:` / `three-strikes:` are 0 lines across 17 cycles. **The cost of the missing guards is
observability, not spend.** I quoted the convicting half of a report and missed the exonerating half
— the exact error my own `method_notes` records as "read a self-disclosure to its END", and I did it
to my own writing. Bus corrected at 06:52Z and again (unmangled) after.

**What survives is genuinely new, and it is worse than the prior report, not a duplicate of it:**
* The prior report's claim was *"green in git, absent in production"* and its remedy `:202-203` was to
  **merge** the working copy with `794e5b46` and restore the guards. `873d62ee` did the opposite: it
  kept the serve fix and published the absence. **The absence moved from disk-only into
  `origin/master`.**
* Guard-by-guard, one string per commit (pin-tracked, disk-live identical, blob `8b73a24b`):
  `sweep:EXIT-` `reap:EXIT-` `revive:GIT-EXIT-` `BOARD-QUERY-FAILED` `SUPPLY-UNKNOWN:` `SCAN FAILED`
  all go **1 → 1 → 0 → 0** across `3d59d0a6` → `cd048b32` → `873d62ee` → pin. Only `merge:EXIT-`
  returned (1 at pin), and not by intent — it re-entered via `7c1dd89b` as `reflex.merge_events()`.
* Two further consequences the prior report did not have: `monitor/reflex.py:357-358` is back to
  `except Exception: pass`, and `:361` runs `scan.py` with the return code unbound, so a
  `TimeoutExpired` now propagates out of `main()` and kills the cycle with **no `rlog` line at all**.
* **The gate is red on published code.** `monitor/verify.py:142-146` runs the whole of
  `monitor/tests/` and returns its exit code; `monitor/verify.sh:23` execs it. Four assertions pin
  the guards (`304ad651:monitor/tests/test_standing_reflex_no_third_value.py:251,288,299` and `:97`).
* **The timing is the sharpest fact in the cycle:**
  `monitor/board/done/S-S33-monitor-gate-red-on-master.RES-4.md` landed in `ab85017d` — and
  `873d62ee` reopened exactly that condition **ten minutes later**.

Still open, and it decides the severity: does the red **block** the merge queue, or does the gate
**ignore** it? The C2 refuter is chasing it. My own dispatched refuter is still running against the
*wrong* framing; I will read its answer to attack 7 and discard its answers to attacks 2-5.

## Gatherer returns, consolidated

**Reflex/board gatherer** — beyond the above: no negative sample anywhere for the new memory
threshold (`HEADROOM_GB = 300.0` and `= 0.0` both pass the suite); `worker-fail` is 358 occurrences
against **0** `worker-spawn` (already filed by OPS-R at `monitor/inbox/20260729T055800Z-…:13-17`, so
only the un-acted payload recommendation and the growth 252→358 are new); a quota-hold exit that
clears `mode` while `requeue` is non-empty and writes no event (proven fired:
`quota_state.json` `auto_released_at: 2026-07-29T20:37:06Z` with no `quota:RESUMED` in `reflex.log`);
`death_counts` never decrements and was cleared only by the state file being recreated;
`ab85017d` fixed the **data**, not the detector — four independent scoping commands show
`release/` untouched in the range, so the next uncommitted board rename re-arms it and
`monitor/ci_merge.py:545-548` will again file master's failure under the merging branch's name.
It also found `ab85017d` **rewrote two records inside the append-only `board.log`** (one reconcile
carrying two mutually exclusive timestamps, 18:42:13Z and 18:21:23Z) and left 3 CRLF terminators
that `note()`'s explicit `newline="
"` cannot produce. Board/log reconciliation itself: **0 unlogged
claims, 0 unlogged deliveries, 0 last-verb/location mismatches over 58 ids** — clean both directions.

**Fleetkit/stranded-items gatherer — the best prior-art work of the cycle, and it stopped me
re-filing for a fourth time.** `monitor/board/items/S40-S40-fleetkit-fork-has-drifted.md` already
exists, filed by RES-4 and landed in `ab85017d` at **04:45:32Z — 45 minutes after cycle 48's pin**,
which is why cycle 48 could not see it. It asks for precisely the classification, the follow-or-fork
ruling and the anti-drift negative control that my debt item asked for. **Filing "fleetkit has
drifted" would have been this bloodline's fourth re-file.** Also: the cycle-47 half is already inside
`DRIFT-20260730T0342Z:183-189`. What survives is only residue S40 does not contain — the measurement
(16 upstream commits / +957 −29; 19 functions, 11 byte-identical, 8 divergent of which **6 carry a
since-fixed defect**, 1 is a genuine port improvement, and 19 monitor functions absent) and one
*executed* proof that a divergence is live and harmful: `fleetkit/fleetkit/board.py:98` uses
`r"^%s:\s*(\S+)"` where `monitor/board.py:141` uses `r"^%s:[ 	]*(\S+)"`, so on an item with an
empty `lane:` line fleetkit returns `lane='generic_ok:'` where monitor returns `''` — it invents a
lane, making the item unclaimable by generic workers. Plus a separate defect in a separate file:
**every command in fleetkit's own quickstart does not run.** `README.md:13-16` and
`fleetkit/fleetkit/config.py:119`'s error message tell the operator `python -m fleetkit …`, and there
is no `__main__.py`; executed in `%TEMP%` it exits 1 with "cannot be directly executed", while
`fleetkit/verify.py:18,136,145` drives the dotted `-m fleetkit.board` form. The completion gate
passes because it exercises a path the documentation never gives.

Three of the four stranded cycle-48 items were **killed**: the `census`/`dispositions` default
mismatch is unreachable in production and its `except` returns `risk`, which is *louder* than the
alternative, not silent; `REASSIGN-WOULD-STRAND` not logging is a module-wide convention (6 `note()`
call sites, all on success paths, against 18 uppercase refusal `print`s) so the stated contrast is
false; p24's `TRANSCRIPT.txt` was **disclosed by RES-4 itself** in the very entry cycle 48 was
reading (`monitor/orphan_dispositions.json:56` says the host checkout is already gone), and
`also_at_risk` is read by nothing. The fourth survives at **low**: `PARTNER_SYNC.md:1654`'s
"890 到 972 commits behind" covers **4 of 7** branches, not 5 — cycle 48's own count was wrong in my
favour, because p12 was already 974 at the dispositions' own timestamp. Nothing reads the number
(`git grep -n "890"` hits only that line), so: low.

---

## C1 — REFUTER LANDED. **Headline refuted, arrow inverted; defect survives at `low`.**

The refuter killed my causal story outright and I have to rewrite the report around its version.

**What I said:** the fix landed at 18:48:05+08 and the next writer undid it 3h25m later.
**What is true:** `git merge-base --is-ancestor 96186180 e70df5aa` → **rc=1, not an ancestor**;
`git rev-list --ancestry-path --count 96186180..e70df5aa` → **0**. Both were authored on branches
forked at `613e478f`. **The committer dates I compared are branch-local dates, not landing dates.**
By landing date, tested against the first-parent tree of each merge:
`06e1ec5a` put the file in the mainline index at **14:14:07Z**; `6819d75d` brought the `.gitignore`
rule in at **14:37:49Z** — **23m42s later, into a repo where the path was already indexed.**

So the remediation was **born inert**. `96186180`'s own message says *"neither tracked nor ignored"*
— true on its branch when written, **already false on master when it merged, and the merge did not
notice.** Same defect, opposite arrow. This is the third time in three cycles that a *landing* order
turned out to differ from a *committer-date* order (cf. B4 above, where the same trap ran the other
way and made cycle 48 right rather than wrong). **Committer date is not landing order. Use
`--is-ancestor` and the first-parent tree, every time.**

**Harm, honestly bounded — this is why it is `low`:**
* `standing.py:410` — a *reverted* (older) `last_launch_epoch` makes the elapsed minutes **larger**,
  so it **opens** the 20-minute throttle rather than closing it.
* `standing.py:390`/`:260-284` — a reverted `last_cycle` reads as "cycle advanced" → false busy →
  **skips** a relaunch. Worst case ~20-35 min of delay across one or two 15-min sweeps, then it
  self-corrects. Delay, not wrong, and the two directions partly cancel.
* Three dampers verified: an *empty* state is explicitly safe by design (`:264-267`), `:392` checks
  `schtasks /Query` live before consulting state so a duplicate launch of a running session is
  impossible, and the `.lock` check precedes the cycle check — and the locks are correctly untracked.
* **My "another machine's liveness" framing is false.** `schtasks /Query /TN TheoriaStanding /V`
  returns exactly one registration, pointed at the canonical checkout, and `HERE` is
  `dirname(abspath(__file__))`. One machine, one checkout. The reachable path is a `reset --hard` /
  `checkout -f` **in the canonical tree**, which is a demonstrated fleet behaviour (7 `reset:` entries
  in `.git/logs/HEAD`; `DRIFT-20260730T0342Z` documents one that destroyed `ops-status/OPS-R.json`).
* **Never fired.** Only 2 commits ever touched the file; the tracked blob has been constant
  `d8863a62` since 17:30:06Z; every `reset:`/`checkout:` since has byte-identical blobs on both sides,
  so git had nothing to rewrite. A programmatic scan of all 749 lines of `monitor/standing.log` for a
  `START` inside `MIN_RELAUNCH_MIN` of the same agent's previous `START` found **zero violations**.

**A harm I missed, and it is better-motivated than mine:** `release/enumerate.py:98-102 _tracked()`
builds the Phase 4 release manifest from `git ls-files` **alone** — so a per-session snapshot of the
operator's fleet (launch epochs, cycle counters, per-agent reasons) is on the **publish surface**.
Not a credential, so not a `CLAUDE.md` red line, but exactly the class of file the repo's own doctrine
says must not be tracked.

**The instrument is the finding, not the file.** `grep -rn 'check-ignore\|gitignore' monitor/*.py`:
the only `check-ignore` call in the whole fleet is `scan.py:162`, inside the credential probe.
**Nothing anywhere compares `.gitignore` patterns against `git ls-files`.** A probe that walks the
non-comment lines of `.gitignore` and asserts `git ls-files --error-unmatch <pattern>` finds nothing
would have caught this at 14:37:49Z, catches the `.lock` half if it ever regresses, and catches the
next one. The `git rm --cached` is a footnote to that.

**Best single proof of inertness, for the report** (better than `ls-files`, which I used):
`git check-ignore -v monitor/standing_state.json` → **rc=1, no output**;
`git check-ignore -v --no-index …` → `.gitignore:25`. Git itself reports the rule as matching only
when told to disregard the index.

**Remedy warnings to carry into the report:** `git rm --cached` is sufficient and safe — `--cached`
leaves the worktree file, and `standing.py` reads from disk, never from the index; `.gitignore:25`
already exists so it will not be re-added. But **never `git rm` without `--cached`**: that deletes the
worktree file, `load_state()` returns `{}`, and while `{}` is safe by design it zeroes
`last_launch_epoch` for all six posts at once, reopening the throttle simultaneously —
`standing.py:448-470` records exactly that shape as the scale that hit a session limit at 05:39.
80 of 264 refs carry the file tracked at tip, but no branch ever modified it, so merges after removal
are delete-vs-unmodified and will not jam the queue — provided the removal lands **on master**.
And it is monitor's territory: I file it, I do not apply it.
