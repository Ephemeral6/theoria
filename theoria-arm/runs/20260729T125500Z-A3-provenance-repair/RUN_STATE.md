# A3 · provenance repair — RES-1 cycle 24, 2026-07-29

The machine-readable account is `MANIFEST.json`; this file is the narrative.

## What was wrong

`origin/agent/a3-campaign-devpile` had been flagged `NEEDS-HUMAN` in
`monitor/ci/merge.log` after three merge attempts, all with the same verdict:
`verify gate red in theoria-arm (verify.py)`. The branch had also drifted far
enough from master to conflict.

Running the verifier in a pristine checkout of the merged tree gave **six**
failing checks. Five were bookkeeping. One was a real hole in the account.

## The real one

`runs/20260729T004020Z-leg01` spent **9 billed ARC actions**, then hit its
2000-command ceiling and died. It never closed its scorecard. That is the exact
failure `harness/spend.py:486` already predicted in prose:

> If the cap binds before the close, the proxy refuses, `_post` sees a
> transport failure, all 40 tries fail, and **the scorecard's score is lost**,
> because it exists only in a successful close response.

So the ledgers claimed 32 billed actions and the closed scorecards accounted
for 23. The 9-action gap was this one run, and card
`2ec0e679-6b92-475e-890c-a3f63d21e14c` was sitting open and undeclared.

**It was settled by measurement, not by adjusting the check.**
`armtools.salvage --slug 20260729T004020Z-leg01 --close` opened a proxy and
closed the card. The API's own count came back **9**, agreeing with the
ledger's count of successful non-RESET `env_step`s to the action. 23 + 9 = 32.

Worth recording why this was possible while the shared pool is still tripped:
the `UNPRICED_SPEND` condition (one unpriced call, seq 7418, still awaiting a
ruling from the monitor) refuses on `unpriced_calls and usd > 0`. A scorecard
close spends **$0.00 and zero actions**, so the gate never applied. The gate is
not a blanket freeze — it stops spending, not accounting. Anyone else blocked
on that pool can still do zero-dollar repair work.

## Two derivation bugs, both the same shape

A field filled from the strongest source the *code* knew about, rather than the
strongest source the *run* left behind.

**`prompt_id` → "P-8".** Both campaign legs died before closing a card, so the
two strongest sources in `backfill.prompt_id_of` had nothing and it fell
through to the `p8` tag on the opened scorecard — the arm's generic tag, not
the item. The reservation's campaign string
(`run_start.spend_gate.campaign`, shaped `arm:prompt_id:game:slug`) named
`A3-campaign-devpile` exactly, and had from the moment the run started.

Added as a source ranked **below** `opaque.prompt_id` — which survived a round
trip through the API — and **above** the tag, which is a label rather than a
field. Parsed strictly: anything that is not exactly four non-empty
colon-separated fields is declined rather than guessed at, because field 1 of a
malformed string is still *a* string, and a lenient parser would have filed the
run under a game id while the manifest looked complete.

**`scorecards_opened_and_never_closed` could not see a salvage.** It was
computed from the run's own ledger only, inside `build()` — and `build()` is
the path taken by every run that died before writing a manifest, which is
precisely the population a salvage exists for. So the manifest that most needed
to know about its salvage was the one structurally unable to.

`amend_payload()` already had the cross-run lookup
(`_scorecard_recovered_elsewhere`, matching `opaque.run_id`); `build()` now
uses it too. Before this, the leg's manifest asserted

> no run — this one or any other in the archive — ever closed it

while `20260729T004020Z-leg01-salvage` sat in the next directory holding the
API's count.

## The five that were merely stale

`20260728T012311Z-…-salvage`, `…-salvage2`, `20260728T014402Z-…-salvage`,
`20260728T015354Z-…-salvage`, `preflight-20260728T012031Z` all failed the
byte-for-byte re-derivation check. Not hand-edited and not changed on disk:
commit `e843a0fb` added four keys to `archive.constraint_8` and regenerated no
manifests. Regenerating them adds +404 bytes each and changes no verdict
(`surprises: 0`, `holds: true` before and after).

**A latent fragility this exposed, not fixed here.** Check 8 re-derives
*backfilled* manifests through `build()`, but *amended* ones only through
`amend_payload()`, which never rewrites existing keys. So any future change to
a derived block in `archive.py` will break exactly the backfilled subset and
leave the amended ones quietly inconsistent — the check cannot see the second
kind of staleness at all.

## The merge itself

Merging master surfaced two collisions worth naming.

* `tests/test_arm.py`, three sites: this branch added `spend_gate=`/
  `expect_pool=` (a private pool per test), master added `runs_root=
  FIXTURE_RUNS_DIR` (keep test runs out of the archive). Two dimensions of the
  same bug — pytest writing into shared production state — fixed independently
  by two sessions. Resolved as the **union**; neither side was wrong.
* `tests/test_bypass_negative.py` arrived from master while this branch's
  pytest hard gate was being written. All six of its tests built their `Run`
  through one `arm_run()` helper that passed no `spend_gate`, so every one
  reserved against the fleet's shared pool. The new gate turned that from an
  invisible billing leak into six red tests. Fixed at the helper.

## Verification

* `python verify.py` — green: 234 tests, one offline run, artefact self-check.
* `verify_provenance.run()` — 0 failed checks (was 6).
* `tests/test_provenance_derivation.py` — 12 new tests. The two invariant tests
  are stated over the whole archive rather than over one run, because the note
  they check makes a claim about the whole archive. Confirmed non-vacuous: the
  tree holds 15 provably-closed cards and 3 manifests carrying a recovery
  pointer.

## Still open

* The `$4.00` unpriced placeholder on the shared pool (seq 7418) is still
  awaiting the monitor's ruling. It no longer blocks A3.
* The g50t campaign leg can be resumed once that is settled.
