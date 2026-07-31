"""A9 -- permutation null on the REAL papers.

If the widened `derive_label_sets` has made the gate trigger-happy, the way to
see it is to destroy the relationship and ask how often it still fires.  Shuffle
each derived label set's answers among its own items (so the label distribution
is preserved exactly and only the pairing is destroyed) and count how often
`metadata_hits` reports anything.

Under a correct gate this should be near zero.  Anything above a couple of
percent is the check crying wolf at the paper shapes actually shipped.
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from exam import leakage
from exam.grading.registry import digest
from exam.papers import BUILDERS, module_for

TRIALS = 2000


def build(qt):
    if qt == "<handover_auto>":
        from exam.papers import handover_auto
        return handover_auto.build()
    return module_for(qt).build()


rng = random.Random(20260729)
print("%-22s %-20s %5s  %-6s  %s"
      % ("paper", "label field", "n", "real", "P(fires | shuffled labels)"))
for qt in sorted(BUILDERS) + ["<handover_auto>"]:
    paper = build(qt)
    sets = leakage.derive_label_sets(paper, paper.key(digest()))
    for field, labels in sorted(sets.items()):
        real = len(leakage.metadata_hits(paper, labels))
        ids = list(labels)
        vals = [labels[i] for i in ids]
        fired = tokfired = 0
        for _ in range(TRIALS):
            rng.shuffle(vals)
            shuffled = dict(zip(ids, vals))
            hits = leakage.metadata_hits(paper, shuffled)
            if hits:
                fired += 1
            if any("token" in h for h in hits):
                tokfired += 1
        print("%-22s %-20s %5d  %-6d  %.3f   (token-level only %.3f)"
              % (paper.paper_id, field, len(labels), real, fired / TRIALS,
                 tokfired / TRIALS))
