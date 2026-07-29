"""S19: telling "asleep" from "closed", and not losing instructions at the seam.

Two failures with the same shape -- something that had stopped looked exactly
like something that was fine, and the instrument had no power to separate them.

1. A sleeping App session and a closed one produce the identical signature: a
   heartbeat file that stops moving. OPS-R slept twelve hours and was read as
   dropped; a session was nearly reopened for nothing.
2. `bus.py read` advanced the cursor past everything it printed. An instruction
   read by a session that then died -- context exhausted, quota, closed tab --
   was already behind the cursor when its successor started. Never refused,
   never answered, just gone, and from the bus's side it had been delivered.
"""

import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import bus                                                      # noqa: E402
import scan                                                     # noqa: E402


def _stamp(offset_seconds):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ",
                         time.gmtime(time.time() + offset_seconds))


# ------------------------------------------------------- wake_at, part (1)

def _heartbeats(tmp_path, monkeypatch, payloads, age_minutes):
    root = tmp_path / "repo"
    d = root / "monitor" / "ops-status"
    d.mkdir(parents=True)
    for rid, payload in payloads.items():
        p = d / ("%s.json" % rid)
        p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        old = time.time() - age_minutes * 60
        os.utime(p, (old, old))
    monkeypatch.setattr(scan, "ROOT", str(root))
    return root


def _all_four(payload):
    return {rid: dict(payload) for rid in ("RES-1", "RES-2", "RES-3", "RES-4")}


def test_a_session_asleep_on_schedule_is_not_reported_as_stalled(tmp_path,
                                                                 monkeypatch):
    """The OPS-R case: silent for hours, and that was the plan."""
    _heartbeats(tmp_path, monkeypatch,
                _all_four({"cycle": 3, "state": "idle",
                           "wake_at": _stamp(3600)}), age_minutes=200)
    r = scan._self_driving()
    assert r["status"] == "green", r
    assert "按计划睡" in r["detail"], r


def test_a_session_that_missed_its_own_appointment_is_red(tmp_path,
                                                          monkeypatch):
    """The companion: wake_at is only worth having if overrunning it is louder.

    Without this, declaring a wake_at would be a way to buy silence.
    """
    _heartbeats(tmp_path, monkeypatch,
                _all_four({"cycle": 3, "state": "idle",
                           "wake_at": _stamp(-3600)}), age_minutes=200)
    r = scan._self_driving()
    assert r["status"] == "risk", r
    assert "没醒" in r["detail"], r


def test_a_stale_heartbeat_without_wake_at_is_still_red(tmp_path, monkeypatch):
    """The old rule has to survive the new field."""
    _heartbeats(tmp_path, monkeypatch,
                _all_four({"cycle": 3, "state": "working"}), age_minutes=200)
    assert scan._self_driving()["status"] == "risk"


def test_a_session_that_never_started_is_not_green(tmp_path, monkeypatch):
    """Was green: the verdict came from a substring search over display rows.

    A researcher with no heartbeat file appended "未启动" and continued, so no
    row contained "疑似停下" and the probe reported everything fine. Never
    started and running well were the same colour.
    """
    root = tmp_path / "repo"
    (root / "monitor" / "ops-status").mkdir(parents=True)
    monkeypatch.setattr(scan, "ROOT", str(root))
    r = scan._self_driving()
    assert r["status"] == "risk", r
    assert "未启动" in r["detail"], r


def test_a_malformed_wake_at_falls_back_instead_of_crashing(tmp_path,
                                                            monkeypatch):
    _heartbeats(tmp_path, monkeypatch,
                _all_four({"cycle": 3, "state": "idle",
                           "wake_at": "tomorrow-ish"}), age_minutes=200)
    assert scan._self_driving()["status"] == "risk"


def test_a_fresh_heartbeat_is_green(tmp_path, monkeypatch):
    _heartbeats(tmp_path, monkeypatch,
                _all_four({"cycle": 9, "state": "working"}), age_minutes=1)
    assert scan._self_driving()["status"] == "green"


# ------------------------------------------- unacked redelivery, part (2)

def _bus(tmp_path, monkeypatch):
    monkeypatch.setattr(bus, "BUS", str(tmp_path / "bus"))
    return tmp_path


def _read(agent, capsys):
    bus.cmd_read(agent)
    return capsys.readouterr().out


def test_an_instruction_read_by_a_session_that_died_comes_back(tmp_path,
                                                               monkeypatch,
                                                               capsys):
    """The seam: read advanced the cursor, the session died, the order vanished."""
    _bus(tmp_path, monkeypatch)
    bus.cmd_send("RES-9", "order", "do the thing")
    assert "do the thing" in _read("RES-9", capsys)      # session A reads...
    # ...and dies here, without acking.
    out = _read("RES-9", capsys)                          # session B starts
    assert "do the thing" in out, "the order was lost at the session boundary"
    assert "从未回执" in out, out


def test_an_acked_instruction_does_not_come_back(tmp_path, monkeypatch,
                                                 capsys):
    """The companion green: redelivery must stop, or every read is a repeat."""
    _bus(tmp_path, monkeypatch)
    bus.cmd_send("RES-9", "order", "do the thing")
    _read("RES-9", capsys)
    bus.cmd_ack("RES-9", 1, "done")
    capsys.readouterr()
    out = _read("RES-9", capsys)
    assert "do the thing" not in out, out
    assert "NO-NEW-MESSAGES" in out, out


def test_a_notice_needs_no_receipt_and_is_not_repeated(tmp_path, monkeypatch,
                                                       capsys):
    """Only instructions are redelivered. A notice repeated forever is noise."""
    _bus(tmp_path, monkeypatch)
    bus.cmd_send("RES-9", "notice", "fyi")
    _read("RES-9", capsys)
    out = _read("RES-9", capsys)
    assert "fyi" not in out, out


def test_an_unacked_urgent_also_comes_back(tmp_path, monkeypatch, capsys):
    _bus(tmp_path, monkeypatch)
    bus.cmd_send("RES-9", "urgent", "stop what you are doing")
    _read("RES-9", capsys)
    assert "stop what you are doing" in _read("RES-9", capsys)
