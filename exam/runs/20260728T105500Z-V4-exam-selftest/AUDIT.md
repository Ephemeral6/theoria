# What V4 asked for, and what was already on disk

Measured on branch `agent/v4-exam-selftest` at its base `98593a0`, **before any
edit**. Every row is a command and its output, not a reading of the docs.

## Baseline

```
$ python -m pytest exam/tests -q
253 passed in 38.44s
```

`exam/STATUS.md` says "157 passed, 1 skipped". That line is stale by 96 tests —
V2-exam-on-worldgen added them and did not update it. Recorded here, fixed in
this run's STATUS edit.

## Ask (1) — 判卷器标定，已知满分与已知零分的假被试

```
$ python -c "from exam.grading.calibration import calibrate_all; ..."
calibrated: True | failures: 0
  heldout    {'oracle': 1.0, 'null': 0.0, 'memoriser': 0.575,  'bluffer': 0.45}
  handover   {'oracle': 1.0, 'null': 0.0, 'memoriser': 0.7174, 'bluffer': 0.3261}
  adaptation {'oracle': 1.0, 'null': 0.0, 'memoriser': 0.1708, 'bluffer': 0.1708}
  verdict    {'oracle': 1.0, 'null': 0.0, 'memoriser': 0.5882, 'bluffer': 0.2647}
```

**Delivered.** Four fakes, `oracle == 1.0` and `null == 0.0` exact on all four
papers, pre-registered bands, and `assert_calibrated` refuses to mark a real
submission when a band misses. The item's parenthetical — 现在没人验过判卷的人
— was true when P-15 started and is no longer true *as literally stated*.

**But it is still true in the way that matters,** and this is the finding that
set this run's plan:

> `oracle == 1.0` and `null == 0.0` pin the marker at its two **endpoints**.
> Nothing on master perturbs a submission by a known amount and checks that the
> score moves by exactly the predicted amount; nothing breaks the marker on
> purpose and checks that the calibration notices.

A marker that is exact at both endpoints and arbitrary in between passes
everything master has. Two named holes follow from that, both already
self-reported by the code rather than discovered here:

* `exam/grading/calibration.py`, comment above `EXPECTED`: "the rubric digest
  does not cover this file, so a quiet widening here would not show up as a
  digest mismatch". `STATUS.md` open weakness 3, same fact. One band has already
  been widened once (D-EX-010) — legitimately, and recorded, but the mechanism
  that would catch an *unrecorded* widening does not exist.
* Nothing anywhere tests the marker for order dependence. `mark()` iterates
  items in key order and rubrics are contractually pure, but "contractually
  pure" is a comment, not a check.

## Ask (2) — 三类判决题各出一题，带构造性依据登记

```
$ python -c "...verdict.build(); Counter(truth['class'])..."
classes: {'solvable_hard': 8, 'large_unsolvable': 4, 'small_unsolvable': 5}
claims:  {'solvable': 8, 'unsolvable': 9}
n items: 17
$ ls exam/artifacts/variant_specs/ | wc -l
17
```

**Delivered, and past the ask.** The item wants one item per class; the paper
carries 5 / 4 / 8, every one with a constructive justification emitted in
`proxy.variants` spec format and validated by constructing a real `Variant`.
The `class` field lives in the **truth** side only — `sheet_side()` keys are
`board, budget, commands, hazards, kind, level_id, objective, question,
relabelled, win_requires, world`, with no `class` among them, so the class is
not a tell on the sheet.

Writing three more items here would add nothing and would dilute a paper whose
mix is already calibrated. **Not rebuilt.** What this run adds instead is the
per-class *reading* of the results, which did not exist — see ask (3).

## Ask (3) — 灵敏度与特异度分开打分，并出一张矩阵

`grading/mark.py:confusion()` returns the pair and refuses to blend it; the
docstring cites Theoria.md 1.11. `calibration._type_specific` asserts the
bluffer at sensitivity 1.0 / specificity 0.0.

**Half delivered.** The pair exists for **one** fake on **one** paper, as a
pass/fail assertion. There is no matrix: no examinee × class table, and no
per-class split at all. That split is the whole reason classes (i) and (ii) are
separate question classes rather than one "unsolvable" bucket —

> an arm whose sensitivity is 1.0 entirely because it aces `small_unsolvable`
> (where exhaustive search answers correctly, for a reason that does not
> transfer) and 0.0 on `large_unsolvable` (where only an invariant can answer)
> has the *same* headline sensitivity as an arm that reasons.

A single blended sensitivity hides exactly the distinction the paper was built
to expose. `artifacts/matrix/` exists but holds one file,
`heldout_worldgen.json`, from V2 — nothing for verdict.

## Red line — the cheater subagent

`STATUS.md` open weakness 11: "Two cheater agents, four sheets, one pass. **No
adversarial reader has seen the fixed sheets.**" The two leaks the first pass
found were fixed after it ran, so the sheets now in `artifacts/papers/` have
never been attacked. The item makes a cheater pass an acceptance condition, and
here it is also the one piece of the original protocol that is genuinely owed.

## Conclusion

Two of the three asks are already delivered; saying so and stopping would meet
the item's letter and miss its point. The work this run does instead:

1. the marker's **middle range**, by mutants with exactly predicted scores;
2. **fault injection into the marker itself**, with a detection matrix whose
   zeros are the report;
3. the **sensitivity/specificity matrix**, split per verdict class;
4. close open weakness 3 — extend the digest to cover the bands and the marker;
5. the **cheater pass against the fixed sheets**.
