"""Convergence interface: LP certificates in the form theory-compiler asked for.

Their M8 sync note: the A1 rehearsal used hand-computed pagoda constants and a
Lean proof by BFS enumeration, and the convergence sprint needs engine-rig's LP
output instead. These tests pin that interface, and pin the negative result that
came with it.
"""

from fractions import Fraction

from dataclasses import replace
from fractions import Fraction

import pytest

from common.jsonio import read_json
from engines.lp_potential.potential import solve_certificate
from fixtures import peg4
from interop import certificate_export as ce
from interop import peg1d

THEIRS = "11011"          # theory-compiler's peg fixture: 5 cells, centre empty


# ------------------------------------------- the generic builder agrees with M1

def test_generic_builder_reproduces_the_frozen_peg4_fixture():
    """peg1d must agree with fixtures/peg4 or the interface rests on a different world."""
    frozen = read_json(peg4.GRAPH_PATH)
    built = peg1d.build_graph(4, "1110", goal_states=frozen["goal_states"])
    assert built["states"] == frozen["states"]
    assert built["move_instances"] == frozen["move_instances"]
    assert built["edges"] == frozen["edges"]
    assert built["reachable"]["1110"] == frozen["reachable"]["1110"]


# ------------------------------------------- their claim, checked independently

def test_their_unsolvability_claim_is_correct():
    """[1,1,0,1,1] really cannot be reduced to one peg -- by enumeration."""
    graph = peg1d.build_graph(5, THEIRS)
    assert graph["solvable"][THEIRS] is False
    reachable = graph["reachable"][THEIRS]
    assert min(state.count("1") for state in reachable) == 2, reachable


def test_no_linear_pagoda_proves_their_stated_goal():
    """`goal count(Peg, alive=true) = 1` admits no linear pagoda certificate.

    Not a solver limitation: infeasible at every bound tried, while instances that
    do admit certificates still get them (see the control below). This is the
    expressiveness finding the convergence sprint has to know about.
    """
    graph = peg1d.build_graph(5, THEIRS)          # goal = any single peg
    for bound in (10, 100, 10000):
        assert solve_certificate(graph, THEIRS, bound=bound) is None, bound


def test_narrowing_the_goal_to_one_cell_does_admit_a_certificate():
    """The disjunction is unprovable; two of its disjuncts are provable."""
    provable, unprovable = [], []
    for j in range(5):
        goal = ["".join("1" if i == j else "0" for i in range(5))]
        graph = peg1d.build_graph(5, THEIRS, goal_states=goal)
        found = solve_certificate(graph, THEIRS, goal_states=goal, bound=10000)
        (provable if found else unprovable).append(j)
    assert provable == [1, 3]
    assert unprovable == [0, 2, 4]


def test_the_solver_still_finds_certificates_where_they_exist():
    """Control: 'infeasible' above is a real answer, not a broken solver."""
    graph = peg1d.build_graph(4, "1110", goal_states=["0100"])
    assert solve_certificate(graph, "1110", goal_states=["0100"]) is not None


# --------------------------------------------------------- the exported document

@pytest.fixture(scope="module")
def document():
    goal = ["01000"]
    graph = peg1d.build_graph(5, THEIRS, goal_states=goal)
    certificate = solve_certificate(graph, THEIRS, goal_states=goal, bound=10000)
    assert certificate is not None
    return ce.build(certificate, graph, claim_name="unsolvable_11011_to_01000")


def test_weights_are_integers_and_the_certificate_still_holds(document):
    assert all(isinstance(w, int) for w in document["weights_integer"])
    assert document["verified"] is True
    assert ce.verify(document) == []


def test_every_obligation_carries_its_own_witnesses(document):
    """Lean should only have to check, never re-derive."""
    closed = document["obligations"]["inv_closed"]
    assert closed["n_checked"] == len(closed["witnesses"]) == 6
    for witness in closed["witnesses"]:
        assert witness["delta"] == (
            witness["w_dst"] - witness["w_src"] - witness["w_over"]
        )
        assert witness["delta"] <= 0
    for witness in document["obligations"]["goal_break"]["witnesses"]:
        assert witness["exceeds_initial_by"] > 0


def test_integer_scaling_preserves_the_rational_certificate(document):
    rational = [Fraction(w) for w in document["weights_rational"]]
    integer = document["weights_integer"]
    ratios = {
        Fraction(integer[i], 1) / rational[i]
        for i in range(len(integer))
        if rational[i] != 0
    }
    assert len(ratios) == 1, "scaling must be a single positive multiple"
    assert next(iter(ratios)) > 0


def test_verify_rejects_a_tampered_certificate(document):
    """The importer must not have to trust the producer."""
    tampered = dict(document)
    tampered["weights_integer"] = list(document["weights_integer"])
    tampered["weights_integer"][2] += 5           # break a move constraint
    assert ce.verify(tampered) != []


def test_verify_rejects_a_goal_that_no_longer_breaks_the_invariant(document):
    tampered = dict(document)
    tampered["goal_states"] = ["10000"]           # potential -1, below the bound
    assert any("does not exceed" in e for e in ce.verify(tampered))


def test_the_document_is_self_contained(document):
    """An importer needs nothing but this file."""
    for key in ("schema", "weights_integer", "initial_state", "goal_states",
                "invariant", "obligations", "conclusion", "initial_potential"):
        assert key in document
    assert document["conclusion"].startswith("no goal state is reachable")


# ------------------------------------- the conclusion is derived, not asserted

def test_the_conclusion_is_not_stated_when_the_obligations_fail():
    """`conclusion` was a literal written above the line that computes `verified`.

    So a document whose obligations fail carried `verified: false` beside
    `conclusion: "no goal state is reachable from X"` -- the verdict as a sibling
    field of the headline it contradicts, which is the shape D-034 exists to
    stop. Found by an adversarial review of the E16 fix, in a file that fix had
    already edited.
    """
    goal = ["01000"]
    graph = peg1d.build_graph(5, THEIRS, goal_states=goal)
    certificate = solve_certificate(graph, THEIRS, goal_states=goal, bound=10000)
    assert certificate is not None

    # Break one weight so `inv_closed` genuinely fails on re-derivation.
    broken = replace(certificate, weights=[Fraction(9)] + list(certificate.weights[1:]))
    document = ce.build(broken, graph, claim_name="deliberately_broken")

    assert document["verified"] is False
    assert not document["conclusion"].startswith("no goal state is reachable")
    assert "nothing follows" in document["conclusion"]
    assert "inv_closed" in document["conclusion"]
    assert ce.verify(document) != []


def test_checked_over_says_what_was_actually_checked():
    """It read "all move instances on the full state space" as a literal.

    That is a producer assertion re-derived by nobody, and it is simply false for
    a document built from a partial move list -- while `n_checked`, `verified`
    and `verify()` all still agree with each other.
    """
    graph = peg1d.build_graph(4, "1110", goal_states=["0100"])
    certificate = solve_certificate(graph, "1110", goal_states=["0100"])
    assert certificate is not None
    full = ce.build(certificate, graph, claim_name="full")
    n = len(full["obligations"]["inv_closed"]["witnesses"])
    assert full["obligations"]["inv_closed"]["checked_over"] == (
        "the %d move instances this document lists" % n)

    partial = replace(certificate, moves=list(certificate.moves[:2]))
    thin = ce.build(partial, graph, claim_name="thin")
    assert thin["obligations"]["inv_closed"]["checked_over"] == (
        "the 2 move instances this document lists")
    assert thin["obligations"]["inv_closed"]["n_checked"] == 2
