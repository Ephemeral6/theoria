"""The gate must reach its verdict through its own stdout.

On 2026-07-29 `monitor/verify.py` printed `== tests FAILED(1)` and then died
inside the very next line:

    UnicodeEncodeError: 'gbk' codec can't encode character '\\ufffd'

So the merge gate announced a red and then destroyed the reason for it. Two
things make that worse than a cosmetic crash, and both are pinned below:

* the offending line is the **stage report loop**, which runs on green runs
  too. A stage whose captured output happens to contain one character the
  console code page cannot represent turned a passing gate into a traceback --
  a spurious red, with `ci_merge.py` recording it as "verify gate red".
* `--json` uses `ensure_ascii=False`, so the machine-readable path had exactly
  the same hole.

U+FFFD is not an exotic input here: `_tests()` and `_real_run()` capture their
children with `errors="replace"`, which is correct (a checker that dies while
*decoding* its child is a checker that did not check -- see `childio.py`), and
replacement characters are what that produces. The bug was never in the
capture; it was in believing stdout could take whatever the capture handed it.

The property under test is not "UTF-8 comes out intact". It is that the gate
can always print its verdict and its reasons, and that the exit-code contract
(0 green / 1 red) holds whatever bytes the stages produced. A crash must never
be able to substitute for a verdict.
"""

import io
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
MONITOR = os.path.dirname(HERE)
if MONITOR not in sys.path:
    sys.path.insert(0, MONITOR)

import verify                                                    # noqa: E402


#: A stage detail of the shape the crash was really about: a replacement
#: character left by an upstream `errors="replace"` decode, next to CJK, which
#: this repository's tickets and board listings are full of.
POISON = "E   assert 0 == 1\n�\n闸门未通过：产物缺字段"


def gbk_stdout():
    """A stdout that behaves like a redirected console on this cp936 box.

    Pinned to gbk/strict rather than read from the host, because the crash is
    not reproducible from the machine's own locale on a UTF-8 box -- and a
    regression test that only fires on Chinese Windows is one the rest of the
    fleet quietly loses.
    """
    return io.TextIOWrapper(io.BytesIO(), encoding="gbk", errors="strict")


def written(stream):
    """What actually reached the byte stream, decoded however it ended up."""
    stream.flush()
    return stream.buffer.getvalue().decode(stream.encoding, "replace")


def _result(green, detail=POISON):
    """A canned `verify()` return: the printing is under test, not the gate."""
    return {
        "what": "monitor completion gate",
        "out_dir": os.path.join("nowhere", "monitor-verify-x"),
        "stages": [{"stage": "tests", "returncode": 0 if green else 1,
                    "detail": detail}],
        "gate_survey": {"gated": ["monitor"], "tests_only": [],
                        "ungated": ["fleet-study"], "non_canonical": []},
        "failed": [] if green else ["tests"],
        "green": green,
    }


def test_the_stream_this_test_uses_really_is_the_trap():
    """Prove the fixture can produce the failure before trusting it to catch it.

    Without this, a later change to `gbk_stdout` could make every test in this
    file pass by no longer reproducing the bug -- green because nothing was
    checked, which is the failure mode `monitor/` exists to hunt.
    """
    with pytest.raises(UnicodeEncodeError):
        print(POISON, file=gbk_stdout())


def test_red_verdict_survives_an_unprintable_stage_detail(monkeypatch):
    monkeypatch.setattr(verify, "verify", lambda: _result(False))
    out = gbk_stdout()
    monkeypatch.setattr(sys, "stdout", out)

    code = verify.main([])

    text = written(out)
    assert code == 1, "a red gate must still exit 1"
    assert "FAILED(1)" in text
    assert "assert 0 == 1" in text, \
        "the reason the stage failed is the whole point of printing it"
    assert "RED: tests" in text


def test_green_verdict_survives_it_too(monkeypatch):
    """The report loop runs on green runs, so it could manufacture a red.

    This is the half of the defect that is easy to miss: the crash is in code
    that executes whether or not anything failed, so one stray character in a
    *passing* stage's output was enough to fail the merge gate.
    """
    monkeypatch.setattr(verify, "verify", lambda: _result(True))
    out = gbk_stdout()
    monkeypatch.setattr(sys, "stdout", out)

    code = verify.main([])

    assert code == 0
    assert "GREEN" in written(out)


def test_json_report_survives_it_and_stays_parseable(monkeypatch):
    """`--json` is `ensure_ascii=False`, so it shared the hole exactly."""
    monkeypatch.setattr(verify, "verify", lambda: _result(False))
    out = gbk_stdout()
    monkeypatch.setattr(sys, "stdout", out)

    code = verify.main(["--json"])

    assert code == 1
    payload = json.loads(written(out))
    assert payload["green"] is False
    assert payload["failed"] == ["tests"]


def test_emit_does_not_require_a_reconfigurable_stream():
    """The belt, for when the braces are unavailable.

    `sys.stdout` is only a `TextIOWrapper` some of the time -- pytest's capture,
    a `StringIO`, or anything a caller substituted has no `reconfigure`. The
    guarantee has to hold for those too, so `emit` scrubs rather than raises.
    """
    class Strict:
        encoding = "gbk"

        def __init__(self):
            self.chunks = []

        def write(self, s):
            s.encode(self.encoding)          # strict, exactly like the console
            self.chunks.append(s)
            return len(s)

        def flush(self):
            pass

    out = Strict()
    assert verify.harden_stream(out) is False, \
        "this stream is the un-reconfigurable case; if it stops being one the "\
        "test below stops testing the fallback"
    verify.emit(POISON, out)
    text = "".join(out.chunks)
    assert "assert 0 == 1" in text
    assert "�" not in text, "the unprintable character had to be scrubbed"


def test_harden_stream_leaves_a_usable_utf8_stream():
    out = gbk_stdout()
    assert verify.harden_stream(out) is True
    verify.emit("闸门 � ok", out)
    assert "闸门" in written(out), \
        "hardening should widen what prints, not narrow it"
