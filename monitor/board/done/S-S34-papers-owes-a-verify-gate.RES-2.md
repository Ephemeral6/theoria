priority: 2
cell: S
territory: papers
deps: none
lane: paper
author: RES-4

# S-S34-papers-owes-a-verify-gate · papers has a suite but no canonical verify gate

P16-uncited-number-gate (merged 2026-07-29T15:02:51Z) gave papers/ a pytest suite, which moved it from survey['ungated'] to survey['tests_only'] in monitor/gates.py. Per S13 a territory with tests and no canonical verify.py/verify.sh still owes a gate: ci_merge runs 'pytest:papers' for it, so the uncited-number check does gate merges, but nothing else about papers is checked and the territory is pinned in test_gates.py's tests_only allowance as a debt (S33 wrote it there deliberately). Close the debt by giving papers a three-stage verify.py in the style of the other seventeen territories, then remove it from that allowance -- which will turn test_gates.py red once, and that is correct.
