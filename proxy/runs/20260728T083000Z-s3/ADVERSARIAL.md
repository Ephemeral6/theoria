# S3 · the adversarial pass, and what it broke

An adversarial subagent was pointed at the wired gate with one instruction:
break the claim. It wrote and **ran** eleven exploit scripts. Its verdict was
that the claim was false in five independent ways, and it was right.

Its own summary is the correct diagnosis:

> The *primitive* is well built and I could not break it. The *system* around it
> does not deliver the property — the pool isn't shared across checkouts,
> dollars are never authorised before they're spent, and the interval between
> permission and accounting leaks at both ends.

Every finding was against code whose own 54 tests were green. That is the lesson
to carry: the suite tested the primitive, and every finding sat in the untested
surface around it.

---

## 1 · The pool was one pool per checkout. There were 51 of them.

The worst finding, and the least visible. `"ledger": "proxy/var/spend_gate.jsonl"`
is relative and resolved against **the importing checkout**. `proxy/var/` is
gitignored, so the file never travels with a branch — and CLAUDE.md *instructs*
every agent to work in `.worktrees/<id>/`.

Measured on this machine: **51 checkouts, each carrying the full $214.90
ceiling, for a combined authorised exposure of $10,959.90.** That is INC-BA-003
reproduced exactly, by the very convention meant to keep sessions out of each
other's way.

It would also have been undetectable afterwards: `fingerprint()` reported the
ledger path *relative to REPO*, so two runs against two different pools carried
byte-identical provenance.

**Fixed.** A relative ledger resolves against `POOL_ROOT` — the **main
checkout**, found by following a worktree's `gitdir:` pointer, which every
linked worktree of the repository agrees on. The fingerprint now also carries
`ledger_abspath`, so a split pool is visible in the record instead of invisible.

## 2 · Dollars were never authorised, only mourned

`model_proxy` minted its permit with `usd=0.0`, so `check` reduced to *"are you
already over?"* and never *"would this put you over?"*. The model proxy is the
only component that spends dollars at all, so the dollar ceiling was a tripwire
**behind** the money rather than a gate in front of it.

Demonstrated: **one call put $600 through a $10 ceiling**, bounded only by what
a single request can cost. Worse, `record()` ran before `run.model_call()`, so
when the trip fired the proxy ledger got **zero** record of the call that spent
the money — provenance destroyed for exactly the call that mattered.

**Fixed** by `PriceTable.ceiling_for(body)`. The Messages API requires
`max_tokens`, so the expensive half of the bill has a stated bound before the
socket opens; the permit carries that ceiling. And **a request with no
computable ceiling is refused rather than sent** — 402, with an incident,
because an unpriceable call is unbounded and the pool has no way to notice it
going by.

## 3 · Unpriced calls were free forever

`UNPRICED_SPEND` guards on `unpriced_calls and usd > 0`, and the only path that
*produced* unpriced calls always presented `usd=0.0`. The rule defended by the
module's longest comment could never fire on the path it was written for.

Demonstrated: **40 real calls, $600 of list-price exposure, pool reporting
$0.00.** Trigger: any model released after the price table was written, or a
typo in the arm's request body.

**Closed at the source** by §2 — an unknown model has no computable ceiling, so
it is refused before the socket rather than discovered after it.

## 4 · The provider's response decided whether the call was billed

Three shapes, all executed:

* `cost()` raises on a usage value `json.loads` accepts but `int()` does not
  (`1e999`, `"1e5"`), and there was no `try/finally` between the response and
  the record: **five real calls, zero ledger rows, indefinitely repeatable.**
* A missing or empty `usage` block priced to **$0.00 with the unpriced flag
  off**, so the pool did not even know it was blind. Strictly worse than §3,
  which at least set a flag.
* An SSE stream cut before `message_delta` loses `output_tokens` — the
  expensive half, at 5× the input rate — and reports the remainder as a
  confident, positive, wrong number.

**Fixed together, with one rule:** a price is trusted only if the usage block
carries **both** halves of the bill; otherwise the call is charged at its
pre-flight ceiling and flagged unpriced. Pricing is wrapped, so a raise charges
the ceiling rather than skipping the record.

Note the deliberate non-rule: *not* `usd > 0`. A model legitimately priced at
$0.00 with a complete usage block is priced, not blind, and flagging it would
jam the pool on nothing — D-027 again, one level down.

## 5 · The retry loop leaked at both ends

Sockets opened and never recorded (a permit tripping on attempt *k* discarded
attempts 1…*k*−1), and five sockets authorised as one, because nothing was
written until the call returned.

The first half was already closed independently while the review ran:
`permit.attempts_made`, incremented before each attempt and charged on both the
normal and the exception path, so requests that happened are charged whether or
not the call they belonged to succeeded. The amplification half is narrowed but
not eliminated — see the open list.

## 6 · Arithmetic

* **`NaN` permanently voided the dollar ceiling.** `NaN` is not `< 0`, and every
  `>` against a NaN total is False. `json.dumps` writes it, `json.loads` reads
  it back, and the ledger is append-only. Demonstrated: after one NaN record, a
  $1,000,000,000 reservation was accepted against a $10 ceiling. Fixed by
  `finite()` on every money argument. `+inf` *did* fail closed — but only by
  accident of float comparison, and a rule that holds by accident is not a rule.
* **`renew()` on an expired lease resurrected re-let headroom.** It checked
  `released` but not expiry. Demonstrated: A's lease lapses, B takes the freed
  headroom, A renews — `held_usd = $20.00` against a $10.00 ceiling, two
  campaigns each believing they hold the whole pool. Not a spend bypass; it is
  the *decision* INC-BA-003 actually was. Fixed.
* **`price_unpriced(usd=0.0, resolves=N)` cleared blindness for nothing** — N
  real calls accounted for at $0.00, and the gate re-opened on the strength of
  it. Now requires a positive amount.

## 7 · Leaked holds made a fail-closed gate an unusable one

Both documented standalone CLIs took a default reservation and then called
`serve_forever()` directly; nothing ever released it. `run_game` released
outside the `with` and with no `finally`, so any exception stranded the run's
whole claim. Demonstrated: **40 abandoned proxies took the shared pool offline
with $0.00 actually spent**, recoverable only by waiting out the TTL.

This is the failure mode that gets a safety mechanism deleted rather than fixed,
so it mattered more than its severity suggests. Both CLIs now release on exit,
and `run_game` is wrapped so every exit path returns what it opened — identified
by comparing live reservations against a snapshot rather than by remembering a
handle, which stays correct even when the run dies before it has one.

---

## What the review could NOT break

Recorded because it is the part that says what is actually load-bearing:

1. **The cross-process lock holds.** 6 processes × 30 `record()` calls: expected
   $1.8000 / 180 actions, got exactly that; 192 ledger lines, 192 distinct
   `seq`. No lost updates, no interleaved lines.
2. **No un-permitted egress path exists.** Exactly two `forward()` call sites,
   both minting a permit first. `replay.py` and `mock/arm_mock.py` use `urlopen`
   only against the *local* proxy, so they route through the gate. Both
   standalone CLIs go through a config that reserves before the server binds.
3. **Every fail-closed precondition held**: missing policy, unparseable policy,
   no ceiling, zero/negative ceiling, missing `default_run_caps`, unwritable
   ledger directory, corrupt line, foreign gate version — all
   `SpendGateUnavailable`, on `totals()`, `check()` **and** `record()` alike.
4. **The permit cannot be forged by accident**: direct construction raises,
   `forward()` without `permit=` is a `TypeError`, `permit=None` fails before
   any socket.
5. **`reserve()`'s admission check is airtight** against `inf` caps,
   over-ceiling caps, and the held term — and it refuses on the action axis even
   when the dollar axis was NaN-poisoned.
6. **`price_unpriced` cannot drive `unpriced` negative or inflate the pool.**
   The hole was `usd == 0`, not the counter.

## Still open — declared, not narrowed

* **check→record is not atomic, so the ceiling is soft under concurrency.** The
  read-sum-append *is* atomic; the interval between the pre-flight and the
  record is not, and nothing on disk represents an in-flight request. Both
  proxies are `ThreadingHTTPServer`. Demonstrated: **seven real requests
  admitted into one action of headroom.** The dollar axis is now bounded by the
  pre-flight ceiling (§2), which is the important half; the action axis
  overshoots by at most `concurrency × max_attempts`. Closing it properly is a
  reserve-commit-settle protocol — a redesign with its own fuzz, not a rushed
  edit at the end of this ticket.
* **The POSIX stale-lock case is unverified.** On Windows the lock file cannot
  be removed while held. Under `flock`, unlink-and-recreate is the classic
  bypass: a second process makes a fresh inode, locks that, and both enter the
  critical section. Untestable from this machine; needs a Linux run before the
  POSIX branch is trusted.
* **`record()` does not check released or expired.** Conservative — refusing to
  record real spend would lose money — but it means `release()` does not
  actually end a claim's write access.
* **A reservation id read from the pool file can be spent under.** In scope per
  `SPEND_GATE.md` §5: the gate stops the failure that happened, not an
  in-process attacker.
* **Truncating the `.lock` sidecar is a one-byte fail-closed DoS** on the pool.
* **`baseline-arms`' own HTTP client is not behind the gate.** It gets the
  `campaign` field and this document; the wiring is that track's to do.
