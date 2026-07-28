# CONFLICT-origin_agent_e9-engine-paper-table.md
branch: origin/agent/e9-engine-paper-table
reason: verify gate red in fuzzlab (verify.py)

```
[ok  ] oracle and battery tests
        ........................................................................ [ 96%]
        ...                                                                      [100%]
[ok  ] campaign smoke, all six engines
          "worlds_checked": 360
        }
        
        -> out\campaign.json
[FAIL] engine-rig's own suite (the tree under test)
                    "or the table was not regenerated (`python -m tools.engine_table`)."
                )
        E       AssertionError: ENGINE_TABLE.md disagrees with the runs under it. Either a run was edited (re-read it, then update the expectation in tools/engine_table.py) or the table was not regenerated (`python -m tools.engine_table`).
        E       assert 1 == 0
        
        tests\test_engine_table.py:29: AssertionError
        ---------------------------- Captured stderr call -----------------------------
        engine_table: 1 fact(s) disagree with their artifacts:
          rig.campaign_worlds: artifact says 60, table expects 500
              at fuzzlab/out/campaign.json :: worlds_per_engine
        
        The table was NOT written. Re-read the run, then update the expectation.
        =========================== short test summary info ===========================
        FAILED tests/test_engine_table.py::test_the_table_is_current_and_every_fact_still_matches_its_artifact

last campaign totals: {"generator_errors": 0, "invariants": 23, "raised": 0, "skipped": 12, "violated": 0, "worlds_checked": 360}

FAILED: engine-rig's own suite (the tree under test)

```
