# S47 — the refusal wave gets a retry predicate

| | |
|---|---|
| prompt | **S47** · `refusal-wave-retry-predicate` |
| worker | `W-9203` |
| branch | `agent/s47-refusal-wave-retry-predicate` |
| base commit | `1e5b3f00` |
| archive | `proxy/runs/20260802T0900Z-S47-refusal-wave-retry-predicate/` (`MANIFEST.json`) |
| tests | **536 passed, 0 failed** (497 at base; +25 predicate, +14 replay). 7 of the 25 fail if `forward()` is made to ignore `retry_body` — measured by mutation, not assumed |
| gates | `python verify.py` green on all five rungs; `verify_contract.sh` 9/10 (the tenth is red on master too, see below); `verify_s47.sh` green |
| cost | **$0.00** — zero API calls, zero model calls, zero network, zero actions charged |

## What landed

1. **`forward.py` gained a caller-supplied retry predicate.** `retry_body` is
   keyword-only with a default of `None`, and is consulted **only for
   `status >= 400` that `RETRY_STATUSES` has already declined**. So it widens
   the policy and cannot narrow it, and unset — which is how `model_proxy` and
   every other caller leave it — the function is byte-for-byte what it was.
   `RETRY_STATUSES` itself does not move: the discriminator for this response is
   in the body, and a status set carrying a body-shaped fact would say something
   false about every other `400`.

2. **`env_proxy.py` owns the ARC knowledge.** `game_not_found_retry(game_id)`
   builds the predicate for a command that named a game — `400` ∧
   `error == "SERVER_ERROR"` ∧ `message` exactly `game <that id> not found`,
   anchored, id captured and compared. `/api/scorecard/*` names no game, so it
   gets no predicate at all. The split exists so that `forward.py`'s first
   docstring line — nothing here knows about ARC — stays true of the one module
   both proxies share and `verify_spend.sh` whitelists as the only route to a
   socket. `D-S47-001`.

3. **An attempt retried on the body is marked.** `http.attempt_log` entries
   carry `"body_retry": true` where that rule fired, and only there, so no
   record written before this change becomes ambiguous. Without it a collapsed
   row is indistinguishable from a rate-limit retry — and the reason to collapse
   this wave at all is that its size stops being invisible. `C-009`.

4. **`tools/refusal_replay.py`** — an offline, zero-spend replay that drives the
   *shipped* predicate over the four archived legs and recomputes, rather than
   asserts, both things that must not move.

## The measurement

Four legs of 2026-07-31, replayed offline at `max_attempts=5`:

| leg | `env_step` before | after | wave | sockets | `actions_agree` |
|---|---:|---:|---:|---:|:--:|
| `20260731T1240Z-A3-level2-carried` | 60 | 15 | 54 | 60 → 60 | true → true |
| `20260731T1310Z-A3-level2-carried-r2` | 99 | 27 | 85 | 99 → 99 | true → true |
| `20260731T1430Z-A3-level2-carried-r3` | 234 | 63 | 200 | 234 → 234 | true → true |
| `20260731T1500Z-A3-sk48-carried-l1` | 177 | 44 | 155 | 177 → 177 | true → true |
| **pooled** | **570** | **149** | **494** | **570 → 570** | **true → true** |

**73.9% fewer rows, and not one socket fewer.** The second half is the honest
half: this change moves ledger rows, not requests. The pool pays exactly what it
paid; what changes is that 570 rows stop pretending to be 570 separate commands
when they were 149 commands' worth of attempts.

**149, not 76.** The obvious idealisation — one logical command, one row — is
wrong, and the replay models `forward()`'s actual bounded loop instead. 73 of the
149 rows exist *because* the 5-attempt budget ran out while the predicate still
wanted to retry; the arm then retries and that is a new row. Row count as a
function of the budget, pooled: 1→570, 2→303, 3→219, 4→170, **5→149**, 6→134,
8→112, 10→104, 16→83.

## Two things found while doing it

**The predicate was being asked about successes.** The first draft consulted
`retry_body` on every terminal status, including the `200` that ends a
successful retry. A test that installs a predicate answering `True`
unconditionally caught it: `forward()` would have discarded a response the pool
had already paid for and gone to buy another. Hence the `>= 400` floor, which
also keeps a refused redirect (RED-01) out of the hook's reach. The design
review did not catch this; the test written to pin "widens, never narrows" did,
because the upper bound was the half nobody was looking at.

**The wave is on `ACTION`, not `RESET`.** In
`20260731T1430Z-A3-level2-carried-r3`, 199 of the 200 refusals are `ACTIONn` and
one is `RESET`. A fix reaching only `RESET` would have closed half a percent of
the finding while looking finished, so the end-to-end coverage runs both.

## What the adversarial review changed

Two independent reviewers were run against the finished change with instructions
to refute it. Neither could construct a false positive for the predicate — they
tried duplicate JSON keys, `NaN`, non-string `message`, Cyrillic homoglyphs,
NBSP and vertical tabs inside `\s+`, a 100k-character id, and an id made of
regex metacharacters — and the offline replay's arithmetic was re-derived
independently and matched (`[15, 27, 63, 44]`, 149). Four things did not survive:

1. **`body_retry` was written on the terminal attempt of an exhausted call**,
   where no retry happens — so a counter over the field over-counted by one per
   exhausted call, and the field contradicted the sentence `LEDGER_FORMAT.md`
   defines it by. **Fixed**: the budget is now checked before the mark. Worse
   than the bug: my own test asserted `all(... for a in attempt_log[:-1])`, and
   the `[:-1]` excluded exactly the entry that was wrong. The assertion now
   names the last entry explicitly and counts the marks.
2. **The id comparison was case-sensitive** while `guard.py:stem()` lowercases
   deliberately and `harness/arc.py:FULL_ID` admits an uppercase stem. An
   upstream echoing `G50T-…` for a request naming `g50t-…` would have produced
   no retry, no marker, no incident and no failing test — S47 doing nothing
   while looking correct. **Fixed**: case-folded, which cannot turn a
   *different* game into a match.
3. **"The pool ceiling is unaffected" was false.** `permit.check()` reads
   recorded spend and `_charge` records after the loop, so a reservation binds
   at `action_cap + (max_attempts - 1)`. Pre-existing and already in
   `SPEND_GATE.md` §5 — but S47 moves it from a rare path onto 87% of traffic.
   **Claim corrected**, in `D-S47-001` and above.
4. **`STATUS.md` said 518 tests when the tree had 534.** Corrected.

And one finding that is real, is not ours, and is now the first thing the inbox
note asks for: `theoria-arm`'s `Budget(commands=2000)` exists, in its own words,
to stop "a wave of transient 400s from turning into an unbounded run", and it
counts arm-level attempts. After this change one of those is up to five sockets,
so the counter written for this exact wave is the one bound that no longer sees
it — a leg sized for 2000 outbound can issue up to 10,000.

The reviewers also showed that **16 of 23 tests passed on master too**. Most are
the mandatory negative controls, which are supposed to; but the mutation matrix
is recorded rather than glossed, because "23 tests" and "7 tests that fail if the
change is reverted" are different claims and only the second one is a gate.

## What is owed after this

* **The retry is now nested and the outer half is not ours.**
  `theoria-arm/harness/arc.py:_retryable` still retries a `400`-not-found up to
  40 times, and each is now up to 5 attempts inside the proxy. On the transient
  this is close to cost-neutral — the arm only re-enters on a non-200, so the
  same requests happen, regrouped. On a **permanently** failing id the worst
  case goes from 40 sockets to 200, and the signature cannot prevent that: a
  retired id returns a byte-identical body, so "permanent" is not a thing these
  three conjuncts can see. Recommendation filed to `monitor/inbox/`, not acted
  on — that file belongs to `theoria-arm`.
* **The action cap is soft, and S47 makes the softness routine.** A reservation
  binds at `action_cap + (max_attempts - 1)`, because the check reads recorded
  spend and the record is written after the loop. `SPEND_GATE.md` §5 already
  says so; closing it means reserve-commit-settle, already open in
  `runs/20260728T083000Z-s3/ADVERSARIAL.md`. Not S47's to do, but S47 is why it
  matters more.
* **Nothing reads `body_retry` yet.** This change writes the field and does not
  consume it — not `refusal_replay.py`, not `replay_spotcheck.py`. It is the
  only place a post-S47 ledger records how many refusals a collapsed row stands
  for, so any tool that wants the wave's size back needs to be taught it.
* **`partition()`'s row-count reading changes meaning on future legs.**
  `armtools/refusal.py` keeps working — no field it reads moved — but one row
  can now stand for up to five refused requests, so `upstream_transient` stops
  equalling the number of refusals. `outbound_accounting()` sums `http.attempts`
  and is unaffected, so the published `OUTBOUND_PER_ACTION = 9.3` does not move.
* **`verify_contract.sh`'s last step is red, on master as well as here.** It runs
  `python -m pytest proxy -q` from the repo root, where the repo-root `tools/`
  package shadows `proxy/tools` and `tests/test_audit_delivery.py` fails at
  collection. Reproduced at `1e5b3f00` before anything was touched. It is
  `proxy` territory and a real defect, but a different one with a different
  cause; left for a cell that owns it rather than folded in here.
* `step_idx` still numbers attempts rather than actions — item 2 of the same
  report, deliberately untouched, because renumbering rewrites the meaning of a
  field in already-published manifests.

Reproduce every number above with
`bash proxy/runs/20260802T0900Z-S47-refusal-wave-retry-predicate/verify_s47.sh`
from the repository root, or the four commands in `MANIFEST.json` → `reproduce`.
