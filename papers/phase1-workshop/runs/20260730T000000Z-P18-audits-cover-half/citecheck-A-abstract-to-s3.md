# CITECHECK slice A — Abstract, §1, §2 and §3

**Audited state.** `papers/phase1-workshop/PAPER.md`, sha256
`6b633fcc35ae612f20f4028eb45aaca1b6ed86a24eb1304af555c46228325376`, **3729**
lines (`wc -l`), **237872** bytes — recomputed in this worktree
(`.worktrees/p18-audits-cover-half-the-paper`, branch
`agent/p18-audits-cover-half-the-paper`), not copied from the stub this file
replaces. The stamp is unchanged from the stub's, so **the paper did not move
under the audit**; the earlier figures were right and are re-derived here rather
than inherited. Slice: lines 1-908 (title block, Abstract, §1, §2, §3, including
the three-line `---` separator that closes §3). Auditor: CITECHECK re-run, P18,
2026-07-30.

**What this file replaces.** The previous version of this report was a stub: a
Summary table asserting Pass A 69/62/7/0, Pass B "~95 checked, 8 wrong", Pass C
9, Pass D 14/4, and a Bottom line naming three load-bearing findings — followed
by a Pass A section and **nothing else**. Passes B, C and D had no bodies at all,
so five of its nine numbers were unfalsifiable and three named findings were
unexaminable. Every count below was re-derived. Where the stub was right it is
confirmed and shown; where it was wrong it is corrected and said to be wrong.
Net: **Pass A confirmed** (69/62/7/0), **Pass B 8 → 12**, **Pass C 9 → 8**,
**Pass D 14 checked → 25, 4 inexact → 5**, and **one of the stub's three
load-bearing findings does not exist** — the §1.2 five-family split it named as
a defect is correct in the file it cites, field for field.

**Method.** The four passes and the precedence rule ("JSON artefacts beat prose
reports") are copied from `papers/phase1-workshop/CITECHECK.md`, whose own target
was the 1319-line v0.3 draft and is therefore stale as a finding list — nine of
its findings land in this slice and **eight of the nine are now fixed** (see
*Regressions and repairs*). Pass A was scripted: every backtick span in lines
1-908 (262 of them), filtered to path-like tokens (containing `/` or ending in a
known extension), tested with `Path.exists` at the worktree root and then against
20 candidate bases. Pass C was scripted the same way (paragraph split, every
digit- or number-word-bearing paragraph tested for a path-like backtick span; 48
hits read by hand to separate genuine orphans from headings, quote blocks and
paragraphs inheriting a lead citation). Passes B and D were manual: every cited
artefact opened and the value read from the named field. Four figures were
**recomputed rather than read** — the paper's own word count (by replicating
`assemble.py`'s `len(body.split())`), the 88/7 development-pile split of the
battery's 95 runs, the 112-attack / 95-success census of the blind round's
delivered artefact, and the 83.6 % cache-TTL share of the cost gap. Zero network
calls, zero API calls. Nothing outside this report was modified.

**Line mapping.** Verified empirically, not assumed. `assemble.py` prepends a
2-line banner (comment + blank) and joins sections with `\n\n---\n\n`, so a
section's first line sits at `3 + Σ(prev lengths) + 3·(prev count)`. I
regenerated the whole file from `sections/*.md` in memory: **the reconstruction is
byte-identical to `PAPER.md` on disk** (same sha256), and every one of the 13
sections' first and last lines was compared byte-for-byte against its section
file's first and last line — 13/13 matched. Within this slice:

| PAPER.md lines | section file | offset |
|---|---|---|
| 3-148 | `sections/00_abstract.md` 1-146 | `PAPER − 2` |
| 149-151 | separator (blank / `---` / blank) | — |
| 152-487 | `sections/01_intro.md` 1-336 | `PAPER − 151` |
| 488-490 | separator | — |
| 491-624 | `sections/02_framework.md` 1-134 | `PAPER − 490` |
| 625-627 | separator | — |
| 628-905 | `sections/03_a0.md` 1-278 | `PAPER − 627` |
| 906-908 | separator | — |

Line 1 is the generated banner and line 2 is blank; neither is in any section
file. Every section:line reference below was spot-checked by reading that line
out of the section file, not computed and trusted.

**Rule under test.** "Every quantitative claim carries the repo-relative path of
the artefact it came from." The draft-status box (L21-25) adds the exemption this
slice must judge: **the abstract is exempt "by convention" — and the exemption
holds "only because every figure below recurs, cited, in the body."** That
conditional is testable, and it is tested here.

---

## Sealed-pile discipline

**No sealed-game material was read.** A regex scan for the repository's game-id
shape (`[a-z0-9]{2,4}[0-9]{2}-[0-9a-f]{8}`) over lines 1-908 returns **zero**
matches — no development-pile id and no sealed-pile id appears anywhere in the
slice. The slice names **DC22** exactly once, at L393 (§1.4), for the *structural
shape* only; its two sources are `Theoria.md` §1.3 and `cold-start-a2/A2_REPORT.md`
§1's INC-004 ruling, which is the single permitted route. I opened both. **No
upstream DC22 artefact, and no artefact of any sealed game, was opened, listed or
searched.** `environment_files/` was never touched.

Two disclosures, so this is not read as broader than it is:

* I opened `arc-recon/data/piles.json` to check §1.0's "development pile of four
  and a sealed pile of 21". That file is the *cut*, not game content, and reading
  it is what CLAUDE.md directs; its `contamination_register` enumerates ids and
  nothing about mechanics. No sealed game's rules, levels, trajectories or
  released artefacts were read.
* §9's live-run manifest (opened for the abstract's cost chain) is on
  `g50t-5849a774`, a **development-pile** game.

---

## Summary

| pass | measure | count |
|---|---|---|
| A | backtick spans in lines 1-908 | 262 |
| A | of those, path-like | 151 spans / **69 distinct tokens** |
| A | resolve as written, repo-relative from the worktree root | **62** |
| A | exist, but **only** under a section-implied base | **7** |
| A | do not exist anywhere in the tree | **0** |
| B | distinct numeric or field-level claims traced to a named file and checked | **~125** |
| B | wrong, stale, mis-attributed, or not present in the cited file | **12** |
| C | numbers with no citation at all, or a citation lacking them | **8** (5 overlap B) |
| D | attributed passages checked (11 blockquotes/code blocks + 14 inline) | **25** |
| D | inexact — insertion, case, truncation, or a rendering matching no source | **5** |

**Bottom line.** No path in the slice is broken, and §3's A0/A0′ material is the
best-anchored stretch of this half of the paper: the A0 artefacts
(`score_vs_truth.json`, `trace_summary.json`, `candidates.jsonl`,
`engines_report.json`, `prime_report.json`) support essentially everything §3.1,
§3.2, §3.4, §3.5 and §3.6 say, down to `base.behavioural.accuracy: 0.987288` and
the three `uncovered_pairs` matching the three `held_out` examples item for item.
The failure mode is concentrated in two places instead.

The first is **§1.2**, which is the paper's strongest section and its most
citation-strained: five of the twelve Pass B findings and four of the eight Pass
C findings are there, all of the same kind — a number that is true in *some*
battery file, attached to a different battery file. The worst is B3, where the
parenthesis meant to disclose a discrepancy gets both halves wrong: it cites
`mechanism_epistemic.py` for eighteen (that file says nineteen) and says "§7.7
says nineteen" (§7.7 says eighteen, and names the test file that holds it).

The second is **inherited prose that the artefacts contradict**. B1 is the
sharpest thing in this slice: §3.3 says A0's three errors are "the Button pressed
from above, from below and from the right", and the artefact's own
`uncovered_pairs` make the third one **from the left** — "from the right" is
precisely the direction that *was* witnessed, modelled, and got right. The gloss
is byte-inherited from `cold-start-a0/THEORIZE_LOG.md`'s seal section and
`A0_REPORT.md` §2, so the paper is faithful to a source that is wrong, which is
exactly the case the precedence rule exists to decide. B2 is the same shape one
layer out: §3.2's parenthetical warning that an artefact "has since moved on" is
itself stale — it reports 5704 where the artefact now says 5284, and
`cold-start-a0/DECISIONS.md` records the move.

Three findings are load-bearing in the sense of surviving into a headline, and
they are resolved individually below: the abstract's cost/leak chain **verifies
completely** except that "84 %" recurs in the body only as 83.6 %; the §1.5 arm
census **is exactly right**, all five arm counts and both the 88/7 split; and the
§1.2 five-family split **is in the file it cites** and the stub's third finding
therefore does not exist. Against that, the one wholly uncited number in the
slice is the one on the front page: the draft-status box's "roughly 27 500 words"
is **36 242** by the paper's own generator.

---

## Pass A — path existence

262 backtick spans in lines 1-908; 151 are path-like, giving **69 distinct
tokens**. **All 69 resolve to something in the tree; none is broken.** Seven are
not repo-relative as written.

| cited as | PAPER.md line | section file:line | actually at |
|---|---|---|---|
| `PAPER.md` | 26 | `00_abstract.md`:24 | `papers/phase1-workshop/PAPER.md` |
| `assemble.py` | 27 | `00_abstract.md`:25 | `papers/phase1-workshop/assemble.py` |
| `A0_REPORT.md` | 349 | `01_intro.md`:198 | `cold-start-a0/A0_REPORT.md` — unambiguous (one file), and cited in full fifteen times elsewhere in the slice |
| `playbook.dsl` | 506 | `02_framework.md`:16 | ambiguous — **15** tracked files carry exactly this name (`git ls-files`); §2.1 means `cold-start-a0/theory/playbook.dsl`. The manual on the line above **is** cited in full as `cold-start-a0/theory/theory.dsl`, so the asymmetry sits inside one bullet pair |
| `THEORIZE_LOG.md` | 549 | `02_framework.md`:59 | ambiguous — **6** tracked files (`a0-spike/`, `cold-start-a0/`, `cold-start-a0/prime/`, `cold-start-a2/`, `cold-start-a3/`, `theoria-arm/`). Generic use ("written down by the LLM in a `THEORIZE_LOG.md`"), and four are enumerated in full three lines later at L552-553 |
| `A0P_REPORT.md` | 757 | `03_a0.md`:130 | `cold-start-a0/prime/A0P_REPORT.md` (cited in full at L738, nineteen lines earlier) |
| `prime_report.json` | 829 | `03_a0.md`:202 | `cold-start-a0/prime/artifacts/prime_report.json` (cited in full at L820, nine lines earlier) |

The stub's Pass A counts (69 / 62 / 7 / 0) are **correct and are confirmed**. Two
of its per-row facts are not, and are corrected above: `playbook.dsl` is 15 files,
not 16; `THEORIZE_LOG.md` is 6 files, not 4, and the stub's enumeration listed
`cold-start-a0/prime/` while omitting `cold-start-a3/` and `theoria-arm/`.

Tokens that resolve but deserve a word:

* `dsl_grammar_v0.1` (L887, `03_a0.md`:260) is a bare grammar name with the
  extension dropped; the file is `CONTRACTS/dsl_grammar_v0.1.md`, cited correctly
  at L506. Not counted above because the extractor cannot see it as a path.
  Cosmetic.
* `engine-rig` (L539, `02_framework.md`:49) is cited as "an `engine-rig` file
  that has not been written". It resolves as a **directory**; the file it names
  does not exist, which is the point of the sentence. Not a finding.
* `battery/artifacts/` (L237) and `battery/audit/exploits/` (L216) are
  directories, both cited as containers rather than sources. Both resolve.
* `figures/…` tokens (L658-660, L731-733) resolve at the **repo root** `figures/`
  tree, which is the intended one: `fig06_concept_timeline.{py,csv,svg}` and
  `fig07_a0_vs_a0prime.{py,csv,svg}` all exist there, light and dark plates
  included. A *second* figure tree exists at `papers/phase1-workshop/figures/`
  (holding `fig1…`/`fig2…`/`fig3…` and `PARITY.md`, cited at L670); the numbering
  differs, so the root-relative citations are unambiguous. Not a finding, and
  §3.1 is explicit about the two trees.
* Two long run-directory paths (L17, L19) resolve, including the
  `RUN_STATE.md` inside the second.
* `[angluin1987lstar]` (L794) is a BibTeX key, not a path; it is present in
  `papers/phase1-workshop/references.bib`:206. Checked, correct, out of Pass A's
  scope.

---

## Pass B — wrong, stale, mis-attributed, or absent from the cited file

Twelve. The stub said eight and characterised "six of the eight" as "the number is
true somewhere, but not in the file named beside it". **That characterisation
half-holds and under-reports the worse class.** Of the twelve, six (B3, B5, B6,
B8, B11, B12) are indeed misplacements of a true number; the other six are
numbers that are wrong, stale, or contradicted by the artefact — B1 and B2 are
the serious ones, B4 is the one on the front page.

| # | § | PAPER.md / section:line | paper says | the artefact says | severity |
|---|---|---|---|---|---|
| **B1** | §3.3 | 750-751 / `03_a0.md`:123-124 | "A0's three errors are not scattered: they are the Button pressed **from above, from below and from the right** (`cold-start-a0/artifacts/score_vs_truth.json`, whose `base.behavioural.accuracy` is `0.987288`)" | The cited artefact's `base.held_out.examples` are `{DOWN, cart (2,2)}`, `{RIGHT, cart (3,1)}`, `{UP, cart (4,2)}`, and `trace_summary.json`'s `a0-base.uncovered_pairs` are the same three, item for item. The Button is at **(3,2)** (`engines_report.json`, `zero_space.global_laws[0].support: ["8@(3,2)", "5@(4,5)"]`). Its four cardinal neighbours are (2,2) above, (4,2) below, (3,1) left, (3,3) right. So the three missing approaches are from **above, below and the LEFT** — and "from the right" is the *one that was witnessed*: `theory.dsl`:49 is `when act=push(Cart, left) and colored(leftof(Cart), 7)`, i.e. the Cart standing at (3,3) and pushing leftward, the single witness R-05 built its whole argument on. The paper names as an error the direction the manual got right. The gloss is inherited verbatim — `cold-start-a0/THEORIZE_LOG.md`:633 ("pressing the Button from above, from below and from the right") and `A0_REPORT.md`:54 ("They are the Button pressed from above, below and the right") — so the paper is faithful to two prose sources that are both wrong, and under its own precedence rule the JSON decides. `0.987288` ✓, "three errors" ✓, "not scattered" ✓ | **medium-high** |
| **B2** | §3.2 | 714-716 / `03_a0.md`:87-89 | "`cold-start-a0/artifacts/engines_report.json` has since moved on — it now reports **5704 bits over 6 tracks**, with 6511/90 demoted to `reidentification.*_before`" | The artefact's rejected-operator row (`segmentation.operator_comparison[1]`, `operator: "connected_components(4)"`) now carries `script_bits: 5284`, `tracks: 6`, with `reidentification.script_bits_before: 6511` and `tracks_before: 90`. The 6/6511/90 halves are exactly right; **5704 is not in the file** (`grep` = 0 hits under `cold-start-a0/artifacts/`). `cold-start-a0/DECISIONS.md`:453 records why: an upstream-pricing fix to `_max_objects` moved it — "A0's losing operator moves 5704 → 5284 bits and the chosen operator does not move". So a parenthetical whose whole job is to warn the reader that an artefact drifted has itself drifted. Not the paper's alone: `PROVENANCE.md`:200, `REVIEW.md`:433 and `REVIEW_TRIAGE.md`:80 all repeat 5704 | **medium** |
| **B3** | §1.2 | 290-292 / `01_intro.md`:139-141 | "a single manual that describes nothing holds **eighteen** of the twenty metrics in that audit's scope at their best reading simultaneously (`battery/audit/exploits/mechanism_epistemic.py`, `omnibus_manual`; **§7.7 says nineteen**, from before `K12`'s defence landed)" | Both halves of the disclosure are wrong. (a) `mechanism_epistemic.py`'s `omnibus_manual` docstring (L852-882) says "**Nineteen** of the twenty metrics in this audit's scope" — the cited file does not contain eighteen. (b) **§7.7 says eighteen**, not nineteen: PAPER.md L2017 reads "holds **eighteen** of the twenty metrics", and L2021-2022 names the actual home of the 18 — `battery/tests/test_exploits_mechanism_epistemic.py`, `assert len(landed) == 18` (verified: line 393), "whose docstring records the figure as 'nineteen before v2.1 closed K12'" (verified: line 387). Eighteen is the true figure — `gaming_audit.json` has 13 of 14 epistemic and 5 of 6 mechanism exploits landing, K12 and M3 excepted, = 18 of 20 ✓ — so the *number* survives; its provenance and its own cross-reference do not. This is a number that was corrected in one section and left with the old section's citation in the other | **medium** |
| **B4** | draft status | 14 / `00_abstract.md`:12 | "at roughly **27 500 words** it is about **six times** a workshop budget" | `assemble.py` computes and prints exactly `len(body.split())`. Replicating it on the current file gives **36 242**. The claim is low by 8 742 words (24 % of the true figure); at a ~4 500-word workshop budget the multiple is ~8×, not six. Carries no citation of any kind, and it is the first quantitative claim a reader meets. Trivially re-derivable — `python papers/phase1-workshop/assemble.py` prints it on every run — which is what makes it a defect rather than an estimate | **medium** |
| **B5** | §1.2 | 244 / `01_intro.md`:93 | "(`battery/PREREG_V9.md`). They wrote **105 attacks, of which 91 landed**:" — introducing a blockquote attributed to `battery/runs/20260729T021247Z-V9-battery-gaming-audit/v9_gaming_audit.json` | `PREREG_V9.md` contains **neither** number (`grep` for 105, 91, 112 = 0 hits). The JSON cited on the very next line records **112** attacks across `verdict.metrics[*].attacks`, of which **95** have `succeeded: true` and 17 do not — I counted them. 105/91 are the *blind-phase* figures, and they are real: 105 is at `battery/STATUS.md`:23 and :50, 91 at `battery/audit/v9/REPORT.md`:137 ("91 条落地攻击"). The 7-attack difference is the sighted round (`battery/audit/v9/attacks/a7_review.py`, exactly 7 attack functions), and 105 + 7 = 112 reconciles cleanly. The abstract discloses the split at L78-79 ("105 in the blind phase and 112 in the delivered artefact") and §7.7a repeats it at L2098; **§1.2 does not**, and the file it points a reader at is the 112 one | **medium-low** |
| **B6** | §1.2 | 247-250 / `01_intro.md`:96-99 | blockquote: "**37 of the 38 metrics were driven to their pre-registered threshold, and the main table fell from nine metrics to two.** — `v9_gaming_audit.json` (`verdict.gameable` 37, `verdict.b14_baseline_main` 9); summarised at `battery/STATUS.md`" | `verdict.gameable` has 37 entries ✓ (all but `M3`); `verdict.b14_baseline_main` has 9 ✓ (`E2 E3 K7 K11 K12 M3 M6 P3 P4`). But the artefact's `verdict.main` is **`[]`** and `verdict.undetermined` is **`["M3"]`** — it already incorporates the sighted round, so it never shows "two" anywhere. The two is prose, at `battery/STATUS.md`:54 ("盲轮先把它从 9 压到 2，交付前的对抗复核把剩下两条也拿掉了"), which the attribution line does name. The paper resolves this in the very next paragraph, so this is a mis-sourced clause rather than a wrong claim — but under the paper's own precedence rule the JSON field it cites contradicts the sentence it is cited for | **low** |
| **B7** | §3.1 | 668-670 / `03_a0.md`:41-43 | "The disagreement, the ruling and the **eleven other quantities** the two implementations were checked against are in `papers/phase1-workshop/figures/PARITY.md`" | `papers/phase1-workshop/figures/check_figure_parity.py::probes()` returns **14** comparisons — 5 on A0 (accuracy, coverage, pairs, revisions, probes), 4 on A0′ (accuracy, coverage, pairs, probes), 3 on fig06 (adjudications, revisions-driven-by-certify, compiler defects), 2 on fig05 (ledger beats, loop beats). `PARITY.md`'s own headline is "**12 agree**", "**1 one-sided**", "**1 disagreement**" = 14. Others besides the disagreement = **13**, or 12 if the one-sided item is excluded from "checked". Eleven matches neither | **low** |
| **B8** | §3.6 | 887-889 / `03_a0.md`:260-262 | "**eleven** mined `*_still_*` rules were rejected as entailed by it" | `engines_report.json`'s `mining.rules` holds **twelve** names matching `*_still_*` (`obj{0,1,2}_still_{UP,DOWN,LEFT,RIGHT}`) — I enumerated them. The eleven is in the cited log but counts a different thing: `cold-start-a0/THEORIZE_LOG.md`:260 (R-07) says entering them "would (a) lengthen the manual by **eleven clauses**", i.e. clauses the manual would gain, not rules the stream carried. R-06 disposes of 2 of the twelve and R-07 of the rest plus three lifted forms, so no reading of the log yields eleven mined rules. Under the precedence rule the JSON gives twelve | **low** |
| **B9** | §1.5 item 3 | 426-429 / `01_intro.md`:275-278 | "the second world's manual reaches 228/228 = 100 % while covering only **107/228** = 47 % of its own state-action pairs … (`cold-start-a0/A0_REPORT.md` §8)" | `A0_REPORT.md` §8 carries "**47 %**" and "**228/228 = 100 %**" verbatim (L247-248) ✓ and supports the design-lesson clause the citation is really attached to ✓ — but it does **not** carry `107/228`. That fraction is at `cold-start-a0/prime/A0P_REPORT.md` §1 and §2 and at `prime_report.json`, `trace.a0p-base.coverage: "107/228"`. §3.3 cites those correctly; the §1.5 summary points at the one file of the three that lacks it | **low** |
| **B10** | §1.3 | 328-330 / `01_intro.md`:177-179 | "the metric cards define **`K4` as the share of the manual's own evidence-annotated clauses that a witness actually backs**" | `capability_spectrum.json`, `cards.K4.definition` reads "**Mean coverage over clauses the manual annotates with one**; the count of unannotated clauses is reported alongside, not folded in." A mean of per-clause coverage ratios is not a share of clauses. On A0 the two coincide (`K4.value: 1.0`, `support {annotated: 7, min_witnesses: 1, unannotated: 3}` — every annotated clause at full coverage), so no number moves; the definition the paper attributes to the card is not the card's. `K2`'s gloss, by contrast, is the card's own words | **low** |
| **B11** | §1.3 | 313-314 / `01_intro.md`:162-163 | "its accuracy is **0.000** (`cold-start-a0/artifacts/score_vs_truth.json`, field `held_out.accuracy`)" | The value is right and the field exists, but its path is `base.held_out.accuracy` — `held_out` is nested under `base`, alongside a `variant` branch with its own numbers (`behavioural.accuracy: 1.0` over 92 pairs). A reader searching for a top-level `held_out` finds none. Same class as §3.4's `run_a`/`run_b` prefixes, which the paper *does* write out | **very low** |
| **B12** | §3.6 | 887-888 / `03_a0.md`:260-261 | the frame axiom "lived in a comment and was hard-coded in **all three backends**" (E-03 in `cold-start-a0/THEORIZE_LOG.md` §E) | E-03's ledger row (`THEORIZE_LOG.md`:359) reads "a comment at the top of `theory.dsl` and a hard-coded rule in **the backends**" — no count. Three is a correct inference (Lean, Python, PDDL are the executable forms; Markdown is a pretty-printer) but it is the paper's arithmetic on the four co-derived forms, not the cited file's figure | **very low** |

### The three load-bearing findings, resolved

The stub named three findings and enumerated none. All three are opened here.

**(a) The abstract's "1 790 probes" / "$6.32" / "84 %" chain (L118-127,
`00_abstract.md`:116-125). It verifies — completely, against artefacts — and the
stub's implication that it does not is unsubstantiated.** Every figure, traced to
a field:

* "**1 790 probes with no hits**" — `exam/artifacts/leakage.json` has four
  `papers` entries whose `probes_declared` are 363 + 58 + 1284 + 85 = **1790**,
  with `probe_hits: 0` and `structural_hits: 0` on all four. Recurs cited in the
  body at L2437-2438 ("**1,790 declared probes across the four papers, 0 probe
  hits, 0 structural hits** (`exam/artifacts/leakage.json`)") — the abstract's
  thin space against the body's comma is the only difference. "three of whose
  four papers have never been sat" recurs as §8.2's heading (L2378) and L2402.
* "a preflight that sent **18 commands** for **zero billable actions and zero
  dollars**" — `theoria-arm/runs/preflight-20260728T012057Z/MANIFEST.json`,
  `budget.commands_sent: 18`, `budget.actions_ok: 0`, `cost.cli_reported_usd: 0.0`.
  All three exact.
* "**seven actions**" and "**$6.32**" — `theoria-arm/runs/20260728T015354Z-g50t-first-contact/MANIFEST.json`,
  `budget.actions_ok: 7` and `cost.cli_reported_usd: 6.317658`. Recurs cited at
  L2704 and L2707.
* "**$5.80**" — same manifest, `cost.from_price_table.usd_total: 5.795338`.
  Recurs cited at L2708 as the full `$5.795338`.
* "**84 % of its size**" — `cost.cache_ttl_diagnosis.under_billed_usd: 0.436763`
  against `cost.delta_usd: -0.52232`. I recomputed: 0.436763 / 0.52232 =
  **0.83617**. §9.4 prints **83.6 %** (L2716-2717) and cites both fields.
* "whose manifest carries the byte-level scan showing no sealed-pile game was
  touched" — same manifest, `sealing.sealed_game_ids_found: []`,
  `sealed_pile_untouched: true`, `cut_integrity: true`, and
  `game_ids_anywhere_in_the_records: ["g50t-5849a774"]` — development pile.

**The one real defect in the chain is small and is about the exemption clause,
not the arithmetic**: the draft-status box conditions the abstract's exemption on
every figure recurring *cited* in the body, and **"84 %" recurs nowhere** — the
body's figure is 83.6 %, and 84 % appears exactly once in the whole 3729-line
file, at L125. Rounding 83.6 up to 84 is defensible; presenting it as a figure
that recurs below is not, because it does not. Everything else in the chain
recurs, cited, exactly as the clause promises.

**(b) The §1.5 "95 runs across 5 arms" arm census (L441-455,
`01_intro.md`:290-304). Exactly right, every number, and it is the best-sourced
paragraph in §1.** From `battery/artifacts/capability_spectrum.json`:
`provenance.n_runs: 95` and `runs` holds 95 entries ✓; `provenance.arms` is
`["bare_cc", "schema_repro", "theoria_a0", "theoria_a0_spike", "theoria_a2"]` —
five, in the paper's order ✓; counting `runs[*].arm` gives `bare_cc` **80**,
`schema_repro` **8**, `theoria_a0` **2**, `theoria_a0_spike` **1**,
`theoria_a2` **4**, summing to **95** ✓ — all five figures and the sum, as
written. The "88 of the 95 runs touch a development-pile game and the other 7 are
synthetic" also holds exactly: `pile` is `dev` on 88 and `synthetic` on 7, the 7
synthetic runs are precisely `a0-base`, `a0-no-button`, `a0-spike`,
`a2-play-record`, `a2-probed`, `a2-refutation`, `a2-sweep` (all three framework
arms, `game_id: null`), and the 88 dev runs split 23/21/24/20 across the four
development-pile games ✓. `provenance.n_games: 4` ✓, and
`provenance.cut.piles_sha256` matches CLAUDE.md's cut digest ✓. The paragraph's
closing warning — that "95 runs across 4 games" is "true of neither number by
itself" — is correct and is the kind of self-correction this rule is for. One
nuance, not a finding: "at zero new game spend and **zero model calls**" is the
battery's own execution cost (`battery/REPORT_V2.md`:8, "Zero API calls, zero
model calls, zero network, zero game spend"), while the cited JSON's
`runs[*].model_calls` is nonzero on 82 of 95 — those are the recomputed-over
runs' original calls, not the battery's. The reading is right; a reader opening
the JSON first will need the second citation to see why.

**(c) The §1.2 attribution of the 38-metric five-family split to
`battery/artifacts/capability_spectrum.json` (L206-208, `01_intro.md`:55-57).
This is not a defect, and the stub's claim that it is one is unsubstantiated.**
The paper says "a battery of **38 metrics over five families** — epistemic (14),
economy (7), exploration (6), mechanism (6) and planning (5)
(`battery/artifacts/capability_spectrum.json`)". That file's `cards` object holds
exactly **38** entries (`E1`-`E7`, `K1`-`K14`, `M1`-`M6`, `P1`-`P5`, `X1`-`X6`),
each with a `family` field, and tallying them gives **epistemic 14, economy 7,
exploration 6, mechanism 6, planning 5** — five families, all five counts, no
sixth family, total 38. The `coverage` object carries the same `family` label per
metric independently. This is a JSON artefact carrying the claim field for field,
which is the strongest form the rule asks for. Recorded as a finding withdrawn:
the earlier report asserted it without enumeration and it does not survive
enumeration.

### Numbers checked and confirmed correct

Traced to the named field of the named file, not to a report. This is the whole
set for lines 1-908, not a sample; roughly 125 distinct claims, of which the
twelve above failed.

* **Abstract · the battery figures** — all recur cited in the body and all trace
  to artefacts: 38-metric battery, "34 of the 38" (`gaming_audit.json`: 34
  entries with `demonstrated.succeeded: true`, 4 false — `E2`, `K12`, `M3`, `P4`),
  "17 … contradicted" (`n_disagreements: 17`), "14 of them claims that a metric
  had been defended" (I counted: exactly 14 of the 17 `disagreements` entries
  have `defended` in `fields_contradicted`), "37 of 38" and "nine to two"
  (`v9_gaming_audit.json`), "105 in the blind phase and 112 in the delivered
  artefact" (112 recomputed from the JSON; recurs at L2098 as "105 of 105 …
  112 of 112"). "the mechanical check … rejected none of the attacks it saw" is
  literally true of the delivered artefact: all **112** attacks carry
  `S3_poverty_certified: true` and `certificate.ok: true`, with zero `violations`.
* **Abstract · the pipeline figures** — 276/276 frames, 22 356/22 356 pixels, 0
  anomalies; 233 of 236; 0.000 with n = 3; 228/228 at 47 % coverage; the
  18-action refutation; "six recorded beats (L1–L6 of an eight-beat ledger)";
  252/252 both arms. Every one recurs cited in §1, §3, §5 or §6, and every one is
  confirmed in this slice or by slice B. 22 356 = 276 × 81 ✓; 8991 = 111 × 81 ✓.
* **§1.0** — `Theoria.md` §1.0 (L10) is "64×64 网格、16 色、确定性规则、规则隐藏。
  它只能做两件事:行动,观察", which is the paper's sentence exactly ✓;
  `arc-recon/README.md`:51 "public set size | **25 games**" ✓ and :181 "scorecard
  `total_actions` **equals successful actions only**" ✓ (the paper's "bills
  successful actions"); `arc-recon/data/piles.json` `dev_pile` has 4 entries and
  `n_sealed: 21` ✓. "up to six per-game actions" is supported by the README's
  per-game action spaces rather than stated as a figure.
* **§1.1** — `Theoria.md` §3.1 (heading at L389) reports 98.98 % at L393 and L395
  ✓, and the paper's two qualifications (a game score, self-reported) track the
  source ✓.
* **§1.2 · the first round** — `battery/artifacts/gaming_audit.json`:
  `n_demonstrated: 38`, `n_disagreements: 17`, `main` with 9 entries, `rule`
  exactly as §1.2 describes it, `demoted_by_demonstration` with 10. 34 landing
  and the four survivors recomputed from `metrics[*].demonstrated.succeeded`.
  `battery/audit/gaming.py`:8-9 carries the mechanical rule verbatim
  ("gameable AND accidental AND NOT defended -> reference / otherwise -> main")
  and :18-20 defines `defended` as "the battery implements the defence" ✓.
* **§1.2 · the main table's two moves** — `battery/REPORT_V2.md`:192 heads "the
  main table fell 19 → 6" ✓ and :338 books "main table 6 → 9" ✓; "four defences"
  is that file's own "## The four" table (:325-332, `P4`/`K12`/`E2`/`K2`) ✓, with
  `K2` recorded as failed, which is why 6 → 9 and not 6 → 10.
* **§1.2 · the three named defences** — `REPORT_V2.md`:209-210 "**P4 is monotone
  in failure** … one action against a 12-step plan scores 0.083" ✓ (direction
  `lower`, so it beats a solved run's 1.000, as the paper says); :218-220 "**K12
  reads six self-reported booleans** from a file its own producer wrote … scores
  1.000" ✓; :376 "dump the bill on turn one, score **0.993** over twenty turns" ✓.
  The paper's parenthetical that 0.993 "is not in `battery/artifacts/`" holds —
  the only 0.993x strings under `battery/artifacts/` are `r2_linear` /
  `r2_quadratic` regression fits, unrelated to `E2` ✓.
* **§1.2 · `E2` as a primary endpoint** — `Theoria.md`:373 (inside Phase 4,
  heading at L366) freezes "**主终点限三个**——U3 达成率、判决题准确率(含特异度)、
  **前载指数**配对差", so the front-load index is one of three ✓, twice claimed
  and twice true (L235, L259).
* **§1.2 · the blind round** — `v9_gaming_audit.json`: `verdict.n_metrics: 38`,
  `n_attacked: 38`, `n_attacks: 112`, `unattacked: []`, `not_gameable: []`,
  `gameable` 37 (all but `M3`), `b14_baseline_main` 9, `demoted_by_v9` 9,
  `undetermined: ["M3"]`, `main: []`, and `rule` stating the S1∧S2∧S3 conjunction
  the paper describes. `battery/PREREG_V9.md`:18 carries the literal
  `git merge-base --is-ancestor <prereg-commit> <results-commit>` ✓. Six blind
  attackers: `battery/audit/v9/attacks/` holds `a1.py`…`a6.py` plus the sighted
  `a7_review.py` ✓.
* **§1.2 · the sighted follow-up** — exactly right, and it is the tightest
  citation in §1.2. `a7_review.py` defines **seven** attacks: four on `E1`
  (`attack_E1_unit_bug`, `attack_E1_retry_rows`, `attack_E1_model_swap`,
  `attack_E1_cache_flag`) and three on `M3`. In the JSON, `E1`'s `unit-bug`,
  `retry-rows`, `model-swap` and `cache-flag` all have `succeeded: true` while
  all five `M3` attacks are false — so "**seven more attacks of which four
  landed, knocking out `E1`**" ✓, and `M3` moved to `undetermined` ✓
  (`PREREG_V9.md` revision 2 is why the bucket exists). 105 + 7 = 112 ✓.
* **§1.2 · the five limits** — "**Eleven** of the 38 first-round exploits
  hard-code their own success … (`battery/audit/exploits/exploration_planning.py`)"
  is exactly right: that file contains exactly **11** literal `succeeded=True`
  assignments (lines 109, 151, 202, 246, 285, 335, 383, 444, 491, 550, 596) and
  the other two exploit modules contain none. The pre-registration breach is
  `PREREG_V9.md`'s 修订 1 (:181-193), which states that `verdict.py` "根本不在预注册
  那个 commit 里", that the `NOT defended` clause "被折叠了" after the results were
  seen, and at :193 calls it "**这条是本轮预注册最实的一处失守**" — the paper's
  "the round's worst lapse" ✓. "passed all 105 attacks and rejected none" is
  `battery/audit/v9/REPORT.md` §7 (:135, :161) ✓. "of the nine demotions … its
  own report grades three *weak*" ✓: §9's strength table (:206-208) is 强 `E2 E3
  K12`, 中 `P3 P4 E1`, 弱 `K7 K11 M6` — three weak of nine, and the 弱 row's
  reason is "该判据对计数型诊断项近乎必然成立", which is the paper's "for
  count-shaped diagnostics the threshold is close to unavoidable" ✓.
* **§1.2 · the stale-baseline disclosure** — the sharpest self-correction in the
  slice and it reproduces exactly. `battery/runs/20260729T025515Z-V18-battery-prereg-check/recompute/gaming_audit.json`
  gives `demonstrated.succeeded` true on **33** and `n_disagreements: 19`, against
  the frozen file's 34 and 17 ✓. (`main` in the recompute is `[]`;
  `battery/STATUS.md`:254 independently books the frozen artefact as 陈的/stale.)
* **§1.3 · A0's two scores** — `cold-start-a0/A0_REPORT.md`:40 "**276/276 frames,
  22 356/22 356 pixels, 0 anomalies**" ✓ and :41 "**233/236 = 98.73 %**" ✓;
  `score_vs_truth.json` `base.behavioural {accuracy 0.987288, agree 233,
  disagree 3, pairs 236, reachable_states 59}` and `base.held_out {accuracy 0.0,
  agree 0, disagree 3, held_out_pairs 3}` ✓.
* **§1.3 · the identity of the missed pairs** — the paper's strongest §1 claim
  and it is exactly true. `trace_summary.json`'s `a0-base.coverage: "233/236"`,
  `covered_pairs: 233`, `state_action_pairs: 236`, and `uncovered_pairs`
  `["cart=(2,2) pressed=0 act=DOWN", "cart=(3,1) pressed=0 act=RIGHT",
  "cart=(4,2) pressed=0 act=UP"]` — the same three, in the same order, as
  `score_vs_truth.json`'s `held_out.examples`. The paper's own hedge (both counts
  descend from the same explorer, so this is auditable rather than independently
  confirmed) is the right hedge.
* **§1.3 · the battery's reading of the same manual** — `capability_spectrum.json`,
  `runs["a0-base"]`: `K4 {value 1.0, support {annotated 7, unannotated 3,
  min_witnesses 1}}` and `K2 {value 0.0, support {pairs 3, agree 0}}` ✓ — 1.000
  over 7 annotated with 3 unannotated ✓, 0.000 over 3 pairs with 0 agreements ✓.
  The run is `arm: theoria_a0`, `pile: synthetic`, `model_calls: 0`, `steps: 275`.
* **§1.3 · the seal** — `score_vs_truth.json`'s `seal` field is "ground truth
  first read at M6, after M4 and M5 were green", and
  `cold-start-a0/THEORIZE_LOG.md`'s "## Ground-truth seal" (:620-626) carries the
  same stamp with the same M4/M5 condition ✓. The paper's insistence that this is
  a self-declaration and not a control tracks both sources ✓.
* **§1.3 · R-05's content** — `THEORIZE_LOG.md` R-05 (:222-245) names exactly
  `press_up`, `press_down`, `press_right` as the zero-evidence directions ✓, and
  the concrete configuration "drive the Cart to (2,2) and push DOWN into an
  unpressed Button" ✓. The paper's care here is warranted and correct: R-05 names
  directions, not coordinate pairs, and the phrase "the three pairs R-05 named"
  really is only in the seal section (:633), written at M6 ✓.
* **§1.3 · the seal's hole** — `THEORIZE_LOG.md`'s preamble (:11-12) is the exact
  sentence the paper bolds ✓, and `A0_REPORT.md` §6 item **3** ("The seal is
  imperfect. The same instance built the world and adjudicated it.") is what
  "§6.3" points at ✓.
* **§1.4** — `cold-start-a2/A2_REPORT.md`:180-181 confirms the pair's identical
  generator, tactic, dependency surface and axiom list; the 18-action refutation
  is at :91, :108, :131 and :178 ✓; INC-004's ruling is the blockquote at :22-27 ✓.
* **§1.5 item 2** — `cold-start-a2/artifacts/loop_ledger.json`
  `summary {absent 0, fail 0, pass 8, total 8}` ✓ with beats `M0, M5, L1, L2, L3,
  L4, L5, L6`, every one `status: pass` ✓ — so "these six are `L1`–`L6` … whose
  other two beats build the exhibit rather than repair it; all 8 pass, 0 fail" is
  exact.
* **§1.5 item 4** — the certificate path resolves and slice B confirms its
  contents; the paper's careful distinction (the certificate is JSON re-checked by
  Python, the machine-checked object is the Lean theorem) is stated in the paper
  rather than borrowed.
* **§1.6** — `cold-start-a2/A2_REPORT.md`:273 "A2 tests the instrument and the
  loop, not the theorizer." ✓ verbatim.
* **§2.1** — `Theoria.md` §1.8 (:94) is "一个概念入册的资格 = **它让说明书变短**",
  which is the paper's "A concept's ticket of admission is that it shortens the
  manual" ✓; §1.10a's block lists `theory.lean`, `theory.py`, `theory.pddl`,
  `theory.md` — the four co-derived forms in the paper's order ✓;
  `cold-start-a0/theory/theory.dsl` exists and is A0's manual ✓.
* **§2.1 · T-8** — `a0-spike/THEORIZE_LOG.md` T-8 confirms every clause: certify
  rewired to the compiled manual, "the generated code immediately walked the
  player off the board", and the cause located in the transcription rather than
  the mined rules ("The mined rules had the right effect all along") ✓.
* **§2.2** — `engine-rig/STATUS.md`:18 books `deadlock_carver` and `ic3_pdr` at
  the `engine-rig-m9-…` tag ✓, and :44 records `ic3_pdr`'s acceptance line met,
  so "the engine itself runs and emits candidate rows" ✓.
  `theory-compiler/STATUS.md`:166 is delivery 9, "**消费端**完成；发射端是
  engine-rig 的文件，未写" ✓. `CONTRACTS/candidates_schema.md` is frozen v0.1 and
  `engine-rig/tools/validate_candidates.py` exists ✓; every row of
  `cold-start-a0/artifacts/candidates.jsonl` has `status: "candidate"` — I checked
  all 29 ✓.
* **§2.2 · T-6** — `a0-spike/THEORIZE_LOG.md` T-6 is exactly the paper's account:
  the adjudicator proposed `(box.row + box.col) mod 2 = 0`, `zero_space` returned
  "a null space of dimension **2**, basis `[[1,0],[0,1]]`" with each coordinate's
  parity conserved separately, and the log itself calls it the engine correcting
  the adjudicator ✓.
* **§2.3** — `Theoria.md` §1.10d's heading (:222) is
  "内环:theorize → certify → probe → plan → commit" ✓; constraint 7 in §1.10e's
  ten-constraint table is "定理未经戳探不得定案" ✓ (the "prediction written down
  before the action" half is §1.10d's probe bullet at :229, "预测先写" — the
  substance is one bullet away from the anchor given).
* **§2.4** — all **eight** failure classes and their order match `Theoria.md`'s
  Phase 3 table (:342-349): 概念不成形, 机制归纳错, 调度失误, 表达力不够,
  证明打不动, 搜索爆炸, 戳探设计差, 修订抖动 ✓. The table is inside
  "## Phase 3 · 框架迭代" (:334), as the paper says ✓.
* **§2.5** — `Theoria.md`:282 is "## Phase 1 · 封闭系统:怎么搭" inside 第二部分
  (:278), so "Part 2, Phase 1" resolves ✓ (this is `CITECHECK.md`'s malformed
  anchor, now fixed). `capability_spectrum.json`'s `battery_version` is the string
  `"v2"` ✓.
* **§3.1 · every milestone figure** — `cold-start-a0/A0_REPORT.md`:24 (M1) gives
  the 9×9 Cart/Button/Door/Portal world, **59 reachable states** and the
  **276-frame** `raw_trace.jsonl` ✓; :27 (M4) gives "cheap certify **22 356/22 356
  pixels**; Lean `inv_all`, **0 axioms**; plan SAT, **12 steps**, world agrees
  frame-for-frame" ✓; :216 (§7) gives "in about **six seconds** of compute" ✓
  (this is `CITECHECK.md`'s uncited-figure finding, now correctly cited to
  "preamble and §7").
* **§3.1 · the 28/29 candidate gap** — exactly handled.
  `candidates.jsonl` has **29** rows: 3 `object_hypothesis`, 23 `rule_hypothesis`,
  2 `invariant`, **1 `plan`** ✓, all `status: "candidate"`.
  `THEORIZE_LOG.md`:33 opens Round 0 on "**28** candidate rows: 3 …, 23 …, 2 …",
  and 3+23+2 = 28 with the `plan` row left out ✓ — the paper's parenthetical is
  precisely right. `theory.dsl` has 3 `object` declarations, 7 `rule`
  declarations, 2 `invariant` lines (:58-59) and 1 `theorem` ✓, and
  `THEORIZE_LOG.md`:598 books the identical tuple "3 objects, 7 rules, 2
  invariants, 1 pending theorem" ✓.
* **§3.1 · Figure 1** — all five figure paths resolve (light and dark plates,
  script, CSV). `figures/csv/fig06_concept_timeline.csv` has 119 rows over 9
  lanes; `event_kind: adjudicated` appears on 20 rows spanning **17** distinct
  `item_id`s (`L-01`…`L-03`, `O-01`…`O-04`, `P-01`, `P-02`, `R-01`…`R-08`), so
  "seventeen decisions" ✓ and `check_figure_parity.py`'s comment explaining why
  17 ids ≠ 20 events is reproduced by the data. `manual-revision` rows: **2**,
  both carrying a `trigger` ✓. `compiler-defect-ABSENT` rows: **3** ✓. The
  `verdict-absent-ABSENT` row is `P-03` with label "the log records no bold
  verdict for this entry" ✓, and `THEORIZE_LOG.md`:341's P-03 heading indeed
  carries no bolded verdict where :332 and :336 do ✓. The paper writes the marker
  as `verdict-absent` where the CSV's value is `verdict-absent-ABSENT`; a
  truncation of a field value, noted rather than counted.
* **§3.1 · the parity ruling** — `papers/phase1-workshop/figures/PARITY.md`:56-70
  carries the 18-vs-17 disagreement, the `"see body"` placeholder, and the ruling
  that "the pipeline is right and this directory is wrong", ending "**17
  adjudications, with one probe designed and never ruled on**" ✓ — the paper's
  "The count is seventeen" and its whole framing ✓.
* **§3.2 · `zero_space`** — `engines_report.json` `zero_space.features: 152` ✓,
  `global_laws[0] {rendering "(8@13 + 5@22) mod 2 = 1", support ["8@(3,2)",
  "5@(4,5)"], value 1}` ✓, and `transitions: 275` ✓. `THEORIZE_LOG.md` L-02
  states "275 transitions of support, by an engine that was handed 152 anonymous
  indicator bits" ✓ and "R-04's rule has one witness; this has all of them" ✓ —
  the paper's "against the *single* witness the rule miner had".
* **§3.2 · CEGIS** — `mining.rules` carries `obj0_recolor8_LEFT`
  (`guard ["act==LEFT","tcolor(LEFT)==7"]`, `coverage "1/1"`, `frontier_size 1`)
  ✓ and `obj2_jump_DOWN` (`guard ["act==DOWN","tcolor(DOWN)==3"]`,
  `coverage "2/2"`, `frontier_size 2`) ✓ — frontier 1 on one witness, frontier 2
  on two, exactly as §3.2 says, and R-02 is where the size-2 frontier was broken.
* **§3.2 · MDL** — `A0_REPORT.md`:97-99 carries "**90 tracks** with **88
  vanishes** and **87 appears** … The uniform-colour operator gave **3 tracks**
  and 216 events. Script bits: **6511 vs 4423**" ✓, and `THEORIZE_LOG.md`:79-86
  (D-A0-007) carries the same table with the same three columns ✓. The live
  artefact's chosen row still reads `script_bits: 4423, tracks: 3` ✓ — only the
  rejected row moved (B2).
* **§3.3 · the four-way difference** — `theory.dsl` has 3 objects / 7 rules and
  `cold-start-a0/prime/theory/theory_prime.dsl` has 3 objects / **21** rules
  (counted) ✓; 59 vs **57** reachable states (`trace_summary.json` and
  `prime_report.json` `trace.a0p-base.reachable_states: 57`) ✓; 236 vs 228
  state-action pairs ✓; Button vs Switch ✓. "Identical except would be a false
  description" is the honest reading of those four.
* **§3.3 · the headline table** — all seven rows are **byte-identical** to
  `cold-start-a0/prime/A0P_REPORT.md` §1's table, including the two renderings of
  233/236 (99 % for coverage, 98.73 % for accuracy) that the source itself prints
  side by side. 107/228 = 0.46930 → 47 % ✓ (`PARITY.md` independently books
  0.469298).
* **§3.3 · the mechanism** — `cold-start-a0/prime/THEORIZE_LOG.md` R-03 accepts
  "**all sixteen clauses**", "Each clause has coverage **1/1** — but there are
  **sixteen of them and every direction-by-polarity combination has its own
  witness**" ✓, which is the paper's sentence and the load-bearing premise of its
  analytic-entailment concession.
* **§3.4 · Run B** — `prime_report.json`: `run_a.certify_cheap {frames 111,
  pixels_checked 8991, anomaly_kinds [], green true}` ✓;
  `run_b.certify_cheap: true` as a **bare boolean** ✓ — the paper's note about
  where that number lives is exactly right, and is `CITECHECK.md`'s finding fixed
  by disclosure; `trace.a0p-base {frames 111, transitions 110, coverage
  "107/228"}` ✓ ("the whole 110-transition history"); `run_b.revisions: 1` and
  `run_b.repair.action: "delete rule push_onto_crate"` ✓;
  `run_b.score_vs_truth_before.accuracy 0.991228` → `_after.accuracy 1.0` ✓ (the
  paper prints the JSON's six digits, not `A0P_REPORT.md`'s 0.9912 — correct
  precedence); `run_b.coverage_probes {probes_run 1, refuted
  ["push_onto_crate"], untested_rules ["push_onto_crate"]}` ✓;
  `engines.executable_probes: 13` of `total_probes: 27` ✓;
  `trace.a0p-base.win_frames: []` ✓, which is why §3.7's "the truncated trace
  never wins" holds. "2 firing states … navigated 3 steps to (2,3), predict
  Cart→(2,4), execute, observe Cart stays at (2,3) → refuted" is
  `A0P_REPORT.md` §3's table row, verbatim in substance ✓, and the two
  `score_vs_truth_before.examples` are both at cart `[2,3]` with action `RIGHT`,
  differing only in `switch_on` — two firing states ✓.
* **§3.5 · the spike** — `a0-spike/THEORIZE_LOG.md` T-9 confirms every figure:
  **341 transitions** replayed exactly, **8 mismatches**, `push2` requiring
  `free(beyond(Box, dir))` but not `free(ahead(Box, dir))`, "All 8 mismatching
  states are unreachable from `s0`; on the **315** reachable states the theory was
  already exact", "**39,960** well-formed states across five levels, **0
  mismatches**", "**1,966 actions** instead of 341" ✓. T-10's table gives `ghost`
  at **6 actions**, `nocross` "**never, in 341 actions**" on `match` and **6**
  elsewhere, and `push1` as the one that flips `unsolvable_mismatch` ✓; the
  declaration `theorem unsolvable_mismatch [depends: push2]` is at
  `a0-spike/THEORIZE_LOG.md`:229 ✓.
* **§3.6 · the collision** — `THEORIZE_LOG.md` O-04's table gives Cart
  **+2967**, Button **−17**, Door **−13** ✓, and `A0_REPORT.md`:112-114 the same
  three ✓; "one event each in 275 transitions against a **21**-bit declaration" is
  O-04's own arithmetic ✓ (`A0_REPORT.md`:118 "costs 21 bits to declare");
  "cells (3,2) and (4,5) change, so they are not board, and if they are not
  objects either then two pixels of every frame are unexplained and cheap certify
  fails at frame 0" is O-04 near-verbatim ✓; `A0_REPORT.md`:241 (§8) books
  "Button −17 → **−5**, Door −13 → **−1** on a responsibility-complete baseline"
  and the exact phrase "**narrowed, not dissolved**" ✓, and `theory.dsl`:21-22
  carries `compress: -5` and `compress: -1` in the manual itself ✓.
* **§3.6 · the expressivity finding** — `THEORIZE_LOG.md`:359 books E-03 in the
  §E ledger with the frame axiom living in a comment ✓;
  `theory_prime.dsl`:20 declares `frame persist` with the gloss "an object no
  firing rule mentions is unchanged" ✓, and `cold-start-a0/prime/THEORIZE_LOG.md`
  R-04 rejects the still-rules as "All consequences of `frame persist`", i.e.
  appealing to something in the file ✓.
* **§3.7** — `A0_REPORT.md` §6 item 5 gives 59 states and "Lean's `decide` is
  affordable at 152 states and will not be at 10⁶" ✓; 57 for A0′ ✓; the seal hole
  in both spikes ✓ (`A0_REPORT.md` §6 item 3, `A0P_REPORT.md` §5).

---

## Pass C — uncited numbers

Eight. Five (C1, C2, C4, C6, C8) are the same defects as B4, B5, B9, B7 and B12
counted in both passes because they fail both tests; the other three are citation
gaps whose values are correct.

| # | § | PAPER.md / section:line | the claim | what it would need |
|---|---|---|---|---|
| **C1** | draft status | 14 / `00_abstract.md`:12 | "at roughly **27 500 words** it is about **six times** a workshop budget" | nothing, and it gets nothing — the only wholly uncited quantitative claim in the slice, and it is on the front page. See B4: `assemble.py`'s own count on this file is **36 242**. The right citation is `assemble.py`'s stdout, which is one command away |
| **C2** | §1.2 | 244 / `01_intro.md`:93 | "They wrote **105 attacks, of which 91 landed**" | a path. See B5: the sentence's citation is `battery/PREREG_V9.md`, which carries neither figure; 105 is `battery/STATUS.md`:23/:50 and 91 is `battery/audit/v9/REPORT.md`:137, and the JSON cited on the next line says 112/95 |
| **C3** | §1.2 | 212-214 / `01_intro.md`:61-63 | "Through v1 the suite checked only that an entry **existed**, never that it was **true**, so a wrong `defended: True` kept a gameable metric in the main table and nothing noticed" | a path. The preceding citation is `battery/audit/gaming.py`, whose docstring states the tier *rule* but says nothing about what the suite checked; the claim is at `battery/REPORT_V2.md`:197 ("wrong `defended: True` therefore kept a gameable metric in the main table"), which §1.2 cites sixteen lines later for a different figure. The claim is true |
| **C4** | §1.5 item 3 | 426-429 / `01_intro.md`:275-278 | "covering only **107/228** = 47 %" | the fraction's own file. See B9: `A0_REPORT.md` §8 has 47 % and 228/228 but not 107/228; `cold-start-a0/prime/artifacts/prime_report.json` (`trace.a0p-base.coverage`) and `A0P_REPORT.md` §1/§2 do |
| **C5** | §3.1 | 661-662 / `03_a0.md`:34-35 | "the manual was revised **zero** times by certify, and every iteration that did happen was in the compiler" — the figure's stated headline, in a paragraph asserting (L660) that "**every number in it** is in `figures/csv/fig06_concept_timeline.csv`" | a field. The CSV has no `revisions_driven_by_certify` column and no zero: it carries two `manual-revision` rows (`REV-01`, `REV-02`, triggered by the candidate pass and by the no-Button UNSAT, neither by certify) and four `certified` rows whose `trigger` reads "no certify->theorize iteration: nothing came back". The zero is an inference from an absence, and `check_figure_parity.py` hard-codes `{"value": "0"}` on the pipeline side rather than reading it from anywhere. So the paragraph's "every number in it is in the CSV" is not true of its own headline. `OPEN_ITEMS.md` C11 is this finding arriving from the figure side |
| **C6** | §3.1 | 668-670 / `03_a0.md`:41-43 | "the **eleven** other quantities the two implementations were checked against" | a countable source. See B7: `check_figure_parity.py::probes()` runs 14 comparisons and `PARITY.md` books 12 agree / 1 one-sided / 1 disagreement |
| **C7** | §1.2 | 247-248 / `01_intro.md`:96-97 | "the main table fell from nine metrics **to two**" | a field. See B6: the artefact named in the attribution line has `verdict.main: []`; the two is `battery/STATUS.md`:54's prose, and STATUS.md is named in the same attribution line — so this is a precedence inversion rather than a missing path |
| **C8** | §3.6 | 887-888 / `03_a0.md`:260-261 | "hard-coded in **all three** backends" | a source for the three. See B12: E-03 says "the backends" with no count |

Paragraphs that *look* orphaned and are not, checked and cleared:

* **The whole abstract** (L39-148) — exempt by the draft-status box's convention.
  Every figure in it was traced anyway, and every one recurs cited in the body
  except "84 %", which recurs as 83.6 % (see load-bearing finding (a)).
* **§3.2's MDL block** (L708-717) — inherits §3.2's lead citation to
  `cold-start-a0/A0_REPORT.md` §3, which carries all six figures, and names
  D-A0-007 explicitly.
* **§3.3's headline table** (L740-748) — the lead at L738 cites
  `cold-start-a0/prime/A0P_REPORT.md` §1 and the table is byte-identical to it.
* **§3.3's "n = 1 per arm"** (L773) — an editorial characterisation, not a
  measurement, and the paper says so in the next sentence.
* **§1.2's closing paragraph** (L279-285) — "falsified **17** of its own author's
  written claims" inherits the `gaming_audit.json` citation from L225-227.
* **§3.5's spike figures** — every one carries `a0-spike/THEORIZE_LOG.md` T-9 or
  T-10 in the sentence that states it.
* **§2.3's two-layer definition** and **§2.4's taxonomy** — both cite
  `Theoria.md` at the head of the passage and neither states a measurement.
* **§3.4's `push_onto_crate` narrative** (L829-834) — inherits `prime_report.json`
  from L820 and `A0P_REPORT.md` §3 from L812/L815, and both carry the figures.

---

## Pass D — quote fidelity

25 attributed passages checked: 11 blockquotes and code blocks, 14 inline
attributed fragments. **Five are inexact.** Every check was byte-for-byte after
unfolding the paper's hard wrap and stripping the source's own `>` and `**`
markers; nothing was accepted on a keyword match.

| # | § | PAPER.md / section:line | quoted as | source | problem |
|---|---|---|---|---|---|
| **D1** | §3.2 | 682-684 / `03_a0.md`:55-57 | a fenced block introduced by "with no vocabulary for buttons or doors, **it returned**": `[cell (3,2) shows 8]  +  [cell (4,5) shows 5]   ≡  1   (mod 2)` | `cold-start-a0/artifacts/engines_report.json`, `zero_space.global_laws[0]`; `cold-start-a0/THEORIZE_LOG.md`:298 | presented as what the engine returned, and it matches **neither** source. The artefact's `rendering` field is `(8@13 + 5@22) mod 2 = 1` with `support ["8@(3,2)", "5@(4,5)"]`; the log's L-02 heading is `[cell(3,2) is 8] + [cell(4,5) is 5] mod 2 = 1`. The paper's version changes "is" to "shows", inserts spaces inside the coordinates, and rewrites `mod 2 = 1` as `≡ 1 (mod 2)`. The *content* is right and the rewrite is a kindness to the reader, but a reader grepping the block finds nothing, and the block is fenced, which reads as transcription. Fixable by one word of framing ("rendered here as") |
| **D2** | §1.3 | 328-330 / `01_intro.md`:177-179 | `K2` defined as accuracy on pairs the trace never covered — "**"the metric replay cannot see"**" | `battery/artifacts/capability_spectrum.json`, `cards.K2.definition` | the card reads "**T**he metric replay cannot see." Case altered inside quotation marks, and the terminal period dropped. Trivial in isolation; listed because the exact-string search fails. The same sentence's gloss of `K4` is a genuine definitional drift and is B10 |
| **D3** | §1.2 | 247-250 / `01_intro.md`:96-99 | a blockquote closed by an em-dash attribution to `battery/runs/…/v9_gaming_audit.json` | the JSON | the file contains no prose at all, so nothing in the blockquote can be a transcription of it; and the sentence's second clause ("to two") is contradicted by the file's own `verdict.main: []`. The parenthetical naming the two fields actually read (`verdict.gameable` 37, `verdict.b14_baseline_main` 9) is the honest part and both are right. The paper's other blockquote in the same section (L223-227) uses the same form without an em-dash attribution and is clean; the fix is to use that form here |
| **D4** | §2.5 | 612-613 / `02_framework.md`:122-123 | > 每个阶段边界定义一个最小可发表单元——Phase 1 结:A0–A2 + 电池对既有轨迹的回算, 独立可成 workshop 文 | `Theoria.md`:381 | **byte-exact as far as it goes**, half-width `:` and `,` preserved — this is `CITECHECK.md`'s punctuation finding, fixed. It is listed here only for the truncation: the source's sentence continues ";Phase 3 结:开发堆案例研究…;Phase 4 结:主论文。" and the quote stops at "workshop 文" with no ellipsis. The framing ("`Theoria.md`'s Phase 4 deliverables clause") makes the scope clear, so this is the mildest item in the table |
| **D5** | §3.4 | 836-838 / `03_a0.md`:209-211 | "The report labels this what it is, and so does this paper: a **controlled experiment with a seeded error, not a discovery** (`cold-start-a0/prime/A0P_REPORT.md` §3, first paragraph)" | `A0P_REPORT.md` §3 ¶1 | the source reads "It is a **controlled experiment**, not a discovery, and it is labelled that way in the seeded manual's own header." The paper inserts "with a seeded error" inside the bolded span it attributes to the report. The insertion is *true* — the whole subsection is about the seed — but the sentence explicitly attributes the label to the report, and the report's label is three words shorter. Bold, not quotation marks, so the mildest class of this defect |

### Quotes verified exact

Byte-for-byte after unfolding the paper's wrap. Bold and `>` markers stripped on
both sides; nothing else adjusted.

* `battery/REPORT_V0.md`:25-26 — "Evidence coverage rewards precisely the caution
  that held-out accuracy punishes. A battery reporting K4 alone would show a
  flawless manual." (§1.3, L332-334) — exact, both sentences.
* `cold-start-a0/THEORIZE_LOG.md` R-05:233-235 — "the manual as written says that
  pushing up into the Button does nothing, and full-history replay will never
  catch that." (§1.3, L341-343) — exact.
* R-05:229 — "**not thin, zero**" (§1.3, L339) — exact.
* R-05:241-242 — "drive the Cart to (2,2) and push DOWN into an unpressed Button"
  (§1.3, L347-348) — exact.
* `THEORIZE_LOG.md`:633 — "the three pairs R-05 named" (§1.3, L349) — exact, and
  the paper's claim that it appears in the **seal section** is right, which is
  the load-bearing part of that sentence.
* `THEORIZE_LOG.md`:11-12 — "the same instance both built the A0 world at M1 and
  adjudicated it at M3" (§1.3, L363-364) — exact.
* `THEORIZE_LOG.md`'s "## Ground-truth seal" heading (§1.3, L359) — exact, and
  `score_vs_truth.json`'s `seal` field carries the same stamp, as the paper says.
* `THEORIZE_LOG.md` L-02:302-305 — "Read literally: over all 275 transitions,
  exactly one of *"the Button shows 8"* and *"the Door exists"* holds. In manual
  vocabulary: **the Door is present if and only if the Button is unpressed.**"
  (§3.2, L690-692) — exact, including the internal quotation marks.
* `cold-start-a2/A2_REPORT.md`:181-182 — "The instrument cannot tell them apart,
  and it is not supposed to be able to." (§1.4, L390-391) — exact.
* `cold-start-a2/A2_REPORT.md`:273 — "A2 tests the instrument and the loop, not
  the theorizer." (§1.6, L477) — exact.
* `cold-start-a0/prime/A0P_REPORT.md` §1:29-34 — "The variable is not how much
  was seen. It is whether what was seen could be seen **again**. …" (§3.3,
  L759-764) — exact, all six lines.
* `A0P_REPORT.md` §1's **seven-row headline table** (§3.3, L740-748) —
  byte-identical, every row, both renderings of 233/236 included.
* `A0P_REPORT.md` §3's fenced `rule push_onto_crate` block (§3.4, L805-808) —
  byte-identical, both lines including `[ev: none cov: 0/0]`.
* `cold-start-a0/prime/artifacts/prime_report.json`, `run_b.certify_lean` (§3.4,
  L826-827) — exact, **including the spacing** `(2, 4)` / `(2, 3)` that
  `A0P_REPORT.md` §3 renders without spaces. The paper follows the JSON, which is
  the precedence rule working.
* `theory-compiler/STATUS.md`:166 — "消费端完成；发射端……未写" (§2.2, L541-542) —
  the ellipsis is honest: the source reads "**消费端**完成；发射端是 engine-rig 的
  文件，未写", and the elided clause is stated in the paper's own preceding
  sentence.
* `Theoria.md` §1.10d:222 — "theorize → certify → probe → plan → commit" (§2.3,
  L564) — exact.
* `Theoria.md` Phase 3's **eight failure classes** (§2.4, L586-590) — all eight,
  in the source's order, half-width punctuation preserved.
* `Theoria.md` §1.0:10 — the 64×64 / sixteen-colours setting (§1.0, L156-159) —
  the paper renders it in English; the two facts and the "exactly two things: act,
  and observe" are the source's.
* `papers/phase1-workshop/figures/PARITY.md`:63 — the placeholder string
  `"see body"` (§3.1, L667-668) — exact.
* `battery/PREREG_V9.md`:192 — "the round's worst lapse" (§1.2, L270) rendering
  "**这条是本轮预注册最实的一处失守**" — a translation, correctly flagged as a
  characterisation ("which calls this…") rather than a quotation.
* `a0-spike/THEORIZE_LOG.md`:229 — `theorem unsolvable_mismatch [depends: push2]`
  (§3.5, L863-865) — exact.
* `capability_spectrum.json` `battery_version: "v2"` (§2.5, L617-618) — exact.

---

## Regressions and repairs since `CITECHECK.md`

`CITECHECK.md` targeted a 1319-line draft. Nine of its findings fall inside what
is now the Abstract–§3 range. Recording the disposition because an audit series
that never checks whether its own findings were acted on is decoration.

| `CITECHECK.md` finding | status now |
|---|---|
| §3.4 "111 frames, 8991 pixels, 0 anomalies" cited to `run_b.certify_cheap`, which is a bare boolean | **fixed by disclosure** — L815-821 now states that Run B's replay is the bare `true`, that the shape lives under `run_a.certify_cheap`, and that both runs replay the same 111-frame trace. Better than a silent repath |
| Abstract/§1.2 the two Lean files "differ in their weight table and in nothing else" | **fixed** — the abstract (L106-108) now claims only identity of generator, tactic, dependency surface and axiom list, and §1.4 (L385-388) says outright that the pair is *not* a minimal pair and points at §5.6's correction |
| §3.1 "29 schema-valid candidates" against the log's 28 (source disagreement 4) | **fixed** — L643-644 now carries the explanation inline, and it is exactly right: 3+23+2 = 28 adjudicated, the 29th row is a `plan` |
| §3.6 uncited "−5 and −1" | **fixed** — L880-882 cites `cold-start-a0/A0_REPORT.md` §8, which carries both |
| §3.1 uncited "about six seconds", cited to the wrong part of the report | **fixed** — L651-652 now reads "(`cold-start-a0/A0_REPORT.md`, preamble and §7)", and the figure is at :216, inside §7 |
| §2.5 malformed anchor "`Theoria.md` Phase 2 §Phase 1" | **fixed** — now "(`Theoria.md`, Part 2, Phase 1)", and `Theoria.md`:282 sits inside 第二部分 at :278 |
| §2.5's Phase 4 quote with full-width `：` `，` substituted for the source's half-width | **fixed** — the quote at L612-613 is now an exact substring of `Theoria.md`:381. Only the un-ellipsised truncation remains (D4) |
| Abstract takes an exemption the binding rule as written does not admit | **fixed by disclosure, with one hole** — the draft-status box (L21-25) now names the exemption and conditions it on every figure recurring cited in the body. The condition fails for exactly one figure: "84 %" (see load-bearing finding (a)) |
| Pass A: `playbook.dsl`, `THEORIZE_LOG.md`, `A0P_REPORT.md`, `prime_report.json` cited bare | **not fixed** — all four are still bare and are rows 4-7 of this report's Pass A table. Three siblings from the same list *were* fixed: `theory.dsl` and `raw_trace.jsonl` are now cited in full at L502/L635, `theory/theory.dsl` at L645/L727, and `PROVENANCE.md` at L23 |

Eight of nine repaired, and the two the paper handled by *disclosure* rather than
by repath are the two it handled best — §3.4's `run_b` boolean and the abstract's
exemption both now say what is wrong with them.

The five new-in-kind findings, none inherited: **B1** (a gloss the artefacts
contradict, in a subsection whose argument depends on it), **B2** (a
staleness warning that went stale), **B3** (a cross-reference that names the
wrong section and the wrong file for the same number), **B4** (the front page's
word count), and **C5** (a figure headline that is not in the CSV the paragraph
says holds every number in it). B1 and B4 are the two a reader can falsify
without leaving the repository: one `diff` of two JSON fields, one run of
`assemble.py`.

---

## What this audit could NOT check

Stated so the coverage claim above is not read as more than it is.

1. **Whether any Lean file compiles, or any suite passes.** Every green/red/
   axiom-list verdict in this slice — A0's `inv_all` with 0 axioms, M5's
   `unsolvable`, A0′ Run A's empty axiom list, Run B's `ArenaEscape` refusal —
   was read from the artefact that records it (`prime_report.json`
   `run_*.certify_lean`, `A0_REPORT.md`'s milestone table), not re-derived. I ran
   no `lean`, no `pytest`, no pipeline. A stale artefact would pass this audit
   unchallenged, and B2 is proof that artefacts in this tree do go stale.
2. **The battery's numbers as computed, only as recorded.** I read
   `capability_spectrum.json`, `gaming_audit.json` and `v9_gaming_audit.json` and
   recomputed *aggregates over their own fields* (the 88/7 split, the 112/95
   attack census, the 34/4 exploit split, the 14-of-17 `defended` count). I did
   **not** re-run `battery/run_battery.py` or any exploit, so I cannot say whether
   any recorded metric value is what the scorer would produce today. §1.2's own
   disclosure that a recompute gives 33/19 rather than 34/17 is the paper naming
   this exact risk, and I confirmed the recompute artefact rather than the
   recompute.
3. **§8's and §9's substance.** I opened `exam/artifacts/leakage.json` and the two
   `theoria-arm` manifests **only** for the abstract's chain, and read only the
   fields that chain names. Everything else about the exam instrument and the live
   runs — the two real leaks, "three of four papers never sat", the sealing
   apparatus, the 1.35 % residual — is slice C's and slice D's, and nothing here
   should be read as auditing it. I did confirm that the abstract's figures recur
   in those sections, which is what the exemption clause requires.
4. **The figure plates.** I read `figures/csv/fig06_concept_timeline.csv` row by
   row and `check_figure_parity.py`'s probe list, and confirmed the four
   `figures/out/{light,dark}/…svg` paths resolve. I did **not** regenerate a
   figure, compare a plate to its CSV, or verify that the rendered plate shows
   what §3.1 and §3.3 say it shows. C5 is a finding about the CSV, not about the
   pixels. §3.3's "one cell of that figure is deliberately empty" was checked only
   as far as `PARITY.md`'s one-sided row, which describes the same refusal.
5. **`figures/`' source registry and determinism.** The CSVs cite registry keys,
   not repo-relative paths. I did not resolve the registry or check that the
   declared hashes match, so §3.1's "parsed out of `THEORIZE_LOG.md`'s own
   headings rather than retyped" is confirmed at the level of the CSV's content
   agreeing with the log, not by reading the parser.
6. **Whether `A0_REPORT.md` §2's and `THEORIZE_LOG.md`'s "from the right" gloss
   should be corrected at source.** B1 establishes that the artefacts contradict
   it and that the paper inherited it. Which of the three files to change, and
   whether the two acceptance reports are editable after the fact (§7.3's
   convention says no report is edited retrospectively), is an adjudication and
   not an audit finding. I have stated what each file says.
7. **Anything about a sealed game.** By rule. §1.4's claims *about the
   substitution* are checkable and were checked (INC-004's ruling text, the
   isomorphism framing, `Theoria.md` §1.3 as the sole admissible source); any
   claim about DC22's own geometry, coverage or search is deliberately
   unverifiable, and the paper says so. `environment_files/` was never opened.
8. **Sources read only where a claim pointed into them.**
   `cold-start-a0/A0_REPORT.md`, `cold-start-a0/THEORIZE_LOG.md`,
   `cold-start-a0/prime/A0P_REPORT.md`, `cold-start-a0/prime/THEORIZE_LOG.md`,
   `a0-spike/THEORIZE_LOG.md` §§T-6/T-8/T-9/T-10, `battery/REPORT_V2.md`,
   `battery/audit/v9/REPORT.md`, `battery/PREREG_V9.md` and `Theoria.md` §§1.0,
   1.8, 1.10a/d/e, Phase 1/3/4 were read where cited and, for the two A0 logs,
   substantially in full — which is how B1 and B8 surfaced. `battery/METRICS.md`,
   `battery/BLINDING.md`, `battery/PREDICTIONS.md` and `battery/STATUS.md` were
   read by targeted search only. A contradiction sitting in an unvisited paragraph
   of any of them would not appear here.

The sibling reports were consulted for method. `citecheck-B-s4-to-s6.md` is
complete and substantiated, and its format is this report's model.
`citecheck-C-s7-to-s8.md` and the two `citecheck-D*` reports were **not** audited
by me and their counts are not endorsed here; slice B records that slice C ends
at line 43 with "*(report in progress)*". This report's counts are substantiated
by the tables above: every Pass A row, Pass B finding, Pass C item and Pass D
item is enumerated with a PAPER.md line, a section:line, a file and a field.
Where I could not check something it is in the list immediately above rather than
absorbed into a total.
