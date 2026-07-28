"""Tests for the oracles, because the oracles have already been wrong twice.

A property battery's most likely output is a **false accusation**. This one
produced two before it produced anything else:

* `probe_frontier` was reported to violate `entropy_matches_bruteforce` on 120
  of 120 worlds. The engine was right every time; the oracle was summing class
  *sizes* where the engine sums `Hypothesis.weight`, and `hypset` draws
  non-uniform weights;
* `fd_adapter` was reported to return 13 plans that "do not execute". The engine
  was right; the oracle keyed its action table on `GroundAction.text`, which is a
  bound method rather than a property, so it recognised no action at all.

Both were caught by looking at the first finding before filing it. Neither would
have been caught by the campaign, which cannot tell a real violation from an
oracle bug — that is what this file is for. Every value below is either computed
by hand or is a closed form.
"""

import math

import pytest

from fuzzlab.oracles import gf2, search


# ------------------------------------------------------------------- entropy

@pytest.mark.parametrize("weights,expected", [
    ([], 0.0),
    ([4], 0.0),
    ([1, 1], 1.0),
    ([1, 1, 1, 1], 2.0),
    ([1, 1, 1], math.log2(3)),
    ([2, 1], 0.9182958340544896),
    ([3, 1], 0.8112781244591328),
    ([2.0, 1.0, 1.0], 1.5),
])
def test_partition_entropy_matches_the_closed_form(weights, expected):
    assert search.partition_entropy(weights) == pytest.approx(expected, abs=1e-12)


def test_partition_entropy_is_weight_based_not_count_based():
    """The distinction that produced the battery's first false accusation.

    Three classes of sizes 1/1/1 but weights 2/1/1 are 1.5 bits, not log2(3).
    """
    assert search.partition_entropy([1, 1, 1]) == pytest.approx(math.log2(3))
    assert search.partition_entropy([2, 1, 1]) == pytest.approx(1.5)
    assert search.partition_entropy([2, 1, 1]) != pytest.approx(math.log2(3))


def test_non_positive_weights_are_skipped_not_counted():
    assert search.partition_entropy([1, 1, 0]) == pytest.approx(1.0)
    assert search.partition_entropy([0, 0]) == 0.0


# ----------------------------------------------------------------------- gf2

def test_null_space_of_an_empty_system_is_everything():
    basis = gf2.null_space([], 3)
    assert len(basis) == 3
    assert gf2.same_span(basis, [1, 2, 4], 3)


def test_null_space_is_orthogonal_to_every_row():
    rows = [0b011, 0b110]                      # x0+x1 = 0, x1+x2 = 0
    basis = gf2.null_space(rows, 3)
    assert len(basis) == 1                     # rank 2, nullity 1
    for vector in basis:
        for row in rows:
            assert bin(vector & row).count("1") % 2 == 0
    assert basis == [0b111]                    # the all-ones vector


def test_full_rank_system_has_only_the_zero_solution():
    assert gf2.null_space([0b001, 0b010, 0b100], 3) == []


def test_in_span_and_same_span_distinguish_equal_dimension_subspaces():
    """Dimension alone is not enough, which is why `same_span` compares RREF."""
    a = [0b001, 0b010]
    b = [0b001, 0b100]
    assert not gf2.same_span(a, b, 3)
    assert gf2.in_span(0b011, a, 3)
    assert not gf2.in_span(0b100, a, 3)


def test_conserved_laws_finds_a_planted_invariant():
    """Two cells that always swap: total parity per colour is conserved."""
    states = [["R", "B"], ["B", "R"], ["R", "B"], ["B", "R"]]
    basis, n_cols = gf2.conserved_laws(states, ["B", "R"])
    assert n_cols == 4
    for law in basis:
        assert gf2.holds_on(law, states, ["B", "R"])


def test_holds_on_rejects_a_law_that_does_not_hold():
    states = [["R", "R"], ["R", "B"]]
    index = gf2.feature_index(2, ["B", "R"])
    only_cell_one_is_b = 1 << index[(1, "B")]
    assert not gf2.holds_on(only_cell_one_is_b, states, ["B", "R"])


# -------------------------------------------------------------- plan replay

def _actions(**spec):
    out = {}
    for name, (pre_pos, pre_neg, add, dele) in spec.items():
        out[name] = {"pre_pos": set(pre_pos), "pre_neg": set(pre_neg),
                     "add": set(add), "del": set(dele)}
    return out


def test_validate_plan_accepts_a_plan_that_reaches_the_goal():
    actions = _actions(go=(["at_a"], [], ["at_b"], ["at_a"]))
    ok, why = search.validate_plan({"at_a"}, ({"at_b"}, set()), actions, ["go"])
    assert ok, why


def test_validate_plan_rejects_an_unmet_precondition():
    actions = _actions(go=(["at_a"], [], ["at_b"], ["at_a"]))
    ok, why = search.validate_plan({"at_c"}, ({"at_b"}, set()), actions, ["go"])
    assert not ok and "preconditions unmet" in why


def test_validate_plan_honours_negative_preconditions():
    """Dropping these would make the validator accept plans the world rejects.

    That is the one direction a validator must never be wrong in, so it gets its
    own test rather than riding on the positive case.
    """
    actions = _actions(go=([], ["locked"], ["at_b"], []))
    ok, _why = search.validate_plan(set(), ({"at_b"}, set()), actions, ["go"])
    assert ok
    ok, why = search.validate_plan({"locked"}, ({"at_b"}, set()), actions, ["go"])
    assert not ok and "negative preconditions" in why


def test_validate_plan_honours_a_negative_goal():
    actions = _actions(go=([], [], ["at_b"], []))
    ok, why = search.validate_plan(set(), ({"at_b"}, {"at_b"}), actions, ["go"])
    assert not ok and "negative goal" in why


def test_validate_plan_rejects_an_unknown_action():
    ok, why = search.validate_plan(set(), (set(), set()), {}, ["nope"])
    assert not ok and "no such action" in why


# ------------------------------------------------------------------- search

def test_optimal_plan_length_counts_the_shortest_route():
    actions = _actions(
        ab=(["a"], [], ["b"], ["a"]),
        bc=(["b"], [], ["c"], ["b"]),
        ac=(["a"], [], ["c"], ["a"]),
    )
    length, exhausted = search.optimal_plan_length({"a"}, ({"c"}, set()), actions)
    assert (length, exhausted) == (1, True)


def test_optimal_plan_length_reports_zero_when_the_goal_already_holds():
    assert search.optimal_plan_length({"c"}, ({"c"}, set()), {}) == (0, True)


def test_optimal_plan_length_proves_unsolvability_by_exhaustion():
    """`(None, True)` is a proof; `(None, False)` is a timeout.  They differ."""
    actions = _actions(ab=(["a"], [], ["b"], ["a"]))
    length, exhausted = search.optimal_plan_length({"a"}, ({"z"}, set()), actions)
    assert length is None and exhausted is True


def test_optimal_plan_length_reports_a_budget_stop_as_not_exhausted():
    actions = _actions(**{
        "grow%d" % i: ([], [], ["p%d" % i], []) for i in range(12)
    })
    length, exhausted = search.optimal_plan_length(set(), ({"zz"}, set()), actions,
                                                   budget=8)
    assert length is None and exhausted is False


def test_distance_to_any_separates_unreachable_from_over_budget():
    graph = {"a": ["b"], "b": ["a"]}
    step = lambda s: graph.get(s, ())          # noqa: E731
    assert search.distance_to_any("a", step, {"a"}) == (0, True)
    assert search.distance_to_any("a", step, {"b"}) == (1, True)
    assert search.distance_to_any("a", step, {"z"}) == (None, True)
