# EP · endpoint 2 gets an executable protocol, and a floor gets a vote

Branch `ep/exam-verdict-prereg`, base `21a724ed`. Territory: `exam`.
Zero network, zero model calls, zero sealed-pile contact, no live spend.

## What the ticket asked, and what was actually there

> 判决题准确率 is the third frozen primary endpoint and has no cross-arm
> pre-registration.

Half true, and the half that was false is the more useful finding.
`freeze/STATS_RULES.md` §2 is a substantial pre-registration: the scalar
(BA from the confusion half), the specificity floor, the ⟨m⟩-selection rule
frozen to a codepoint-ordered prefix, and a gaming audit that had already caught
two holes and registered them as launch blockers. What was missing was
**everything executable**: no scoring rule tied to the code by more than a line
number, no directional prediction per arm per class, and §2's own two rulings
unimplemented — `freeze/launch_blockers.json` 9.15 and 9.16, both
`state: unimplemented`, 9.15 with `negative_target_exists: false`.

So the ticket's four items map onto that:

| asked | found | done |
|---|---|---|
| 1. which classes have items, on what constructive basis | all three, 5 / 4 / 8, every item with a spec-level justification | emitted as an inventory artefact, per item, quoting the spec's own field |
| 2. class (ii) does not embody its claimed difficulty | already withdrawn by D-EX-028 — **but still shipping in a generated artefact** | fixed, gated, and the structural argument for why it cannot be bought back written down |
| 3. pre-registration: scoring rule, per-arm per-class behaviour, sens/spec separately | absent | `exam/prereg.py` + `PREREG_VERDICT.md`, checked against the built paper on every verify run |
| 4. negative controls in both directions | one direction only (`bluffer`), and the mirror missing | seven controls, three floors, leave-one-out — which refuted the first draft |

## The measurement that changed the design

`prereg.floor_leave_one_out()` disables each floor in turn and re-judges every
control. First run:

```
{"all_floors": [], "without_S_min": [], "without_c_min": ["memoriser"],
 "without_ba_floor": ["denier"]}
```

`without_S_min: []` — deleting the specificity floor changed **no verdict**.
`bluffer`, `abstainer` and `null` all fail the BA floor as well, so the floor
`STATS_RULES.md` §2.2 calls a 一票否决 had never been observed to cast one, and
this document's draft claim that it caught the abstainer and the null was simply
wrong. `overclaimer` was built to be the case only `S_min` refuses — sensitivity
1.000, specificity 0.375, BA 0.688, full class-(ii) coverage. Now:

```
{"all_floors": [], "without_S_min": ["overclaimer"],
 "without_c_min": ["memoriser"], "without_ba_floor": ["denier"]}
```

Each floor catches exactly one control alone. The table is recomputed on every
verify run and pinned by `test_every_floor_catches_something_on_its_own`.

## The control table as shipped

| examinee | sens | spec | BA | cov (ii) | cert | verdict |
|---|---|---|---|---|---|---|
| `oracle` | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | **成立** |
| `bluffer` | 1.000 | 0.000 | 0.500 | 1.000 | 0.000 | 不成立 |
| `denier` | 0.000 | 1.000 | 0.500 | 1.000 | -- | 不成立 |
| `overclaimer` | 1.000 | 0.375 | 0.688 | 1.000 | 0.000 | 不成立 |
| `abstainer` | 0.000 | 0.000 | 0.000 | 0.000 | -- | 不成立 |
| `memoriser` | 0.556 | 0.625 | 0.590 | 0.000 | 1.000 | 不可结论 |
| `null` | 0.000 | 0.000 | 0.000 | 0.000 | -- | 不成立 |
| `cheater-v4` (real) | 1.000 | 1.000 | 1.000 | 1.000 | **0.000** | **成立** |

Rates are after 弃权计错; the marker's observed rates ship beside them. The last
row is the honest residual: the endpoint credits a reader who was handed the
sheet and nothing else, and the only column that separates it from ground truth
is the one `STATS_RULES.md` §2.2 demotes to exploratory. Reported, not gated,
and raised to freeze through the inbox — see §5 of
`monitor/inbox/20260801T0000Z-exam-endpoint2-prereg-and-two-launch-blockers.md`.

## Class (ii), the part that is not fixable here

The withdrawal was made three cycles ago and had not reached
`artifacts/matrix/verdict_confusion.json`, which is the copy a reader quotes.
Fixed, and `tools/check_withdrawn_claims.py` now scans every tracked live
surface in the territory (105 files; `exam/runs/**` exempt, because a provenance
archive that quotes what it was investigating must not be rewritten).

On constructing genuinely harder items: it cannot be done under the frozen
operator library, and the reason is structural rather than a lack of effort.
构造性依据 requires the truth to follow from construction, so every unsolvable
item has a short proof — all nine carry one in the closed grammar, checkable in
polynomial time. And all five wrapper-legal operators are **monotone**: they
remove behaviour and never un-latch a switch, which is exactly the structure a
relaxation settles for free. A level whose relaxation returns *unknown* needs a
non-monotone dynamic, and the wrapper cannot introduce one because the hosted
environment owns the dynamics. Written into the inventory artefact next to the
items, and filed to freeze so C4's wording does not inherit the stronger claim.

## Gates

```
python -m pytest exam/tests -q      → see MANIFEST.json `gates`
python exam/verify.py               → see MANIFEST.json `gates`
```

Two new verify stages: `build_prereg` (the pre-registration still describes the
paper that builds, and every control is still judged as pre-registered) and
`withdrawn_claims`.

**The rubric digest moved**, `f01dbeb2b6c6` → `26a518d99d99`, because the digest
is over rubric source and a false sentence in a docstring was corrected. Every
artefact was rebuilt and committed with that reason. A digest that ignored prose
would let the rubric's description of what it measures drift free of the rubric.

## Residual, stated plainly

* **The cross-arm test is not implemented and is not implied.** This decides one
  transcript on one paper. ⟨m⟩ is needs_human in freeze and §2.2.1's arithmetic
  already shows ⟨m⟩ ≤ 12 kills C4 before any data exists. Not exam's call.
* **⟨S_min⟩ and ⟨c_min⟩ are executed, not adopted.** 0.5 each; the first is
  §2.2's own suggestion, the second is exam's proposal with an argument.
  Leave-one-out says the floor at 0.5 refuses exactly one control that nothing
  else refuses; it says nothing about where else the floor could sit.
* **The endpoint credits `cheater-v4`.** Above, and in the inbox.
* **Class (ii) still measures method selection**, not invariant necessity, and
  no work inside `exam` can change that.
* **No arm has sat this paper.** Asserted by
  `test_no_arm_has_sat_this_paper_yet`, which reads the answers directory rather
  than trusting this sentence.
