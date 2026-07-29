# CONFLICT-origin_agent_a3-campaign-devpile.md
branch: origin/agent/a3-campaign-devpile
reason: tests red in theoria-arm

```
.....................................................F
================================== FAILURES ===================================
_____________________ test_the_archive_stays_accountable ______________________

    def test_the_archive_stays_accountable():
        """`verify_provenance`'s nine checks, run as part of the suite.
    
        The archive is the thing Phase 4 reads back to account for every ARC action
        this arm spent. A check that only runs when somebody remembers to run it is
        not a guarantee.
        """
        from armtools import verify_provenance               # noqa: PLC0415
    
        checks = verify_provenance.run()
>       assert not checks.failed, [
            "%s: %s" % (r["check"], r["detail"]) for r in checks.failed]
E       AssertionError: ["every run has a MANIFEST.json: missing for ['20260729T004020Z-leg01'] -- run `python -m armtools.backfill --all`", "...recard opened and never closed is declared as such: orphaned and undeclared: ['2ec0e679-6b92-475e-890c-a3f63d21e14c']"]
E       assert not [{'check': 'every run has a MANIFEST.json', 'detail': "missing for ['20260729T004020Z-leg01'] -- run `python -m armtoo...osed is declared as such', 'detail': "orphaned and undeclared: ['2ec0e679-6b92-475e-890c-a3f63d21e14c']", 'ok': False}]
E        +  where [{'check': 'every run has a MANIFEST.json', 'detail': "missing for ['20260729T004020Z-leg01'] -- run `python -m armtoo...osed is declared as such', 'detail': "orphaned and undeclared: ['2ec0e679-6b92-475e-890c-a3f63d21e14c']", 'ok': False}] = <armtools.verify_provenance.Checks object at 0x0000022707D797F0>.failed

tests\test_arm.py:866: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_arm.py::test_the_archive_stays_accountable - AssertionError...
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!

```
