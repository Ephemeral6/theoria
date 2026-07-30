# Row-level sample audit of citecheck slice C (§7–§8) — the slice nobody had read

**What this is.** An independent sample re-verification of individual rows in
`citecheck-C-s7-to-s8.md`. It is the missing half of
`row-sample-audit.md`, which drew 31 rows from A/B/D1/D2 and explicitly
recorded that C was not sampled because it was still being rewritten.
`CITECHECK-2026-07-30.md` names that gap in its own text: §7–§8 is
"the one fifth of this stamp resting on a single author." This file tests
whether slice C's rows are *true*, not whether they are *present*.

Auditor: independent row-level sampler (second reader for slice C), P18,
2026-07-30. Worktree `.worktrees/p18-audits-cover-half-the-paper`, branch
`agent/p18-audits-cover-half-the-paper`. No git write command was run; no slice
file, no `PAPER.md`, no `MANIFEST.json`, no `verify_paper.py` and no
`row-sample-audit.md` was edited. This file is the only artefact written.

---

## Sampling method — declared before the results

Copied from `row-sample-audit.md` rather than invented, so the result is
comparable to its 31/31.

The frame is every enumerated row in slice C: the 3 Pass A table rows and the
Pass A notes, the 10 Pass B findings, the 49 bullets of *Numbers checked and
confirmed correct*, the 11 Pass C rows, the 6 Pass D findings, the 23 bullets of
*Quotes verified exact*, the 6 rows of the self-corrections table, and the 10
rows of *Where the stub's asserted counts were wrong*.

The draw is **deliberately weighted, not random**, on the same stated priority
order:

1. rows the slice itself calls load-bearing or high — and, above all, the claim
   the abstract calls **the strongest result**, which lives in this slice;
2. rows asserting a specific integer, ratio or exact quoted string;
3. rows in *Numbers checked and confirmed correct* and *Quotes verified exact* —
   sampled deliberately, because a false confirmation is more dangerous than a
   false finding: nothing downstream re-checks it;
4. rows where slice C touches an artefact another slice also touches, so a
   cross-slice contradiction would show.

Two additions the brief asked for, both outside the row frame and reported
separately: the **gate-E rulings** over `07_battery.md` / `08_exam.md` are tested
against their own stated evidence, and slice C's **header counts** are
re-derived from the rows beneath them.

Quota: ≥12 rows. Actual draw: **42 rows** (4 abstract-chain, 10 Pass B, 6 Pass D,
17 confirmed-correct, 4 Pass C, 1 whole-slice Pass A sweep), plus 5 rulings and
the header-count re-derivation. Nothing drawn was dropped.

### The exact rows drawn, listed before any of them was checked

**Priority 1 — the abstract's strongest result (4).** The abstract at PAPER L61
opens "**The strongest result is a negative one about our own metrics**" and
the claim runs L61–81. Its four checkable links all sit in slice C's §7.7/§7.7a:

- **R1** — §7.7 confirmed row: the executable register (`n_demonstrated` 38,
  `n_disagreements` 17, `main` 9, `reference` 29, 34 landed / 4 not,
  `register_tier` main 19, `tier` main 9, `demoted_by_demonstration` 10)
- **R2** — §7.7a confirmed row: the blind round read **both** as first written
  (`git show 0b6e4939:…`) and as delivered — 105/91/`main == ["E1","M3"]`/no
  `undetermined` key, against 112/95/`main []`/`undetermined ["M3"]`/37
- **R3** — §7.7a limit 4: the poverty certificate passed 105 of 105 and 112 of 112
- **R4** — §7.7a: `battery/METRICS.md`'s empty published main table

**Priority 2 — every Pass B row (10):** B1 (§8.3 `label_sets_checked`, **high**),
B2 (§8.4 "no cheater response … is archived", **high**), B3 (§8.4 the struck-out
weakness 11, **high**), B4 (§7.6 ρ = −0.83's provenance, **medium-high**),
B5 (§7.1 "two of the five arms"), B6 (§7.7a limit 2's inverted "stricter"),
B7 (§8.2 the band replaced-vs-widened), B8 (§7.10a `ledger.jsonl` 560 rows),
B9 (§7.2a −0.562 / −0.188), B10 (§8.2 "never been answered by anything but the
four fakes").

**Priority 3 — every Pass D row (6):** D1 (**load-bearing**: a sentence
attributed to "the directory" that exists nowhere), D2, D3, D4, D5, D6.

**Priority 4 — confirmed-correct rows (17):** CC1 §7.1 slot counts
1433/2066/111/3610; CC2 §7.1 provenance in 1 of 7 artefacts; CC3 §7.2's whole
effect-size table (8 δ, 16 medians, direction column, verdict tally); CC4 §7.2's
Schema-side-runs column, `model_calls` 197–564 vs 0, median steps 450/27;
CC5 §7.2a `stats.py` unpaired δ + P3's sign test; CC6 §7.5's 0.125/0.25 power
floor; CC7 §7.9's 32-cluster de-redundancy and five retirements; CC8 §7.9's
257-of-703 pair coverage against v1's archived artefact; CC9 §7.10's single
goal-reaching run; CC10 §7.10a's **three pile digests** and 111 CRLF pairs;
CC11 §7.7's epistemic-family test (`assert len(landed) == 18`) — *also read by
slice A*; CC12 §8.1's four papers 80/80, 29/46, 60/144, 17/34; CC13 §8.3's 1,790
probes / 0 / 0 — *also read by `row-sample-audit.md`*; CC14 §8.2's calibration
block; CC15 §7.10a's empty capability column across four instruments;
CC16 §7.10a's 78-vs-40-vs-30 budget arithmetic; CC17 §7.7a limit 1's two commits
and "four of the nine would have stayed".

**Priority 5 — Pass C (4):** C1 (the largest uncited block), C3 (the "34" that is
in no field), C4 (105/91/37 cited to two files that carry none of them),
C9+C10 (`exam/STATUS.md` quoted three times, cited zero times).

**Priority 6 — Pass A (1 sweep):** every path-like backtick token in PAPER.md
L1669–2520, re-extracted and `Path.exists`-tested independently, because the
index's one genuine whole-paper result is "0 broken paths."

---

## Preliminary: the objects audited are the pinned ones

Recomputed in this worktree, not copied:

| object | expected | measured |
|---|---|---|
| `PAPER.md` sha256 | `6b633fcc…25376` | `6b633fcc35ae612f20f4028eb45aaca1b6ed86a24eb1304af555c46228325376` ✓ |
| `PAPER.md` bytes / newlines | 237872 / 3729 | 237872 / 3729 ✓ |
| `citecheck-C-s7-to-s8.md` sha256 | `f75e5289…` (MANIFEST) | `f75e5289982122f063af9cb882bfd18ff77ffcc7f41635f1435c581767fd002e` ✓ |
| `citecheck-C-s7-to-s8.md` bytes / newlines | 69933 / 784 | 69933 / 784 ✓ |

`verify_paper.py` in this worktree reports **PASS 7/7**, and gate A confirms
`PAPER.md == assemble(sections/)` byte-identically over 13 sections — so slice
C's line mapping (`PAPER − 1668` for §7, `PAPER − 2324` for §8) rests on a
verified generator, not an assertion.

---

## Results

**Tally over the 42 sampled rows: 42 HOLD, 0 WRONG, 0 UNVERIFIABLE.**

Nine of the 42 hold with a stated imprecision inside them (a line anchor off by
a few lines, a slightly overreaching characterisation, or emphasis added inside a
quotation). Each is named in place. None changes a verdict, none is a wrong
value, and none is load-bearing. Separately: **one of the five gate-E rulings
over this span has a false stated justification** — that is not a slice C row
and is reported in its own section.

### Priority 1 — the abstract's strongest result: HOLDS, every link

This is the highest-priority row and the answer is unambiguous. Read from
`battery/artifacts/gaming_audit.json` and from
`battery/runs/20260729T021247Z-V9-battery-gaming-audit/v9_gaming_audit.json`
both as it sits and at commit `0b6e4939`.

**R1 (§7.7, the executable register) — HOLDS, every figure.**
`gaming_audit.json`: `n_demonstrated` **38**, `n_disagreements` **17**, `main`
= `["E2","E3","K11","K12","K7","M3","M6","P3","P4"]` (**9**), `reference` **29**.
Counting `metrics[*].demonstrated.succeeded` gives **34 true / 4 false**, the
four being **E2, K12, M3, P4** — so the abstract's "34 of the 38 metrics can be
driven to a good score" is the artefact's own count. Counting
`metrics[*].register_tier == "main"` gives **19**, `tier == "main"` gives **9**,
`demoted_by_demonstration` has **10** entries. And the abstract's "**14 of them**
claims that a metric had been defended", which slice C does not itself check:
`disagreements` is a 17-element list and exactly **14** of them carry `defended`
in `fields_contradicted`. Every endpoint in slice C's row reproduces, and the
arithmetic the paper prints (19 − 13 = 6, 13 − 3 = 10, 6 + 3 = 9) closes.
`battery/REPORT_V2.md` **L83** does name the intermediate six by hand
("Main table at this point in the round: E3, K11, K7, M3, M6, P3.") — the exact
line slice C cites.

**R2 (§7.7a, the blind round, read at the frozen commit) — HOLDS in full, and
this is the sharpest thing in the slice.**

| | as first written (`0b6e4939`) | as delivered |
|---|---|---|
| `verdict.n_attacks` | **105** ✓ | **112** ✓ |
| attack records / `succeeded` | 105 / **91** ✓ | 112 / **95** ✓ |
| `verdict.main` | **`["E1","M3"]`** ✓ | **`[]`** ✓ |
| `undetermined` | **key absent entirely** ✓ | **`["M3"]`** ✓ |
| `not_gameable` | `["M3"]` ✓ | `[]` |
| `gameable` / `reference` | 37 / 36 | **37** / **37** ✓ |
| `b14_baseline_main` | absent | the nine ✓ |
| `M3` `n_landed` / `n_attacks` | 0 / 2 | **0 / 5** ✓ |

112 − 105 = **7 more attacks**, 95 − 91 = **4 more landed** ✓. So the abstract's
"raised the first number to 37 of 38 and cut the table of metrics trusted to rank
arms from nine to two" is exact, and so is "the other was moved to a tier created
for it afterwards" — `battery/PREREG_V9.md` 修订 2 (L195–200) records
`undetermined` being added and M3 moving into it. The one clause I most expected
to fail — "the `undetermined` tier did not yet exist" — is verified by the *key
being absent from the JSON*, not by prose.

**R3 (limit 4, the certificate that rejected nothing) — HOLDS.**
`S3_poverty_certified` is `true` on **105 of 105** attack records at `0b6e4939`
and **112 of 112** in the delivered artefact. `battery/audit/v9/REPORT.md` §9(a)
L161 states the same ("105 次全过，0 次违规") and L165–170 exhibits the **two**
constructions that performed real search and certified clean (the outer-factory
BFS closure, and `lambda` plus a conditional comprehension) — exactly two, as
slice C says.

**R4 (the empty published table) — HOLDS.** `battery/METRICS.md` **L33** is
`**Main table (0):** ` and **L35** is `**Reference (38):**` followed by all 38
ids. And the contradiction slice C flags is real: `gaming_audit.json` still
records `main` as the nine, by the leave-published-artefacts-alone rule.

**Verdict on the strongest result: it holds, at both rounds, against the frozen
artefact and the delivered one.** Slice C's audit of it is correct and I could
not move any of its figures.

### Priority 2 — Pass B: 10 of 10 hold

**B1 (§8.3 `label_sets_checked`, high) — HOLDS. The paper is wrong and the cited
file is the one that refutes it.** `exam/artifacts/leakage.json` `papers[*]`:
`p15-heldout-a0` → `["event","level_name"]`; `p15-handover-a0` → **`["rule"]`**;
`p15-adaptation-a0` → **`["exact_on_heldout","label","verdict"]`**;
`p15-verdict-a2` → `["board_size_class","class","search_credible","witness_length"]`.
**No paper has an empty label set.** PAPER L2460–2462 says the artefact "records
`label_sets_checked: []` for the handover and adaptation papers". Claimed `[]`,
actual `["rule"]` and `["exact_on_heldout","label","verdict"]`.

**B2 (§8.4 "no cheater response … is archived", high) — HOLDS, both halves.**
The gitignore half is exact: `exam/.gitignore` **line 9** is `artifacts/cheater/`
✓. The archive half fails: `exam/artifacts/answers/p15-verdict-a2.cheater-v4.answers.json`
exists, `examinee_id: "cheater-v4"`, `answers` holds **17** items and
`meta.exploit_per_item` is a **17**-entry map. It is scored as its own row of
`exam/artifacts/matrix/verdict_confusion.json` (`examinees["cheater-v4"]`,
`is_fake: false`, `awarded 17.0`, `fraction 0.5`). `exam/tests/test_selftest.py`
L614–641 asserts against it, by name, twice. `exam/leakage.py` L25–26 reads "Its
transcript is archived next to the paper."

**B3 (§8.4 the superseded weakness, high) — HOLDS, verbatim.**
`exam/STATUS.md` **L267–273** reads "11. ~~**Two cheater agents, four sheets, one
pass.**~~ **Partly closed by V4.** Two more cheaters have now sat the two sheets
that changed — verdict and held-out — and both results are above." — struck
through, exactly as slice C reports. `exam/runs/20260728T105500Z-V4-exam-selftest/CHEATER.md`
L3–6 quotes the weakness and answers it: "The two sheets that changed when P-15's
leaks were fixed are `p15-verdict-a2` and `p15-heldout-a0`. Both have now been
attacked." *(One imprecision in slice C, not in the finding: it renders that last
sentence in bold and the source does not. See "Imprecisions inside holding rows".)*

**B4 (§7.6, ρ = −0.83's exhaustive provenance claim, medium-high) — HOLDS, both
halves.** First half: `grep` for `-0.83` over all seven files of
`battery/artifacts/` returns only `-0.833333333`, an unrelated metric value ✓.
Second half: **`battery/STATUS.md` does not contain the string.** Its only
`0.83`-shaped token is `p=0.833` at L276, a different quantity in a different
section. W-4 is at **L160–165** exactly as slice C says, and it carries the
27–45 % failure rate and **ρ=+0.857** between E6 and P5 — a different pair and a
different sign. `battery/REPORT_V0.md` **L60** does carry "ρ = −0.83", so the
paper's first named file is right and its second is wrong. Slice C's "only other
occurrence in the tree",
`battery/runs/20260729T025515Z-V18-battery-prereg-check/REVIEW_TABLE.md` **L135**
("v0 自查 P1~P5 rho=−0.83"), is confirmed — it uses U+2212, which is why a naive
ASCII grep misses it. *Scope note:* the value also appears in the paper's own
apparatus (`PROVENANCE.md` L129 repeats the same wrong attribution to
`battery/STATUS.md`; `REVIEW.md`, `CITECHECK.md`). "Only other occurrence" is
true of the `battery/` tree, not of the repository.

**B5 (§7.1 "two of the five arms") — HOLDS.** `capability_spectrum.json`: the S1
campaign is **48 runs**, all `arm: "bare_cc"`, `campaign: "S1 baseline-parity"`,
`source` ∈ {`ledger.ar25.jsonl`, `ledger.g50t.jsonl`, `ledger.sk48.jsonl`,
`ledger.tn36.jsonl`} at 12 each. `bare_cc` has 80 runs total, so 32 are outside
S1 and `bare_cc` is not a gitignored arm. Only `schema_repro` (**8** runs,
`source: "schema_traces"`) is wholly absent. `battery/STATUS.md` **L32–33** says
"否则会静默少掉一整条臂和一整个战役" — one arm and one campaign, which is what
the paper's own next clause says and not what its lead phrase says.

**B6 (§7.7a limit 2, the inversion) — HOLDS, and limits 1 and 2 do contradict
each other.** `battery/PREREG_V9.md` 修订 1, **L189–191**: "`defended` 作为逐
指标布尔量把 K12 与 E2 提回了主表 … 方向上它把规则改**严**了" — the version
that lifted K12 and E2 back is the *literal, un-collapsed, pre-registered* form,
and the **collapse** is what made the rule stricter. PAPER L2090–2091 says the
self-report "records having run **the stricter version** first and seen it lift
K12 and E2 back". Inverted. And slice C's added point holds: limit 1
(PAPER L2085–2087) says applying the published un-collapsed rule leaves four
metrics in the table against a published zero, i.e. the published form is the
*looser* one. The surrounding claims all check: `git log --follow` on
`battery/audit/v9/verdict.py` bottoms out at **`520dc5dd`**, whose diffstat adds
`attacks/a1.py … a6.py`, `mutants.py`, `run.py` and `verdict.py` in one commit;
**`9892d23c`** adds `BLINDING.md`, `PREREG_V9.md`, `attack.py`, `check.py`,
`make_blind.py`, `prereg.py` (and `__init__.py`) — thresholds and the poverty
certificate, no adjudication. All **three** committed versions of `verdict.py`
(`520dc5dd`, `2f68c448`, `efc21d12`) compute `defended` only to record it as
`defended_by_v9`, each carrying the comment "`NOT defended` in the
pre-registered formula is not a per-metric …" — so "no commit ever contained the
un-collapsed form" is right.

**B7 (§8.2 "replaced rather than widened") — HOLDS, and the JSON beats the
heading.** `exam/grading/calibration.py` **L93–95** opens the block "# WIDENED
AFTER FIRST CONTACT -- see D-EX-010. The original band was # Band(0.0, 0.35,
"returning the unchanged frame is right only where # nothing moved"), and the
built paper scored 0.45" ✓. `exam/artifacts/calibration.json`
`pre_registered["heldout/bluffer"].band` = **`"in [0, 0.5]"`** ✓.
`exam/DECISIONS.md` D-EX-010's heading is "… was replaced rather than widened"
(L153) while its body **L157** says "The band is now `[0, 0.50]` and the work is
done by two new checks", and the same file at L391 calls it "widened … once
(D-EX-010), legitimately". 0.45, 0.35 and the two replacement checks
(`bluffer_hits_ceiling`, `oracle_minus_bluffer ≥ 0.50`) are all correct.

**B8 (§7.10a `ledger.jsonl` "0 throughout") — HOLDS.** `baseline-arms/ledger.jsonl`
has **560** rows. Exactly **185** carry `levels_completed`, all **0**. The other
**375** do not carry the key. So "0 throughout" reads as 560 of 560 and is 185 of
560. *Imprecision in slice C:* it describes all 375 as model-call rows; 274 are
(160 with `prompt_chars`/`duration_ms`, 114 `attempt` rows), and the remaining
**101** are env-action rows (`action`, `arm`, `failed`, `frame`, `game_id`). The
finding is unaffected — none of the 375 carries the field.

**B9 (§7.2a, three decimals on a 33-value grid) — HOLDS.** The arithmetic is
right: `battery/audit/stats.py` L64–66 divides by `len(highs) * len(lows)` = 16,
so δ ∈ {−16/16 … +16/16} = **33** values. The artefact values are
`cliffs_delta` **−0.5625** (X3) and **−0.1875** (X2). The paper prints −0.562 and
−0.188 — and `battery/REPORT_V2.md` **L66/L68** print exactly `**−0.562**` and
`−0.188`, so slice C is right that the paper reproduces the report's rendering
rather than the artefact's value, in the one paragraph whose subject is spurious
precision.

**B10 (§8.2 "no answers or reports exist for them in the tree") — HOLDS, on the
verdict paper.** The answer file above is an answer for `p15-verdict-a2` by a
fifth, non-fake examinee, and `exam/artifacts/matrix/verdict_confusion.md` has a
section headed "## Examinees this matrix cannot tell apart" whose first bullet is
"* **`cheater-v4`, `oracle`** — every cell identical, scores 0.5000, 1.0000." —
slice C's "identical in every cell", verbatim from the artefact. The held-out
half also checks: `exam/STATUS.md` weakness 12 L275 reads "Measured at **79/80**
by V4's cheater and confirmed". Adaptation is indeed the only genuinely untouched
one.

### Priority 3 — Pass D: 6 of 6 hold

**D1 (the sentence attributed to "the directory", load-bearing) — HOLDS. The
sentence does not exist.** Searching every tracked `.md`/`.py`/`.json`/`.jsonl`/
`.txt`/`.dsl`/`.lean` file for "nobody has looked for" returns exactly four hits:
`papers/phase1-workshop/PAPER.md` L2495, its own source
`papers/phase1-workshop/sections/08_exam.md` L171, and two lines of slice C
itself. Nothing in `exam/`. The nearest real sentence is `exam/STATUS.md`
**L272**: "a cheater pass is a sample, not a proof: what it did not find is not
absent." An italicised paraphrase introduced as a quotation and attributed to a
directory — and it is the superseded form of the point (B3).

**D2 (§8.2's second blockquote) — HOLDS, both defects.** `exam/STATUS.md`
**L164–166**: "…the difference shows up as **多付的搜索成本 ≈ 玩法书缓存的计算
量** — a cost, not an accuracy." The paper (L2418) writes "多付的搜索成本 — a
**cost**, not an accuracy": the clause "≈ 玩法书缓存的计算量" is deleted from
**inside the bold span with no ellipsis**, and the bold is moved off the Chinese
onto "cost". Both as slice C states.

**D3 (`exam/guard.py`'s scope sentence) — HOLDS.** L81–83: "Not a sandbox -- a
process determined to get out can get out.  It is a tripwire for the accident
that actually happens: **a helper three imports down that quietly fetches
something.**" The paper (L2473–2474) closes the quotation at "happens." — the
dropped clause is the only part that says what accident, and no ellipsis marks
it.

**D4 (§8.1's held-out rubric blockquote) — HOLDS, all three alterations.**
`exam/grading/rubrics_heldout.py` L5–7: "**On** a 7x7 A0 board a typical
transition changes two cells, so an examinee that returns the *input frame
unchanged* already scores 47/49 = 96% under a cells-correct rubric". The paper
lowercases the "on", drops the italics, and writes "96 %".

**D5 (a quotation sourced to the wrong file) — HOLDS.** "a rubric that can see
who it is marking is a rubric that can flatter" is `exam/model.py`'s `Rubric`
docstring, at **L242–243** (slice C says L240–241 — see imprecisions). It is not
in `exam/grading/mark.py`, the one path the sentence names; `mark.py` L3–4 does
support the sentence's first half ("It looks up each item's rubric by id, hands
it (answer, truth, item)").

**D6 (§8.2's first blockquote) — HOLDS.** `exam/STATUS.md` L157–162; the paper
stops at "would be wrong." and drops "The sheet needs harder items — boards where
a manual-only reader must actually pay for the search — before the delta means
anything." Truncation at a sentence boundary with no ellipsis, and slice C is
right that this is the mildest of its six.

### Priority 4 — the confirmed-correct rows: 17 of 17 hold, under recomputation

These were the real test. Each was recomputed from the artefact rather than read
back off the report.

**CC1 §7.1's slot counts — HOLD, and they reconcile.** Summing
`capability_spectrum.json` `coverage[*].by_status` over all 38 metrics:
**ok 1433, not-applicable 2066, insufficient-data 111**, total **3610** = 38 × 95.

**CC2 §7.1's provenance asymmetry — HOLDS, 1 of 7.** `battery/artifacts/` holds
seven JSON files; `provenance` is a top-level key of `capability_spectrum.json`
**only**. `arm_contrast`, `discrimination`, `discrimination_arms`,
`gaming_audit`, `redundancy`, `validation_material`: none.
`provenance.cut.piles_sha256` = `3feca53e…41bbc19a`, `provenance.input_digests`
has **6** entries, `provenance.n_runs` 95, `provenance.n_games` 4.

**CC3 §7.2's whole effect-size table — HOLDS, every cell.** From
`discrimination_arms.json`: P1 `+1.0` / 0.793492681 / 1.015264428; P2 `+1.0` /
−0.155038916 / 0.008213513; E4 `−0.875` / 0.248594407 / 0.053614176; X1
`−0.625` / 0.278435693 / 0.084637118; X4 `−0.625` / 0.09305205 / 0.010863339;
X3 `−0.5625` / 0.014987662 / −0.007395678; P3 `−0.375` / 0.129786631 /
0.00093633; X2 `−0.1875` / 0.975238357 / 0.94085297. All eight δ and all sixteen
medians round to the printed values. `agrees_with_declared_direction` is `false`
on **exactly X3 and X2**. `verdict` is `"underpowered"` on all eight and on
nothing else (23 `no-data` + 7 `not-ranked` = 38). Ten metrics have
`n_paired_games ≥ 2` (the eight plus P5 and X5); exactly eight carry a
`cliffs_delta`.

**CC4 §7.2's Schema-side column and the confound — HOLD.** Counting
`status == "ok"` among the 8 `schema_repro` runs: **P1 4/8, P2 4/8, E4 4/8,
X1 8/8, X4 8/8, X3 8/8, P3 8/8, X2 8/8** — every cell as printed. `model_calls`
on the `claude_fable_opus` collection: **279, 197, 288, 564** (the paper's
"197–564"); on `gpt_5_6_sol`: **0, 0, 0, 0**. Median `steps` over the 8
`schema_repro` runs **450.0**, over the 80 `bare_cc` runs **27.0**. The arm is
4 games × 2 collections = 8, confirmed by enumeration of `(game_id, model)`.

**CC5 §7.2a's statistic — HOLDS.** `battery/audit/stats.py` L55–66:
`cliffs_delta` is `(greater - lesser) / (len(highs) * len(lows))` over the full
cross-product — unpaired, exactly as the paper says; only `sign_test` pairs.
P3: `cliffs_delta −0.375` with `agrees_with_declared_direction: true` against
`sign_test {wins 1, losses 2, ties 1, n 3, p_value 1.0}`. X2 has the identical
sign-test shape.

**CC6 §7.5's power floor — HOLDS.** `discrimination_arms.json` carries a
top-level `power` string ("a two-sided sign test needs 6 non-tied paired games…")
and `min_attainable_p` under every ranked metric's `sign_test`. **P3, X2 and X3**
each have `ties: 1`, `n: 3`, `min_attainable_p: 0.25`; the other five sit at
**0.125**. Three of eight at the worse floor, exactly as claimed.
`REPORT_V0.md` L40–43 is the blockquote, byte-exact, bold on **0.125** and
**Six** included.

**CC7 §7.9's de-redundancy — HOLDS, including the paper's two corrections of its
sources.** `redundancy.json`: `n_clusters` **32**, `n_metrics` **38**,
`n_eliminated` **5**; the five retirements are **E7→E4 (shared_runs 70)**,
**K14→K5 (5)**, **K7→K5 (5)** with `rho_with_representative` **1.0**,
**K8→K10 (5)**, **X4→X1 (87)**. `cross_family_clusters` is the single
`[["K6","X1","X4"]]`, and that is the **only** cluster of the 32 carrying a
`warning` key, against one global `coverage_note`. The multi-member clusters are
`{E4,E7}`, `{K10,K8}`, `{K14,K5,K7}`, `{K6,X1,X4}` — so **two** K-only clusters
with three retirements between them, against `REPORT_V2.md` **L186**'s "The
three K-family clusters". Both corrections are right.

**CC8 §7.9's pair coverage — HOLDS, against v1's own archive.**
`redundancy.json` `n_pairs` **703**, `n_pairs_measured` **257**, and the `matrix`
list has 703 entries of which exactly **257** carry a non-null `rho`.
`battery/runs/P-14/redundancy.json`: `n_pairs` **703**, `n_pairs_measured`
**257**, `n_clusters` **33** — v1's identical coverage and one more cluster, as
claimed.

**CC9 §7.10's single goal-reaching run — HOLDS.** P4 returns `status: "ok"` on
exactly **one** of the 95 runs, `a2-refutation`, `support {actions 18,
optimal 18, won true}`, `value 1.0`.

**CC10 §7.10a's three pile digests — HOLD, all three, recomputed.**
`arc-recon/data/piles.json` was hashed and parsed in memory; nothing from it was
printed or read beyond digests and counters. Canonical JSON of the payload minus
its own `sha256` field (compact, sorted keys) →
`3feca53e5ede695cfa46ae994cb95fd6b43abb9d97295e8c87e6302b41bbc19a`, matching
`CLAUDE.md` and the file's own `sha256` field. LF-normalised bytes →
`d3140eff4889095f64aff6360697eeff0a1b159a53d80a1ef6407b2c4dd5b8c9`, which is
D-B-011's value. The bytes as they sit on this Windows checkout →
`f2ef44d100caee9075b9c52b6c2694d9bb47d628702e0c1911655eb9f9790826`, the paper's
third value, which D-B-011 does **not** carry. **111** CRLF pairs.
`git ls-files --eol` reports `i/lf w/crlf attr/` (no attribute);
`git check-attr -a` returns nothing; the root `.gitattributes` has exactly two
lines, `PARTNER_SYNC.md merge=union` and `monitor/board/** text eol=lf`, neither
covering it. `battery/DECISIONS.md` **D-B-011** exists at L124 and says what it
is cited for. Every element of the most digest-heavy row in the slice reproduces.

**CC11 §7.7's epistemic family — HOLDS on the value, and exposes a cross-slice
anchor disagreement.** `battery/tests/test_exploits_mechanism_epistemic.py`
**L393** is literally `assert len(landed) == 18` ✓. The docstring sentence
"Eighteen of twenty metrics in this family are reachable at or near their best
value by a run with none of the capability -- nineteen before v2.1 closed K12"
is at **L386–388**. Slice C cites it as "L381-382" (blank lines); slice A, per
`row-sample-audit.md`, cites L387. **Slice A is right and slice C's anchor is off
by five lines.** Scope 14 epistemic + 6 mechanism = 20 ✓; the test also asserts
`not exploits["K12"].succeeded` ✓.

**CC12 §8.1's four papers — HOLDS exactly.** `exam/artifacts/papers/*.paper.json`
(`n_items` / `total_points`): held-out **80 / 80.0**, handover **29 / 46.0**,
adaptation **60 / 144.0**, verdict **17 / 34.0**.

**CC13 §8.3's static checks — HOLDS, and agrees with the sibling audit.**
`leakage.json` `probes_declared` = 363 + 58 + 1284 + 85 = **1790**; `probe_hits`
and `structural_hits` are **0** on all four. `row-sample-audit.md`'s
A/load-bearing (a) row reports the same four figures and the same total from the
same file — **no cross-slice disagreement.** The five attack surfaces are named
functions in `exam/leakage.py` at exactly the lines slice C gives:
`probe_hits` **56**, `structural_hits` **86**, `positional_report` **95**,
`metadata_hits` **232**, `cheater_brief` **1146**; and the module docstring
still opens "Three checks" (L3) while describing a fourth at L23.

**CC14 §8.2's calibration block — HOLDS, every figure.**
`exam/artifacts/calibration.json`: `calibrated true`, `failures []`; oracle
`fraction 1.0` and null `fraction 0.0` on all four papers. Held-out memoriser
`axes.by_split` = `{replay: 1.0 (40/40), heldout: 0.15 (6/40)}` with
`gap_replay_minus_heldout: 0.85`; `by_split_event` gives
`replay/blocked_crossing 5/5` against `heldout/blocked_crossing 0/5`. Verdict
bluffer `axes.confusion` = `{tp 9, fp 8, tn 0, fn 0, sensitivity 1.0,
specificity 0.0}`, and `structural_expectations.verdict_bluffer_pair` reads "the
bluffer must show sensitivity 1.0 and specificity 0.0". Adaptation memoriser
`axes.silently_wrong` = **2**, and 0 for every other adaptation mode. Both
handover reports: `awarded 46.0`, `possible 46.0`, `fraction 1.0`,
`axes.tier2_minus_tier1` **null** with an explanatory
`tier2_minus_tier1_note`. `assert_calibrated` raises at
`exam/grading/calibration.py` **L524–531**.

**CC15 §7.10a's empty capability column — HOLDS, all four instruments.**
`theoria-arm/runs/20260728T015354Z-g50t-first-contact/run.json`:
`summary.scorecard.total_levels_completed` **0**,
`total_environments_completed` **0**, `environments[0].completed` **false**,
`environments[0].runs[0].level_actions` **[7, 0, 0, 0, 0, 0, 0]** — four fields
of one object, as the paper says. The three `ablation-arm/artifacts/{a0-base,
a2-base,a2-charitable}/episode.jsonl` files each contain **exactly one** row with
`levels_completed: 1`, and every row in all three carries `card_id: null` and
`score: null`. `baseline-arms/runs/20260728T103135Z-a7/envelope.json`
`pooled_cv.levels_completed` is **null** and is the *only* null in `pooled_cv`,
beside `usd_per_action 0.033244` and `http_per_action 0.09574`.

**CC16 §7.10a's budget arithmetic — HOLDS.**
`theoria-arm/runs/20260728T210000Z-a3-level-boundary/FINDINGS.md` L11–14:
`level_baseline_actions: [78, 175, 179, 230, 96, 54, 67]`, "**78 successful
actions**", "The authorised budget is **40 per level**". The a7 envelope's
`games["g50t-5849a774"].stats.actions_ok` is `{min 30.0, mean 30.0, max 30.0}`
— so 30 delivered against 40 authorised against 78 needed, and "neither budget
buys the first level" is arithmetic on read values. *Imprecision:* slice C calls
30.0 "the a7 envelope's per-cell figure"; it is g50t's (sk48 is 26/27/28, tn36
23/23.67/24). g50t is the right cell, since the 78 is g50t's.

**CC17 §7.7a limit 1 — HOLDS, and it is the sharpest check in the section.**
Commits as above (R2/B6). The delivered artefact's `rule` field publishes the
pre-registered form verbatim, `NOT defended` included. Applying it to the
artefact's own per-metric fields — `gameable ∧ accidental_if_gameable ∧
defended_by_v9 ∧ prior_tier == "main"` — selects exactly **E2, E3, K12, M6**:
**four of the nine would have stayed**, and no fifth qualifies (E1 is also
`defended_by_v9` but its `prior_tier` is `reference` in the delivered artefact).
Limit 5 also holds: no metric row carries a strength field — the 11 keys are
`R1_promotion_refused, accidental_if_gameable, attacks, defence, defended_by_v9,
gameable, n_attacks, n_landed, prior_tier, r2_satisfied, v9_tier`, exactly slice
C's list — while `battery/audit/v9/REPORT.md` §9(c)'s table (L204–208) grades
强 = E2/E3/K12, 中 = P3/P4/E1, 弱 = K7/K11/M6: nine metrics including E1 and
omitting M3. Limit 3's sentence is at REPORT.md **L226** ("裁决里除
`accidental` 之外没有任何字段是作者断言的"), limit 6's heading at **L120**
("## 6. 攻击面的形状：这不是 37 个独立发现"), limit 7's figure at **L137**
("91 条落地攻击里 51 条捏造生产者侧记录"). `battery/BLINDING.md` **L12** says
六个攻击者, each with an independent copy, mutually invisible; §2 (L32ff) shows
`battery/audit/gaming.py` and `battery/audit/exploits/` both withheld. The two
blind-fall figures are in §2's table: P4 **0.05 after 10000 failed actions**
(L42), K12 **1.0 on a repair episode that spent zero environment actions**
(L60).

### Priority 5 — Pass C: 4 of 4 hold

**C1 (§8.1's uncited eight) — HOLDS, and it is the largest uncited block.** The
eight items/points figures are `n_items` and `total_points` of the four
`exam/artifacts/papers/*.paper.json` files (verified in CC12). **None of those
four paths appears in PAPER.md L1669–2520** — my independent path extraction over
the slice lists no `exam/artifacts/papers/…` token at all. The row citations name
`exam/papers/heldout.py` and its three siblings, and `exam/model.py`.

**C3 (§7.7's "34") — HOLDS.** PAPER L1974–1977's parenthesis names four fields —
`n_demonstrated` 38, `n_disagreements` 17, `main` 9, `reference` 29, all four
verified in R1 — and **none of them is 34**. 34 is a count over
`metrics[*].demonstrated.succeeded`, which `gaming_audit.json` does not
aggregate; I had to compute it.

**C4 (§7.7a's 105 / 91 / 37) — HOLDS.** The citation at PAPER L2034 is
`battery/BLINDING.md` and `battery/PREREG_V9.md`. Neither carries any of the
three figures — both predate the attacks, and `9892d23c` (which introduces both)
contains no results. All three are in the V9 run artefact at `0b6e4939`
(verified in R2). And the count is right: my path extraction over L1669–2520
finds **no** occurrence of
`battery/runs/20260729T021247Z-V9-battery-gaming-audit/…`, so §7 — the section
that reports the round — never names the file the round produced.

**C9 + C10 (`exam/STATUS.md`) — HOLD.** My independent extraction of every
path-like backtick token in L1669–2520 (all 57, listed by line below) contains
**no `exam/STATUS.md`**, while §8 quotes it three times: L2411–2414 (STATUS
L157–162), L2416–2418 (L164–166) and L2493 (weakness 11, L267). Quoted three
times, cited zero times.

### Priority 6 — Pass A: 0 broken paths, and one token missing from slice C's frame

Independently re-extracted: every backtick span in PAPER.md L1669–2520, filtered
to tokens matching `^[A-Za-z0-9_.\-/{},*]+$` that contain a `/`, a known
extension, or a leading dot; then `Path.exists` at the worktree root; then brace
expansion; then a section-implied base.

| measure | slice C | this audit |
|---|---|---|
| distinct path citations | 56 | **57** |
| resolve as written from the tree root | 53 | **54** |
| resolve only under a section-implied base | 1 (`mark.py`) | **1** ✓ |
| resolve only after brace expansion | 2 | **2** ✓ |
| **do not exist anywhere in the tree** | **0** | **0** ✓ |

**The index's one genuine whole-paper result survives: every path slice C cites
resolves.** `mark.py` (L2371) resolves to exactly one file, `exam/grading/mark.py`,
which the same subsection cites in full nineteen lines earlier;
`ablation-arm/artifacts/{a0-base,a2-base,a2-charitable}/episode.jsonl` (L2245)
expands to three files that all exist;
`exam/artifacts/reports/p15-handover-a0.reader-tier{1,2}.report.json` (L2404)
expands to two that both exist. 54 + 1 + 2 = 57, and every one of the 57 was
opened or stat'd.

**The one-token difference is real and identifiable: `.gitattributes` at
L2316.** It is a backticked repo-relative path citation ("has no
`.gitattributes` covering it"), it resolves at the worktree root, and slice C's
extractor did not classify it as path-like — its Pass A frame is
57 spans = 56 paths + 1 false positive (`ok_steps / optimal`), where the true
figure is 57 paths + 1 false positive over 58 spans. Slice C did *open* the file
— its §7.10a confirmed bullet reads its two lines correctly (verified in CC10) —
it simply is not in the count. So slice C's **56 is one low, and its 53 is one
low**, which makes the index's aggregate 313 one low for this slice. It does not
touch the "0 broken" result and it is not a defect in the paper.

---

## Slice C's header counts against its own rows

| header claim | rows beneath it | verdict |
|---|---|---|
| B · wrong, mis-attributed, or absent: **10** | B1–B10 enumerated, 10 distinct ids | **matches** |
| C · uncited: **11** (1 overlaps B) | C1–C11 enumerated, 11 distinct ids; C9 declared as the overlap | **matches** |
| D · inexact: **6** | D1–D6 enumerated, 6 distinct ids | **matches** |
| D · attributed passages checked: **31 = 9 blockquotes + 22 inline** | **9** blockquote groups independently counted in PAPER L1669–2520 | first term **matches exactly**; the 22 inline is not enumerable from the 23 *Quotes verified exact* bullets (several bullets carry two or three fragments) |
| A · 57 spans / 1 false positive / 56 / 53 / 1 / 2 / 0 | not enumerated in the report | **56 and 53 are each one low** (see Pass A above); 1, 2 and 0 confirmed |
| B · claims checked: **~150** | 49 confirmed bullets carrying **205** ✓-marks, plus 10 defects | **not reproducible as a number**, which slice C says itself in limit 8 ("a count of claims I opened a file for, not a claim of exhaustiveness") |

**Result: unlike this directory's `MANIFEST.json`, slice C's three defect counts
do reconcile with the rows beneath them.** The counting-rule disease
`row-sample-audit.md` found one level up does not recur here. Two soft figures
(the ~150 and the "22 inline") are not re-derivable, and slice C flags the first
of those itself. The two Pass A counts are off by one in the same direction.

---

## The gate-E rulings over this span — tested against their own stated evidence

The brief asked for four §7 rulings. **There are three, not four**, and I could
find no fourth at HEAD either (`git show HEAD:…/verify_paper.py` gives the same
three). `08_exam.md` carries two more, so slice C's span holds **five of the
paper's ten** `ADJUDICATED_UNCITED` entries — still more than any other section,
and the highest concentration in the paper. Verdicts, each tested by running the
gate's own `_blocks()` over the section files:

| # | ruling anchor | verdict |
|---|---|---|
| 1 | `07_battery.md` · "every δ here is a multiple of 1/16" | **HOLDS in full** |
| 2 | `07_battery.md` · "bill shape's distribution rests on 67 runs" | **holds on substance; stated locator wrong** |
| 3 | `07_battery.md` · "and the main table moved twice" | **HOLDS** |
| 4 | `08_exam.md` · "the 0.000 that could be computed from two" | **holds on substance; stated locator wrong by one block** |
| 5 | `08_exam.md` · "**n = 1 per handover tier**, on a saturated" | **stated evidence is FALSE** |

**Ruling 1 — HOLDS, every element.** "δ is (#greater − #less) over the 4 × 4
cross-arm pairs (`battery/audit/stats.py`)": true, `stats.py` L64–66. "arithmetic
on the n = 4 stated in this same block": true, the block opens "A second
consequence of n = 4 per side". "−0.562 and −0.188 restate rows of §7.2's table":
true, PAPER L1737 and L1739. "whose preamble cites
`battery/artifacts/discrimination_arms.json`": true, L1728. The two blocks
immediately above the ruled block cite `stats.py` and
`discrimination_arms.json` respectively.

**Ruling 3 — HOLDS.** It is a heading (PAPER L1964, `### 7.7 The anti-gaming
register became executable, and the main table moved twice`). "19 → 6 on
demonstration and 6 → 9 after four defences" is stated at L1977–1978 and cited to
`gaming_audit.json` (L1976) with the intermediate 6 attributed to
`battery/REPORT_V2.md` (L1980) — and 19 / 9 / 10 all reproduce from the artefact
(R1), with L83 naming the six by hand. "the further 9 → 2 → 0 is 7.7a's blind
round and is counted there" is true (R2, R4). The only slack is "the block below",
which is the *second* block below; nothing turns on it.

**Ruling 2 — substance true, locator stale.** "A one-sentence restatement of the
E2 distribution established **four lines above**, where it carries
`battery/artifacts/capability_spectrum.json`" — the E2 distribution and its
citation are at PAPER **L2271–2274**, and the ruled sentence is at **L2288**:
**fifteen** lines above, not four. Structurally the ruling is right (it is the
immediately preceding block, and that block does carry the path); and the second
half checks — §7.10a does cite
`baseline-arms/runs/20260728T103135Z-a7/envelope.json` (L2248) for the empty
capability column. The preceding paragraph has visibly been extended since the
ruling was written (four of its lines run well past the wrap width), so the
locator decayed while the keyed anchor held. Minor, but it is a ruling stating a
distance that is no longer true.

**Ruling 4 — substance true, locator wrong by one block.** "Both artefacts it
would be computed from are cited **one block above**": the block one above
(PAPER L2408) cites only `Theoria.md`; the two handover reports are cited in the
block **two** above (PAPER L2402,
`exam/artifacts/reports/p15-handover-a0.reader-tier{1,2}.report.json`). The
substantive half is true: both reports record `axes.tier2_minus_tier1` as
**null** with a note (CC14), and the paragraph does explicitly refuse the number
("We report the tier difference as **unmeasured**").

**Ruling 5 — the stated evidence is FALSE, and this is the most consequential
thing in this section.** The ruling reads: "Restates the sample size of the
handover result **cited one block above** (one report per tier, both named
there)."

* The block one above the ruled block is the §8.4 **heading** ("What the exam
  does not establish"), which cites nothing. Two above cites `exam/guard.py` and
  `exam/tests/test_core.py`; three above cites `exam/artifacts/leakage.json`.
* The two handover reports are cited in block **[12]** of `08_exam.md`; the ruled
  block is **[24]**. That is twelve blocks and ~76 PAPER lines earlier, in §8.2,
  with the whole of **§8.3** in between.

So the justification's one factual assertion about where the evidence sits is
wrong — the same failure class the `11_limitations.md` ruling in gate F records
against an earlier version of itself.

**And the consequence is larger than the wording.** A ruling clears its **entire
block**, and `_blocks()` merges a bullet list into one block: the ruled block is
the whole 18-line, six-bullet §8.4 list (PAPER L2478–2495). So a ruling written
about "n = 1 per handover tier" also exempts:

* "**The cheater's numbers are prose, not artefacts** … no cheater response or
  transcript is archived" — slice C's **B2**, *high*, refuted by a file in
  `exam/artifacts/`;
* "**Two cheater agents, four sheets, one pass**" — slice C's **B3** (*high*) and
  **C9**, a sentence its source has struck through and which §8 never cites;
* "*the leaks that remain are the ones nobody has looked for yet*" — slice C's
  **D1**, a quotation that exists nowhere in the repository.

`08_exam.md` has exactly **two** blocks carrying quantities with no citation, and
both are ruled; those two rulings are all that stands between gate E and §8. The
`BROAD` guard cannot see this, because block merging makes six bullets one block
and the ruling therefore matches exactly one. **A green `E UNCITED` is not
evidence about §8.4's cheater bullets**, and anyone reading the gate as coverage
of the paper's most-contradicted passage is reading it wrong.

This is a finding about `verify_paper.py`, not about slice C — slice C audits
`PAPER.md` and found all three of those defects on its own. I state it because
the brief asked for it and because the index's disposition section leans on gate
greenness.

---

## Cross-slice consistency

Checked deliberately on the artefacts slice C shares with a sibling.
`row-sample-audit.md` reported "no disagreement found" across A/B/D1/D2; adding C
changes that only cosmetically.

* **`gaming_audit.json`** (slice A and D2 read it; slice C reads it hardest):
  `n_demonstrated 38`, `n_disagreements 17`, `main` the nine,
  `demoted_by_demonstration` 10, 34 succeeded / 4 not (`E2, K12, M3, P4`), and
  14 of the 17 disagreements carrying `defended`. **Identical readings in all
  three slices and in the earlier sampler.** No tension.
* **`v9_gaming_audit.json`** (slice A and D2 read the delivered form; slice C
  reads both forms): delivered `n_metrics 38`, `n_attacked 38`, `n_attacks 112`,
  `gameable` 37, `b14_baseline_main` the nine, `demoted_by_v9` nine including M3,
  `undetermined ["M3"]`, `main []`, `unattacked []`, `not_gameable []`, 95
  landed, 112/112 certified. Every figure agrees with `row-sample-audit.md`'s
  cross-slice section. Slice C additionally reads `0b6e4939` and is right there
  too.
* **`capability_spectrum.json`** (A, B, C, D2): `battery_version "v2"`, 38 cards
  over five families (epistemic 14, economy 7, mechanism 6, exploration 6,
  planning 5), 95 runs over five arms (80/8/4/2/1), `schema_repro` 8,
  `provenance.n_games 4`, `provenance.cut.piles_sha256 3feca53e…41bbc19a`. No
  contradiction between any pair of slices.
* **`exam/artifacts/leakage.json`** (slice A's load-bearing (a) via the earlier
  sampler; slice C's §8.3 and B1): 1790 declared probes, 0 probe hits, 0
  structural hits, four papers. Same readings.
* **`battery/tests/test_exploits_mechanism_epistemic.py`** (slice A's B3; slice
  C's §7.7): both agree `assert len(landed) == 18` is at **L393**. They disagree
  on the docstring anchor — slice A L387, slice C L381-382 — and **slice A is
  right** (the sentence is at L386–388). A cosmetic disagreement about a line
  number, the first cross-slice disagreement of any kind found in this run, and
  it changes no value.

---

## Imprecisions inside holding rows

Recorded so the 42/42 is not read as more than it is. None is a wrong value and
none is load-bearing.

1. **Three line anchors are off** — slice C cites the epistemic test's docstring
   at "L381-382" (actual L386–388, and slice A has L387); `exam/model.py`'s
   `Rubric` docstring at "L240-241" (the quoted sentence is at L242–243);
   `mark.py`'s `confusion` docstring at "L100-101" (the quoted fragment begins on
   L99). Every one opens on the right content within a few lines, which is the
   same class and the same severity as the three anchor slips
   `row-sample-audit.md` found in A and D1.
2. **Emphasis added inside three quotations.** Slice C renders CHEATER.md's
   "Both have now been attacked." in bold (the source has none), bolds
   `battery/STATUS.md`'s "一整条臂和一整个战役" (the source has none), and
   compresses `registry.py` L8–9's "travels onto every sheet at build time and
   onto every report at grading time" to "travels onto every sheet and report"
   inside quotation marks. This is precisely the defect class slice C's own D2
   and D6 rows are about, committed by the auditor.
3. **B8 over-characterises the 375**: 274 are model-call rows, 101 are env-action
   rows. The finding does not depend on it.
4. **CC16's "the a7 envelope's per-cell figure"** is g50t's cell specifically;
   two of the three games differ.
5. **B4's "the only other occurrence in the tree"** is true of `battery/`; the
   paper's own apparatus (`PROVENANCE.md` L129, `REVIEW.md`, `CITECHECK.md`)
   carries the value too — and `PROVENANCE.md` repeats the same wrong attribution
   to `battery/STATUS.md`, which is where the defect probably entered.
6. **CC17's list of `9892d23c`'s files** omits `battery/audit/v9/__init__.py`.
7. **Pass A's 56 and 53 are each one low** — see the Pass A section.

---

## What this audit could NOT check

1. **Nothing was executed** beyond `verify_paper.py` (read-only, 7/7) and `git`
   read commands. No `battery/run_battery.py`, no exam rebuild, no `pytest` over
   `battery/` or `exam/`. Slice C's own limit 1 applies to me identically: a
   stale artefact passes this audit unchallenged, and B1 is proof that artefacts
   in `exam/` do go stale.
2. **The `~150` claims-checked figure cannot be verified as a number**, only as
   an honest statement of what was opened. I did not attempt to enumerate 150
   claims.
3. **Pass D's "22 inline" is not re-derivable** from the report's own bullets. I
   verified the 9 blockquotes exactly and all 6 inexact rows; I did not
   reconstruct the inline 22.
4. **`exam/STATUS.md` (1122 lines) and `battery/audit/v9/REPORT.md` (229) were
   read only where a claim pointed into them** — STATUS at L155–170 and
   L263–300, REPORT at its heading list, §6, §7, §9(a) and §9(c). A
   contradiction in an unvisited paragraph would not appear here. Same caveat as
   slice C's limit 7.
5. **Sealed-pile material was never opened.** `arc-recon/data/piles.json` was
   hashed and parsed in memory to drop one field; its three digests, its CRLF
   count and its top-level key *count* are the only things that left it, and
   nothing from it is reproduced here. No game id outside the four
   development-pile ids appears anywhere in this file.
   `environment_files/` was never touched, no local engine or swarm runner was
   invoked, and no network or API call was made. §7.10a's "no arm in this
   repository has completed a level" and §7.1's "zero sealed-pile reads" remain
   unverifiable in principle for me exactly as for slice C, and I inherit its
   record of that rather than pretending to close it.
6. **`baseline-arms/schema_traces/` is gitignored and absent**, so CC4's 8-run
   composition and 197–564 range were checked only through
   `capability_spectrum.json`'s derived statistics — the same route slice C took,
   and the only one available.
7. **Ruling intent** — I tested each ruling's *stated evidence*, not whether the
   adjudication it reaches is the right call. Whether §8.4's bullet list should
   carry a path is a judgement; whether the handover reports are cited one block
   above is a fact, and it is not.

---

## Verdict on the question the index needs answered

**Slice C supports a `binding` stamp. Of the 42 rows I drew — weighted onto its
high findings, its confirmed-correct bullets, and the claim the abstract calls
the strongest result — 42 hold, none is wrong, and none is unverifiable.**

Three things make that a stronger result than the bare tally:

* **The strongest result checks out at the source.** The abstract's 34-of-38,
  17-contradicted-14-defended, 37-of-38, nine-to-two, and 105/112-certified chain
  reproduces from `gaming_audit.json` and from the V9 artefact read at
  `0b6e4939`, including the negative claim that the `undetermined` tier did not
  yet exist — verified by a key's absence from a frozen blob, not by prose.
  Slice C audited it correctly and I could not move a figure.
* **The confirmed-correct rows survived enumeration, not inspection.** The three
  pile digests were recomputed from bytes; the 3610 slot count, the 703/257 pair
  matrix, the 33-value δ grid, the five retirements, the 49-cell effect-size
  table and the four-of-nine counterfactual were each recomputed from the
  artefact rather than read back off the report. These are the rows nothing
  downstream re-checks, and they are where the slice is strongest.
* **Slice C's own defect counts reconcile with its rows** — B 10, C 11, D 6 all
  match, and the 9 blockquotes match exactly. The counting-rule defect
  `row-sample-audit.md` found in this directory's `MANIFEST.json` does not
  recur inside the slice.

**Two corrections the index should absorb before it is quoted, neither fatal:**

1. **Slice C's Pass A frame is one citation short.** `.gitattributes` (PAPER
   L2316) is a real, resolving, repo-relative path citation that its extractor
   dropped. The true figures are **57 distinct citations, 54 resolving as
   written**, not 56 and 53 — so the index's row "distinct path-like tokens …
   C 56 … total 313†" and "resolve as written … 53 … **282**" are each one low.
   **The headline result is untouched: 0 broken paths, and I checked all 57, not
   a sample.**
2. **Gate E's ruling for §8.4 has a false stated justification**, and because a
   ruling clears its whole merged block, that one ruling exempts the bullets
   carrying slice C's B2, B3, C9 and D1 — three of its four load-bearing §8
   findings. Green on `E UNCITED` therefore says nothing about §8.4. This is a
   defect in `verify_paper.py`'s adjudication table, not in slice C, but the
   index's *Disposition* leans on gate greenness and should not lean on it here.
   Ruling 2's "four lines above" (actually fifteen) and ruling 4's "one block
   above" (actually two) are the same decay in milder form. **§7's three rulings
   — not four — are otherwise sound, and rulings 1 and 3 hold element for
   element.**

**Does the index overclaim?** In one specific and one general way. Specifically,
its Pass A aggregate for slice C is one low, and the brief's premise of four §7
rulings is wrong (there are three). Generally — and this is the honest ceiling —
the index's GAP paragraph said slice C rested on a single author; it now rests on
two, and the second reader moved nothing. I did not manufacture a finding to
improve on that, and the one WRONG-class result available here is in the gate,
not in the slice.

**Scope.** Read-only throughout: no `git add`, `commit`, `push` or `checkout`; no
slice file, `PAPER.md`, `MANIFEST.json`, `verify_paper.py`, `test_nosecret_gate.py`,
`CITECHECK*.md` or `row-sample-audit.md` was modified. `verify_paper.py` was
imported to reuse its `_blocks()` and `ADJUDICATED_UNCITED`, and not written to.
This file is the only artefact created.
