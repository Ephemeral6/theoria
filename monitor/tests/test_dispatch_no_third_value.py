"""S28 finding 11: the launch receipt, the missing CLI, and the unread ledger.

Three shapes of the same bug in the launch path:

* `ok = r.returncode == 0` in `via_task` is the **scheduler's** receipt, not the
  session's life. `schtasks /Run` returns 0 the instant it hands the task over,
  so a session that dies one second later produced the identical `ok=True` --
  and `standing.log`'s `START ... ok=True` is the fleet's primary record that a
  researcher was brought up.
* `_runner.py` took `shutil.which("claude")` with no guard, so a missing CLI
  became `subprocess.run([None, ...])` -> TypeError -> `code=-1`: an environment
  fault recorded as an ordinary session failure.
* `dispatch-logs/exits.json` had 36 non-zero exits recorded and **no reader
  anywhere in the repo**. Connecting it also revealed the file was corrupt and
  had been silently dropping every write for 4.9 hours.

Every test has a negative control, because a check that always fires says
nothing. The controls that matter most here: a healthy launch must still print
the word `started` (reflex greps for it), and a valid ledger must read `ok=True`
with `problem=None`.
"""

import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import dispatch                     # noqa: E402
import _runner                      # noqa: E402


VALID = {"W-1": [{"code": 0, "seconds": 3869, "log": "a.log",
                  "ended": "2026-07-28T08:26:12Z"},
                 {"code": 1, "seconds": 48, "log": "b.log",
                  "ended": "2026-07-28T15:59:49Z"}]}


# --------------------------------------------------------------------------
# the ledger reader
# --------------------------------------------------------------------------

def test_a_valid_ledger_reads_clean(tmp_path):
    """NEGATIVE CONTROL for every corruption test below."""
    p = tmp_path / "exits.json"
    p.write_text(json.dumps(VALID), encoding="utf-8")

    got = dispatch.read_exits(str(p))

    assert got["ok"] is True
    assert got["problem"] is None
    assert got["data"] == VALID


def test_a_corrupt_ledger_is_not_reported_as_an_empty_one(tmp_path):
    """The real corruption shape: one complete object plus another's tail.

    Produced by two sessions writing the same `exits.json.tmp` at once.
    """
    p = tmp_path / "exits.json"
    p.write_text(json.dumps(VALID) + '120,\n  "log": "x.log"\n  }\n ]\n}',
                 encoding="utf-8")

    got = dispatch.read_exits(str(p))

    assert got["ok"] is False, "corrupt must not read as healthy"
    assert "corrupt" in got["problem"]
    # ...and it still salvages the history rather than throwing it away
    assert got["data"] == VALID


def test_a_missing_ledger_is_distinguishable_from_an_empty_one(tmp_path):
    """`missing` has to reach the caller.

    The first run of `exit_summary` against the live ledger was given a path
    that did not exist, and it answered `ok=True sessions=0` -- "no ledger" and
    "nobody has died" collapsed into one healthy-looking answer, which is this
    item's whole subject reproduced inside its own fix.
    """
    got = dispatch.read_exits(str(tmp_path / "nope.json"))
    assert got["missing"] is True

    summary = dispatch.exit_summary(path=str(tmp_path / "nope.json"))
    assert summary["missing"] is True, "exit_summary must not drop the flag"

    p = tmp_path / "exits.json"
    p.write_text("{}", encoding="utf-8")
    empty = dispatch.exit_summary(path=str(p))
    assert empty["missing"] is False and empty["ok"] is True
    assert empty["runs"] == 0
    assert empty != summary, "an absent ledger and an empty one must differ"


def test_exit_summary_counts_what_the_start_line_cannot_see(tmp_path):
    p = tmp_path / "exits.json"
    p.write_text(json.dumps(VALID), encoding="utf-8")

    s = dispatch.exit_summary(path=str(p))

    assert (s["sessions"], s["runs"]) == (1, 2)
    assert s["nonzero"] == 1
    assert s["short"] == 1, "48s is a session that died on arrival"
    assert s["newest_ended"] == "2026-07-28T15:59:49Z"


def test_a_healthy_ledger_reports_zero_deaths_not_a_false_alarm(tmp_path):
    """NEGATIVE CONTROL: long clean runs must count as neither short nor bad."""
    p = tmp_path / "exits.json"
    p.write_text(json.dumps({"W-9": [{"code": 0, "seconds": 5000,
                                      "log": "c.log",
                                      "ended": "2026-07-28T09:00:00Z"}]}),
                 encoding="utf-8")

    s = dispatch.exit_summary(path=str(p))

    assert (s["nonzero"], s["short"]) == (0, 0)
    assert s["ok"] is True and s["problem"] is None


# --------------------------------------------------------------------------
# the writer that was corrupting it
# --------------------------------------------------------------------------

def test_each_writer_gets_its_own_temp_file(tmp_path, monkeypatch):
    """The cause of the corruption: every session shared `exits.json.tmp`.

    Two sessions exiting at once each opened that one path with "w" and wrote at
    independent offsets, so the file ended up as one complete object plus the
    tail of another. Recorded on the live box at 2026-07-29T15:59:01Z.
    """
    seen = []
    real_open = open

    def spy(path, *a, **kw):
        if str(path).endswith(".tmp"):
            seen.append(os.path.basename(str(path)))
        return real_open(path, *a, **kw)

    exits = tmp_path / "exits.json"
    monkeypatch.setattr(_runner, "EXITS", str(exits))
    monkeypatch.setattr("builtins.open", spy)
    _runner.record_exit("W-1", {"code": 0, "seconds": 10})

    assert seen, "no temp file was used at all"
    assert str(os.getpid()) in seen[0], (
        "the temp name must be unique per writer, got %r" % seen[0])


def test_recoverable_corruption_is_salvaged_in_place(tmp_path, monkeypatch):
    """The real live shape -- a valid object plus a trailing fragment -- is
    recoverable, so the history is kept AND the new record lands. It is still
    reported: the writers are losing records while it lasts."""
    exits = tmp_path / "exits.json"
    exits.write_text(json.dumps(VALID) + "garbage", encoding="utf-8")
    fail = tmp_path / "fail.log"
    monkeypatch.setattr(_runner, "EXITS", str(exits))
    monkeypatch.setattr(_runner, "EXITS_FAIL", str(fail))

    _runner.record_exit("W-2", {"code": 0, "seconds": 10})

    healed = json.loads(exits.read_text(encoding="utf-8"))
    assert healed["W-1"] == VALID["W-1"], "the history must survive"
    assert healed["W-2"] == [{"code": 0, "seconds": 10}]
    assert not [f for f in os.listdir(tmp_path) if ".corrupt-" in f], (
        "recoverable damage must not be quarantined -- that would be data loss")
    assert "recovered valid prefix" in fail.read_text(encoding="utf-8")


def test_unrecoverable_corruption_is_quarantined_not_overwritten(
        tmp_path, monkeypatch):
    """History is worth more than the one record being written, so an
    unparseable ledger is moved aside rather than replaced."""
    exits = tmp_path / "exits.json"
    exits.write_text("!!! not json at all", encoding="utf-8")
    monkeypatch.setattr(_runner, "EXITS", str(exits))
    monkeypatch.setattr(_runner, "EXITS_FAIL", str(tmp_path / "fail.log"))

    _runner.record_exit("W-2", {"code": 0, "seconds": 10})

    quarantined = [f for f in os.listdir(tmp_path) if ".corrupt-" in f]
    assert quarantined, "the unreadable ledger must be kept, not silently lost"
    assert (tmp_path / quarantined[0]).read_text(
        encoding="utf-8") == "!!! not json at all"
    # and the new record still gets written to a fresh ledger
    assert json.loads(exits.read_text(encoding="utf-8"))["W-2"]


def test_a_failed_ledger_write_stops_being_silent(tmp_path, monkeypatch):
    """`except Exception: pass` was right to not kill the session, and wrong to
    swallow the failure too. 62 sessions exited into a corrupt ledger over 4.9
    hours and nothing anywhere said so."""
    exits = tmp_path / "exits.json"
    exits.write_text("{not json at all", encoding="utf-8")
    fail = tmp_path / "fail.log"
    monkeypatch.setattr(_runner, "EXITS", str(exits))
    monkeypatch.setattr(_runner, "EXITS_FAIL", str(fail))

    _runner.record_exit("W-3", {"code": 0, "seconds": 10})

    assert fail.exists(), "the write failure must leave a trace somewhere"
    assert "W-3" in fail.read_text(encoding="utf-8")


def test_a_successful_write_leaves_no_complaint(tmp_path, monkeypatch):
    """NEGATIVE CONTROL: the happy path must stay completely silent."""
    exits = tmp_path / "exits.json"
    exits.write_text(json.dumps(VALID), encoding="utf-8")
    fail = tmp_path / "fail.log"
    monkeypatch.setattr(_runner, "EXITS", str(exits))
    monkeypatch.setattr(_runner, "EXITS_FAIL", str(fail))

    _runner.record_exit("W-1", {"code": 0, "seconds": 99})

    assert not fail.exists(), "a clean write must not write to the failure log"
    assert len(json.loads(exits.read_text(encoding="utf-8"))["W-1"]) == 3


def test_record_exit_still_never_takes_the_session_down(tmp_path, monkeypatch):
    """The original guarantee must survive the fix: observability may not raise."""
    monkeypatch.setattr(_runner, "EXITS", str(tmp_path / "sub" / "x.json"))
    monkeypatch.setattr(_runner, "EXITS_FAIL", str(tmp_path / "sub" / "f.log"))
    _runner.record_exit("W-4", {"code": 0})       # must not raise


# --------------------------------------------------------------------------
# the missing CLI
# --------------------------------------------------------------------------

def test_a_missing_claude_cli_exits_127_and_is_named(tmp_path, monkeypatch):
    log = tmp_path / "s.log"
    recorded = []
    monkeypatch.setattr(_runner.shutil, "which", lambda n: None)
    monkeypatch.setattr(_runner, "record_exit",
                        lambda pid, info: recorded.append((pid, info)))
    monkeypatch.setattr(_runner, "resolve",
                        lambda pid: (str(tmp_path / "p.md"), str(log), "opus"))
    (tmp_path / "p.md").write_text("hello", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["_runner.py", "Z0-test"])

    with pytest.raises(SystemExit) as exc:
        _runner.main()

    assert exc.value.code == 127, (
        "a missing CLI must be its own loud exit code, not a generic failure")
    assert recorded and recorded[0][1]["error"], "the cause must be named"
    assert "not on PATH" in recorded[0][1]["error"]
    assert "abort" in log.read_text(encoding="utf-8")


def test_the_guard_uses_sys_exit_not_return():
    """`__main__` calls `main()` and throws the return value away, so a
    `return 127` would have exited 0 -- this bug one level down."""
    src = open(os.path.join(HERE, "_runner.py"), encoding="utf-8").read()
    i = src.index("not on PATH")
    assert "sys.exit(127)" in src[i:i + 900]


# --------------------------------------------------------------------------
# the launch receipt
# --------------------------------------------------------------------------

@pytest.fixture
def sandboxed_via_task(tmp_path, monkeypatch):
    """Run via_task without a scheduler, a session, or a cent of API spend."""
    monkeypatch.setattr(dispatch, "LOGS", str(tmp_path))
    monkeypatch.setattr(dispatch, "REGISTRY", str(tmp_path / "reg.json"))
    monkeypatch.setattr(dispatch, "PROMPTS", str(tmp_path))
    monkeypatch.setattr(dispatch, "model_for", lambda p: "opus")
    monkeypatch.setattr(dispatch, "LAUNCH_SETTLE_S", 0)

    class R:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setattr(dispatch.subprocess, "run", lambda *a, **kw: R())
    return monkeypatch


def test_a_session_that_dies_on_arrival_is_not_reported_as_started(
        sandboxed_via_task, capsys):
    """Before the fix this returned True and printed `started`, identically to
    a healthy launch, because `schtasks /Run` had exited 0."""
    sandboxed_via_task.setattr(dispatch, "task_state", lambda t: "Ready")

    status = dispatch.via_task("RES-9", "x.md")

    assert status.startswith("died-on-arrival")
    assert "started" not in capsys.readouterr().out, (
        "reflex greps stdout for 'started' to count a launch as successful")


def test_a_running_session_still_reports_started(sandboxed_via_task, capsys):
    """NEGATIVE CONTROL. The happy path must be untouched, including the exact
    word reflex greps for."""
    sandboxed_via_task.setattr(dispatch, "task_state", lambda t: "Running")

    status = dispatch.via_task("RES-9", "x.md")

    assert status == "running"
    assert "started" in capsys.readouterr().out


def test_a_chinese_console_running_state_still_counts(sandboxed_via_task):
    """schtasks emits the console code page; this box is cp936. The repo has
    paid for a GBK/UTF-8 mismatch five times, once reporting eight live workers
    as dead."""
    sandboxed_via_task.setattr(dispatch, "task_state", lambda t: "正在运行")
    assert dispatch.via_task("RES-9", "x.md") == "running"


def test_an_unrecognised_state_is_not_assumed_healthy(sandboxed_via_task):
    sandboxed_via_task.setattr(dispatch, "task_state", lambda t: "unknown")
    assert dispatch.via_task("RES-9", "x.md") == "state-unknown"


def test_a_scheduler_that_refuses_is_still_distinct(tmp_path, monkeypatch):
    """Three outcomes, three values: the scheduler declined / it ran / it
    vanished. Collapsing any two of them loses the name of who to go ask."""
    monkeypatch.setattr(dispatch, "LOGS", str(tmp_path))
    monkeypatch.setattr(dispatch, "REGISTRY", str(tmp_path / "reg.json"))
    monkeypatch.setattr(dispatch, "PROMPTS", str(tmp_path))
    monkeypatch.setattr(dispatch, "model_for", lambda p: "opus")
    monkeypatch.setattr(dispatch, "LAUNCH_SETTLE_S", 0)

    class R:
        returncode = 1
        stdout = ""
        stderr = "access denied"

    monkeypatch.setattr(dispatch.subprocess, "run", lambda *a, **kw: R())
    assert dispatch.via_task("RES-9", "x.md") == "declined"


def test_standing_compares_the_status_explicitly():
    """A non-empty string is truthy, so `if ok:` would call a dead session a
    success -- the same false signal, moved two files over."""
    src = open(os.path.join(HERE, "standing.py"), encoding="utf-8").read()
    assert 'if ok == "running":' in src
    assert "\n        if ok:\n" not in src


def test_the_new_lines_survive_a_cp936_console():
    """ADV-2/D11: this was a `for` over a conditional with no counter, so **zero
    matches meant zero assertions** -- it passed against the pre-fix `dispatch.py`
    and `_runner.py`, where none of these lines exist yet, and renaming the status
    string would have left it green forever.

    A source scan that silently matches nothing is the purest form of the thing
    this whole item is about: a check that cannot go red, reporting success.
    """
    matched = 0
    for mod in ("dispatch.py", "_runner.py"):
        src = open(os.path.join(HERE, mod), encoding="utf-8").read()
        for line in src.splitlines():
            if "died-on-arrival" in line or "not on PATH" in line:
                line.encode("cp936")    # must not raise
                matched += 1

    # Both strings are load-bearing status vocabulary: `died-on-arrival` is the
    # third value this item added, `not on PATH` is the missing-CLI guard.
    assert matched >= 2, (
        "the cp936 scan matched %d lines; the status strings it is meant to "
        "protect have been renamed or removed, so it was checking nothing"
        % matched)
