# Row-level sample audit of the four `complete` citecheck slices

**What this is.** An independent sample re-verification of individual rows in
`citecheck-A-abstract-to-s3.md`, `citecheck-B-s4-to-s6.md`,
`citecheck-D1-s9-to-s10.md` and `citecheck-D2-s11-to-s12.md`. Those four are
marked `complete` in this directory's `MANIFEST.json` on a **structural** check
(four pass sections + a limits section + enumerated rows + no in-progress
marker). Nobody but each slice's own author had ever re-verified a row. This
file tests whether the rows are *true*, not whether they are *present*.

Auditor: independent sampler, P18, 2026-07-30. Worktree
`.worktrees/p18-audits-cover-half-the-paper`, branch
`agent/p18-audits-cover-half-the-paper`. No git write command was run and no
slice file was edited.

---

## Sampling method — declared before the results

The frame is every enumerated row in the four slices: Pass A path rows, Pass B
findings, Pass C orphan rows, Pass D quote rows, the named load-bearing
findings, D2's "flattering-direction" A-rows, and the bulleted items in each
slice's *Numbers checked and confirmed correct* section.

The draw is **deliberately weighted, not random**, on the stated priority order:

1. rows the slice itself calls load-bearing, high, or high-severity;
2. rows asserting a specific integer, ratio or exact quoted string (the ones a
   reader can falsify, and therefore the ones a binding stamp is vouching for);
3. rows in the *confirmed correct* subsections — sampled deliberately, because a
   false confirmation is more dangerous than a false finding: nothing downstream
   re-checks it;
4. rows where two slices touch the same artefact, so a cross-slice contradiction
   would show.

Cosmetic/very-low rows were deliberately under-sampled; a wrong "very low" row
does not threaten a binding stamp, a wrong "high" row does.

Quotas: ≥5 rows per slice, ≥24 total. Actual draw: **31 rows** (A 9, B 8,
D1 7, D2 7).

### The exact rows drawn, listed before any of them was checked

**Slice A (9):**
- A/B1 — §3.3 "from above, from below and from the right" (medium-high, the
  slice's sharpest finding)
- A/B2 — §3.2 `engines_report.json` 5704 vs 5284 (medium)
- A/B3 — §1.2 eighteen/nineteen and the §7.7 cross-reference (medium)
- A/B4 — draft-status "roughly 27 500 words" vs a recomputed 36 242 (medium)
- A/B7 — §3.1 "eleven other quantities" vs `PARITY.md` (low)
- A/load-bearing (c) — the **withdrawn** finding: the §1.2 38-metric
  five-family split (the fabrication this ticket's brief cites as precedent)
- A/load-bearing (b) — *confirmed correct*: the §1.5 95-runs / five-arm census
  and the 88/7 split
- A/confirmed — the §3.1 28-vs-29 candidate gap
- A/D2 — quote fidelity: `cards.K2.definition` case alteration

**Slice B (8):**
- B/B1 — §6.1 "35 lines" vs a real `diff` (medium-high)
- B/B4 — §6.3 "13 anomalies, 8 of 891 pixels" in files the paper never cites
  (medium)
- B/B6 — §4.4 BFS reachable set of four vs five (medium-low)
- B/B3 — §4.2 83/75/8 tests vs 364 collected (medium)
- B/D5 — quote fidelity: "missing rule, not wrong rule" sourced to the wrong
  file
- B/confirmed — §5.6 the 52-line Lean diff and its 28+8+2+2+12 decomposition
- B/confirmed — §6.1 eight placed cells, all eight moved; 62/63 reachable
- B/confirmed — §6.5 the playbook byte-identity test that does not exist

**Slice D1 (7):**
- D1/B1+B2+B3 — §10.2's `worldgen/core/truth.py` staleness cluster: "byte-for-
  byte unchanged on the mainline", "13 of 35" → 0 of 35, and the two quoted
  strings (all three **high**)
- D1/B4 — §10.4 `scope_exhaustive` / E15 (**high**)
- D1/B5 — §9.2 guard fingerprint attributed to a manifest with no guard block
- D1/B8 — §10.3 "28 distinct Python sites" vs 27
- D1/B10 — §10.7 six vs five work items
- D1/D1 — the `proxy/DECISIONS.md` blockquote paraphrase (**high**)
- D1/confirmed — §10.6's self-census: "verified" occurs eight times outside
  §10, at eight named lines

**Slice D2 (7):**
- D2/B1 — §11.2 `CLAUDE.md` "never_audited" (**high**)
- D2/B3 — §12.2 "neither engine is exercised" (**high**)
- D2/B5 — §11.1(d) five gaps vs nine E-rows (medium)
- D2/B7 — §11.4 "8 runs" absent from both cited files (medium)
- D2/A-1 — `CONTRACTS/dsl_grammar_v0.3.md` and the 376 mispredictions (**high**)
- D2/confirmed — §11.3 "every economy metric is `not-applicable`", 7 × 7, zero
  exceptions
- D2/confirmed — Pass A's bibliography row: 65/65 bib keys resolve, 70 entries

---

## Preliminary: the files audited are the pinned ones

Recomputed in this worktree. All four `complete` slices match `MANIFEST.json`
byte for byte:

| slice | sha256 | bytes | lines |
|---|---|---|---|
| A | MATCH | 70908 ✓ | 810 ✓ |
| B | MATCH | 48343 ✓ | 536 ✓ |
| D1 | MATCH | 58103 ✓ | 607 ✓ |
| D2 | MATCH | 54642 ✓ | 706 ✓ |

And the audited state all four slices declare for the paper is correct:
`PAPER.md` sha256 `6b633fcc…25376`, 237872 bytes, 3729 newline-bytes —
recomputed. Regenerating `PAPER.md` from `sections/*.md` in memory reproduces
the file on disk exactly (13 sections), so all four slices' line-mapping method
is sound, not merely asserted.

---

## Results

**Tally: 31 of 31 sampled rows hold. 0 wrong, 0 overstated, 0 unverifiable.**
Plus 9 further rows checked opportunistically in the course of the above, all
holding, listed at the end. The one defect found is not in a row — it is in the
`MANIFEST.json` count that established `complete`, and is recorded in
*Findings outside the sample* below.

### Slice A — 9 of 9 hold

**A/B1 (§3.3, "from above, from below and from the right") — HOLDS, and it is
the real thing.** PAPER L750-751 reads exactly as quoted.
`cold-start-a0/artifacts/score_vs_truth.json` `base.held_out.examples` are
`{DOWN, cart (2,2)}`, `{RIGHT, cart (3,1)}`, `{UP, cart (4,2)}`, and
`trace_summary.json` `a0-base.uncovered_pairs` are the same three, item for item
— both read directly. `engines_report.json` `zero_space.global_laws[0].support`
is `["8@(3,2)", "5@(4,5)"]`, so the Button is at (3,2). (2,2)+DOWN, (4,2)+UP and
(3,1)+RIGHT all land on (3,2), so the third missing approach is **from the
left**. `cold-start-a0/theory/theory.dsl`:49 is
`when act=push(Cart, left) and colored(leftof(Cart), 7) then recolored(Button, 8)`
— the Cart at (3,3) pushing leftward, i.e. from the right, which is the one the
manual got right. Every element of the row verified independently.

**A/B2 (§3.2, 5704) — HOLDS.** PAPER L714-716 says the artefact "now reports
5704 bits over 6 tracks". `engines_report.json`
`segmentation.operator_comparison[1]` (`operator: "connected_components(4)"`,
`chosen: false`) carries `script_bits: 5284`, `tracks: 6`, with
`reidentification.script_bits_before: 6511` / `tracks_before: 90`. `grep 5704`
under `cold-start-a0/artifacts/` = 0 hits. `cold-start-a0/DECISIONS.md`:453
reads "A0's losing operator moves 5704 → 5284 bits and the chosen operator does
not move". Exact.

**A/B3 (§1.2, eighteen/nineteen) — HOLDS, both halves.** (a)
`mechanism_epistemic.py`'s `omnibus_manual` docstring says "**Nineteen** of the
twenty metrics in this audit's scope" — the cited file does not contain
eighteen. (b) PAPER L2017 (§7.7) says "**eighteen**", not nineteen; L2021-2022
names `battery/tests/test_exploits_mechanism_epistemic.py`, and that file's line
393 is `assert len(landed) == 18` with line 387 carrying "nineteen before v2.1
closed K12". All four line anchors open on the right content.

**A/B4 (draft status, 27 500 words) — HOLDS exactly.** Replicating
`assemble.py`'s `len(body.split())` over `sections/*.md` gives **36 242**.
PAPER L14 says "roughly 27 500 words". Uncited, and low by 8 742.

**A/B7 (§3.1, "eleven other quantities") — HOLDS.**
`figures/check_figure_parity.py::probes()` returns exactly 14 comparisons — 5 on
A0, 4 on A0′, 3 on fig06 (adjudications, revisions-driven-by-certify, compiler
defects), 2 on fig05 (ledger beats, loop beats proper) — read off the function
body. `PARITY.md` books 12 agree / 1 one-sided / 1 disagreement = 14. PAPER
L668-670 says eleven. Eleven matches neither.

**A/load-bearing (c), the WITHDRAWN finding — HOLDS; the withdrawal is
correct.** This is the one the brief flags as fabricated in the stub, so it was
re-enumerated from scratch. `battery/artifacts/capability_spectrum.json`
`cards` holds exactly **38** entries, and tallying their `family` fields gives
**epistemic 14, economy 7, mechanism 6, exploration 6, planning 5** — five
families, no sixth, total 38, exactly what §1.2 attributes to that file. The
stub's finding does not exist and slice A is right to have withdrawn it.

**A/load-bearing (b), the §1.5 arm census — HOLDS, every number.**
`capability_spectrum.json`: `provenance.n_runs: 95`, `runs` holds 95 entries;
`provenance.arms` = `["bare_cc","schema_repro","theoria_a0","theoria_a0_spike",
"theoria_a2"]` in the paper's order; counting `runs[*].arm` gives 80 / 8 / 2 /
1 / 4 = 95; `pile` is `dev` on 88 and `synthetic` on 7; the 7 synthetic are
exactly `a0-base, a0-no-button, a0-spike, a2-play-record, a2-probed,
a2-refutation, a2-sweep`; the 88 dev runs split ar25 23 / g50t 21 / sk48 24 /
tn36 20; `provenance.n_games: 4`; `provenance.cut.piles_sha256` is
`3feca53e…41bbc19a`, matching CLAUDE.md's digest. A "confirmed correct" row that
survives independent recomputation in full.

**A/confirmed, the §3.1 28-vs-29 candidate gap — HOLDS.**
`cold-start-a0/artifacts/candidates.jsonl` has 29 rows: 3 `object_hypothesis`,
23 `rule_hypothesis`, 2 `invariant`, 1 `plan`, all `status: "candidate"`.
`THEORIZE_LOG.md`:33 opens Round 0 on "28 candidate rows: 3 `object_hypothesis`,
23 `rule_hypothesis`," and :598 books "3 objects, 7 rules, 2 invariants, 1
pending theorem". The paper's parenthetical is precisely right.

**A/D2 (quote fidelity, `cards.K2.definition`) — HOLDS.** The card reads
"Accuracy on state-action pairs the trace never covered. **T**he metric replay
cannot see**.**" PAPER L329-330 renders it inside quotation marks as "the metric
replay cannot see" — case altered, terminal period dropped. Byte-compared.

### Slice B — 8 of 8 hold

**B/B1 (§6.1, "35 lines") — HOLDS, and reproduces to the character.** Running
`diff cold-start-a3/theory/generated_l1/theory.py generated_l2/theory.py`: 8
hunks, **20 changed content lines**, 8 range headers, 7 `---` separators,
`| wc -l` = **35**. So the paper's 35 is the length of `diff`'s output, not the
size of the difference. `cold-start-a3/tests/test_transfer.py` contains no
occurrence of 35 at all; the two tests it does define
(`test_the_two_levels_compile_to_the_same_mechanism_code`,
`test_the_guard_and_effect_functions_are_byte_identical`) assert no count.

**B/B4 (§6.3, "13 anomalies, 8 of 891 pixels") — HOLDS.** PAPER L1572 carries
the table row. `negative_controls.json` records no anomaly or pixel counts of
any kind. `cold-start-a3/artifacts/arm_l2neg.json` and `arm_l2rew.json` both
carry `certify_replay: {anomaly_count: 13, pixels_unexplained: 8,
pixels_checked: 891, frames: 11, green: false}` — identical, so "same figures"
✓ — and `grep` for `arm_l2neg` / `arm_l2rew` / `arm_l2_from_scratch` over
`PAPER.md` returns **0**. *One nit, not a defect:* the row enumerates 7 of
`negative_controls.json`'s 13 per-control keys (it omits `arm`, `edit`,
`first_mismatch`, `level`, `outcome`, `planned`). The finding is unaffected —
none of the six is an anomaly or pixel count.

**B/B6 (§4.4, the BFS reachable set) — HOLDS.** Calling
`engine-rig/interop/peg1d.build_graph(5, "11011")` gives
`['00111','01001','10010','11011','11100']` — **five** states, minimum 2 pegs.
PAPER L1009-1010 prints a four-element set omitting the initial state.

**B/B3 (§4.2, 83 / 75 / 8) — HOLDS, every sub-claim.** `theory-compiler/STATUS.md`
L364 "83 passed（含 8 项真 Lean 编译）" and L367 "8 项 Lean 编译测试自动跳过，其余
75 项照常" — both inside the P-5 section; the later C7 section at L385 records
"319 passed, 1 skipped". `python -m pytest --collect-only` in this worktree
collects **364 tests** (run, not inferred). `test_gen_lean.py` carries exactly
**6** `@needs_lean`, at lines 86/97/114/194/249/348. Tree-wide the lean gates
are 6 + 2 (`test_e2e_rehearsal.py`:110,134) + 2 (`test_gen_lean_deadlock.py`) +
1 (`test_ic3_certificate.py`) = **11**. Every figure in the row reproduces.

**B/D5 (quote sourced to the wrong file) — HOLDS.** PAPER L1335-1336 quotes
**"missing rule, not wrong rule"** citing `locate_report.json`. That file's
`located.reading` says "the defect is a **MISSING RULE, not a wrong one**" — the
lowercase string is not in it. The exact string is
`loop_ledger.json` `beats[L2].detail.diagnosis: "missing rule, not wrong rule"`.

**B/confirmed, §5.6's Lean diff — HOLDS, including the decomposition.**
Recomputed on `generated_holed/theory.lean` vs `generated_repaired/theory.lean`:
plain `diff` gives **52 changed lines in 15 groups**, `diff -u` gives **7
hunks**. `=> 0` occurs 21 times in the holed file and 35 in the repaired one.
Both headers read "States: 148" and differ only `a2-holed` → `a2-repaired`.
`native_decide` / `Mathlib` / `sorry` = 0 in both.

**B/confirmed, §6.1's eight placed cells — HOLDS, all eight.**
`ground_truth.json`: `cart_start` (6,1)→(6,7), `door_cell` (6,7)→(3,1), `exit_a`
(1,6)→(1,5), `exit_b` (3,2)→(4,1), `goal_cell` (7,7)→(1,1), `portal_a`
(2,2)→(5,1), `portal_b` (2,6)→(1,6), `switch_cell` (4,1)→(7,6) — every value as
printed, and all eight moved. Reachable states 62 (l1) / 63 (l2) ✓.

**B/confirmed, §6.5's missing playbook test — HOLDS.**
`grep -rn test_the_playbook_is_byte_identical_across_levels` over the whole tree
hits only the two `playbook.dsl` files that cite it (and this run's own
reports). The test does not exist.

### Slice D1 — 7 of 7 hold

**D1/B1 + B2 + B3, the §10.2 staleness cluster (all three high) — HOLD, in
full, and this is the most consequential thing in the four slices.** PAPER
L2852-2870 reads exactly as the slice quotes it, including "**13 of 35**",
"`_(prose only, unverified)_`", the present-tense `.get("holds", True)`
expression, and "the line stands **byte-for-byte unchanged on the mainline**".
Against the tree:

* `worldgen/core/truth.py`:208-210 declares `INV_HOLDS` / `INV_VIOLATED` /
  `INV_UNVERIFIED`; `classify_invariants` at :239-241 requires
  `status == "holds"` **and** `verified is True` **and** `holds is True`; :471
  publishes `"invariant_status": classify_invariants(invariants)` and :472
  `"invariants_all_hold": all_invariants_hold(invariants)`. The quoted
  expression survives only in documentation, and the module docstring at :14-18
  describes the old shape in the past tense ("**until V19**").
* Recomputed over all 35 `worldgen/out/worlds/*/ground_truth.json`: 35 files,
  `invariant_status.unverified == []` in **all 35**, `invariants_all_hold: true`
  in all 35, **0** with any invariant lacking a `holds` key. It is **0 of 35**.
* `_(prose only, unverified)_` occurs in **0** of the 35 `GROUND_TRUTH.md`
  files; the renderer now emits `_(**unverified** — %s)_` with the note at :342
  "prose only — no callable check, so this claim is unverified, which is not the
  same as true".
* The commits are real and dated as stated: `23ec1793` (2026-07-29 07:28:58,
  "worldgen: \"I could not check this\" was being written as \"this holds\""),
  `abd9d47b` (08:18:19), `99204472` (12:50:22, E15). `git merge-base
  --is-ancestor` confirms **none** of the three is an ancestor of `32f078c2`
  (2026-07-29 14:42:54) — so the slice's timing analysis is right too: the
  section was correct when verified and was falsified by later merges.
* The twist the slice adds is also true: `truth.py`:203 states the denominator
  outright ("Thirteen of the thirty-five shipped `ground_truth.json` files…"),
  eleven lines above the code the paper quotes, in the past tense.

**D1/B4 (§10.4, `scope_exhaustive` / E15, high) — HOLDS.** PAPER L3001-3010
reads exactly as quoted, including "**Still open**" and "A reader of the
published stream still cannot tell a proved `scope: \"global\"` from an
unsearched one". `zerospace.py`:43 declares `UNDETERMINED`; :300 sets
`quotient_scope = GLOBAL if not truncated_cells else UNDETERMINED`; `Law.as_json`
emits `scope_proved: False`, `subset_enumeration_limit`, `truncated_cells`, an
`error` naming the cap and a `scope_note` on any `UNDETERMINED` law (:124-140);
the comment at :245-250 states the mechanism verbatim. The slice's own
qualification is also right: `Law.as_json` still emits no key literally named
`scope_exhaustive`, while `ZeroSpaceResult.as_json` does, at :193.

**D1/B5 (§9.2, the guard fingerprint) — HOLDS.** The first-contact
`MANIFEST.json`'s top-level keys are exactly the 25 the slice enumerates, in
that order, and there is **no `guard` block**; `sealing` carries only the
byte-scan counters. PAPER L2611-2614 attributes the 4/21/`deny` fingerprint to
that manifest.

**D1/B8 (§10.3, "28 distinct Python sites") — HOLDS.** Scripted over
`SURVEY-environment-as-semantics.md` lines 138-230: **27** distinct `.py`
tokens, and my list is identical to the slice's 27, item for item.
`toolchain.probe` is present in the span, which is what a 28th count would have
to be. PAPER L2929 says 28.

**D1/B10 (§10.7, six vs five work items) — HOLDS.**
`inputs-verbatim/PROVENANCE.md`:13 says "One machine-local copy was backing
**five** work-board items and a section of this paper";
`runs/…P14-honesty-section/RUN_STATE.md`:107 says "They back **six** work items
and this section"; PAPER L3158 says six and cites neither.

**D1/D1 (the §9.3 blockquote, high) — HOLDS, all three edits.**
`proxy/DECISIONS.md`:468-470 reads "the ledger is complete and self-consistent,
and the arm cannot write **to** it — but the operator can. Phase 1's \"no
bypass\" **property** was always **about** the arm, **and it holds.**" PAPER
L2669-2671 sets in block-quotation "…cannot write it…", "\"no bypass\" was
always **a claim about** the arm", "**and that one still holds.**" — with no
path anywhere in §9. A paraphrase presented as a quotation.

**D1/confirmed, §10.6's self-census — HOLDS, exactly.** Recounted over the
current `PAPER.md`: "verified" (case-insensitive, compounds included) occurs at
L183, 438, 943, 963, 1691, 2855, 2858, 2863, 2932, 2977, 3099, 3139, 3142,
3144, 3146, 3147, 3149, 3488, 3656, 3721 — **eight** of them outside
L2735-3194, at precisely the eight lines the slice names, and each maps to the
paper's own description of it. 已验证 occurs exactly **once**, at L3149. This is
the row I most expected to break, and it does not.

### Slice D2 — 7 of 7 hold

**D2/B1 (§11.2, `never_audited`, high) — HOLDS, including the commit
attribution.** `grep never_audited CLAUDE.md` = **0**. PAPER L3289-3290 says
"`CLAUDE.md` **states** that no game has been played and that all 25 are
registered `never_audited`". `git show 32059928 -- CLAUDE.md` shows that commit
(2026-07-28 14:00:40) deleting exactly "As of this writing no game has been
played: the cut was made from catalogue metadata alone and all 25 are registered
`never_audited`." `11_limitations.md`'s last commit is `325e9476`, 2026-07-29
23:03:29 — 33 hours later, as stated.

**D2/B3 (§12.2, "neither engine is exercised", high) — HOLDS.** PAPER
L3640-3641 carries the sentence. (a) PAPER L2993-3000 (§10.4) does report a
census result about `engine-rig/engines/deadlock_carver/__init__.py`'s
`PruningReport.same_answer`, ending "Now gated". (b) `theory-compiler/STATUS.md`
L15-21 is an acceptance table giving `deadlock_carver` two Lean-checked
certificates (28,672 and 1,792 leaf goals; 60 s and 4.2 s; 九条全空) and
`ic3_pdr` peg4 on both the `computational` and `algebraic` routes. *Reading
note:* half (a) is the finding — a result in this paper does exercise one of the
two engines. Half (b) is weaker support, since an acceptance table in a cited
file is not itself "a result in this paper"; the row does not depend on it.

**D2/B5 (§11.1(d), five gaps) — HOLDS.** `cold-start-a0/THEORIZE_LOG.md`'s §E
table runs E-01 through **E-09** at lines 357-365, with E-06…E-09 each marked
**discharged** and carrying a "see below". PAPER L3238-3240 says "an
expressivity ledger of **five** gaps (§E: E-01 … E-05)". `E-07`, `E-08` and
`E-09` return **0** hits in `PAPER.md`. E-06 is at :362, which §11.3 itself
cites.

**D2/B7 (§11.4, "8 runs") — HOLDS.** PAPER L3424-3427 states "8 runs" citing
`baseline-arms/SCHEMA_LOCATE.md` and `battery/DECISIONS.md` D-B-019.
`SCHEMA_LOCATE.md` contains no standalone 8; D-B-019 (from :262) is titled
"«No Schema arm» was two different facts, and v1 reported the wrong one" and
carries no count. The 8 is `capability_spectrum.json` `runs` with
`arm: schema_repro` — independently counted as 8.

**D2/A-1 (`dsl_grammar_v0.3.md`, high) — HOLDS.** `CONTRACTS/` holds
`dsl_grammar_v0.1.md`, `v0.2.md` **and `v0.3.md`**, plus
`candidates_schema_v0.2.md`, `deadlock_certificate_v0.1.md` and
`ic3_certificate_v0.1.md`. v0.3's header: Status 定稿, Effective 2026-07-28,
"**Supersedes:** `dsl_grammar_v0.2.md`". Its stated reason is "v0.2 used a word
in a definition and never defined it", the forcing entries are `a0-spike`'s
**X-1** and **X-5**, and its §1 table gives R2 "**376 mispredictions** over the
39,960 pairs". `v0.3` returns **0** hits in `PAPER.md`.

**D2/confirmed, "every economy metric is `not-applicable`" — HOLDS, zero
exceptions.** Recomputed: 7 economy cards (E1-E7) × 7 `theoria*` runs
(`a0-base, a0-no-button, a0-spike, a2-play-record, a2-probed, a2-refutation,
a2-sweep`) = **49 cells**, every one `status: "not-applicable"` with
`value: null`. A universal quantifier stated in a confirmed-correct row and true
under enumeration.

**D2/confirmed, the bibliography row — HOLDS, exactly.** §12 (L3486-3729) cites
**65** distinct backticked bib keys inside brackets; **all 65** resolve in
`papers/phase1-workshop/references.bib`, which has **70** entries; the 5 unused
are `beasley1992pegsolitaire`, `cropper2021popper`, `evans2018dilp`,
`hubert2026alphaproof`, `trinh2024alphageometry` — the slice's list, exactly.
Zero `[bib: TODO]` markers. (My first extraction pass got 64 and named a sixth
unused key; the miss was my tokenizer's — `ha2018world` is cited at L3505 inside
a bracket containing prose. The slice was right and I was wrong.)

---

## Cross-slice consistency

Checked deliberately, because a disagreement between slices about one artefact
would be top-severity. **No disagreement found.** The shared surfaces:

* `v9_gaming_audit.json` (slice A's B5/B6 and confirmed rows; slice D2's B4):
  `n_metrics 38`, `n_attacked 38`, `n_attacks 112`, `gameable` 37,
  `b14_baseline_main` = `[E2,E3,K7,K11,K12,M3,M6,P3,P4]`, `demoted_by_v9` 9
  including M3, `undetermined` `["M3"]`, `main` `[]`, `unattacked` `[]`,
  `not_gameable` `[]`. A's "gameable 37, all but M3" and D2's "demoted_by_v9 =
  all nine including M3" are both true and not in tension. Recounted the attack
  census: **112 attacks, 95 succeeded**, and all 112 carry
  `S3_poverty_certified: true` and `certificate.ok: true` with zero violations —
  exactly A's recomputation. Both slices agree the JSON never says "two".
* `gaming_audit.json` (A and D2 both): `n_demonstrated 38`, `n_disagreements
  17`, `main` 9, `demoted_by_demonstration` 10, 34 succeeded / 4 not
  (`E2, K12, M3, P4`), and exactly **14** of the 17 disagreements carry
  `defended` in `fields_contradicted`. Identical in both slices, and both right.
* `loop_ledger.json` (A §1.5 item 2, B §5.5, D2 §11.5): `summary {absent 0,
  fail 0, pass 8, total 8}` — all three agree, all three correct.
* The first-contact `MANIFEST.json` cost block (A's abstract chain, D1's §9.4):
  `budget.actions_ok: 7`, `cost.cli_reported_usd: 6.317658`,
  `from_price_table.usd_total: 5.795338` — identical readings in both slices.
* `capability_spectrum.json` (A, B, D2 all read it): 38 cards, 95 runs,
  schema_repro 8, battery_version `"v2"` — no contradiction between slices.

---

## Findings outside the sample

**1. `MANIFEST.json`'s `completeness_check` row count for slice A is not
produced by the rule that produces the other three.** The manifest records
"A 73 rows, B 57, D1 73, D2 65" as the checked property behind `complete`.
Counting markdown table lines: A 73 pipe-lines / 7 separators, B 64 / 7, D1
82 / 9, D2 73 / 8. The rule *pipe-lines minus separator lines* reproduces
**B 57 ✓, D1 73 ✓, D2 65 ✓** and gives **A 66**, not 73. The rule *all
pipe-lines* gives A 73 and overshoots the other three by exactly their separator
counts. So no single mechanical rule yields all four figures: A's 73 was counted
one way and B/D1/D2 the other. This is not a row defect — every row I sampled in
A is sound — but it is a count in the very artefact that establishes `complete`,
and it is the same defect class P18 exists to fix, one level further up. It
should be restated with its counting rule before anything binding cites it.

**2. `MANIFEST.json`'s prose is stale about slice A.** `slice_state_note` says
"**A and C** are recorded here as stubs on purpose" and `stub_census` lists
"citecheck A (Pass A only, B/C/D counted but never enumerated)", while the
`citation_slices` entry for A now reads `state: "complete"` with a full
`counts_corrected_vs_stub` note. Both prose fields describe the pre-rewrite A.
Harmless to a reader who reads the whole file; misleading to a gate that greps
it.

**3. Slice B's closing paragraph is stale in the same direction** — it says
"`citecheck-A-abstract-to-s3.md` ends after Pass A (77 lines, no Pass B/C/D
sections)". True when B was written, false now (A is 810 lines with all four
passes). Slice A's own closing paragraph notes the reverse relationship
correctly. Not a row defect; worth a superseding line rather than an edit.

**4. Three line anchors are off by one or two**, all cosmetic and none
load-bearing: slice A cites the `omnibus_manual` docstring as "L852-882" where
852 is the `def` line; slice D1 cites the `_(**unverified** — %s)_` emission at
"line 559" where it is at 557; slice D1 cites `Law.as_json`'s degradation block
as "lines 121-140" where the `if self.scope == UNDETERMINED:` guard is at 124.
Every one opens on the right content within two lines.

---

## Rows checked opportunistically while verifying the above (9, all hold)

* **A, Pass A rows 4 and 5** — `git ls-files` gives exactly **15** tracked files
  whose basename is `playbook.dsl` and exactly **6** named `THEORIZE_LOG.md`
  (`a0-spike/`, `cold-start-a0/`, `cold-start-a0/prime/`, `cold-start-a2/`,
  `cold-start-a3/`, `theoria-arm/`) — the slice's corrections to the stub's 16
  and 4 are both right, and its six-directory enumeration is exact.
* **A/B8** — `engines_report.json` `mining.rules` holds exactly **twelve**
  `*_still_*` names (`obj{0,1,2}_still_{UP,DOWN,LEFT,RIGHT}`); the paper says
  eleven.
* **A/B10** — `cards.K4.definition` is "Mean coverage over clauses the manual
  annotates with one; the count of unannotated clauses is reported alongside,
  not folded in." — a mean, not the share the paper attributes to it.
* **A/C5** — `figures/csv/fig06_concept_timeline.csv`: 119 rows over 9 lanes;
  `adjudicated` on 20 rows spanning **17** distinct `item_id`s (L-01…L-03,
  O-01…O-04, P-01, P-02, R-01…R-08); **2** `manual-revision` rows (REV-01
  triggered by "one pass over all 28 candidates plus the board map", REV-02 by
  the no-Button UNSAT — neither by certify); **3** `compiler-defect-ABSENT`;
  one `verdict-absent-ABSENT`, `P-03`, label "the log records no bold verdict
  for this entry"; and **no** `revisions_driven_by_certify` column. Both the
  confirmed row and C5's finding hold.
* **A/load-bearing (a)** — `exam/artifacts/leakage.json` has four `papers`
  entries with `probes_declared` 363 + 58 + 1284 + 85 = **1790**, `probe_hits: 0`
  and `structural_hits: 0` on all four. And the exemption hole is real: "84 %"
  occurs **exactly once** in the 3729-line paper, at L125; 83.6 % is at L2717.
* **B/B10** — `ground_truth.json` `a3-l1` lists **21** `guard_contexts`
  (including four `blocked_*` and three `door_*`) against **14**
  `rule_generating_contexts`.
* **D1 confirmed, the bypass ledger** — `theoria-arm/evidence/model-proxy-401.jsonl`
  has **131** rows: **66** `bypass_attempt` and **65** `model_call`.
* **D2 confirmed, §11.5's exploit figures** — see the cross-slice section: 17
  disagreements, 14 with `defended`, both exact.
* **All four slices' paper stamp** — sha256, bytes and line count recomputed and
  correct in all four.

---

## Judgement

**The sample came back clean: 31 of 31, plus 9 opportunistic rows, hold.** That
is the honest result and no finding has been manufactured to improve on it.

On the evidence of this sample the four slices are **sound enough to carry a
`binding` stamp** — with one condition that is not about the rows: the
`MANIFEST.json` row count that established `complete` (finding 1 above) uses two
different counting rules for slice A and for B/D1/D2, and should be restated
with its rule before a gate starts vouching for it. Fix the count, and the
binding synthesis has a checked foundation.

Two observations that bear on how much this sample licenses:

* The weighting was toward the load-bearing and the numeric, which is where
  defects are most consequential and — on this evidence — where these slices are
  strongest. Every high-severity row I drew (D1's B1/B2/B3/B4/D1, D2's
  B1/B3/A-1) reproduced in full, including the parts that needed recomputation
  from 35 artefacts, a `git merge-base` ancestry test and a `pytest --collect`.
* The confirmed-correct rows were the real test, since nothing downstream
  re-checks them, and they held under enumeration rather than under inspection:
  the 95-run arm census, the 49 economy cells, the 65 bib keys, the eight
  "verified" occurrences and the 52-line Lean diff were each recomputed from the
  artefacts rather than read back off the report.

The known precedent for row-level error — slice A's stub, whose per-pass counts
were wrong and whose §1.2 five-family finding was fabricated — does **not**
recur in the rewritten A. The withdrawal is correct: `capability_spectrum.json`
carries the 38-metric five-family split field for field, exactly as slice A now
says.

**Sealed-pile discipline.** No sealed game was opened, named, listed or
searched. `arc-recon/` was not read beyond what CLAUDE.md quotes; the only pile
artefact touched was `capability_spectrum.json`'s `provenance.cut.piles_sha256`,
compared as a digest against CLAUDE.md. `environment_files/` was never touched.
No sampled row required sealed material, so there is no
unverifiable-under-the-cut entry.

**Scope.** Read-only throughout: no git write command, and no citecheck slice
edited. This file is the only artefact written.

