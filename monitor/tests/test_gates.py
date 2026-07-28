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
    assert row["cmd"][0] == "bash"


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
    assert set(survey["ungated"]) <= {"CONTRACTS", "browser-ops", "papers",
                                      "release"}, survey["ungated"]
    assert "proxy" in survey["non_canonical"]


def test_describe_makes_an_ungated_merge_readable():
    assert gates.describe({"kind": "none"}, "papers") == "UNGATED:papers"
    assert gates.describe({"kind": "pytest"}, "engine-rig") == "pytest:engine-rig"
    assert gates.describe({"kind": "verify", "name": "verify.py"},
                          "exam") == "verify:exam(verify.py)"
