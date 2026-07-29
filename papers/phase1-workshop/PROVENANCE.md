# PROVENANCE — every load-bearing number, and where it came from

The draft's binding rule is that a number with no path does not go in. This file
is the index of that rule: one row per claim that carries weight in the argument,
with the artefact a reader should open to check it. `CITECHECK.md` is the
mechanical audit of the same rule and is the place where any failures are
recorded.

**Precedence.** Where a JSON artefact and a prose report disagree, the artefact
wins and the disagreement is noted in the last table. Where a report and a
*later* artefact disagree because the world moved on after the report was
written, the paper cites both and says which is later; no report was edited.

---

## §1 — the hook

| claim | value | source |
|---|---|---|
| A0 replay, frames | 276/276, 0 anomalies | `cold-start-a0/A0_REPORT.md` §2 |
| A0 replay, pixels | 22 356/22 356 | `cold-start-a0/A0_REPORT.md` §2 |
| A0 behavioural accuracy | 233/236 = 0.987288 | `cold-start-a0/artifacts/score_vs_truth.json` → `base.behavioural` |
| A0 held-out accuracy | 0.000 on 3 pairs | ibid. → `base.held_out` |
| the three missed pairs | Button from above, below, right | ibid. → `base.held_out.examples`; predicted at `cold-start-a0/THEORIZE_LOG.md` R-05 |
| ground-truth seal | first read at M6 | `cold-start-a0/THEORIZE_LOG.md` §Ground-truth seal; `score_vs_truth.json` → `seal` |
| the seal's hole | same instance built and adjudicated | `cold-start-a0/THEORIZE_LOG.md` preamble; `cold-start-a0/A0_REPORT.md` §6.3 |
| K4 = 1.000, K2 = 0.000 | same manual, same recompute; K4 over 7 annotated clauses, K2 over 3 pairs with 0 agreements, unchanged from v0 to v2 | `battery/artifacts/capability_spectrum.json`, run `a0-base`. §1's blockquote is `battery/REPORT_V0.md`'s own wording and stays attributed to it |
| A2's two Lean files | identical in generator, tactic, dependency surface and axiom list — **not** identical but for the weight table; see the disagreements table | `cold-start-a2/theory/generated_holed/theory.lean`, `…/generated_repaired/theory.lean` |
| the refuting episode | 18 actions, win on frame 18 | `cold-start-a2/artifacts/refutation.json`, `solved_episode.jsonl` |

## §3 — A0 and A0′

| claim | value | source |
|---|---|---|
| A0 world size | 59 reachable states, 276 frames | `cold-start-a0/A0_REPORT.md` §1; `cold-start-a0/artifacts/trace_summary.json` |
| candidates adjudicated | 29 schema-valid | `cold-start-a0/A0_REPORT.md` §1; `cold-start-a0/artifacts/candidates.jsonl` |
| manual size | 3 objects, 7 rules, 2 invariants, 1 pending theorem | `cold-start-a0/A0_REPORT.md` §1; `cold-start-a0/theory/theory.dsl` |
| Lean obligations | 2/2, axiom lists empty | `cold-start-a0/A0_REPORT.md` §2; `cold-start-a0/artifacts/certify_lean_generated_theory_lean.json` |
| plan | SAT, 12 steps | `cold-start-a0/artifacts/plan_generated.json` |
| the conservation law | 275 transitions of support, 152 indicator bits | `cold-start-a0/THEORIZE_LOG.md` L-02; `cold-start-a0/artifacts/engines_report.json` |
| segmentation, script bits | 6511 vs 4423; 90 tracks vs 3 | `cold-start-a0/THEORIZE_LOG.md` D-A0-007 §Segmentation operator |
| per-object accounts | Cart +2967, Button −17, Door −13 | `cold-start-a0/artifacts/concept_accounts.json`; `THEORIZE_LOG.md` O-04 |
| accounts, responsibility-complete | Button −5, Door −1 | `cold-start-a0/A0_REPORT.md` §8 |
| A0′ coverage | 107/228 = 47 % | `cold-start-a0/prime/artifacts/prime_report.json` → `trace["a0p-base"]` |
| A0′ accuracy | 228/228 = 1.0000 | ibid. → `run_a.score_vs_truth` |
| A0′ executable probes | 13 of 27 designed | ibid. → `engines` |
| A0′ re-identification | 7 tracks → 3, 48 bits saved | ibid. → `engines.reidentification` |
| Run B replay | 111 frames, 8991 pixels, 0 anomalies | ibid. → `run_b` / `run_a.certify_cheap` |
| Run B repair | 1 revision, 0.991228 → 1.0000 | ibid. → `run_b.score_vs_truth_before` / `_after` |
| the `ArenaEscape` diagnostic | verbatim string | ibid. → `run_b.certify_lean` |
| a0-spike T-9 | 8 mismatches, all unreachable; 39 960 states, 0 mismatches; 1 966 vs 341 actions | `a0-spike/THEORIZE_LOG.md` T-9 |
| a0-spike T-10 | detection latencies 6 / 18 / 18 / never | `a0-spike/THEORIZE_LOG.md` T-10 |

## §4 — A1

| claim | value | source |
|---|---|---|
| the solved weight vector | `[-1,1,0,1,-1]` | `engine-rig/interop/certificates/pagoda_5_11011_to_00010.json`; `theory-compiler/STATUS.md` |
| the rehearsal's hand weights | `[1,2,3,2,1]` | `theory-compiler/STATUS.md` §M8 差异 |
| obligations re-verified, not trusted | — | `theory-compiler/src/theory_compiler/certificate.py` |
| `inv_closed` | 6 move instances, all delta ≤ 0 | the certificate JSON → `obligations.inv_closed` |
| `goal_break` | goal potential 1 > initial 0 | ibid. → `obligations.goal_break` |
| four theorems, empty axiom lists | `inv_init`, `inv_closed`, `inv_all`, `unsolvable` | `theory-compiler/STATUS.md` |
| the negative control | `w .p1 := 7` → `decide` false, all four `[sorryAx]`, exit 1 | `theory-compiler/STATUS.md` §独立复核 |
| E-06, the unproved goal | 3 of 5 end states not derivable by linear pagoda | `theory-compiler/STATUS.md` §未清偿; `engine-rig/tests/test_interop.py` |
| the refusal | `CertificateGapError`, names the uncovered end states | `theory-compiler/STATUS.md` |
| empty axioms vs linear proof | not simultaneously available; 2³³ on the English board | `theory-compiler/STATUS.md`; `theory-compiler/DECISIONS.md` D-TC-008 |
| test count | 83 passed, 8 invoking `lean` | `theory-compiler/STATUS.md` |

## §5 — A2

| claim | value | source |
|---|---|---|
| the authority for the substitution | INC-004 ruling, option (b) | `cold-start-a2/artifacts/loop_ledger.json` → `authority`; `arc-recon/README.md` |
| history coverage | 163 of 164 pairs, omitting exactly the firing pair | `cold-start-a2/artifacts/trace_summary.json` |
| holed manual, cheap certify | 184 frames, 14 904 pixels, 0 anomalies | `cold-start-a2/artifacts/exhibit_report.json` |
| holed manual, plan | UNSAT | `cold-start-a2/artifacts/plan_holed.json` |
| holed manual, Lean | GREEN, `decide` only, `#print axioms` = `[]`, 148 states | `cold-start-a2/theory/generated_holed/theory.lean`; `exhibit_report.json` |
| the world's refutation | 18 actions, win | `cold-start-a2/artifacts/refutation.json` |
| the bound, artefact side | 248 frames, `green: false`, 44 anomalies, first at t184 (6,4) | `cold-start-a2/artifacts/exhibit_report.json` → `certify_cheap_vs_full_sweep` |
| the bound, pixel count | 128 unexplained of 20 088 checked | `cold-start-a2/A2_REPORT.md` §2 only — **the artefact does not carry this figure**, and the paper cites it to the report |
| localisation | board ✗, goal ✗, step ✓ at t=11 | `cold-start-a2/artifacts/locate_report.json` |
| probes | 5 designed, 4 executed, 1 unrunnable; 184 → 196 frames | `cold-start-a2/artifacts/probes.jsonl`, `probe_report.json` |
| the ledger | 8 beats, 8 pass, 0 fail, 0 absent | `cold-start-a2/artifacts/loop_ledger.json` |
| the stale certificate's corpse | Lean fails at line 769 | `cold-start-a2/theory/generated_repaired_stale/` |
| read-only verification | 258 files hashed, 0 changed | `cold-start-a2/A2_REPORT.md` §7 only — `upstream_pin.json` pins 22 files and does not carry this figure |
| upstream pinning | every imported file hashed | `cold-start-a2/artifacts/upstream_pin.json` |

## §6 — A3, the second level

| claim | value | source |
|---|---|---|
| like-for-like bill, actions | 346 -> 10 = 0.029 | `cold-start-a3/artifacts/bill_table.md` (same level, books vs no books) |
| like-for-like bill, frames | 347 -> 11 | ibid. |
| the four zeros | engine stages, candidates, theorize rounds, clauses all 0 | ibid.; `cold-start-a3/artifacts/bill_l2_transfer.json` |
| verification unchanged | compile 1, certify 3, plan 1 in both columns | ibid. |
| cost to first plan | 1 frame, 0 actions (cold start: 333 / 332) | `cold-start-a3/artifacts/bill_l2_transfer.json` -> `cost_to_first_plan` |
| problem fields | 6 derived from the frame, 3 supplied | `cold-start-a3/artifacts/provenance_l2_transfer.json` |
| plan and outcome | SAT, length 10, win, 10 actions spent | `cold-start-a3/artifacts/arm_l2_transfer.json` |
| referee's shortest for L2 | 10 | `cold-start-a3/artifacts/ground_truth.json` |
| carried manual vs truth | 252/252 = 1.0, all reachable pairs (no held-out set exists) | `cold-start-a3/artifacts/score_vs_truth.json` |
| reachable states | L1 62, L2 63 | `cold-start-a3/artifacts/ground_truth.json` |
| generated-theory diff | 35 lines, confined to LANDMARKS/BOARD/is_goal/initial_state | `cold-start-a3/tests/test_transfer.py` |
| negative controls, both caught | `all_caught: true`, `none_claimed_a_win: true` | `cold-start-a3/artifacts/negative_controls.json` |
| ... replay is the layer that caught them | 13 anomalies, 8 of 891 pixels unexplained; static and Lean both green | ibid. |
| ... `l2-oneway` reachable states | 63 -> 34, unsolvable | ibid.; `ground_truth.json` |
| ... `l2-rewired` shortest | 15 | `ground_truth.json` (`DECISIONS.md` D-A3-010 says 14 and is stale) |
| blind control agreement | 0 % as written; all 20 of L1's clauses canonically, plus 8 the blind arm added | `cold-start-a3/artifacts/domain_agreement.json` -> `as_written` |
| blind control theorize rounds | 5, of which 2 went to toolchain conformance | `cold-start-a3/A3_REPORT.md` §4 |
| planner backend | `stub-bfs`, not Fast Downward | every artefact's `plan.backend` |
| incident A3-I1 | blind partially broken in round 3; verdicts fixed in round 1 | `cold-start-a3/DECISIONS.md`; `A3_REPORT.md` |
| the playbook's transfer | **asserted, not measured** — no code path reads `theory/playbook.dsl`, and the byte-identity test its docstring cites does not exist | grep of `cold-start-a3/tests/` and `a3pipeline/` |

## §7 — the battery

**Re-derived at P7 against `battery_version: "v2"`.** The rows below replaced a
block that indexed v0 — 26 runs, 2 arms, 29 metrics — after §7 was rewritten.
Every value here is read from an artefact; the two rows that are a *report's*
statement rather than an artefact's say so, because that is the distinction this
index exists to keep.

| claim | value | source |
|---|---|---|
| scope of the recompute | 95 runs, 5 arms, 4 games, 38 metrics, 1 433 computed values | `battery/artifacts/capability_spectrum.json` (`battery_version: "v2"`) |
| the specified gradient | CC vs Schema paired by game; 10 of 38 metrics pair, 8 rankable, every verdict `underpowered` | `battery/artifacts/discrimination_arms.json` |
| smallest attainable p | 0.125 at 4 non-tied paired games — but **0.25 for P3, X2 and X3**, which each lose a game to a tie and fall to `sign_test.n: 3`; floor is 6 non-tied pairs | `battery/artifacts/discrimination_arms.json`, top-level `power` and per-metric `sign_test.min_attainable_p` |
| X3 separates backwards | δ = −0.562 against a declared `higher` direction; wrong-direction warning raised automatically | `battery/artifacts/discrimination_arms.json`, X3 `warning` |
| P1 reads opposite on the two passes | δ = **−0.750** on the model ladder, δ = **+1.000** on the specified gradient | `battery/artifacts/discrimination.json`; `battery/artifacts/discrimination_arms.json`. The artefact's own `role` field says the disagreement is information rather than noise |
| P1 ↔ failure-rate correlation | ρ = −0.83 | `battery/REPORT_V0.md`; `battery/STATUS.md` W-4. **No artefact carries this value** — it is quoted as a v0 statement, not a v2 measurement. v2 re-measures the same pair at **ρ = −0.899 over 82 shared runs** (`battery/artifacts/redundancy.json`, `matrix`), so the finding survived re-measurement even though the number cannot be reproduced. It is not the paper's only report-only battery figure: the pre-registration scoreboard, the 27–45 % pilot failure band, and the main table's intermediate 6 are the others, each marked as such in its own row or in §7 |
| E5 as a price list | δ = +1.000 on the model ladder, flagged wrong-direction | `battery/artifacts/discrimination.json` |
| E2 front-load confound | δ = +1.000 in the declared direction, 4 wins of 4 paired games, p = 0.125 against a floor of 0.125 | `battery/artifacts/discrimination.json`, E2 `sign_test` |
| E2 on the specified gradient | `no-data` — the Schema corpus records no cost under any spelling, so **zero** E2 pairs can form | `battery/artifacts/discrimination_arms.json`, E2 |
| K4 / K2 on `a0-base` | 1.000 over 7 annotated clauses; 0.000 over 3 pairs, 0 agreements | `battery/artifacts/capability_spectrum.json`, run `a0-base` |
| the executable anti-gaming audit | 38 exploits, 34 still land, 17 register entries contradicted; main table 9, reference 29 | `battery/artifacts/gaming_audit.json` |
| de-redundancy | 32 clusters over 38 metrics, 5 retired into representatives, 1 cross-family cluster; 257 of 703 pairs measurable | `battery/artifacts/redundancy.json` |
| never validated on any gradient | 21 of 38 — all epistemic, all mechanism, and P4 | `battery/artifacts/validation_material.json`, `n_unvalidated` |
| the pre-registration's seal | K1, K2, K7, K8 (v0 seal) and K14 (v1 table) on A0 marked `[seen]` — five in all | `battery/PREDICTIONS.md` |
| the v2 pre-registration scoreboard | 7 hits / 11 misses of 18 read strictly; 11 of 18 honouring the registered conditional | `battery/REPORT_V2.md` — a report's statement, not an artefact's |

**Two rows were deleted rather than updated.** The v0 index carried an *X5
cross-check* row ("59 distinct states, agreeing with a differently-computed
count"); `papers/phase1-workshop/REVIEW.md` showed both counts descend from
`cold-start-a0/world/explorer.py`, so the claim left §7 instead of being repaired,
and an index row for a claim the paper no longer makes would be worse than none.
The per-model dollar figures under *E5* and the per-model medians under *E2* went
the same way — §7 now cites the effect sizes and not those aggregates.

## §9 — the preflight

| claim | value | source |
|---|---|---|
| the run of record | `preflight-20260728T012057Z` (an earlier attempt 26 s before aborted at 2 records) | `theoria-arm/runs/` |
| ledger records | 23 | `.../preflight-20260728T012057Z/ledger.jsonl` |
| RESET attempts | 18 (17 x 400, 1 x 200) | ibid. |
| scored actions | **0** — `total_actions: 0`, `level_actions: [0]x7`, `score: 0.0` | ibid. seq 22, the API's own close response |
| reconciliation | `successful_actions: 0` over 18 env steps | `.../MANIFEST.json` -> `reconciliation` |
| cost | `model_calls: 0`, `usd: 0.0` | `.../MANIFEST.json` -> `cost` |
| sealing counters | `bypass_attempts: 0`, `guard_blocks: 0`, `credential_in_body: 0`, `incidents: 0` | `.../MANIFEST.json` -> `sealing` |
| guard fingerprint | cut v1, 4 development, 21 sealed, `unknown_policy: "deny"` | `.../ledger.jsonl` seq 1 |
| RESET is not billed | 4 scorecards originally, extended to 32 | `baseline-arms/BUDGET_REPORT.md`; `proxy/scoring/arc_v1.py` (its fixture header still says 31 and is stale) |
| ... and its stated limit | a *refused* request is unbilled; a semantically wasted one returns 200 and is billed | `proxy/scoring/arc_v1.py` |
| sealed pile byte scan | `sealed_game_ids_found: []`, `sealed_pile_untouched: true`, `cut_integrity: true` | `theoria-arm/runs/20260728T015354Z-g50t-first-contact/MANIFEST.json` (the preflight manifest predates this scan) |
| the bypass counter does fire | 66 `bypass_attempt` incidents, 65 consecutive 401s | `theoria-arm/evidence/model-proxy-401.jsonl` |
| red-team pass | 46 attacks, 29 landed on first contact, all 46 now blocked | `proxy/REDTEAM.md`; `proxy/STATUS.md` |
| model side not proxied | `proxied: false` on every model call | `theoria-arm/GAPS.md` GAP 1; `theoria-arm/harness/modelcall.py` |
| spend gate postdates the run | gate wired 08:42 Z, preflight ran 01:20 Z; `env_proxy.py` hashes differ | `proxy/runs/20260728T083000Z-s3/MANIFEST.json` vs the preflight's `upstream_pin` |
| ... and never ran live | "offline throughout; the gate was never pointed at a live upstream" | `proxy/runs/20260728T083000Z-s3/MANIFEST.json` -> `money_spent` |
| replay spot-check | 16 sessions, 9 positions, **372 pairwise comparisons**, 0 disagreements, one game | `proxy/runs/p9-shell-harden/replay_spotcheck_ar25.json` |
| ... what it measures | the environment's determinism, not that the proxies reproduce a run | `proxy/STATUS.md` |
| ledger authenticity | self-consistent, not authenticated; hash chain registered, not built | `proxy/STATUS.md` D-024; `proxy/REDTEAM.md` RED-40 |
| no credential byte scan of the live ledger | the arm's archiver advertises it and accepts an unused `key_len` parameter | `theoria-arm/armtools/archive.py` |
| first contact, for contrast | 7 actions, 5 model calls, score 0.0, 0 of 7 levels | `theoria-arm/runs/20260728T015354Z-g50t-first-contact/MANIFEST.json` |
| wall-clock confounded | two arms on one quota concurrently | `theoria-arm/INCIDENTS.md` INC-TA-001 |
| cache reads structurally zero | fresh process per call, by design | ibid. INC-TA-005 |

## §11 — limitations

| claim | value | source |
|---|---|---|
| INC-004 | DC22 → `design_document_disclosed` | `cold-start-a2/A2_REPORT.md` §1; `arc-recon/README.md` |
| INC-BA-001 | 9 sealed games contaminated, 2 materially | `baseline-arms/INCIDENTS.md`; `baseline-arms/TOUCHED_GAMES.md` |
| development pile played | 4 games, 109 + 44 successful actions, `levels_completed` 0 throughout | `baseline-arms/TOUCHED_GAMES.md`; `baseline-arms/ledger.jsonl` (560 rows) |
| determinism precheck | PASS on all four, 9/9 · 3/3 · 9/9 · 9/9 | `arc-recon/README.md`; `arc-recon/data/precheck.json` |
| Fast Downward, A0 | connected; agrees with the stub on all three instances | `cold-start-a0/BLOCKER_FAST_DOWNWARD.md`; `cold-start-a0/artifacts/fd_real.json`; `cold-start-a0/STATUS.md` |
| Fast Downward, A2 and engine-rig | still the bundled BFS stub | `cold-start-a2/A2_REPORT.md` §8; `engine-rig/STATUS.md` |
| no LLM in the loop on A0 | every economy metric `not-applicable` | `battery/REPORT_V0.md` §Coverage |
| revision counts across the paper | 0, 0, 1, 1 | `cold-start-a0/THEORIZE_LOG.md`; `prime_report.json`; `cold-start-a2/artifacts/repair_report.json` |
| concurrent-session incident | two sessions, one budget, one quota | `baseline-arms/INCIDENTS.md` INC-BA-003 |

---

## Known source disagreements, and which the paper follows

| topic | the two sources | what the paper does |
|---|---|---|
| whether the economy family collapsed | `battery/REPORT_V2.md` says "the economy family collapsed to `no-data`"; the same report's own process-1 table lists **E4** at δ = −0.875 over 4 paired games, and `battery/artifacts/discrimination_arms.json` agrees | **follows the artefacts.** Four of seven economy metrics resolved to `no-data` — E2, E3, E5, E7. E1 and E6 are direction-less diagnostics returned `not-ranked`, and E4 is `underpowered` at δ = −0.875 over 4 paired games, because it is a curvature fit over *context tokens* and its `needs` field asks for `model_calls` rather than a price. §7.3 states the exception; the report is not edited |
| how much of the Schema arm backs each metric | nothing in the source reports distinguishes them; `battery/artifacts/capability_spectrum.json` shows the Codex-side collection recording `model_calls: 0` on all four runs while the Claude-side records 197–564 | **follows the artefact, and adds a column.** P1, P2 and E4 divide by model calls, so their Schema side rests on **4 of 8** runs — one vendor's collection — where the other five rankable metrics use all 8. §7.2's table carries this per row; it is a confound beyond the arm-and-harness bundle the artefact already declares |
| the two A2 Lean files | `cold-start-a2/A2_REPORT.md` §4 and `DECISIONS.md` D-A2-005 say they "differ in their weight table and in nothing else"; `diff` of the two files shows 52 changed lines, including `def Goal` (`c10` vs `c34`) and four `step` entries (`c31` vs `c35`) | **follows the files.** §5.6 corrects the report explicitly and states what the correction costs the exhibit. The report is not edited |
| the discriminative verdicts | `battery/REPORT_V0.md` says "every discriminative verdict"; the artefacts have three verdict values, not two. At v2: 13 `underpowered`, 18 `no-data`, 7 `not-ranked` on the model ladder, and 8 / 23 / 7 on the specified gradient (`battery/artifacts/discrimination.json`, `discrimination_arms.json`) | **follows the artefacts.** §7.2 and §11.4 say "every *ranked* metric", 31 of 38 on each pass. The v0 form of this row read "24 of 29" and was re-derived at P7 |
| A0's segmentation figures | `A0_REPORT.md` §3 and `THEORIZE_LOG.md` D-A0-007 gives 6511 bits / 90 tracks; `cold-start-a0/artifacts/engines_report.json` now gives 5704 / 6, with the older pair under `reidentification.*_before` | **follows the report**, because that is the account the adjudication was made from; §3.2 states the disagreement |
| A2's revision count | no file in the tree states one; `loop_ledger.json`'s L4 beat records `re_derivable_from_grown_evidence: true` and no number | §11.3 says so, and marks "one revision" for A2 as the paper's reading of the ledger rather than a citable figure |
| A0's candidate count | `THEORIZE_LOG.md` Round 0 says 28; `cold-start-a0/artifacts/candidates.jsonl` has 29 rows | **follows the artefact** (29), and §3.1 explains the gap: the 29th row is a `plan` the log did not adjudicate |
| Fast Downward connectivity | `cold-start-a0/A0_REPORT.md` §5/§6.5 says "still not connected"; `cold-start-a0/BLOCKER_FAST_DOWNWARD.md` and `STATUS.md` record it as connected on 2026-07-28 | cites both, states which is later, and does not edit the report (§7.3) |
| whether any game has been played | `CLAUDE.md` says no game has been played and all 25 are `never_audited`; `baseline-arms/TOUCHED_GAMES.md` records all four development-pile games at `trajectories_reviewed` | follows the ledger and corrects `CLAUDE.md` explicitly (§11.2) |
| the exhibit theorem's name | `cold-start-a2/artifacts/refutation.json` names it `right_room_locked` with `lean_target: "unsolvable"`; `A2_REPORT.md` §2/§4 uses `unsolvable` throughout | follows the report's Lean-level name and records the discrepancy here |
| the pile hash | `CLAUDE.md` publishes `3feca53e…` as if it were a file hash; the file itself hashes to `d3140eff…` | reports the battery's finding (D-B-011): the cut is intact, only the description misleads |
