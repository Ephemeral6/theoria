"""Change B: goal-absence is a state, not a leaf status.

The finding these tests defend is in `inner/goal.py`'s docstring and in
`test_the_four_carried_legs_never_produced_a_plan` below, which reads the
artefacts rather than repeating a claim about them.

Every check in this file that can say *no* is shown saying no. The criterion in
`GoalState.proposal_due` has four conjuncts and there is one test per conjunct
that makes that conjunct, alone, refuse -- because a criterion that has only
ever been observed to fire is not a criterion, it is a constant.
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

from armtools import archive                          # noqa: E402
from inner import commit as commit_beat               # noqa: E402
from inner import goal as goal_beat                   # noqa: E402
from inner import plan as plan_beat                   # noqa: E402
from inner.books import Books                         # noqa: E402
from inner.goal import GoalState                      # noqa: E402
from inner.grammar_card import WORKED_EXAMPLE         # noqa: E402


# --------------------------------------------------------------- the reading
LEGS = ("20260731T1240Z-A3-level2-carried",
        "20260731T1310Z-A3-level2-carried-r2",
        "20260731T1430Z-A3-level2-carried-r3",
        "20260731T1500Z-A3-sk48-carried-l1")


def test_the_four_carried_legs_never_produced_a_plan():
    """The whole of change B's premise, read off the artefacts.

    If this ever goes red because a leg produced a plan, change B's premise has
    changed and the module above it must be re-argued, not patched.
    """
    seen = 0
    for slug in LEGS:
        run_dir = os.path.join(ARM, "runs", slug)
        plan_path = os.path.join(run_dir, "plan.json")
        commit_path = os.path.join(run_dir, "commit.json")
        if not (os.path.exists(plan_path) and os.path.exists(commit_path)):
            continue
        seen += 1
        with open(plan_path, encoding="utf-8") as fh:
            reports = json.load(fh)
        with open(commit_path, encoding="utf-8") as fh:
            commits = json.load(fh)

        assert reports, "%s recorded no plan beat at all" % slug
        statuses = {r.get("status") for r in reports}
        assert statuses == {"no_goal_declared"}, (slug, sorted(statuses))
        # Neither rung of the ladder was even entered: `plan` returns before
        # `_tier_pddl`. So this is not a search that ran out of nodes.
        assert all(r.get("tiers") == [] for r in reports), slug
        assert all(r.get("plan") is None for r in reports), slug
        assert commits == [], "%s executed a plan it never had" % slug

    if not seen:
        pytest.skip("none of the four carried legs is present in this checkout")


# ------------------------------------------------------- reading the manual
def test_a_manual_with_a_goal_clause_is_read_as_having_one():
    assert goal_beat.has_goal(WORKED_EXAMPLE) is True
    assert goal_beat.absence_signature(WORKED_EXAMPLE) is None
    read = goal_beat.read_manual(WORKED_EXAMPLE)
    assert read == {"goal_declared": True, "absence_is_signed": False,
                    "absence_signature": None}


def test_a_manual_with_no_goal_clause_is_read_as_lacking_one():
    text = WORKED_EXAMPLE.replace("goal:\n  goal count(Cart) = 1\n", "")
    assert goal_beat.has_goal(text) is False
    assert goal_beat.read_manual(text)["absence_is_signed"] is False


@pytest.mark.parametrize("name", [
    # The two theorem names the live carried manuals actually signed their
    # absences with. Verbatim, because the detector's whole job is to recognise
    # what the desk really writes, not what a test author would have written.
    "the_goal_section_is_absent_on_purpose",
    "no_goal_is_signed_and_that_is_deliberate",
])
def test_a_signed_absence_is_distinguished_from_silence(name):
    signed = "laws:\n  theorem %s \"argued at length\"\n" % name
    assert goal_beat.absence_signature(signed) == name
    assert goal_beat.read_manual(signed)["absence_is_signed"] is True

    silent = "laws:\n  theorem some_other_claim \"unrelated\"\n"
    assert goal_beat.absence_signature(silent) is None
    assert goal_beat.read_manual(silent)["absence_is_signed"] is False


def test_a_theorem_merely_mentioning_a_goal_is_not_a_signature():
    """The detector must be narrow. A theorem about the goal's *contents* is
    not an argument that there is no goal, and reading it as one would let a
    manual look like it had taken a position it never took."""
    text = "laws:\n  theorem the_goal_is_probably_the_socket \"a guess\"\n"
    assert goal_beat.absence_signature(text) is None


def test_a_manual_that_declares_a_goal_can_never_have_a_signature():
    """Both facts come from one manual and they must not both be true: an
    absence signature on a manual WITH a goal would be a contradiction the
    record could not resolve."""
    text = WORKED_EXAMPLE + (
        "\nlaws:\n  theorem the_goal_section_is_absent_on_purpose \"x\"\n")
    assert goal_beat.has_goal(text) is True
    assert goal_beat.absence_signature(text) is None


# ------------------------------------------------------------------- modes
def _state(protocol="record", **kw):
    return GoalState(protocol, **kw)


def test_a_turn_with_a_goal_is_planning_and_a_turn_without_one_is_not():
    state = _state()
    with_goal = state.observe(turn=1, theory_text=WORKED_EXAMPLE,
                              plan_report={"status": "sat"},
                              distinct_states=9, actions_spent=3,
                              has_predictor=True)
    assert with_goal["mode"] == "planning"
    assert with_goal["goal_declared"] is True

    without = state.observe(turn=2, theory_text="semantics:\n  frame persist\n",
                            plan_report={"status": "no_goal_declared"},
                            distinct_states=9, actions_spent=7,
                            has_predictor=True)
    assert without["mode"] == "exploring_no_goal"
    assert without["turns_without_goal"] == 1
    assert without["turns_planning"] == 1
    assert state.first_no_goal_turn == 2


def test_a_turn_with_no_predictor_is_neither():
    state = _state()
    block = state.observe(turn=1, theory_text="", plan_report=None,
                          distinct_states=0, actions_spent=0,
                          has_predictor=False)
    assert block["mode"] == "no_manual"
    assert state.turns_without_manual == 1
    assert state.turns_without_goal == 0


def test_actions_are_attributed_to_the_state_the_turn_was_in():
    """A turn spent planning must not count toward "spent without a goal" --
    that is exactly the confusion this module exists to remove."""
    state = _state()
    state.observe(turn=1, theory_text=WORKED_EXAMPLE,
                  plan_report={"status": "sat"}, distinct_states=4,
                  actions_spent=10, has_predictor=True)
    assert state.actions_without_goal == 0
    state.observe(turn=2, theory_text="semantics:\n", plan_report=None,
                  distinct_states=4, actions_spent=14, has_predictor=True)
    assert state.actions_without_goal == 14


def test_the_plan_status_histogram_is_the_finding():
    """56 calls, one status. The summary must be able to show that shape."""
    state = _state()
    for turn in range(1, 6):
        state.observe(turn=turn, theory_text="semantics:\n",
                      plan_report={"status": "no_goal_declared"},
                      distinct_states=3, actions_spent=turn,
                      has_predictor=True)
    assert state.summary()["plan_status_counts"] == {"no_goal_declared": 5}


# ------------------------------------- the criterion, one refusal at a time
def _due(state, **kw):
    args = {"mode": "exploring_no_goal", "distinct_states": 99,
            "has_predictor": True}
    args.update(kw)
    return state.proposal_due(**args)


def test_the_criterion_can_say_yes():
    """The positive control. Without it the four refusals below could all be
    satisfied by a criterion that never fires at all."""
    verdict = _due(_state())
    assert verdict["due"] is True
    assert verdict["refused_because"] == []
    assert len(verdict["checks"]) == 4
    assert all(c["ok"] for c in verdict["checks"])


def test_conjunct_one_refuses_a_manual_that_already_has_a_goal():
    verdict = _due(_state(), mode="planning")
    assert verdict["due"] is False
    assert len(verdict["refused_because"]) == 1
    assert "declares no winning condition" in verdict["refused_because"][0]


def test_conjunct_two_refuses_when_there_is_no_predictor():
    verdict = _due(_state(), mode="no_manual", has_predictor=False)
    # Two refuse here, and both are named -- the mode and the predictor. A
    # criterion that reported only the first would hide the second.
    assert verdict["due"] is False
    assert any("compiled predictor" in r for r in verdict["refused_because"])


def test_conjunct_three_refuses_until_new_world_arrives():
    """The conjunct taken straight from what the manuals said they were
    waiting for. Turns and dollars do not move it; distinct states do."""
    state = _state(min_new_states=4)
    assert _due(state, distinct_states=3)["due"] is False
    assert _due(state, distinct_states=3)["new_states"] == 3
    assert _due(state, distinct_states=4)["due"] is True

    # And after a proposal the bar MOVES: the same 4 states no longer qualify.
    state.record_proposal(turn=1, distinct_states=4, reason="test")
    verdict = _due(state, distinct_states=4)
    assert verdict["due"] is False
    assert verdict["new_states"] == 0
    assert any("since the last proposal" in r
               for r in verdict["refused_because"])
    assert _due(state, distinct_states=8)["due"] is True


def test_conjunct_four_refuses_once_the_leg_has_asked_enough():
    state = _state(max_proposals=2)
    state.record_proposal(turn=1, distinct_states=10, reason="t")
    state.record_proposal(turn=2, distinct_states=20, reason="t")
    verdict = _due(state, distinct_states=99)
    assert verdict["due"] is False
    assert any("proposal budget" in r for r in verdict["refused_because"])


def test_every_refusal_names_the_number_it_read():
    """A refusal that does not say what it saw cannot be audited from the
    artefact, which is the failure mode change B is about."""
    verdict = _due(_state(min_new_states=4), distinct_states=1)
    reads = {c["check"]: c["read"] for c in verdict["checks"]}
    assert 1 in reads.values()
    assert all("read" in c for c in verdict["checks"])


# ------------------------------------------------------- answering the ask
@pytest.mark.parametrize("reply,expected", [
    (WORKED_EXAMPLE, "signed"),
    ("laws:\n  theorem no_goal_is_signed_and_that_is_deliberate \"why\"\n",
     "declined_with_argument"),
    ("semantics:\n  frame persist\n", "silent"),
])
def test_all_three_answers_to_a_proposal_are_recorded(reply, expected):
    state = _state("propose")
    state.record_proposal(turn=1, distinct_states=8, reason="t")
    entry = state.answer_proposal(theory_text=reply)
    assert entry["answered"] == expected
    assert state.summary()["proposals"][0]["answered"] == expected


def test_an_unanswered_proposal_stays_unanswered_in_the_record():
    """A booked ask that no theorize ever carried must not be quietly dropped:
    `answered: null` is the record saying the ask was never sent."""
    state = _state("propose")
    state.record_proposal(turn=1, distinct_states=8, reason="t")
    assert state.summary()["proposals"][0]["answered"] is None


def test_answering_twice_does_not_overwrite_the_first_answer():
    state = _state("propose")
    state.record_proposal(turn=1, distinct_states=8, reason="t")
    state.answer_proposal(theory_text="semantics:\n")
    state.answer_proposal(theory_text=WORKED_EXAMPLE)
    assert state.summary()["proposals"][0]["answered"] == "silent"


# ------------------------------------------------------------- the rungs
def test_the_rungs_are_named_and_a_typo_is_refused_at_construction():
    assert goal_beat.PROTOCOLS == ("off", "record", "propose")
    assert goal_beat.DEFAULT_PROTOCOL == "off"
    with pytest.raises(ValueError) as excinfo:
        GoalState("on")
    assert "not a goal protocol" in str(excinfo.value)


def test_off_is_disabled_and_the_other_two_are_not():
    assert GoalState("off").enabled is False
    assert GoalState("record").enabled is True
    assert GoalState("propose").enabled is True


def test_the_reading_line_says_no_proposal_was_made_and_why():
    state = _state("propose")
    state.observe(turn=1, theory_text="semantics:\n",
                  plan_report={"status": "no_goal_declared"},
                  distinct_states=1, actions_spent=2, has_predictor=True)
    reading = state.summary()["reading"]
    assert "no winning condition" in reading
    assert "UNSIGNED" in reading
    assert "criterion refused every turn" in reading


def test_a_signed_absence_reads_differently_from_silence_in_the_summary():
    state = _state()
    state.observe(turn=1,
                  theory_text=("laws:\n  theorem "
                               "the_goal_section_is_absent_on_purpose \"x\"\n"),
                  plan_report={"status": "no_goal_declared"},
                  distinct_states=1, actions_spent=2, has_predictor=True)
    assert "SIGNED" in state.summary()["reading"]
    assert (state.summary()["absence_signature"]
            == "the_goal_section_is_absent_on_purpose")


# ------------------------------------------------ the prompt rider (offline)
def test_the_rider_asks_for_a_goal_OR_an_argument_and_names_the_cost():
    state = _state("propose")
    for turn in range(1, 4):
        state.observe(turn=turn, theory_text="semantics:\n",
                      plan_report={"status": "no_goal_declared"},
                      distinct_states=9, actions_spent=turn * 5,
                      has_predictor=True)
    entry = state.record_proposal(turn=3, distinct_states=9, reason="t")
    rider = goal_beat.prompt_rider(state, entry, 9)
    assert "no_goal_declared" in rider
    assert "3 turn(s)" in rider and "15 action(s)" in rider
    # Both answers offered; only silence refused.
    assert "A `goal` clause" in rider
    assert "A `theorem`" in rider
    assert "not acceptable is silence" in rider
    # And it must not instruct the desk to invent one.
    assert "request to invent one" in rider


# ------------------------------------------------------ scoreboard columns
def test_the_scoreboard_columns_distinguish_not_measured_from_measured():
    """`None` is not `False`. A campaign of unmeasured legs must not report
    itself as a campaign that always had a goal."""
    assert goal_beat.turn_row_fields(None) == {
        "goal_mode": None, "goal_declared": None, "goal_proposal_due": None}
    assert goal_beat.turn_row_fields({"turn": 1}) == {
        "goal_mode": None, "goal_declared": None, "goal_proposal_due": None}

    measured = goal_beat.turn_row_fields({"goal": {
        "mode": "exploring_no_goal", "goal_declared": False,
        "proposal": {"due": False}}})
    assert measured == {"goal_mode": "exploring_no_goal",
                        "goal_declared": False, "goal_proposal_due": False}


def test_turn_series_carries_the_goal_columns_off_a_turns_json(tmp_path):
    run_dir = str(tmp_path)
    turns = [
        {"turn": 1, "actions_before": 0, "theorize_rounds": 0,
         "goal": {"mode": "exploring_no_goal", "goal_declared": False,
                  "proposal": {"due": False}}},
        {"turn": 2, "actions_before": 1, "theorize_rounds": 0,
         "goal": {"mode": "planning", "goal_declared": True,
                  "proposal": {"due": False}}},
        # A turn from a run played on the `off` rung: no block at all.
        {"turn": 3, "actions_before": 2, "theorize_rounds": 0},
    ]
    with open(os.path.join(run_dir, "turns.json"), "w", encoding="utf-8") as fh:
        json.dump(turns, fh)

    doc = archive.turn_series(run_dir, records=[])
    modes = [row["goal_mode"] for row in doc["rows"]]
    assert modes == ["exploring_no_goal", "planning", None]
    assert [row["goal_declared"] for row in doc["rows"]] == [False, True, None]


def test_a_reconstructed_spine_reports_not_measured_rather_than_guessing(
        tmp_path):
    """With no `turns.json` the ledger carries no goal state, and inferring one
    would be a fabrication. `None` on every row is the honest answer."""
    doc = archive.turn_series(str(tmp_path), records=[])
    assert doc["rows"], "the reconstruction produced no rows to check"
    assert all(row["goal_mode"] is None for row in doc["rows"])
    assert all("goal_declared" in row for row in doc["rows"])


# =========================================================================
#  THE NEGATIVE CONTROL THE TICKET ASKS FOR
#
#  An arm WITH a goal must still plan and commit exactly as before, at every
#  rung. If change B could only be shown to do something on a goal-less
#  manual, it would be indistinguishable from a change that broke planning.
# =========================================================================
def _books_with_a_reachable_goal(tmp_path):
    theory = WORKED_EXAMPLE.replace("goal count(Cart) = 1",
                                    "goal Cart.pos = (0, 1)")
    books = Books(str(tmp_path))
    books.write(theory=theory, playbook="# none\n")
    books.write_problem({"name": "l", "grid": [3, 3], "background": 0,
                         "board": [[0] * 3 for _ in range(3)],
                         "objects": [{"name": "Cart", "type": "Cart",
                                      "pos": [2, 1], "color": 6}]})
    compiled = books.compile_all()
    namespace, error = books.load_predictor()
    assert namespace is not None, error
    return books, namespace, compiled


class _FakeWorld:
    """`send(action_id)` returning exactly what the manual predicted.

    A perfectly-predicted world is the right control here: the question is
    whether the commit beat still runs and still marks every frame, not whether
    the manual is right about anything.
    """

    def __init__(self, namespace):
        self.namespace = namespace
        self.state = namespace["initial_state"]()
        self.sent = []

    def __call__(self, action_id):
        self.sent.append(action_id)
        self.state = self.namespace["step"](self.state, ("key", action_id))
        return 200, {"state": "NOT_FINISHED"}, [self.namespace["render"](
            self.state)]


class _EmptyStore:
    actions = []

    def __len__(self):
        return 0


@pytest.mark.parametrize("protocol", ["off", "record", "propose"])
def test_an_arm_with_a_goal_still_plans_and_commits_at_every_rung(
        protocol, tmp_path):
    books, namespace, compiled = _books_with_a_reachable_goal(tmp_path)

    report = plan_beat.plan(books, namespace, compiled)
    assert report["status"] == "sat", report
    assert report["plan"] == [["key", 1], ["key", 1]]
    assert report["backend"] == "object-state-bfs"

    world = _FakeWorld(namespace)
    executed = commit_beat.execute(namespace, report["plan"], send=world,
                                   store=_EmptyStore(),
                                   action_to_arc=commit_beat.action_to_arc)
    assert executed["outcome"] == "completed"
    assert executed["planned"] == executed["executed"] == 2
    assert executed["matched"] == 2
    assert executed["abandoned_at"] is None
    assert world.sent == [1, 1]

    # And the goal state, observing that same turn, must call it planning and
    # must NOT ask for a goal -- refusing on conjunct one, by name.
    state = GoalState(protocol)
    if protocol == "off":
        assert state.enabled is False
        return
    block = state.observe(turn=1, theory_text=books.theory,
                          plan_report=report, distinct_states=99,
                          actions_spent=2, has_predictor=True)
    assert block["mode"] == "planning"
    assert block["goal_declared"] is True
    assert block["proposal"]["due"] is False
    assert any("declares no winning condition" in r
               for r in block["proposal"]["refused_because"])
    assert state.proposals == []
    assert state.summary()["turns_without_goal"] == 0
    assert "searching for something the whole time" in state.summary()["reading"]


def test_the_same_manual_without_its_goal_stops_planning_and_the_state_says_so(
        tmp_path):
    """The other half of the control: one edit to the manual, and the same
    machinery reports the other state. Without this pair, `planning` could be
    a constant too."""
    books, namespace, compiled = _books_with_a_reachable_goal(tmp_path)
    stripped = books.theory.replace("goal:\n  goal Cart.pos = (0, 1)\n", "")
    assert stripped != books.theory
    books.write(theory=stripped, playbook="# none\n")
    compiled = books.compile_all()
    namespace, error = books.load_predictor()
    assert namespace is not None, error

    report = plan_beat.plan(books, namespace, compiled)
    assert report["status"] == "no_goal_declared"
    assert report["tiers"] == []
    assert report["plan"] is None

    state = GoalState("propose")
    block = state.observe(turn=1, theory_text=books.theory,
                          plan_report=report, distinct_states=99,
                          actions_spent=2, has_predictor=True)
    assert block["mode"] == "exploring_no_goal"
    assert block["proposal"]["due"] is True


# ---------------------------------------------------- R1b: what the records
# said, and the three things they could not say.
#
# `20260801T001851Z-R1b-g50t-a` delivered the rider three times and was refused
# three times with an argument; `20260801T001851Z-R1b-sk48-b` booked one ask
# that never left the peg. Both legs' summaries read `goal_declared_ever:
# False` with `answered: null` or `declined_with_argument`, and no field
# separated "was not asked" from "was asked and said no". These are the fields
# that separate them.

def test_a_failed_check_does_not_read_as_an_assertion():
    """`refused_because` used to quote the check verbatim.

    Every check is worded as the condition that must HOLD, so R1b's records
    say `refused_because: ["enough new world has arrived to change the answer
    ... >= 4"]` -- the reason nothing happened, phrased as though something
    had. The substring is still there for callers that match on it; what
    changed is that a reader can now tell which way it went.
    """
    state = _state("propose")
    state.observe(turn=1, theory_text="semantics:\n",
                  plan_report={"status": "no_goal_declared"},
                  distinct_states=1, actions_spent=1, has_predictor=True)
    verdict = state.proposal_due(mode="exploring_no_goal", distinct_states=1,
                                 has_predictor=True)
    assert verdict["due"] is False
    assert len(verdict["refused_because"]) == 1
    refusal = verdict["refused_because"][0]
    assert refusal.startswith("NO -- ")
    assert "enough new world has arrived" in refusal      # the old substring
    assert "[read: 1]" in refusal                          # and the number


def test_every_refusal_is_negated_and_every_passing_check_is_absent():
    """The negative control on the negation itself: a due proposal must have
    an EMPTY refusal list, not a list of negated passing checks."""
    state = _state("propose")
    verdict = state.proposal_due(mode="exploring_no_goal", distinct_states=9,
                                 has_predictor=True)
    assert verdict["due"] is True
    assert verdict["refused_because"] == []
    assert all(c["ok"] for c in verdict["checks"])


def test_booked_and_delivered_are_separate_facts():
    state = _state("propose")
    state.record_proposal(turn=1, distinct_states=8, reason="t")
    assert state.summary()["proposals_made"] == 1
    assert state.summary()["proposals_delivered"] == 0
    assert state.proposals[0]["delivered_on_turn"] is None

    state.mark_delivered(turn=3)
    assert state.summary()["proposals_delivered"] == 1
    assert state.proposals[0]["delivered_on_turn"] == 3
    # Still unanswered: delivery is not an answer.
    assert state.summary()["proposals_answered"] == 0


def test_an_ask_that_never_left_the_peg_says_so_in_the_reading():
    """The sk48-b sentence. The old reading called this "1 proposal(s) were
    made", which a reader takes as a question the desk answered badly."""
    state = _state("propose")
    state.observe(turn=1, theory_text="semantics:\n",
                  plan_report={"status": "no_goal_declared"},
                  distinct_states=9, actions_spent=5, has_predictor=True)
    state.record_proposal(turn=1, distinct_states=9, reason="t")
    reading = state.summary()["reading"]
    assert "1 proposal(s) were BOOKED and 0 were DELIVERED" in reading
    assert "NOTHING HERE IS EVIDENCE ABOUT THE DESK" in reading


def test_a_delivered_ask_with_no_reply_says_unknown_not_negative():
    state = _state("propose")
    state.observe(turn=1, theory_text="semantics:\n",
                  plan_report={"status": "no_goal_declared"},
                  distinct_states=9, actions_spent=5, has_predictor=True)
    state.record_proposal(turn=1, distinct_states=9, reason="t")
    state.mark_delivered(turn=2)
    reading = state.summary()["reading"]
    assert "1 proposal(s) were BOOKED and 1 were DELIVERED" in reading
    assert "UNKNOWN on this leg, not negative" in reading
    assert "never left the peg" not in reading


def test_a_refused_ask_reads_as_a_position():
    state = _state("propose")
    state.observe(turn=1, theory_text="semantics:\n",
                  plan_report={"status": "no_goal_declared"},
                  distinct_states=9, actions_spent=5, has_predictor=True)
    state.record_proposal(turn=1, distinct_states=9, reason="t")
    state.mark_delivered(turn=2)
    state.answer_proposal(theory_text=(
        "laws:\n  theorem the_goal_is_absent_because_reach \"x\"\n"))
    reading = state.summary()["reading"]
    assert "answers: declined_with_argument" in reading
    assert "UNKNOWN on this leg" not in reading


def test_mark_delivered_on_a_leg_that_booked_nothing_is_a_no_op():
    state = _state("propose")
    assert state.mark_delivered(turn=1) is None
    assert state.summary()["proposals_delivered"] == 0


# ------------------------------------------- the rider's third channel (R1b)
def test_the_rider_now_asks_about_reach_and_not_only_about_confidence():
    """R1b's three refusals were arguments about what the goal section can
    SAY. The rider engaged the soundness half and had no channel for the
    other, so the desk put its actual target in a theorem of its own naming
    where nothing reads it."""
    state = _state("propose")
    state.observe(turn=1, theory_text="semantics:\n",
                  plan_report={"status": "no_goal_declared"},
                  distinct_states=9, actions_spent=5, has_predictor=True)
    entry = state.record_proposal(turn=1, distinct_states=9, reason="t")
    rider = goal_beat.prompt_rider(state, entry, 9)

    assert "Three answers are acceptable" in rider
    assert goal_beat.TARGET_THEOREM_PREFIX in rider
    assert "cannot SAY what you believe wins" in rider
    # It must not read as permission to decline more easily.
    assert "not a substitute for answer 2" in rider
    # And the first two channels survive unchanged.
    assert "A `goal` clause" in rider
    assert "A `theorem`" in rider
    assert "not acceptable is silence" in rider


def test_the_target_theorem_name_is_not_an_absence_signature():
    """A manual that names its target has not thereby argued for having no
    goal. If `absence_signature` matched the third channel's prefix, answering
    3 would silently satisfy 2."""
    name = goal_beat.TARGET_THEOREM_PREFIX + "_the_body_in_the_socket"
    text = 'laws:\n  theorem %s "the 5x5 body seated at (8,7)"\n' % name
    assert goal_beat.absence_signature(text) is None
    assert goal_beat.read_manual(text)["absence_is_signed"] is False
