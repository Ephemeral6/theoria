# U3 census

Discovery: `exam/u3_census.py`.  Every verdict below is the return value of a `freeze/u3.py` function -- this census decides *which* books exist, never *whether* one attained.

**17 / 24 books attained U3.**

> STATS_RULES.md §1.2: the U3 attainment rate's denominator is fixed at 19 sealed games (12 at the clean layer), with no exclusions and no cap.  Nothing on disk today is a sealed game, so the frozen rate is not computable from this census and this census does not claim to compute it.

| book | territory | verdict | label | route | files |
|---|---|---|---|---|---|
| `a0-spike/artifacts` | a0-spike | **attained** | discharged | u3.evaluate | A0.lean |
| `cold-start-a0/prime/theory/generated` | cold-start-a0 | not attained | vacuous | u3.evaluate | theory.lean |
| `cold-start-a0/theory/generated` | cold-start-a0 | **attained** | discharged | u3.evaluate | theory.lean |
| `cold-start-a0/theory/generated_no_button` | cold-start-a0 | **attained** | discharged | u3.evaluate | theory.lean |
| `cold-start-a2/theory/generated` | cold-start-a2 | **attained** | discharged | u3.evaluate | theory.lean |
| `cold-start-a2/theory/generated_holed` | cold-start-a2 | **attained** | discharged | u3.evaluate | theory.lean |
| `cold-start-a2/theory/generated_repaired` | cold-start-a2 | **attained** | discharged | u3.evaluate | theory.lean, theory_latch.lean |
| `cold-start-a2/theory/generated_repaired_stale` | cold-start-a2 | not attained | failing_obligation | u3.evaluate | theory.lean |
| `cold-start-a3/runs/20260728T1800Z-A6-transfer-protocol/generated/a3_l2_oneway` | cold-start-a3 | **attained** | discharged | u3.evaluate | theory.lean |
| `cold-start-a3/runs/20260728T1800Z-A6-transfer-protocol/generated/a3_l2_positive` | cold-start-a3 | **attained** | discharged | u3.evaluate | theory.lean |
| `cold-start-a3/runs/20260728T1800Z-A6-transfer-protocol/generated/a3_l2_rewired` | cold-start-a3 | **attained** | discharged | u3.evaluate | theory.lean |
| `cold-start-a3/theory/generated_l1` | cold-start-a3 | **attained** | discharged | u3.evaluate | theory.lean |
| `cold-start-a3/theory/generated_l1_vacuous` | cold-start-a3 | not attained | vacuous | u3.evaluate | theory.lean |
| `cold-start-a3/theory/generated_l2` | cold-start-a3 | **attained** | discharged | u3.evaluate | theory.lean |
| `cold-start-a3/theory/generated_l2_scratch` | cold-start-a3 | **attained** | discharged | u3.evaluate | theory.lean |
| `cold-start-a3/theory/generated_l2neg` | cold-start-a3 | **attained** | discharged | u3.evaluate | theory.lean |
| `cold-start-a3/theory/generated_l2rew` | cold-start-a3 | **attained** | discharged | u3.evaluate | theory.lean |
| `theory-compiler/handover_packages/a0-cart/levels/base` | theory-compiler | not attained | unclassified | u3.evaluate | Level.lean |
| `theory-compiler/handover_packages/a0-cart/levels/no-button` | theory-compiler | not attained | unclassified | u3.evaluate | Level.lean |
| `theory-compiler/handover_packages/a0-sokoban2/levels/crossing-up` | theory-compiler | not attained | unclassified | u3.evaluate | Level.lean |
| `theory-compiler/handover_packages/a0-sokoban2/levels/match` | theory-compiler | not attained | unclassified | u3.evaluate | Level.lean |
| `theory-compiler/lean` | theory-compiler | **attained** | discharged | u3.evaluate | TheoriaLean.lean |
| `theory-compiler/runs/20260728T080019Z-C4-deadlock-lean` | theory-compiler | **attained** | discharged | u3.evaluate | corner.lean, pair.lean |
| `theory-compiler/runs/20260728T080019Z-C4-deadlock-lean/verify` | theory-compiler | **attained** | discharged | u3.evaluate | Control_corner.lean, Control_pair.lean, Deadlock_corner.lean, Deadlock_pair.lean, Ic3_algebraic.lean, Ic3_computational.lean |

## labels

* `discharged` — 17
* `failing_obligation` — 1
* `unclassified` — 4
* `vacuous` — 2

## theorem-kind coverage of the (c) check

| kind | theorems seen | (c) passed | (c) never ran | check implemented? |
|---|---|---|---|---|
| `invariant` | 39 | 35 | 0 | yes |
| `point_claim` | 20 | 0 | 20 | no — permanent, §1.2.1 asks nothing of this shape |
| `prune` | 2 | 2 | 0 | yes |
| `unclassified` | 16 | 0 | 16 | no — fails closed |
| `unsolvable` | 1 | 0 | 0 | yes |
| `witness` | 10 | 0 | 10 | no — permanent, §1.2.1 asks nothing of this shape |

**Coverage gaps (a defect): `unclassified`.**

**Permanent non-attainers (not a defect): `point_claim`, `witness`.**

A kind in `coverage_gaps` has no implemented §1.2.1 (c) check in freeze/u3.py, so every theorem of that kind fails closed and cannot carry its development to `discharged`, no matter what it proves. A kind in `permanent_non_attainers` (`point_claim`, `witness`) is a supporting obligation rather than a claim about the world; §1.2.1 writes no requirement for it and none is missing. Only the first list is a defect.


## runs that reached certify with no book

**20 runs, 0 attained.** Runs that reached the certify stage and emitted no Lean development. Reported separately and NEVER folded into the book rate: a run with no book fails U3 for a different reason than a book that proves a tautology, and folding them would let 'the arm stopped writing manuals' raise the attainment rate.

| label | runs |
|---|---|
| `declared_refusal` | 10 |
| `no_evidence` | 9 |
| `no_proof_layer` | 1 |

## excluded subtrees (declared, not silent)

* `a0-spike/pipeline/__pycache__` — build cache
* `a0-spike/world/__pycache__` — build cache
* `battery/__pycache__` — build cache
* `cold-start-a2/a2world/__pycache__` — build cache
* `engine-rig/common/__pycache__` — build cache
* `engine-rig/engines/__pycache__` — build cache
* `engine-rig/engines/cegis_miner/__pycache__` — build cache
* `engine-rig/engines/mdl_segmenter/__pycache__` — build cache
* `engine-rig/engines/zero_space/__pycache__` — build cache
* `exam/__pycache__` — build cache
* `exam/grading/__pycache__` — build cache
* `exam/papers/__pycache__` — build cache
* `exam/runs/20260730T021500Z-V23-large-space/__pycache__` — build cache
* `exam/tests/__pycache__` — build cache
* `exam/tools/__pycache__` — build cache
* `freeze/__pycache__` — build cache
* `monitor/runs/_worktree-scratch-archive` — archived byte-copies of other territories' trees; counting them double-counts books already counted at their real home
* `proxy/__pycache__` — build cache
* `theory-compiler/src/theory_compiler/__pycache__` — build cache
* `theory-compiler/src/theory_compiler/parser/__pycache__` — build cache
* `worldgen/__pycache__` — build cache
* `worldgen/core/__pycache__` — build cache
* `worldgen/mechanisms/__pycache__` — build cache
