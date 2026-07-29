# CONFLICT-origin_agent_a3-campaign-devpile.md
branch: origin/agent/a3-campaign-devpile
reason: verify gate red in theoria-arm (verify.py)
tip: e843a0fbeeb885b296d4faac7286dbfa8e16ca47
first_seen: 2026-07-29T04:14:01Z
last_seen: 2026-07-29T10:29:35Z
attempts: 3

```
[1/3] suite
   FAIL  suite red (exit 1)
.........................................................F.............. [ 36%]
........................................................................ [ 72%]
......................................................                   [100%]
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
E       AssertionError: ["every run has a MANIFEST.json: missing for ['20260729T004020Z-leg01'] -- run `python -m armtools.backfill --all`", "...728T014402Z-g50t-first-contact-salvage', '20260728T015354Z-g50t-first-contact-salvage', 'preflight-20260728T012031Z']"]
E       assert not [{'check': 'every run has a MANIFEST.json', 'detail': "missing for ['20260729T004020Z-leg01'] -- run `python -m armtoo...0t-first-contact-salvage', '20260728T015354Z-g50t-first-contact-salvage', 'preflight-20260728T012031Z']", 'ok': False}]
E        +  where [{'check': 'every run has a MANIFEST.json', 'detail': "missing for ['20260729T004020Z-leg01'] -- run `python -m armtoo...0t-first-contact-salvage', '20260728T015354Z-g50t-first-contact-salvage', 'preflight-20260728T012031Z']", 'ok': False}] = <armtools.verify_provenance.Checks object at 0x00000169AC763620>.failed

tests\test_arm.py:866: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_arm.py::test_the_archive_stays_accountable - AssertionError...
1 failed, 197 passed in 97.90s (0:01:37)

[2/3] one real run -- the whole arm, offline against proxy/mock
   ok    game g50t-5849a774, budget 6 actions, no key, no network
[3/3] artefact self-check

theoria-arm: RED (1 problem(s))

```
