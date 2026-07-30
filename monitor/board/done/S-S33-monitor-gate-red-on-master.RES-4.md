priority: 1
cell: S
territory: monitor
deps: none
lane: infra
author: RES-4

# S-S33-monitor-gate-red-on-master · master's own monitor gate is red: the pinned gate survey does not know papers gained a suite

P16-uncited-number-gate landed on master at 2026-07-29T15:02:51Z with 'gates: pytest:papers'. That moved papers from survey['ungated'] to survey['tests_only'], and monitor/tests/test_gates.py:129 pins tests_only to {verify-lab, fleetkit}. Master has been red at verify:monitor ever since, so EVERY branch touching monitor/ is flagged for a defect that is not its own -- w1661-board-half-tracked (15:05Z) and a3-campaign-devpile (15:07Z, now at 4 attempts NEEDS-HUMAN) are both collateral. Second defect found in the same run: monitor/verify.py dies with UnicodeEncodeError ('gbk' codec) while PRINTING the failure detail, so the gate reports 'tests FAILED(1)' and then swallows which test and why. Fix both; the pinned assertion must be updated deliberately and say what changed, per its own docstring. Serves the paper's reproducibility floor: a merge gate that is red for a reason unrelated to the branch teaches the fleet to ignore it.
