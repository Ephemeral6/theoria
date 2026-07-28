"""The loop, and the one property the driver is not allowed to have.

`DESIGN.md` §7.2: the ablated arm's loop must fail to turn *because of the
incision*, never because a step table was written with the repair beats left
out.  That is a property of the driver's source as much as of its output, so it
is asserted both ways here.
"""

from __future__ import annotations

import json
import os

import pytest

import run_arm
from ablcore.surprise import SurpriseBus

ARM = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ------------------------------------------------- the schedule, not a table

def test_theorize_is_on_the_beat_list():
    """If it were missing, "the loop does not turn" would be a tautology about
    this file rather than a finding about the arm."""
    assert "theorize" in run_arm.BEATS
    assert run_arm.BEATS.index("loop_gate") < run_arm.BEATS.index("theorize")


def test_the_schedule_is_the_bus_predicate_and_nothing_else():
    bus = SurpriseBus(ablated=True)
    assert bus.turns_the_loop() is False
    bus.raise_("replay_mismatch", {"anything": True}, beat="certify")
    assert bus.turns_the_loop() is True
    assert bus.turns_the_loop() is (not bus.empty())


def test_a_surprise_would_owe_a_theorize_turn():
    """The other side of P-6: when the bus is non-empty the driver records a
    debt. A run that never turned the loop *and* could never have owed one
    would not be evidence about the incision."""
    report = run_arm.run_world(run_arm.WORLD_BY_KEY["a2-holed"])
    assert report["beats"]["theorize"]["owed"] is False

    source = open(os.path.join(ARM, "run_arm.py"), encoding="utf-8").read()
    assert '"owed": True' in source, (
        "the driver has no branch that records an owed theorize turn, so the "
        "empty bus in every run proves nothing about the incision")


# --------------------------------------------------------------- the outcome

@pytest.fixture(scope="module")
def run_all_report():
    return run_arm.run_all()


def test_no_world_turns_the_loop_and_each_says_why(run_all_report):
    assert run_all_report["loop_turned_on"] == []
    for key, report in run_all_report["worlds"].items():
        theorize = report["beats"]["theorize"]
        assert theorize["owed"] is False, key
        why = theorize["why_not_owed"]
        assert why and len(why) > 40, key
        # The two causes must not blur: a silent run on a correct manual is the
        # framework working; a silent run on a wrong UNSAT is the finding.
        if report["beats"]["plan"]["status"] == "UNSAT":
            assert "THIS IS THE FINDING" in why, key
        else:
            assert "working as" in why, key


def test_the_pre_registered_pixel_counts_hold(run_all_report):
    assert run_all_report["pre_registered_holds"], \
        run_all_report["pre_registered_failures"]
    stated = {k: r["beats"]["certify"]["pre_registered"]["observed_pixels"]
              for k, r in run_all_report["worlds"].items()
              if r["beats"]["certify"]["pre_registered"]["expected_pixels"]}
    assert stated == {"a0-base": 22356, "a2-base": 20088,
                      "a2-holed": 14904, "a2-charitable": 20088}


def test_a_wrong_trace_turns_the_run_red_rather_than_plausible():
    """The check added after the driver's first run was wrong.

    `a2-holed` on the sweep instead of its evidence produced a green-looking run
    with a turning loop and a falsified-looking P-6. The pixel count is a
    fingerprint of which record was replayed, so it is what catches this.
    """
    spec = run_arm.WORLD_BY_KEY["a2-holed"]
    wrong = run_arm.WorldRun(
        spec.key, spec.dsl, "cold-start-a2/artifacts/raw_trace.jsonl",
        spec.world, expect_pixels=spec.expect_pixels,
        expect_frames=spec.expect_frames)
    report = run_arm.run_world(wrong, out_root=os.path.join(
        ARM, "artifacts", "_determinism", "wrong-trace"))
    check = report["beats"]["certify"]["pre_registered"]
    assert check["holds"] is False
    assert check["observed_pixels"] != 14904
    assert any("fingerprint" in line for line in check["failures"])


def test_the_sweep_is_reported_and_never_reaches_the_bus(run_all_report):
    holed = run_all_report["worlds"]["a2-holed"]
    sweep = holed["beats"]["certify"]["sweep"]
    assert sweep["reaches_the_bus"] is False
    assert sweep["report"]["green"] is False
    assert len(sweep["report"]["anomalies"]) == 44
    assert holed["surprises"]["count"] == 0, (
        "the sweep leaked onto the bus; the loop would then be turning on the "
        "referee's knowledge and the exhibit would be worthless")


def test_seven_kinds_become_six(run_all_report):
    assert run_all_report["surprise_kinds_in_taxonomy"] == 7
    assert run_all_report["surprise_kinds_available_to_this_arm"] == 6


def test_upstream_is_pinned_around_the_run(run_all_report):
    assert run_all_report["upstream_unchanged"] is True
    assert run_all_report["upstream_trees_hashed"] > 300


# ----------------------------------------------------------------- P-6 itself

def test_a_true_impossibility_and_a_false_one_are_indistinguishable(run_all_report):
    """The result the A4 ticket asks for."""
    exhibits = run_all_report["exhibits"]
    assert exhibits["available"] is True
    assert exhibits["n_fields"] == 10
    assert exhibits["indistinguishable"] is True
    assert exhibits["n_identical"] == exhibits["n_fields"]
    truth = exhibits["ground_truth"]
    assert truth["a0-no-button"]["really_solvable"] is False
    assert truth["a2-holed"]["really_solvable"] is True
    for name, row in exhibits["fields"].items():
        assert row["same"] is True, name


def test_the_comparison_would_report_a_difference_if_there_were_one():
    """A comparator that always says `same` is not a comparator."""
    report = run_arm.run_all(["a0-base", "a0-no-button", "a2-holed"])
    doctored = json.loads(json.dumps(report["worlds"]))
    doctored["a2-holed"]["verdict"] = "solvable"
    result = run_arm._exhibit_comparison(doctored)
    assert result["indistinguishable"] is False
    assert result["fields"]["verdict"]["same"] is False
    assert "must be diagnosed" in result["reading"]
