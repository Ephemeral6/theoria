"""The hash chain, and every tampering it is supposed to catch.

D-024 / RED-40: the ledger is self-consistent, not authenticated.  Every check
the repo had was the file against itself, so a carefully written forgery
reconciled clean.  The chain closes the half that a local change *can* close --
tamper-evidence after the head is published.

Each test below performs a real edit on a real ledger and requires the verifier
to go red.  This repo has been bitten four times in one day by checks that pass
because they never ran, so a tamper detector that has never been shown a tamper
is not evidence of anything.  Note especially the positive control at the
bottom: an untouched file must verify, or "always red" would pass every test
here while being just as useless.
"""

import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from proxy.ledger import Ledger, line_hash                  # noqa: E402
from proxy.tools import verify_chain                        # noqa: E402


def _ledger(tmp_path, n=6):
    path = str(tmp_path / "ledger.jsonl")
    led = Ledger(path)
    for i in range(n):
        led.append("env_meta", "r1", "probe", http={"step": i})
    return path


def _lines(path):
    with open(path, "rb") as fh:
        return [l.rstrip(b"\r\n") for l in fh if l.strip()]


def _rewrite(path, lines):
    with open(path, "wb") as fh:
        for l in lines:
            fh.write(l + b"\n")


# ------------------------------------------------------------- the chain works

def test_an_untouched_ledger_verifies(tmp_path):
    """The positive control.

    Without it a verifier hard-wired to return FAIL would satisfy every other
    test in this file.
    """
    path = _ledger(tmp_path)
    report = verify_chain.verify(path)
    assert report["verdict"] == "PASS", report
    assert report["lines"] == 6
    assert report["chained"] == 6
    assert report["unchained"] == 0
    assert report["breaks"] == []


def test_first_record_has_a_null_prev(tmp_path):
    path = _ledger(tmp_path, n=3)
    first = json.loads(_lines(path)[0].decode("utf-8"))
    assert "prev" in first, "absent and null are different claims"
    assert first["prev"] is None


def test_each_prev_is_the_previous_lines_bytes(tmp_path):
    path = _ledger(tmp_path, n=5)
    lines = _lines(path)
    for i in range(1, len(lines)):
        rec = json.loads(lines[i].decode("utf-8"))
        assert rec["prev"] == line_hash(lines[i - 1]), \
            "link %d does not hash its own predecessor" % i


def test_a_second_writer_resumes_the_chain(tmp_path):
    """A fresh Ledger object over an existing file must not restart the chain."""
    path = _ledger(tmp_path, n=3)
    again = Ledger(path)
    again.append("env_meta", "r1", "probe", http={"step": 99})
    assert verify_chain.verify(path)["verdict"] == "PASS"
    lines = _lines(path)
    assert json.loads(lines[3].decode("utf-8"))["prev"] == line_hash(lines[2])


# ------------------------------------------------------------ the tamperings

def test_editing_one_field_is_caught(tmp_path):
    """The headline requirement: change one line and it must be caught."""
    path = _ledger(tmp_path)
    lines = _lines(path)
    rec = json.loads(lines[2].decode("utf-8"))
    rec["http"] = {"step": 999}
    lines[2] = json.dumps(rec, sort_keys=True, ensure_ascii=True,
                          separators=(",", ":")).encode("utf-8")
    _rewrite(path, lines)

    report = verify_chain.verify(path)
    assert report["verdict"] == "FAIL", report
    assert report["first_break"] == 4, \
        "the break shows at the line *after* the edit, whose prev no longer matches"
    assert report["breaks"][0]["kind"] == "broken_link"


def test_deleting_a_line_is_caught(tmp_path):
    path = _ledger(tmp_path)
    lines = _lines(path)
    del lines[3]
    _rewrite(path, lines)
    report = verify_chain.verify(path)
    assert report["verdict"] == "FAIL", report
    assert report["breaks"][0]["kind"] == "broken_link"


def test_inserting_a_forged_line_is_caught(tmp_path):
    """A forger who appends a plausible record cannot link it in."""
    path = _ledger(tmp_path)
    lines = _lines(path)
    forged = json.loads(lines[2].decode("utf-8"))
    forged["seq"] = 99
    forged["http"] = {"step": "forged"}
    lines.insert(3, json.dumps(forged, sort_keys=True, ensure_ascii=True,
                               separators=(",", ":")).encode("utf-8"))
    _rewrite(path, lines)
    assert verify_chain.verify(path)["verdict"] == "FAIL"


def test_swapping_two_records_is_caught(tmp_path):
    path = _ledger(tmp_path)
    lines = _lines(path)
    lines[2], lines[3] = lines[3], lines[2]
    _rewrite(path, lines)
    assert verify_chain.verify(path)["verdict"] == "FAIL"


def test_truncating_the_front_is_caught(tmp_path):
    """Dropping the beginning leaves a record claiming a predecessor that is gone."""
    path = _ledger(tmp_path)
    lines = _lines(path)
    _rewrite(path, lines[2:])
    report = verify_chain.verify(path)
    assert report["verdict"] == "FAIL", report
    assert report["breaks"][0]["kind"] == "orphan_head"


def test_whitespace_only_change_is_caught(tmp_path):
    """The chain is over bytes, so a re-spelled but equivalent record breaks it.

    That is the intended strictness: the question is "are these the bytes that
    were written", not "does this parse to the same object".
    """
    path = _ledger(tmp_path)
    lines = _lines(path)
    rec = json.loads(lines[1].decode("utf-8"))
    lines[1] = json.dumps(rec, sort_keys=True, indent=None,
                          separators=(", ", ": ")).encode("utf-8")
    _rewrite(path, lines)
    assert verify_chain.verify(path)["verdict"] == "FAIL"


def test_rewriting_the_whole_chain_is_NOT_caught_without_a_published_head(tmp_path):
    """The honest limit, pinned as a test so nobody oversells the property.

    A forger who rewrites every line and recomputes the chain end to end
    produces a file that verifies.  Only the head published outside the file
    catches that -- which is why `--expect-head` exists.
    """
    path = _ledger(tmp_path)
    real_head = verify_chain.verify(path)["head"]

    forged = str(tmp_path / "forged.jsonl")
    led = Ledger(forged)
    for i in range(6):
        led.append("env_meta", "r1", "probe", http={"step": i * 1000})

    assert verify_chain.verify(forged)["verdict"] == "PASS", \
        "a wholly rewritten chain is internally consistent -- that is the point"
    assert verify_chain.verify(forged)["head"] != real_head, \
        "but it cannot reproduce the head that was published"


def test_expect_head_catches_the_wholesale_rewrite(tmp_path, capsys):
    path = _ledger(tmp_path)
    published = verify_chain.verify(path)["head"]

    forged = str(tmp_path / "forged.jsonl")
    led = Ledger(forged)
    for i in range(6):
        led.append("env_meta", "r1", "probe", http={"step": i * 1000})

    assert verify_chain.main([forged, "--expect-head", published]) == 1
    assert verify_chain.main([path, "--expect-head", published]) == 0


# ------------------------------------------------------- unchained and empty

def test_a_stream_with_no_prev_is_unchained_not_verified(tmp_path):
    """"No chain" must never report as "chain verified"."""
    path = str(tmp_path / "v0.jsonl")
    rec = {"v": "1.0", "event": "env_meta", "seq": 1, "ts": "2026-07-28T00:00:00.000Z",
           "run_id": "r1", "arm": "probe", "http": {}}
    _rewrite(path, [json.dumps(rec, sort_keys=True, separators=(",", ":")).encode()])
    report = verify_chain.verify(path)
    assert report["verdict"] == "UNCHAINED", report
    assert verify_chain.main([path]) == 2


def test_an_empty_file_is_not_a_pass(tmp_path):
    path = str(tmp_path / "empty.jsonl")
    open(path, "wb").close()
    report = verify_chain.verify(path)
    assert report["verdict"] == "EMPTY", report
    assert verify_chain.main([path]) != 0


def test_a_missing_file_is_not_a_pass(tmp_path):
    report = verify_chain.verify(str(tmp_path / "nope.jsonl"))
    assert report["verdict"] == "MISSING"


def test_partially_chained_stream_is_reported_as_partial(tmp_path):
    """A file written across the change that introduced the chain."""
    path = str(tmp_path / "mixed.jsonl")
    old = {"v": "1.0", "event": "env_meta", "seq": 1, "ts": "2026-07-28T00:00:00.000Z",
           "run_id": "r1", "arm": "probe", "http": {}}
    _rewrite(path, [json.dumps(old, sort_keys=True, separators=(",", ":")).encode()])
    Ledger(path).append("env_meta", "r1", "probe", http={"step": 2})
    report = verify_chain.verify(path)
    assert report["verdict"] == "PARTIAL", report
    assert report["unchained"] == 1 and report["chained"] == 1


def test_one_unreadable_line_does_not_destroy_the_rest(tmp_path):
    """RED-44's shape: a garbage line is a break, not an exception."""
    path = _ledger(tmp_path)
    lines = _lines(path)
    lines[2] = b"{not json at all"
    _rewrite(path, lines)
    report = verify_chain.verify(path)
    assert report["verdict"] == "FAIL"
    assert any(b["kind"] == "unreadable" for b in report["breaks"])
    assert report["lines"] == 6, "the walk continued past the bad line"


# ---------------------------------------------------------------- the writer

def test_a_caller_cannot_set_prev(tmp_path):
    """If a caller could supply `prev`, the chain would be forgeable in-band."""
    from proxy import canon
    led = Ledger(str(tmp_path / "l.jsonl"))
    with pytest.raises(canon.NonCanonicalField):
        led.append("env_meta", "r1", "probe", http={}, prev="sha256:deadbeef")


def test_the_cli_runs_as_a_module(tmp_path):
    path = _ledger(tmp_path, n=3)
    repo = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    r = subprocess.run([sys.executable, "-m", "proxy.tools.verify_chain",
                        path, "--json"],
                       cwd=repo, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    assert r.returncode == 0, r.stdout + r.stderr
    assert json.loads(r.stdout)["verdict"] == "PASS"
