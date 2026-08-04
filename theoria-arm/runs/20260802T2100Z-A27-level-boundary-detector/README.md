# A27 — the level boundary, the second witness, and the denominator

Offline. No ARC action, no model call, no network, no ledger, $0.

## The board item, and where the evidence contradicts it

> the arm cannot see a win even if it gets one

Half right, and the half that is right is the expensive half.

**The arm does see the win.** `inner/loop.py:_record` passes `levels_completed`
off *every* gameplay envelope into `LevelLog.observe`, and an increase fires
`_on_level_boundary` on that same call — mid-leg, before `_record` returns.
`_main_loop` reads `state == "WIN"` at the top of every turn and drives
`_try_advance_level`. Both of ARC's two plausible level signals have been
handled since `inner/levels.py` was written. `LEVEL_SIGNAL_UNKNOWN` is a note
about *which* signal fires, not about whether either is watched.

**The arm does not see the price of one.** `score`, `level_scores`,
`level_actions`, `level_count` and `level_baseline_actions` appear on no ARC
gameplay response — `_summary` says it in one line, `"score": None` — and the
only code path that ever fetched a scorecard was `close_scorecard`, called from
`_finish`, *after* `_main_loop` has returned, on a card D-015 records as
unrecoverable once closed. Every scorecard-side fact about a leg arrived
strictly after the leg could act on it.

That is what makes the ticket's decisive number decisive. g50t level 1 costs a
reference solver **78** actions. The best leg this arm has ever run spent **33**.
That ratio sat in a document the arm could have asked for at any moment, for
free, from the first RESET onward — and the arm asked once, at the end, where it
is a post-mortem.

`Theoria.md` Phase 2 layer 4 is often cited here as licensing a score-jump
derivation: *level 若非 API 字段则由 score 跳变推导*. It is an API field, so that
clause does not apply. The clause in the **same paragraph** that is still owed is
the other one: *账本推得的分数必须等于 API scorecard 分数,不等 = incident*. See
GAP A27-4.

## What is in this directory

| file | what it is |
|---|---|
| `measure_boundaries.py` | reads every `*.jsonl` under the three arms' `runs/` and counts boundaries, states, scorecards and baselines. No network. |
| `MEASUREMENT.json` | its output. |
| `GATES.txt` | the three gates, verbatim. |
| `RUN_STATE.md` | the narrative. |
| `make_manifest.py` / `MANIFEST.json` | provenance, rendered through `armtools.backfill.render`. |

## The answer to A27's fourth question

**No recorded leg contains a boundary to detect.** Across 2,700 `env_step` rows
in `theoria-arm`, `baseline-arms` and `ablation-arm`, `levels_completed` is `0`
on the 547 rows carrying it and absent on the other 2,153; `state` is
`NOT_FINISHED` on all 547 and never `WIN` or `GAME_OVER`. All 47 recoverable
scorecards read `total_levels_completed: 0`, `score: 0.0` and all-zero
`level_scores`. The only `WIN` rows anywhere in the repository belong to
`ablation-arm`'s offline A0/A2 worlds and to a `proxy/` mock probe.

So every positive case in `tests/test_scoreboard.py` is synthetic, and the
detector is **untested on a real positive**.
`test_no_recorded_leg_contains_a_real_boundary` asserts that state of the record,
so it fails on the day it stops being true.

## What the scan found that nobody was looking for

`level_baseline_actions: [8, 8, 8]` with `level_count: 3` is recorded against
**three different game ids**. A roster belongs to one game, so that vector is not
a roster — it is `proxy/mock`'s constant. Seven ledger files carry it. Unlabelled,
it would make a mock leg's `reach` report read `at_or_above_reference` against a
reference cost of 8 where the real g50t level 1 is 78. `ScoreWatch` therefore
carries the leg's `offline` flag and labels the number. GAP A27-5.

## Reproduce

```bash
cd theoria-arm/runs/20260802T2100Z-A27-level-boundary-detector
python measure_boundaries.py
python make_manifest.py
cd ../.. && python -m pytest -q && python verify.py && python -m armtools.verify_provenance
```
