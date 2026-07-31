# CONFLICT-origin_master.md
branch: origin/master
reason: BASE RED in monitor (verify.sh): origin/master fails this gate on its own
tip: 3be306394b76bbdfab17e5d02e54c3bfcbe7f8da
base: 3be306394b76bbdfab17e5d02e54c3bfcbe7f8da
first_seen: 2026-07-30T21:43:49Z
last_seen: 2026-07-30T22:23:20Z
attempts: 10

```
--- cause lines (lifted out of the transcript) ---
== tests              FAILED(1)
E        +    where ['RES-1', 'RES-2', 'RES-3', 'RES-4', 'OPS-M', 'OPS-A'] = standing.STANDING_ORDER
>       assert launches == standing.MAX_STANDING, (
E       AssertionError: the cap must still bind on healthy launches: 0
E       assert 0 == 5
E        +  where 5 = standing.MAX_STANDING
FAILED tests/test_scan_failure_exit.py::test_a_blinded_conflict_probe_does_not_report_green
FAILED tests/test_scan_no_third_value.py::test_a_deleted_append_only_file_is_a_risk
FAILED tests/test_scan_no_third_value.py::test_all_files_present_still_reads_green
FAILED tests/test_standing_reflex_no_third_value.py::test_the_ci_merge_step_is_not_reimplemented_anywhere
FAILED tests/test_standing_reflex_no_third_value.py::test_a_declined_launch_is_not_counted_and_not_staggered
FAILED tests/test_standing_reflex_no_third_value.py::test_a_running_launch_is_both_counted_and_reported_started
--- tail of the transcript ---
no_third_value.py:400: AssertionError
_________ test_a_running_launch_is_both_counted_and_reported_started __________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001C09A860EC0>
tmp_path = WindowsPath('C:/Users/user/AppData/Local/Temp/pytest-of-user/pytest-3577/test_a_running_launch_is_both_0')

    def test_a_running_launch_is_both_counted_and_reported_started(monkeypatch,
                                                                   tmp_path):
        """NEGATIVE CONTROL: the healthy path keeps both meanings. `running` must
        still be capped and staggered *and* still be the only status that counts as
        a successful start -- the distinction the first commit was right to draw.
        """
        launches, staggers = _drive_sweep(monkeypatch, tmp_path, "running")
    
>       assert launches == standing.MAX_STANDING, (
            "the cap must still bind on healthy launches: %d" % launches)
E       AssertionError: the cap must still bind on healthy launches: 0
E       assert 0 == 5
E        +  where 5 = standing.MAX_STANDING

tests\test_standing_reflex_no_third_value.py:414: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_scan_failure_exit.py::test_a_blinded_conflict_probe_does_not_report_green
FAILED tests/test_scan_no_third_value.py::test_a_deleted_append_only_file_is_a_risk
FAILED tests/test_scan_no_third_value.py::test_all_files_present_still_reads_green
FAILED tests/test_standing_reflex_no_third_value.py::test_the_ci_merge_step_is_not_reimplemented_anywhere
FAILED tests/test_standing_reflex_no_third_value.py::test_a_declined_launch_is_not_counted_and_not_staggered
FAILED tests/test_standing_reflex_no_third_value.py::test_a_running_launch_is_both_counted_and_reported_started
======================================================================
== board states disjoint ok
======================================================================
no id is in done/ and on the shelf at the same time (137 delivered, 7 claimed)
======================================================================
== real run           ok
======================================================================
scan.build wrote history.jsonl, index.html, state.json
gates: 25 gated, 1 tests-only, 0 UNGATED
board.py list: 162 line(s)
======================================================================
== artifact fields    ok
======================================================================
state.json carries all 13 required fields; the gate survey is consistent

RED: tests

```
