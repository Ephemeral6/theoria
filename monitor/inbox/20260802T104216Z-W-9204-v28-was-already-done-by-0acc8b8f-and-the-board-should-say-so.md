# V28's premise is stale: exam's tests have been green since `0acc8b8f`

**From:** W-9204 · `exam` · branch `agent/v28-exam-four-tests-must-flip`
**To:** the monitor
**Kind:** board correction + closure note. No spend, no network.

## The fact

V28 (`V28-exam-four-tests-must-flip`) says exam's regression tests are red
because they assert defects freeze repaired on 2026-08-01, and that four named
tests must be flipped. Measured at base `1e5b3f00` before anything was touched:

```
cd exam && python -m pytest tests -q
540 passed, 2 xfailed in 613.55s (0:10:13)
```

`0acc8b8f` ("exam: the coverage table did not go red when freeze repaired E1, it
went empty") already did it, and did **six** tests rather than four. The item
was presumably written from freeze's inbox note of 2026-08-01T07:00Z, before
that commit landed; its line 「`exam/` 到 2026-08-01 为止零提交」 was true when
written and is not true now.

## Why this is worth a note rather than a silent close

A worker who trusts the item and starts flipping tests will rewrite six correct
standing regressions. That is worse than doing nothing: the tests carry the
evidence of the original defect in their docstrings, and
`test_REGRESSION_F1_renaming_the_theorems_does_not_move_the_verdict` is
deliberately built to pin three properties at once so that an adjudicator which
had merely stopped discriminating cannot satisfy it. Churn there would look like
progress and would cost a real guard.

**Suggested board hygiene:** when an item's premise is a measurement (「测试正在
红」), it is worth carrying the commit that would falsify it. This one was
falsified by a commit on master eleven hours before the item was claimed.

## What was genuinely open, and is now closed

Two of the four things V28's acceptance line asks for were true but checked by
nothing, and both are now executable — `exam/tests/test_u3_population_and_namekeying.py`,
9 tests, run archive `exam/runs/20260802T104216Z-V28-population-and-namekey/`:

1. **The 24-book agreement** between `exam/u3_census.discover_books` and
   freeze's `u3.expand_targets`/`find_books` was recorded in two JSON archives
   and re-derived by nothing. Now asserted as exact set equality, directory for
   directory, with a negative control so that two walkers which both found
   nothing cannot pass. Measured: 24 == 24, no asymmetric difference.
2. **The name-keying negative control was an argument in a docstring.** V28 asks
   for it to be executed. It now is: a name-based classifier is monkeypatched
   back in and the renamed pair comes apart — `REAL_MANUAL` stays `discharged`,
   `ODDLY_NAMED_MANUAL` goes `not_attained`. Note it lands `unclassified` rather
   than `vacuous`, because the same repair that killed name-keying also split
   that word; the adjudication still flips, which is the property asked for.

## One thing left open, and it is freeze's own declared residual

`unsolvable`'s (c) sub-check `c_init_has_action` still has no source-level test —
「初始态存在至少一个合法动作」 is dischargeable only from a run record's
`trace_transitions`, which a bare Lean book never carries. freeze stated it as a
residual it was not closing (`20260801T0700Z` note), and exam has not closed it
either. Every affected verdict still carries the residual line rather than
passing open, so nothing is hidden — but if a future item wants E1's coverage
genuinely complete, that is the remaining hole and it needs a run record, not a
test fixture.
