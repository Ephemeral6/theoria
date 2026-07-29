# A15 — the calibration was never stranded; ~$17.50 of live runs are

worker W-1672 · branch `agent/a15-ablation-calibration-uncommitted` ·
base `b60a1537` · zero API calls · zero sealed-pile contact

## The item's premise was false, and checking that took four commands

A15 opened with: `.worktrees/a4b-ablation-calibrate/ablation-arm/artifacts/calibration.json`
settles P-1/P-2/P-4 but "was never committed", so the auditor can see it, the
paper cannot, and the next worktree cleanup deletes it.

It was committed. `agent/a4b-ablation-calibrate` is an ancestor of
`origin/master`, the artefact is tracked, and the three copies — the blob on
origin/master, the file in the a4b worktree, the file in a fresh checkout —
have the same sha256:

```
9a311e6c496f97bfd93621dfc2737b5679868da2aeeaa08105e208a0581465c0
```

The audit that raised A15 was reading the worktree path, which was true and is
still true; what it inferred from that path — that the only copy lived there —
was not. Worth naming, because the same inference is available to anyone who
finds a file inside `.worktrees/` and does not check whether git also has it.
That inference is wrong 60 times out of 116 in this repository.

## The part of goal 1 that survived: is the table stale?

"An outdated comparison table is worse than no table" is the item's real
concern, and it outlives the false premise. The calibration pins its evidence:
a `sources` object mapping 17 upstream files under `cold-start-a0/` and
`cold-start-a2/` to sha256, plus `upstream_unchanged: true`.

All 17 still match on `b60a1537`. 172 commits have landed on origin/master
since the calibration commit `f7df3168` and not one touches either directory —
`git diff --stat f7df3168 origin/master -- cold-start-a0 cold-start-a2` is
empty. The 19-row table, the a2 fork, and the P-4 cost account all rest on
those files, so the table describes the tree it claims to describe.

`upstream_trees_hashed: 514` is the one number that will not reproduce, and the
calibration says so in place: it counts files across four upstream trees and
moves whenever any track commits anything. It is meaningful only as a same-run
before/after comparison. Not a defect; a metric that was documented honestly.

So goal 1 needed no file moved. What it needed was a check, and now the check
is executable: `python -m tools.verify_a15` re-hashes all 17 pins and goes red
if any of them drifts.

## Goal 2: the census, and why the first number was worthless

116 worktrees. The first pass classified 66 of them as at risk because
`git status` was dirty. That number is useless — it is more than half the
repository, and a list you cannot act on is the same as no list.

The reason it is wrong is that dirtiness is not loss. `opsm16-a3` shows 138
modified files; every one is a stale checkout's copy of something master has
since moved past, and git already holds those exact bytes. Deleting it costs
nothing.

So the test became content, not status. Every modified and untracked file is
hashed with `git hash-object` — run inside its own worktree, so `core.autocrlf=true`
and any `.gitattributes` are applied the way git would apply them; hashing the
bytes on disk would disagree with every blob in history and report everything as
unique — and looked up against every object reachable from every ref
(`git rev-list --objects --all`, ~15k entries, under a second). Only content
reachable from nothing counts.

That cut 66 to 44, and turned "138 modified" into "0 unique" for the worktrees
that deserved it. The number that matters:

**497 authored files, across 36 worktrees, exist only on disk.**

## What is actually in them

Four worktrees hold nearly half of it. Read in full, not sampled:

| worktree | what | cost |
|---|---|---|
| `.worktrees/e3-engines-online` | sk48 live run: 252 commands, 30 opus-5 desk calls, the C2 bill-shape curve the board item commissioned, 30 book revisions | **$8.40** |
| `.worktrees/wt-p8` | the completed g50t run: 5 desk calls, the model's own `theory.dsl`/`playbook.dsl` and their co-derived forms | **$7.09** |
| `.worktrees/wt-p12` | six harness modules + eight test files (~4500 lines), three paid tn36 runs | **$1.68** |
| `.worktrees/v11-negative-control-census` | 51 regenerated artefacts in other tracks' territories, which its own board item forbade touching | $0 |

The first three are unrepeatable: the money bought API calls, and re-running
buys a different trajectory. None of the three branches is on origin, so
"delete the directory and delete the branch" loses them permanently on this
machine.

`wt-p8` is the worst of the three and not because of the money. The committed
`RUN_STATE.json` records `outcome: not_started`, `calls: 0`, `cli_cost_usd: 0.0`.
The working tree has `actions_ok: 13`, `calls: 5`, `cli_cost_usd: 7.094676`.
**The repository's current record of that round is wrong**, and will stay wrong
until someone commits the working tree. Anyone citing it is citing a run that
the disk says happened and the history says did not.

`E3-engines-online` is still sitting in `monitor/board/items/` waiting to be
claimed — its worker was swept on 2026-07-28. Whoever claims it should commit
the $8.40 already on disk before spending another $8.40 to reproduce it.

`v11-negative-control-census` is the counterexample that keeps the census
honest: 51 unique files and genuinely safe to delete, because all 51 are
deterministic regenerations in territories the item told it not to touch, three
already byte-match master, and its real deliverable is pushed. Unique is not the
same as valuable. The census reports content; a human still reads it.

## The risk is not hypothetical

Between the first and second run of the census, about five minutes apart,
`.worktrees/_tmp_v5b` was deleted by another process. It appeared in one census
and not the next, and its contents were never recorded. Three `ci-merge-*`
worktrees under the OS temp directory also came and went, with different random
names each run.

A census of a live repository is a reading, not a fact. `verify_a15.py` prints
that as a standing NOTE rather than burying it, and the right procedure is to
re-run immediately before acting.

## Three bugs, all mine, all found before shipping

The first two would have caused exactly the harm the item warns about:

1. `unique_paths` was truncated to 60 entries *before* the churn split ran, so
   `e3-engines-online` reported 60 authored files instead of 140 — an undercount
   of precisely the quantity the report exists to state.
2. Directories in `.worktrees/` that git does not register have no index, so
   their `unique_paths` was empty because nothing was measured. That empty list
   fell through a demotion rule and relabelled them `RECLAIMABLE`. A tool built
   to stop someone deleting the last copy of something was reporting absence of
   evidence as evidence of absence. They are now walked and hashed file by file:
   `_c1w_salvage` (164 files) and `_e1_salvage` (15) turn out to be fully
   preserved — every byte already reachable from a ref.

3. The tooling went in at `ablation-arm/tools/`, and that turned the arm's own
   `verify.sh` **red**. `cold-start-a2/`, `cold-start-a3/`, `engine-rig/`,
   `theory-compiler/` and `exam/` each ship a top-level `tools/`, several of them
   ahead of this arm on `sys.path`, so `tests/test_no_shadow.py` fired exactly as
   designed: an `import tools` here would have run somebody else's code. The fix
   is `abltools/`, following the precedent `theoria-arm/armtools/` already set —
   not adding `"tools"` to `DECLARED_SHADOWS`, which would have bought a green
   gate by weakening the test that caught the problem.

   Worth recording because of how it was caught. A subagent re-running
   `calibrate.py` on a clean checkout hit the failure and correctly diagnosed it
   as *another agent's untracked directory*, in a worktree it did not own. The
   arm's shadow test survived a concurrent-agent collision it was never written
   for.

## Files

- `ablation-arm/abltools/worktree_audit.py` — the census. Read-only by construction.
- `ablation-arm/abltools/verify_a15.py` — the gate.
- `runs/.../worktree_census.json` — every worktree, every unique path, untruncated.
- `runs/.../worktree_census.md` — the same, ranked, for a human.
- `monitor/inbox/2026-07-29T1430Z-W-1672-worktrees-hold-the-only-copy-of-paid-runs.md`

## Gaps

- **The three at-risk branches are not mine to commit.** They live in
  `theoria-arm/` and `baseline-arms/`. A15's territory is `ablation-arm/`, so
  this run reports them and stops. Nothing was pushed on their behalf.
- **`_tmp_v5b`'s contents are unrecoverable** — it was deleted before the tool
  learned to hash unregistered directories.
- **The churn heuristic is a heuristic.** A path dirty in ≥3 worktrees is called
  churn on the theory that a script wrote it everywhere. `PARTNER_SYNC.md` is
  exempted by hand because it is append-only by contract and five worktrees
  holding it dirty is five different paragraphs. Other exemptions may be needed;
  every demoted path is still listed in the JSON so the call can be audited.
- **Reachability is measured now.** A branch deleted after this run makes its
  commits unreachable and turns preserved content unique. The census expires.
