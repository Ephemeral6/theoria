# CONFLICT-origin_agent_v16-determinism-has-no-caller.md
branch: origin/agent/v16-determinism-has-no-caller
reason: verify gate red in monitor (verify.sh)

```
======================================================================
== tests              FAILED(1)
======================================================================
release'}
E         
E         Extra items in the left set:
E         'fleet-study'

tests\test_gates.py:105: AssertionError
_________________ test_a_limit_signature_flips_normal_to_hold _________________

rig = <conftest.rig.<locals>.Rig object at 0x000001CC1262B8C0>

    def test_a_limit_signature_flips_normal_to_hold(rig):
        rig.write_state()
        rig.dead_session("P-8", "working...\n%s\n" % LIMIT_LINE)
    
        assert quota.check() == 2
    
        st = rig.read_state()
        assert st["mode"] == "hold"
>       assert st["requeue"] == ["P-8"]
E       AssertionError: assert [] == ['P-8']
E         
E         Right contains one more item: 'P-8'
E         Use -v to get more diff

tests\test_quota.py:45: AssertionError
---------------------------- Captured stdout call -----------------------------
HOLD — 日志中的限额签名：hit your session limit · resets 8:20pm
__________ test_a_session_that_pushed_its_branch_is_not_a_quota_kill __________

rig = <conftest.rig.<locals>.Rig object at 0x000001CC1262BB60>

    def test_a_session_that_pushed_its_branch_is_not_a_quota_kill(rig):
        """It finished. A limit line in the log of a session whose work landed is
        history, not a live outage."""
        rig.write_state()
        rig.dead_session("P-8", LIMIT_LINE, pushed=True)
    
>       assert quota.check() == 0
E       assert 2 == 0
E        +  where 2 = <function check at 0x000001CC1256FD80>()
E        +    where <function check at 0x000001CC1256FD80> = quota.check

tests\test_quota.py:68: AssertionError
---------------------------- Captured stdout call -----------------------------
HOLD — 日志中的限额签名：hit your session limit · resets 8:20pm
=========================== short test summary info ===========================
FAILED tests/test_gates.py::test_this_repository_is_where_the_survey_says_it_is
FAILED tests/test_quota.py::test_a_limit_signature_flips_normal_to_hold - Ass...
FAILED tests/test_quota.py::test_a_session_that_pushed_its_branch_is_not_a_quota_kill
======================================================================
== real run           ok
======================================================================
scan.build wrote history.jsonl, index.html, state.json
gates: 8 gated, 9 tests-only, 5 UNGATED
  ungated: CONTRACTS, browser-ops, fleet-study, papers, release
board.py list: 61 line(s)
======================================================================
== artifact fields    ok
======================================================================
state.json carries all 10 required fields; the gate survey is consistent

territories that merge with nothing checking them: CONTRACTS, browser-ops, fleet-study, papers, release
(reported, not a failure -- making it visible is the fix; refusing to merge them would stop the repository dead)

RED: tests

```
