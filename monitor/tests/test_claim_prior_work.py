"""Claiming an item must say so when somebody has already worked it.

On 2026-07-29 S21 was implemented twice and S27 three times. Every duplicate
session found what looked like a clean item, and every time the evidence was
already on disk under a name derived from the item id. Nothing looked.

The interesting test here is the **negative** one. A warning that fires on every
claim is a warning nobody reads, and this warning sits at the end of a long item
body where fatigue is cheapest to acquire.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import board                                                    # noqa: E402


def _fake_git(monkeypatch, branches, ahead="3"):
    """Stand in for the two read-only git calls `prior_work` makes."""
    def fake(repo, *args):
        if args[0] == "branch":
            return branches
        if args[0] == "rev-list":
            return [ahead]
        return []
    monkeypatch.setattr(board, "_git", fake)


def _repo(tmp_path, worktrees=()):
    (tmp_path / ".worktrees").mkdir()
    for name in worktrees:
        (tmp_path / ".worktrees" / name).mkdir()
    return str(tmp_path)


# ------------------------------------------------------------ it does warn

def test_a_branch_named_after_the_item_is_reported(tmp_path, monkeypatch):
    _fake_git(monkeypatch, ["  agent/s21-app-session-death"], ahead="2")
    out = board.prior_work("S21-app-session-death", _repo(tmp_path))
    assert out, "a branch for this item exists and nothing was said"
    joined = "\n".join(out)
    assert "agent/s21-app-session-death" in joined
    assert "2" in joined, "the commit count is what says 'real work', not 'a stub'"
    assert "接续" in joined


def test_a_merged_branch_says_already_done_not_someone_is_working(tmp_path,
                                                                 monkeypatch):
    """Zero commits ahead of master is different news, and the useful kind.

    An hour after S21 was delivered its branch read exactly like this. "Someone
    may be working on it" would send the reader to go and look; "already merged"
    tells them to stop.
    """
    _fake_git(monkeypatch, ["  agent/s21-app-session-death"], ahead="0")
    out = board.prior_work("S21-app-session-death", _repo(tmp_path))
    assert "已并入" in "\n".join(out)


def test_a_worktree_with_no_branch_still_warns(tmp_path, monkeypatch):
    """The S27 case: an untracked file in a worktree, no branch, no commit.

    A ref-based check finds exactly nothing here, which is why the directory
    listing is not redundant with the branch listing.
    """
    _fake_git(monkeypatch, [])
    out = board.prior_work("S27-credential-triage",
                           _repo(tmp_path, ["s27-credential-triage"]))
    assert out
    assert ".worktrees/s27-credential-triage" in "\n".join(out)


def test_the_same_branch_local_and_remote_is_reported_once(tmp_path, monkeypatch):
    _fake_git(monkeypatch, ["* agent/s28-thing",
                            "  remotes/origin/agent/s28-thing"])
    out = board.prior_work("S28-thing", _repo(tmp_path))
    assert sum(1 for l in out if "agent/s28-thing" in l) == 1


def test_the_origin_head_alias_is_not_a_branch(tmp_path, monkeypatch):
    _fake_git(monkeypatch, ["  remotes/origin/HEAD -> origin/s29-x",
                            "  agent/s29-x"])
    out = board.prior_work("S29-x", _repo(tmp_path))
    assert not any("->" in l for l in out)


# ------------------------------------------- the negative samples: stay quiet

def test_no_branch_and_no_worktree_says_nothing(tmp_path, monkeypatch):
    """The one that keeps the warning worth reading.

    If this fails, every claim carries a warning, and a warning on every claim
    is indistinguishable from no warning at all.
    """
    _fake_git(monkeypatch, [])
    assert board.prior_work("S30-brand-new", _repo(tmp_path)) == []


def test_a_similar_but_different_item_does_not_match(tmp_path, monkeypatch):
    """`--list *slug*` is a glob, so this is really asserting the glob is
    anchored on the full item id and not on some shared prefix."""
    _fake_git(monkeypatch, [])          # git itself did the filtering
    out = board.prior_work("S31-other", _repo(tmp_path, ["s99-unrelated"]))
    assert out == []


# --------------------------------------------------- it must never break claim

def test_the_warning_survives_this_host_s_console_encoding(tmp_path, monkeypatch):
    """Caught in the act: the first draft used U+26A0 as the warning glyph.

    The console here is cp936, which has no U+26A0, so printing it raises
    UnicodeEncodeError -- and it would raise *after* `cmd_claim` renamed the
    item into `claimed/`. The board would record a successful claim while the
    agent saw only a traceback and no work. That is the same host locale that
    once reported eight live workers as dead.
    """
    _fake_git(monkeypatch, ["  agent/s34-thing"])
    out = board.prior_work("S34-thing", _repo(tmp_path, ["s34-thing"]))
    assert out
    for line in out:
        line.encode("cp936")            # raises if an un-encodable glyph is back


def test_a_failing_git_command_returns_nothing_rather_than_raising(tmp_path):
    """The real `_git`, unpatched. A claim that fails because git was missing,
    slow, or mid-rebase would be a worse bug than the one being fixed."""
    assert board._git(str(tmp_path), "definitely-not-a-git-command") == []


def test_a_directory_that_is_not_a_repo_produces_no_warning(tmp_path):
    """End to end with the real `_git`: `tmp_path` has no git repo above it in
    any meaningful sense, so `branch --list` fails and nothing is claimed to
    exist. Silence, not a crash, and not a false alarm either."""
    assert board.prior_work("S32-nothing-here", _repo(tmp_path)) == []


def test_missing_worktrees_directory_is_fine(tmp_path, monkeypatch):
    _fake_git(monkeypatch, [])
    assert board.prior_work("S33-x", str(tmp_path)) == []
