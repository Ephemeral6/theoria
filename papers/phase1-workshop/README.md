# papers/phase1-workshop

The Phase 1 minimum publishable unit, as `Theoria.md`'s Phase 4 deliverables
clause defines it:

> 每个阶段边界定义一个最小可发表单元——Phase 1 结：A0–A2 + 电池对既有轨迹的回算，
> 独立可成 workshop 文

A Markdown draft, not a submission. Authorship, venue and bibliography are
placeholders; figures are data first and styling later.

## Layout

| path | what it is |
|---|---|
| `PAPER.md` | **generated** — do not hand-edit |
| `sections/*.md` | the editable source, one file per section |
| `assemble.py` | concatenates `sections/*.md` into `PAPER.md`, in filename order |
| `OUTLINE.md` | the frame the sections were written to, including the red lines |
| `PROVENANCE.md` | every load-bearing number in the paper → the file it came from |
| `figures/*.py` | figure **data** extractors, deterministic |
| `figures/data/*.json` | extracted payloads |
| `figures/*.txt` | plain-text renderings, for reading before anything is styled |
| `REVIEW-2026-08-01.md`, `CITECHECK-2026-08-01.md` | **the live pair** — binding on the current `PAPER.md`. Both are *delta* audits of the 2026-08-01 probe-frontier correction; the coverage of the untouched text is carried by the chain of stale predecessors they name |
| `REVIEW-2026-07-31.md`, `CITECHECK-2026-07-31.md` | **retired 2026-08-01.** Delta audits of the four-forms correction; still true of that text, no longer covering the target |
| `REVIEW-2026-07-30.md`, `CITECHECK-2026-07-30.md` | **retired 2026-07-31.** The last full-paper passes; `CITECHECK-2026-07-30.md` is an index over five slice files under `runs/` |
| `REVIEW.md`, `CITECHECK.md` | **retired.** Both are pinned to a `PAPER.md` of 75,885 bytes, which is 29.1% of the current text; both carry `status: stale` and a `superseded_by` in their own stamp |

Do not read this table for which audit is binding: it is prose and it has been
wrong before — it named the 2026-07-30 pair as live for a day after the
2026-07-31 pair superseded them. `verify_paper.py`'s **G AUDITSTAMP** prints the
answer from the stamps themselves on every run, and `audit_stamp.binding_audits`
is the programmatic form.
| `runs/` | the run archive for this piece of work |

## Rebuild

```bash
cd papers/phase1-workshop
python figures/fig1_concept_timeline.py
python figures/fig2_coverage_accuracy.py
python figures/fig3_loop_ledger.py
python assemble.py
```

No network, no API key, no model call, no game spend. The extractors read only
files already committed to this repository and are byte-deterministic: running
them twice produces identical output, which is the property that lets a reviewer
check a figure rather than trust it.

## The rules this draft is held to

1. **Every number points at a file in this tree**, cited by repo-relative path.
   `CITECHECK-2026-07-30.md` is the mechanical test of that rule; its findings
   are not hidden. Each audit report opens with an ```` ```audit-stamp ````
   block naming the sha256, line count and byte count of what it audited, and
   `verify_paper.py`'s check **G AUDITSTAMP** goes red when a report calling
   itself `binding` no longer covers the current text. Two audits sitting in
   this directory describing themselves in the present tense while pinned to a
   third of it is what that gate exists to stop, and it is what this table said
   until 2026-07-30.
2. **No experiment, no "we show".** Anything not run is a limitation or is
   absent. This paper reports no play, no baseline comparison, and no claim from
   the Phase 3 claim menu.
3. **No source report was edited.** The acceptance reports are read-only inputs.
   Where a report and a later artefact disagree, the paper cites both and says
   which is later (see §7.3 on Fast Downward).
4. **The sealed pile is not touched.** The only sealed-pile statements are the
   contamination records already on file (INC-004, INC-BA-001), cited from
   `arc-recon/README.md`, `cold-start-a2/A2_REPORT.md` and
   `baseline-arms/INCIDENTS.md`.

## Sources

Nothing in the draft is new work. It is a reading of:

* `cold-start-a0/A0_REPORT.md`, `cold-start-a0/THEORIZE_LOG.md`
* `cold-start-a0/prime/A0P_REPORT.md`, `cold-start-a0/prime/THEORIZE_LOG.md`
* `a0-spike/THEORIZE_LOG.md`
* `theory-compiler/STATUS.md`, `theory-compiler/DECISIONS.md`
* `cold-start-a2/A2_REPORT.md` and its `artifacts/`
* `battery/REPORT_V2.md` and `battery/artifacts/` (current — `battery_version: "v2"`), `battery/PREDICTIONS.md`, with `battery/REPORT_V0.md` for the v0 statements §7 still quotes and `battery/REPORT_V1.md` for the v1 counts it cites
* `Theoria.md`, for the mandate and the narrative skeleton
