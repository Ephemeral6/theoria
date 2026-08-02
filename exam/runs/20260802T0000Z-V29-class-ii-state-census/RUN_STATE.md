# V29 — class (ii)'s state space, counted

## The question

Class (ii) of the verdict paper is "large-space unsolvable" and carries a share
of the third primary endpoint. The number that made it large was
`subset_lower_bound`'s 2^m — a floor proved from a construction, never a count —
and the shipped truth record said `enumeration_attempted: false` beside
`enumerated: null`. The brief asked for three things: compute the state space
for every class (ii) item; move any item that turns out to be exhaustively
decidable into class (i); and if none survives, report that the class has no
instance.

## What was found

**All four items survive, and the class is not empty.** Three are now counted
exactly on the shipped board; the fourth is bracketed.

| item | board | state space | method |
|---|---|---|---|
| ii1 `vq-721d09813c` | gantry k=60 | 159,507,359,494,189,904,748,456,847,233,641,349,120 | symbolic, exact |
| ii2 `vq-6150a6eeb7` | lattice k=60 | 159,507,359,494,189,904,748,456,847,233,641,349,120 | symbolic, exact |
| ii4 `vq-2986ed8ffc` | orchard k=60 | 886,151,997,189,943,915,269,204,706,853,563,048 | symbolic, exact |
| ii3 `vq-ee54166153` | spindle, budget 150 | 1.661e37 .. 4.133e63 | two-sided bracket |

Every number clears the 2^m the construction proves — by 120x, 120x and 8/3x,
and for ii3 the bracket's *lower* side alone is 19 orders of magnitude above the
2^60 that was being published for it.

**The brief's premise was half stale and is corrected rather than followed.**
It read the class as claiming "only invariant reasoning can answer this". That
claim was already withdrawn (D-EX-028): every class (ii) item is settled by an
exhaustive computation over at most 600 nodes. Nothing here revives it. What was
genuinely missing was the census, and the census does not bear on the
withdrawal — the count says the *naive* method cannot run, the 600 nodes say
*a* method can, and both now sit on the same record under a test that fails if
either is dropped.

## What was built

* `exam/state_space.py` — three instruments in order of what they assume:
  the naive enumerator itself (`naive_reach`), symbolic reachability over a BDD
  of the latch mask (`exact_count`), and a two-sided bracket for budgeted combs
  (`budgeted_bracket`). Each is a positive whitelist that refuses with a reason
  rather than falling back; a counter that guesses when its premise fails
  produces a number indistinguishable from a count.
* `exam/tools/state_census.py` — the table, recomputed live, reading nothing
  from `artifacts/`.
* `exam/tests/test_state_space.py` — 111 tests. The load-bearing one runs the
  census and the naive enumerator on the same constructor+operator families at
  every size the enumerator can finish (k=2..6) and requires exact agreement.

## Gate outputs

* `python -m pytest exam/tests -q` — see `gates.txt`.
* `python exam/verify.py` — see `gates.txt`.

## What is not closed

* **The ii3 bracket is 26 orders of magnitude wide.** Both sides are sound and
  computed; the true count is not known. Closing it needs a minimum-cost walk
  model that handles a walk traversing an alcove row horizontally, which is
  exactly where the simple `2 commands per dip` cost formula fails. Measured and
  left open rather than approximated.
* **Brute force can only check the census where brute force can run**, k=2..6
  against a shipped k=60. What is extrapolated is the method, not a fitted
  curve, but no independent instrument has confirmed 1.595e38 and none can.
* One pre-existing suite failure is environmental and unrelated:
  `test_u3_census.py::test_REGRESSION_F1_deadlock_paradigm_on_disk_attains`
  fails on this machine with Lean reporting `out of memory`, on the baseline
  commit as well as here.
