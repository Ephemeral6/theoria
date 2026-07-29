"""Injection self-test for the worktree reaper.

A reaper is a delete button, so the only tests worth having are the ones that
manufacture something it must **refuse** to delete.  Every case below builds a
real git repository with real worktrees in a tmp dir and checks the verdict.

The bar this file defends: a worktree with uncommitted work must survive, and
"I could not tell" must never resolve to "safe to remove".  31 of the 115
worktrees on this machine on 2026-07-29 were dirty and belonged to sessions
still running; a reaper that got that wrong once would destroy a colleague's
uncommitted work to reclaim 130 MB.
"""

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import reap_worktrees as reap                                   # noqa: E402


def git(*args, cwd):
    r = subprocess.run(["git"] + list(args), cwd=cwd, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0, "git %s failed: %s" % (" ".join(args), r.stderr)
    return r.stdout


def _repo(tmp_path):
    """A repo with an `origin/master` that worktree branches can be compared to."""
    root = str(tmp_path / "repo")
    os.makedirs(root)
    git("init", "-q", "-b", "master", cwd=root)
    git("config", "user.email", "t@t", cwd=root)
    git("config", "user.name", "t", cwd=root)
    with open(os.path.join(root, "f.txt"), "w") as fh:
        fh.write("base\n")
    git("add", "-A", cwd=root)
    git("commit", "-qm", "base", cwd=root)
    # A local ref standing in for the remote, so `--is-ancestor` has a target
    # without needing a network.
    git("update-ref", "refs/remotes/origin/master", "HEAD", cwd=root)
    return root


def _worktree(root, name, branch, commit=False, dirty=False, untracked=False):
    path = os.path.join(root, "wt", name)
    git("worktree", "add", "-q", "-b", branch, path, "master", cwd=root)
    if commit:
        with open(os.path.join(path, "f.txt"), "a") as fh:
            fh.write("%s\n" % name)
        git("add", "-A", cwd=path)
        git("commit", "-qm", name, cwd=path)
    if dirty:
        with open(os.path.join(path, "f.txt"), "a") as fh:
            fh.write("uncommitted\n")
    if untracked:
        with open(os.path.join(path, "scratch.txt"), "w") as fh:
            fh.write("not committed yet\n")
    return path


def verdict_for(root, path, min_idle=0):
    """`min_idle=0` by default: these worktrees are seconds old on purpose.

    The idle guard is exercised by its own test below rather than by making
    every other test wait an hour.
    """
    rows = {os.path.normpath(r["path"]): r
            for r in reap.classify(root, min_idle=min_idle)}
    return rows[os.path.normpath(path)]


# ------------------------------------------------------------ it does reap

def test_a_finished_worktree_is_reaped(tmp_path):
    """The positive control.

    Without it a reaper hardcoded to refuse everything would pass every other
    test in this file while reclaiming nothing.
    """
    root = _repo(tmp_path)
    path = _worktree(root, "done", "agent/done")
    row = verdict_for(root, path)
    assert row["verdict"] == "reap", row
    assert "on origin/master" in row["why"]


def test_a_branch_merged_into_master_is_reaped(tmp_path):
    root = _repo(tmp_path)
    path = _worktree(root, "landed", "agent/landed", commit=True)
    git("merge", "--no-ff", "-q", "-m", "land", "agent/landed", cwd=root)
    git("update-ref", "refs/remotes/origin/master", "HEAD", cwd=root)
    assert verdict_for(root, path)["verdict"] == "reap"


# --------------------------------------------------------- it refuses to reap

def test_uncommitted_tracked_changes_are_never_reaped(tmp_path):
    root = _repo(tmp_path)
    path = _worktree(root, "inflight", "agent/inflight", dirty=True)
    row = verdict_for(root, path)
    assert row["verdict"] == "keep", row
    assert "work in flight" in row["why"]


def test_untracked_files_alone_are_enough_to_save_it(tmp_path):
    """The case a tracked-only check would delete.

    A session that has written a file and not yet added it looks exactly like a
    finished worktree unless untracked files are counted.  This is the single
    most dangerous shape, because it is the shape of work that has had the most
    effort put into it and the least protection.
    """
    root = _repo(tmp_path)
    path = _worktree(root, "scratch", "agent/scratch", untracked=True)
    row = verdict_for(root, path)
    assert row["verdict"] == "keep", row
    assert "work in flight" in row["why"]


def test_an_unmerged_branch_is_never_reaped(tmp_path):
    root = _repo(tmp_path)
    path = _worktree(root, "ahead", "agent/ahead", commit=True)
    row = verdict_for(root, path)
    assert row["verdict"] == "keep", row
    assert "not yet on origin/master" in row["why"]


def test_the_main_checkout_is_never_reaped(tmp_path):
    root = _repo(tmp_path)
    _worktree(root, "any", "agent/any")
    row = verdict_for(root, root)
    assert row["verdict"] == "keep"
    assert "main checkout" in row["why"]


def test_a_detached_worktree_is_kept_not_guessed_about(tmp_path):
    """No branch means no ancestry question, so there is nothing to decide."""
    root = _repo(tmp_path)
    path = os.path.join(root, "wt", "detached")
    git("worktree", "add", "-q", "--detach", path, "master", cwd=root)
    row = verdict_for(root, path)
    assert row["verdict"] == "keep", row
    assert "detached" in row["why"]


def test_a_worktree_git_cannot_read_is_kept(tmp_path, monkeypatch):
    """"Could not check" must not resolve to "safe to delete".

    This is the reaper's version of the failure the whole S16 ticket is about:
    a check that could not run reading as a check that passed.  Here the
    consequence would be deletion, so it fails closed.
    """
    root = _repo(tmp_path)
    path = _worktree(root, "unreadable", "agent/unreadable")

    real = reap.sh

    def broken(*args, cwd=None):
        if args[:2] == ("git", "status") and cwd and "unreadable" in cwd:
            class R:
                returncode = 128
                stdout = ""
                stderr = "fatal: not a git repository"
            return R()
        return real(*args, cwd=cwd)

    monkeypatch.setattr(reap, "sh", broken)
    row = verdict_for(root, path)
    assert row["verdict"] == "keep", row
    assert "git status failed" in row["why"]


# ------------------------------------------------------------- the dry run

def test_dry_run_is_the_default_and_removes_nothing(tmp_path, monkeypatch, capsys):
    root = _repo(tmp_path)
    path = _worktree(root, "done", "agent/done")
    monkeypatch.setattr(reap, "ROOT", root)
    monkeypatch.setattr(sys, "argv", ["reap_worktrees.py", "--min-idle", "0"])
    assert reap.main() == 0
    assert os.path.isdir(path), "a dry run must not delete anything"
    assert "dry run" in capsys.readouterr().out


def test_apply_removes_only_the_finished_one(tmp_path, monkeypatch):
    root = _repo(tmp_path)
    done = _worktree(root, "done", "agent/done")
    busy = _worktree(root, "busy", "agent/busy", dirty=True)
    ahead = _worktree(root, "ahead", "agent/ahead", commit=True)
    monkeypatch.setattr(reap, "ROOT", root)
    monkeypatch.setattr(sys, "argv",
                        ["reap_worktrees.py", "--apply", "--min-idle", "0"])
    assert reap.main() == 0
    assert not os.path.isdir(done), "the finished worktree should be gone"
    assert os.path.isdir(busy), "uncommitted work must survive --apply"
    assert os.path.isdir(ahead), "an unmerged branch must survive --apply"


# ------------------------------------------------------------- the idle guard

def test_a_recently_touched_worktree_is_not_reaped(tmp_path):
    """Clean and merged is not the same as abandoned.

    A session that has just committed and is about to write its next file is
    indistinguishable from a finished one by status and ancestry alone.
    Deleting it would make this tool cause the exact class of failure it exists
    to fix, so recency is the tie-breaker and it fails closed.
    """
    root = _repo(tmp_path)
    path = _worktree(root, "warm", "agent/warm")
    row = verdict_for(root, path, min_idle=60)
    assert row["verdict"] == "keep", row
    assert "somebody may still be in it" in row["why"]
    # ...and the same worktree with the guard relaxed is reapable, so the test
    # above is measuring the guard and not some unrelated refusal.
    assert verdict_for(root, path, min_idle=0)["verdict"] == "reap"


def test_unreadable_mtimes_fail_closed(tmp_path, monkeypatch):
    root = _repo(tmp_path)
    path = _worktree(root, "opaque", "agent/opaque")
    monkeypatch.setattr(reap, "idle_minutes", lambda p, **k: None)
    row = verdict_for(root, path, min_idle=60)
    assert row["verdict"] == "keep", row
    assert "refusing to guess" in row["why"]
