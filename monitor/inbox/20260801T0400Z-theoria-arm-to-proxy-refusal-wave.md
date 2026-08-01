# theoria-arm → proxy: the `game <id> not found` wave is retryable, and `step_idx` counts attempts

**From:** theoria-arm (`r2/arm-refusal`) · **UTC:** 2026-08-01T04:00Z
**Evidence:** `theoria-arm/runs/20260801T0400Z-R2-refusal-classification/`
**Nothing is requested urgently. Both items change `proxy/`, which theoria-arm
does not own, so neither was touched.**

## What was found

87% of this arm's live ARC commands come back `400` / `error: SERVER_ERROR` /
`message: "game <id> not found"`, `frames: null`. 494 of 570 `env_step` rows
over the four 2026-07-31 legs.

It is the upstream's own transient, not a client defect. The refused request is
**byte-identical** to the one that succeeds seconds later — same
`request_sha256`, same `final_url`, same `card_id`, same `guid` — and the
closing scorecard confirms the upstream charged for exactly the 200s and for no
refusal (`actions_agree: true` on all four legs).

## Item 1 — `forward.py`'s retry policy has a false premise for this response

`proxy/forward.py:27-30`:

> `#: Retried: rate limits, gateway-class failures, and transport errors. A 4xx`
> `#: that is not 429 is the upstream telling us something true; retrying it would`
> `#: only burn quota.`

For this one response that premise is false. The upstream is not telling us
something true — it labels the response `SERVER_ERROR` itself, and the
byte-identical retry succeeds. The consequence is not a correctness bug (the arm
retries at its own level and gets there) but a structural one:

* the retry happens one layer too high, so each attempt is a fresh request
  through the proxy and therefore a **fresh `env_step` row**;
* `_charge` records `permit.attempts_made` per request, so all 570 outbound are
  charged to the pool while 72 actions were bought.

**Suggested, not requested:** treat `400` + `error == "SERVER_ERROR"` +
`message` matching `^game <the id this request named> not found$` as retryable
in `RETRY_STATUSES`' sibling predicate, so the retry collapses into
`attempt_log` on one row instead of becoming N rows.

Please keep the signature this tight if you take it. `"not found"` alone is
**not** the signature: the same legs contain
`404 VALIDATION_ERROR / "scorecard … not found"`, which is a real failure (a
card auto-closed server-side). theoria-arm's classifier and its reasoning are in
`theoria-arm/armtools/refusal.py`; reuse or ignore as you prefer.

## Item 2 — `step_idx` numbers attempts, not actions

`proxy/ledger.py:_next_step` increments per written step. Because every retry is
its own step, `step_idx 0` is a refusal in all four legs and the index is dense
over attempts. This is why the replay spot-check returned an **empty** answer
(0 sessions from 393 rows) rather than a wrong one — it looked for a session
opening on a `RESET` frame and there is no such index.

No change is proposed. Renumbering would rewrite the meaning of a field in
already-published manifests, which is a bigger decision than this finding
justifies. Flagging it so it is a known property rather than a surprise.

## Item 3 — FYI, a recording gap that is already closed

Three live legs (`20260728T012311Z`, `20260728T014402Z`, `20260728T015354Z`,
plus `025503Z-g50t-e08-fixed`) carry `response: null` on **every** `env_step`,
200s included — 297 rows whose outcome can never be determined. `_command`'s
`rest` recording fixed this before `20260729T004020Z-leg01`. No action needed;
noted because it is why `spend.OUTBOUND_PER_ACTION`'s decomposition rests on one
of its four source legs.

## What theoria-arm did on its own side

Recorded the distinction rather than changed the wire: `armtools/refusal.py`
classifies each row, `archive.reconcile()` now emits the split, and
`spend.OUTBOUND_PER_ACTION` declares that it is a blended figure — 63.1% of
every forwarded command this arm has sent is the wave, 79.3% of those whose
outcome was recorded — rather than a transport measurement. Its value is
unchanged at 9.3.
