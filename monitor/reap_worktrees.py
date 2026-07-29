"""Reap worktrees whose work is already on master.

    python monitor/reap_worktrees.py            # say what it would remove
    python monitor/reap_worktrees.py --apply    # remove them

Worktrees live inside the repo by convention and nothing has ever removed one.
On 2026-07-29 there were **115 registered, 71 of them finished**, the disk was
at 99% with 9.1 GB free, and the way that surfaced was a merge failing with

    a0-spike/verify.py  RED(suite): OSError: [Errno 28] No space left on device

-- a full disk wearing the costume of a broken territory.  Nobody reading that
flag would have gone looking for worktrees, which is the whole problem: the
resource ran out somewhere with no gauge, so the first symptom appeared in an
unrelated place and blamed it.

## What may be reaped, and why the bar is that high

Three conditions, all required:

  * the worktree's branch is an **ancestor of `origin/master`** -- its work is
    published, so nothing is lost;
  * `git status --porcelain` is **empty**, including untracked files;
  * it is not the main checkout.

Untracked files count.  A session that has written a file and not yet committed
it looks identical to a finished worktree under a tracked-only check, and 31 of
the 115 here were dirty -- work in flight belonging to sessions that are still
running.  Deleting one would destroy a colleague's uncommitted work to reclaim
130 MB, which is the worst trade in this repository.

## Why dry-run is the default

The obvious failure of a reaper is that it runs too eagerly once and everyone
switches it off.  Printing first costs a second and makes the decision
reviewable, so `--apply` is an explicit act.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def sh(*args, cwd=None):
    """UTF-8, never the host locale: this box is cp936 and a branch name or a
    path with a non-ASCII character would otherwise raise inside the check."""
    return subprocess.run(list(args), cwd=cwd or ROOT, capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


def worktrees(root=ROOT):
    """Every registered worktree as {path, branch}, main checkout included."""
    out = sh("git", "worktree", "list", "--porcelain", cwd=root).stdout
    entries, cur = [], {}
    for line in out.splitlines():
        if line.startswith("worktree "):
            if cur:
                entries.append(cur)
            cur = {"path": line[len("worktree "):], "branch": None}
        elif line.startswith("branch "):
            cur["branch"] = line[len("branch "):].replace("refs/heads/", "")
        elif line.startswith("detached"):
            cur["branch"] = None
    if cur:
        entries.append(cur)
    return entries


def classify(root=None, upstream="origin/master", min_idle=60):
    """Each worktree with a verdict and the reason for it.

    `root` is resolved here rather than bound as a default, because a default
    evaluated at import time cannot be redirected afterwards -- the same shape
    that makes `proxy.scoring.score_run`'s `scores_dir` immovable from outside.
    Here it would have meant every check silently answering about the real
    checkout instead of the one asked about.
    """
    root = root or ROOT
    rows = []
    main = os.path.normpath(root)
    for e in worktrees(root):
        path, branch = e["path"], e["branch"]
        row = {"path": path, "branch": branch, "verdict": None, "why": ""}
        if os.path.normpath(path) == main:
            row.update(verdict="keep", why="the main checkout")
        elif not os.path.isdir(path):
            row.update(verdict="stale", why="registered but not on disk")
        elif branch is None:
            row.update(verdict="keep", why="detached HEAD -- no branch to "
                                           "check against master")
        else:
            status = sh("git", "status", "--porcelain",
                        "--untracked-files=all", cwd=path)
            if status.returncode != 0:
                # A worktree git cannot read is not a worktree this may delete.
                # "Could not check" must never resolve to "safe to remove".
                row.update(verdict="keep",
                           why="git status failed here: %s"
                               % (status.stderr or "").strip()[:120])
            elif status.stdout.strip():
                n = len(status.stdout.strip().splitlines())
                row.update(verdict="keep",
                           why="%d uncommitted change(s) -- work in flight" % n)
            else:
                # `cwd=root`, not the module default.  Without it the ancestry
                # question is asked of whichever checkout this file happens to
                # live in, which answers confidently about a different
                # repository -- and the confident wrong answer here is
                # "not merged", so it fails closed rather than deleting. That
                # is luck, not design, so the cwd is explicit.
                merged = sh("git", "merge-base", "--is-ancestor",
                            branch, upstream, cwd=root)
                if merged.returncode == 0:
                    idle = idle_minutes(path)
                    if idle is None:
                        row.update(verdict="keep",
                                   why="could not read any mtime here; "
                                       "refusing to guess it is abandoned")
                    elif idle < min_idle:
                        row.update(verdict="keep",
                                   why="touched %.0f min ago (< %d) -- clean "
                                       "and merged, but somebody may still be "
                                       "in it" % (idle, min_idle))
                    else:
                        row.update(verdict="reap",
                                   why="clean, %s is on %s, idle %.0f min"
                                       % (branch, upstream, idle))
                else:
                    row.update(verdict="keep",
                               why="%s is not yet on %s" % (branch, upstream))
        rows.append(row)
    return rows


def idle_minutes(path, cap=4000):
    """Minutes since anything under `path` was last touched.

    "Clean and merged" is not the same as "abandoned".  A session that has just
    committed and is about to write its next file looks exactly like a finished
    one, and deleting its worktree out from under it would be this tool causing
    precisely the class of failure it was written to fix.  Recency is the
    cheapest available proxy for "someone is still here".

    Walks at most a few thousand entries: a worktree is ~2000 files and the
    answer only needs to be roughly right.
    """
    newest, seen = 0.0, 0
    for dirpath, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__")]
        for name in files:
            try:
                newest = max(newest, os.path.getmtime(os.path.join(dirpath, name)))
            except OSError:
                continue
            seen += 1
            if seen >= cap:
                break
        if seen >= cap:
            break
    if not newest:
        return None                      # nothing readable; caller fails closed
    import time
    return (time.time() - newest) / 60.0


def disk_free_gb(path=ROOT):
    total, used, free = shutil.disk_usage(path)
    return free / (1024 ** 3), total / (1024 ** 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="actually remove them; without this it only reports")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--upstream", default="origin/master")
    ap.add_argument("--min-idle", type=int, default=60, dest="min_idle",
                    help="minutes a clean, merged worktree must have been "
                         "untouched before it counts as abandoned")
    args = ap.parse_args()

    rows = classify(root=ROOT, upstream=args.upstream,
                    min_idle=args.min_idle)
    reap = [r for r in rows if r["verdict"] == "reap"]
    keep = [r for r in rows if r["verdict"] == "keep"]
    stale = [r for r in rows if r["verdict"] == "stale"]

    free, total = disk_free_gb()
    if args.json:
        print(json.dumps({"free_gb": round(free, 1), "total_gb": round(total, 1),
                          "reap": len(reap), "keep": len(keep),
                          "stale": len(stale), "rows": rows},
                         indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print("disk: %.1f GB free of %.0f GB (%.0f%% used)"
              % (free, total, 100 * (1 - free / total)))
        print("%d worktree(s): %d finished, %d kept, %d registered-but-gone"
              % (len(rows), len(reap), len(keep), len(stale)))
        for r in reap[:60]:
            print("  reap  %-40s %s" % (os.path.basename(r["path"]), r["why"]))
        for r in stale:
            print("  stale %-40s %s" % (os.path.basename(r["path"]), r["why"]))

    if not args.apply:
        # Prose only outside --json.  A --json mode that also prints a sentence
        # produces output no parser accepts, which is a small lie of the same
        # family as the rest of this file's subject.
        if (reap or stale) and not args.json:
            print("\ndry run. re-run with --apply to remove %d worktree(s)."
                  % (len(reap) + len(stale)))
        return 0

    removed = 0
    for r in reap + stale:
        out = sh("git", "worktree", "remove", "--force", r["path"])
        if out.returncode != 0:
            print("  FAILED %s: %s" % (r["path"], (out.stderr or "").strip()[:160]))
            continue
        removed += 1
    sh("git", "worktree", "prune")
    after, _ = disk_free_gb()
    print("removed %d worktree(s); disk %.1f -> %.1f GB free"
          % (removed, free, after))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
