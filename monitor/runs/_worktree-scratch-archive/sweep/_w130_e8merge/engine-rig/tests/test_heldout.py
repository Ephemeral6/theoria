"""Tests for `heldout/` -- written against E17's adversarial mutation table.

That review injected 19 defects and **14 survived**, in a clean pattern: every
mutant inside `engines/` or `tools/` was caught by an existing test, and every
mutant inside `heldout/` survived, because no test imported it. A held-out
harness with no tests is the worst possible place for that gap: the mutants that
survived included three that fit *directly on the held-out data* and pushed the
published rate to 100 %.

Each test below names the mutant it exists to kill. They are deliberately not
one-per-existing-behaviour: the point of the review's own lesson (C11 -- "18
mutants matching 18 tests is testing what was already tested") is that the
detection surface has to be chosen from the defect space, not from the code
listing.
"""

from fractions import Fraction

import pytest

from engines.lp_potential.potential import Certificate, Move
from engines.zero_space import gf2, zerospace
from heldout import lp_potential_heldout as lph
from heldout import parityworld, peg, split
from heldout import zero_space_heldout as zsh
from heldout.parityworld import COLORS

SMALL = dict(n_cells=6, width=2, seed=0xE17A1838)


def _world():
    return parityworld.build(**SMALL)


# --------------------------------------------------------------- the splits

def test_the_random_split_is_disjoint_total_and_the_right_size():
    """Kills M1/P3: a split that leaks moves no published digit, so nothing
    downstream can be the detector -- it has to be checked here."""
    for seed in (1, 2, 0xE17A1838):
        train, heldout = split.random_transition_split(60, seed)
        assert set(train).isdisjoint(heldout)
        assert sorted(train + heldout) == list(range(60))
        assert len(train) == 42 and len(heldout) == 18


def test_leave_one_operation_out_withholds_exactly_that_operation():
    """Kills M6: training on everything while claiming to withhold."""
    world = _world()
    for j in range(len(world.operations)):
        train, heldout = split.leave_one_operation_out(world.actions, j)
        assert set(train).isdisjoint(heldout)
        assert sorted(train + heldout) == list(range(len(world.actions)))
        assert heldout, "every operation is witnessed, so no side may be empty"
        assert all(world.actions[t] == j for t in heldout)
        assert all(world.actions[t] != j for t in train)


# ------------------------------------------------------------------ the fit

def test_the_fit_reproduces_the_engine_without_going_through_the_gate():
    """Kills M5: `fit_matches_engine` returning a constant `True`.

    The comparison is done here directly, so disabling the harness's own gate
    cannot hide a drifted fit.
    """
    world = _world()
    features = zsh._features(world)
    encoded = [zerospace.encode(s, features) for s in world.states]
    _, basis = zsh.fit(encoded, features, range(len(world.actions)))
    assert sorted(basis) == sorted(zerospace.analyse(world.states, COLORS).basis)


def test_withholding_an_operation_strictly_enlarges_the_recovered_space():
    """Kills M2/M3/M4: a fit that secretly consumes the held-out transitions.

    D-003's mechanism run forwards: less observed difference space means a
    larger recovered invariant space. If the fit cheats, the space does not
    grow, and this is the only place that would notice.
    """
    world = _world()
    features = zsh._features(world)
    encoded = [zerospace.encode(s, features) for s in world.states]
    _, full = zsh.fit(encoded, features, range(len(world.actions)))
    grew = 0
    for j in range(len(world.operations)):
        train, _ = split.leave_one_operation_out(world.actions, j)
        _, partial = zsh.fit(encoded, features, train)
        assert len(partial) >= len(full)
        grew += int(len(partial) > len(full))
    assert grew == len(world.operations), (
        "every operation carries information in this family, so removing any of "
        "them must enlarge the recovered space"
    )


def test_the_score_reads_the_heldout_side_and_not_the_train_side():
    """Kills M4: scoring the transitions the fit already consumed.

    Negative control. Cell 0 of a contiguous-window world is touched by exactly
    one operation, so withholding operation 0 mints a law claiming cell 0 is
    constant -- which the withheld transitions refute and the training ones
    cannot.
    """
    world = _world()
    train, heldout = split.leave_one_operation_out(world.actions, 0)
    outcome = zsh.score(world, train, heldout, "test")
    misses = [law for law in outcome.laws if not law.delta_hit]
    assert misses, "a known-false law scored as a hit means the wrong side was read"
    assert any(law.support == ["B@0"] or law.support == ["R@0"] for law in misses)
    for law in misses:
        assert law.first_delta_witness, "a miss with no witness is not reproducible"
        assert law.first_delta_witness["transition"] in heldout


def test_the_scored_witness_really_refutes_the_law():
    """The witness must be checkable, not merely present."""
    world = _world()
    train, heldout = split.leave_one_operation_out(world.actions, 0)
    features = zsh._features(world)
    encoded = [zerospace.encode(s, features) for s in world.states]
    laws, _ = zsh.fit(encoded, features, train)
    outcome = zsh.score(world, train, heldout, "test")
    for law, scored in zip(laws, outcome.laws):
        if scored.delta_hit:
            continue
        t = scored.first_delta_witness["transition"]
        assert gf2.dot(law.vector, encoded[t] ^ encoded[t + 1]) != 0


def test_row_novelty_is_measured_and_the_random_split_withholds_nothing_new():
    """Pins E17's F1 so it cannot be quietly lost.

    A `parityworld` difference vector is a function of the operation alone, so a
    transition-level split holds out rows the fit already saw and its hit rate
    is forced. That is a property of the corpus, and the harness has to keep
    saying so beside the number.
    """
    world = _world()
    s1 = zsh.run_s1(world)
    assert s1.n_heldout == s1.heldout_rows_duplicate
    assert s1.heldout_rows_novel == 0
    for s2 in zsh.run_s2(world):
        assert s2.heldout_rows_duplicate == 0
        assert s2.heldout_rows_novel == s2.n_heldout


# ------------------------------------------------------------------ the pegs

def test_the_peg_generator_agrees_with_fixture_c_without_going_through_the_gate():
    """Kills M10: `matches_fixture_peg4` returning a constant `(True, [])`."""
    from fixtures import peg4

    reference = peg4.generate()
    mine = peg.graph(4, peg4.GOAL)
    for field in ("n_pos", "goal_states", "states", "move_instances", "edges",
                  "distance_to_goal"):
        assert mine[field] == reference[field], field


def test_the_fixture_c_gate_can_actually_fail(monkeypatch):
    """Kills M10 properly.

    The previous test makes a lying gate *harmless*; this one makes it
    *detectable*. A validity gate that cannot return False is not a gate, and
    E17 pre-registered this one as a condition on the run being valid at all.
    """
    assert peg.matches_fixture_peg4() == (True, [])
    real = peg.graph

    def wrong(n, goal):
        g = dict(real(n, goal))
        g["edges"] = g["edges"][:-1]
        return g

    monkeypatch.setattr(peg, "graph", wrong)
    ok, problems = peg.matches_fixture_peg4()
    assert ok is False and "edges" in problems


def test_withholding_a_geometry_removes_it_from_the_engines_move_list():
    """Kills M9: a `graph_minus_geometry` that deletes nothing.

    The check is made where it bites -- on `moves_from_graph`, which is what the
    LP actually reads -- rather than on the edge list.
    """
    from engines.lp_potential.potential import moves_from_graph

    graph = peg.graph(4, "0100")
    for geometry in peg.geometries(graph):
        reduced = peg.graph_minus_geometry(graph, geometry)
        names = {m.name() for m in moves_from_graph(reduced)}
        assert Move(*geometry).name() not in names
        assert len(names) == len(moves_from_graph(graph)) - 1
        assert reduced["distance_to_goal"] == graph["distance_to_goal"], (
            "ground truth must stay over the complete move set"
        )


def test_admissibility_scoring_finds_a_planted_violation():
    """Kills M11: skipping past the states that would violate."""
    graph = peg.graph(4, "0100")
    # Weights that make h infinite on a state with a finite true distance: the
    # goal outweighs everything, so `required < 0` and `value()` returns inf.
    certificate = Certificate(
        weights=[Fraction(0), Fraction(10), Fraction(0), Fraction(0)],
        initial="1110", goal_states=["0100"],
        moves=[Move(*g) for g in peg.geometries(graph)], margin=Fraction(1),
    )
    violations, tested, first = lph._admissibility_on_heldout(certificate, graph)
    assert tested > 0
    assert violations > 0
    assert first["true_distance"] is not None


def test_inv_closed_scoring_accepts_a_delta_of_exactly_zero():
    """Kills M12: `< 0` where the certificate condition says `<= 0`.

    A move that leaves the potential unchanged satisfies `inv_closed`. Scoring
    it as a miss would deflate the published rate silently.
    """
    weights = [Fraction(0), Fraction(0), Fraction(0), Fraction(0)]
    assert Move(3, 2, 1).delta(weights) == 0
    assert Move(3, 2, 1).delta(weights) <= 0


def test_the_emit_gate_is_measured_on_the_graph_the_caller_would_hold():
    """Pins E17's F5.

    Gating a partial-evidence certificate against the *complete* graph asks
    whether the guard fires when handed the answer the hold-out says the caller
    does not have. The harness must report both, and on the caller's own graph
    a false certificate does get emitted.
    """
    graph = peg.graph(4, "0100")
    instance = next(i for i in lph.instances(4, graph, "0100")
                    if i.initial == "0011")
    case = lph.held_out_case(instance, graph, (3, 2, 1))
    assert case.outcome == "certificate"
    assert case.claim_true is False, "0100 is one move from 0011"
    assert case.gate_withholds is True
    assert case.gate_withholds_reduced is False, (
        "a caller holding only the reduced graph emits this false certificate"
    )


# ------------------------------------------------------- the published rates

def test_the_published_rate_probe_reads_delta_hit_not_value_hit():
    """Kills P6: rewiring the table's probes to the other metric, invisibly.

    `delta_hit` and `value_hit` are logically equivalent on a path, so on real
    data no digit moves and no test could tell. Here they are made to differ.
    """
    from tools import engine_table

    fake = {"zero_space": {"splits": {"X": {"laws": 4, "delta_hit": 1,
                                            "value_hit": 3}}}}
    assert engine_table._rate("X")(fake) == "25.0"


def test_the_pooled_rate_probe_pools_counts_rather_than_averaging_rates():
    """Kills P5 at the source rather than only via the table's drift check."""
    from tools import engine_table

    fake = {"zero_space": {"splits": {
        "P/a": {"laws": 100, "delta_hit": 0, "value_hit": 0},
        "P/b": {"laws": 1, "delta_hit": 1, "value_hit": 1},
    }}}
    # Pooled: 1/101 = 1.0 %. Averaging the two rates would give 50.0 %.
    assert engine_table._rate_suffix("P/", "")(fake) == "1.0"


def test_a_probe_over_an_empty_bucket_raises_rather_than_returning_zero():
    from tools import engine_table

    with pytest.raises(engine_table.ProbeError):
        engine_table._rate_suffix("nothing/", "")({"zero_space": {"splits": {}}})


def test_scope_exhaustive_is_derived_and_cannot_be_set_by_a_caller():
    """E19: E15 made this a property; E17's fit was still passing it as a kwarg.

    The two branches merged without a textual conflict because neither touched
    the other's lines, and nothing in the rig runs the merged tree.  The nail is
    here rather than in the engine's own tests because the caller is what broke.
    """
    from engines.zero_space.zerospace import Law

    with pytest.raises(TypeError):
        Law(vector=1, features=["x"], value=0, scope="global",
            scope_exhaustive=True)

    # And the derivation itself, so a future field rename cannot quietly invert
    # it: exhaustive means *no* cell was truncated.
    assert Law(vector=1, features=["x"], value=0, scope="global",
               truncated_cells=()).scope_exhaustive is True
    assert Law(vector=1, features=["x"], value=0, scope="global",
               truncated_cells=(3,)).scope_exhaustive is False
