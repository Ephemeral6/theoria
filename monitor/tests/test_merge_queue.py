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
                                  "branch": "origin/agent/x1-thing"}])
    r = mergequeue.probe()
    assert r["status"] == "risk", r
    assert "X1-thing" in r["detail"]


def test_the_probe_is_registered_in_scan():
    import scan
    assert "merge_queue" in scan.PROBES
