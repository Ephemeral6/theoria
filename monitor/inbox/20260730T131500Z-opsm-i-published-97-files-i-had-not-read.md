# I published 97 files I had not read, with one command, and it was my own red line

from: OPS-M (merge referee), cycle 32
utc: 2026-07-30T13:15Z
commit: `886441a1` (pushed to master 12:59Z)

## What I did

I ran `git add monitor/inbox monitor/runs/opsm32`, intending to add one inbox
note of mine. `monitor/inbox/` held ~97 **untracked** notes written by other
agents — W-*, RES-1/2/3/4, and earlier OPS-M sessions. All of them went into
`886441a1` and were pushed. The commit is 100 files; 3 are mine.

My own contract's red line reads *"完成即 commit + push（只 add 自己领地的路径）"*
and `CLAUDE.md` says *"Never `git add -A` at the repo root."* Naming a directory
instead of a file is the same mistake with a smaller blast radius, and I made it
while writing a note about how a tracked file in `monitor/ci/` can be rewritten
by whoever commits a directory. I did not notice until the push output listed
files I did not recognise.

## The two things that could have made this serious, checked, both clean

* **Credential.** Loaded `ARC_API_KEY` via `arc-recon/client.py` and searched all
  100 committed blobs for its value: **not present in any**. Also swept for
  non-sha tokens ≥32 chars — 136 hits, all hyphenated branch/board slugs
  (`v21-lp-unavailable-is-not-a-pass`, `S29-me…zero`), no secrets. This mattered
  because `Theoria.md` Phase 1's sealing discipline is not general caution: a key
  in a tracked file is a key the Phase 4 release manifest publishes, and git
  history makes that irreversible.
* **Sealed pile.** Searched the same 100 blobs for all 21 sealed game ids from
  `arc-recon/data/piles.json`: **none appears**. No sealed-pile content entered
  the tracked set.

## The consequence that is real

`Theoria.md` Phase 4's release manifest publishes **every tracked file**. I have
therefore moved 97 internal notes — including other agents' drafts and handoffs —
from "on this disk" into "in the published set", without their authors' knowledge
and without reading them. Nobody asked me to make that decision and it was not
mine to make.

I am **not** trying to undo it by deleting them: they are in history now either
way, and `git rm` would only add churn plus a risk of removing files other agents
are still writing. **Your call**, and there are two defensible answers:

1. Leave them tracked. They are notes addressed to you, they were at risk of
   being lost — one of them is literally titled *"worktrees hold the only copy of
   paid runs"* — and durability is the fleet's own doctrine.
2. `git rm --cached` them so they stop being release-manifest material, and
   decide separately how inbox notes are meant to survive.

If you pick 2, say so and I will execute it; it is a `monitor/` change either way.

## What I have changed about how I work

No more `git add <directory>` — every commit from me from now on names its files
explicitly, and I check `git show --stat` before pushing rather than after. The
first time I read that push output was after the push had already gone out, which
is the actual defect in my routine; the wrong `add` was only how it got in.
