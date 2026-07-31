"""S42 defect 1: `cmd_sweep` used to take work away from workers still running.

`board.py` shipped `_PREFIX = ""` and never assigned it anywhere in the package
(`from fleetkit import config as _config` appeared exactly once, on the import
line). So `if len(cols) >= 3 and _PREFIX and _PREFIX in cols[0]` was constantly
false, `live` was constantly empty, and every `W-*` claim was judged an orphan
and freed -- including the ones being worked on at that moment.

That is `KNOWN_TRAPS.md` entry 1 word for word ("every worker reads as dead. The
board releases live claims"), latent in the package that ships the warning. And
`config.py` validates `task_prefix` as non-empty for precisely this reason, so
the gate was checking a copy the code never opened.

## How this reproduces it

`schtasks` is injected, not run: `subprocess.run` is monkeypatched to return a
synthetic CSV in which one worker is Running and one is Ready, encoded in the
console code page exactly as the real tool emits it (`KNOWN_TRAPS.md` entry 1's
other half). Both workers hold a claim. The check is that the Ready one's claim
is freed and the Running one's is left alone.

Against the pre-S42 code the Running one is freed too, which is the whole bug;
these tests are red there and green here.

## And the third answer

Not knowing whether a worker is alive is not the same as knowing it is dead.
With no `fleet.json` there is no prefix, and sweep now refuses (exit 3) instead
of freeing everything.
"""

import importlib
import json
import os
import subprocess
import sys

import pytest

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KIT)

from fleetkit import config                                     # noqa: E402

#: One Running, one Ready, in the shape `schtasks /Query /FO CSV /NH` produces:
#: leading backslash on the task name, quoted columns, status in column 3.
CSV = ('"\\SweepProbe-W-777","2026-07-30 12:00:00","Running"\n'
       '"\\SweepProbe-W-888","2026-07-30 12:00:00","Ready"\n')


def _fleet(tmp_path, prefix="SweepProbe-", write_config=True):
    """A repo root with fleet.json, and a state tree under it."""
    root = tmp_path / "newproject"
    (root / "src").mkdir(parents=True)
    (root / "docs").mkdir()
    if write_config:
        config.write_default(str(root), task_prefix=prefix,
                             territories=["src", "docs"])
    home = root / ".fleet"
    home.mkdir()
    return root, home


def _board(monkeypatch, home):
    """Import board with FLEET_HOME pointed at `home`.

    HERE is read at import time, so the module is reloaded rather than merely
    imported -- a stale HERE would silently exercise the wrong tree.
    """
    monkeypatch.setenv("FLEET_HOME", str(home))
    monkeypatch.delenv("FLEET_ROOT", raising=False)
    import fleetkit.board as board
    return importlib.reload(board)


def _claim(home, iid, worker, territory="src"):
    claimed = home / "board" / "claimed"
    claimed.mkdir(parents=True, exist_ok=True)
    (claimed / ("%s.%s.md" % (iid, worker))).write_text(
        "priority: 2\ncell: T\nterritory: %s\ndeps: none\n\n# %s\n"
        % (territory, iid), encoding="utf-8")


def _inject_schtasks(monkeypatch, csv=CSV, returncode=0):
    """Stand in for the real `schtasks`, emitting the CONSOLE code page.

    Not utf-8: that substitution is itself `KNOWN_TRAPS.md` entry 1, and a
    fixture that gets it wrong would prove the fix against the wrong input.
    """
    import locale
    console = locale.getpreferredencoding(False) or "utf-8"
    calls = []

    class _Result:
        def __init__(self):
            self.returncode = returncode
            self.stdout = csv.encode(console, "replace")
            self.stderr = b""

    def fake_run(argv, *a, **kw):
        calls.append(argv)
        return _Result()

    monkeypatch.setattr(subprocess, "run", fake_run)
    return calls


# ---------------------------------------------------------------- the defect

def test_a_running_workers_claim_survives_a_sweep(tmp_path, monkeypatch):
    """The one that matters: sweep must not take work off a live worker.

    Pre-S42 this fails -- W-777 is Running and its claim is freed anyway,
    because `_PREFIX` was "" so nothing ever entered `live`.
    """
    _root, home = _fleet(tmp_path)
    _claim(home, "T1-live", "W-777", territory="src")
    _claim(home, "T2-dead", "W-888", territory="docs")
    board = _board(monkeypatch, home)
    _inject_schtasks(monkeypatch)

    assert board.cmd_sweep() == 0

    still_claimed = sorted(os.listdir(home / "board" / "claimed"))
    assert still_claimed == ["T1-live.W-777.md"], (
        "sweep freed a claim held by a worker whose scheduled task is Running: "
        "%s" % still_claimed)
    assert os.path.exists(home / "board" / "items" / "T2-dead.md"), (
        "the genuinely orphaned claim was not freed -- sweep must still sweep")


def test_the_prefix_comes_from_fleet_json_not_from_a_literal(tmp_path,
                                                             monkeypatch):
    """`task_prefix()` reads config. The pre-S42 module never opened it."""
    root, home = _fleet(tmp_path, prefix="SomeOtherFleet-")
    board = _board(monkeypatch, home)

    assert board.task_prefix() == "SomeOtherFleet-"
    assert board.config_root() == os.path.abspath(str(root))
    assert not hasattr(board, "_PREFIX"), (
        "_PREFIX is back. It was a module global nothing ever assigned; the "
        "prefix must be read from fleet.json at the point of use.")


def test_the_verdict_flips_with_the_configured_prefix_and_nothing_else(
        tmp_path, monkeypatch):
    """The discriminating run: same CSV, same claim, two configs, two answers.

    Under `SweepProbe-` the task table says W-777 is Running and its claim is
    kept. Under `DifferentFleet-` no task matches, W-777 is not this fleet's
    worker, and the claim is freed. Nothing else varies, so the decision
    demonstrably comes from `fleet.json` -- which is exactly what could not be
    said of a literal that was never assigned.
    """
    kept = []
    for prefix in ("SweepProbe-", "DifferentFleet-"):
        root, home = _fleet(tmp_path / prefix, prefix=prefix)
        _claim(home, "T1-live", "W-777")
        board = _board(monkeypatch, home)
        _inject_schtasks(monkeypatch)
        assert board.cmd_sweep() == 0
        kept.append(os.listdir(home / "board" / "claimed"))

    assert kept[0] == ["T1-live.W-777.md"], "matching prefix: claim must survive"
    assert kept[1] == [], "non-matching prefix: the claim is not this fleet's"


# ------------------------------------------------- not knowing is not death

def test_sweep_refuses_when_there_is_no_config_to_read_the_prefix_from(
        tmp_path, monkeypatch):
    """Third value. Pre-S42 this case swept everything; now it sweeps nothing.

    This is the state a fleet is in the moment someone runs the board from a
    directory with no `fleet.json` -- which, before S42, was every directory,
    because nothing ever read one.
    """
    _root, home = _fleet(tmp_path, write_config=False)
    _claim(home, "T1-live", "W-777")
    _claim(home, "T2-also", "W-888", territory="docs")
    board = _board(monkeypatch, home)
    _inject_schtasks(monkeypatch)

    assert board.cmd_sweep() == 3
    assert sorted(os.listdir(home / "board" / "claimed")) == [
        "T1-live.W-777.md", "T2-also.W-888.md"], (
        "sweep freed claims while unable to tell a live worker from a dead one")


def test_sweep_refuses_when_the_task_query_itself_failed(tmp_path, monkeypatch):
    """A failed `schtasks` gives empty stdout, which reads exactly like "nobody
    is running". Judge a worker by its artefacts, not by an exit code nobody
    looked at."""
    _root, home = _fleet(tmp_path)
    _claim(home, "T1-live", "W-777")
    board = _board(monkeypatch, home)
    _inject_schtasks(monkeypatch, csv="", returncode=1)

    assert board.cmd_sweep() == 3
    assert os.listdir(home / "board" / "claimed") == ["T1-live.W-777.md"]


def test_task_prefix_raises_rather_than_defaulting(tmp_path, monkeypatch):
    root = tmp_path / "bare"
    root.mkdir()
    monkeypatch.setenv("FLEET_ROOT", str(root))
    monkeypatch.setenv("FLEET_HOME", str(root))
    import fleetkit.board as board
    board = importlib.reload(board)

    with pytest.raises(config.ConfigError) as exc:
        board.task_prefix()
    assert "liveness" in str(exc.value) or "live worker" in str(exc.value)


def test_an_empty_prefix_in_the_config_cannot_reach_the_sweep(tmp_path,
                                                              monkeypatch):
    """config.validate already refuses this; the point is that board.py is now
    downstream of that refusal instead of shipping its own empty copy."""
    root = tmp_path / "p"
    root.mkdir()
    (root / config.CONFIG_NAME).write_text(
        json.dumps({"task_prefix": "", "territories": ["src"]}),
        encoding="utf-8")
    monkeypatch.setenv("FLEET_ROOT", str(root))
    monkeypatch.setenv("FLEET_HOME", str(root))
    import fleetkit.board as board
    board = importlib.reload(board)
    _claim(root, "T1-live", "W-777")
    _inject_schtasks(monkeypatch)

    assert board.cmd_sweep() == 3
    assert os.listdir(root / "board" / "claimed") == ["T1-live.W-777.md"]
