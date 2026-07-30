# CITECHECK slice A — Abstract through §3

**Audited state.** `papers/phase1-workshop/PAPER.md`, sha256
`6b633fcc35ae612f20f4028eb45aaca1b6ed86a24eb1304af555c46228325376`, 3729 lines,
237872 bytes. Slice: lines 1-908 (§Abstract-§3). Auditor: CITECHECK re-run, P18,
2026-07-30.

**Method.** The four passes and the precedence rule ("JSON artefacts beat prose
reports") are copied from `papers/phase1-workshop/CITECHECK.md`, whose own target
was the 1319-line v0.3 draft and is therefore stale as a finding list. Pass A was
scripted (every backtick span in lines 1-908, filtered to path-like tokens, tested
with `os.path.exists` at the worktree root and then against 13 candidate bases);
Passes B, C and D were manual, each cited artefact opened and the value read from
the named field.

**Line mapping.** `assemble.py` prepends a 2-line banner and joins sections with
`\n\n---\n\n`, so within this slice:

| PAPER.md lines | section file | offset |
|---|---|---|
| 3-148 | `sections/00_abstract.md` 1-146 | `PAPER − 2` |
| 152-487 | `sections/01_intro.md` 1-336 | `PAPER − 151` |
| 491-624 | `sections/02_framework.md` 1-134 | `PAPER − 490` |
| 628-905 | `sections/03_a0.md` 1-278 | `PAPER − 627` |

---

## Summary

| pass | measure | count |
|---|---|---|
| A | distinct path-like tokens cited in backticks | **69** |
| A | resolve as written, repo-relative from the worktree root | **62** |
| A | exist, but **only** under a section-implied base | **7** |
| A | do not exist anywhere in the tree | **0** |
| B | distinct numeric claims traced to a file and checked | **~95** |
| B | wrong, mis-attributed, or not present in the cited file | **8** |
| C | numbers with no citation at all, or a citation lacking them | **9** |
| D | attributed quotations checked (blockquotes + inline fragments) | **14** |
| D | inexact — paraphrase, compression, or punctuation-normalised | **4** |

**Bottom line.** No path in the slice is broken. The rule's failure mode here is
not broken links but *citations that point at the wrong artefact for the number
they carry*: six of the eight Pass B findings are of the form "the number is true
somewhere, but not in the file named beside it". Three findings are load-bearing —
they survive into the abstract or a headline claim of §1: the abstract's
"1 790 probes" / "$6.32" / "84 %" chain, the §1.5 "95 runs across 5 arms" arm
census, and the §1.2 sentence attributing the 38-metric five-family split to
`battery/artifacts/capability_spectrum.json`.

---

## Pass A — path existence

69 distinct path-like backtick tokens in lines 1-908. **All 69 resolve to
something in the tree; none is broken.** Seven are not repo-relative as written.

| cited as | PAPER.md line | section file:line | actually at |
|---|---|---|---|
| `PAPER.md` | 26 | `00_abstract.md`:24 | `papers/phase1-workshop/PAPER.md` |
| `assemble.py` | 27 | `00_abstract.md`:25 | `papers/phase1-workshop/assemble.py` |
| `A0_REPORT.md` | 349 | `01_intro.md`:198 | `cold-start-a0/A0_REPORT.md` |
| `playbook.dsl` | 506 | `02_framework.md`:16 | ambiguous — 16 files carry the name; §2.1 means `cold-start-a0/theory/playbook.dsl` (the manual on the line above is cited in full as `cold-start-a0/theory/theory.dsl`, so the asymmetry is visible on one line) |
| `THEORIZE_LOG.md` | 549 | `02_framework.md`:59 | ambiguous — 4 files (`cold-start-a0/`, `cold-start-a0/prime/`, `cold-start-a2/`, `a0-spike/`); generic use ("written down by the LLM in a `THEORIZE_LOG.md`"), and the four are enumerated in full three lines later |
| `A0P_REPORT.md` | 757 | `03_a0.md`:130 | `cold-start-a0/prime/A0P_REPORT.md` |
| `prime_report.json` | 829 | `03_a0.md`:202 | `cold-start-a0/prime/artifacts/prime_report.json` (cited in full at L820, nine lines earlier) |

One near-miss not counted above: `dsl_grammar_v0.1` (L887, `03_a0.md`:260) is a
bare grammar name with the extension dropped; the file is
`CONTRACTS/dsl_grammar_v0.1.md`, cited correctly at L506. Cosmetic.

`figures/…` tokens (L658-660, L731-733) resolve at the **repo root** `figures/`
directory, which is the intended one — `figures/fig06_concept_timeline.py` and
`figures/csv/fig06_concept_timeline.csv` both exist there. Note that a *second*
figure tree exists at `papers/phase1-workshop/figures/` (holding `fig1…`, `fig2…`,
`fig3…` and `PARITY.md`, cited at L670); the two use different numbering, so the
root-relative citations are unambiguous. Not a finding.
