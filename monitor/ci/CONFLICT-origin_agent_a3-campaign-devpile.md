# CONFLICT-origin_agent_a3-campaign-devpile.md
branch: origin/agent/a3-campaign-devpile
reason: verify gate red in theoria-arm (verify.py)
tip: a5812063b9a6b7b699bd8acb58f96dd770c298f8
base: 3d59d0a63cffeb0e1f865c2bacc8508c5232087b
first_seen: 2026-07-29T04:14:01Z
last_seen: 2026-07-30T04:03:14Z
attempts: 21

```
--- cause lines (lifted out of the transcript) ---
   FAIL  suite red (exit 1)
>       assert not checks.failed, [
E       AssertionError: ["re-deriving every manifest reproduces it byte for byte: drifted: ['20260728T012311Z-g50t-first-contact-salvage', '20...50t-first-contact-salvage', '20260729T004020Z-leg01', '20260729T004020Z-leg01-salvage', 'preflight-20260728T012031Z']"]
E       assert not [{'check': 're-deriving every manifest reproduces it byte for byte', 'detail': "drifted: ['20260728T012311Z-g50t-first...act-salvage', '20260729T004020Z-leg01', '20260729T004020Z-leg01-salvage', 'preflight-20260728T012031Z']", 'ok': False}]
E        +  where [{'check': 're-deriving every manifest reproduces it byte for byte', 'detail': "drifted: ['20260728T012311Z-g50t-first...act-salvage', '20260729T004020Z-leg01', '20260729T004020Z-leg01-salvage', 'preflight-20260728T012031Z']", 'ok': False}] = <armtools.verify_provenance.Checks obje
FAILED tests/test_arm.py::test_the_archive_stays_accountable - AssertionError...
--- tail of the transcript ---
[1/3] suite
   FAIL  suite red (exit 1)
.........................................................F.............. [ 29%]
........................................................................ [ 58%]
........................................................................ [ 87%]
...............................                                          [100%]
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
E       AssertionError: ["re-deriving every manifest reproduces it byte for byte: drifted: ['20260728T012311Z-g50t-first-contact-salvage', '20...50t-first-contact-salvage', '20260729T004020Z-leg01', '20260729T004020Z-leg01-salvage', 'preflight-20260728T012031Z']"]
E       assert not [{'check': 're-deriving every manifest reproduces it byte for byte', 'detail': "drifted: ['20260728T012311Z-g50t-first...act-salvage', '20260729T004020Z-leg01', '20260729T004020Z-leg01-salvage', 'preflight-20260728T012031Z']", 'ok': False}]
E        +  where [{'check': 're-deriving every manifest reproduces it byte for byte', 'detail': "drifted: ['20260728T012311Z-g50t-first...act-salvage', '20260729T004020Z-leg01', '20260729T004020Z-leg01-salvage', 'preflight-20260728T012031Z']", 'ok': False}] = <armtools.verify_provenance.Checks object at 0x0000020B1BD0B8C0>.failed

tests\test_arm.py:901: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_arm.py::test_the_archive_stays_accountable - AssertionError...
1 failed, 246 passed in 164.55s (0:02:44)

[2/3] one real run -- the whole arm, offline against proxy/mock
   ok    game g50t-5849a774, budget 6 actions, no key, no network
[3/3] artefact self-check

theoria-arm: RED (1 problem(s))

```
