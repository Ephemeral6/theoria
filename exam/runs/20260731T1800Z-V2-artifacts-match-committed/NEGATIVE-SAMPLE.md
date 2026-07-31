# NEGATIVE-SAMPLE — one flipped byte, and the stage that still went green

The ticket's fourth item, run as an experiment rather than argued.

## The edit

One value inside one tracked artefact, chosen to be invisible to every schema
check in the territory:

```
exam/artifacts/calibration.json
-      "fraction": 1.0
+      "fraction": 1.1
```

`git diff --stat -- exam/artifacts` → ` exam/artifacts/calibration.json | 2 +-`.

## Dirty tree — `python exam/verify.py`

```
== artifacts_match_committed
==============================================================================
working tree vs HEAD under exam/artifacts: DIFFERS
exam/artifacts/calibration.json | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
comparing an existing build: <TMP>\exam-verify-8rrq3a_j\artifacts
producers rewrote 32 of 41 tracked artefacts; 1 of those differ from the seed
  MISMATCH  exam/artifacts/calibration.json

What is committed under exam/artifacts is not what this code produces. Two dispositions and they are not interchangeable: if the artefacts are stale, rebuild them (`python -m exam.tools.build_papers`, `run_exam --calibrate`, `run_selftest`) and commit the diff with the reason; if the generator changed by mistake, revert the generator. Deciding which is a judgement, so this gate reports and does not adopt.

```

```
== summary
==============================================================================
  build_papers               ok
  pytest                     FAILED(1)
  run_exam --calibrate       ok
  run_selftest               ok
  artefact_locations         ok
  artifacts_match_committed  FAILED(1)
  determinism                ok

RED: pytest, artifacts_match_committed
```

Two stages red, and the interesting line is the one that stayed green:
**`determinism` passed**, byte-identical digests under both hash seeds. That is
exactly the old gate set's blind spot — two fresh builds agreeing with each other
say nothing about the file on disk — and it is why this ticket existed.

`pytest` going red as well is not redundancy: the same two questions are pinned
as tests, so a reader who runs only the suite still sees it.

## Clean tree — the same command

Restored with `git checkout -- exam/artifacts/calibration.json`; the full run is
in `GATE-OUTPUT.md`, ending:

```
  artifacts_match_committed  ok

GREEN
```

Both directions, because a gate that always reports drift is as green in a
one-sided test as one that always reports a match.
