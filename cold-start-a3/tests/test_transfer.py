"""C3, as assertions.

The report's claims are here as tests, so that a reader who does not believe
`A3_REPORT.md` can run the suite instead of reading it.  Three of these are the
claim itself:

* `test_the_two_levels_compile_to_the_same_mechanism_code` — what "the domain
  travels" means at the level of an artefact you can diff;
* `test_the_transfer_arm_wrote_no_clause_and_ran_no_engine` — the bill's zeros,
  read off the meter rather than off the prose;
* `test_the_transfer_arm_planned_before_spending_an_action` — the front-loading
  shape C2 predicts and C3 cashes.
"""

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import pytest  # noqa: E402

import _bootstrap  # noqa: F401,E402

from a3pipeline import problem_frame  # noqa: E402

ARTIFACTS = os.path.join(HERE, "artifacts")
THEORY = os.path.join(HERE, "theory")


def _artifact(name):
    path = os.path.join(ARTIFACTS, name)
    if not os.path.exists(path):
        pytest.skip("%s absent — run `python run_all.py` first" % name)
    return json.load(open(path, encoding="utf-8"))


# ------------------------------------------------- the domain actually travels

#: Lines that are *allowed* to differ between two levels' generated
#: predictors.  Everything else is mechanism and must be identical.
LEVEL_DATA = re.compile(
    r"^(LANDMARKS|GRID|BACKGROUND)\b"
    r"|^\s*\[[\d,\s]+\],?\s*$"          # a BOARD row
    r"|^\s*return state\.Cart_pos == "  # the bound goal
    r"|^\s*\w+_pos=\(\d+, \d+\),"       # initial_state placements
    r"|^\s*\w+_colour=\d+,"
    r"|^\s*\w+_present=(True|False),"
)


def test_the_two_levels_compile_to_the_same_mechanism_code():
    """The strongest available form of "the domain travels".

    Both levels' `theory.py` is generated from the *same* `domain.dsl`.  If the
    split is real, the two files differ only where level data is interpolated —
    the landmark table, the board, the goal cell, the initial placements — and
    every guard and every effect is byte-identical.  That is checked here line
    by line rather than asserted, because "the same manual" is exactly the
    claim someone would want to see evidence for.
    """
    for name in ("generated_l1", "generated_l2"):
        if not os.path.exists(os.path.join(THEORY, name, "theory.py")):
            pytest.skip("%s absent — run `python run_all.py` first" % name)

    left = open(os.path.join(THEORY, "generated_l1", "theory.py"),
                encoding="utf-8").read().splitlines()
    right = open(os.path.join(THEORY, "generated_l2", "theory.py"),
                 encoding="utf-8").read().splitlines()

    import difflib
    offending = []
    for line in difflib.unified_diff(left, right, lineterm="", n=0):
        if line.startswith(("---", "+++", "@@")):
            continue
        body = line[1:]
        if not body.strip():
            continue
        if not LEVEL_DATA.search(body):
            offending.append(line)

    assert not offending, (
        "the two levels' predictors differ outside the level-data block, so "
        "the domain did not travel unchanged:\n" + "\n".join(offending[:20]))

    # And the diff must be non-empty, or the two levels are the same level.
    assert left != right


def test_the_guard_and_effect_functions_are_byte_identical():
    """The same claim, sliced the other way: compare the code, not the diff."""
    def mechanism(path):
        text = open(path, encoding="utf-8").read()
        blocks = re.findall(
            r"^def (_guard_\w+|_effect_\w+|step|_free|_cell_colour|_neighbour)"
            r"\(.*?(?=^def |\Z)", text, re.S | re.M)
        bodies = re.findall(
            r"^def (?:_guard_\w+|_effect_\w+|step|_free|_cell_colour|"
            r"_neighbour)\(.*?(?=^def |\Z)", text, re.S | re.M)
        return blocks, "".join(bodies)

    for name in ("generated_l1", "generated_l2"):
        if not os.path.exists(os.path.join(THEORY, name, "theory.py")):
            pytest.skip("run `python run_all.py` first")

    names_l1, body_l1 = mechanism(os.path.join(THEORY, "generated_l1", "theory.py"))
    names_l2, body_l2 = mechanism(os.path.join(THEORY, "generated_l2", "theory.py"))
    assert names_l1 == names_l2
    assert names_l1, "no mechanism functions found — the matcher is wrong"
    assert body_l1 == body_l2


# --------------------------------------------------------------- the bill

def test_the_transfer_arm_wrote_no_clause_and_ran_no_engine():
    bill = _artifact("bill_l2_transfer.json")
    counts = bill["counts"]
    assert counts["engine_stages"] == 0
    assert counts["candidates_adjudicated"] == 0
    assert counts["theorize_rounds"] == 0
    assert counts["dsl_clauses_written"] == 0


def test_the_transfer_arm_saw_exactly_one_frame_before_planning():
    bill = _artifact("bill_l2_transfer.json")
    first = bill["cost_to_first_plan"]
    assert first is not None, "the arm never reached a plan"
    assert first["world_frames"] == 1
    assert first["world_actions"] == 0


def test_the_transfer_arm_planned_before_spending_an_action():
    """Front-loading, in the only unit that costs money on a live game.

    The cold start spends its entire action budget *before* it can plan; the
    transfer arm spends none, and then spends exactly its plan's length.
    """
    transfer = _artifact("bill_l2_transfer.json")
    cold = _artifact("bill_l1_cold_start.json")
    assert transfer["cost_to_first_plan"]["world_actions"] == 0
    assert cold["cost_to_first_plan"]["world_actions"] > 300


def test_the_cold_start_baseline_is_the_expensive_one():
    transfer = _artifact("bill_l2_transfer.json")["counts"]
    cold = _artifact("bill_l1_cold_start.json")["counts"]
    assert transfer["world_frames"] < cold["world_frames"] / 10
    assert transfer["world_actions"] < cold["world_actions"] / 10


# ------------------------------------------------------ the arm actually won

def test_the_transfer_arm_won_and_the_world_agreed_frame_for_frame():
    arm = _artifact("arm_l2_transfer.json")
    assert arm["outcome"] == "win"
    assert arm["certify_static"]["green"] is True
    assert arm["certify_replay"]["green"] is True
    assert arm["certify_replay"]["anomaly_count"] == 0
    assert arm["execution"]["win"] is True


def test_the_carried_plan_is_as_short_as_the_referee_s():
    """The manual is not merely sufficient; it is not paying a detour for its
    ignorance.  Compared against the referee's shortest solution, read from
    `ground_truth.json` — the one place the truth lives."""
    truth = _artifact("ground_truth.json")
    arm = _artifact("arm_l2_transfer.json")
    shortest = truth["levels"]["a3-l2"]["truth"]["shortest_solution_length"]
    assert arm["plan"]["length"] == shortest


# --------------------------------------------- the problem, rebuilt from a frame

def test_one_frame_rebuilds_the_same_problem_a_whole_sweep_does():
    """The domain/problem split's other half.

    If a frame yielded a *different* problem than the sweep, the transfer arm
    would be solving a level slightly unlike the one the control arm solved and
    the comparison would be meaningless.
    """
    for name in ("l2_sweep.jsonl", "l2_frame0.json"):
        if not os.path.exists(os.path.join(ARTIFACTS, name)):
            pytest.skip("run `python run_all.py` first")

    constants = dict(goal_cell=(1, 1), exit_a=(1, 5), exit_b=(4, 1))
    from_trace, _ = problem_frame.from_trace(
        os.path.join(ARTIFACTS, "l2_sweep.jsonl"), "a3-l2", **constants)
    from_frame, _ = problem_frame.from_frame(
        os.path.join(ARTIFACTS, "l2_frame0.json"), "a3-l2", **constants)

    comparison = problem_frame.compare_problems(from_trace, from_frame)
    assert comparison["differing_fields"] == [], comparison
    assert comparison["equal"] is True, comparison
    assert comparison["fields"], "compare_problems compared nothing"


def test_the_provenance_records_what_was_supplied():
    """The concession is a number in the table, not a footnote."""
    prov = _artifact("provenance_l2_transfer.json")
    blob = json.dumps(prov)
    for field in ("goal_cell", "exit_a", "exit_b"):
        assert field in blob
    assert "supplied" in blob
    assert "derived_from_frame" in blob


# -------------------------------------------------------- the negative controls

def test_both_negative_controls_were_caught_and_neither_claimed_a_win():
    verdict = _artifact("negative_controls.json")
    assert verdict["all_caught"] is True
    assert verdict["none_claimed_a_win"] is True
    for row in verdict["controls"]:
        assert row["theorize_triggered"] is True
        assert row["replay_certify_green"] is False


def test_the_board_cannot_reveal_a_transition_function_edit():
    """The honest limit of the free half of the safety valve.

    Both controls pass the static check.  If this test ever fails, the
    negative controls have started differing in their pixels and are no longer
    testing what they were built to test.
    """
    verdict = _artifact("negative_controls.json")
    for row in verdict["controls"]:
        assert row["static_certify_green"] is True


# ------------------------------- the strong check: correctness, not consistency

def test_the_carried_manual_is_correct_on_every_reachable_pair_of_level_2():
    """Replay says "consistent with what I saw"; this says "right".

    The referee walks the whole reachable set and compares rendered frames.
    252 of 252, on a level the manual was never induced from and never
    explored.  A0 scored 233/236 the same way and the three it missed were
    invisible to full-history replay.
    """
    score = _artifact("score_vs_truth.json")
    carried = [r for r in score["results"]
               if r["theory"].endswith("generated_l2/theory.py")]
    if not carried:
        pytest.skip("run `python run_all.py` first")
    row = carried[0]
    assert row["level"] == "a3-l2"
    assert row["perfect"] is True, row["mismatches"][:3]
    assert row["accuracy"] == 1.0
    assert row["pairs_checked"] > 200


def test_the_level_1_manual_is_correct_on_its_own_level_too():
    score = _artifact("score_vs_truth.json")
    own = [r for r in score["results"]
           if r["theory"].endswith("generated_l1/theory.py")]
    if not own:
        pytest.skip("run `python run_all.py` first")
    assert own[0]["perfect"] is True, own[0]["mismatches"][:3]
