"""The merge bot must stop re-deriving a verdict it already has -- and must
stop holding the moment the branch moves.

Both halves are here on purpose.  A hold that never releases is the failure
this repo has hit twice already (a quota that only entered `hold`, a probe that
could only ever say `partial`), so the second test is the negative sample S20
requires: it fails if `last_attempt`/`flag` ever start ignoring the tip.
"""

import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
MONITOR = os.path.dirname(HERE)
if MONITOR not in sys.path:
    sys.path.insert(0, MONITOR)

import ci_merge                                                     # noqa: E402


@pytest.fixture
def ci_dir(tmp_path, monkeypatch):
    d = tmp_path / "ci"
    d.mkdir()
    monkeypatch.setattr(ci_merge, "CI_DIR", str(d))
    monkeypatch.setattr(ci_merge, "LOG", str(d / "merge.log"))
    return d


def _held(branch, tip, base=None):
    """The condition main() uses -- now *the* condition, not a copy of it.

    This used to restate the rule inline, which meant main() and the tests
    could drift apart silently. S21 shipped exactly that way: a docstring, a
    commit message and a reflex comment all describing a third condition the
    code never had, with ten tests encoding the code instead of the rule.
    `should_hold` is the single copy; both sides call it.
    """
    return ci_merge.should_hold(ci_merge.last_attempt(branch), tip,
                                base if base is not None
                                else ci_merge.branch_tip("origin/master"))


def test_a_flag_records_the_tip_and_counts_attempts(ci_dir):
    b = "origin/agent/x-demo"
    ci_merge.flag(b, "merge conflict", "detail", tip="aaa111")
    memo = ci_merge.last_attempt(b)
    assert memo["tip"] == "aaa111"
    assert memo["reason"] == "merge conflict"
    assert memo["attempts"] == "1"
    assert memo["first_seen"] == memo["last_seen"]

    # A second failure on a *new* tip keeps first_seen and advances the count,
    # which is what lets a reader see "stuck for two hours" rather than "failed".
    ci_merge.flag(b, "merge conflict", "detail", tip="bbb222")
    memo2 = ci_merge.last_attempt(b)
    assert memo2["attempts"] == "2"
    assert memo2["first_seen"] == memo["first_seen"]
    assert memo2["tip"] == "bbb222"


def test_an_unchanged_branch_is_held(ci_dir):
    b = "origin/agent/x-stuck"
    ci_merge.flag(b, "tests red in engine-rig", "boom", tip="cafe01")
    assert _held(b, "cafe01") is True


def test_a_moved_branch_is_not_held(ci_dir):
    """The negative sample: the hold must release on a push.

    If this ever passes with the branch still held, the bot has become a door
    that only opens inward -- a delivered fix would sit behind a verdict about
    code that no longer exists.
    """
    b = "origin/agent/x-fixed"
    ci_merge.flag(b, "verify gate red in monitor (verify.sh)", "boom",
                  tip="cafe01")
    assert _held(b, "cafe01") is True          # still stuck on the old tip
    assert _held(b, "d00d02") is False         # author pushed: must retry


def test_a_branch_never_flagged_is_not_held(ci_dir):
    assert _held("origin/agent/x-new", "anything") is False


def test_three_attempts_name_a_human_in_the_log(ci_dir):
    b = "origin/agent/x-loop"
    for tip in ("t1", "t2", "t3"):
        ci_merge.flag(b, "merge conflict", "detail", tip=tip)
    log = (ci_dir / "merge.log").read_text(encoding="utf-8")
    assert "NEEDS-HUMAN" in log.splitlines()[-1]
    # ...and not before, or every transient failure would page someone.
    assert "NEEDS-HUMAN" not in log.splitlines()[0]


# ---------------------------------------- transient failures must not be held

def test_a_push_race_is_retried_even_though_the_tip_never_moved(ci_dir):
    """The deadlock with no exit.

    The hold is keyed on the tip, on the reasoning that a push of new work is
    what makes an old verdict stale. That is right for a verdict *about the
    branch* -- a merge conflict, a red gate. A lost push race is not about the
    branch, so nothing about the branch can ever clear it, and the hold waits
    for a push that has no reason to come.

    Measured 2026-07-29: c10-unsolvable-proof-canon lost a push race on tip
    984f7b11, which never moved, and was printed in HELD every five minutes
    for 5 h 53 min with zero retries. It merged the moment something re-ran it.
    """
    b = "origin/agent/c10-unsolvable-proof-canon"
    ci_merge.flag(b, "push rejected (race?)", "rejected", tip="984f7b11")
    assert not _held(b, "984f7b11"), "a push race held on an unchanged tip"


def test_a_failed_worktree_add_is_retried(ci_dir):
    b = "origin/agent/x"
    ci_merge.flag(b, "worktree add failed", "disk", tip="aaa111")
    assert not _held(b, "aaa111")


def test_a_timeout_is_retried(ci_dir):
    b = "origin/agent/x"
    ci_merge.flag(b, "verify gate timed out in engine-rig", "slow", tip="aaa111")
    assert not _held(b, "aaa111")


def test_a_red_gate_is_still_held(ci_dir):
    """The negative sample. Retrying a real verdict on an unchanged tip is what
    produced 915 FLAG lines over 24 branches while nothing merged."""
    b = "origin/agent/e15-solver-status-bit"
    ci_merge.flag(b, "verify gate red in engine-rig (verify.py)", "boom",
                  tip="d2b75c26")
    assert _held(b, "d2b75c26")


def test_a_merge_conflict_is_still_held(ci_dir):
    b = "origin/agent/p10-figures-into-paper"
    ci_merge.flag(b, "merge conflict", "conflict", tip="aaa111")
    assert _held(b, "aaa111")


def test_protected_root_files_is_still_held(ci_dir):
    b = "origin/agent/s11-sealed-halfguard"
    ci_merge.flag(b, "touches protected root files", "root", tip="aaa111")
    assert _held(b, "aaa111")


# ------------------------------ a verdict is about the MERGED tree, not the tip

def test_a_verdict_is_dropped_when_the_base_moves(ci_dir):
    """p13-figure-numbering, exactly.

    Its red came from a coverage probe in `figures/`. Master cured that probe
    at 05:15Z. The branch never moved, so the tip-keyed hold kept the verdict
    alive and the flag still read "verify gate red in figures" six hours later
    with zero retries -- while the tree it described no longer existed.

    A gate runs on origin/master merged with the branch. Both halves have to be
    unchanged for the old answer to still be the answer.
    """
    b = "origin/agent/p13-figure-numbering"
    ci_merge.flag(b, "verify gate red in figures (verify.sh)", "boom",
                  tip="72730d5b")
    assert _held(b, "72730d5b"), "unchanged base should still hold"
    assert not _held(b, "72730d5b", base="master-moved-since"), \
        "the base moved and the verdict was kept anyway"


def test_a_flag_written_before_base_existed_is_retried_not_skipped(ci_dir):
    """Old flags have no `base:`. Unknown must read as "retry": one wasted
    re-run each, once, versus keeping the failure mode above."""
    b = "origin/agent/legacy"
    path = ci_merge.flag_path(b)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# x\nbranch: %s\nreason: merge conflict\ntip: aaa111\n"
                 "first_seen: t\nlast_seen: t\nattempts: 1\n\n```\nd\n```\n" % b)
    assert not _held(b, "aaa111", base="anything")


def test_the_base_is_recorded_in_the_flag_header(ci_dir):
    b = "origin/agent/x"
    ci_merge.flag(b, "merge conflict", "detail", tip="aaa111")
    assert ci_merge.last_attempt(b).get("base") == \
        ci_merge.branch_tip("origin/master")
