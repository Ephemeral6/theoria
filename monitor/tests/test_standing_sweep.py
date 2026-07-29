"""Injection self-test for the standing-session sweep.

Three standing researchers were killed by a session limit on 2026-07-29 and six
items -- including the campaign mainline -- stayed locked for two hours because
`sweep` refused to touch anything that was not a `W-*` worker. The refusal was
right at the time: nothing could tell a dead App session from a busy one.

This adds the判据 and, more importantly, the negative samples. **The cost of a
wrong answer is asymmetric**, and every test below exists to hold that shape:
freeing a live session's claim puts two agents in one territory, which is the
single failure the board exists to prevent; leaving a dead one locked costs a
delay. So the interesting tests are not the releases -- they are the refusals.
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import board                                                    # noqa: E402


def _fleet(tmp_path, monkeypatch):
    home = tmp_path / "monitor"
    for sub in ("board/items", "board/claimed", "board/done", "ops-status"):
        (home / sub).mkdir(parents=True)
    monkeypatch.setattr(board, "HERE", str(home))
    monkeypatch.setattr(board, "BOARD", str(home / "board"))
    monkeypatch.setattr(board, "ITEMS", str(home / "board" / "items"))
    monkeypatch.setattr(board, "CLAIMED", str(home / "board" / "claimed"))
    monkeypatch.setattr(board, "DONE", str(home / "board" / "done"))
    monkeypatch.setattr(board, "LOG", str(home / "board" / "board.log"))
    monkeypatch.setattr(board, "OPS_STATUS", str(home / "ops-status"))
    return home


def _heartbeat(home, agent, age_min):
    p = home / "ops-status" / ("%s.json" % agent)
    p.write_text(json.dumps({"id": agent, "state": "working"}), encoding="utf-8")
    when = time.time() - age_min * 60
    os.utime(p, (when, when))
    return p


def _urgent(home, agent, age_min):
    d = home / "bus" / agent
    d.mkdir(parents=True, exist_ok=True)
    p = d / "URGENT"
    p.write_text("wake up", encoding="utf-8")
    when = time.time() - age_min * 60
    os.utime(p, (when, when))
    return p


def _claim(home, iid, agent, territory="src"):
    p = home / "board" / "claimed" / ("%s.%s.md" % (iid, agent))
    p.write_text("priority: 2\ncell: X\nterritory: %s\ndeps: none\n\n# %s\n"
                 % (territory, iid), encoding="utf-8")
    return p


# ------------------------------------------------------- it does release

def test_a_dead_standing_session_is_released(tmp_path, monkeypatch):
    """The positive control: all three conditions hold."""
    home = _fleet(tmp_path, monkeypatch)
    _heartbeat(home, "RES-9", age_min=200)
    _urgent(home, "RES-9", age_min=120)
    dead, why = board.standing_verdict("RES-9")
    assert dead, why
    assert "still unread" in why


def test_the_released_item_carries_the_inheritance_warning(tmp_path, monkeypatch):
    """A freed claim otherwise looks exactly like one nobody ever took.

    That is how the same work gets done twice: the next holder sees a clean
    item and starts over, while a half-finished branch sits on the remote.
    """
    home = _fleet(tmp_path, monkeypatch)
    _heartbeat(home, "RES-9", age_min=200)
    _urgent(home, "RES-9", age_min=120)
    _claim(home, "X1-thing", "RES-9")
    board.cmd_sweep(include_standing=True)

    text = (home / "board" / "items" / "X1-thing.md").read_text(encoding="utf-8")
    assert "RES-9" in text
    assert "半成品" in text
    assert "origin/agent/x1-thing" in text


def test_the_release_is_written_to_the_board_log(tmp_path, monkeypatch):
    home = _fleet(tmp_path, monkeypatch)
    _heartbeat(home, "RES-9", age_min=200)
    _urgent(home, "RES-9", age_min=120)
    _claim(home, "X1-thing", "RES-9")
    board.cmd_sweep(include_standing=True)
    log = (home / "board" / "board.log").read_text(encoding="utf-8")
    assert "SWEEP X1-thing released" in log
    assert "standing RES-9" in log


# ------------------------------- the negative samples: it must NOT release

def test_a_fresh_heartbeat_is_never_released(tmp_path, monkeypatch):
    """S21's explicit ask: do not kill a session inside a long task.

    This is the one that matters. Getting it wrong puts two agents in one
    territory, which is the failure the whole board exists to prevent.
    """
    home = _fleet(tmp_path, monkeypatch)
    _heartbeat(home, "RES-9", age_min=3)
    _urgent(home, "RES-9", age_min=120)          # even with an urgent pending
    dead, why = board.standing_verdict("RES-9")
    assert not dead, why
    assert "under the" in why


def test_silence_without_a_pending_urgent_is_not_death(tmp_path, monkeypatch):
    """Two of three conditions is not the criterion.

    A session can work for a long time without saying anything. Only an
    unanswered URGENT makes the silence mean something, because noticing it
    between sub-steps is the one thing the contract requires.
    """
    home = _fleet(tmp_path, monkeypatch)
    _heartbeat(home, "RES-9", age_min=300)
    dead, why = board.standing_verdict("RES-9")
    assert not dead, why
    assert "no URGENT was pending" in why


def test_a_very_recent_urgent_does_not_convict(tmp_path, monkeypatch):
    """It may simply not have come round yet."""
    home = _fleet(tmp_path, monkeypatch)
    _heartbeat(home, "RES-9", age_min=300)
    _urgent(home, "RES-9", age_min=5)
    dead, why = board.standing_verdict("RES-9")
    assert not dead, why
    assert "not yet one cycle" in why


def test_a_missing_heartbeat_is_never_started_not_died(tmp_path, monkeypatch):
    _fleet(tmp_path, monkeypatch)
    dead, why = board.standing_verdict("RES-9")
    assert not dead
    assert "never started" in why


def test_default_sweep_still_leaves_standing_sessions_alone(tmp_path, monkeypatch):
    """The flag is opt-in. Every existing caller keeps the old behaviour."""
    home = _fleet(tmp_path, monkeypatch)
    _heartbeat(home, "RES-9", age_min=500)
    _urgent(home, "RES-9", age_min=300)
    _claim(home, "X1-thing", "RES-9")
    board.cmd_sweep()                                # no include_standing
    assert (home / "board" / "claimed" / "X1-thing.RES-9.md").exists()


def test_a_live_and_a_dead_standing_session_side_by_side(tmp_path, monkeypatch):
    """The whole judgement in one run: release one, keep the other."""
    home = _fleet(tmp_path, monkeypatch)
    _heartbeat(home, "RES-8", age_min=2)
    _urgent(home, "RES-8", age_min=200)
    _claim(home, "A1-live", "RES-8", territory="src")

    _heartbeat(home, "RES-9", age_min=400)
    _urgent(home, "RES-9", age_min=200)
    _claim(home, "B1-dead", "RES-9", territory="docs")

    board.cmd_sweep(include_standing=True)
    assert (home / "board" / "claimed" / "A1-live.RES-8.md").exists()
    assert not (home / "board" / "claimed" / "B1-dead.RES-9.md").exists()
    assert (home / "board" / "items" / "B1-dead.md").exists()


def test_the_two_thresholds_come_from_one_number():
    """A second copy of "how long is too long" drifts from the first."""
    assert board.STANDING_CYCLE_MIN == board.STALE_MIN
    assert board.STANDING_DEAD_MIN == board.STALE_MIN * 2
