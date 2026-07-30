"""S43 second half: ci_merge blamed nine branches for a red master could not see.

`unmerged_branches()` enumerates `origin/agent/*` and nothing else, so a commit
made directly onto master is gated by nothing -- there is no code path in
`ci_merge.py` that runs a gate against an unmerged `origin/master`. When
`873d62ee` went straight onto master and turned `monitor`'s suite red, the gate
noticed 9m47s later (04:29:32Z MERGED with monitor green -> 04:55:40Z the commit
-> 05:05:27Z the first FLAG) and wrote the red down against the next branch that
happened to touch `monitor/`. Nine branches were held that way, the longest for
6h41m, and every one of them had a failure set byte-identical to master's with
zero novel failures. The instrument was firing correctly and blaming the wrong
party every time.

`base_verdict` / `blame_the_base` are the attribution fix. These tests drive
them against a stubbed `sh`, because the real thing runs a 500-second gate.
"""

import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import ci_merge                     # noqa: E402


class _R:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


@pytest.fixture
def flag_sandbox(tmp_path, monkeypatch):
    """Redirect `flag()`'s real file writes into tmp_path, and nothing more.

    Deliberately touches **no symbol this item added**. The counter tests below
    are about `flag()`, which has existed all along, so their red on an
    unpatched master has to be a behavioural red -- an inherited `attempts` --
    and not an AttributeError from a fixture reaching for `BASE_MEMO`. The first
    draft of this file used one shared fixture and every test on master errored
    at fixture setup, which proves the symbol is new and nothing whatever about
    the behaviour. That is the weak evidence this whole item is about.
    """
    monkeypatch.setattr(ci_merge, "CI_DIR", str(tmp_path))
    monkeypatch.setattr(ci_merge, "flag_path",
                        lambda b: str(tmp_path / ("F-%s.md" % b.replace("/", "_"))))
    lines = []
    monkeypatch.setattr(ci_merge, "log_line", lines.append)
    monkeypatch.setattr(ci_merge, "branch_tip", lambda b: "BASE0000")
    return lines


@pytest.fixture
def isolated_ci(tmp_path, monkeypatch, flag_sandbox):
    """`flag_sandbox` plus the base-probe machinery this item introduced."""
    monkeypatch.setattr(ci_merge, "BASE_MEMO", str(tmp_path / "base_gates.json"))
    monkeypatch.setattr(ci_merge.gates, "gate_env", lambda wt: {})
    return flag_sandbox


ROW = {"kind": "verify", "cmd": ["pytest"], "name": "verify.sh"}


def _stub_sh(monkeypatch, gate_rc, checkout_rc=0, calls=None):
    def fake(args, cwd=None, timeout=None, extra_env=None):
        if calls is not None:
            calls.append(args)
        if args[:2] == ["git", "checkout"]:
            return _R(checkout_rc)
        if args[:2] == ["git", "clean"]:
            return _R(0)
        return _R(gate_rc, stdout="gate output")
    monkeypatch.setattr(ci_merge, "sh", fake)


# --------------------------------------------------------------------------
# base_verdict
# --------------------------------------------------------------------------

def test_a_red_base_is_reported_as_red(isolated_ci, monkeypatch, tmp_path):
    _stub_sh(monkeypatch, gate_rc=1)
    assert ci_merge.base_verdict(str(tmp_path), "monitor", ROW, "BASE0000") == 1


def test_a_green_base_is_reported_as_green(isolated_ci, monkeypatch, tmp_path):
    """NEGATIVE CONTROL. If this ever returns non-zero the fix exonerates every
    branch and the gate stops meaning anything at all."""
    _stub_sh(monkeypatch, gate_rc=0)
    assert ci_merge.base_verdict(str(tmp_path), "monitor", ROW, "BASE0000") == 0


def test_a_probe_that_could_not_run_is_None_and_never_green(isolated_ci,
                                                            monkeypatch,
                                                            tmp_path):
    """The single most dangerous failure direction in this whole change.

    Returning 0 when the base could not be measured silently restores
    branch-blaming -- the exact bug -- while looking like it is working.
    """
    _stub_sh(monkeypatch, gate_rc=1, checkout_rc=1)
    v = ci_merge.base_verdict(str(tmp_path), "monitor", ROW, "BASE0000")

    assert v is None
    assert v != 0, "a failed probe must not read as 'the base is clean'"


def test_the_verdict_is_memoised_per_master_sha_and_territory(isolated_ci,
                                                              monkeypatch,
                                                              tmp_path):
    """Nine branches tripping over one red master must pay for one gate run,
    not nine. Today they each pay ~500s to re-derive the identical verdict."""
    calls = []
    _stub_sh(monkeypatch, gate_rc=1, calls=calls)

    ci_merge.base_verdict(str(tmp_path), "monitor", ROW, "BASE0000")
    runs_after_first = len([c for c in calls if c == ["pytest"]])
    ci_merge.base_verdict(str(tmp_path), "monitor", ROW, "BASE0000")
    ci_merge.base_verdict(str(tmp_path), "monitor", ROW, "BASE0000")

    assert runs_after_first == 1
    assert len([c for c in calls if c == ["pytest"]]) == 1, (
        "the gate was re-run despite a memoised verdict")

    memo = json.load(open(tmp_path / "base_gates.json", encoding="utf-8"))
    assert memo == {"BASE0000/monitor": 1}


def test_a_new_master_sha_is_measured_again(isolated_ci, monkeypatch, tmp_path):
    """NEGATIVE CONTROL for the memo: keyed on the sha, so a fixed master is
    re-measured rather than remembered as broken forever."""
    calls = []
    _stub_sh(monkeypatch, gate_rc=0, calls=calls)

    ci_merge.base_verdict(str(tmp_path), "monitor", ROW, "BASE0000")
    ci_merge.base_verdict(str(tmp_path), "monitor", ROW, "BASE1111")

    assert len([c for c in calls if c == ["pytest"]]) == 2


# --------------------------------------------------------------------------
# blame_the_base -- who the log names
# --------------------------------------------------------------------------

def test_a_red_base_names_master_and_spares_the_branch(isolated_ci, monkeypatch,
                                                       tmp_path):
    _stub_sh(monkeypatch, gate_rc=1)
    lines = isolated_ci

    blamed = ci_merge.blame_the_base("origin/agent/innocent", str(tmp_path),
                                     "monitor", ROW, "verify gate red in monitor",
                                     "detail", "TIP1")

    assert blamed is True
    assert not os.path.exists(tmp_path / "F-origin_agent_innocent.md"), (
        "the innocent branch got a flag file anyway, so its attempts counter "
        "still inflates and it still reads as a broken branch")
    assert any("BASE RED" in l and "origin/master" in l for l in lines)
    assert any("NOT at fault" in l for l in lines)


def test_a_green_base_still_blames_the_branch(isolated_ci, monkeypatch,
                                              tmp_path):
    """NEGATIVE CONTROL, and the one that keeps the gate a gate. A branch that
    genuinely breaks a green master must still be caught and named."""
    _stub_sh(monkeypatch, gate_rc=0)

    blamed = ci_merge.blame_the_base("origin/agent/guilty", str(tmp_path),
                                     "monitor", ROW, "tests red in monitor",
                                     "detail", "TIP1")

    assert blamed is False, "a branch that broke a clean master was exonerated"


def test_an_unmeasurable_base_blames_nobody_silently(isolated_ci, monkeypatch,
                                                     tmp_path):
    _stub_sh(monkeypatch, gate_rc=1, checkout_rc=1)

    blamed = ci_merge.blame_the_base("origin/agent/unknown", str(tmp_path),
                                     "monitor", ROW, "tests red in monitor",
                                     "detail", "TIP1")

    assert blamed is False
    flag = open(tmp_path / "F-origin_agent_unknown.md", encoding="utf-8").read()
    assert "could not determine" in flag, (
        "an unmeasurable base must say so on the flag, not quietly pick a side")


def test_the_master_flag_line_starts_with_FLAG(isolated_ci, monkeypatch,
                                               tmp_path):
    """`reflex.merge_events` scrapes merge.log with a literal
    `startswith("MERGED")` / `startswith("FLAG")`. A line beginning `ALARM` or
    `MASTER-RED` would be written here and never reach reflex.log or the
    dashboard -- a fix invisible in exactly the way the bug was.
    """
    _stub_sh(monkeypatch, gate_rc=1)
    lines = isolated_ci

    ci_merge.blame_the_base("origin/agent/x", str(tmp_path), "monitor", ROW,
                            "tests red in monitor", "detail", "TIP1")

    base_lines = [l for l in lines if "BASE RED" in l]
    assert base_lines, "nothing was logged at all"
    for l in base_lines:
        assert l.startswith("FLAG"), (
            "reflex scrapes for a FLAG prefix; %r will never be seen" % l[:40])


# --------------------------------------------------------------------------
# the counter that lied
# --------------------------------------------------------------------------

class _Clock:
    """A controlled clock. Wall time makes the `first_seen` assertion below a
    coin flip: four `flag()` calls land in the same second, so a carried-forward
    stamp and a freshly-taken one compare equal and the test passes on the bug.
    """

    def __init__(self):
        self.t = 0

    def gmtime(self):
        return self.t

    def strftime(self, fmt, t):
        return "2026-07-30T00:00:%02dZ" % t


def test_a_different_failure_does_not_inherit_the_old_counter(flag_sandbox,
                                                              monkeypatch,
                                                              tmp_path):
    """`a3-campaign-devpile` wore `NEEDS-HUMAN: 28 attempts since 07-29T04:14`
    assembled from three unrelated reasons under one counter, and that badge --
    which reads as "chronically broken branch" -- is why it was written off."""
    clock = _Clock()
    monkeypatch.setattr(ci_merge, "time", clock)
    b = "origin/agent/a3"
    for _ in range(3):
        ci_merge.flag(b, "tests red in theoria-arm", "d")
        clock.t += 10
    same = ci_merge.last_attempt(b)
    assert same["attempts"] == "3", "the same failure must keep accumulating"
    assert same["first_seen"] == "2026-07-30T00:00:00Z"

    ci_merge.flag(b, "verify gate red in monitor", "d")
    fresh = ci_merge.last_attempt(b)

    assert fresh["attempts"] == "1", (
        "a brand-new failure inherited the old reason's count (%s)"
        % fresh["attempts"])
    assert fresh["first_seen"] == "2026-07-30T00:00:30Z", (
        "the new failure inherited the old one's start time (%s), so the badge "
        "claims a duration that never happened" % fresh["first_seen"])


def test_the_same_failure_still_reaches_needs_human(flag_sandbox, tmp_path):
    """NEGATIVE CONTROL: resetting on a changed reason must not defeat the
    escalation. Three attempts at one reason still has to summon a human."""
    lines = flag_sandbox
    b = "origin/agent/stuck"
    for _ in range(3):
        ci_merge.flag(b, "tests red in monitor", "d")

    assert any("NEEDS-HUMAN" in l for l in lines), (
        "a genuinely stuck branch stopped escalating")
