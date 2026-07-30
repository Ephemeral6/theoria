# A stored Lean transcript for A1's four theorems

RES-2, 2026-07-30, during P18's adversarial round. **This file exists because
`RULING.md` §3 says it does not.** That caveat read: "The empty axiom list is
test-asserted, not stored. No `lean` transcript exists anywhere in the tree; the
assertion lives in tests that *skip* when the toolchain is absent … Under this
paper's own rule that an invited check must survive being run, a reader without Lean
cannot run this one."

The first half was true and is now false, for this run. The second half is unchanged
and still limits what the paper may claim — see **What this does not fix** below.

## What was run

```
$ cd theory-compiler/lean
$ lean TheoriaLean.lean
'inv_init' does not depend on any axioms
'inv_closed' does not depend on any axioms
'inv_all' does not depend on any axioms
'unsolvable' does not depend on any axioms
$ echo $?
0
```

Verbatim stdout of the real kernel, and the whole of it — four lines, no warnings,
no `sorry`, exit 0. The four `#print axioms` directives that produce it are
`theory-compiler/lean/TheoriaLean.lean:154-157`.

## Provenance

| field | value |
|---|---|
| toolchain | `Lean (version 4.9.0, x86_64-w64-windows-gnu, commit 8f9843a4a5fe, Release)` |
| `lean` resolved to | `/c/Users/user/.elan/bin/lean` |
| artefact | `theory-compiler/lean/TheoriaLean.lean` |
| artefact sha256 | `951981b68c6a07859c954ed288bff2b0a84eead76255511291677a2d5496bee0` |
| artefact bytes | 4113 |
| repo commit | `994d35d25b4edc7be860ea427c952b87342bef6e` |
| imports in the artefact | **none** — `grep -nE "^import"` returns nothing, so no Mathlib |
| `native_decide` / `sorry` / `axiom` declarations | none; the only occurrence of the string "axiom" outside `#print axioms` is a header comment at `:24` |

The Python-side assertion also ran and passed rather than skipping:
`theory-compiler/tests/test_gen_lean.py::test_computational_proof_has_no_axioms`
**PASSED**, and the whole of `test_gen_lean.py` is **21 passed, 0 skipped** on this
machine. The gate is `LEAN = shutil.which("lean")` at `:32` with
`needs_lean = pytest.mark.skipif(LEAN is None, …)` at `:33`, and the tests invoke the
real binary at `:51` — so a machine with the toolchain really does check this, and
one without it really does skip.

## What this does not fix

* **A transcript is not a proof, and a stored transcript is not a re-run one.** This
  records that a kernel accepted the file at one sha256 on one machine. A reader
  still cannot verify it without a toolchain; they can only see what the toolchain
  said and check the hash of what it was said about. That is strictly better than
  prose and strictly weaker than running it.
* **`OPEN_ITEMS.md` C8 stays open.** C8 is broader than this file: the paper does not
  say a Lean toolchain is required, and 83/83 becomes 75 passed / 8 skipped without
  one. Nothing here says that; C8 is where it belongs.
* **The negative control is still prose only.** `RULING.md` §3's other half — that
  perturbing one weight makes all four theorems report `[sorryAx]` — was not run
  here and remains recorded rather than demonstrated. Running it would mean editing
  a tracked artefact in the theory-compiler track's territory, which this item may
  not do. It stays with C8.
* **This file is in `papers/`, deliberately.** It is P18's evidence, not a
  theory-compiler artefact. Storing a transcript inside `theory-compiler/lean/` would
  be the right permanent home and is that track's call, not this item's.
