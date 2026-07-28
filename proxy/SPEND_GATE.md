# SPEND_GATE.md — one pool, one lock, one sum

`proxy/spend_gate.py` is the shared, cross-session register of what has been
spent against one ARC key and one Anthropic bill. This file is its interface
document: what it costs not to have one, how each track plugs in, and what the
gate does **not** protect against.

---

## 1 · Why a convention was not enough

The rule this replaces was a good rule, and it failed anyway. That is the part
worth understanding before reading the API.

**INC-BA-003.** Two Claude Code sessions started two campaigns ninety seconds
apart, in one directory, against one ARC key and one Anthropic bill. Both had
budget gates. **Both gates were correct.** Both were counters inside a process,
so neither could see the other, and the worst-case combined exposure was
**$214.90** that nobody had authorised as a total.

Three damages, and one of them is not repairable:

1. **Unbounded exposure.** Neither session could state the combined number, so
   neither could stop at it.
2. **A measurement that was paid for and cannot be re-bought at that price.**
   The variance envelope was measured under the other campaign's four-process
   load, so its `http/action` and wall-clock figures carry contention and
   cannot be compared with the M4 pilot's unit costs. That is permanent.
3. **An append-only file that mixed two campaigns with no line able to say
   which was which** (`PARTNER_SYNC.md:456`). Append-only means it could not be
   repaired afterwards; battery had to reverse-derive attribution from
   `out/campaign_cells.jsonl` (D-B-013).

`arc-recon/data/incidents.jsonl` INC-011 then recorded the same shape on a
$1.3544 measurement and called it, in its own words, a **standing hazard**.

**The reason a convention could not have prevented it** — and this is the whole
design argument — is that the second session obeyed every rule it knew about,
including the pile cut, which is a far more demanding rule than "check the
budget". It did not fail at compliance. The rule it needed **did not exist to
be known**. A convention only binds the people who have read it, and the set of
people who have read it is not a set you can enumerate at 03:00 when a second
session starts.

What works is what the sealed-pile guard does: **be a function on the first line
of the path that spends**, so that obeying is not something anyone has to
remember. `assert_playable()` is not a rule about sealed games; it is a function
that raises. This module is the same shape, applied to money.

---

## 2 · The four ideas

```
pool ceiling   a number a human wrote down, in spend_policy.json
reservation    a claim on part of the pool, visible to every other process
               before it starts
record         what was actually spent, appended under an OS file lock
the check      reads the GLOBAL sum, never this process's own counter
```

**Three properties, and each one is a test.**

* **Atomic.** Read-sum-append happens inside one exclusive OS-level file lock,
  so two processes cannot both observe the same headroom and both take it. A
  `threading.Lock` would have passed a threaded test and still lost the money:
  INC-BA-003's writers were four separate OS processes.
  `tests/test_spend_gate_concurrency.py` launches real interpreters.
* **Global.** Every query sums the whole ledger — every campaign, every
  session, every run. A gate that reads its own counter *is* the defect.
* **Fail-closed, with no optional form.** No `enabled` flag, no environment
  variable, no `gate=None`. Missing lock primitive, unreadable policy,
  unwritable ledger, corrupt line, absent or expired reservation — every one
  refuses egress and raises. A test asserts the source contains no
  `os.environ`, no `getenv`, and no `enabled` switch.

**A reservation is a lease, not a lock.** It expires, so a session that dies
mid-campaign does not hold the pool's headroom until a human notices. Expiry
releases the **hold**; it never releases the **spend**, which is permanent and
keeps counting against the pool forever.

**`record` appends before it evaluates the caps, and appends even when it is
the record that breaches them.** Money that was spent is a fact. A gate that
refused to write down an over-budget spend would be a gate that makes the pool
look under budget. The breach raises *after* the fact is on disk.

---

## 3 · How each track plugs in

### The proxy package — already wired, nothing to do

`forward.forward()` takes a keyword-only `permit` with **no default**, so a
caller that forgot the gate gets a `TypeError` at the call site rather than a
line in the next incident report. Both proxies mint one per request and record
afterwards:

| proxy | what it charges | when |
|---|---|---|
| `env_proxy` | **actions** — one per outbound ARC HTTP request, which is the unit `spend_policy.json` defines and the one the 600 rpm limit is charged against | on both the normal and the exception path, against `permit.attempts_made`, so requests that happened are charged whether or not the call they belonged to succeeded |
| `model_proxy` | **dollars** — pre-authorised at `PriceTable.ceiling_for(body)` before the socket, settled at `PriceTable.cost(model, usage)` after | both. The pre-flight is what makes the ceiling a gate rather than a tripwire behind the money |

**A model request with no computable cost ceiling is refused, not sent** — 402
plus a `spend_gate_refused` incident. The Messages API requires `max_tokens`, so
the expensive half of the bill has a stated bound before the socket opens; a
model absent from `proxy/pricing/` has no bound at all, and an unbounded call is
one the pool cannot notice going by. This is also what closes the older hole
where an unknown model was silently free.

**A price is trusted only if the response's `usage` carries both halves of the
bill.** Otherwise the call is charged at its pre-flight ceiling and flagged
unpriced. A missing block, an empty one, a typo'd key, an SSE stream cut before
`message_delta` (which loses `output_tokens`, the expensive half at 5× the input
rate), or a `usage` value that makes `cost()` raise — all charge the ceiling
rather than zero. The rule is deliberately *not* "usd > 0": a model legitimately
priced at $0.00 with a complete usage block is priced, not blind.

`runner.run_game()` takes **one** reservation for the run and shares it with
both proxies, then releases it when the run ends. Declare a real budget and it
is used instead:

```python
run_game("ar25-0c556536", arm="theoria",
         campaign="phase3-variance-envelope",
         usd_cap=50.0, action_cap=2600)
```

The reservation id and the pool fingerprint land in the run's `run_start`
record, so a run that drew on a widened ceiling is identifiable afterwards.

### Any other caller — three lines

```python
from proxy.spend_gate import SpendGate

gate = SpendGate()
res = gate.reserve("phase3-variance-envelope", usd_cap=50.0, action_cap=2600)
try:
    gate.check(res, usd=0.0, actions=1)       # before the money leaves
    ...                                        # spend it
    gate.record(res, usd=0.0217, actions=1)    # after, always
finally:
    gate.release(res)
```

Module-level `reserve` / `check` / `record` / `release` / `totals` exist on a
default gate for callers that want the shorter form — same gate, same policy,
not a looser path.

### `baseline-arms` — the `campaign` field

`harness/ledger.py` now writes `campaign` on every `env_step` and `model_call`,
read from `BASELINE_ARMS_CAMPAIGN` (a property of the launch, like the shard) or
written as an explicit `"unknown"`. **Explicit, never omitted**: "we do not
know" and "the field is missing" look identical to a later reader, and only one
of them is honest.

History is **not** rewritten. `ledger.jsonl` is append-only and nothing in it is
*wrong* — it is silent, and the attribution is recoverable at read time:

```bash
python baseline-arms/harness/ledger.py     # the attribution report
```

The rule has exactly one source and no inference: a line's own `campaign` wins;
otherwise `run_id` is looked up in `out/campaign_cells.jsonl`; otherwise
`unknown`. Nothing is guessed from timestamps or from which games ran together —
that kind of reconstruction is what would make a spend figure unfalsifiable.

Measured on the ledger as it stands: **560 lines, 151 decidable from the cell
records, 409 undecidable and staying that way.**

### The monitor

```bash
python -m proxy.spend_gate            # human view
python -m proxy.spend_gate --json     # for a probe
```

The report names every campaign with money against it and flags concurrent live
reservations — which is exactly what INC-BA-003 could not see.

---

## 4 · Reading the refusals

| rule | what happened | what to do |
|---|---|---|
| `POOL_USD_CEILING` | the **global** total, across every campaign, would pass the ceiling | look at `by_campaign` in the error's totals; the money may not be yours |
| `POOL_ACTION_CEILING` | same, for outbound ARC requests | |
| `RESERVATION_USD_CAP` / `RESERVATION_ACTION_CAP` | your own claim is exhausted; the pool may be fine | reserve again, or reserve bigger next time |
| `UNPRICED_SPEND` | a model call could not be priced, so the dollar total is a lower bound | add the model to `proxy/pricing/`, then `price_unpriced()` |
| `NoReservation` | no claim, or it expired or was released | `reserve()`, or `renew()` a long campaign |
| `SpendGateUnavailable` | the gate could not do its job | **this is not a budget problem.** Fix the policy/ledger/lock and re-run |

**`UNPRICED_SPEND` is scoped, and that scoping is a bug fix rather than a
softening.** The first version refused *everything* on one unpriced call.
Wiring the gate to the egress path is what exposed it: one mock model call with
a name absent from `proxy/pricing/` stopped the *environment* proxy — which
spends no dollars at all — for every session sharing the pool, permanently,
because the ledger is append-only and nothing could take it back. A gate that
bricks the whole programme on a missing price-table row is not fail-closed; it
is a single point of failure wearing fail-closed's clothes. Now an unpriced call
blocks further **dollar** spend only, and `price_unpriced(res, usd=…,
resolves=…, reason=…)` is the way back — appended, never edited, and it refuses
a blank reason or a claim to resolve more blindness than exists.

---

## 5 · The threat model, at the size it actually holds

State it small, the way `LEDGER_FORMAT.md` had to after RED-15.

**What the gate stops:** a process spending money it has not claimed; two
sessions each believing they hold the whole budget; a spend nobody can attribute
to a campaign; an over-budget spend going unrecorded; a request opening a socket
without the gate having been consulted.

**One pool file, and where it lives.** A relative `ledger` in the policy
resolves against the **main checkout**, not the importing one. This is not a
detail: `proxy/var/` is gitignored and CLAUDE.md instructs every agent to work
in `.worktrees/<id>/`, so resolving against the importer gave **one pool per
worktree — 51 of them on this machine, each carrying the full ceiling, for
$10,959.90 of combined authorised exposure.** An adversarial pass found it, and
found that it was undetectable afterwards because the fingerprint recorded the
path *relative* to the checkout. `fingerprint()` now carries `ledger_abspath`.

**What it does not stop, and cannot:**

* **A soft ceiling under concurrency.** The read-sum-append is atomic; the
  interval between the pre-flight `check` and the `record` is not, and nothing
  on disk represents an in-flight request. Both proxies are threaded, so the
  action total can overshoot by up to `concurrency × max_attempts` — seven real
  requests were admitted into one action of headroom in an adversarial test. The
  dollar axis is bounded by the pre-flight ceiling. Closing the action axis
  means a reserve-commit-settle protocol, which is a redesign and is recorded as
  open in `runs/20260728T083000Z-s3/ADVERSARIAL.md`.
* **The POSIX stale-lock case is unverified.** Under `flock`, unlink-and-recreate
  is the classic bypass. Untestable on Windows; needs a Linux run.

* **An in-process attacker with import rights.** `_MINT` guards `SpendPermit`
  against constructing one by accident or by convenience — the failure that
  actually happened — not against code that can reach the module namespace as
  easily as you just did.
* **Code outside `proxy/` that talks to the network itself.** The gate is on
  the proxy's egress path. An arm that opens its own socket to `api.anthropic.com`
  is outside it — which is what the credential injection design already makes
  useless (an arm holds no key), but the gate is not the thing enforcing that.
* **Money spent outside these two upstreams.** Claude Code's own token usage
  for the sessions writing this code is not in the pool. `monitor/quota.py`
  watches the 5-hour window and is a different instrument for a different
  resource.
* **A human editing `spend_policy.json`.** That is the intended way to raise the
  ceiling. It is tracked, its sha256 is recorded in every run's `run_start`, and
  changing it is supposed to be a reviewable diff plus a `PARTNER_SYNC` line.
* **Deleting `proxy/var/spend_gate.jsonl`.** That resets the total, and the
  recovery is a human act — move it aside, record an incident, start a fresh
  pool — not something the module can defend against. It does *not* silently
  resurrect a live reservation: a handle whose claim is not on disk is refused.

---

## 6 · The pool

`proxy/spend_policy.json`, tracked, human-authored:

| field | value | why |
|---|---|---|
| `usd_ceiling` | 214.90 | not new authority: $50 (BUDGET_REPORT G1, approved as P-7) + $164.90 (the other session's stop-loss). Exactly the worst-case combined exposure INC-BA-003 computed and could not bound. This file is the first place their sum is a ceiling rather than an accident. |
| `action_ceiling` | 24,000 | outbound ARC requests, the combined figure in INC-BA-003's shared-resource table. **Not** the scorecard's successful-action count (BUDGET_REPORT 4.1). |
| `default_run_caps` | $5.00 / 600 actions | what a run that declares no budget gets. Deliberately small — not declaring should be inconvenient, not unlimited. $5 is under a tenth of the whole approved programme; 600 actions is one minute at the documented rate limit. |
| `default_ttl_seconds` | 3600 | how long a claim holds before a dead session stops blocking the pool |

Raising any of them is a human act: edit the file, say why in its `provenance`
block, and append the change to `PARTNER_SYNC.md`.

---

## 7 · Verifying it

```bash
cd proxy && bash verify_spend.sh
```

Offline: the gate's own suite, the multi-process fuzz against real interpreters,
the whole proxy suite with the gate on the egress path, a source-level check
that no bypass switch exists, and the `baseline-arms` attribution report.
