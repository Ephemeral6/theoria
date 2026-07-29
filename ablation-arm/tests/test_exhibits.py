"""The three exhibits, including the one that does not hold.

E3 is asserted **not** to be constructible, with the measurements that show it.
That reads oddly until you notice the alternative: a test that skipped E3, or
one that asserted `holds is True` and was therefore deleted when it failed,
would leave the repository with no record that a designed exhibit had expired.
`DESIGN.md` §10 pre-registered the outcome; this pins it.

If someone later restores the mechanism E3 needs, this file fails — and that
failure is the correct signal, not a nuisance. The instruction it should carry
is written into the assertion message.
"""

from __future__ import annotations

import pytest

from exhibits import e1_a0, e2_a2, e3_charitable, run_all


@pytest.fixture(scope="module")
def reports():
    return run_all()["exhibits"]


# ----------------------------------------------------------------------- E1

def test_e1_same_verdict_and_no_reason(reports):
    report = reports["E1"]
    assert report["holds"] is True
    assert report["verdict"]["ablated_arm"] == "unsolvable"
    assert report["verdict"]["settled_by"] == "search"
    assert report["verdict"]["is_correct"] is True
    assert "constructive" in report["verdict"]["constructive_ground"] or \
        "Door" in report["verdict"]["constructive_ground"]

    reason = report["the_reason"]
    assert reason["full_arm_certificate"] == [{"axioms": [], "name": "unsolvable"}]
    assert reason["ablated_arm_certificate"] is None
    assert reason["ablated_arm_certificate_owed"] is False
    assert reason["ablated_arm_directed_probes"] == 0
    assert reason["distinguishes_proof_from_exhaustion"] is False


def test_e1_reads_the_arm_rather_than_re_deriving_it():
    """The exhibit must report what the arm did. If it recomputed the verdict
    itself, it could agree with a run that never happened."""
    source = open(e1_a0.__file__, encoding="utf-8").read()
    assert "run_report.json" in source
    assert "run_plan" not in source


# ----------------------------------------------------------------------- E2

def test_e2_believes_a_false_impossibility_in_silence(reports):
    report = reports["E2"]
    assert report["holds"] is True
    own = report["on_its_own_evidence"]
    assert own["cheap_layer_green"] is True
    assert own["frames"] == 184 and own["pixels_checked"] == 14904
    assert own["anomaly_kinds"] == []

    assert report["verdict"]["ablated_arm"] == "unsolvable"
    assert report["verdict"]["certificate_owed"] is False
    assert report["verdict"]["directed_probes_scheduled"] == 0
    assert report["the_world"]["really_solvable"] is True
    assert report["the_world"]["so_the_verdict_is"] == "FALSE"
    assert report["the_loop"]["surprises"] == 0
    assert report["the_loop"]["turns"] is False


def test_e2_charity_control_shows_the_arm_can_still_localise(reports):
    """The review's first punch, answered with a measurement.

    This is the assertion that would have to change if the ablation really did
    remove the ability to repair -- and it does not.
    """
    charity = reports["E2"]["charity_control"]
    assert charity["localised"] is True
    assert charity["culprits"] == ["mispredicted_step"]
    assert charity["n_step_diffs"] == 1
    assert charity["checks"]["misread_board"] is False
    assert charity["checks"]["wrong_goal_test"] is False
    assert charity["upstream_unchanged"] is True


def test_e2_sweep_is_reported_and_disarmed(reports):
    sweep = reports["E2"]["the_sweep"]
    assert sweep["green"] is False
    assert sweep["anomalies"] == 44
    assert sweep["reaches_the_bus"] is False


# ----------------------------------------------------------------------- E3

def test_e3_is_not_constructible_and_says_why(reports):
    report = reports["E3"]
    assert report["constructible"] is False
    assert report["holds"] is False

    m = report["measurements"]
    assert m["M1_workaround_is_a_noop"]["holds"] is True, (
        "the D-A2-006 workaround is doing something again. If that is a real "
        "restoration rather than a regression, E3 may be constructible once "
        "more -- rebuild it and rewrite this test rather than relaxing it.")
    identical = m["M1_workaround_is_a_noop"][
        "pddl_byte_identical_with_patch_on_and_off"]
    assert identical == {"problem.pddl": True, "domain.pddl": True}

    why = m["M2_why"]
    assert why["cell_objects_named_in_problem_pddl"] > why["cells_in_derived_arena"]
    assert why["portal_entry_grounded_without_the_patch"] is True

    plans = m["M3_complete_manual_full_evidence"]["plans"]
    assert plans["patched"]["status"] == "SAT"
    assert plans["unpatched"]["status"] == "SAT"
    assert plans["patched"]["teleport_in_plan"] is True


def test_e3_records_the_two_halves_that_cannot_be_brought_together(reports):
    m = reports["E3"]["measurements"]
    truncated = m["M4_complete_manual_truncated_evidence"]
    assert truncated["cheap_layer"]["green"] is True
    assert truncated["plan_status"] == "UNSAT"
    assert truncated["locate_raised"] is not None
    assert "portal_exit" in truncated["locate_raised"]

    empty = m["M5_empty_culprit_set"]
    assert empty["culprits"] == []
    assert empty["n_step_diffs"] == 0
    assert empty["but_the_plan_was"] == "SAT"


def test_e3_hands_its_surviving_point_to_e2(reports):
    """The falsifier must say where the defended claim went, or a reader is
    left thinking the review's punch was never answered."""
    report = reports["E3"]
    assert "charity_control" in report["what_survives"]
    assert report["what_is_lost"]
    assert "DESIGN.md §10" in report["falsifier"]


# --------------------------------------------------------------- the runner

def test_a_falsifier_is_a_result_and_not_a_red_build():
    import run_exhibits

    assert run_exhibits.main([]) == 0


def test_the_summary_names_what_did_not_hold():
    payload = run_all()
    assert payload["all_hold"] is False
    assert payload["not_holding"] == ["E3"]
