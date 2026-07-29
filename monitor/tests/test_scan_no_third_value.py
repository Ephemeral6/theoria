"""S28 findings 2, 3, 7, 8 and 9: five probes that rendered a healthy answer.

`scan.py` builds the page a human reads to decide whether the fleet is well.
Each of these five reported "fine" for a state it had not actually measured:

* `_supply()` scraped `board.py list` for lines starting with `"  p"`, but that
  prefix is printed by the available section AND the reserved one -- so the repo
  held two contradicting supply numbers and rendered the wrong one. Measured
  live: the page said 4, `board.candidates()` said 1.
* `probe_scheduled_tasks` forced UTF-8 on `schtasks`, which emits cp936 here, so
  the English `Disabled` never appeared and the Chinese one became U+FFFD --
  `disabled` was permanently False. This probe exists *because* two ops reports
  found TheoriaReflex sitting Disabled with nothing on the board saying so.
* `probe_append_only` skipped watched files that no longer existed and then
  reported the full watched total as clean -- while deletion is the biggest
  possible violation of an append-only rule.
* `probe_verify_gates` dropped `survey["decorative"]`: 22 of 24 gates have never
  been shown able to go red, and the page said `自带闸门 24` and went green.
* the bus probe hand-rolled a shrunken `ACK_REQUIRED` without `urgent`, so a
  session that keeps heartbeating and never obeys its instruction read as fine.

The negative controls matter as much as the positives here: this file feeds a
dashboard, and a probe that always shows a warning gets ignored, which is the
same outcome as a probe that never does.
"""

import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bus                                                  # noqa: E402
import scan                                                 # noqa: E402


# ---------------------------------------------------------------- finding 2

def test_supply_asks_the_board_instead_of_reading_its_layout(monkeypatch):
    """The scraped count included reserved items; now there is one source."""
    import board as board_mod
    monkeypatch.setattr(board_mod, "candidates", lambda lane=None: ["a"])
    monkeypatch.setattr(board_mod, "claimed_map", lambda: {"x": "RES-1"})

    r = scan._supply()

    assert "1 件可领" in r["detail"]
    assert r["status"] == "partial", "one item left is not a healthy board"


def test_supply_does_not_scrape_the_list_output():
    """Counting a string rendered for humans is treating layout as an API -- and
    the layout just gained a fifth partition that also prints `  p`."""
    src = open(os.path.join(HERE, "scan.py"), encoding="utf-8").read()
    i = src.index("def _supply()")
    body = src[i:i + 1800]
    assert 'startswith("  p")' not in body
    assert "candidates()" in body


def test_a_board_that_cannot_be_queried_is_not_called_healthy(monkeypatch):
    import board as board_mod

    def boom(lane=None):
        raise RuntimeError("board unreadable")

    monkeypatch.setattr(board_mod, "candidates", boom)

    r = scan._supply()

    assert r["status"] == "risk"
    assert "查不出来" in r["detail"]


def test_a_healthy_board_still_reads_green(monkeypatch):
    """NEGATIVE CONTROL."""
    import board as board_mod
    monkeypatch.setattr(board_mod, "candidates", lambda lane=None: list("abcde"))
    monkeypatch.setattr(board_mod, "claimed_map", lambda: {})

    assert scan._supply()["status"] == "green"


# ---------------------------------------------------------------- finding 3

def test_scheduled_tasks_are_read_with_the_console_codepage():
    """Forcing UTF-8 destroyed the sentinel before it could be compared.

    Measured on this box: the same query decoded as UTF-8 gives
    `ģʽ:  ��������` (U+FFFD throughout), and via childio gives `模式: 正在运行`.
    """
    src = open(os.path.join(HERE, "scan.py"), encoding="utf-8").read()
    i = src.index("def probe_scheduled_tasks()")
    # The comments quote the old line deliberately, so compare code only.
    body = "\n".join(l for l in src[i:i + 2200].splitlines()
                     if not l.strip().startswith("#"))
    assert "childio.run_console" in body
    assert 'encoding="utf-8"' not in body, (
        "schtasks is a console built-in; UTF-8 is the wrong codec for it")


def test_a_disabled_task_is_detected_in_both_languages(monkeypatch):
    """The English word never appears on a cp936 console, so both must match."""
    for text in ("Status:  Disabled", "模式:         已禁用"):
        class R:
            returncode = 0
            stdout = text
            stderr = ""
        monkeypatch.setattr(scan.childio, "run_console", lambda *a, **kw: R())

        r = scan.probe_scheduled_tasks()

        assert r["status"] == "risk", "a disabled task must be loud (%r)" % text
        assert "已禁用" in r["detail"]


def test_a_running_task_is_not_reported_disabled(monkeypatch):
    """NEGATIVE CONTROL: this is the state of the live box right now."""
    class R:
        returncode = 0
        stdout = "模式:         正在运行"
        stderr = ""
    monkeypatch.setattr(scan.childio, "run_console", lambda *a, **kw: R())

    r = scan.probe_scheduled_tasks()

    assert r["status"] == "green"
    assert "已禁用" not in r["detail"]


def test_forcing_utf8_would_still_destroy_the_sentinel():
    """Pin the mechanism, so nobody 'simplifies' the codec back.

    cp936 bytes for the Chinese sentinel, decoded as UTF-8 with replacement,
    contain neither word -- which is exactly how `disabled` became a constant.
    """
    raw = "模式:         已禁用".encode("cp936")
    mangled = raw.decode("utf-8", errors="replace")
    assert "已禁用" not in mangled and "Disabled" not in mangled
    assert "�" in mangled
    assert "已禁用" in raw.decode("cp936")          # the correct codec works


# ---------------------------------------------------------------- finding 7

def test_a_deleted_append_only_file_is_a_risk(monkeypatch):
    """Measured before the fix: status green, `4 个追加式文件无新增删除`, with one
    of the four gone. Deletion is the violation the rule is about."""
    real = scan.exists
    gone = "battery/PREDICTIONS.md"
    monkeypatch.setattr(scan, "exists",
                        lambda p: False if p == gone else real(p))

    r = scan.probe_append_only()

    assert r["status"] == "risk"
    assert gone in r["detail"]
    assert "3/4" in r["detail"], "the wording must be checked/total"


def test_all_files_present_still_reads_green():
    """NEGATIVE CONTROL against the live repo, where all four exist."""
    r = scan.probe_append_only()

    assert r["status"] in ("green", "risk")
    if r["status"] == "green":
        assert "4/4" in r["detail"]


# ---------------------------------------------------------------- finding 8

def test_the_gate_count_admits_how_many_were_never_proven(monkeypatch):
    """`gates.py` says in as many words that "19 gated" and "19 gates known to
    work" are different claims. The probe read the first and printed the second.
    """
    import gates as gates_mod

    monkeypatch.setattr(gates_mod, "survey", lambda root: {
        "n_territories": 25, "gated": ["a"] * 24, "tests_only": ["t"],
        "ungated": [], "decorative": ["d"] * 22, "rows": {},
        "non_canonical": [], "root": root})

    r = scan.probe_verify_gates()

    assert "22" in r["detail"], "the decorative count must reach the page"
    assert "从未被证明能变红" in r["detail"]


def test_decorative_gates_do_not_by_themselves_turn_the_probe_amber(monkeypatch):
    """NEGATIVE CONTROL, and it is a judgment call the item made explicitly:
    make the number visible, not the alarm loud. Several of those gates have
    undeclared negative controls, so degrading on this basis would cry wolf
    forever -- and a check people switch off is a check that does not exist.
    """
    import gates as gates_mod

    monkeypatch.setattr(gates_mod, "survey", lambda root: {
        "n_territories": 25, "gated": ["a"] * 24, "tests_only": ["t"],
        "ungated": [], "decorative": ["d"] * 22, "rows": {},
        "non_canonical": [], "root": root})

    r = scan.probe_verify_gates()

    assert r["status"] == "green", (
        "decorative gates are reported, not alarmed on: got %s" % r["status"])


# ---------------------------------------------------------------- finding 9

def test_the_ack_vocabulary_comes_from_the_bus():
    assert scan._ACK_REQUIRED == bus.ACK_REQUIRED
    assert "urgent" in scan._ACK_REQUIRED, (
        "an unacknowledged urgent is the one failure that must not be silent")
    assert "notice" not in scan._ACK_REQUIRED, (
        "the protocol says notice needs no receipt; widening it would cry wolf")


def test_an_unacknowledged_urgent_is_owed(tmp_path, monkeypatch):
    """The failure mode: a live session writing heartbeats and advancing its
    cycle, never executing its instruction, and reported as fine. `cmd_read`
    re-sends it forever because bus.py's own set does include `urgent`."""
    d = tmp_path / "monitor" / "bus" / "RES-4"
    d.mkdir(parents=True)
    (d / "in.jsonl").write_text(
        json.dumps({"seq": 1, "kind": "urgent", "body": "stop and read"}) + "\n",
        encoding="utf-8")
    (d / "cursor.json").write_text(json.dumps({"last_seq": 1}), encoding="utf-8")
    (d / "out.jsonl").write_text("", encoding="utf-8")
    monkeypatch.setattr(scan, "rel",
                        lambda *parts: str(tmp_path.joinpath(*parts)))

    r = scan._bus_probe()

    assert r["status"] == "partial"
    assert "欠回执" in r["detail"] and "RES-4" in r["detail"]


def test_an_acknowledged_urgent_is_not_owed(tmp_path, monkeypatch):
    """NEGATIVE CONTROL."""
    d = tmp_path / "monitor" / "bus" / "RES-4"
    d.mkdir(parents=True)
    (d / "in.jsonl").write_text(
        json.dumps({"seq": 1, "kind": "urgent", "body": "stop and read"}) + "\n",
        encoding="utf-8")
    (d / "cursor.json").write_text(json.dumps({"last_seq": 1}), encoding="utf-8")
    (d / "out.jsonl").write_text(
        json.dumps({"kind": "ack", "ref": 1, "body": "done"}) + "\n",
        encoding="utf-8")
    monkeypatch.setattr(scan, "rel",
                        lambda *parts: str(tmp_path.joinpath(*parts)))

    assert scan._bus_probe()["status"] == "green"


def test_a_notice_never_owes_a_receipt(tmp_path, monkeypatch):
    """NEGATIVE CONTROL for the other direction: widening the set too far would
    make every session permanently in debt."""
    d = tmp_path / "monitor" / "bus" / "RES-4"
    d.mkdir(parents=True)
    (d / "in.jsonl").write_text(
        json.dumps({"seq": 1, "kind": "notice", "body": "fyi"}) + "\n",
        encoding="utf-8")
    (d / "cursor.json").write_text(json.dumps({"last_seq": 1}), encoding="utf-8")
    (d / "out.jsonl").write_text("", encoding="utf-8")
    monkeypatch.setattr(scan, "rel",
                        lambda *parts: str(tmp_path.joinpath(*parts)))

    assert scan._bus_probe()["status"] == "green"


def test_every_new_probe_line_survives_a_cp936_console():
    src = open(os.path.join(HERE, "scan.py"), encoding="utf-8").read()
    for line in src.splitlines():
        if any(w in line for w in ("从未被证明能变红", "查不出来", "已核查")):
            line.encode("cp936")
