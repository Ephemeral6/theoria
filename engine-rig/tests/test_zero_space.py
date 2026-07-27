"""M4 acceptance: the GF(2) null space recovers (#Red) mod 2, up to equivalence."""

import pytest

from common.jsonio import read_json, read_jsonl
from engines import zero_space
from engines.zero_space import gf2
from fixtures import pair_flip
from tools.validate_candidates import validate_rows


@pytest.fixture(scope="module")
def analysed():
    rows = read_jsonl(pair_flip.TRAJ_PATH)
    truth = read_json(pair_flip.TRUTH_PATH)
    states = [row["state"] for row in rows]
    return zero_space.analyse(states, ["R", "B"]), states, truth


def _red_parity(result):
    return zero_space.red_parity_vector(result.features, "R")


def _blue_parity(result):
    return zero_space.red_parity_vector(result.features, "B")


# ------------------------------------------------------------- the recovery

def test_difference_space_and_null_space_have_the_expected_dimensions(analysed):
    result, _, _ = analysed
    assert result.n_features == 16                 # 8 cells x 2 colours
    assert result.difference_rank == 7             # the 7 adjacent pairs
    assert result.dimension == 16 - 7 == 9


def test_red_parity_is_recovered(analysed):
    result, _, _ = analysed
    assert result.contains(_red_parity(result))


def test_recovered_space_is_exactly_red_parity_plus_the_encoding_laws(analysed):
    """The equivalence check: nothing missing, nothing extra claimed."""
    result, _, _ = analysed
    assert zero_space.equivalent_modulo_encoding(result, _red_parity(result))


def test_exactly_one_law_says_something_about_the_world(analysed):
    result, _, truth = analysed
    assert len(result.cell_local_laws()) == 8
    globals_ = result.global_laws()
    assert len(globals_) == 1
    assert globals_[0].value == truth["red_parity"]
    assert globals_[0].rendering() == "(#R) mod 2 = %d" % truth["red_parity"]


# ---------------------------------------------- equivalence, not string match

def test_blue_parity_is_the_same_law_expressed_differently(analysed):
    """(#Blue) mod 2 is a different vector and an equivalent law; both must pass."""
    result, _, _ = analysed
    red, blue = _red_parity(result), _blue_parity(result)
    assert red != blue
    assert result.contains(blue)
    assert zero_space.equivalent_modulo_encoding(result, blue)


def test_any_representative_of_the_global_coset_is_accepted(analysed):
    """Add encoding laws to the recovered law: still the same law."""
    result, _, _ = analysed
    red = _red_parity(result)
    for local in zero_space.cell_local_subspace(result.features):
        shifted = red ^ local
        assert result.contains(shifted)
        assert zero_space.equivalent_modulo_encoding(result, shifted)


def test_an_unrelated_vector_is_not_accepted_as_the_law(analysed):
    """The equivalence check must be able to say no."""
    result, _, _ = analysed
    single_cell_red = 1 << result.features.index(zero_space.Feature(0, "R"))
    assert not result.contains(single_cell_red)
    assert not zero_space.equivalent_modulo_encoding(result, single_cell_red)


# --------------------------------------------------------------- soundness

def test_every_reported_law_is_constant_along_the_trajectory(analysed):
    result, states, _ = analysed
    assert zero_space.verify(result, states)


def test_laws_are_re_checked_independently_of_the_elimination(analysed):
    result, states, _ = analysed
    encoded = [zero_space.encode(s, result.features) for s in states]
    for law in result.laws:
        values = {gf2.dot(law.vector, x) for x in encoded}
        assert values == {law.value}, law.rendering()


def test_parity_is_not_recovered_from_a_world_that_breaks_it():
    """A single-cell flip destroys red parity; the engine must not report it."""
    states = [["R", "B", "R", "B"]]
    for _ in range(6):
        current = list(states[-1])
        current[0] = "B" if current[0] == "R" else "R"
        states.append(current)
    result = zero_space.analyse(states, ["R", "B"])
    assert not result.contains(_red_parity(result))
    assert zero_space.verify(result, states)


def test_a_world_with_no_actions_at_all_yields_every_law():
    """Degenerate but honest: no differences, so nothing is ruled out."""
    states = [["R", "B"], ["R", "B"]]
    result = zero_space.analyse(states, ["R", "B"])
    assert result.difference_rank == 0
    assert result.dimension == 4


# ------------------------------------------------------------ GF(2) toolkit

def test_null_space_is_orthogonal_to_every_row():
    rows = [0b1011, 0b0110, 0b1101]
    basis = gf2.null_space(rows, 4)
    for vector in basis:
        for row in rows:
            assert gf2.dot(row, vector) == 0
    assert len(basis) == 4 - gf2.rank(rows)


def test_rank_and_span_equality():
    assert gf2.rank([0b110, 0b011, 0b101]) == 2      # third is the sum of the first two
    assert gf2.span_equal([0b110, 0b011], [0b011, 0b101])
    assert not gf2.span_equal([0b110], [0b011])


def test_in_span_and_reduce_modulo():
    basis = [0b0011, 0b1100]
    assert gf2.in_span(0b1111, basis)
    assert not gf2.in_span(0b0001, basis)
    assert gf2.reduce_modulo(0b1111, basis) == 0


# ------------------------------------------------------- contract compliance

def test_candidates_satisfy_the_frozen_schema(analysed):
    result, _, truth = analysed
    rows = zero_space.candidates(result, timestamp="2026-07-27T00:00:00Z")
    assert validate_rows(rows) == []
    assert len(rows) == 9
    assert all(row["kind"] == "invariant" for row in rows)
    assert all(row["engine"] == "zero_space" for row in rows)
    assert all(row["evidence"]["coverage"] == "40/40" for row in rows)
    global_rows = [r for r in rows if r["payload"]["scope"] == "global"]
    assert len(global_rows) == 1
    payload = global_rows[0]["payload"]
    assert payload["form"] == "gf2_linear"
    assert payload["modulus"] == 2
    assert payload["value"] == truth["red_parity"]
    assert sorted(payload["support"]) == sorted("R@%d" % i for i in range(8))
