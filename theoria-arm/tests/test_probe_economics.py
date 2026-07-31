"""What a probe is worth, and when the arm should stop buying them.

Every fixture in this file is a transcription of something the four live legs of
2026-07-31 actually did. No key, no network, no model call.

The legs, for the record (`runs/<id>/RUN_STATE.json`, `probes.jsonl`,
`turns.json`):

===========================================  =======  =======  ======  ========
run                                          actions  probes   $       levels
===========================================  =======  =======  ======  ========
20260731T1240Z-A3-level2-carried                   5       0    0.00          0
20260731T1310Z-A3-level2-carried-r2               13       8    9.56          0
20260731T1430Z-A3-level2-carried-r3               33      28   13.44          0
20260731T1500Z-A3-sk48-carried-l1                 21      16   12.25          0
===========================================  =======  =======  ======  ========

Two facts drive everything here:

1. **Every resolved probe was vacuous.** 28/28 on r3, 16/16 on l1: the observed
   grid hash matched no hypothesis, so `survived` was `[]` every single time.
   The design report claimed 0.54--1.0 bits; the realised gain was 0.
2. **`plan` returned `no_goal_declared` on 29/29 turns of r3** and fired no
   surprise, so `commit` never ran and the desk was never told.
"""

import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(HERE)
if ARM not in sys.path:
    sys.path.insert(0, ARM)

import _bootstrap                                     # noqa: E402,F401

from inner import plan as plan_beat                   # noqa: E402
from inner import probe as probe_beat                 # noqa: E402
from inner.surprise import KINDS, Register            # noqa: E402


# -- the real shape of a vacuous probe, from r3's P-01 ---------------------
#
# 16 hypotheses, a two-class partition worth 0.696 bits by design, and an
# observation ('af3bb95d3135e37c') that appears in neither class.
R3_P01_PREDICTIONS = {
    "manual": "25cac958273811a3",
    "inert": "9bb17844cc3a57c9",
    "without_key2_body_arrives": "9bb17844cc3a57c9",
    "without_key2_body_leaves": "9bb17844cc3a57c9",
    "without_key5_body_clears": "25cac958273811a3",
    "without_key5_body_respawns": "25cac958273811a3",
    "without_key5_slot1_dims": "25cac958273811a3",
    "without_key5_slot2_centre_darkens": "25cac958273811a3",
    "without_key5_slot2_row1_lights": "25cac958273811a3",
    "without_key5_slot2_row2_left_lights": "25cac958273811a3",
    "without_key5_slot2_row2_right_lights": "25cac958273811a3",
    "without_key5_slot2_row3_lights": "25cac958273811a3",
    "without_key5_underline1_dims": "25cac958273811a3",
    "without_key5_underline2_lights": "25cac958273811a3",
    "without_meter_burn_key2_rightmost": "25cac958273811a3",
    "without_meter_burn_key4_next": "25cac958273811a3",
}
R3_P01_OBSERVED = "af3bb95d3135e37c"
R3_P01_DESIGN = {"best": {"action": ["key", 2], "entropy_bits": 0.696212260125,
                          "n_classes": 2}}


# =========================================================================
# information_gain_bits: what the answer actually eliminated
# =========================================================================

def test_r3_p01_realised_gain_is_zero_not_the_designed_0_696_bits():
    """The gap the four legs never measured.

    `probe_frontier` promised 0.696 bits. The world answered outside the
    partition, so nothing was eliminated and the true gain is 0.
    """
    gain, vacuous = probe_beat.information_gain_bits(
        R3_P01_PREDICTIONS, R3_P01_OBSERVED)
    assert vacuous is True
    assert gain == 0.0
    assert R3_P01_DESIGN["best"]["entropy_bits"] > 0.5, (
        "the design's expected bits and the realised bits must be able to "
        "disagree, or measuring the second buys nothing")


def test_a_vacuous_gain_is_zero_and_never_infinite():
    """`log2(n/0)` is the trap: reported naively, the least informative probe
    in the run would rank as the most informative one ever."""
    gain, vacuous = probe_beat.information_gain_bits(
        {"a": "x", "b": "y"}, "nothing-like-either")
    assert vacuous is True
    assert gain == 0.0


def test_one_survivor_out_of_sixteen_is_four_bits():
    predictions = {"h%02d" % i: "hash%02d" % i for i in range(16)}
    gain, vacuous = probe_beat.information_gain_bits(predictions, "hash07")
    assert vacuous is False
    assert gain == pytest.approx(4.0)


def test_every_hypothesis_agreeing_is_zero_bits_and_not_vacuous():
    """Agreement is the case `probe_frontier` already refuses to spend an
    action on. It is 0 bits, but it is not the empty posterior -- the two must
    stay distinguishable, because they call for opposite repairs."""
    gain, vacuous = probe_beat.information_gain_bits(
        {"manual": "same", "inert": "same"}, "same")
    assert vacuous is False
    assert gain == pytest.approx(0.0)


def test_no_hypotheses_at_all_is_not_reported_as_vacuous():
    gain, vacuous = probe_beat.information_gain_bits({}, "anything")
    assert (gain, vacuous) == (0.0, False)


# =========================================================================
# the record: a vacuous probe says so, in the file and to the desk
# =========================================================================

def _log(tmp_path):
    return probe_beat.ProbeLog(str(tmp_path / "probes.jsonl"))


def test_result_row_carries_gain_vacuity_and_the_designed_expectation(tmp_path):
    log = _log(tmp_path)
    probe_id = log.record_design(action=2, design_report=R3_P01_DESIGN,
                                 predictions=R3_P01_PREDICTIONS, step_idx=6)
    row = log.record_result(probe_id, observed=R3_P01_OBSERVED,
                            status=200, n_frames=9)

    assert row["frontier_vacuous"] is True
    assert row["information_gain_bits"] == 0.0
    assert row["expected_bits"] == pytest.approx(0.696212260125)
    assert row["n_hypotheses"] == 16
    assert row["n_survivors"] == 0
    assert row["manual_survived"] is False


def test_the_vacuous_verdict_does_not_say_only_that_the_manual_was_wrong(
        tmp_path):
    """The sentence the desk was sent 28 times on r3, at about $1.6 a time.

    "THE MANUAL WAS WRONG" invites a patch to a rule. When `inert` is refuted
    too, no edit to the existing rules -- and no deletion of one -- can reach
    the observation, so that sentence points the most expensive step in the
    loop at the wrong repair.
    """
    log = _log(tmp_path)
    probe_id = log.record_design(action=2, design_report=R3_P01_DESIGN,
                                 predictions=R3_P01_PREDICTIONS, step_idx=6)
    row = log.record_result(probe_id, observed=R3_P01_OBSERVED,
                            status=200, n_frames=9)

    verdict = row["verdict"]
    assert "FRONTIER DID NOT CONTAIN THE WORLD" in verdict
    assert "inert" in verdict
    assert "0.0 bits" in verdict
    assert "0.696" in verdict, "the claimed bits must appear beside the real 0"


def test_an_ordinary_refutation_keeps_the_ordinary_verdict(tmp_path):
    """One survivor is a real discrimination and must not be reworded."""
    log = _log(tmp_path)
    predictions = {"manual": "aaa", "inert": "bbb", "without_r": "ccc"}
    probe_id = log.record_design(action=1, design_report={}, predictions=predictions,
                                 step_idx=0)
    row = log.record_result(probe_id, observed="bbb", status=200, n_frames=2)

    assert row["frontier_vacuous"] is False
    assert row["survived"] == ["inert"]
    assert row["verdict"].startswith("THE MANUAL WAS WRONG")
    assert row["information_gain_bits"] == pytest.approx(1.5849625007)


def test_a_surviving_manual_is_unchanged(tmp_path):
    log = _log(tmp_path)
    predictions = {"manual": "aaa", "inert": "bbb"}
    probe_id = log.record_design(action=1, design_report={},
                                 predictions=predictions, step_idx=0)
    row = log.record_result(probe_id, observed="aaa", status=200, n_frames=2)
    assert row["manual_survived"] is True
    assert row["verdict"] == "the manual predicted this transition"
    assert row["frontier_vacuous"] is False


# =========================================================================
# the streak: three vacuous answers are a message about the frontier
# =========================================================================

def test_vacuous_streak_counts_up_and_is_broken_by_a_survivor(tmp_path):
    log = _log(tmp_path)
    for expected in (1, 2, 3):
        probe_id = log.record_design(action=expected, design_report={},
                                     predictions={"manual": "m%d" % expected,
                                                  "inert": "i%d" % expected},
                                     step_idx=expected)
        row = log.record_result(probe_id, observed="unmatched-%d" % expected,
                                status=200, n_frames=2)
        assert row["vacuous_streak"] == expected

    probe_id = log.record_design(action=9, design_report={},
                                 predictions={"manual": "m", "inert": "i"},
                                 step_idx=9)
    row = log.record_result(probe_id, observed="i", status=200, n_frames=2)
    assert row["vacuous_streak"] == 0
    assert log.vacuous_streak == 0


def test_r3_would_have_stopped_probing_after_three_not_twenty_eight(tmp_path):
    """Replay r3's shape: 28 probes, every one vacuous.

    The streak reaches the cap on the third and stays over it, so the loop's
    guard (`MAX_VACUOUS_PROBES_IN_A_ROW`) is armed for the remaining 25.
    """
    from inner.loop import MAX_VACUOUS_PROBES_IN_A_ROW

    log = _log(tmp_path)
    armed_at = None
    for i in range(28):
        probe_id = log.record_design(action=(2 if i % 2 == 0 else 5),
                                     design_report=R3_P01_DESIGN,
                                     predictions={"manual": "m%02d" % i,
                                                  "inert": "i%02d" % i},
                                     step_idx=i)
        log.record_result(probe_id, observed="world-said-%02d" % i,
                          status=200, n_frames=9)
        if armed_at is None and log.vacuous_streak >= MAX_VACUOUS_PROBES_IN_A_ROW:
            armed_at = i + 1
    assert armed_at == MAX_VACUOUS_PROBES_IN_A_ROW == 3
    assert log.vacuous_streak == 28


# =========================================================================
# the repeat: r3 ran two experiments four times
# =========================================================================

def test_identical_action_and_predictions_are_the_same_experiment():
    a = probe_beat.fingerprint(5, {"manual": "65612ce2b219fbe6",
                                   "inert": "132f0bf441d96376"})
    b = probe_beat.fingerprint(5, {"inert": "132f0bf441d96376",
                                   "manual": "65612ce2b219fbe6"})
    assert a == b, "key order is not part of the experiment"


def test_a_different_action_or_a_different_prediction_is_a_different_experiment():
    base = probe_beat.fingerprint(5, {"manual": "aaa", "inert": "bbb"})
    assert probe_beat.fingerprint(2, {"manual": "aaa", "inert": "bbb"}) != base
    assert probe_beat.fingerprint(5, {"manual": "aaa", "inert": "ccc"}) != base


def test_the_log_recognises_r3_p27_as_a_repeat_of_p25(tmp_path):
    """From `20260731T1430Z-A3-level2-carried-r3/probes.jsonl`: P-25 and P-27
    are byte-identical designs on ACTION5, as are P-26 and P-28. Four actions,
    two questions."""
    log = _log(tmp_path)
    p25 = {"manual": "65612ce2b219fbe6", "inert": "132f0bf441d96376"}
    p26 = {"manual": "70eb49bbc21b44e9", "inert": "132f0bf441d96376"}

    assert log.already_asked(5, p25) is None
    first = log.record_design(action=5, design_report={}, predictions=p25,
                              step_idx=25)
    log.record_design(action=5, design_report={}, predictions=p26, step_idx=26)

    assert log.already_asked(5, p25) == first
    assert log.already_asked(5, p26) is not None
    assert log.already_asked(5, {"manual": "new", "inert": "state"}) is None


def test_repeat_is_marked_on_the_design_row_itself(tmp_path):
    log = _log(tmp_path)
    predictions = {"manual": "aaa", "inert": "bbb"}
    first = log.record_design(action=5, design_report={},
                              predictions=predictions, step_idx=1)
    second = log.record_design(action=5, design_report={},
                               predictions=predictions, step_idx=3)
    rows = [json.loads(line) for line
            in open(str(tmp_path / "probes.jsonl"), encoding="utf-8")]
    by_id = {r["probe_id"]: r for r in rows}
    assert by_id[first]["repeat_of"] is None
    assert by_id[second]["repeat_of"] == first
    assert by_id[first]["fingerprint"] == by_id[second]["fingerprint"]


# =========================================================================
# no_goal_declared: the surprise that never fired
# =========================================================================

NO_GOAL = {
    "status": "no_goal_declared",
    "detail": ("the manual states no winning condition, so `is_goal` is "
               "`False` everywhere and no search can succeed."),
}


def test_no_goal_declared_now_reaches_the_desk():
    register = Register()
    fired = plan_beat.surprises_from(NO_GOAL, register, reported=set(),
                                     token="pb-1")
    assert len(fired) == 1
    assert fired[0].kind == "heuristic_miss"


def test_it_is_computational_family_so_it_asks_for_a_playbook_edit():
    """The goal lives in the playbook, and the computational family is the one
    whose book is the playbook. That is why no eighth surprise is needed."""
    register = Register()
    fired = plan_beat.surprises_from(NO_GOAL, register, reported=set(),
                                     token="pb-1")
    assert fired[0].family == "computational"
    assert fired[0].book == "playbook.dsl"
    assert fired[0].payload["book_to_edit"] == "playbook.dsl"


def test_no_eighth_surprise_kind_was_invented():
    assert len(KINDS) == 7
    assert "heuristic_miss" in KINDS
    assert "no_goal_declared" not in KINDS


def test_the_detail_names_the_consequence_the_desk_was_never_told():
    register = Register()
    fired = plan_beat.surprises_from(NO_GOAL, register, reported=set(),
                                     token="pb-1")
    detail = fired[0].detail
    assert "commit" in detail and "probe" in detail
    assert fired[0].payload["consequence"].startswith("plan never returns sat")


def test_it_fires_once_per_playbook_revision_not_once_per_turn():
    """r3 hit `no_goal_declared` on all 29 turns. Firing every turn would call
    the desk every turn to be told the same thing; firing never is what
    actually happened. Once per revision is the honest middle."""
    register = Register()
    reported: set = set()
    for _ in range(29):
        plan_beat.surprises_from(NO_GOAL, register, reported=reported,
                                 token="playbook-rev-A")
    assert register.counts()["heuristic_miss"] == 1

    # A rewrite that still forgets the goal is a new failure to fix it.
    plan_beat.surprises_from(NO_GOAL, register, reported=reported,
                             token="playbook-rev-B")
    assert register.counts()["heuristic_miss"] == 2


def test_search_timeout_still_fires_and_no_goal_does_not_swallow_it():
    register = Register()
    plan_beat.surprises_from({"status": "search_timeout", "detail": "nodes",
                              "expansions": 5000}, register, reported=set(),
                             token="pb")
    assert register.counts()["search_timeout"] == 1
    assert register.counts()["heuristic_miss"] == 0


def test_a_sat_plan_fires_nothing():
    register = Register()
    assert plan_beat.surprises_from({"status": "sat", "plan": [1, 2]}, register,
                                    reported=set(), token="pb") == []
    assert register.counts() == {kind: 0 for kind in KINDS}


def test_the_old_two_argument_call_still_works():
    """`surprises_from(report, register)` is called from `inner/loop.py` and
    from tests written before this change; the gap guard is opt-in."""
    register = Register()
    fired = plan_beat.surprises_from(NO_GOAL, register)
    assert len(fired) == 1 and fired[0].kind == "heuristic_miss"
