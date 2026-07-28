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
| K4 = 1.000, K2 = 0.000 | same manual, same recompute | `battery/REPORT_V0.md`; `battery/artifacts/capability_spectrum.json` |
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
| segmentation, script bits | 6511 vs 4423; 90 tracks vs 3 | `cold-start-a0/THEORIZE_LOG.md` O-01 §Segmentation operator |
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

## §6 — the battery

| claim | value | source |
|---|---|---|
| scope of the recompute | 26 runs, 4 games, 2 arms | `battery/REPORT_V0.md`; `battery/artifacts/capability_spectrum.json` |
| smallest attainable p | 0.125 at 4 paired games; floor is 6 | `battery/artifacts/discrimination.json` |
| P1 confound | δ = −1.000; haiku 0.96 vs opus 0.52 actions/call; 28–45 % step failure | `battery/artifacts/capability_spectrum.json`, `discrimination.json` — the paper uses the artefact's aggregates, not `REPORT_V0.md`'s 0.97 / 27 % |
| P1 ↔ failure-rate correlation | ρ = −0.83 | `battery/REPORT_V0.md`; `battery/STATUS.md` W-4. **No artefact carries it** — the one battery number in the paper that cannot be re-derived from `battery/artifacts/` |
| E5 as a price list | δ = +1.000; $0.031 / $0.124 / $0.279 per action | `battery/REPORT_V0.md`; `battery/artifacts/capability_spectrum.json` |
| E2 front-load confound | haiku 0.20, sonnet 0.25, opus 0.28; δ = +1.000 | ibid. |
| de-redundancy | 2 clusters at \|ρ\| ≥ 0.9; 27 clusters from 29 metrics; ρ = 0.916, 0.909 | `battery/artifacts/redundancy.json` |
| the pre-registration's seal | K1, K2, K7, K8 on A0 marked `[seen]` | `battery/PREDICTIONS.md` |
| X5 cross-check | 59 distinct states, agreeing with a differently-computed count | `battery/artifacts/capability_spectrum.json`; `cold-start-a0/artifacts/trace_summary.json` |

## §7 — limitations

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
| the two A2 Lean files | `cold-start-a2/A2_REPORT.md` §4 and `DECISIONS.md` D-A2-005 say they "differ in their weight table and in nothing else"; `diff` of the two files shows 52 changed lines, including `def Goal` (`c10` vs `c34`) and four `step` entries (`c31` vs `c35`) | **follows the files.** §5.6 corrects the report explicitly and states what the correction costs the exhibit. The report is not edited |
| the discriminative verdicts | `battery/REPORT_V0.md` says "every discriminative verdict"; `battery/artifacts/discrimination.json` has three verdict values — 11 `underpowered`, 13 `no-data`, 5 `not-ranked` | **follows the artefact.** §6.4 and §7.4 say "every ranked metric", 24 of 29 |
| A0's segmentation figures | `A0_REPORT.md` §3 and `THEORIZE_LOG.md` O-01 give 6511 bits / 90 tracks; `cold-start-a0/artifacts/engines_report.json` now gives 5704 / 6, with the older pair under `reidentification.*_before` | **follows the report**, because that is the account the adjudication was made from; §3.2 states the disagreement |
| A2's revision count | no file in the tree states one; `loop_ledger.json`'s L4 beat records `re_derivable_from_grown_evidence: true` and no number | §7.3 says so, and marks "one revision" for A2 as the paper's reading of the ledger rather than a citable figure |
| A0's candidate count | `THEORIZE_LOG.md` Round 0 says 28; `cold-start-a0/artifacts/candidates.jsonl` has 29 rows | **follows the artefact** (29), and §3.1 explains the gap: the 29th row is a `plan` the log did not adjudicate |
| Fast Downward connectivity | `cold-start-a0/A0_REPORT.md` §5/§6.5 says "still not connected"; `cold-start-a0/BLOCKER_FAST_DOWNWARD.md` and `STATUS.md` record it as connected on 2026-07-28 | cites both, states which is later, and does not edit the report (§7.3) |
| whether any game has been played | `CLAUDE.md` says no game has been played and all 25 are `never_audited`; `baseline-arms/TOUCHED_GAMES.md` records all four development-pile games at `trajectories_reviewed` | follows the ledger and corrects `CLAUDE.md` explicitly (§7.2) |
| the exhibit theorem's name | `cold-start-a2/artifacts/refutation.json` names it `right_room_locked` with `lean_target: "unsolvable"`; `A2_REPORT.md` §2/§4 uses `unsolvable` throughout | follows the report's Lean-level name and records the discrepancy here |
| the pile hash | `CLAUDE.md` publishes `3feca53e…` as if it were a file hash; the file itself hashes to `d3140eff…` | reports the battery's finding (D-B-011): the cut is intact, only the description misleads |
