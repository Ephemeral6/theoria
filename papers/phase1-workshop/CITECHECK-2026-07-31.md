# CITECHECK — 2026-07-31 delta: the four-forms correction

```audit-stamp
target: papers/phase1-workshop/PAPER.md
sha256: 0c173e2219ff727cb3f10d2463cef9a15578c19bfcb44ee8f3f54d9231a48d49
lines: 3825
bytes: 244675
scope: delta audit of the 2026-07-31 four-forms correction (five edited sites in the abstract, §1.5, §2.1, §3.1, §11.3); everything outside those edits is unchanged from the state CITECHECK-2026-07-30.md pinned, and that file's five-slice index remains the evidence for it
status: stale
superseded_by: CITECHECK-2026-08-01.md
date: 2026-07-31
```

**Retired 2026-08-01.** The four-forms delta this file audits is unchanged and
its verdicts still hold of that text, but `PAPER.md` moved again on 2026-08-01
(the probe-frontier correction), so this stamp no longer covers the target and
is flipped by its own rule rather than by anyone's judgement.

**What this file is.** The successor `CITECHECK-2026-07-30.md`'s stamp names.
It is a **delta audit, not a re-audit**: the 2026-07-31 edit touched five sites
(`sections/00_abstract.md`, `sections/01_intro.md` §1.5 item 3,
`sections/02_framework.md` §2.1, `sections/03_a0.md` §3.1,
`sections/11_limitations.md` §11.3) to repair the "four co-derived forms"
claim against `crosscheck/FOUR_FORMS_TRUTH.md`, and this file audits the
paths, numbers and quotes those edits introduced — nothing else. For the
unchanged remainder of the paper, the covering audit is still the five-slice
index in `CITECHECK-2026-07-30.md` and
`runs/20260730T000000Z-P18-audits-cover-half/`; it audited the same bytes,
which have not moved. That carrying-forward is a claim about byte-identity of
the untouched text, not a fresh reading of it, and it is stated here so nobody
reads this stamp as a full re-audit.

## Every quantitative claim the delta introduced, checked against its artefact

| claim (as edited) | where in the paper | artefact | checked how | verdict |
|---|---|---|---|---|
| general backend compiled **0 of 303** actions to usable PDDL, pre-repair | abstract, §1.5, §2.1, §11.3 | `crosscheck/FOUR_FORMS_TRUTH.md` §1; frozen run `crosscheck/runs/20260730T120005Z-C14-four-forms-is-three-and-a-half/` | §1's headline table read: 303 owed, 0 good, 0.0 %; every slicing row is 0 | ok |
| zero survives every slicing of the denominator | §11.3 | same, §1 slicing table (9 rows, max good 0) | table read row by row | ok |
| Fast Downward accepted only domains whose actions assert nothing | §11.3 | same, §2: 7 accepted domains, all 21 actions doubly empty | §2 table read | ok |
| repaired 2026-07-31 | abstract, §1.5, §2.1, §3.1, §11.3 | commit 8a69426a "theory-compiler: the fourth form is generated, not hand-fitted — gen_pddl repaired"; `PARTNER_SYNC.md` heading `## [theory-compiler] 2026-07-31T06:03Z gen-pddl-repaired` | commit and sync paragraph read | ok |
| post-repair census: **196 of 299** semantically non-empty, **103 declared refusals**, 34 refused theories | abstract, §1.5, §11.3 | `crosscheck/runs/20260731T061500Z-C14-after-the-repair/out/census.md` | header table read: 299 owed / 196 good / 103 defective, `file-refused: 103`, "refused outright 34 (103 rules)" | ok |
| every planning number in the paper produced through `cold-start-a0/compile/gen_pddl_a0.py` and per-world drivers | abstract, §1.5, §2.1, §3.1, §11.3 | `crosscheck/runs/20260730T120005Z-C14-four-forms-is-three-and-a-half/out/TWO_BACKENDS.md` ("Every planning number in the paper is B's": A0 `fd_real.json` fingerprints, A2/A3/A6/ablation drivers enumerated) | document read; fingerprint argument (cell naming `c%d-%d`, three-parameter `press-left`) checked against its cited lines | ok |
| repaired backend grounds every schema and solves the A0 level in 12 steps | §3.1, §11.3 | `theory-compiler/tests/test_e2e_rehearsal.py`, `test_pddl_compiled_against_the_level_solves_like_the_world` | test read: asserts grounded == schemas and BFS `depth == 12`; the paper's wording was corrected during this audit to plan *length*, not identical action sequence | ok |
| `a0-cart` ships all five files of its four forms generated; `a0-sokoban2`'s planning form is a declared refusal printed on its cover | §11.3 | `theory-compiler/handover_packages/a0-cart/README.md` (five-row form table, all "yes"); `theory-compiler/handover_packages/a0-sokoban2/README.md` (planning rows "no — see below", `UnsupportedClause` reason quoted) | both READMEs read | ok |
| `theoria-arm/inner/books.py` turns red on an undeclared PDDL failure; green keyed on planning and prose forms too | §2.1, §11.3 | `theoria-arm/inner/books.py` (`result["ok"] = python form and "pddl" not in errors and "markdown" not in errors`; declared refusals recorded under `refusals` do not turn it red) | code read at the assignment | ok |
| the generator parses its own output before shipping | §2.1, §11.3 | commit 8a69426a message; `theory-compiler/src/theory_compiler/generators/gen_pddl.py` (post-repair self-check via `strips.parse_domain`) | commit message and generator diff read | ok |
| census measured the PDDL form only; Lean/Python/Markdown not verified by it | abstract, §11.3 | `crosscheck/FOUR_FORMS_TRUTH.md` §8 ("Measures the PDDL form only") | scope section read | ok |

## Findings

* **One wording defect found and fixed during the audit** (recorded because an
  audit with zero findings should say what it looked for): the first draft of
  the §3.1 and §11.3 edits said the repaired backend solves the level "with the
  same 12-step plan". The pinning test asserts plan *length* (BFS depth 12),
  not action-sequence identity; both sentences now say so.
* **Two register defects found and fixed during the audit:** the abstract and
  §1.5 first said "196 of 299 actions usable" post-repair, where the census's
  own bar is "semantically non-empty and well-formed" and its §3 caveat calls
  that a ceiling on correctness, not a floor; both sites now use the census's
  words and §11.3 states the ceiling caveat with its citation
  (`crosscheck/FOUR_FORMS_TRUTH.md` §3).
* **A known one-decimal discrepancy, avoided rather than resolved:** the
  post-repair fraction is printed as 65.5 % in
  `crosscheck/runs/20260731T061500Z-C14-after-the-repair/out/census.md` and as
  65.6 % in `crosscheck/FOUR_FORMS_TRUTH.md`'s superseded-section table
  (196/299 = 65.55…). The paper cites the counts, not the percentage.
* The delta adds no bare-filename citations and no line-anchored citations;
  `verify_paper.py` checks B, E and F were run after the edit and report no
  finding attributable to it.
