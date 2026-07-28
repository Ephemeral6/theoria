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
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import gates                                                        # noqa: E402
CI_DIR = os.path.join(HERE, "ci")
LOCK = os.path.join(CI_DIR, "merge.lock")
LOG = os.path.join(CI_DIR, "merge.log")

PYTEST = [sys.executable, "-m", "pytest", "-q", "-x"]
NO_TESTS_COLLECTED = 5      # pytest's exit code for "found nothing to run"

# Whether a directory is gated is read off the merged tree, not off a list.
#
# It was a list, and the list went stale the way lists do: six directories
# holding 509 tests between them sat in a "docs/data only" set while their
# branches merged with no gate at all, and because a skipped suite and a passing
# suite are the same single MERGED line in the log, nothing ever said so.  The
# hand-written repair then got four of its seven entries wrong in the same
# commit -- `ablation-arm` has no tests and `fuzzlab`'s pytest.ini pointed at a
# directory containing none, so both would have failed every branch that touched
# them with "tests red"; `arc-recon` (82) and `baseline-arms` (32) were left
# ungated.  A table maintained by hand is a claim about the tree that nothing
# checks against the tree.  So: ask the tree.
#
# TEST_CMDS is now only for directories whose gate is *not* plain pytest.
TEST_CMDS = {}

# Territory this rig recognises.  This set no longer decides whether tests run;
# it only answers "has anyone declared this directory?", so a branch touching
# somewhere nobody has heard of still stops for M-0's judgment.
KNOWN_DIRS = {"engine-rig", "theory-compiler", "proxy", "battery",
              "cold-start-a0", "cold-start-a2", "cold-start-a3", "a0-spike",
              "exam", "worldgen", "fuzzlab", "theoria-arm", "ablation-arm",
              "arc-recon", "baseline-arms", "papers", "figures", "freeze",
              "release", "crosscheck", "browser-ops", "monitor", "CONTRACTS",
              ".claude",
              # M-0 裁决 2026-07-29（监控代行）：两块新领地准入。
              # `fleet-study` 是舰队自身的证据集（S17 建），`verify-lab` 是
              # RES-3 那三路普查与负控探针的落脚处——六条已交付分支卡在
              # 「unknown territory」上等的就是这一句。准入不等于免检：
              # 两块地按 S13 各自欠一个闸门，`gates.py` 的普查会一直把它们
              # 记成 UNGATED，直到它们自己交出来。
              "fleet-study", "verify-lab"}


def gate_for(worktree, directory):
    """What to run for `directory`, as `{kind, cmd, name, why}`.

    Asked of the merged tree, so a directory that grows a suite -- or a gate --
    is gated from its very first merge and nobody has to remember to come back
    here.  The answer comes from `gates.py`, which `scan.probe_verify_gates`
    also reads: two implementations of "what is this territory's gate" would
    drift, and the comment above records what that cost the last time.

    `TEST_CMDS` still wins when a directory is listed there, which is how an
    override survives.  It is empty today.
    """
    if directory in TEST_CMDS:
        return {"kind": "pytest", "cmd": TEST_CMDS[directory],
                "name": None, "canonical": None, "why": "TEST_CMDS override"}
    return gates.gate_for(worktree, directory)


def sh(args, cwd=ROOT, timeout=1800):
    # 子进程的 stdout 在这里是管道，Windows 上 Python 于是按 cp936 编码，
    # 闸门只要打印一个非 GBK 字符就死于 UnicodeEncodeError——而 ci_merge
    # 把它记成「verify gate red」。monitor 自己的闸门就是这么红的。
    # 这仓库已经为 GBK/UTF-8 付过四次账，所以在唯一的出口处钉死。
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace",
                          timeout=timeout, env=env)


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
               if d not in KNOWN_DIRS
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
        ran, ungated = [], []
        for d in sorted(dirs):
            row = gate_for(wt, d)
            if row["kind"] == "none":
                # S13: an ungated merge is now *said out loud*. It used to be
                # indistinguishable from a gated one -- both were the same
                # single MERGED line -- which is how ten territories went
                # without a gate and nobody could see it. This does not block
                # the merge: making the openness visible is the fix, refusing
                # to merge anything ungated would stop the repository dead.
                if os.path.isdir(os.path.join(wt, d)):
                    ungated.append(d)
                continue
            cmd = row["cmd"]
            r = sh(cmd, cwd=os.path.join(wt, d), timeout=1800)
            if row["kind"] == "verify" and r.returncode != 0:
                flag(branch, "verify gate red in %s (%s)" % (d, row["name"]),
                     r.stdout + r.stderr)
                return False
            if r.returncode == NO_TESTS_COLLECTED:
                # The directory holds test_*.py and pytest still found nothing
                # to run, so its configuration is pointed somewhere else.  That
                # is a broken gate, not a passing one, and it is reported as
                # its own thing: read as "green" it would be the fourth time
                # this repo mistook a check that cannot run for a check that
                # passed.
                flag(branch, "test suite in %s collects nothing "
                             "(gate misconfigured, not a red suite)" % d,
                     r.stdout + r.stderr)
                return False
            if r.returncode != 0:
                flag(branch, "tests red in %s" % d,
                     (r.stdout + r.stderr))
                return False
            ran.append(gates.describe(row, d))

        # A gate that writes into the tree it is gating can turn itself red, and
        # worse, can turn the *next* directory's gate red for a reason that has
        # nothing to do with the branch. Reported rather than blocked: several
        # gates regenerate artefacts on purpose (`exam/verify.py` rebuilds its
        # papers), so failing here would block every merge that touches them.
        # Naming the files is what lets a reader tell the two apart.
        dirty = sh(["git", "status", "--porcelain"], cwd=wt).stdout.split()
        dirtied = sorted({p for p in dirty if "/" in p})[:6]

        r = sh(["git", "push", "origin", "HEAD:master"], cwd=wt)
        if r.returncode != 0:
            flag(branch, "push rejected (race?)", r.stderr)
            return False
        sh(["git", "push", "origin", "--delete",
            branch.replace("origin/", "")])
        # Which gates ran is part of the record.  Without it "tested and passed"
        # and "never tested" are the same line, which is exactly how 509 tests
        # stayed skipped without anyone noticing.  S13 adds the other half: a
        # territory with no gate at all is now named, every time, rather than
        # being absent from a list of what ran.
        parts = ["MERGED %s (dirs: %s; gates: %s"
                 % (branch, ",".join(sorted(dirs)), ",".join(ran) or "none")]
        if ungated:
            parts.append("; NO GATE, MERGED UNCHECKED: %s" % ",".join(ungated))
        if dirtied:
            parts.append("; a gate dirtied the worktree: %s" % ",".join(dirtied))
        parts.append(")")
        log_line("".join(parts))
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
