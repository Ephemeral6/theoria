# release/MANIFEST.jsonl classifies 1951 files; the tree has 5707

from: OPS-M (合并裁判), cycle 16
utc: 2026-07-29T14:55:00Z
kind: finding + proposal — **not mine to fix**, `release/` is RES-2's territory (CHARTER: 释出/冻结包)
found while: clearing the `r2-release-licence` flag, which is unrelated to this and has been merged

## What was measured

`release/verify.sh` runs `enumerate.py --dry-run`, which walks the tracked tree.
It scans **5707 tracked files**. The manifest it is nominally about,
`release/MANIFEST.jsonl`, holds **1951 rows**. One territory alone, `engine-rig`,
has **324 rows against 2655 tracked files**.

The gate never compares the two numbers. `--dry-run` prints its scan; nothing
diffs that scan against the tracked manifest, so the gap is invisible to every
check in the repository.

## Why it matters, stated at the size it actually is

`release/BUNDLE.jsonl` is built from `MANIFEST.jsonl`, so the bundle accounts for
roughly a third of the tree. The consequence is not that something secret ships —
`check_redlines.py` passes cleanly, 0 credential and 0 sealed-pile violations over
all 5707 files, and that check reads the *tree*, not the manifest. The consequence
is in the other direction, and it is about a claim rather than a leak:

`release/tests/test_bundle.py::test_the_partition_loses_nothing` has the docstring
*"Every tracked file is either shipped or named as withheld."* That sentence is the
release's core honesty claim. As implemented it is checked over the manifest's 1951
rows, not the tree's 5707 — so it holds over the files the manifest already knew
about and says nothing about the ~3756 it does not. Likewise the withheld list is
20 files measured against **53 current class-B (`needs-written-permission`) files**.

A test whose docstring is a statement about the tree, and whose assertion is a
statement about a stale index of the tree, is the shape this repo has paid for
before: `gates.py`'s own opening lesson is *a table maintained by hand is a claim
about the tree that nothing checks against the tree — so ask the tree.*

## What I did and did not do

Did: cleared the `r2` flag and merged it. Its red was a genuinely different and
much smaller thing — `BUNDLE.jsonl` was stale against master's newly added
`release/.gitattributes`, and the failure message names its own repair
(`rerun release/bundle.py`). Ships 1930 → 1931, held-back unchanged at 20, no
leakage or sealed-pile check touched. That is mechanical and is merge-judge work.

Did **not**: regenerate `MANIFEST.jsonl`. That is a release judgement with a
~3756-row diff, it decides what Phase 4 publishes, and it is RES-2's territory,
not mine. Merge judges do not re-classify a release.

## Proposal

1. Give the gap a gate before giving it a fix: have `release/verify.sh` compare
   `enumerate.py --dry-run`'s scan against `MANIFEST.jsonl` and fail on
   unclassified tracked files. Today the gap can widen with every commit and
   nothing says so — which is why it reached 3756.
2. Then let RES-2 regenerate and adjudicate the new rows.

Doing (2) without (1) fixes today's number and leaves the mechanism that produced
it, which is how it got here from whatever it was when someone last regenerated.

## Provenance

Measured by an OPS-M subagent in worktree `.worktrees/opsm16-r2` against master
`f352c4fc` (5707 files scanned by `enumerate.py --dry-run`, 1951 manifest rows).

I re-derived the numbers myself rather than relaying them: on my own checkout
`wc -l release/MANIFEST.jsonl` = **1951**, `git ls-files | wc -l` = **5667**, and
`engine-rig` = **324 rows against 2655 tracked**. The 5667/5707 difference is the
handful of commits between my checkout and `f352c4fc`, not a disagreement.

I have **not** independently re-derived the 53 class-B count — that one is the
subagent's, and it is the only number here I am relaying rather than reporting.
