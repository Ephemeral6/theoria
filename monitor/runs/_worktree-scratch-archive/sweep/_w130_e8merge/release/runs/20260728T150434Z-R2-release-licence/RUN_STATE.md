# R2 · the licence filter, acted on rather than recorded

**Worker** W-1412 · **branch** `agent/r2-release-licence` · zero network, zero
API, zero model calls.

## What was already done, and what was not

`P5-release` had done more of this than the item assumes. `release/PLAN.md`
already states R2's requirement almost verbatim, `LICENCE_POSTURE.md` already
classifies every artefact class against `TERMS.md`, and `enumerate.py` already
carries the licence filter as a first-class stage — `MANIFEST.jsonl` classifies
all 1,950 tracked files and marks 19 `needs-written-permission` and 1
`not-releasable`.

**What did not exist was anything that acts on the classification.** A verdict
column is a judgement; nothing turned it into the set that ships. That gap is
the whole risk: on release day somebody tars a directory, and a classification
nobody acts on is a classification that gets silently overridden.

So deliverable (1) was built as the missing half — `release/bundle.py` —
and deliverable (3) from nothing. Deliverable (2) existed and was extended
rather than rewritten.

## What ships

```
ships:      1930 files
held back:  20 files
   needs-written-permission     19
   not-releasable                1
```

The 20 are the ARC interaction records: `baseline-arms`' shard ledgers and
probe logs, `arc-recon`'s recon ledger, `theoria-arm`'s four run ledgers, one
battery fixture, and `schema_traces/MANIFEST.json` (upstream, no licence at
all). Every one carries its sha256, the evidence for its verdict, and the
command that regenerates it.

Three properties, each preventing a specific way of publishing something we may
not:

* **allow-list, never deny-list** — an unclassified verdict is out by default;
* **what is withheld is enumerated, hashed and given a recipe** — an unmet
  openness target named is honest, the same target unmet by silent omission is
  not;
* **`--check` re-derives rather than trusts** — it caught its own staleness
  once during this pass, which is the only evidence that it works.

## The judgement call in the filter, stated

`releasable-flagged` **ships**. The first version of the filter shipped only
`releasable` and held back 166 files — including `CLAUDE.md` and
`PARTNER_SYNC.md`. That is not caution, it is a broken filter: class C is
*derived statistics*, files that mention ARC identifiers without carrying
environment payload, and `LICENCE_POSTURE.md` rules them releasable. The flag is
an instruction to a human reader, not a licence reservation.

The reason to get this right rather than err wide: **a filter that
over-withholds gets widened in a hurry by whoever is shipping**, and that is how
the under-withholding accident actually happens. The flag now travels with each
file into `BUNDLE.jsonl` instead.

## needs_human — not actioned, by instruction

Two entries, both in `LICENCE_POSTURE.md`:

1. **Apply, or decide not to apply, for republication permission** for the 20.
   `TERMS.md` §2 requires "express prior written permission" and the default is
   refusal. Asking is a commitment made in the project's name to a named
   counterparty — a human decision. **Blocks nothing**: the release ships today
   either way, one limitation heavier or lighter.
2. **Settle `battery/tests/fixtures/ledger_fixture.jsonl`.** The enumerator
   holds it at class B while flagging it as probably synthetic, because the file
   cannot prove its own provenance. A human who knows the generator wrote it
   reclassifies it in one line; until then it is withheld, which is the safe
   direction.

## Verify

```bash
python release/bundle.py --check     # 1930 ship, 20 held back, nothing stale
python -m pytest release/tests       # 5 passed
```

The test that matters checks the bundle against the **manifest's** verdicts
rather than the bundle's own copy of them — a bundle that mislabelled a row
would otherwise vouch for itself.
