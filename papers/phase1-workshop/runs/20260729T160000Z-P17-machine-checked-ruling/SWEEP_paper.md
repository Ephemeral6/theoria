# Fact-check round 2 — paper-wide sweep

Independent subagent, read-only. Three sweeps: proof-strength verbs, the §5.6
weight-table correction (the item's task 3), and what the paper's own gates
would and would not catch.

## Sweep 1 — proof-strength verbs

The class is **small and mostly clean**. `sections/00_abstract.md` has zero
loose uses: it says "Lean signs an axiom-free impossibility theorem" and "a Lean
proof with an empty axiom list", both correctly attached to Lean output.
Fourteen further occurrences across `03_a0.md`, `04_a1.md`, `05_a2.md`,
`06_a3_transfer.md`, `08_exam.md`, `10_adjudication.md`, `11_limitations.md`,
`12_related.md` were checked and are correctly attached to a Lean theorem, or
quote a JSON field *in order to criticise it*. `10_adjudication.md` already runs
a self-audit of the word `verified` and deliberately downgrades it.

Two flags survive.

* **§5.2 item 3** — the subject of this ruling. Now closed.
* **§1 and §4, and `11_limitations.md` inheriting them** — *"a machine-checked
  impossibility certificate whose weights cross a data boundary"*, as a
  contribution bullet in the intro and as **§4's heading**. The adjective sits on
  the *certificate*, which is an LP-produced JSON re-checked by a Python
  `verify()` — and §4 itself spends two paragraphs establishing that the blob's
  own `verified: true` field is not to be trusted. A Lean theorem does exist
  downstream, so the phrase survives a charitable reading. A contribution bullet
  and a section heading are the two worst places to depend on one. **Recorded as
  OPEN_ITEMS C12**, not fixed here: it is out of this item's scope, and a
  heading change is not a one-word edit.

**No gate would have caught either.** Grepping the proof vocabulary across
`verify_paper.py`, `test_uncited_gate.py` and `test_bare_gate.py` finds no
pattern — the six checks are structural (assembly equality, path resolution,
byte-determinism, secret absence, citation *presence*, citation *uniqueness*).
Check E would have passed §5.2 item 3 unchanged, because its block merges with
the table and the table's cells carry real artefact paths: *any* real path
satisfies the block, which `verify_paper.py:53-55` already documents as the
known gap.

## Sweep 2 — the item's task 3

**(a) The correction is intact.** `sections/05_a2.md` §5.6, the block beginning
*"A correction to the source report, and it matters"*, is present and complete,
including the `def Goal` bullet, the four-`step`-entries bullet, and the
follow-through on what survives and what is lost.

**(b) Nothing anywhere still asserts the old claim.** Every occurrence in the
paper directory either states it in order to refute it or states the corrected
version — `sections/01_intro.md` ("The two files are *not* a minimal pair"),
`sections/00_abstract.md` (the four narrow dimensions only), `PROVENANCE.md`
(which explicitly negates it and carries a disagreements row resolving
*follows the files*), `CITECHECK.md`, `REVIEW.md`, `REVIEW_TRIAGE.md`,
`OPEN_ITEMS.md`, and the historical run records. **No figure caption, CSV row,
or figure payload asserts a minimal pair** — the figure text makes the surviving
claim instead ("the instrument cannot tell the two Lean files apart").

**(c) The diff re-measured, independently, and re-measured again by me.** All
four of §5.6's numbers are right: 52 changed lines (27 removed + 25 added), 14
of them the weight table, `def Goal` differing `c10` against `c34`, and exactly
four `step` entries — all the same clause across the four colour × door strata,
`⟨Cell.c31, …⟩, .down` mapping to `c31` against `c35`. The header comment and
the comment above `def I` account for the remainder; the arithmetic closes.

**One thing did not survive being run, in the paragraph that states the rule
that it must.** §5.6 said *"`diff` the two files and 52 lines change across 7
hunks"*. Confirmed at the shell: `diff -u` gives 7 hunks, plain `diff` gives 15
groups of the same 52 lines, `diff -U0` gives 15. The line count is a property
of the files; **the hunk count is a property of the command**, and the command
the sentence names is not the one that yields 7. Fixed in this run: §5.6 now
says `diff -u`, gives the reason, and states what plain `diff` returns instead.

**One residual left standing deliberately.** `CITECHECK.md` reports the same
finding at **70 diff lines** against §5.6's 52. 70 is not reproducible directly;
the nearest artefact is `diff -U0`'s 69-line total output, which counts hunk and
file headers as diff lines. The audits are kept unedited by OUTLINE red line 3,
so the number stays and the divergence is recorded as **OPEN_ITEMS B5**.

## Sweep 3 — the gates, and whether this edit could break one

| check | what it enforces | this edit |
|---|---|---|
| **A GENERATED** | `PAPER.md` byte-equals `assemble(sections/)` | the one guaranteed break; `assemble.py` was re-run |
| **B PATHS** | every path-shaped backticked token resolves, unambiguously | new cells add `cold-start-a2/...` paths; all resolve |
| **C FIGDATA** | figure extractors byte-deterministic | untouched by section text |
| **D NOSECRET** | no `.env` value in any published file | untouched |
| **E UNCITED** | every quantity-bearing block cites an artefact | safe: `_emit` merges `\|`-leading rows into the preamble block, which carries citations |
| **F BARE** | a backticked bare filename must resolve to exactly one file | **the real hazard for a new column** — a cell containing `theory.lean` would be `AMBIGUOUS` against 16 files. Avoided: the `kind` values are plain words |

There is **no table-shape check and no word-count check** anywhere; nothing
parses markdown table structure or counts columns. Adding a column is invisible
to every gate except A, and A is deterministic and was satisfied.
