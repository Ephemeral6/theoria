# S41 — run state

item: `S41-S41-prior-work-scans-one-of-two`
branch: `agent/s41-prior-work-scans-one-of-two`
base: `7972a075` (origin/master)
worktree: `.worktrees/s41-prior-work`
researcher: RES-4

## What was wrong

`monitor/board.py:prior_work` warned "somebody may already be doing this work"
by listing one directory: `os.listdir(repo/'.worktrees')`. This machine keeps
worktrees in more than one place, and the one it did not look in is the one
where the incident happened — S36 recorded three PAID shards in
`.claude/worktrees/p11-arc-hygiene` evading two separate checks at once, both
of which globbed only `.worktrees/`.

The failure direction is the reassuring one. Nothing raises, the claim
succeeds, the item is renamed into `claimed/`, and two sessions start the same
paid run. The only signal that would have stopped it is the one that was blind.

## What changed

`monitor/board.py`, one function and three new helpers above it:

* `WORKTREE_ROOTS` — the two on-disk roots. Note what this is *not*: it is not
  the enumerator. It is used only by the orphan sweep.
* `_registered_worktrees(repo)` — pass 1. Parses
  `git worktree list --porcelain`, drops record 0 (git always emits the main
  checkout first), and drops the tree we are standing in. Root-agnostic, so it
  also covers `ci_merge`'s `%TEMP%` trees, which neither root constant names.
  Parsing follows `reap_worktrees.py:worktrees()`.
* `_orphan_worktrees(repo, registered)` — pass 2. Sweeps both roots for
  directories git has no registration for. Six exist here; `git worktree list`
  and `reap_worktrees.py` are both blind to them, so pass 1 alone would have
  been a new blind spot in place of the old one. Filters `os.path.isdir`,
  because `.worktrees/` also holds 12 loose files.
* `_worktree_label(repo, path)` — renders `.worktrees/x`,
  `.claude/worktrees/x`, or an absolute path for anything outside the repo.
  Handles the Windows cases: git prints forward slashes, `os.path.join`
  produces backslashes, and `os.path.relpath` raises `ValueError` across
  drives.

`prior_work` now runs both passes and says which one produced each hit and
which root it is in. The old text hard-coded `工作树 .worktrees/%s`, which was
not merely cosmetic — a hit in the harness root would have been *reported as*
living in `.worktrees/`, sending the reader to look where it is not.

The branch half of `prior_work` is untouched, including the "0 commits ahead
means already merged, which is different news" distinction. A test pins it.

## Encoding

Every line the function can emit is ASCII and Chinese only. This console is
cp936; a glyph outside it raises `UnicodeEncodeError` *after* `cmd_claim` has
renamed the item into `claimed/`, so the board records a successful claim while
the agent sees a traceback and no work. `test_every_line_survives_this_host_s_console_encoding`
re-runs `.encode("cp936")` over all four new line shapes rather than trusting
the inherited control, because the new lines are longer and there are more of
them.

## What was verified

* Replay of the S36 case on the LIVE tree: old code returns `[]` for
  `p11-arc-hygiene`, new code returns `.claude/worktrees/p11-arc-hygiene`.
  This is the whole item, measured rather than argued.
* Live census of both roots plus `%TEMP%` — numbers in `FINDINGS.md` §1-3.
* 19 new tests, both directions. The positive control is a WIP existing ONLY
  under `.claude/worktrees/`; the negative controls are a brand-new item name
  against a populated pair of roots, a loose file in each root, and the main
  checkout itself when its directory name contains the slug.
* Full suite before and after: 5 failed / 390 passed / 2 xfailed -> 5 failed /
  409 passed / 2 xfailed. Same five pre-existing failures, no new ones.

Tests do not read this machine's real worktrees. `prior_work` already took a
`repo` argument and every git call goes through `board._git`, so a `tmp_path`
directory plus a stubbed `_git` is a complete world — no refactor for
testability was needed. A test that read the live roots would change its own
verdict every time somebody reaped a worktree.

## What was NOT done, on purpose

* **No other call site was touched.** The brief's requirement 4 (survey the
  8 asymmetric skip sets repo-wide, decide on a shared helper) was superseded
  mid-run by RES-4: the 8-figure does not reproduce, and the shared-helper
  answer is **no**. Recorded in `FINDINGS.md` §6.
* **`scan.py:48 SKIP_DIRS` is left alone** though it names neither worktree
  root, so two `os.walk(ROOT)` scans descend into all 252 worktrees. It is a
  different decision from a half-done exclusion and changing it would change
  what the ARC key-leak scan covers. Recorded in `FINDINGS.md` §7 so it is not
  rediscovered from scratch.
* **The six orphaned checkouts were not reaped.** S41 makes them visible; it
  does not adjudicate them. `reap_worktrees.py` still cannot see them.
* No push, no merge, no board mutation — RES-4 does those.
* `monitor/master_tree_guard.py` was not consulted as a reference. RES-4
  corrected the brief mid-run: it does not exist on origin/master (it is S39's,
  unmerged). `reap_worktrees.py:57-72` and `proxy/spend_gate.py:71-92` were
  used instead. `proxy/` was read only, never written.

## The lint

RES-4 asked for a never-again mechanism scoped to `monitor/`, in place of the
rejected shared helper. It is in the same test file: an `ast` pass over every
top-level `monitor/*.py` that fails when a skip set names one worktree root and
not the other. It passes today; the two adjudications required to make it
honest — one false positive narrowed, one real-but-out-of-scope site
deliberately not flagged — are in `FINDINGS.md` §7. It carries its own control
that proves it can fail.
