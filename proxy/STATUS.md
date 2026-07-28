# `/proxy/` — status

**P-9 delivered: the frozen scorer, the canon guard, a red team that landed 29
attacks and now lands none, and the first real data point behind Phase 1's
bit-exact replay line.** 180 tests pass. Nothing here has spent a dollar or
reached the internet.

Previously: P-2 built the double proxy, the shared ledger format, and the checks
that make Phase 1's three closure properties falsifiable rather than asserted.

## Against P-9's acceptance list

| Required | State |
|---|---|
| frozen scorer wired in and frozen, version + hash into `run.json` | ✅ `proxy/scoring/`, `SCORING.md`. `frozen.json` holds the source hash; drift refuses to score; the fingerprint goes into `run_start` **and** `run.json`, and is verified before the game starts |
| each game scored the moment it ends, reconciled against the scorecard | ✅ `runner.run_game` calls `score_run` after `run_end`; the report lands in `proxy/var/scores/<run_id>.json` |
| a disagreement files an incident automatically | ✅ `score_mismatch`, and `score_unreconciled` when the obligation could not be discharged at all |
| absorb baseline's measured caliber (failed 400s unbilled, `total_actions` = successful actions) | ✅ and **extended**: 32/32 real scorecards, four games, two campaigns — `tests/fixtures/scorecard_corpus.json` |
| independent red team writes an attack set | ✅ 46 attacks in `tests/test_redteam.py`; `REDTEAM.md` is the report |
| the sealed test blocks all of them | ✅ **all 46 blocked**, no `xfail` markers left. 29 landed on first contact; each fix keeps the original finding as a comment on the test that closes it |
| the attack set stays resident in the suite | ✅ 44 tests, run on every `pytest` |
| proxy refuses a non-canonical field (F-16) | ✅ `canon.py`, consulted by the writer before serialisation and by `tools/validate_ledger.py` on read |
| migrator interface document for `baseline-arms` | ✅ `CANON_MIGRATION.md`; the migrator itself is `tools/upgrade_ledger.py`, the migration of the stock ledgers is P-12's |
| bit-exact replay spot check on the envelope's first game | ✅ `runs/p9-shell-harden/replay_spotcheck_ar25.json` — 16 sessions, 9 positions, 372 pairwise comparisons, zero disagreements |

Beyond the list: `LEDGER_FORMAT.md`'s two promised tools now exist
(`validate_ledger.py` §18, `upgrade_ledger.py` §7), `env_step` gained the
`response` field that made "complete record" true, and the mock now returns the
scorecard shape 32 real cards actually have.

## The replay spot check, stated at its real size

`baseline-arms`'s harness opens every session with a fixed probe sweep before
the model chooses anything, and it opened fourteen sessions on `ar25-0c556536`;
`arc-recon`'s determinism precheck ran the same opening on the same game in a
different campaign, on a different day, through a different harness. Sixteen
sessions with an identical opening are sixteen replays of that opening, and
they agree bit for bit on all nine positions.

What that is: cross-session, cross-campaign determinism **of the environment**,
on **one** game, for $0.

What it is not: evidence that these proxies reproduce a run. That needs a live
replay through `replay.py` and is still owed. The acceptance line asks for two
games; this is the first.

## What this does not yet do

* **It has never seen the live API.** Everything runs against `proxy/mock/`.
  One of the two surprises this file used to predict has been spent offline:
  the scorecard's shape is now known from 32 real cards and the mock returns it.
  The other — RESET's cross-session semantics — is still modelled optimistically.
* **The ledger is self-consistent, not authenticated (D-024).** The red team's
  sharpest finding has no local fix: every check is the file against itself, so
  a careful enough forger writing canonical records reconciles clean. P-9 raised
  the price — the frame hash must hash its own frames, `seq` must be dense and
  unique, one run is one arm, the card's totals must add up, the canon validator
  runs on the audit path — but a price is not a proof. The structural answer is
  a hash chain with the head published outside the file; it changes the envelope
  and so needs a version bump and three arms' agreement.
* **Three guard limits, stated rather than implied (D-022, D-023).** The
  value-join that catches an id split across two fields depends on key order;
  base64 is chased one level; a secret the writer has never seen and that does
  not look like one cannot be redacted — `LEDGER_FORMAT.md` §4 now says so
  instead of claiming otherwise.
* **`g50t-5849a774` is registered non-deterministic** in
  `arc-recon/data/precheck.json`. A replay failure on that game means the world,
  not the harness.
* **Streaming is buffered, not passed through live** (D-012).
* **Three-arm integration is not done.** Wiring `baseline-arms` in is
  configuration rather than code, and it has not been done.
* **Two things the Phase 2 battery still cannot get.** An independent review
  from the battery author's viewpoint closed four of its five stated gaps
  (`arm` and `game_id` on `model_call`, `pricing_ref` in place of a scalar
  cost, `level_boundary` as a recorded field) and left the fifth open: there is
  no turn index distinct from `step_idx`. It also found that `cost.py` never
  reads a record's own `pricing_ref`, so a stream priced under a different
  table yields plausible wrong dollars, and that nothing writes a **per-call**
  cost series — which is the shape the economy metric family is made of. Both
  are registered here and neither is fixed; they are the first items for the
  next pass on this surface.

## Where the credential lives

In `.env` at the repo root, read inside the proxies and nowhere else. It is not
in any tracked file here. Since P-9 the protection runs in both directions: a
credential cannot reach the ledger, and a credential an upstream reflects back
cannot reach the arm either — that leak used to leave the ledger clean, so it
was unrecorded as well as unstopped.
