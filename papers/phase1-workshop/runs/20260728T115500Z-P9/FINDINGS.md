# P9 — opening reconnaissance, written before any edit

RES-2, branch `agent/p9-paper-to-submittable`, base `d1733df`. Nothing has been
edited yet; this file exists so the reconnaissance is not lost with the session
that did it.

## Two of the work order's four clauses are stale, and one is a territory conflict

`monitor/board/items/P9-paper-to-submittable.md` asks for four things. Checked
against `master` at `d1733df`:

| clause | state on master | verdict |
|---|---|---|
| write A0/A0′, A2, A3 as publication-quality body text, every number pointing at a tree file | §3 (`03_a0.md`, 261 lines), §5 (`05_a2.md`, 266), §6 (`06_a3_transfer.md`, 197) all exist and are substantial | **real work remains, but it is revision, not drafting** |
| "the battery section is marked stale — update it to the latest REPORT" | **already done.** `sections/07_battery.md:9-14` opens "This section reports **v2** … 95 runs across 5 arms … 38 metrics", and `OPEN_ITEMS.md` A1 is struck through: *"Closed at P7 — §7 re-derived against `battery_version: v2`, every number read from `battery/artifacts/*.json` rather than from report prose"* | **stale premise** |
| wire the figures to `figures/`'s deterministic pipeline, no hand-pasted images | not yet checked in detail; `papers/phase1-workshop/figures/` still holds its own `fig1/fig2/fig3` scripts and a `data/` directory, separate from the root `figures/` pipeline | **real, and probably the largest piece** |
| reviewer subagent on novelty / evidence / reproducibility | `OPEN_ITEMS.md` A4 records that a third audit is owed: `REVIEW.md` audited a 75,885-byte draft, `CITECHECK.md` a 91,244-byte one, and three sections have landed since | **real** |

**This is the second work order in a row whose premise had been overtaken.** P8's
said figure 2's theoria column was empty when P4 had already drawn it; this one
says §7 is stale when P7 has already re-derived it. Both are the same failure at
the level of the board rather than the code: an item's text is written once and
the tree moves under it. Reported to the monitor rather than silently
reinterpreted, because the next researcher will read the same text.

## Blocker: `papers` is claimed twice

`monitor/board/claimed/P7-paper-section7.APP-P7.md` is still claimed by `APP-P7`
and its territory is `papers` — the same territory the board has just handed me
for P9. P7's output is visibly on master (§7 is v2), so the claim may simply be
unreleased; but "may simply be" is not something to edit another session's
territory on. **No file under `papers/` has been modified by this branch.**

Two ways out, and the choice is the monitor's, not mine:

1. If P7 is finished, release its claim and P9 proceeds over the whole of
   `papers/`.
2. If P7 is still in flight, P9 should be scoped to the parts P7 is not holding
   — on the evidence, `papers/phase1-workshop/figures/` and the third audit pass,
   neither of which touches `sections/07_battery.md`.

## What the next session should do first

1. Read `monitor/mailbox/RES-2.md` for the monitor's ruling on the collision.
2. Re-read `OPEN_ITEMS.md` — it is the live checklist and it is *more* current
   than the board item. Its own top-priority set is now **A2** (abstract wording,
   unblocked by A1's closure), **A3** (the "three pairs" gloss that turns an
   anecdote into evidence), **A4** (third audit), **B1** (22 citations violating
   the paper's own repo-relative rule, 9 of them ambiguous across 6–24 real
   candidates), and **D** (claim-scoping half of related work).
3. The figure clause is the one the work order asks for that nobody has done:
   `papers/phase1-workshop/figures/` has its own scripts and its own `data/`,
   while the deterministic pipeline with the hash manifest and eight gates lives
   at `figures/`. Wiring the paper to the latter is exactly the "no hand-pasted
   images" requirement, and P8 has just left that pipeline green and documented.

## Discipline

Zero API calls, zero model calls, zero network, zero spend. Sealed pile
untouched. No file edited outside this run directory.
