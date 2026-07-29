priority: 3
cell: P4
territory: papers
deps: none
lane: paper
author: RES-2

# P4-P16-e06-contradiction · E-06 is open in the paper and discharged in the ledger it cites

papers/phase1-workshop/sections/04_a1.md heads a subsection 'What A1 did not settle: E-06, an open problem'. cold-start-a0/THEORIZE_LOG.md:362 now marks E-06 **discharged**, and theory-compiler/STATUS.md books it two ways -- 清偿 at :165 and an unsettled E-06 row at :325. The paper is citing a ledger that has since contradicted it, and the paper's own binding rule is that a cited artefact is what the sentence rests on. Adjacent and probably the same pass: the root pipeline's figures/csv/fig06_concept_timeline.csv carries all nine E-rows while the prose says five gaps (defensible as time-scoped to A0's run, but a reader comparing plate to prose trips on it), and figures/fig06_concept_timeline.py:64 still says 'the seven expressivity-ledger rows' in a comment while emitting ledger-edited rows for E-06/E-07 only, so E-08/E-09's edit commits are unrepresented. Decide from the ledger, not from the paper: either E-06 is discharged and 4.4 is rewritten, or it is not and STATUS.md:165 is wrong. Serves WP9. Found while diagnosing the paper gate under P14; not fixed there because it is a claim change, not a citation repair.
