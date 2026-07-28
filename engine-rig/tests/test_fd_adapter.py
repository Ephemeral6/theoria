"""M6 acceptance: the adapter returns the hand-verified optimal plan.

The hand argument for the gripper instance: each of the two balls needs one pick
and one drop (4 actions), and at least one move is needed since both start in the
wrong room (1), so 5 is a lower bound; pick/pick/move/drop/drop attains it.
That literal 5 is asserted directly, the plan is checked by an independent
validator, and optimality is re-derived here by exhaustive enumeration below
depth 5 -- three checks that do not share code with the search.
"""

import pytest

from engines import fd_adapter
from engines.fd_adapter import backends
from engines.fd_adapter.pddl import PddlError, ground_actions, parse_domain, parse_problem
from engines.fd_adapter.validate import InvalidPlan, validate_plan
from tools.validate_candidates import validate_rows

HAND_VERIFIED_OPTIMUM = 5


@pytest.fixture(scope="module")
def instance():
    domain = parse_domain(fd_adapter.read(fd_adapter.DOMAIN_PATH))
    problem = parse_problem(fd_adapter.read(fd_adapter.PROBLEM_PATH))
    return domain, problem


@pytest.fixture(scope="module")
def plan():
    return fd_adapter.solve(prefer="stub")


# ------------------------------------------------------------------ the plan

def test_plan_length_equals_the_hand_verified_optimum(plan):
    assert plan.length == HAND_VERIFIED_OPTIMUM


def test_plan_is_valid_under_an_independent_validator(instance, plan):
    domain, problem = instance
    assert validate_plan(domain, problem, plan.actions)


def test_no_shorter_plan_exists(instance):
    """Optimality re-derived by exhaustive enumeration, not by trusting the search."""
    domain, problem = instance
    actions = ground_actions(domain, problem)

    def holds(state):
        return all(a in state for a in problem.goal_positive) and not any(
            a in state for a in problem.goal_negative
        )

    def explore(state, depth):
        if holds(state):
            return True
        if depth == 0:
            return False
        for action in actions:
            if not all(a in state for a in action.pre_positive):
                continue
            if any(a in state for a in action.pre_negative):
                continue
            nxt = (state - set(action.del_effects)) | set(action.add_effects)
            if explore(nxt, depth - 1):
                return True
        return False

    assert not explore(frozenset(problem.init), HAND_VERIFIED_OPTIMUM - 1)


def test_the_plan_is_the_expected_one(plan):
    assert plan.actions == [
        "(pick ball1 rooma left)",
        "(pick ball2 rooma right)",
        "(move rooma roomb)",
        "(drop ball1 roomb left)",
        "(drop ball2 roomb right)",
    ]


def test_plan_reports_which_backend_produced_it(plan):
    assert plan.backend in backends.TIERS
    assert plan.optimal is True


# ------------------------------------------------------------------ the parser

def test_domain_parses_into_types_predicates_and_actions(instance):
    domain, _ = instance
    assert domain.name == "gripper"
    assert domain.types == {"room": "object", "ball": "object", "gripper": "object"}
    assert sorted(domain.predicates) == ["at", "at-robby", "carry", "free"]
    assert sorted(a.name for a in domain.actions) == ["drop", "move", "pick"]


def test_problem_parses_into_typed_objects_init_and_goal(instance):
    _, problem = instance
    assert problem.domain_name == "gripper"
    assert dict(problem.objects)["ball1"] == "ball"
    assert ("at-robby", "rooma") in problem.init
    assert ("at", "ball1", "roomb") in problem.goal_positive


def test_grounding_respects_parameter_types(instance):
    domain, problem = instance
    grounded = ground_actions(domain, problem)
    assert len(grounded) == 4 + 8 + 8          # move / pick / drop
    for action in grounded:
        if action.name == "pick":
            ball, room, gripper = action.args
            assert ball.startswith("ball")
            assert room.startswith("room")
            assert gripper in ("left", "right")


def test_unsupported_pddl_is_rejected_rather_than_mis_parsed():
    text = """
    (define (domain broken) (:requirements :strips)
      (:predicates (p ?x))
      (:action a :parameters () :precondition (forall (?x) (p ?x)) :effect (p a)))
    """
    with pytest.raises(PddlError):
        parse_domain(text)


# ---------------------------------------------------------------- the validator

def test_validator_rejects_an_out_of_order_plan(instance):
    domain, problem = instance
    with pytest.raises(InvalidPlan):
        validate_plan(domain, problem, ["(drop ball1 rooma left)"])


def test_validator_rejects_an_unknown_action(instance):
    domain, problem = instance
    with pytest.raises(InvalidPlan):
        validate_plan(domain, problem, ["(teleport ball1 roomb)"])


def test_validator_rejects_a_plan_that_stops_short(instance):
    domain, problem = instance
    with pytest.raises(InvalidPlan):
        validate_plan(
            domain,
            problem,
            ["(pick ball1 rooma left)", "(move rooma roomb)", "(drop ball1 roomb left)"],
        )


def test_validator_accepts_a_different_but_correct_plan(instance):
    """Optimality is not the same as uniqueness; a longer valid plan still validates."""
    domain, problem = instance
    assert validate_plan(
        domain,
        problem,
        [
            "(pick ball1 rooma left)",
            "(move rooma roomb)",
            "(drop ball1 roomb left)",
            "(move roomb rooma)",
            "(pick ball2 rooma left)",
            "(move rooma roomb)",
            "(drop ball2 roomb left)",
        ],
    )


# ---------------------------------------------------------- the Fast Downward path

def test_fast_downward_plan_files_parse_even_without_fast_downward():
    text = "(pick ball1 rooma left)\n(move rooma roomb)\n; cost = 2 (unit cost)\n"
    assert backends.parse_sas_plan(text) == [
        "(pick ball1 rooma left)",
        "(move rooma roomb)",
    ]


@pytest.mark.skipif(
    backends.find_fast_downward() is None, reason="Fast Downward is not installed"
)
def test_fast_downward_agrees_with_the_stub(instance):
    domain, problem = instance
    fd_plan = fd_adapter.solve()
    assert fd_plan.backend == backends.FD_OPTIMAL
    assert fd_plan.length == HAND_VERIFIED_OPTIMUM
    assert validate_plan(domain, problem, fd_plan.actions)


def test_backend_selection_falls_back_without_crashing():
    assert fd_adapter.solve(prefer="stub").backend == "stub-bfs"


def test_the_rung_that_answered_is_in_the_payload(plan):
    """A length means different things per rung, so the payload always names one."""
    payload = plan.as_json()
    assert payload["backend"] in backends.TIERS
    assert payload["search"] == "bfs"


# ------------------------------------------------------- contract compliance

def test_candidates_satisfy_the_frozen_schema(plan):
    rows = fd_adapter.candidates(plan, timestamp="2026-07-27T00:00:00Z")
    assert validate_rows(rows) == []
    assert len(rows) == 1
    row = rows[0]
    assert row["engine"] == "fd_adapter"
    assert row["kind"] == "plan"
    payload = row["payload"]
    assert payload["length"] == HAND_VERIFIED_OPTIMUM
    assert payload["optimal"] is True
    assert payload["domain"] == "gripper"
    assert len(payload["actions"]) == HAND_VERIFIED_OPTIMUM
