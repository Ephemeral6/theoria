"""Which commit was this arm at when a run happened?

Every ledger's `run_start` record carries an `arm_version` -- a count of this
arm's `.py` files and one sha256 over their contents, computed by
`_bootstrap.arm_version()`. No ledger carries the commit. But `arm_version` is
a pure function of the arm's own sources, so it can be recomputed at any commit
in history and matched. That turns "which commit was this?" from a thing you
remember into a thing you check.

Three answers are possible and the difference matters:

* **matched** -- exactly one tree state in history hashes to the recorded
  value. The commit (or commits, if a later one left the arm's `.py` files
  untouched) is named, and the branches containing it are named with it.
* **no match** -- the run executed against a working tree that was never
  committed in that state. This is the common case for a run made mid-session,
  and it is a real finding rather than a tool failure: the run is not
  reproducible from git, and the manifest must say so.
* **ambiguous** -- several unrelated commits share the hash. Reported with all
  of them; the caller decides using time.

The hash is reconstructed from git objects, not from the working tree, so this
module is read-only with respect to the checkout and gives the same answer on
any clone.

    python -m armtools.armversion --scan            # every distinct tree state
    python -m armtools.armversion --hash <sha256>   # find one
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap                                     # noqa: F401  (sys.path)

ARM_PREFIX = "theoria-arm/"


def _git(*args: str, binary: bool = False):
    out = subprocess.run(["git", *args], cwd=_bootstrap.REPO,
                         capture_output=True, timeout=120)
    if out.returncode != 0:
        raise RuntimeError("git %s failed: %s"
                           % (" ".join(args), out.stderr.decode("utf-8", "replace")))
    return out.stdout if binary else out.stdout.decode("utf-8")


def _counted(rel: str) -> bool:
    """The same filter `_bootstrap.arm_version()` applies, stated over paths.

    `_bootstrap` walks the arm and skips a directory when `"__pycache__" in
    root` or `os.sep + "runs" in root` -- both **substring** tests, not
    component tests. `runsim/`, `runs_old/` and `__pycache__x/` therefore all
    get skipped by the walk, and a component-wise reimplementation would count
    them. No such directory has ever existed under this arm (checked with
    `git log --all --full-history --name-only`), so the two rules have never
    disagreed on real data -- but a reimplementation that is only accidentally
    equivalent is a trap, and the divergence would have been silent: a file the
    recorded hash never saw would be counted, and the run would report
    `no_match` for no reason.

    Mirrored here on the path *relative to the arm root*, with a leading
    separator so the first component is tested like any other. The walk's test
    also sees the absolute prefix above the arm; see `_bootstrap.arm_version`,
    where that is now handled rather than inherited.
    """
    if not rel.endswith(".py"):
        return False
    directory = "/" + "/".join(rel.split("/")[:-1])
    return "__pycache__" not in directory and "/runs" not in directory


def arm_version_at(commit: str) -> Optional[Dict[str, Any]]:
    """Recompute `_bootstrap.arm_version()` from a commit's tree.

    Returns None if the arm does not exist at that commit.
    """
    try:
        tree = _git("rev-parse", "%s:%s" % (commit, ARM_PREFIX.rstrip("/"))).strip()
    except RuntimeError:
        return None
    return _arm_version_of_tree(tree)


def _arm_version_of_tree(tree: str) -> Optional[Dict[str, Any]]:
    """The same, keyed by the arm's subtree rather than by a commit.

    Many commits share one arm subtree -- most commits in this repository touch
    another track entirely -- so caching on the tree oid is what makes an
    exhaustive scan of every reachable commit cheap.
    """
    try:
        listing = _git("ls-tree", "-r", "-z", tree)
    except RuntimeError:
        return None

    blobs: Dict[str, str] = {}
    for entry in listing.split("\0"):
        if not entry:
            continue
        meta, _, rel = entry.partition("\t")
        fields = meta.split()
        if len(fields) < 3 or fields[1] != "blob":
            continue
        if _counted(rel):
            blobs[rel] = fields[2]
    if not blobs:
        return None

    digests = {rel: hashlib.sha256(_git("cat-file", "blob", oid, binary=True)
                                   ).hexdigest()
               for rel, oid in blobs.items()}
    blob = "".join("%s=%s\n" % kv for kv in sorted(digests.items()))
    return {"files": len(digests),
            "sha256": hashlib.sha256(blob.encode("utf-8")).hexdigest()}


def scan(refs: str = "--all") -> Dict[str, Any]:
    """**Every** reachable commit, with the arm hash its tree carries.

    The obvious implementation walks `git log --all -- theoria-arm`, on the
    reasoning that only a commit touching the arm can change the hash. That is
    true and it is the wrong scan, because the question is not "where did the
    hash change" but "which commits carry this hash" -- and every commit that
    left the arm alone carries its parent's. On this repository one arm version
    is shared by 187 commits while the arm-touching log finds one of them, so
    a lookup would report `matched` and name a single commit where 187 are
    equally consistent. An adversarial review found this; no manifest here was
    wrong, by luck of which hashes the runs happened to record.

    So: every commit from `rev-list --all`, resolved to its `theoria-arm`
    subtree. Distinct subtrees are few (17 across 347 commits), and the hash is
    computed once per subtree rather than once per commit, which is what makes
    the exhaustive scan affordable.

    Still not covered, and said rather than implied: commits reachable only
    from the reflog or dangling entirely. `locate`'s verdicts are about what is
    reachable from a ref.
    """
    revs = [line.strip() for line in _git("rev-list", refs).split("\n")
            if line.strip()]

    # One batch call resolves every commit to its arm subtree oid; a per-commit
    # `rev-parse` would be 347 process launches.
    query = "".join("%s:%s\n" % (sha, ARM_PREFIX.rstrip("/")) for sha in revs)
    out = subprocess.run(["git", "cat-file", "--batch-check"],
                         cwd=_bootstrap.REPO, input=query.encode("utf-8"),
                         capture_output=True, timeout=300)
    tree_of: Dict[str, str] = {}
    for sha, line in zip(revs, out.stdout.decode("utf-8").splitlines()):
        fields = line.split()
        if len(fields) >= 2 and fields[1] == "tree":
            tree_of[sha] = fields[0]

    when = {}
    for line in _git("log", refs, "--format=%H %ct").split("\n"):
        line = line.strip()
        if line:
            sha, _, ct = line.partition(" ")
            when[sha] = int(ct)

    version_of_tree: Dict[str, Optional[Dict[str, Any]]] = {}
    commits: List[Dict[str, Any]] = []
    by_hash: Dict[str, List[Dict[str, Any]]] = {}
    for sha in revs:
        tree = tree_of.get(sha)
        if tree is None:                                # the arm did not exist yet
            continue
        if tree not in version_of_tree:
            version_of_tree[tree] = _arm_version_of_tree(tree)
        version = version_of_tree[tree]
        if version is None:
            continue
        entry = {"commit": sha, "unix": when.get(sha, 0),
                 "files": version["files"], "arm_sha256": version["sha256"]}
        commits.append(entry)
        by_hash.setdefault(version["sha256"], []).append(entry)

    commits.sort(key=lambda c: -c["unix"])
    for group in by_hash.values():
        group.sort(key=lambda c: c["unix"])
    return {"refs": refs,
            "commits_scanned": len(revs),
            "commits_carrying_the_arm": len(commits),
            "distinct_arm_subtrees": len(version_of_tree),
            "distinct_arm_versions": len(by_hash),
            "by_hash": by_hash, "commits": commits}


def branches_containing(commit: str) -> List[str]:
    try:
        out = _git("branch", "-a", "--contains", commit, "--format=%(refname:short)")
    except RuntimeError:
        return []
    return sorted(b.strip() for b in out.split("\n") if b.strip())


def locate(arm_sha256: str, table: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Answer the question for one recorded `arm_version.sha256`."""
    table = table if table is not None else scan()
    if not (isinstance(arm_sha256, str) and len(arm_sha256) == 64
            and all(c in "0123456789abcdef" for c in arm_sha256.lower())):
        return {
            "verdict": "not_a_sha256",
            "arm_sha256": arm_sha256,
            "commits": [],
            "detail": ("that is not a 64-character hex digest. Answering "
                       "`no_match` to a mistyped hash would hand back the "
                       "whole 'this run ran against uncommitted files' story "
                       "for what is really a typo."),
        }
    hits = table["by_hash"].get(arm_sha256) or []
    if not hits:
        return {
            "verdict": "no_match",
            "arm_sha256": arm_sha256,
            "commits": [],
            "detail": ("no commit reachable from any ref carries this "
                       "arm_version, so the run executed against a working "
                       "tree that was never committed in that state. The run "
                       "is therefore not reproducible from git alone. "
                       "(Commits reachable only from the reflog, or dangling, "
                       "are outside this scan.)"),
        }
    # Deliberately no branch list. `git branch --contains` answers "which
    # branches hold this commit *today*", which grows every time anyone in this
    # repo pushes -- it is a fact about the repository now, not about the run,
    # and putting it in a manifest makes the manifest drift under a colleague's
    # unrelated work. `branches_containing` is still available for a human at
    # the CLI, where a moving answer is fine.
    return {
        "verdict": "matched" if len(hits) == 1 else "ambiguous",
        "arm_sha256": arm_sha256,
        "commits": [h["commit"] for h in hits],
        "earliest_commit": hits[0]["commit"],
        "detail": ("exactly one commit reachable from any ref carries this "
                   "arm_version"
                   if len(hits) == 1 else
                   "%d commits carry this arm_version -- the arm's .py files "
                   "are byte-identical at each, and `arm_version` covers `.py` "
                   "only, so commits differing in a prompt, a log or a fixture "
                   "are indistinguishable here. The earliest is the one the "
                   "sources first appeared in; disambiguate the rest by time."
                   % len(hits)),
    }


def nearest_by_time(unix_ts: int, table: Optional[Dict[str, Any]] = None
                    ) -> Dict[str, Any]:
    """The commit window a run fell into, for when the hash does not match.

    Not an answer to "which commit" -- an honest bracket around it.
    """
    table = table if table is not None else scan()
    before = [c for c in table["commits"] if c["unix"] <= unix_ts]
    after = [c for c in table["commits"] if c["unix"] > unix_ts]
    pick = lambda xs, key: (sorted(xs, key=key)[0] if xs else None)   # noqa: E731
    return {
        "last_commit_before": pick(before, lambda c: -c["unix"]),
        "first_commit_after": pick(after, lambda c: c["unix"]),
        "note": ("the run happened between these two commits; its arm_version "
                 "matches neither, so its sources were uncommitted edits "
                 "somewhere inside that window"),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--hash")
    ap.add_argument("--commit")
    args = ap.parse_args(argv)

    if args.commit:
        print(json.dumps(arm_version_at(args.commit), indent=1, sort_keys=True))
    elif args.hash:
        found = locate(args.hash)
        found["branches_today"] = sorted(
            {b for c in found["commits"] for b in branches_containing(c)})
        print(json.dumps(found, indent=1, sort_keys=True))
    elif args.scan:
        table = scan()
        print(json.dumps({k: v for k, v in table.items() if k != "commits"},
                         indent=1, sort_keys=True, default=str))
    else:
        ap.error("one of --scan / --hash / --commit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
