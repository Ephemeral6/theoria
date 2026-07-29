"""Injection self-test for the merge-queue probe, including the negative sample.

S25's fourth item asks for a branch that must jam, and an assertion that the
probe reports it *and* that the wait is growing. That last half is the one
worth insisting on: a probe that notices a jam but whose number drifts down
while the jam persists is worse than none, because it reads as progress.

The count of blocked branches does exactly that -- merge two easy branches and
it falls while the stuck one has not moved. Which is why the headline is the
oldest wait, and why the test below advances a clock and requires the number
to go up.
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import mergequeue                                               # noqa: E402


def _log(tmp_path, lines):
    p = tmp_path / "merge.log"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(p)


FLAG = "%s FLAG origin/agent/%s: %s"


def test_a_branch_that_keeps_failing_is_reported_and_its_wait_grows(
        tmp_path, monkeypatch):
    """The negative sample: a branch that will never merge on its own."""
    path = _log(tmp_path, [
        FLAG % ("2026-07-29T00:00:00Z", "jammed", "merge conflict"),
        FLAG % ("2026-07-29T00:10:00Z", "jammed", "merge conflict"),
        FLAG % ("2026-07-29T00:20:00Z", "jammed", "merge conflict"),
    ])
    monkeypatch.setattr(mergequeue, "LOG", path)
    monkeypatch.setattr(mergequeue, "unmerged_branches",
                        lambda: ["origin/agent/jammed"])

    first = mergequeue._stamp("2026-07-29T00:00:00Z")
    early = mergequeue.survey(now=first + 30 * 60)
    later = mergequeue.survey(now=first + 300 * 60)

    assert early["blocked"] == 1
    assert round(early["oldest_stuck_min"]) == 30
    assert round(later["oldest_stuck_min"]) == 300
    assert later["oldest_stuck_min"] > early["oldest_stuck_min"], (
        "the headline number must rise while the jam persists")


def test_the_headline_does_not_fall_when_an_easy_branch_merges(
        tmp_path, monkeypatch):
    """Why the count is not the headline.

    Clearing an unrelated branch shortens the queue without touching the stuck
    one. A metric that improves for reasons unrelated to the problem stops
    being read.
    """
    path = _log(tmp_path, [
        FLAG % ("2026-07-29T00:00:00Z", "jammed", "merge conflict"),
        FLAG % ("2026-07-29T00:05:00Z", "easy", "tests red in x"),
    ])
    monkeypatch.setattr(mergequeue, "LOG", path)
    t0 = mergequeue._stamp("2026-07-29T00:00:00Z") + 200 * 60

    monkeypatch.setattr(mergequeue, "unmerged_branches",
                        lambda: ["origin/agent/jammed", "origin/agent/easy"])
    before = mergequeue.survey(now=t0)
    monkeypatch.setattr(mergequeue, "unmerged_branches",
                        lambda: ["origin/agent/jammed"])
    after = mergequeue.survey(now=t0)

    assert after["blocked"] < before["blocked"], "the count fell"
    assert after["oldest_stuck_min"] == before["oldest_stuck_min"], (
        "the headline must not move when the stuck branch did not")


def test_a_branch_that_merged_leaves_the_queue(tmp_path, monkeypatch):
    """git is the authority on what is outstanding, not the log.

    Reading the log alone would keep reporting a branch somebody merged by
    hand, and a probe that complains about solved problems gets muted.
    """
    path = _log(tmp_path, [
        FLAG % ("2026-07-29T00:00:00Z", "fixed", "merge conflict"),
        "2026-07-29T01:00:00Z MERGED origin/agent/fixed (dirs: x)",
    ])
    monkeypatch.setattr(mergequeue, "LOG", path)
    monkeypatch.setattr(mergequeue, "unmerged_branches", lambda: [])
    s = mergequeue.survey()
    assert s["blocked"] == 0 and s["unmerged"] == 0


def test_an_empty_queue_is_green_and_a_jam_is_risk(tmp_path, monkeypatch):
    path = _log(tmp_path, [])
    monkeypatch.setattr(mergequeue, "LOG", path)
    monkeypatch.setattr(mergequeue, "unmerged_branches", lambda: [])
    monkeypatch.setattr(mergequeue, "done_not_on_master", lambda: [])
    assert mergequeue.probe()["status"] == "green"

    path2 = _log(tmp_path, [FLAG % ("2026-01-01T00:00:00Z", "old",
                                    "merge conflict")])
    monkeypatch.setattr(mergequeue, "LOG", path2)
    monkeypatch.setattr(mergequeue, "unmerged_branches",
                        lambda: ["origin/agent/old"])
    r = mergequeue.probe()
    assert r["status"] == "risk", r
    assert "分钟" in r["detail"]


def test_an_unmerged_branch_never_tried_is_not_counted_as_stuck(
        tmp_path, monkeypatch):
    """Just pushed is not the same as jammed, and conflating them inflates the
    headline until nobody believes it."""
    monkeypatch.setattr(mergequeue, "LOG", _log(tmp_path, []))
    monkeypatch.setattr(mergequeue, "unmerged_branches",
                        lambda: ["origin/agent/brand-new"])
    s = mergequeue.survey()
    assert s["unmerged"] == 1 and s["blocked"] == 0
    assert "not yet tried" in s["rows"][0]["note"]


def test_a_missing_log_is_not_a_crash(tmp_path, monkeypatch):
    monkeypatch.setattr(mergequeue, "LOG", str(tmp_path / "nope.log"))
    monkeypatch.setattr(mergequeue, "unmerged_branches", lambda: [])
    monkeypatch.setattr(mergequeue, "done_not_on_master", lambda: [])
    assert mergequeue.probe()["status"] == "green"


def test_done_on_the_board_but_absent_from_master_is_risk(monkeypatch):
    """The 11.5-point overstatement, as a check.

    `done` means pushed; merging is a different machine. When they diverge the
    board keeps scoring work that master never received.
    """
    monkeypatch.setattr(mergequeue, "unmerged_branches", lambda: [])
    monkeypatch.setattr(mergequeue, "done_not_on_master",
                        lambda: [{"item": "X1-thing",
                                  "branch": "origin/agent/x1-thing",
                                  "state": "queued"}])
    r = mergequeue.probe()
    assert r["status"] == "risk", r
    assert "X1-thing" in r["detail"]
    # A queued branch must NOT be described as missing from the remote.
    assert "没推上远端" not in r["detail"], r


def test_a_done_item_that_was_never_pushed_is_named_as_such(monkeypatch):
    """The failure the merge queue cannot see by construction.

    S16-silent-failure-hunt was `done` on the board for hours while its branch
    existed only in one checkout. The queue reads `origin/agent/*`, so it
    reported nothing waiting -- truthfully. Being absent from the queue has to
    read louder than being slow in it, not quieter.
    """
    monkeypatch.setattr(mergequeue, "unmerged_branches", lambda: [])
    monkeypatch.setattr(mergequeue, "done_not_on_master",
                        lambda: [{"item": "S16-silent-failure-hunt",
                                  "branch": "agent/s16-silent-failure-hunt",
                                  "state": "unpushed"}])
    r = mergequeue.probe()
    assert r["status"] == "risk", r
    assert "S16-silent-failure-hunt" in r["detail"]
    assert "没推上远端" in r["detail"], r


def test_the_probe_is_registered_in_scan():
    import scan
    assert "merge_queue" in scan.PROBES


# --------------------------------------------------- the starvation ordering

def test_the_longest_waiting_branch_is_tried_first(tmp_path, monkeypatch):
    """Alphabetical order plus a --max cap starves the tail of the queue.

    v5-battery-freeze sat unattempted for 40 minutes across four ticks while
    the rig merged other branches each time, because it sorts last and the run
    stops after two successes. Its blocker had already been fixed; nothing
    retried it to find out.
    """
    import ci_merge
    path = _log(tmp_path, [
        FLAG % ("2026-07-29T00:00:00Z", "v5-last-alphabetically", "gate red"),
        FLAG % ("2026-07-29T01:00:00Z", "a1-first-alphabetically", "gate red"),
    ])
    monkeypatch.setattr(mergequeue, "LOG", path)
    order = ci_merge.starved_first(["origin/agent/a1-first-alphabetically",
                                    "origin/agent/v5-last-alphabetically"])
    assert order[0] == "origin/agent/v5-last-alphabetically", order


def test_a_never_tried_branch_goes_before_everything(tmp_path, monkeypatch):
    """Nothing is known about a fresh push, so it costs one attempt to find out."""
    import ci_merge
    path = _log(tmp_path, [FLAG % ("2026-07-29T00:00:00Z", "old", "gate red")])
    monkeypatch.setattr(mergequeue, "LOG", path)
    order = ci_merge.starved_first(["origin/agent/old", "origin/agent/fresh"])
    assert order[0] == "origin/agent/fresh", order


def test_ordering_never_stops_a_merge_run(monkeypatch):
    """If the heuristic breaks, merging continues unordered.

    Unordered merging is the old behaviour: worse, not broken. A scheduling
    nicety must never be able to take the merge rig down.
    """
    import ci_merge

    def boom(*_a, **_k):
        raise RuntimeError("log unreadable")

    monkeypatch.setattr(mergequeue, "read_log", boom)
    got = ci_merge.starved_first(["origin/agent/b", "origin/agent/a"])
    assert got == ["origin/agent/b", "origin/agent/a"]


# ------------------------------------------- the never-pushed branch, for real
#
# The probe test above monkeypatches `done_not_on_master`, so it proves the
# wording and nothing about the git logic underneath. This one builds an actual
# repository with an actual remote, because the discrimination that matters --
# "no remote ref because it was never pushed" versus "no remote ref because it
# merged and the robot deleted it" -- exists only in git, and getting it wrong
# in the safe direction (reporting merged work as missing) is how a probe earns
# its way into the muted pile.

import subprocess


def _git(repo, *a):
    r = subprocess.run(["git"] + list(a), cwd=repo, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0, (a, r.stdout, r.stderr)
    return r.stdout.strip()


def _repo_with_three_kinds_of_branch(tmp_path):
    """origin/master plus: one merged+deleted, one pushed, one never pushed."""
    remote = tmp_path / "remote.git"
    remote.mkdir()
    _git(remote, "init", "--bare", "-q", "-b", "master")
    work = tmp_path / "work"
    work.mkdir()
    _git(work, "init", "-q", "-b", "master")
    _git(work, "config", "user.email", "t@t")
    _git(work, "config", "user.name", "t")
    (work / "f").write_text("0\n", encoding="utf-8")
    _git(work, "add", "f")
    _git(work, "commit", "-qm", "base")
    _git(work, "remote", "add", "origin", str(remote))
    _git(work, "push", "-q", "origin", "master")

    def branch(name, text):
        _git(work, "checkout", "-q", "-b", "agent/" + name, "master")
        (work / name).write_text(text, encoding="utf-8")
        _git(work, "add", name)
        _git(work, "commit", "-qm", name)

    # (a) merged, remote branch deleted afterwards -- must NOT be reported
    branch("merged-and-gone", "a")
    _git(work, "checkout", "-q", "master")
    _git(work, "merge", "-q", "--no-ff", "-m", "m", "agent/merged-and-gone")
    _git(work, "push", "-q", "origin", "master")
    # (b) pushed and still unmerged -- belongs to unmerged_branches(), not here
    branch("pushed-waiting", "b")
    _git(work, "push", "-q", "origin", "agent/pushed-waiting")
    # (c) never pushed -- the S16 case
    branch("never-pushed", "c")
    _git(work, "checkout", "-q", "master")
    _git(work, "fetch", "-q", "origin")
    return str(work)


def test_unpushed_finds_the_branch_that_never_left_the_laptop(tmp_path,
                                                              monkeypatch):
    repo = _repo_with_three_kinds_of_branch(tmp_path)
    monkeypatch.setattr(mergequeue, "ROOT", repo)
    assert mergequeue.unpushed_branches() == ["agent/never-pushed"]


def test_a_merged_branch_whose_remote_was_deleted_is_not_reported(tmp_path,
                                                                  monkeypatch):
    """The false positive that would get this probe muted."""
    repo = _repo_with_three_kinds_of_branch(tmp_path)
    monkeypatch.setattr(mergequeue, "ROOT", repo)
    assert "agent/merged-and-gone" not in mergequeue.unpushed_branches()


def test_a_pushed_branch_is_left_to_the_queue_not_double_counted(tmp_path,
                                                                 monkeypatch):
    repo = _repo_with_three_kinds_of_branch(tmp_path)
    monkeypatch.setattr(mergequeue, "ROOT", repo)
    assert "agent/pushed-waiting" not in mergequeue.unpushed_branches()
    assert "origin/agent/pushed-waiting" in mergequeue.unmerged_branches()
