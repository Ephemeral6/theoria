# LIVE-ARM-READINGS -- the live arm becomes battery material, measurement-only

The live Theoria arm's committed A3 leg archives (theoria-arm/runs/) are now
read by the battery through a new extractor (battery/adapters/theoria_live.py)
and reduced to a tracked companion artefact
(battery/artifacts_live/live_arm_readings.json) by battery/audit/live_arm.py.
Landed exactly on the live_tiers amendment path of 2026-07-31: new module +
new test + new artifacts_live/ reading, freeze buckets extended, freeze:*
blocks re-rendered, dated amendment appended to BATTERY_V1.md; the only
frozen files edited are freeze.py and verify.py (the freeze machinery).

Measurement-only, per the prereg's own text (decision recorded in the
amendment and inside the artefact): PREDICTIONS.md untouched (frozen prefix +
whole-file digest both intact), battery/artifacts/ untouched (PREREG_V9 s5),
run_battery.py untouched (CC-vs-Schema gradient does not include this arm).

Material: 4 genuine live legs on g50t-5849a774 (dev pile), 62 measured cells.
- epistemic: K1 K3 K4 K5 K6 K7 K8 K9 K10 K11 K14 (11 metrics with live readings)
- economy:   E1 E4 E5 E6 E7 (5 metrics; E2/E3 insufficient-data under 8 turns)
- exploration: X1-X6; planning: P1 P2 P3 P5; mechanism: none (no ground truth,
  structurally not-applicable).
Excluded with recorded reasons: 7 mock-upstream rig legs, 1 zero-step salvage
stub. Sealed-pile ids raise; negative controls in test_theoria_live.py.

Gates: freeze.check() empty; suite 410 passed; python -m battery.verify green
across all 7 rungs (rung 7 is new: companion staleness RED, non-dev row RED,
empty epistemic/economy reading RED).
