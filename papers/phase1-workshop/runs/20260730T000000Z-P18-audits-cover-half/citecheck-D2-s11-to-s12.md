# CITECHECK slice D2 — §11 (limitations) and §12 (related work)

**Audited state.** `papers/phase1-workshop/PAPER.md`, sha256
`6b633fcc35ae612f20f4028eb45aaca1b6ed86a24eb1304af555c46228325376`, 3729 lines
(newline-byte count, `wc -l` semantics), 237872 bytes. Measured in this run, not
copied. Slice: lines 3198-3729 (§11-§12). Auditor: CITECHECK re-run, P18,
2026-07-30. First audit ever to read these sections.

**Line mapping.** `assemble.py` prepends a 2-line banner and joins sections with
`\n\n---\n\n`. Within this slice:

| PAPER.md lines | section file | offset |
|---|---|---|
| 3198-3482 | `sections/11_limitations.md` 1-285 | `PAPER − 3197` |
| 3486-3729 | `sections/12_related.md` 1-244 | `PAPER − 3485` |

Verified empirically, not asserted: `all(PAPER[3197+i] == 11_limitations[i]` for
`i` in 1..285`)` is `True`, and the same for `−3485` over 12_related's 244 lines.
L3483 blank, L3484 `---`, L3485 blank. Every finding below gives both numbers.

**Rule under test.** "Every quantitative claim carries the repo-relative path of
the artefact it came from." Four passes: path existence, number verification,
orphan numbers, quote fidelity. Precedence: **JSON artefacts beat prose reports**
(`papers/phase1-workshop/CITECHECK.md`).

---

## Summary

| pass | measure | count |
|---|---|---|
| A | distinct path-like tokens cited in backticks | **52** |
| A | resolve as written, repo-relative from the tree root | **45** |
| A | resolve only under a section-implied base | **3** |
| A | resolve only after restoring a dropped extension / module→file | **2** |
| A | ambiguous bare filename (>1 candidate in tree) | **1** |
| A | absent by design, and the prose says so | **1** |
| A | do not exist anywhere in the tree | **0** |
| A | bibliography keys cited, resolving in `references.bib` | **65 / 65** |
| B | distinct numeric claims traced to a file and checked | **~95** |
| B | wrong, mis-attributed, or not present in the cited file | **9** |
| C | numbers with no citation at all, or a citation lacking them | **9** |
| D | attributed quotations checked (blockquotes + inline fragments) | **16** |
| D | inexact — emphasis dropped, truncated, or re-rendered | **4** |
| — | **flattering-direction findings** (hazard a) | **9** (4 high) |
| — | §12 external claims classified | **67** |

**Bottom line.** No path in the slice is broken and, unlike slice A, almost
nothing here is cited to the wrong base. The failure mode of a limitations
section is different and this one has it in quantity: **§11 is systematically
blind to §6 (A3) and §9 (the live chain)** — neither section, neither report,
neither incident is mentioned anywhere in §11 — and §11.5's closing sentence
disclaims "the bill shape, transfer, the exam, the cost magnitude" as
"unevidenced here and not claimed" while §6.2 is headed *The bill*, §6 is
transfer, §8 is the exam and §9.4 reports live spend. Beside that, four
disclosure clauses are materially weaker than the artefacts they cite: §11.1(d)
omits `CONTRACTS/dsl_grammar_v0.3.md` entirely (the paper never mentions it),
§11.4 reports one of the seven pre-registration defects `battery/PREDICTIONS.md`
records, §11.1(f) is the *contamination-grading* clause and reports no grading,
and §11.2's whole premise is a `CLAUDE.md` sentence deleted 33 hours before
§11's last edit. Both leads I was asked to test independently are confirmed.

---

## Pass A — path existence

52 distinct path-like references in lines 3198-3729. **None is broken.**

| cited as | PAPER.md line | section file:line | status |
|---|---|---|---|
| `A0P_REPORT.md` | 3345 | `11_limitations.md`:148 | base-relative; is `cold-start-a0/prime/A0P_REPORT.md`, cited in full at L3321 and L3337 |
| `BLOCKER_FAST_DOWNWARD.md` | 3392 | `11_limitations.md`:195 | base-relative; is `cold-start-a0/BLOCKER_FAST_DOWNWARD.md`, cited in full at L3375 |
| `fd_real.json` | 3387 | `11_limitations.md`:190 | base-relative; is `cold-start-a0/artifacts/fd_real.json`, cited in full at L3376 |
| `dsl_grammar_v0.1` | 3237 | `11_limitations.md`:40 | extension dropped; is `CONTRACTS/dsl_grammar_v0.1.md`. Same near-miss slice A flagged at L887 — so it is now twice in the paper |
| `prime.run_prime` | 3378 | `11_limitations.md`:181 | Python module path; is `cold-start-a0/prime/run_prime.py` |
| `theory.dsl` | 3245 | `11_limitations.md`:48 | **ambiguous** — 3 files carry the name (`a0-spike/theory/`, `cold-start-a0/theory/`, `cold-start-a2/theory/`). §11.1(d) means `cold-start-a0/theory/theory.dsl` |
| `.toolchain/` | 3388 | `11_limitations.md`:191 | absent, **correctly**: the sentence's own point is that it "is gitignored and not in the tree" |

The remaining 45 resolve exactly as written from the tree root, including the
long ones (`battery/runs/20260729T021247Z-V9-battery-gaming-audit/v9_gaming_audit.json`,
`engine-rig/interop/certificates/pagoda_5_11011_to_00010.json`,
`papers/phase1-workshop/runs/20260728T102014Z-P7/search-traces/`) and the
line-anchored one (`cold-start-a0/pipeline/plan_stage.py:59` — line 59 really is
`plan = fd_adapter.solve(domain, instance, prefer="stub")`).

**Bibliography.** §12 cites 65 distinct bib keys. All 65 resolve in
`papers/phase1-workshop/references.bib` (70 entries; 5 are unused in this slice:
`beasley1992pegsolitaire`, `cropper2021popper`, `evans2018dilp`,
`hubert2026alphaproof`, `trinh2024alphageometry`). Zero `[bib: TODO]` markers
remain in the slice.

One stale internal path, not counted above: every one of the eight
`search-traces/line*.md` files scopes itself to
`papers/phase1-workshop/sections/**11**_related.md` §8.2. The section is now
`12_related.md` §12.2 — the traces were written when related work was §8. Not a
broken link (§12 cites the directory, not the files), but a reader following the
trace's own scope line lands on the limitations section.

---

## Pass B — wrong, mis-attributed, or absent numbers

| # | § | PAPER / file line | paper says | the cited file says | severity |
|---|---|---|---|---|---|
| B1 | §11.2 | L3289-3290 / `11`:92-93 | "`CLAUDE.md` **states** that no game has been played and that all 25 are registered `never_audited`" | `never_audited` **does not appear in `CLAUDE.md`**. Commit `32059928` (2026-07-28 14:00) deleted "As of this writing no game has been played … all 25 are registered `never_audited`" and replaced it with a Status paragraph that already reports the play, the four `trajectories_reviewed` games, INC-BA-001's nine, and F-11. `11_limitations.md` was last edited 2026-07-29 23:03 — 33 hours later | **high** |
| B2 | §12.1 | L3536-3539 / `12`:51-54 | "**No arm of this paper was run against WorldCoder, Schema, or any other system.** This paper reports no comparison" | `battery/artifacts/discrimination_arms.json`: `gradient` = "bare_cc (weaker) vs schema_repro (stronger), paired by game", `arms_present` 2, `control_runs` 88, 38 metric verdicts. `capability_spectrum.json` `runs`: 8 `schema_repro` runs. §7.2 prints an eight-row cross-arm table of Cliff's δ. §11.4 calls the same arm "what let process 1 run on the gradient `Theoria.md` specifies". "Run *against*" is defensible (nobody executed the harness); "reports no comparison" is not | **high** |
| B3 | §12.2 | L3640-3641 / `12`:155-156 | "**Neither of those two engines is exercised by any result in this paper.**" | (a) §10.4 (`10_adjudication.md`:259-266 = PAPER L2993-3000) reports a census result about `engine-rig/engines/deadlock_carver/__init__.py`'s `PruningReport.same_answer` — computed, serialised, published beside the theorem it refutes, "**Now gated**". (b) `theory-compiler/STATUS.md`:15-21 — the file §11.1(b) and §11.3 both cite for A1 — is an acceptance table in which `deadlock_carver` carries two Lean-checked certificates (28,672 and 1,792 leaf goals; 60 s and 4.2 s; "九条全空") and `ic3_pdr` peg4 carries `inv_init`/`inv_closed`/`inv_all`/`unsolvable` on both the `computational` and `algebraic` routes. Also in tension with §12.2's own two preceding sentences, which state in the present tense what each engine "supplies" | **high** |
| B4 | §11.5 | L3473-3479 / `11`:276-282 | "37 of its 38 metrics driven to those thresholds and its main table **cut from nine to two** — and to zero by a sighted follow-up review (`battery/runs/…/v9_gaming_audit.json`)" | that JSON has `verdict.gameable` = 37 ✓ and `verdict.b14_baseline_main` = 9 ✓, but `verdict.main` = **`[]`** and `verdict.demoted_by_v9` = all nine including `M3`. The number **two appears nowhere in the verdict**; nine→zero is what the cited artefact reports directly. The nine→two→zero split is prose-only, in `battery/audit/v9/REPORT.md` §9(b) ("主表由 {E1, M3} 变成空集"), and rests on `E1` having been in the main table, which neither `gaming_audit.json` `main` nor `v9_gaming_audit.json` `b14_baseline_main` records | **medium-high** |
| B5 | §11.1(d) | L3238-3240 / `11`:41-43 | "A0's run produced an expressivity ledger of **five gaps** (`cold-start-a0/THEORIZE_LOG.md` §E: E-01 … E-05)" | that §E table has **nine** rows, E-01 through E-09 (`THEORIZE_LOG.md`:357-365), with E-06…E-09 each carrying a "see below" full write-up. The five is the ledger as first committed (`848d683a`, 2026-07-28 01:02); E-06 landed `406d69f1` and E-07/E-08/E-09 `4dd8e0f7`. §11.3 (L3357) itself cites E-06 *as a `THEORIZE_LOG.md` entry*, so the paper contradicts its own count 119 lines later. `E-07`, `E-08`, `E-09` appear **nowhere** in PAPER.md | **medium** |
| B6 | §11.3 | L3331-3332 / `11`:134-135 | "0 (A0), 0 (A0′ Run A) and 1 (A0′ Run B), **each** recorded as a `revisions` field in `cold-start-a0/prime/artifacts/prime_report.json`" | that file has exactly **two** `revisions` fields — `run_a.revisions: 0`, `run_b.revisions: 1`. A0's 0 is prose in `cold-start-a0/A0_REPORT.md`:173 ("The revision count is 0") and is not a field anywhere. Separately: both values in the JSON are **literals in the generator** — `cold-start-a0/prime/run_prime.py`:117 `run_a = {"revisions": 0}` and :169 `run_b["revisions"] = 1` — so "recorded as a field" is true and "measured" would not be | **medium** |
| B7 | §11.4 | L3424-3425 / `11`:227-228 | "There **is** a Schema arm — **8 runs** of released upstream trajectories … (`baseline-arms/SCHEMA_LOCATE.md`; `battery/DECISIONS.md` D-B-019)" | neither cited file carries 8. `SCHEMA_LOCATE.md` is about the harness; D-B-019 answers yes/no, not a count. The 8 is `battery/artifacts/capability_spectrum.json` `runs`, arm `schema_repro` (confirmed: 8; also `discrimination_arms.json` `control_runs` 88 = 80 + 8). §7.2 cites this correctly; §11.4's restatement drops the artefact | **medium** |
| B8 | §11.1(f) | L3282-3283 / `11`:82-83 | "Phase 4's exam items must now avoid those nine." | that is `baseline-arms/INCIDENTS.md`'s **recommendation 3** ("考卷子集…避开这 9 局"), explicitly handed to `arc-recon` and a human. The ruling actually made is F-11, recorded in `arc-recon/data/claim_set.json`: `claim_set_size` **19**, `quarantined` **2** (ls20, ft09), `retained_with_sensitivity_analysis` **7** — the seven are *retained* with a disclosure obligation, not avoided. Under the paper's own precedence rule the JSON governs. `F-11`, `claim_set` and `quarantin` return **zero** hits in PAPER.md | **medium** |
| B9 | §12.2 | L3589-3592 / `12`:104-107 | "That literature certifies tasks whose rules are **given**; here the rules were *induced* … so the LP's constraints are mined by `zero_space` and `cegis_miner` rather than read off a domain description" | true of A0/A2, false of the one certificate §12.2 exhibits three paragraphs earlier. `engine-rig/interop/certificates/pagoda_5_11011_to_00010.json` has `inv_closed.checked_over` = "**the 6 move instances this document lists**" — a 5-position peg-solitaire strip whose jump rules are given, not mined. The stated delta does not hold of the paper's own exhibited artefact | **low-medium** |

### Numbers checked and confirmed correct

Traced to the named field of the named artefact, not to a report:

* **§11.1(b)** — 59 (`cold-start-a0/artifacts/score_vs_truth.json`,
  `base.behavioural.reachable_states`); 57 (`prime_report.json`,
  `trace.a0p-base.reachable_states`); "55 reachable states, 148 in the Lean"
  verbatim in `cold-start-a2/A2_REPORT.md` §8; `theory-compiler/STATUS.md`:352-354
  carries the whole trade-off — `computational` empty-axiom at `O(2^n)`,
  `algebraic` linear with `propext, Quot.sound`, `2^33` on the 33-hole English
  board, D-TC-008, and "全部验证只跑在**一个** 5 格夹具上".
* **§11.1(c)** — 9/9, 3/3, 9/9, 9/9 all `"verdict": "PASS"` in
  `arc-recon/data/precheck.json`, in that game order (ar25, g50t, sk48, tn36),
  with `deterministic: true` and `cross_session_residue: false` on all four.
* **§11.1(f)** — nine sealed games in INC-BA-001's table, two graded 实质泄露
  (materially). Read as a count and a grade column only.
* **§11.2** — "4 局 × 3 模型 = 12 格，另加 sonnet 的 2 次重跑"; "109 个成功动作";
  "本轮新增成功动作 44 个" on `ar25`; `levels_completed` 0 throughout
  (`baseline-arms/TOUCHED_GAMES.md`); `baseline-arms/ledger.jsonl` = **560** rows,
  independently counted.
* **§11.3** — `upstream_pin.json` `sha256` map pins **22** files, `missing: 0`;
  the **258** is `cold-start-a2/A2_REPORT.md` §7 ("258 files, 0 changed") and the
  paper says so explicitly; `loop_ledger.json` L4 beat carries
  `re_derivable_from_grown_evidence: true` and **no** count, exactly as claimed;
  `engine-rig/tests/test_interop.py`:68 `assert unprovable == [0, 2, 4]` — three
  of five singletons; `CertificateGapError` in `theory-compiler/DECISIONS.md`:99
  (D-TC-010) superseded by D-TC-022:300; E-06 **discharged** in
  `THEORIZE_LOG.md`:362; `plan_stage.py`:59 `prefer="stub"`;
  `BLOCKER_FAST_DOWNWARD.md` title dated 2026-07-28; "still not connected" at
  `A0_REPORT.md`:155 and :201; "three failed compiler attempts" at :242 item 4.
* **§11.3's "every economy metric is `not-applicable` on the Theoria arm"** —
  recomputed: all 7 economy metrics on all 7 `theoria*` runs in
  `battery/artifacts/capability_spectrum.json` have `status:
  "not-applicable"`, `value: null`, reason "the run records no model calls" (E6:
  "no HTTP attempt count per step"). **Zero exceptions.**
* **§11.4** — `discrimination.json`: 38 metrics, 13 `underpowered` + 18 `no-data`
  = **31**, 7 `not-ranked` (E1, E6, K7, K11, M6, P5, X5). `discrimination_arms.json`:
  8 + 23 = **31**, the same 7 `not-ranked`. Both "31 of 38 / other 7" claims are
  right, and this closes CITECHECK's old high finding (which was against a
  29-metric file). `min_attainable_p: 0.125` present; `power` string carries the
  six-non-tied-games floor verbatim; `role` field confirms the ladder is
  secondary and `discrimination_arms.json` primary. `validation_material.json`:
  `n_unvalidated: 21`, `unvalidated` = all 14 K + all 6 M + P4 — exactly "the
  entire epistemic family, the entire mechanism family, and P4"; `control_arms`
  = `["bare_cc","schema_repro"]`. `battery/PREDICTIONS.md`: `[seen]` on A0 is
  K1, K2, K7, K8 in the v0 seal (":31") plus K14 "[seen for A0 and A2]" (":217")
  = five ✓. INC-BA-003 exists at `baseline-arms/INCIDENTS.md`:89.
* **§11.5** — `gaming_audit.json`: `n_demonstrated` 38, `n_disagreements` **17**,
  and exactly **14** of the 17 have `defended` in `fields_contradicted` ✓;
  `v9_gaming_audit.json` `verdict.gameable` = **37** of 38 (M3 the exception) ✓;
  "six recorded beats" = L1–L6 of `loop_ledger.json`'s 8 beats
  (`summary: {absent:0, fail:0, pass:8, total:8}`) ✓; "§1.2 states the five
  limits" ✓ (`01_intro.md`:110 "**Five limits, and none of them is small.**",
  and the amended adjudication rule is the third of them).
* **§12.1** — 98.98 % and +56pp both in `Theoria.md`:393 ✓. The Schema
  attribution is corroborated twice in-repo:
  `search-traces/line0-schema-attribution.md` (project-page BibTeX + a second
  independent source, "CONFIRMED, two independent sources") and
  `references.bib`:193-200, whose `note` says "No paper, no arXiv id, no DOI, no
  released harness code. Commonly mis-cited as ``Feng et al.''; Feng is the last
  author." `zeng2026schema`'s author list has Zeng first, Feng eleventh ✓.
* **§12.2** — `zero_space`'s description checks out line for line against
  `engine-rig/engines/zero_space/zerospace.py`:3-6 and :282-284 (one indicator
  per `(cell, colour)`, `encoded[t] ^ encoded[t+1]`, `gf2.null_space`).
  `lp_potential` "sound but incomplete" is `engine-rig/DECISIONS.md` D-014 ✓
  (the mis-citation to `engine-rig/STATUS.md` that CITECHECK found is fixed in
  both §11.3 and §12.2).
* **§12.3** — `papers/phase1-workshop/REVIEW.md`:371 is issue 14 and :388 names
  "Chow's W-method, Vasilevskii" as uncited priors ✓; `references.bib` contains
  no `vasilevskii` key, so "**not** cited here" is true of the bibliography ✓.
* **§12's process claim** — the eight `line*.md` traces exist and each opens with
  a two-independent-sources rule; `line5` records one DROPPED candidate, which is
  what "dropped rather than hedged" needs; `audit-sample-a.md` is a 20-record
  adversarial re-check reporting "24 CLEAN, 1 DEFECT, 0 UNVERIFIABLE" and five
  action items. **Two of those actions were carried out**: `references.bib`:185
  now reads "Hong, Joshua" / "Wang, Daisy" (action 1) and :133 uses PMLR's long
  name forms for Genie (action 3). The 13 bib keys absent from the traces by key
  name are all present in `line2-planning-certificates.md` by author and title
  (Berlekamp/Kiyomi/Eriksson/Pommerening/Seipp/Culberson/Edelkamp/Hoffmann/Helmert
  all hit), so the "one file per line" claim holds.

---

## Flattering-direction findings (hazard a)

A caveat stated more weakly than the artefacts warrant, or dropped between
drafts, is treated here as a finding of the same class as a wrong number.

### A-1 (high) · §11.1(d) reports two grammar versions where the tree has three

§11.1(d) is the pre-declared clause "语法脚手架披露 — disclose the grammar
scaffolding" (PAPER L3236-3248 / `11_limitations.md`:39-51). It says v0.1 was
frozen before A0, five gaps were logged, `CONTRACTS/dsl_grammar_v0.2.md` was
authored to close them, and closes: "The ledger is public, the grammar diff is
public, and v0.1 was not edited."

**`CONTRACTS/dsl_grammar_v0.3.md` exists** — Status 定稿, Effective 2026-07-28,
"**Supersedes:** `dsl_grammar_v0.2.md`" — and the string `v0.3` appears **nowhere
in PAPER.md**. Its stated reason is the same class of defect §11.1(d) itself
calls "the load-bearing disclosure": "This revision exists because v0.2 used a
word in a definition and never defined it." The word is `mentions`, in v0.2's
`frame persist` rule — the frame axiom, i.e. E-03 again — and v0.3 §1 tabulates
three inequivalent readings, of which R2 yields **376 mispredictions** over
a0-spike's 39,960 pairs and R3 yields 0. The forcing ledger entries are
`a0-spike`'s **X-1** and **X-5**; `X-1` and `X-5` also return zero hits in
PAPER.md.

So the clause whose entire subject is scaffolding movement understates the
movement by one version and omits the one revision forced by a measured
misprediction count. Two further contracts the clause does not mention:
`CONTRACTS/candidates_schema_v0.2.md` (beside the "frozen v0.1" schema §2.5
cites) and the two new certificate contracts
`CONTRACTS/{deadlock,ic3}_certificate_v0.1.md` — the latter written for exactly
the two engines §12.2 says are unexercised.

### A-2 (high) · §11.5's closing sentence disclaims four things the paper reports

PAPER L3481-3482 / `11_limitations.md`:284-285: "Everything else in `Theoria.md`
— the ordering claim, **the bill shape, transfer, the exam,** the cost magnitude
— is unevidenced here and is not claimed."

* **transfer** — §6 *is* A3 transfer. `06_a3_transfer.md`:5-8: "In the claim menu
  of `Theoria.md` §3.2 this is C3".
* **the bill shape** — `06_a3_transfer.md`:40 is headed "### 6.2 The bill" and
  prints a like-for-like table (world frames 347 → 11, ratio 0.032; world actions
  346 → 10, ratio 0.029) citing `cold-start-a3/artifacts/bill_table.md`.
* **the exam** — §8 is "The exam — four papers, **one sat**, and a check that did
  nothing".
* **the cost magnitude** — §9.4 "What was spent, in the end": 7 successful
  actions, 40 commands sent, 5 model calls, cited to
  `theoria-arm/runs/20260728T015354Z-g50t-first-contact/MANIFEST.json`.

Read literally, the last sentence of the limitations section denies that three of
the paper's twelve sections exist. Each of those sections *does* qualify itself
properly in place; §11 does not inherit the qualifications, it contradicts them.

### A-3 (high) · §11 never mentions §6 or §9 at all

Every `§n` cross-reference in `11_limitations.md` (grepped): §1, §3, §4, §5, §7,
§10. **No §6, no §9, no §12.** No `cold-start-a3/` path is cited anywhere in the
slice; no `theoria-arm/` path either. Consequences:

* §11.1(b) "Every world in this paper is tiny" enumerates A0 (59), A0′ (57), A2
  (55/148) and A1 (5-hole) and **omits A3's two 9×9 levels** — 62 and 63
  reachable states, which `06_a3_transfer.md`:174 lists as A3's own scale caveat.
* §11.1(e) "Every world in **§3–§5** was built by us" narrows the scope so that
  §6 falls outside the sentence rather than inside it. A3's world *is*
  self-built (`cold-start-a3/a3world/a3_world.py`), so nothing is gained by the
  narrowing except that §6 goes unmentioned.
* §11.3, "What the individual acceptances do not show", omits all six items of
  §6.5 — including "**the playbook's transfer is a design claim, not a
  measurement**: … no code path in A3 reads or compiles
  `cold-start-a3/theory/playbook.dsl`, and the byte-identity test its docstring
  cites **does not exist in the tree**", and "Three level constants were
  supplied, not derived".
* §11.3 also omits all four items of §9.3, "Four things the preflight does not
  establish" — including "**The spend gate did not gate this run**" and "**no
  conclusion about input-token composition may be drawn from this ledger**"
  (GAP 1, `proxied: false`).
* §11.4's data-integrity note names INC-BA-003 only. §9.4 records a *second*
  concurrency incident, INC-TA-001, of which it says "**every wall-clock and
  HTTP-amplification number this track reports is confounded**". §11.4 says "any
  aggregate read off that ledger inherits the incident" about one ledger and
  says nothing about the other.
* §11.3's theorize-step caveat says "done by hand here, **as in A0**". §6.5 item
  6 says "The theorize step is a person, here **as in A0 and A2**". A3 is the
  third instance and is not counted.

### A-4 (high) · §11.5 drops the sealing caveat the abstract carries — lead 1, confirmed

PAPER L3458-3460 / `11_limitations.md`:261-263: "that on those worlds a manual can
be perfect on replay and wrong about the world in a way that was **predicted in
advance and later measured**". No qualification.

The abstract states the same result *with* the caveat
(`00_abstract.md`:87-90): "The miss was written down in the adjudication log, by
direction, *before* the ground truth was opened — **though the seal on that
ordering is the authors' own declaration, and the same instance built the world
and adjudicated it.**" §11.3 (PAPER L3319-3323) states it a third time: "**The
seal has one hole, in the same place twice.** … that is weaker than a genuine
blind and the reports count it as a threat to the result rather than a
footnote."

Two things make this a finding rather than a compression. First, §11.5 is the
paper's tightest claim statement — "The one thing this paper claims", "Itemised,
and in the order a reader can check them" — so an item there is a headline, not a
summary. Second, the **immediately following item in the same list does carry an
inline qualification**: "an A0/A0′ contrast which is **not** controlled — the two
worlds differ in mechanism, rule count, state count and explorer budget at once,
so the outcome is entailed by the construction (§3.3) —". The list therefore
qualifies where it chooses to, and does not choose to here. As reported. Confirmed
from the artefacts and the abstract, not by echoing the lead.

### A-5 (high) · §11.4 reports one of seven pre-registration defects its own citation records

§11.4's entire pre-registration disclosure (PAPER L3433-3436 /
`11_limitations.md`:236-239) is: "the battery's author also wrote the metric
definitions, which is structurally impossible to blind; five metrics on A0 are
marked `[seen]` post-dictions in `battery/PREDICTIONS.md` … rather than being
passed off as predictions". Both halves verify. `battery/PREDICTIONS.md` — cited
in that sentence, last edited `be5987c1` 2026-07-29 11:33, **11½ hours before**
`11_limitations.md`'s last edit — additionally records, none of it in PAPER.md:

1. **"十三条预测已经被盘上现存的数据证伪，此前只报过两条"** (:528) — thirteen
   registered predictions already falsified by data already in
   `battery/artifacts/`, of which only two had been reported. The table names
   M5, K7, K10, K2, X1, X2, X6, K14 and v2's X1/X3/X4/P2/P3/E4.
2. **Three of the file's best-advertised predictions reclassified 「可满足但无信息」**
   (:551) — X3, P2 and K7 are each satisfied by a zero-capability arm ("撞墙卡死
   32 步，得 1.000"), and X3 is the exploration family's declared signature.
3. **Metric-definition drift after pre-registration** (:563) — E2's registered
   name `frontload_index_25` "**在 `battery/metrics/` 里从未存在**"; the axis was
   changed from model-call to decision in v1 and the head from `ceil` to
   interpolation in v2.1, with the file's own admission that "**every published
   E2 value moves**" — and E2 is a `Theoria.md` Phase 4 primary endpoint. E3's
   registered `convergence_turn_90` likewise "从未存在". Four further definition
   elements did not exist when the predictions naming them were written.
4. **None of `Theoria.md`'s three primary endpoints is pre-registered in the
   form it asks for** (:581) — U3 attainment is named by no prediction in the
   file; verdict accuracy has only synthetic-candidate blocks; the front-load
   index registers an *order* where `Theoria.md` asks for a **paired difference**
   (no quantity, no n, no α).
5. **The v2 seal declares two leaks** (:268-275) — upstream per-game outcome
   scores encoded in directory names, and per-game file counts and byte sizes.
   §7.3 mentions these; §11.4 does not.
6. **The v1 procedural discount** (:174) — "the discount applies to all nine rows
   below".
7. **A registered, unrepaired conflict with a frozen hash** (:598) — appending
   the recheck broke `BATTERY_V1.md`'s full-text hash; the file's own rule calls
   this "正当的工作、不正当的冻结" and requires a new freeze, which was not made.

Item 3 is the serious one: a definition changed after results were seen is
strictly worse than "structurally impossible to blind", and it is what §11.4
reports *instead of*. `frontload_index_25`, `convergence_turn_90`, 「可满足但无
信息」 and `BATTERY_V1` all return zero hits across `sections/*.md`.

### A-6 (medium) · §11.1(f) is the contamination-grading clause and reports no grading

The clause transcribed at PAPER L3259-3260 / `11_limitations.md`:59-60 is
"封存堆污染**分级**与预训练先验" — contamination *grading*. §11.1(f) reports two
incidents and a prior, and never reports a grading. Absent from §11.1(f) and from
the whole paper:

* the level ladder itself (`never_audited` / `blurb_glimpsed` /
  `design_document_disclosed` / `trajectories_reviewed`) — only two levels are
  named, in passing, inside the INC-004 bullet;
* the **F-11 ruling** and the reduction of the held-out claim set from 21 to
  **19** (`arc-recon/data/claim_set.json`: `claim_set_size` 19, `quarantined`
  `[ls20, ft09]`, `retained_with_sensitivity_analysis` 7 of 7);
* the **standing obligation** those artefacts impose: "every statistic over the
  claim set must be reported a second time with the seven retained-but-disclosed
  games excluded (sensitivity analysis); **if the two disagree, the weaker figure
  governs**" (`arc-recon/data/contamination_log.jsonl`, the F-11 entries);
* the residual question `claim_set.json` flags for the owner about the A2 game:
  "the ruling's stated basis is that a *material* leak of mechanics is
  unrepairable, and `design_document_disclosed` is mechanics prose … **Calling
  dc22 'minor-exposure' is therefore wrong** even though retaining it is what the
  ruling says. It is the most exposed game inside the claim set and the first to
  move under sensitivity analysis." §11.1(f)'s INC-004 bullet presents that
  game's grade as settled;
* that the A2 game has **two** independent exposure routes, not one — the design
  document *and* one of INC-BA-001's nine ("**它也在 INC-BA-001 的九次一瞥之
  中**"). §11.1(f)'s first bullet gives only the design-document route.

`F-11`, `claim_set`, `quarantin` and "sensitivity analysis" in this sense: zero
hits in PAPER.md.

### A-7 (medium) · §11.2's premise is stale

See B1. The *substance* of §11.2 verifies completely (12 cells, 2 reruns, 109
actions, 44 more, 560 rows, `levels_completed` 0 throughout). What is stale is
the framing: the subsection is titled "A correction to the repository's own
summary" and closes "it is corrected here because a paper that repeated
`CLAUDE.md`'s sentence would be repeating something false" — of a sentence
`CLAUDE.md` no longer contains, and whose replacement carries the F-11 /
claim-set-19 information §11.1(f) omits. The file being corrected is now more
complete on contamination than the clause correcting it.

### A-8 (low) · §11.5 uses the frozen exploit figures and not the recomputed ones

§11.5 reports "contradicted 17 of its own register entries by demonstration — 14
of them defence claims (`battery/artifacts/gaming_audit.json`)". Correct against
the frozen artefact, and correct under the precedence rule. §1.2
(`01_intro.md`:144-149) additionally records that "re-running the same code
against the tree as it now stands gives **33** exploits landing and **19**
contradicted entries rather than 34 and 17"
(`battery/runs/20260729T025515Z-V18-battery-prereg-check/recompute/gaming_audit.json`).
The limitations section takes the flatter number without the bookkeeping note the
introduction carries.

### A-9 (low) · "five metrics … marked `[seen]`" is true and narrowly scoped

`battery/PREDICTIONS.md` marks **eleven** metrics `[seen]` across arms — K1, K2,
K7, K8 (A0), K14 (A0 and A2), K12, K13 (A2), M4, M5, M6 (a0-spike) and E6 (every
ARC arm). "Five metrics **on A0**" is exactly right; the paper does not say how
much larger the post-diction set is once other arms are counted, and §11.4 is the
place a reader would look for that.

---

## Pass C — orphan numbers

| # | § | PAPER / file line | the claim | what it would need |
|---|---|---|---|---|
| C1 | §11.5 | L3467 / `11`:270 | "the refutation loop closed on a false theorem in **six** recorded beats" | a path. It is `cold-start-a2/artifacts/loop_ledger.json`, `beats` L1–L6 of 8 (`summary.total: 8`) — cited 202 lines earlier, in a different subsection, for a different purpose. The abstract, which is exempt, gives the fuller "L1–L6 of an eight-beat ledger"; §11.5 gives neither the path nor the eight |
| C2 | §11.5 | L3464-3466 / `11`:267-269 | "whose **empty axiom list** is a check that has been made to fail on purpose" | a path. The negative control is `theory-compiler/STATUS.md`:343-346 (`w .p1` 1→7, four theorems become `[sorryAx]`, exit 1) |
| C3 | §11.3 | L3348-3350 / `11`:151-153 | "**Three of the five** singleton end states are pinned by `engine-rig`'s own tests as *not derivable*" | a path. `engine-rig` is named as a track, not a file. The assertion is `engine-rig/tests/test_interop.py`:68, `assert unprovable == [0, 2, 4]`. The citation actually attached to the sentence is `theory-compiler/STATUS.md` / D-TC-010 |
| C4 | §11.3 | L3311-3316 / `11`:114-119 | "**every** economy metric is `not-applicable` on the Theoria arm" | the artefact. The only path attached is the prose `battery/REPORT_V0.md`, quoted for a different sentence. The universal quantifier is checkable — and true — only in `battery/artifacts/capability_spectrum.json` (7 metrics × 7 theoria runs, all `not-applicable`). The paper's own precedence rule says the JSON should be the citation |
| C5 | §11.4 | L3419-3420 / `11`:222-223 | "a smallest attainable p of **0.125**" and "**six** non-tied paired games is the floor" | field names. Both inherit L3416-3417's two paths, but the values live in `metrics.*.min_attainable_p` and the top-level `power` string, neither named. §11.4 names fields elsewhere (`n_unvalidated`-style), so the omission is local |
| C6 | §11.4 | L3437-3439 / `11`:240-242 | "a count that adding a whole second control arm **moved by zero** (`validation_material.json`)" | a *second* path. The artefact gives the current state (`n_unvalidated: 21`, `control_arms` of 2) and nothing about the previous count. The before/after is `battery/REPORT_V1.md` → `REPORT_V2.md`, which §7.3 cites and §11.4 does not |
| C7 | §11.1(b) | L3222 / `11`:25 | "Lean's `decide` is affordable at these sizes and will not be at **10⁶**" | nothing — rhetorical, and reads as such |
| C8 | §11.5 | L3463, L3477-3478 / `11`:266, 280-281 | "(§3.3)", "(§7.7 … §1.2)" | paths. Internal section refs standing where the binding rule asks for artefacts. Defensible by the abstract's convention, but §11.5 is body text |
| C9 | §12 | L3491-3492 / `12`:6-7 | "**one file per line** below" | the directory has 8 `line*.md` files for 9 thematic blocks: `line5-pcc-spec-validity.md` covers both the proof-carrying-code paragraph and the specification-validity paragraph. Not wrong; not one-to-one either |

One paragraph that looks orphaned and is not: §11.1(b)'s whole trade-off block
(`O(2ⁿ)`, `2³³`, 33-hole board, `propext`, `Quot.sound`, D-TC-008) inherits the
`theory-compiler/STATUS.md` citation on L3221-3222, which carries all six figures
in one paragraph at :350-354.

---

## Pass D — quote fidelity

16 attributed passages checked — 3 blockquotes / tables and 13 inline attributed
fragments. Four are inexact.

| # | § | PAPER / file line | quoted as | source | problem |
|---|---|---|---|---|---|
| D1 | §11.3 | L3307-3309 / `11`:110-112 | blockquote "Nothing about whether an LLM would have written these manuals. The theorize step is done by hand here, as in A0 — the DSL files are checked in as artefacts. A2 tests the instrument and the loop, not the theorizer." | `cold-start-a2/A2_REPORT.md` §8 | **213 of 213 characters match after removing two `**` pairs.** The source is a list bullet whose first sentence is bold: "* **Nothing about whether an LLM would have written these manuals.** The theorize step…". Emphasis and bullet silently dropped; wording verbatim |
| D2 | §11.3 | L3390-3391 / `11`:193-194 | FD "could not be built (three failed compiler attempts)" | `cold-start-a0/A0_REPORT.md`:242 | source reads "could not be built (three failed compiler attempts, `STATUS.md`)". The paper closes the parenthesis one token early, dropping the source's own citation from inside its own parenthetical |
| D3 | §12.1 | L3543-3545 / `12`:58-60 | the three-wave table, captioned "— reproduced from `Theoria.md` §3.1" | `Theoria.md`:397-401 | faithful in 14 of 15 cells. The exception is the wave-III **representatives** cell: source `本文` = "this paper"; paper "**this line of work**". A self-designation is broadened into a designation of a research line, in the row that also claims "true of everything". Rows I and II keep their representatives verbatim, so the change is confined to the authors' own row |
| D4 | §12.2 | L3569-3571 / `12`:84-86 | "It is **sound but incomplete**: it never certifies a solvable configuration, **and** some genuinely unsolvable ones admit no *linear certificate*" | `CLAUDE.md` / `engine-rig/DECISIONS.md` D-014 | §11.3 (L3364-3366) quotes the same sentence exactly and says the phrasing is `CLAUDE.md`'s; §12.2 re-renders it (`and` for `but`, "linear certificate" for "linear pagoda") without marking it as a paraphrase. Neither is inside quotation marks, so this is an internal inconsistency rather than a misquotation |

### Quotes verified exact

* `battery/REPORT_V0.md` "A0 ran engines and hand adjudication with no LLM in the
  loop, so it has no model calls" (PAPER L3311-3313) — byte-exact.
* `Theoria.md`:395 "若预测本身就是理解,第一波已经赢了" (PAPER L3534 /
  `12`:29-30) — byte-exact **including the half-width comma**. This closes
  CITECHECK's §8.1 punctuation finding: §12 transcribes the source's half-width
  punctuation, where the old §8.1 normalised it to full-width.
* `cold-start-a0/A0_REPORT.md` "still not connected" (§5 table :155 and §6 :201)
  — exact, both sites, as attributed.
* `cold-start-a2/artifacts/loop_ledger.json`
  `re_derivable_from_grown_evidence: true` — exact field and value.
* `CertificateGapError`, `goal count(Peg, alive) = 1`, `prefer="stub"`,
  `scope_exhaustive`-adjacent identifiers, `[seen]`, `not-applicable`,
  `design_document_disclosed`, `never_audited` — all exact as identifiers.
* `theory-compiler/STATUS.md` "「空公理集」与「证明规模线性」不同时为真" is
  rendered as an English paraphrase ("**not simultaneously available**") and
  presented as a paraphrase, not a quotation. Correct handling.
* `baseline-arms/INCIDENTS.md`'s 「读了就全污染」 / 「按目录名精确挑出开发堆 4
  局」 becomes "a read-it-and-you-contaminate-everything object whose only safe
  use is directory-name-exact selection of development-pile games" (PAPER
  L3279-3282) — a faithful paraphrase, presented as one.
* `search-traces/line5-pcc-spec-validity.md` carries Dijkstra's sentence
  ("Program testing can be used to show the presence of bugs, but never to show
  their absence!") verbatim as §12.2 quotes it. The *source* of that sentence is
  external and was not consulted.
* §12.3's instruction "the abstract should not read as though it were" is met:
  `00_abstract.md`:107-108 says "That is a demonstration of a failure mode, not
  evidence about anything." The abstract does not carry §12.3's stronger point
  that the outcome is "analytically guaranteed by the construction".

---

## §12 classification — claims about other people's work

The deliverable for §12. **67** distinct claims classified. Nothing was looked up
online; classification (ii) is precisely the set that could not be.

| class | count |
|---|---|
| **(i) checkable against a repo artefact** | **22** |
| **(ii) characterisation of external literature this repo cannot verify offline** | **30** |
| **(iii) stated so broadly it is not falsifiable** | **15** |

### (i) checkable against a repo artefact — 22

Includes the whole Schema-attribution block (project page, no venue / arXiv /
DOI / harness code; Zeng not Feng; Feng last author; 98.98 %/+56pp are
`Theoria.md`'s summary) — corroborated by `line0-schema-attribution.md`,
`references.bib`:193-200 and `baseline-arms/SCHEMA_LOCATE.md`; the
`lecun2022path` "unrefereed position paper" caveat (`audit-sample-a.md` record 9,
"CLEAN (no venue, no DOI — correctly so)", and a bib entry with no venue); every
claim §12.2 makes about this repo's own engines; "This paper runs no LLM-based
prover … no result depends on neural proof search"; the Vasilevskii
non-citation; the process claims in §12's preamble; and all 65 bib keys.

**Two of the 22 are false** — B2 ("This paper reports no comparison") and B3
("Neither of those two engines is exercised by any result in this paper") — and
**one is false of the artefact it exhibits** — B9. Being checkable is what made
them findable; the (ii) set carries no such guarantee.

### (ii) unverifiable offline — 30

Ha & Schmidhuber's latent transitions and controller-in-its-own-dream;
`ha2018recurrent` as the refereed companion under a different title; MuZero
"given no rules … deliberately predicting only what search needs"; WorldCoder's
write-and-repair-Python loop and its consistency requirement; RAP's forward-pass
world model; Schema's replay-the-entire-recorded-history check;
`brooks2024sora`'s "own scope statement excludes implementation details";
potential heuristics as LP lower bounds; operator counting recovering heuristic
families as LPs; the pagoda function's introduction in *Winning Ways* to prove
peg-solitaire configurations unreachable; `kiyomi2001pegsolitaire` as its LP
relaxation; unsolvability claims once taken on trust; certificate formats and
then a proof system built to close that gap; two-valued collapse as a known
move; sketching / SyGuS / CEGIS characterisations; the version-space ancestry;
`cropper2022ilp30`'s axes; `yang2007arms` as the action-model-learning problem;
Petri place invariants as the left null space of the incidence matrix; the
IC3/PDR lineage; siphon-based deadlock prevention; the older model-checking
line's given-model assumption; PCC and certifying-algorithms ancestry; Appel's
accounting question; the Dijkstra attribution itself; V&V and the
`boehm1984vandv` / `demillo1979social` / `fetzer1988veryidea` arguments
predating this work; `ammons2002mining`'s 2002 claim; the LLM+ATP list as
feasibility basis and checker source; autoformalisation's statements translating
an original that already denotes; Angluin's reset assumption; Chow's W-method
rationale.

**One flag inside this class.** §12's preamble asserts "Every citation in this
section was cross-verified against **two independent sources**". For
`brooks2024sora`, `audit-sample-a.md` records the opposite: "CLEAN (primary page
403 to me; **secondary corroboration only**)", with action item 4 still
outstanding — "Whoever finalises the bibliography should open it in a browser
once and confirm the 13-name contributor list against the page itself, since I
could only reach it through secondary citations." §12.1 leans on that record for
a substantive claim ("whose own scope statement excludes implementation
details"). The trace's own hedge is not carried into §12. Separately,
`liang2023codeaspolicies` was verified CLEAN (record 13) and then dropped from
`references.bib` — the preamble's dropping rule is stated for records that could
*not* be confirmed twice, so this direction is undocumented.

### (iii) not falsifiable as stated — 15

1. **The wave-III table row** (PAPER L3545 / `12`:60): "| III | **formal theory**
   | replay + proof + active experiment | **true of everything (and refutable by
   reality)** | this line of work |". **Lead 2's sibling, confirmed and worse
   than reported.** Three problems, compounding. (a) "true of everything" over
   "this line of work" is a claim with no possible counterexample procedure. (b)
   The source says `本文` — *this paper* — so the generalisation to a line of work
   is the paper's own (D3). (c) The paper's **title** is "**Neither layer
   certifies the manual against the world**" (`00_abstract.md`:1 / PAPER L3), and
   §5.6's exhibit is a Lean-checked impossibility theorem that is false of its
   world. The regime the row credits with carrying "true of everything" is the
   one the paper's headline result says certifies nothing against the world.
   §12.1's prose then re-asserts it in the paper's own voice at `12`:64-68 ("The
   regime decides what the model may carry … 'True of everything' … is what
   neither carries"), which removes the "reproduced from `Theoria.md`" defence
   for the surrounding paragraph.
2. "What these predictions never pass through is a checkable concept; the model
   is weights, with nowhere inside it to audit" (`12`:31-33) — universal negative
   over an entire wave.
3. "'True of everything' … is what **neither** carries" (`12`:64-68) — universal
   negative over waves I and II.
4. "PlaNet and the Dreamer line made planning in imagination a **mainstream
   method**".
5. "made frame-by-frame prediction **increasingly convincing**".
6. "Schema **pushed the wave to its ceiling**".
7. "no reproduction of it exists here **or anywhere**" — unbounded. Note also
   that the arm the artefacts carry is literally named `schema_repro`, and
   `battery/DECISIONS.md` D-B-019 is the file that draws the distinction
   ("can we *run* Schema and get our own reproduction score? **no**"); §12.1
   states the conclusion without the distinction that makes it true.
8. "differing **mainly** in what they may see".
9. "it is the **closest published analogue** of what this engine does".
10. "by that survey's axes this work occupies an **unremarkable corner**".
11. "the honest name for that object is a version space — **an ancestor, not a
    contrast**".
12. "it is why an LLM proposing a formal statement that a machine then checks is
    a buildable loop **at all**".
13. "That work proves theorems inside a *given* formal library … where the
    statement is supplied and **correct by construction**".
14. "Autoformalisation is the **nearest neighbour**".
15. "**the oldest caveat in the field**".

---

## Source disagreements

| # | the two sources | what they disagree about | which the paper followed |
|---|---|---|---|
| 1 | `battery/runs/…/v9_gaming_audit.json` **vs** `battery/audit/v9/REPORT.md` §9(b) | JSON: `b14_baseline_main` 9, `demoted_by_v9` all 9 including M3, `main` `[]`. Report: post-blind main was `{E1, M3}` (two), emptied afterwards by a sighted review. The JSON also never has E1 in `main` at all (nor does frozen `gaming_audit.json`); the report explains this at :188 as E1's baseline having flipped `reference`→`main` after its B14 exploit | **the report** — §11.5 and §1.2 both take nine→two→zero. Under the paper's own precedence rule the JSON wins and the chain is nine→zero. See B4 |
| 2 | `arc-recon/data/claim_set.json` + `contamination_log.jsonl` (F-11) **vs** `baseline-arms/INCIDENTS.md` recommendation 3 | ruling: 2 quarantined, 7 retained inside a 19-game claim set with a sensitivity-analysis obligation. Recommendation: exam items should avoid all nine | **the prose recommendation** — §11.1(f). The JSON ruling, the claim-set size and the standing obligation appear nowhere in the paper. See B8, A-6 |
| 3 | `cold-start-a0/THEORIZE_LOG.md` §E (nine entries) **vs** §11.1(d)'s "five gaps" | the ledger grew from five to nine between 2026-07-28 01:02 and 2026-07-29 01:52. §11.3 cites E-06 from the same file; E-07/E-08/E-09 appear nowhere in the paper | **the ledger's first state.** Defensible as "A0's run produced", presented as the whole ledger. See B5 |
| 4 | `CONTRACTS/dsl_grammar_v0.3.md` **vs** §11.1(d) | v0.3 exists, supersedes v0.2, and is forced by an undefined word in v0.2's frame-persist rule (376 mispredictions on one reading) | **§11.1(d) stops at v0.2.** v0.3 is unmentioned in the entire paper. See A-1 |
| 5 | `CLAUDE.md` (as of `32059928`, 2026-07-28 14:00) **vs** §11.2 | CLAUDE.md no longer contains the sentence §11.2 exists to correct, and its replacement carries the F-11 ruling §11.1(f) omits | **§11.2 addresses the deleted sentence in the present tense.** See B1, A-7 |
| 6 | `battery/PREDICTIONS.md` (recheck sections, 2026-07-29 11:33) **vs** §11.4 | seven further pre-registration defects, including post-hoc definition changes to a Phase 4 primary endpoint | **§11.4 reports the weaker, older caveat.** See A-5 |
| 7 | §12.2 (`12`:155) **vs** §10.4 (`10`:259-266) and `theory-compiler/STATUS.md`:15-21 | whether `deadlock_carver` and `ic3_pdr` are exercised by any result | **§12.2 asserts they are not**, in absolute form, in the same paragraph that describes what they supply. See B3 |
| 8 | §12.1 (`12`:52-54) **vs** §7.2 and `discrimination_arms.json` | whether this paper reports a comparison against Schema | **§12.1 says it reports none**; §7.2 prints eight rows of cross-arm Cliff's δ. See B2 |

---

## Sealed-pile discipline

**Clean, with one artefact-level note.**

* The slice contains **zero** ARC game-id-shaped tokens (`[a-z0-9]{4}-[0-9a-f]{8}`)
  — scripted over lines 3198-3729, empty result — and therefore names no sealed
  game and no development-pile game by id.
* §11.1(f) discusses the sealed pile at length and deliberately does **not** name
  the A2 game: "The upstream game named in `Theoria.md`'s A2 item is in the
  sealed pile". The elision is cosmetic within the paper — the name (`DC22`)
  appears 13 times in §5 (PAPER L393, L1114-L1178), which is outside this slice
  and belongs to slice B.
* Nine sealed games are counted, and none named, in §11.1(f).
* **Artefact note.** Two artefacts cited by this slice name the sealed A2 game:
  `cold-start-a2/artifacts/loop_ledger.json`'s `authority` string ("a self-built
  world isomorphic to DC22's failure structure"), and — reached while verifying
  B8 — `arc-recon/data/claim_set.json` / `contamination_log.jsonl`, which carry
  `dc22-fdcac232` with its grading note. Both were read for the *ruling and the
  grade*, never for mechanics.
* `baseline-arms/INCIDENTS.md` INC-BA-001 was opened to verify the count "nine …
  two of them materially". I read the game-id column and the self-assessed
  leakage-grade column and stopped there. **No mechanics description for any
  sealed game was read**, and the paragraphs of that incident that discuss
  upstream artifact structure were read only for the institutional consequence
  §11.1(f) paraphrases.
* No sealed game was played, inspected, or read about. Zero API calls. Zero
  network requests. No external paper, page or DOI was looked up: every claim
  about external literature was classified rather than verified, and the only
  records consulted for it were the in-repo search traces.

---

## What I could NOT check, and why

1. **Every (ii)-class claim in §12 — 30 of them.** Characterisations of
   Ha & Schmidhuber, Dreamer, MuZero, Genie, JEPA, Sora, WorldCoder, RAP,
   Schema, potential heuristics, operator counting, LM-cut, PDBs, *Winning
   Ways*, Kiyomi, Eriksson, Hoffmann, Fast Downward's paper, Sketch/SyGuS,
   Mitchell, Lau, Muggleton, Cropper, ARMS, Petri, Murata, Colom, IC3/PDR,
   Ezpeleta, Clarke, Queille, McMillan, Necula, Appel, McConnell, Blum,
   Dijkstra, Boehm, DeMillo, Fetzer, Ammons, the LLM+ATP line, Lean/Mathlib,
   autoformalisation, Angluin, Chow. **Reason: zero-network is a hard constraint
   of this audit.** What I could and did check is the in-repo *record* of the
   external verification — the eight `search-traces/line*.md` files, the two
   audit samples, and `references.bib`. Those confirm that a two-source
   procedure was run and that its action items were applied; they cannot confirm
   that any external work says what §12 says it says.
2. **`brooks2024sora`'s scope statement**, specifically. The repo's own auditor
   could not reach the primary page either (403), and left an action item asking
   a human to open it in a browser. Neither of us can close it offline.
3. **Whether `theory-compiler/STATUS.md`'s `ic3_pdr` / `deadlock_carver`
   acceptance rows were produced by a run this paper reports.** I established
   that the rows exist, carry compile times and leaf-goal counts, and sit in the
   file §11.1(b) and §11.3 cite — enough to make §12.2's absolute claim
   unsupportable as written. Deciding whether "exercised by a result *in this
   paper*" is meant to exclude a §10 census finding and a `theory-compiler`
   sprint acceptance is an editorial call, not an audit one.
4. **Whether §11.1(a)'s "This paper reports no cost comparison between arms" is
   exhaustively true.** I verified the economy family is `not-applicable` on all
   seven Theoria runs, and that §6.5 declares A3's bill "structural, not
   economic". But §9.4 reports live spend, and §7.2's E4 row carries a real
   cross-arm effect size. Adjudicating "cost comparison" against those needs a
   definition the paper does not give.
5. **Lean-checking anything.** No `lean` toolchain was invoked; `.toolchain/` is
   gitignored, as §11.3 says. The axiom-list and leaf-goal figures in
   `theory-compiler/STATUS.md` were read, not reproduced.
6. **Whether §11.4's "moved by zero" held historically.** `validation_material.json`
   records only the current `n_unvalidated: 21`. The previous count is in
   `battery/REPORT_V1.md` prose, which §11.4 does not cite (C6). I checked the
   current state and §7.3's account of the change, not the v1 artefact.
7. **Slice-external corroboration.** Where I read §1.2, §5, §6, §7, §8, §9 and
   §10 it was to test §11's and §12's claims *about* them. Those sections belong
   to slices A, B, C and D1 and are not audited here.

---

## Audit method

Pass A was scripted: every backtick span in lines 3198-3729 was extracted,
filtered to path-like tokens (containing `/`, or ending in one of eleven
extensions), then tested with `os.path.exists` at the worktree root and against
18 candidate bases; bib keys were extracted by the pattern
`` `[a-z][a-z0-9]*\d{4}[a-z0-9]*` `` and diffed against `@type{key,` in
`references.bib` and against the concatenated search traces. Pass C was
scripted for paragraph-level orphans and then done by hand at claim level over
the full numeric-token inventory of the slice (printed line by line). Passes B
and D were manual: each cited artefact was opened (UTF-8; several sources are
Chinese) and the value read from the named field. Recomputed rather than read:
the file digest, line count and byte count; the `discrimination.json` and
`discrimination_arms.json` verdict histograms; the `gaming_audit.json`
`fields_contradicted` count; the `v9_gaming_audit.json` verdict-list lengths; the
per-arm run census in `capability_spectrum.json`; the economy-family
`not-applicable` sweep across all Theoria runs; the `validation_material.json`
family breakdown; the `ledger.jsonl` row count; the two `theory.lean` files'
diff; and the `11_limitations.md` / `12_related.md` line-offset identity over all
529 lines. Git history was consulted (`git log -S`) only to date four files
relative to §11's last edit.

Scripts were run inline and not saved. Nothing outside this file was modified;
nothing was committed or pushed.
