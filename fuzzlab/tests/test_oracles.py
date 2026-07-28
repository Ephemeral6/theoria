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

from fuzzlab import campaign, prng
from fuzzlab.oracles import gf2, motion, search
from fuzzlab.worlds import gridworld


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


# --------------------------------------------------------------------- motion
#
# `oracles/motion.py` is the truth source for `cegis_miner`'s `effect.*`, so it
# is the one place a bug would turn a correct engine into a filed defect. Every
# case below is a hand-built frame pair with the answer written out.

def _grid(rows):
    return [list(r) for r in rows]


def test_motion_reads_a_unit_step():
    a = _grid([[0, 0, 0], [0, 5, 0], [0, 0, 0]])
    b = _grid([[0, 0, 0], [0, 0, 5], [0, 0, 0]])
    m = motion.read_motion(a, b, (1, 1), 5, 0)
    assert (m.type, m.delta, m.to, m.frm) == ("move", (0, 1), (1, 2), (1, 1))


def test_motion_reads_no_change_as_none():
    a = _grid([[0, 5], [0, 0]])
    assert motion.read_motion(a, _grid([[0, 5], [0, 0]]), (1, 1), 5, 0).type == "none"


def test_motion_handles_an_overlapping_step_of_a_tall_mover():
    """The vacated and entered strips do not touch the displacement directly.

    A 2x1 mover stepping down vacates its top row and enters the row below its
    bottom -- two cells two apart -- so any oracle that read the displacement off
    the diff's corners would answer (2, 0) here. The right answer is (1, 0).
    """
    a = _grid([[7, 0], [7, 0], [0, 0]])
    b = _grid([[0, 0], [7, 0], [7, 0]])
    m = motion.read_motion(a, b, (2, 1), 7, 0)
    assert (m.type, m.delta) == ("move", (1, 0))


def test_motion_reads_a_teleport_with_disjoint_before_and_after():
    a = _grid([[3, 0, 0], [0, 0, 0], [0, 0, 0]])
    b = _grid([[0, 0, 0], [0, 0, 0], [0, 0, 3]])
    m = motion.read_motion(a, b, (1, 1), 3, 0)
    assert (m.type, m.delta, m.to) == ("move", (2, 2), (2, 2))


def test_motion_is_not_fooled_by_a_same_coloured_neighbour():
    """A static obstacle of the mover's colour sits where a wrong reading lands.

    The 1x2 mover at (0,0) steps right to (0,1); an obstacle of the same colour
    occupies (0,3). Two anchors of a 1x2 all-colour block cover the entered
    cell, so the candidate set is genuinely ambiguous and only the exact replay
    against frame `b` discards the wrong one.
    """
    a = _grid([[4, 4, 0, 4], [0, 0, 0, 0]])
    b = _grid([[0, 4, 4, 4], [0, 0, 0, 0]])
    m = motion.read_motion(a, b, (1, 2), 4, 0)
    assert (m.type, m.delta) == ("move", (0, 1))


def test_motion_refuses_a_diff_no_rigid_translation_explains():
    """Two objects move at once: the oracle must say so, not pick one."""
    a = _grid([[6, 0, 0], [6, 0, 0]])
    b = _grid([[0, 6, 0], [0, 0, 6]])
    with pytest.raises(motion.Unreadable):
        motion.read_motion(a, b, (1, 1), 6, 0)


def test_motion_refuses_a_recolour():
    """A changed cell that is neither mover->background nor background->mover."""
    a = _grid([[2, 0], [0, 0]])
    b = _grid([[2, 9], [0, 0]])
    with pytest.raises(motion.Unreadable):
        motion.read_motion(a, b, (1, 1), 2, 0)


#: The end-to-end sweep's width. `MUTATION.md` quotes a transition count taken
#: from this constant, and an adversarial review caught the previous version of
#: that sentence citing "4455 transitions over 200 worlds" when the shipped test
#: swept five. The measurement had really been made -- but only in a scratch
#: script, so the repository could not reproduce the number it published. The
#: sweep is the test now, and the number is whatever this constant produces.
SWEEP_WORLDS = 200


def test_motion_agrees_with_the_generator_across_the_corpus():
    """The oracle against the world's own transition function, in bulk.

    The per-world case below is the readable one; this is the one whose number
    is quotable. It is the check that would have caught a silently wrong oracle
    before it filed 21 false accusations, so it sweeps a corpus rather than a
    handful of indices, and it reports the transition count so a report citing
    it can be checked against a run.
    """
    checked = 0
    for index in range(SWEEP_WORLDS):
        world = gridworld.generate(
            prng.derive(campaign.DEFAULT_SEED, "gridworld", index))
        read = motion.motions(world)
        assert not motion.unreadable_reasons(world), index
        for t in range(len(world.action_list)):
            want = (world.anchors[t + 1][0] - world.anchors[t][0],
                    world.anchors[t + 1][1] - world.anchors[t][1])
            got = read[t]
            if want == (0, 0):
                assert got.type == "none", (index, t, got)
            else:
                assert (got.type, got.delta, got.to) ==                     ("move", want, tuple(world.anchors[t + 1])), (index, t, got)
            checked += 1
    # Pinned so the figure quoted in MUTATION.md cannot drift away from the
    # code that produces it without a test failing.
    assert checked == 4455, checked


@pytest.mark.parametrize("index", [0, 3, 11, 29, 57])
def test_motion_agrees_with_the_generator_on_whole_gridworlds(index):
    """The oracle against the world's own transition function, end to end.

    `gridworld.Rules.step` is "the world's transition function, standing alone
    from any engine" and `world.anchors` is its record. The oracle never reads
    either -- it works from the rendered pixels -- so agreement across a whole
    trajectory is an independent confirmation, and it is the check that would
    catch a silently wrong oracle before it filed 21 false accusations.
    """
    world = gridworld.generate(prng.derive(campaign.DEFAULT_SEED, "gridworld", index))
    read = motion.motions(world)
    assert not motion.unreadable_reasons(world)
    for t in range(len(world.action_list)):
        want = (world.anchors[t + 1][0] - world.anchors[t][0],
                world.anchors[t + 1][1] - world.anchors[t][1])
        got = read[t]
        if want == (0, 0):
            assert got.type == "none", (index, t, got)
        else:
            assert (got.type, got.delta, got.to) == \
                ("move", want, tuple(world.anchors[t + 1])), (index, t, got)


def test_mover_anchors_reconstructs_the_whole_trajectory():
    world = gridworld.generate(prng.derive(campaign.DEFAULT_SEED, "gridworld", 3))
    anchors = motion.mover_anchors(world)
    assert anchors is not None
    assert anchors == [tuple(a) for a in world.anchors[:len(anchors)]]
