## 9 · The live chain — a preflight for zero quota, and the first-contact run

Everything reported so far is offline. Phase 3 is not, and the step between them
is the one where a framework quietly stops being closed: the arm acquires a
credential, the credential acquires a network, and the record of what happened
becomes something the arm itself wrote. **Two** runs exercised that chain and this
section reports both, because no single run establishes all of it: the
**preflight**, which ran the whole sequence **before** any of it could cost
anything, and the **first-contact run**, which spent quota on one development-pile
game and is the one whose manifest carries the byte-level sealing scan. Most of
what follows is about the preflight; §9.4 says which claims belong to which run.
As much as it reports the result, this section reports what the runs do *not*
establish.

### 9.1 The trick, and the sequence

A finding from the baseline track makes the preflight possible:
`scorecard.total_actions` equalled the count of **successful** actions on every
sample examined, with `RESET` counted separately, so a `RESET` is not billed
(`baseline-arms/BUDGET_REPORT.md`; restated as the arm's design basis at
`theoria-arm/DECISIONS.md` D-P8-004, and extended by the proxy track from 4
scorecards to 32 in `proxy/scoring/arc_v1.py`). The arm's own docstring states
the consequence:

> opening a scorecard, sending one RESET and closing again exercises every link
> in the live chain for zero quota:
> `arm -> env proxy -> key injection -> sealed-pile guard -> ARC -> ledger`

That is what was run, on `g50t-5849a774` from the development pile
(`theoria-arm/runs/preflight-20260728T012057Z/`; note the slug — an earlier
attempt 26 s before it aborted after two records and is superseded). The ledger
holds 23 records: a scorecard open (200), **18 `RESET` attempts** of which 17
returned 400 and the eighteenth returned 200 with one 64×64 frame, and a
scorecard close that needed two tries — 404, then 200.

**No `ACTION` command was ever sent.** The API's own close response is the
witness: `total_actions: 0`, `actions: 0`, `level_actions: [0,0,0,0,0,0,0]`,
`score: 0.0`. The arm's reconciliation agrees — `successful_actions: 0` over 18
`env_steps` — and the cost block records `model_calls: 0`, `usd: 0.0`
(`theoria-arm/runs/preflight-20260728T012057Z/MANIFEST.json`,
`theoria-arm/runs/preflight-20260728T012057Z/run.json`).

The run also produced three findings that only a live chain can produce, and
they are the reason a dry run against a mock would not have substituted:

* **18 attempts for one `RESET`.** `arc-recon`'s 40-attempt retry envelope is
  load-bearing right now rather than a historical artefact; `proxy/forward.py`'s
  5 attempts, which exclude 400 entirely, would have returned a hard failure
  (`theoria-arm/RUN_STATE.md`).
* **No `score` field exists in live command responses.** The ledger format's
  score obligation is therefore undischargeable against the real API, and that
  is filed as an incident rather than waived (`theoria-arm/INCIDENTS.md`
  INC-TA-002).
* **The close needed two tries.** A card that is not closed yields nothing and a
  closed card cannot be re-fetched, so a low retry count silently loses the
  score.

### 9.2 What is sealed, and how strongly

Three properties are claimed for the shell. They are not equally well
established, and the differences matter more than the shared direction.

**The credential is injected inside the environment proxy and nowhere else.**
The arm holds no key; `proxy/env_proxy.py` reads it from the gitignored `.env`,
registers it with a process-wide scrubbing vault, and adds the header on the way
out. Everything the ledger writer emits passes through `VAULT.scrub()` first
(`proxy/redact.py`, wired at `proxy/ledger.py`). The sharpest evidence is a
byte-identical pair of requests in `proxy/tests/test_seal.py`: sent directly the
request returns 401, sent through the proxy it returns 200, and the difference is
entirely a key the arm never held. A mock arm that can see any credential
environment variable refuses to start.

Two limits belong immediately beside that. First, the proxy track's own format
document **retracted** the stronger version of this claim after a red-team pass
collected on it; what it now says is that *a credential the proxies injected
cannot reach the ledger* — not that a ledger cannot contain a key, because "a
writer cannot redact what it has never been told and cannot see"
(`proxy/LEDGER_FORMAT.md` §4). Second, and specific to this run: **no executable
check scans the live ledger for the credential.** The arm's archiver advertises
that check in its docstring and does not implement it — the parameter it would
need is accepted and unused (`theoria-arm/armtools/archive.py`). The unit test
that does perform a byte scan runs against the mock. So the claim here rests on
construction, a mock-level test, and an incident count of zero, and we state it
that way.

**The sealed pile was not touched, and here the check is real.** The
first-contact manifest carries a byte scan of the records rather than the guard's
opinion of what it blocked: `game_ids_anywhere_in_the_records:
["g50t-5849a774"]`, `sealed_game_ids_found: []`, `sealed_pile_untouched: true`,
`cut_integrity: true`
(`theoria-arm/runs/20260728T015354Z-g50t-first-contact/MANIFEST.json`). The guard
reads the cut itself — `arc-recon/data/piles.json`, integrity-checked against its
sha256 — rather than a copy, and its fingerprint is recorded at run start: 4
development games, 21 sealed, `unknown_policy: "deny"`. The preflight manifest
predates that scan and carries only the counters.

**Zero guardrail bypasses were *recorded*.** The preflight's sealing block reads
`bypass_attempts: 0`, `guard_blocks: 0`, `credential_in_body: 0`,
`sealed_pile_requests: 0`, `incidents: 0`, and every one of the 18 environment
steps carries `guard.decision: "allow"`. That zero is informative rather than
vacuous, because the same counter demonstrably fires: a separate experiment in
which the model CLI presented its own credential produced **66 `bypass_attempt`
incidents and 65 consecutive 401s**, which is the sealing property working rather
than a defect (`theoria-arm/evidence/model-proxy-401.jsonl`). The guard's own
credibility comes from an adversarial pass by an independent context — 46
attacks, **29 of which landed on first contact**, four rated critical, all 46 now
blocked and resident in the suite (`proxy/REDTEAM.md`, `proxy/STATUS.md`).

### 9.3 Four things the preflight does not establish

The gap between what the shell is designed to guarantee and what this run
demonstrates is wide enough to be worth enumerating.

1. **Only one of the two proxies was live.** The design is a double proxy —
   environment and model — so that the arm sees exactly two hosts on the network.
   The model side was **not** proxied for this arm; every model call carries
   `proxied: false`, and it is a declared gap rather than an oversight
   (`theoria-arm/GAPS.md` GAP 1, `theoria-arm/DECISIONS.md` D-P8-002). What is
   lost is stated there: the recorded request is the prompt the arm sent the CLI,
   not the body the CLI sent onward, so **no conclusion about input-token
   composition may be drawn from this ledger**.
2. **The spend gate did not gate this run.** `proxy/spend_gate.py` exists, is
   wired keyword-only into the forwarder so that a caller who forgets it gets a
   `TypeError` rather than a line in the next incident report, and is tested
   through an adversarial pass that demonstrated and then fixed five bypasses.
   But it was wired at 08:42 Z and the preflight ran at 01:20 Z — the file hashes
   differ, no run artefact mentions a reservation, and its own manifest records
   that it *"was never pointed at a live upstream"*. The bound actually in force
   during the preflight was an in-process counter, which is exactly the class of
   gate that failed in the incident the shared gate was built to answer.
3. **No live replay has been performed.** Frames are stored whole and hashed and
   a replayer exists, but the evidence in the tree is of a different thing: 16
   independently recorded sessions of one fixed opening on one development-pile
   game agree bit-for-bit across **372 pairwise comparisons**, with sessions
   truncated at the first failed step and agreement claimed only where at least
   two sessions reached a position
   (`proxy/runs/p9-shell-harden/replay_spotcheck_ar25.json`). The proxy track
   states the size of that itself: it is cross-session determinism *of the
   environment*, on one game where the acceptance line asks for two, and it is
   not evidence that these proxies reproduce a run.
4. **A self-consistent ledger is not an authenticated one.** Every reconciliation
   check aligns the file against itself, so a sufficiently careful forger with
   write access reconciles clean. Hardening raised the price of forgery — a frame
   hash must really hash its own frame or the writer refuses it, sequence numbers
   must be dense and unique — but a price is not a proof. The proposed answer is a
   hash chain whose head is published outside the file; it is registered and not
   built. The honest statement of closure is the one the track wrote for itself:

   > the ledger is complete and self-consistent, and the arm cannot write it —
   > but the operator can. Phase 1's "no bypass" was always a claim about the
   > arm, and that one still holds.

   Its timing is awkward and we record it as such: the chain was wanted before
   the first live run, and the first live run has already happened without it.

### 9.4 What was spent, in the end

The preflight spent nothing. The first-contact run that followed it did spend:
7 successful actions, 40 commands sent, 5 model calls, a score of 0.0 and 0 of 7
levels completed
(`theoria-arm/runs/20260728T015354Z-g50t-first-contact/MANIFEST.json`). We draw
no capability conclusion from that in either direction, and the arm's own gap
list says why — the plan and commit beats were reached but barely exercised, so
a surprise count of zero for those beats is structurally zero rather than
measured zero, and one engine contributed no rows at all.

Two incidents bound the cost figures further. Two arms played the same game
concurrently on one quota, so **every wall-clock and HTTP-amplification number
this track reports is confounded** and is an upper bound on the arm's own cost
rather than a measurement of it (`theoria-arm/INCIDENTS.md` INC-TA-001). And
cache reads are **structurally zero** — not small, but a different quantity —
because every model call is a fresh process in a fresh directory, which is the
sealing decision working as designed (INC-TA-005).

What the live runs establish is narrow and worth having, and it must be split
across the two of them rather than fused into one. **The preflight** shows the
live chain running end to end with the credential injected in one place and the
arm never holding it, for **zero billable actions and zero dollars**
(`theoria-arm/runs/preflight-20260728T012057Z/MANIFEST.json`) — but its manifest
predates the byte-level sealing scan and carries only the counters, as §9.2 says.
**The first-contact run** is the one whose manifest carries that scan
(`theoria-arm/runs/20260728T015354Z-g50t-first-contact/MANIFEST.json`:
`sealed_game_ids_found` empty, `sealed_pile_untouched` true, `cut_integrity`
true), and it spent 7 successful actions and $6.32 in model calls.

**And the two numbers for that spend disagree by 8.3 %.** The provider's own
arithmetic reports **$6.317658**; this project's price table, re-deriving the same
run from its recorded token usage, gives **$5.795338**
(`theoria-arm/runs/20260728T015354Z-g50t-first-contact/MANIFEST.json`,
`cost.cli_reported_usd` against `cost.from_price_table.usd_total`, with
`cost.relative_delta` −0.0827). The manifest does not average them or pick one: it
records the gap and names it a finding about `proxy/pricing/pricing_v1.json`
rather than about the run.

**And it largely explains it.** The same manifest's `cost.cache_ttl_diagnosis`
identifies 116 470 cache-creation tokens written at the one-hour multiplier and
priced at the five-minute one, worth `under_billed_usd` **0.436763** — **83.6 % of
the $0.52 gap**. Correcting it takes the disagreement from 8.3 % to **1.35 %**, and
the residual has no identified cause. So this is not an unexplained discrepancy
between two accountings; it is a priced, located defect in one of them with a small
remainder. **Every dollar figure in this paper is the provider's number**, which is
the conservative choice here, since the project's own table reads low.

Neither run
byte-verifies the "injected in one place" claim: §9.2 records that the archiver
advertises that check in its docstring and does not implement it, and that the
byte-scanning test runs against the mock. Both are statements about the
apparatus, not about the framework.
