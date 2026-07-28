"""The gate table, which is not a table.

`ci_merge`'s own comment records what the last hand-maintained version cost:
*a table maintained by hand is a claim about the tree that nothing checks
against the tree.* These tests check the asking-the-tree against the tree.
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

import gates                                                       # noqa: E402


def test_the_three_kinds_are_the_whole_answer():
    for name in gates.territories(ROOT):
        row = gates.gate_for(ROOT, name)
        assert row["kind"] in ("verify", "pytest", "none"), name
        assert row["why"], name
        assert (row["cmd"] is None) == (row["kind"] == "none"), name


def test_a_territory_that_ships_a_gate_is_read_as_gated(tmp_path):
    (tmp_path / "t").mkdir()
    (tmp_path / "t" / "verify.sh").write_text("#!/bin/sh\nexit 0\n")
    row = gates.gate_for(str(tmp_path), "t")
    assert row["kind"] == "verify" and row["canonical"] is True
    # 旧断言是 `row["cmd"][0] == "bash"`——它断的是那个字符串，而**字符串一直是对的**：
    # PATH 上的 bash 是 WSL 的（另一个 Linux，没有 python），Windows 绝对路径里的
    # 反斜杠又被它当成转义吃掉。于是 8 条已交付分支被判成 verify gate red，
    # 而这条测试全程绿着（2026-07-29）。所以现在断的是**它跑得起来**。
    import subprocess
    r = subprocess.run(row["cmd"], cwd=str(tmp_path / "t"),
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, (row["cmd"], r.stdout, r.stderr)


def test_verify_py_counts_and_runs_under_this_interpreter(tmp_path):
    (tmp_path / "t").mkdir()
    (tmp_path / "t" / "verify.py").write_text("raise SystemExit(0)\n")
    row = gates.gate_for(str(tmp_path), "t")
    assert row["kind"] == "verify"
    assert row["cmd"][0] == sys.executable


def test_a_gate_under_another_name_is_found_and_said_to_be_unusual(tmp_path):
    """`proxy/verify_spend.sh` is a real gate under a non-canonical name.

    A matcher that knew only the two canonical names would call `proxy`
    ungated -- false, confident, and exactly the sort of report that gets a
    probe switched off.
    """
    (tmp_path / "t").mkdir()
    (tmp_path / "t" / "verify_spend.sh").write_text("exit 0\n")
    row = gates.gate_for(str(tmp_path), "t")
    assert row["kind"] == "verify"
    assert row["canonical"] is False
    assert row["name"] == "verify_spend.sh"


def test_the_canonical_name_wins_when_both_exist(tmp_path):
    (tmp_path / "t").mkdir()
    (tmp_path / "t" / "verify.sh").write_text("exit 0\n")
    (tmp_path / "t" / "verify_spend.sh").write_text("exit 0\n")
    assert gates.gate_for(str(tmp_path), "t")["name"] == "verify.sh"


def test_tests_are_the_gate_when_there_is_no_script(tmp_path):
    (tmp_path / "t" / "sub").mkdir(parents=True)
    (tmp_path / "t" / "sub" / "test_thing.py").write_text("def test_x(): pass\n")
    row = gates.gate_for(str(tmp_path), "t")
    assert row["kind"] == "pytest"
    assert "-m" in row["cmd"] and "pytest" in row["cmd"]


def test_nothing_to_run_says_so_rather_than_looking_like_a_pass(tmp_path):
    (tmp_path / "t").mkdir()
    row = gates.gate_for(str(tmp_path), "t")
    assert row["kind"] == "none"
    assert "nothing checking it" in row["why"]


def test_a_directory_that_does_not_exist_is_not_a_crash(tmp_path):
    """A branch can delete a territory. A merge rig that crashed on that would
    be worse than one that merged it."""
    assert gates.gate_for(str(tmp_path), "never-existed")["kind"] == "none"


def test_the_survey_partitions_every_territory_exactly_once():
    survey = gates.survey(ROOT)
    parts = survey["gated"] + survey["tests_only"] + survey["ungated"]
    assert sorted(parts) == sorted(survey["rows"])
    assert len(parts) == len(set(parts)) == survey["n_territories"]


def test_this_repository_is_where_the_survey_says_it_is():
    """Pinned deliberately. When a territory gains or loses a gate this test
    fails, and the correct response is to update it *and* say so in the item
    that changed it -- which is the visibility S13 exists to create."""
    survey = gates.survey(ROOT)
    assert "monitor" in survey["gated"], (
        "the rig that enforces gates must have one; it did not until S13")
    # fleet-study 是 2026-07-29 新落地的领地，尚无闸门——按上面那条规矩，
    # 更新这个集合的同时要说明：它的闸门由 S17-fleet-evidence-capture 负责补，
    # 补上之后这条测试会再红一次，那是对的。
    assert set(survey["ungated"]) <= {"CONTRACTS", "browser-ops", "papers",
                                      "release", "fleet-study",
                                      "verify-lab"}, survey["ungated"]
    assert "proxy" in survey["non_canonical"]


def test_describe_makes_an_ungated_merge_readable():
    assert gates.describe({"kind": "none"}, "papers") == "UNGATED:papers"
    assert gates.describe({"kind": "pytest"}, "engine-rig") == "pytest:engine-rig"
    assert gates.describe({"kind": "verify", "name": "verify.py"},
                          "exam") == "verify:exam(verify.py)"
