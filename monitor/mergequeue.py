"""What is stuck in the merge queue, and for how long.

    python monitor/mergequeue.py
    python monitor/mergequeue.py --json

Twenty-one probes watched this repository and not one of them read
`monitor/ci/merge.log`. Five delivered branches were re-flagged every ten
minutes from 2026-07-28 15:22 and sat there for ten hours while the dashboard
showed nothing, because a branch that fails to merge produces no signal anywhere
a human looks -- the flag file is written, overwritten, and read by no one.

## The headline number is the longest wait, not the count

The count moves with merge activity and can fall while nothing is fixed: merge
two easy branches and the queue shortens without the stuck one moving. **The
oldest blockage only goes down when it is actually resolved**, so that is the
number this reports first. A metric that improves for reasons unrelated to the
problem trains people to stop reading it.

## The second question: does `done` mean what it says

The board records an item as `done` when its branch is pushed. Merging is a
separate machine. When merging jams, `board/done/` keeps filling and the score
computed from it keeps rising while `master` gains nothing -- an audit on
2026-07-29 measured 11.5 percentage points of overstatement from exactly this.

So this also asks the tree: for each delivered item, do the files its branch
claims to add exist on `origin/master`? A `done` whose artefacts are not on the
mainline is not a lie, but it is a different claim than the one the board is
making, and the difference has to be visible.
"""

import argparse
import json
import os
import re
import subprocess
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CI_DIR = os.path.join(HERE, "ci")
LOG = os.path.join(CI_DIR, "merge.log")

#: Above this, a blocked branch has stopped being "in progress" and has become
#: a thing nobody is looking at. Two hours is roughly twelve reflex ticks.
STUCK_RISK_MIN = 120
STUCK_PARTIAL_MIN = 30

_FLAG = re.compile(r"^(\S+) FLAG (\S+): (.*)$")
_MERGED = re.compile(r"^(\S+) MERGED (\S+)")


def _stamp(text):
    try:
        return time.mktime(time.strptime(text, "%Y-%m-%dT%H:%M:%SZ")) - time.timezone
    except ValueError:
        return None


def read_log(path=None):
    """First and last FLAG per branch, and which branches later merged.

    `path` is resolved in the body, not bound as a default. A default evaluated
    at import cannot be redirected afterwards, so every caller silently reads
    the real log however it was asked -- which in a test means the assertions
    are about production data and pass or fail for the wrong reasons. Three
    separate modules in this repository have carried that shape
    (`proxy.scoring.score_run`'s scores_dir, `reap_worktrees.classify`'s root,
    and this one, written after finding the other two).
    """
    path = path or LOG
    first, last, merged = {}, {}, set()
    if not os.path.exists(path):
        return first, last, merged
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.rstrip("\n")
            m = _FLAG.match(line)
            if m:
                when, branch, reason = m.group(1), m.group(2), m.group(3)
                t = _stamp(when)
                if t is None:
                    continue
                first.setdefault(branch, (t, reason))
                last[branch] = (t, reason)
                continue
            m = _MERGED.match(line)
            if m:
                merged.add(m.group(2))
    return first, last, merged


def unmerged_branches():
    """Branches git still considers unmerged -- the authority, not the log.

    The log says what the rig *tried*; only git says what is still outstanding.
    Reading the log alone would keep reporting a branch that someone merged by
    hand, and a probe that cries about solved problems gets muted.
    """
    def sh(*a):
        return subprocess.run(list(a), cwd=ROOT, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
    out = sh("git", "branch", "-r", "--list", "origin/agent/*",
             "--format=%(refname:short)").stdout.split()
    todo = []
    for b in out:
        if sh("git", "merge-base", "--is-ancestor", b, "origin/master").returncode != 0:
            todo.append(b)
    return todo


def survey(now=None):
    now = now or time.time()
    first, last, merged = read_log()
    live = set(unmerged_branches())
    rows = []
    for branch in sorted(live):
        f = first.get(branch)
        l = last.get(branch)
        if not f:
            rows.append({"branch": branch, "reason": None, "stuck_min": None,
                         "attempts_since": None,
                         "note": "unmerged and never flagged -- not yet tried"})
            continue
        rows.append({"branch": branch,
                     "reason": l[1],
                     "first_flagged": f[0],
                     "stuck_min": round((now - f[0]) / 60, 1),
                     "note": ""})
    stuck = [r for r in rows if r["stuck_min"] is not None]
    oldest = max((r["stuck_min"] for r in stuck), default=0.0)
    by_reason = {}
    for r in stuck:
        key = re.sub(r"\s*\(.*\)$", "", r["reason"] or "?")
        by_reason[key] = by_reason.get(key, 0) + 1
    return {"rows": rows, "unmerged": len(rows), "blocked": len(stuck),
            "oldest_stuck_min": oldest, "by_reason": by_reason,
            "merged_ever": len(merged)}


def unpushed_branches():
    """Local agent branches with no counterpart on the remote, not yet on master.

    `unmerged_branches()` enumerates `origin/agent/*`, so it can only ever see a
    branch that reached the remote.  A branch that was never pushed is not
    "waiting in the queue" -- it is not in the queue at all, and every probe
    that reads the queue reports it as fine.  That is the strictly worse
    failure, and it is the one the queue is structurally blind to.

    Found the hard way: S16-silent-failure-hunt sat `done` on the board for
    hours with its branch existing only in this checkout.  The board said
    delivered, the merge log said nothing was waiting, and both were telling
    the truth.
    """
    def sh(*a):
        return subprocess.run(list(a), cwd=ROOT, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
    local = sh("git", "for-each-ref", "--format=%(refname:short)",
               "refs/heads/agent").stdout.split()
    remote = set(sh("git", "branch", "-r", "--list", "origin/agent/*",
                    "--format=%(refname:short)").stdout.split())
    todo = []
    for b in local:
        if "origin/" + b in remote:
            continue                      # pushed; unmerged_branches() owns it
        # No remote ref can mean two opposite things: never pushed, or merged
        # and the remote branch deleted.  Only git can tell them apart.
        if sh("git", "merge-base", "--is-ancestor", b,
              "origin/master").returncode != 0:
            todo.append(b)
    return todo


def done_not_on_master():
    """Board items marked done whose branch is not on master.

    The board's `done` means "pushed", and merging is a different machine. When
    the two diverge the score keeps climbing while master gains nothing.

    Two ways to diverge, and they are not equally bad.  `queued` is the branch
    the merge robot is chewing on; `unpushed` never reached the robot, so no
    amount of waiting will fix it and no other probe will mention it.
    """
    done_dir = os.path.join(HERE, "board", "done")
    if not os.path.isdir(done_dir):
        return []
    # An item id maps to its branch by the fleet's own naming rule.
    short = {b.replace("origin/agent/", ""): (b, "queued")
             for b in unmerged_branches()}
    for b in unpushed_branches():
        short.setdefault(b.replace("agent/", ""), (b, "unpushed"))
    out = []
    for name in sorted(os.listdir(done_dir)):
        if not name.endswith(".md"):
            continue
        iid = name[:-3].split(".")[0]
        slug = iid.lower()
        if slug in short:
            branch, state = short[slug]
            out.append({"item": iid, "branch": branch, "state": state})
    return out


def probe():
    """scan.py probe entry point."""
    s = survey()
    gap = done_not_on_master()
    bits = []
    if gap:
        bits.append("**%d 件板上已 done、分支却还没进 master**：%s"
                    % (len(gap), "、".join(g["item"] for g in gap[:5])))
    # Called out separately: these are not slow, they are absent.  Folding them
    # into the count above would let them wait behind a queue they never joined.
    never = [g for g in gap if g["state"] == "unpushed"]
    if never:
        bits.append("其中 **%d 件根本没推上远端**（不是排队慢，是不在队里）：%s"
                    % (len(never), "、".join(g["item"] for g in never[:5])))
    if s["blocked"]:
        reasons = "；".join("%s×%d" % (k, v)
                            for k, v in sorted(s["by_reason"].items(),
                                               key=lambda kv: -kv[1])[:4])
        head = ("**合并队列最久的一条卡了 %.0f 分钟**（%d 条待合、%d 条被 flag）：%s"
                % (s["oldest_stuck_min"], s["unmerged"], s["blocked"], reasons))
    else:
        head = "合并队列：%d 条待合，无一被 flag" % s["unmerged"]
    detail = "。".join([head] + bits) + "。"
    if s["oldest_stuck_min"] >= STUCK_RISK_MIN or gap:
        return {"status": "risk", "detail": detail}
    if s["oldest_stuck_min"] >= STUCK_PARTIAL_MIN:
        return {"status": "partial", "detail": detail}
    return {"status": "green", "detail": detail}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    s = survey()
    gap = done_not_on_master()
    if args.json:
        print(json.dumps({"survey": s, "done_not_on_master": gap},
                         indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    print("oldest blockage: %.0f min   unmerged: %d   flagged: %d"
          % (s["oldest_stuck_min"], s["unmerged"], s["blocked"]))
    for k, v in sorted(s["by_reason"].items(), key=lambda kv: -kv[1]):
        print("  %-3d %s" % (v, k))
    for r in sorted((r for r in s["rows"] if r["stuck_min"]),
                    key=lambda r: -r["stuck_min"])[:10]:
        print("  %6.0f min  %-46s %s"
              % (r["stuck_min"], r["branch"], (r["reason"] or "")[:50]))
    if gap:
        print("\ndone on the board, absent from master (%d):" % len(gap))
        for g in gap:
            print("  %-34s %-46s %s" % (g["item"], g["branch"], g["state"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
