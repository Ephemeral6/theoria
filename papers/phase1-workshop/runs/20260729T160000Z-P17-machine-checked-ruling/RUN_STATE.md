# P17-machine-checked-ruling — run state

RES-2, paper lane. Item `monitor/board/claimed/P17-P17-machine-checked-ruling.RES-2.md`.
Branch `agent/p17-machine-checked-ruling`, base `78c76bdf` (the tip of
`agent/p17-bare-filename-citations`, this lane's previous item, still queued for
merge — so this branch stacks on it rather than on `master`).

The narrative. `MANIFEST.json` is the provenance; `RULING.md` is the deliverable;
`FACTCHECK_rows.md` and `SWEEP_paper.md` are the evidence it was decided on.

## What was asked, and what the ruling did

Three tasks. Rule on §5.2's "The isomorphism is machine-checked, clause by
clause"; if kept, label every row of its table with the kind of check behind it;
and confirm that §5.6's earlier correction about the two Lean files still holds
and is not contradicted anywhere else.

**Verdict: delete the claim, keep the ledger, label every row.** Option 3 for the
sentence, option 1 for the table. Explicitly *not* option 2 — the reasoning is in
`RULING.md` §3, and the short form is that qualification fixes the adjective and
leaves the noun: after any softening, the sentence still asserts an *isomorphism*
established by *checking*, and the far side is still this project's own paragraph
in `Theoria.md` §1.3, which a reader will silently replace with DC22. The
authorising ruling D-A2-001 had already scoped the far side to the description;
the sentence had outrun its own warrant.

## The counts the ruling was decided on

Fact-check round 1 classified all six rows against the artefacts, not against the
paper: **1 Lean** (row 5, and only its Lean half), **5 computed-from-artefact**,
**0 refuted**.

**The item's own statement of the facts was wrong**, and that is the most useful
thing this run found. The item says one row "was refuted by an episode". No row
was refuted; the *manual's `unsolvable` theorem* was, and that row's clause —
而这一关人类可解 — is confirmed as strongly as any row in the table.
`refutation.json`'s `verdict` field names the theorem as the refuted object, in a
field the table did not quote. The item's author is the paper's most careful
available reader, reading with the table in front of them and this exact sentence
under examination, and they read the column the wrong way; my own first reading
made the same mistake. A cell that misleads its own commissioning reader is the
strongest evidence a table can produce against itself. So the ruling repaired the
cell, and the table now reports a *stronger* result than it appeared to: no
clause comes out against the built world.

## Four row-level mismatches, repaired with the labels

None was in the item's scope; all four are in the ruling's, because a `kind`
column is a promise that each row means what it says — a row labelled `Lean`
whose other half is a BFS stub is a worse misstatement than the same row
unlabelled. Detail in `RULING.md` §6. In brief: row 5's plan half runs the
bundled BFS stub and returns UNSAT on a manual *containing* the rule too (§5.8's
D-A2-006), so the Lean half carries the row and the cell now says so; row 3 cited
two fields that are not in the file it named (both statements true, neither at
the cited path — which §5.6's own rule forbids); rows 2 and 4 were tagged
`(compressed)` and are verbatim substrings of `Theoria.md`; row 1's "the only
proposal" was unscoped and read as contradicting row 4.

## Task 3 — the §5.6 correction

Intact. The correction is present, and nothing in the paper, the figures or the
CSVs still asserts the superseded "differ in their weight table and in nothing
else". The diff was re-measured independently: 52 changed content lines
(27 removed + 25 added), `def Goal` c10 vs c34, and four `step` clauses — all
four of §5.6's numbers check out.

**One defect found inside the correction itself.** §5.6 invited a plain `diff`
and reported **7 hunks**, which is `diff -u`'s number; plain `diff` gives 15. A
correction that invites a check the check does not survive is the same defect
class the correction was written to fix, one level up. Fixed by naming the
convention where the number is used.

Two OPEN_ITEMS opened, one closed:

* **C13 closed** — by this ruling, not by a softening.
* **C12 opened** — the same proof-verb defect survives in two more prominent
  places than the one that was fixed: §1's contribution list and §4's own
  *heading* both read "a machine-checked impossibility certificate", and §11
  inherits the phrasing. Self-supplied to the board as
  `P18-P18-certificate-verb-ruling`, queued behind this item because the board
  gives one holder per territory.
* **B5 opened** — `CITECHECK.md` says the Lean diff is 70 lines, §5.6 says 52.
  Re-measured: 52 is right under every convention; 70 is not reproducible
  directly and the nearest artefact is `diff -U0`'s 69-line total output, which
  counts hunk and file headers as diff lines. The audits are kept unedited by
  OUTLINE's red line 3, so this is **recorded, not reconciled** — the fix was to
  state the counting convention where the number is used, and the audit's 70 is
  left standing.

## Tests

`python verify_paper.py` → **PASS (6/6)** after each commit, and again at
delivery. Zero API calls, zero model calls against the game, $0.00, zero sealed
pile contact. Only `papers/` is touched.

## Adversarial round

Three independent adversaries, run at cycle 26 against the applied text rather
than against the draft: (1) try to overturn the verdict and find a *new*
overclaim in the replacement prose, (2) re-run every citation in the rewritten
item and the fine-print paragraph, (3) sweep the rest of the paper for damage
from the edit and for the same defect surviving elsewhere.

*Results recorded below once in — this section is written before them on purpose,
so that what was asked of the adversaries is on disk independently of what they
found.*
