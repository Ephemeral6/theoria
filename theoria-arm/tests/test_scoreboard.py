"""The second witness: the scoreboard, the denominator, and the two absences.

No key, no network, no model call. Every scorecard here is either hand-built or
lifted verbatim from `runs/20260728T012311Z-g50t-first-contact-salvage2/
ledger.jsonl`, which is the real closed g50t card and the source of
`level_baseline_actions = [78, 175, 179, 230, 96, 54, 67]`.

Most of this file is about a distinction that the old record could not express
and that A27 turns on:

* **not measured** -- no reading was taken, or only one was, so no jump could
  have been seen. `boundary_observed` is `null`.
* **measured absent** -- readings were taken and nothing moved.
  `boundary_observed` is `false`.

Reporting the first as the second is how "we did not look" becomes "we looked
and there was nothing", and every live leg this repo has ever run sits in the
first category. The positive cases below are all synthetic, and
`test_no_recorded_leg_contains_a_real_boundary` is the test that says so out
loud rather than leaving the reader to notice.
"""

import json
import os
import sys
import types

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(HERE)
if ARM not in sys.path:
    sys.path.insert(0, ARM)

import _bootstrap                                     # noqa: E402,F401

from harness.budget import Budget                     # noqa: E402
from inner.levels import LevelLog                     # noqa: E402
from inner.loop import TheoriaArm                     # noqa: E402
from inner.scoreboard import (                        # noqa: E402
    DEFAULT_PROTOCOL, PROTOCOLS, ScoreWatch, WITNESS_THEOREM_PREFIX,
    reading_from_envelope, reading_from_scorecard, witness_from_boundary,
    witness_rider)

GAME = "g50t-5849a774"

#: The real thing, from the ledger cited in the module docstring. Trimmed to the
#: keys this module reads; every value is as recorded.
REAL_G50T_CARD = {
    "card_id": "32ca4788-e9a7-424e-926c-a47b557c03a9",
    "score": 0.0,
    "total_actions": 5,
    "total_levels": 7,
    "total_levels_completed": 0,
    "environments": [{
        "id": GAME,
        "level_count": 7,
        "levels_completed": 0,
        "score": 0.0,
        "runs": [{
            "actions": 5,
            "completed": False,
            "guid": "b56594af-04ea-443f-a975-5442a5311f3b",
            "level_actions": [5, 0, 0, 0, 0, 0, 0],
            "level_baseline_actions": [78, 175, 179, 230, 96, 54, 67],
            "level_scores": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            "levels_completed": 0,
            "score": 0.0,
            "state": "NOT_FINISHED",
        }],
    }],
}


def _card(*, score=0.0, level_scores=None, level_actions=None,
          levels_completed=0, guid="g-1"):
    return {
        "card_id": "card-1",
        "score": score,
        "total_levels_completed": levels_completed,
        "environments": [{
            "id": GAME,
            "level_count": 7,
            "runs": [{
                "guid": guid,
                "level_actions": level_actions or [0] * 7,
                "level_baseline_actions": [78, 175, 179, 230, 96, 54, 67],
                "level_scores": level_scores or [0.0] * 7,
                "levels_completed": levels_completed,
                "score": score,
                "state": "NOT_FINISHED",
            }],
        }],
    }


def _envelope(grid, levels_completed=0, state="NOT_FINISHED"):
    body = {"frame": [grid], "state": state, "win_levels": 7,
            "available_actions": [1, 2, 3, 4, 5]}
    if levels_completed is not None:
        body["levels_completed"] = levels_completed
    return body


def _arm(tmp_path, **kwargs):
    run_dir = str(tmp_path)
    os.makedirs(run_dir, exist_ok=True)
    run = types.SimpleNamespace(dir=run_dir, run=None, run_id="r-pytest")
    kwargs.setdefault("offline", True)
    return TheoriaArm(env_base="http://127.0.0.1:1", run=run,
                      game_id=GAME, **kwargs)


def _feed(arm, grid, levels_completed=0, action="ACTION1"):
    return arm._record(action, 200, _envelope(grid, levels_completed))


G0 = [[0, 0], [0, 0]]
G1 = [[0, 6], [0, 0]]
G2 = [[3, 3], [3, 3]]


# ============================================== 1. what a reading actually is
def test_an_envelope_reading_has_no_score_and_says_null_not_zero():
    """The whole reason the arm is blind here. `score` is not zero on a
    gameplay response; it does not exist. `0.0` would be a measurement nobody
    took, and every later diff would compare against it."""
    reading = reading_from_envelope(_envelope(G0, levels_completed=0))
    assert reading["score"] is None
    assert reading["level_scores"] is None
    assert reading["level_baseline_actions"] is None
    assert reading["levels_completed"] == 0        # this one WAS read
    assert reading["level_count"] == 7             # `win_levels`


def test_a_scorecard_reading_carries_the_four_fields_no_envelope_has():
    reading = reading_from_scorecard(REAL_G50T_CARD, game_id=GAME)
    assert reading["score"] == 0.0
    assert reading["level_scores"] == [0.0] * 7
    assert reading["level_actions"] == [5, 0, 0, 0, 0, 0, 0]
    assert reading["level_baseline_actions"] == [78, 175, 179, 230, 96, 54, 67]
    assert reading["level_count"] == 7


def test_the_run_row_is_selected_by_guid_never_summed():
    """A card outlives a RESET and holds one row per session. Summing them, or
    taking the wrong one, puts another session's actions into this leg's
    denominator."""
    card = _card(level_actions=[9] * 7, guid="g-mine")
    card["environments"][0]["runs"].insert(0, {
        "guid": "g-other", "level_actions": [99] * 7,
        "level_baseline_actions": [1] * 7, "level_scores": [0.0] * 7,
        "levels_completed": 0, "score": 0.0})
    picked = reading_from_scorecard(card, game_id=GAME, guid="g-mine")
    assert picked["level_actions"] == [9] * 7
    assert picked["row_selected_by"] == "guid"

    # No guid: the last row, and it says so, so a reader can tell the fallback
    # from the match.
    fallback = reading_from_scorecard(card, game_id=GAME)
    assert fallback["row_selected_by"] == "last_row"
    assert fallback["level_actions"] == [9] * 7


def test_the_environment_is_selected_by_game_id():
    card = _card()
    card["environments"].insert(0, {"id": "zz99-deadbeef", "level_count": 3,
                                    "runs": [{"guid": "x",
                                              "level_baseline_actions": [1, 2, 3],
                                              "level_scores": [0.0] * 3,
                                              "level_actions": [0] * 3,
                                              "levels_completed": 0}]})
    reading = reading_from_scorecard(card, game_id=GAME)
    assert reading["level_baseline_actions"] == [78, 175, 179, 230, 96, 54, 67]
    assert reading["level_count"] == 7


def test_a_malformed_card_reads_as_all_unknown_and_does_not_raise():
    for junk in (None, [], "", {"environments": []}, {"environments": [{}]}):
        reading = reading_from_scorecard(junk, game_id=GAME)
        assert reading["level_baseline_actions"] is None
        assert reading["source"] == "scorecard"


# ============================================ 2. the negative control, twice
def test_the_first_reading_is_a_floor_and_never_a_boundary():
    """A leg that resumes a card already carrying a score must not report a
    boundary on its first look. Comparing reading one against an assumed zero
    is how a fabricated level completion gets into a figure."""
    watch = ScoreWatch("scorecard", game_id=GAME)
    fired = watch.observe_scorecard(_card(score=3.0, levels_completed=3), turn=1)
    assert fired == []
    assert watch.events == []
    assert watch.boundary_verdict()["verdict"] == "not_measured"
    assert watch.boundary_verdict()["boundary_observed"] is None


def test_one_reading_is_not_measured_and_two_flat_ones_are_measured_absent():
    """The distinction this whole file exists for. Absence of a measurement and
    a measured absence are different claims about a leg."""
    watch = ScoreWatch("scorecard", game_id=GAME)
    watch.observe_scorecard(REAL_G50T_CARD, guid="b56594af-04ea-443f-a975-5442a5311f3b",
                            turn=1)
    first = watch.boundary_verdict()
    assert first["verdict"] == "not_measured"
    assert first["boundary_observed"] is None
    assert first["score_moved"] is None

    watch.observe_scorecard(REAL_G50T_CARD, guid="b56594af-04ea-443f-a975-5442a5311f3b",
                            turn=5)
    second = watch.boundary_verdict()
    assert second["verdict"] == "measured_absent"
    assert second["boundary_observed"] is False
    assert second["score_moved"] is False
    assert second["readings"] == 2
    assert "looked and saw nothing" in second["detail"]


def test_a_flat_leg_on_the_envelope_rung_reports_absence_not_a_boundary():
    """Twelve steps, no counter movement. The negative control for the rung
    that every leg will actually run on."""
    watch = ScoreWatch("envelope", game_id=GAME)
    for i in range(12):
        watch.observe_envelope(_envelope(G0 if i % 2 else G1, levels_completed=0),
                               turn=i, step_idx=i)
    verdict = watch.boundary_verdict()
    assert verdict["verdict"] == "measured_absent"
    assert verdict["boundary_observed"] is False
    assert watch.events == []
    # And the reading says WHY no score could have moved, rather than leaving a
    # null looking like a zero.
    assert "carry no `score` field" in watch.summary()["reading"]


def test_off_reads_nothing_and_reports_off():
    watch = ScoreWatch("off", game_id=GAME)
    assert watch.observe_scorecard(_card(score=9.0), turn=1) == []
    assert watch.observe_envelope(_envelope(G0, levels_completed=4)) == []
    assert watch.boundary_verdict()["verdict"] == "off"
    assert watch.boundary_verdict()["boundary_observed"] is None
    assert sum(watch.readings.values()) == 0


def test_an_unknown_protocol_is_refused_at_construction():
    with pytest.raises(ValueError) as excinfo:
        ScoreWatch("scoreboard")
    assert "off, envelope, scorecard" in str(excinfo.value)
    assert DEFAULT_PROTOCOL in PROTOCOLS


# ================================================ 3. the synthetic positives
def test_a_synthetic_score_jump_is_detected():
    """The detector has never fired on real data, so this is the only evidence
    that it fires at all."""
    watch = ScoreWatch("scorecard", game_id=GAME)
    watch.observe_scorecard(_card(score=0.0), turn=1)
    fired = watch.observe_scorecard(_card(score=1.0), turn=5)
    kinds = [e["event"] for e in fired]
    assert "score_moved" in kinds
    moved = [e for e in fired if e["event"] == "score_moved"][0]
    assert moved["from"] == 0.0 and moved["to"] == 1.0
    assert moved["turn"] == 5
    verdict = watch.boundary_verdict()
    assert verdict["verdict"] == "observed"
    assert verdict["score_moved"] is True


def test_a_synthetic_level_score_jump_names_the_level():
    watch = ScoreWatch("scorecard", game_id=GAME)
    watch.observe_scorecard(_card(level_scores=[0.0] * 7), turn=1)
    fired = watch.observe_scorecard(
        _card(level_scores=[1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]), turn=5)
    per_level = [e for e in fired if e["event"] == "level_score_moved"]
    assert len(per_level) == 1
    assert per_level[0]["level_index"] == 0
    assert per_level[0]["level"] == 1
    assert per_level[0]["signal"] == "level_scores[0]"


def test_a_synthetic_counter_jump_on_the_scorecard_is_a_boundary():
    watch = ScoreWatch("scorecard", game_id=GAME)
    watch.observe_scorecard(_card(levels_completed=0), turn=1)
    fired = watch.observe_scorecard(_card(levels_completed=1), turn=5)
    boundaries = [e for e in fired if e["event"] == "level_boundary"]
    assert len(boundaries) == 1
    assert boundaries[0]["signal"] == "levels_completed:scorecard"
    assert watch.boundary_verdict()["boundary_observed"] is True


def test_a_synthetic_counter_jump_on_the_envelope_is_a_boundary():
    watch = ScoreWatch("envelope", game_id=GAME)
    watch.observe_envelope(_envelope(G0, levels_completed=0), step_idx=0)
    fired = watch.observe_envelope(_envelope(G1, levels_completed=1), step_idx=1)
    assert [e["signal"] for e in fired] == ["levels_completed:envelope"]


def test_a_decrease_is_never_a_boundary():
    """A full reset would decrease the counter. `LevelLog` refuses it and so
    does this, for the same reason: the arm must not cut a trajectory in half
    because a number went backwards."""
    watch = ScoreWatch("scorecard", game_id=GAME)
    watch.observe_scorecard(_card(score=2.0, levels_completed=2), turn=1)
    fired = watch.observe_scorecard(_card(score=0.0, levels_completed=0), turn=5)
    assert fired == []
    assert watch.boundary_verdict()["verdict"] == "measured_absent"


def test_the_two_sources_diff_against_their_own_history():
    """An envelope reading carries no score; a scorecard reading does. If the
    two shared a history, every alternation would look like a score appearing
    and vanishing."""
    watch = ScoreWatch("scorecard", game_id=GAME)
    watch.observe_scorecard(_card(score=1.0), turn=1)
    watch.observe_envelope(_envelope(G0, levels_completed=0), step_idx=0)
    watch.observe_scorecard(_card(score=1.0), turn=5)
    watch.observe_envelope(_envelope(G0, levels_completed=0), step_idx=1)
    assert watch.events == []


# ================================================== 4. the two witnesses meet
def test_corroborate_says_all_four_of_its_answers():
    """A check that has never been shown to be capable of saying no has not
    been shown to check anything."""
    watch = ScoreWatch("scorecard", game_id=GAME)
    assert watch.corroborate(None)["verdict"] == "not_measured"
    assert watch.corroborate(0)["verdict"] == "envelope_only"

    watch.observe_scorecard(_card(levels_completed=0), turn=1)
    assert watch.corroborate(None)["verdict"] == "scorecard_only"
    assert watch.corroborate(0)["verdict"] == "agree"

    disagreement = watch.corroborate(1)
    assert disagreement["verdict"] == "disagree"
    assert disagreement["envelope"] == 1 and disagreement["scorecard"] == 0
    assert "cannot tell which" in disagreement["detail"]


def test_the_cadence_refusal_is_written_down_with_the_number_it_read():
    watch = ScoreWatch("scorecard", game_id=GAME, scorecard_every=4)
    assert watch.due_for_scorecard(1)["due"] is True
    watch.observe_scorecard(_card(), turn=1)
    refused = watch.due_for_scorecard(2)
    assert refused["due"] is False
    assert refused["refused_because"][0].startswith("NO -- ")
    assert "[read: 1]" in refused["refused_because"][0]
    assert watch.due_for_scorecard(5)["due"] is True


def test_the_envelope_rung_never_asks_for_a_scorecard():
    watch = ScoreWatch("envelope", game_id=GAME)
    due = watch.due_for_scorecard(1)
    assert due["due"] is False
    assert "the scorecard rung is on" in due["refused_because"][0]


# ============================================= 5. the denominator (A27's fact)
def test_reach_is_not_measured_without_a_baseline_and_never_guesses():
    watch = ScoreWatch("envelope", game_id=GAME)
    report = watch.reach(level=1, actions_spent_this_level=5, actions_left=27)
    assert report["verdict"] == "not_measured"
    assert report["baseline_actions_for_level"] is None
    assert "exists only on a scorecard" in report["reading"]


def test_reach_reproduces_the_arithmetic_the_board_item_turns_on():
    """g50t level 1 costs a reference solver 78 actions. A leg holding 27 more
    after spending 5 is 46 short of the reference. That is the number no leg has
    ever been shown mid-flight."""
    watch = ScoreWatch("scorecard", game_id=GAME)
    watch.observe_scorecard(REAL_G50T_CARD, guid="b56594af-04ea-443f-a975-5442a5311f3b",
                            turn=1)
    report = watch.reach(level=1, actions_spent_this_level=5, actions_left=27)
    assert report["baseline_actions_for_level"] == 78
    assert report["remaining_reference"] == 73
    assert report["headroom"] == -46               # 27 held, 73 still to go
    assert report["verdict"] == "below_reference"
    # And it refuses to overclaim: the baseline is a reference, not a bound.
    assert "not a lower bound" in report["reading"]


def test_reach_says_at_or_above_when_the_leg_can_cover_the_reference():
    watch = ScoreWatch("scorecard", game_id=GAME)
    watch.observe_scorecard(REAL_G50T_CARD, guid="b56594af-04ea-443f-a975-5442a5311f3b",
                            turn=1)
    report = watch.reach(level=1, actions_spent_this_level=10, actions_left=120)
    assert report["verdict"] == "at_or_above_reference"
    assert report["headroom"] == 120 - 68


def test_reach_reports_a_level_outside_the_roster_rather_than_clamping():
    watch = ScoreWatch("scorecard", game_id=GAME)
    watch.observe_scorecard(REAL_G50T_CARD, guid="b56594af-04ea-443f-a975-5442a5311f3b",
                            turn=1)
    report = watch.reach(level=9, actions_spent_this_level=0, actions_left=10)
    assert report["verdict"] == "level_out_of_range"


def test_reach_without_a_remaining_count_makes_no_comparison():
    watch = ScoreWatch("scorecard", game_id=GAME)
    watch.observe_scorecard(REAL_G50T_CARD, turn=1)
    report = watch.reach(level=2, actions_spent_this_level=0, actions_left=None)
    assert report["verdict"] == "actions_left_unknown"
    assert report["baseline_actions_for_level"] == 175


def test_a_mock_baseline_is_labelled_as_one():
    """The hazard the archive scan turned up. `level_baseline_actions:
    [8, 8, 8]` with `level_count: 3` is recorded against **three different game
    ids** in this repository -- g50t, sk48 and ar25 -- so it is not a roster; it
    is `proxy/mock`'s constant answer. Unlabelled, it would make a mock leg read
    `at_or_above_reference` against a reference cost of 8 where the real g50t
    level 1 is 78."""
    mock_card = _card()
    mock_card["environments"][0]["level_count"] = 3
    mock_card["environments"][0]["runs"][0]["level_baseline_actions"] = [8, 8, 8]

    watch = ScoreWatch("scorecard", game_id=GAME, offline=True)
    watch.observe_scorecard(mock_card, turn=1)
    report = watch.reach(level=1, actions_spent_this_level=0, actions_left=32)
    assert report["baseline_is_from_a_mock"] is True
    assert "MOCK" in report["baseline_source"]
    assert "proxy/mock" in watch.summary()["reading"]
    assert watch.summary()["offline"] is True

    live = ScoreWatch("scorecard", game_id=GAME, offline=False)
    live.observe_scorecard(REAL_G50T_CARD, turn=1)
    live_report = live.reach(level=1, actions_spent_this_level=0, actions_left=32)
    assert live_report["baseline_is_from_a_mock"] is False
    assert live_report["baseline_source"] == "scorecard.level_baseline_actions"


def test_the_baseline_is_sticky_once_read():
    """A later reading that omits the field must not erase the denominator: the
    arm learned it, and unlearning it would send `reach` back to
    `not_measured` for the rest of the leg."""
    watch = ScoreWatch("scorecard", game_id=GAME)
    watch.observe_scorecard(REAL_G50T_CARD, turn=1)
    watch.observe_scorecard({"card_id": "x", "environments": []}, turn=5)
    assert watch.baseline_actions == [78, 175, 179, 230, 96, 54, 67]


# ============================================== 6. the arm, driven end to end
def test_the_arm_consults_the_scoreboard_every_turn_and_records_absence(tmp_path):
    """A27's per-turn requirement, and the negative control for it: the block
    is in the turn record whether or not anything moved."""
    arm = _arm(tmp_path)
    for i in range(6):
        _feed(arm, G0 if i % 2 else G1, levels_completed=0)
    record = {}
    arm._consult_scoreboard(record, turn=3)
    block = record["scoreboard"]
    assert block["protocol"] == "envelope"
    assert block["boundary"]["verdict"] == "measured_absent"
    assert block["boundary"]["boundary_observed"] is False
    assert block["corroboration"]["verdict"] == "envelope_only"
    assert block["reach"]["verdict"] == "not_measured"
    # The free rung dialled nothing.
    assert block["scorecard_read"] is None
    assert arm.budget.reads == 0


def test_a_boundary_writes_a_witness_to_disk_with_the_winning_frame(tmp_path):
    """The observation half, whole. The step carrying the increment is the first
    frame of the NEXT level, so the witness must hold the one before it."""
    arm = _arm(tmp_path)
    arm.arc.win_levels = 7
    _feed(arm, G0, levels_completed=0, action="RESET")
    for _ in range(3):
        _feed(arm, G1, levels_completed=0)
    _feed(arm, G2, levels_completed=0, action="ACTION3")   # the winning frame
    _feed(arm, G0, levels_completed=1, action="ACTION2")   # the boundary

    assert len(arm.witnessed_wins) == 1
    witness = arm.witnessed_wins[0]
    assert witness["witness"] == "level_cleared"
    assert witness["from_level"] == 1 and witness["to_level"] == 2
    assert witness["final_grid"] == G2
    assert witness["final_grid_hash"]
    assert witness["opening_grid_hash"]
    assert witness["reach_at_boundary"]["verdict"] == "not_measured"
    assert "generalising" in witness["goal_evidence"].lower()

    on_disk = json.load(open(os.path.join(arm.dir, "witnessed_wins.json"),
                             encoding="utf-8"))
    assert on_disk == arm.witnessed_wins


def test_a_leg_with_no_boundary_writes_no_witness(tmp_path):
    """Absence, again: an empty list and no file, never a fabricated entry."""
    arm = _arm(tmp_path)
    for i in range(8):
        _feed(arm, G0 if i % 2 else G1, levels_completed=0)
    assert arm.witnessed_wins == []
    assert not os.path.exists(os.path.join(arm.dir, "witnessed_wins.json"))
    assert arm.summary()["scoreboard"]["boundary"]["boundary_observed"] is False


def test_the_summary_carries_the_scoreboard_only_when_the_rung_is_on(tmp_path):
    on = _arm(tmp_path / "on")
    _feed(on, G0)
    _feed(on, G1)
    assert "scoreboard" in on.summary()
    assert on.summary()["witnessed_wins"] == []

    off = _arm(tmp_path / "off", scoreboard_protocol="off")
    _feed(off, G0)
    _feed(off, G1)
    assert "scoreboard" not in off.summary()
    assert "witnessed_wins" not in off.summary()


def test_the_witness_never_ends_a_leg(tmp_path):
    """An instrument that can kill a run is a liability. The one turn in this
    project's history where a level is cleared is the worst possible turn to
    raise on."""
    arm = _arm(tmp_path)
    arm.arc.win_levels = 7
    _feed(arm, G0, levels_completed=0, action="RESET")
    _feed(arm, G1, levels_completed=0)

    def boom(*args, **kwargs):
        raise RuntimeError("the instrument broke")

    arm.scoreboard.corroborate = boom
    step = _feed(arm, G2, levels_completed=1, action="ACTION2")
    assert step is not None
    assert arm.levels.completed == 1               # the boundary still happened
    event = arm.levels.events[-1]
    assert "the instrument broke" in event["witness_error"]
    assert arm.witnessed_wins == []


def test_a_scorecard_read_costs_a_command_and_no_action(tmp_path):
    """`total_actions` counts successful ACTIONs and a read is not one, so the
    action ceiling must not gate it -- exactly as it does not gate RESET."""
    arm = _arm(tmp_path)
    arm.arc.card_id = "card-1"
    arm.budget = Budget(actions=1, commands=50)
    arm.arc.budget = arm.budget
    arm.budget.actions_ok = 1                      # the action ceiling is spent
    assert arm.budget.actions_left == 0

    arm.arc._get = lambda path: (200, _card(score=0.0))
    card = arm.arc.read_scorecard()
    assert card is not None
    assert arm.budget.reads == 1
    assert arm.budget.commands_sent == 1
    assert arm.budget.actions_ok == 1              # unchanged
    assert arm.arc.attempt_log[-1]["readonly"] is True


def test_a_failed_scorecard_read_returns_none_and_does_not_raise(tmp_path):
    arm = _arm(tmp_path)
    arm.arc.card_id = "card-1"
    arm.arc._get = lambda path: (-1, {"error": "URLError: nope"})
    assert arm.arc.read_scorecard() is None
    assert arm.arc.attempt_log[-1]["ok"] is False
    # One attempt. Losing a reading loses nothing; the next turn asks again.
    assert arm.arc.attempt_log[-1]["attempts"] == 1


def test_no_card_means_no_read_and_no_spend(tmp_path):
    arm = _arm(tmp_path)
    arm.arc.card_id = None
    assert arm.arc.read_scorecard() is None
    assert arm.budget.reads == 0


# ================================================== 7. the path to the goal
def test_the_rider_is_a_pure_function_of_a_witness():
    event = {"event": "level_boundary", "signal": "levels_completed",
             "from_level": 1, "to_level": 2, "step_idx": 12, "action": "ACTION2",
             "turn": 4, "actions_spent": 33}
    witness = witness_from_boundary(event, final_grid=G2,
                                    final_grid_hash="sha256:abc",
                                    opening_grid_hash="sha256:def",
                                    actions_this_level=33)
    text = witness_rider(witness)
    assert "Level 1 was completed at step 12" in text
    assert WITNESS_THEOREM_PREFIX in text
    assert "one instance, not a condition" in text
    # It engages the refusal R1b measured, on its own terms.
    assert "no winning state had been seen" in text
    # Pure: same witness, same bytes.
    assert witness_rider(witness) == text


def test_the_witness_survives_a_boundary_with_nothing_around_it():
    """`force()` events carry no `action` and a leg can hit a boundary on its
    first recorded step. Neither may produce a KeyError on the one turn that
    matters."""
    witness = witness_from_boundary({"event": "level_boundary",
                                     "from_level": 1, "to_level": 2,
                                     "step_idx": 0, "signal": "win_then_reset"})
    assert witness["action"] is None
    assert witness["final_grid"] is None
    assert isinstance(witness_rider(witness), str)


# ============================================ 8. what the record does NOT have
def test_no_recorded_leg_contains_a_real_boundary():
    """The honest caveat, as a test rather than a sentence in a report.

    Every positive case in this file is synthetic. Across all `env_step` records
    written by the three arms -- 2,700 rows at the time of writing --
    `levels_completed` is `0` wherever it is present and absent elsewhere, and
    every one of the 27 closed scorecards reads `total_levels_completed: 0`,
    `score: 0.0` and `level_scores: [0.0, ...]`. The detector has therefore
    never been exercised on a real positive, and this test fails the day that
    stops being true -- which is the day someone should come back and read the
    positives above against a real one.
    """
    reading = reading_from_scorecard(REAL_G50T_CARD, game_id=GAME)
    assert reading["levels_completed"] == 0
    assert reading["score"] == 0.0
    assert reading["level_scores"] == [0.0] * 7
    assert sum(reading["level_actions"]) == 5

    watch = ScoreWatch("scorecard", game_id=GAME)
    for turn in (1, 5, 9):
        watch.observe_scorecard(REAL_G50T_CARD, turn=turn)
    assert watch.events == []
    assert watch.boundary_verdict()["verdict"] == "measured_absent"
    # What the leg COULD have known, and did not: 78 against 5 spent.
    assert watch.reach(level=1, actions_spent_this_level=5,
                       actions_left=115)["baseline_actions_for_level"] == 78


def test_the_level_log_and_the_watch_are_independent_witnesses(tmp_path):
    """The watch must not be what fires `_on_level_boundary`: if it were, a
    scorecard glitch could manufacture a boundary in the arm's own record."""
    arm = _arm(tmp_path)
    arm.arc.win_levels = 7
    _feed(arm, G0, levels_completed=0, action="RESET")
    # A scorecard claiming a completed level, straight into the watch.
    arm.scoreboard.observe_scorecard(_card(levels_completed=0), turn=1)
    arm.scoreboard.observe_scorecard(_card(levels_completed=1, score=1.0), turn=5)
    assert arm.scoreboard.boundary_verdict()["boundary_observed"] is True
    # ... and the arm's own level record is untouched.
    assert arm.levels.completed == 0
    assert arm.levels.events == []
    assert arm.witnessed_wins == []
    # The disagreement is reported rather than resolved.
    assert arm.scoreboard.corroborate(arm.levels.completed)["verdict"] == "disagree"


def test_a_bare_level_log_and_a_watch_agree_on_the_same_stream():
    """Same envelopes into both instruments, same answer -- which is the
    property that makes a disagreement meaningful when one appears."""
    log = LevelLog()
    watch = ScoreWatch("envelope", game_id=GAME)
    stream = [0, 0, 0, 1, 1, 2]
    for idx, completed in enumerate(stream):
        log.observe(levels_completed=completed, step_idx=idx, action="ACTION1")
        watch.observe_envelope(_envelope(G0, levels_completed=completed),
                               step_idx=idx)
    assert log.completed == 2
    assert len([e for e in watch.events if e["event"] == "level_boundary"]) == 2
    assert watch.corroborate(log.completed)["verdict"] == "envelope_only"
