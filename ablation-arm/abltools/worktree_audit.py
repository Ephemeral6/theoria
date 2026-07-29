#!/usr/bin/env python
"""Read-only census of every worktree in this repo: what would be lost if it were deleted.

Written for board item A15. The item's premise was that a finished calibration
existed only inside `.worktrees/a4b-ablation-calibrate/` and had never been
committed. That turned out to be false -- the branch merged and the artefact is
tracked on master -- but the *class* of risk is real: this repo carries 113
worktrees, and `git worktree remove` is irreversible. Somebody has to be able to
answer "which of these still hold the only copy of something" without opening
113 directories by hand.

So this is deliberately not a cleanup tool. It never deletes, never checks out,
never fetches, never writes anywhere except the two report files it is told to
write. Its whole output is a ranked list the monitor can act on.

    python -m abltools.worktree_audit --json out.json --md out.md

The ranking that matters is `disposition`:

    AT-RISK      deleting this loses work that exists nowhere else
    RECOVERABLE  unmerged, but every commit is on origin -- the branch survives
    RECLAIMABLE  merged into origin/master and clean -- deleting loses nothing

`AT-RISK` is the only class a human needs to read. The other two are counted so
the census is complete, because "the list was short" is a different claim from
"the list was short because I only looked at ten of them".

The whole difficulty is in what counts as AT-RISK, and `git status` alone gets
it badly wrong. A first pass of this census called 66 of 117 worktrees at risk,
which is the same as saying nothing: most of those "modifications" are a stale
checkout's copy of a file that master has since moved past, or a re-run that
regenerated an artefact to a state git already has. Deleting those loses
nothing, because the bytes are already in the object database.

So dirtiness is not the test. Content is. For every modified or untracked file
in a worktree this tool computes the file's git blob hash -- via `git
hash-object`, run inside that worktree, so that `core.autocrlf=true` and any
`.gitattributes` are applied exactly as git would apply them -- and asks whether
that blob is already reachable from some ref. A file whose exact content is
already in history is `preserved`; only a file whose content exists nowhere else
is `unique`, and only `unique` content (or a commit that is on no remote) makes
a worktree AT-RISK.

That distinction is the deliverable. Without it the list is 66 directories long
and unusable; with it, it is short enough to act on.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys
from pathlib import Path

# The mainline every branch is measured against. Deliberately the remote ref:
# local `master` in this repo has run 48 commits behind origin/master, and
# measuring against it would have reported dozens of merged branches as unmerged.
UPSTREAM = "origin/master"

# Directories whose contents are treated as "results" rather than scaffolding
# when they show up untracked. Used only to describe a worktree in the report --
# never to decide whether it is at risk.
RESULT_DIRS = ("runs/", "artifacts/", "out/", "exhibits/", "theory/")


def git(*args: str, cwd: str | None = None, check: bool = True) -> str:
    """Run git and hand back stdout. `--no-optional-locks` so a read-only census
    cannot end up refreshing an index in a worktree it does not own."""
    proc = subprocess.run(
        ["git", "--no-optional-locks", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} (cwd={cwd}) -> {proc.returncode}\n{proc.stderr}")
    return proc.stdout


def git_ok(*args: str, cwd: str | None = None) -> bool:
    proc = subprocess.run(
        ["git", "--no-optional-locks", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode == 0


def enumerate_worktrees(repo: str) -> list[dict]:
    """Every worktree git knows about, plus any directory sitting in
    `.worktrees/` that git has forgotten. The second half matters: a stale
    `.worktrees/foo` whose registration was pruned still holds files, and it is
    exactly the kind of thing that gets deleted without being looked at."""
    out = git("worktree", "list", "--porcelain", cwd=repo)
    registered: list[dict] = []
    cur: dict = {}
    for line in out.splitlines():
        if not line.strip():
            if cur:
                registered.append(cur)
                cur = {}
            continue
        key, _, val = line.partition(" ")
        if key == "worktree":
            cur = {"path": val, "registered": True}
        elif key == "HEAD":
            cur["head"] = val
        elif key == "branch":
            cur["branch"] = val.replace("refs/heads/", "")
        elif key == "detached":
            cur["branch"] = None
        elif key == "bare":
            cur["bare"] = True
    if cur:
        registered.append(cur)

    known = {os.path.normcase(os.path.abspath(w["path"])) for w in registered}
    wt_root = Path(repo) / ".worktrees"
    if wt_root.is_dir():
        for child in sorted(wt_root.iterdir()):
            if not child.is_dir():
                continue
            if os.path.normcase(os.path.abspath(str(child))) not in known:
                registered.append(
                    {"path": str(child), "registered": False, "head": None, "branch": None}
                )
    return registered


def reachable_blobs(repo: str) -> set[str]:
    """Every object reachable from every ref. ~15k entries in this repo and under
    a second to list, so the precision is nearly free.

    Reachability, not mere existence, is the right question: an object can linger
    in the database after the only branch pointing at it is gone, and `git gc`
    will drop it. If nothing points at the content, it is not preserved.
    """
    out = git("rev-list", "--objects", "--all", cwd=repo)
    return {line.split(" ", 1)[0] for line in out.splitlines() if line}


def blob_hashes(worktree: str, paths: list[str]) -> dict[str, str | None]:
    """git blob hash for each path, computed BY GIT inside the worktree.

    Not hashlib. `core.autocrlf=true` is set repo-wide, so a working file holding
    CRLF corresponds to an LF blob; hashing the bytes on disk would disagree with
    every blob in history and report all of them as unique. `hash-object` applies
    the same filters git would, which is the only way the comparison means
    anything.
    """
    if not paths:
        return {}
    proc = subprocess.run(
        ["git", "--no-optional-locks", "hash-object", "--stdin-paths"],
        cwd=worktree,
        input="\n".join(paths) + "\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    if len(lines) == len(paths):
        return dict(zip(paths, lines))
    # A path git refuses (vanished mid-scan, unreadable) desynchronises the
    # batch, so fall back to one call per path rather than mis-pairing hashes.
    out: dict[str, str | None] = {}
    for p in paths:
        one = subprocess.run(
            ["git", "--no-optional-locks", "hash-object", "--", p],
            cwd=worktree, capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        out[p] = one.stdout.strip() if one.returncode == 0 and one.stdout.strip() else None
    return out


def classify_status(porcelain: str) -> dict:
    """Split `git status --porcelain` into the three things that decide risk:
    staged/modified tracked files, and untracked files."""
    modified: list[str] = []
    untracked: list[str] = []
    for line in porcelain.splitlines():
        if len(line) < 3:
            continue
        code, path = line[:2], line[3:]
        # Rename entries read `R  old -> new`; the new path is the one on disk.
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        path = path.strip('"')
        if code == "??":
            untracked.append(path)
        else:
            modified.append(path)
    return {"modified": sorted(modified), "untracked": sorted(untracked)}


def audit_one(repo: str, wt: dict, blobs: set[str], self_path: str | None = None) -> dict:
    path = wt["path"]
    rel = os.path.relpath(path, repo).replace("\\", "/")
    inside = not rel.startswith("..")
    rec: dict = {
        "path": rel,
        "abs_path": path,
        "registered": wt.get("registered", True),
        "branch": wt.get("branch"),
        "head": wt.get("head"),
        "is_primary": os.path.normcase(os.path.abspath(path)) == os.path.normcase(os.path.abspath(repo)),
        "inside_repo": inside,
        # `.claude/worktrees/` belongs to the agent harness, not to this project's
        # `.worktrees/` convention. Worth reporting -- it is still disk holding
        # possibly-unique bytes -- but it is not the monitor's to clean up.
        "harness_owned": rel.startswith(".claude/"),
        "is_self": bool(self_path)
        and os.path.normcase(os.path.abspath(path)) == os.path.normcase(os.path.abspath(self_path)),
        "errors": [],
    }

    if not os.path.isdir(path):
        rec["errors"].append("directory does not exist (worktree registration is stale)")
        rec["disposition"] = "MISSING"
        rec["why"] = "git lists this worktree but the directory is gone; `git worktree prune` is the fix"
        return rec

    if not rec["registered"]:
        # Not a git worktree at all: no index, no HEAD, so `git status` says
        # nothing about it. These are the most dangerous directories in the
        # census -- names like `_c1w_salvage` suggest somebody rescued work here
        # and never put it anywhere -- so hash every file rather than settling
        # for a file count.
        files: list[str] = []
        for root, dirs, names in os.walk(path):
            dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", "node_modules")]
            for n in names:
                files.append(os.path.relpath(os.path.join(root, n), path).replace("\\", "/"))
        files.sort()
        rec["file_count"] = len(files)
        hashes = blob_hashes(path, files)
        uniq = [p for p in files if hashes.get(p) and hashes[p] not in blobs]
        unhashable = [p for p in files if not hashes.get(p)]
        rec["modified_count"] = 0
        rec["untracked_count"] = len(files)
        rec["unique_paths"] = sorted(uniq)
        rec["unique_count"] = len(uniq)
        rec["preserved_count"] = len(files) - len(uniq) - len(unhashable)
        rec["unhashable"] = sorted(unhashable)[:20]
        rec["unhashable_count"] = len(unhashable)
        rec["unique_results_count"] = sum(1 for p in uniq if any(s in p for s in RESULT_DIRS))
        rec["merged"] = False
        rec["commits_ahead"] = None
        rec["on_remote"] = False
        rec["remote_ref"] = None
        rec["unregistered_note"] = (
            f"directory in .worktrees/ that git does not track as a worktree; "
            f"{len(files)} files, none under version control here"
        )
        rec.update(decide(rec))
        return rec

    try:
        # -uall: an untracked DIRECTORY is reported as a single `dir/` entry by
        # default, which cannot be hashed and would hide however many files are
        # under it. Expanding to files is what makes the uniqueness test total.
        porcelain = git("status", "--porcelain", "-uall", cwd=path)
    except RuntimeError as exc:
        rec["errors"].append(f"status failed: {exc}")
        rec["disposition"] = "UNKNOWN"
        rec["why"] = "git status did not run; inspect by hand before removing"
        return rec

    st = classify_status(porcelain)
    rec["modified_count"] = len(st["modified"])
    rec["untracked_count"] = len(st["untracked"])

    # The load-bearing step: is any of this content actually only here?
    dirty = st["modified"] + st["untracked"]
    hashes = blob_hashes(path, dirty)
    unique: list[str] = []
    preserved: list[str] = []
    unhashable: list[str] = []
    for p in dirty:
        h = hashes.get(p)
        if h is None:
            unhashable.append(p)
        elif h in blobs:
            preserved.append(p)
        else:
            unique.append(p)
    # Not truncated. An earlier cut of this capped the list at 60 before the
    # churn split ran, which quietly turned "140 unique paths" into "60 authored"
    # -- an undercount of exactly the number the report exists to state. The JSON
    # carries every path; only the Markdown elides.
    rec["unique_paths"] = sorted(unique)
    rec["unique_count"] = len(unique)
    rec["preserved_count"] = len(preserved)
    rec["unhashable"] = sorted(unhashable)[:20]
    rec["unhashable_count"] = len(unhashable)
    rec["unique_results_count"] = sum(
        1 for p in unique if any(seg in p for seg in RESULT_DIRS)
    )

    rec["modified"] = st["modified"][:40]
    rec["untracked"] = st["untracked"][:40]
    rec["modified_truncated"] = len(st["modified"]) > 40
    rec["untracked_truncated"] = len(st["untracked"]) > 40

    branch = rec["branch"]
    head = rec["head"]

    # Merged? Measured commit-to-commit, so a detached HEAD is judged the same
    # way a branch is -- what matters is whether the commit is reachable from
    # the mainline, not whether somebody gave it a name.
    rec["merged"] = bool(head) and git_ok("merge-base", "--is-ancestor", head, UPSTREAM, cwd=repo)

    if head and not rec["merged"]:
        try:
            rec["commits_ahead"] = int(git("rev-list", "--count", f"{UPSTREAM}..{head}", cwd=repo).strip())
        except (RuntimeError, ValueError):
            rec["commits_ahead"] = None
    else:
        rec["commits_ahead"] = 0

    # Is every commit on this branch also on origin? If so the branch survives
    # deleting the directory, and losing the checkout costs nothing.
    rec["on_remote"] = False
    rec["remote_ref"] = None
    if branch:
        remote_ref = f"refs/remotes/origin/{branch}"
        if git_ok("rev-parse", "--verify", "--quiet", remote_ref, cwd=repo):
            rec["remote_ref"] = f"origin/{branch}"
            rec["on_remote"] = bool(head) and git_ok(
                "merge-base", "--is-ancestor", head, remote_ref, cwd=repo
            )

    rec.update(decide(rec))
    return rec


def decide(rec: dict) -> dict:
    """The one judgement in this file: what does deleting this directory cost?

    Order matters. Content that exists nowhere else outranks everything, because
    it is the only state git cannot get back. Then commits that are on no remote
    -- recoverable in principle from a reflog, but not from a deleted worktree
    plus a pruned branch, so they count as loss. Then merged-and-clean, free.

    Note what is deliberately NOT here: `modified_count`. A worktree with 138
    modified files and zero unique blobs has nothing to lose; a worktree with one
    modified file whose content is nowhere else has everything to lose. Counting
    dirt instead of content is what made the first pass of this census useless.
    """
    if rec["is_primary"]:
        return {
            "disposition": "PRIMARY",
            "why": f"the main checkout, not a disposable worktree "
                   f"({rec.get('unique_count', 0)} paths hold content found nowhere else)",
        }

    unique = rec.get("unique_count", 0)
    unhashable = rec.get("unhashable_count", 0)
    preserved = rec.get("preserved_count", 0)

    if unique or unhashable:
        bits = []
        if unique:
            bits.append(f"{unique} path(s) whose exact content is in no commit on any ref")
        if unhashable:
            bits.append(f"{unhashable} path(s) git could not hash")
        detail = "; ".join(bits)
        if rec.get("unique_results_count"):
            detail += f" ({rec['unique_results_count']} under a results dir)"
        if preserved:
            detail += f"; a further {preserved} dirty path(s) are already in history"
        return {"disposition": "AT-RISK", "why": detail}

    if not rec["merged"]:
        if rec["on_remote"]:
            return {
                "disposition": "RECOVERABLE",
                "why": f"{rec['commits_ahead']} commit(s) ahead of {UPSTREAM}, all pushed to {rec['remote_ref']}",
            }
        return {
            "disposition": "AT-RISK",
            "why": f"{rec['commits_ahead']} commit(s) ahead of {UPSTREAM} and on no remote -- "
                   f"this checkout is the only place that history exists",
        }

    if preserved:
        return {
            "disposition": "RECLAIMABLE",
            "why": f"merged into {UPSTREAM}; {preserved} dirty path(s), but every one of them "
                   f"holds content already reachable from a ref",
        }
    return {
        "disposition": "RECLAIMABLE",
        "why": f"merged into {UPSTREAM}, no uncommitted changes",
    }


RANK = {"AT-RISK": 0, "UNKNOWN": 1, "RECOVERABLE": 2, "MISSING": 3, "RECLAIMABLE": 4, "PRIMARY": 5}

# Paths that are machine state by construction: a lock a process forgot to drop,
# bytecode, the determinism scratch root the arm's own .gitignore already
# disclaims. Content-unique every time and worth nothing.
MACHINE_STATE = (".lock", ".pyc", "__pycache__/", "artifacts/_determinism/")

# How many worktrees a path must be independently dirty in before it is called
# churn rather than work. Three is the point where "somebody edited this here"
# stops being the simpler explanation than "a script rewrites this everywhere".
UBIQUITY_THRESHOLD = 3

# Files the ubiquity rule must never demote, however many worktrees they are
# dirty in. `PARTNER_SYNC.md` is append-only by contract (CLAUDE.md): five
# worktrees each holding an uncommitted paragraph is five different paragraphs,
# not one file a script rewrote five times, and the ubiquity heuristic cannot
# tell those apart. Losing a paragraph is exactly the loss this census exists to
# prevent, so the heuristic yields to the contract.
NEVER_CHURN = ("PARTNER_SYNC.md",)


def annotate_churn(records: list[dict]) -> dict:
    """Split each worktree's unique content into work and noise.

    Two signals, and only the second one is a judgement of mine:

    * empirical -- a path that is independently dirty in >= UBIQUITY_THRESHOLD
      separate worktrees is a file some script rewrites wherever it runs, not
      something a person edited in each of nine places. This is measured from
      the census itself rather than asserted.
    * declared -- MACHINE_STATE, a deliberately tiny list of suffixes that are
      state by definition.

    Nothing is dropped: `unique_paths` still carries every path. This only adds
    a count so a reader can see the shape of what is at stake without having to
    decide, for each of 327 paths, whether a `.lock` file matters.
    """
    freq: dict[str, int] = {}
    for r in records:
        for p in set(r.get("unique_paths", [])):
            freq[p] = freq.get(p, 0) + 1

    ubiquitous = {p for p, n in freq.items() if n >= UBIQUITY_THRESHOLD}
    for r in records:
        # A record that never got a status scan -- an unregistered directory, a
        # worktree whose status failed -- has an empty `unique_paths` because
        # nothing was measured, not because nothing is there. An earlier cut let
        # that empty list fall through the demotion below and relabelled a
        # directory full of untracked files as RECLAIMABLE. Absence of evidence
        # was being reported as evidence of absence, in a tool whose entire job
        # is to stop someone deleting the last copy of something.
        if "unique_count" not in r:
            r["unique_authored"] = []
            r["unique_authored_count"] = None
            r["unique_churn_count"] = None
            continue

        authored, noise = [], []
        for p in r.get("unique_paths", []):
            if any(p.endswith(n) for n in NEVER_CHURN):
                authored.append(p)
            elif p in ubiquitous or any(m in p for m in MACHINE_STATE):
                noise.append(p)
            else:
                authored.append(p)
        r["unique_authored"] = authored
        r["unique_authored_count"] = len(authored)
        r["unique_churn_count"] = len(noise)
        if r.get("disposition") == "AT-RISK" and not authored and not r.get("unhashable_count"):
            if r.get("commits_ahead") and not r.get("on_remote"):
                pass  # still at risk for its commits, leave the verdict alone
            elif not r.get("registered", True):
                r["disposition"] = "RECLAIMABLE"
                r["why"] = (
                    f"unregistered directory, {r.get('file_count', 0)} files, none of them tracked "
                    f"here -- but every one hashes to a blob already reachable from a ref, so the "
                    f"content survives without it"
                )
            elif noise:
                r["disposition"] = "RECLAIMABLE"
                r["why"] = (
                    f"{len(noise)} content-unique path(s), but every one is machine state or a file "
                    f"rewritten in >={UBIQUITY_THRESHOLD} worktrees -- nothing authored is only here"
                )
            else:
                r["disposition"] = "RECLAIMABLE"
                r["why"] = f"merged into {UPSTREAM}; nothing on disk that git does not already have"
    return {"ubiquitous_paths": sorted(ubiquitous), "path_frequency": freq}


def render_md(report: dict) -> str:
    L: list[str] = []
    s = report["summary"]
    L.append("# Worktree census — what deleting each one would cost")
    L.append("")
    L.append(f"Generated by `ablation-arm/abltools/worktree_audit.py` against `{UPSTREAM}` "
             f"at `{report['upstream_head'][:8]}`. Read-only: this tool has never deleted anything.")
    L.append("")
    L.append(f"**{s['total']} worktrees.** "
             f"{s['AT-RISK']} at risk · {s['RECOVERABLE']} recoverable · "
             f"{s['RECLAIMABLE']} reclaimable · {s['PRIMARY']} primary · "
             f"{s.get('MISSING',0)} missing · {s.get('UNKNOWN',0)} unknown")
    L.append("")
    L.append(f"**{s.get('authored_paths_only_on_disk', 0)} authored files, across "
             f"{s.get('worktrees_holding_authored_content', 0)} worktrees, exist only on disk** — "
             f"their exact bytes are in no commit reachable from any ref. That is the number "
             f"a cleanup would destroy.")
    L.append("")
    L.append("Dirtiness is not the test here; content is. A worktree can show 138 modified files "
             "and be perfectly safe to delete, because those files are a stale checkout's copy of "
             "something master has since moved past — git already has those bytes. Every modified "
             "and untracked file below was hashed with `git hash-object` (inside its own worktree, "
             "so `core.autocrlf` and `.gitattributes` apply) and looked up against every object "
             "reachable from every ref. Only content found nowhere else counts.")
    L.append("")
    if report.get("ubiquitous_paths"):
        L.append(f"Paths independently dirty in ≥{report['ubiquity_threshold']} worktrees are "
                 f"counted as churn rather than work — a script rewrites them wherever it runs: "
                 + ", ".join(f"`{p}`" for p in report["ubiquitous_paths"]) + ". They are still "
                 "listed per worktree; they just do not, alone, make one at risk.")
        L.append("")
    L.append("| disposition | meaning | count |")
    L.append("|---|---|---|")
    L.append(f"| `AT-RISK` | deleting loses work that exists nowhere else | {s['AT-RISK']} |")
    L.append(f"| `RECOVERABLE` | unmerged, but every commit is on origin | {s['RECOVERABLE']} |")
    L.append(f"| `RECLAIMABLE` | merged into `{UPSTREAM}`, clean — free to remove | {s['RECLAIMABLE']} |")
    L.append(f"| `MISSING` | registered but the directory is gone (`git worktree prune`) | {s.get('MISSING',0)} |")
    L.append(f"| `UNKNOWN` | git status did not run — inspect by hand | {s.get('UNKNOWN',0)} |")
    L.append(f"| `PRIMARY` | the main checkout, not disposable | {s['PRIMARY']} |")
    L.append("")

    for disp in ("AT-RISK", "UNKNOWN", "RECOVERABLE", "MISSING", "RECLAIMABLE", "PRIMARY"):
        rows = [r for r in report["worktrees"] if r["disposition"] == disp]
        if not rows:
            continue
        L.append(f"## {disp} ({len(rows)})")
        L.append("")
        if disp == "RECLAIMABLE":
            L.append("Merged and clean. Listed compactly; every one of these is safe to remove.")
            L.append("")
            L.append("| path | branch |")
            L.append("|---|---|")
            for r in rows:
                L.append(f"| `{r['path']}` | `{r.get('branch') or '(detached)'}` |")
            L.append("")
            continue

        L.append("| path | branch | ahead | on origin | dirty | of which unique | authored | why |")
        L.append("|---|---|---|---|---|---|---|---|")
        for r in rows:
            dirty = r.get("modified_count", 0) + r.get("untracked_count", 0)
            L.append(
                f"| `{r['path']}` | `{r.get('branch') or '(detached)'}` "
                f"| {r.get('commits_ahead', '—')} "
                f"| {'yes' if r.get('on_remote') else 'no'} "
                f"| {dirty} | {r.get('unique_count', '—')} "
                f"| **{r.get('unique_authored_count') if r.get('unique_authored_count') is not None else 'not scanned'}** "
                f"| {r['why']} |"
            )
        L.append("")

        if disp == "AT-RISK":
            L.append("### What is actually only here")
            L.append("")
            L.append("Per worktree, the files whose content is in no commit on any ref. "
                     "Machine state and churn are counted but not listed.")
            L.append("")
            for r in rows:
                if not r.get("unique_authored") and not r.get("unhashable"):
                    continue
                L.append(f"**`{r['path']}`** — branch `{r.get('branch') or '(detached)'}`, "
                         f"{r.get('unique_authored_count', 0)} authored "
                         f"(+{r.get('unique_churn_count', 0)} churn/state)")
                L.append("")
                for p in r.get("unique_authored", [])[:40]:
                    L.append(f"- `{p}`")
                extra = r.get("unique_authored_count", 0) - len(r.get("unique_authored", [])[:40])
                if extra > 0:
                    L.append(f"- …and {extra} more")
                for p in r.get("unhashable", []):
                    L.append(f"- `{p}` — git could not hash this; inspect by hand")
                L.append("")
    return "\n".join(L) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo", default=None, help="repo root (default: this file's repo)")
    ap.add_argument("--json", dest="json_out", default=None)
    ap.add_argument("--md", dest="md_out", default=None)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    repo = args.repo or git("rev-parse", "--show-toplevel").strip()
    # A worktree's toplevel is the worktree, not the repo that owns it. Walk to
    # the common dir so the census covers every sibling and not just this one.
    common = Path(git("rev-parse", "--git-common-dir", cwd=repo).strip())
    if not common.is_absolute():
        common = (Path(repo) / common).resolve()
    repo = str(common.parent)

    upstream_head = git("rev-parse", UPSTREAM, cwd=repo).strip()
    blobs = reachable_blobs(repo)
    self_path = str(Path(__file__).resolve().parent.parent.parent)

    wts = enumerate_worktrees(repo)
    records = []
    for i, wt in enumerate(wts, 1):
        if not args.quiet:
            print(f"[{i}/{len(wts)}] {wt['path']}", file=sys.stderr)
        records.append(audit_one(repo, wt, blobs, self_path))

    churn = annotate_churn(records)
    records.sort(
        key=lambda r: (RANK.get(r["disposition"], 9), -(r.get("unique_authored_count") or 0), r["path"])
    )

    summary = {"total": len(records)}
    for d in RANK:
        summary[d] = sum(1 for r in records if r["disposition"] == d)
    summary["authored_paths_only_on_disk"] = sum(r.get("unique_authored_count") or 0 for r in records)
    summary["worktrees_holding_authored_content"] = sum(
        1 for r in records if r.get("unique_authored_count")
    )

    report = {
        "prompt_id": "A15-ablation-calibration-uncommitted",
        "tool": "ablation-arm/abltools/worktree_audit.py",
        "upstream": UPSTREAM,
        "upstream_head": upstream_head,
        "repo": repo.replace("\\", "/"),
        "read_only": True,
        "deleted_anything": False,
        "ubiquity_threshold": UBIQUITY_THRESHOLD,
        "ubiquitous_paths": churn["ubiquitous_paths"],
        "summary": summary,
        "worktrees": records,
    }

    if args.json_out:
        with io.open(args.json_out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report, fh, indent=2, ensure_ascii=False, sort_keys=False)
            fh.write("\n")
    if args.md_out:
        with io.open(args.md_out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(render_md(report))

    if not args.quiet:
        print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
