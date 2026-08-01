"""What became of the goal ask, and the four answers that are not the same.

`armtools/goal_forensics.py` exists to stop one sentence -- "the mechanism
fired and did not connect" -- from covering four events with four different
fixes. So the suite's shape is: every verdict in the closed set is fired by a
synthetic leg built for it, every verdict is refused on the legs that belong to
the others, and then the two real R1b legs are asserted to land where a human
reading their transcripts put them.

The synthetic legs are built on disk rather than by calling the classifier's
internals, because the thing under test is a reading of *files* and a test that
bypasses the files would not notice a change to what the arm writes.
"""

import io
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(HERE)
if ARM not in sys.path:
    sys.path.insert(0, ARM)

import _bootstrap                                      # noqa: E402,F401

from armtools import goal_forensics                    # noqa: E402
from inner import goal as goal_beat                    # noqa: E402

RUNS = os.path.join(ARM, "runs")

DECLINED = (
    "laws:\n"
    "  theorem the_goal_is_absent_because_no_instance_can_name_it "
    "\"the socket cells have never changed, so they are board\"\n")


def _leg(tmp_path, name, *, turns, summary, theory=""):
    """A leg on disk with exactly the three files the forensics reads."""
    root = os.path.join(str(tmp_path), name)
    os.makedirs(os.path.join(root, "books"), exist_ok=True)
    for rel, doc in (("turns.json", turns),
                     ("RUN_STATE.json", {"goal": summary})):
        with io.open(os.path.join(root, rel), "w", encoding="utf-8",
                     newline="\n") as fh:
            json.dump(doc, fh)
    with io.open(os.path.join(root, "books", "theory.dsl"), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write(theory)
    return root


def _summary(**kw):
    base = {"protocol": "propose", "proposals": [], "goal_declared_ever": False,
            "absence_signature": None, "plan_status_counts": {}}
    base.update(kw)
    return base


# ------------------------------------------------------- every verdict fires
def test_a_leg_with_no_goal_block_is_not_measured(tmp_path):
    """The absence case. A leg from before inner/goal.py must not be counted
    as a leg where the desk declined."""
    root = _leg(tmp_path, "old", turns=[{"turn": 1}], summary=None)
    out = goal_forensics.leg(root)
    assert out["verdict"] == "not_measured"
    assert "Nothing here is evidence" in out["what_it_means"]


def test_the_record_rung_can_never_be_read_as_a_refusal(tmp_path):
    root = _leg(tmp_path, "rec",
                turns=[{"turn": 1, "goal": {"mode": "exploring_no_goal",
                                            "proposal": {"due": False}}}],
                summary=_summary(protocol="record"))
    assert goal_forensics.leg(root)["verdict"] == "recorded_only"


def test_a_criterion_that_refused_every_turn_is_never_booked(tmp_path):
    root = _leg(tmp_path, "nb",
                turns=[{"turn": 1, "goal": {"mode": "exploring_no_goal",
                                            "proposal": {"due": False}}}],
                summary=_summary())
    out = goal_forensics.leg(root)
    assert out["verdict"] == "never_booked"
    assert "goal.proposal_due" in out["what_it_means"]


def test_an_ask_that_never_left_the_peg_is_not_the_desk_declining(tmp_path):
    """The R1b-sk48-b shape, as a unit.

    This is the verdict the round record could not produce, and the reason the
    round's one-line summary was wrong about half its own evidence.
    """
    root = _leg(tmp_path, "peg",
                turns=[{"turn": 1, "goal": {"mode": "exploring_no_goal",
                                            "proposal": {"due": True}}}],
                summary=_summary(proposals=[{"proposal_idx": 1, "turn": 1,
                                             "answered": None,
                                             "delivered_on_turn": None}]))
    out = goal_forensics.leg(root)
    assert out["verdict"] == "booked_never_delivered"
    assert "was never asked" in out["what_it_means"]


def test_a_delivered_ask_whose_reply_never_came_back_says_unknown(tmp_path):
    """`delivered` with no answer is a transport verdict, not a desk verdict."""
    root = _leg(tmp_path, "lost",
                turns=[{"turn": 1, "goal": {"mode": "exploring_no_goal",
                                            "proposal": {"due": True}}},
                       {"turn": 2, "goal_rider": "delivered"}],
                summary=_summary(proposals=[{"proposal_idx": 1, "turn": 1,
                                             "answered": None,
                                             "delivered_on_turn": 2}]))
    out = goal_forensics.leg(root)
    assert out["verdict"] == "delivered_answer_lost"
    assert "unknown, not negative" in out["what_it_means"]


def test_a_signed_refusal_is_a_position_and_reports_the_argument(tmp_path):
    root = _leg(tmp_path, "declined",
                turns=[{"turn": 1, "goal": {"mode": "exploring_no_goal",
                                            "proposal": {"due": True}}},
                       {"turn": 2,
                        "goal_rider": "answered: declined_with_argument"}],
                summary=_summary(proposals=[{"proposal_idx": 1, "turn": 1,
                                             "answered":
                                                 "declined_with_argument",
                                             "delivered_on_turn": 2}]),
                theory=DECLINED)
    out = goal_forensics.leg(root)
    assert out["verdict"] == "declined_with_argument"
    assert out["refusal_theorems"] == [
        {"theorem": "the_goal_is_absent_because_no_instance_can_name_it",
         "argument": "the socket cells have never changed, so they are board"}]
    assert "NOT the plumbing" in out["what_it_means"]


def test_a_goal_clause_reports_signed(tmp_path):
    root = _leg(tmp_path, "signed",
                turns=[{"turn": 1, "goal": {"mode": "exploring_no_goal",
                                            "proposal": {"due": True}}},
                       {"turn": 2, "goal_rider": "answered: signed"}],
                summary=_summary(proposals=[{"proposal_idx": 1, "turn": 1,
                                             "answered": "signed",
                                             "delivered_on_turn": 2}],
                                 goal_declared_ever=True))
    assert goal_forensics.leg(root)["verdict"] == "signed"


def test_silence_is_the_only_verdict_that_blames_the_answer(tmp_path):
    root = _leg(tmp_path, "silent",
                turns=[{"turn": 1, "goal": {"mode": "exploring_no_goal",
                                            "proposal": {"due": True}}},
                       {"turn": 2, "goal_rider": "answered: silent"}],
                summary=_summary(proposals=[{"proposal_idx": 1, "turn": 1,
                                             "answered": "silent",
                                             "delivered_on_turn": 2}]))
    out = goal_forensics.leg(root)
    assert out["verdict"] == "silent"
    assert "defect in the ANSWER" in out["what_it_means"]


def test_the_sweep_refuses_to_read_an_empty_root_as_a_clean_result(tmp_path):
    report = goal_forensics.sweep(str(tmp_path))
    assert report["legs_read"] == 0
    assert "not a clean result" in report["reading"]


# ------------------------------------------------- the theorem readers, both
def test_the_refusal_reader_ignores_a_theorem_that_merely_says_goal():
    """Narrow on purpose: a theorem about the goal is not an argument for
    having none. Without this the reader would report a signed absence on any
    manual that mentions winning."""
    text = ('laws:\n  theorem the_goal_is_reachable_in_four_moves "x"\n')
    assert goal_forensics.extract_refusal_theorems(text) == []


def test_the_target_reader_and_the_absence_reader_do_not_overlap():
    """The third channel's theorem must not be mistaken for a signature.

    `the_goal_i_cannot_write_is_...` contains `goal`, so a looser absence rule
    would count naming the target as arguing there is none -- the exact
    conflation the third channel exists to undo.
    """
    name = goal_beat.TARGET_THEOREM_PREFIX + "_the_body_in_the_socket"
    text = 'laws:\n  theorem %s "rows 50-54, cols 44-48"\n' % name
    assert goal_beat.absence_signature(text) is None
    assert goal_forensics.extract_refusal_theorems(text) == []
    assert goal_forensics.extract_target_theorems(text) == [
        {"theorem": name, "target": "rows 50-54, cols 44-48"}]


def test_the_target_reader_finds_nothing_on_the_manuals_that_predate_it():
    """Negative control against the real archive.

    Both R1b manuals DO name their target -- in prose, under names of their
    own choosing. The reader must report zero rather than pattern-match its
    way to a hit, because a reader that finds the third channel before the
    third channel shipped would prove nothing about the third channel.
    """
    for name in ("20260801T001851Z-R1b-g50t-a",
                 "20260801T001851Z-R1b-sk48-b"):
        out = goal_forensics.leg(os.path.join(RUNS, name))
        assert out["target_theorems"] == [], name


# ------------------------------------------------------------- the real legs
def test_the_g50t_leg_was_answered_and_refused_three_times():
    out = goal_forensics.leg(os.path.join(RUNS,
                                          "20260801T001851Z-R1b-g50t-a"))
    assert out["verdict"] == "declined_with_argument"
    assert out["proposals_booked"] == 3
    assert out["answers"] == ["declined_with_argument"] * 3
    assert out["goal_declared_ever"] is False
    assert (out["absence_signature"]
            == "the_goal_is_absent_because_no_instance_can_name_the_socket")
    # The argument is in the record now, not just its name.
    assert out["refusal_theorems"]
    argument = out["refusal_theorems"][0]["argument"]
    assert "no_goal_declared" in argument or "is_goal compiles to False" in argument


def test_the_sk48_leg_never_delivered_its_ask_and_is_confounded():
    out = goal_forensics.leg(os.path.join(RUNS,
                                          "20260801T001851Z-R1b-sk48-b"))
    assert out["verdict"] == "booked_never_delivered"
    assert out["proposals_booked"] == 1
    assert out["answers"] == []
    # Five of its six desk replies were lost in transit, so its silence is not
    # the desk's silence.
    assert out["transport"]["counts"]["lost_continuation"] == 5
    assert out["confounded_by_transport"] is True


def test_the_two_r1b_legs_do_not_get_the_same_verdict():
    """The whole point, as one assertion.

    R1b reported one outcome for the round. Its two legs failed for reasons
    with nothing in common, and a fix aimed at either one would have missed
    the other entirely.
    """
    report = goal_forensics.sweep(RUNS)
    measured = {r["leg"]: r["verdict"] for r in report["legs"]
                if r["verdict"] != "not_measured"}
    assert measured == {
        "20260801T001851Z-R1b-g50t-a": "declined_with_argument",
        "20260801T001851Z-R1b-sk48-b": "booked_never_delivered",
    }, measured


@pytest.mark.parametrize("phrase", [
    "answered and REFUSED",
    "booked an ask that was never posted",
    "must not be quoted as the desk declining",
])
def test_the_archive_reading_states_both_stories(phrase):
    assert phrase in goal_forensics.sweep(RUNS)["reading"]
