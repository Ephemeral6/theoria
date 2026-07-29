"""The two halves of S13: the merge rig runs a gate, and says when there is none.

Neither half is testable by reading `ci_merge.py` — the interesting behaviour is
what lands in `merge.log`, and the whole point of S13 is that the log used to say
the same thing whether a gate ran or not.
"""

from __future__ import annotations

import os
import sys

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(HERE)
for path in (HERE, ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

import ci_merge                                                    # noqa: E402
import gates                                                       # noqa: E402
import scan                                                        # noqa: E402


# ------------------------------------------------- the rig asks one authority

def test_ci_merge_and_the_probe_read_the_same_answer():
    """Two implementations of "what is this territory's gate" drift. The last
    time they did, 509 tests sat unrun and the hand-written repair got four of
    seven entries wrong in the same commit."""
    for name in gates.territories(ROOT):
        assert ci_merge.gate_for(ROOT, name) == gates.gate_for(ROOT, name), name


def test_an_override_still_wins(monkeypatch):
    monkeypatch.setitem(ci_merge.TEST_CMDS, "exam", ["echo", "override"])
    row = ci_merge.gate_for(ROOT, "exam")
    assert row["kind"] == "pytest" and row["cmd"] == ["echo", "override"]


def test_a_verify_script_supersedes_the_test_suite(tmp_path):
    """Running both would double the slowest part of a merge to re-check what
    the gate just checked, and a merge rig that is slow gets bypassed."""
    (tmp_path / "t").mkdir()
    (tmp_path / "t" / "verify.sh").write_text("exit 0\n")
    (tmp_path / "t" / "test_x.py").write_text("def test_x(): pass\n")
    assert gates.gate_for(str(tmp_path), "t")["kind"] == "verify"


# --------------------------------------------- the log has to say what ran

def test_the_merge_log_line_names_gated_and_ungated_separately():
    """The shape of the line, built the way `try_merge` builds it."""
    # The `pytest` rung is built from a synthetic row rather than from a real
    # territory.  S14 gave every territory that had a suite its own verify
    # script, so there is currently no tests-only territory left to name here --
    # and a test that silently stopped exercising one of the three kinds because
    # the tree moved under it is the failure this whole module is about.
    ran = [gates.describe(gates.gate_for(ROOT, "exam"), "exam"),
           gates.describe({"kind": "pytest"}, "engine-rig")]
    ungated = ["papers"]
    parts = ["MERGED b (dirs: exam,engine-rig,papers; gates: %s" % ",".join(ran)]
    parts.append("; NO GATE, MERGED UNCHECKED: %s" % ",".join(ungated))
    parts.append(")")
    line = "".join(parts)
    assert "verify:exam(verify.py)" in line
    assert "pytest:engine-rig" in line
    assert "NO GATE, MERGED UNCHECKED: papers" in line


def test_ci_merge_still_refuses_a_red_verify_gate():
    """Source-level, because the alternative is merging a branch to prove it.

    The two failure paths must be distinguishable in the flag: a red `verify`
    and a red `pytest` are different reports, and a reader who cannot tell them
    apart cannot tell whether the territory's own gate exists.
    """
    source = open(os.path.join(HERE, "ci_merge.py"), encoding="utf-8").read()
    assert 'verify gate red in' in source
    assert 'tests red in' in source
    assert 'NO GATE, MERGED UNCHECKED' in source
    assert 'a gate dirtied the worktree' in source


# ------------------------------------------- a gate must not dirty the tree

def test_a_real_scan_can_run_without_touching_the_workspace(tmp_path):
    """S13's explicit warning, made executable.

    `scan.build` used to write `state.json`, `index.html` and `history.jsonl`
    into `monitor/` unconditionally, so `monitor`'s own gate could not run a
    real scan without dirtying the tree it was gating -- and a gate that dirties
    the tree can turn the *next* territory's gate red for a reason that has
    nothing to do with the branch.
    """
    out = str(tmp_path)
    scan.build(False, out_dir=out)
    written = sorted(os.listdir(out))
    assert written == ["history.jsonl", "index.html", "state.json"]
    for name in written:
        assert os.path.getsize(os.path.join(out, name)) > 0, name


# ------------------------------------------------------------- the probe

def test_the_probe_separates_claimed_but_absent_from_never_had_one():
    result = scan.probe_verify_gates()
    assert result["status"] in ("green", "amber", "risk")
    detail = result["detail"]
    if result["status"] == "amber":
        assert "无人检查" in detail
        assert "从来没人要求过" in detail, (
            "an ungated territory is not somebody breaking a promise, and a "
            "report that reads like an accusation gets switched off")
    assert "领地" in detail


def test_prose_naming_a_rule_is_not_read_as_a_missing_file(tmp_path, monkeypatch):
    """The false positive S13's own ticket text produced on the first run.

    `若该领地存在 verify.sh/verify.py 就必须跑它` was read as a claim that a
    file called `verify.sh/verify.py` exists. A checker that cries wolf is a
    checker that gets switched off, and a switched-off checker and an absent
    one are the same thing.
    """
    board = tmp_path / "monitor" / "board" / "items"
    board.mkdir(parents=True)
    (board / "X.md").write_text(
        "若该领地存在 verify.sh/verify.py 就必须跑它\n"
        "并且 exam/verify.py 必须绿\n", encoding="utf-8")
    monkeypatch.setattr(scan, "ROOT", ROOT)
    result = scan.probe_verify_gates()
    assert "verify.sh/verify.py（" not in result["detail"], (
        "the rule sentence was read as a path claim")


def test_the_probe_would_still_catch_a_named_script_that_was_never_built():
    """The original DRIFT it was written for: C2 merged naming a
    `a0-spike/verify.sh` that was never created."""
    import re

    pattern = re.compile(r"([\w./-]+/verify[\w.-]*\.(?:sh|py))")
    known = set(gates.territories(ROOT))
    hit = pattern.search("交付前 a0-spike/verify.sh 必须绿")
    assert hit and hit.group(1).split("/")[0] in known
    assert not os.path.exists(os.path.join(ROOT, hit.group(1)))
