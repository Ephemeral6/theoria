# E15-solver-status-bit — pre-registration

Committed **before** any of the four items was run, so that
`git merge-base --is-ancestor <this commit> <the commit carrying the results>`
is checkable. Ticket: `monitor/board/claimed/E15-solver-status-bit.RES-3.md`.

Base commit `e942ee6d1ea6109175032a0af67adda357ea1f0c`, branch
`agent/e15-solver-status-bit`, Python 3.13.13, scipy 1.17.1, numpy 2.4.4.

## What this item is and is not

`lp_potential` is **sound but incomplete**, and the incompleteness is a
documented boundary (`CLAUDE.md`), not a defect. Silence is a correct answer.
What is being fixed is narrower: the engine cannot currently tell a reader
*which kind* of silence it is producing, because HiGHS status 1 / 2 / 3 / 4 all
arrive at the caller through one value. Nothing below treats "no certificate"
as a bug, and no acceptance criterion here gets easier if the silence rate goes
down.

The 29.2 % figure already published by E11 is expected to **stand**. If the
re-run disagrees with E11's hand derivation, the hand derivation wins and the
disagreement is written up; the artifact is not adjusted to match.

## P1 — the status bit survives to the caller

Pass iff all of:

1. `engines.lp_potential.potential.solve(...)` returns an `LpOutcome` whose
   `status` is one of exactly `certified`, `no_linear_pagoda`, `budget`,
   `unbounded`, `numerical`, `undecided` — never `None`.
2. `LpOutcome.no_linear_pagoda` is true **only** when the HiGHS status was `2`.
   Statuses 1, 3, 4 and any unrecognised code map to statuses for which
   `decided` is false.
3. The public entry `engines.lp_potential.run` branches on `outcome.status`
   *by name*, not on `certificate is None`: an undecided outcome raises
   `LpUnavailable` carrying the specific status word, a `no_linear_pagoda`
   outcome returns `(None, None)`.
4. `LpOutcome.as_json()` carries `status`, `solver_status`, `bound`, `margin`,
   `decided`, so a consumer reads the classification off the artifact instead
   of re-deriving it.
5. Existing behaviour is preserved where it was already right:
   `solve_certificate` still returns a `Certificate` or `None` and still raises
   `LpUnavailable` on 1/3/4 (the C11 tests keep passing unchanged).

## P2 — the 639 re-issued, readable off the artifact

`census.py` re-runs the E11 corpus: campaign seed `0x00005EEDC1E4F002`,
`fuzzlab.prng.derive(seed, "jumpgraph", i)` for `i = 0…2999`, exhaustive forward
BFS for ground truth, engine answer via `lp_potential.solve`.

Pass iff all of:

1. Every row of `census.jsonl` carries the engine's own `status` word and
   `solver_status` integer. **No column in it is computed by re-solving the LP
   outside the engine.**
2. `SUMMARY.json`, derived from that file by counting `status` strings alone,
   reports the incompleteness rate. Pre-registered expectation from E11 §4.1
   and §4.3, as exact integers:

   | quantity | expected |
   |---|---|
   | worlds | 3000 |
   | goal genuinely unreachable | 2189 |
   | certificate issued | 1550 |
   | no certificate | 1450 |
   | silent **and** genuinely unreachable | 639 |
   | incompleteness rate | 639 / 2189 = 29.2 % |
   | `CertificateError` | 0 |
   | outcomes not decided (status 1/3/4) | 0 |

3. A row-by-row table against E11's hand derivation
   (`runs/20260729T000000Z-E11-engine-crosscheck-deep/partials/lp_potential-via-exhaustive.md`
   §6): of the 639, **639 are HiGHS status 2 at `bound=10`**, **638 stay
   infeasible at `bound` 100 / 1e4 / 1e6**, and **exactly 1 becomes feasible
   once the box is widened** — seed `17475932563032345095`, campaign index
   2302, weights `[12, 9, 3, 7, -1, 11, 10, -4]`, re-verified in exact
   `Fraction` arithmetic.
   Any mismatch: E11's derivation is authoritative, the census keeps its own
   number, and `RECONCILIATION.md` states which line diverged and why.
   (Note for the record: the ticket's prose says "638 of the 639 silences were
   status 2, the other was the hard-coded `bound=10`". E11 §6 actually says all
   **639** are status 2 *at* `bound=10`, and 1 of those 639 is feasible at a
   wider box. The census tests E11's wording, which is the primary source.)

## P3 — zero_space says its `scope` was not proved

Pass iff, on a trajectory whose cells carry more than
`SUBSET_ENUMERATION_LIMIT = 8` colours:

1. **No** law reports `scope == "global"`. The degraded label is a distinct
   word, so a consumer filtering on `"global"` gets fewer laws, never a wrongly
   promoted one.
2. The degradation is written *positively* into the payload — the shape
   `bench/ladder.py:74-82` uses for an over-budget rung (`proved_unsolvable:
   False` **plus** an `error` naming the budget): the payload carries the limit,
   the truncated cells, and a sentence saying what the label now means.
3. Those extra keys appear **only** on degraded rows. `engine-rig/artifacts/
   candidates.jsonl` is sha256-pinned in `release/MANIFEST.jsonl`
   (`679fe331cbc82191928a63b766c8f853c236756fce27ef71928d9af7078cfdad`) and the
   candidate ids are content-addressed; a payload key added unconditionally
   re-hashes every zero_space row and invalidates a manifest this track does not
   own. **Regenerating the artifacts must leave that sha256 unchanged** — that
   is itself a pass condition.

## P4 — two negative controls that go red on the old behaviour

Both run the **real public entry point** in a **subprocess** and are judged on
the process exit code and on fields of the artifact it writes — not on the
return value of an internal function.

* **N1 — iteration limit.** A real `linprog`/HiGHS call driven to HiGHS status 1
  by a genuine `maxiter` option (not a stubbed solver object). Asserts the
  outcome is **not** `no_linear_pagoda`, that `decided` is false, and that the
  public entry refuses rather than returning `(None, None)`. Exit 0 on hold,
  exit 1 on violation.
* **N2 — more than 8 colours.** A real `zero_space.run` over a trajectory with
  a >8-colour palette. Asserts no emitted candidate payload has
  `scope == "global"` and that every degraded payload carries the budget.
  Exit 0 on hold, exit 1 on violation.

`tests/test_solver_status_bit.py` invokes both as subprocesses and asserts
`returncode == 0`.

**Non-vacuity is part of the pass condition.** With the structured result
collapsed back to a bare `None` (and, for N2, with the degraded `scope`
restored to `"global"`), both controls must exit **1**. A control that stays
green under the reverted engine has not tested anything and this item is not
done.

## P5 — the mutation surface is wider than the test surface

C11's lesson: 18 mutants that happen to correspond one-to-one with 18 tests is
"testing what was tested". The mutation battery must contain strictly more
mutants than the number of assertions written for this item, and must include
mutants nobody wrote a test *for* — in particular mutants that only a survivor
count can reveal. Surviving mutants are reported as survivors, not deleted.

## Out of scope, stated so it cannot be quietly claimed later

* No exact rational infeasibility certificate (Farkas dual) is produced. "No
  linear pagoda exists within the box" remains a HiGHS claim, and E11 §7 already
  says so. Distinguishing status 2 from status 1 does not upgrade it.
* The `bound=10` box is **not** widened and no default is changed. The census
  reports the box-limited silence separately; changing the default would move
  every published number and is a different item.
* `candidates.jsonl`'s schema is not widened for `lp_potential`, for the same
  manifest reason as P3.
* Zero API calls, zero sealed-pile contact, nothing outside `engine-rig/` is
  written.
