# OUTLINE — Phase 1 workshop paper

The frame every section draft must fit. Written before the sections; kept so a
reader can see what the sections were asked to do.

**Mandate.** `Theoria.md` Phase 4, 阶段交付物: *"Phase 1 结：A0–A2 + 电池对既有
轨迹的回算，独立可成 workshop 文"*. The narrative skeleton is `Theoria.md` §3.2;
this paper is the Phase-1-sized cut of it, not the main paper.

## Red lines, binding on every section

1. **Every number points at a file in this tree.** Cite with a repo-relative
   path, e.g. `cold-start-a0/artifacts/score_vs_truth.json`. A number with no
   path does not go in.
2. **No experiment, no "we show".** Anything not actually run is written as a
   limitation or is absent. In particular: nothing about DC22, nothing about
   ARC play, nothing about scale, nothing about an LLM writing the manuals.
3. **No report text is edited.** The four acceptance reports and `REPORT_V0.md`
   are read-only sources. Quote them; do not revise them.
4. **Authorship is a placeholder.** No real names, no affiliations.
5. **The sealed pile is not touched.** The only sealed-pile statement permitted
   is the INC-004 caveat, cited from `arc-recon/README.md` and
   `cold-start-a2/A2_REPORT.md` §1.

## Section map

| § | title | owner file | primary sources |
|---|---|---|---|
| 0 | Title, placeholder authorship, abstract | `sections/00_abstract.md` | all |
| 1 | Intro — the hook: a perfect score and a broken theory | `sections/01_intro.md` | `cold-start-a0/THEORIZE_LOG.md` R-05; `cold-start-a0/artifacts/score_vs_truth.json`; `cold-start-a2/A2_REPORT.md` §2 |
| 2 | The framework, in the amount this paper needs | `sections/02_framework.md` | `Theoria.md` §1.7–1.10 |
| 3 | A0 / A0′ — reversibility beats coverage | `sections/03_a0.md` | `cold-start-a0/A0_REPORT.md`; `cold-start-a0/prime/A0P_REPORT.md`; `cold-start-a0/prime/artifacts/prime_report.json` |
| 4 | A1 — a certificate that crosses a data boundary | `sections/04_a1.md` | `theory-compiler/STATUS.md`; `engine-rig/interop/certificates/pagoda_5_11011_to_00010.json` |
| 5 | A2 — the exhibit and the repair loop | `sections/05_a2.md` | `cold-start-a2/A2_REPORT.md`; `cold-start-a2/artifacts/loop_ledger.json` |
| 6 | A3 — the second level, and which layer catches a broken one | `sections/06_a3_transfer.md` | `cold-start-a3/A3_REPORT.md`; `cold-start-a3/artifacts/bill_table.md`; `.../negative_controls.json`; `.../score_vs_truth.json` |
| 7 | The metrics battery, recomputed over existing trajectories | `sections/07_battery.md` | `battery/REPORT_V2.md`; `battery/PREDICTIONS.md`; `battery/artifacts/*.json`; `battery/REPORT_V0.md` and `battery/REPORT_V1.md` for the v0/v1 statements the section still quotes |
| 8 | The exam — four question types, and what the grader cannot see | `sections/08_exam.md` | `exam/` |
| 9 | The preflight — a real credential path with nothing spent | `sections/09_preflight.md` | `theoria-arm/`; `proxy/`; `arc-recon/` |
| 10 | Does the adjudication surface exist? A census of the implementation | `sections/10_adjudication.md` | the four census reports, preserved verbatim at `papers/phase1-workshop/runs/20260729T140000Z-P14-honesty-section/inputs-verbatim/`; `engine-rig/ENGINE_TABLE.md`; the engine sources they name |
| 11 | Limitations and honesty clauses | `sections/11_limitations.md` | `Theoria.md` §3.2 item 8; every report's "what this does not show" |
| 12 | Related work — six lines, with a bibliography | `sections/12_related.md` | `Theoria.md` §3.1 and §3.2 item 7; verification traces in `papers/phase1-workshop/runs/20260728T102014Z-P7/` |

§12 grew from one paragraph to six lines at P7, which is the fix REVIEW issue 14
asks for. A sixth red line binds it and only it:

6. **A bibliographic record that could not be cross-verified against two
   independent sources is not cited.** Not softened, not hedged — absent. Every
   record in §12 carries a trace in
   `papers/phase1-workshop/runs/20260728T102014Z-P7/search-traces/` naming the two
   sources and what each confirmed, and a 20 % adversarial re-check was run over
   the set. Where a system has no citable venue — Schema, Sora, several prover
   papers — it is cited as what it is, and no arXiv id, DOI or venue is invented
   to fill the slot.

Sections 6, 8 and 9 are the v0.2 additions; the renumbering map from v0.1, which
`CITECHECK.md` and `REVIEW.md` were run against, is
`runs/20260728T092517Z-P6/SECTION_RENUMBER.md`. Red line 3 covers those two files
too — they are audit records of a state the draft was in, and are not edited to
match the state it is in now.

Figures: the repository's deterministic pipeline at **`figures/`** (repo root) —
not this directory. Each plate is built by one script through a CSV audit layer
from a hashed source registry, and `figures/verify.sh` holds eight gates over it
(two builds byte-identical, committed tree equal to a fresh build, every source
hash unchanged, no undeclared read, and a coverage probe). Styling lives in
`figures/theme.py` and nowhere else.

| fig | content | built by | plate | numbers |
|---|---|---|---|---|
| 1 | concept-birth timeline, with triggers | `figures/fig06_concept_timeline.py` | `figures/out/{light,dark}/fig06_concept_timeline.{svg,png}` | `figures/csv/fig06_concept_timeline.csv` |
| 2 | A0 vs A0′ coverage × accuracy | `figures/fig07_a0_vs_a0prime.py` | `figures/out/{light,dark}/fig07_a0_vs_a0prime.{svg,png}` | `figures/csv/fig07_a0_vs_a0prime.csv` |
| 3 | A2 打脸→重证 ledger flow | `figures/fig05_a2_repair_loop.py` | `figures/out/{light,dark}/fig05_a2_repair_loop.{svg,png}` | `figures/csv/fig05_a2_repair_loop.csv` |

`papers/phase1-workshop/figures/` held a **second implementation** of these same
three figures. It is no longer the source; it is kept as the witness, and
`check_figure_parity.py` there makes the two answer the same questions. What
that comparison found — twelve agreements, one disagreement about what counts as
evidence, and one miscount the paper had been carrying — is in
`papers/phase1-workshop/figures/PARITY.md`.

## House style

* Past tense for what was run; present tense for what an artefact says.
* Numbers inline, path in backticks immediately after or in the table's own
  column. Do not batch citations at the end of a paragraph.
* Where a report already says something well, quote it in a blockquote and
  attribute the file. Paraphrase is where numbers get corrupted.
* No exclamation marks, no "surprisingly", no "we were pleased to find".
* Chinese terms from the framework (打脸/定位/戳探/修订/重证/解出) may stay, with
  an English gloss on first use.
