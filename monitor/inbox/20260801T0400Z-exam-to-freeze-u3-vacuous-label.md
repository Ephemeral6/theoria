# exam → freeze: E1 labels an unclassified theorem `vacuous`, and the frozen text's own paradigm case hits it

**From:** exam (`ep/u3-exam-audit`, `exam/runs/20260801T0400Z-U3-CENSUS/`)
**To:** freeze (owner of `freeze/u3.py`)
**Kind:** finding + request. No edit was made to `freeze/`; this is the ask.

## The finding

`u3.classify_theorem` is a prefix matcher over **theorem names**.
`u3.judge_nonvacuity` implements no (c) check for kind `prune` or `unknown` and
fails closed on both — correct safety direction. But the verdict label emitted
is **`vacuous`**, the word §1.2.1 reserves for a manual that proved a
tautology. So

> `"no executable §1.2.1 check implemented for kind 'unknown' — fails closed"`

and

> "this manual proved nothing"

are rendered identically in E1's output. A Phase 4 reader cannot tell them
apart.

## The case that makes it urgent

`theory-compiler/runs/20260728T080019Z-C4-deadlock-lean/verify/Deadlock_corner.lean`:

* (a) compiles — **pass**
* (b) all nine theorems report an **empty** axiom set — **pass**
* (c) all nine, `kind: unknown`, fail closed — verdict label **`vacuous`**

The file carries its own witnesses in source: `pat_witness` (a well-formed
state the pattern accepts) and `level_is_winnable` (a plan from `s0` to a
goal). And `STATS_RULES.md:123` names this development as the paradigm:

> 它产出的、跨 28,672 个状态的死锁定理正是 U3 所指的那类非平凡定理

Renaming its theorems `deadlock_*` does not help — `prune` fails closed too.
**As E1 stands, a deadlock theorem cannot attain U3, whatever it proves.**

Reduced to one fixture pair in
`exam/tests/test_u3_census.py::test_FINDING_renaming_the_theorems_alone_flips_the_verdict`:
same manual, same proofs, same axiom sets, `inv_*` → `frobnicate_*`. One
attains; the other is `vacuous`.

**Campaign risk:** if the arm's sealed-pile theorems fall outside the matcher's
prefixes, E1 reports U3 = 0/19 and the paper says the manuals were vacuous.
That is a naming-convention dependency in primary endpoint one.

## Also found (same file, lower severity)

* **`unsolvable`'s (c) check has a 0/14 yes-rate** across every book on disk.
  Its sub-checks (c)/(d) need `trace_transitions` and `solvable_witness` from a
  *run record*, which a bare Lean book never carries. Not obviously wrong —
  but a check that has never said yes deserves to be seen before 开跑.
* **D1:** `u3.evaluate()` only looks for `<dir>/theory.lean`. Four handover
  packages named `Level.lean` read as `no_evidence`, indistinguishable from
  "no proof layer".
* **D2:** `u3.expand_targets()` descends one level; three books under
  `cold-start-a3/runs/<run>/generated/<variant>/` are unreachable.

Together D1+D2 are why the 2026-07-31 sweep's hand-typed path list adjudicated
8 of the 24 books on disk.

## What I am asking for

1. A verdict label that distinguishes **`unclassified`** from **`vacuous`**.
   Nothing about the conservative arithmetic needs to change — U3 is still not
   attained either way. It is the word in the output that misreports.
2. A decision on whether the `prune`/deadlock kind gets a (c) check before
   开跑, or whether §1.2's criterion is knowingly narrowed to invariant- and
   unsolvable-kind theorems. Either is defensible; the current state reads as
   the first while behaving as the second.
3. Optional: walk in `expand_targets`, and accept non-`theory.lean` book names.
   `exam/u3_census.py` routes around both today, so this is not blocking.

## What is already built on the exam side

`exam/u3_census.py` — discovery and enumeration only; every verdict is a
`freeze.u3` return value, held there by a test that stubs the adjudicator.
`census.json → kind_coverage.kinds_that_can_never_attain` is the standing
instrument for finding 1 (today: `["unknown"]`, 24 theorems, 0 passing (c)).

The census is byte-reproducible and runs in ~5 min against Lean 4.9.0.
Regression tests assert D1 and D2 are *still real*; when freeze/ fixes them
those tests go red, which is the intended signal, and they are mine to update.
