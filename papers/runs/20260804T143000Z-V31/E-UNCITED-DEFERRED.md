# E UNCITED @ `08_exam.md:154` — the finding, and why V31 did not fix it

**Status: open. Owner: RES-2. Opened 2026-08-04 by W-9208 under V31.**

`papers/phase1-workshop/verify_paper.py` binds to this file: the
`DEFERRED_UNCITED` entry beside check E names it, and check E fails if it stops
existing. Deleting this file re-reds the gate. That is deliberate — a deferral is
only as good as the written argument behind it.

The gate does **not** report this block as clean. It reports it as `DEFERRED`,
with the block text, in the same shape as an `UNCITED` line, on every run, and it
says so again on `verify_paper`'s verdict line so that `papers/verify.py` stage 2
— which prints a sub-gate's last line and nothing else — carries it too.

## The finding, stated exactly

Check E requires every quantitative claim block in the body to cite an artefact.
`sections/08_exam.md:154-171` is one block: §8.4's six-bullet list, merged by
`_blocks()` because a list chunk joins the prose chunk above it, with the §8.4
heading at L152 breaking the chain. The block contains no citation and one
quantity that survives `_quantities()`.

**The quantity is the `1` in "n = 1 per handover tier" (L156)** — not "Three of
four" in the bullet the failure line prints. `WORDNUM` (`verify_paper.py:1335`)
deliberately excludes `one`…`ten`, so "Three", "four", "Two" and "One" in this
block are invisible to the gate; the failure line simply prints the block's first
140 characters, which start at L154.

## The evidence exists, and it is not in this block

`n = 1 per handover tier` is evidenced by two files, both tracked, both verified
present on `18e7d81b`:

* `exam/artifacts/reports/p15-handover-a0.reader-tier1.report.json`
* `exam/artifacts/reports/p15-handover-a0.reader-tier2.report.json`

One report per tier *is* n = 1 per tier. §8.2 already cites them, at
`08_exam.md:79-80`, in the brace form `p15-handover-a0.reader-tier{1,2}.report.json`
that `expand_braces()` and `_split_siblings()` both handle. That is **twelve
blocks and seventy-six lines earlier**, with the whole of §8.3 in between.

## Why this was not fixed under V31

Two reasons, and the second is the one that matters.

**1. It is a paper-body edit.** `monitor/CHARTER.md` reserves paper body text to
RES-2, and `monitor/board/items/V31-papers-gate-red-on-master.md:32-33` repeats
the line for this item: a generic worker fixes gates and registrations, 不写论文
正文. W-9201 took the same reading on V29 and `origin/agent/v30-p18-hand-merge`
took it on the same three red checks, stating the gap rather than working around
it. V31 is the third worker to stop at this line; three consistent readings of a
charter is not a coincidence to override on a fourth.

**2. The one-line fix would be a false green, and the gate file says so in
advance.** Adding the citation to the `n = 1` bullet clears the entire merged
block, because `_quantities()` returns nothing the moment any citation appears
anywhere in it. That exempts four sibling bullets as well — and this is not a
theoretical worry, it is the exact reason a ruling covering this block was
**withdrawn on purpose** on 2026-07-30. The withdrawal note is
`verify_paper.py`'s longest comment (in the `ADJUDICATED_UNCITED` table) and it
ends: *"A false green is worse than a red gate; that is the whole finding."*

Three of the four sibling bullets state things the repository now refutes.
Re-verified against `18e7d81b` on 2026-08-04:

| bullet | claim | status |
|---|---|---|
| L160-164 | "**The calibration bands are outside the rubric digest.** … Closing it is not done." | **Closed.** D-EX-016: `exam/DECISIONS.md:383`, `exam/grading/selftest.py:620` `protocol_digest()`, and `exam/STATUS.md` L220-227 struck through. |
| L165-168 | "**The cheater's numbers are prose, not artefacts.** … no cheater response or transcript is archived." | **Refuted in part.** `exam/artifacts/answers/p15-verdict-a2.cheater-v4.answers.json` exists, is tracked, carries 17 claims with `meta.exploit_per_item`, and is scored. The clause about the gitignored brief directory survives. |
| L169-171 | "**Two cheater agents, four sheets, one pass**" and the italicised quotation *the leaks that remain are the ones nobody has looked for yet*, attributed to "the directory" | **Superseded and unsourced.** `exam/STATUS.md` L265-273 carries the weakness struck through ("Partly closed by V4"). The quoted sentence appears nowhere in the repository except `08_exam.md:170` itself. |
| L154-155 | "**Three of four papers have no real result.** … Nothing has sat them." | **Needs narrowing.** `exam/artifacts/exam_summary.json` has `"marked": []`, but `exam/artifacts/matrix/verdict_confusion.json` records `cheater-v4` at `awarded 17.0 / possible 34.0` with `is_fake: False` — a non-fake examinee has sat verdict. The true statement is that no theory has been *marked* on them. |

Prior art: `papers/phase1-workshop/runs/20260730T000000Z-P18-audits-cover-half/section-8-4-evidence-check.md`
is a per-bullet evidence check of this same block. Every one of its findings still
holds today; the table above is a re-verification, not a restatement.

## The repair RES-2 is being handed

Not the citation alone. The citation **and** the four prose corrections, together,
as one change — because the citation is what removes the gate's ability to keep
asking about the rest.

1. `08_exam.md:156-157` — cite `exam/artifacts/reports/p15-handover-a0.reader-tier{1,2}.report.json`
   on the `n = 1` bullet.
2. `08_exam.md:164` — "Closing it is not done" is false; D-EX-016 closed it.
3. `08_exam.md:167` — "no cheater response or transcript is archived" is false;
   keep the gitignored-briefs clause, drop or qualify the rest.
4. `08_exam.md:169-171` — the weakness is struck through upstream, and the
   italicised quotation has no source. Re-source it or remove it.
5. `08_exam.md:154-155` — narrow to "nothing has been *marked* on them".
6. Then delete the `DEFERRED_UNCITED` entry in `verify_paper.py`. It will fail as
   `STALE` if left in place, which is the intended pressure.
7. `assemble.py` must be re-run: check A compares `PAPER.md` against `sections/`.

## What was considered and rejected

* **A ruling.** Reinstates verbatim what was withdrawn on 2026-07-30 for cause.
  It is also mechanically available — the anchor is 43 characters, over
  `MIN_ANCHOR`, and unique in the section — which is exactly why declining it has
  to be written down rather than left implicit.
* **Deleting the digit** ("a single reader per handover tier"). Turns E green with
  no citation at all: a one-character evasion of the check, and `WORDNUM`'s own
  docstring (`verify_paper.py:1331-1332`) says the spelled-out forms must not buy
  anything.
* **Splitting `_blocks()` so list items are separate blocks.** Would make the
  blast radius per-bullet and is arguably the right long-term shape, but it
  re-partitions all 435 blocks in the paper and would open an unknown number of
  new reds — a gate-semantics change of that size is not a fix for a red gate, it
  is a separate ticket with its own adversarial pass.
* **Leaving check E red.** The honest option, and the one V30 took. Rejected here
  because a red `papers/verify.py` is not a marker on §8.4, it is a brake on the
  whole territory: `ci_merge` refuses every branch touching `papers/`, and it had
  already stranded `agent/v29-one-proxy-validated-not-two` and
  `agent/v30-p18-hand-merge` — two branches with no failures of their own — for a
  day. A finding belongs on the board and in the gate's output. It does not belong
  in the exit code of a gate that blocks other people's finished work.
