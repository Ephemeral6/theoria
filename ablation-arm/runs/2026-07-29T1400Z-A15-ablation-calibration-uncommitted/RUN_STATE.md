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
That inference is wrong 57 times out of 114 in this repository.

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
is executable: `python -m abltools.verify_a15` re-hashes all 17 pins, and separately pins the
five `ablation-arm/` files the table cites that the artefact's own `sources`
object does not cover.

## Goal 2: the census, and why the first number was worthless

114 worktrees. The first pass classified 66 of them as at risk because
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

That cut 66 to 45, and turned "138 modified" into "0 unique" for the worktrees
that deserved it. The number that matters:

**622 authored files, across 37 worktrees, exist only on disk.**

Every count in this document is a reading taken at one census, not a constant.
Successive runs minutes apart returned 117, 116, 115 and 114 worktrees and
between 601 and 629 authored-only files, because branches merge, `ci-merge-*`
worktrees rotate through the OS temp directory, and at least one directory was
deleted mid-run. `worktree_census.json` carries the `upstream_head` its numbers
belong to and is the authority; the gate prints how many commits behind that head
now is. Quote the JSON, not this paragraph.

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
honest: 51 content-unique files and genuinely safe to delete, because all 51 are
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

## Seven bugs, all mine, all found before shipping

Every one of them failed in the same direction — toward saying "safe to
delete" — which is the direction that costs something. Three were caught by a
subagent tasked with refuting this work rather than checking it.

1. `unique_paths` was truncated to 60 entries *before* the churn split ran, so
   `e3-engines-online` reported 60 authored files instead of 140 — an undercount
   of precisely the quantity the report exists to state.
2. Directories in `.worktrees/` that git does not register have no index, so
   their `unique_paths` was empty because nothing was measured. That empty list
   fell through a demotion rule and relabelled them `RECLAIMABLE`. A tool built
   to stop someone deleting the last copy of something was reporting absence of
   evidence as evidence of absence.
3. **The one that nearly shipped.** `git hash-object --stdin-paths` resolves a
   relative path against the repository *top-level*, not the process cwd. For a
   registered worktree those are the same directory, so the bug is invisible;
   for `.worktrees/_c1w_salvage` — inside the repo but not a worktree of it —
   every relative path silently addressed the **main checkout's** file instead.
   The census dutifully hashed 164 files it had not been asked about, found all
   of them in history, and reported a directory of unreviewed pre-commit work as
   holding nothing unique. The fix is absolute paths; the truth is 128 of those
   164 files exist in no commit on any ref.

   It was caught by a triage subagent whose byte-level count (128) contradicted
   my census (0). Two independent methods disagreeing is the only reason it was
   found — a self-check I had written specifically to catch this class of error
   passed, because the per-path fallback it exercised resolves correctly. The
   guard that actually works compares the batch result against the single-path
   form on a *spread* of paths: the first path in `_c1w_salvage` happens to be
   identical in both locations, so a one-sample check sat there agreeing with a
   batch that had mis-addressed all 164 entries.
4. `monitor/bus/*/out.jsonl` sat at frequency exactly 3 — the ubiquity threshold
   — and was demoted to churn, printing three worktrees under "every one of
   these is safe to remove" while each held one unpublished agent bus message
   present in no commit on any ref. This is the identical situation the
   `PARTNER_SYNC.md` exemption exists to prevent; I had written the exemption and
   then failed to see that the bus is the same shape. Now in `NEVER_CHURN`.
5. `git status` C-quotes any path containing a non-ASCII byte, and the parser
   only stripped the surrounding quotes. Every such file was reported as "git
   could not hash this" — a limitation git does not have — which silently
   exempted every non-ASCII filename from the uniqueness test, in a repository
   where agents write Chinese throughout. Fixed by reading the NUL-delimited
   `-z` form; the census now has zero unhashable paths.
6. `commits_ahead` is `None` when `rev-list --count` cannot run. `None` is falsy,
   so an unmerged worktree on no remote fell through the demotion guard and was
   relabelled "merged into origin/master; nothing on disk that git does not
   already have" — a sentence that was false in both halves.
7. Blob membership proves the *bytes* survive, not the *file*.
   `e11-engine-crosscheck-deep` holds four SURVEY documents whose content exists
   on a ref only because a paper copied them verbatim into its own inputs
   directory; the run directory that CLAUDE.md's provenance rule requires exists
   on no ref at all. The census said "safe to remove". There is now a distinct
   `preserved_elsewhere` class — 16 worktrees are in it — and it does not print
   as safe.

8. The tooling went in at `ablation-arm/tools/`, and that turned the arm's own
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

- **The at-risk branches are not mine to commit.** They live in `theoria-arm/`,
  `baseline-arms/` and the harness's own `.claude/worktrees/`. A15's territory is
  `ablation-arm/`, so this run reports them and stops. Nothing was pushed on
  their behalf. Four now need someone with the right territory:
  `agent/e3-engines-online`, `agent/p8-theoria-arm`, `agent/p12-envelope-finish`,
  and `.claude/worktrees/p11-arc-hygiene/baseline-arms/out/shards/` — that last
  one is 628 KB of paid ARC transport-A/B evidence on a branch that reads as
  fully merged, in a directory a `.worktrees/`-scoped sweep would not even open.
- **`_tmp_v5b`'s contents are unrecoverable** — it was deleted before the tool
  learned to hash unregistered directories.
- **The calibration's own pin covers only half of what it cites.** All 17
  `sources` entries are upstream (`cold-start-a0/`, `cold-start-a2/`); not one is
  an `ablation-arm/` path, yet every row of the 19-row table reads its left-hand
  value out of this arm's artefacts — the half under active development.
  `verify_a15.py` now pins those five cited files independently, by comparing
  committed blobs against the calibration commit, but the artefact itself is
  still unguarded there. Fixing it properly means adding them to `SOURCES` in
  `calibrate.py` and re-running, which is A4b's scope, not A15's.
- **`upstream_unchanged` cannot detect drift.** It records that `calibrate.py`
  hashed 514 files and found none changed *within a single run* — it stores a
  count and a boolean, no digest, so nothing can re-derive it. It is a frozen
  assertion about 2026-07-28. The only cross-run drift detector in the artefact
  is `sources`, and the gate asserting `upstream_unchanged is True` can fail only
  from someone editing the file, not from the world moving.
- **The churn heuristic is a heuristic.** A path dirty in ≥3 worktrees is called
  churn on the theory that a script wrote it everywhere. Two exemptions are
  hand-written (`PARTNER_SYNC.md`, `/out.jsonl`) because they are append-only
  streams, where N dirty worktrees means N different appends. The second was
  added only after an adversarial review found three worktrees printed as safe
  while holding unpublished bus messages — so the list is demonstrably
  incomplete, not demonstrably complete. Every demoted path stays in the JSON so
  the call can be audited.
- **Four of the gate's census assertions cannot fail** — `read_only`,
  `deleted_anything`, and the two summing checks re-derive values the writing
  tool guarantees. They are tripwires against the artefact being hand-edited, not
  against the census being wrong, and should be read as nothing more.
- **Reachability is measured now.** A branch deleted after this run makes its
  commits unreachable and turns preserved content unique. The census expires; the
  gate prints how many commits stale it is rather than failing, because
  origin/master moves every few minutes here and a permanently red gate is one
  nobody reads.
