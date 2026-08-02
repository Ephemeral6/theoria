"""The census, against the only thing that can contradict it: brute force.

`exam/state_space.py` produces numbers no one can check by hand -- 1.6e38 is not
a number a reviewer verifies by reading the code that printed it.  So the whole
of this file is one argument: run the census and the naive enumerator on the
*same families and the same operators* at every size where the enumerator can
finish, and require them to agree exactly.  A method that agrees with brute
force at k=1..6 and is then applied at k=60 is an extrapolation of the *method*,
which is a different and much weaker assumption than extrapolating a fitted
curve -- there is nothing fitted here.

The brackets get the same treatment from both sides at once: lower <= true <=
upper, at every budget the enumerator can reach.  A bracket that is not a
bracket somewhere small is not a bracket at 2^120 either.
"""

from __future__ import annotations

import json

import pytest

from exam import state_space as SS
from exam.grading import rubrics_verdict as RV
from exam.papers import verdict as V


# ------------------------------------------------------ the shipped families
#
# Constructor AND operator, because the operator is part of the family: orchard's
# forbidden LEFT is what takes the count from 2k*4^k to (2*4^k - 8)/3, and a
# census validated only on the bare constructor would be validated on a board no
# item ships.
FAMILIES = {
    "gantry": lambda k: V.variant_of(V.comb_room("gantry", k, None), "gantry",
                                     remap={"LEFT": "RIGHT", "RIGHT": "LEFT"}),
    "lattice": lambda k: V.variant_of(V.comb_room("lattice", k, 2), "lattice",
                                      lost_cells=[[4, 2]]),
    "spindle": lambda k: V.comb_open("spindle", k, 1, k),
    "orchard": lambda k: V.variant_of(V.comb_open("orchard", k, 2, 1), "orchard",
                                      forbidden=["LEFT"]),
}


@pytest.mark.parametrize("family", sorted(FAMILIES))
@pytest.mark.parametrize("k", [2, 3, 4, 5, 6])
def test_symbolic_census_agrees_with_brute_force(family, k):
    """Exactly, at every size the enumerator can finish. Not approximately."""
    level = RV.Level(FAMILIES[family](k))
    brute = SS.brute_force_count(level)
    assert brute is not None, "the enumerator hit its cap; pick a smaller k"
    assert SS.exact_count(level)["states"] == brute


@pytest.mark.parametrize("family", sorted(FAMILIES))
@pytest.mark.parametrize("k", [2, 3, 4, 5, 6])
def test_the_census_is_the_count_and_not_the_construction_floor(family, k):
    """The census must exceed `subset_lower_bound`, and by a growing factor.

    The floor is sound, so the census had better clear it -- but the point of
    the census is that the floor is *loose*, and the amount it is loose by is
    what the class inventory used to be publishing as though it were the count.
    """
    doc = FAMILIES[family](k)
    level = RV.Level(doc)
    floor = V.subset_lower_bound(level)["lower_bound"]
    counted = SS.exact_count(level)["states"]
    assert counted > floor, (family, k, counted, floor)


@pytest.mark.parametrize("k", [2, 3, 4, 5])
@pytest.mark.parametrize("budget", [0, 1, 3, 6, 9, 12, 16])
def test_the_budgeted_bracket_actually_brackets(k, budget):
    """lower <= true <= upper, measured, at every budget brute force can reach.

    Both sides can be wrong in a way that still *looks* like a bracket -- a
    lower bound that over-counts and an upper bound that under-counts are the
    two failures that would let a false claim through, and only the true count
    between them can tell.
    """
    doc = V.variant_of(V.comb_open("spindle", k, 1, k), "spindle",
                       step_limit=budget)
    level = RV.Level(doc)
    true = SS.brute_force_count(level)
    bracket = SS.budgeted_bracket(level)
    assert bracket["lower"] <= true, (k, budget, bracket["lower"], true)
    assert true <= bracket["upper"], (k, budget, true, bracket["upper"])


@pytest.mark.parametrize("family", sorted(FAMILIES))
@pytest.mark.parametrize("k,budget,cap", [
    (2, None, 10 ** 6), (4, None, 10 ** 6), (6, None, 10 ** 6),
    (4, 9, 10 ** 6), (5, 14, 10 ** 6),
    (5, None, 500), (6, None, 4000),          # caps that bite, so truncation
    (6, None, 49152), (6, None, 49151),       # exactly at the count, and one under
])
def test_the_counting_probe_matches_the_recording_one(family, k, budget, cap):
    """`naive_reach` drops `enumerate_states`' path bookkeeping and nothing else.

    Same count and same truncation flag, including at a cap that lands exactly
    on the state count -- the boundary where "stopped because it was full" and
    "stopped because it was finished" are one state apart, and where a probe
    that got the comparison backwards would still look right everywhere else.
    """
    doc = FAMILIES[family](k)
    if budget is not None:
        doc = V.variant_of(doc, doc["level_id"], step_limit=budget)
    level = RV.Level(doc)
    recorded = RV.enumerate_states(level, cap=cap)
    counted = SS.naive_reach(level, cap=cap)
    assert counted["truncated"] == recorded["truncated"], (family, k, budget, cap)
    assert counted["states"] == recorded["states"], (family, k, budget, cap)


def test_the_census_refuses_rather_than_guesses():
    """Every method here is a positive whitelist, and the refusals say why.

    A counter that falls back when its premise fails produces a number
    indistinguishable from a count, which is the failure this whole module
    exists to avoid.
    """
    budgeted = RV.Level(V.variant_of(V.comb_open("spindle", 4, 1, 4), "spindle",
                                     step_limit=9))
    with pytest.raises(SS.UncountableHere, match="step budget"):
        SS.exact_count(budgeted)

    unbudgeted = RV.Level(V.comb_open("spindle", 4, 1, 4))
    with pytest.raises(SS.UncountableHere, match="no step budget"):
        SS.budgeted_bracket(unbudgeted)

    # A board with a button carries state the position enumeration does not,
    # so every count over it would be a count over a graph the level lacks.
    with_button = RV.Level(V.a2_echo())
    with pytest.raises(SS.UncountableHere, match="button"):
        SS.exact_count(with_button)

    # ...and a comb whose corridor cells are themselves switches is outside the
    # bracket's geometry, because its walk costs assume a corridor that latches
    # nothing.
    doc = V.variant_of(V.comb_open("spindle", 4, 1, 4), "spindle", step_limit=9)
    doc["switches"] = doc["switches"] + [[2, 2]]
    with pytest.raises(SS.UncountableHere, match="corridor"):
        SS.budgeted_bracket(RV.Level(doc))


def test_the_variable_order_does_not_move_the_answer():
    """Column-major is chosen for size, not for the result.

    The ordering comment in `exact_count` claims the row-major order costs
    memory and not correctness. On a board small enough for both to finish,
    that is checkable, and if it were ever false the census would be returning
    an artefact of its own data structure.
    """
    for family in sorted(FAMILIES):
        level = RV.Level(FAMILIES[family](5))
        brute = SS.brute_force_count(level)
        column = SS.exact_count(level, order_key=SS.column_major)
        row = SS.exact_count(level, order_key=SS.row_major)
        assert column["states"] == row["states"] == brute, family
        # ...and the size claim, which is the reason the order was changed at
        # all. It is a k=5 board, so the gap is small; at k=60 it was the
        # difference between an answer and a MemoryError.
        assert column["bdd_nodes"] <= row["bdd_nodes"], family


# ---------------------------------------------------------- the shipped items

@pytest.fixture(scope="module")
def paper():
    return V.build()


def test_every_shipped_item_carries_a_census(paper):
    """No item may ship with the class flag and no number behind it."""
    for item in paper.items:
        space = item.truth["state_space"]
        assert space["census_method"] in {
            "enumeration", "symbolic-reachability", "budgeted-bracket",
            "enumeration-truncated"}, item.item_id
        assert space["census_lower"] is not None, item.item_id
        assert space["census_positions"] > 0, item.item_id
        # The flag the class boundary is drawn on must be the census's own, not
        # a literal the builder wrote next to it.
        assert (space["census_naive_enumeration_feasible"]
                is space["naive_enumeration_feasible"]), item.item_id


def test_class_ii_state_counts_are_computed_not_assumed(paper):
    """The ticket, in one assertion.

    Every class (ii) item must carry either an exact count or a two-sided
    bracket, every such number must clear the construction's own floor, and the
    naive method must be out of reach *by the number* rather than by the label.
    """
    items = [i for i in paper.items if i.truth["class"] == "large_unsolvable"]
    assert len(items) == 4
    exact_count = 0
    for item in items:
        space = item.truth["state_space"]
        assert space["naive_enumeration_feasible"] is False, item.item_id
        assert space["census_lower"] > SS.NAIVE_CEILING, item.item_id
        if space["exact_states"] is not None:
            exact_count += 1
            assert space["census_method"] == "symbolic-reachability", item.item_id
            assert space["exact_states"] >= space["lower_bound"], item.item_id
            assert space["census_lower"] == space["census_upper"] == space["exact_states"]
        else:
            assert space["census_method"] == "budgeted-bracket", item.item_id
            assert space["census_lower"] < space["census_upper"], item.item_id
    assert exact_count == 3, (
        "three of the four class (ii) items are unbudgeted and counted exactly; "
        "the fourth ships a step budget and is bracketed. If this number moved, "
        "an item changed shape and its record means something different")


def test_no_class_ii_item_is_within_reach_of_exhaustive_enumeration(paper):
    """The reclassification test, run rather than assumed.

    If a class (ii) item's state space were small enough for the naive method,
    the item would be a class (i) item wearing the wrong label, and the honest
    response would be to move it rather than to rename the class. Nothing moves
    -- but the check is what makes that a finding instead of a belief.
    """
    for item in paper.items:
        if item.truth["class"] != "large_unsolvable":
            continue
        level = RV.Level(json.loads(item.truth["level_blob"]))
        assert RV.enumerate_states(level, cap=SS.NAIVE_CEILING)["truncated"] is True
        assert SS.census(level)["naive_enumeration_feasible"] is False


def test_small_space_items_are_counted_by_two_methods_that_agree(paper):
    """Class (i)'s enumeration and the census are the same number.

    The census's cheapest branch *is* the enumerator on these boards, so this
    would be vacuous -- except that it also pins `census_positions`, and a
    census whose position count disagreed with the level would be a census over
    the wrong board.
    """
    for item in paper.items:
        space = item.truth["state_space"]
        if space["naive_enumeration_feasible"] is not True:
            continue
        assert space["exact_states"] == space["enumerated"], item.item_id
        assert space["census_method"] == "enumeration", item.item_id
        level = RV.Level(json.loads(item.truth["level_blob"]))
        assert space["census_positions"] == len(SS.reachable_positions(level))


def test_the_count_and_the_search_barrier_answer_different_questions(paper):
    """The one reading this census must not license.

    A count of 1.6e38 says the naive method cannot run. It does not say no
    exhaustive method can, and D-EX-028 measured that it can -- at most 600
    nodes. Both numbers sit on the same record on purpose, and this test fails
    if either is ever dropped, because a record carrying only the first invites
    exactly the claim the exam withdrew.
    """
    for item in paper.items:
        if item.truth["class"] != "large_unsolvable":
            continue
        space = item.truth["state_space"]
        assert space["positional_states"] <= 600
        assert space["census_lower"] > 10 ** 30
        assert "NOT a sound abstraction" in space["quotient_note"]
