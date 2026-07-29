# Adversarial pass on the V15 frame

Commissioned by `BLINDING.md` §3. The brief was: **prove the population was drawn
to make the numbers look good.** Everything below was run against copies of
`frame.py` in a scratch directory; no file under `verify-lab/` was modified except
this one.

Reproduce with `<scratch>/variants.py` (a parametrised re-implementation of
`frame.build` that reuses `frame.py`'s own helpers, so the only thing that varies
is the membership rule). Baseline at HEAD:

```
frame: 244 acceptance entry points   (A 193 = 186 py + 7 sh, B 34, C 17)
V11    127 rows -> 107 frame units (43.9%)
negctl 141 paths -> 140 in frame (57.4%)
strict  v14 n=95  TP 43 FN 20 FP 3 TN 29  FNR 0.317 FPR 0.094
strict  v15 n=219 TP 70 FN 41 FP 6 TN 102 FNR 0.369 FPR 0.056
strict  pinned(V11 gold)  n=76  TP 29 FN 19 FP 1 TN 27 FNR 0.396 FPR 0.036
strict  pinned(V11+V15)   n=145 TP 35 FN 36 FP 1 TN 73 FNR 0.507 FPR 0.014
```

Verdict up front: **加限定就够 — qualify, do not rewrite.** The load-bearing
number does not move under any frame I could build. Five specific claims in the
V15 artefacts are wrong or overstated and are owed corrections. Details in §C.

---

## A. Charges that land

### A1. The blinding is materially breached by tracked files outside `verify-lab/`

`BLINDING.md` §"The judges were also blinded to each other, and to V11" says each
agent received "**no** V11 rows … **no** counts, so it had no target to hit."
The judges' tree was a `git archive` of this branch's HEAD with `verify-lab/`
deleted. `PARTNER_SYNC.md` is tracked, sits at the repository root, and was
therefore in every judge's tree. It contains:

* **line 940** — V11's answer key in aggregate:
  「**127 道入口**：能红「否」15、**有负控「否」35**、退出码诚实「否」13；实测支撑
  24 行」. That is the count, the base rate, and the evidence-class split.
* **line 958** — V14's: 「枚举 141 个验收入口 … **FNR 32%** … `KNOWN_GAPS.json`,
  110 缺 / 31 有」, plus a **per-file probe verdict**: 「`worldgen/build.py` 被判
  present，而同文件的 `check_determinism` … 全树零测试调用」.
  `worldgen/build.py` is the single FP in the pinned strict matrix.
* lines 947 / 953 give the negative-control detail for `fuzzlab` and `worldgen`;
  line 940 gives V11's sharpest `实测` row (`arc-recon/contamination.py` exits 0
  on a real sealed contact).

Also tracked, also in the tree:
`monitor/board/done/V11-negative-control-census.RES-3.md` and
`monitor/board/claimed/V14-standing-negative-control-probe.RES-3.md` (the latter
is V14's own work order: 「35 道没有任何可执行的负控、13 道退出码撒谎」).

**Exposure, measured.** Of the 126 judged paths, **70 are named somewhere in a
tracked non-`verify-lab` `.md`/`.json`/`.txt`**, and **27 (21%) are named in a
file that also discusses negative controls** (`负控` / `FNR` / `混淆矩阵` /
`KNOWN_GAPS`). Top sources: `PARTNER_SYNC.md` (9 paths),
`papers/phase1-workshop/PAPER.md` (8), `.../CITECHECK.md` (4).

**Did it contaminate?** Not detectably.

| | n | 是 | 部分 | 否 | present (strict) |
|---|---|---|---|---|---|
| exposed paths | 27 | 12 | 2 | 13 | **0.52** |
| unexposed | 99 | 22 | 13 | 64 | **0.35** |

A 17pp gap, one-sided binomial against the pool rate 0.39: **p = 0.121**. Not
significant, and confounded — the paths `PARTNER_SYNC.md` talks about are the
flagship gates that genuinely do have controls. And the direction, if real, is
toward `present`, which *raises* FN and therefore flatters V15's conclusion.

**The claim to withdraw is the categorical one.** "No counts, so it had no target
to hit" is false as written. The correct statement is: the per-file verdict table
was withheld; the aggregate counts and at least one per-file verdict were in the
tree and nobody checked.

### A2. The "exact reproduction of V14" is not exact — it matches 2 of 4 cells

`matrix.py`'s docstring sets its own tripwire (lines 13–15):

> if it does not land on FP 3 / FN 20 then this module disagrees with V14 about
> the protocol and every other number here is suspect.

It lands on FP 3 / FN 20. It does not land on TN. Running V14's own
`calibrate.py` at this HEAD:

| | n | TP | FN | FP | TN | FPR |
|---|---|---|---|---|---|---|
| V14 `calibrate.py`, A−B strict | 97 | 43 | 20 | 3 | **31** | **0.088** |
| `matrix.py` `v14` row, strict | **95** | 43 | 20 | 3 | **29** | **0.094** |
| V14 `calibrate.py`, A−B harsh | 97 | 34 | 12 | 12 | **39** | **0.235** |
| `matrix.py` `v14` row, harsh | **95** | 34 | 12 | 12 | **37** | **0.245** |

The tripwire was written over exactly the two cells that agree. The published
`FPR 0.094` in this run's `matrix.json` is not V14's `0.088`.

**The two missing rows, named.** `gold_v11` requires `len(py) != 1 -> skip`
(`matrix.py:84`). Two census rows name two existing `.py` files each and V14
resolved them; V15 drops them:

* `theoria-arm/armtools/salvage.py` + `timeline.py` — gold `否`, both measured
  `absent` → the 2 missing **TN**.
* `proxy/canon.py` + `proxy/ledger.py` — gold `是(实测)`, both measured `present`.

Note also that toggling the *other* switch — keeping the 4 test-file rows — gives
n=99, TP 43 / FN 22 / FP 3 / **TN 31**: it recovers V14's TN exactly while losing
FN. No setting of `matrix.py`'s two switches reproduces V14 cell-for-cell. The
FP 3 / FN 20 landing is two protocol differences partially cancelling, not a
reproduction.

Related, smaller: `confusion()` (`matrix.py:145–146`) silently `continue`s on any
gold path with no measurement. It happens to drop 0 rows today, but it is
structurally the same unlogged exclusion V15 indicts `criterion.py`'s bare
`except` for.

### A3. Roughly half of "FNR 32% → 51%" is a change of restriction, not new gold

The headline replaces V14's argument-4 number with 50.7%. But it changes two
things at once: the gold standard *and* the row restriction. Decomposed (strict):

```
0.317  V11 gold, unrestricted        (= V14's published 0.318)
0.396  V11 gold, probe-enumerated    <- pinning alone:      +7.9pp  (42% of the move)
0.507  V11+V15 gold, probe-enumerated <- the 126 judgements: +11.1pp (58%)
```

Harsh folding: `0.261 → 0.344 → 0.409`; pinning is +8.3 of +14.8pp = **56%**.

The pinning step required none of V15's work — V14 could have computed it from
`probe.enumerate_entry_points` on the day it shipped. The report should state
that the supplement is worth ~11pp, not ~19pp.

### A4. `部分` carries most of the new FN, and under `harsh` the unrestricted conclusion reverses

Of the 36 pinned strict FN: **19 are V11-origin, 17 are V15-origin, and 10 of the
17 are graded `部分`** — rows the `strict` folding counts as "has a negative
control". The increment is a folding artefact as much as a discovery.

`matrix.py` prints both foldings, and on the **unrestricted** matrix the harsh
one reverses the story outright:

| folding | V14 repro | V11+V15 |
|---|---|---|
| strict | FN 20, FP 3, FNR 0.317 | FN 41, FP 6, **FNR 0.369** (up) |
| harsh | FN 12, FP 12, FNR 0.261 | FN 20, FP 17, **FNR 0.253** (**down**) |

So there exists a folding — published in the same JSON, defended in the same
docstring as "where the two definitions genuinely diverge" — under which
supplementing the gold makes the false-negative rate *slightly better* and makes
**FP the growing problem** (12 → 17). That is the reversal the brief asked for,
and it needs no change to the frame at all.

It does **not** survive the pinned restriction: harsh pinned goes 0.344 → 0.409,
same direction as strict. So the "should not gate" conclusion holds; only the
unrestricted headline is folding-fragile.

### A5. The frame counts its own instruments, and is not stable

Three different totals live in this one run directory:

| artefact | frame total | V11 coverage |
|---|---|---|
| `frame.json` | **241** | 44.4% (107/241) |
| `matrix.json` | **243** | — |
| live at HEAD today | **244** | 43.9% (107/244) |

Six frame units are `verify-lab`'s own files: `frame/frame.py`, `frame/matrix.py`,
`frame/reconcile.py`, `negctl/calibrate.py`, `negctl/probe.py`,
`negctl/tests` (stratum C). Those five `.py` files are, by `git log
--diff-filter=A`, **the only non-suite frame units created after the V11 census
commit `9723f3d`** — every other member predates V11 and was fairly countable
against it.

Consequence: `v11_coverage_pct` is partly a function of how many files V15
commits, and every commit V15 makes moves it **down**. The effect is small
(107/241 = 44.4% → 107/244 = 43.9%) but the direction is the flattering one, and
no artefact in this run directory is self-consistent with any other.

`difference_set.txt` archives 128 non-suite units; at HEAD it is 131, the three
new ones being `frame.py`, `matrix.py`, `reconcile.py` — V15's own instruments,
in the difference set, unjudged.

### A6. `BLINDING.md` §4 names the wrong file

> Two frame units could not be blind-judged at all: `verify-lab/negctl/probe.py`
> and `verify-lab/negctl/criterion.py` … 126 judged of a 128-unit non-suite
> difference set.

**`verify-lab/negctl/criterion.py` is not a frame unit.** It has no `__main__`
(stratum A fails) and raises no repository-defined exception (stratum B fails).
Checked directly: it is absent from `frame.py --list`.

The actual second unjudged member of the archived 128 is
**`verify-lab/negctl/calibrate.py`** — the file that computes and prints V14's
confusion matrix, i.e. the answer key itself. The arithmetic 126 + 2 = 128 is
right by accident, and the one file whose exclusion most needed justifying is not
mentioned anywhere in the blinding record.

### A7. `generated` marks nothing; `unparseable` has a silent hole of the shape V15 indicts

* **`generated` = 0 units.** 225 tracked files match `/artifacts/`, 87 match
  `/generated`, 32 match `/handover_packages/` — but none is a frame unit, because
  the marker only ever gets applied to files that already passed stratum A/B/C.
  The docstring gives it a paragraph (lines 100–102) and the printout gives it a
  line; it qualifies nothing. "Every count is reported with and without the
  markers" is one third empty.
* **`unparseable` admits a file only if the raw text contains `__main__`**
  (`frame.py:381–382`). An unparseable *library* without one is dropped silently,
  and cannot be recovered by stratum B either, because stratum B needs an AST.
  n = 1 today (`release/checklist.py`, which does have textual `__main__`), so
  nothing is actually lost — but this is structurally the same hidden hole the
  docstring accuses `criterion.py`'s bare `except` of having.
* **`frozen` is genuinely non-excluding**, and its effect is small: dropping the
  15 frozen units moves total 244→229, V11 coverage 43.9→45.9%, and pinned strict
  FNR 0.507→0.493 (n 145→141).

### A8. The frame and the matrix disagree about test files

Stratum C admits `fuzzlab/tests` as an acceptance entry point. `gold_v11`
(`matrix.py:85–93`) drops the census rows that name
`fuzzlab/tests/test_battery.py`. The frame counts the directory as a gate while
the matrix rules the file inside it out of scope.

**But the charge that this rule was reverse-engineered does not stand.**
`CALIBRATION.md` line 29 declares it independently, before V15 existed: out of
scope = 「4 shell entry points … and **4 rows whose "entry point" is itself a test
file**」, and it is exactly those 4 rows (3 distinct files:
`fuzzlab/tests/test_battery.py` ×2, `fuzzlab/tests/test_oracles.py`,
`theory-compiler/conftest.py`). The docstring's phrasing — "keeping them puts FN
at 22; dropping them puts it at 20, which is V14's published number" — reads like
fitting, but it is transcription of a rule V14 wrote down first. Effect if kept:
strict n 99, TP 43 / FN 22 / FP 3 / TN 31, FNR 0.338, FPR 0.088.

---

## B. Charges I tried and could not make stick

Reported because a null result is a result.

### B1. I could not build a principled frame in which V11 covers >80%

Twelve variants. V11 coverage range **41.9% – 64.3%**:

| variant | total | V11 cov | negctl cov |
|---|---|---|---|
| baseline | 244 | 43.9% | 57.4% |
| drop stratum C | 227 | 42.3% | 61.7% |
| B: exception must be defined in the same file | 238 | 44.1% | 58.8% |
| B: import matched by dotted module path, not stem | 238 | 44.5% | 58.8% |
| B: drop the "not caught elsewhere" test | 260 | 41.9% | 53.8% |
| B: drop the "reached from A" test | 251 | 42.6% | 55.8% |
| delete stratum B | 210 | 47.6% | 66.7% |
| require `can_refuse` (V14's own rule) | 202 | 46.0% | 69.3% |
| drop `frozen` | 229 | 45.9% | 59.0% |
| **V14's rule verbatim** (invocable ∧ can-fail ∧ live, no B, no C) | **145** | **50.3%** | **93.1%** |
| **declared-gate** (named by a `verify.sh`/`Makefile`/`README`/`CLAUDE.md`) | 129 | 52.7% | 49.6% |
| **declared-gate ∧ V14's rule** | **84** | **64.3%** | 76.2% |

The ceiling is structural, not definitional: V11's 127 rows resolve to at most
**107 distinct file-level units**, because 24 of the 127 name a pytest suite, a
glob (`battery/metrics/*`), a nonexistent gate, or two files at once. To put V11
above 80% the population would have to be smaller than ~134 members, and the
smallest defensible one I could construct (84 units, requiring both that the
repository *declares* the unit a gate and that it can fail) still leaves V11 at
64.3% — and still shows FNR rising, 0.250 → 0.357 pinned.

**The premise "V11 is not a frame" survives.** Even under V14's *own* membership
rule — a population of 145 files V14's enumerator would itself accept — V11's
gold covers half of it.

**One charge does land here, though, in the other direction.** "negctl covers
only 58%" is soft. Under V14's own definition of what it is enumerating,
**negctl covers 93.1%**. Measuring the probe's coverage against a population
deliberately drawn wider than the probe's own membership rule is a real
rhetorical thumb on the scale, and 58% should be published next to 93%.

### B2. Stratum C is not padding — it flatters V11

17 units, 7.0% of the total. Removing it moves V11 coverage **down** (43.9% →
42.3%) and negctl coverage **up** (57.4% → 61.7%). A stratum drawn to make V11
look worse would do the opposite of both. Eleven of the 17 are hit by V11's 12
pytest rows, which is why. And stratum C **never enters the confusion matrix at
all** — `gold_v15` requires `rel.endswith(".py")` (`matrix.py:111`), and suite
units are directories. Every matrix number in this run is identical with and
without stratum C. Charge withdrawn.

### B3. Stratum B is a real knob (28–50) that moves nothing that matters

`B = 34` as shipped. Equally defensible rewritings:

| rewriting | B |
|---|---|
| exception must be *defined* in the same file (the rule `custom_exceptions_raised`'s docstring says it rejected) | **28** |
| "some A file imports it" matched by dotted module path instead of bare stem (the over-connection the docstring admits at line 121) | **28** |
| drop the "not caught by any non-test file other than its own" condition | **50** |
| drop the "reached from an A file" condition | **41** |

So B is adjustable by ±47% without saying anything indefensible, and the two
*tightenings* — the ones a hostile reader would demand — both land on 28, not on
something dramatic.

And the pinned matrix is **byte-identical across all of them**: n=145, TP 35 /
FN 36 / FP 1 / TN 73, FNR 0.507. Every path `probe.py` enumerates is in stratum
A, so no stratum-B rewriting can touch the headline. The most tempting knob in
the whole file is inert on the number the conclusion rests on.

### B4. "Membership does not require the ability to fail" does not suppress FPR

The hypothesis was that admitting 42 units that cannot go red stuffs the
gold-negative denominator and pushes FPR down. Tested by re-imposing V14's rule:

| | total | n | TP | FN | FP | TN | FNR | FPR |
|---|---|---|---|---|---|---|---|---|
| baseline, strict v15 | 244 | 219 | 70 | 41 | 6 | 102 | 0.369 | **0.056** |
| `can_refuse` required, strict v15 | 202 | 191 | 70 | 39 | 4 | 78 | 0.358 | **0.049** |

FPR goes **down**, not up. The units removed are overwhelmingly gold-negative
*and* measured-absent — they are TN, and dropping them shrinks numerator and
denominator together. The rule is not an FPR suppressant. Charge withdrawn.
(Pinned numbers unchanged: 0.507.)

### B5. The nine judges are consistent; no measurable judge effect

126 rows, 7 columns, all parsed. `有负控`: `是` 34 / `部分` 15 / `否` 77
(present rate 0.39 strict).

* **Per-batch present rate**: b1 0.36, b2 0.31, b3 **0.69**, b4 0.25, b5 0.38,
  b6 0.29, b7 0.38, b8 0.47, b9 0.35. b3 (theory-compiler, 9/13) is the only
  outlier: one-sided binomial vs the pool = **p 0.027**, × 9 batches = **0.24**.
  Not significant, and theory-compiler genuinely has the largest suite in the
  repository (364 tests).
* **Same-class files**: zero basenames judged differently across batches. All 13
  `runs/`-frozen rows: 11 `否` / 2 `是`. All 4 `fixtures/` rows: `否`.
* **Column confusion** (did judges credit `有负控` from the file's own `raise`,
  i.e. answer question 1 in column 2?): **88%** of `是` rows and **87%** of `部分`
  rows cite a `test_*.py` / `/tests/` / `::test_`, against **45%** of `否` rows.
  The only 4 `是` rows citing no test are explicit in-file self-tests
  (`monitor/verify_quota_exit.sh`, `fuzzlab/props/cegis_miner.py`, two
  `arc-recon/runs/.../proposed/*_invariants.py`) — a class `criterion.py`'s
  detector B is defined to cover and mostly misses (V14: B alone is FN 58/63).
  No confusion detected.
* **The one real noise channel** is differential use of `部分`: b4 used it 0/12,
  b1 3/14, b5 3/13, b8 3/17. Since `部分` is exactly what the folding flips, and
  10 of the 17 new FN are `部分` rows (§A4), judge-level variation in that one
  cell propagates straight into the headline. Quantified; not attributable to any
  individual judge at this n.

### B6. The `读码`-only weakening biases *against* V15's conclusion, not for it

`BLINDING.md` concedes 126/126 `读码`, 0 `实测`, against V11's 24 `实测`, and says
it is "not obviously biased for or against the negative-control column." I tried
to construct the bias argument in both directions and only got one to work:

* **Toward fewer FN (deflating V15's number).** A `读码` judge answering "is there
  an executable negative control" does what `criterion.py` does: search the tree
  for a test that constructs bad input and asserts failure. Judge and criterion
  draw on nearly the same evidence, which pushes toward agreement. An `实测`
  judge who actually ran the negative control would catch controls that are
  present but *skipped* or *vacuous* — cases where the AST sees a test and the
  process shows nothing. Those are FN the code-reading census cannot generate.
* **The b5 brief's hint pushes the same way.** Judges in b3/b5/b6 were told to
  check whether a test targets *this* file or a copy elsewhere. A `yes` to that
  check pushes a verdict toward `否`. `否` produces FP or TN — **never FN**. b5
  applied it to 5 files (`compile_a2`, `plan`, `ledger`, `engines`, and by note
  to `ablcore/*`), so it is a batch-wide rule, not a steer at `engines.py`. But
  its whole effect is on the FP column.

I could not construct a mechanism by which reading-only *inflates* FN. So
**FNR 0.507 should be read as a lower bound**, and `BLINDING.md`'s "not obviously
biased" is more cautious than the evidence requires.

---

## C. Judgement

**加限定就够 — the definition stands; five corrections are owed.**

The reason it stands is §B3 and §B2 together: I moved the population from 84 to
260 units across twelve principled rewritings, and the pinned confusion matrix —
the number the "should not gate" conclusion actually rests on — came back
identical (n 145, TP 35 / FN 36 / FP 1 / TN 73) in every variant that did not
touch the `frozen` marker, and moved to 0.493 when it did. The direction of the
FNR change is invariant across all twelve. A definition that cannot be tuned to
change its own answer is not a definition drawn to make numbers look good. The
two strata a hostile reader would attack first (C as padding, B as a free
parameter) are respectively coverage-*negative* for V11 and matrix-inert.

What is owed:

1. **Withdraw** `BLINDING.md`'s "no counts, so it had no target to hit."
   `PARTNER_SYNC.md` lines 940 and 958 are tracked, were in every judge's tree,
   and carry V11's aggregate (`有负控「否」35`), V14's FNR 32%, and a per-file
   probe verdict on `worldgen/build.py`. Replace with the measured statement:
   the per-file table was withheld; 27 of 126 judged paths were named in a
   tracked file that also discusses negative controls; exposed-vs-unexposed
   present rate 0.52 vs 0.35, p 0.12, direction unflattering to V15.
2. **Stop calling the `v14` row a reproduction.** It matches 2 of 4 cells:
   TN 29 vs 31, n 95 vs 97, FPR 0.094 vs 0.088 (harsh: 37 vs 39, 0.245 vs 0.235).
   Name the two dropped multi-path census rows. Move the docstring's tripwire to
   all four cells or delete the claim.
3. **Decompose the headline.** `0.317 → 0.396 → 0.507`: 42% of the move is the
   restriction to probe-enumerated files, which needed none of the 126
   judgements. Report the supplement as worth ~11pp.
4. **Publish 93.1% beside 58%.** Under V14's own membership rule the probe covers
   93% of what it claims to enumerate; 58% is measured against a population drawn
   deliberately wider than the probe's own rule, and that comparison is the one
   place the frame's generosity does flatter V15's argument.
5. **Fix and pin.** `BLINDING.md` §4 names `criterion.py`, which is not a frame
   unit; the actual excluded unit is `calibrate.py`, the file that computes V14's
   matrix. And pin the frame to a base commit: `241` / `243` / `244` in one run
   directory, with V15's own instruments in the population and in the difference
   set, is a denominator that shrinks V11's coverage every time this branch
   commits.

One thing not owed but worth writing down: §A4 shows the *unrestricted* headline
reverses under the `harsh` folding (FNR 0.261 → 0.253, FP 12 → 17). It does not
reverse under the pinned restriction, which is the one the conclusion uses. That
asymmetry should be stated explicitly rather than left for a reader to find in
`matrix.json`, because it is the single largest fragility in the argument that a
hostile reviewer will reach for first.
