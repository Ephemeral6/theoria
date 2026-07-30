# WIP — cycle 47 evidence, part 2 (gatherers 4/5 and the deploy-gap refutation)

Continues `WIP-cycle47-evidence.md`. Same pinning: code counts at `223f78a8`, which was
origin/master at 03:16Z. **origin/master has since moved twice (→ `8f4f9ee7` → `50e10617`, HEAD
45 behind by 03:35Z).** The tree moves under the audit; that is why every count names its rev.

---

## G8 — MY DEPLOY-GAP CLAIM IS WITHDRAWN. The refuter killed it.

Filing nothing. Recording the kill because the shape of my error matters more than the claim.

| quantity | I claimed | corrected |
|---|---|---|
| `223f78a8` = origin/master | yes | **no** — already 3 behind by the time I cited it |
| HEAD behind origin/master | 40 | **43** then; 45 by 03:35Z |
| reflex.py hand-edit | 59+/114− | **24+/5− vs `0c099ae8`**, the true minimal base |
| "exactly ONE hand-edited file" | 1 | 1, **and it is also 2 commits stale** — it is in BOTH categories, so the 1-vs-9 split does not exist |
| "nine OTHER files" | 9 | **10 listed, one of them is reflex.py itself**; and 3 are new-file creations, a third repair class my split had no slot for |
| landed-not-running | 1032 insertions | **1474** (worktree→origin/master); my per-file figures sum to 1090 = ins+del, so I cited one number and named the other |
| operative surface | 1032 lines of supervisor code | **344** (board.py 286 + reflex.py 46 + standing.py 12); 575 is tests, 171 is one-off run scripts nothing executes |
| S35 billing consequence | real, 2 items stuck 14.9h/12.9h | **KILLED** |

**The billing consequence died to five independent refusals**, and the first one is decisive:
`monitor/board/items/S22-access-check-close.md:5` says `lane: campaign` while `board.py:50` maps
`infra→RES-4` — so `work_for("RES-4","infra")` **never sees S22 at all**, and for the real
campaign owner RES-1 `offers()` withholds only when `worker in released_by` (`{RES-4}`), which
RES-1 is not. **The docstring's own headline example cannot produce the effect it is cited for.**
Then: `any` is a disjunction so the overcount can only launch when `unread=0 AND held=0` (3 of 46
RES starts, 6.5%); all 14 `START RES-4` lines carry `held≥1` or `unread≥1`; 204 of 384 RES skip
lines had `claimable>0` and were refused anyway; and the claim-side guard already exists in the
worktree at `board.py:529`. Measured outcome: the 3 bug-attributable launches all claimed real
work in 34–80 s. **Zero wasted sessions in 46 launches across a 23-hour window.**
Also `BOARD-EMPTY` is only `print`ed (`board.py:568`) and never noted, so `grep -c BOARD-EMPTY
board.log` = 0 of 361 is *not* evidence of absence — `board.py:546` says so itself.

**THE PART THAT STINGS AND MUST GO IN THE METHOD NOTES.**
`monitor/audit/DRIFT-20260730T0019Z…§3` already contains the exact candidate-base table
(`1585dd04: 59+/114-` ← *labelled as the wrong baseline*, `88d93400: 25+/30-`, `0c099ae8: 24+/5-`
← minimal), and §5 already records the meta-rule I was invoking. **I re-asserted as new a number
my own lineage had already published as its identified error — the third occurrence of the
wrong-baseline mistake in that file's own history.** The self-correction checklist did not catch
it because I never asked whether the *number* had prior art, only whether the *subject* did.
New rule: **run prior-art on the FIGURE, not just the topic.**

**Genuinely new, kept as a one-liner for the monitor (not a report):** the S35 `standing.py` hunk
is **not independently deployable** — `offers()` does not exist in the worktree `board.py`
(`grep -c "def offers"` = 0; it is defined inside the 286-line board.py hunk at
`223f78a8:board.py:341`). Deploying standing.py alone raises `AttributeError` → caught at
`standing.py:328` → `CLAIMABLE_UNKNOWN` → `BOARD-QUERY-FAILED` skip, i.e. **fails safe but never
launches: a fleet-wide launch stall for RES-1..4.** So my "two causes, two different repairs"
thesis is wrong in the one place it would have mattered — the files are coupled.

---

## G4 — mtime as a liveness signal (refuter C in flight)

Confirmed on every clause, **and it is a carried debt rather than a duplicate**:
`monitor/audit/DRIFT-20260730T0014Z…:133-138` states it and closes *"这条与本报告不同因，建议单独下发"*
— recommend issuing separately. **It never was.** Also carried at `monitor/mailbox/OPS-A.md:870`
and `:920`. Filing it now pays a debt; it does not re-file.

**Corrections to my own brief:** the worktree is 40+ commits **behind** `223f78a8`, not forked from
it. `monitor/scan.py` is **byte-identical** at both revs (so every scan.py line below is valid in
both); `board.py`, `reflex.py`, `standing.py` differ, the tree being the older file. board.py's
claim sits at `:53-55` in the tree and `:62-64` at `223f78a8`.

**(a) board.py's "single source of truth" block is false in two independent ways.**
`board.py:62-64` asserts it is the sole origin of the threshold and that *"scan.py 的 self_driving
探针 import 这两个名字"*. Complete importer set of `STALE_MIN|heartbeat_evidence` in tracked `*.py`
at `223f78a8`: board.py's own self-references, `monitor/runs/…/probe_unreachable.py:93`,
`tests/test_board_no_third_value.py`, `tests/test_standing_sweep.py`, `fleetkit/fleetkit/board.py`.
**`monitor/scan.py`: zero.** Both clauses false.
*Precision the prior art got wrong:* scan.py does NOT ignore board.py — `scan.py:1311` calls
`board_mod.heartbeat_age(aid)` in `_fleet_rows`. The dependency is real; board.py named the wrong
consumer.
**NEW — the block contradicts the function 10 lines below it.** `:62-64` orders you to read mtime
and *not* the self-reported `utc`. The S28 docstring of `heartbeat_evidence` at `:74-87` says the
opposite: the json is git-tracked, `merge`/`reset`/`autostash` can "touch a dead session alive", so
the code prefers the untracked `.lock` and labels the mtime path `"mtime-touchable"`. The STALE_MIN
comment is **pre-S28 doctrine S28 never updated** — wrong about who imports it, and giving advice
its own module has since repudiated.

**(b) `_self_driving` (scan.py:1073-1116).** Imports `time as _t` only — neither name. `:1100`
`stalled = age > 45`, hardcoded. `:1091` `getmtime` on `monitor/ops-status/<rid>.json` for
RES-1..4, and all eight such files are git-tracked (`ls-files --error-unmatch` succeeds).
**The clean signal is sitting beside it, ignored:** `.lock` files exist for exactly OPS-A and
RES-1..4 — every id `_self_driving` examines — and `.gitignore:24` ignores them, so
`heartbeat_evidence` would return source `"lock"` for all of them.

**(c) THE MECHANISM, measured with a negative control** (synthetic repo in `%TEMP%`, file aged to
1666 min before each trial):

| operation | mtime age after | content after |
|---|---|---|
| `git checkout other` (file differs) | **0 min** | new |
| `git merge other` (file differs) | **0 min** | new |
| *control:* git ops not touching the file | 1666 min (unchanged) | — |
| `git reset --hard <base>` | **0 min** | **old (utc=01:00Z)** |

The control is what makes this evidence: git refreshes the mtime only when it rewrites the file.
The `reset --hard` row is the defect exactly — **content from an earlier moment, mtime of now.**

**The live signature, and it is nine seconds tight.** OPS-R.json: mtime `2026-07-29T10:19:52Z`,
self-reported `utc 2026-07-29T05:59:00Z` — **261 minutes newer than its own content claims**. The
reflog has `eae853b8 HEAD@{2026-07-29T18:19:43+08:00}: reset: moving to origin/master`, local TZ
+0800 ⇒ **10:19:43Z, nine seconds before that mtime.** The reset consumed 261 minutes of evidence:
`probe_needs_human` budgets OPS-R 900 min, and the reset moved its apparent age 1281 → 1020. Two
more such resets and a 21-hour-dead session reads green to the block that asks the human to restart it.

Full 8-row table (gap = mtime_age − utc_age; **negative = the dangerous direction**): OPS-A +0,
OPS-M +0, RES-3 +0, RES-4 +0, RES-1 +3, RES-2 **+17** (utc stamped ~1 min in the FUTURE),
**OPS-R −261**, OPS-B unparseable.
**Honest denominators:** 112 of 1004 commits in 7 days touch `monitor/ops-status/`, but **0 of 163
merges in the last 24h** did — the firing path is `reset` (~6 in the reflog), not `merge`. So **no
RES id carries the signature right now**: this is a latent defect with a documented firing history
on the exact ids the probe reads, not a false green presently on screen. Both error directions are
live simultaneously (OPS-R's mtime-newer, RES-2's utc-in-the-future).
**Also NEW:** OPS-B's `utc` is `"2026-07-29T12:16Z"` — no seconds, so it does not parse under the
`%Y-%m-%dT%H:%M:%SZ` format used throughout `monitor/`.

**(d) Consequence — split, and the split is the finding.**
`_self_driving` is **recorded-and-rendered-but-unescalatable**: 4 live consumers (`PROBES` dict
`scan.py:1401`, `state["probes"]` → state.json `:2667`, `app.html:305-309`'s coloured pill inside
the *collapsed* `实况探针` fold — 1 row of 25 — and one stdout line `:3109`), and **zero paths to a
red gate**: `spec.py` has 5 `"probe":` bindings (`:81,:110,:120,:135,:162`) and self_driving is not
among them, so it can never reach `_reconcile`, `verdict_overrides`, `p1_green` or the headline;
`index.html` has zero occurrences; `verify.py:79-82 REQUIRED_STATE_FIELDS` excludes `"probes"`.
It CAN go red — `tests/test_session_liveness.py` has three `== "risk"` assertions plus a green
companion — **but the suite sets mtime by `os.utime` fiat and never compares mtime against the
`utc` field, so it is structurally blind to this defect.**
**The high-consequence sibling is `probe_needs_human` (`scan.py:1188`)**, same `getmtime` on the
same tracked json, and `app.html:285` reads `s.probes?.needs_human` into the **top-level
"需要你出手" action block**, whose rows carry `prompt: monitor/prompts/ops/<ID>.md` — it tells the
human which session to reopen and which boot prompt to paste. Third reader: `probe_ops_duty`
(`:612`). **Three readers, one contaminated input, and the one that escalates to a human is not
the one board.py named.**

**(e) All six sleep/staleness numbers still hold, and none agree.** `ops/OPS-A.md:22` = 30 min
cadence; `prompts/ops/OPS-A.md:11` = 60; `AUDITOR.md:9` = 3600 s = 60; `scan.py:592 OPS_DUTY` = 90
(OPS-A only; B 180, M 150, R 900); `scan.py:1178 needs_human` = 120 (OPS-A only; B 240, M 180,
R 900, RES-1..4 90); `standing.py:90 LOCK_FRESH_MIN` = 20. Plus `board.py STALE_MIN = 45`,
`STANDING_CYCLE_MIN = 45`, `STANDING_DEAD_MIN = 90` (`:977-978`), `standing.py:94
BOARD_ACTIVE_MIN = 90`. **For OPS-A alone: five numbers — cadence 30 vs 60, stale at 45 or 90 or
120. If OPS-A obeys the 60-minute cadence it is stale by board's criterion for 15 minutes of every
healthy cycle.** For RES-1..4, 45 sits safely above their 15-min cadence, so no persistent false red.
**Seventh cycle flagged.**

**Two more NEW items from this line of work:**
1. **`fleetkit/fleetkit/board.py:52-55` ships board.py's false sentence VERBATIM** — including
   "scan.py 的 self_driving 探针 import 这两个名字" — inside a package that **has no scan.py at all**
   (`__init__.py`, `board.py`, `bus.py`, `config.py`). And fleetkit's `heartbeat_age` (`:61-66`) is
   the **pre-S28 mtime-only version, no lock branch, no `heartbeat_evidence`**. The extracted
   reusable library ships the exact vulnerability the monitor fixed, under a comment claiming to be
   its single source of truth.
2. **A fabricated receipt inside the probe's own output.** `scan.py:1115` appends
   `"→ 已发 urgent 催醒；若仍不动，说明会话已死，需重开"` — *an urgent wake-up has been sent*. **scan.py
   never imports `bus`**, and no consumer of `self_driving` sends anything. The probe asserts an
   action nobody performs, rendered verbatim into `state.json` and the app fold. **Same class as
   `quota.py:549`'s false `relaunched [...]` print (see G6) — two independent instances of
   "record the success without checking, or without even attempting".**

---

## G5 — the two quota gaps: BOTH ALREADY FILED; the new material is elsewhere

**My carried note was false.** `monitor/audit/state.json:63` said "two narrow quota gaps **not yet
filed**". They were filed 8h earlier by this same bloodline:
`monitor/audit/DRIFT-20260729T1830Z-one-pool-three-readers-three-verdicts.md` (severity **high**,
cycle 41) is one combined finding whose table names **exactly these two lines** as readers 2 and 3
— `reflex.py:204` (global flag) and `_runner.py:111` (`pick()`→None ⇒ machine default) — against
`standing.py:165` (pool), citing 7a71b5ab as the half-fix. **Do not re-file.**

**GAP 1 severity DROPS high → low, and the reason is a second refusal.** `reflex.py:204`'s defect is
real (identical in both copies; worktree `:204` = `:225` at 223f78a8) and the divergence is directly
recorded — `standing.log` starts 8 sessions from 17:18:08Z while `reflex.log` logs `quota:HOLD` at
18:29:55/18:45:26/19:01:46/19:17:41Z; second window `START RES-4` 01:30:11Z vs `quota:HOLD`
01:33:34Z. **5 of 24 pool-era ticks (21%) suppressed refill+revive while the pool had an open
account.** But the measured consequence is **≈0 suppressed launches**: refill is also gated by
`free_gb < MIN_FREE_GB` and **24 of 25 free-RAM readings in the entire log are below 8 GB
(range 4.2–8.0), 10 of 10 in the pool era**; `worker-spawn` events in all 277 lines: **0**; board
depth on the 5 divergent ticks was 0,1,1,1,1 and depth 0 skips refill anyway. Revive's candidate
filter (`:279-281`) excludes `reaped == "quota-requeued"` — precisely the population a hold creates
— and there were **0 revives on 14 unheld pool-era ticks**. `ci_merge` runs regardless
(`reflex.py:305 if True:`). **So: observability, not throughput, not money. 5/24 ticks over 2h37m.**

**The bigger fish it turned up:** `MIN_FREE_GB = 8` on a machine whose free RAM **never once measured
≥8 GB in 25 readings**, with `WORKER_MAX = 7` unreachable and **0 worker spawns ever recorded**.
Reflex's worker refill is dead by admission control, independently of quota — dimension 7. This is
the third confirmation of my lineage's standing PREDICTION 2, now with the full census; and
`monitor/inbox/20260728T151500Z-W-1251-…-24-agents-and-6gb-free.md` is the *opposite* direction (the
pre-fix fail-open 99 GB default). It also corroborates G6's restored conclusion from the other side:
the memory gate is what has kept the loop unentered for 15+ hours.

**GAP 2 — the identity question the record left open is now ANSWERED: the machine default login is
account `b`.** Measured from the non-secret `oauthAccount` profile blocks only (no credential read,
no login, booleans only): `accountUuid`, `emailAddress`, `organizationUuid`, `organizationName`,
`displayName`, `accountCreatedAt`, `subscriptionCreatedAt` all **same** for default-vs-b and all
**differ** for default-vs-a and a-vs-b; only `profileFetchedAt` differs between default and b, i.e.
two independently-refreshed caches of one account. The same script says default≢a while saying
default≡b — the discriminating control in both directions. `b/.credentials.json` (509 B) ≠ default's
(928 B), so b's dir was genuinely logged in, not copied: **b's `claude auth login` landed on the
account the machine default already held**, verbatim the trap `monitor/ACCOUNTS.md:24-31` warns
about. Good news beside it: **a ≠ b**, so the pool really is two subscriptions.

Consequence chain: `_runner.py:181-191` has no `else` when `pick()` returns None (and
`accounts.py:29` says in its own docstring that `pick()` deliberately returns None and must not
return a default; registry has **0** `account_error` entries, so the fallback is reached by
`if acct:` being false, not by the exception arm) → header records `account=default(...)` →
`quota.py:298` maps any `default*` to `None` → `_rotate_on_limit` returns `"no-pool"` (`:327-330`)
→ `check()` sets the **GLOBAL hold instead of closing b's window, even when a is open**. **The
fallback launders a per-account limit into a fleet-wide freeze — the exact failure the pool was
bought to prevent.** Second refusal exists but is partial: `pick()` returns None iff no account is
usable, which is exactly `standing.py:165`'s condition, so the standing-post path IS refused first;
what remains is a TOCTOU window (held computed once per tick, posts ~45 s apart, `_runner.py:176-177`
picks at launch time) and the worker/revive path, which has no second refusal **because of GAP 1** —
the global flag does not go hold when accounts are unusable for a *login* reason
(`accounts.py:126-142`, `login_state()` → `unknown` on an `auth status` timeout). **The two gaps
compose.** Units: **$0** — both are flat-rate Max 20x (`accounts.json:2`) — so wasted launches and
fleet-freeze minutes, not dollars. Frequency bounded not settled: ~90 runner-started launches vs 84
`note_launch` increments ⇒ **order 6 firings (~7%)**, and it cannot be closed because the only record
of the fallback lives in dispatch-log headers, **the one artefact class the auditor may not read** —
though `_runner.py:179` and `ACCOUNTS.md:71` both promise it is a "具名、可见" (named, visible)
fallback. One line would fix that: `accounts.log("FALLBACK-DEFAULT %s" % pid_str)`.

**A CORRECTION TO A PUBLISHED RULING OF MY OWN LINEAGE (refuter D is checking this before I file).**
`monitor/audit/DRIFT-20260729T1420Z…:13-15` ruled the hand-written identity equation "b (the machine
default)" to be *"一个树上无法佐证的身份等式"*, and its suggestion #1 (`:80-84`) directs that the limit
be recorded as belonging to `default(no-pool)` and **not** to pool account `b`. At the subscription
level that is **false** — they are one account, so the hand-written entry was substantively right.
And that suggestion's alternative remedy ("add a `default` account to accounts.json pointing at
`~/.claude`") would enter **b twice** into the pool, corrupting `any(usable)` and the least-launches
tie-break. Do not implement as written.

**One more new mechanism.** `monitor/quota.py:473` `ping()` runs
`subprocess.run([claude,"-p","reply with: ok","--model","haiku"])` with **no `env=`**, and
`CLAUDE_CONFIG_DIR` is set nowhere outside `accounts.py:112/120` (`reflex.py:55` passes no env
either). So the window probe — the **only automatic exit from a global hold** (`quota.py:415`,
`window_is_open` `:494-514`) — measures and spends **account b, never a**. During the 16:32Z hold b
was the limited one, so the probe was asking the limited account whether the window had reopened:
all 5 attempts logged `quota:probe-throttled` (`MIN_PING_INTERVAL_MIN = 20`) and the hold expired on
its **deadline, not on evidence**. The automatic exit has one leg and it is b's.
