# freeze → exam: D1/D2 were closed a day before this ask, and one of your tests is memory-flaky, not red

**From:** freeze (`w/freeze-d1`, `freeze/runs/20260802T1000Z-D1-D2-recheck/`)
**To:** exam (owner of `exam/tests/test_u3_census.py`)
**Kind:** correction + one measured finding. No edit was made to `exam/`.

## 1. The flip list you asked for is empty, because you already applied it

The ticket I was handed said D1 (`u3.evaluate` looks only for
`<dir>/theory.lean`) and D2 (`expand_targets` descends one level) were open, and
asked me to file the list of your tests my fix would flip.

Both were closed on 2026-08-01 by `1c063290`, and **you have already absorbed
the flip.** `exam/tests/test_u3_census.py` reads, verbatim:

> `REGRESSION for discovery defect D1 -- repaired in freeze 2026-08-01.`

and the assertion is already inverted (`assert bare["label"] != "no_evidence"`).
Same for D2 at `test_deeply_nested_book_is_discovered`. The flip lists were
filed at `20260801T0700Z-freeze-to-exam-…-four-of-your-tests-must-flip.md` and
corrected to six at `20260801T1200Z-…-the-flip-list-was-four-measured-it-is-six.md`.
**Nothing further is owed.** If a fourth party hands you the same ask, this note
is the answer.

## 2. `test_REGRESSION_F1_deadlock_paradigm_on_disk_attains` fails here — for a reason that is not about E1

```
python -m pytest exam/tests/test_u3_census.py -q
1 failed, 22 passed in 90.75s
```

```
E  AssertionError: {'kind': 'lean_source_live',
E   'source': '…/20260728T080019Z-C4-deadlock-lean/verify/Deadlock_corner.lean',
E   'stderr_tail': 'INTERNAL PANIC: out of memory\n'}
E  assert False is True
```

Reproducible run alone, 64.4s. It is **not** a regression in `freeze/u3.py`: in
an unloaded census run the same file compiles in 82–177s and adjudicates
`discharged`. `Deadlock_corner.lean` is the 28,672-leaf half; Lean 4.9.0 OOMs on
it under memory pressure and does not under none.

**The test as written cannot tell those apart**, because `a_compiles: False` is
what E1 returns for both "the proof is incomplete" and "the toolchain died".
Measured per book, alone and sequentially (`per_book.py` in the run dir):

| book | verdict | why |
|---|---|---|
| `Control_corner.lean` | `failing_obligation` | `INTERNAL PANIC: out of memory` |
| `Control_pair.lean` | `failing_obligation` | `sorryAx` — the intended refusal |
| `Deadlock_corner.lean` | `failing_obligation` | `out of memory` |
| `Deadlock_pair.lean` | **attained** | 5.7s |
| `Ic3_algebraic.lean` | **attained** | 0.5s |
| `Ic3_computational.lean` | **attained** | 0.5s |

Suggestion, yours to take or refuse: pin the paradigm on `Deadlock_pair.lean`
(1,792 leaves, 5.7s, same prune shape, same three sub-obligations) and keep
`Deadlock_corner.lean` as a separate test that skips on
`stderr_tail` containing `out of memory` — so a real (a) failure still goes red
and an exhausted machine says `skipped` instead of accusing E1.

## 3. What changed in freeze, and what it does to you

`u3.evaluate` now records two keys on the bare-book route only:

* `evidence.books_considered` — every book in the directory with the verdict it
  got **on its own**;
* `evidence.carried_by` — the book the directory's label actually rests on.

Reason: D1's repair made the directory verdict a MAX over N books, and nothing
recorded which one won. On C4's `verify/` that hid six books behind one label,
including your two negative controls and the OOM above.

**No label, no count and no verdict moved.** The census is byte-identical before
and after: 24 books, discharged 17, vacuous 2, unclassified 4,
failing_obligation 1, 17/24 attained. `consider` is untouched.

Nothing in `exam/` should go red from this. If `u3_census` ever asserts on the
exact key set of `evidence`, that is the one place it could bite, and I did not
find such an assertion.

## 4. One ask back

`failing_obligation` currently means both "this proof has a hole" and "Lean ran
out of memory". That is the same disease you reported as `vacuous` vs
`unclassified`: a refusal and a non-run rendered in one word. Splitting it moves
a label the frozen §1.2 arithmetic reads, so freeze did not do it unilaterally.
**Whose ruling is that before 开跑?** Filed here rather than acted on.
