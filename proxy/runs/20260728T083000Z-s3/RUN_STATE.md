# S3 · 共享花费闸门 — running notes

Worker `W-1540`, branch `agent/s3-spend-gate-v2`, base `733dcfd`.
Written as the work happens; the conclusions at the bottom are the last thing added.

## 0 · Provenance of the code this ticket starts from — read this first

`proxy/spend_gate.py` and `proxy/spend_policy.json` did **not** come from a blank
page. They were found as **uncommitted, untracked files in a dead session's
worktree**, `.worktrees/wt-s3/`, written 2026-07-28T04:07Z by a worker that
never committed and is no longer running (`agent/s3-spend-gate` still points at
its baseline `c47366c`; the board shows no prior claim of this item, and the
three live worker tasks hold other items). 916 lines, no tests, no docs, wired
into nothing.

The board item was written believing the file does not exist — W-1521 checked at
its own start time and correctly reported `proxy/spend_gate.py` absent, which it
was, four hours before that file was written.

I salvaged it rather than rewriting it, because rewriting would have thrown away
a good design and produced a second one to reconcile. What that means for how
this ticket must be read: **the 916 lines are inherited and unverified.** Nothing
in them had ever been executed. Everything below is what it took to find out
whether they work, and what had to change.

I did not touch `.worktrees/wt-s3/`; the files were copied out. My branch is
`agent/s3-spend-gate-v2` because `agent/s3-spend-gate` is checked out in that
worktree and taking it would have meant destroying another session's directory.

## 1 · What the inherited code already gets right

Read in full before changing anything. The design is sound and matches OPS-R's
proposal more closely than the proposal's own sketch did:

* **Read-sum-append inside one exclusive OS-level file lock**, so two processes
  cannot both observe the same headroom and both take it. `threading.Lock`
  would not have been enough — INC-BA-003's writers were four separate OS
  processes started by a session that could not see this one.
* **The check reads the global sum**, over every campaign and every session,
  never this process's own counter. That sentence is the entire point.
* **Reservations hold headroom, they do not announce it.** A live reservation's
  unspent remainder is subtracted from what anyone else may reserve. That middle
  term is exactly what INC-BA-003 lacked: both sessions were told the truth
  about the pool, and both were told it before the other took its share.
* **A lease, not a lock**: reservations expire, so a session that dies
  mid-campaign does not hold the pool's headroom until a human notices. Expiry
  releases the *hold*; it never releases the *spend*.
* **`record` appends before it evaluates the caps, and appends even when it is
  the record that breaches them.** Money that was spent is a fact. A gate that
  refused to write down an over-budget spend would be a gate that makes the pool
  look under budget.
* **No `enabled` flag, no environment variable, no `gate=None`.** Every failure
  mode — missing lock primitive, unreadable policy, unwritable ledger, corrupt
  line, absent or expired reservation — refuses egress and raises.

## 2 · Faults found in the inherited code

### 2.1 · The write probe raced against itself

`_assert_writable` created and removed a probe file with a **shared name**. Two
gates constructed at the same instant — the normal case, since concurrency is
what this module is for — would each create and each remove the same file, and
whichever lost would see `FileNotFoundError` from its own `os.remove` and refuse
to spend. A fail-closed gate that fails closed on *itself* is an outage.

Fixed: the probe carries the pid, and its removal is in a `finally` that
tolerates its absence.

### 2.2 · One unpriced call bricked the entire pool, permanently

The important one, and it was only visible once the gate was wired to the egress
path — which is the argument for wiring it rather than shipping it beside the
code that spends.

`check()` refused **every** spend, of any kind, if any call in the pool had ever
been unpriced. In the test suite that meant: one mock model call with a name
absent from `proxy/pricing/` poisoned the shared pool, and thereafter the
*environment* proxy — which spends no dollars at all — could not open a socket.
Eight unrelated seal and red-team tests went red. In production it would have
been worse: the pool is shared across sessions, the ledger is append-only, and
nothing could take it back. A missing price-table row would have stopped every
campaign in the programme with no recovery short of moving the ledger aside.

The intent was right and the scope was wrong. An unpriced call makes the
**dollar** total a lower bound; it says nothing about ARC actions, which are
counted by the request. Now:

* `check(usd > 0)` refuses while blindness exists — the gate would otherwise be
  comparing a real number against one it knows is too small;
* `check(usd == 0, actions > 0)` proceeds;
* `price_unpriced(res, usd=…, resolves=…, reason=…)` is the way back — appended
  rather than edited, a stated reason required, and it refuses to resolve more
  blindness than the pool has, since otherwise the count could go negative and
  re-open the gate on nothing.

D-027 records the general form: a gate that can brick the whole programme on one
missing row is not fail-closed, it is a single point of failure wearing
fail-closed's clothes — and the difference matters because the first kind gets
fixed and the second kind gets disabled.

### 2.3 · The interface a live caller had already guessed

`theoria-arm/armtools/spend_check.py` was written against this gate before it
existed, defensively, loading it by path and calling
`module.reserve(campaign, usd_cap, action_cap)` — a **module-level** function.
The inherited code only had `SpendGate().reserve(...)`, so the caller would have
found the file, imported it, and silently fallen back to "absent".

Module-level `reserve` / `check` / `record` / `release` / `totals` now exist on a
lazily-constructed default gate. Same class, same policy, not a looser path —
there is a test asserting the module-level form refuses everything the class
form refuses.

## 3 · What had to be built, beyond the salvage

**Tests: 48 offline + 6 multi-process.** The inherited code had none, and had
never been executed. Two things the suite is deliberately built around:

* Every property has a **negative control**. `test_every_worker_actually_got_through`
  exists because an assertion over four workers that all silently failed would
  pass the "nothing is lost" test too. `test_without_truncation_the_same_prefix_would_read_incomplete`'s
  analogue here is `test_check_prevents_where_record_accounts`.
* The concurrency tests spawn **real interpreters**, not threads. A
  `threading.Lock` passes a threaded test and would still have lost the money:
  INC-BA-003's writers were four separate OS processes started by a session that
  could not see this one.

The first fuzz run found a **test** bug rather than a gate bug, and it is worth
recording because it is the failure mode of concurrency tests generally: with no
hold, worker 0 reserved, spent and released before worker 1 had started, so four
workers each got the whole pool and the admission check was never under
contention. The workers now hold their claims while the others try.

**Egress wiring.** `forward.forward()` requires a keyword-only `permit` with no
default; both proxies mint one per request; `runner.run_game()` takes one
reservation for the run, shares it with both proxies, releases it at the end and
fingerprints the pool into `run_start`. 225 → 234 tests, all green.

**A session-scoped conftest fixture** points the whole proxy suite at a scratch
pool. Without it, every proxy test would append fictional dollars to the tracked
`proxy/var/spend_gate.jsonl` and eat real headroom — and the gate is deliberately
unable to tell test money from real money. It is autouse and session-scoped so
it also covers tests nobody has written yet, which is the same failure shape the
gate itself exists to stop.

**The `campaign` field**, in `baseline-arms/harness/ledger.py` (the one sanctioned
cross-border edit) and in the proxy's `run_start`. History is attributed at read
time rather than rewritten — D-028. Measured: **560 lines, 151 decidable from
`out/campaign_cells.jsonl`, 409 undecidable and staying so.**

## 4 · The adversarial pass

An adversarial subagent was pointed at the wired gate with one instruction:
break the claim. It wrote and ran eleven exploit scripts, and it broke the claim
in five independent ways -- every one of them against code whose own 54 tests
were green. Full findings, fixes, what it could NOT break, and what is still
open: [ADVERSARIAL.md](ADVERSARIAL.md).

The one-line version, in its own words: *the primitive is well built and I could
not break it; the system around it does not deliver the property.* The pool was
one pool per checkout (51 of them, $10,959.90 of combined authorised exposure);
dollars were never authorised before they were spent (one call put $600 through
a $10 ceiling); and the interval between permission and accounting leaked at
both ends.

All five are fixed and each has a test. The residue is listed in ADVERSARIAL.md
under "Still open" -- most importantly, **check->record is not atomic, so the
action ceiling is soft under concurrency**: seven real requests were admitted
into one action of headroom. The dollar axis is now bounded by the pre-flight
ceiling, which is the half that was unbounded. Closing the action axis properly
is a reserve-commit-settle protocol -- a redesign with its own fuzz, not a
rushed edit at the end of this ticket.

## 5 · Verify

```bash
cd proxy && bash verify_spend.sh
```

Green. **257 tests** in the proxy suite (180 inherited + 77 new): 58 unit, 15
egress-bypass, 6 multi-process fuzz, plus 32 in `baseline-arms`. Offline
throughout -- **$0.00 and 0 ARC actions spent by this ticket.**
