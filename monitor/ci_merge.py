"""Merge-on-delivery (upgrade #2): the deterministic happy path of M-0.

    python monitor/ci_merge.py            # merge up to 2 delivered branches
    python monitor/ci_merge.py --dry-run

Territories are mutually exclusive, so merges of disjoint branches commute —
the happy path needs no judgment, only a test gate. For each origin agent/*
branch not yet merged: merge into master in a throwaway worktree, run the
test suites of every top-level dir the branch touched, push on green.
Anything non-happy (conflict, red tests, unknown dir) is left for a real
M-0 session with a flag file in monitor/ci/.

Safety: single-instance lock; never runs while an M-0 session is alive;
PARTNER_SYNC.md merges by union (.gitattributes) since it is append-only.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CI_DIR = os.path.join(HERE, "ci")
LOCK = os.path.join(CI_DIR, "merge.lock")
LOG = os.path.join(CI_DIR, "merge.log")

# top-level dir -> test command (run from that dir inside the merge worktree)
TEST_CMDS = {
    "engine-rig": [sys.executable, "-m", "pytest", "-q", "-x"],
    "theory-compiler": [sys.executable, "-m", "pytest", "-q", "-x"],
    "proxy": [sys.executable, "-m", "pytest", "-q", "-x"],
    "battery": [sys.executable, "-m", "pytest", "-q", "-x"],
    "cold-start-a0": [sys.executable, "-m", "pytest", "-q", "-x"],
    "cold-start-a2": [sys.executable, "-m", "pytest", "-q", "-x"],
    "a0-spike": [sys.executable, "-m", "pytest", "-q", "-x"],
    "exam": [sys.executable, "-m", "pytest", "-q", "-x"],
}
# dirs that are docs/data only — merge without a test run
NO_TEST_OK = {"papers", "figures", "freeze", "release", "worldgen", "fuzzlab",
              "crosscheck", "browser-ops", "monitor", "arc-recon",
              "baseline-arms", "theoria-arm", "ablation-arm", "cold-start-a3",
              "CONTRACTS", ".claude"}


def sh(args, cwd=ROOT, timeout=1800):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                          timeout=timeout)


def log_line(msg):
    os.makedirs(CI_DIR, exist_ok=True)
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write("%s %s\n" % (stamp, msg))
    print(msg)


def flag(branch, reason, detail):
    os.makedirs(CI_DIR, exist_ok=True)
    name = "CONFLICT-%s.md" % branch.replace("/", "_")
    with open(os.path.join(CI_DIR, name), "w", encoding="utf-8") as fh:
        fh.write("# %s\nbranch: %s\nreason: %s\n\n```\n%s\n```\n"
                 % (name, branch, reason, detail[-4000:]))
    log_line("FLAG %s: %s" % (branch, reason))


def m0_alive():
    reg_path = os.path.join(HERE, "dispatch-logs", "registry.json")
    if not os.path.exists(reg_path):
        return False
    reg = json.load(open(reg_path, encoding="utf-8"))
    entry = reg.get("M-0")
    if not entry or entry.get("reaped"):
        return False
    out = sh(["tasklist", "/FI", "PID eq %d" % entry["pid"], "/FO", "CSV"])
    return str(entry["pid"]) in out.stdout


def take_lock():
    os.makedirs(CI_DIR, exist_ok=True)
    if os.path.exists(LOCK):
        age = time.time() - os.path.getmtime(LOCK)
        if age < 3600:
            return False
        os.remove(LOCK)  # stale
    with open(LOCK, "w") as fh:
        fh.write(str(os.getpid()))
    return True


def release_lock():
    try:
        os.remove(LOCK)
    except OSError:
        pass


def unmerged_branches():
    sh(["git", "fetch", "--prune", "origin"])
    out = sh(["git", "branch", "-r", "--list", "origin/agent/*",
              "--format=%(refname:short)"]).stdout.split()
    todo = []
    for b in out:
        merged = sh(["git", "merge-base", "--is-ancestor", b, "origin/master"])
        if merged.returncode != 0:
            todo.append(b)
    return todo


def touched_dirs(branch):
    base = sh(["git", "merge-base", "origin/master", branch]).stdout.strip()
    out = sh(["git", "diff", "--name-only", base, branch]).stdout
    return {line.split("/")[0] for line in out.splitlines() if line.strip()}


def try_merge(branch):
    dirs = touched_dirs(branch)
    unknown = {d for d in dirs
               if d not in TEST_CMDS and d not in NO_TEST_OK
               and "." not in d and d != "PARTNER_SYNC.md"}
    root_files = {d for d in dirs if "." in d}
    bad_root = root_files - {"PARTNER_SYNC.md", "README.md", ".gitignore",
                             ".gitattributes"}
    if bad_root & {".env", "Theoria.md", "CLAUDE.md", "LICENSE"} or \
            (bad_root and any(f in ("piles.json",) for f in bad_root)):
        flag(branch, "touches protected root files", str(sorted(bad_root)))
        return False
    if unknown:
        flag(branch, "touches unknown territory (needs M-0 judgment)",
             str(sorted(unknown)))
        return False

    wt = tempfile.mkdtemp(prefix="ci-merge-")
    try:
        r = sh(["git", "worktree", "add", "--detach", wt, "origin/master"])
        if r.returncode != 0:
            flag(branch, "worktree add failed", r.stderr)
            return False
        r = sh(["git", "merge", "--no-ff", "--no-edit", branch], cwd=wt)
        if r.returncode != 0:
            sh(["git", "merge", "--abort"], cwd=wt)
            flag(branch, "merge conflict", r.stdout + r.stderr)
            return False
        for d in sorted(dirs & set(TEST_CMDS)):
            r = sh(TEST_CMDS[d], cwd=os.path.join(wt, d), timeout=1800)
            if r.returncode != 0:
                flag(branch, "tests red in %s" % d,
                     (r.stdout + r.stderr))
                return False
        r = sh(["git", "push", "origin", "HEAD:master"], cwd=wt)
        if r.returncode != 0:
            flag(branch, "push rejected (race?)", r.stderr)
            return False
        sh(["git", "push", "origin", "--delete",
            branch.replace("origin/", "")])
        log_line("MERGED %s (dirs: %s)" % (branch, ",".join(sorted(dirs))))
        return True
    finally:
        sh(["git", "worktree", "remove", "--force", wt])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max", type=int, default=2)
    args = ap.parse_args()
    if m0_alive():
        print("M-0 session alive — CI stands down.")
        return 0
    todo = unmerged_branches()
    if args.dry_run or not todo:
        print("delivered, unmerged:", todo or "none")
        return 0
    if not take_lock():
        print("another merge in progress.")
        return 0
    try:
        done = 0
        for b in todo:
            if done >= args.max:
                break
            if try_merge(b):
                done += 1
        # keep local master in step with origin so later merges see reality
        sh(["git", "pull", "--ff-only", "origin", "master"])
        return 0
    finally:
        release_lock()


if __name__ == "__main__":
    raise SystemExit(main())
