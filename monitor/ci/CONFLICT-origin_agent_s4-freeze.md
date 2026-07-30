# CONFLICT-origin_agent_s4-freeze.md
branch: origin/agent/s4-freeze
reason: verify gate red in freeze (verify.sh)
tip: f47b6b30ca70f1f1a47e3ef894e0bfbb8e8dcc3e
base: 3d59d0a63cffeb0e1f865c2bacc8508c5232087b
first_seen: 2026-07-29T23:09:27Z
last_seen: 2026-07-30T04:06:01Z
attempts: 7

```
--- cause lines (lifted out of the transcript) ---
[31m  FAIL  BUDGET_TABLE.{json,md} no longer recompute from the ledgers -- regenerate and read the diff[0m
--- tail of the transcript ---
carries an owner, a landing path and a clearing condition[0m

[15] the other two generated artefacts still describe their sources
[32m  PASS  build_engine_manifest.py --verify: ENGINE_MANIFEST.md still pins the tree it describes[0m
[32m  PASS  negative control fires: zeroing one pinned hash in a copy of ENGINE_MANIFEST.md turns this stage red[0m
[31m  FAIL  BUDGET_TABLE.{json,md} no longer recompute from the ledgers -- regenerate and read the diff[0m
        DRIFT: freeze/BUDGET_TABLE.json no longer describes this tree.
               sections that moved: balance, pool, projection, verdict
               `pool`/`balance` moved => THE BALANCE MOVED. A frozen
               budget table with a stale balance is the failure this
               gate exists to catch. Regenerate and re-read it.
        DRIFT: the generated block in freeze/BUDGET_TABLE.md is stale or was hand-edited.
        POOL ABSENT: the pool is gitignored (proxy/.gitignore:3) and this checkout does not have one; every balance figure below is unverifiable here
[33m  NOTE  negative control not run: the relocated copy does not reproduce 15b's own verdict, so a red from it would prove nothing about the real budget table[0m
[32m  PASS  citation section-anchoring: 9 controls and live anchors pass (a needle in a NEIGHBOURING section is drift, a renamed heading is missing-section)[0m

[16] one endpoint, one wording: each pinned rule is STATED in both files
[32m  PASS  E1 (U3 attainment rate): defining sentence, scalar, unit, test, direction and pass line are each STATED in both files
[0m
[32m  PASS  E2 (adjudication-question accuracy): defining sentence, scalar, unit, test, direction and pass line are each STATED in both files
[0m
[32m  PASS  E3 (front-loading index paired difference): defining sentence, scalar, unit, test, direction and pass line are each STATED in both files
[0m
[32m  PASS  negative control fires: mutating the BA formula in C4 ((灵敏度 + 特异度)/2 -> (灵敏度 + 特异度)/3) turns probe E2/scalar red
[0m
[32m  PASS  negative control fires: mutating the U3 denominator in C1's 成立版 (⟨X_obs/19⟩ -> ⟨X_obs/21⟩) turns probe E1/unit red
[0m
[33m  NOTE  one-endpoint-one-wording: 0 hard divergence(s), 0 soft, over 52 checks -- a green means each pinned rule is STATED in both files, NOT that the two files agree (see WHAT IT CANNOT DO in this stage's header, and endpoints/WORDING_AUDIT.md for the ranked list)[0m

==============================================================
[31m DRAFT INCOMPLETE -- 1 check(s) failed[0m
==============================================================

```
