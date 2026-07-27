"""ic3_pdr: the fallback invariant engine, on the case that needs a fallback.

The headline is one line of Fixture C: configuration **0111** is unsolvable and
no linear pagoda proves it (D-014 says so, as a test).  IC3 proves it anyway,
and the invariant it returns is re-checked by code that shares nothing with the
search.

Everything here also has to hold in the other direction -- a method that returns
an invariant for a *solvable* configuration would be worthless -- so 1101 is
tested for a counterexample, not merely for "no invariant".
"""

import pytest

from common.jsonio import read_json, read_jsonl
from engines import ic3_pdr, lp_potential
from engines.ic3_pdr import check as ic3_check
from engines.ic3_pdr.system import satisfies_all
from fixtures import peg4
from tools.validate_candidates import validate_file


@pytest.fixture(scope="module")
def graph():
    return read_json(peg4.GRAPH_PATH)


def system_for(graph, config):
    return ic3_pdr.peg_system(graph, config)


# ------------------------------------------------------- the acceptance line

def test_the_lp_really_has_nothing_to_say_about_0111(graph):
    """The premise of this whole engine, restated where it is being relied on."""
    assert graph["solvable"]["0111"] is False
    assert lp_potential.solve_certificate(graph, "0111") is None


def test_ic3_proves_0111_unsolvable_where_the_lp_cannot(graph):
    system = system_for(graph, "0111")
    verdict, check = ic3_pdr.run(system)

    assert isinstance(verdict, ic3_pdr.Invariant)
    assert check.conditions == {"inv_init": True, "inv_closed": True, "goal_break": True}
    assert check.witnesses == {}


def test_the_0111_invariant_is_the_one_it_looks_like(graph):
    """Pinned, because a silently weakened invariant still passes the checker.

    In words: positions 1 and 2 always hold the same thing.  Which is true and
    not obvious -- and is not a potential function, which is why the LP could
    not reach it.
    """
    system = system_for(graph, "0111")
    verdict, _ = ic3_pdr.run(system)
    assert system.render_cnf(verdict.clauses) == "(!pos1 | pos2) & (pos1 | !pos2)"

    inside = {
        system.render_state(s) for s in system.states if satisfies_all(s, verdict.clauses)
    }
    assert inside == {"0000", "0001", "0110", "0111", "1000", "1001", "1110", "1111"}


def test_the_converged_frame_is_reduced_before_it_is_emitted(graph):
    """IC3 converges on a frame with a redundant clause; the engine drops it."""
    system = system_for(graph, "0111")
    verdict, _ = ic3_pdr.run(system)
    assert verdict.clauses_dropped == 1
    assert ic3_pdr.is_inductive(system, verdict.clauses)


def test_every_clause_that_survives_minimisation_is_load_bearing(graph):
    """Minimal means minimal: remove any one clause and the invariant fails."""
    for config in ("1110", "0111", "1011"):
        system = system_for(graph, config)
        verdict, _ = ic3_pdr.run(system)
        for clause in verdict.clauses:
            without = [c for c in verdict.clauses if c != clause]
            assert not ic3_check.verify(system, without).holds


def test_the_invariant_contains_every_reachable_state(graph):
    """Soundness from the other side: over-approximating means over-approximating."""
    for config in peg4.INITIAL_CONFIGS:
        if graph["solvable"][config]:
            continue
        system = system_for(graph, config)
        verdict, _ = ic3_pdr.run(system)
        inside = {
            system.render_state(s)
            for s in system.states
            if satisfies_all(s, verdict.clauses)
        }
        assert set(graph["reachable"][config]) <= inside


@pytest.mark.parametrize("config", ["1110", "0111", "1011"])
def test_every_unsolvable_configuration_gets_an_invariant(graph, config):
    assert graph["solvable"][config] is False
    verdict, check = ic3_pdr.run(system_for(graph, config))
    assert isinstance(verdict, ic3_pdr.Invariant)
    assert check.holds


def test_the_solvable_configuration_gets_a_counterexample_not_an_invariant(graph):
    system = system_for(graph, "1101")
    verdict, replayed = ic3_pdr.run(system)

    assert isinstance(verdict, ic3_pdr.Counterexample)
    assert replayed is True
    assert verdict.length == peg4.distance_to_goal("1101") == 2
    assert [system.render_state(s) for s in verdict.states] == ["1101", "0011", "0100"]


def test_ic3_and_the_lp_never_disagree(graph):
    """Two engines, two invariant shapes, one fact. IC3 is strictly the wider net."""
    for config in peg4.INITIAL_CONFIGS:
        verdict, _ = ic3_pdr.run(system_for(graph, config))
        proved = isinstance(verdict, ic3_pdr.Invariant)
        assert proved is (not graph["solvable"][config])
        if lp_potential.solve_certificate(graph, config) is not None:
            assert proved


# --------------------------------------------------- the independent checker

def test_the_checker_refuses_an_invariant_with_a_clause_removed(graph):
    system = system_for(graph, "0111")
    verdict, _ = ic3_pdr.run(system)
    result = ic3_check.verify(system, verdict.clauses[1:])
    assert not result.holds
    assert result.witnesses


def test_the_checker_refuses_an_invariant_that_excludes_the_start(graph):
    system = system_for(graph, "0111")
    result = ic3_check.verify(system, [frozenset({(3, False)})])
    assert result.conditions["inv_init"] is False
    assert result.witnesses["inv_init"] == ["0111"]


def test_the_checker_refuses_an_invariant_that_lets_the_goal_in(graph):
    """The empty CNF is true everywhere: closed, holds at the start, useless."""
    system = system_for(graph, "0111")
    result = ic3_check.verify(system, [])
    assert result.conditions["inv_init"] is True
    assert result.conditions["inv_closed"] is True
    assert result.conditions["goal_break"] is False


def test_the_checker_refuses_a_counterexample_that_does_not_replay(graph):
    system = system_for(graph, "1101")
    verdict, _ = ic3_pdr.run(system)
    assert ic3_check.replay(system, verdict.states, verdict.moves)
    assert not ic3_check.replay(system, verdict.states, ("jump(9,9,9)",) * len(verdict.moves))
    assert not ic3_check.replay(system, verdict.states[1:], verdict.moves)


def test_run_raises_rather_than_emitting_an_unverified_invariant(graph, monkeypatch):
    system = system_for(graph, "0111")
    monkeypatch.setattr(
        ic3_pdr, "verify",
        lambda s, c: ic3_check.CheckResult({"inv_init": False}, {"inv_init": ["x"]}, 16, 0),
    )
    with pytest.raises(ic3_pdr.Ic3Error):
        ic3_pdr.run(system)


# ------------------------------------------------------ determinism, emission

def test_two_runs_produce_the_same_invariant(graph):
    first, _ = ic3_pdr.run(system_for(graph, "1011"))
    second, _ = ic3_pdr.run(system_for(graph, "1011"))
    assert first.clauses == second.clauses
    assert first.level == second.level


def test_the_emitted_stream_satisfies_the_frozen_schema(graph, tmp_path):
    out = str(tmp_path / "candidates.jsonl")
    ic3_pdr.run(system_for(graph, "0111"), out_path=out, timestamp="2026-07-27T00:00:00Z")
    ic3_pdr.run(system_for(graph, "1101"), out_path=out, timestamp="2026-07-27T00:00:00Z")

    assert validate_file(out) == []
    rows = read_jsonl(out)
    assert [row["kind"] for row in rows] == ["invariant", "plan"]
    assert all(row["engine"] == "lp_potential" for row in rows)
    assert all(row["payload"]["producer"] == "ic3_pdr" for row in rows)

    invariant = rows[0]["payload"]
    assert invariant["form"] == "inductive_invariant"
    assert invariant["conditions"] == {
        "inv_init": True, "inv_closed": True, "goal_break": True,
    }
    assert rows[1]["payload"]["form"] == "counterexample_path"
    assert rows[1]["payload"]["replayed"] is True
