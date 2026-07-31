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
close spends **$0.00**, so the gate never applied. The gate is not a blanket
freeze — it stops spending, not accounting. Anyone else blocked on that pool
can still do zero-dollar repair work.

> **Correction (2026-07-29, RES-1 cycle 26, from an adversarial recheck).**
> This paragraph first read "**$0.00 and zero actions**". The second half was
> false, and it is the half that was doing the justifying. The pool's own
> ledger charges **one action per close request**: `proxy/var/spend_gate.jsonl`
> holds 424 close-spend records carrying 424 actions, three of them
> (seq 10588–10590) belonging to this salvage's own reservation. Under the
> pool's stated unit — one action = one outbound ARC HTTP request — "zero
> actions" was simply wrong.
>
> The conclusion survives, because it never rested on the action count:
> `UNPRICED_SPEND` keys on `usd > 0` and the dollars really were 0.00. But the
> stated reason was half wrong, and "the gate didn't stop me" is exactly the
> sentence that has to be right for the right reason. The ARC accounting total
> of 32 is unaffected either way — ARC bills successful non-RESET actions, not
> close requests, which is why these three never appeared in it.

## Two derivation bugs, both the same shape

A field filled from the strongest source the *code* knew about, rather than the
strongest source the *run* left behind.

**`prompt_id` → "P-8".** The campaign legs' manifests fell through to the `p8`
tag on the opened scorecard — the arm's generic tag, not the item. The
reservation's campaign string (`run_start.spend_gate.campaign`, shaped
`arm:prompt_id:game:slug`) named `A3-campaign-devpile` exactly, and had from
the moment the run started.

Added as a source ranked **below** `opaque.prompt_id` — which survived a round
trip through the API — and **above** the tag, which is a label rather than a
field. Parsed strictly: anything that is not exactly four non-empty
colon-separated fields is declined rather than guessed at, because field 1 of a
malformed string is still *a* string, and a lenient parser would have filed the
run under a game id while the manifest looked complete.

> **Correction and near-total reversal (2026-07-29, RES-1 cycle 26, from an
> adversarial recheck). This section was the ship-blocking one.** Three things
> in it were wrong; the paragraph above has been trimmed to what survives.
>
> **(1) "Both campaign legs died before closing a card" was false.**
> `20260729T105729Z-leg01` closed card `db32f0cd-…` (`total_actions: 5`) after
> eleven 404s and a 200. So it had `opaque.prompt_id` all along, that source
> outranks the campaign string, and the new source never fired for it — the
> leg is still filed under `P-8`. Only one of the two named legs was ever
> touched by the fix the section describes.
>
> **(2) The declared ranking was inverted on the one run it did fire for.**
> `prompt_id_of` searched only the run's *own* records for `opaque.prompt_id`,
> while `build()` twenty-nine lines later loaded the salvage that held that
> very card. So the strongest source was in hand and the weakest-but-one was
> used: `runs/20260729T004020Z-leg01/MANIFEST.json` said `A3-campaign-devpile`
> while `runs/20260729T004020Z-leg01-salvage/MANIFEST.json`, **holding the same
> card**, said `P-8`. Before the change the archive was consistently wrong;
> after it, inconsistent — which is harder to see and harder to correct.
>
> **(3) The new source was never evidence.** The campaign string's `prompt_id`
> field comes from `harness/run.py`'s module-level `PROMPT_ID`, exactly as
> hardcoded as the `p8` tag it was promoted above — and it was recorded in the
> manifest as "written by the reservation at run start", which is provenance
> language for a default. Re-deriving across the archive showed **7 runs would
> flip**, including `a3-gate-mock` and two desk-gate live proofs that were
> never campaign legs at all.
>
> **What was done.** The root cause was two contradictory constants in the live
> path: `inner/loop.py` stamped a literal `"P-8"` into every card's `opaque`
> while `harness/run.py` stamped `PROMPT_ID` into every campaign string. They
> are now one value, `Run.prompt_id`, and `inner/loop.py` reads it. The
> cross-run salvage is consulted for `opaque.prompt_id` **before** the campaign
> string, so the source declared strongest is the source actually used, and the
> campaign string's docstring now says in as many words that it is a
> declaration rather than an observation. `20260729T004020Z-leg01` regenerated
> to `P-8`, sourced to the salvage that closed its card; all three manifests in
> that family now agree.
>
> **What the archive says now is what it can prove**: at the time these runs
> ran, the arm declared itself `P-8` and the API echoed that back. It is not
> the item id, and the manifest no longer pretends to have observed one.

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

---

## Round 2 — what the adversarial recheck found, and what it did not

Two independent adversarial passes were run before this branch was pushed
(cycle 25's pass died with its session without writing anything down, so it was
redone in cycle 26 — a conclusion that exists only in a dead session's context
did not happen).

**The accounting half could not be refuted.** The reviewer recounted 32 and 23
by hand from the raw ledgers without using any arm code, reproduced 6→0 failed
checks against a clean `git archive` extraction of `8d42d523`, confirmed
`verify_provenance.py` is **byte-identical** across the range (no check was
loosened, no threshold or skip added), and confirmed the five regenerated
manifests differ by exactly +404 bytes each with `holds: true` / `surprises: 0`
unchanged as context lines. It also confirmed the two 9s are genuinely
independent: the ledger's own count of successful non-RESET `env_step`s, and
the API's `total_actions` returned verbatim in the close response
(`harness/arc.py:270-271` returns the parsed body; nothing is recomputed), with
third-party corroboration in the proxy's own gitignored `spend_gate.jsonl`
whose timestamps interleave correctly with the salvage's three attempts.

**The code half was refuted, and it was ship-blocking.** Both corrections are
recorded inline above, at the sections they falsify, rather than only here.

**Two things it found that are recorded but NOT fixed here:**

* `runs/20260729T004020Z-leg01/MANIFEST.json` carries
  `quota.billed_actions_from_scorecard: null` while the recovered count of 9
  lives only in `scorecard_recovered_by`. The reconciliation is an
  archive-level property (verifier check 4), not a per-manifest one, so a
  reader of the `quota` block alone still sees a null where the number is. The
  orphan flag was removed by this work; the number was not moved into the field
  whose job is to report it.
* `_scorecard_recovered_elsewhere` reports the *directory name* as `slug` and
  does not partition by `run_id`, so in a multi-run ledger
  (`runs/a3-gate-mock/ledger.jsonl` holds three) the pointer can name a
  directory rather than the run that closed the card. Not triggered by anything
  in the archive today.

**And one that is fixed:** `test_a_run_whose_card_was_salvaged_can_be_navigated_to_the_number`
could not go red under the regression its own docstring describes — removing
the pointer removed the only thing it looked at, so it skipped instead of
failing. It now treats "opened, never closed, no pointer, but the archive shows
the card closed" as the failure it is, and asserts it had a subject at all.
A new test, `test_a_salvaged_card_outranks_the_campaign_string`, pins the
inverted ranking directly: restoring the old value on disk makes it red with
"the archive contradicts itself about one card".
