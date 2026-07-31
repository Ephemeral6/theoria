"""E18 -- the four defects that were only visible on a corpus that never happens.

`tools/survey_numbers/lp_incomplete.py` audits `lp_potential` over 3000 worlds
whose solver-status histogram is `{0: 1550, 2: 1450}`.  Every branch that handles
an *undecided* solve is therefore dead code on the real corpus, and four defects
lived in that dead code -- three of them the same defect commit `2a1c30d` exists
to remove ("a tool that failed is not a fact about the world"), reappearing
inside the audit written to check it.

They were found by an adversarial review that built a synthetic corpus, injected
it, threw the harness away, and wrote the findings into
`runs/20260730T120000Z-E18/adversarial/undecided_injection.json`.  An injection
harness that exists once and is thrown away is how the defects got in, so it
lives here now.

Fast on purpose: no world is solved.  The rows are exactly the shape `survey()`
emits, and where a solver is needed at all it is replaced by a function that
returns the outcome the test is about.  Compare `tests/test_survey_numbers.py`,
which guards the wiring; this file guards the predicates.
"""

from fractions import Fraction

import pytest

from engines.lp_potential import potential
from tools.survey_numbers import lp_incomplete as L


# --------------------------------------------------------------- the corpus

def row(i, *, reachable, certificate_issued, solver_status, engine_status,
        certificate_error=False, seed=None):
    """One `survey()` row, by hand."""
    return {
        "i": i, "seed": 1000 + i if seed is None else seed,
        "n_pos": 5, "n_goals": 1, "n_triples": 5,
        "reachable": reachable, "bfs_exhausted": True, "states_enumerated": 4,
        "oracles_agree": True,
        "certificate_issued": certificate_issued,
        "certificate_error": certificate_error,
        "engine_status": engine_status,
        "solver_status": solver_status,
        "lp_unavailable": engine_status in (potential.BUDGET, potential.UNBOUNDED,
                                            potential.NUMERICAL,
                                            potential.UNDECIDED),
        "run_vs_decide_disagreement": False,
    }


@pytest.fixture
def injected():
    """Ten unreachable worlds: 4 certified (st 0), 3 infeasible (st 2), 3 capped (st 1).

    The status-1 worlds are the ones that have never occurred.  The truth:

    * new rule -- "no linear pagoda" is status 2 only  -> numerator 3
    * old rule -- pre-2a1c30d, "not success"           -> numerator 6
    * the two rules differ on exactly the 3 status-1 worlds
    """
    rows = [row(i, reachable=False, certificate_issued=True, solver_status=0,
                engine_status=potential.CERTIFIED) for i in range(4)]
    rows += [row(4 + i, reachable=False, certificate_issued=False, solver_status=2,
                 engine_status=potential.NO_LINEAR_PAGODA) for i in range(3)]
    rows += [row(7 + i, reachable=False, certificate_issued=False, solver_status=1,
                 engine_status=potential.BUDGET) for i in range(3)]
    return rows


# ------------------------------------------------- F1: the numerator predicate

def test_incompleteness_does_not_count_a_solver_failure_as_a_fact(injected):
    """An iteration limit is not "no linear pagoda exists"."""
    result = L._incompleteness(injected)
    assert result["numerator"] == 3, (
        "the numerator counted %d of 10 unreachable worlds; 3 of them are "
        "HiGHS status 1, which says the solver stopped, not that the geometry "
        "refuses. `not certificate_issued` is the collapsed predicate 2a1c30d "
        "removed from the engine and it must not come back in the audit."
        % result["numerator"]
    )
    assert result["denominator"] == 10
    # and the collapsed reading is still published, so the gap is visible
    assert result["collapsed_reading_would_be"] == 6


def test_undecided_worlds_are_set_apart_and_named(injected):
    result = L._incompleteness(injected)
    apart = result["set_apart"]
    assert apart["total"] == 3
    assert apart["by_engine_status"] == {potential.BUDGET: 3}
    assert result["certified"] == 4
    assert result["accounted"] is True, (
        "numerator + certified + set_apart must exhaust the denominator, or a "
        "world has gone missing between the three buckets"
    )


def test_certificate_error_is_its_own_row_not_an_incompleteness():
    """Weights that failed exact re-checking are a fact about the LP, not the world."""
    rows = [row(0, reachable=False, certificate_issued=False, solver_status=None,
                engine_status="certificate_error", certificate_error=True)]
    result = L._incompleteness(rows)
    assert result["numerator"] == 0
    assert result["set_apart"]["certificate_error"] == 1


# ------------------------------------------------------- F2: the caliber count

def test_caliber_counts_the_old_rule_directly_instead_of_adding_a_delta(injected):
    """`old = new + extra` double-counted: the extras were already inside `new`."""
    caliber = L._caliber(injected, None)
    assert caliber["old_rule_numerator"] == 6, (
        "old rule = `not result.success` = status != 0, which is 3 status-2 "
        "worlds plus 3 status-1 worlds = 6. Reported %d, an overshoot of %d -- "
        "the status-1 worlds counted once in the new numerator and once again "
        "as `extra`." % (caliber["old_rule_numerator"],
                         caliber["old_rule_numerator"] - 6)
    )
    assert caliber["worlds_where_the_rules_differ"] == 3
    assert caliber["delta_numerator"] == 3
    assert caliber["old_rule_denominator"] == 10


def test_caliber_delta_is_zero_when_no_solve_was_undecided():
    """The real corpus: the two rules are different functions that happen to agree."""
    rows = [row(i, reachable=False, certificate_issued=True, solver_status=0,
                engine_status=potential.CERTIFIED) for i in range(4)]
    rows += [row(4 + i, reachable=False, certificate_issued=False, solver_status=2,
                 engine_status=potential.NO_LINEAR_PAGODA) for i in range(6)]
    caliber = L._caliber(rows, None)
    assert caliber["old_rule_numerator"] == caliber["old_rule_denominator"] - 4 == 6
    assert caliber["delta_numerator"] == 0
    assert caliber["worlds_where_the_rules_differ"] == 0


# --------------------------------------------- F3 / F4: the wider-box sweep

def _one_silent_row():
    """A real world, so `_wider_box` has a graph to hand to the patched solver."""
    seed = L.prng.derive(L.CAMPAIGN_SEED, L.FAMILY, 0)
    return [row(0, reachable=False, certificate_issued=False, solver_status=2,
                engine_status=potential.NO_LINEAR_PAGODA, seed=seed)]


def _outcome(status, solver_status, bound):
    return potential.LpOutcome(status=status, solver_status=solver_status,
                               solver_message="injected", bound=bound, margin=1)


def _patch_decide(monkeypatch, at_1e6):
    """`decide` says `no_linear_pagoda` at 100 and 10^4, and `at_1e6(bound)` at 10^6.

    Patching the solver rather than the world keeps the test at a millisecond
    and makes the injected outcome the only variable.
    """
    def fake_decide(graph, initial, **kw):
        if kw.get("bound") == 10 ** 6:
            return at_1e6(10 ** 6)
        return _outcome(potential.NO_LINEAR_PAGODA, 2, kw.get("bound"))

    monkeypatch.setattr(L.lp_potential, "decide", fake_decide)


def _raise_lp_unavailable(bound):
    raise potential.LpUnavailable(
        "injected: HiGHS hit its iteration limit",
        _outcome(potential.BUDGET, 1, bound))


def _raise_certificate_error(bound):
    raise potential.CertificateError("injected: weights failed exact re-checking")


def _return_budget(bound):
    return _outcome(potential.BUDGET, 1, bound)


@pytest.mark.parametrize("failure,label", [
    (_raise_lp_unavailable, "lp_unavailable"),
    (_raise_certificate_error, "certificate_error"),
    (_return_budget, potential.BUDGET),
])
def test_a_failed_solve_at_a_wider_bound_is_not_a_blocked_box(monkeypatch,
                                                              failure, label):
    """`lp.box_blocked` means "the box was refusing", which a failure never shows.

    `CertificateError` is the live one: `Fraction(float(v)).limit_denominator(1000)`
    on weights near 10^6 fails exact re-checking far more readily than at
    `|w| <= 10`, so this branch is reachable on real data in a way the others
    are not.
    """
    _patch_decide(monkeypatch, failure)
    rows = _one_silent_row()
    wider = L._wider_box(rows)

    assert wider["box_blocked"]["recomputed"] == 0, (
        "a %s at bound=10^6 was counted as a world the box was blocking" % label
    )
    assert wider["solve_failed"]["count"] == 1
    assert wider["solve_failed"]["worlds"][0]["failure"] == label
    # ... and therefore is not subtracted from lp.no_farkas
    assert L._no_farkas(rows, wider)["recomputed"] == 1, (
        "a solver failure was subtracted from lp.no_farkas, which counts worlds "
        "whose infeasibility rests on HiGHS -- a failed solve does not remove one"
    )
    # it does still stop the world being called "infeasible at all three"
    assert wider["still_infeasible_at_all_three"]["recomputed"] == 0


def test_a_genuine_certified_result_at_a_wider_bound_is_a_blocked_box(monkeypatch):
    """The positive control: only status 0 may enter `box_blocked`."""
    world = L.jumpgraph.generate(L.prng.derive(L.CAMPAIGN_SEED, L.FAMILY, 0))
    certificate = potential.Certificate(
        weights=[Fraction(0)] * world.spec.n_pos,
        initial=world.spec.initial,
        goal_states=list(world.spec.goal_states),
        moves=[], margin=Fraction(1),
    )

    def certified(bound):
        return potential.LpOutcome(
            status=potential.CERTIFIED, solver_status=0,
            solver_message="injected", bound=bound, margin=1,
            certificate=certificate)

    _patch_decide(monkeypatch, certified)
    rows = _one_silent_row()
    wider = L._wider_box(rows)
    assert wider["box_blocked"]["recomputed"] == 1
    assert wider["solve_failed"]["count"] == 0
    assert L._no_farkas(rows, wider)["recomputed"] == 0


def test_a_returned_undecided_status_is_visible_in_the_bounds_table(monkeypatch):
    """`decide` RETURNS budget/unbounded/numerical; it does not raise them.

    The summary field used to read one tally key named "undecided", which the
    raise path wrote and the return path did not -- so a returned `budget`
    landed in `status_counts` and the summary said 0.  An empty result reading
    as a pass.
    """
    _patch_decide(monkeypatch, _return_budget)
    wider = L._wider_box(_one_silent_row())
    table = wider["bounds"]["1000000"]

    assert table["status_counts"].get(potential.BUDGET) == 1
    assert table["undecided_returned"] == 1, (
        "status_counts saw the returned `budget` and the summary field did not"
    )
    assert table["solve_failed"] == 1
    assert table["still_infeasible"] == 0
    assert table["accounted"] is True, (
        "still_infeasible + feasible + undecided + raised + errors must equal "
        "the number probed, or an outcome fell between the buckets"
    )
    # the raise path has its own counter and does not collide with the return path
    assert table["lp_unavailable_raised"] == 0


def test_a_raised_lp_unavailable_is_counted_apart_from_a_returned_one(monkeypatch):
    _patch_decide(monkeypatch, _raise_lp_unavailable)
    table = L._wider_box(_one_silent_row())["bounds"]["1000000"]
    assert table["lp_unavailable_raised"] == 1
    assert table["undecided_returned"] == 0
    assert table["solve_failed"] == 1
    assert table["accounted"] is True


# --------------------------------------- F5: the set-identity claim is not made

def test_the_tautological_set_identity_check_is_gone(monkeypatch):
    """It returned True for the empty list and could not fail on real data."""
    _patch_decide(monkeypatch, _return_budget)
    rows = _one_silent_row()
    denominators = L._denominators(rows, L._wider_box(rows))

    assert "same_set_of_worlds" not in denominators, (
        "`same_set_of_worlds` was a subset test on the one-element box_blocked "
        "list -- true for the empty list, and guaranteed by construction "
        "otherwise, since _wider_box selects its silent set with the identical "
        "predicate. A field that cannot fail is not evidence."
    )
    identity = denominators["set_identity"]
    assert identity["checked_here"] is False
    assert "no world list" in identity["not_established"]
    assert len(identity["numerator_world_ids_sha256"]) == 64


# ---------------------------------------------- the exact rational upgrade

class _Spec:
    """The three fields `pagoda_system` reads."""

    def __init__(self, n_pos, triples, initial, goal_states):
        self.n_pos = n_pos
        self.triples = tuple(triples)
        self.initial = initial
        self.goal_states = tuple(goal_states)


def test_phase1_proves_infeasibility_with_a_checkable_farkas_vector():
    """One peg, one goal that needs the potential to rise: no pagoda can exist.

    Positions 0 and 1; the only move takes (0,1) -> 2 ... except there is no
    move at all here, so the single constraint is `pot(goal) - pot(init) >= 1`
    with `goal == init`, which is `0 >= 1`.  Infeasible, and the multiplier is
    the trivial one.
    """
    spec = _Spec(2, [], "10", ["10"])
    verdict = L.decide_exactly(spec)
    assert verdict["feasible"] is False
    assert verdict["verification"]["valid"] is True
    assert verdict["verification"]["multipliers_nonnegative"] is True
    assert verdict["verification"]["combination_is_zero"] is True
    assert verdict["verification"]["rhs_is_negative"] is True


def test_phase1_finds_a_pagoda_when_one_exists_and_it_re_checks_exactly():
    spec = _Spec(2, [], "10", ["01"])          # w_1 - w_0 >= 1, no move rows
    verdict = L.decide_exactly(spec)
    assert verdict["feasible"] is True
    assert verdict["exact_recheck_over_spec_triples"]["holds"] is True


def test_a_reachable_goal_admits_no_pagoda_and_the_proof_is_emitted():
    """Soundness. The move (0,1)->2 reaches the goal, so the potential would rise."""
    spec = _Spec(3, [(0, 1, 2)], "110", ["001"])
    verdict = L.decide_exactly(spec)
    assert verdict["feasible"] is False
    assert verdict["verification"]["valid"] is True
    # w_2 - w_0 - w_1 <= 0 and w_0 + w_1 - w_2 <= -1 sum to 0 <= -1
    assert verdict["farkas_multipliers"] == [1, 1]


def test_check_farkas_rejects_a_forged_certificate():
    """The verifier is the point; it has to be able to say no."""
    spec = _Spec(3, [(0, 1, 2)], "110", ["001"])
    matrix, rhs = L.pagoda_system(spec)
    assert L.check_farkas([1, 1], matrix, rhs)["valid"] is True
    assert L.check_farkas([1, 0], matrix, rhs)["valid"] is False    # rhs not < 0
    assert L.check_farkas([-1, -1], matrix, rhs)["valid"] is False  # not >= 0


def test_primitive_integers_normalises_the_ray():
    assert L.primitive_integers([Fraction(2, 3), Fraction(4, 3)]) == [1, 2]
    assert L.primitive_integers([Fraction(0), Fraction(5)]) == [0, 1]
