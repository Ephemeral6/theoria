"""A flag about a branch that already merged is worse than no flag at all.

`clear_flag` only ever ran from `try_merge`'s success path, and
`unmerged_branches` drops anything already in master -- so a branch that merged
by any other route (into a sibling agent branch that then merged, or by hand)
kept its flag for good. `agent/e9-engine-paper-table` did exactly that on
2026-07-29 and was still being counted among the branches holding up the queue.

The negative samples are the point here, as they were for `clear_flag` itself.
Clearing too eagerly deletes the only record of a real failure, so "I cannot
resolve this branch" must not be allowed to mean "this branch is finished".
"""

import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
MONITOR = os.path.dirname(HERE)
if MONITOR not in sys.path:
    sys.path.insert(0, MONITOR)

import ci_merge                                                     # noqa: E402


class _Result(object):
    def __init__(self, returncode=0, stdout=""):
        self.returncode = returncode
        self.stdout = stdout


@pytest.fixture
def ci_dir(tmp_path, monkeypatch):
    d = tmp_path / "ci"
    d.mkdir()
    monkeypatch.setattr(ci_merge, "CI_DIR", str(d))
    monkeypatch.setattr(ci_merge, "LOG", str(d / "merge.log"))
    (tmp_path / "done").mkdir()
    monkeypatch.setattr(ci_merge, "DONE_DIR", str(tmp_path / "done"),
                        raising=False)
    return d


def _git(monkeypatch, merged=(), unknown=()):
    """Stand in for git: `merged` are ancestors of master, `unknown` unresolvable."""
    def fake(args, **kw):
        if args[:3] == ["git", "rev-parse", "--verify"]:
            return _Result(1 if args[-1] in unknown else 0)
        if args[:2] == ["git", "merge-base"]:
            return _Result(0 if args[-2] in merged else 1)
        return _Result(0)
    monkeypatch.setattr(ci_merge, "sh", fake)


# ------------------------------------------------------------- it does clear

def test_a_branch_that_merged_by_another_route_loses_its_flag(ci_dir,
                                                              monkeypatch):
    """The e9 case exactly: merged into a sibling branch, never seen by
    try_merge again, flag left shouting about a tree that no longer exists."""
    b = "origin/agent/e9-engine-paper-table"
    ci_merge.flag(b, "verify gate red in engine-rig", "boom", tip="139ed99c")
    assert os.path.exists(ci_merge.flag_path(b))

    _git(monkeypatch, merged=[b])
    retired = ci_merge.sweep_stale_flags(todo=[])

    assert retired == [b]
    assert not os.path.exists(ci_merge.flag_path(b))


def test_the_sweep_is_recorded_in_the_log(ci_dir, monkeypatch):
    b = "origin/agent/e9-thing"
    ci_merge.flag(b, "verify gate red", "boom", tip="a1")
    _git(monkeypatch, merged=[b])
    ci_merge.sweep_stale_flags(todo=[])
    assert "SWEEP-FLAGS retired 1" in open(ci_merge.LOG, encoding="utf-8").read()


# --------------------------------------------- the negative samples: keep it

def test_a_branch_still_waiting_keeps_its_flag(ci_dir, monkeypatch):
    """The one that matters. A branch in `todo` is still queued, and its flag
    is the verdict that stops it being re-run every tick."""
    b = "origin/agent/e15-solver-status-bit"
    ci_merge.flag(b, "verify gate red", "boom", tip="d2b75c26")
    _git(monkeypatch, merged=[b])          # even if git says merged
    assert ci_merge.sweep_stale_flags(todo=[b]) == []
    assert os.path.exists(ci_merge.flag_path(b))


def test_an_unresolvable_branch_keeps_its_flag(ci_dir, monkeypatch):
    """"I cannot resolve this" and "this is done" are different facts, and
    only one of them is safe to act on. A deleted or never-pushed branch must
    not have the record of its failure quietly retired."""
    b = "origin/agent/gone-branch"
    ci_merge.flag(b, "verify gate red", "boom", tip="a1")
    _git(monkeypatch, merged=[b], unknown=[b])
    assert ci_merge.sweep_stale_flags(todo=[]) == []
    assert os.path.exists(ci_merge.flag_path(b))


def test_an_unmerged_branch_missing_from_todo_keeps_its_flag(ci_dir,
                                                             monkeypatch):
    """Absence from `todo` is not proof of merge -- the ancestor check is."""
    b = "origin/agent/still-open"
    ci_merge.flag(b, "verify gate red", "boom", tip="a1")
    _git(monkeypatch, merged=[])           # not an ancestor of master
    assert ci_merge.sweep_stale_flags(todo=[]) == []
    assert os.path.exists(ci_merge.flag_path(b))


def test_an_empty_ci_dir_is_not_an_error(ci_dir, monkeypatch):
    _git(monkeypatch)
    assert ci_merge.sweep_stale_flags(todo=[]) == []


# ------------------------------------------------ reading the branch back out

def test_the_branch_is_read_from_the_header_not_the_filename(ci_dir):
    """`/` -> `_` is not injective, so a branch containing an underscore
    cannot be recovered from the filename. The header has always carried it."""
    b = "origin/agent/has_underscore/in-it"
    ci_merge.flag(b, "verify gate red", "boom", tip="a1")
    assert ci_merge.flag_branch(ci_merge.flag_path(b)) == b


def test_a_file_with_no_branch_header_is_skipped_not_guessed(ci_dir,
                                                             monkeypatch):
    (ci_dir / "CONFLICT-hand-written.md").write_text("no header here\n",
                                                     encoding="utf-8")
    _git(monkeypatch)
    assert ci_merge.sweep_stale_flags(todo=[]) == []
    assert (ci_dir / "CONFLICT-hand-written.md").exists()
