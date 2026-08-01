# R2 — the 87% refusal wave is the upstream, and the defect is the record

**Cell:** R2-refusal-classification · **Branch:** `r2/arm-refusal` · offline only,
no live run, no spend.

## The question

494 of 570 live `env_step` rows across the four 2026-07-31 legs are
`400 SERVER_ERROR` with detail `game <id> not found`, `frames: null`,
`n_frames: 0`. Is the arm sending something wrong, or is this expected?

## The answer: expected, and nothing on this side causes it

The decisive record is that **the refused request is byte-identical to the one
that succeeds**. On `20260731T1240Z-A3-level2-carried` all eleven `RESET` rows
carry `request_sha256: sha256:726d8f3e…`, the same `final_url`, the same
`card_id`. Ten are `400`; the eleventh is `200` and returns a frame and a
`guid`.

Four hypotheses, each killed by a record rather than by argument:

| hypothesis | verdict | the record that settles it |
|---|---|---|
| game id malformed | no | the closing scorecard lists `g50t-5849a774` with `level_count: 7`, a `guid` and 5 actions |
| sent before RESET | no | `step_idx 0` *is* a `RESET`, and it is refused |
| session / scorecard token missing | no | refusals after `step_idx 10` carry the same `guid` as the successes interleaved with them |
| race with scorecard open | no | `scorecard/open` returned `200` two seconds before the first refusal; refusals continue for five more minutes |

The refusal rate is 0.900 / 0.859 / 0.855 / 0.876 across two games and 4.5
hours — too stable for a flaky network, too partial for a malformed client. The
API's own error name is `SERVER_ERROR`. `harness/arc.py:_retryable` already
retries it and the retry works; that is why 72 actions landed.

So this is case 3 of the ticket: **documented-normal recorded identically to a
real failure.** The wire behaviour is correct and is left alone.

## What was actually broken

* `proxy/ledger.py:_next_step` gives every refused attempt its own `step_idx`,
  so `step_idx` numbers attempts, not actions, and `step_idx 0` is a refusal in
  all four legs. That is why the replay spot-check returned **empty** (0 of 393
  rows) rather than wrong.
* `archive.reconcile()` averaged `http_amplification` over an undifferentiated
  mass of non-200 rows: weather and breakage produced the same number.
* `spend.OUTBOUND_PER_ACTION = 9.3` inherited a numerator that is mostly
  weather while being consumed as a statement about this arm's transport. Of
  its 251 requests, 27 bought an action, 86 are the wave, and 138 are
  `unrecorded` — 76% of the classifiable remainder is weather.

## Cost

| leg | wall s | s inside refusals | share | refusals | actions | refusals/action |
|---|---:|---:|---:|---:|---:|---:|
| 1240Z-level2-carried | 290 | 96 | 33.1% | 54 | 5 | 10.80 |
| 1310Z-level2-carried-r2 | 3319 | 101 | 3.0% | 85 | 13 | 6.54 |
| 1430Z-level2-carried-r3 | 5121 | 228 | 4.5% | 200 | 33 | 6.06 |
| 1500Z-sk48-carried-l1 | 6318 | 170 | 2.7% | 155 | 21 | 7.38 |
| **total** | **15048** | **595** | **4.0%** | **494** | **72** | **6.86** |

**The wave is not a wall-clock problem** — 4.0% of elapsed time; LLM think time
dominates (~10 min between command bursts). It is a *reservation* problem: at
9.3 a 300-action leg reserves `ceil(300 × 9.3 × 2.0) + 36 = 5616` outbound,
where the productive traffic needs 685. That 8.2× hold is taken from a shared
pool for the length of the lease.

The arm's own `http_amplification` of 12.0 is attempts per successful ACTION
and is already flagged `http_amplification_is_really_attempts: true`. The
transport ratio, which only the proxy ledger can compute, is 7.917 pooled.

**No measurement of arm capability is perturbed.** `actions_agree` is true on
all four legs: the closed scorecard counted 5 / 13 / 33 / 21 actions, exactly
the 200s. The upstream charged for no refusal.

## Built

* `armtools/refusal.py` — the signature, a total classifier over six outcomes,
  outbound accounting in the pool's own unit, and
  `derive_outbound_per_action()`.
* `armtools/archive.py:reconcile()` — emits `outcomes` and `outbound` when
  asked (`outcomes=True`). `http_amplification` is unchanged; this is an
  addition, not a redefinition.
* `harness/spend.py` — `OUTBOUND_PER_ACTION_REGIME = "blended"` and
  `OUTBOUND_PER_ACTION_DECOMPOSITION`, both carried into every plan's
  `arithmetic`.
* `tests/test_refusal_classification.py` — 22 tests.

**The value 9.3 is deliberately not moved.** Under-reserving cost
`20260729T004020Z-leg01` its run; an unspent hold is returned by `release()`.
What changed is that the constant now declares which regime it measures and a
test re-derives it from the ledgers.

## Residual gaps, stated honestly

1. **`upstream_failure` is 0 across every ledger this arm has.** The classifier
   has never said "real failure" on real data. Its ability to say no rests on
   synthetic mutations of real rows (and was verified by breaking the
   classifier and watching 8 tests fail). A genuinely-broken live leg has not
   been observed.
2. **Three of the four legs behind 9.3 cannot be decomposed at all.** They
   predate the proxy recording response bodies — `response: null` on every row,
   200s included — so 149 of the constant's 251 outbound requests are
   unattributable. They are counted as `unrecorded`, not as failures. The
   constant is defensible; its decomposition rests on one of its four legs.
3. **The fix does not stop the retry storm**, because the fix that would is in
   `proxy/`, which is read-only from here. Filed to `monitor/inbox/`.
4. **`step_idx` still counts attempts.** Renumbering it is a proxy-side ledger
   change and would rewrite the meaning of a field in published manifests; it
   is described in the inbox item, not done here.
5. The 07-31 refusal rate is measured on two games only (`g50t`, `sk48`), both
   development pile.
6. **The split is not in `MANIFEST.json`, and deliberately so.** The first cut
   extended `reconcile()` unconditionally, and `verify_provenance` check 9 went
   red: it re-derives every published manifest and compares byte for byte, and
   manifests embed `reconciliation: reconcile(...)`, so 25 of them stopped
   reproducing. That is the check working. Putting the split into manifests
   means re-deriving and amending ~25 records of real spend — a migration, and
   not something to smuggle in under a bug fix. `outcomes=True` is available for
   callers; the archive's own derivation is untouched.
