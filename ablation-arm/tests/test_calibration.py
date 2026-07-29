"""A4b's calibration table — the claims `REPORT.md` makes, pinned.

`REPORT.md` is prose and prose drifts.  Every load-bearing number in it comes out
of `calibrate.build()`, and this file asserts the ones the report's argument
rests on, so that a change which quietly breaks the comparison breaks a test
instead of just making the report wrong.

Two asymmetries are asserted **as** asymmetries, deliberately:

* the A0 half asserts that the two arms are the *same* on everything a benchmark
  scores. A test that demanded a difference there would be a test written to
  make the ablation look good;
* the A2 half asserts that they *differ*, and that the ablated arm is the one
  that is wrong. That is the finding, and it is the one that would be quietly
  lost if the exhibit ever stopped working.

`test_theorize_rounds_is_reported_as_not_comparable` is the one that matters
most on a re-read: it pins an *absence*. The work order asked for a number that
does not exist, and the honest output is a stated reason. A later edit that
replaced `NOT_COMPARABLE` with a plausible integer would improve the table's
looks and destroy its truth, so it fails here.
"""

from __future__ import annotations

import json
import os

import pytest

import calibrate

ARM = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="module")
def report():
    return calibrate.build()


# --------------------------------------------------------------- the A0 half

def test_a0_replay_is_byte_equal_to_the_full_arm(report):
    """P-1, which A4a could only record."""
    rows = [r for r in report["a0_table"]["rows"]
            if r["quantity"].startswith("replay accuracy")]
    assert rows, "the replay rows disappeared from the table"
    for row in rows:
        assert row["same"] is True, row
    pixels = {r["quantity"]: r["ablated_arm"] for r in rows
              if "pixels checked" in r["quantity"]}
    assert 22356 in pixels.values() and 9072 in pixels.values()


def test_a0_score_equals_the_full_arm(report):
    """P-2.  Equal, and the caveat that makes the equality readable is present."""
    rows = [r for r in report["a0_table"]["rows"]
            if r["quantity"].startswith("score ")]
    assert rows
    for row in rows:
        assert row["same"] is True, row
    p2 = next(p for p in report["predictions"] if p["name"] == "P-2")
    assert p2["holds"] is True
    assert "BY CONSTRUCTION" in p2["caveat"], (
        "P-2's equality is partly constructive because both arms hold the same "
        "manual. Dropping the caveat turns a true number into a false claim "
        "about induction.")


def test_a0_verdict_is_identical_and_correct(report):
    """P-5, both halves — A4a settled `correct`, this settles `identical`."""
    row = next(r for r in report["a0_table"]["rows"]
               if "a0-no-button verdict" in r["quantity"])
    assert row["same"] is True
    assert "unsolvable" in str(row["ablated_arm"])
    assert "CORRECT" in row["note"]


def test_the_only_a0_differences_are_the_reason(report):
    """The whole shape of E1's testimony: 判决相同,理由蒸发.

    Every differing row on A0 must be about the certificate or how the verdict
    was settled. A difference anywhere else would mean the blade cut into the
    representation layer and DESIGN.md §10 item 1 says the attribution is then
    void.
    """
    differing = report["a0_table"]["differing_on"]
    assert differing, "if nothing differs on A0, the certificate column vanished"
    for quantity in differing:
        assert quantity.startswith("certificate") or \
            quantity.startswith("settled_by"), (
                "%s differs between the arms and is not a certificate row. The "
                "cut is supposed to be invisible to everything except the "
                "proof obligation (DESIGN.md §10 item 1)." % quantity)


def test_theorize_rounds_is_reported_as_not_comparable(report):
    """The work order asked for a number that does not exist. Pin the absence."""
    row = next(r for r in report["a0_table"]["rows"]
               if r["quantity"] == "theorize rounds · a0")
    assert row["ablated_arm"] == calibrate.NOT_COMPARABLE
    assert row["same"] is None
    assert "never theorized" in row["note"]
    assert "DOWNGRADE_REPORT" in row["source"] or "DOWNGRADE_REPORT" in row["note"]
    assert any(item["quantity"] == "theorize rounds · a0"
               for item in report["not_comparable"])


# --------------------------------------------------------------- the A2 half

def test_a2_is_the_same_input_up_to_the_fork(report):
    """If the two arms did not agree up to the fork, the fork proves nothing."""
    for row in report["a2_fork"]["identical_up_to_the_fork"]:
        if row["quantity"] in ("manual", "evidence"):
            continue            # same content, different path spellings
        assert row["same"] is True, row


def test_a2_the_full_arm_proves_a_theorem_that_is_false(report):
    """The premise: it type-checks *and* it is false of the world."""
    fork = report["a2_fork"]
    assert fork["holds"] is True
    assert "false of the world" in fork["what_it_is"]
    checked = next(r for r in fork["the_fork"]
                   if r["quantity"] == "theorem machine-checked")
    assert '"axioms": []' in checked["full_arm"]
    assert "REFUTABLE" in checked["note"]


def test_a2_the_ablated_arm_believes_it_and_the_full_arm_does_not(report):
    fork = {r["quantity"]: r for r in report["a2_fork"]["the_fork"]}
    assert fork["was the false theorem refuted"]["full_arm"] is True
    assert fork["was the false theorem refuted"]["ablated_arm"] is False
    assert fork["loop turns"]["full_arm"] is True
    assert fork["loop turns"]["ablated_arm"] is False
    assert fork["final verdict is TRUE of the world"]["full_arm"] is True
    assert fork["final verdict is TRUE of the world"]["ablated_arm"] is False
    assert fork["directed probes scheduled"]["ablated_arm"] == 0
    assert fork["`depends:` clauses the theorem rests on"]["ablated_arm"] == 0


def test_a2_the_repair_machinery_is_intact_and_idle(report):
    """The reviewer's punch, answered inside the table rather than in a footnote."""
    row = next(r for r in report["a2_fork"]["the_fork"]
               if r["quantity"] == "localisation performed")
    assert row["full_arm"] == ["mispredicted_step"]
    assert "charity_control" in str(row["ablated_arm"])
    assert "goes and gets" in row["note"]


def test_a2_this_arm_cannot_tell_a_true_impossibility_from_a_false_one(report):
    inside = report["a2_fork"]["e1_vs_e2_inside_this_arm"]
    assert inside["indistinguishable"] is True
    assert inside["n_identical"] == inside["n_decision_fields"]


# ------------------------------------------------------------------ the cost

def test_cost_is_not_reported_in_dollars(report):
    """$0 vs $0 is true and useless; the report must say so rather than tie."""
    row = next(r for r in report["cost"]["rows"]
               if r["quantity"] == "cost · dollars")
    assert row["full_arm"] == calibrate.NOT_MEASURED
    assert row["ablated_arm"] == calibrate.NOT_MEASURED
    assert row["comparable"] is False


def test_p4_holds_and_the_ablated_side_is_zero_by_construction(report):
    p4 = next(p for p in report["predictions"] if p["name"] == "P-4")
    assert p4["holds"] is True
    assert p4["evidence"]["dearer_on"] == []
    numeric = [r for r in report["cost"]["rows"] if r["comparable"]]
    assert numeric
    for row in numeric:
        assert row["ablated_arm"] <= row["full_arm"], row


def test_the_full_arm_spends_world_steps_this_arm_does_not(report):
    """The unit that transfers to the wild, where a step is an API call."""
    row = next(r for r in report["cost"]["rows"]
               if "world steps" in r["quantity"])
    assert row["full_arm"] == 12 and row["ablated_arm"] == 0


# ------------------------------------------------------------------- hygiene

def test_calibration_reads_the_arm_rather_than_re_running_it():
    """A table that recomputed the verdicts could agree with a run that never
    happened. It must read `artifacts/*/run_report.json`."""
    source = open(calibrate.__file__, encoding="utf-8").read()
    assert "run_report.json" in source
    assert "run_plan" not in source


def test_upstream_is_unchanged_by_building_the_table(report):
    assert report["upstream_unchanged"] is True, report["upstream_files_changed"]
    assert report["upstream_trees_hashed"] > 400


def test_every_source_number_is_pinned(report):
    """Each upstream file a number was read out of is hashed into the report."""
    assert set(report["sources"]) == set(calibrate.SOURCES), (
        "a source went missing between SOURCES and the pin; a number in the "
        "table would then have no checkable provenance")


def test_the_limits_are_stated(report):
    """DESIGN.md §10 item 5 requires the two-offline-worlds limit to be printed
    with every conclusion. Pinning it is cheaper than remembering it."""
    joined = " ".join(report["limits"])
    assert "MECHANISM" in joined and "effect size" in joined
    assert "constructive" in joined


def test_the_written_artifact_matches_what_build_returns(report):
    """`REPORT.md` quotes the file on disk, so the file on disk is the thing
    tested. A stale `calibration.json` beside a passing test would be the worst
    of both."""
    path = os.path.join(ARM, "artifacts", "calibration.json")
    if not os.path.exists(path):
        pytest.skip("calibration.json not written yet; run calibrate.py")
    with open(path, encoding="utf-8") as handle:
        on_disk = json.load(handle)
    assert on_disk["a0_table"]["differing_on"] == \
        report["a0_table"]["differing_on"]
    assert on_disk["predictions_hold"] == report["predictions_hold"]
