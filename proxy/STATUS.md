# `/proxy/` — status

**S9 delivered: the canon is additive-safe, the five fields P-8 was already
writing are canonical, and a change that narrows the shared contract can no
longer arrive on another track unannounced.** 295 tests pass. Nothing here has
spent a dollar or reached the internet.

Previously: P-9 delivered the frozen scorer, the canon guard, a red team that
landed 29 attacks and now lands none, and the first real data point behind
Phase 1's bit-exact replay line. P-2 built the double proxy, the shared ledger
format, and the checks that make Phase 1's three closure properties falsifiable
rather than asserted.

## S9 — the closure that cost $2.695

`LEDGER_FORMAT.md` §4 closed `model_call`'s field set **after** P-8 began
writing `beat`/`label`/`transport`/`proxied`/`proxy_gap` on that record. Arms
import `proxy/` as a library, so the closure arrived on a commit the `theoria`
arm had never touched. Its first live desk call was refused at serialisation
after the provider had been paid; the reply was discarded and the ledger held
zero `model_call` records (INC-TA-006, reported by W-1521 and fixed on its side).

Three things changed here, and the reasons are D-030 and D-031:

| | |
|---|---|
| `canon.py` is **additive-safe** | an unlisted field on `env_step`/`model_call` is warned about (`UnknownField`, tallied in `Ledger.unknown_fields`) and **written**. A writer that runs after the money is spent may not refuse — a refusal cannot un-spend it, only destroy the evidence. What stays refused is what is *wrong* rather than unknown: v0 spellings, dollar figures (§5), caller-set envelope fields, missing required fields, corrupting types |
| the five fields are **canonical** | §4 lists them, with what each is for. `beat` is the one that matters most: it is why Theoria.md constraint 8 is checkable *from the ledger* rather than asserted in prose |
| tightenings must be **announced** | `CONTRACT_CHANGES.md` is the procedure; `canon_contract.json` pins `canon.describe()` plus `ledger.py`'s three registries; `python -m proxy.tools.contract` diffs and labels each delta `additive`/`tightening`; `tests/test_contract_changes.py` fails the suite when they disagree. **The fingerprint is the authority and the classifier only the explanation** — an unmodelled delta reads as a tightening, because "found no tightening" and "understood the change" are different statements and only the second is a clearance |

The read side moved with it: `validate_ledger.py` reports an unlisted field as a
**notice** and leaves the verdict alone, because the frozen scorer calls it from
S-12 and a scorer that fails a run over a field it could ignore is the same
mistake one direction over.

```bash
cd proxy && bash verify_contract.sh          # the S9 green light, offline
python -m proxy.tools.contract --fingerprint # the line an importing track pins
```

**For a track that imports `proxy/`:** put that fingerprint in your run manifest
and *diff it between runs*. `proxy/` can publish it; only you know which two
runs were supposed to be comparable. A pin that is never compared documents an
incident afterwards instead of preventing one.

Two things an adversarial review of this change caught, kept here because both
are the same mistake wearing different clothes:

* **The warning was itself a refusal.** `warnings.warn` raises whenever the
  ambient filter says `error`, and `UnknownField` is an `Exception` — so under
  `python -W error` the writer raised, the arm's `except Exception` said "the
  desk failed", and INC-TA-006 was rebuilt out of the warning meant to replace
  it. The tally now comes first and cannot raise; the warning is emitted
  defensively. `verify_contract.sh` runs a real subprocess under a real
  `-W error` to keep it that way.
* **The frozen scorer was only half frozen.** S-12 delegates to
  `tools/validate_ledger.py`, which consults `canon.py`, so this change moved
  what the scorer returns while `arc_v1.py` hashed exactly as before and
  `verify_frozen()` reported all clear. `frozen.json`'s `arc_v1` entry now
  carries `depends_on` and the check covers it. Freezing the source of a rule
  whose behaviour lives partly in its imports is a half-freeze, and a
  half-freeze reads as a whole one.

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
| proxy refuses a non-canonical field (F-16) | ✅ `canon.py`, consulted by the writer before serialisation and by `tools/validate_ledger.py` on read. **Narrowed by S9**: it refuses a spelling the format *forbids*; a field the format does not mention is warned about and kept (D-030) |
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
  a hash chain with the head published outside the file, proposed in
  `monitor/inbox/20260728T2200Z-proxy-ledger-hash-chain.md`. It is **cheaper
  than D-024 first said**: with `prev` optional the format stays at `v1.0`, so
  no version bump and no coordination with the other arms — the compulsion
  comes from the published head, not from the field being required. The
  deadline is the first live run rather than Phase 4, because a chain is
  evidence only for records written after it exists.
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
* **The contract detector sees the pinned contract and nothing else.** The rule
  in `CONTRACT_CHANGES.md` §2 — widening is free, narrowing is breaking —
  applies by its own terms to the spend gate's protocol, the guard's verdict
  semantics and `cost.py`'s pricing tables, and **no code checks any of them**.
  Nor can any test verify that an announcement was written or that the wait
  happened; the board is a board, not a scheduler. Widening the pin is the
  obvious next thing and is not done.
* **§5's dollar ban is a list of names, not a price detector.** `usd_spent` is
  not on the list and is written. That was already true of auxiliary payloads,
  which have always been open; what S9 changed is that the two shapes now
  behave like them. Recorded as a test so it cannot be read as a guarantee.
* **One pinned P-9 artefact no longer reproduces.** `validate_file`'s report
  gained a `notices` key, so the output hashed in
  `runs/p9-shell-harden/MANIFEST.json` differs. Nothing recomputes
  `proxy/runs/*` hashes, so this would have failed silently and only for
  whoever tried to reproduce P-9. Left as documented drift: rewriting a past
  run's manifest to match a later format is the manoeuvre `CANON_MIGRATION.md`
  §7 declines for the same reason.

## Where the credential lives

In `.env` at the repo root, read inside the proxies and nowhere else. It is not
in any tracked file here. Since P-9 the protection runs in both directions: a
credential cannot reach the ledger, and a credential an upstream reflects back
cannot reach the arm either — that leak used to leave the ledger clean, so it
was unrecorded as well as unstopped.
