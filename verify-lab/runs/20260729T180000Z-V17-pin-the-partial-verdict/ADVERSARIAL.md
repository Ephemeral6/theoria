# Adversarial pass on the `部分` criterion

Commissioned to break `verify-lab/PARTIAL_CRITERION.md`, not to praise it. Two
charges were named: **(a)** does the criterion hide the disagreement in another
cell rather than resolve it, and **(b)** is the agreement improvement real or
three agents converging on one document.

Everything below was re-derived. `agree.py`, `overlap.py`, `sample.py`,
`shapes.py`, `refold.py`, `blindtree.py` were run; `po`, Fleiss κ, the bootstrap,
the blinding residue and the confusion matrix were recomputed from the judge
tables by an independent script in a scratch directory. No file under
`verify-lab/` was modified except this one.

**Reviewed state.** `MANIFEST.json` `head_commit` `139f70b`, base `f09555c`.
The run directory changed under me mid-review: `MANIFEST.json`, `refold.py`,
`refold.json`, `RELIABILITY.md` and the bootstrap block in
`agreement.stdout.txt` all appeared after I had read the earlier artefacts. Where
`RELIABILITY.md` already concedes a point I say so and do not claim it.

Verdict up front: **加限定就够 — qualify, do not withdraw.** The criterion is
under-specified in four places its own judges named, one worked example cites the
wrong assertion, and two published claims are false as written and must be
withdrawn. But the load-bearing finding of the run — that the criterion did *not*
significantly raise inter-judge reliability — is honestly reported, and I found
one measurement the author did not compute that materially strengthens the case
that the document does something real. Details in §C.

**The single most useful number in this run is not in any artefact.** The
author's preregistered dry read matches the *new* arm's majority on 21/22 rows
(13/14 on the `部分` stratum) and the *old* arm's majority on **9/22** (3/14).
Same model, same tree, same 22 files. The document moves where the consensus sits
by **+54 percentage points** while moving how tightly the judges agree with each
other by **+0.078 κ, CI crossing zero**. That is the honest description of what
happened: *the criterion relocated the consensus without tightening it*, and it
relocated it in the direction that lowers the measured FNR. Neither
`RELIABILITY.md` nor the criterion says this.

---

## A. Charges that land

### A1. Worked example 3.3 cites the one assertion that fails its own D3 — adjudicated

`RELIABILITY.md:178-181` refers N2's contradiction charge to this review. Here is
the adjudication, and it splits.

**N2's charge as stated does not stand.** N2 (`judgements/N2.md:64-72`) claims
§3.3 and the panel's unanimous `否(D3)` on `certify_a3.py` "cannot both be right."
They can. Chain of custody, verified in the tree:

| step | file:line | what it does to the value |
|---|---|---|
| origin | `cold-start-a0/certify/replay.py:111` | `"green": not anomalies` |
| hop 1 | `cold-start-a3/a3pipeline/certify_a3.py:87` | `return replay.certify(...)` — pass-through |
| hop 2 | `cold-start-a3/a3pipeline/certify_a3.py:109` | `"green": report.get("green")` — pass-through |
| hop 3 | `cold-start-a3/a3pipeline/transfer.py:183` | `report["certify_replay"] = certify_a3.cheap_brief(replay)` — pass-through |
| hop 4 | `cold-start-a3/a3pipeline/negctl.py:115` | written out as `replay_certify_green` |
| assertion | `cold-start-a3/tests/test_transfer.py:217` | `assert row["replay_certify_green"] is False` |

By `PARTIAL_CRITERION.md:156` ("看那行断言里的表达式出自哪个文件") that value is
`replay.py`'s. `certify_a3.py` contributes nothing to it and owns nothing else in
the chain, so `否(D3)` is correct and the three judges are right.

But `transfer.py` **does** own a value in the same artefact:
`transfer.py:196` computes `report["outcome"]` itself, `negctl.py:106` derives
`caught = (report.get("outcome") != "win")` from it, `negctl.py:126` aggregates
`all_caught`, and `test_transfer.py:213` asserts `verdict["all_caught"] is True`.
`transfer.py:195` likewise owns `theorize_triggered`, asserted at
`test_transfer.py:216`. Either of those passes D3. So §3.3's **verdict** survives.

**What lands is the citation.** `PARTIAL_CRITERION.md:103` picks, out of the six
assertions in `test_transfer.py:211-218`, the exactly one that fails D3:

> `tests/test_transfer.py:211-218` 断言 `replay_certify_green is False`。

A judge who reads §3.3 literally learns that asserting `replay_certify_green`
satisfies D3. Applied to `certify_a3.py` that yields `部分`; three judges who read
the same document produced `否` instead, unanimously, by inventing a rule the
document does not contain (thin wrappers do not inherit the wrapped file's red —
N1.md:2.2, N3.md point 2). **The criterion got the right answers on both rows for
a reason it never states, and the reason it does state gives the wrong answer on
one of them.** §3.3 must cite `test_transfer.py:213` (`all_caught`) or `:216`
(`theorize_triggered`) and say in one sentence that a pure forwarding layer owns
none of its callee's values.

Cost, measured: this is not cosmetic. `certify_a3.py` is one of the 8 rows whose
re-judgement moves the pinned strict matrix (`refold.stdout.txt`), and N1 marked
it `判据不决` for exactly this reason (`N1.md:21`, `N1.md:72`).

### A2. The reason code — the criterion's only stated defence — is measurably worse than the question it replaced

`PARTIAL_CRITERION.md:67-70` states the defence for charge (a) verbatim:

> `部分` 变窄了，但被挪走的行**带着标签**，任何人都可以在 `D1`/`D2`/`D3`
> 任一处重新划线再折叠一次，不必重判。（对抗复核会专打「窄格藏分歧」这一条 ——
> 理由码就是给它准备的账。）

`RELIABILITY.md:154-159` publishes verdict `po=0.939` next to reason-code
`po=0.773` and calls the ledger "比它记的判决更不一致". That is the wrong
comparison. The question is not whether the reason code is noisier than the
verdict; it is whether the criterion's **total output** is more reliable than the
undefined question it replaced. Computed on the joint label `(verdict, reason)`:

| | n | po | Fleiss κ | unanimous |
|---|---|---|---|---|
| `old` arm, verdict only (no definition of `部分`) | 22 | 0.848 | **0.764** | 17/22 |
| `new` arm, verdict only | 22 | 0.939 | 0.882 | 20/22 |
| **`new` arm, joint (verdict + reason code)** | 22 | **0.773** | **0.718** | 15/22 |
| `old` arm, verdict only, `部分` stratum | 14 | 0.810 | **0.689** | 10/14 |
| **`new` arm, joint, `部分` stratum** | 14 | **0.738** | **0.669** | 9/14 |

κ is chance-corrected, so the extra categories are already paid for. **The full
label the criterion emits is less reliable than the bare verdict of the question
that had no definition at all: κ 0.718 against 0.764, and 0.669 against 0.689 on
the stratum that matters.** The verdict column got quieter by +0.118 κ; the label
as a whole got noisier by −0.046 κ.

The defence at `PARTIAL_CRITERION.md:67-70` therefore fails as written. A ledger
that cannot be reproduced by a second reader is not a ledger, and this one is
reproduced less often than the thing it was meant to make auditable.

**The sharpest single exhibit is `monitor/scan.py`.** Verdict unanimous `否`;
reason codes `D3/D0/D2` (`agreement.json:361-365`) — three judges, three
different diagnoses, **no majority reason code at all**. The row is therefore
untyped, and the promised re-fold is undefined on it: re-fold at D3 and it is
`部分` for N1 and `否` for N2/N3; re-fold at D2 and it is `部分` for N1 and N3 and
`否` for N2. "不必重判" is false for this row. It is one of 5 rows (23% of the
sample, 38% of the 13 unanimous-`否` rows) whose verdict is unanimous and whose
reason is not: `e2_a2.py` `D2/D2/D3`, `ci_merge.py` `D1/D0/D1`, `reflex.py`
`D1/D0/D1`, `scan.py` `D3/D0/D2`, `fig2_coverage_accuracy.py` `D1/D0/D1`.

**`否` is a bag, and its composition is measurable.** Of the new arm's 43 `否`
votes: `D2` 20 (47%), `D1` 9 (21%), `D3` 7 (16%), `D0` 7 (16%). Four different
pathologies in one cell, and N2's point 1 is right that `D0` ("cannot go red at
all") is categorically unlike the other three ("could go red, nobody showed it").

**The `是` cell absorbed one row, and it is disclosed.**
`theory-compiler/.../strips_encoding.py` moved `部分 → 是` unanimously. V15's cell
(`SUPPLEMENT_TABLE.md:62`) grades it `部分` precisely because the single control
hits only the constructor and `verify()`'s own rejection path "全树无任何测试或坏
fixture 演示过". `PARTIAL_CRITERION.md:147-150` declares within-file coverage gaps
out of scope and calls it "一次真的放宽" in advance. So this is honest, not
absorption by stealth — but it is the *only* thing keeping `部分` from being a
pure drain in the `是` direction, and it is one row.

### A3. The placebo cannot fire, and its entire measured movement is D0 contamination

This is charge (b) and it lands twice.

**(i) The stated decision rule is unfalsifiable.** `agree.py:10-14` and
`RELIABILITY.md:61-63` state it: 「如果新判据组连它也更一致，多出来的一致就不是
判据」. The `old` arm scored `po = 1.000, κ = 1.000, unanimous 22/22`
(`agreement.stdout.txt:4`). "更一致" is unattainable above a ceiling. **The
probability that the placebo fires, under the author's own rule, is exactly
zero.** A test that cannot fail returns no information when it does not fail.

`RELIABILITY.md:115-117` nonetheless concludes:

> 所以「一致率的改善来自趋同压力」这条指控，在能测到的范围内**不成立**。

That inference is invalid and **must be withdrawn**. The correct statement is:
the placebo had no headroom, so this design could not have detected convergence
pressure on the placebo column even if it were total.

**(ii) All of the placebo's movement is criterion coupling.** The placebo moved
on exactly **2 of 22 rows**. Per-row, both arms:

| row | `old` 能红 | `new` 能红 | `new` 有负控 reason |
|---|---|---|---|
| `monitor/gates.py` | 部分/部分/部分 | **否/部分/否** | `D0/D0/D0` |
| `cold-start-a0/pipeline/engines_stage.py` | 部分/部分/部分 | **是/部分/部分** | `D2/D2/D2` |
| the other 20 rows | — | identical to `old`, unanimous | — |

`gates.py` is the one row on which all three new judges wrote `D0`, and it is
also the row where two of them flipped 能红 to `否`. That is `D0` writing directly
into the placebo column, exactly the coupling `BLINDING.md:64-66` admits ("会有
一点真实的溢出"). Measured, it is not 一点: **1 of the 2 movements, i.e. half the
entire placebo signal, is the criterion's own D0 test answering the placebo's
question.** Remove `gates.py` and the placebo delta is a single row on which one
judge said `是` where everyone else said `部分`.

So the placebo neither could have detected convergence (ceiling) nor is clean of
the criterion (D0). It carries no evidence in either direction. Both
`RELIABILITY.md:115-118` and `BLINDING.md:61-66` overstate it.

**(iii) The n is far too small, and this the author does now report.** Running
`agree.py` at HEAD gives the bootstrap the artefacts I first read did not have:

```
has_negctl_all             +0.118  95% CI [-0.109, +0.330]  P(delta<=0)=0.141
has_negctl_partial_stratum +0.078  95% CI [-0.533, +0.415]  P(delta<=0)=0.348
can_red_PLACEBO            -0.124  95% CI [-0.306, +0.000]  P(delta<=0)=1.000
```

On the 14-row stratum the interval is **0.948 wide against an effect of 0.078** —
a factor of 12. The data cannot distinguish "the criterion halved reliability"
from "the criterion nearly doubled it". `RELIABILITY.md:98-113` reports this
straight and calls the run under-powered; that concession stands and I have
nothing to add to it except that the *only* interval in the table that excludes
zero is the placebo's **fall**.

### A4. Five of 22 rows were marked `判据不决` by a judge who read the criterion, and no artefact says so

The judges were given a `判据不决` flag and used it:

* `N1.md:37` — 「标 `判据不决` 的行：**4**」: `certify_a2.py`, `exhibit.py`,
  `repair.py`, `certify_a3.py` (`N1.md:18,19,20,21`).
* `N3.md:35` — 「标注 `判据不决` 的行：**1**（`engine-rig/recheck/verify_all.py`）」.
* `N2.md:31` — 「`判据不决` **0** 行」.

Union: **5 distinct rows, 23% of the sample, 36% of the `部分` stratum.**

`agree.py:58-60` records the fourth table cell only when it matches
`^(D[0-3]|C|—|-)$`; the flag lives in the evidence cell and is discarded.
`agreement.json` contains no trace of it and `RELIABILITY.md` mentions it **zero
times** (grep).

Why this matters more than a missing column: line up the flagged rows against the
rows where anything was at stake.

| row | new-arm outcome | flagged `判据不决`? |
|---|---|---|
| `cold-start-a2/a2pipeline/certify_a2.py` | 部分 (unanimous) | **yes** (N1) |
| `cold-start-a2/a2pipeline/repair.py` | 部分 (unanimous) | **yes** (N1) |
| `cold-start-a0/certify/replay.py` | 部分 (unanimous) | no |
| `cold-start-a2/a2pipeline/exhibit.py` | **SPLIT** 否/否/部分 | **yes** (N1) |
| `engine-rig/recheck/verify_all.py` | **SPLIT** 否/否/部分 | **yes** (N3) |
| `cold-start-a3/a3pipeline/certify_a3.py` | 否, the A1 row | **yes** (N1) |

**Four of the five rows that carry a `部分` verdict or split the panel are rows a
criterion-reading judge declared the criterion does not decide.** The criterion is
confident exactly where the answer was already obvious (13 unanimous `否`, 4
unanimous `是`) and explicitly undecided where it is not. `po = 0.939` is computed
over forced choices on those rows. The number is not wrong; it is reported without
the fact that a fifth of it is forced.

The four under-specifications, all independently named by two or three judges,
are: **D0 precedence over D1/D2/D3** (N1 §2.3, N2 §1, N3 §4 — four rows), **the
"一件" requirement when runner and assertion live in two committed files** (N1
§2.1 — the default shape of all three cold-start arms), **`C` when `main` is a
one-line forward** (N1 §2.5, N2 §3 — `quota.py` would fall `是 → 部分` on the
literal text), and **D3 on pure forwarding layers** (N1 §2.2, N3 §2, A1 above).
`RELIABILITY.md:207-209` already owes three of these. The count 5/22 is owed too.

### A5. `BLINDING.md`'s categorical sentence is false for the new arm — and it is the same defect V15 was ordered to withdraw

`BLINDING.md:30`:

> 判定员另外拿到的只有 `PARTIAL_CRITERION.md` 的一份副本（新判据组三人），
> 以及 22 条路径。**没有任何判定员拿到 V11 或 V15 的任何一格。**

The second sentence is false. `PARTIAL_CRITERION.md` — handed to N1/N2/N3 and to
nobody else — contains, verbatim:

* **Seven published cells**, with their census and batch: §3.1 `fig02_bill_shape.py`
  (V15 b8), §3.2 `worldgen/mutate.py` (V11), §3.3 `transfer.py` (「V15，b6，**原判
  `是`**」, line 98), §3.4 `run_qc.py --mutants` (V11), §3.5 `archive.py` (「原判
  `部分`」, line 126), §3.6 `ledger.py` (V15 b5), §3.7 `battery/run_battery.py`
  (V11).
* **V11/V15 aggregate statistics**, at `PARTIAL_CRITERION.md:10-12`:
  「十五个判定员用它的比例从 **0%（b4，0/12）到 30%（engine-rig 组，6/20）**…
  V15 的 17 个新增 pinned 假阴里有 **10 个**是它」 — the per-batch base rate of the
  contested cell, the folding semantics, and the cell's contribution to the
  headline false-negative count.

That is a target. It tells the new arm that `部分` is the cell that flips the
folding, that it carries 10 of 17 pinned false negatives, and that batch-level
usage ranges 0–30%. The old arm received none of it. **This is an uncontrolled
asymmetry between the arms, distinct from convergence pressure, and the placebo
does not touch it.**

The aggravating fact is the precedent. `runs/20260729T120000Z-V15-census-sampling-frame/ADVERSARIAL.md:390-396`
required, as owed item 1:

> **Withdraw** `BLINDING.md`'s "no counts, so it had no target to hit."

One round later the same author wrote the same categorical sentence, and this time
the counts are not in a stray tracked file that nobody checked — they are in the
document he deliberately handed one arm and not the other.

**What does not land** is that the six examples were reused as answers: verified,
none of the seven worked-example paths appears among the 22 (§B4). What does land
is adjacency: the sampled rows `certify_a3.py` and `run_l1.py` sit in the same
package as §3.3's `transfer.py` and share `negctl.py` and `test_transfer.py`
with it; `certify_a2.py`/`exhibit.py`/`repair.py` share `tests/test_a2.py` with
§3.6's `ledger.py`; the sampled `papers/…/figures/fig2_coverage_accuracy.py` is
near enough to §3.1's `figures/fig02_bill_shape.py` that N2 had to write a
disambiguation note (`N2.md:27`). **7 of 22 rows (32%) have their evidence chain
walked through in the criterion under a neighbouring filename.**
`PARTIAL_CRITERION.md:76`'s 「这六行都不在重判样本里」 is true and insufficient.

### A6. Two of the four worked examples that change a published cell do not say they change it

Recovered the prior cell for all seven examples from `rows.py`:

| § | path | published cell | criterion says | disclosed in the document? |
|---|---|---|---|---|
| 3.1 | `figures/fig02_bill_shape.py` | V15 部分 | 部分 | n/a (no change) |
| 3.2 | `worldgen/mutate.py::mutation_gate_failures` | V11 部分 | 部分 | n/a |
| 3.3 | `cold-start-a3/a3pipeline/transfer.py` | V15 **是** | 部分 | **yes**, line 98 |
| 3.4 | `worldgen/qc/run_qc.py --mutants` | V11 **部分** | **是** | **no** |
| 3.5 | `theoria-arm/armtools/archive.py` | V11 **部分** | 否 | **yes**, line 126 |
| 3.6 | `cold-start-a2/a2pipeline/ledger.py` | V15 否 | 否 | n/a |
| 3.7 | `battery/run_battery.py` | V11 **部分** | 否 | **no** |

Four examples change a cell. The two that are disclosed are the two that support
the document's rhetoric — 3.3 shows `部分` being *fed* from `是`
(`PARTIAL_CRITERION.md:108-109`: 「这一例是**故意选的**」), 3.5 shows a
disciplined tightening the document wants credit for. The two that are silent are
3.4, presented under the heading 「反例 —— 不是 `部分`」 as an obvious `是` when
V11's own auditor graded it `部分`, and 3.7, presented as an obvious `否(D1)`
when V11 graded it `部分`.

Net effect of the criterion on its own seven examples: `部分` 5 → 3, a 40% drain,
the same direction and roughly the same magnitude as the 14 → 2 drain it produced
on the sample. The examples are not a neutral illustration of the rule; they are
a preview of its effect, and half their movement is undeclared.

### A7. 45% of the FNR movement rests on `D0`, and the panel does not agree `D0` applies

`refold.stdout.txt` and `RELIABILITY.md:186-196`:

```
strict pinned  before  n=145  TP 35  FN 36  FP 1   TN 73   FNR 0.507
strict pinned  after   n=145  TP 34  FN 28  FP 2   TN 81   FNR 0.452
```

Eight pinned false negatives removed, −5.5pp. I recomputed the matrix holding the
five rows that received any `D0` vote at V15's cell instead of the new arm's:

```
strict pinned  after, D0-touched rows not substituted
                       n=145  TP 34  FN 31  FP 2   TN 78   FNR 0.477
```

**3 of the 8 removed false negatives — 2.5 of the 5.5 percentage points, 45% of
the movement — come from rows on which a judge invoked `D0`** (`monitor/gates.py`,
`monitor/reflex.py`, `monitor/scan.py`). `PARTIAL_CRITERION.md:44-46` says of
`D0`, in the document's own words:

> 这一条是**故意保守的**：它把这类行放进 gold-negative，只会**压低**测出来的假阴率。

So the criterion's self-declared thumb on the scale is worth 2.5pp of a 5.5pp
result. Worse: **on 2 of those 3 rows the panel does not agree that `D0` applies.**
`reflex.py` is `D1/D0/D1`, `scan.py` is `D3/D0/D2`; only `gates.py` is unanimous
`D0`. N1 (`N1.md` §2.3) and N3 (`N3.md` §4) both refuse `D0` on `reflex.py` and
say in terms why: its "control" is a real pre-registered mutant caught by an AST
assertion, and `ci_merge.py`'s is a source grep — 「那是这份普查最该记下的东西，
塞进 `D0` 会把它抹掉」.

`RELIABILITY.md:200-201` already says no FNR may be republished on this basis. The
decomposition — 2.5pp of 5.5pp from a conservative-by-design test the judges do not
agree fires — is owed alongside it.

Side effect worth naming: `worldgen/generate.py` becomes a **new false positive**
in the after-matrix (`FP_paths` goes from `['worldgen/build.py']` to
`['worldgen/build.py', 'worldgen/generate.py']`). `worldgen/build.py` is the one FP
whose per-file verdict V15's adversarial pass found leaked in `PARTNER_SYNC.md`.
The FP column is now two rows and both have provenance a reader should be told
about.

### A8. `shapes.py` — one of the four pairs is not one shape, and the docstring's own claim about the pairs is wrong

The brief asked whether the four pairings are real. Re-read all four against the
census cells.

**Pair 1 (`ci_merge.py` 否 / `reflex.py` 部分, "control only reads source") —
stands, with a caveat.** `SUPPLEMENT_TABLE.md:28` and `:32`: both controls never
execute E. But `reflex.py` has a **pre-registered mutant** (`mutants.py:45-50`)
caught by an AST assertion, and `ci_merge.py` has `assert 'verify gate red in' in
source`. A pre-registered mutant is one of the four things V11's question names by
name. Same shape along the axis "never executes E", different along an axis the
question itself enumerates. The pairing is fair; the note should say which axis.

**Pair 2 (`engines.py` 否 / `scan.py` 部分 / `generate.py` 部分, "control hits a
second implementation") — does not stand.** Three different shapes:

* `engines.py` (`SUPPLEMENT_TABLE.md:79`): 「全树 `test_*.py` 无一处 import/调用
  `a2pipeline.engines`」 — **no test touches the file at all**. That is the D1
  shape (the criterion's own §3.7), not the D3 shape.
* `scan.py` (`:33`): a test 「另写了一份 regex 而不是调 `scan.probe_verify_gates`
  —— 打的是规则的第二个副本」 — a re-implementation. D3, copy flavour.
* `generate.py` (`:144`): the control asserts on `worldgen/core/spec.validate` — a
  **dependency**. D3, dependency flavour.

The criterion separates all three. And the readers of the criterion did not put
`generate.py` in the D3 bucket at all: all three wrote **`D2`**
(`agreement.json:376-380`), with N2 spelling out why (`N2.md:29`: 「若拿它充数就是
D3…按 D2」). So the pairing is contradicted by the very judges the criterion
produced.

This matters beyond the script: `PARTIAL_CRITERION.md:126-128` uses b5's
`engines.py` note as the **motivating precedent for D3** — 「b5 的判定员…已经独立
写下同一条规则：「按判据一律不算，故判 `否`」」. b5's `否` rests primarily on
"no test touches this file", which is D1's ground, not D3's. The precedent is
weaker than the document claims.

**Pair 3 (`theory_parser.py` 是 / `strips_encoding.py` 部分) — stands as a shape,
weak as evidence of inconsistency.** `SUPPLEMENT_TABLE.md:59` and `:62` really do
describe the same shape (some rejection paths demonstrated, others not) inside one
batch. But they differ 7-fold in degree — 7 test sites across 2 files versus 1 test
site hitting only the constructor — and b3's cells state the proportion explicitly.
A judge grading on coverage proportion is not being inconsistent; the criterion
resolves the pair by *declaring proportion irrelevant*
(`PARTIAL_CRITERION.md:147-150`), which is a rule change, not the exposure of an
error.

**Pair 4 — stands**, and is correctly labelled consistent.

**`shapes.py:6` is factually wrong**: 「Three of the four pairs below are inside a
single batch, so they are not even inter-judge disagreement」. Pair 1 is b1/b1 and
pair 3 is b3/b3 — **two**. Pair 2 spans b5/b1/b9 and pair 4 spans V15 b6 and V11
`arms`. The docstring's inference ("one judge using the cell two ways within one
sitting") is available for exactly half the list.

### A9. Three counting errors in the instruments' own documentation

* `PARTIAL_CRITERION.md:74` — 「## 3. **六个**实例」. §3 lists **seven** (3.1–3.7).
  `:76` 「这**六**行都不在重判样本里」 — seven rows, and the claim is true of all
  seven (§B4).
* `sample.py:1` — 「The **20** rows re-judged in V17」; `sample.py:11` — 「``partial``
  **12** rows」. The sample is **22** rows with **14** in the partial stratum
  (`sample.stdout.txt`, `sample.json:5`). Both off by two.
* `sample.py:22-24` — 「**Five of the six** examples are V11 rows」. Four of the
  seven are V11 (`mutate.py`, `run_qc.py`, `archive.py`, `battery/run_battery.py`);
  three are V15. The comment at `sample.py:45-48` gets it right and contradicts the
  docstring four lines above it.

None of these changes a number. All three are in the files a reader is told to
audit the design against.

### A10. `blindtree.py` cannot reproduce its own published figure

`blindtree.py:71-73` reads the **live working tree** via `git ls-files`, not a
pinned commit. `blindtree.stdout.txt` publishes 「2287 kept, 290 removed」;
re-running the documented command today at the manifest's own `head_commit`
gives **2287 kept, 318 removed** (`verify-lab/` alone has gone 64 → 92 as this
run's own artefacts landed). The `sha256` recorded for `blindtree.stdout.txt` in
`MANIFEST.json` therefore certifies an output the tool can no longer produce.

V15 learned this exact lesson one commit earlier (`acdfcd7`, "one git archive per
revision, and every artifact regenerated at the pin"). `blindtree.py` should take
a `--rev` and read `git ls-tree -r <rev>`.

Second, smaller: the residue scan (`blindtree.py:107`) only opens
`.md/.json/.txt/.jsonl`. A `.py` or `.sh` naming a sampled path next to verdict
vocabulary would be invisible to it. I re-ran the scan without the extension
filter and with basename-only matching as well — still 0 (§B3) — so nothing is
lost today, but the measurement is narrower than the claim it supports.

---

## B. Charges I tried and could not make stick

Reported because a null result is a result.

### B1. "The author wrote down his own answers and handed out a key" — refuted, and the refutation is the best number in the run

The obvious form of this charge is that the criterion pre-decides the 22 rows, so
`po = 0.939` is the agreement of a lookup. The discriminating test is whether the
author's preregistered dry read also predicts the arm that **did not** get the
document. It does not, by a mile:

| the preregistered dry read agrees with… | all 22 | `部分` stratum (14) |
|---|---|---|
| the **new** arm's majority | **21/22 (95.5%)** | **13/14 (93%)** |
| the **old** arm's majority | **9/22 (41%)** | **3/14 (21%)** |
| V15's published cell | 10/22 (45%) | 3/14 (21%) |

Same model, same tree, same files, same day. Three instances given only V11's
question land 41% of the way to the author's reading; three instances given the
document land 95%. The `+54pp` cannot be shared model priors — the old arm *is*
the shared model prior, and it sits somewhere else entirely.

So the document does something large and reproducible. What it does is **move
where the consensus is**, not tighten it: the same experiment that produces +54pp
of relocation produces +0.078 κ of tightening with a CI of [−0.533, +0.415]. Both
statements are true simultaneously and they are not in tension — the old arm was
already internally consistent (κ 0.689) and consistently *elsewhere*.

This measurement is not in `agree.py`, `RELIABILITY.md`, or `PREREGISTRATION.md`,
and it is the strongest thing this run has. It is also double-edged, which is why
it belongs here rather than in §A: a document that relocates the consensus 54pp
toward its author's private answer, while not measurably improving how much
readers agree with each other, is exactly what "the author wrote down his answer
and everyone who read it copied him" would look like from the outside. The reason
it is nevertheless not that charge is `PREREGISTRATION.md`'s timestamp
(`MANIFEST.json` `preregistration_commit` `4a47472`, one commit before HEAD
`139f70b`) plus the reason-code miss rate: the author's dry read matches the
judges' reason codes only **16/22 (73%)**, *below* the judges' own reason-code
agreement of 0.773, and it is systematically harsher on `D3` (the author wrote
`D3` five times where the panel wrote `D2` three times). A copied key would not
miss its own labels more often than the copiers miss each other's.

**The author's own honesty check passes.** `PREREGISTRATION.md:15-16` promises
that any row where the panel disagrees with the dry read is reported the panel's
way. There is exactly one such row — `engine-rig/recheck/verify_all.py`, dry read
`部分(C)`, panel `否` (`否/否/部分`) — and `RELIABILITY.md:131` reports it as `否`.
No retro-fitting found.

### B2. The 12 intra-judge repeats are genuinely distinct entry points

`RELIABILITY.md:41-45` dismisses all 12 as deliberate granularity, citing one
example. I checked all 12 in `overlap.json`. Every one names two or three
*different* entry points in one file — `arc-recon/client.py` 密钥密封 vs
`load_api_key`; `exam/verify.py` 五阶段总闸 vs `::_determinism`;
`proxy/spend_gate.py` `SpendGate` vs `__main__`; `worldgen/qc/run_qc.py` 三世界闸
vs `--mutants`; and so on. Not one is the same entry point judged twice. The
dismissal stands and so does 「这份金标准在今天之前从来没有过任何信度证据」
(`RELIABILITY.md:47-48`). Charge withdrawn.

One byproduct: `worldgen/qc/run_qc.py --mutants` is graded **`部分`** in V11's own
table, which is what feeds §A6's finding that `PARTIAL_CRITERION.md:113` presents
it as `是` without saying it moved.

### B3. The blinding residue claim is true, and more robustly than measured

`BLINDING.md:37-40` claims 0 of 22 sampled paths appear in a tracked, kept file
carrying this lab's verdict vocabulary. I reproduced the removal list from
`git ls-files` (the prefix list at `blindtree.py:45-56` is auditable exactly as
claimed) and re-ran the residue scan three ways: the author's way (full path,
`.md/.json/.txt/.jsonl`), with **no extension filter at all**, and matching on
**basename only** (which would catch a document saying 「`quota.py` 的负控」
without the directory). All three return **0**. The claim survives a stricter test
than the one that produced it.

The four surviving topic-file mentions (`BLINDING.md:44-49`) are as described:
`PAPER.md` §4.3, one run `MANIFEST.json`, two `RUN_STATE.md`. Keeping them is the
right call for the stated reason.

### B4. The seven worked examples really are all excluded from the 22

`sample.py:43` excludes only `figures/fig02_bill_shape.py` by name and
`sample.py:49-62` hand-lists the control strata. I checked all seven example paths
against `sample.json`: none appears. Four are V11 rows and `sample.py:66` draws
only from `v15_rows()`, so they cannot appear; `transfer.py` (V15 b6, `是`) and
`ledger.py` (V15 b5, `否`) are excluded because neither is in `PRESENT`/`ABSENT`.
The exclusion is operationally complete even though the docstring describing it
is wrong three ways (§A9). Charge withdrawn.

### B5. Zero inter-judge overlap survives falsification

`overlap.py`'s claim is that no path in the 253 was judged by two judges. I
attacked three ways.

* **Judge attribution.** `rows.py` maps V11 rows to their 领地 column and V15 rows
  to their 批次 column, giving 6 + 9 = 15 judges over 253 rows. That is the right
  granularity: V11's territories and V15's batches are the units that were
  dispatched independently. The one honest caveat — that these are 15 *dispatch
  units* of one model, not 15 people — is stated at `MANIFEST.json` `judges.model`
  and `BLINDING.md:67-68`.
* **Multi-path rows.** `overlap.py:39` indexes a multi-path row under **each** of
  its paths, so a row naming two files cannot hide an overlap; it manufactures
  extra chances for one. 233 distinct paths from 253 rows, and still zero.
* **The design argument.** V15's frame is V11's complement by construction, so
  zero is expected. I could not find a path in both.

The claim stands. The stronger sentence built on it —
「这份金标准…从来没有过任何信度证据」 — also stands given §B2.

### B6. The re-fold is not unusable — three of its four cut points hold up

§A2 shows the reason-code ledger is noisier than the verdict. I tried to push that
to "therefore the promised re-fold is worthless" and could not. Agreement at each
cut point, new arm, promoting `否(Dk)` back to `部分`:

| cut point | all 22 po | κ | `部分` majority rows |
|---|---|---|---|
| as published (`C` only) | 0.939 | 0.882 | 3 |
| `+D3` | 0.909 | 0.847 | 5 |
| `+D3+D2` | 0.970 | **0.947** | 13 |
| `+D3+D2+D1` | 0.879 | **0.730** | 17 |

Three of four folds land at κ ≥ 0.847, above the old arm's 0.764. So a reader
*can* re-fold and get a partition at least as reliable as the status quo — the
mechanism works even though the ledger behind it is noisy. Two qualifications
belong in the report rather than being suppressed: the `+D3+D2+D1` fold lands at
**κ 0.730, below the undefined question's 0.764**, so the loosest re-fold is worse
than no criterion; and the `部分` population swings **3 → 17 of 22 (14% → 77%)**
across the cut points, which means "re-fold at any of D1/D2/D3" is not a knob, it
is the whole answer. Charge downgraded from "the defence fails" to "the defence
works mechanically and fails evidentially" (§A2).

### B7. I could not find a judge who read outside the tree

`BLINDING.md:56-60` concedes the read-only constraint is instruction-level, not
enforced, and asks judges to self-report. All six self-report compliance
(`O1.md:44`, `O2.md:35`, `O3.md:41`, `N3.md:6`). I grepped all six reports for
absolute paths, `Desktop`, `verify-lab`, `PARTNER_SYNC`, `monitor/board`,
`monitor/inbox`, `FNR`, `混淆矩阵`, `KNOWN_GAPS`. Every hit is either a
self-report of *not* having read the file, or — in the new arm — a phrase the
judge got from `PARTIAL_CRITERION.md` itself (`N3.md:84` quotes 「红被接到了空处」,
which is `PARTIAL_CRITERION.md:56`). No evidence of an out-of-tree read. This is
absence of evidence and nothing more; the honest statement remains
`BLINDING.md:57-60`'s.

### B8. Every worked-example line citation except §3.3's checks out

I opened all seven. `check_coverage.py:230-293` (§3.1), `test_mutate.py:527-548`
and `mutate.py:1453-1456` (§3.2), `run_qc.py:435` (§3.4), `test_arm.py:137/:145`
(§3.5), `test_a2.py:314-318` (§3.6), `run_battery.py:260` (§3.7) all say what the
criterion says they say. Only §3.3's assertion citation is wrong, and that is §A1.

### B9. The arithmetic is right

Recomputed `po`, Fleiss κ, unanimity and the category distributions for both arms,
both fields, both scopes from the judge tables with an independent implementation.
Every published figure reproduces to three decimals: `old` 0.848/0.764,
0.810/0.689, 1.000/1.000; `new` 0.939/0.882, 0.905/0.770, 0.939/0.872. The Fleiss
implementation at `agree.py:81-97` is the standard fixed-panel form and is
correct. The majority rule at `agree.py:206-207` breaks ties toward `是` over
`部分` over `否`; no row in this sample is a three-way tie, so it never fires.
`read_table` parsed 22/22 rows for all six judges with no silent drops.

---

## C. Judgement

**加限定就够 — the criterion stands, with two withdrawals and eight corrections.**

The reason it stands rather than being withdrawn is §B1 and §B6 together. The
document demonstrably determines the answer: it moves three independent readers
from 41% agreement with the author's private reading to 95%, on rows none of them
had seen worked through. That is not nothing, and it is not a lookup — the author
misses his own reason codes more often than the judges miss each other's. The
re-fold mechanism works at three of four cut points. And the run's central finding
— that none of this rises to a significant reliability improvement — is reported
straight, in the commit message, in `RELIABILITY.md:98-113`, and in
`RELIABILITY.md:203-213`, before any reviewer asked.

The reason it needs qualifying rather than publishing as-is is that its own
defence against the commissioned charge (a) is measurably weaker than the thing it
replaced (§A2: joint κ 0.718 against 0.764), and its answer to charge (b) rests on
a placebo that could not have fired (§A3).

What is owed:

1. **Withdraw** `RELIABILITY.md:115-117`'s 「「一致率的改善来自趋同压力」这条指控…
   **不成立**」. The `old` arm scored `po = κ = 1.000` on the placebo, so the
   author's own decision rule ("if the new arm agrees *more*") had probability
   zero of firing. Replace with: the placebo had no headroom and this design could
   not detect convergence on it. Add the measurement — the placebo moved on 2 of
   22 rows and one of the two (`monitor/gates.py`, reasons `D0/D0/D0`) is the
   criterion's `D0` test writing into the placebo column, so half the placebo's
   entire signal is coupling, not independence.

2. **Withdraw** `BLINDING.md:30`'s 「**没有任何判定员拿到 V11 或 V15 的任何一格。**」
   It is false for the new arm and only the new arm. `PARTIAL_CRITERION.md` §3
   carries seven published cells with census and batch labels, and
   `PARTIAL_CRITERION.md:10-12` carries V11/V15 aggregates including the per-batch
   `部分` rate (0/12 to 6/20) and 「17 个新增 pinned 假阴里有 10 个是它」. Replace
   with the measured statement, and name it as an uncontrolled asymmetry between
   the arms that the placebo does not cover. This is the second round in which
   this sentence has had to be withdrawn.

3. **Fix `PARTIAL_CRITERION.md:103`.** §3.3 cites `replay_certify_green is False`
   — the one assertion in `test_transfer.py:211-218` that fails its own D3, because
   the value originates at `cold-start-a0/certify/replay.py:111` and passes through
   `certify_a3.py:87`, `:109` and `transfer.py:183` untouched. Cite
   `test_transfer.py:213` (`all_caught`, derived from `transfer.py:196`'s own
   `outcome`) or `:216` (`theorize_triggered`, `transfer.py:195`). The verdict
   `部分` survives; the evidence for it does not. Add the missing sentence: **a
   pure forwarding layer owns none of its callee's values, and therefore can never
   satisfy D3.** Three judges invented that rule independently (N1 §2.2, N3 §2) to
   reach the right answer on `certify_a3.py`; it should not have to be invented.

4. **Publish the joint-label reliability, or drop the reason code.** The report
   currently compares reason-code `po` (0.773) with verdict `po` (0.939)
   (`RELIABILITY.md:154-159`). The comparison that decides the commissioned charge
   is against the **old arm**: the criterion's full output scores **κ 0.718**
   (`po` 0.773) where the undefined question scored **κ 0.764** (`po` 0.848), and
   **0.669 against 0.689** on the `部分` stratum. State plainly that the ledger is
   less reproducible than the cell it was built to make auditable, and name
   `monitor/scan.py` — unanimous verdict, reason codes `D3/D0/D2`, no majority at
   all, re-fold undefined.

5. **Report the `判据不决` count.** Five of 22 rows (23%; 36% of the `部分`
   stratum) were flagged by a criterion-reading judge as rows the criterion does
   not decide — `N1.md:37` (4) and `N3.md:35` (1) — and four of them are the four
   rows that carry a `部分` verdict or split the panel. `agree.py:58-60` discards
   the flag and no artefact mentions it. Either parse it into `agreement.json` as
   a fourth column or state the count in `RELIABILITY.md` §6. Until then `po =
   0.939` is a forced-choice statistic and should be labelled one.

6. **Decompose the FNR movement.** `refold.stdout.txt`'s −5.5pp is not one thing.
   Holding the five `D0`-touched rows at V15's cell gives `FN 31 / FNR 0.477`
   instead of `FN 28 / 0.452`: **2.5 of the 5.5pp (45%) comes from `D0`**, the test
   `PARTIAL_CRITERION.md:44-46` itself calls 「故意保守的…只会**压低**测出来的
   假阴率」 — and on two of those three rows (`reflex.py` `D1/D0/D1`, `scan.py`
   `D3/D0/D2`) the panel does not agree `D0` fires. Also name the new false
   positive: `worldgen/generate.py` joins `worldgen/build.py` in the FP column.
   `RELIABILITY.md:200-201`'s ban on republishing an FNR stands and should be
   restated next to this decomposition.

7. **Disclose the two silent example movements, and fix the count.**
   `PARTIAL_CRITERION.md:113` grades `worldgen/qc/run_qc.py --mutants` `是` where
   V11 graded it `部分`; `:136` grades `battery/run_battery.py` `否` where V11
   graded it `部分`. §3.3 and §3.5 disclose their movements; these two do not, and
   they move in the direction the document is least eager to advertise. Also: §3
   is headed 「六个实例」 and contains **seven**.

8. **Repair `shapes.py`.** `shapes.py:6`'s 「Three of the four pairs below are
   inside a single batch」 is **two** (b1/b1 and b3/b3); pair 2 spans b5/b1/b9.
   Pair 2 is not one shape: `engines.py`'s cell (`SUPPLEMENT_TABLE.md:79`) says no
   test imports or calls the file at all, which is D1's ground, not D3's — and all
   three criterion-readers graded the sampled member of that pair
   (`worldgen/generate.py`) **`D2`**, not `D3`. Since
   `PARTIAL_CRITERION.md:126-128` uses b5's `engines.py` note as the motivating
   precedent for D3, that precedent needs re-citing or dropping.

9. **Pin `blindtree.py`.** It reads the live working tree (`blindtree.py:71-73`),
   so its published `290 removed` is now `318` at the manifest's own
   `head_commit`, and the `sha256` in `MANIFEST.json` certifies an output the tool
   cannot regenerate. Take a `--rev` and read `git ls-tree -r`. Widen the residue
   scan past `.md/.json/.txt/.jsonl` while you are there — the claim it supports
   survives the wider scan (§B3), so the narrowing buys nothing and costs
   credibility.

10. **Fix the three counting errors in `sample.py`** (`:1` "20 rows" → 22; `:11`
    "12 rows" → 14; `:22-24` "five of the six examples are V11" → four of the
    seven, and it contradicts the correct comment at `:45-48`).

One thing not owed but worth writing down, because it is the sentence this run
earned and nobody has said: **the criterion did not resolve the disagreement, did
not hide it, and did not shrink it — it moved it.** The consensus location shifted
54 points toward the author's reading (§B1); the consensus tightness did not
significantly change (Δκ +0.078, CI [−0.533, +0.415]); and the direction of the
shift lowers the measured false-negative rate of the tool under test by 5.5pp,
45% of it via a test the document itself labels deliberately conservative (§A7).
Any future round that reports the first of those three numbers without the other
two is reporting a result that is not there.
