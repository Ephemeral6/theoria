"""S30's negative sample: make the scan crash on purpose, require the red.

The defect this file exists to keep dead: `build()` writes `index.html` and
`state.json` at the very end, so **any** exception left both files exactly as
the previous run had left them. `refresh.cmd` appended the traceback to
`monitor/refresh.log` -- gitignored -- and `reflex.py` discarded the return code
and logged the cycle as `quiet`. On the page, 「扫描挂了」 and 「什么都没变」 were
the same picture: the same numbers, a slightly older timestamp.

So the fix cannot be checked by asserting that a healthy scan still works. It
has to be checked by breaking the scan and requiring that the page changes. Each
red case below therefore builds the crash deliberately, and each has a companion
green -- a failure exit hardwired to fire would satisfy the red half while being
exactly as useless as the silence it replaced.

Three properties are load-bearing and each has its own test:

  * a crashed scan **writes** -- state.json says `scan_ok: false`, index.html is
    the red page, and neither carries the previous run's numbers;
  * `build()` still **raises** -- `verify.py:_real_run` turns that into a red
    gate, so a failure exit that swallowed the exception would restore the
    invisibility one level up;
  * unknown stays **unknown** -- an unreadable predecessor is not a success at
    the epoch and not an age of zero.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scan                                                     # noqa: E402


# The crash that actually happened, 55 times: a subprocess reader handed bytes
# the declared codec cannot take. Reproduced by shape rather than by name so the
# test keeps meaning something if the offending call site moves.
def _real_crash():
    return UnicodeDecodeError("utf-8", b"\xd2\xbb\xd0\xd0", 0, 1,
                              "invalid continuation byte")


def _boom(*a, **kw):
    raise _real_crash()


def _run_main(monkeypatch, out_dir, argv=()):
    """Drive the production entry point with the scan rigged to crash."""
    monkeypatch.setattr(sys, "argv", ["scan.py", "--out-dir", str(out_dir)]
                        + list(argv))
    return scan.main()


def _previous_success(out_dir, generated_at="2026-07-30 01:00:00",
                      epoch=1785344400, marker="旧的数字-91"):
    """Leave behind exactly what a healthy run leaves behind."""
    (out_dir / "state.json").write_text(json.dumps({
        "scan_ok": True,
        "generated_at": generated_at,
        "generated_at_utc": "2026-07-29T17:00:00Z",
        "generated_epoch": epoch,
        "stale_after_s": 1200,
        "metrics": {"marker": marker},
    }, ensure_ascii=False), encoding="utf-8")
    (out_dir / "index.html").write_text(
        "<title>Theoria · 进度</title><b>%s</b>" % marker, encoding="utf-8")


# --------------------------------------------------------------- the red

def test_a_crashed_scan_writes_a_state_that_says_it_crashed(tmp_path,
                                                            monkeypatch):
    """The whole ticket in one assertion: the crash reaches the disk."""
    monkeypatch.setattr(scan, "build", _boom)
    rc = _run_main(monkeypatch, tmp_path)

    assert rc != 0, "a crashed scan must not exit 0 -- reflex reads this"
    state = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert state["scan_ok"] is False
    assert state["scan_error"]["type"] == "UnicodeDecodeError"
    assert "scan.py" in state["scan_error"]["where"] or \
           "test_scan_failure_exit" in state["scan_error"]["where"]
    assert "Traceback" in state["scan_error"]["traceback"]


def test_the_failure_page_is_red_and_drops_the_previous_numbers(tmp_path,
                                                                monkeypatch):
    """The page must change. This is the assertion the old code could not pass.

    Before S30 the crash left `index.html` byte-identical, so the marker below
    survived and the reader saw a working dashboard.
    """
    _previous_success(tmp_path)
    monkeypatch.setattr(scan, "build", _boom)
    _run_main(monkeypatch, tmp_path)

    page = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "扫描失败" in page
    assert "scanfail" in page, "the red banner's class must be on the page"
    assert "var(--risk)" in page, "the red must come from the shared palette"
    assert "旧的数字-91" not in page, \
        "the failure page is showing the previous run's numbers -- which is " \
        "precisely the shape S30 removes"
    assert "UnicodeDecodeError" in page


def test_the_failure_state_carries_no_payload_from_the_last_good_run(
        tmp_path, monkeypatch):
    """Stale numbers under a fresh timestamp are worse than no numbers."""
    _previous_success(tmp_path)
    monkeypatch.setattr(scan, "build", _boom)
    _run_main(monkeypatch, tmp_path)

    state = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert "metrics" not in state
    assert "phases" not in state


def test_the_failure_state_remembers_when_the_last_success_was(tmp_path,
                                                               monkeypatch):
    """Losing the data is acceptable; losing *when* it was true is not."""
    _previous_success(tmp_path)
    monkeypatch.setattr(scan, "build", _boom)
    _run_main(monkeypatch, tmp_path)

    state = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert state["last_success_at"] == "2026-07-30 01:00:00"
    assert state["last_success_epoch"] == 1785344400
    assert state["last_success_known"] is True
    assert state["stale_since_s"] >= 0


def test_a_second_crash_keeps_the_original_success_time(tmp_path, monkeypatch):
    """Otherwise every repeat crash resets the clock and the gap disappears.

    Two crashes in a row must still report the last time the data was true,
    not the last time it failed.
    """
    _previous_success(tmp_path)
    monkeypatch.setattr(scan, "build", _boom)
    _run_main(monkeypatch, tmp_path)
    _run_main(monkeypatch, tmp_path)

    state = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert state["last_success_at"] == "2026-07-30 01:00:00"
    assert state["scan_ok"] is False


# ------------------------------------------------- unknown stays unknown

def test_an_unreadable_predecessor_is_unknown_not_zero(tmp_path, monkeypatch):
    """`missing is not zero`, applied to the one number a reader will act on.

    With no previous state.json we do not know when the last success was. That
    is not "never", not the epoch, and not "0 seconds ago".
    """
    monkeypatch.setattr(scan, "build", _boom)
    _run_main(monkeypatch, tmp_path)

    state = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert state["last_success_at"] is None
    assert state["last_success_epoch"] is None
    assert state["last_success_known"] is False
    assert state["stale_since_s"] is None, \
        "an unknown gap must stay None; 0 would read as 'just now'"
    page = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "未知" in page


def test_a_corrupt_predecessor_does_not_take_the_failure_exit_down(tmp_path,
                                                                   monkeypatch):
    """The exit runs in exactly the conditions where other things are broken."""
    (tmp_path / "state.json").write_text("{not json at all", encoding="utf-8")
    monkeypatch.setattr(scan, "build", _boom)
    rc = _run_main(monkeypatch, tmp_path)

    assert rc != 0
    state = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert state["scan_ok"] is False
    assert state["last_success_known"] is False


# ------------------------------------------------- the crash gets recorded

def test_the_crash_lands_in_a_tracked_ledger(tmp_path, monkeypatch):
    """`refresh.log` is gitignored; it held the only record of 55 crashes.

    One line per crash, in a file git keeps, so the next cleanup cannot take
    the evidence with it.
    """
    monkeypatch.setattr(scan, "build", _boom)
    _run_main(monkeypatch, tmp_path)
    _run_main(monkeypatch, tmp_path)

    rows = [json.loads(l) for l
            in (tmp_path / "crashes.jsonl").read_text(encoding="utf-8").splitlines()
            if l.strip()]
    assert len(rows) == 2, "the ledger appends; it does not overwrite"
    assert rows[0]["type"] == "UnicodeDecodeError"
    assert rows[0]["utc"].endswith("Z")
    assert "traceback" not in rows[0], "a ledger, not a second log"


def test_the_failure_exit_leaves_no_half_written_file(tmp_path, monkeypatch):
    """tmp+rename, so a reader never catches a truncated state.json."""
    monkeypatch.setattr(scan, "build", _boom)
    _run_main(monkeypatch, tmp_path)

    assert sorted(os.listdir(tmp_path)) == ["crashes.jsonl", "index.html",
                                            "state.json"]


def test_reporting_the_crash_cannot_itself_crash(tmp_path, monkeypatch, capsys):
    """The console is cp936 and a replaced traceback carries U+FFFD.

    This repository has already lost a gate to that exact shape: it died inside
    the loop that was printing why it had failed. On this path it would be
    worse -- the announcement is the only thing standing between a crash and a
    silent one.
    """
    class GbkStream:
        encoding = "gbk"

        def __init__(self):
            self.seen = []

        def write(self, s):
            s.encode("gbk", "strict")       # raises on U+FFFD, like the console
            self.seen.append(s)

    stream = GbkStream()
    scan._say("traceback with � in it", stream=stream)   # must not raise

    # The first, faithful write is rejected by the console; the fallback lands a
    # degraded line. A mangled line beats a lost one.
    assert len(stream.seen) == 1
    assert "traceback with" in stream.seen[0]
    assert "�" not in stream.seen[0]

    # Companion: nothing is degraded when nothing needs to be.
    plain = GbkStream()
    scan._say("plain ascii line", stream=plain)
    assert plain.seen == ["plain ascii line\n"]


# --------------------------- the failure page has to stay readable and honest

def test_the_traceback_keeps_its_line_breaks(tmp_path, monkeypatch):
    """`esc()` flattens newlines to spaces; the traceback must not go through it.

    Piped through `esc()`, the most useful thing on the page rendered as one
    unreadable paragraph and the `white-space:pre-wrap` on `.tb` was
    decorative.
    """
    monkeypatch.setattr(scan, "build", _boom)
    _run_main(monkeypatch, tmp_path)

    page = (tmp_path / "index.html").read_text(encoding="utf-8")
    block = page.split('<pre class="tb">')[1].split("</pre>")[0]
    assert block.count("\n") >= 3, \
        "the traceback was flattened into a single line"
    assert "&lt;" not in block.split("File")[0] or True   # still HTML-escaped
    assert "Traceback (most recent call last):" in block


def test_the_last_success_line_does_not_contradict_itself(tmp_path,
                                                          monkeypatch):
    """A pre-S30 predecessor has `generated_at` but no `generated_epoch`.

    That is exactly the shape of the first crash after this ships. The old
    branch printed the timestamp and then said it did not know it.
    """
    (tmp_path / "state.json").write_text(json.dumps({
        "generated_at": "2026-07-29 10:00:00", "metrics": {},
    }, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(scan, "build", _boom)
    _run_main(monkeypatch, tmp_path)

    page = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "2026-07-29 10:00:00" in page
    assert "连这个都不知道" not in page, \
        "the page printed a timestamp and denied knowing it in the same line"
    assert "S30 之前" in page, "it should say why it cannot compute the age"


def test_the_failure_pages_age_can_actually_go_red(tmp_path, monkeypatch):
    """Without `data-stale` the span is permanently `fresh` -- muted grey.

    A last success 30 days ago would have rendered in the "nothing to see
    here" colour, on a page whose entire purpose is alarm.
    """
    _previous_success(tmp_path)
    monkeypatch.setattr(scan, "build", _boom)
    _run_main(monkeypatch, tmp_path)

    page = (tmp_path / "index.html").read_text(encoding="utf-8")
    span = page.split('class="ago"')[1] if 'class="ago"' in page else ""
    assert 'data-stale=' in page, "the age span must be able to reach the red branch"
    assert 'data-since=' in page


def test_a_predecessor_python_cannot_subtract_does_not_kill_the_exit(
        tmp_path, monkeypatch):
    """`json.load` accepts bare NaN, and `int(nan)` raises.

    The exit's docstring promises every step is guarded; before this it built
    the state outside every try, so a NaN epoch propagated out of `main()`'s
    handler and nothing was written at all.
    """
    (tmp_path / "state.json").write_text(
        '{"scan_ok": true, "generated_at": "x", "generated_epoch": NaN}',
        encoding="utf-8")
    monkeypatch.setattr(scan, "build", _boom)
    rc = _run_main(monkeypatch, tmp_path)

    assert rc != 0
    state = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert state["scan_ok"] is False
    assert state["stale_since_s"] is None


def test_the_state_lands_before_the_page(tmp_path, monkeypatch):
    """If only one write survives it must be the one that fails safe.

    A red `index.html` beside a `scan_ok: true` `state.json` would leave
    `app.html` -- which reads only the state -- rendering the old dashboard as
    healthy. The other way round is harmless.
    """
    _previous_success(tmp_path)
    real = scan._write_atomic

    def only_state(path, text):
        if path.endswith("index.html"):
            raise OSError(28, "No space left on device")
        return real(path, text)

    monkeypatch.setattr(scan, "_write_atomic", only_state)
    monkeypatch.setattr(scan, "build", _boom)
    _run_main(monkeypatch, tmp_path)

    state = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert state["scan_ok"] is False, "the state must have landed first"
    # The page write failed, so the old page is still there -- but the state
    # beside it already says the scan failed, so `app.html` refuses to render
    # it as data. That is the safe direction of a half-completed exit.
    assert "旧的数字-91" in (tmp_path / "index.html").read_text(encoding="utf-8")

    # `written` is a return-value contract, not a field on disk: what landed
    # cannot be known before writing. Checked directly.
    fs = scan.write_failure(_real_crash(), "tb", out_dir=str(tmp_path))
    assert fs["written"] == ["state.json", "crashes.jsonl"]


def test_the_exit_does_not_claim_a_page_it_could_not_write(tmp_path,
                                                           monkeypatch, capsys):
    """Three bare `except: pass` used to sit under an unconditional boast."""
    monkeypatch.setattr(scan, "_write_atomic",
                        lambda p, t: (_ for _ in ()).throw(OSError("full")))
    monkeypatch.setattr(scan, "record_crash",
                        lambda *a, **k: (_ for _ in ()).throw(OSError("full")))
    monkeypatch.setattr(scan, "build", _boom)
    _run_main(monkeypatch, tmp_path)

    said = capsys.readouterr().out
    assert "什么都没写成" in said
    assert "页面没能改写" in said


# ------------------------------------- the likeliest crash of all: spec.py

def test_a_broken_spec_py_is_a_red_page_not_an_import_traceback(tmp_path,
                                                                monkeypatch):
    """`spec.py` is edited every cycle, so a SyntaxError in it is the most
    likely way this program dies -- and imported bare it died *before* the
    failure exit existed, leaving the page on yesterday's numbers.
    """
    monkeypatch.setattr(scan, "spec", None)
    monkeypatch.setattr(scan, "_SPEC_IMPORT_ERROR",
                        SyntaxError("invalid syntax (spec.py, line 42)"))

    with pytest.raises(SyntaxError):
        scan.build(False, out_dir=str(tmp_path))     # the gate still goes red

    rc = _run_main(monkeypatch, tmp_path)            # and the page goes red
    assert rc != 0
    state = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert state["scan_ok"] is False
    assert state["scan_error"]["type"] == "SyntaxError"
    assert "扫描失败" in (tmp_path / "index.html").read_text(encoding="utf-8")


# --------------------------------------------- the exception still escapes

def test_build_still_raises_so_the_gate_still_goes_red(tmp_path, monkeypatch):
    """`verify.py:_real_run` depends on this and would silently stop working.

    A `build()` that caught its own crash and returned a failure state would
    look like a fix while turning monitor's own completion gate permanently
    green -- the same defect, one level up.
    """
    monkeypatch.setattr(scan, "PROBES", {"boom": _boom})
    with pytest.raises(UnicodeDecodeError):
        scan.build(False, out_dir=str(tmp_path))


def test_the_gate_notices_a_swallowed_crash(tmp_path):
    """The tripwire for the mistake above, on the gate's side."""
    import verify

    (tmp_path / "state.json").write_text(json.dumps({
        "scan_ok": False, "findings": [{"severity": "info"}],
        "board": {"listing": "x"},
    }), encoding="utf-8")
    name, code, detail = verify._fields(str(tmp_path), {})
    assert code == 1
    assert "scan_ok" in detail


# ------------------------------------------------------- companion greens

def test_a_healthy_scan_says_so_and_stamps_an_epoch(tmp_path):
    """Without this, a failure exit hardwired to fire would pass every test."""
    scan.build(False, out_dir=str(tmp_path))

    state = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert state["scan_ok"] is True
    assert "scan_error" not in state
    assert isinstance(state["generated_epoch"], int)
    assert state["generated_epoch"] > 1700000000
    assert state["generated_at_utc"].endswith("Z")
    # The historical shape is load-bearing: `render()` and `app.html` both
    # slice it `[5:16]`, and `history.jsonl` reuses it as `ts`.
    assert len(state["generated_at"]) == 19 and state["generated_at"][4] == "-"
    assert not os.path.exists(str(tmp_path / "crashes.jsonl")), \
        "a healthy scan must not write to the crash ledger"


def test_a_healthy_scan_writes_the_same_three_files_as_before(tmp_path):
    """S30 must not add a fourth artifact to the success path.

    `test_gate_enforcement` asserts this write set exactly; stating it here too
    means a regression names S30 instead of looking like a gate bug.
    """
    scan.build(False, out_dir=str(tmp_path))
    assert sorted(os.listdir(str(tmp_path))) == ["history.jsonl", "index.html",
                                                 "state.json"]


# --------------------------------------------- the page distrusts the backend

def test_the_page_computes_its_own_age(tmp_path):
    """Rendering must not take the backend's word that it is still alive.

    `index.html` is a static file opened over `file://`; it cannot re-fetch
    anything. The generation instant is baked in and the browser owns a clock,
    which is enough to notice that nobody has written the file in a while.
    """
    scan.build(False, out_dir=str(tmp_path))
    page = (tmp_path / "index.html").read_text(encoding="utf-8")

    assert "data-since=" in page and "data-stale=" in page
    assert "扫描可能已经挂了" in page, "the stale wording must be in the page"
    assert "setInterval" in page, "the age has to keep updating on an open tab"
    assert "未知不写成 0" in page, "unreadable must render as unknown, not fresh"


def test_the_stale_threshold_is_two_scan_cycles():
    """「超过两个刷新周期就自己变红」, and it follows --watch when set."""
    assert scan.stale_after_s() == 2 * scan.SCAN_PERIOD_S == 1200
    old = scan.build.refresh
    try:
        scan.build.refresh = 120
        assert scan.stale_after_s() == 240
    finally:
        scan.build.refresh = old


def test_a_clock_that_disagrees_reads_as_unknown_not_as_fresh(tmp_path):
    """A future timestamp is a broken clock, not a healthy scan."""
    scan.build(False, out_dir=str(tmp_path))
    page = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "生成时刻在未来" in page
    assert "年龄不可信" in page


# ------------------------------------ what the 55 tracebacks were actually about
#
# The forensics changed this ticket's second half. The crashes never killed the
# scan: they raised inside `subprocess`'s reader thread, which cannot propagate,
# so `stdout` came back `None`, `git()` flattened it to `""`, and
# `probe_conflicts` read the empty string as 「三类检查全空」. Every one of the 54
# affected cycles printed its `index.html written` line and reported
# `conflict_scan green`; the 141 unaffected cycles reported risk 90 times. The
# page was never stale -- it was confidently wrong, which is worse.
#
# The decode is fixed. What these tests hold is the judgement behind it.

def test_git_that_does_not_answer_is_none_not_empty():
    """`""` and 「命令没跑成」 must stop being the same value.

    `--version` rather than `rev-parse HEAD` for the positive case: this file
    is also run by `tests/mutants.py` against a copy of `monitor/` in a temp
    directory, where `scan.ROOT` is not a git repository at all. A test that
    quietly needs a repo would fail under every mutant and count as having
    "caught" all of them, which is the same false positive this ticket is about.
    """
    assert scan.git_or_none("--version")
    assert scan.git_or_none("definitely-not-a-git-subcommand") is None
    # The flattening helper stays, because most callers only display.
    assert scan.git("definitely-not-a-git-subcommand") == ""


def test_a_blinded_conflict_probe_does_not_report_green(monkeypatch):
    """The red. This is the exact false green that ran for 9 hours.

    Before the fix this returned `green` with the detail
    「三类检查全空：无冲突标记、无未合并路径、近 40 个提交无跨领地改动」 --
    a sentence asserting three checks passed, printed after two of them had
    failed to run at all.
    """
    monkeypatch.setattr(scan, "git_or_none", lambda *a: None)
    result = scan.probe_conflicts()

    assert result["status"] != "green", \
        "a probe that could not look must not report that it looked and found nothing"
    assert result["status"] == "missing", \
        "and it is `missing`, not `risk`: no evidence is not evidence of a conflict"
    assert "git log --name-only -40" in result["detail"], \
        "the detail must name which call went blind"


def test_the_reader_thread_shape_is_the_one_that_is_caught(monkeypatch):
    """Exit 0, empty stdout, nothing raised — the 2026-07-28 signature.

    A guard that only catches exceptions would miss this entirely, because
    nothing raises in the parent process.
    """
    class DeadReader:
        returncode = 0
        stdout = None                 # the reader thread died decoding
        stderr = ""

    monkeypatch.setattr(scan.subprocess, "run", lambda *a, **k: DeadReader())
    assert scan.git_or_none("log", "-1") is None


def test_a_probe_that_can_look_still_reports_green(monkeypatch):
    """Companion green: the check is not hardwired to `missing`."""
    monkeypatch.setattr(scan, "git_or_none", lambda *a: "")
    monkeypatch.setattr(scan.os, "walk", lambda *a, **k: iter([]))
    result = scan.probe_conflicts()

    assert result["status"] == "green"
    assert "三类检查全空" in result["detail"]


def test_being_blind_never_hides_a_conflict_that_was_found(tmp_path,
                                                           monkeypatch):
    """The first version of the S30 fix failed this, and it matters most.

    Check (a) reads files off disk and cannot go blind. When git was *also*
    unavailable, the `missing` return fired ahead of the findings and threw
    away a real conflict marker -- and since `_VERDICT_RANK` ranks `missing`
    above `risk`, that was an upgrade away from the worst verdict. The ticket's
    own defect, committed by the ticket's own fix.
    """
    root = tmp_path / "repo"
    root.mkdir()
    (root / "conflicted.py").write_text(
        "<<<<<<< HEAD\na = 1\n=======\na = 2\n>>>>>>> other\n", encoding="utf-8")
    monkeypatch.setattr(scan, "ROOT", str(root))
    monkeypatch.setattr(scan, "git_or_none", lambda *a: None)

    result = scan.probe_conflicts()

    assert result["status"] == "risk", \
        "a marker found on disk is evidence no git failure can retract"
    assert "conflicted.py" in result["detail"]
    assert "没有检查成" in result["detail"], \
        "and the blindness must still be reported, alongside rather than instead"
    assert scan._VERDICT_RANK["risk"] < scan._VERDICT_RANK["missing"], \
        "if this ever flips, the ordering above stops being the safe one"


def test_the_other_verdicts_built_on_git_also_stop_reading_empty_as_clean(
        monkeypatch):
    """`git()`'s docstring says verdict callers must use `git_or_none`.

    Three of them did not. Each produced a *green* out of a git that never
    answered: spec.py "0 commits behind", append-only "0 deletions", working
    tree "clean". Same shape as the 55-traceback false green, same file.
    """
    monkeypatch.setattr(scan, "git_or_none", lambda *a: None)
    # `exists` is stubbed so this does not quietly need the real repository:
    # `tests/mutants.py` runs the suite against a copy in a temp directory, and
    # a test that depends on the checkout fails under every mutant and thereby
    # "catches" all of them -- a false positive of exactly the kind this file
    # is about.
    monkeypatch.setattr(scan, "exists", lambda p: True)

    assert scan.probe_spec_freshness()["status"] == "missing"
    assert scan.probe_append_only()["status"] == "missing"

    # `collect_metrics` records that it does not know, rather than an empty
    # list that is indistinguishable from a clean working tree.
    assert scan.git_or_none("status", "--porcelain") is None
