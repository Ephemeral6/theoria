"""The worldgen adapter, its gate, and the axis-C row it produces.

Fast and offline by construction.  Only the two smallest worlds are exercised --
`t1-switch-latch` (34 declared states) and `t1-tokens-lock` (128) -- because the
full gradient is a run, not a test, and a suite that walked it would spend
seconds to re-measure what `runs/.../axis_compose.json` already records.

The load-bearing test in this file is `test_gate_catches_*`.  A gate that only
ever passes is decoration: it is the thing standing between "IC3 proved something
about this world" and "IC3 proved something fast about a world that is not this
one", so it has to be shown refusing a system that has been broken in exactly the
ways the adapter could plausibly break one -- a truncated slot domain, a dropped
edge, a relabelled rule, a bad set that is actually reachable.
"""

import copy
import json

import pytest

from ic3bounds import axis_compose, harness, worldgen_system
from ic3bounds.worldgen_system import EncodingError, UnsupportedWorld
from engines.ic3_pdr import pdr
from engines.ic3_pdr.system import System

SMALL = "t1-switch-latch"
NEXT = "t1-tokens-lock"

# The published shape of every rung, from `worldgen` alone.  Pinned here because
# the whole axis rests on the declared product being what the ladder says it is:
# if a world's floor count or a slot domain moved, the table would still print
# but it would no longer be the gradient it claims to walk.
EXPECTED = {
    "t1-switch-latch":       (1, 17, 18, 34),
    "t1-tokens-lock":        (1, 16, 19, 128),
    "t2-cycler-lock":        (2, 16, 19, 128),
    "t2-lock-fragile":       (2, 24, 30, 576),
    "t3-cycler-portal-lock": (3, 36, 41, 432),
    "t3-latch-maze":         (3, 35, 42, 1680),
}


@pytest.fixture(scope="module")
def small():
    return worldgen_system.build_system(SMALL)


# --------------------------------------------------------------- the layout

@pytest.mark.parametrize("world_id", sorted(EXPECTED))
def test_declared_shape_matches_the_ladder(world_id):
    families, floor, variables, product = EXPECTED[world_id]
    info = worldgen_system.summary(world_id)
    assert (info["n_families"], info["n_floor_cells"],
            info["n_variables"], info["declared_product"]) == (
        families, floor, variables, product)
    assert info["declared_product"] == floor * _domain_product(info)


def _domain_product(info):
    total = 1
    for slot in info["layout"]["slots"]:
        total *= len(slot["domain"])
    return total


def test_slot_domains_are_the_families_own(small):
    """A `fragile` tile is three-valued and a `cycler` runs over `range(k)`.

    The single most likely way to get a fast invariant about the wrong world is
    to encode a multi-valued slot as a boolean, so the domains are asserted
    rather than trusted.
    """
    kinds = {}
    for world_id in ("t2-lock-fragile", "t2-cycler-lock", NEXT, SMALL):
        for slot in worldgen_system.summary(world_id)["layout"]["slots"]:
            kinds.setdefault(slot["kind"], set()).add(tuple(slot["domain"]))
    assert kinds["fragile"] == {(0, 1, 2)}
    assert kinds["token"] == {(0, 1)}
    assert kinds["switch"] == {(0, 1)}
    assert kinds["cycler"] == {(0, 1)}          # t2-cycler-lock declares k=2


def test_encoding_round_trips_on_every_declared_state():
    for world_id in (SMALL, NEXT):
        _world, layout = worldgen_system.build_layout(world_id)
        declared = layout.declared()
        assert len(declared) == layout.declared_product
        encoded = [layout.encode(state) for state in declared]
        assert len(set(encoded)) == len(encoded)         # injective
        for state, bits in zip(declared, encoded):
            assert layout.decode(bits) == state          # and inverted


def test_decode_refuses_a_malformed_bit_vector(small):
    layout = small.layout
    bits = list(small.states[0])
    hot = bits.index(True)
    bits[hot] = False
    with pytest.raises(EncodingError):
        layout.decode(tuple(bits))


def test_push_and_gravity_worlds_are_refused():
    """Refused, not approximated.  A `push` slot's domain is the floor set."""
    for world_id in ("t1-push-open", "t2-gravity-push"):
        with pytest.raises(UnsupportedWorld):
            worldgen_system.build_layout(world_id)


# ------------------------------------------------------------------ the gate

def test_gate_passes_on_the_two_small_worlds():
    for world_id in (SMALL, NEXT):
        system = worldgen_system.build_system(world_id)
        info = worldgen_system.summary(world_id)
        assert worldgen_system.transcription_mismatches(
            system, info["n_variables"], info["initial"],
            tuple(info["bad_states"])) == []


def _rebuilt(system, **changes):
    """A copy of `system` with one field replaced -- the broken-adapter fixture."""
    fields = {
        "name": system.name, "variables": system.variables,
        "states": system.states, "init": system.init, "bad": system.bad,
        "transitions": system.transitions, "layout": system.layout,
        "world": system.world, "bad_set": system.bad_set,
    }
    fields.update(changes)
    return worldgen_system.WorldSystem(**fields)


def _reachable_source(system):
    """A state the gate's oracle actually walks.

    `GridWorld.transitions()` enumerates the reachable set, so a broken edge out
    of a declared-but-unreachable state is outside what check 6 can see -- see
    `transcription_mismatches`, which says so. Breaking a *reachable* source is
    what tests the check that exists.
    """
    return system.layout.encode(system.world.initial())


def test_gate_catches_a_dropped_edge(small):
    """The failure the whole axis is exposed to: an edge that quietly vanishes."""
    transitions = dict(small.transitions)
    source = _reachable_source(small)
    transitions[source] = transitions[source][1:]
    problems = worldgen_system.transcription_mismatches(_rebuilt(small,
                                                                 transitions=transitions))
    assert problems and any("transitions from" in p for p in problems)


def test_gate_catches_a_relabelled_rule(small):
    """`DOWN:walk` where the world says `DOWN:press_latch` is a different world.

    The rule tag rides in the move label for exactly this reason: an adapter that
    got the successor right and the rule wrong would otherwise pass.
    """
    transitions = dict(small.transitions)
    source = _reachable_source(small)
    _label, target = transitions[source][0]
    transitions[source] = (("UP:not_a_rule", target),) + transitions[source][1:]
    problems = worldgen_system.transcription_mismatches(_rebuilt(small,
                                                                 transitions=transitions))
    assert problems and any("transitions from" in p for p in problems)


def test_gate_catches_a_shrunken_state_set(small):
    """Drop the states a slot's widest value reaches and the product is wrong."""
    problems = worldgen_system.transcription_mismatches(
        _rebuilt(small, states=small.states[:-2]))
    assert problems and any("declared" in p for p in problems)


def test_gate_catches_a_reachable_bad_set(small):
    """A bad set the agent can actually get to makes the row a BFS, not a proof."""
    reachable = sorted(small.layout.encode(s) for s in small.world.reachable())
    problems = worldgen_system.transcription_mismatches(
        _rebuilt(small, bad=(reachable[0],)))
    assert problems and any("REACHABLE" in p for p in problems)


def test_gate_catches_an_empty_bad_set(small):
    problems = worldgen_system.transcription_mismatches(_rebuilt(small, bad=()))
    assert problems and any("empty" in p for p in problems)


def test_gate_catches_a_wrong_initial_state(small):
    other = next(s for s in small.states if s != small.init[0])
    problems = worldgen_system.transcription_mismatches(_rebuilt(small,
                                                                init=(other,)))
    assert problems and any(p.startswith("init") for p in problems)


def test_gate_catches_a_spec_that_disagrees_with_the_system(small):
    """The spec crosses a process boundary as JSON; the child re-checks it."""
    problems = worldgen_system.transcription_mismatches(
        small, small.layout.n_variables + 1, None, None)
    assert problems and any("variable count" in p for p in problems)


# ------------------------------------------------------ the bad set is honest

@pytest.mark.parametrize("world_id", [SMALL, NEXT])
def test_bad_set_is_unreachable_and_mechanism_separated(world_id):
    """`GridWorld.reachable()` is the independent oracle, and it is asked directly."""
    world, layout = worldgen_system.build_layout(world_id)
    bad_set = worldgen_system.BAD_SETS[world_id](world, layout)
    reachable = world.reachable()
    assert not any(bad_set.predicate(state) for state in reachable)
    hit = [state for state in layout.declared() if bad_set.predicate(state)]
    assert hit, "an empty bad set proves nothing"
    # Separated by a mechanism, not by a wall: the cells the bad set names are
    # cells the agent CAN stand on, in some other configuration of the state.
    from worldgen.core import solvability
    standable = set(solvability.agent_cells(world))
    assert set(bad_set.cells) <= standable


# ------------------------------------------------------------ the determinism

def test_the_system_is_byte_stable(small):
    again = worldgen_system.build_system(SMALL)
    assert again.states == small.states
    assert again.init == small.init
    assert again.bad == small.bad
    assert again.transitions == small.transitions
    assert list(again.states) == sorted(again.states)
    for moves in again.transitions.values():
        assert list(moves) == sorted(moves)


# ---------------------------------------------------------------- the row

def test_spec_round_trips_through_json():
    spec = axis_compose.spec_for(SMALL)
    again = axis_compose.ComposeSpec.from_json(json.loads(json.dumps(spec.as_json())))
    assert again == spec
    assert again.world_id == SMALL
    assert again.n_states == EXPECTED[SMALL][3]


def test_one_rung_in_process_is_an_invariant():
    """The whole row, through `harness.measure_in_process` -- the one runner."""
    spec = axis_compose.spec_for(SMALL)
    record = axis_compose.measure_one(spec)
    det = record["deterministic"]
    assert det["verdict"] == harness.INVARIANT
    assert det["escalate"] is False
    # `n_states` is the declared product, not 2 ** n_variables. That correction
    # is the one place this axis departs from the harness's blank record and it
    # is the difference between reporting 34 states and claiming 262144.
    assert det["n_states"] == EXPECTED[SMALL][3]
    assert det["n_states"] != 2 ** spec.n
    assert det["checker_conditions"] == {"inv_closed": True, "inv_init": True,
                                         "goal_break": True}
    assert 0 < det["n_satisfying"] < det["n_states"]     # not vacuous, not empty
    assert set(det.keys()) == set(harness.DETERMINISTIC_FIELDS)


def test_the_invariant_is_about_the_mechanism_not_the_geometry():
    """`t1-switch-latch`: the latch is what keeps the agent out of the chamber."""
    spec = axis_compose.spec_for(SMALL)
    record = axis_compose.measure_one(spec)
    cnf = record["deterministic"]["cnf_text"]
    assert "switch_r4c1" in cnf
    info = worldgen_system.summary(SMALL)
    assert axis_compose.families_in_invariant(cnf, info) == ["geometry", "switch_door"]
    # And it says more than "the goal is not reachable in this configuration":
    # the bad set is one state and the invariant excludes the whole chamber.
    assert axis_compose.derived(record, info)["strengthening"] > 1.0


def test_measure_one_restores_the_harness(small):
    """The patch is a seam, not a mutation: a leaked one would rebuild every
    later peg row as a worldgen system."""
    before = (harness.build_system, harness.transcription_mismatches)
    axis_compose.measure_one(axis_compose.spec_for(SMALL))
    assert (harness.build_system, harness.transcription_mismatches) == before


def test_a_broken_adapter_is_adapter_mismatch_not_a_boundary(monkeypatch):
    """The taxonomy's whole point: a wrong world is never reported as slow."""
    honest = worldgen_system.build_system

    def broken(world_id):
        system = honest(world_id)
        transitions = dict(system.transitions)
        source = _reachable_source(system)
        transitions[source] = ()
        return _rebuilt(system, transitions=transitions)

    monkeypatch.setattr(worldgen_system, "build_system", broken)
    record = axis_compose.measure_one(axis_compose.spec_for(SMALL))
    det = record["deterministic"]
    assert det["verdict"] == harness.ADAPTER_MISMATCH
    assert det["escalate"] is True
    assert det["machine_dependent"] is False
    assert det["verdict"] != harness.TIMEOUT


# ------------------------------------------------------------- the reporting

def test_recheck_column_is_not_available_never_passed():
    """No worldgen-to-ruleset transcriber exists, so the column says so."""
    info = worldgen_system.summary(SMALL)
    record = axis_compose.measure_one(axis_compose.spec_for(SMALL))
    assert axis_compose.derived(record, info)["recheck"] == "not available"
    assert axis_compose.RECHECK_STATUS == "not available"


def test_report_carries_the_shrunken_domain_caveat():
    payload = axis_compose.report([], 180.0, [SMALL], False)
    assert "shrunken-domain" in payload["shrunken_domain_caveat"]
    assert payload["recheck"]["status"] == "not available"
    assert payload["axis_letter"] == "C"
    assert list(payload["matched_pair"]["worlds"]) == list(axis_compose.MATCHED_PAIR)


def test_matched_pair_is_matched_in_size_and_variables():
    """Steps 2 and 3 are the axis; if they stop matching there is no axis."""
    left, right = (worldgen_system.summary(w) for w in axis_compose.MATCHED_PAIR)
    assert left["declared_product"] == right["declared_product"]
    assert left["n_variables"] == right["n_variables"]
    assert left["n_families"] == 1 and right["n_families"] == 2
