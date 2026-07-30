"""The flag must keep the cause, not merely the end of the transcript.

`r2-release-licence` was flagged every five minutes for nineteen hours with a
record that is a wall of `-- ok` notes ending in `VERIFY: RED`. Nothing in it
says which step failed, because the flag kept `detail[-4000:]` and a verbose
gate's last 4000 characters are the part *after* the failure.

Same shape as everything else in this lane, one level up: the instrument ran,
produced output, and the output omitted the finding. A record that cannot be
acted on is barely better than none, and worse in one way -- it looks like one.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ci_merge                                                 # noqa: E402


def _verbose_gate(cause="   FAIL  licence check exited 2"):
    """The r2 shape: one failure early, hundreds of reassuring lines after."""
    noise = "\n".join("  note   everything fine here %d" % i
                      for i in range(500))
    return "step 3 of 7\n%s\n%s\nVERIFY: RED" % (cause, noise)


def test_the_cause_survives_when_the_old_truncation_would_have_lost_it():
    detail = _verbose_gate()
    assert "licence check exited 2" not in detail[-4000:], (
        "this test is meaningless unless the old rule really did lose it")
    out = ci_merge.excerpt(detail)
    assert "licence check exited 2" in out


def test_the_tail_is_still_kept_for_context():
    out = ci_merge.excerpt(_verbose_gate())
    assert "VERIFY: RED" in out


def test_a_transcript_with_no_recognisable_cause_falls_back_to_the_tail():
    """Unrecognised must not mean empty.

    A gate whose failure wording this module has never seen still deserves the
    old behaviour, not a blank record.
    """
    detail = "\n".join("  note %d" % i for i in range(500))
    out = ci_merge.excerpt(detail)
    assert out == detail[-ci_merge._KEEP_TAIL:]
    assert out.strip()


def test_common_failure_wordings_are_all_recognised():
    for cause in ("FAILED tests/test_x.py::test_y",
                  "E       assert 1 == 0",
                  "Traceback (most recent call last):",
                  "TypeError: Law.__init__() got an unexpected keyword",
                  "ModuleNotFoundError: No module named 'battery'",
                  "/bin/bash: No such file or directory",
                  "   FAIL  suite red (exit 1)",
                  "verify gate red in release (verify.sh)",
                  "run_all exited 3"):
        out = ci_merge.excerpt(_verbose_gate(cause))
        assert cause.strip()[:24] in out, cause


def test_the_excerpt_is_bounded():
    """A flag file is read by a human; an unbounded one is not read at all."""
    huge = "\n".join("FAILED test_%d.py::case" % i for i in range(5000))
    out = ci_merge.excerpt(huge)
    assert len(out) < 20000, len(out)
    assert "more cause line(s)" in out, "silent truncation is the thing we fix"


def test_empty_detail_does_not_crash():
    assert ci_merge.excerpt("") == ""
    assert ci_merge.excerpt(None) == ""
