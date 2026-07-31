"""E18 — every survey number that reaches the paper gets a script.

Each module in this package recomputes one number that the E11 cross-check
(`engine-rig/runs/20260729T000000Z-E11-engine-crosscheck-deep/`) reported as
prose only.  A module exposes `compute() -> dict` and is runnable as
`python -m tools.survey_numbers.<name>` from `engine-rig/`.

Prose is not evidence.  The recomputed value is the number of record; where it
disagrees with the E11 prose, the disagreement is reported, not smoothed over.
"""
