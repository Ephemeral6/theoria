# Section renumbering, v0.2 → v0.3

One section lands in the body, so the two after it move. This follows the map in
`papers/phase1-workshop/runs/20260728T092517Z-P6/SECTION_RENUMBER.md` and its
rule: **filename order and section order stay the same thing**, because
`assemble.py` concatenates `sections/*.md` in sorted filename order.

`CITECHECK.md` and `REVIEW.md` were run against earlier drafts and are kept
unedited, so anyone following a finding from either file needs this map as well
as P6's.

| v0.2 file | v0.2 § | v0.3 file | v0.3 § |
|---|---|---|---|
| `sections/00_abstract.md` … `sections/09_preflight.md` | — / 1–9 | unchanged | — / 1–9 |
| — | — | **`sections/10_adjudication.md`** | **10** (new) |
| `sections/10_limitations.md` | 10 | `sections/11_limitations.md` | 11 |
| `sections/11_related.md` | 11 | `sections/12_related.md` | 12 |

Subsections move with their sections: 10.1–10.5 → 11.1–11.5, 11.1–11.3 →
12.1–12.3. Only the heading lines changed in the two moved files; their bodies
are untouched by the renumber.

## Every cross-reference that moved

Swept for `§10`, `§11`, `§10.n`, `§11.n`, `Section 10|11` across `sections/` and
every live document in `papers/phase1-workshop/`. Seven references inside
`sections/`, and eleven in the surrounding documents:

| File | Was | Now |
|---|---|---|
| `sections/00_abstract.md` :40 | §11.1 | §12.1 |
| `sections/01_intro.md` :37 | §11.1 | §12.1 |
| `sections/01_intro.md` :304 | §10.5 | §11.5 |
| `sections/01_intro.md` :318 | §10.1 | §11.1 |
| `sections/01_intro.md` :329 | Section 10 | Section 11 |
| `sections/02_framework.md` :4 | §11 | §12 |
| `sections/03_a0.md` :67 | §11.1 | §12.1 |
| `OUTLINE.md` :39–40 | rows 10, 11 | rows 11, 12, with a new row 10 inserted above them |
| `OUTLINE.md` (prose ×2) | §11 | §12 |
| `PROVENANCE.md` :176, 199, 201, 204 | §10, §10.4, §10.3, §10.2 | §11, §11.4, §11.3, §11.2 |
| `OPEN_ITEMS.md` :26, 105 | §10, §10.1(c) | §11, §11.1(c) |
| `OPEN_ITEMS.md` :47, 58, 62, 82 | §11, §11.3 | §12, §12.3 |
| `REVIEW_TRIAGE.md` :60, 63, 65, 107 | §11.2, §10.3, §11, §10.1 | §12.2, §11.3, §12, §11.1 |

## What was deliberately **not** edited

* **`REVIEW_TRIAGE.md` :111–136 and :177** — the record of the P6/P7 renumber
  itself. Those lines describe the numbering as it stood then; rewriting them
  would falsify a record of a past state. Same reasoning as P6's for
  `CITECHECK.md` and `REVIEW.md`.
* **Everything under `papers/phase1-workshop/runs/`** — about 230 occurrences
  across 20 dated run records. No report in this repository is edited after the
  fact; that is what this map is for.
* **`PARTNER_SYNC.md`** — four real references to the paper's §11 (lines 739,
  740, 742, 1221). The board is append-only and is corrected only by appending,
  never by rewriting.
* Roughly 60 apparent hits elsewhere in the repository (`figures/PLAN.md §3/§10`,
  `ablation-arm/DESIGN.md §10`, `baseline-arms/BUDGET_REPORT.md §11.x`, the ARC
  terms-of-service §11, and GPL licence text) are **other documents' own section
  numbers**, not this paper's. Checked one by one; none is a reference to
  `PAPER.md`.

## Verification

`python papers/phase1-workshop/verify_paper.py` check A (GENERATED) passes after
`assemble.py`, so `PAPER.md` is the concatenation of the renamed files in the new
order. Checks B (PATHS) and C (FIGDATA) fail identically before and after this
change — three broken citations in `03_a0.md` / `06_a3_transfer.md` and one stale
figure payload, all pre-existing and none of them in the new section. Measured by
running `verify_paper.py` with `sections/10_adjudication.md` temporarily removed:
identical B and C output, 176 path citations instead of 197. The new section adds
21 path citations and **zero** broken ones.
