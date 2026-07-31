"""S44: a gate's own runtime is a measurement, and nothing was taking it.

`monitor/tests` grew from tens of seconds to minutes to (under load) half an
hour, and not one thing in this repository said a word while it happened. Every
single run still printed `passed`. The cost only became visible on the day it
started lying: `verify.py`'s pytest stage had a 900-second ceiling, the
`TimeoutExpired` propagated out of the stage, the gate crashed, and `ci_merge`
wrote it down as `verify gate red in monitor` -- holding **nine delivered
branches** for a defect none of them had, one of them being the branch carrying
the fix.

Two things are held here.

## 1. The timeout must not be able to masquerade as a red suite

This is the whole cost of the incident in one property. `_tests()` returns 124
-- the conventional timeout code, distinguishable from pytest's own 1 -- and
says in words that nothing was proved either way. A test that only checked "the
gate goes non-zero on timeout" would have passed against the broken version too,
because the broken version went non-zero by crashing.

## 2. The one expensive check stays exactly one

`conftest.real_scan` collapsed six real `scan.build()` calls into one and took
338.7s off a 460.8s suite (measured 2026-07-31, `pytest --durations=50`). That
saving is one `scan.build(` away from being undone by a well-meaning seventh
test, and nothing about the suite's output would look different -- it would just
be a minute slower, again, invisibly, which is the shape of the whole item.

Deliberately **not** held here: a hard assertion that the suite finishes within
N seconds. Wall-clock on this box is contended -- the 30-minute figure in the
original report was measured with six concurrent pytest processes, against
460.8s idle -- so such a test would go red on a busy afternoon and hold branches
for a machine's mood. That is the exact harm being repaired, and re-creating it
one layer up would be a poor trade. The budget is reported by the gate on every
run instead (`verify.py:TESTS_BUDGET_S`), so growth is visible in the merge log
rather than enforced by a coin flip. The reasoning is written down in
`monitor/DECISIONS.md` under S44-a.
"""

import os
import re
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import verify                                                    # noqa: E402

TESTS = os.path.dirname(os.path.abspath(__file__))


# ------------------------------------------------- 1. the manufactured timeout

def test_a_suite_that_times_out_is_124_and_not_a_red_suite(tmp_path,
                                                           monkeypatch):
    """The negative sample. A test built to exceed the ceiling; require 124.

    The verdict a reader acts on is the *number*, so the number is what is
    asserted. 1 means "your branch broke something". 124 means "the gate ran out
    of clock and knows nothing about your branch". Nine branches were held
    because those two were the same observation.
    """
    slow = tmp_path / "tests"
    slow.mkdir()
    (slow / "test_glacier.py").write_text(
        "import time\n\n\ndef test_slower_than_the_gate():\n"
        "    time.sleep(30)\n", encoding="utf-8")

    monkeypatch.setattr(verify, "HERE", str(tmp_path))
    monkeypatch.setattr(verify, "TESTS_TIMEOUT_S", 3)

    label, code, detail = verify._tests()

    assert label == "tests"
    assert code == 124, \
        "a timeout reported as 1 is a branch blamed for the machine's clock"
    assert "TIMED OUT" in detail
    assert "NOT a red suite" in detail


def test_a_genuinely_failing_suite_is_still_1(tmp_path, monkeypatch):
    """Companion green -- or rather, companion red.

    Without this, `_tests()` could return 124 unconditionally and satisfy the
    test above while making every real failure unreportable. The pair is the
    check; neither half alone is.
    """
    suite = tmp_path / "tests"
    suite.mkdir()
    (suite / "test_no.py").write_text(
        "def test_no():\n    assert False, 'manufactured failure'\n",
        encoding="utf-8")

    monkeypatch.setattr(verify, "HERE", str(tmp_path))
    monkeypatch.setattr(verify, "TESTS_TIMEOUT_S", 120)

    _, code, detail = verify._tests()

    assert code == 1, "a real failure must not hide behind the timeout code"
    assert "TIMED OUT" not in detail
    assert "manufactured failure" in detail


def test_a_passing_suite_is_0_and_carries_its_duration(tmp_path, monkeypatch):
    """The third outcome, and the measurement the incident happened without.

    Elapsed seconds are on the stage's own detail, every run, green or red. That
    is the actual repair for "the gate's cost is invisible": a number in the
    merge log that a reader can watch grow.
    """
    suite = tmp_path / "tests"
    suite.mkdir()
    (suite / "test_ok.py").write_text("def test_ok():\n    assert True\n",
                                      encoding="utf-8")

    monkeypatch.setattr(verify, "HERE", str(tmp_path))
    monkeypatch.setattr(verify, "TESTS_TIMEOUT_S", 120)

    _, code, detail = verify._tests()

    assert code == 0
    assert re.search(r"took \d+(\.\d+)?s", detail), \
        "the stage must state how long it took, or growth stays invisible again"


def test_the_over_budget_line_appears_only_when_over_budget(tmp_path,
                                                            monkeypatch):
    """Loud, and only when it means something.

    A banner printed on every run is wallpaper; the reason `probe`-shaped things
    get switched off in this repo is that they cried wolf. So the budget line is
    manufactured here by shrinking the budget rather than by slowing the suite.
    """
    suite = tmp_path / "tests"
    suite.mkdir()
    (suite / "test_ok.py").write_text(
        "import time\n\n\ndef test_ok():\n    time.sleep(1.5)\n",
        encoding="utf-8")
    monkeypatch.setattr(verify, "HERE", str(tmp_path))
    monkeypatch.setattr(verify, "TESTS_TIMEOUT_S", 120)

    monkeypatch.setattr(verify, "TESTS_BUDGET_S", 1)
    _, code, over = verify._tests()
    assert code == 0, "over budget is not a failure -- the suite passed"
    assert "OVER BUDGET" in over

    monkeypatch.setattr(verify, "TESTS_BUDGET_S", 600)
    _, _, under = verify._tests()
    assert "OVER BUDGET" not in under


def test_the_budget_is_below_the_timeout(tmp_path):
    """Otherwise the suite reports its own obesity only after the ceiling has
    already misreported it as a failure -- which is the incident, verbatim."""
    assert verify.TESTS_BUDGET_S < verify.TESTS_TIMEOUT_S
    assert verify.TESTS_BUDGET_S == 300, \
        "S44's target is 300s; moving it is a decision, not a tweak"


# ---------------------------------------- 2. the expensive check stays one

_REAL_BUILD = re.compile(r"scan\.build\s*\(\s*False")
#: The opt-out. Not a suppression -- a signature: whoever writes it is stating
#: that this call does not complete a scan (it raises first, or it is a string
#: literal in another test's fixture) or that it must, and why.
_EXEMPT = "real-scan-exempt:"


def _unexempted_builds(name):
    src = open(os.path.join(TESTS, name), encoding="utf-8").read().splitlines()
    out = []
    for i, line in enumerate(src):
        if not _REAL_BUILD.search(line):
            continue
        # Four lines of context: a reason worth writing rarely fits on one, and
        # the call is often wrapped in a `with pytest.raises(...)` of its own.
        window = "\n".join(src[max(0, i - 4):i + 1])
        if _EXEMPT not in window:
            out.append("%s:%d" % (name, i + 1))
    return out


def test_only_the_shared_fixture_runs_a_real_scan():
    """A seventh real `scan.build()` would put ~55s back, invisibly.

    Load-independent on purpose: this reads the sources rather than timing
    anything, so it means the same thing on an idle box and a contended one.
    A test that genuinely needs its own scan is not forbidden -- it is required
    to write `# real-scan-exempt: <reason>` on or just above the call, which is
    the whole difference between a considered exception and a silent
    regression.
    """
    allowed = {"conftest.py", os.path.basename(__file__)}
    offenders = []
    for name in sorted(os.listdir(TESTS)):
        if not name.endswith(".py") or name in allowed:
            continue
        offenders += _unexempted_builds(name)
    assert offenders == [], (
        "these run their own real scan.build instead of the session fixture "
        "`real_scan`; each costs ~55s and six of them were 74%% of the suite. "
        "If one of them genuinely must, say so with `# %s <reason>`: %s"
        % (_EXEMPT, ", ".join(offenders)))


def test_the_exemption_is_a_declaration_and_not_a_blanket(tmp_path,
                                                          monkeypatch):
    """Positive control for the check above -- it must be able to fire.

    A source-reading guard that matched nothing would pass forever and look
    exactly like compliance, which is the failure mode this repository named in
    `test_gate_does_not_dirty_the_tree.py` and then repeated twice elsewhere.
    """
    monkeypatch.setattr(sys.modules[__name__], "TESTS", str(tmp_path))
    (tmp_path / "test_sneaky.py").write_text(
        "import scan\n\n\ndef test_x(tmp_path):\n"
        "    scan.build(False, out_dir=str(tmp_path))\n", encoding="utf-8")
    assert _unexempted_builds("test_sneaky.py") == ["test_sneaky.py:5"]

    (tmp_path / "test_declared.py").write_text(
        "import scan\n\n\ndef test_x(tmp_path):\n"
        "    # real-scan-exempt: raises before the scan does any work\n"
        "    scan.build(False, out_dir=str(tmp_path))\n", encoding="utf-8")
    assert _unexempted_builds("test_declared.py") == []


def test_the_shared_fixture_really_is_a_real_scan(real_scan):
    """The saving is only legitimate if what it shares is the genuine article.

    A fixture that stubbed `build` would make every consumer fast and every
    consumer meaningless -- the same trade the item forbids, dressed as a
    speed-up.
    """
    assert real_scan.files == ["history.jsonl", "index.html", "state.json"]
    assert real_scan.state["scan_ok"] is True
    assert isinstance(real_scan.state.get("findings"), list)
    assert real_scan.state["findings"], \
        "every probe returned nothing -- that is a stubbed scan, not a scan"
    assert len(real_scan.page) > 10000, "the rendered page is a real page"
