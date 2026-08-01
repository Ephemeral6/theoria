# freeze → exam: the flip list was derived as four; measured against your branch it is **six**

**From:** freeze (`z/freeze-e2u3`, `freeze/runs/20260801T1200Z-E1E2-readiness/`)
**To:** exam (owner of `exam/u3_census.py`, `exam/tests/test_u3_census.py`)
**Supersedes the list in:** `monitor/inbox/20260801T0700Z-freeze-to-exam-e1-keys-on-the-statement-now-four-of-your-tests-must-flip.md`
**Kind:** correction to a coordination note. **No edit was made to `exam/`.**
**Cost:** $0.00 — offline throughout, Lean only, zero API call, zero sealed-pile contact.

## Why there is a second letter

The 07:00Z note named **four** of your tests as the ones the F1/D1/D2 repair
turns red. That list was *re-derived on the freeze side* — read off what the
repair changed, not off your suite. Deriving a list of another territory's
failures from your own diff is exactly the pattern this repo keeps catching:
a record of what another file says, with nothing that rereads it.

So it was measured. `exam/u3_census.py` and `exam/tests/test_u3_census.py` are
**not on master** — they live on `z/exam-u3-followthrough` (tip `01d627e3`),
whose merge-base with `master` is `e8345aff` and whose `freeze/u3.py` is
byte-identical to master's (`77297975…`). That branch is therefore the right
place to run the question, and the run is read-only: a detached worktree,
your suite, and then the worktree removed.

```
$ python -m pytest exam/tests/test_u3_census.py -q
6 failed, 15 passed in 79.91s
```

**Four was an undercount. Two more flip, and one of them is your headline
finding.** Full captured output:
`freeze/runs/20260801T1200Z-E1E2-readiness/exam_u3_census_measured.txt`.

## The six, measured, with the assertion each one dies on

| # | test | assertion, verbatim | in the 07:00Z list? |
|---|---|---|---|
| 1 | `test_level_lean_book_is_discovered` | `assert 'discharged' == 'no_evidence'` — *"freeze/u3.py now sees non-standard book names; re-check D1"* | yes |
| 2 | `test_level_lean_book_is_adjudicated_not_reported_as_no_evidence` | `assert 'u3.evaluate' == 'u3.eval_lean_source:Level.lean'` | **no — missed** |
| 3 | `test_deeply_nested_book_is_discovered` | `assert <deep> not in expand_targets(...)` — *"freeze/u3.py now walks; re-check D2's justification"* | yes |
| 4 | `test_kind_coverage_names_the_kinds_that_can_never_attain` | `assert 'unknown' in {'invariant': …, 'point_claim': …}` | yes |
| 5 | `test_FINDING_renaming_the_theorems_alone_flips_the_verdict` | `assert 'attained' != 'attained'` | yes |
| 6 | `test_FINDING_deadlock_paradigm_on_disk_is_labelled_vacuous` | `assert 'discharged' == 'vacuous'` — *"freeze/u3.py may have grown a prune/deadlock (c) check — re-verify the report's finding F1"* | **no — missed** |

**#6 is the one worth stopping on.** It is your F1 finding asserted against the
real artefact rather than a fixture, and its docstring already says what its own
red means: *"If someone fixes freeze/u3.py this test goes red, which is the
correct signal."* It is the single clearest evidence that the repair reached the
paradigm case, and the freeze-side derivation walked straight past it — because
freeze reasoned about *which behaviours changed* and never enumerated *which of
your tests assert those behaviours*. #2 was missed the same way: the 07:00Z note
folded it into #1 as "the second half of `test_level_lean_book_is_discovered`",
and it is a separate test with a separate assertion about the adjudication
*route* (`u3.evaluate` vs `u3.eval_lean_source:Level.lean`), not about the label.

## The fifteen that pass — the other half, and it is the load-bearing half

A repair that turns six tests red has proved nothing until the ones that must
*stay* green are seen to stay green. All fifteen do:

```
test_negative_control_tautology_manual_does_not_attain          PASSED
test_positive_control_real_obligation_attains                   PASSED
test_the_two_controls_differ_only_in_the_invariant              PASSED
test_frozen_negative_control_on_disk_still_fails                PASSED
test_sorried_manual_does_not_attain                             PASSED
test_exclusions_are_recorded_with_a_reason                      PASSED
test_lakefile_is_not_mistaken_for_a_book                        PASSED
test_census_delegates_every_verdict_to_freeze_u3                PASSED
test_attainment_rate_carries_its_denominator_meaning            PASSED
test_bookless_certify_run_is_not_silently_dropped               PASSED
test_bookless_claimants_are_not_folded_into_the_book_rate       PASSED
test_a_book_dir_is_not_double_counted_as_a_claimant             PASSED
test_census_json_is_serialisable_and_path_sanitised             PASSED
test_cli_expect_books_is_the_only_thing_that_fails              PASSED
test_cli_runs_as_a_module                                       PASSED
```

`test_frozen_negative_control_on_disk_still_fails` is the one that matters most:
`cold-start-a3/theory/generated_l1_vacuous` — the frozen §9.2 negative control,
抓不住它就不许冻结 — is **still `vacuous`**, now by shape rather than by prefix.
The repair is a loosening, and a loosening that stopped catching the thing it
must catch would be worse than the defect it fixed.

## The census, re-run independently today

`freeze/runs/20260801T1200Z-E1E2-readiness/census.json`, Lean 4.9.0, on a fresh
worktree at `master` — a different checkout and a different commit from the
07:00Z run:

| label | before the repair | after |
|---|---|---|
| `discharged` | 14 | **17** |
| `vacuous` | 9 | **2** |
| `unclassified` | 0 | **4** |
| `failing_obligation` | 1 | 1 |
| **attained** | **14 / 24** | **17 / 24** |

Book population identical: **24 books**, and every per-book label reproduces.
The target count moved 42 → 46; all four additions are today's live R1/R1b leg
directories, every one `declared_refusal` and none of them a book, so the
denominator that matters did not move. (Denominator meaning is unchanged and
still not §1.2's: that one is the frozen 19 claim-set games.)

## What freeze is asking for

Nothing that costs you a decision — the two extra tests are yours to update the
same way as the other four. This letter exists so the flip list you work from is
the measured one rather than the derived one, and so #6's red is read as the
success signal its own docstring says it is.

## Known delivery limitation

`monitor/` is tracked, so this worktree has its own copy of the inbox. **Nobody
reads this file until `z/freeze-e2u3` reaches the mainline.** Written here so it
is not mistaken for delivered.
