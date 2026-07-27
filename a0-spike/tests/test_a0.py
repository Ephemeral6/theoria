"""A0 acceptance: the cold-start loop closes, and its verdicts match ground truth."""

import os
import sys

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "engine-rig"))

from pipeline import explore, run_a0, stages          # noqa: E402
from world import levels, sokoban2                    # noqa: E402


@pytest.fixture(scope="module")
def report():
    return run_a0.run()


# ------------------------------------------------------------------ the world

def test_the_conservation_law_actually_holds():
    """A push moves the box two cells, so each coordinate's parity survives."""
    for name, level in levels.LEVELS.items():
        cells = sokoban2.reachable_box_cells(level)
        assert len({(r + c) % 2 for r, c in cells}) == 1, name
        assert len({r % 2 for r, c in cells}) == 1, name
        assert len({c % 2 for r, c in cells}) == 1, name


def test_the_two_levels_differ_only_in_the_target():
    assert levels.MATCH.box == levels.MISMATCH.box
    assert levels.MATCH.player == levels.MISMATCH.player
    assert levels.MATCH.walls == levels.MISMATCH.walls
    assert levels.MATCH.target != levels.MISMATCH.target


def test_ground_truth_solvability_is_what_the_design_intended():
    truth = levels.ground_truth()
    assert truth["match"]["solvable"] is True
    assert truth["match"]["optimal_plan_length"] == 2
    assert truth["mismatch"]["solvable"] is False
    assert truth["match"]["parity_matches"] is True
    assert truth["mismatch"]["parity_matches"] is False


# --------------------------------------------------------------- the pipeline

def test_perception_finds_two_movers_and_a_board(report):
    assert report["perceive"]["movers"] == 2
    assert report["perceive"]["board"] >= 3


def test_the_edit_script_beats_the_pixel_baseline(report):
    assert report["perceive"]["script_bits"] < report["perceive"]["baseline_bits"]


def test_push_rules_require_the_box_to_have_somewhere_to_go(report):
    """The under-guarded first pass is the bug; this is the fix (THEORIZE_LOG T-4)."""
    pushes = [r for r in report["mine"]["rules"] if r["name"].startswith("push2")]
    assert len(pushes) == 4
    for rule in pushes:
        direction = rule["name"].split("_")[1]
        assert "ahead_is_box(%s)" % direction in rule["guard"]
        assert "box_beyond_free(%s)" % direction in rule["guard"]
        assert int(rule["coverage"].split("/")[0]) >= 8


def test_walk_rules_are_the_simple_thing(report):
    walks = [r for r in report["mine"]["rules"] if r["name"].startswith("walk")]
    assert len(walks) == 4
    for rule in walks:
        direction = rule["name"].split("_")[1]
        assert sorted(rule["guard"]) == ["act==%s" % direction, "ahead_free(%s)" % direction]


def test_the_blocked_class_needed_more_than_one_conjunction(report):
    """It is genuinely disjunctive; sequential covering is why it is expressible."""
    blocked = [r for r in report["mine"]["rules"] if r["name"].startswith("blocked")]
    assert len(blocked) > 4, "a single rule per direction would mean the split failed"


def test_certify_replays_every_transition_exactly(report):
    certificate = report["certify"]
    assert certificate["transitions"] >= 300
    assert certificate["replay_exact"] is True
    assert certificate["replay_failures"] == []


def test_every_transition_has_exactly_one_successor(report):
    """Constraint 9, on the induced rules."""
    assert report["certify"]["exactly_one_successor"] is True
    assert report["certify"]["ambiguities"] == []


def test_the_conservation_law_is_recovered_from_the_trajectory(report):
    law = report["prove"]
    assert law["row_plus_col_is_conserved"] is True
    assert law["null_space_dimension"] == 2, "both coordinate parities are conserved"


# ------------------------------------------------------------- the two verdicts

def test_the_solvable_level_is_planned_and_won(report):
    entry = report["levels"]["match"]
    assert entry["planner_consulted"] is True
    assert entry["won"] is True
    assert entry["plan_length"] == levels.ground_truth()["match"]["optimal_plan_length"]


def test_the_plan_actually_moves_the_box_onto_the_target(report):
    """Executed in the world, not merely returned by the planner."""
    entry = report["levels"]["match"]
    assert tuple(entry["executed_box_at"]) == levels.MATCH.target


def test_the_unsolvable_level_is_refused_without_search(report):
    """The point of the theorem: no planner is consulted at all."""
    entry = report["levels"]["mismatch"]
    assert entry["theorem"]["unsolvable"] is True
    assert entry["planner_consulted"] is False
    assert entry["theorem"]["goal_breaks_invariant"] is True


def test_both_verdicts_agree_with_ground_truth(report):
    for name, grade in report["grading"].items():
        assert grade["agrees"], name


def test_the_theorem_explains_itself_in_the_manuals_vocabulary(report):
    explanation = report["levels"]["mismatch"]["theorem"]["explanation"]
    assert "奇偶" in explanation
    assert report["levels"]["mismatch"]["theorem"]["invariant"] == "(box.row + box.col) mod 2"


# ------------------------------------------------------------- determinism

def test_the_evidence_set_is_deterministic():
    a = explore.evidence_set(levels.MATCH, per_class=4)
    b = explore.evidence_set(levels.MATCH, per_class=4)
    assert [e["actions"] for e in a["episodes"]] == [e["actions"] for e in b["episodes"]]


def test_mining_is_deterministic():
    evidence = explore.evidence_set(levels.MATCH, per_class=4)
    transitions = stages.transitions_from_episodes(evidence["episodes"])
    first = [r.as_json() for r in stages.mine(transitions)]
    second = [r.as_json() for r in stages.mine(transitions)]
    assert first == second
