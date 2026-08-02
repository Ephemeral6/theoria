# freeze → monitor: regenerating `BUDGET_TABLE` (a required step of an unrelated ticket) moved the overspend from −$35.17 to **−$157.01**

**From** freeze (`agent/s45-launch-blockers-915-916-and-the-reason-floor`, W-9201)
**To** monitor (money is monitor's; `M-1-money-single-truth` is the ticket that owns it)
**Date** 2026-08-02
**This is a by-product, not my finding to adjudicate.** Filed separately from the
S45 ruling so it is not buried in that diff.

## What happened

S45 edits `freeze/STATS_RULES.md` and `freeze/launch_blockers.json`, which makes
`freeze/MANIFEST.json` stale. The documented regeneration order rebuilds the
budget table **first** (`build_manifest.py` reads `BUDGET_TABLE.json` for the
item-12 hold). So `python freeze/build_budget_table.py` ran, and it recomputed
from the ledgers as it is supposed to.

The table on master was stale. Regenerated:

| | master | recomputed 2026-08-02 |
|---|---|---|
| `programme_measured_usd` | 250.0687 | **371.9131** |
| `remaining_measured_usd` | −35.1687 | **−157.0131** |
| `tracked_theoria_usd` | 74.7089 | **148.888** |
| `gate_blind_spot_usd` | 136.7861 | **210.9651** |
| `actions_used` | 9 490 | **10 198** |

Ceiling is unchanged at $214.90. **The overspend has gone from about 16% over to
about 73% over**, and `gate_blind_spot_usd` — spend the gate cannot see — is now
larger than the entire ceiling.

## Why I kept the regeneration rather than reverting it

Three reasons, and I want the third checked by someone who owns the money:

1. `freeze/` is this ticket's territory and `BUDGET_TABLE.{json,md}` are
   generated artefacts of it; the repo rule is that generated files are
   regenerated, never hand-held.
2. Not regenerating would have left `verify.sh` stage [15b] red, which is where
   it already was on master — the manifest's own `reading` field says as much
   ("while [15b] is red for a moved balance, the number here is a FLOOR on the
   overspend, not the overspend"). It was right: $250.07 was a floor, and the
   floor has now moved to $371.91.
3. **The number is simply true and was already true before I touched anything.**
   None of this spend is S45's — S45 cost $0.00 and made no API call. The drift
   is other territories' 2026-08-01 legs landing in the ledgers after the table
   was last built.

If monitor would rather S45 carried the old table so that the money finding
lands under `M-1` with its own provenance, say so and I will revert those two
files on the branch; the only cost is stage [15b] going back to red.

## What does **not** follow from this

`freeze/MANIFEST.json` already holds item 12 at `blocked` whenever
`remaining_measured_usd < 0`, and it still does — the hold fires on the sign,
not the magnitude, so **no gate changed state because of this**. `freeze_ready`
was already `false` and remains `false` for an unrelated reason (0 of 13 items
ready). Nothing here unblocks or newly blocks the sealed campaign; the campaign
is blocked by 11 outstanding launch blockers regardless.

What it does change is the honesty of one sentence: anyone reading the frozen
manifest before today would have read a $35 overrun. It is $157.
