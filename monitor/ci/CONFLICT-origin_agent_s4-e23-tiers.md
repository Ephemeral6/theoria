# CONFLICT-origin_agent_s4-e23-tiers.md
branch: origin/agent/s4-e23-tiers
reason: verify gate red in freeze (verify.sh)
tip: 6eaf2da2dc18e7fceca4f6ed089e87d7da469d1d
base: 3d59d0a63cffeb0e1f865c2bacc8508c5232087b
first_seen: 2026-07-30T03:48:38Z
last_seen: 2026-07-30T03:48:38Z
attempts: 1

```
--- cause lines (lifted out of the transcript) ---
[31m  FAIL  BUDGET_TABLE.{json,md} no longer recompute from the ledgers -- regenerate and read the diff[0m
--- tail of the transcript ---
/.gitignore:3) and this checkout does not have one; every balance figure below is unverifiable here
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
[32m  PASS  negative control fires: mutating C4's pointer at the two-tier ruling (§4.4.3 -> §4.4.9) turns probe E2/conj red
[0m
[32m  PASS  negative control fires: mutating C2's pointer at the two-tier ruling (same mutation, other probe) (§4.4.3 -> §4.4.9) turns probe E3/conj red
[0m
[32m  PASS  negative control fires: mutating the evaluable-pair symbol in C2's 成立版, back to the taken ⟨k⟩ (可评的 ⟨v⟩ 对 -> 可评的 ⟨k⟩ 对) turns probe */vsym red
[0m
[32m  PASS  negative control fires: mutating the Holm family size invariant in C1 (family 恒为三个主终点 -> family 恒为两个主终点) turns probe */family red
[0m
[33m  NOTE  one-endpoint-one-wording: 0 hard divergence(s), 0 soft, over 56 checks -- a green means each pinned rule is STATED in both files, NOT that the two files agree (see WHAT IT CANNOT DO in this stage's header, and endpoints/WORDING_AUDIT.md for the ranked list)[0m

[17] §4.4 two-tier ruling for the paired endpoints (E2/E3) recomputes
[32m  PASS  tier_conj.py --verify: §4.4.2's power table, §4.4.3's verdict table and §9.22's boundary claim all match the arithmetic[0m
[32m  PASS  negative control fires: putting the first draft's wrong p (0.0078 -> 0.0039) back into the prose table turns this stage red[0m

==============================================================
[31m DRAFT INCOMPLETE -- 1 check(s) failed[0m
==============================================================

```
