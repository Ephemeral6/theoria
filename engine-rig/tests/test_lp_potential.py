"""M5 acceptance: pagoda weights that certify unsolvability and bound the search."""

import math
from dataclasses import replace
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


# ------------------------------------------------- the headline reads the check

#: A certificate that passes all three exact conditions and is still wrong about
#: the world, because one legal move was never in the list it was checked
#: against.  `jump(3,2,1)` is dropped; the remaining three are non-increasing
#: under these weights, so `check_exactly` returns True three times over.  Found
#: by exhaustive search over integer weights in [-4,4]: with the *complete* move
#: list there is no such vector, which is the point -- the gap is the shared
#: premise, not the arithmetic.  See DECISIONS.md D-035, site 1.
DROPPED_MOVE = "jump(3,2,1)"
HOLES_WEIGHTS = [-4, 0, -4, -4]


def _certificate_missing_one_move(graph):
    moves = [m for m in moves_from_graph(graph) if m.name() != DROPPED_MOVE]
    assert len(moves) == 3
    certificate = lp_potential.Certificate(
        weights=[Fraction(w) for w in HOLES_WEIGHTS],
        initial=UNSOLVABLE,
        goal_states=list(graph["goal_states"]),
        moves=moves,
        margin=Fraction(1),
    )
    certificate.conditions = lp_potential.check_exactly(certificate)
    return certificate


def test_admissible_is_false_when_the_certificate_fails_its_own_recheck(solved):
    """The negative sample E16 asks for: `holds=False` must reach the headline.

    `"admissible": True` used to be a literal in the payload, so this certificate
    -- which fails the exact rational re-check its own admissibility argument
    rests on -- published itself as admissible anyway.
    """
    certificate, heuristic = solved
    broken = replace(certificate, conditions={
        "inv_init": True, "inv_closed": False, "goal_break": True,
    })
    assert broken.holds is False

    payload = lp_potential.Heuristic(
        certificate=broken, max_decrease=heuristic.max_decrease
    ).as_json()
    assert payload["admissible"] is False
    assert payload["admissible_basis"]["certificate_holds"] is False


def test_an_unchecked_certificate_is_not_admissible(solved):
    """Empty `conditions` means nobody ran the check -- not that it passed."""
    certificate, heuristic = solved
    unchecked = replace(certificate, conditions={})
    assert unchecked.holds is False
    payload = lp_potential.Heuristic(
        certificate=unchecked, max_decrease=heuristic.max_decrease
    ).as_json()
    assert payload["admissible"] is False


def test_a_counterexample_in_the_check_overrides_a_holding_certificate(graph):
    """The empirical half can only subtract, and here it has to.

    This certificate `holds` -- all three conditions, exact, over the rationals --
    and the heuristic built from it says `h = inf` for two states that are one
    and two moves from the goal.  `h = inf` is a per-state *unsolvability* claim,
    so the payload's old literal published a false unsolvability claim as
    admissible.  What went wrong is not the arithmetic: it is that
    `check_exactly` iterates the move list the producer handed it, so a move
    missing from that list is unconstrained in the LP and unexamined in the
    re-check at once.
    """
    certificate = _certificate_missing_one_move(graph)
    assert certificate.holds is True
    assert certificate.conditions == {
        "inv_init": True, "inv_closed": True, "goal_break": True,
    }

    heuristic = lp_potential.heuristic_from(certificate)
    report = lp_potential.admissibility_report(heuristic, graph)
    counterexamples = [r for r in report if not r["admissible"]]
    assert [r["state"] for r in counterexamples] == ["0011", "1101"]
    assert all(math.isinf(r["h"]) for r in counterexamples)
    assert [r["true_distance"] for r in counterexamples] == [1, 2]

    payload = heuristic.as_json(report)
    assert payload["admissible"] is False
    assert payload["admissible_basis"]["certificate_holds"] is True
    assert payload["admissible_basis"]["counterexamples"] == counterexamples

    # ...and end to end through the emitter, which is where it reaches an
    # artefact.  The default there is to withhold both rows outright, so the
    # marked form is what carries the verdict into a payload.
    assert lp_potential.candidates(certificate, heuristic, graph,
                                   timestamp="2026-07-27T00:00:00Z") == []
    rows = lp_potential.candidates(certificate, heuristic, graph,
                                   timestamp="2026-07-27T00:00:00Z", on_unsound="mark")
    assert validate_rows(rows) == []
    assert rows[1]["payload"]["admissible"] is False


def test_the_headline_and_the_evidence_come_from_one_expression(solved, graph):
    """No payload may carry `admissible: true` beside a check that disagrees.

    D-033's finding, applied here: two sites computing the same verdict is the
    defect, so this asserts the invariant over a spread of certificates rather
    than pinning the implementation.
    """
    certificate, heuristic = solved
    variants = [
        certificate,
        _certificate_missing_one_move(graph),
        replace(certificate, conditions={"inv_init": True, "inv_closed": False,
                                         "goal_break": True}),
        replace(certificate, conditions={}),
    ]
    seen = set()
    for variant in variants:
        h = lp_potential.heuristic_from(variant)
        report = lp_potential.admissibility_report(h, graph)
        payload = h.as_json(report)
        expected = variant.holds and all(r["admissible"] for r in report)
        assert payload["admissible"] == expected
        seen.add(payload["admissible"])
    assert seen == {True, False}, "the spread must exercise both verdicts"


# --------------------------------- the premises are checked against the graph

def test_the_invariant_row_is_gated_too_not_just_the_heuristic(graph):
    """The first cut of E16 gated one of the two rows. That was the same defect.

    Both rows come from one weight vector. Gating only the heuristic left the
    invariant going out as `goal unreachable from 1110` with all three conditions
    `true`, beside a heuristic row whose counterexamples prove `inv_closed` is
    false over the real move set -- two rows contradicting each other, nothing
    saying which wins. Found by an adversarial review of the fix, not by the fix.
    """
    certificate = _certificate_missing_one_move(graph)
    heuristic = lp_potential.heuristic_from(certificate)
    assert certificate.holds is True                    # the premise it was checked on

    assert lp_potential.candidates(certificate, heuristic, graph,
                                   timestamp="2026-07-27T00:00:00Z") == []

    rows = lp_potential.candidates(certificate, heuristic, graph,
                                   timestamp="2026-07-27T00:00:00Z", on_unsound="mark")
    assert validate_rows(rows) == []
    assert [row["payload"]["unsound"] for row in rows] == [True, True]
    assert rows[0]["payload"]["holds"] is False
    assert rows[1]["payload"]["admissible"] is False


def test_the_premise_check_asks_the_graph_not_the_certificate(graph):
    """`check_exactly` cannot catch a move missing from the list it iterates.

    So the emitter recomputes `inv_closed` over every geometry the graph has --
    the one check the certificate's own inputs structurally cannot perform.
    """
    certificate = _certificate_missing_one_move(graph)
    check = lp_potential.premises_against_graph(certificate, graph)
    assert check["move_list_complete"] is False
    assert check["missing_moves"] == [DROPPED_MOVE]
    assert check["moves_raising_potential"] == [DROPPED_MOVE]
    assert check["sound_over_graph"] is False

    honest, _ = lp_potential.run(graph, UNSOLVABLE)
    clean = lp_potential.premises_against_graph(honest, graph)
    assert clean["sound_over_graph"] is True
    assert clean["missing_moves"] == [] and clean["moves_raising_potential"] == []


def test_conditions_alone_cannot_be_read_as_a_verdict(solved, graph):
    """`all({}.values())` is True, so the payload has to publish `holds` itself."""
    certificate, _ = solved
    unchecked = replace(certificate, conditions={})
    assert all(unchecked.as_json()["conditions"].values()) is True   # the trap
    assert unchecked.as_json()["holds"] is False                    # the verdict


def test_a_foreign_goal_set_is_not_scored_against_the_graphs_distances(graph):
    """`run(..., goal_states=[...])` is supported; the empirical check is not.

    `admissibility_report` measures h against `graph["distance_to_goal"]`, which
    is the distance to the *graph's* goals. On a certificate about another set
    those distances answer a different question, and every row it produces is a
    fabricated counterexample -- a provably admissible heuristic published as
    inadmissible. So the check is declined rather than mis-scored.
    """
    certificate, heuristic = lp_potential.run(graph, "0111", goal_states=["1010"])
    assert certificate is not None
    rows = lp_potential.candidates(certificate, heuristic, graph,
                                   timestamp="2026-07-27T00:00:00Z")
    assert validate_rows(rows) == []
    payload = rows[1]["payload"]
    assert payload["admissible"] is True
    assert "not comparable" in payload["admissible_basis"]["empirical_check"]
    assert "admissibility_check" not in payload
    assert payload["premise_check"]["goal_states_match_graph"] is False


def test_an_empty_report_is_vacuous_not_a_pass(solved):
    """`not []` is True. "No state was examined" must not read as "all passed"."""
    _, heuristic = solved
    basis = heuristic.as_json([])["admissible_basis"]
    assert "vacuous" in basis["empirical_check"]
    assert basis["counterexamples"] == []


def test_an_unknown_unsound_policy_is_refused(solved, graph):
    certificate, heuristic = solved
    with pytest.raises(ValueError):
        lp_potential.candidates(certificate, heuristic, graph, on_unsound="ship-it")
