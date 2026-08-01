# BOARDREFILL — the board was empty and today's evidence had nowhere to go

Territory: `monitor`. Branch `z/monitor-board-refill`, base commit `e8345aff`.
Offline throughout: no ARC call, no desk call, no round, no leg, no network.
No sealed-pile game id appears in anything written here.

## What the board looked like

`python board.py list` at base commit: **4 available** (A18, A19, A20, A21),
0 claimed, 164 done. Four items, all authored in the same closeout push
(`monitor/runs/2026-08-01T023624Z-P1PUSH4`), none of them touching a single
thing measured today. Meanwhile eight cross-territory asks sat in
`monitor/inbox/` unclaimed and R2 landed a measurement that reclassifies the
whole probe programme. The queue existed; it was in a chat log and in nine
Markdown files, not on the board.

## What was written

Ten items, every one traced to a measurement or a filed ask that exists today.
Nothing was invented; the sourcing column below is the point of the exercise.

| id | pri | territory | traces to |
|---|---|---|---|
| A22-r3-generated-frontier-round | 1 | theoria-arm | `runs/20260801T0900Z-R2-frontier-by-generation/{MEASUREMENT,REPLAY}.json` + `_rounds/20260801T001851Z-R1b/round.json` (the price) |
| A23-anchor-drift-on-the-default-leg | 1 | theoria-arm | GAP R2-1; MEASUREMENT.json's 35/52 |
| A24-round-scoreboard-columns-are-null | 1 | theoria-arm | `_rounds/*/round.json` — `theorize_rounds` and `game_id` null on 4 of 4 legs |
| A27-freeze-gate-reads-the-rewritable-half | 1 | theoria-arm | inbox `20260731T1830Z-P12-…`, unclaimed |
| A25-change-sentence-not-bound-to-the-knob | 2 | theoria-arm | R1b's own `change` string, and R1's missing `knobs` key |
| A26-frontier-width-and-probe-yield-as-scoreboard | 2 | theoria-arm | `ITERATION_PROTOCOL.md` §2.4 |
| A28-desk-through-the-model-proxy-behind-a-flag | 2 | theoria-arm | inbox `2026-08-01T0000Z-P12-…`, unclaimed |
| C15-the-unnameable-cell-has-no-home-in-the-dsl | 2 | theory-compiler | GAP R2-2; REPLAY.json's per-generator hit counts |
| S45-launch-blockers-915-916-and-the-reason-floor | 1 | freeze | `freeze/MANIFEST.json` verdict + inbox `20260801T0000Z-exam-…`, unclaimed |
| S46-turn-costs-mixes-two-axes | 2 | battery | inbox `2026-08-01T0300Z-freeze-…`, unclaimed |
| S47-refusal-wave-retry-predicate | 2 | proxy | inbox `20260801T0400Z-theoria-arm-…`, unclaimed |
| V28-exam-four-tests-must-flip | 2 | exam | inbox `20260801T0700Z-freeze-…`, unclaimed |
| V29-one-proxy-validated-not-two | 3 | papers | inbox `20260731T1800Z-S32-…`, unclaimed |
| S48-schema-column-withdrawal-claims-text | 3 | freeze | inbox `20260801T0600Z-PROP-…`, unclaimed |

Fourteen, not ten. Every item states what was measured, what is owed, what the
acceptance is, and what the negative control must be — the last one is not
garnish: A23, A24, A25, A26, S45, S46, S47, V28, V29 and S48 each name a case
the check must be seen to **refuse**, and several name the case it must be seen
to **pass**, because a gate that only ever says no has not been shown to
discriminate either.

## Spend

**Exactly one item carries `spend: api`, and it is blocked.** A22 is the R3
confirmation round for `--frontier generated`. Its price is measured, not
estimated: R1b's two legs cost $17.749106 and $17.390721, **$35.139827** for the
round (`_rounds/20260801T001851Z-R1b/round.json`), and
`ITERATION_PROTOCOL.md` §2.10 puts a four-leg confirmation round at **$40–55**.
The programme has spent about **$285 against a $214.90 ceiling** and the owner
has not ruled, so the item says in its own text that no session claiming it has
spend authority, and it names the offline half that must be finished first.
The other thirteen items are `spend: none`.

A28 is the one that reads like it needs money and does not: the offline half is
the flag and its tests, and the funded `ANTHROPIC_API_KEY` that would let a
proxied desk reach a provider is an **owner action**, not a board item.

## The reconciliation

`INBOX_RECONCILE.md`. Eight asks filed to territories that never saw them, one
that was claimed (battery→theoria-arm on `curves.json`, landed as `82e8e25e`),
and one proposal with four addressees that cannot be a single board item because
one of its halves edits `Theoria.md`. The claimed row is the method's negative
control — the same query returns a commit for it and nothing for the other eight.

## Honest residue

1. **The clock.** This machine's UTC reads `2026-08-01T03:57:19Z` while artefacts
   this run cites are stamped up to `09:00Z` (R2) and `07:00Z` (freeze→exam). The
   directory name is the machine-observed time, unedited. The ordering it implies
   is therefore wrong, and hand-typing a later one would have been the fleet's
   most-fired sanity failure rather than a fix. Recorded, not corrected.
2. **The reconciliation's blind spot** is stated in `INBOX_RECONCILE.md`: work on
   an unmerged branch is invisible to a `git log` over master, so "unclaimed"
   means "not on master", not "nobody is working on it".
3. **No item was verified by doing it.** Every acceptance and every negative
   control here is a specification written from evidence, not a demonstration.
   The first one to be claimed is the first test of whether they are writable.
4. **Cells C15 and the `theory-compiler` territory**: that track has been quiet
   in the recent history read for this run, and the item may sit. It is filed
   against the territory that owns the grammar regardless, because filing it
   against a convenient owner would be worse than filing it against a slow one.
