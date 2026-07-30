# CITECHECK slice C — §7 (metrics battery) and §8 (the exam)

**Audited state.** `papers/phase1-workshop/PAPER.md`, sha256
`6b633fcc35ae612f20f4028eb45aaca1b6ed86a24eb1304af555c46228325376`, 3729 lines,
237872 bytes. Slice: lines 1669-2520 (§7-§8). Auditor: CITECHECK re-run, P18,
2026-07-30.

**Line mapping.** PAPER.md L1669-2321 = `sections/07_battery.md` L1-653
(offset −1668). PAPER.md L2325-2517 = `sections/08_exam.md` L1-193
(offset −2324). Every finding below gives both.

**Rule under test.** "Every quantitative claim carries the repo-relative path of
the artefact it came from." Four passes: path existence, number verification,
orphan numbers, quote fidelity. Precedence: JSON artefacts beat prose reports.

**Sealed-pile discipline.** Nothing in §7 or §8 names a sealed game. Every game
id that appears in the slice or in the artefacts opened for it is
development-pile (`ar25-0c556536`, `g50t-5849a774`, `sk48-d8078629`,
`tn36-ef4dde99`). `exam/guard.py` and `battery` provenance were read only for
their cut *counts*, never for sealed-game content. No sealed material was read.

---

## Summary

| pass | measure | count |
|---|---|---|
| A | distinct path-like tokens cited in backticks | **56** |
| A | resolve as written, repo-relative from the tree root | **53** |
| A | resolve only under a section-implied base | **1** |
| A | resolve only after brace expansion (shell-style `{a,b}`) | **2** |
| A | do not exist anywhere in the tree | **0** |
| B | distinct numeric claims traced to a file and checked | **~185** |
| B | wrong, mis-attributed, or not present in the cited file | **6** |
| C | numbers with no citation at all, or a citation lacking them | **7** |
| D | attributed quotations checked (blockquotes + inline fragments) | **21** |
| D | inexact — paraphrase, compression, or truncation | **4** |

*(counts finalised at the end of the run; see the pass sections below)*

---

*(report in progress — sections appended as each pass completes)*
