# P18 task 3 · B5 — is the 70-vs-52 disagreement still only recorded?

RES-2, 2026-07-30. The item's third task: "顺带确认 P17 开的 **B5**
(`CITECHECK.md` 说 70 diff lines、§5.6 说 52) 是否还只是记录、没被谁悄悄改成矛盾."

**Answer: still only recorded. No contradiction reached the paper, and every number
§5.6 states reproduces.** Measured here rather than read off B5's own account of
itself, for the reason §0 of `RULING.md` gives.

## The two sides, as they stand today

| document | line | number | text |
|---|---|---|---|
| `CITECHECK.md` | :103 | **70** | "`diff` of the two files: 70 diff lines" |
| `sections/05_a2.md` | :267-271 | **52** | "`diff -u` the two files and 52 lines change across 7 hunks … a reader running plain `diff` gets the same 52 lines in 15 groups" |

`CITECHECK.md`'s last commit touching it is `080f05da` — the commit that *applied*
the audits, i.e. before B5 was opened at P17. **Nobody has edited the audit since**,
which is what OUTLINE red line 3 requires. `sections/05_a2.md` has moved since (P17's
three commits), and its current text is the one that states the counting convention.
`PAPER.md:1371-1373` carries the same 52 as its section source — assembled artefact
and source agree.

## What I measured

Against `cold-start-a2/theory/generated_holed/theory.lean` and
`…/generated_repaired/theory.lean` (69564 and 69430 bytes):

| convention | command | result | §5.6 says |
|---|---|---|---|
| plain `diff`, changed lines | `diff A B \| grep -cE '^[<>]'` | **52** | 52 ✓ |
| `diff -u`, hunks | `diff -u A B \| grep -c '^@@'` | **7** | 7 ✓ |
| `diff -U0`, groups | `diff -U0 A B \| grep -c '^@@'` | **15** | 15 ✓ |
| `diff -U0`, total output lines | `diff -U0 A B \| wc -l` | **69** | — |

The weight-table share checks out too: 14 lines of the form `| .cNN => 0` on the
added side (c3, c4, c9, c10, c15, c16, c21, c22, c27, c28, c32, c33, c35, c36), each
against a removed counterpart — **28 of the 52**, exactly as §5.6 says, and the reason
the entry count and the line count differ. The four changed `step` clauses are all
`⟨Cell.c31, ButtonColour.v7|v8, DoorPresent.yes|no⟩, .down`, and `def Goal` moves
`Cell.c10` → `Cell.c34`. §5.6's decomposition is accurate.

## Where 70 nearly comes from

`diff -U0`'s output is **69** lines, and it decomposes exactly:

    2 file headers (---, +++)  +  15 hunk headers (@@)  +  52 changed lines  =  69

So B5's account of the audit's number is reproducible as an explanation and the
number itself is not: 70 is one past the nearest artefact any convention yields.
B5 already says "70 is not reproducible directly", and that remains the honest
statement — I did not find a convention that gives 70.

## Disposition

**No change to B5, and none to either document.** The disagreement is disclosed in
`OPEN_ITEMS.md` B5, the audit stays unedited by OUTLINE red line 3, and §5.6 carries
the convention at the point of use, which is the repair P17 chose. What this check
adds is that the numbers were re-measured a second time, by a second session, from
the files — and that the audit has not been quietly edited in the interval. B5 stays
**open — recorded, not reconciled**, which is the correct state for it, not a defect
waiting on someone.
