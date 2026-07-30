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
import re
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


BASE_MEMO = os.path.join(CI_DIR, "base_gates.json")


def base_verdict(wt, directory, row, base_sha):
    """Is this territory's gate red on `origin/master` **alone**?

    Returns 0 (base green), non-zero (base red), or None (could not tell).

    S43. `unmerged_branches()` only ever enumerates `origin/agent/*`, so a commit
    made directly on master is gated by nothing -- there is no code path in this
    file that runs a gate against an unmerged `origin/master`. On 2026-07-30
    `873d62ee` went straight onto master and turned `monitor`'s suite red; the
    gate noticed 9m47s later and, having no notion of a base verdict, wrote the
    red down against the next branch that happened to touch `monitor/`. Nine
    branches were held that way, one of them for 6h41m, and one accumulated a
    `NEEDS-HUMAN: 28 attempts` badge for three unrelated failures. Every held
    branch's failure set was byte-identical to master's, with zero novel
    failures -- so the instrument was firing correctly and blaming the wrong
    party every single time.

    `should_hold` already argues (at length) that a gate verdict is a statement
    about the *merged* tree and therefore depends on `origin/master` as much as
    on the branch. It applies that only to retry scheduling. This applies it to
    attribution, which is where it changes who gets blamed.

    Cost on the green path is exactly zero: nothing calls this until a gate has
    already gone red. On the red path it is one extra gate run per
    `(master sha, territory)`, memoised -- so nine branches tripping over the
    same red master pay for it once between them, where today they each pay in
    full to re-derive the identical verdict.
    """
    key = "%s/%s" % (base_sha, directory)
    try:
        memo = json.load(open(BASE_MEMO, encoding="utf-8"))
    except Exception:
        memo = {}
    if key in memo:
        return memo[key]

    # The worktree currently holds the merged tree. We are on our way to
    # refusing this branch either way, so resetting it to the base costs
    # nothing that is still needed.
    if sh(["git", "checkout", "--force", base_sha], cwd=wt).returncode != 0:
        return None
    # Untracked leftovers from the gate run we just did would otherwise be read
    # as part of the base. `-fdq` and not `-fdxq`: ignored files are the
    # toolchain, not the branch's doing.
    sh(["git", "clean", "-fdq"], cwd=wt)

    r = sh(row["cmd"], cwd=os.path.join(wt, directory), timeout=1800,
           extra_env=gates.gate_env(wt))
    rc = r.returncode

    # **Never fall back to "the base is green."** Returning 0 on a failed probe
    # silently restores branch-blaming, which is the bug this exists to end;
    # None makes the caller say "could not tell" instead of picking a side.
    memo[key] = rc
    try:
        os.makedirs(CI_DIR, exist_ok=True)
        # Written to the real CI_DIR, never into `wt` -- the dirty-worktree
        # check below would otherwise report this memo as a gate dirtying the
        # tree it was gating.
        tmp = BASE_MEMO + ".tmp"
        json.dump(memo, open(tmp, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1, sort_keys=True)
        os.replace(tmp, BASE_MEMO)
    except Exception:
        pass            # the verdict is still good for this run
    return rc


def blame_the_base(branch, wt, directory, row, reason, detail, tip):
    """Decide whether `reason` belongs to the branch or to master, and say so.

    Returns True when master was named instead of the branch. The branch is
    still refused either way -- merging into a red master is not made safe by
    knowing whose fault it is -- but the branch's `attempts` counter does not
    inflate, and the log names the thing that is actually broken.
    """
    base_sha = branch_tip("origin/master")
    rc = base_verdict(wt, directory, row, base_sha)
    if rc is None:
        flag(branch, "%s (could not determine whether origin/master is already "
                     "red here -- base probe failed)" % reason, detail, tip=tip)
        return False
    if rc == 0:
        return False                    # the base is clean: the branch owns it
    # The prefix must stay `FLAG`: `reflex.merge_events` scrapes this log with a
    # literal `startswith("MERGED")` / `startswith("FLAG")`, so a line beginning
    # `ALARM` or `MASTER-RED` would be written here and never reach reflex.log
    # or the dashboard -- invisible in exactly the way the bug was.
    flag("origin/master",
         "BASE RED in %s (%s): origin/master fails this gate on its own"
         % (directory, row.get("name") or row["kind"]), detail,
         tip=base_sha)
    log_line("FLAG origin/master: BASE RED in %s -- %s adds no new failure and "
             "is NOT at fault; every branch touching %s is blocked by master"
             % (directory, branch, directory))
    return True


def sh(args, cwd=ROOT, timeout=1800, extra_env=None):
    # 子进程的 stdout 在这里是管道，Windows 上 Python 于是按 cp936 编码，
    # 闸门只要打印一个非 GBK 字符就死于 UnicodeEncodeError——而 ci_merge
    # 把它记成「verify gate red」。monitor 自己的闸门就是这么红的。
    # 这仓库已经为 GBK/UTF-8 付过四次账，所以在唯一的出口处钉死。
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    if extra_env:
        env.update(extra_env)
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace",
                          timeout=timeout, env=env)


def log_line(msg):
    os.makedirs(CI_DIR, exist_ok=True)
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write("%s %s\n" % (stamp, msg))
    print(msg)


def flag_path(branch):
    return os.path.join(CI_DIR,
                        "CONFLICT-%s.md" % branch.replace("/", "_"))


def branch_tip(branch):
    out = sh(["git", "rev-parse", branch])
    return out.stdout.strip() if out.returncode == 0 else ""


# Holding a branch is a claim that re-running it would reach the same verdict,
# and that claim is only sound when the verdict was about the branch.
#
# `push rejected (race?)` is decided *after* every gate has already passed, by
# whether master moved between building the worktree and pushing it.  It is a
# fact about master, not about the branch, so the tip test -- which asks only
# whether the branch changed -- answers a question nobody asked and parks work
# that is already green.
#
# Measured rather than argued: `c10-unsolvable-proof-canon` was flagged this
# way at 04:15Z, listed in every HELD line for six hours, and then merged on
# the first retry with nothing about it changed; `s21-app-session-death` did
# the same the following cycle.  Two for two.  Retrying a race is how a race is
# won, and the retry is cheap compared to leaving finished work on the floor.
#
# Deliberately narrow: conflicts and red gates stay held, because those really
# are properties of the branch and re-deriving them costs a worktree and a full
# gate run.  The hold itself was worth having -- it replaced 169 retries and
# 915 identical FLAG lines.  What was wrong was only which failures it covers.
#
# Two other reasons belong to the same kind and were added when this landed
# next to S29: `worktree add failed` is a fact about the disk and `... timed
# out` is a fact about the machine's load.  Neither was caused by the branch,
# so neither can be cleared by it -- the same deadlock, differently worded.
# The matching is case-insensitive because the reason strings this rig writes
# are sentences, not tokens ("verify gate timed out in engine-rig").
#
# Widening the set is only safe because the retries are now capped; see
# `TRANSIENT_RETRY_CAP` below.  Unbounded retry is what wrote the 915 lines.
TRANSIENT_REASONS = ("push rejected", "worktree add failed", "timed out")


def is_transient(reason):
    """Did this verdict describe the world around the branch rather than it?"""
    low = (reason or "").lower()
    return any(t in low for t in TRANSIENT_REASONS)


def last_attempt(branch):
    """What the previous run already tried on this branch, or {} if none.

    Read back out of the flag file's own header, because that is the file that
    already survives between runs and the one a human reads.
    """
    path = flag_path(branch)
    if not os.path.exists(path):
        return {}
    memo = {}
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("```"):
                    break
                if ":" in line:
                    k, _, v = line.partition(":")
                    memo[k.strip().lstrip("# ")] = v.strip()
    except OSError:
        return {}
    return memo


#: How many times a transient failure is retried before it is held like any
#: other. Set to the same number that already pages a human in `flag`, so the
#: retries stop exactly when someone is being told to look.
TRANSIENT_RETRY_CAP = 3


def should_hold(memo, tip, base=None):
    """Skip this branch? The hold rule itself, in one place.

    A gate verdict is a statement about the **merged** tree, so it depends on
    `origin/master` as much as on the branch. Keying the hold on the tip alone
    made a verdict outlive the thing it described: `p13-figure-numbering` was
    red because of a coverage probe in `figures/`, master cured that probe at
    05:15Z, and the flag still read "verify gate red in figures" six hours
    later with no retry. The comment above the old condition claimed "skipping
    is therefore never a way for a fixed branch to stay stuck" -- p13 is the
    counterexample, because it was fixed by the *base* moving, not the tip.

    A flag written before `base:` existed has no base recorded. That is read as
    "retry", not "skip": one wasted re-run per old flag, once, versus keeping
    the failure mode this argument is about.

    Extracted because `test_ci_merge_hold.py` had grown its own copy of the
    condition, and a second copy of a rule drifts from the first. S21 shipped
    with a docstring, a commit message and a reflex comment all describing a
    third condition its code never had -- nothing caught it, because the tests
    encoded the code rather than the rule. One function, one caller each side.

    Transient failures are retried, but only `TRANSIENT_RETRY_CAP` times.
    Retrying them forever would rebuild the exact problem the tip-keyed hold
    was written to stop: on 2026-07-28 unbounded retries wrote 915 FLAG lines
    across 24 branches, the same 21 strings every five minutes, while nothing
    merged. A permanently-recurring transient is no longer transient, and the
    honest thing to do with it is stop guessing and name a human -- which
    `flag` already does at the same count.
    """
    if not (memo.get("tip") and memo["tip"] == tip):
        return False
    if base is not None and memo.get("base", "") != base:
        return False                      # the base moved, or was never recorded
    if not is_transient(memo.get("reason", "")):
        return True
    try:
        attempts = int(memo.get("attempts", "0"))
    except ValueError:
        attempts = 0
    return attempts >= TRANSIENT_RETRY_CAP


def flag_branch(path):
    """The branch a flag file is about, read out of its own header.

    `last_attempt` goes branch -> file; sweeping the directory needs the other
    direction, and the header has carried `branch:` since `flag` first wrote
    it. Deriving it from the filename instead would mean undoing the
    `/` -> `_` substitution, which is not injective: a branch legitimately
    containing an underscore would come back as a different branch.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("```"):
                    break
                if line.startswith("branch:"):
                    return line.partition(":")[2].strip()
    except OSError:
        return ""
    return ""


def sweep_stale_flags(todo):
    """Retire flags for branches that merged by some route other than this one.

    `clear_flag` is only reachable from `try_merge`'s success path, and
    `unmerged_branches` drops everything already an ancestor of origin/master.
    Between them, a branch that merged **any other way** -- merged into a
    sibling agent branch that then merged, or merged by hand -- keeps its flag
    for good, because `try_merge` is never called on it again to clear it.

    `agent/e9-engine-paper-table` did exactly that on 2026-07-29: it reached
    master via `3e6d47be`, and hours later its flag was still being counted
    among the "verify gate red" branches holding up the queue, describing a
    disagreement in a merged tree that no longer exists.

    This is the failure `clear_flag`'s own docstring names -- a stale flag is
    not noise, it is the loudest evidence in the directory and it is *wrong* --
    coming back through the one path the original fix did not cover.

    Deliberately narrow: it clears only flags whose branch is **provably** an
    ancestor of origin/master. A branch that merely vanished (deleted, renamed,
    never pushed) keeps its flag, because "I cannot resolve this" and "this is
    finished" are different facts and only one of them is safe to act on.
    """
    waiting, retired = set(todo), []
    for name in sorted(os.listdir(CI_DIR)) if os.path.isdir(CI_DIR) else []:
        if not (name.startswith("CONFLICT-") and name.endswith(".md")):
            continue
        branch = flag_branch(os.path.join(CI_DIR, name))
        if not branch or branch in waiting:
            continue
        if sh(["git", "rev-parse", "--verify", "--quiet",
               branch]).returncode != 0:
            continue                      # unresolvable is not the same as done
        if sh(["git", "merge-base", "--is-ancestor",
               branch, "origin/master"]).returncode != 0:
            continue
        clear_flag(branch)
        retired.append(branch)
    if retired:
        log_line("SWEEP-FLAGS retired %d stale flag(s): %s"
                 % (len(retired), ", ".join(retired)))
    return retired


#: Lines worth surfacing out of a long gate transcript.
_CAUSE = re.compile(
    r"(FAILED|^E\s|Traceback|Error:|error:|assert |FAIL\b|"
    r"ModuleNotFound|No such file|exited \d|red in )", re.M)

#: How much of the transcript the flag keeps.
_KEEP_TAIL = 2600
_KEEP_CAUSE = 24


def excerpt(detail):
    """Keep the *cause*, not merely the end.

    This was `detail[-4000:]`, and for a verbose gate the last 4000 characters
    are the part after the failure -- so `r2-release-licence`'s flag is a wall
    of `-- ok` notes ending in `VERIFY: RED`, with nothing anywhere in it that
    says which step failed. The flag existed, was written every five minutes
    for nineteen hours, and could not be acted on.

    That is the same shape as the rest of this file's subject, one level up:
    the instrument ran, produced output, and the output omitted the finding.
    A record that cannot be acted on is not much better than no record, and it
    is worse in one way -- it looks like one.

    So the lines that name a cause are lifted to the top, and the tail is kept
    after them for context.
    """
    if not detail:
        return ""
    lines = detail.splitlines()
    causes = [l for l in lines if _CAUSE.search(l)]
    tail = detail[-_KEEP_TAIL:]
    if not causes:
        return tail
    picked = causes[:_KEEP_CAUSE]
    head = "\n".join(l[:300] for l in picked)
    more = ("\n... and %d more cause line(s)" % (len(causes) - len(picked))
            if len(causes) > len(picked) else "")
    return ("--- cause lines (lifted out of the transcript) ---\n%s%s\n"
            "--- tail of the transcript ---\n%s" % (head, more, tail))


def flag(branch, reason, detail, tip=None):
    """Record a failure, keeping how long it has been failing and on what tip.

    `tip` is the branch SHA the failure belongs to.  Without it every run
    re-attempted every stuck branch and wrote the same line again: on the night
    of 2026-07-28 that produced 915 FLAG lines over 24 branches, the same 21
    strings every five minutes, while `MERGED` sat unchanged for hours.  A
    failure that cannot change is not news the twentieth time, and printing it
    anyway is what made a stalled queue look like a working one.

    Keeping `first_seen` and `attempts` is the other half: the eighth failure
    and the first were indistinguishable in the log, so nothing -- no probe, no
    reader -- could react to a branch having been stuck for two hours.
    """
    os.makedirs(CI_DIR, exist_ok=True)
    prev = last_attempt(branch)
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    # S43: the carry-forward did not compare `reason`, so a branch that failed
    # three unrelated ways in a row accumulated one counter across all of them.
    # `a3-campaign-devpile` wore `NEEDS-HUMAN: 28 attempts since 07-29T04:14`
    # built out of "tests red in theoria-arm", then "verify gate red in
    # theoria-arm", then "verify gate red in monitor" -- and that badge, which
    # reads as "chronically broken branch", is why it was written off. A new
    # failure is news; it must not inherit the sentence passed on an old one.
    if prev.get("reason") and prev.get("reason") != reason:
        prev = {}
    first_seen = prev.get("first_seen") or stamp
    try:
        attempts = int(prev.get("attempts", "0")) + 1
    except ValueError:
        attempts = 1
    path = flag_path(branch)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# %s\nbranch: %s\nreason: %s\ntip: %s\nbase: %s\n"
                 "first_seen: %s\nlast_seen: %s\nattempts: %s\n\n```\n%s\n```\n"
                 % (os.path.basename(path), branch, reason, tip or "",
                    branch_tip("origin/master"),
                    first_seen, stamp, attempts, excerpt(detail)))
    suffix = ""
    if attempts >= 3:
        # Three distinct tips have failed the same way.  Retrying is no longer
        # the useful act; naming it for a human is.
        suffix = "  [NEEDS-HUMAN: %d attempts since %s]" % (attempts, first_seen)
    log_line("FLAG %s: %s%s" % (branch, reason, suffix))


def clear_flag(branch):
    """Retire a branch's flag once that branch has merged.

    A flag was written on failure and then left behind for good, so `ci_merge`
    accumulated verdicts about branches that had since merged -- 13 of 24 at
    one point (OPS-M cycle 10).  Two of those ghosts were still displaying the
    eaten-backslash bash error four hours after that bug was fixed, which is
    the part that matters: a stale flag is not merely noise, it is the loudest
    evidence in the directory and it is *wrong*.  Anyone triaging reads the
    biggest, angriest file first and starts debugging something that no longer
    exists.  All 13 had been merged by this very function, so clearing it here
    is where the knowledge already is.

    Moved rather than deleted: the failure did happen, and what it said is
    worth keeping.  The stamp is so a branch that failed, merged, and failed
    again does not overwrite its own history.
    """
    path = flag_path(branch)
    if not os.path.exists(path):
        return
    archive = os.path.join(CI_DIR, "archive")
    os.makedirs(archive, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    stem = os.path.join(archive,
                        "%s.%s" % (os.path.basename(path)[:-len(".md")], stamp))
    # A second's resolution is not uniqueness: two clears inside the same
    # second gave the same name and `os.replace` overwrote the first one
    # silently -- which is the thing this function exists to stop.
    dest, n = stem + ".md", 1
    while os.path.exists(dest):
        n += 1
        dest = "%s-%d.md" % (stem, n)
    try:
        os.replace(path, dest)
    except OSError:
        # Never fail a merge that already succeeded over its own bookkeeping.
        return
    log_line("CLEARED flag for %s (merged)" % branch)


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


def board_territories():
    """工作板自己签发过的领地。

    W-1641 量出来的代价（2026-07-29）：`fleet-study` 是**板签发的**
    （S17 条目自带 `territory: fleet-study`），而合并机器人有另一份手工白名单，
    两份定义只在分支推上来时才对账——对不上就是 **6 小时 37 分、63 次同一句
    FLAG**，而条目持有者在这期间因会话额度死了，没人知道交付卡住了。

    这与 `gates.py` 开头那条教训是同一个：一张手工表是一个关于树的声称，
    而没有任何东西拿它去对树；`gates.py` 的答案是「去问树」，这里的答案是
    「去问板」。板是「什么算领地」的权威，合并机器人不该再存一份平行定义。"""
    out = set()
    try:
        sys.path.insert(0, HERE)
        import board as _board
        for d in (_board.ITEMS, _board.CLAIMED, _board.DONE):
            if not os.path.isdir(d):
                continue
            for f in os.listdir(d):
                if f.endswith(".md"):
                    t = _board.meta(os.path.join(d, f)).get("territory")
                    if t and t != "?":
                        out.add(t)
    except Exception:
        pass
    return out


def try_merge(branch):
    tip = branch_tip(branch)
    dirs = touched_dirs(branch)
    known = KNOWN_DIRS | board_territories()
    unknown = {d for d in dirs
               if d not in known
               and "." not in d and d != "PARTNER_SYNC.md"}
    root_files = {d for d in dirs if "." in d}
    bad_root = root_files - {"PARTNER_SYNC.md", "README.md", ".gitignore",
                             ".gitattributes"}
    if bad_root & {".env", "Theoria.md", "CLAUDE.md", "LICENSE"} or \
            (bad_root and any(f in ("piles.json",) for f in bad_root)):
        flag(branch, "touches protected root files", str(sorted(bad_root)), tip=tip)
        return False
    if unknown:
        flag(branch, "touches unknown territory (needs M-0 judgment)",
             str(sorted(unknown)), tip=tip)
        return False

    wt = tempfile.mkdtemp(prefix="ci-merge-")
    try:
        r = sh(["git", "worktree", "add", "--detach", wt, "origin/master"])
        if r.returncode != 0:
            flag(branch, "worktree add failed", r.stderr, tip=tip)
            return False
        r = sh(["git", "merge", "--no-ff", "--no-edit", branch], cwd=wt)
        if r.returncode != 0:
            sh(["git", "merge", "--abort"], cwd=wt)
            flag(branch, "merge conflict", r.stdout + r.stderr, tip=tip)
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
            # A gate runs at its own territory with the merged tree's root
            # importable -- see gates.gate_env. Without it a verify.py that
            # imports its own package dies before the gate runs, and that is
            # recorded as the territory failing its check rather than as the
            # runner never having said where a gate runs from.
            r = sh(cmd, cwd=os.path.join(wt, d), timeout=1800,
                   extra_env=gates.gate_env(wt))
            if row["kind"] == "verify" and r.returncode != 0:
                reason = "verify gate red in %s (%s)" % (d, row["name"])
                if not blame_the_base(branch, wt, d, row, reason,
                                      r.stdout + r.stderr, tip):
                    flag(branch, reason, r.stdout + r.stderr, tip=tip)
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
                     r.stdout + r.stderr, tip=tip)
                return False
            if r.returncode != 0:
                reason = "tests red in %s" % d
                if not blame_the_base(branch, wt, d, row, reason,
                                      r.stdout + r.stderr, tip):
                    flag(branch, reason, (r.stdout + r.stderr), tip=tip)
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
            flag(branch, "push rejected (race?)", r.stderr, tip=tip)
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
        # The branch merged, so whatever this rig said about it last time is
        # now a statement about the past.  Retired here rather than left for a
        # human to sweep, which is how it accumulated in the first place.
        clear_flag(branch)
        return True
    finally:
        sh(["git", "worktree", "remove", "--force", wt])


def starved_first(branches):
    """Longest-waiting first, never-tried before that.

    `unmerged_branches()` returns git's order, which is alphabetical, and the
    loop below stops after `--max` successful merges. So a branch late in the
    alphabet is only ever reached on a tick where fewer than `--max` earlier
    branches succeed -- and when the queue is jammed at the front, never.

    Measured, not theorised: `v5-battery-freeze` was last attempted at 01:36
    and was still sitting unattempted 40 minutes and four ticks later, while
    the rig merged other branches each time. Its actual blocker had already
    been fixed hours earlier; nothing retried it to find out.

    Ordering by wait makes the queue fair without a scheduler: a branch that
    has just been pushed goes first (nothing is known about it yet), then the
    one that has been waiting longest. It is the same quantity this repo's
    merge-queue probe reports as its headline, for the same reason -- it only
    improves when something is really resolved.
    """
    try:
        import mergequeue
        first, _last, _merged = mergequeue.read_log()
    except Exception:
        # Never let the ordering heuristic stop a merge run: unordered merging
        # is the old behaviour, which is worse but not broken.
        return list(branches)
    return sorted(branches, key=lambda b: first.get(b, (0.0, ""))[0])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max", type=int, default=2)
    args = ap.parse_args()
    # Every way this run can merge nothing now leaves a line in merge.log.
    # All three were a bare `print` to a console nobody reads followed by exit
    # 0, so "stood down for eight hours", "nothing was waiting" and "merged
    # everything cleanly" were the same observation from outside.  Standing
    # down is correct behaviour and stays exit 0 -- it just stops being
    # invisible, which is the same argument S13 made for UNGATED.
    if m0_alive():
        log_line("STOOD DOWN: an M-0 session is alive; merged nothing")
        return 0
    if args.dry_run:
        # Asked *before* unmerged_branches(), which opens with `git fetch`.  A
        # --dry-run that goes to the network is not a dry run, and it is why
        # this command cannot serve as anyone's completion gate.
        print("delivered, unmerged:", unmerged_branches() or "none")
        return 0
    todo = starved_first(unmerged_branches())
    # Before deciding anything, drop verdicts about branches that are already
    # in master. They cost nothing to keep and everything to read: triage
    # starts at the biggest, angriest file in the directory.
    sweep_stale_flags(todo)
    if not todo:
        log_line("IDLE: no delivered branch was waiting")
        return 0
    if not take_lock():
        log_line("BLOCKED: another merge holds the lock; merged nothing")
        return 0
    try:
        done = 0
        held = []
        for b in todo:
            if done >= args.max:
                break
            # A branch whose tip has not moved since its last failure will fail
            # the same way again.  Re-running it costs a worktree and a full
            # test suite to re-derive a verdict already on disk, and -- worse --
            # writes the identical FLAG line again, which is how 24 stuck
            # branches produced 915 of them while nothing merged for hours.
            #
            # The condition is deliberately on the *tip*, not on the branch: a
            # push of new work is exactly the event that makes the old verdict
            # stale, and that retries immediately.  Skipping is therefore never
            # a way for a fixed branch to stay stuck.
            memo = last_attempt(b)
            # `should_hold` is the one copy of this rule -- it subsumes the
            # inline tip-and-not-transient test that used to stand here, and
            # adds the base check and the retry cap.  The tests call the same
            # function, so the two cannot drift.
            if should_hold(memo, branch_tip(b), branch_tip("origin/master")):
                held.append((b, memo.get("reason", "?"),
                             memo.get("attempts", "?")))
                continue
            if try_merge(b):
                done += 1
        if held:
            # One line for the whole held set, so the log's growth tracks
            # progress rather than the passage of time.
            log_line("HELD %d unchanged since last verdict: %s"
                     % (len(held),
                        "; ".join("%s (%s, %sx)"
                                  % (b.replace("origin/agent/", ""), r, n)
                                  for b, r, n in held[:8])))
        # keep local master in step with origin so later merges see reality
        sh(["git", "pull", "--ff-only", "origin", "master"])
        return 0
    finally:
        release_lock()


if __name__ == "__main__":
    raise SystemExit(main())
