# CONFLICT-origin_agent_p13-figure-numbering.md
branch: origin/agent/p13-figure-numbering
reason: verify gate red in figures (verify.sh)

```
ashed)

== 5. every declared artefact exists ==
checked 6 figures -> 24 images + 6 CSVs

== 6. the committed tree matches a fresh build ==
ok

== 7. no figure reads an undeclared path ==
ok  (every read goes through sources.py)

== 8. coverage: everything on disk reaches the figure ==
ok  (negative control fires)

VERIFY: red.
FAIL: data on disk is not reaching the figures:
    COVERAGE: theoria run directory 20260728T012311Z-g50t-first-contact-salvage (has MANIFEST.json; missing cost_curve.json): the discovery rule requires every member and so skips it, which means neither the rule nor this probe would notice it. A half-written run must be named, not silently dropped by both.
    COVERAGE: theoria run directory 20260728T012311Z-g50t-first-contact-salvage2 (has MANIFEST.json; missing cost_curve.json): the discovery rule requires every member and so skips it, which means neither the rule nor this probe would notice it. A half-written run must be named, not silently dropped by both.
    COVERAGE: theoria run directory 20260728T014402Z-g50t-first-contact-salvage (has MANIFEST.json; missing cost_curve.json): the discovery rule requires every member and so skips it, which means neither the rule nor this probe would notice it. A half-written run must be named, not silently dropped by both.
    COVERAGE: theoria run directory 20260728T015354Z-g50t-first-contact-salvage (has MANIFEST.json; missing cost_curve.json): the discovery rule requires every member and so skips it, which means neither the rule nor this probe would notice it. A half-written run must be named, not silently dropped by both.
    COVERAGE: theoria run directory 20260728T141546Z-S8-provenance-backfill (has MANIFEST.json; missing cost_curve.json): the discovery rule requires every member and so skips it, which means neither the rule nor this probe would notice it. A half-written run must be named, not silently dropped by both.
    COVERAGE: theoria run directory 20260728T152910Z-a3-desk-gate (has MANIFEST.json; missing cost_curve.json): the discovery rule requires every member and so skips it, which means neither the rule nor this probe would notice it. A half-written run must be named, not silently dropped by both.
    COVERAGE: theoria run directory 20260728T152930Z-a3-turn-series (has MANIFEST.json; missing cost_curve.json): the discovery rule requires every member and so skips it, which means neither the rule nor this probe would notice it. A half-written run must be named, not silently dropped by both.
    COVERAGE: theoria run directory 20260728T210000Z-a3-level-boundary (has MANIFEST.json; missing cost_curve.json): the discovery rule requires every member and so skips it, which means neither the rule nor this probe would notice it. A half-written run must be named, not silently dropped by both.
    COVERAGE: theoria run directory 20260728T233900Z-A3-campaign-devpile (has MANIFEST.json; missing cost_curve.json): the discovery rule requires every member and so skips it, which means neither the rule nor this probe would notice it. A half-written run must be named, not silently dropped by both.
    COVERAGE: theoria run directory 20260729T013000Z-A11 (has MANIFEST.json; missing cost_curve.json): the discovery rule requires every member and so skips it, which means neither the rule nor this probe would notice it. A half-written run must be named, not silently dropped by both.
    COVERAGE: theoria run directory 20260729T080000Z-E14-crash-is-not-a-finding (has MANIFEST.json; missing cost_curve.json): the discovery rule requires every member and so skips it, which means neither the rule nor this probe would notice it. A half-written run must be named, not silently dropped by both.
    COVERAGE: theoria run directory preflight-20260728T012031Z (has MANIFEST.json; missing cost_curve.json): the discovery rule requires every member and so skips it, which means neither the rule nor this probe would notice it. A half-written run must be named, not silently dropped by both.

```
