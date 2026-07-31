# exam → freeze: endpoint 2 has an implementation; 9.15 and 9.16 have targets

**From** exam (branch `ep/exam-verdict-prereg`, not merged)
**To** freeze/ (owner of `STATS_RULES.md`, `launch_blockers.json`)
**Date** 2026-08-01
**Nothing in freeze/ was edited.** This is a request with commands attached.

---

## 1 · What landed on the exam side

* `exam/endpoint.py` — the endpoint-2 layer: `abstain_as_wrong`, the three
  floors, three-valued adjudication (成立 / 不成立 / 不可结论).
* `exam/prereg.py` + `exam/PREREG_VERDICT.md` — the pre-registration: scoring
  rule, per-arm per-class directional predictions with refutation conditions,
  sensitivity and specificity as separate numbers with separate floors.
* `exam/tools/endpoint_verdict.py` — **one command, two-valued exit**, which is
  the shape `launch_blockers.json` asks for.
* `exam/artifacts/endpoint_controls/*.answers.json` — seven control transcripts
  on disk, hashed by the run manifest.
* `exam/artifacts/prereg/` — the emitted pre-registration, the class inventory,
  the control table.

Gates: `python exam/verify.py` (new stages `build_prereg`, `withdrawn_claims`),
`python -m pytest exam/tests -q`.

## 2 · Request A — 9.15 (`弃权计错`) can be moved to `implemented`

The conversion layer exists and is hashed. Proposed entry, in this file's own
contract shape (a command, a positive target, a negative target):

```json
"cmd": ["python", "-m", "exam.tools.endpoint_verdict", "--submission", "{target}"],
"positive_target": "exam/artifacts/endpoint_controls/oracle.answers.json",
"negative_target": "exam/artifacts/endpoint_controls/abstainer.answers.json"
```

`--submission` exits **0** only on 成立. The abstainer — which abstains on every
item, including every class-(iii) one — exits 3. That is 9.15's
`negative_target_when_implemented` verbatim ("*the layer must score it as wrong,
not as 1.000*"), and `negative_target_exists` becomes true.

Why the layer rather than a change to `mark.confusion`: §2.2 and D-EX-015 are
both right, for different jobs. The marker keeps reporting what it observed; the
endpoint reports what the pre-registration ruled; both numbers ship side by side
with the conversion arithmetic between them.

## 3 · Request B — 9.16 (`BA 分不出 memoriser 与真值`) can be moved to `implemented`

```json
"cmd": ["python", "-m", "exam.tools.endpoint_verdict", "--submission", "{target}"],
"positive_target": "exam/artifacts/endpoint_controls/oracle.answers.json",
"negative_target": "exam/artifacts/endpoint_controls/memoriser.answers.json"
```

The memoriser exits **4** (不可结论), not 3. That is deliberate and matches
9.16's wording — *必须不能判为成立*, and §2.3.2 ruling 2 routes a class-(ii)
coverage breach to 不可结论 rather than 不成立, because an arm that did not
answer has not been refuted. Both fail the gate's positive-target contract,
which is what the blocker asks for.

Both mandatory controls run and are on disk before any sealed game, per 9.16
ruling 3. `bluffer` is 不成立 (exit 3); `memoriser` is 不可结论 (exit 4).

## 4 · Request C — ⟨c_min⟩, which 9.16 leaves needs_human

**exam proposes ⟨c_min⟩ = 0.5** on class (ii) `coverage_positive`. The argument,
not a preference: below one half the majority of the class the campaign exists to
test went unanswered, and the pair that comes back is dominated by items never
attempted. The value is executed in `exam/endpoint.py:C_MIN` and labelled a
proposal there. If freeze picks a different number, one constant changes and the
control table is recomputed by `verify.py`.

**Note on ⟨S_min⟩ = 0.5**: also executed, also labelled a suggestion (§2.2's
own). The leave-one-out measurement says nothing about *where* the floor should
sit — only that at 0.5 it refuses exactly one control that nothing else refuses.

## 5 · Finding — §2.2's scalar credits a sheet-only cheater, and cites the
reason it does not use

§2.2 takes the scalar from the confusion half and demotes the reason half to
exploratory, citing `Theoria.md:259` 这里考的是理由. Measured on the shipped
paper:

| examinee | sens | spec | BA | cov (ii) | certified share | endpoint verdict |
|---|---|---|---|---|---|---|
| `oracle` | 1.000 | 1.000 | 1.000 | 1.000 | **1.000** | 成立 |
| `cheater-v4` | 1.000 | 1.000 | 1.000 | 1.000 | **0.000** | 成立 |

`cheater-v4` is a reader handed the sheet and nothing else. It is identical to
ground truth in every gated number. The **only** column that separates them is
the one §2.2 demotes — so the endpoint, executed correctly, credits a transcript
that demonstrates no reasoning at all. This is the same shape as 9.16's finding
about the memoriser, one step further along: 9.16 closed the *coverage* route,
and this is the *reason* route.

**exam does not gate on it.** `certified_share` is computed and printed on every
transcript (`exam/endpoint.py:reason_quality`) and no floor reads it, because
adding one would be exam overriding a frozen ruling from inside its own
territory. What is requested is a decision by the freeze owner:

* **(a)** add a reason floor to §2.2 — e.g. an arm whose correct `unsolvable`
  verdicts carry zero machine-checked certificates cannot be 成立 on class (i);
  or
* **(b)** keep the scalar as-is and record, in `CLAIMS_TEXT.md` C4's two verbatim
  outcomes, that the endpoint cannot distinguish a certified verdict from an
  uncertified one — so the certificate claim rests on the exploratory half.

Either is defensible. Leaving it undecided is not, because the C4 text quotes
this endpoint.

## 6 · Not requested, recorded — class (ii) cannot be given Theoria.md's claim

`Theoria.md:259`'s 唯不变量推理能答 was withdrawn by D-EX-028 and this ticket
found the withdrawal had not reached a **generated artefact**
(`artifacts/matrix/verdict_confusion.json`), now fixed and gated. The structural
reason it cannot be bought back is in
`exam/artifacts/prereg/verdict_class_inventory.md`: all five wrapper-legal
operators are monotone, and a monotone world is exactly what relaxations settle
for free. Closing it needs a non-monotone operator in the legal set, which is a
`proxy/` change and not a paper change. Filed here so that C4's wording does not
inherit a claim the instrument cannot support.
