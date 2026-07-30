# CITECHECK — mechanical audit of the draft's binding rule

```audit-stamp
target: papers/phase1-workshop/PAPER.md
sha256: 4208b69cdd6197a7b5f401223601a56b476d8c9a2f7a471b1412ab469c6dbd7d
lines: 1318
bytes: 75885
scope: full text of the first assembled draft (commit 4959df1c)
status: stale
superseded_by: CITECHECK-2026-07-30.md
date: 2026-07-28
```

> **This report is stale and is kept for the record.** It audited the whole paper
> as it stood on 2026-07-28 — the blob below, 1318 lines / 75,885 bytes.
> `PAPER.md` is now 3729 lines and 237,872 bytes, so this pass covers **31.9 % of
> it by bytes**, and none of §7–§12: not the metrics battery, the exam, the live
> chain, the adjudication census, the limitations or the related work. Its
> findings about the text it read are not withdrawn — most were acted on, and
> `runs/20260730T000000Z-P18-audits-cover-half/delta-old-vs-new.md` reconciles
> every one of them against the current paper. What expired is its *coverage*.
> `CITECHECK-2026-07-30.md` is the binding citation audit of the current text; it
> indexes five slice reports that together cover L1–3729 with no gap.
>
> The irony is worth leaving on the page. This is the audit of the rule that
> every claim must name the artefact it came from, and it stated its own target in
> prose only — so `verify_paper.py` reported PASS for weeks while the audited
> fraction fell from 100 % to 31.9 %. The stamp above is what P18 added on
> 2026-07-30, and check G (`audit_stamp.py`) is what makes the same drift loud
> next time.
>
> **`lines: 1318` is the newline-byte count (`wc -l` semantics).** The paragraph
> immediately below says "1319", counting a last line with no trailing newline.
> The blob named by the sha has 1318 newlines — confirmed out of `PAPER.md`'s git
> history, not copied from this file's prose. In a staleness stamp that
> off-by-one is indistinguishable from a paper that gained one line, which is why
> the stamp fixes the convention and `REVIEW.md`'s stamp carries the same note.

**Target.** `papers/phase1-workshop/PAPER.md`, 1319 lines, sha256
`4208b69cdd6197a7b5f401223601a56b476d8c9a2f7a471b1412ab469c6dbd7d`
(mtime 2026-07-28 08:47:19). The file was edited by a concurrent session *during*
this audit — §2.2 (engine count), §5.4 (full-sweep pixel counts) and §6.7 (X5
citation) were corrected mid-pass, and `PROVENANCE.md` was created. Every finding
below is against the hash above; re-run the audit if the hash has moved.

**The rule under test.** "Every quantitative claim carries the repo-relative path
of the artefact it came from." Four passes: path existence, number verification,
orphan numbers, quote fidelity.

**Precedence used.** JSON artefacts beat prose reports. Where they disagree it is
recorded in `## Source disagreements` with the branch the paper followed.

---

## Summary

| pass | measure | count |
|---|---|---|
| A | distinct path-like tokens cited in backticks | **83** |
| A | resolve as written, repo-relative from the tree root | **52** |
| A | exist, but **only** under a section-implied base — not repo-relative | **31** |
| A | do not exist anywhere in the tree | **0** |
| B | distinct numeric claims traced to a file and checked | **~160** |
| B | wrong, mis-attributed, or not present in the cited file | **10** |
| C | numbers with no citation at all, or a citation lacking them | **7** |
| D | attributed quotations checked (blockquotes + inline fragments) | **31** |
| D | inexact — paraphrase, compression, or punctuation-normalised | **8** |

**Bottom line.** No path in the paper is broken: every cited artefact exists.
But 31 of 83 citations are *not* repo-relative — they are bare filenames or
`artifacts/…` fragments that only resolve if the reader carries the section's
directory in their head, which is precisely what the binding rule forbids. Two
numeric findings are load-bearing rather than cosmetic: the claim that the two
Lean files "differ in their weight table and in nothing else" is false of the
files, and the claim that every discriminative verdict is `underpowered` or
`no-data` is false of `discrimination.json`. Both are inherited from the source
reports rather than invented by the paper, and both survive into the abstract.

---

## Broken paths

**None.** All 83 path-like backtick tokens resolve to something in the tree.
`PROVENANCE.md`, referenced in the draft-status note at L13, was absent when this
audit began and now exists at `papers/phase1-workshop/PROVENANCE.md`.

### Not repo-relative (31) — the rule violation Pass A actually found

These are cited as bare filenames or partial paths. They resolve, but only under
a base the reader has to infer.

| cited as | paper lines | actually at |
|---|---|---|
| `PROVENANCE.md` | 13 | `papers/phase1-workshop/PROVENANCE.md` |
| `theory.dsl` | 196, 1063 | `cold-start-a0/theory/theory.dsl` (also `cold-start-a2/`) |
| `playbook.dsl` | 200 | `cold-start-a0/theory/playbook.dsl` |
| `THEORIZE_LOG.md` | 237, 1132 | ambiguous — 4 files carry this name (`cold-start-a0/`, `cold-start-a0/prime/`, `cold-start-a2/`, `a0-spike/`) |
| `raw_trace.jsonl` | 315 | ambiguous — 3 files (`cold-start-a0/`, `cold-start-a0/prime/`, `cold-start-a2/`) |
| `theory/theory.dsl` | 323, 706 | ambiguous — `cold-start-a0/`, `cold-start-a2/`, `a0-spike/` |
| `A0P_REPORT.md` | 393, 1156 | `cold-start-a0/prime/A0P_REPORT.md` |
| `prime_report.json` | 436 | `cold-start-a0/prime/artifacts/prime_report.json` |
| `gen_lean.py` | 588 | `theory-compiler/src/theory_compiler/generators/gen_lean.py` |
| `engines_diff.json` | 697 | `cold-start-a2/artifacts/engines_diff.json` |
| `trace_summary.json` | 698 | ambiguous — 3 files; §5.2 means `cold-start-a2/artifacts/` |
| `artifacts/plan_holed.json` | 720 | `cold-start-a2/artifacts/plan_holed.json` |
| `theory/generated_holed/theory.lean` | 723 | `cold-start-a2/theory/generated_holed/theory.lean` |
| `A2_REPORT.md` | 728, 821 | `cold-start-a2/A2_REPORT.md` |
| `solved_episode.jsonl` | 728 | `cold-start-a2/artifacts/solved_episode.jsonl` |
| `refute.py` | 758 | `cold-start-a2/a2pipeline/refute.py` |
| `locate.py` | 759 | `cold-start-a2/a2pipeline/locate.py` |
| `probe.py` | 760 | `cold-start-a2/a2pipeline/probe.py` |
| `artifacts/refutation.json` | 764 | `cold-start-a2/artifacts/refutation.json` |
| `artifacts/locate_report.json` | 765, 781 | `cold-start-a2/artifacts/locate_report.json` |
| `artifacts/probes.jsonl` | 766, 823 | `cold-start-a2/artifacts/probes.jsonl` |
| `theory/theory_repaired.dsl` | 767, 789 | `cold-start-a2/theory/theory_repaired.dsl` |
| `artifacts/repair_report.json` | 768, 794 | `cold-start-a2/artifacts/repair_report.json` |
| `artifacts/plan_repaired.json` | 769 | `cold-start-a2/artifacts/plan_repaired.json` |
| `artifacts/probe_report.json` | 787 | `cold-start-a2/artifacts/probe_report.json` |
| `theory/generated_repaired_stale/` | 791 | `cold-start-a2/theory/generated_repaired_stale/` |
| `generated_holed/theory.lean` | 802 | `cold-start-a2/theory/generated_holed/theory.lean` |
| `generated_repaired/theory.lean` | 802 | `cold-start-a2/theory/generated_repaired/theory.lean` |
| `probed_trace.jsonl` | 826 | `cold-start-a2/artifacts/probed_trace.jsonl` |
| `artifacts/engines_diff_probed.json` | 827 | `cold-start-a2/artifacts/engines_diff_probed.json` |
| `run_battery.py` | 880 | `battery/run_battery.py` |

Four of these (`THEORIZE_LOG.md`, `raw_trace.jsonl`, `theory/theory.dsl`,
`trace_summary.json`) are genuinely ambiguous: more than one file in the tree
carries the name, and the paper cites them in sections that discuss two or three
of those directories at once. Those four are the ones a referee could actually
mis-resolve.

---

## Wrong numbers

| § | paper says | file says | file path | severity |
|---|---|---|---|---|
| §6.4, §7.4 | "Every discriminative verdict came back `underpowered` or `no-data`" | 29 metrics: **11** `underpowered`, **13** `no-data`, **5** `not-ranked` (`E1`, `K7`, `K11`, `P5`, `X5`, each `"note": "diagnostic metric; it describes a run, it does not rank one"`) | `battery/artifacts/discrimination.json` | **high** |
| Abstract, §1.2, §5.6 | the two Lean files are "identical in generator, tactic, dependency surface and axiom list, differing only in a weight table" / "differ in their weight table and in nothing else" | `diff` of the two files: 70 diff lines. Besides the `w` table they differ in **four `step` clauses** (`⟨Cell.c31, …⟩, .down => c31` vs `=> c35` — the teleport), in **`Goal`** (`s.cart == Cell.c10` vs `Cell.c34`), in the header line (`a2-holed` vs `a2-repaired`) and in the invariant comment block | `cold-start-a2/theory/generated_holed/theory.lean`, `…/generated_repaired/theory.lean` | **high** |
| §3.4 | "111 frames, 8991 pixels, 0 anomalies (`prime_report.json`, `run_b.certify_cheap`)" | `run_b.certify_cheap` is the bare boolean `true`. The frame/pixel/anomaly triple is in `run_a.certify_cheap`; for Run B it appears only in `A0P_REPORT.md` §3's table | `cold-start-a0/prime/artifacts/prime_report.json` | medium |
| §6.5 | P1: "haiku 0.97 actions per call" | no aggregation of the artefact yields 0.97 — run-level mean **0.9606** (n=12), pooled actions/calls **0.7698**, mean of per-game medians **0.8631**. (opus "0.52" ✓ = 0.5176 run-level mean) | `battery/artifacts/capability_spectrum.json` | medium |
| §7.3 | "**`lp_potential` is sound but incomplete.** It never certifies a solvable configuration, but some genuinely unsolvable ones admit no linear pagoda (`engine-rig/STATUS.md`)" | that sentence is **verbatim `CLAUDE.md`**. `engine-rig/STATUS.md` contains no such sentence. The substance is at `engine-rig/DECISIONS.md` D-014 ("The method is sound but incomplete") and `engine-rig/interop/README.md` | `engine-rig/STATUS.md` | medium |
| §7.3 | "verifies read-only-ness by hashing **258 files** before and after a full run (`cold-start-a2/artifacts/upstream_pin.json`)" | `upstream_pin.json` pins **22** files (`sha256` map). The 258 figure is `tools.verify_readonly`'s count, stated only in `cold-start-a2/A2_REPORT.md` §7 | `cold-start-a2/artifacts/upstream_pin.json` | medium |
| §6.5 | E5: "haiku $0.031/action" | run-level mean **0.03174**, mean of per-game medians **0.0329**, median of per-game medians **0.0291**. (sonnet 0.124 ✓, opus 0.279 ✓ against the run-level mean — so the haiku figure is aggregated differently from its two neighbours, or rounded down) | `battery/artifacts/capability_spectrum.json` | low |
| §6.5 | "Between **27 %** and 45 % of pilot steps failed outright" | pooled `P5` failure rate per model: haiku **28.3 %**, sonnet **36.1 %**, opus **45.1 %**. Upper bound ✓; lower bound is 28 %, not 27 % | `battery/artifacts/capability_spectrum.json` | low |
| §5.5 | Lean fails "at line 769 — `tactic 'decide' proved that the proposition ... is false` (`artifacts/repair_report.json`, `stale_certificate`)" | the JSON's `first_error` string is truncated at `…proved that the proposition` — no "is false". Line 769 ✓, the `[sorryAx]` axiom report ✓. The full phrase appears only in `cold-start-a2/A2_REPORT.md` §3 | `cold-start-a2/artifacts/repair_report.json` | low |
| §3.1 | "producing **29 schema-valid candidates** (M2)" | `candidates.jsonl` has 29 rows (23 `rule_hypothesis`, 3 `object_hypothesis`, 2 `invariant`, 1 `plan`) ✓ — but `cold-start-a0/THEORIZE_LOG.md` Round 0 opens "**28** candidate rows: 3 / 23 / 2 / 0". The log counts only what it adjudicated | `cold-start-a0/artifacts/candidates.jsonl` | low (paper is right; see disagreements) |

### Numbers checked and confirmed correct (spot list)

Everything else in §1, §3, §4, §5, §6 traced. Confirmed against artefacts, not
just against reports:

* **A0** — 276/276 frames; 22 356/22 356 px (= 276 × 81); 233/236 = 0.987288 and
  held-out 0/3 = 0.0 with the three examples being Button-from-above/below/right
  (`score_vs_truth.json`); 59 reachable states; 275 transitions; 12-step SAT plan;
  variant 92/92 = 1.0; `seal` field present; 3 objects / 7 rules / 2 invariants /
  1 pending theorem; 152 indicator bits; frontier sizes 1 and 2; 90 tracks / 332
  events / 6511 bits vs 3 tracks / 216 events / 4423 bits (`THEORIZE_LOG` O-03
  table); Cart +2967, Button −17, Door −13 (`THEORIZE_LOG` O-04); −5 / −1 in
  `A0_REPORT.md` §8; eleven `*_still_*` rules.
* **A0′** — 57 reachable states; 228 state-action pairs; 107/228 = 46.9 %; 13
  executable probes of 27 designed; 111 frames / 8991 px / 0 anomalies; 110
  transitions; `score_vs_truth_before` 0.991228 → `_after` 1.0; 0 untested rules;
  sixteen 1/1 clauses (`prime/THEORIZE_LOG.md` R-03); 40 % truncation and the
  whole §3.3 table verbatim from `A0P_REPORT.md` §1.
* **a0-spike** — 341 transitions; 8 mismatches; 315 reachable; 39,960 states over
  five levels, 0 mismatches; 1,966 vs 341 actions; `ghost` 6, `nocross` never in
  341 / 6 elsewhere; `[depends: push2]`; null space of dimension 2 (T-6).
* **A1** — `weights_integer` `[-1,1,0,1,-1]`; `inv_closed` `n_checked: 6` with
  deltas `0, 0, -2, -2, 0, 0` in that order; `inv_init` value `0`; `goal_break`
  witness `00010` potential `1`; `"verified": true` present and ignored by
  `certificate.py` (D-TC-009); M8 weights `[1,2,3,2,1]` (D4); 83/83 tests, 8
  invoking `lean`; `w .p1` 1→7 negative control with `[sorryAx]` and exit 1;
  `assert unprovable == [0, 2, 4]` **verbatim** in `engine-rig/tests/test_interop.py`;
  BFS reachable set `{00111, 11100, 01001, 10010}`; 5 of 32 → 31/32 (D-TC-012);
  O(2^n)/O(n) and `propext`/`Quot.sound` (D-TC-008); 2^33 on the 33-hole board.
* **A2** — 184 frames / 14 904 px (= 184 × 81) / 0 anomalies; 163/164 with the
  single omitted pair `cart=(6,4) pressed=1 act=DOWN`; `cut_rule` text; 55
  reachable states; 148 states in **both** Lean headers; `#print axioms unsolvable`
  present in both, no `sorry`, no `native_decide`, no `Mathlib`; `=> 0` count is
  **21** in the holed file and **35** in the repaired one; 18-action episode with
  `win_frames: [18]`; 44 anomalies over 3 kinds, first at `t: 184`, cell `[6,4]`,
  248 frames on the sweep; loop ledger `{"absent":0,"fail":0,"pass":8,"total":8}`
  with M0 and M5 preceding L1–L6; probe P-01 prediction `stays` → observation
  `jumps to (7,6)`; P-03 hypothetical at 1.0 bits; trace 184 → 196 frames
  (`loop_ledger` L3 `trace_grew`); repaired plan SAT length 18, `execution_mismatches: []`.
* **Battery** — `provenance.n_runs: 26`, `n_games: 4`, arms `["bare_cc","theoria_a0"]`;
  29 metric cards over 5 families (E/K/M/P/X); `main` 15 / `reference` 14 in
  `gaming_audit.json`; a0-base K4 = 1.0 with `annotated: 7`, K2 = 0.0 with
  `{agree: 0, pairs: 3}`, K1 = 0.987288; K6 value 706.333 with `best: 2125`,
  `worst: -5`, `concepts: 3`; X5 = 59.0 cross-checking `cold-start-a0/artifacts/trace_summary.json`
  `reachable_states: 59`; `min_attainable_p: 0.125` and the top-level `power`
  string; `warning` fields present on P1 and E5 and absent on E2; E2 δ = +1.0
  with `wins: 4, losses: 0, ties: 0`; E2 per-model 0.1994 / 0.2521 / 0.2830 by
  mean of per-game medians (matches 0.20 / 0.25 / 0.28); redundancy
  `n_clusters: 27`, `n_metrics: 29`, `min_shared_runs: 4`, `threshold: 0.9`,
  strong pairs +0.916 and +0.909; E2/E3 eight-turn floor in `gaming_audit.json`.
* **Pile digest** — independently recomputed. `arc-recon/data/piles.json` hashes
  to `d3140eff4889…` **after LF normalisation** (the worktree checkout is CRLF, so
  the raw bytes give `f2ef44d1…`), and `sha256(json.dumps(payload minus 'sha256',
  sort_keys=True, separators=(',',':')))` = `3feca53e5ede…41bbc19a` exactly. §6.7's
  claim is correct in every part.
* **§7** — precheck 9/9, 3/3, 9/9, 9/9 all `"verdict": "PASS"`; nine sealed games
  in INC-BA-001 with `ls20`/`ft09` marked 实质泄露 (materially); `ledger.jsonl`
  **560** rows; 12 cells + 2 reruns, 109 successful actions, 44 more on `ar25`,
  all four at `trajectories_reviewed`, `levels_completed` 0 throughout; FD agrees
  with the stub on `a0-base` (12), `a0-no-button` (UNSAT) and `a0p-base` (10) in
  `fd_real.json`, `identical_plan: true` on all three.
* **§8** — 98.98 % and +56pp both present in `Theoria.md` §3.1; the three-wave
  table is a faithful translation of `Theoria.md`'s (representatives
  Dreamer/MuZero/Genie, WorldCoder/Schema, 本文); every system the paper names
  (Ha & Schmidhuber, PlaNet, Dreamer, MuZero, Genie, JEPA, WorldCoder, RAP,
  Schema, LM-cut, operator-counting, PDB, CEGIS, ILP, Petri, IC3,
  proof-carrying code, LLM+ATP) is named in `Theoria.md`. `[bib: TODO]` is
  honest: `Theoria.md` contains no arXiv id, URL or reference section.
* **§5.1's "175 frames"** — traces to `Theoria.md` §1.3 ("模型重放 175/175 全对"),
  which is the only source INC-004 permits. No upstream DC22 artefact is needed
  for it, and none was read.

---

## Uncited numbers

| § | the sentence | what it would need |
|---|---|---|
| §3.6 (L485) | "The §8 addendum corrects the accounting … the accounts move to **−5** and **−1**" | a path. "§8" alone; resolves to `cold-start-a0/A0_REPORT.md` §8, which does carry −17→−5 and −13→−1 |
| §3.1 (L329) | "The whole run takes about six seconds." | a path. The `≈6 s` is in `cold-start-a0/A0_REPORT.md`'s run-instruction line, not in the §1 milestone table the paragraph cites |
| §7.3 (L1144) | "verifies read-only-ness by hashing **258 files** before and after a full run" | the citation attached is `upstream_pin.json`, which does not contain 258; needs `cold-start-a2/A2_REPORT.md` §7 |
| §7.3 (L1146) | "Revision counts across the whole paper are 0 (A0), 0 (A0′ Run A), 1 (A0′ Run B), **1 (A2)**" | the first three are in `prime_report.json` / `A0_REPORT.md` §6.1. **No file in the tree states A2's revision count**; the L4 修订 beat in `loop_ledger.json` records `re_derivable_from_grown_evidence: true` and no count |
| §6.5 (L949) | "P1 correlates with the failure rate at **ρ = −0.83**" | cited to `battery/REPORT_V0.md` and `battery/STATUS.md` W-4, both of which state it — but **no artefact carries the correlation**. It is the one battery number that cannot be re-derived from `artifacts/`. (The `-0.83` that does appear in `capability_spectrum.json` is `P2`'s value on an unrelated run.) |
| §2.5 (L289) | "before any money is spent on play (`Theoria.md` Phase 2 §Phase 1)" | malformed anchor. `Theoria.md` has `## Phase 1 · 封闭系统` inside 第二部分 (Part Two). There is no "Phase 2 §Phase 1"; it should read Part 2, Phase 1 |
| Abstract (L27, L53) | every number in the abstract — 276/276, 22 356, 3 of 236, 0.000, 228/228, 18-action, six beats, 26 trajectories, four paired games, *p* = 0.125 | nothing, by convention — but the binding rule as written ("every quantitative claim carries the repo-relative path") admits no exception, and the abstract takes one. Each figure is correctly cited in the body |

Two paragraphs that *look* orphaned but are not: §3.2's "152 anonymous indicator
bits" and the whole MDL block (90 tracks / 88 vanishes / 87 appears / 3 tracks /
6511 vs 4423) inherit §3.2's lead citation to `cold-start-a0/A0_REPORT.md` §3,
which carries all six figures. §3.3's "n = 1 per arm" is an editorial
characterisation, not a measurement.

---

## Inexact quotes

31 attributed passages checked — 16 blockquotes and 15 inline attributed
fragments. Eight are inexact.

| § | quoted as | source | problem |
|---|---|---|---|
| §2.5 (L299) | 每个阶段边界定义一个最小可发表单元——Phase 1 结**：**A0–A2 + 电池对既有轨迹的回算**，**独立可成 workshop 文 | `Theoria.md`, Phase 4 deliverables | punctuation silently normalised: the source uses half-width `:` and `,` throughout, the quote uses full-width `：` `，`. Wording otherwise verbatim |
| §4.1 (L521) | **A1 孔明棋**：…依赖假设为空。判死赌的是管线接通**，**不是 LLM 灵感**；**找不回**，**直接判死。 | `Theoria.md`, Phase 1, 三件离线验收 | same punctuation normalisation. Note §5.1 quotes the adjacent A2 bullet with the *original* half-width punctuation — so the paper is internally inconsistent about how it transcribes this document |
| §4.1 (L534) | "三个小检查代替无穷穷举**，**检查量与状态空间大小无关" | `Theoria.md` §1.5 | half-width `,` in source |
| §6.1 (L859) | 同一本账**，**两次使用 | `Theoria.md` Phase 2 | half-width `,` in source |
| §8.1 (L1250) | "若预测本身就是理解**，**第一波已经赢了" | `Theoria.md` §3.1 | half-width `,` in source |
| §5.2 table (L698) | `"那条规则从未触发"`, attributed to `Theoria.md` §1.3 | source reads 缺的那条传送规则从未触发 | compression, not a quotation. Presented inside quotation marks in a table headed `Theoria.md` §1.3 |
| §5.2 table (L700) | `"重放全对"`, attributed to `Theoria.md` §1.3 | source reads 模型重放 175/175 全对 | same — a compressed fragment in quotation marks. (The other four cells in that column — 漏了一条传送规则, 不欠任何一帧, 完备搜索"正确地"证明了目标不可达, 而这一关人类可解 — *are* exact substrings) |
| §5.5 (L793) | `tactic 'decide' proved that the proposition ... is false`, cited to `artifacts/repair_report.json` `stale_certificate` | the JSON string ends at `…proved that the proposition` | quoted accurately, but from a different file: the full phrase is `cold-start-a2/A2_REPORT.md` §3 |

### Quotes verified exact

`battery/REPORT_V0.md` "Evidence coverage rewards precisely the caution…" (twice,
§1 and §6.3) · `cold-start-a0/THEORIZE_LOG.md` R-05 "the manual as written says
that pushing up into the Button does nothing…" · R-05 "not thin, zero" ·
`THEORIZE_LOG.md` L-02 "Read literally: over all 275 transitions…" ·
`THEORIZE_LOG.md` preamble "the same instance both built the A0 world at M1 and
adjudicated it at M3" · `cold-start-a0/prime/A0P_REPORT.md` §1 "The variable is
not how much was seen…" (6 lines, exact) · `prime_report.json`
`run_b.certify_lean` ArenaEscape string (exact, including the spacing `(2, 4)`
that `A0P_REPORT.md` renders without spaces — the paper follows the JSON, which
is right) · `cold-start-a2/A2_REPORT.md` §4 "The instrument cannot tell them
apart…" · §2 "Nothing in that column is broken…" · §8 "Nothing about whether an
LLM would have written these manuals…" · `Theoria.md` A2 item (half-width
punctuation preserved) · the INC-004 ruling · `exhibit_report.json`'s `reading`
field · `battery/PREDICTIONS.md` seal declaration "K1, K2, K7 and K8 on A0 are
therefore post-dictions…" · `battery/REPORT_V0.md` power paragraph ·
`gaming_audit.json` "K4 must never be reported without K2 beside it" ·
`theory-compiler/STATUS.md` "本 sprint 唯一的开放问题" and "空公理集"与"证明规模
线性"不同时为真 and 一字未改 · `battery/REPORT_V0.md` "A0 ran engines and hand
adjudication with no LLM in the loop, so it has no model calls" ·
`cold-start-a0/A0_REPORT.md` "Fast Downward is still not connected" (§5 and §6.5,
both) · `engine-rig/tests/test_interop.py` `assert unprovable == [0, 2, 4]`.

One reformatting worth noting rather than faulting: §4.2's code block compresses
`theory-compiler/STATUS.md`'s four separate `lean → 'inv_init' … does not depend
on any axioms` lines into one line reading `'inv_init' / 'inv_closed' / 'inv_all'
/ 'unsolvable'`. It is presented as a code block, not a quotation, and loses no
content — but it is not a transcription.

---

## Source disagreements

| # | the two files | what they disagree about | which the paper followed |
|---|---|---|---|
| 1 | `battery/artifacts/discrimination.json` **vs** `battery/REPORT_V0.md` | the report says "Every discriminative verdict came back `underpowered` or `no-data`"; the JSON has 5 `not-ranked` verdicts alongside the 11 + 13 | **the report** — twice, at §6.4 and §7.4. Under the paper's own precedence rule the JSON wins, and the sentence needs "of the 24 ranked metrics" or similar |
| 2 | `cold-start-a2/A2_REPORT.md` §4 **vs** the two `theory.lean` files | the report says the pair differ "in their weight table and in nothing else"; the files also differ in `step`, `Goal`, header and comments. The report's *own* table lists a differing goal row two lines above the sentence | **the report** — and the claim is promoted into the abstract |
| 3 | `cold-start-a2/artifacts/exhibit_report.json` **vs** `cold-start-a2/A2_REPORT.md` §2 | the JSON's `certify_cheap_vs_full_sweep` block carries `anomalies`, `frames`, `first_anomaly` but **no pixel counts**; the report states 128 unexplained of 20 088 checked | **handled correctly.** §5.4 now reports the JSON's fields and says explicitly that the pixel count "the artefact itself does not carry; it is cited to the report rather than to the JSON". (20 088 = 248 × 81, so it is at least arithmetically consistent) |
| 4 | `cold-start-a0/THEORIZE_LOG.md` Round 0 **vs** `cold-start-a0/A0_REPORT.md` §1 and `artifacts/candidates.jsonl` | 28 vs 29 candidates. The file has 29 rows; the 29th is a `plan` row the log did not adjudicate | **the artefact** (29). Correct, but a reader comparing §3.1 to the log will hit the gap |
| 5 | `cold-start-a0/A0_REPORT.md` §5, §6.5 **vs** `cold-start-a0/STATUS.md` + `artifacts/fd_real.json` | "Fast Downward is still not connected" vs FD built, wired, and agreeing with the stub on all three instances | **handled correctly.** §7.3 cites both, states which is later, and explains that no report is edited after the fact |
| 6 | `CLAUDE.md` **vs** `baseline-arms/TOUCHED_GAMES.md` + `arc-recon/README.md` | "no game has been played … all 25 are registered `never_audited`" vs four dev-pile games at `trajectories_reviewed` and nine sealed games disclosed via INC-BA-001 | **handled correctly.** §7.2 exists precisely to correct it, and the correction checks out row by row |
| 7 | `CLAUDE.md` **vs** `engine-rig/STATUS.md` | six engines / eight milestones / 150 tests vs eight engines / nine milestones / 218 passed, 1 skipped | **handled correctly** in the current draft. §2.2 now says "Six engines carried the acceptances reported here" and names `deadlock_carver` and `ic3_pdr` as M9 additions not exercised by any result. (§8.2 cites `ic3_pdr` as a related-work anchor, which is consistent) |
| 8 | `CLAUDE.md` **vs** `arc-recon/data/piles.json` | the digest is described as the file's sha256 and is not | **the artefact.** §6.7's account is exactly right; both hashes reproduce |
| 9 | `CLAUDE.md` **vs** `engine-rig/DECISIONS.md` D-014 / `engine-rig/interop/README.md` | all three say `lp_potential` is sound but incomplete; `engine-rig/STATUS.md`, which §7.3 cites, does not | **CLAUDE.md's wording, STATUS.md's path.** See the wrong-numbers table |

---

## Audit method

Pass A extraction was scripted, not sampled: every backtick span in the file was
collected, filtered to path-like tokens (containing `/` or ending in a known
extension), and tested with `os.path.exists` first at the repo root and then
against 19 candidate bases. Pass C was likewise scripted — the paper was split
into paragraphs, every paragraph containing a digit was tested for a path-like
backtick span, and the 13 hits were then read by hand to separate genuine orphans
from paragraphs inheriting a section-lead citation. Passes B and D were manual:
each cited artefact was opened (UTF-8 throughout; several sources are Chinese)
and the value read from the named field. The pile digest, the two Lean files and
the battery aggregates were recomputed rather than read.

Scripts were run inline and not saved. Nothing outside this file was modified.
