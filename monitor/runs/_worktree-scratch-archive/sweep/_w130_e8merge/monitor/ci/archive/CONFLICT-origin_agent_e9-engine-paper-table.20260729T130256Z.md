# CONFLICT-origin_agent_e9-engine-paper-table.md
branch: origin/agent/e9-engine-paper-table
reason: verify gate red in engine-rig (verify.py)
tip: 139ed99cade1b3c9a84103e44cb3989e3b35a7b7
first_seen: 2026-07-29T04:16:53Z
last_seen: 2026-07-29T04:16:53Z
attempts: 1

```
[1/3] suite
   FAIL  suite red (exit 1)
.......ss.................ss............................sssss........... [ 13%]
............sss......................................................... [ 27%]
.....................F.................s................................ [ 40%]
....ss.................................................................. [ 54%]
........................................................................ [ 67%]
........................................................................ [ 81%]
..........................ssss...s.........s..s..s...........ssss....... [ 94%]
...........................                                              [100%]
================================== FAILURES ===================================
_____ test_the_table_is_current_and_every_fact_still_matches_its_artifact _____

    def test_the_table_is_current_and_every_fact_still_matches_its_artifact():
        rc = engine_table.main(["--check"])
        if rc == 3:
            pytest.skip("an artifact ENGINE_TABLE.md is built from is not on this machine")
>       assert rc == 0, (
            "ENGINE_TABLE.md disagrees with the runs under it. Either a run was "
            "edited (re-read it, then update the expectation in tools/engine_table.py) "
            "or the table was not regenerated (`python -m tools.engine_table`)."
        )
E       AssertionError: ENGINE_TABLE.md disagrees with the runs under it. Either a run was edited (re-read it, then update the expectation in tools/engine_table.py) or the table was not regenerated (`python -m tools.engine_table`).
E       assert 1 == 0

tests\test_engine_table.py:29: AssertionError
---------------------------- Captured stderr call -----------------------------
engine_table: 3 fact(s) disagree with their artifacts:
  rig.campaign_worlds: artifact says 60, table expects 500
      at fuzzlab/out/campaign.json :: worlds_per_engine
  rig.mutants: artifact says 64, table expects 55
      at fuzzlab/out/mutation.*.json :: sum over the six mutation.<engine>.json of len(mutants)
  rig.survivors: artifact says 14, table expects 15
      at fuzzlab/out/mutation.*.json :: sum over the six mutation.<engine>.json of count(survived)

The table was NOT written. Re-read the run, then update the expectation.
=========================== short test summary info ===========================
FAILED tests/test_engine_table.py::test_the_table_is_current_and_every_fact_still_matches_its_artifact

[2/3] one real run -- eight engines end to end, offline
   ok    wrote candidates.jsonl
[3/3] artefact self-check

engine-rig: RED (1 problem(s))

```
