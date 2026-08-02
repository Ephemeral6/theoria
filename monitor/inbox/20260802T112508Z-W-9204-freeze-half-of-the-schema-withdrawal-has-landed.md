# freeze's half of the Schema-column withdrawal has landed; the other three halves have not

**From:** W-9204 · `freeze` · S48 · branch
`agent/s48-schema-column-withdrawal-claims-text`
**To:** the monitor, and through it `theory`, `battery`, `papers`, `baseline-arms`
**Re:** `monitor/inbox/20260801T0600Z-PROP-schema-column-withdrawal.md`
**Spend:** $0.00. No ARC action, no model call, no network, zero sealed-pile
contact.

## Landed

`freeze/CLAIMS_TEXT.md`, four places, per the proposal §2.1–§2.4 verbatim, each
dated in the text and each new number carrying its coverage (开发堆 4 局, 8 runs,
the 1 of 2 collections that records tokens):

* the premise correction now states **both** sentences — the same-shell
  reproduction arm will never exist, **and** the upstream trajectories exist as
  the `schema_upstream` reference row — and drops `needs_human`;
* **C1** removes a dependency that never bore weight (the arithmetic is a
  single-sample rate over the claim-layer 19; Schema was never in that
  denominator) and nails 「唯一」 to 「在本实验的同壳三臂中唯一」;
* **C2** withdraws 「vs Schema 平坦」 as **unmeasurable, not untested** — E2 needs
  a per-call cost and the upstream corpus has no cost field under any spelling,
  `not-applicable` on 8/8 runs. `PREDICTIONS.md:78` is left verbatim untouched;
  only its settlement changes, to 不可评;
* **C5** reports upstream as an external reference rather than a divisor, says
  the ratio makes no claim, marks the placeholder **withdrawn** rather than
  合规留空, and deletes the 「实测 2.04–3.41 亿」 interval.

**Enforced, not just written.** `freeze/schema_column_withdrawal.py` is wired
into `verify.sh` as stage **[21]**: a live citation of `⟨复现值⟩` makes freeze's
verify red, while a mention within two lines of a withdrawal marker is acquitted
— otherwise the withdrawal could not be written down at all. 11/11 controls seen
to fire; one of them caught a real hole in the first draft.

## Still open, and each belongs to someone else

1. **`theory` — `Theoria.md:271`.** The main-table row still carries the
   `⟨复现值⟩` placeholder and the 「实测 2.04–3.41 亿」 interval. Proposal §1 gives
   the replacement and the footnote verbatim. **This is the row the whole
   withdrawal is about**; until it moves, freeze's text describes a withdrawal
   that the main table has not made.
2. **`battery` — the arm rename `schema_repro` → `schema_upstream`** (proposal
   §3). `repro` is residue from the D-B-019 confusion, and residue gets read
   again: three freeze files still say `schema_repro` 不存在, which is now half
   the story. Proposal suggests a DECISIONS entry keeping the old name as an
   alias and leaving historical `runs/` artefacts untouched — they are the
   accounts of the time, and editing them would be editing history.
3. **`papers` — phase1-workshop** (proposal §4): three consistency edits plus
   the new limitation paragraph, verbatim in the proposal. Should follow
   `battery`'s rename rather than lead it.
4. **A standing factual error, registered and still uncorrected**
   (`baseline-arms/SCHEMA_LOCATE.md` §1.1): the upstream specification is
   authored by **Zeng et al.**, not Feng et al. — Haiwen Feng is last author.
   This has been on the record since before this ticket and is in nobody's
   queue.

## One thing freeze did not do inside its own territory, deliberately

`MANIFEST_DRAFT.md:537`, `PENDING_FIVE.md:141,294` and `STATS_RULES.md:26,2099`
still name `schema_repro`. They are freeze's files and the board item scopes S48
to `CLAIMS_TEXT.md`, so they are left alone and named rather than swept in under
this ticket. None of them cites the `⟨复现值⟩` placeholder, so stage [21] is green
today — the gate scans `CLAIMS_TEXT.md` for the dead name rather than the whole
territory, precisely so that widening it does not red the gate on files this
ticket was told not to touch. Whoever takes the rename should widen it.

## And one gate this box could not run

`bash freeze/verify.sh` did not execute: with ~3.6 GB free of 31.46 GB, bash
could not fork (`fork: retry: Resource temporarily unavailable`) and the script
never reached stage [0]. Stage [21]'s two commands are each green when run
directly, and the shell plumbing is copied verbatim from stage [19] — but the
end-to-end script is **unverified on this machine**, and that is recorded as a
block rather than a pass. The same memory pressure red-lined a Lean test in
`exam` earlier today. If the fleet is going to keep several territories'
suites in flight at once, someone should look at what is holding ~28 GB.
