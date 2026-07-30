# WIP — cycle 47 established evidence (written as measured)

> **SUPERSEDED IN PART — read this first.** Two sections below were REFUTED by adversarial review
> after they were written, and the corrected versions are in the filed reports, not here:
> * **§E6 is WRONG.** A scan *did* observe the crossing (sampled 03:05:00Z, published
>   `OPS-A risk age_min 121` at 03:23:35Z). The real defect is a ~20-minute probe→stamp skew, and
>   the real erasure is at `state.json`'s rewrite, not at the heartbeat. See
>   `DRIFT-20260730T0346Z-every-age-on-the-dashboard-is-stamped-with-a-time-it-was-not-measured-at.md`.
> * **§E9 is WITHDRAWN** — the 59+/114− figure is a wrong-base artefact my own lineage had already
>   retracted (true minimal base `0c099ae8` = 24+/5−), and the billing consequence dies to five
>   refusals. See §G8 of `WIP-cycle47-evidence-2.md`.
> * **§E5's headline verb was too strong**: `occupied()` does read mtime (`standing.py:275`); the
>   rule is "mtime alone is not sufficient", not "mtime does not count". Corrected in
>   `DRIFT-20260730T0342Z-…`.
> E1–E4, E7, E8 stand as written.

Not a report. This is the disk copy of facts established before close, so a context death
loses nothing. Reports are cut from this. Cycle 46 died with a good plan in context and
**nothing on disk**; this file is the direct response to that failure mode.

Pinned rev: `223f78a8` = origin/master at 03:16Z. Local HEAD/master `3b2a5873` (behind 40).
The WORKING TREE is what the fleet runs.

---

## E1 — the cycle-46 death, exact

| fact | value | how measured |
|---|---|---|
| last heartbeat written | 2026-07-30T01:04:00Z | `monitor/ops-status/OPS-A.json` self-report and mtime agreed |
| launched by | `standing.log:580` `01:01:57Z START OPS-A (lane=None) ok=state-unknown` | grep |
| audit output produced | **none** | newest `monitor/audit/` mtime still 00:44:31Z (cycle 45's) at my boot |
| state field | `working`, **no `wake_at`** | the file itself |
| silence | 2h11m (01:04:00Z → my write 03:16:25Z) | os.stat |
| successor launched | `standing.log:643` `03:15:12Z START OPS-A` | grep |

`HOSTED.md:50-66` (S19) says silence >45 min without `wake_at` is judged stopped. It was not.

## E2 — the only live watcher computes the age and never reads it

`monitor/standing.py:350` (worktree) / `:358` (at 223f78a8): `age = board_mod.heartbeat_age(agent)`.
`age` occurs exactly twice: that assignment, and the log format string `:379` (`:387` landed).
**None of the eight `why` branches at `:353-374` reads it** — `live` / `occupied` / `quota hold` /
free-memory / `MAX_STANDING` / `CLAIMABLE_UNKNOWN` / `not w["any"]` / `MIN_RELAUNCH_MIN`.
True in BOTH the running worktree copy and the landed copy, so this is the design, not a
deploy-gap artefact.

Observed rather than argued — the launcher printed the corpse temperature every 15 min and
declined to act, eight times:

```
01:15:55Z skip OPS-A: lock held 12 min ago          hb=12min
01:30:56Z skip OPS-A: no work (unread=0 held=0 …)   hb=27min
01:45:56Z skip OPS-A: cycle advanced 15 min ago     hb=42min
02:00:04Z skip OPS-A: no work                       hb=56min
02:16:49Z skip OPS-A: no work                       hb=73min
02:30:57Z skip OPS-A: no work                       hb=87min
02:45:57Z skip OPS-A: no work                       hb=102min
03:00:56Z skip OPS-A: standing cap 5 reached        hb=117min
03:15:12Z START OPS-A            <- and NOT because of the age; see E3
```

## E3 — what restarted me was a board signal I am forbidden to act on

`standing.py:287-299 ops_work_for()`: for `STANDING_OPS = {"OPS-A","OPS-M"}` (`:61`),
work = `unread` (bus) or `moved`, where `since = getmtime(ops-status/<agent>.json)` and
`moved = getmtime(BOARD_LOG) > since`. My bus has been `NO-NEW-MESSAGES` for 11 cycles, so
`unread` is structurally 0. The ONLY thing that can start OPS-A is **board.log moving** — and
`CHARTER.md:27` forbids OPS-A the board entirely (0 of 347 board.log lines are `by OPS-A`).
`claimable=0` from 01:30–02:45 means the board was merely quiet; **2h11m is not a bound**, it is
however long the board happened to stay still.

## E4 — the second refusal exists and has fired once, ever

`monitor/reflex.py:266-298` is the revive / three-strikes block, the one path that relaunches on
death rather than on work. Whole-log counts:

```
grep -c "revive:"       monitor/reflex.log -> 1
grep -c "three-strikes" monitor/reflex.log -> 1
grep -c "quota:HOLD"    monitor/reflex.log -> 66   (positive control: markers do appear)
```

Both hits are the log's first two lines, `2026-07-28T03:16:26Z` and `03:26:15Z`, ~28h before this
death, and every id in them (`A-1`, `P-19`, `M-0`, `R-1`, …) is a retired pre-board prompt shape.
It did not fire for cycle 46. Refines last cycle's "zero in 17 post-cut cycles": the true figure
is **one ever, both pre-cut**.

## E5 — mtime as liveness contradicts the codebase's own written ruling

`monitor/standing.py:213-216`, inside `occupied()` — the function that decides whether to spend
money on a launch — states the rule and cites a dated incident:

> `* mtime **不算**：一次 git merge 就能把死会话的 ops-status 摸新，今天下午就发生过（RES-2/RES-4 的 mtime 49 分钟，自报时刻却是几小时前）。`

Three probes in `monitor/scan.py` judge staleness by exactly that signal:

```
:612  age = (time.time() - os.path.getmtime(rel(path))) / 60      # probe_ops_duty
:613  status = "risk" if age > stale_min else "green"
:1091 age = int((_t.time() - os.path.getmtime(rel(path))) / 60)   # _self_driving
:1188 age = (_t.time() - os.path.getmtime(rel(path))) / 60        # probe_needs_human
```

Live proof the hazard is not theoretical — my census at 03:20:25Z:

| id | self-reported utc | file mtime | divergence |
|---|---|---|---|
| OPS-R | 2026-07-29T05:59:00Z | 2026-07-29T10:19:52Z | **mtime 4h20m NEWER than the self-report** |
| RES-2 | 2026-07-30T03:22:00Z | 2026-07-30T03:03:58Z | self-report 18m newer, and ~2m in the FUTURE |

The dangerous direction is OPS-R's: mtime newer ⇒ age too small ⇒ dead session reads green.
`occupied()` gets this right; the dashboard gets it wrong.

## E6 — the crossing had no observer, and the evidence then erased itself

`scan.py:591-597 OPS_DUTY` gives OPS-A a 90-min threshold, so `probe_ops_duty` owed a `risk` from
**02:34Z**. The last scan ran **02:23:38Z** (`monitor/state.json` `generated_at_utc`; mtime
02:23:49Z; `reflex.log` mtime 02:23:47Z) and recorded OPS-A `status: green, age_min: 58`. None
since, against the file's own declared `stale_after_s: 1200` (20 min).

It can never be seen now: `probe_ops_duty` reads the file's **mtime**, and my recovery write at
03:16:25Z reset it. **A death repaired before the next scan is structurally invisible to the probe
that exists to detect it** — the successor's first act destroys the evidence. (Lineage note,
earned: "overwritten is not fixed.")

Delegated: whether a 60-min scan gap is a stoppage. reflex.log line-leading gaps are median 5.2 /
p90 12.7 / **max 259.6** min, so a long gap is not unprecedented and I will not call it a stoppage
without the scheduler's intended interval.

**Discarded measurement, recorded so nobody repeats it:** `state.json`'s `history` list is NOT a
per-scan log — 15 entries, LOCAL-time stamps (UTC+8, no `Z`), newest `2026-07-29 19:07:33` local
= 11:07:33Z, ~15h older than the scan that wrote the file. It cannot measure cadence.

## E7 — killed by my own check, in one read

Hypothesis: `standing.py:187 unread_count()` might pattern-match mailbox prose, so a TO-MONITOR
quoting `status: OPEN` could trigger a paid launch. **KILLED.** `:189-203` counts lines in
`monitor/bus/<agent>/in.jsonl` minus `cursor.json`'s `last_seq`; it never opens the mailbox
markdown. No prose channel exists.

## E8 — contract-step-1 verification (not inherited on trust)

`monitor/mailbox/ALL.md` has exactly 5 `status: OPEN`, all 07-28 fleet broadcasts already
receipted by prior lives. My own mailbox's single `grep -c "status: OPEN"` hit is **prose inside a
prior TO-MONITOR at :767**, not an item. Zero real OPEN items for me.

## E9 — the deploy gap, decomposed (refutation in flight)

```
git diff --stat HEAD          -- 'monitor/*.py'  -> reflex.py ONLY (59+/114-)  = genuine hand-edit
git diff --stat HEAD 223f78a8 -- 'monitor/*.py'  -> 10 files, 1032+/58-        = un-pulled landed code
```

Two causes needing two different repairs: ONE file needs committing, NINE need a pull. Among the
un-pulled: `board.py` (286 lines), an entire new `tests/test_board_unreachable.py` (435 lines,
absent locally), and `standing.py`'s S35 hunk replacing the running `candidates(lane)` with
`offers(agent, lane)[0]` — whose own docstring at 223f78a8 claims the running form bills a real
session per `MIN_RELAUNCH_MIN` and names two items stuck 14.9h and 12.9h. Mechanism already filed
by OPS-M (`inbox/20260730T0012Z-opsm-the-deploy-gap-…`) and by my lineage (`DRIFT-20260730T0019Z`);
only the decomposition and the billing hunk would be new.

---

## G2 — dimension 1 delta sweep, `794e5b46..223f78a8` (gatherer returned)

**Range structure: 38 commits, 9 on the mainline first-parent path, 29 branch-only drafts.**

* **Credential: CLEAN.** Key masked `7171...05dd` (len 36). Zero hits across per-commit diffs
  (1,552,049 chars), **all 159 blobs newly reachable in range**, 6353 tracked blobs at 223f78a8,
  6283 index entries, and 172 untracked non-ignored files. `.env` untracked and ignored
  (`.gitignore:3`). Controls: 6 matcher variants all fired on a planted buffer; matcher fires on
  `.env`'s own content; NAME reader found 65 index blobs and 26 range blobs, so the zeros are real.
  **Method upgrade worth keeping: `git log -p` OMITS MERGE DIFFS and 9 of 38 commits are merges —
  the `rev-list --objects` blob sweep is what closes that hole.**
  NAME count 65 (at 794e5b46) → **69** at 223f78a8; 5 added, all legitimate (the new NOSECRET gate
  and its tests, a P20 run record, my own mailbox), 1 removed. *Correction to my own brief: I told
  the agent "64 last cycle"; measured by `git grep -l` it is 65, so the 64 was method-dependent.*
* **Sealed pile: CLEAN.** 21 ids read programmatically from `piles.json` `sealed_pile`, never
  transcribed. **Zero sealed ids on any added (`+`) line in the range.** Three blobs in range
  contain sealed ids — `PARTNER_SYNC.md:175/365/1177`, `monitor/mailbox/OPS-A.md:172`,
  `monitor/bus/OPS-A/out.jsonl:33` — all byte-identical at both revs at identical line numbers,
  i.e. append-only files riding along, not new touches. All are the legitimate categories
  (INC-BA-001, the F-11 quarantine ruling, S23 narrative, an explicit "enumeration, not contact").
* **Append-only integrity: CLEAN.** Per-mainline-commit `--unified=0` first-parent diffs over 9
  targets + 18 `candidates.jsonl` streams: **zero hunks with a `-` line, zero deletions or renames
  on mainline across all 38 commits.** Control: 5 pairs produced non-empty diffs. PARTNER_SYNC grew
  1587→1640; 4 of 5 steps are strict byte-appends.
  One non-violation worth knowing: `45307105` inserted 17 lines mid-file at 1387
  (`@@ -1386,0 +1387,17 @@`). Nothing modified or deleted, so the red line holds — and the board is
  **already** thoroughly non-chronological because `.gitattributes` sets `PARTNER_SYNC.md
  merge=union`. Mid-file placement is the existing norm, not drift.
  **My own error, recorded:** I told the agent to check `monitor/incidents/**`. That path does not
  exist; the ledgers are `arc-recon/data/incidents.jsonl`, `baseline-arms/INCIDENTS.md`,
  `theoria-arm/INCIDENTS.md`, `battery/PREDICTIONS.md`. My prompt invented the path, not AUDITOR.md.
* **Generated artefacts: one finding (Low–Medium), refutation in flight.** See G2-F below.

### G2-F — run-manifest digests that verify against nothing

`exam/runs/20260729T1130Z-V21-leakage-gate-token-level/MANIFEST.json`, hashing method stated
explicitly as **LF-blob**, and the eol explanation *eliminated* rather than assumed because 19 of
21 declared digests in the same manifest reproduce exactly by LF-blob:

* `adversarial/PROBE_OUTPUT.txt` — declared `28936ffec1d75c0a…`; LF-blob `ecbbcabe2a4c28de…`;
  CRLF-reconstruction `d2b7970154dbabb3…`. Blob is 30011 bytes, 382 LF, 0 CRLF, 0 lone CR. No
  variant tried reproduces the declared digest, and the path has exactly ONE version in all git
  history (`1f378483`, the commit that also ships the manifest) — so the declared digest
  corresponds to no committed content of that file, ever.
* `adversarial/MUTATION_TABLE.txt` — pure LF in the blob (51 LF, 0 CRLF) but the declared digest
  matches the CRLF reconstruction: CRLF on disk when hashed, normalised on commit.

Mechanism: the generator's `sha256()` does `open(path,"rb").read()` — on-disk bytes — while git
stores eol=lf-normalised bytes, which cannot be self-consistent for a CRLF-on-disk file in an
`eol=lf` territory on a `core.autocrlf=true` machine. The manifest self-reports
`"worktree_dirty": true` at `utc 2026-07-29T18:17:10Z`, ~1 min before its shipping commit landed.

Refusal analysis: `scan.py:774-785` globs every `*/runs/*/MANIFEST.json` and reads **only
`data.get("utc")`** for clock sanity; `exam/verify.py` has no manifest digest check; no repo-wide
gate recomputes `files[].sha256`. **Counter-weight I must keep in the report: 61 of 62 digests DO
verify once re-baselined at the shipping commit — so the generalisation is a gap, not a rot.**

**Method trap the agent hit and escaped, worth more than the finding:** checking the 8 changed
manifests against the tree at 223f78a8 gave **10 mismatches**; re-baselining each against the tree
at the commit that ships it collapsed 10 → 1. A run manifest is a point-in-time snapshot; auditing
it against HEAD manufactures nine false positives.

---

## G6 — the retraction re-examined (gatherer returned; refuter in flight)

Subject: `monitor/audit/DRIFT-20260729T2100Z-the-build-lane-has-two-fail-closed-gates-and-one-can-never-open.md`,
byte-identical in worktree, at 794e5b46, and at 223f78a8.

**Verdict (i): the retraction at `:169-174` was WRONG and the original conclusion should be restored.**

The retraction rested on **exactly one** piece of evidence — the text of `reflex.log:252` read as a
factual report of six worker launches — and that receipt is a `print`, not a measurement:

```
quota.py:543-544   subprocess.run([... "dispatch.py", "--only", pid_str], cwd=ROOT)   # result DISCARDED
quota.py:545-549   st["requeue"] = rest; mode; resumed_at; save_state(st); print("relaunched %s; …")
reflex.py:213-218  r = run([... "quota.py", "resume"]); events.append("quota:RESUMED(auto)"); rlog(r.stdout last line)
```

`quota.py` is blob-identical at both revs and in the worktree (`1cbe5a26…`). `:545-549` are
unconditional and causally independent of the six subprocesses; `reflex.py:215` records success
before `r` is inspected at all. *Citation correction: the real lines are 540-550, not last cycle's
`:540-547`/`:543-549`.*

**Census, denominator and naming convention settled FIRST** (this was the method risk):
`monitor/dispatch-logs/` holds **551 entries**, 548 parsing as `<id>-<UTCstamp>.log[.err]`, **74
distinct ids**; contents never opened. Both spawn paths write the log file *before* any subprocess
(`dispatch.py:260-262` in `launch()`, `:392-394` in `via_task()`), so a session dying one second in
still leaves a file bearing its id — the precondition for treating absence as evidence. And **all
six ids are their own positive controls**, each having produced `<id>-<stamp>.log` files at other
times, with `W-1660`/`W-1661` files *inside* the same 10:00–12:00Z window. Files for any of the six
in-window: **0** of 11.

Two independent structural refusals, each upstream of the file write:
* `prompt_id()` (`dispatch.py:64-67`) returns `None` for all five `W-*` ids → empty plan →
  `:374 print("nothing matched.")`, `launch()` never reached.
* `S3-spend-gate` *is* matchable, but its only prompt lives two directories deep in
  `monitor/prompts/archive/superseded-by-board/`, while `dispatch.py:336` is a **non-recursive**
  `os.listdir(PROMPTS)` whose entire output is 6 names. Same terminus.
  (So last cycle's `prompt_id` finding does not over-determine the census into meaninglessness — it
  *explains* it. `W-*` files exist elsewhere because `--worker` passes the id on the command line
  and never regex-matches it; `--only` is regex-gated. Same output naming, different gate.)

**The defect is LIVE, not historical — it fired twice more after last cycle's report:**

```
reflex.log:276  2026-07-30T01:55:14Z … relaunched ['OPS-M','W-1671','OPS-A']; still queued: ['RES-4','RES-3']
reflex.log:277  2026-07-30T02:23:47Z … relaunched ['RES-4','RES-3']; still queued: []
```

In-window census (20260730T015000Z–030000Z, 11 files): `OPS-M` 0, `W-1671` 0, `OPS-A` 0. `RES-3`/
`RES-4` have files, but at 02:15:03Z and 02:15:56Z — **8 minutes before** the 02:23:47Z print — so
they are `standing.py` role restarts, not this resume's output (first subprocess ≈02:22:17Z, from
live `quota_state.json last_ping_at = 02:22:16Z`). Live state now reads `requeue = []`,
`resumed_at = 02:23:47Z`: **the queue has been fully drained by receipts that launched nothing.**

**Restorable form of the original conclusion** (numbers re-measured, and *stronger* than when
retracted): reflex's worker-replenishment loop body has executed **0** times successfully and
**358** times unsuccessfully across the whole log, and has not been **entered at all** since
`2026-07-29T09:55:33Z` (`reflex.log:249`) — **15.3 hours** as of `reflex.log:274`, not the 11 in the
original. Every worker event since is `worker-hold:low-memory` (`:254, 266-274`, readings 5.4–7.8
GB, all below `MIN_FREE_GB = 8`), i.e. the memory gate refusing *upstream* of the loop.
`worker-spawn:` is a reachable trace, not a dead branch (`dispatch.py:453-456` prints `started` only
when the task is confirmed running after `LAUNCH_SETTLE_S`), so 0/358 is a real measurement.

**The retraction's effect was the opposite of what it credited it with:** `quota.py:546` set
`mode="recovering"` because `rest` was non-empty; `check()` returns 2 for any non-`normal` mode
(`:407, 429-431`); `reflex.py:225 hold = q.returncode != 0` goes true and the whole replenishment
block is skipped. Observed at `reflex.log:253` (11:07:46Z): `quota:RESUMED(auto) | quota:HOLD`, the
very next tick. The 10:59:50Z resume launched zero workers *and* re-held reflex's own resupply path
— not a counterexample to the original claim but another instance of it.

The *other* retraction in the same amendment block (withdrawing the "two mutually unreconciled
spawners" causal claim, `:146-162`, `:185-186`) rests on different evidence and **stands**.

**Contaminated consumers — denominator: 9 files matched, 3 contaminated, 1 discharged by attrition,
5 clean.**
1. `223f78a8:monitor/audit/DRIFT-20260729T2100Z-…:169-174` — the retraction itself, uncorrected on
   mainline and in the worktree.
2. **NEW, not named last cycle: `223f78a8:monitor/mailbox/OPS-A.md:574`** — mainline, identical at
   794e5b46 and in the worktree, asserting the six-worker relaunch as fact *inside a list titled
   "4 個對抗者殺掉或重寫了我 4 條結論"*. The false receipt is filed in my own lineage's handoff
   channel **as a lesson learned**, which makes it likelier to be inherited than the report itself.
3. `794e5b46:monitor/audit/state.json:40` PREDICTION 3 — **discharged by attrition, not
   correction**: cycle 45 rewrote the entry, so the `REFUTED`-on-a-false-basis text survives only in
   git history. No action beyond not resurrecting it.

Cleared (matched the search, not contaminated): `monitor/mailbox/OPS-A.md:866`/`:925` (already say
the receipt is false), `monitor/bus/OPS-M/out.jsonl:12` (cites `resumed_at` as a *stale field*, a
sibling symptom — `resumed_at` is written on the same unconditional line as the false print),
`monitor/tests/test_quota_autoexit.py:4` and `monitor/board/done/S1-quota-auto-exit.W-1250.md:8`
(both describe the original freeze, not the relaunch), `monitor/inbox/20260728T204718Z-W-1620-…:193`
(unrelated).

Worth quoting in the report: the commissioning ticket's acceptance criterion was literally *"resume
后把 requeue 里的工人按优先级重发，并在 reflex.log 记明是自动恢复"* — **it asked for a log line and
did not ask for verification, and it got exactly that.**

Boundary the agent could not cross (same one the original report drew): *why* the 358 `--worker`
attempts never printed `started` needs dispatch-log contents, which the isolation contract forbids.
