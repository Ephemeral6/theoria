# `/proxy/` — run state

| | |
|---|---|
| prompt | **P-9** · shell hardening |
| branch | `agent/p9-shell-harden` |
| base commit | `edb3c37` |
| archive | `proxy/runs/p9-shell-harden/` (`MANIFEST.json`) |
| tests | 180 passed, 0 failed |
| cost | **$0.00** — zero API calls, zero model calls, zero network |

## What landed

1. **The frozen scorer** — `proxy/scoring/`, `SCORING.md`. Hashed, registered,
   named in every artefact, verified before a game starts, run the moment one
   ends. Calibrated against 32 real scorecards; it refuses to reimplement the
   ARC partial-credit percentage because no card in that corpus completed a
   level, so the formula is not determined by evidence we hold.
2. **The canon guard** — `proxy/canon.py`. F-16 executed: a non-canonical field
   cannot be written and cannot be accepted. Interface for `baseline-arms` in
   `CANON_MIGRATION.md`; `tools/upgrade_ledger.py` and
   `tools/validate_ledger.py` close the two gaps `LEDGER_FORMAT.md` had been
   promising since P-2.
3. **The red team** — 46 attacks by an independent context, 29 landed on first
   contact, all 46 blocked now, the suite resident. `REDTEAM.md` carries the
   audit as delivered plus what changed and what is still open.
4. **The replay spot check** — 16 sessions, two campaigns, two harnesses, nine
   positions, 372 pairwise comparisons, zero disagreements, on `ar25-0c556536`,
   for $0.

## What is owed after this

* a live run through the proxies — nothing here has met the real API;
* the second game for the replay-spot-check line, and a real replay through
  `replay.py`;
* record authentication (D-024) — a hash chain, which needs a version bump;
* the battery's turn axis, and `cost.py` reading each record's own
  `pricing_ref` plus a per-call cost series.

Reproduce every artefact in the archive with the four commands in
`runs/p9-shell-harden/MANIFEST.json` → `reproduce`.
