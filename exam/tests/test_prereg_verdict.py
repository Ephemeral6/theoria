"""The pre-registration must describe the paper that exists, or it is fiction.

A pre-registration is only worth anything if it was written first *and* still
matches; the second half is the one that decays silently, because a paper can be
edited without anyone re-reading the document that registered it.
"""

from __future__ import annotations

import os

import pytest

from exam import prereg
from exam.grading import rubrics_verdict as rv
from exam.grading.registry import digest
from exam.papers import module_for


def test_the_prereg_matches_the_built_paper():
    """Class sizes, points, weights, grammar, floors -- all of it, computed."""
    assert prereg.check() == []


def test_a_changed_item_mix_turns_it_red(monkeypatch):
    """事后挑题目组合 is the gaming route STATS_RULES 2.3 closes by freezing the
    mix; this asserts the freeze is executable rather than written down."""
    monkeypatch.setitem(prereg.SCORING_RULE, "class_sizes",
                        {"small_unsolvable": 5, "large_unsolvable": 3,
                         "solvable_hard": 9})
    failures = prereg.check()
    assert any("class sizes" in f for f in failures), failures


def test_a_changed_rubric_weight_turns_it_red(monkeypatch):
    """The weights are protocol numbers: half claim, half reason, search at 0.4.

    Moving one silently would redefine what the endpoint measures while every
    other gate stayed green -- which is the argument D-EX-016 makes for the
    protocol digest, applied to the three numbers the digest does not name.
    """
    monkeypatch.setattr(rv, "SEARCH_CREDIT", 1.0)
    failures = prereg.check()
    assert any("weights" in f for f in failures), failures


def test_every_arm_has_a_prediction_and_a_refutation_for_every_class():
    """A cell left empty is a cell that can be filled in after the results."""
    classes = set(prereg.SCORING_RULE["class_sizes"])
    for arm in prereg.ARMS:
        for klass in classes:
            rows = [r for r in prereg.ARM_EXPECTATIONS
                    if r["arm"] == arm and r["class"] == klass]
            assert len(rows) == 1, (arm, klass)
            assert rows[0]["refuted_if"].strip(), (arm, klass)


def test_a_missing_prediction_turns_it_red(monkeypatch):
    """The check above reads the table; this one proves the check can fail."""
    trimmed = tuple(r for r in prereg.ARM_EXPECTATIONS
                    if not (r["arm"] == "theoria"
                            and r["class"] == "large_unsolvable"))
    monkeypatch.setattr(prereg, "ARM_EXPECTATIONS", trimmed)
    failures = prereg.check()
    assert any("theoria" in f and "large_unsolvable" in f for f in failures), failures


def test_no_arm_has_sat_this_paper_yet():
    """`written_before` is a factual claim, so it is checked rather than said.

    The four calibration fakes and `cheater-v4` are on disk; an arm is not.  If
    one appears, this test fails and the pre-registration has to be re-dated
    rather than quietly kept.
    """
    from exam.model import ANSWERS_DIR, read_json
    module = module_for("verdict")
    paper_id = module.PAPER_ID
    seen = []
    if os.path.isdir(ANSWERS_DIR):
        for name in sorted(os.listdir(ANSWERS_DIR)):
            if name.startswith("%s." % paper_id) and name.endswith(".answers.json"):
                seen.append(read_json(os.path.join(ANSWERS_DIR, name))["examinee_id"])
    assert not (set(seen) & set(prereg.ARMS)), (
        "an arm has already submitted to %s: %s. The pre-registration claims it "
        "was written before any arm sat the paper, and that claim is now false."
        % (paper_id, sorted(set(seen) & set(prereg.ARMS))))


def test_the_prereg_artifacts_exist_and_agree_with_the_code():
    """The emitted JSON is the copy a reader quotes; it must not drift."""
    from exam.model import ARTIFACTS, read_json
    path = os.path.join(ARTIFACTS, "prereg", "verdict_prereg.json")
    if not os.path.isfile(path):
        pytest.skip("prereg artefacts not built in this tree")
    doc = read_json(path)
    assert doc["paper_check_failures"] == []
    assert doc["control_check_failures"] == []
    assert doc["prereg"]["floors"]["S_min"]["value"] == prereg.FLOOR_CLAIMS["S_min"]["value"]
    assert doc["control_table"]["rubric_digest"] == digest(), (
        "the committed pre-registration was built against a different rubric")
