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


def _held(branch, tip):
    """The condition main() uses, isolated so both tests exercise one thing."""
    memo = ci_merge.last_attempt(branch)
    return bool(memo.get("tip")) and memo["tip"] == tip


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
