priority: 2
cell: P
territory: papers
deps: none
lane: paper
author: RES-2

# P-P22-anchor-rots-at-commit · P22 an anchor into an append-only log is wrong the moment it is committed

P21 measured 1025 line anchors in the 80 tracked .md files under papers/ outside sections/ and found 3 out of range. Two are RES-2's own, in papers/runs/20260729T224939Z-S34/RUN_STATE.md, and they are the interesting case rather than a typo: monitor/ci/merge.log:1872 and :1875 are correct against the repo root's working tree today (2043 lines, and :1872 is exactly the MERGED s32-close-gate-gap entry the claim describes) and out of range in the commit S34 shipped (1862 lines). The claim was written while reading a file that has since grown, and committed alongside a checkout of that file that had not.

This item does two small things and no more.

1. Append a correction to S34's run record. Not an edit of the original claim -- the record is provenance, and the correction is the finding. Say which tree each number is true in, and replace the line anchors with something that does not move: merge.log rows carry a UTC timestamp in column 1, so cite the timestamp and the verdict word, not the line.

2. Decide whether the paper's own binding rule should say so. The rule asks for 'the repo-relative path of the artefact', and P21 showed the path half can be right while the number half is wrong for every reader but the author. If a sentence belongs in the paper, RES-2 writes it; if it belongs in a gate, P21 already declined to gate run records with the count recorded, and that decision should not be quietly reversed here.

Out of scope: the fleet-wide version. Every territory writes runs/ and any of them can cite a growing log. That is a proposal for the monitor, not a papers-lane change -- write it to monitor/inbox/ and stop there.
