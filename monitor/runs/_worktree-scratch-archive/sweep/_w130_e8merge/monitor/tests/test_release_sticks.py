"""Injection self-test: a handed-back item must not come straight back.

S22 was claimed four times and released three, and the last gap between release
and re-claim was **11 seconds**. Every round cost a session a fresh read of the
context to reach the conclusion the previous round had already reached: this
work needs a spending authority the agent does not have.

That is a livelock, not a deadlock, and it fails in the reassuring direction --
the log shows claims and releases ticking along, the board looks busy, and
progress is exactly zero. It was not one agent's mistake: C9 and
A4-ablation-online were each handed back by two different workers. So the board
changes, not the people.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import board                                                    # noqa: E402


def _fleet(tmp_path, monkeypatch):
    home = tmp_path / "monitor"
    for sub in ("board/items", "board/claimed", "board/done", "ops-status"):
        (home / sub).mkdir(parents=True)
    monkeypatch.setattr(board, "HERE", str(home))
    monkeypatch.setattr(board, "ITEMS", str(home / "board" / "items"))
    monkeypatch.setattr(board, "CLAIMED", str(home / "board" / "claimed"))
    monkeypatch.setattr(board, "DONE", str(home / "board" / "done"))
    monkeypatch.setattr(board, "LOG", str(home / "board" / "board.log"))
    monkeypatch.setattr(board, "OPS_STATUS", str(home / "ops-status"))
    # No lane owners, so lane gating cannot confuse these cases.
    monkeypatch.setattr(board, "LANE_OWNER", {})
    return home


def _item(home, iid, territory="src", lane=None):
    body = "priority: 2\ncell: X\nterritory: %s\ndeps: none\n" % territory
    if lane:
        body += "lane: %s\n" % lane
    body += "\n# %s\n\nwork.\n" % iid
    (home / "board" / "items" / ("%s.md" % iid)).write_text(body,
                                                            encoding="utf-8")


def test_the_same_worker_does_not_get_it_back(tmp_path, monkeypatch, capsys):
    """The exact S22 loop: claim, release, claim -- and the second claim must
    not return the same item."""
    home = _fleet(tmp_path, monkeypatch)
    _item(home, "S22-costly")

    assert board.cmd_claim("RES-4") == 0
    capsys.readouterr()
    assert board.cmd_release("S22-costly", "RES-4", "needs spend authority") == 0
    capsys.readouterr()

    assert board.cmd_claim("RES-4") == 3, "it came straight back"
    out = capsys.readouterr().out
    assert "BOARD-EMPTY" in out


def test_someone_else_can_still_take_it(tmp_path, monkeypatch, capsys):
    """One agent's refusal is about that agent, not about the item.

    Withholding it from everybody would turn a personal blocker into a
    permanently dead item -- which is worse than the loop it replaces.
    """
    home = _fleet(tmp_path, monkeypatch)
    _item(home, "S22-costly")
    board.cmd_claim("RES-4")
    board.cmd_release("S22-costly", "RES-4", "needs spend authority")
    capsys.readouterr()

    assert board.cmd_claim("RES-1") == 0
    assert (home / "board" / "claimed" / "S22-costly.RES-1.md").exists()


def test_board_empty_says_what_it_is_hiding(tmp_path, monkeypatch, capsys):
    """A bare BOARD-EMPTY over withheld work is the trap this board already hit.

    "There is nothing to do" and "there is nothing I will show you" have to
    look different, or the next reader debugs the wrong thing -- which is
    exactly what board-empty-is-misleading recorded the first time.
    """
    home = _fleet(tmp_path, monkeypatch)
    _item(home, "S22-costly")
    board.cmd_claim("RES-4")
    board.cmd_release("S22-costly", "RES-4", "needs spend authority")
    capsys.readouterr()

    board.cmd_claim("RES-4")
    out = capsys.readouterr().out
    assert "BOARD-EMPTY" in out
    assert "S22-costly" in out, out
    assert "别人仍可领" in out, out


def test_the_releaser_and_reason_are_recorded_on_the_item(tmp_path,
                                                          monkeypatch, capsys):
    home = _fleet(tmp_path, monkeypatch)
    _item(home, "S22-costly")
    board.cmd_claim("RES-4")
    board.cmd_release("S22-costly", "RES-4", "needs spend authority")
    capsys.readouterr()

    text = (home / "board" / "items" / "S22-costly.md").read_text(
        encoding="utf-8")
    assert "released_by: RES-4" in text
    assert "needs spend authority" in text
    # and meta() must be able to read it back
    m = board.meta(str(home / "board" / "items" / "S22-costly.md"))
    assert board.released_by(m) == {"RES-4"}


def test_two_releasers_are_both_remembered(tmp_path, monkeypatch, capsys):
    """C9 and A4 were each handed back by two different workers.

    A single-token parse would keep only the first and re-offer the item to
    everyone after them, which is the bug wearing the fix's clothes.
    """
    home = _fleet(tmp_path, monkeypatch)
    _item(home, "C9-hard")
    for who in ("W-1", "W-2"):
        board.cmd_claim(who)
        board.cmd_release("C9-hard", who, "cannot do it")
    capsys.readouterr()

    m = board.meta(str(home / "board" / "items" / "C9-hard.md"))
    assert board.released_by(m) == {"W-1", "W-2"}
    assert board.cmd_claim("W-1") == 3
    assert board.cmd_claim("W-2") == 3
    capsys.readouterr()
    assert board.cmd_claim("W-3") == 0


def test_a_released_item_is_still_offered_to_a_fresh_worker_first_time(
        tmp_path, monkeypatch, capsys):
    """The positive control.

    Without it, a board that withheld everything from everyone would satisfy
    every other test in this file.
    """
    home = _fleet(tmp_path, monkeypatch)
    _item(home, "A1-fine")
    assert board.cmd_claim("W-9") == 0
    capsys.readouterr()


def test_releasing_twice_does_not_duplicate_the_name(tmp_path, monkeypatch,
                                                     capsys):
    home = _fleet(tmp_path, monkeypatch)
    _item(home, "X1-thing")
    board.cmd_claim("RES-4")
    board.cmd_release("X1-thing", "RES-4", "first")
    # A second cycle can only happen if someone re-claims it; simulate the
    # monitor handing it back deliberately.
    os.rename(str(home / "board" / "items" / "X1-thing.md"),
              str(home / "board" / "claimed" / "X1-thing.RES-4.md"))
    board.cmd_release("X1-thing", "RES-4", "second")
    capsys.readouterr()
    m = board.meta(str(home / "board" / "items" / "X1-thing.md"))
    assert board.released_by(m) == {"RES-4"}
