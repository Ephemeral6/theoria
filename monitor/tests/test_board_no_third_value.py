"""S28 findings 1, 4 and 5: three ways the board looked healthier than it was.

* `cmd_list` printed four partitions, and the territory mutex removed an item
  from **all four**. Measured on the live board: 11 items on the shelf, 7 of them
  ready and mentioned nowhere, while the header said `available: 1`. A stuck
  board and a busy fleet rendered identically.
* `heartbeat_age` read the mtime of a **git-tracked** file, so any merge or reset
  touched a dead session's heartbeat back to life -- and the error only ever
  points at "the owner is alive, keep the lane reserved, keep the territory
  locked".
* `cmd_claim` caught bare `OSError` around the claim rename and `continue`d, so a
  locked file produced `BOARD-EMPTY`, which workers are told means "wrap up and
  exit". The exception was discarded and `note()` only runs on the success path,
  so the fake BOARD-EMPTY left nothing in board.log.

The negative controls are the load-bearing tests: a board with nothing withheld
must not print the new partition at all, and a genuine claim race must still be
swallowed silently.
"""

import os
import sys

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import board                                                    # noqa: E402


ITEM = """priority: %(pri)s
cell: X1
territory: %(territory)s
deps: %(deps)s
lane: %(lane)s
%(extra)s
# %(iid)s

body
"""


@pytest.fixture
def rig(tmp_path, monkeypatch):
    """An isolated board: its own items/, claimed/, done/ and ops-status/."""
    for sub in ("board/items", "board/claimed", "board/done", "ops-status"):
        (tmp_path / sub).mkdir(parents=True)
    monkeypatch.setattr(board, "ITEMS", str(tmp_path / "board" / "items"))
    monkeypatch.setattr(board, "CLAIMED", str(tmp_path / "board" / "claimed"))
    monkeypatch.setattr(board, "DONE", str(tmp_path / "board" / "done"))
    monkeypatch.setattr(board, "OPS_STATUS", str(tmp_path / "ops-status"))
    monkeypatch.setattr(board, "LOG", str(tmp_path / "board.log"))

    class Rig:
        root = tmp_path

        def item(self, iid, territory="t1", lane="", pri=1, deps="none",
                 extra=""):
            (tmp_path / "board" / "items" / ("%s.md" % iid)).write_text(
                ITEM % {"iid": iid, "territory": territory, "lane": lane,
                        "pri": pri, "deps": deps, "extra": extra},
                encoding="utf-8")

        def claim(self, iid, worker, territory="t1"):
            (tmp_path / "board" / "claimed"
             / ("%s.%s.md" % (iid, worker))).write_text(
                ITEM % {"iid": iid, "territory": territory, "lane": "",
                        "pri": 1, "deps": "none", "extra": ""},
                encoding="utf-8")

        def heartbeat(self, agent, lock=None, json_age=None):
            import json as _j
            import time as _t
            p = tmp_path / "ops-status" / ("%s.json" % agent)
            p.write_text(_j.dumps({"id": agent, "cycle": 1}), encoding="utf-8")
            if json_age is not None:
                old = _t.time() - json_age * 60
                os.utime(p, (old, old))
            if lock is not None:
                lp = tmp_path / "ops-status" / ("%s.lock" % agent)
                lp.write_text("stamp", encoding="utf-8")
                old = _t.time() - lock * 60
                os.utime(lp, (old, old))

    return Rig()


def _list(capsys):
    board.cmd_list()
    return capsys.readouterr().out


# ---------------------------------------------------------------- finding 1

def test_a_territory_blocked_item_is_no_longer_invisible(rig, capsys):
    rig.item("READY-1", territory="shared")
    rig.claim("HOLDER-1", "RES-1", territory="shared")

    out = _list(capsys)

    assert "=== territory-blocked (1) ===" in out
    assert "READY-1" in out
    assert "HOLDER-1" in out, "the reader has to know which claim to wait on"


def test_nothing_withheld_prints_no_new_partition(rig, capsys):
    """NEGATIVE CONTROL. A partition that always shows up is noise, and this one
    sits above a 122-line done list where attention is cheapest to lose."""
    rig.item("READY-1", territory="t1")

    out = _list(capsys)

    assert "territory-blocked" not in out
    assert "READY-1" in out, "it should simply be available"


def test_an_item_on_an_ownerless_lane_is_also_surfaced(rig, capsys):
    """The second invisibility class: `reserved` only walks LANE_OWNER's keys,
    so a lane with no standing researcher appears in neither partition."""
    rig.item("ORPHAN-1", lane="nosuchlane")

    out = _list(capsys)

    assert "ORPHAN-1" in out
    assert "nosuchlane" in out


def test_a_dependency_blocked_item_is_not_double_reported(rig, capsys):
    """NEGATIVE CONTROL: `blocked` already reports these; two partitions
    claiming the same item would make the counts lie."""
    rig.item("WAITER-1", deps="NOT-DONE-YET")

    out = _list(capsys)

    assert "=== blocked ===" in out
    assert "territory-blocked" not in out


def test_an_unexplained_exclusion_says_so_instead_of_hiding(rig, capsys,
                                                            monkeypatch):
    """If someone adds a sixth exclusion rule to `candidates()` and forgets this
    partition, the item must still surface -- as `reason unknown`. Silence is
    the failure mode being fixed; an honest 'I do not know' is not."""
    rig.item("MYSTERY-1")
    monkeypatch.setattr(board, "candidates", lambda lane=None: [])

    out = _list(capsys)

    assert "MYSTERY-1" in out
    assert "原因不明" in out


def test_the_new_partition_survives_a_cp936_console(rig, capsys):
    """A previous fix raised UnicodeEncodeError *after* renaming an item into
    claimed/: the board logged a successful claim and the claimer saw a
    traceback and zero work."""
    rig.item("READY-1", territory="shared")
    rig.claim("HOLDER-1", "RES-1", territory="shared")

    for line in _list(capsys).splitlines():
        line.encode("cp936")


# ---------------------------------------------------------------- finding 4

def test_the_lock_is_preferred_over_the_tracked_file(rig):
    """The recorded incident: OPS-R.json self-reported 05:59Z, heartbeat_age
    said 12 minutes, and the reflog showed a 10:19:43Z reset touching it.

    A stale session whose tracked heartbeat was touched forward by git must
    still read as stale, because the lock is untracked and git cannot reach it.
    """
    rig.heartbeat("OPS-R", lock=200, json_age=0)      # git touched the json

    age, source = board.heartbeat_evidence("OPS-R")

    assert source == "lock"
    assert age >= 199, "the touched mtime must not win: got %s" % age


def test_a_missing_lock_says_the_number_is_touchable(rig):
    rig.heartbeat("OPS-X", lock=None, json_age=5)

    age, source = board.heartbeat_evidence("OPS-X")

    assert (age, source) == (5, "mtime-touchable")


def test_never_started_is_still_none(rig):
    """NEGATIVE CONTROL: the contract callers rely on must not change."""
    assert board.heartbeat_evidence("NOBODY") == (None, "never-started")
    assert board.heartbeat_age("NOBODY") is None


def test_a_live_session_reads_fresh(rig):
    """NEGATIVE CONTROL: the fix must not declare live sessions dead."""
    rig.heartbeat("RES-9", lock=1, json_age=1)
    assert board.heartbeat_age("RES-9") <= 1


def test_stale_lanes_now_rests_on_the_untouchable_signal(rig, monkeypatch):
    """`stale_lanes` decides whether a lane's work opens up to generic workers,
    so this is the consumer where a touched mtime costs the most."""
    lane, owner = sorted(board.LANE_OWNER.items())[0]
    rig.heartbeat(owner, lock=board.STALE_MIN + 60, json_age=0)
    for other in board.LANE_OWNER.values():
        if other != owner:
            rig.heartbeat(other, lock=0, json_age=0)

    assert lane in board.stale_lanes(), (
        "an owner silent past STALE_MIN must free its lane even when git "
        "touched its heartbeat file")


# ---------------------------------------------------------------- finding 5

def test_a_locked_file_no_longer_becomes_board_empty(rig, monkeypatch):
    """WinError 32 is an OSError subclass and the monitor holds these files
    open, so this is the common case, not the exotic one. It must raise rather
    than tell the worker the board is empty."""
    rig.item("READY-1", lane="infra")

    def locked(src, dst):
        raise PermissionError(32, "The process cannot access the file")

    monkeypatch.setattr(board.os, "rename", locked)

    with pytest.raises(PermissionError):
        board.cmd_claim("RES-4", lane="infra")


def test_a_genuine_claim_race_is_still_swallowed(rig, monkeypatch, capsys):
    """NEGATIVE CONTROL. The docstring says the expected race is another worker
    getting there first; that must stay silent, or every busy moment on the
    board becomes a crash."""
    rig.item("READY-1", lane="infra")

    def taken(src, dst):
        raise FileNotFoundError(2, "No such file or directory")

    monkeypatch.setattr(board.os, "rename", taken)

    board.cmd_claim("RES-4", lane="infra")            # must not raise
    assert "BOARD-EMPTY" in capsys.readouterr().out


def test_the_claim_rename_catches_only_the_expected_race():
    src = open(os.path.join(HERE, "board.py"), encoding="utf-8").read()
    i = src.index("os.rename(src, dst)")
    # Comments in the window mention the old `except OSError:` on purpose, so
    # compare code lines only.
    code = [l for l in src[i:i + 900].splitlines()
            if not l.strip().startswith("#")]
    window = "\n".join(code)
    assert "except FileNotFoundError:" in window
    assert "except OSError:" not in window


def test_an_empty_metadata_field_does_not_borrow_the_next_line(tmp_path):
    """Found while writing these tests, and the same disease: `\\s*` crossed the
    newline, so an empty `lane:` parsed as the title line's `#`. A field nobody
    filled in became a field with a plausible-looking value."""
    p = tmp_path / "x.md"
    p.write_text("priority: 1\nterritory: t1\nlane: \ndeps: none\n\n# X-1\n\nb\n",
                 encoding="utf-8")

    m = board.meta(str(p))

    assert m["lane"] == "", "an empty field must stay empty, got %r" % m["lane"]
    assert m["territory"] == "t1", "NEGATIVE CONTROL: real values still parse"
