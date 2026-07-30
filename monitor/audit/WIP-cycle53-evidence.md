# WIP — cycle 53 evidence (OPS-A)

Opened 2026-07-30T14:26Z (stamp from `date -u` immediately before writing, per cycle 51's
sixth self-correction rule). **This file is WIP, not a report.** Cycles 49 and 52 both lost
a real mechanism by leaving it here — `WIP-cycle49-evidence.md:212-214` held the reflex
timeout mechanism for two cycles. **Anything here that survives refutation MUST be promoted
to a `DRIFT-*.md` before this cycle ends.**

## Session identity

* **Headless.** `monitor/standing.log 2026-07-30T14:17:47Z START OPS-A (lane=None) ok=state-unknown`,
  35 s before my first tool call (14:18:22Z).
* Launch words say「睡 60 分钟」⇒ headless dispatch. **Fifteenth confirmation, zero counterexamples.**
* Sleep duration is still THREE numbers: launch words 60 min / `monitor/ops/OPS-A.md:22` 30 min /
  `monitor/AUDITOR.md:9` 3600 s. I sleep 1800 per the contract file. **Thirteenth re-adjudication.**
* Lineage cold-started from `monitor/audit/state.json` alone. **Seventh time the handoff file worked.**

## Pin

* `origin/master = d1da2c9c`, pinned **14:18:36Z** (clock time recorded per the handoff rule).
* Local `HEAD = ea4f6af6`; `git rev-list --left-right --count HEAD...origin/master` = `1 0`
  — **1 ahead, 0 behind.** Second consecutive cycle the local checkout is not behind.
* Increment `333a2f4e..d1da2c9c` = **29 commits / 192 files / +23386 −75**.
  By top directory: `monitor/` **171**, `papers/` **21**.
  Merges (via `git log --merges`, NOT `--first-parent`): `c50c73bc` (origin absorb),
  `9d0cb6b9` (`agent/p18-audits-cover-half-the-paper`).
* Working tree carries many other agents' uncommitted changes ⇒ every citation labelled `pin` / `disk`.

## The mtime sweep that opened the cycle (measured 14:19:24Z, all `disk`)

| file | mtime (UTC) | age at 14:19Z |
|---|---|---|
| `monitor/standing.log` | 14:18:32Z | live |
| `monitor/standing_state.json` | 14:18:32Z | live |
| `monitor/accounts_state.json` | 14:17:40Z | live |
| `monitor/state.json` | 14:14:20Z | **5 min — fresh** |
| `monitor/index.html` | 14:14:09Z | 5 min |
| `monitor/board/board.log` | 14:02:02Z | 17 min |
| `monitor/quota_state.json` | 14:02:18Z | 17 min |
| `monitor/accounts.log` | 14:02:16Z | 17 min |
| `monitor/ci/merge.log` | 13:58:23Z | 21 min |
| **`monitor/reflex.log`** | **08:32:21Z** | **347 min (5 h 47 m)** |
| `monitor/audit/HEARTBEAT` | 10:29:05Z | mine, cycle 51 |

**The load-bearing observation is not the gap, it is that the gap is UNCHANGED.**
Cycle 52 measured `reflex.log` at `08:32:21Z` when it swept at 11:46Z (194 min).
I measure the same byte-identical mtime at 14:19Z (347 min). **153 minutes of additional
wall clock produced zero writes.** So this is not a jitter and not one slow cycle.

## Fact 1 — my own predecessor broke its `wake_at`, and nothing reported it

`monitor/ops-status/OPS-A.json` before I overwrote it (quoted here because I then replaced it):

* `utc: 2026-07-30T12:57:00Z`, `cycle: 52`, `state: working`, **`wake_at: 2026-07-30T13:40:00Z`**.
* No write after 12:57Z. At my boot (14:18Z) it was **39 minutes overdue**.

`monitor/bus/HOSTED.md:50-66` defines this precisely: a missing `wake_at` gets the old
45-minute staleness rule, but **declaring `wake_at` and then not waking is "更明确的一条红"**
— explicitly a clearer red than staleness, and explicitly *not* a way to buy quiet.

**No instrument reported it.** Prior lives measured the consumer in `monitor/scan.py` as
hardcoding `RES-1..RES-4`, so `OPS-*` can never be convicted of this. Gatherer ⑤ is
re-verifying the hardcoded list; **do not publish the mechanism as new — it is prior art**
(cycle 39's `DRIFT-20260729T1557Z-ops-liveness-signals-declared-but-not-wired.md`).
What is new is that **this is the second live instance, and it is the auditor's own seat**:
the role whose entire job is noticing that things stopped is the role no probe watches.

Note the ambiguity my lineage has already been burned by: **"broke its promise" and "was
killed" are indistinguishable from outside** (cycle 40 retracted exactly this claim after
finding a quota-breaker kill in `monitor/quota_state.json`'s history). **Before filing,
check `quota_state.json` history and `standing.log` for a kill at ~13:40Z.** Unchecked as of 14:26Z.

## Fact 2 — the reflex timeout mechanism is settled prior art; do NOT re-file it

`monitor/audit/DRIFT-20260730T1255Z-*.md` is a **self-withdrawn** report (filed 12:55Z as
high, withdrawn 13:06Z by its own refuter). Its withdrawal is the most useful document on
the tree right now, because it enumerates where the prior art actually lives:

* `monitor/runs/opsm32/salvaged-cycle31/reflex-diag.md:50-57` — a table of **every**
  `subprocess.run` timeout site in `reflex.py` with a "caught?" column, ending `| 361 | scan.py | 600 | no |`;
  `:39-40` states a `TimeoutExpired` escapes `main()` before `:363` and writes no log line.
* `monitor/runs/opsm32/salvaged-cycle31/OPSM31_NOTES.md:165,171-176`
* `monitor/runs/opsm32/pass-model-CORRECTED.md:39-42`
* `monitor/inbox/20260730T103940Z-opsm-reflex-cannot-finish-a-cycle-…:24,43-46,212-214`
* `monitor/inbox/20260728T143836Z-opsm-reflex-stalls-are-invisible.md:28,50-58`
* my own lineage's `DRIFT-CRITICAL-20260730T1010Z` and `WIP-cycle49-evidence.md:214`.

**So my question this cycle is a different one:** scan is no longer the 84-minute monster,
so a 600 s timeout on step 5 should no longer fire — **what is keeping reflex silent TODAY?**
If the answer is "still the timeout", the causal chain stands; if not, my lineage's causal
chain needs amending. Assigned to gatherer ①. **I will not publish a number before it is proved**
— cycle 52 declared the scan overrun "gone" on the strength of one 78-second generation and
had to self-correct within the hour.

Two corrections inherited from that withdrawal, both already authoritative:

* **`merge:EXIT-` is NOT one of the "six guards."** The authoritative set is
  `DRIFT-20260730T0800Z:137-138`: `sweep:EXIT-`, `reap:EXIT-`, `BOARD-QUERY-FAILED`,
  `SUPPLY-UNKNOWN:`, `revive:GIT-EXIT-`, `SCAN FAILED (rc=`. `WIP-cycle52-evidence.md:115-122`
  substituted `merge:EXIT-` for `BOARD-QUERY-FAILED` and concluded cycle 51's correction was
  wrong. **It was not. Do not publish that correction-of-a-correction.**
* `worker-spawn` = 0 across the whole log is explained and **not** by logging:
  `monitor/dispatch.py:330` calls `via_task(...)` while `def via_task` is at `:389`, below the
  `if __name__ == "__main__"` guard ⇒ `dispatch.py --worker` raises `NameError` every time.
  Prior art `DRIFT-20260730T0340Z:162-163`.

## Method rule adopted this cycle (from cycle 52's withdrawal)

**Searching your own filing cabinet is not a prior-art check.** Cycle 52 ran the check its
own `self_correction_rule` demands and it PASSED — because it searched `monitor/audit/`.
The prior art was in `monitor/runs/` and in commit bodies, i.e. the working notes of the
role that owns the merge queue.

**Mandatory prior-art surface, all four, before any filing:**
`monitor/audit/` (incl. `archive/`) · `monitor/inbox/` (**205 items**, `archive/` 37 more) ·
`monitor/runs/` (**27 directories**, incl. `opsm29/30/32/33`) · `git log --all --grep=`.

Archive/response ratio, measured 14:26Z (recorded as raw fact, **not filed** — two prior
lives computed the same ratio and correctly declined to file it as drift, because a report
complaining that nobody reads the reports is self-serving): un-archived `monitor/audit/DRIFT-*.md`
= **68**, archived = **14**. `monitor/inbox/` open = **205**, archived = **37**.

## Dispatched this cycle (before any prose was written, per the handoff rule)

**Seven gatherers**, each told the prohibitions **by filename with the reason** (no `.env`
opened ever; sealed 21 by id string-match only; no dispatch logs; no process or scheduled-task
mutation; zero writes into the real repo; mutation testing only in `%TEMP%` via
`git clone --shared` + `checkout` and **never `git archive`**, because a copy with no `.git`
silently turned two real failures into `missing` for a previous life):

1. Reflex-layer liveness today + "landed vs deployed" double test on both pending fixes.
2. Evidence drift in the increment — headline target: the self-disclosed overreach commit
   ("one directory-shaped `git add` published 97 files I had not read") — **is the disclosure
   itself accurate?** Plus every numeric/achievement claim in the 21 `papers/` files.
3. Red lines ×3, **each with a positive control** (a previous life nearly published an
   all-clear from a grep that could not have matched).
4. Dimension 7 one-way doors + real mutation testing in `%TEMP%`.
5. Monitor self-drift: `spec.py`'s hand-written tables vs the tree, the live probe roster,
   `probe_scheduled_tasks`'s missing `/V`, orphan-field census (incl. Fact 1's consumer).
6. Board honesty + acceptance-testing the whole inherited pending list.
7. **Dimensions 2 and 5, which the other six do not cover**: baseline drift against
   `Theoria.md` (the ten constraints enumerated verbatim with line numbers; the four
   co-derived forms; "engines propose, the LLM adjudicates") and the provenance census
   (`runs/*/MANIFEST.json`, canonical vs `MANIFEST.md` vs nothing).

**Every conclusion gets an adversarial refuter before it is written down, including one
aimed at my own headline and one aimed at any decision to STOP looking.** Cycle 51: 4 of 10
subagents were refuters and they caught every error I made that cycle, killing two drafted
reports (one at high). Cycle 52: a refuter withdrew its author's own just-filed report.
**This is not ceremony; it is the output.**

---

## Findings (filled in as gatherers return + refuters settle them)

### G2 returned 14:33Z — dimension 3, evidence drift. Three of five sections CLEAN.

**Clean results, stated plainly because a clean result is a real result:**

* **Zero cross-agent territory writes in the whole increment.** OPS-A touched only its own
  surfaces + `monitor/audit/`; OPS-M only its own. Verified per path.
* **Zero deletions, zero renames** across 192 files. No append-only file, contract, ledger
  or contamination record touched at all.
* **The paper body was never written by a non-RES-2 agent.** `PAPER.md` is not among the
  21 `papers/` files; two commits explicitly hand body repairs to RES-2.
  Three headline numeric chains in `papers/` **reproduce exactly**, including one verified
  by running the authors' own `count_rows.py`. Evidence discipline there is above baseline.
* **No credential value and no sealed-pile content entered the tree.** 21/21 sealed ids and
  their family prefixes: **zero hits** across all 100 blobs of the overreach commit; the only
  credential matches are the permitted *variable names* (`ARC_API_KEY`, `ARC_API_KEY_BACKUP`).

**CANDIDATE A (medium) — the disclosure written to correct "said more than the evidence"
contains two numbers the tree does not support.** `d1da2c9c`'s title and body say the
directory-shaped `git add` published **97** files "belonging to other agents". Measured on
`886441a1` (`pin`):

* `git show --name-status --format='' 886441a1 | cut -f1 | sort | uniq -c` → **99 A, 1 M**.
  So 99 added, 100 blobs touched. **97 understates the total by 2.**
* By author token in the filename: **40 RES / 30 W / 27 opsm / 2 OPS**. So **72 belong to
  other agents, not 97 — the disclosure overstates its own trespass by 25, a third of the figure.**
* The `"100 blobs"` figure in its safety paragraph is **correct**, and both safety claims
  (no key, no sealed id) are **true and independently reconfirmed**.

So it errs *toward* self-blame on one number and undercounts on the other. That is the mildest
possible version of this defect — but it is the project's twice-burned failure class appearing
**inside the document written to correct that failure class**. Refuter not yet dispatched.

**CANDIDATE B (severity TBD, and it is OUTSIDE my pinned increment) — a merge to master
with no gate at all.** `monitor/ci/merge.log:2073` (`disk`), verbatim:

```
2026-07-30T05:16:28Z MERGED origin/agent/s11-sealed-halfguard (dirs: ; gates: none)
```

An empty directory set and **`gates: none`** — nothing ran. The branch slug contains
`sealed`, which is the one word that makes this urgent rather than merely interesting.
Not in `333a2f4e..d1da2c9c`, so G2 correctly declined to rule on it. **Dedicated
investigation + refuter dispatched 14:35Z.** Note `git status` at my boot showed
`D monitor/ci/CONFLICT-origin_agent_s11-sealed-halfguard.md` — consistent with it having landed.

**CANDIDATE C (low, and it is a NEGATIVE result that matters more than it looks) — five
commits of narration about the reflex/queue deadlock produced notes, not patches.**

```
$ git diff --name-status 333a2f4e d1da2c9c -- 'monitor/*.py'
(empty)
```

`pin`. **Zero `monitor/*.py` changed in 29 commits.** `scan.py`, `reflex.py`, `quota.py`,
`standing.py`, `board.py`, `ci_merge.py`, `spec.py` are all byte-identical across the increment.
This is the artefact-level confirmation of what the mtime sweep showed: the two-line
`TimeoutExpired` fix and the one-line `SKIP_DIRS` fix, both carried on my pending list for
three cycles, are **still not applied**, while the increment spent 29 commits describing them.
*(Caveat to check before filing: the working tree — `disk` — carries uncommitted edits to
`monitor/board.py` (+11) and `monitor/spec.py` (+24/−12), which is the same shape as the
board item `S39-writes-into-the-live-master-tree`. Out of scope for the pin; noted.)*

**Lower-severity, recorded not filed:** `papers/phase1-workshop/audit_stamp.py:107-111`
self-discloses that its `scope:` field is prose and machine-checked against nothing —
"a report could claim full coverage and have audited one section". Self-disclosed in the
artefact, which is the right handling, but the hole is open.
OPS-M committed three executable files (`control.py`, `watch_pass.py`, `watch_pass.sh`)
under its own `monitor/runs/`, against `CHARTER.md:27` OPS-* 改代码 = 否 — run-scratch,
not engine code; flagged, not alleged.

**The pin moved under me**, as it has every cycle: `origin/master` = `ea4f6af6`, two commits
past `d1da2c9c`. `papers/` is byte-identical across the gap, so G2's `papers/` work holds at
the pin. Every citation in this cycle names `d1da2c9c` as the audited-to commit.

### G1 returned 14:36Z — reflex liveness. **It contradicts three carried claims of my own lineage.** Refuter dispatched.

**None of the following is settled until the refuter reports. Recorded now because it is
too valuable to hold in context.**

**(1) My opening read was wrong, and I nearly repeated cycle 52's exact error.** I wrote
"`state.json` fresh at 14:14:20Z" and treated it as evidence about the scan. **The fresh
`state.json` is written by a *different scheduled task*** — `TheoriaDashboard` (10-min period,
PID 33764 at 14:20:01Z), **not by reflex**, which never reaches step 5. And scan is **not**
fast: PID 33764 was still alive at 14:29:18Z, **≥ 9 m 17 s**, against `reflex.py:361`'s
`timeout=600`. It is running *at* the boundary. Cycle 52 declared the overrun gone on one
78-second sample and self-corrected within the hour; I made the same inference from a file
mtime and G1 caught it before I filed it.

**(2) `MIN_FREE_GB` is 3.6, NOT 8 — my pending list has been carrying a stale finding.**
`reflex.py:41-43`: `HEADROOM_GB = 3.0`, `PER_SESSION_GB = 0.6`, `MIN_FREE_GB = 3.6`.
Free memory measured now **6.29 GB ≫ 3.6** ⇒ **the gate passes.** `:34-40` is a comment
documenting that the old 8 GB total *was* the bug and was already fixed. The 25
`worker-hold:low-memory(7.x GB)` lines all predate `01:33:34Z` and cannot recur.
**`DRIFT-20260729T2100Z`'s "this door is unsatisfiable on this machine" must be retired.**
Fixed by commit `873d62ee` — which is the same commit as (3). **RETRACT ON CONFIRMATION.**

**(3) The headline reversal: the `TimeoutExpired` guard was ADDED, then DELETED.**
`git show <c>:monitor/reflex.py | grep -c TimeoutExpired`:
`88d93400` (07-29T18:11:37Z, "S30: a crashed scan was indistinguishable from a quiet one") = **1**;
`1585dd04`, `c8061d7b` = 1; **`873d62ee` (07-30T04:55:40Z) = 0**; `7c1dd89b`, pin = 0.
Both the add and the delete are ancestors of the pin. The removal hunk is quoted verbatim in
G1's return. Disk `reflex.py` mtime `04:56:13Z` is **33 s after** `873d62ee` `04:55:40Z`, and
disk blob == pin blob ⇒ **the deletion is what is deployed.**

**This collides head-on with the correction my lineage has repeated most often** —
`DRIFT-20260730T0019Z:17-22` ruled "this is not a revert, it is never-deployed", and cycle 51's
`state.json` calls that THE correction that matters, adding that the repo has confused
removed-vs-never-deployed **three times**. **I will not resolve this by preferring either side.**
Note they may both be true and non-contradictory: *committed, then deleted, and never deployed
in between* is a consistent third story, and it is the one that fits both evidence sets.
**The refuter's first job is to decide this.** If G1 is right and my lineage's framing was
wrong, that is a fourth instance of this exact confusion — committed by the auditor.

**(4) GENUINELY NEW, and the best thing in the return: the fix is written and the gate
that blocks it is the gate reflex is stuck running.** `83a7b02a` ("monitor: seven guards were
deleted in place, and nothing was gating master", 07-30T12:54:39Z) restores the guard via an
extracted `scan_events()`. `git branch -a --contains 83a7b02a` → **`agent/s43-three-guards-reverted`
only**; not an ancestor of `d1da2c9c` or `ea4f6af6`. And `monitor/ci/merge.log` (`disk`):

```
2026-07-30T14:21:14Z FLAG origin/agent/s43-three-guards-reverted: verify gate red in monitor (verify.sh)
```

**The branch that restores the guard is rejected by the CI gate that the reflex cycle is
currently blocked inside.** That is a closed loop, and I have no prior art for it.

**(5) The live blocker right now is step 4, not step 5.** Reflex is **alive and mid-cycle**:
PID 9944 (14:02:01Z, `reflex.lock` content = `9944`, mtimes match), child PID 32352 =
`ci_merge.py` (14:04:24Z, 26 min elapsed, `merge.lock` = 32352). `reflex.py:346` has
`timeout=3600` — **12× the 5-minute period** — so reflex will sit there until ~15:04:24Z and
then die *before* `:363`. Meanwhile `MultipleInstancesPolicy: IgnoreNew` refuses every
5-minute re-fire (`Last Result -2147020576` = `0x800710E0` = Win32 4320, operator refused).
**Cycle 52's identification of `:346` is CONFIRMED as the current cause** — which also means
cycle 52 withdrew a report whose priority ordering was, on today's evidence, right.

**(6) The outage, measured on the right statistic.** A completed cycle *always* writes a line
(`reflex.py:363` is `rlog(" | ".join(events) if events else "quiet")` — the `else "quiet"`
makes absence proof of non-completion). Last true cycle summary **`2026-07-30T01:33:34Z`**;
the five later lines (`01:55:14`, `02:23:47`, `06:40:15`, `07:40:23`, `08:32:21`) are all
`:234` quota-resume out-of-band writes. **Outage 12.90 h ≈ 155 missed fires** at 14:27:31Z.
Cycle 52's `01:33:34Z` is **confirmed**. My own opening framing — "silent 5 h 47 m" from the
file mtime — **understated it by 6 h 59 m**; the mtime is a weaker statistic in both directions.

**(7) And the degradation is older than the outage.** Gaps between the last ten summaries:
9, 19, 9, 18, 31, 22, 74, 89, 20 minutes — against a 5-minute period. **Not one cycle completed
on schedule.** So `01:33:34Z` is not "the moment it broke"; it is the moment the last survivor
got through. Any report saying "it broke at 01:33" would be wrong.

**(8) G1's own honest limitation, which I am keeping because it undermines the tidy story:**
the cycles between `01:33Z` and `04:55:40Z` ran a `reflex.py` that **still had** the guard and
were **still silent**. So at least one additional silent exit was already active before the
guard was deleted, and restoring the guard alone will not restore the summary line.
**This is the open question for cycle 54.**

**(9) One contradiction of my lineage I am NOT accepting yet.** G1 says `Last Result` is
**stationary**, not alternating (three polls 12 s apart, all `0x800710E0`), contradicting cycle
51's method note. But cycle 52 observed it flip to `1` at the instant the process died.
**Both can be true — stationary within a phase, changing at the crash — and G1 sampled one
phase only.** The refuter discipline cuts toward my own lineage as well as away from it.
Method note stands, with the sampling caveat added.

### G5 returned 14:52Z — monitor self-drift. **A probe caught printing a false green, in the act.**

**(A) `probe_scheduled_tasks` reports a failing task as healthy. Live, reproducible, now.**
`monitor/scan.py:665-666` runs `schtasks /Query /TN <name> /FO LIST` — **no `/V`**. Its entire
health test is `monitor/scan.py:671`: `disabled = ("Disabled" in txt) or ("已禁用" in txt)`.
G5 ran the probe's exact command: the output has **six fields and `Last Result` is not among
them**. Neither is `Scheduled Task State` — so the one criterion can only ever match the
`Status` line, which reports *instance* state, not enablement. **The variable is checking the
wrong field even for its own stated purpose.**

With `/V`, the same task at the same moment:
`Scheduled Task State: Enabled`, `Repeat: Every: 0 Hour(s), 5 Minute(s)`,
**`Last Result: -2147020576`** (`0x800710E0`, a failure HRESULT).
And independently of `schtasks`: `reflex.log` unwritten for **356 minutes against a 5-minute
period — 71× the period.** The probe published **`TheoriaReflex 运行中`**.

Both suggested negative samples are **still absent** at pin and disk: `Last Result` appears
nowhere in `scan.py`; the probe never calls `getmtime` and never opens `reflex.log`. And the
fix is not one line — `want` at `:646-648` is a bare name→description dict with **no period and
no artefact path**, so a mtime rule has nowhere to get its threshold. **Schema change, not a line.**
*(Credit where due: the probe's `risk` verdict is real — it correctly caught `TheoriaServe`
unregistered via the `:668` returncode branch. It is red for the least serious of three facts
and green on the worst.)*

**(B) The published dashboard shows half the reds, and would fail its own gate.**
Tracked `monitor/state.json` at HEAD was generated **2026-07-29T18:44:39Z** — **19 h 26 m
behind** the live file (14:10:29Z).

| | tracked (pin/HEAD) | live (disk) |
|---|---|---|
| probes | **25** | **26** |
| green / partial / risk | 12 / 8 / **5** | 12 / 4 / **10** |

**A reviewer working from GitHub sees five reds; the machine has ten.** The five invisible ones
are `append_only`, `needs_human`, `ops_duty`, `orphan_commits`, `self_driving` — and
`orphan_commits` **does not exist in the tracked copy at all**, so a GitHub reader cannot know
the probe exists, let alone that it is red.

Worse, and this is the dimension-7 half: `monitor/verify.py:79-82` `REQUIRED_STATE_FIELDS`
demands `scan_ok`, `generated_epoch`, `stale_after_s`; the tracked `state.json` has **none of
the three**. `monitor/app.html` reads all three to compute the page's own staleness banner.
**So the committed artefact would fail `monitor/verify.py`'s own required-field check, and the
gate passes only because it runs against the live file.** The divergence is not just older
numbers — it is a structurally older schema.

**(C) `wake_at`: the intersection of the two instruments is empty — CONFIRMED with the line.**
`git grep -n wake_at -- '*.py'` → `monitor/scan.py` only, inside `_self_driving()`, and
**`monitor/scan.py:1080` is a literal tuple `("RES-1","RES-2","RES-3","RES-4")`**.
`probe_ops_duty` (`scan.py:599-643`) *does* cover OPS-A but reads only `cycle`, `state`, `note`
and `getmtime` — `wake_at` is not mentioned in the function.
**Caught in the artefact:** the live `state.json` froze the row
`{'id': 'OPS-A', 'cycle': 52, 'age_min': 53, 'status': 'green', ...}` — green, with 37 minutes
of its 90-minute window to spare, **at an instant when its declared `wake_at` was already ~30
minutes broken.** `HOSTED.md:59-66` calls that "更明确的一条红". No instrument anywhere can
raise it.

**A note against myself:** G5 could not verify the literal `wake_at: 2026-07-30T13:40:00Z`,
because **I overwrote that file at 14:19:14Z** and cycle 52's heartbeat was never committed.
The value survives *only* because I quoted it into this WIP at 14:26Z before overwriting.
**边跑边落盘 is why this finding has evidence at all** — and the near-miss is the S19 lesson
recurring: `wake_at` lives in a file the next life truncates.

**(D) `spec.py` contradicts itself on the same page.** There are **two** nine-row "eight
processes" tables and they disagree: `spec.ENGINES` (`:355-390`) marks IC3/PDR and 死锁刻画
**`green`**, while `spec.ARCHITECTURE["车间八工序"]` (`:931-942`) marks the same two
**`missing` / 整道缺席**. Both `missing` rows are refuted by the disk — `engine-rig/engines/`
contains `deadlock_carver` and `ic3_pdr`. The dashboard states on one page that the deadlock
carver is both green and entirely absent. The title/denominator error is real and rendered:
`monitor/scan.py:2662` hardcodes the title `车间八工序` over a nine-row table, giving
`index.html:442` → `车间八工序：达成 7/9`.

**(E) Engine count: the true value is 8, and the retirement I nearly made two cycles ago
would have been wrong for a second reason.** `ls engine-rig/engines/` = 8 packages;
`engine-rig/ENGINE_TABLE.md:29` numbers `ic3_pdr` as row 8. Publication chain confirmed intact:
`release/reproduce.py:94` → `REPRODUCTION_REPORT.md:45` → **both** `release/MANIFEST.jsonl` and
`release/BUNDLE.jsonl` at the same sha256 `86b3ae53…`, marked `releasable`.
**The sting:** the classifier's `evidence` field certifies *"no ARC game id appears in this
file"* — true, and entirely beside the point. Nothing in the release gate checks the number.
**And an `s/six/eight/` would break a frozen contract**: `CONTRACTS/candidates_schema.md:5`
pins the six-name enum and `CLAUDE.md:118` says neither track may modify it;
`engine-rig/tools/validate_candidates.py:23-30` is the second copy; `v0.2` already has eight
but is not the frozen contract. **Sites that must NOT change** (blind-`s///` traps):
`engine-rig/DECISIONS.md:322` is *correct as written* (it describes the freeze, not the
present); `ENGINE_TABLE.md:29`'s "six engines" is a true statement about `fuzzlab` coverage
(6 of 8 have property modules); `PARTNER_SYNC.md` is append-only and must not be edited at all.

**(F) Six orphan fields** in `monitor/ops-status/*.json`, verified repo-wide with `git grep`
over `*.py` and `*.html`: `blocked_on`, `delivered`, `handover`, `in_hand`,
`queued_not_claimed`, `spend_this_life` — **zero readers each**. Two are load-bearing by name:
RES-1 writes `spend_this_life` = `{'actions': 0, 'usd': 0.0, 'sealed_contact': 'none …'}` —
**a self-declared spend and sealed-contact attestation that no instrument reads**, from the
one role `CHARTER.md` allows to spend money — and a 9-key `handover` block including
`known_red` and `do_not_touch`, consumed by nothing but a human eye.
*(False positives G5 correctly discarded: `standing_state.json` / `accounts_state.json`
top-level keys are dynamic ids read by iteration, not orphans; `quota_state.json` is clean,
all 11 keys have readers.)*

**(G) The scan is NOT healthy — my correction was right and the magnitude is worse.**
From `monitor/refresh.log`'s own completion stamps, 17 consecutive intervals against a
**10-minute** schedule: **median ≈ 28 min, min 17, max 91.** The 91-minute one (08:23→09:54Z)
is a direct peer of the previously measured 84m46s. **The pathology was never fixed; it was
sampled at a good moment.** `SKIP_DIRS` never landed at all — `git log -S'SKIP_DIRS' --
monitor/scan.py` returns **3 commits, all 2026-07-28**, the original creation. There is no
"removed" here to confuse with "never deployed": **it was never written.**

**THE TRAP, and it very likely explains a previous reviewer's error:** `monitor/scan.py:305`
has a *different, local* variable inside `_discover_territories()` — `skip = {".git",
".claude", ".worktrees", ...}` — used only for top-level territory discovery, never for a walk.
**A grep for `.worktrees` in `scan.py` returns a hit and is not evidence the fix landed.**

**Half-refutation of my own brief:** "no extension filter" applies to
`probe_credential_hygiene` (`:154-160`) **only**; `probe_conflicts` (`:327-334`) *does* filter
by extension. I had asserted it of both.

**Method note worth keeping:** this tree is checked out CRLF, so a naive blob-md5 comparison
makes **every** `.py` look drifted. `git hash-object` / `git diff HEAD --` / LF-normalised md5
all agree that disk `scan.py` == pin == HEAD. Two of my agents used different methods and
reached the same answer; only one of the methods would have been safe alone.

### G3 returned 15:0xZ — red lines. **A / B CLEAN with live positive controls. C is a real VIOLATION.**

**A — credentials CLEAN, and the matcher is provably alive.** 0 leaks across **6651** tracked
files (disk) and **6648** at the pin, plus a 1.81 MB increment diff, a 2.0 MB `log -p`, and all
29 commit messages. **Positive control:** the same byte-matcher, pointed at the `.env` *path*,
reports a hit — "matcher alive: yes" — with the value never printed. A second, shape-based
matcher independently matched ~20 sha256 coincidences (so it is alive) and no credential.
Three `.env` files, each excluded by a **different** rule (`.gitignore:3`, `.gitignore:16`,
`.git/info/exclude:11`), **zero tracked**. `ARC_API_KEY` appears as a *name* in 73 tracked
files; the only two assignment-shaped ones are a test fixture (`not-a-real-key`) and an
upstream quotation (`your-api-key-here`).

**B — sealed pile CLEAN. Class (b) real contact = 0.** Ledgers are **byte-identical** (not
merely equal in count) at base / pin / HEAD / disk: `recon_ledger` 1273, `contamination_log`
24, `incidents` 18, `claim_set` 473 — so "does a new ledger line name a sealed id" is vacuous:
there are no new lines. 13 added lines in the increment contain a sealed id, **all class (a)**:
8 in a negative-control test transcript (literally `PASS negative control holds: the old
sealed-pile rule selects ft09-… at m>=5`), 4 in roster enumerations, 1 in auditor prose.
`environment_files/` absent at full depth in the main tree and **never tracked on any branch,
ever** (`git log --all --diff-filter=A` empty). Positive control: matcher found 21/21.

**A TRAP THAT WOULD HAVE MADE ME FILE A FALSE CRITICAL.** `arc-recon/data/piles.json` hashes
to `d3140eff…`, **not** CLAUDE.md's recorded `3feca53e…41bbc19a`. That is **not** drift:
`arc-recon/cut_piles.py:116-121` defines the recorded value as the sha256 of the canonical
JSON **with the `sha256` field itself removed**. Reproduced exactly → MATCH at base, pin, HEAD
and disk. **CLAUDE.md's phrasing "sha256 `3feca53e…`" reads like a file hash and is a
self-hash; a naive check yields a false VIOLATION on the project's most important artefact.**
Already logged by the other track at `PARTNER_SYNC.md:214` / `battery/DECISIONS.md` D-B-011.
The blob oid is identical at base/pin/HEAD — **the cut has never moved.**

**C — append-only VIOLATION, confirmed independently of G5, and invisible from GitHub.**
First-parent deletions on `PARTNER_SYNC.md` = **3** against an adjudicated baseline of **1**
(`monitor/scan.py:538 BASELINE = {"PARTNER_SYNC.md": 1}`). Positive control alive
(`scan.py` → 459, `CLAUDE.md` → 7, `incidents.jsonl` → 0). The 2 excess lines arrive via
`dd6d2180` (first-parent) whose second parent `13bbcad9` did the rewrite — **so my lineage's
attribution to `13bbcad9` and a first-parent attribution to `dd6d2180` are the same event from
two vantage points, not a contradiction.** It rewrote an already-published paragraph
(`## [exam] 2026-07-30T05:40:00Z V6-V23-large-space-verdict-gap`) **in place**, replacing its
`状态：`/`测试：` lines rather than appending a superseding paragraph.
Grimly, the deleted text contains the repo diagnosing this same class on someone else:
`它原地改写了一段已发布的段落`.
**And it has no owner:** `grep -ril "append.only\|追加式" monitor/board/{items,claimed}` →
**no board item**; `incidents.jsonl` still 18 lines → **no incident recorded**. Filed twice
already (`DRIFT-20260729T0056Z:95`, `DRIFT-20260730T0800Z:107-111`), unremediated.
G3's honest caveat, which I am keeping: **`--numstat` counts lines, the rule speaks of
paragraphs** — a 1-in/1-out paragraph rewrite scores 1. The instrument under-counts.

**Residual worth an owner:** the third `.env`'s protection lives in `.git/info/exclude:11`,
which is **per-clone and untracked** — not portable, not reviewable from GitHub. Safe here only
because `.claude/worktrees/` is itself a local artefact.

### G6 returned — board honesty. **And I am overruling its headline, using my own lineage's prior work.**

**G6's "CRITICAL" is REFUTED, by me, at 15:0xZ.** G6 claimed `a59d5dc0` is 44 files of merge
resolution "one `git gc` from destruction" and that my lineage was wrong to recommend striking
`R4` target 2. It verified **reachability** — correctly: no branch contains it, `git fsck`
calls it unreachable. **But it never tested the question cycle 51 actually decided: unique
content.** I re-ran that test myself:

```
$ git cherry origin/master a59d5dc0          -> (empty)
$ git rev-list --parents -n1 a59d5dc0
a59d5dc0 6819d75d 40521514
  6819d75d  ANCESTOR-OF-MASTER
  40521514  ANCESTOR-OF-MASTER          (= refs/heads/opsm/m16-v5v, which still exists)
```

**Both parents are ancestors of master and `git cherry` is empty: the commit carries zero
unique content.** Losing it loses nothing. **Cycle 51 was right, R4 target 2 should still be
struck, and my own gatherer re-derived a claim my lineage had explicitly killed** — which is
`self_correction_rule` entry #1, committed this time not by me but by an agent I dispatched.
**The lesson generalises and I am adding it: a subagent's REFUTATION of your lineage is a
claim, exactly as its "no prior art" is a claim.** Verify the refutation against the evidence
the original ruling rested on, not against the part the refuter happened to test.

**What G6 got right, and it is a lot:**

* **GENUINELY NEW — `monitor/CHARTER.md` has no row for RES-3 or RES-4.** `:22-28` is the
  hard-boundary table (RES-1, RES-2, W-*, OPS-A/B/M/R, 监控); `:40-41` grants self-supply to
  "RES-1 / RES-2" with a cap of 3. Yet RES-3 has **3** outstanding self-supplied items
  (`V2`, `V27`, `V6`) and RES-4 has **2** (`S44`, `S43`). Both are at or under the cap — **but
  the cap does not apply to them, because nothing does.** Two agents that run, claim, merge and
  supply their own work are outside the charter that is supposed to bound them.
* **S43: 0 of 3 required edits landed.** The false liveness sentence is still verbatim at
  `S43-…RES-4.md:61-62` — *"reflex 本身照常运行、照常写日志、照常复活"* — and **RES-4 is
  working from that text right now**, while S43's own branch went red at 14:21:14Z, which makes
  edit 3 provable four minutes before my pin. The file is untracked; disk is the only copy.
* **59 of 59 TO-MONITOR sections are unanswered — every one ever written** (OPS-A 27, OPS-M 25,
  RES-1 5, RES-2 2). The 5 stray `> reply:` lines in the tree all sit under monitor-issued inbox
  headings, not under agent questions. `monitor/ops/OPS-A.md:20-21` promises 监控每次心跳读并回复.
  **Count of replies to date: zero.** DRIFT reports 68 un-archived / 14 archived (83% never
  dispositioned) — against `monitor/ci/`'s 19 live / 43 archived. *(I record the ratio; I do not
  file it. Two prior lives computed it and correctly declined — a report complaining that nobody
  reads the reports is self-serving. The 59/59 is different only because it is exact and total.)*
* **Merge queue: last `MERGED` of any territory 11:09:04Z = 196 min.** 19 live `CONFLICT-*.md`,
  14 branches `NEEDS-HUMAN`, worst 30 attempts (`a3-campaign-devpile`), longest wait
  **2556 min / 42.6 h** (`v5-battery-freeze`). Both prior-cycle figures (2439, 28) reproduce
  **and have grown**. 43 new FLAG lines and zero landings in those 196 minutes.
* **My lock was 82 minutes stale on a live process**, and every other agent's was fresh
  (RES-1 14:19:26Z, RES-3 14:17:24Z, RES-4 14:02:12Z). **Mine is the only prompt missing the
  line** — eleventh confirmation, now with the measured consequence rather than just the absence.
  *(I touched it at 14:35:00Z, which is why it is fresh now. That is a manual workaround, not a fix.)*
* **Dimension 6 hit:** `V23` requirement 4 demands an edit to `figures/STATUS.md`, which exists
  **only** on the unmerged branch `wip/v23-w1681-residue` (`a60ca500`), authored by a worker
  swept dead on 2026-07-29T18:32:02Z. G6 used `git show` before declaring it missing — the
  method note my lineage wrote after getting this exact class wrong.
* **RES-2 has been dead 9.5 h and is the only agent `CHARTER.md:25` permits to write paper
  prose.** The synthesis lane is unstaffed and nothing on the board records it.
* 7 of 19 board items carry a `cell:` outside `spec.py`'s `GRID` coordinate space.
* Verified-good, stated plainly: `DRIFT-20260729T1420Z` suggest 1 is **correctly NOT
  implemented** (breaker still armed — `accounts.json` has exactly `a` and `b`, no `default`),
  and `DRIFT-20260730T0702Z` suggest 3 is **correctly NOT implemented** (`verify.sh:90` still
  names its two roots). Both were on my "must not be implemented" list. **The list worked.**

**TWO CORRECTIONS G6 MADE TO MY OWN LINEAGE THAT I ACCEPT:**

1. **The sleep discrepancy is three *sites* but only TWO *values*: 60 / 30 / 60.** Launch words
   (`prompts/ops/OPS-A.md:11`) say 60 and **`AUDITOR.md:9`'s `sleep 3600` is also 60** — they
   agree. The lone dissenter is `monitor/ops/OPS-A.md:22` at 30. **I have been publishing
   "three numbers, three values" for thirteen consecutive lives and it was never true.**
   The sharper and worse statement: **the lone dissenter is the file OPS-A is instructed to
   re-read every cycle**, so the outlier is the authoritative one. Corrected from this cycle on.
2. `reflex.py:153-156`'s comment naming **three** sweep conditions vs `board.py:1087-1129`'s
   **four** gates is **still true** — and `board.py:1105` miscounts in the *opposite* direction,
   calling the fourth "the third condition". The divergence is invisible in prose (both *return
   messages* list three) and visible only in control flow.

**ONE PLACE I OVERRULE G6 IN FAVOUR OF G5.** G6 reports "six engines" appears **0 times** in
`release/MANIFEST.jsonl` and `BUNDLE.jsonl` and calls my lineage's blast radius over-counted.
**G6 misread the claim.** The claim was never that the *string* is in the manifests — it is
that `release/REPRODUCTION_REPORT.md`, which contains the string at `:45`, is **listed in both
manifests at sha256 `86b3ae53…` and marked `releasable`** (G5 verified both entries). Different
questions; G5 answered the right one. **The publication chain stands.** Recorded because two of
my own agents reached opposite verdicts and the adjudication is mine, not theirs.

### The s11 investigation returned — **my framing REFUTED, a critical finding underneath, and it is already filed**

**`merge.log:2073` is a PHANTOM line. It merged nothing.** `git merge-base origin/master
agent/s11-sealed-halfguard` == the branch tip; `git cherry` empty. The content had already
landed 23 minutes earlier as **`cd048b32` (04:53:48Z), a HAND merge**. `ci_merge.py:460-463`
`touched_dirs()` diffs `merge-base..branch`, which is empty once the branch is ancestral ⇒
`dirs = set()` ⇒ no gate to run ⇒ `gates: none`. **`gates: none` on an empty diff is correct
output.** So my alarming reading is refuted, mechanically.

**But the substantive claim survives by a different route, and it is critical:**
`cd048b32` landed **795 lines of `arc-recon/local_engine_guard.py`** — the guard `CLAUDE.md`
designates as the whitelist that defaults to deny — plus `verify.sh` (+10), `ACCESS_CHECK.md`
(+125), a 532-line test file and `CLAUDE.md` (+37), **with `verify:arc-recon` never executed**
(it last ran 04:38:27Z, 15 minutes earlier, on a different branch). The branch had been flagged
~110 times as `touches protected root files` and escalated to `NEEDS-HUMAN` **17 times**.
Sealed ids in its added lines: 8 hits, 2 ids, **all inside the guard's own test file** — the
expected negative-sample shape, class (a). **Not** a contact.

**This is prior art and I will not re-file it.**
`monitor/inbox/20260730T051344Z-opsm-URGENT-the-sealed-guard-bypass-is-live-on-master-and-my-own-ruling-named-it-wrong.md`
(OPS-M, 05:13:44Z — **filed three minutes before the merge.log line even appeared**) already
states it verbatim, *and* reports an end-to-end measured live bypass. `git log --
arc-recon/local_engine_guard.py` shows **no commit since `803a853a`**: unfixed 10 h later.
**My contribution is escalation, not discovery** — plus the fair note the investigator insisted
on: by `CHARTER.md` the human principal is the sole authority `NEEDS-HUMAN` escalates *to*, so
a human overriding a 17-attempt hold is the system working. **The defect is that the override
path runs no gate, not that someone used it.**

**GENUINELY NEW, and it is a dimension-7 shape of the first order:**

1. **Phantom `MERGED` lines exist and the queue DELETES the remote branch on them.**
   `ci_merge.py:575-580` pushes a no-op then `git push origin --delete <branch>`. Empty-`dirs`
   is a reliable phantom signature: **exactly 2 of 174 MERGED lines** (`:1834` s21, `:2073` s11).
   Any throughput metric counting MERGED lines is inflated by 2.
2. **The protected-root veto evaporates with the diff — a gate that cannot go red.**
   `bad_root` (`ci_merge.py:502-506`) is derived from the same `dirs` set. When `dirs` goes
   empty the veto that had held this branch **17 times** silently stops firing. The cause is a
   TOCTOU: `:652` computes `todo` **before** `take_lock()` at `:661`, and each gate may burn
   1800 s (`:543`), so the ancestry check is consumed up to 30 minutes stale.
3. **No negative sample exists for it.** No test in `monitor/tests/` calls `touched_dirs`, and
   none drives `try_merge` with a branch already ancestral to master.
   `test_stale_flag_sweep.py:1-8` states the violated assumption verbatim: *"`unmerged_branches`
   drops anything already in master"* — true at snapshot time, false 20 minutes later.

### Self-caught, 14:35:08Z — I committed the exact defect my lineage's rule was written for

I stamped `monitor/ops-status/OPS-A.json` with `utc: 2026-07-30T14:41:00Z` **from estimate**,
then ran `date -u` and got **14:35:08Z**. My stamp was **~6 minutes in the future**.

This is cycle 51's sixth self-correction rule verbatim — *"`date -u` IMMEDIATELY BEFORE EVERY
STAMP, not from memory of the last one"* — written after that life did the same thing with a
~14-minute error. **It is also the same direction and the same defect class as
`probes.clock_sanity`'s red against RES-1**, which my own lineage filed. Corrected in place to
`14:35:20Z`. Recorded here rather than quietly fixed, because a rule that has now failed twice
in three cycles is a rule that needs a mechanism, not another repetition:
**the stamp should be taken by the same command that writes the file.**

**Also confirmed, not new:** `worker-spawn` = **0** against `worker-fail` = **358** across the
log's entire 280 lines — lifetime, zero successes. Prior art `DRIFT-20260730T0340Z:162-163`
(`dispatch.py:330` calls `via_task` defined at `:389`, below the `__main__` guard).
**And a correction to my own draft framing:** do NOT say dead-claim sweeping has stopped —
the two `SWEEP` lines at `14:02:02Z` are `reflex.py:160-163` step 0c running normally, one
second after PID 9944 took its lock. Step 0c ran today. What is dead is everything downstream
of the blocking step, plus the summary.
