"""M3 acceptance: push is mined with high coverage, teleport is flagged 1/1."""

import pytest

from common.jsonio import read_json, read_jsonl
from engines import cegis_miner, mdl_segmenter
from engines.cegis_miner.atoms import Atom, State, evaluate
from engines.cegis_miner.miner import Effect, NoSeparatingGuard, Transition
from fixtures import cart_world
from tools.validate_candidates import validate_rows


@pytest.fixture(scope="module")
def mined():
    rows = read_jsonl(cart_world.TRAJ_PATH)
    truth = read_json(cart_world.TRUTH_PATH)
    frames = [row["frame"] for row in rows]
    actions = [row["action"] for row in rows]
    seg = mdl_segmenter.segment_trajectory(frames)
    transitions = cegis_miner.transitions_from_segmentation(frames, actions, seg)
    return cegis_miner.mine(transitions), transitions, truth


def _holds(guard, transition):
    return all(evaluate(atom, transition.state, transition.action) for atom in guard)


# --------------------------------------------------------------- the two rules

def test_push_rule_is_mined_with_the_right_guard_and_effect(mined):
    result, _, truth = mined
    push = result.by_name("push")
    assert push is not None
    assert push.guard_names() == ["act==?dir", "free(strip(?dir))"]
    assert push.effect.as_json() == {"type": "move", "direction": "?dir"}
    n_moves = sum(1 for e in truth["events"] if e.startswith("move:"))
    assert push.coverage == "%d/%d" % (n_moves, n_moves)
    assert n_moves > 20, "the push rule should rest on plenty of evidence"
    assert sorted(push.lifted_from) == ["push_DOWN", "push_LEFT", "push_RIGHT", "push_UP"]


def test_teleport_rule_is_mined_and_flagged_as_single_witness(mined):
    result, _, truth = mined
    teleport = result.by_name("teleport")
    assert teleport is not None
    assert teleport.coverage == "1/1"
    assert teleport.guard_names() == ["at(%d,%d)" % tuple(truth["portal_a"])]
    effect = teleport.effect.as_json()
    assert effect["type"] == "move"
    assert effect["to"] == truth["portal_b"]
    assert abs(effect["dy"]) + abs(effect["dx"]) > 1, "teleport is not a unit step"
    assert teleport.support == [truth["teleport_transition"]]


def test_teleport_has_the_thinnest_evidence_of_all_mined_rules(mined):
    result, _, _ = mined
    teleport = result.by_name("teleport")
    push = result.by_name("push")
    assert len(teleport.support) < len(push.support)
    assert len(teleport.support) == 1


# ------------------------------------------------------ per-direction ground rules

@pytest.mark.parametrize("direction", ["UP", "DOWN", "LEFT", "RIGHT"])
def test_each_direction_push_rule_matches_ground_truth(mined, direction):
    result, _, truth = mined
    rule = result.by_name("push_%s" % direction)
    assert rule is not None
    assert rule.guard_names() == ["act==%s" % direction, "free(strip(%s))" % direction]
    dy, dx = cart_world.DELTA[direction]
    assert (rule.effect.dy, rule.effect.dx) == (dy, dx)
    expected = [i for i, e in enumerate(truth["events"]) if e == "move:" + direction]
    assert rule.support == expected
    assert rule.coverage == "%d/%d" % (len(expected), len(expected))


def test_blocked_rules_cover_the_noop_transitions(mined):
    result, _, truth = mined
    covered = sorted(
        i for r in result.rules if r.effect.type == "none" for i in r.support
    )
    expected = [i for i, e in enumerate(truth["events"]) if e == "noop"]
    assert covered == expected


# --------------------------------------------------------------- the frontier

def test_frontier_keeps_the_indistinguishable_guards_rather_than_guessing(mined):
    """free / in_bounds cannot be told apart on a one-object board (D-002)."""
    result, _, _ = mined
    push = result.by_name("push")
    frontier = [sorted(a.name for a in g) for g in push.frontier]
    assert ["act==?dir", "free(strip(?dir))"] in frontier
    assert ["act==?dir", "in_bounds(strip(?dir))"] in frontier


def test_frontier_of_the_single_witness_rules_holds_more_than_one_hypothesis(mined):
    """One witness cannot pin a guard down, and the engine does not pretend it can."""
    result, _, _ = mined
    for name in ("teleport", "blocked_UP"):
        rule = result.by_name(name)
        assert len(rule.frontier) > 1, name


def test_frontier_of_blocked_up_still_contains_the_general_wall_guard(mined):
    """The cheap position guard wins, but the general one is not thrown away."""
    result, _, _ = mined
    rule = result.by_name("blocked_UP")
    frontier = [set(sorted(a.name for a in g)) for g in rule.frontier]
    assert any(
        {"act==UP", "!in_bounds(strip(UP))"} <= guard for guard in frontier
    ), frontier


def test_every_frontier_guard_really_is_consistent_with_the_ledger(mined):
    """Re-check the frontier by direct evaluation, not by the miner's bitmasks."""
    result, transitions, _ = mined
    for rule in result.rules:
        support = set(rule.support)
        for guard in rule.frontier:
            fires = {t.index for t in transitions if _holds(guard, t)}
            assert fires == support, (rule.name, sorted(a.name for a in guard))


# ------------------------------------------------------- counterexample-guided

def test_synthesis_is_actually_counterexample_guided(mined):
    result, transitions, _ = mined
    for rule in result.rules:
        assert rule.cegis_trace, rule.name
        for step in rule.cegis_trace:
            cex = step["counterexample"]
            assert cex not in rule.support
            atom = next(a for a in rule.cegis_guard if a.name == step["added"]) \
                if any(a.name == step["added"] for a in rule.cegis_guard) else None
            if atom is not None:
                offender = transitions[cex]
                assert not evaluate(atom, offender.state, offender.action)


def test_the_cegis_guard_itself_separates_its_effect_class(mined):
    result, transitions, _ = mined
    for rule in result.rules:
        fires = {t.index for t in transitions if _holds(rule.cegis_guard, t)}
        assert fires == set(rule.support), rule.name


def test_contradictory_evidence_is_reported_not_papered_over():
    """Same state, same action, two different effects -- no guard can separate them."""
    frame = tuple(tuple(0 for _ in range(6)) for _ in range(6))
    state = State(frame=frame, anchor=(2, 2), shape=(1, 1))
    transitions = [
        Transition(0, state, "UP", Effect("move", dy=-1, dx=0)),
        Transition(1, state, "UP", Effect("none")),
    ]
    with pytest.raises(NoSeparatingGuard):
        cegis_miner.mine(transitions)


# -------------------------------------------------- constraint 9 and coverage

def test_ground_rule_guards_are_mutually_exclusive(mined):
    result, _, _ = mined
    assert result.guards_are_mutually_exclusive()


def test_the_rule_set_explains_every_transition(mined):
    result, _, _ = mined
    assert result.explains_every_transition()


def test_coverage_denominator_counts_every_transition_the_guard_admits(mined):
    result, transitions, _ = mined
    for rule in result.rules:
        k, n = (int(x) for x in rule.coverage.split("/"))
        fires = [t.index for t in transitions if _holds(rule.guard, t)]
        assert n == len(fires), rule.name
        assert k == len(rule.support), rule.name


# ------------------------------------------------------- contract compliance

def test_candidates_satisfy_the_frozen_schema(mined):
    result, _, _ = mined
    rows = cegis_miner.candidates(result, timestamp="2026-07-27T00:00:00Z")
    assert validate_rows(rows) == []
    assert all(row["kind"] == "rule_hypothesis" for row in rows)
    assert all(row["engine"] == "cegis_miner" for row in rows)
    names = {row["payload"]["name"]: row for row in rows}
    assert "push" in names and "teleport" in names
    assert names["teleport"]["evidence"]["coverage"] == "1/1"
    assert names["teleport"]["evidence"]["transitions"] == [25]
    k, n = (int(x) for x in names["push"]["evidence"]["coverage"].split("/"))
    assert k == n > 20
