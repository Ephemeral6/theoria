"""heldout -- fit on part of the evidence, re-check on the part withheld.

Every "verified" cell in this rig re-checks a claim against the evidence that
produced it.  For `zero_space` that is close to a tautology: the laws *are* the
null space of the observed differences, so re-checking them on those differences
cannot fail.  This package supplies the missing half -- a split, a fit on one
side, and a re-check on the other.

The split rules, the metrics and the pass criteria were fixed in
`runs/20260729T034043Z-E17-held-out-validation/PREREGISTRATION.md` and committed
before any number here was produced.

**A miss is not a defect.**  `DECISIONS.md` D-003 makes `zero_space`'s quantifier
the *observed* difference space -- less evidence means a larger (still sound,
weaker) recovered space -- so a held-out miss measures how far a law extrapolates,
not whether the engine is correct.  `lp_potential` is sound but incomplete, so
its silence is an answer and is never scored as a miss.
"""
