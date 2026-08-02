# `freeze/build_manifest.py` will silently not hash `dsl_grammar_v0.4.md`

**From:** W-9204 · `theory-compiler` · C15 · branch
`agent/c15-the-unnameable-cell-has-no-home-in-the-dsl`
**To:** the monitor, and through it whoever owns `freeze/`
**Severity:** low now, wrong later. No action needed from me; I may not edit
`freeze/`.

## The fact

`freeze/build_manifest.py:79-98` hard-codes item n=2, 「DSL 语法版本（两本书）」,
as an explicit path list naming `dsl_grammar_v0.1.md`, `v0.2.md` and `v0.3.md`.
It hashes only listed paths — there is no `CONTRACTS/*.md` glob — so
`CONTRACTS/dsl_grammar_v0.4.md`, landed 2026-08-02 by C15, will be **absent from
the freeze manifest** until that list gains it.

Why it matters more than a missing row: the Phase 4 release manifest is what
publishes the tracked tree, and v0.4 is the file that carries the **refusal** of
GAP R2-2 — a contract clause. A frozen release whose manifest does not cover the
contract it ships is exactly the shortfall the manifest exists to prevent, and
it fails open rather than closed: no error, just an unhashed file.

## The repair

Add `CONTRACTS/dsl_grammar_v0.4.md` to the item-2 path list. If the list is
meant to track every grammar version forever, a sorted glob over
`CONTRACTS/dsl_grammar_v*.md` would close the class rather than this instance —
that is a design call for `freeze/`, not for me, and I note only that the same
list has already gone stale once (its own note flags the stale version citations,
including `CLAUDE.md:64`).

## The adjacent one, same class

`CLAUDE.md`'s frozen-contracts table lists v0.1 / v0.2 / v0.3 and does not
mention v0.4. `CLAUDE.md` is a root shared surface rather than this track's
file, so it is reported and not edited. Suggested row, matching the existing
wording for v0.2/v0.3:

```
| `dsl_grammar_v0.4.md` | final; theory-compiler sole owner (no countersign required). Refuses the board-cell extension (GAP R2-2); adds no production. |
```
