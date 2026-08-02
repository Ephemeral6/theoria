# V28 — running notes

**Cell:** V28 · **Territory:** `exam` · **Worker:** W-9204 · **Branch:**
`agent/v28-exam-four-tests-must-flip` · **Base:** `1e5b3f00`
**Spend:** $0.00 — no ARC action, no model call, no network, zero sealed-pile
contact. `freeze/` read only.

---

## 1. The board item is stale, and saying so is most of the work

V28 says exam's regression tests are red because they assert defects freeze
repaired on 2026-08-01, and asks for four named tests to be flipped. **They were
already flipped**, by `0acc8b8f` ("exam: the coverage table did not go red when
freeze repaired E1, it went empty"), which is on master. That commit did more
than the inbox note asked:

* it flipped **six** tests, not four — freeze's note named four; the two it did
  not name are `test_level_lean_book_is_adjudicated_not_reported_as_no_evidence`
  and `test_FINDING_deadlock_paradigm_on_disk_is_labelled_vacuous`. The commit
  message puts both on the record precisely because *"four tests must flip" is
  the kind of claim a later reader checks by counting*;
* it kept the evidence of the defect in every docstring and inverted only the
  assertions;
* it fixed a defect of its own finding: `kind_coverage()` decided "this kind has
  no (c) check" by sniffing for the substring `"no executable"` in E1's `why`
  text. The repair stopped writing that sentence, so the coverage table reported
  `kinds_that_can_never_attain: []` — a clean bill of health manufactured by a
  lookup miss, on the one output whose whole job is reporting gaps. It keys on
  the exported `theorem_shape.KINDS_WITH_A_C_CHECK` now.

So the honest V28 deliverable is not "flip the tests". It is: **verify the
acceptance line item by item, and close the parts of it nothing executes.**

## 2. What the acceptance asks, and where each part actually stood

| acceptance item | status on arrival |
|---|---|
| `pytest exam/tests -q` green | see §4 |
| `u3_census.py` agrees with freeze's D2 on the book population (24, both sides enumerating independently) | agreed **in two JSON archives**, re-derived by nothing |
| negative sample 1 — re-install a name-based kind classifier, `vacuous`/`discharged` must flip | **argued in a docstring, never executed** |
| negative sample 2 — an `unclassified` theorem must make the development fail closed | covered at the census layer by `test_kind_coverage_reports_a_real_gap_as_a_gap` |

Two of the four had no executable check. That is the gap this run closes.

## 3. Measured before asserted

**The populations.** `probe_enumeration.py`, run in this worktree:

```
exam   : 24
freeze : 24
agree  : True
only exam   (0): []
only freeze (0): []
```

Exact set equality, directory for directory, across two genuinely independent
walkers: exam's `discover_books` uses `os.walk` to arbitrary depth and filters
`.lean` files by **name** (`SCAFFOLD_NAMES`); freeze's `expand_targets` bounds
depth at `max_depth=12`, excludes by directory name, and admits a file only if
`states_a_theorem` finds a `theorem`/`lemma` in it — **content**. One filters by
name where the other filters by content; one bounds depth where the other does
not. That is why the agreement is worth pinning, and it takes no Lean.

**The name-key control.** `probe_namekey.py`. Repaired adjudicator first:

```
REAL_MANUAL          label=discharged     kinds=['invariant', 'point_claim'] hints=['invariant']
ODDLY_NAMED_MANUAL   label=discharged     kinds=['invariant', 'point_claim'] hints=[None]
TAUTOLOGY_MANUAL     label=vacuous        kinds=['invariant', 'point_claim'] hints=['invariant']
```

Then with a name-keyed classifier monkeypatched back in:

```
REAL_MANUAL          label=discharged
ODDLY_NAMED_MANUAL   label=unclassified
```

The pair comes apart on a rename alone. Two things worth stating exactly,
because a control described loosely is a control nobody can check:

* It flips to **`unclassified`, not `vacuous`.** Before 2026-08-01 one word
  carried both meanings and this rename produced `vacuous`; the same repair that
  killed name-keying also split the word, so an unrecognised name now lands in
  the fail-closed bucket. The adjudication still flips — `attained` to
  `not_attained` — which is the property V28 asks to see move.
* The whole control runs at the **judgment layer** (`u3.judge_development` with
  `compiles=True` and a synthesised empty axiom report), so (a) and (b) are
  granted and only (c) can decide. No Lean, no disk, sub-second.

## 4. Gates

`python -m pytest exam/tests -q` is slow here — `u3.find_lean()` resolves to a
real toolchain on this box, so the `needs_lean` tests genuinely compile rather
than skipping, and the suite takes ten minutes rather than seconds. A run that
reports the same totals in far less time was probably skipping them; check
`find_lean()` before reading it as agreement. Baseline and post-change runs are
recorded in
`GATES.txt` rather than in this file, so the numbers sit next to the commands
that produced them.

## 5. What this run does not do

1. **It does not re-litigate `0acc8b8f`.** The six flipped tests are read and
   checked against freeze's inbox note; they are not rewritten.
2. **It adds no coverage for `unsolvable`'s (c) sub-check `c_init_has_action`**,
   which freeze declared as an open residual it is not closing: 「初始态存在至少
   一个合法动作」 is dischargeable only from a run record's `trace_transitions`,
   which a bare Lean book never carries. Still open, still exam's instrument to
   keep pointing at.
3. **`EXPECTED_BOOKS = 24` is a constant in a test.** If books are genuinely
   added the test fails and a human must update it and both run archives. That
   is the intended cost — the alternative is a population guard that agrees with
   whatever it finds.
