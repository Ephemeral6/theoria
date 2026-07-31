# Every gate added by this ticket, observed red

> 一个从没说过「不」的检查，没有被证明检查了任何东西。

Four gates land here. Each one is shown failing on a real input before it is
claimed to work, and the input is named so the failure can be reproduced.

---

## 1 · `check_withdrawn_claims` on the tree as it stood at `master`

The pre-fix source of `confusion_matrix.py`, and — the one that matters — the
**generated artefact** built from it:

```
$ git show master:exam/grading/confusion_matrix.py > /tmp/prefix_confusion_matrix.py
$ python -c "from exam.tools import check_withdrawn_claims as cw; print(cw.scan(['/tmp/prefix_confusion_matrix.py']))"
exam/grading/confusion_matrix.py (at master):12 [only-invariant-en]
hits: 1

$ git show master:exam/artifacts/matrix/verdict_confusion.json > /tmp/prefix_matrix.json
$ python -c "... cw.scan(['/tmp/prefix_matrix.json'])"
matrix artifact at master, hits: 1
  line 3 only-invariant-en :: "large_unsolvable": "(ii) 2^60 to 2^120 configurations; only an invariant can answer",
```

D-EX-028 withdrew that sentence on 2026-07-30. It was still in a tracked,
generated artefact on 2026-08-01, which makes the artefact the version a reader
quotes and the decision log the version nobody reads.

Whole-tree scan before the fixes: **8 hits in 105 tracked files**, in
`STATUS.md` (×3), `artifacts/matrix/verdict_confusion.json`,
`grading/confusion_matrix.py`, `grading/rubrics_verdict.py`,
`papers/verdict.py` and `tests/test_verdict.py`. After: 0.

**The scanner was also seen to be wrong in the other direction, twice, and both
times the measurement is what said so.**

* First version had no acquittal window and reported **63 hits**, nearly all of
  them records *of* the withdrawal — including `README.md`'s own sentence
  announcing it. A scanner that fires on the fix gets switched off within a day.
* First version also scanned `exam/runs/**`, the provenance archive, whose
  V23 directory quotes the withdrawn field name on nearly every page **because
  that is what it was investigating**. Demanding those be rewritten would be
  asking for the record to be falsified.

## 2 · `S_min` disabled — the specificity floor

```
$ python -c "from exam import endpoint as ep, prereg; ep.S_MIN = 0.0; print(prereg.check_controls())"
 - control overclaimer was judged '成立', pre-registered '不成立'
 - control abstainer   was judged '不可结论', pre-registered '不成立'
 - control null        was judged '不可结论', pre-registered '不成立'
```

`overclaimer` becoming **成立** is the point: sensitivity 1.000, specificity
0.375, BA 0.688, full class-(ii) coverage. It clears every other floor.

**This gate was green when it should not have been, and that is why
`overclaimer` exists.** The first control set was `bluffer`, `abstainer`,
`null`; with those three, `prereg.floor_leave_one_out()` returned
`{"without_S_min": []}` — deleting the specificity floor changed no verdict at
all, because all three also fail the BA floor. The floor `STATS_RULES.md` §2.2
calls a 一票否决 had never been observed to cast a vote.

## 3 · `c_min` disabled — the class (ii) coverage floor

```
$ python -c "from exam import endpoint as ep, prereg; ep.C_MIN = 0.0; print(prereg.check_controls())"
 - control memoriser was judged '成立', pre-registered '不可结论'
```

The memoriser answers 0 of 4 large-space items and its converted pair is
0.556 / 0.625 — enough for both other floors. This is `launch_blockers.json`
9.16 verbatim: *an arm that has never answered the class the campaign exists to
test*.

## 4 · The conversion removed — the floor with no total order

The abstainer, scored by the marker rather than by the endpoint layer:

```
observed pair for abstainer (what mark.confusion reports): None None
obs_spec < 0.5 raises TypeError: '<' not supported between instances of 'NoneType' and 'float'
converted pair: 0.0 0.0
```

`launch_blockers.json` 9.15 in three lines: the pre-registered veto is
`specificity < ⟨S_min⟩`, and against the implementation §2.2 cites, an arm that
abstains on every class-(iii) item makes that expression not false but
*undefined*. Under 弃权计错 the same transcript reads 0.0 / 0.0 and the floor
applies.

## 5 · The pre-registration itself, mutated

Pinned by `tests/test_prereg_verdict.py`, each with a named break:

| mutation | what turns red |
|---|---|
| item mix 5/3/9 instead of 5/4/8 | `class sizes are …, pre-registered …` |
| `SEARCH_CREDIT = 1.0` | `rubric weights are …, pre-registered …` |
| drop the (theoria, large_unsolvable) row | `0 expectations for (theoria, large_unsolvable)` |
| a confusion cell missing `unclassified_on_positive` | `KeyError` from `abstain_as_wrong` — a conversion that silently missed an escape would restore the defect it closes |
| a cell whose converted denominator ≠ the declared class size | `AssertionError` — an item was lost on a path the conversion does not know about |
