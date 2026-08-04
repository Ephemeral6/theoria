# D1/D2 recheck — the defects were already closed, and closing them left a new one

**Territory:** freeze · **Branch:** `w/freeze-d1` · **Base:** master `b4540026`
**UTC:** 2026-08-02T10:00Z · **Offline:** Lean 4.9.0 only. No API, no model, no
network, no spend, no sealed-pile contact.

## The brief was wrong, and this is the evidence

The ticket said D1 (`u3.evaluate()` looks only for `<dir>/theory.lean`) and D2
(`expand_targets` descends one level) are the live blocker on U3 attainment,
that four `Level.lean` packages read `no_evidence`, and that the C4 sokoban
deadlock proof is among them.

Three of those four claims are false on `b4540026`:

* **D1 and D2 were closed on 2026-08-01** by commit `1c063290`, which is an
  ancestor of the base this ticket was cut from. `freeze/u3.py:862` is
  `find_books`, which takes any `.lean` that states a theorem;
  `expand_targets` walks to `max_depth=12` and returns its exclusions with
  reasons. Both carry `D1`/`D2` comments naming exam's report.
* **The four `Level.lean` packages are found.** They are
  `theory-compiler/handover_packages/{a0-cart/levels/base, a0-cart/levels/no-button,
  a0-sokoban2/levels/crossing-up, a0-sokoban2/levels/match}`. They adjudicate
  `unclassified`, not `no_evidence` — found, compiled, (b) passed, and E1 has no
  §1.2.1 check for their assertion kind. That is a different open question and
  it is not a discovery defect.
* **C4 is not one of them.** It is
  `theory-compiler/runs/20260728T080019Z-C4-deadlock-lean`, its books are
  `corner.lean` / `pair.lean`, and it **attains** — `discharged`, (a) pass,
  (b) pass, (c) discharged on `closed_pinned`, `dead`, `dead_closed`,
  `dead_persists`.

**So the answer to the ticket's question 2 already exists: the F1 repair works
on a real deadlock proof.** It is not new evidence produced here; it is
re-derived here, which is worth something but is not what was asked for.

## Census, re-derived independently

`census.py` re-run from this worktree against the whole repo:

| | 2026-07-31 sweep | 2026-08-01 census | this run |
|---|---|---|---|
| directories walked | hand-typed list | 44 | **50** |
| books found | 8 | 24 | **24** |
| discharged | 14 | 17 | **17** |
| vacuous | 9 | 2 | **2** |
| unclassified | 0 | 4 | **4** |
| failing_obligation | 1 | 1 | **1** |
| **attained** | — | 17/24 | **17/24** |

Byte-for-byte the same book verdicts as the archived 08-01 census. The
directory count moved 44 → 50 because six `theoria-arm/runs/` dirs appeared
since; every one is bookless, so the book denominator did not move.

The ticket's stated baseline — discharged 14, vacuous 8, unclassified 1,
failing_obligation 1 — matches no census on disk. The real pre-repair figures
were 14 / 9 / 0 / 1. Recorded as a discrepancy, not reconciled.

## What is actually new: D1's second half

D1's repair widened the search from one candidate book per directory to N. That
turned the directory verdict into a **max over books** — `consider` keeps the
first book at the highest stage rank and drops every other book's verdict
unrecorded. Nothing said so, and two live cases were riding on the silence.

**Measured, `per_book.py`, each C4 book adjudicated alone:**

| directory | book | verdict |
|---|---|---|
| `…C4-deadlock-lean` | `corner.lean` | `failing_obligation` — Lean `out of memory` |
| `…C4-deadlock-lean` | `pair.lean` | **attained**, 5.3s |
| `…/verify` | `Control_corner.lean` | `failing_obligation` — `INTERNAL PANIC: out of memory` |
| `…/verify` | `Control_pair.lean` | `failing_obligation` — `sorryAx` |
| `…/verify` | `Deadlock_corner.lean` | `failing_obligation` — Lean `out of memory` |
| `…/verify` | `Deadlock_pair.lean` | **attained**, 5.7s |
| `…/verify` | `Ic3_algebraic.lean` | **attained**, 0.5s |
| `…/verify` | `Ic3_computational.lean` | **attained**, 0.5s |

The `corner` half is the 28,672-leaf development `STATS_RULES.md:123` names as
the paradigm. Under memory pressure Lean OOMs on it; in an unloaded census run
it compiles in 82–177s and is `discharged`. **Criterion (a) on the paradigm
development is machine-memory-dependent, and the directory reads `discharged`
either way because `pair.lean` carries it when `corner.lean` cannot.** A verdict
that is stable in the output and unstable underneath is the thing a freeze
record must not ship silently.

`verify/` also holds `Control_corner.lean` and `Control_pair.lean` — negative
controls. They are correctly refused. Nothing in the old output showed they were
weighed at all, so a reader could not tell refusal from never-reached.

**The change:** `u3.evaluate` now records, on the bare-book route only,
`evidence.books_considered` — every book with the verdict it got on its own —
and `evidence.carried_by`, the book the directory's label rests on. `consider`
is untouched; no label and no count moved (the census above is post-change and
identical). This is an audit trail, not a criterion.

Rosters that now exist and were invisible before:

```
cold-start-a2/theory/generated_repaired -> discharged | carried_by: theory.lean
      theory.lean discharged
      theory_latch.lean discharged
theory-compiler/runs/20260728T080019Z-C4-deadlock-lean -> discharged | carried_by: corner.lean
      corner.lean discharged
      pair.lean discharged
theory-compiler/runs/20260728T080019Z-C4-deadlock-lean/verify -> discharged | carried_by: Deadlock_corner.lean
      Control_corner.lean failing_obligation
      Control_pair.lean failing_obligation
      Deadlock_corner.lean discharged
      Deadlock_pair.lean discharged
      Ic3_algebraic.lean discharged
      Ic3_computational.lean discharged
```

Three tests hold it, one of them the negative control that blinds `find_books`
to the attaining book and requires the roster to shrink with the search — a
roster that reported both books unconditionally would look identical on the
happy path and prove nothing.

## Residual, stated and not closed

**`failing_obligation` covers two different facts.** `Control_pair.lean`
(genuinely holed, `sorryAx`) and `Deadlock_corner.lean` (proof is fine, the
toolchain ran out of memory) get the same label. That is the same species of
defect exam reported for `vacuous`/`unclassified`: a check that refused and a
check that could not run are rendered identically. Splitting it would move a
label that the frozen §1.2 arithmetic reads, so it is **not** done here. It is
an ask, and it belongs to whoever rules on labels before 开跑.

**The 28,672-leaf half has no recorded memory requirement.** Nothing on disk
says how much RAM criterion (a) needs for it. Until that is measured, a green
E1 on the C4 directory is not evidence that the paradigm development compiled —
only that some book in it did. `carried_by` is now the instrument for reading
that; it is not a fix.
