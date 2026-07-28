# CONFLICT-origin_agent_s14-gates-for-all.md
branch: origin/agent/s14-gates-for-all
reason: verify gate red in monitor (verify.sh)

```
======================================================================
== tests              FAILED(1)
======================================================================
.....F.F............................x [ 97%]
x.                                                                       [100%]
================================== FAILURES ===================================
_________________ test_a_limit_signature_flips_normal_to_hold _________________

rig = <conftest.rig.<locals>.Rig object at 0x00000259E90CB620>

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

rig = <conftest.rig.<locals>.Rig object at 0x00000259E90CBB60>

    def test_a_session_that_pushed_its_branch_is_not_a_quota_kill(rig):
        """It finished. A limit line in the log of a session whose work landed is
        history, not a live outage."""
        rig.write_state()
        rig.dead_session("P-8", LIMIT_LINE, pushed=True)
    
>       assert quota.check() == 0
E       assert 2 == 0
E        +  where 2 = <function check at 0x00000259E901FD80>()
E        +    where <function check at 0x00000259E901FD80> = quota.check

tests\test_quota.py:68: AssertionError
---------------------------- Captured stdout call -----------------------------
HOLD — 日志中的限额签名：hit your session limit · resets 8:20pm
=========================== short test summary info ===========================
FAILED tests/test_quota.py::test_a_limit_signature_flips_normal_to_hold - Ass...
FAILED tests/test_quota.py::test_a_session_that_pushed_its_branch_is_not_a_quota_kill
======================================================================
== real run           ok
======================================================================
scan.build wrote history.jsonl, index.html, state.json
gates: 17 gated, 0 tests-only, 5 UNGATED
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
