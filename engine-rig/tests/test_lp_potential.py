"""M5 acceptance: pagoda weights that certify unsolvability and bound the search."""

import math
from fractions import Fraction

import pytest

from common.jsonio import read_json
from engines import lp_potential
from engines.lp_potential.potential import moves_from_graph
from fixtures import peg4
from tools.validate_candidates import validate_rows

UNSOLVABLE = "1110"
SOLVABLE = "1101"


@pytest.fixture(scope="module")
def graph():
    return read_json(peg4.GRAPH_PATH)


@pytest.fixture(scope="module")
def solved(graph):
    certificate, heuristic = lp_potential.run(graph, UNSOLVABLE)
    assert certificate is not None
    return certificate, heuristic


def _potential(weights, state):
    return sum((weights[i] for i, cell in enumerate(state) if cell == "1"), Fraction(0))


# ------------------------------------------------ the ground truth it rests on

def test_the_target_configuration_really_is_unsolvable(graph):
    """Hand-checkable by enumeration: 1110 reaches only 1001, never the goal."""
    assert graph["solvable"][UNSOLVABLE] is False
    assert graph["reachable"][UNSOLVABLE] == ["1001", "1110"]
    assert graph["goal"] not in graph["reachable"][UNSOLVABLE]
    assert graph["distance_to_goal"][UNSOLVABLE] is None


def test_the_comparison_configuration_really_is_solvable(graph):
    assert graph["solvable"][SOLVABLE] is True
    assert graph["distance_to_goal"][SOLVABLE] == 2


# ------------------------------------------------------------ the certificate

def test_certificate_weights_are_exact_rationals(solved):
    certificate, _ = solved
    assert all(isinstance(w, Fraction) for w in certificate.weights)


def test_the_three_certificate_conditions_hold(solved, graph):
    """Re-derived here in exact arithmetic, not by asking the engine again."""
    certificate, _ = solved
    weights = certificate.weights
    bound = _potential(weights, UNSOLVABLE)

    # 1. the invariant holds at the start
    assert _potential(weights, UNSOLVABLE) <= bound

    # 2. no legal move breaks it -- checked on every move instance over the FULL
    #    state space, so the argument does not depend on what is reachable
    for move in moves_from_graph(graph):
        delta = weights[move.dst] - weights[move.src] - weights[move.over]
        assert delta <= 0, move.name()

    # 3. winning requires breaking it
    for goal in graph["goal_states"]:
        assert _potential(weights, goal) > bound

    assert certificate.conditions == {
        "inv_init": True,
        "inv_closed": True,
        "goal_break": True,
    }


def test_the_certificate_covers_every_edge_of_the_state_graph(solved, graph):
    certificate, _ = solved
    constrained = {(m.src, m.over, m.dst) for m in certificate.moves}
    for edge in graph["edges"]:
        assert tuple(edge["positions"]) in constrained


def test_potential_is_non_increasing_on_every_edge(solved, graph):
    certificate, _ = solved
    for edge in graph["edges"]:
        before = certificate.potential(edge["src_state"])
        after = certificate.potential(edge["dst_state"])
        assert after <= before, edge


def test_no_certificate_exists_for_a_solvable_configuration(graph):
    """Soundness: the method must be unable to prove something false."""
    certificate, heuristic = lp_potential.run(graph, SOLVABLE)
    assert certificate is None
    assert heuristic is None


def test_the_method_is_sound_on_every_configuration(graph):
    """A certificate is produced only where the enumeration agrees it is unsolvable."""
    for config in graph["initial_configs"]:
        certificate, _ = lp_potential.run(graph, config)
        if certificate is not None:
            assert graph["solvable"][config] is False, config


def test_linear_pagodas_are_sound_but_not_complete(graph):
    """0111 is unsolvable and no linear potential proves it. Stated, not hidden."""
    assert graph["solvable"]["0111"] is False
    assert lp_potential.solve_certificate(graph, "0111") is None


# --------------------------------------------------------------- the heuristic

def test_heuristic_never_exceeds_the_true_shortest_path(solved, graph):
    """Admissibility, on every state from which the goal is actually reachable."""
    _, heuristic = solved
    checked = 0
    for state, distance in graph["distance_to_goal"].items():
        if distance is None:
            continue
        assert heuristic.value(state) <= distance, state
        checked += 1
    assert checked >= 3


def test_heuristic_on_the_solvable_configuration_is_a_valid_lower_bound(solved, graph):
    _, heuristic = solved
    value = heuristic.value(SOLVABLE)
    assert value <= graph["distance_to_goal"][SOLVABLE]
    assert value >= 0


def test_heuristic_is_zero_at_the_goal(solved, graph):
    _, heuristic = solved
    assert heuristic.value(graph["goal"]) == 0


def test_an_infinite_heuristic_only_ever_means_genuinely_unreachable(solved, graph):
    """h = inf is a per-state unsolvability claim; every one of them must be true."""
    _, heuristic = solved
    infinite = [s for s in graph["states"] if math.isinf(heuristic.value(s))]
    assert infinite
    for state in infinite:
        assert graph["distance_to_goal"][state] is None, state


def test_the_report_marks_every_checked_state_admissible(solved, graph):
    _, heuristic = solved
    report = lp_potential.admissibility_report(heuristic, graph)
    assert report
    assert all(row["admissible"] for row in report)
    assert all(row["h"] <= row["true_distance"] for row in report)


# ------------------------------------------------------- contract compliance

def test_candidates_satisfy_the_frozen_schema(solved, graph):
    certificate, heuristic = solved
    rows = lp_potential.candidates(
        certificate, heuristic, graph, timestamp="2026-07-27T00:00:00Z"
    )
    assert validate_rows(rows) == []
    kinds = [row["kind"] for row in rows]
    assert kinds == ["invariant", "heuristic"]
    assert all(row["engine"] == "lp_potential" for row in rows)

    invariant = rows[0]["payload"]
    assert invariant["form"] == "potential_weights"
    assert invariant["initial"] == UNSOLVABLE
    assert invariant["conditions"] == {
        "inv_init": True,
        "inv_closed": True,
        "goal_break": True,
    }
    assert all("/" in w or w.lstrip("-").isdigit() for w in invariant["weights"])

    heuristic_payload = rows[1]["payload"]
    assert heuristic_payload["form"] == "potential_lower_bound"
    assert heuristic_payload["admissible"] is True
    assert all(row["admissible"] for row in heuristic_payload["admissibility_check"])


def test_the_certificate_and_the_heuristic_share_one_weight_vector(solved, graph):
    """'Certificate and heuristic are the same object' -- literally, here."""
    certificate, heuristic = solved
    rows = lp_potential.candidates(
        certificate, heuristic, graph, timestamp="2026-07-27T00:00:00Z"
    )
    assert rows[0]["payload"]["weights"] == rows[1]["payload"]["weights"]
