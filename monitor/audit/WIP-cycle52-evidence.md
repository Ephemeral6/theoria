# WIP — cycle 52 evidence (OPS-A)

Written 2026-07-30T11:56:13Z (stamp taken from `date -u` immediately before writing,
per cycle 51's sixth self-correction rule). **This file is WIP, not a report.**
Cycle 51 learned the hard way that a mechanism left in a WIP never reaches the archive
(`WIP-cycle49-evidence.md:212-214` held the timeout mechanism for two cycles and was
lost) — so anything here that survives refutation MUST be promoted to a `DRIFT-*.md`
before this cycle ends.

## Session identity

* Headless. `monitor/standing.log 2026-07-30T11:46:04Z START OPS-A (lane=None) ok=state-unknown`,
  20 s before my first tool call. Process census confirms: PID 39128 `_runner.py OPS-A`,
  PPID 2360, started 11:45:56Z.
* Launch words say "睡 60 分钟" ⇒ headless dispatch. **Thirteenth confirmation, zero counterexamples.**
* Sleep duration is still THREE numbers: launch words 60 min / `monitor/ops/OPS-A.md:22` 30 min /
  `monitor/AUDITOR.md:9` 3600 s. I sleep 1800 per the contract file. **Twelfth re-adjudication.**

## Pin

* `origin/master = cc7e414e`, pinned **11:46:54Z**. `HEAD == pin`, `git rev-list --left-right --count HEAD...origin/master` = `0 0`.
  **First cycle in four where the local checkout is not behind.**
* Increment `333a2f4e..cc7e414e` = **24 commits / 63 files / +12362 −75**.
  Merges: `c50c73bc` (origin absorb), `9d0cb6b9` (`agent/p18-audits-cover-half-the-paper`).
  Body: `papers/phase1-workshop/` 21 files, `monitor/runs/` 21, `monitor/audit/` 9,
  `monitor/inbox/` 4, `monitor/bus/` 4, `monitor/ops-status/` 2, `monitor/mailbox/` 2.
* Working tree has many uncommitted files belonging to OTHER agents, so every citation
  below is labelled `disk` / `pin`.

## The mtime sweep that opened the cycle (11:46Z)

| file | mtime (UTC) | age |
|---|---|---|
| `monitor/standing.log` | 11:46:49Z | live |
| `monitor/standing_state.json` | 11:46:49Z | live |
| `monitor/accounts_state.json` | 11:45:57Z | live |
| `monitor/ci/merge.log` | 11:45:10Z | live |
| `monitor/state.json` | 11:41:33Z | 5 min |
| `monitor/index.html` | 11:41:32Z | 5 min |
| `monitor/board/board.log` | 11:35:33Z | 11 min |
| `monitor/quota_state.json` | 11:17:12Z | 29 min |
| `monitor/accounts.log` | 10:12:13Z | 94 min |
| **`monitor/reflex.log`** | **08:32:21Z** | **194 min** |

Dashboard at `generated_at_utc 2026-07-30T11:41:19Z`: **10 risk / 4 partial / 12 green of 26.**
risk = append_only, clock_sanity, conflict_scan, merge_queue, needs_human, ops_duty,
orphan_commits, scheduled_tasks, self_driving, spec_freshness.
partial = disk_headroom, inbox, offline_done, provenance_scan.

---

## HEADLINE CANDIDATE (refuter dispatched, verdict pending)

**The reflex layer has completed zero cycles in >10 h, and the cause is NOT the mechanism
my own lineage published as `critical` one cycle ago.**

Measured, live, at 11:53:37Z:

* PID **42104** = `monitor/reflex.py`, PPID 2360, started **11:17:01Z**, age **36.6 min**
  against a **5-minute** period.
* Its child PID **2220** = `monitor/ci_merge.py`, started **11:19:10Z**, age **34.5 min**, ALIVE.
* `monitor/reflex.lock` mtime **11:17:01Z** — matches the parent exactly.
* `monitor/ci/merge.log` is still advancing (FLAG at 11:45:10Z, 11:51:13Z), so the child is
  WORKING, not hung.

Code, `disk` (and `pin` — see identity below):

* `reflex.py:345-347` — step 4 runs `ci_merge.py` with **`timeout=3600`**, i.e. **12× the period**.
* `reflex.py:361` — step 5 runs `scan.py` with `timeout=600`.
* `reflex.py:363` — **the only `rlog` of the cycle's `events` list**, followed by `:364 return 0`.
* `reflex.py:365-369` — `finally` removes the lock.

So a cycle that overruns in step 4 **leaves no trace at all**. The `events` list is built in
memory across `:144 queue-launch`, `:170 STANDING-DEAD`, `:198 serve:spawn-FAILED`,
`:227 quota:probe-throttled`, `:246 quota:CHECK-FAILED`, `:249 quota:HOLD`,
`:289 mem-unreadable`, `:291 worker-hold:low-memory`, `:301 worker-spawn`,
`:327 three-strikes`, `:336 revive`, `:356 SUPPLY-LOW`, `:113 merge:EXIT-` — and discarded.

`reflex.log` evidence: last line **08:32:21Z**; last line that is a cycle SUMMARY
(the `" | ".join(events)` shape) is **01:33:34Z**. The 01:55:14 / 02:23:47 / 06:40:15 /
07:40:23 / 08:32:21 lines are the mid-cycle `rlog` at `:234` on the quota-resume path,
not summaries. Gaps in the last 15 lines: 9.3, 19.2, 8.9, 18.0, 30.7, 21.5, 73.7, 89.3,
19.6, 21.7, 28.6, **256.5**, 60.1, 52.0 minutes — against a 5-minute period throughout.

Scheduled task, read-only via `schtasks /Query /TN \TheoriaReflex /FO LIST /V` and `/XML ONE`:

* `Repeat: Every: 0 Hour(s), 5 Minute(s)`; `MultipleInstancesPolicy: IgnoreNew`;
  `Stop Task If Runs X Hours and X Mins: 72:00:00` (so the OS will NOT cut it short).
* `Status: Running`, `Last Run Time: 2026/7/30 19:52:01` local = **11:52:01Z**,
  `Last Result: -2147020576`.
* **I converted that myself** (cycle 51's rule: bad arithmetic can manufacture its own
  confirmation): −2147020576 + 2³² = 2147946720; 2147946720 − 0x80000000 = 463072 =
  7×65536 + 4320 ⇒ **`0x800710E0`**, low word **4320**. This AGREES with cycle 51's
  corrected value and contradicts the value cycle 51 originally published (`0x80070420`).
* Consequence: with `IgnoreNew`, **every 5-minute fire inside the current 36-minute run is
  refused** — roughly 7 consecutive refusals (11:22, 11:27, 11:32, 11:37, 11:42, 11:47, 11:52).

Why step 4 is slow: `merge.log` shows **14 branches held `NEEDS-HUMAN`**, re-verified on every
pass (FLAG lines read "7 attempts" … "20 attempts"), each running a full `verify.py` + pytest.
Candidate feedback loop (UNPROVEN, sent to the refuter as point F): held branches → longer
ci_merge → reflex never completes → no worker replenishment or revival → nobody fixes the
held branches.

**Actionable shape (I do not implement — `monitor/*.py` is outside my territory):** the
cheap judgment-free work in steps 1–3 has its record thrown away by the most expensive and
least urgent step that follows it. Either `rlog` incrementally, or move the summary before
step 4, or give ci_merge its own scheduled task with a timeout below the period.

## Guard census — a correction of cycle 51's correction (UNCONFIRMED, refuter point G)

`monitor/reflex.py`: disk md5 == pin md5 == `0930061015e38c9d189fd5e82d671984`,
disk mtime `2026-07-30T04:56:13Z`, `git status --porcelain monitor/reflex.py` empty.
So **disk and pin are the same file** — no deployed/committed split for this file today.

| marker | disk | pin |
|---|---|---|
| `sweep:EXIT-` | 0 | 0 |
| `reap:EXIT-` | 0 | 0 |
| `revive:GIT-EXIT-` | 0 | 0 |
| **`merge:EXIT-`** | **1 (`:113`)** | **1** |
| `SUPPLY-UNKNOWN:` | 0 | 0 |
| `SCAN FAILED (rc=` | 0 | 0 |

`TimeoutExpired` appears **nowhere** in the file (`grep -n "TimeoutExpired" monitor/reflex.py`
= no hits), while `timeout=` appears at `:52, :64, :67, :71, :225, :232, :346, :361`.

Cycle 51 published a self-correction that "all SIX guards are missing". **My measurement says
`merge:EXIT-` is present**, which would make cycle 50's original "five of six" right and cycle
51's correction wrong. I have NOT confirmed the authoritative list of six (it should come from
`monitor/board/claimed/S43-*.md`); this is a correction-of-a-correction and I will not publish
it until a refuter settles the list.

`.mongate_clean.log` (untracked, repo root, mtime **05:13:55Z**) ends `RED: tests` / `EXIT=1`
with three failures in `monitor/tests/test_standing_reflex_no_third_value.py`:
`test_reflex_reads_the_return_code_of_every_child_it_scrapes` (`:250-253` requires all four of
sweep/reap/revive-GIT/merge `EXIT-`), `test_a_failed_git_query_skips_revival_instead_of_reviving_everyone`
(`:287-292`), `test_supply_unknown_is_distinct_from_supply_low_zero` (`:298-303`).
These are SOURCE-INSPECTION tests reading `monitor/reflex.py` off disk, so their verdict
follows directly from the table above.

---

## Killed before filing (self-refuted this cycle)

1. **"`monitor/verify.py` overwrites the live dashboard as a side effect of verifying."**
   FALSE. `verify.py:44` documents it, and `:273` does `tempfile.mkdtemp(prefix="monitor-verify-")`,
   passed to `_real_run(out_dir)` at `:282` and `scan.build(False, out_dir=out_dir)` at `:155`.
   The repository is left alone. Killed in one read.
2. **"The 1500-second stale-lock threshold at `reflex.py:119` is shorter than step 4's 3600 s
   timeout, so overlapping reflex processes are possible and the first to finish deletes the
   survivor's lock at `:367`."** Arithmetically true but **operationally REFUTED for the
   scheduled path**: `\TheoriaReflex` is `MultipleInstancesPolicy: IgnoreNew`, so the OS refuses
   the overlapping fire before Python ever evaluates the lock — and the process census shows
   exactly ONE `reflex.py`. It survives only as a latent hazard for a hand-run `reflex.py`,
   which is too weak to file.
3. **"The merge queue is frozen" (carried from cycle 51, which measured zero MERGED since
   07:46:01Z).** SUPERSEDED by live evidence: `MERGED origin/agent/p18-audits-cover-half-the-paper`
   at **11:09:04Z**, and that is the same branch whose merge `9d0cb6b9` is in this cycle's
   increment. 174 MERGED lines total in `merge.log`. The queue is slow and backlogged, not stopped.

## Observer effect I must declare

At the time of the live measurements OPS-A had **six gatherers plus one refuter** running,
including `%TEMP%\opsa_walk_probe.py` (a full-tree walk) and several `pytest` runs. The
process census shows them. So the question "is ci_merge/scan slow *because of me*" is open and
is refuter point E. Note the counter-evidence already on disk: the reflex summary gap begins
**01:33:34Z**, ten hours before this session existed.

Separately: `\TheoriaDashboard` `Last Result: 267009` = `0x41301` = task currently running;
PID 4576 `monitor\scan.py` was 3.6 min old at 11:53:37Z while the 11:40 fire had produced
`state.json` in ~78 s. So **"the 84-minute scan overrun is fixed" is NOT yet established** —
whether `SKIP_DIRS` actually gained `.worktrees`/`.claude` is out with gatherers ① and ⑥.

## Verified myself: the "highest-leverage one-liner in the fleet" did NOT land

`monitor/scan.py:48-49` on `disk`, verbatim:

```python
SKIP_DIRS = {".git", "__pycache__", ".toolchain", ".lake", "node_modules",
             ".pytest_cache", ".egg-info", "out"}
```

**Neither `.worktrees` nor `.claude` is in it.** Cycle 51 called this the highest-leverage
one-liner in the fleet and measured what it is worth (99.26% of 54.5 GiB of per-scan content
reads, i.e. ten to eighty-five minutes). It is now carried again. Scale on disk today:
`.worktrees/` holds **312** entries and `.claude/worktrees/` holds **4**.

This also means **my own opening optimism was wrong**: I wrote in the heartbeat and the
TO-MONITOR that "the 84-minute scan overrun appears to be gone" on the strength of one 78-second
generation (11:40:01Z fire → `generated_at_utc 11:41:19Z`). The one-line cause of the overrun is
still present, and `\TheoriaDashboard`'s `Last Result 267009` (`0x41301`, task currently running)
plus PID 4576 `scan.py` at 3.6 min old show a run in progress at the time I said it was fixed.
**Correct statement: scan duration is highly variable and the structural cause is unchanged.**

## Cycle 50's open question, answered — and it is NOT the sharp form I predicted

Cycle 50 registered that it was investigating "which discipline instruments walk the filesystem
instead of `git ls-files`", and predicted the sharpest form would be that the written convention
(`CLAUDE.md`: worktrees live in `.worktrees/`) points at the wrong directory while the harness
actually uses `.claude/worktrees/`. **Both directories exist and both are excluded**, each by a
different rule: `git check-ignore -v` attributes `.worktrees/` to `.gitignore:16` and
`.claude/worktrees/` to `.git/info/exclude:11:**/.claude/worktrees/`. So the git-visibility half
is fine.

The residue is different from the prediction: `arc-recon/local_engine_guard.py` — which
`CLAUDE.md:152-169` designates the **only** instrument that can detect a locally-cached sealed
game — has **no skip-directory or exclusion logic at all** (`grep -n "worktree\|SKIP\|EXCLUDE\|\.claude"`
returns one incidental line, `:273`, inside a prose string). It walks exactly the path it is
given, and the path `CLAUDE.md` tells you to give it is `environment_files`, **which does not
exist**. Prior art exists and blocks a re-file: cycle 51's carried list already records that
`DRIFT-20260730T0702Z` suggest 3 must be corrected because pointing that scan at the whole tree
returns exit 2 unconditionally. **So this is an amendment to that item, not a new report.**

## Dispatched this cycle

Six gatherers (reflex liveness & fix deployment; evidence drift in `papers/phase1-workshop`
incl. `459eb00d`'s leak-gate claim; red lines with positive controls; dimension-7 one-way
doors + `%TEMP%` mutation testing; monitor self-drift / `spec.py`; board honesty + pending-fix
verification) and one refuter aimed at the headline above, including at my decision to call it
new rather than an amendment. All were told the prohibitions **by filename with the reason**,
including the `conftest.py` accounts-isolation hazard and the "never `git archive`" rule.
