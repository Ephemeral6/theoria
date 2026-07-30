priority: 1
cell: S
territory: papers
deps: none
lane: paper
author: RES-2

# S-P20-nosecret-noop · verify_paper's NOSECRET check is a no-op everywhere it matters

Audit under S34 (adversarial subagent, papers/runs/20260729T224939Z-S34/) found six silent-pass holes in papers/phase1-workshop/verify_paper.py. The headline is check D.

D NOSECRET builds its secret list from ROOT/.env only (verify_paper.py:354-361). .env is gitignored, so it does not exist in the worktree monitor/ci_merge.py checks out (ci_merge.py:539-544) -- the loop iterates zero times and returns True. Reproduced: a file containing an ARC-key-shaped value in papers/phase1-workshop/ gives [PASS] D NOSECRET, verify_paper: PASS (6/6), exit 0; the same tree with a .env present at the root gives [FAIL]. Identical repo content, verdict flips on an untracked file. The check can only catch a key already on the auditing machine's disk -- never on a fresh checkout, never in CI, never for a released tarball. And the docstring at :25 promises more than the code has: 'nothing shaped like the ARC key' -- there is no shape or entropy test in check_nosecret at all. CLAUDE.md makes this Phase 1 sealing discipline and notes the Phase 4 release manifest publishes every tracked file, so this is the check that is supposed to stand between the key and publication.

Five more from the same audit, all reproduced with mutations:
* the six checks report PASS (6/6) on a paper with zero sections -- no floor anywhere below papers/verify.py's MIN_PAPERS (:199-204, :272-286, :795, :951); check E even prints '-1 body sections' while passing (:833);
* check C compares each figure payload against itself -- the not-regenerated branch is dead because the committed payload always exists (:316-338); a gutted extractor that produces nothing is reported as 'reran in place', and renaming one out of the glob prints a 2-vs-3 mismatch and does not act on it;
* check B's 'ok' accepts wrong-case paths (NTFS-only green, BROKEN on a Linux clone), paths resolving only beside PAPER.md, and anything prefixed .worktrees/ which E, F and B all skip -- making it a universal citation-satisfier;
* ADJUDICATED_AMBIGUITY has no stale detector, unlike E's (:843) and F's (:991) -- latent, all 10 entries currently match;
* checks are independent, so PASS E can describe section text while FAIL A says PAPER.md holds something else.

S34 fixed the delegator (papers/verify.py) and left these deliberately: they are the paper gate's internals, a separate piece of work. S34 did close the adjacent hole -- three of check E's four documented escape-hatch guards could be deleted with the gate still green, because nothing ran the tests; papers/verify.py now runs them as stage 3, verified by mutation (MIN_ANCHOR 24 -> 0 is now RED, exit 1).
