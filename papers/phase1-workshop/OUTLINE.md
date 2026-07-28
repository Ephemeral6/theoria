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
| 6 | The metrics battery, recomputed over existing trajectories | `sections/06_battery.md` | `battery/REPORT_V0.md`; `battery/PREDICTIONS.md`; `battery/artifacts/*.json` |
| 7 | Limitations and honesty clauses | `sections/07_limitations.md` | `Theoria.md` §3.2 item 8; every report's "what this does not show" |
| 8 | Related work, in one paragraph | `sections/08_related.md` | `Theoria.md` §3.1 |

Figures: `figures/` — data extraction is a script, styling is later.

| fig | content | data script |
|---|---|---|
| 1 | concept-birth timeline, with triggers | `figures/fig1_concept_timeline.py` |
| 2 | A0 vs A0′ coverage × accuracy | `figures/fig2_coverage_accuracy.py` |
| 3 | A2 打脸→重证 ledger flow | `figures/fig3_loop_ledger.py` |

## House style

* Past tense for what was run; present tense for what an artefact says.
* Numbers inline, path in backticks immediately after or in the table's own
  column. Do not batch citations at the end of a paragraph.
* Where a report already says something well, quote it in a blockquote and
  attribute the file. Paraphrase is where numbers get corrupted.
* No exclamation marks, no "surprisingly", no "we were pleased to find".
* Chinese terms from the framework (打脸/定位/戳探/修订/重证/解出) may stay, with
  an English gloss on first use.
