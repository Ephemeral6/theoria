"""probe_frontier + fd_adapter: a probe that knows what it costs to run.

A0 emitted zero executable probes (THEORIZE_LOG P-01..P-03), so the machinery
was never exercised on the question it exists to answer.  Two configurations
here, worth exactly one bit each, and the planner is what tells them apart:

  * `p_row1` reachable in 10 moves, so it is executable at a path cost of 11;
  * `p_side` unreachable, so the honest output is a verdict, not a design.
"""

import math

import pytest

from common.jsonio import read_jsonl
from engines import deadlock_carver as dc
from engines import fd_adapter
from engines import probe_frontier as pf
from engines.fd_adapter.pddl import parse_domain, parse_problem
from engines.probe_frontier import sokoban_probe as sp
from fixtures import sokoban
from tools.validate_candidates import validate_file


@pytest.fixture(scope="module")
def world():
    with open(sokoban.DOMAIN_PATH, "r", encoding="utf-8") as fh:
        domain = parse_domain(fh.read())
    with open(sokoban.RING.path, "r", encoding="utf-8") as fh:
        problem = parse_problem(fh.read())
    return domain, problem


@pytest.fixture(scope="module")
def probes(world):
    domain, problem = world
    bundle = sp.build()
    return {
        p.configuration.name: p
        for p in pf.design(bundle["hypotheses"], bundle["configurations"], domain, problem)
    }


# ------------------------------------------------------------- the frontier

def test_the_frontier_survives_the_evidence_and_a_third_hypothesis_does_not():
    """Consistency is a filter here, not a rubber stamp."""
    assert sp.consistent(sp.H_FREE_PUSH)
    assert sp.consistent(sp.H_NO_CORNER_ENTRY)
    assert not sp.consistent(sp.H_BOXES_NEVER_MOVE)


def test_the_two_survivors_agree_on_everything_the_ring_ever_showed():
    for board, action, observed in sp.PAST_EVIDENCE:
        assert sp.H_FREE_PUSH.predict(board, action) == observed
        assert sp.H_NO_CORNER_ENTRY.predict(board, action) == observed


def test_they_come_apart_only_on_a_push_into_a_corner():
    """Both configurations split, and they split on the same disagreement."""
    for board, action in ((sp.ROW1, "left"), (sp.SIDE, "down")):
        assert sp.H_FREE_PUSH.predict(board, action) == sp.PUSH
        assert sp.H_NO_CORNER_ENTRY.predict(board, action) == sp.BLOCKED


# ------------------------------------------------------- the planner's answer

def test_the_reachable_probe_is_promoted_and_carries_its_plan(probes):
    probe = probes["p_row1"]
    assert probe.tier == pf.EXECUTABLE
    assert probe.reach.status == pf.REACHABLE
    assert probe.best.action == "left"
    assert probe.entropy == 1.0
    assert probe.reach.length == 10
    assert probe.cost == 11.0
    assert probe.value == pytest.approx(1.0 / 11.0)


def test_the_reach_plan_really_reaches_the_configuration(world, probes):
    """Validated by fd_adapter's independent replayer, not by the search."""
    domain, base = world
    probe = probes["p_row1"]
    problem = pf.reachability_problem(base, probe.configuration.goal_atoms, "check")
    assert fd_adapter.validate_plan(domain, problem, probe.reach.plan)


def test_the_reach_plan_walks_the_long_way_round_rather_than_pushing(probes):
    """The box must still be where the probe wants it when the player arrives."""
    plan = probes["p_row1"].reach.plan
    assert len(plan) == 10
    assert all(step.startswith("(move ") for step in plan)


def test_the_unreachable_probe_gets_a_verdict_not_a_design(probes):
    probe = probes["p_side"]
    assert probe.reach.status == pf.UNREACHABLE
    assert probe.tier == pf.HYPOTHETICAL
    assert probe.reach.plan is None
    assert probe.cost == math.inf
    assert probe.value == 0.0
    # It is not that the probe is uninformative -- it is a full bit, unrunnable.
    assert probe.entropy == 1.0
    assert probe.best.action == "down"


def test_path_cost_is_what_orders_them(probes, world):
    domain, problem = world
    bundle = sp.build()
    ranked = pf.design(bundle["hypotheses"], bundle["configurations"], domain, problem)
    assert [p.configuration.name for p in ranked] == ["p_row1", "p_side"]
    assert ranked[0].entropy == ranked[1].entropy      # equal bits...
    assert ranked[0].value > ranked[1].value           # ...separated by cost alone


def test_the_hand_computed_answers_are_the_engine_answers(probes):
    hand = sp.build()["hand_computed"]
    assert probes["p_row1"].best.action == hand["p_row1"]["action"]
    assert probes["p_row1"].reach.length == hand["p_row1"]["reach_length"]
    assert probes["p_row1"].cost == hand["p_row1"]["cost"]
    assert probes["p_side"].reach.status == hand["p_side"]["reach"]


# -------------------------------------------------- the reachability problem

def test_the_reachability_problem_changes_the_goal_and_nothing_else(world):
    _, base = world
    goal = sp.ROW1.goal_atoms()
    derived = pf.reachability_problem(base, goal, "reach-test")
    assert derived.init == base.init
    assert derived.objects == base.objects
    assert derived.domain_name == base.domain_name
    assert derived.goal_positive == [tuple(atom) for atom in goal]
    assert derived.goal_negative == []
    assert base.goal_positive != derived.goal_positive    # the base is untouched


def test_deadlock_pruning_speeds_the_query_without_changing_the_answer(world):
    """One theorem, three consumers: candidates, the planner, and this."""
    domain, base = world
    bundle = sp.build()
    theorems = dc.carve(dc.Task.build(domain, base))
    blind = pf.design(bundle["hypotheses"], bundle["configurations"], domain, base)
    pruned = pf.design(
        bundle["hypotheses"], bundle["configurations"], domain, base,
        prune=dc.pruner(theorems),
    )
    assert [p.reach.status for p in blind] == [p.reach.status for p in pruned]
    assert [p.reach.plan for p in blind] == [p.reach.plan for p in pruned]
    assert sum(p.reach.expansions for p in pruned) < sum(p.reach.expansions for p in blind)


# ---------------------------------------------------------------- emission

def test_the_emitted_stream_satisfies_the_frozen_schema(world, tmp_path):
    domain, base = world
    out = str(tmp_path / "candidates.jsonl")
    bundle = sp.build()
    pf.run_with_planner(
        bundle["hypotheses"], bundle["configurations"], domain, base,
        transitions=list(range(len(bundle["evidence"]))),
        out_path=out, timestamp="2026-07-27T00:00:00Z",
    )
    assert validate_file(out) == []

    rows = read_jsonl(out)
    assert len(rows) == 2
    assert all(row["engine"] == "probe_frontier" for row in rows)
    assert all(row["kind"] == "probe_design" for row in rows)

    by_name = {row["payload"]["configuration"]: row["payload"] for row in rows}
    assert by_name["p_row1"]["tier"] == "executable"
    assert by_name["p_row1"]["reach"]["length"] == 10
    assert by_name["p_row1"]["cost"] == 11.0
    assert by_name["p_side"]["verdict"] == "unreachable"
    assert by_name["p_side"]["cost"] is None


def test_the_payload_still_carries_the_older_probe_design_keys(world, tmp_path):
    """Extended, not replaced -- a reader of the M7 shape still reads this one."""
    domain, base = world
    out = str(tmp_path / "candidates.jsonl")
    bundle = sp.build()
    pf.run_with_planner(bundle["hypotheses"], bundle["configurations"], domain, base,
                        out_path=out, timestamp="2026-07-27T00:00:00Z")
    payload = read_jsonl(out)[0]["payload"]
    for key in ("action", "entropy_bits", "value_bits_per_cost", "cost",
                "n_hypotheses", "hypotheses", "partition", "ranking", "state",
                "rendering"):
        assert key in payload
    assert payload["state"][1].count("$") == 1        # the board, drawn
    assert payload["state"][1].count("@") == 1
