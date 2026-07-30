# CITECHECK slice B — §4 (A1), §5 (A2) and §6 (A3)

**Audited state.** `papers/phase1-workshop/PAPER.md`, sha256
`6b633fcc35ae612f20f4028eb45aaca1b6ed86a24eb1304af555c46228325376`, **3729**
lines (newline bytes, `wc -l`), **237872** bytes — measured in this worktree, not
copied from a sibling. Slice: lines 909-1668 (§4-§6, including the three-line
`---` separator that closes §6). Auditor: CITECHECK re-run, P18, 2026-07-30.

**Method.** The four passes and the precedence rule ("JSON artefacts beat prose
reports") are copied from `papers/phase1-workshop/CITECHECK.md`, whose own target
was the 1319-line v0.3 draft and is therefore stale as a finding list — eight of
its findings land in this slice and **five of the eight are now fixed** (see
*Regressions and repairs* below). Pass A was scripted (every backtick span in
lines 909-1668, filtered to path-like tokens, tested with `Path.exists` at the
worktree root and then against 16 candidate bases). Pass C was scripted
(paragraph split, every digit-bearing paragraph tested for a path-like backtick
span; 37 hits read by hand to separate genuine orphans from paragraphs inheriting
a lead citation). Passes B and D were manual: every cited artefact opened and the
value read from the named field. Four figures were **recomputed rather than
read** — the two Lean-file diffs, the L1/L2 predictor diff, the peg-5 BFS
reachable set (by calling `engine-rig/interop/peg1d.build_graph`), and the
hybrid Lean development (by calling `generate_lean` on the five-goal problem).
Zero network calls. Nothing outside this report was modified.

**Line mapping.** Verified empirically, not assumed: `assemble.py` prepends a
2-line banner (comment + blank) and joins sections with `\n\n---\n\n`, so a
section's first line is at `3 + Σ(prev lengths) + 3·(prev count)`. Every
section's first and last PAPER.md line was compared byte-for-byte against the
section file's first and last line; all 13 matched. Within this slice:

| PAPER.md lines | section file | offset |
|---|---|---|
| 909-1104 | `sections/04_a1.md` 1-196 | `PAPER − 908` |
| 1105-1107 | separator (blank / `---` / blank) | — |
| 1108-1449 | `sections/05_a2.md` 1-342 | `PAPER − 1107` |
| 1450-1452 | separator | — |
| 1453-1665 | `sections/06_a3_transfer.md` 1-213 | `PAPER − 1452` |
| 1666-1668 | separator | — |

Regenerating `PAPER.md` from `sections/*.md` reproduces the file on disk
byte-for-byte, so the mapping is exact and not merely consistent.

**Rule under test.** "Every quantitative claim carries the repo-relative path of
the artefact it came from."

---

## Sealed-pile discipline

**No sealed-game material was read, and none is named by id.** A regex scan for
the repository's game-id shape (`[a-z0-9]{2,4}[0-9]{2}-[0-9a-f]{8}`) over lines
909-1668 returns **zero** matches, and the same scan over every artefact opened
for this audit (all of `cold-start-a2/artifacts/`, all of
`cold-start-a3/artifacts/`, both `A*_REPORT.md`, both `DECISIONS.md`,
`theory-compiler/STATUS.md`, `theory-compiler/DECISIONS.md`,
`CONTRACTS/dsl_grammar_v0.2.md`) also returns zero. No development-pile id
appears either — §4-§6 are about self-built worlds and a 5-cell peg board, not
about ARC games.

The slice does name **DC22** 12 times, all inside §5.1-§5.2. DC22 is a
sealed-pile game, and this is the exact case INC-004 was ruled on: its *id* is
deliberately absent from `cold-start-a2/` (`cold-start-a2/A2_REPORT.md` §1 says
so in as many words), and the only permitted source for anything about it is the
structural description already printed in `Theoria.md` §1.3. For Pass D I opened
`Theoria.md` §1.3 — the design document, which INC-004 names as the sole
admissible source — and nothing else. **No upstream DC22 artefact was opened,
searched for, or listed.** §5.1's own text is the discipline being followed, not
breached.

---

## Summary

| pass | measure | count |
|---|---|---|
| A | distinct path-like tokens cited in backticks | **74** |
| A | of those, not paths at all (false positives of the extractor) | **2** |
| A | resolve as written, repo-relative from the worktree root | **69** |
| A | resolve only under a section-implied base | **3** (2 distinct files) |
| A | do not exist anywhere in the tree | **0** |
| B | distinct numeric claims traced to a named file and checked | **~130** |
| B | wrong, mis-attributed, or not present in the cited file | **11** |
| C | numbers with no citation at all, or a citation lacking them | **7** (1 overlaps B) |
| D | attributed passages checked (9 blockquotes/code blocks + 17 inline) | **26** |
| D | inexact — compression, case, truncation, punctuation substitution | **5** |

**Bottom line.** No path in the slice is broken, and §4-§6 are, on the whole,
the best-cited stretch of the paper: §5 in particular survives sustained
pressure, and three of its most aggressive self-corrections (the 163/220
denominator, the 52-line Lean diff, the `first_error` truncation) reproduce
exactly when you run them. The rule's failure mode here is concentrated in **§6**,
which is where the paper stops naming the artefact and starts trusting
`A3_REPORT.md`: five of the eleven Pass B findings and six of the seven Pass C
findings are in §6, and §6.3's negative-control table — the one table whose whole
job is to show that the safety valve is real — carries four figures that appear
in no file the paper cites. Three findings are load-bearing rather than cosmetic:
the "35-line diff" that a reader running `diff` gets 20 lines for (B1), the
first-plan comparison that silently swaps arms inside a subsection built on
"like-for-like" (B2), and §6.3's uncited 13/8/891 (B4/C1).

---

## Pass A — path existence

74 distinct path-like backtick tokens in lines 909-1668. Two are extractor false
positives, not citations: `1/1` (L1195, a coverage figure) and
`push_up 56/56 → 38/38` (L1239, a DSL annotation quoted inline). Of the
remaining 72, **all 72 resolve to something in the tree; none is broken.** Three
tokens (two distinct files) are not repo-relative as written.

| cited as | PAPER.md line | section file:line | actually at |
|---|---|---|---|
| `gen_lean.py` | 997 | `04_a1.md`:89 | `theory-compiler/src/theory_compiler/generators/gen_lean.py` — unambiguous (one file in the tree), and cited in full with a line range at L1036 |
| `locate.py` | 1309 | `05_a2.md`:202 | `cold-start-a2/a2pipeline/locate.py` — unambiguous (one file). Its two siblings on the same and adjacent lines, `refute.py` and `probe.py`, **are** cited in full, so the asymmetry sits inside one sentence |
| `locate.py:36` | 1312 | `05_a2.md`:205 | ibid.; line 36 is `from a2world.ground_truth import read_trace` ✓ |

Notes on tokens that resolve but deserve a word:

* `engine-rig/engines/lp_potential` (L973) is a **directory**, not a file, and is
  cited as the producer of a weight vector. It is also the literal value of the
  certificate's `produced_by` field, so the citation is the artefact's own.
* `figures/csv/fig05_a2_repair_loop.csv`, `figures/fig05_a2_repair_loop.py` and
  `figures/out/light/fig05_a2_repair_loop.svg` (L1294-1296) all resolve at the
  **repo root** `figures/` tree, which is the intended one. As slice A notes, a
  second figure tree exists at `papers/phase1-workshop/figures/`; the numbering
  differs, so there is no ambiguity. Not a finding.
* `theory-compiler/src/theory_compiler/generators/gen_lean.py:722-724` (L1036)
  and `cold-start-a2/a2pipeline/probe.py:59` (L1311) are line-anchored
  citations. **Both anchors are correct**: 722-724 is exactly
  `closed it with an empty axiom set. The two proofs are kept **separate and /
  attributed**, because they are not the same argument and a reader should be /
  able to see which one carried which goal:`, and probe.py:59 is exactly
  `from a2world import a2_world  # noqa: E402`. The paper also cites `:786` for
  the concession; line 786 is
  `L.append("  so they are all closed the same way here, by exhausting the")` ✓.
  Line-anchored citations into live code are the most fragile kind in the paper
  and these three are the only ones in the slice; all three hold today.

---

## Pass B — wrong numbers, mis-attributions, numbers absent from the cited file

| # | § | PAPER.md / section:line | paper says | the artefact says | severity |
|---|---|---|---|---|---|
| **B1** | §6.1 | 1488, 1490 / `06`:36, 38 | "the diff between them is **35 lines** confined to `LANDMARKS`, `BOARD`, `is_goal` and `initial_state` — the guard and effect functions are byte-identical, which `cold-start-a3/tests/test_transfer.py` asserts rather than eyeballs" | `test_transfer.py` asserts **no count at all** — `test_the_two_levels_compile_to_the_same_mechanism_code` checks that every differing line matches a `LEVEL_DATA` regex, and `test_the_guard_and_effect_functions_are_byte_identical` extracts the mechanism functions and compares them. `diff generated_l1/theory.py generated_l2/theory.py` gives **20 changed lines in 8 groups**; 35 is the total length of `diff`'s *output* (20 content + 8 range headers + 7 `---` separators), i.e. `diff a b \| wc -l` = 35. The 35 traces to two prose reports: `cold-start-a3/A3_REPORT.md` §3 ("A 35-line diff between two working predictors, all of it level data") and `cold-start-a3/RUN_STATE.md` L25. `papers/phase1-workshop/PROVENANCE.md` L103 repeats the mis-attribution to `test_transfer.py` | **medium-high** |
| **B2** | §6.2 | 1515-1516 / `06`:63-64 | "the cold start needed **333 frames and 332 actions** to reach the same point (`cold-start-a3/artifacts/bill_table.md`)" | `bill_table.md`'s "Cost to first plan" table: `l1_cold_start` = 333/332, `l2_from_scratch` = **337/336**, `l2_transfer` = 1/0. The subsection opens by insisting "The number C3 is about is the **like-for-like** one: the same level, with books against without" and its main table uses the `l2_from_scratch` column throughout; the first-plan sentence silently switches to the L1 arm — a different level, whose plan solves a different problem — while saying "the same point" | **medium** |
| **B3** | §4.2 | 980-984 / `04`:72-77 | "The suite is **83 tests and 83 pass** … **Eight** are gated behind `pytest.mark.skipif(shutil.which("lean") is None, …)` (`theory-compiler/tests/test_gen_lean.py`), so without Lean the run is **75 passed, 8 skipped** (`theory-compiler/STATUS.md`)" | 83/75/8 is verbatim from `STATUS.md` L364 and L367 — but those lines are inside the **P-5 (真 A1) sprint section**, and the same file's later C7 section (L385) records **319 passed, 1 skipped**. `python -m pytest --collect-only` in this worktree collects **364 tests**. Separately, the named file holds **6** lean-gated tests today (`@needs_lean` at 86/97/114/194/249/348), and **4** at the A1 commit `f58959e7`; the rest live in `test_e2e_rehearsal.py` (2), `test_gen_lean_deadlock.py` (2) and `test_ic3_certificate.py` (1), for 11 lean-gated tests in the tree. The paper's own §7.3 handles the analogous `engine-rig` staleness by citing both counts and saying which is later; §4.2 does not | **medium** |
| **B4** | §6.3 | 1572 / `06`:120 | table row "replay certify \| **red**: **13 anomalies, 8 of 891 pixels** unexplained \| **red**: same figures" | Neither cited artefact carries these. `negative_controls.json` records only `caught`, `claimed_a_win`, `anomaly_kinds`, `replay_certify_green`, `static_certify_green`, `theorize_triggered`, `world_is_solvable`; `a3pipeline/negctl.py` computes but does not persist them. The figures are `certify_replay.anomaly_count: 13`, `pixels_unexplained: 8`, `pixels_checked: 891` in **`cold-start-a3/artifacts/arm_l2neg.json`** and **`arm_l2rew.json`** — two files the paper cites **nowhere** (`grep -c` over `PAPER.md` = 0). Values confirmed correct in those files, and identical across both arms, so "same figures" ✓ | **medium** |
| **B5** | §4.2 | 976-978 / `04`:68-70 | "The M8 rehearsal's weights were `[1, 2, 3, 2, 1]`, hand-computed and typed in as literal constants (**D4**, `theory-compiler/DECISIONS.md`)" | D4 (`theory-compiler/DECISIONS.md` L27-31, "素材 B 不变量来源") supports the *characterisation* — "使用文献已知的 pagoda 权重函数（手算验证后直接填入 DSL 作为字面常量）" — but **never states the vector**. `grep` for the vector over `theory-compiler/DECISIONS.md` returns nothing. It is at `theory-compiler/STATUS.md` L296. Known internally and unfixed: `papers/phase1-workshop/OPEN_ITEMS.md` L103, `REVIEW.md` L459, `REVIEW_TRIAGE.md` L100 all flag it | **medium** |
| **B6** | §4.4 | 1009-1010 / `04`:101-102 | "The configuration is genuinely unsolvable — BFS gives reachable set `{00111, 11100, 01001, 10010}`, minimum 2 pegs" | Recomputed: `engine-rig/interop/peg1d.build_graph(5, "11011")["reachable"]["11011"]` = `['00111', '01001', '10010', '11011', '11100']` — **five** states. The initial state is in its own reachable set. The paper's four-element rendering is copied from `theory-compiler/STATUS.md` L333; **the same tree states it correctly as five in two places the paper cites within the same subsection** — `theory-compiler/DECISIONS.md` D-TC-022 ("从 `11011` 出发可达集只有 5 个态（`11011`/`00111`/`11100`/`01001`/`10010`）") and `STATUS.md` L227 ("只有 5 个可达态"). Under the paper's own precedence rule the engine wins. "minimum 2 pegs" ✓ (min over the five is 2) | **medium-low** |
| **B7** | §5.3 | 1236-1243 / `05`:129-136 | "`diff` also shows the header block rewritten, every coverage annotation rescored to the shorter history (`push_up 56/56 → 38/38`, and so on for the other three directions), `events:` losing `jumped`, and `laws:` swapping `teleport_is_colour_triggered` for `right_room_locked`. **Every one of those** is either annotation or a consequence of the deletion" | All four named items verified ✓ (56/56→38/38, 51/51→39/39, 39/39→32/32, 43/43→35/35; `jumped` dropped from `events:`; the law swapped). But the enumeration is not complete, and the next sentence asserts completeness over it: the diff also changes the `Cart` word-table annotation `[segment: uniform_color ev: t0-t247 compress: 1891]` → `[… ev: t0-t183 compress: 1433]` (a *description-length* figure, not a coverage annotation), and deletes four comment blocks — the `compress:` note citing `../artifacts/concept_accounts.json` and THEORIZE_LOG O-04, the three inline `semantics:` glosses, and the six-line thin-evidence block above `teleport_down`. All are annotation, so the paper's *claim* survives; its *list* does not, and the list is what a reader running the diff will check against | **low** |
| **B8** | §5.8 | 1437-1439 / `05`:330-332 | "**It was worked around in A2 before any A2 plan was run**" | `cold-start-a2/DECISIONS.md` D-A2-006 says the opposite in its own words: "A2's goal is reachable only through the teleport, so it produces a wrong answer immediately — **the control manual came back UNSAT on the first attempt**." A plan *was* run before the workaround and returned the defective UNSAT; that is how the defect was found. §5.2's narrower phrasing of the same fact ("before any of these plans were run", L1213-1215) is the defensible one, so the paper contradicts itself between two subsections | **low** |
| **B9** | §6.5 | 1621-1623 / `06`:169-171 | "**Three level constants were supplied, not derived** — the goal cell and the two portal exits … Six of nine fields came from the frame; three did not (`cold-start-a3/artifacts/provenance_l2_transfer.json`)" | `fields` has 9 keys ✓, `derived_fields: 6` ✓, `supplied_fields: 3` ✓. But the three *supplied fields* are `goal_cell`, `landmarks` and `name` — the two portal exits are both inside `landmarks`, and the third supplied field is the level's **name**, which is not a level constant of the world. Three constants live in two fields; the counts coincide at 3 and the members do not. `A3_REPORT.md` §6 makes the same elision ("it *is* three fields the arm did not have to work out") | **low** |
| **B10** | §6.5 | 1617-1619 / `06`:165-166 | "Outside the containment condition — **every guard context** L2 needs was witnessed in L1 —" | `A3_REPORT.md` §6 reads "every **rule-generating** guard context level 2 needs was witnessed in level 1". The dropped adjective is load-bearing: `cold-start-a3/artifacts/ground_truth.json` lists **21** `guard_contexts` (including four `blocked_*` and three `door_*`) against **14** `rule_generating_contexts`. The paper widens a 14-context containment claim into a 21-context one | **low** |
| **B11** | §5.4 | 1274-1279 / `05`:167-172 | "**44 anomalies** across three kinds … — **the cheap layer caps its anomaly list** — … (`cold-start-a2/artifacts/exhibit_report.json`, `certify_cheap_vs_full_sweep`)" | 44 ✓, three kinds ✓, first at t184 cell (6,4) ✓. The **cap** is not in the cited block, which carries no anomaly list at all. It is real but lives in code the paper does not cite: `cold-start-a0/certify/replay.py` L68 and L82, `if len(anomalies) < 40`. Worth naming rather than waving at, because 44 > 40 means the cap actually bites here | **low** |

### Numbers checked and confirmed correct

Traced to the named field of the named file, not to a report. §4-§6 are dense; this
is the whole set, not a sample of it.

* **§4 · the certificate** — `engine-rig/interop/certificates/pagoda_5_11011_to_00010.json`:
  `weights_integer` `[-1, 1, 0, 1, -1]`; `inv_closed.n_checked: 6` with witness
  deltas `0, 0, -2, -2, 0, 0` **in that order**; `inv_init.value: 0`;
  `goal_break` witness `00010` with `potential: 1`; `"verified": true` present;
  `produced_by: "engine-rig/engines/lp_potential"`.
  `theory-compiler/src/theory_compiler/certificate.py` re-derives from
  `weights_integer` and re-enumerates the move geometry (D-TC-009 confirms the
  reason: upstream `verify()` re-does the arithmetic but never checks witness
  completeness).
* **§4 · the negative control** — `theory-compiler/STATUS.md` L343-346: `w .p1`
  1→7, `decide proved ... is false`, all four theorems
  `depends on axioms: [sorryAx]`, exit code 1, and the review's two further
  confirmations (`gen_lean.py` carries no hard-coded vector; the move set is
  derived from the predictor).
* **§4 · the method gap** — `engine-rig/tests/test_interop.py` L68 holds
  `assert unprovable == [0, 2, 4]` verbatim, and L67 `assert provable == [1, 3]`
  independently confirms "certificate for `01000` and `00010` only". Five
  singleton end states ✓. D-014 exists at `engine-rig/DECISIONS.md` L242 and says
  what it is cited for.
* **§4 · E-06's closure** — `cold-start-a0/THEORIZE_LOG.md` L362 books E-06
  **discharged** with the exact reason the paper quotes; `theory-compiler/DECISIONS.md`
  D-TC-022 (L300) supersedes D-TC-010 (L97); the commit order is checkable and
  correct — `f58959e7` is `Tue Jul 28 02:47:59 2026 +0800` and `672044a8` is
  `Tue Jul 28 10:24:29 2026 +0800`, subject `theory-compiler: close E-06 by using
  the second method it already had`.
* **§4 · the hybrid branch** — I generated it. `generate_lean` on the five-goal
  problem emits a `theorem unsolvable` closed by `rintro` / `rw [no_goal_state s]`
  / `Bool.noConfusion` — it **does not invoke `inv_all`**, exactly as the paper
  says; `inv_all` is emitted (line 115 of the output) and referenced only by
  `#print axioms`. The per-goal attribution is a Python-computed comment block
  (output lines 11-19). A1's own fixture `theory-compiler/tests/fixtures/peg5_problem.json`
  has `"goal_states": ["00010"]` ✓, and `theory-compiler/lean/TheoriaLean.lean`'s
  `unsolvable` **does** invoke `inv_all` (L149, `have h1 := inv_all _ hr`) ✓.
  The six tests split exactly as claimed: four generate against a five-goal
  problem (`test_goals_the_certificate_does_not_cover_go_to_the_other_method`,
  `test_the_uncovered_goals_are_closed_by_exhaustion`,
  `test_the_two_methods_stay_attributed`,
  `test_the_hybrid_development_compiles_with_an_empty_axiom_set`) and two check a
  refusal (`test_a_reachable_goal_is_refused_rather_than_proved`,
  `test_an_unenumerable_world_is_still_refused`). `ANY_SINGLE_PEG` is declared at
  `test_gen_lean.py`:280 ✓.
* **§4 · the double-booking** — both halves reproduce. `theory-compiler/STATUS.md`
  books E-06 清偿 in its delivery table (L160, L165) while L325 still heads
  `### 未清偿：新增台账 E-06`; `CONTRACTS/dsl_grammar_v0.2.md` says
  "E-06 was that case and is now discharged" (L255) **and**
  "**E-06 is not discharged, and item 9 is not it.**" (L293).
* **§4.5** — D-TC-008's table gives `computational` empty / `O(2^n)` and
  `algebraic` `propext, Quot.sound` / `O(n)`, with the Lean-4.9-`Int`-lemma
  reason stated ✓; 2^33 on the 33-hole board ✓; `sorryAx`/`ofReduceBool` never
  emitted ✓; one 5-cell fixture ✓; D-TC-012's "32 个占位串里只检查了 5 个 …
  覆盖 31/32" ✓; D-TC-013 ✓; E-01…E-05 discharged at
  `CONTRACTS/dsl_grammar_v0.2.md` L290 with `semantics:` mandatory (L274, L318) ✓;
  `一字未改` at `STATUS.md` L307 ✓; Lean 4.9.0 at `STATUS.md` L14 ✓.
* **§5.2 · the denominators** — `cold-start-a2/artifacts/trace_summary.json`:
  `history_trace.coverage "163/164"`, `scope "every reachable state with the Cart
  in the left room"`, `frames 184`, `transitions 183`, `reachable_states 55`,
  `states_in_scope 41`; `raw_trace.coverage "220/220"`, `scope "every reachable
  state"`, `frames 248`, `states_in_scope 55`; `history_omitted_pairs
  ["cart=(6,4) pressed=1 act=DOWN"]`; `portal_transition 183`; `cut_rule` exact.
  163/220 = 0.7409 → **74 %** ✓ and 163/164 = 99.4 % ✓ — the paper's arithmetic
  and its point both hold, and both readings really are in one file.
* **§5.2 · the six clauses** — `engines_diff.json` has exactly one
  `rules_with_a_jump_effect` entry in the sweep stream (`obj1_jump_DOWN`,
  `coverage "1/1"`, effect `dx 2, dy 1` so |dy|+|dx| = 3 > 1) and an **empty**
  list in the history stream, with `verdict.history_proposes_a_jump: false` ✓;
  `exhibit_report.certify_cheap` = `{transitions 183, pixels_checked 14904,
  pixels_unexplained 0, anomaly_kinds [], frames 184, green true}` ✓
  (14904 = 184 × 81); `certify_lean.axiom_reports [{name unsolvable, axioms []}]` ✓;
  `refutation.episode` = `{length 18, final_win true, win_frames [18]}` ✓ and its
  `verdict` field does name the theorem as the refuted object ✓.
* **§5.2 · the plan differential** — `plan_generated.json` and
  `plan_repaired.json` are both `status SAT, length 18, backend "stub-bfs",
  execution_mismatches []`; `plan_holed.json` is `status UNSAT`. So "SAT in 18 on
  both manuals that contain the teleport rule and UNSAT only on the holed one" ✓.
  `cold-start-a2/a2pipeline/plan.py` L70 is `fd_adapter.solve(domain, instance,
  prefer="stub")` ✓; `engine-rig/engines/fd_adapter/search.py` L165-166 raises on
  budget exhaustion rather than returning ✓; `pddl_addressable` is defined at
  `compile_a2.py`:121 and called at :171 ✓.
* **§5.3 · the exhibit** — `zero_space.region_size: 21`, `value: 1`,
  `difference_rank: 21`, `arena: 37` ✓; `theorem unsolvable : ¬ ∃ s : St,
  Reachable s ∧ Goal s = true` is byte-exact at
  `generated_holed/theory.lean`:784 ✓; "States: 148" in the header of both Lean
  files ✓; `grep -c` for `native_decide`/`Mathlib`/`sorry` = **0** in both ✓;
  `certify_lean.lean` path contains `v4.9.0` ✓; the deleted rule block is
  byte-identical to `theory.dsl` modulo a two-space dedent ✓.
* **§5.4 · the bound** — `certify_cheap_vs_full_sweep` = `{anomalies 44,
  anomaly_kinds [goal_mismatch, render_mismatch, unowned_pixel], frames 248,
  green false, first_anomaly {t 184, cell [6,4], kind render_mismatch, manual 6,
  world 0}}` ✓. The paper reorders the three kinds out of the artefact's
  alphabetical order; it is not presented as a quotation, so not a finding.
  128 unexplained of 20 088 is correctly attributed to `A2_REPORT.md` §2 (L112-113)
  with the explicit note that the JSON does not carry it ✓.
* **§5.5 · the loop** — `loop_ledger.json` `summary {absent 0, fail 0, pass 8,
  total 8}` with beats `M0, M5, L1…L6` ✓; `locate_report.json` `checks
  {mispredicted_step true, misread_board false, wrong_goal_test false}`, `located
  {t 11, mover_at [6,4], action DOWN, manual_predicts [6,4], world_shows [7,6]}` ✓;
  `probe_report.json` `probes_designed 5, run 4, executable 4, not_separable 1,
  trace_frames_before 184, trace_frames_after 196` ✓ and P-03's note carries
  "ranks a separating experiment at **1.0 bits** but classifies it hypothetical"
  with the `tcolor(DOWN)==3` / `at(6,4)` frontier ✓; `theory_repaired.dsl`:78-79
  carries `teleport_is_colour_triggered` with `[depends: teleport_down probe:
  pending]` ✓; `repair_report.stale_certificate.first_error` is line **769**,
  truncated at `…proved that the proposition` ✓, with `axiom_reports [{name
  unsolvable, axioms ["sorryAx"]}]` and `returncode 1`. D-A2-010's sentence is
  quoted exactly and the paper's correction of it is correct: `probe.py`:59 imports
  `a2_world` and uses it at 107-109; `locate.py`:36 imports `a2world.ground_truth`.
* **§5.5 · Figure 3** — all three figure paths resolve. `figures/csv/fig05_a2_repair_loop.csv`
  gives `M0`/`M5` phase `prelude` and `L1`-`L6` phase `loop` ✓, and
  `figures/fig05_a2_repair_loop.py`'s docstring L12-16 states the same split. The
  claim "the plate never shows the ledger's own 8/8 summary" **holds**: the string
  `8/8` occurs once in `fig05_a2_repair_loop.svg` and only inside an XML comment,
  never as rendered text. (The CSV audit layer *does* carry `ledger_beats_total = 8`
  and `ledger_beats_pass = 8` in `accounting` rows — a nuance, since the paper
  cites the CSV as "numbers" in the same parenthesis, but the sentence is about
  the plate and the plate is clean.)
* **§5.6 · the two Lean files** — recomputed. `diff -u` gives **7 hunks**; plain
  `diff` gives **52 changed lines in 15 groups**; the paper's account of why the
  two groupings differ is exactly right. The 52 account for themselves:
  28 weight-table lines (14 entries × 2, at 723/724, 729/730, 735/736, 741/742,
  747/748, 752/753, 755/756), 8 `step`-table lines (4 entries × 2, at 243, 391,
  539, 687, each `Cell.c31` → `Cell.c35`, one per colour × door stratum), 2 for
  `def Goal` (711, `Cell.c10` → `Cell.c34`), 2 for the header line (3,
  `a2-holed` → `a2-repaired`), 12 for the comment region above `def I`
  (758-766). 28 + 8 + 2 + 2 + 12 = 52 exactly. `c10 = (2, 7)` and `c34 = (7, 1)`
  are both in the files' own cell maps (L21, L45) ✓; `=> 0` counts are 21 in the
  holed file and 35 in the repaired one ✓, matching the two files' own comments
  ("w = 0 exactly on the 21 cells" / "w = 0 on the 35 cells"). "0 of 55
  reachable states" is `A2_REPORT.md` §4 L178 verbatim ✓. And the hedge about
  `generated_repaired_stale/` is better than hedged: that file's `def Goal` **is**
  `Cell.c10` with the 21-cell weight table and it fails — so "nearly what
  `generated_repaired_stale/` already is" understates its own case.
* **§5.7** — `probes.jsonl` P-01 holds
  `predictions.holed_manual__nothing_happens: "stays"` against
  `observation: "jumps to (7,6)"`, with a `note` confirming the prediction was on
  the record before the action ✓; `engines_diff_probed.json`
  `verdict.probed_evidence_proposes_a_jump: true` with `obj1_jump_DOWN` at
  transition 194 ✓; `test_the_repair_agrees_with_the_control_on_that_rule` exists
  at `cold-start-a2/tests/test_a2.py`:154 and does compare the extracted `when`
  clause of `teleport_down` for equality ✓.
* **§5.8** — D-A2-006 confirms every mechanical clause: `gen_pddl_a0::_problem`
  emits cell objects only for `problem.arena` cells; a static coloured Portal
  entry is in neither the floor nor the dynamic set; `teleport-down`'s
  `?p - markedcell` never grounds; A0's goal was reachable through the Door so the
  bug was latent and "produced a correct answer by luck" ✓. D-A2-007 confirms the
  locale-decode failure (`subprocess.run(text=True)`, GBK, U+2019 and ⟨⟩ in
  *error* messages only) and that A0 never had a red Lean file ✓.
  `upstream_pin.json` is a per-file `sha256` map (22 entries) — §5.8 states no
  count, so it is clean here; the "258 files" problem is §7.3's, i.e. slice C's.
* **§6.1** — `ground_truth.json` `levels.a3-l1.truth.reachable_states: 62` and
  `a3-l2: 63` ✓. **Eight placed cells, all eight moved**: `cart_start`
  (6,1)→(6,7), `door_cell` (6,7)→(3,1), `exit_a` (1,6)→(1,5), `exit_b`
  (3,2)→(4,1), `goal_cell` (7,7)→(1,1), `portal_a` (2,2)→(5,1), `portal_b`
  (2,6)→(1,6), `switch_cell` (4,1)→(7,6). That is the strongest claim in §6.1 and
  it is exactly true.
* **§6.2** — every cell of the bill table matches `bill_table.md`'s like-for-like
  block: 347/11 → 0.0317 (paper 0.032 ✓), 346/10 → 0.0289 (paper 0.029 ✓), 1/0,
  35/0, 5/0, 33/0, and compile/certify/plan 1/3/1 both sides ✓. Transfer-arm
  first-plan cost 1 frame / 0 actions ✓. `arm_l2_transfer.json`: `outcome "win"`,
  `execution.actions_spent 10`, `plan {status SAT, length 10, backend
  "stub-bfs"}`, `certify_replay {frames 11, pixels_checked 891, anomaly_count 0,
  green true}`, `certify_lean.axiom_reports [{name inv_all, axioms []}]` ✓. Plan
  length 10 equals `ground_truth.json`'s `a3-l2.truth.shortest_solution_length: 10` ✓.
  (`outcome` is top-level and `actions_spent` is nested under `execution`; the
  paper prints them as a pair. Nit, not a finding.)
* **§6.2 · the tie at ceiling** — `score_vs_truth.json` `results[1]` (carried
  manual, "THE CARRIED MANUAL on a level it never explored") = 252/252 and
  `results[2]` ("the control arm's manual, induced from level 2's own sweep") =
  252/252 ✓. The index `results[2]` is correct 0-based, and
  `theory/generated_l2_scratch/` exists ✓. This is the paper's own correction of
  an earlier one-sided denominator and it checks out.
* **§6.3** — `negative_controls.json` `all_caught: true`,
  `none_claimed_a_win: true`, `static_layer_caught_any: false`, and per control
  `static_certify_green true`, `replay_certify_green false`,
  `theorize_triggered true`, `claimed_a_win false`, `world_is_solvable`
  false/true ✓. Recomputed independently: the two controls' `plan.actions` and
  `plan.directions` are **byte-identical** to the honest transfer arm's, so
  "the same plan" is literally true. `a3-l2-rewired` solvable in 15 ✓ (both
  `ground_truth.json`'s `shortest_solution` length and `negctl.py` L35).
  Every arm artefact has `plan.backend: "stub-bfs"` — all six of them ✓.
* **§6.4** — `domain_agreement.json` `as_written.strict_agreement: 0.0` → 0 % ✓;
  `canonical_agreed: 20` against `canonical_rules_left: 20` ✓;
  `canonical_only_in_right: [8 items]` ✓; blind arm 5 theorize rounds against the
  L1 cold start's 1 ✓ (`bill_table.md`). (The artefact also carries
  `canonical_agreement: 0.7143` = 20/28, the two-sided figure; the paper gives the
  one-sided "all 20 of L1's clauses" but immediately prints the 8, so a reader can
  reconstruct it.)
* **§6.5** — the six items are a faithful compression of `A3_REPORT.md` §6's six
  bolded headings, in order. The report has a **seventh** bolded item
  ("`fd_adapter` is still the bundled BFS stub"), and the paper correctly moves it
  out of the six into its "Two further caveats" paragraph rather than
  miscounting ✓. The playbook claim is exactly right and is the sharpest negative
  check in §6: `cold-start-a3/theory/playbook.dsl` L18 cites
  `tests/test_transfer.py::test_the_playbook_is_byte_identical_across_levels`, and
  `grep -rn` over the whole tree finds that name **only in the two playbook.dsl
  files themselves** — the test does not exist ✓.
* **§6.6** — A3-I1 (`cold-start-a3/DECISIONS.md` L272) confirms every clause:
  round 3, a Lean diagnosis, the docstring of
  `a3pipeline/compile_a3.switch_latch_invariant` naming `Switch`, `Door` and
  `switch_door_latch`, the unprompted disclosure with a self-proposed remedy,
  names contaminated / verdicts not ("All of them were fixed in round 1, two
  rounds before the read. Rounds 2–4 changed none"), and the convergence result
  resting on the preserved `as_written` snapshot ✓. Four defects ✓
  (D-A3-003/004/005/007), and the two the paper elevates are the two the report
  itself calls unsound: D-A3-005 ("a confident **UNSAT for a correct manual** …
  That is unsound, not incomplete") and D-A3-007 (`I := true`, every gate green,
  empty axiom list, proves nothing) ✓. `cold-start-a3/theory/generated_l1_vacuous/`
  exists and holds all six forms ✓.

---

## Pass C — uncited numbers

Seven. C1 is the same defect as B4, counted in both passes because it fails both
tests; the other six are citation gaps rather than wrong values.

| # | § | PAPER.md / section:line | the claim | what it would need |
|---|---|---|---|---|
| **C1** | §6.3 | 1572 / `06`:120 | "13 anomalies, 8 of 891 pixels unexplained" | a path. See B4: the figures are in `cold-start-a3/artifacts/arm_l2neg.json` / `arm_l2rew.json` (`certify_replay.anomaly_count`, `pixels_unexplained`, `pixels_checked`), neither of which the paper cites anywhere |
| **C2** | §6.3 | 1557-1558 / `06`:105-106 | "The level becomes unsolvable; reachable states drop from **63 to 34**" | a path. The bullet's citation is `cold-start-a3/a3pipeline/negctl.py`, which carries the *15* (L35, "Level 2 stays solvable in 15") but not 63 or 34. Those are `ground_truth.json`'s `a3-l2.truth.reachable_states: 63` and `a3-l2-oneway.truth.reachable_states: 34`, cited two subsections earlier for a different claim |
| **C3** | §6.3 | 1568 / `06`:116 | table row "first frame vs honest L2 \| **byte-identical** \| byte-identical" | a path. No artefact records it; the source is `cold-start-a3/A3_REPORT.md` §5 ("the rendered first frames are **byte-identical** to level 2's — a test asserts it"), which the paper cites thirteen lines later for a different quotation |
| **C4** | §6.3 | 1570, 1573 / `06`:118, 121 | "plan \| SAT, **length 10** — the same plan" and "Lean \| green \| green" | a path. Both are in the uncited `arm_l2neg.json` / `arm_l2rew.json` (`plan.length: 10`, identical `plan.actions`, `certify_lean.green: true`). All three values are correct — I recomputed the plan identity — but the reader has no way to get to them |
| **C5** | §6.6 | 1658-1665 / `06`:206-213 | "**four defects** in the toolchain … the PDDL backend cannot encode more than one portal … a Lean invariant helper keyed on object *name* silently degrades to `I := true`" | a path. The paragraph carries none; the preceding paragraph's `cold-start-a3/DECISIONS.md` (cited for A3-I1) does contain D-A3-003/004/005/007, and `A3_REPORT.md` §7 is titled "Four defects found in the reused instrument", but neither is attached and neither decision id is named |
| **C6** | §6.1 | 1483 / `06`:31 | the three-arm table's **blind control** row cites `cold-start-a3/artifacts/domain_agreement.json` | the arm's own artefact. The other two rows cite `arm_l1_cold_start.json` and `arm_l2_transfer.json`; `domain_agreement.json` is a manual-vs-manual comparison, not the arm's bill or result. `cold-start-a3/artifacts/arm_l2_from_scratch.json` exists, is where §6.2's entire "L2 from scratch" column comes from, and is cited **nowhere in the paper** |
| **C7** | §5.7 | 1420 / `05`:313 | "asserted by a test — `test_the_repair_agrees_with_the_control_on_that_rule`, byte-identical `when` clauses" | a path. The test is named without one; it is at `cold-start-a2/tests/test_a2.py`:154. Not a number, but the same rule: the reader is invited to check something and not told where |

Paragraphs that *look* orphaned and are not, checked and cleared: §5.1's
difference table (lead cites `A2_REPORT.md` §1, and the table is byte-identical to
it), §5.3's deleted-rule code block (lead cites both DSL files on L1236), §5.6's
bullet list (lead names both Lean files), §6.2's bill table (lead cites
`bill_table.md`), §4.4's E-06 narrative paragraph (contains no measurement).

---

## Pass D — quote fidelity

26 attributed passages checked: 9 blockquotes and code blocks, 17 inline
attributed fragments. Five are inexact. Every check was byte-for-byte after
unfolding the paper's hard wrap and stripping the source's own `>` markers;
nothing was accepted on the strength of a keyword match.

| # | § | PAPER.md / section:line | quoted as | source | problem |
|---|---|---|---|---|---|
| **D1** | §4.2 | 940-951 / `04`:32-43 | a fenced block introduced by "`theory-compiler/STATUS.md` **records** the accepted chain" | `theory-compiler/STATUS.md` L275-288 | 10 of the 11 lines are byte-identical, full-width punctuation included. The source's **four separate lines** — `lean → 'inv_init' does not depend on any axioms`, then `'inv_closed'`, `'inv_all'`, `'unsolvable'` — are compressed into one line reading `lean → 'inv_init' / 'inv_closed' / 'inv_all' / 'unsolvable'`. Presented as a transcription of a record; a reader grepping for that line finds nothing. Inherited from `CITECHECK.md`'s closing note and **not fixed** |
| **D2** | §6.2 | 1547-1548 / `06`:95-96 | > Replay against a trajectory answers **"**is the manual consistent with what I saw**"**. This answers **"**is the manual right**"**. | `cold-start-a3/artifacts/score_vs_truth.json`, `reading` | two defects. (a) The artefact uses **single** quotes — `'is the manual consistent with what I saw'` — and the paper silently substitutes double. (b) The `reading` field has a **third sentence** the paper drops with no ellipsis: "For the carried manual the level was never explored, so this is the accuracy of transfer rather than of induction." That sentence is the one that says what the number measures, in a subsection whose whole argument is about what the number measures |
| **D3** | §4.4 | 1056-1057 / `04`:148-149 | "The generator's own banner says it in the file it emits: **"they are all closed the same way here, by exhausting the reachable set.**"" | `gen_lean.py`:786-787 | the emitted text is "**so** they are all closed the same way here, by exhausting the reachable set." The leading "so" is dropped without an ellipsis, and the two `L.append` fragments are joined across the emitted line break. Content otherwise exact |
| **D4** | §4.4 | 1075 / `04`:167 | "**t**his used to assert a refusal, and the change is the point (E-06)" | `theory-compiler/tests/test_gen_lean.py`:127 | the docstring opens "**T**his used to assert a refusal…". Case altered inside quotation marks. Trivial in isolation, listed because a reader grepping the exact string gets nothing. The same class covers §4.4's "close E-06 by using the second method it already had" (L1067), which elides the commit subject's `theory-compiler: ` prefix without an ellipsis, and §4.4's "**E-06 is not discharged**" (L1071), whose source bold span runs on to ", and item 9 is not it." |
| **D5** | §5.5 | 1335-1336 / `05`:228-229 | the diagnosis is **"missing rule, not wrong rule"** … (`cold-start-a2/artifacts/locate_report.json`) | `locate_report.json` reads "the defect is a **MISSING RULE, not a wrong one**" | quoted accurately, but from a different file. The exact lowercase string is `cold-start-a2/artifacts/loop_ledger.json`, `beats[L2].detail.diagnosis: "missing rule, not wrong rule"` — cited five lines earlier, at L1326, for the beat count |

### Quotes verified exact

* `Theoria.md` Phase 1's **A1 孔明棋** bullet (§4.1, L916-917) — byte-exact once
  the wrap is unfolded, **half-width punctuation preserved throughout**. This is
  `CITECHECK.md`'s §4.1 finding, now fixed.
* `Theoria.md` §1.5 "三个小检查代替无穷穷举,检查量与状态空间大小无关" (§4.1,
  L927-928) — byte-exact, half-width comma preserved. `CITECHECK.md`'s finding,
  fixed.
* `Theoria.md` Phase 1's **A2 DC22 重放** bullet (§5.1, L1114-1116) —
  byte-exact.
* the **INC-004 ruling** (§5.1, L1124-1128) — byte-exact against
  `cold-start-a2/A2_REPORT.md` L23-27, modulo the source's own `>` markers.
* `cold-start-a2/A2_REPORT.md` §1's five-row difference table (§5.1, L1132-1139)
  — byte-exact, all five rows.
* the **six `Theoria.md` §1.3 clause quotes** (§5.2 table, L1195-1200) — all six
  are exact substrings of §1.3: `漏了一条传送规则`,
  `缺的那条传送规则从未触发`, `不欠任何一帧`, `模型重放 175/175 全对`,
  `完备搜索"正确地"证明了目标不可达`, `而这一关人类可解`. `CITECHECK.md` found
  two of these compressed ("那条规则从未触发", "重放全对"); **both are fixed**.
  §5.2's surrounding characterisation of the same paragraph ("a perfect replay
  score can coexist with bankrupt understanding", "the failure is structural
  rather than an implementation flaw") also tracks the source
  ("模型预测满分,理解破产", "不是实现瑕疵,是方法的构造决定的").
* `cold-start-a2/A2_REPORT.md` §2 "Nothing in that column is broken…" (§5.3,
  L1267-1270) — byte-exact, bold markers included.
* `cold-start-a2/artifacts/exhibit_report.json`'s `reading` field (§5.4,
  L1288-1290) — byte-exact, all three clauses.
* `cold-start-a2/DECISIONS.md` D-A2-010 "import no world module at all" (§5.5,
  L1310) — exact, and the paper's refutation of it is correct on both imports.
* the `first_error` truncation note (§5.5, L1348-1351) — the paper says the JSON
  string stops at `…proved that the proposition` (true) and attributes the full
  `tactic 'decide' proved that the proposition ... is false` to
  `cold-start-a2/A2_REPORT.md` §3 (true, L159-160). This is `CITECHECK.md`'s §5.5
  finding, **fixed by disclosure** — the paper now names the discrepancy instead
  of papering over it.
* `theory-compiler/STATUS.md` fragments: `本 sprint 唯一的开放问题` (L1082),
  `未清偿：新增台账 E-06` (L1078), `"空公理集"与"证明规模线性"不同时为真`
  (L1085, flagged "verbatim in substance" and dropping only the trailing 。),
  `一字未改` (L1104), `decide proved ... is false` and
  `depends on axioms: [sorryAx]` (L995-996) — all exact.
* `CONTRACTS/dsl_grammar_v0.2.md` "E-06 … is now discharged" (L1078) — the
  ellipsis is honest; the source reads "E-06 was that case and is now discharged".
* `cold-start-a0/THEORIZE_LOG.md` E-06's discharge reason (L1035) — exact.
* `gen_lean.py` "kept **separate and attributed**, because they are not the same
  argument" (L1036-1037) — exact after unfolding one source wrap.
* `cold-start-a3/A3_REPORT.md` §5 "Carrying a domain to a new level buys a plan
  for zero actions…" (§6.3, L1581-1583) — byte-exact.
* `cold-start-a3/A3_REPORT.md` §4 "The gap between 0 % and full agreement is not
  noise…" (§6.4, L1602-1604) — byte-exact.
* §5.3's deleted `rule teleport_down` code block (L1245-1248) — byte-identical to
  `cold-start-a2/theory/theory.dsl` modulo a uniform two-space dedent.

---

## Regressions and repairs since `CITECHECK.md`

`CITECHECK.md` targeted a 1319-line draft. Eight of its findings fall inside what
is now §4-§6. Recording the disposition because an audit series that never checks
whether its own findings were acted on is decoration.

| `CITECHECK.md` finding | status now |
|---|---|
| §5.5 Lean `first_error` quoted from the wrong file | **fixed by disclosure** — §5.5 now states the truncation and names `A2_REPORT.md` §3 |
| §5.2 table "那条规则从未触发" a compression | **fixed** — now the exact `缺的那条传送规则从未触发` |
| §5.2 table "重放全对" a compression | **fixed** — now the exact `模型重放 175/175 全对` |
| §4.1 A1 bullet's punctuation silently normalised to full-width | **fixed** — half-width throughout |
| §4.1 "三个小检查代替无穷穷举,…" half-width comma | **fixed** |
| Abstract/§1.2/§5.6 the two Lean files "differ in their weight table and in nothing else" | **fixed, and well** — §5.6 now corrects the source report, gives 52 lines / 7 hunks / 15 groups, itemises the `Goal`, four `step` entries and two comment regions, and explains what is lost with the false version. Every figure reproduces |
| §4.2's four-line `lean →` block compressed into one | **not fixed** (D1) |
| §4.2 `[1,2,3,2,1]` cited to D4, which never names it | **not fixed** (B5), despite being flagged in `OPEN_ITEMS.md`, `REVIEW.md` and `REVIEW_TRIAGE.md` |

Two findings in this slice are new-in-kind rather than inherited, and both are in
§6: **B1** (a check the paper invites the reader to run, which returns a different
number) and **B4/C1** (a table of results whose figures are in files the paper
never names). §6 is the youngest section in the slice and the least
artefact-anchored; §5, by contrast, has clearly been audited hard already and
holds up.

---

## What this audit could NOT check

Stated so the coverage claim above is not read as more than it is.

1. **Whether `theory-compiler`'s suite actually passes.** I collected it (364
   tests) and read the lean gates, but did not execute the suite. B3's finding is
   about the *counts* the paper attributes to `STATUS.md`, not about pass/fail.
2. **Whether the generated Lean actually compiles.** `lean` is on PATH in this
   worktree (`/c/Users/user/.elan/bin/lean`), but I did not run it on any file. All
   green/red/axiom-list verdicts in §4-§6 were read from the artefacts that record
   them (`exhibit_report.certify_lean`, `repair_report.certify_lean`,
   `arm_*.certify_lean`), not re-derived. A stale artefact would pass this audit.
3. **The figure plate's rendering.** I grepped `fig05_a2_repair_loop.svg` for the
   `8/8` string and read the CSV audit layer, but did not regenerate the figure or
   compare the plate to its CSV. "Drawn as prelude" is checked at the level of the
   CSV's `phase` column and the script's docstring, not of the pixels.
4. **`exhibit_report.certify_cheap_vs_full_sweep`'s 44 against the capped list.**
   The cap is at 40 for two of the three anomaly kinds (`replay.py` L68, L82), so
   44 total is consistent with a capped list, but I did not re-run the sweep to
   confirm that 44 is the true count rather than a partially-capped one. This is
   the one number in §5.4 I can neither confirm nor refute.
5. **`figures/` determinism and the CSV's `evidence` aliases.** The CSV cites
   registry keys (`a2_trace_summary:raw_trace.frames`), not repo-relative paths. I
   spot-checked several against the artefacts and they were right, but I did not
   resolve the registry systematically — the alias table itself was not opened.
6. **Anything about DC22.** By rule. §5.1-§5.2's claims *about the substitution*
   are checkable and were checked (INC-004's ruling text, the isomorphism table,
   the six §1.3 clauses); its claims about DC22's own geometry, coverage or search
   are deliberately unverifiable and the paper says so.
7. **The 175-frame figure** (§5.1's table, inherited from `A2_REPORT.md` §1)
   traces to `Theoria.md` §1.3, which INC-004 permits, and I confirmed it appears
   there as `模型重放 175/175 全对`. No upstream artefact was consulted, and none
   could be.
8. **`cold-start-a3/A3_REPORT.md` §§1-2, 7-9 and `cold-start-a2/THEORIZE_LOG.md`
   were read only where a claim pointed into them.** Neither was read end to end,
   so a contradiction sitting in an unvisited paragraph of either would not appear
   here. §4's `theory-compiler/STATUS.md` and both `DECISIONS.md` files *were*
   read in full, which is how B6's five-vs-four reachable set and B5's D4 gap
   surfaced.

Both sibling reports were consulted for method and are **incomplete as delivered**:
`citecheck-A-abstract-to-s3.md` ends after Pass A (77 lines, no Pass B/C/D
sections), and `citecheck-C-s7-to-s8.md` ends at line 43 with "*(report in
progress — sections appended as each pass completes)*". Their summary tables state
Pass B/C/D counts that their bodies do not substantiate. This report's counts are
substantiated by the tables above; where I could not check something it is in the
list immediately above rather than absorbed into a total.
