# GATE-OUTPUT — `python exam/verify.py` on `cleanup2/v2exam`, base `6fabcc7e`

Verbatim, with the machine's temp path elided to `<TMP>` per D-EX-031. That path
is where the producers wrote instead of into `exam/artifacts/`.

## The new stage

```
== artifacts_match_committed
==============================================================================
working tree vs HEAD under exam/artifacts: clean
comparing an existing build: <TMP>\exam-verify-6wh_hbwz\artifacts
producers rewrote 32 of 41 tracked artefacts; 0 of those differ from the seed
artifacts match committed: 41 tracked files, all reproduced

```

## Summary

```
== summary
==============================================================================
  build_papers               ok
  pytest                     ok
  run_exam --calibrate       ok
  run_selftest               ok
  artefact_locations         ok
  artifacts_match_committed  ok
  determinism                ok

GREEN
```

## The tracked tree after the run

```
$ git status --porcelain exam/artifacts
(empty)
```

Nothing under `exam/artifacts/` changed during a full verify run — the point of
the restructure, and false before it.

## pytest, inside the run

```
489 passed, 2 xfailed in 166.29s (0:02:46)
```

Baseline on `master` before this branch: `481 passed, 2 xfailed in 161.84s`.
The eight new tests are `exam/tests/test_artifacts_match_committed.py`.
