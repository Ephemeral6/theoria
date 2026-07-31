# 判决题准确率(含特异度) — exam's half of the pre-registration

> 主终点限三个——U3 达成率、**判决题准确率(含特异度)**、前载指数配对差
> — `Theoria.md:373`

**Status: exam's half is frozen with this commit. The freeze-bound half is
proposed, not adopted** — three of the numbers below live in `freeze/` and two
of them are `needs_human` there. This document says what `exam` executes and what
it asks `freeze/` to adopt; the request is
`monitor/inbox/20260801T0000Z-exam-endpoint2-prereg-and-two-blockers.md`.

Machine-readable twin: [`prereg.py`](prereg.py) (`PREREG`, checked against the
built paper by `prereg.check()`), emitted to
[`artifacts/prereg/verdict_prereg.json`](artifacts/prereg/verdict_prereg.json).
Where this prose and that module disagree, **the module is right** — it is the
one a gate reads.

---

## 0. What was missing, in one paragraph

`freeze/STATS_RULES.md` §2 pre-registers the statistic, the specificity floor,
the ⟨m⟩-selection rule and a gaming audit. It does not carry a scoring rule tied
to the code by anything but line numbers, it carries no per-arm per-class
directional prediction, and two of its own rulings are **not** what the
implementation it cites does — both registered as launch blockers (9.15, 9.16)
and both unimplemented until this commit. So the endpoint had a statistic and no
executable protocol, which is the state in which a result can be produced and
then interpreted.

---

## 1. The scoring rule, as executed

| | |
|---|---|
| paper | `p15-verdict-a2`, 17 items, frozen mix **5 / 4 / 8** |
| points | 2.0 per item, unsolvable and solvable alike |
| split | half the item is the **claim**, half is the **reason** |
| search credit | `"I searched and found nothing"` pays **0.4 of the reason**, and only where the space is small enough for that to be true |
| certificate grammar | closed: `invariant`, `cut_set`, `counting`. Every number in a submitted certificate is re-derived from the level |
| answer alphabet | `unsolvable`, `solvable`, `abstain`. Anything else is unreadable, and unreadable is **not** an abstention |
| endpoint scalar | **BA = (sensitivity + specificity) / 2**, from the confusion half after 弃权计错 |
| the score is not the scalar | the marks total folds the reason half in; reported, never the endpoint (STATS_RULES §2.2) |

The three weights (0.5 / 0.5 / 0.4) are pre-registered in `prereg.py` and
compared against the live rubric constants on every verify run. Moving one turns
the gate red instead of quietly redefining the endpoint.

## 2. 弃权计错 — the conversion, and why it is a layer

`STATS_RULES.md` §2.2 rules that an abstention counts as wrong and names
`mark.confusion()` as the implementation. That implementation does the opposite
and D-EX-015 records the opposite as the right call. **Both are right, for
different jobs**, so neither is edited: `exam/endpoint.py:abstain_as_wrong` is a
layer over the marker's output that folds all three non-answers —
`abstained`, `unanswered`, `unclassified` — into the error cell on the truth's
own side.

Two consequences, and the second is the one that matters:

* `tp + fn` and `tn + fp` equal the class sizes, on every examinee;
* therefore **neither rate is ever undefined**, and `specificity < S_min` has a
  total order. Before this, an arm that abstained its way to an empty negative
  denominator got `None`, and `None < 0.5` is not false — the one-vote veto was
  structurally untriggerable (`launch_blockers` 9.15).

**Coverage is read before the conversion, never after.** Conversion fills every
denominator by construction, so a coverage computed afterwards is the constant
1.0 wearing a measurement's name.

## 3. The readouts

**Reported, always, and as separate numbers:** sensitivity; specificity;
class-(ii) `coverage_positive`; the three non-answer counts; `certified_share`.

**Derived:** BA. It never appears without both halves beside it.

**Forbidden:** BA alone; a single accuracy over all 17 items; any rate whose
denominator excluded abstentions.

## 4. The floors, and what each is for

| floor | value | source | catches, alone |
|---|---|---|---|
| `S_min` | 0.5 | STATS_RULES §2.2 (⟨S_min⟩ needs_human) — breach is **不成立**, whatever BA says | `overclaimer` |
| `c_min` | 0.5 | `launch_blockers` 9.16 (⟨c_min⟩ needs_human; **exam proposes 0.5**) — breach is **不可结论**, never 不成立 | `memoriser` |
| BA | > 0.5, strict | **exam**: both constant strategies score exactly 0.5 | `denier` |

The BA floor is not a taste. Always-`unsolvable` gives (1.0, 0.0);
always-`solvable` gives (0.0, 1.0); each averages to one half. `BA > 0.5` is
therefore the weakest possible statement that an arm did something a constant
does not do, and `>=` would credit the controls themselves.

**Rule order is part of the pre-registration**: specificity floor, then class
(ii) coverage, then BA. §2.2 makes the specificity veto independent of BA, so it
cannot sit behind a test that might exit first; coverage routes to 不可结论
because an arm that did not answer has not been refuted.

## 5. The arms' expected behaviour, per class

Written before any arm sits the paper. Each row has a refutation condition; the
full table with reasons is `prereg.ARM_EXPECTATIONS`, and a missing cell is a
build failure.

| | class (i) small | class (ii) large | class (iii) solvable-hard |
|---|---|---|---|
| **bare_cc** | verdict often right, `certified_share` **0.0** — no deliverable to write a certificate in | coverage **below `c_min`**: abstains or does not answer | specificity **≥ S_min** — this is where the bare arm should look best |
| **ablation** (−定理义务) | same verdict accuracy as theoria, materially lower `certified_share` | answers, right about as often as theoria, no certificate | specificity ≥ S_min and no lower than theoria's |
| **theoria** | sensitivity 1.0, `certified_share` **> 0.5** | coverage **1.0**, sensitivity 1.0 — abstention here is a failure, not caution | specificity **≥ 0.75**, above the floor with margin |

The discriminating prediction is not the verdict, it is the reason: bare_cc and
the ablation are predicted to reach the same verdicts and to be unable to
certify them. If theoria's class-(i) `certified_share` does not exceed bare_cc's,
that row is refuted and the endpoint says so.

## 6. The negative controls — both directions, and one blind spot

Run before any arm, hashed, and on disk under
[`artifacts/endpoint_controls/`](artifacts/endpoint_controls/).

| control | sens | spec | BA | cov (ii) | verdict |
|---|---|---|---|---|---|
| `oracle` | 1.000 | 1.000 | 1.000 | 1.000 | **成立** |
| `bluffer` — always `unsolvable` | 1.000 | 0.000 | 0.500 | 1.000 | 不成立 |
| `denier` — always `solvable` | 0.000 | 1.000 | 0.500 | 1.000 | 不成立 |
| `overclaimer` — `unsolvable` but for three | 1.000 | 0.375 | 0.688 | 1.000 | 不成立 |
| `abstainer` | 0.000 | 0.000 | 0.000 | 0.000 | 不成立 |
| `memoriser` | 0.556 | 0.625 | 0.590 | 0.000 | 不可结论 |
| `null` | 0.000 | 0.000 | 0.000 | 0.000 | 不成立 |

`bluffer` and `denier` are a matched pair: one buys sensitivity with
specificity, the other the transpose. A gate that had only ever seen the first
could not be told apart from one that simply distrusts the word `unsolvable`.

**`overclaimer` exists because a measurement refuted this document's first
draft.** `S_min` was written down as the floor that catches the abstainer and
the null submission; disabling `S_min` changed no verdict at all, because both
of those fail the BA floor too. A floor that has never been observed to cast a
vote is a floor carried on the strength of its name, so a control was built to
be the case only `S_min` refuses. Leave-one-out is recomputed on every verify
run and pinned by a test.

**The blind spot, stated rather than hidden.** `cheater-v4` — a real transcript
from a reader handed the sheet and nothing else — is **credited**, and is
identical to `oracle` in every gated number. The one column that separates them
is `certified_share`, 0.000 against 1.000, and `STATS_RULES.md` §2.2 demotes
exactly that column to exploratory while citing 这里考的是理由 as the reason for
its choice of scalar. exam publishes the number on every transcript and does not
gate on it: legislating it here would be one territory overruling a frozen
document from inside its own. The amendment is in the inbox.

## 7. Scope — what a `成立` from this gate does not mean

This decides **one transcript on one paper**: the floors, and whether the pair
can be read at all. `STATS_RULES.md` §2.2.1's cross-arm paired test over ⟨m⟩
exam games is not implemented here and is not implied. ⟨m⟩ is `needs_human`, and
§2.2.1's own arithmetic shows ⟨m⟩ ≤ 12 kills C4 before any data exists — that
decision is not exam's to make and nothing here anticipates it.

## 8. Class (ii) — what it may claim

Theoria.md 1.11 calls class (ii) 唯不变量推理能答. **That is withdrawn**
(D-EX-028) and this pre-registration does not restate it. What class (ii)
establishes is `naive_enumeration_feasible: False` against a constructive bound
of 2^60 to 2^120, and what it scores is **method selection under an apparent
search barrier**. Every shipped item of the class is settled by an exhaustive
computation over at most 600 nodes.

Why it cannot be given the stronger claim, and what it would take, is
[`artifacts/prereg/verdict_class_inventory.md`](artifacts/prereg/verdict_class_inventory.md)'s
closing section: a variant known unsolvable *by construction* has a short proof
by definition, and the five wrapper-legal operators are all monotone, so no
wrapper can build a level whose relaxation returns *unknown*. Closing it needs a
non-monotone operator in the legal set — an environment-proxy change, not a
paper change.
