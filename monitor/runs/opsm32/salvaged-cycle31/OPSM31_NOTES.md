# OPS-M cycle 31 — running notes (write-as-you-go; context is not storage)

session restarted after cycle 30 hit the context wall. Resumed as cycle 31.
master at start of cycle: `cc7e414eb3bfde3325a50f9ce0e8dc896bda2b84`

## Boot facts (OBSERVED)

- bus: `NO-NEW-MESSAGES`; no `monitor/bus/OPS-M/URGENT`.
- `monitor/ci/merge.lock` contains pid `2220`; `Get-Process 2220` → **alive**, started
  2026-07-30 19:19:10 local (= 11:19:10Z). So the ci_merge death I watched at 11:14:32Z
  last cycle was followed by a restart 5 minutes later. `merge.log` fresh through 11:45Z.
- `monitor/reflex.log` last line still `2026-07-30T08:32:21Z` → 200+ minutes silent while
  merge.log stayed fresh. (Agent 5 is establishing whether that means dead or quiet.)
- master's `freeze/verify.sh` last stage header is `echo "[14] every gap in the kit names
  who fixes it, where, and how it clears"` (line 847). **CONFIRMED by `git cat-file -p
  master:freeze/verify.sh`**: no `[15]`, no `[16]`. So cycle 30 was right that master is
  not a valid comparator for the stage that reds s4-freeze.
- main checkout HAS `proxy/var/{ledger.jsonl,runs,scores,spend_gate.jsonl}` (gitignored via
  `proxy/.gitignore: var/`). A fresh worktree does not. Candidate explanation for
  s4-freeze's `POOL ABSENT` + BUDGET_TABLE drift. **UNPROVEN — agent 1 is testing it.**

## CORRECTION to my own cycle-30 claim (found 11:55Z, before escalating it again)

Cycle 30's heartbeat said the queue "has literally never run that gate on it [a3's
theoria-arm gate], because ci_merge returns on first red and sorted() puts monitor before
theoria-arm, so the one measurement that would show a3's value is structurally
unreachable."

**That is false as stated.** `monitor/ci/merge.log` contains:
- 19 × `FLAG origin/agent/a3-campaign-devpile: verify gate red in theoria-arm (verify.py)`
- 4 × `FLAG origin/agent/a3-campaign-devpile: tests red in theoria-arm`
- 1 × `MERGED origin/agent/a3-campaign-devpile` at 2026-07-29T00:25:10Z
  (dirs: PARTNER_SYNC.md,monitor,theoria-arm; gates: verify:monitor(verify.sh),
  pytest:theoria-arm) — **a3 has landed on master once already.**

The defensible version is narrower: *while* monitor is red, theoria-arm is masked for that
attempt. "Never" was wrong, and wrong in the direction that made my own escalation sound
more urgent — the same failure mode I flagged in myself last cycle (two errors both
skewed toward making things look worse).

## A SECOND contradiction, between two of my own verdicts on a3

- **Verdict X** (`NOTE-BY-OPS-M` line in merge.log, 2026-07-29): a3 is **GUILTY** —
  `tests/test_arm.py::test_the_archive_stays_accountable`, manifest re-derivation drift on
  leg `20260729T004020Z-leg01`, *"green on clean master and red with a3 merged"*.
- **Verdict Y** (cycle 30 heartbeat, 2026-07-30T11:18Z): a3 is **THE REPAIR** — control
  RED, merged GREEN.

Exactly opposite. Agent 6 is re-measuring both arms at current master and reconstructing
how both came to be recorded. **Until it reports, I must not re-escalate "a3 is the
repair" — that is now an open question, not a finding.**

## Agents dispatched (11:48–11:57Z)

| # | scope | arms |
|---|---|---|
| 1 | s4-freeze | tip-alone vs merged, freeze gate + mechanism of BUDGET_TABLE drift |
| 2 | s4-e23-tiers | tip-alone vs merged (vs master iff the stage exists there) |
| 3 | monitor gate control @cc7e414e + s38 merged arm | full failing-id sets |
| 4 | s41 + s42 merged arms | full failing-id sets; told to watch for the third category (branch's new test correctly catches master's defect) |
| 5 | reflex 200-min silence | read-only forensics; told to refute my two prior claims |
| 6 | a3 contradiction | theoria-arm ctl vs merged; resolve X vs Y |

Still to do after they report: set comparison at my level, then ONE adversarial agent
whose only job is to break my rulings, then inbox + mailbox + push.

## RESULT 1 — s4-freeze: ENVIRONMENT-ARTIFACT (agent 1, ~12:00Z)

Arm A (tip `f47b6b30` alone) RC=1. Arm B (merged onto master, clean, merge `c8a8c53a`) RC=1.
**Transcripts byte-identical modulo worktree path.** The merge contributes nothing.
=> the branch does not cause its own red. Same stage `[15]`, same single failure.

**Mechanism (two independent causes, both outside the branch):**
1. `freeze/build_budget_table.py:78-88 resolve_pool()` reads `proxy/var/spend_gate.jsonl`,
   gitignored (`proxy/.gitignore:3`). It walks *up* out of a checkout whose path contains
   `.worktrees` to find the main checkout's pool. **`monitor/ci_merge.py:513` uses
   `tempfile.mkdtemp(prefix="ci-merge-")`**, i.e. `%TEMP%\ci-merge-*` — `.worktrees` is not
   a path component, the walk-up never fires, `resolve_pool` → `None`, and
   `freeze/verify.sh:1158` calls `--verify` WITHOUT `--allow-absent-pool`, so rc=1
   unconditionally. Reproduced the queue's flag text verbatim (incl. the 4-section list and
   the POOL ABSENT sentence) by monkeypatching only `resolve_pool` → single-variable proof.
2. Even WITH the pool reachable it is still red: the pool is **live append-only runtime
   data**. Committed table pins `pool.sha256/lines/max_seq` at 12929; fresh build = 13947,
   and it moved again to 13967 while the agent watched. $0 of new money — the *action*
   headroom moved. Any committed table goes stale within minutes, in any checkout.

**Note on self-interference:** the churning records are pytest traffic, e.g.
`{'kind':'release','campaign':'theoria-arm:A3-campaign-devpile:...:pytest-count-...'}` —
our own gate/measurement runs write to the spend-gate ledger, so measuring makes this
particular drift worse. Does not create the defect; does mean the number can never settle.

**master itself is red here too**: run in the main checkout (pool present, read-only —
verified by identical `git status --porcelain` and identical sha256 of all three artefacts
before/after) → RC=1 with `sections that moved: balance, citations, pool, verdict` plus
`CITATION DRIFT: freeze/STATS_RULES.md:777, :791`. **The branch FIXES the citation half**
(it moved those anchors to `CITED_IN_SECTION`; Arm A shows no CITATION DRIFT) and cannot
fix the pool half.

**The stage currently carries zero information** and says so itself, in the real queue
transcript and both arms: `NOTE negative control not run: the relocated copy does not
reproduce 15b's own verdict, so a red from it would prove nothing about the real budget
table`. Unconditionally red ⇒ cannot distinguish a clean table from a forged one.

**CORRECTION #3 to me (agent 1 refused my framing, correctly).** I told it "a fresh git
worktree will NOT have `proxy/var/`". False. A worktree under `.worktrees/` DOES reach the
main pool — deliberately, `build_budget_table.py:74-77` says one-pool-per-worktree was a
real defect worth $10,959.90 of authorised exposure (`proxy/SPEND_GATE.md:219-226`). The
discriminating variable is **whether `.worktrees` is a component of the checkout path**,
not worktree-vs-main. My version would have sent the monitor after the wrong variable.

**Fix menu (for the monitor — only it may change `monitor/`):** passing
`--allow-absent-pool` is necessary but NOT sufficient (pool-less `build()` yields different
balance/pool/projection/verdict). Moving ci_merge's worktrees under `.worktrees/` — which
would also bring it into line with CLAUDE.md's own worktree convention — removes POOL
ABSENT but the stage stays red (cause 2). **Only real fix: stage 15b must compare the
pool-independent sections (policy, pricing, factors, unit_prices, tracked_*, citations) and
check the pool half only where a pool exists.** That is a `freeze/` change, i.e. s4's
owner, not the monitor.

## RESULT 2 — s4-e23-tiers: same verdict, same mechanism, plus the thing that decides both (agent 2, ~12:07Z)

Arm A (tip `6eaf2da2`) RC=1; Arm B (master+merge → `d92e3993`, clean, 22 files/4406 ins) RC=1;
**byte-identical modulo path** again. Arm C correctly skipped: master's verify.sh never
invokes `build_budget_table.py` at all (`grep` = 0 matches), so master cannot produce a
comparable datum. Same stage 15b, same `sections that moved: balance, pool, verdict`.
Branch pins `pool.lines: 12995`; live pool 13947 → 13967 in ten minutes.

**Two INDEPENDENT agents, separate contexts, converged on the same mechanism** (ci_merge's
`tempfile.mkdtemp` defeats `resolve_pool`'s `.worktrees` walk-up; plus the pool churns).
That is the strongest evidence I have this cycle.

**Agent 2 sharpens one of agent 1's points, in the direction of less hope:**
`--allow-absent-pool` would NOT rescue it even partially — in `main()` the JSON drift
comparison sets `rc = 1` **before** the pool check is reached, and the `pool` section itself
(`present: true` vs `false`) is a hard DRIFT. So that flag is not "necessary but
insufficient"; it is simply inert here.

**THE FINDING THAT DECIDES THE DISPOSITION.** The two mutually exclusive states:
- table generated WITH a pool (`present: true`) ⇒ red in ci_merge's temp worktree;
- table generated WITHOUT a pool (`present: false`) ⇒ red in every real checkout.
There is no table that is green in both. And therefore:
**if either s4 branch merges, stage [15] lands in master's `freeze/verify.sh` and
`freeze/`'s gate is permanently red in ci_merge for EVERY subsequent branch touching
`freeze/`.** Merging these by ruling would not clear two flags; it would convert two flags
into a permanent territory-wide block. => **Do NOT merge by ruling. Send back.**

**And the red IS branch-attributable after all — just not the way the flag says.** The
branch's own header comment documents the defect it shipped: *"15b goes red on its own after
any spend, with no edit anywhere"* and *"a red from 15b therefore does not distinguish
'somebody hand-edited the table' from 'the balance moved since it was last regenerated'"*.
So: **environment-artifact for the red, branch-caused for the un-mergeability.** The author
wired a gate into the queue that they had already written down was un-greenable.
s4-e23-tiers adds `[15]`, `[16]`, `[17]`; s4-freeze adds `[15]`, `[16]`.

**Combined ruling for both s4 branches (draft, pending adversary):** HOLD, and write inbox
for `freeze/`'s owner — 15b must split the pool-dependent sections
(pool/balance/projection/verdict) from the pool-independent ones and check the former only
where a pool exists. Separately, recommend the monitor move ci_merge's worktree from
`tempfile.mkdtemp` to `.worktrees/` — that does not fix 15b, but it removes a whole class of
"the queue's checkout is not like any real checkout" defects and brings ci_merge into line
with CLAUDE.md's own worktree convention. Note the flag reason ("verify gate red in freeze")
is true but useless; both attempts counters (13 and 7) are counting a deterministic,
unfixable-by-the-author-as-specified red.

## RESULT 3 — reflex: ALIVE BUT LIVELOCKED, and ci_merge is the child that kills it (agent 5)

**Verdict: alive, livelocked, heartbeat dead.** `reflex.py` pid **42104** started 11:17:01Z
(parent = the scheduler); `ci_merge.py` pid **2220**'s parent IS 42104. So reflex is executing
its steps right now — it simply never reaches the log line.

**Root cause (INFERRED, high confidence): `reflex.py:345-346`,
`subprocess.run(ci_merge.py, timeout=3600)`, unguarded.** ci_merge routinely needs >60 min
(~15 flagged branches, a full verify gate each, `ci_merge.py:543 timeout=1800` per gate, and
`--max 2` at L635 caps successful *merges*, not attempts). So every cycle is killed
mid-merge and dies before `reflex.py:363`. Nothing between L124 and L363 catches
`TimeoutExpired`; eight child calls, all unguarded.

**Corroboration is airtight and OBSERVED**: `monitor/ci/merge.lock` has LastWriteTime
19:19:13 but **CreationTime 10:14:15Z** — NTFS tunneling preserved the ctime of the *previous*
ci_merge's lock, which means that lock was still on disk for pid 2220 to discard as stale,
which means the previous ci_merge **never ran its `finally: release_lock()` — it was killed**.
10:14:15Z + 3600s = 11:14:15Z; next 5-min trigger 11:17:01; pid 42104 started 11:17:01.
Every timestamp matches to the second. That is my cycle-30 "watched it die" event, now with
its mechanism attached.

**CORRECTION #4 — my "200 minutes of silence" was wrong by 3x, and wrong in the direction
that UNDERSTATED it.** The last five reflex.log lines are the **mid-cycle** `rlog` at L234
(`quota: window reopened...`), not the end-of-cycle line at L363. The last actual
**cycle completion** is `2026-07-30T01:33:34Z` (reflex.log:275). **No cycle has completed in
10h20m.** The 08:32:21Z line proves only that a cycle reached L234.

**CORRECTION #5 — and this one invalidates the fix I have been pushing for two cycles.**
I have been telling the monitor S43's correct scope is "four `except` guards + my three lines
+ forward-fix". On the guards: `873d62ee` deleted **seven** hardening items, of which exactly
**one** was an `except` block deleted outright; "four" matches the four *returncode* checks,
not except guards. One of those four (`merge:EXIT`) was **already restored** by `c8061d7b`
(reflex.py:111-113). And decisively: **the ci_merge timeout guard never existed in either
version of the file** — `873d62ee` did not delete it. **So restoring everything `873d62ee`
removed would NOT bring the heartbeat back.** It would print `SCAN FAILED` when the secondary
path fires, nothing more. S43 as I specified it fixes the tests, not the outage.
(`scan.py` measures ~92 s against its 600 s timeout, so it is not the live cause; and the
`scan.py` pid 4576 alive right now belongs to **TheoriaDashboard/refresh.cmd**, not reflex.)

**Two hazards to publish:**
- `reflex.lock`'s mtime is never refreshed, so "age" = time since the instance *started*, and
  the live lock is already older than the 1500 s stale threshold. **Anyone who hand-runs
  `python monitor/reflex.py` right now deletes a live instance's lock and runs a second reflex
  concurrently**, after which 42104's `finally` deletes the newcomer's lock. Do not hand-run it.
- `Microsoft-Windows-TaskScheduler/Operational` is **disabled**, so no start/stop history
  exists for any Theoria task. And a fresh `monitor/index.html` is NOT evidence reflex is
  healthy — `TheoriaDashboard` regenerates it every 10 min independently. (That kills another
  candidate liveness instrument, after I already had to withdraw `merge.log` in cycle 19.)

**THE SPIRAL, which is my own beat and I had not named it.** Flags accumulate → each pass runs
a full gate per flagged branch → the pass exceeds 3600 s → reflex kills it mid-pass → flags
never clear → more branches accumulate → the pass gets slower. The queue has not completed a
pass in over 10 hours, so **`attempts:` counters are not measuring branch stubbornness, they
are measuring how often a doomed pass got as far as that branch.** Every NEEDS-HUMAN number I
have escalated (28, 24, 23, 20, 19, 13, 7...) is built on that. My own measurement load makes
each gate slower and is a contributing, non-causal factor — worth saying out loud.

**PREDICTION TO CHECK AT 12:19:10Z (agent 5's, falsifiable):** pid 2220 is killed at
12:19:10Z; pid 42104 exits with **no new reflex.log line**; a fresh reflex starts ~12:22:0x.
I will check this myself before writing the inbox — it converts the root cause from inferred
to observed.
