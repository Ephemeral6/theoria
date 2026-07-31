"""Axis B rests on one claim: a re-encoding changes the words, not the world.

Every number in `IC3_BOUNDS.md`'s axis B table is a comparison between two rungs
that are supposed to be the *same problem* asked in different vocabularies.  If
that is false anywhere -- if a scheme merges two states, or loses an edge, or
quietly makes the question easier -- then the table is not a measurement of
predicate count, it is a measurement of whatever else changed, and every
sentence drawn from it is wrong.  So the claim is tested first and hardest here,
before anything that reads the table.

The second claim is the one that gives axis B a recheck column at all: a `dual`
certificate has an exact native form, so it can be handed to `recheck/`, which
shares no code with the engine.  That is tested by counting the same set twice
through the bijection and refusing to accept the two numbers as equal on faith.
"""

import json

import pytest

from engines.ic3_pdr import check as ic3_check
from engines.ic3_pdr import pdr
from ic3bounds import axis_predicates, harness, reencode

# peg4/0111 is the M9 anchor: unsolvable, no linear pagoda, IC3's whole reason
# for existing.  peg4/1101 is solvable, and is on this list because a scheme
# that made an unsolvable problem look unsolvable would pass every test above
# while being useless -- the counterexample side has to survive re-encoding too.
UNSOLVABLE = (4, "0111", "0100")
SOLVABLE = (4, "1101", "0100")

SCHEMES = (
    (reencode.BINARY, 0),
    (reencode.NATIVE, 0),
    (reencode.DUAL, 1),
    (reencode.DUAL, 2),
    (reencode.DUAL, 4),
    (reencode.ONEHOT, 0),
)


def _system(n, initial, goal):
    return harness.build_system(harness.StepSpec(
        axis="predicates", label="peg%d" % n, n=n,
        initial=initial, goal_states=(goal,)))


def _recoded(n, initial, goal, scheme, k):
    system = _system(n, initial, goal)
    recoding = reencode.recoding_for(system, scheme, k)
    return system, recoding, reencode.reencode(system, recoding)


# --------------------------------------------------- the world does not move

@pytest.mark.parametrize("scheme,k", SCHEMES)
def test_a_recoding_is_a_bijection_on_states(scheme, k):
    system, recoding, recoded = _recoded(*UNSOLVABLE, scheme, k)
    assert len(recoded.states) == len(system.states)
    assert len(set(recoded.states)) == len(recoded.states)
    assert list(recoded.states) == sorted(recoded.states)


@pytest.mark.parametrize("scheme,k", SCHEMES)
def test_every_labelled_edge_survives_re_encoding(scheme, k):
    """Not just the edge count -- the labels and the endpoints.

    A scheme that preserved the *number* of successors while permuting where
    they go would leave |S| and the degree sequence untouched and change the
    answer, which is exactly the failure a count-only check cannot see.
    """
    system, recoding, recoded = _recoded(*UNSOLVABLE, scheme, k)
    for state in system.states:
        before = sorted((label, recoding.encode(target))
                        for label, target in system.moves(state))
        assert sorted(recoded.moves(recoding.encode(state))) == before


@pytest.mark.parametrize("scheme,k", SCHEMES)
def test_the_gate_passes_on_a_recoding_that_is_one(scheme, k):
    system, recoding, recoded = _recoded(*UNSOLVABLE, scheme, k)
    assert reencode.recoding_mismatches(system, recoded, recoding) == []


@pytest.mark.parametrize("scheme,k", SCHEMES)
def test_the_verdict_does_not_depend_on_the_vocabulary(scheme, k):
    """The unsolvable configuration stays unsolvable in every alphabet."""
    _, _, recoded = _recoded(*UNSOLVABLE, scheme, k)
    verdict = pdr.ic3(recoded, max_levels=64)
    assert isinstance(verdict, pdr.Invariant)
    assert ic3_check.verify(recoded, verdict.clauses).holds


@pytest.mark.parametrize("scheme,k", SCHEMES)
def test_a_solvable_configuration_still_has_no_invariant_in_any_alphabet(scheme, k):
    """The row that makes the others mean something.

    A re-encoding that made the goal unreachable would produce invariants
    everywhere and a table of beautifully cheap ones.  `1101` reaches `0100` in
    two moves and must keep doing so however it is spelled.
    """
    _, _, recoded = _recoded(*SOLVABLE, scheme, k)
    verdict = pdr.ic3(recoded, max_levels=64)
    assert isinstance(verdict, pdr.Counterexample)
    assert ic3_check.replay(recoded, verdict.states, verdict.moves)
    assert verdict.length == 2


def test_the_reachable_set_is_the_same_size_in_every_alphabet():
    """`abstraction`'s denominator, checked once rather than trusted per row."""
    system = _system(*UNSOLVABLE)
    native = axis_predicates.reachable_count(system)
    for scheme, k in SCHEMES:
        _, _, recoded = _recoded(*UNSOLVABLE, scheme, k)
        assert axis_predicates.reachable_count(recoded) == native


# ------------------------------------------------------- the gate is not a nod

def test_the_gate_catches_a_lost_edge():
    system, recoding, recoded = _recoded(*UNSOLVABLE, reencode.DUAL, 2)
    victim = next(s for s in recoded.states if recoded.moves(s))
    broken = dict(recoded.transitions)
    broken[victim] = broken[victim][1:]
    maimed = type(recoded)(
        name=recoded.name, variables=recoded.variables, states=recoded.states,
        init=recoded.init, bad=recoded.bad, transitions=broken)
    problems = reencode.recoding_mismatches(system, maimed, recoding)
    assert problems and any("transitions from" in p for p in problems)


def test_the_gate_catches_a_state_set_that_moved():
    """|S| moving is the one thing this axis cannot survive, so it is named.

    Shrinking rather than growing, because peg-N's state set is already the
    whole bit space and there is nothing to add to it -- which is itself worth
    knowing: on this family a *lost* state is the only size drift possible, and
    a gate that only watched for growth would never fire.
    """
    system, recoding, recoded = _recoded(*UNSOLVABLE, reencode.NATIVE, 0)
    thinned = type(recoded)(
        name=recoded.name, variables=recoded.variables,
        states=recoded.states[1:],
        init=recoded.init, bad=recoded.bad, transitions=recoded.transitions)
    problems = reencode.recoding_mismatches(system, thinned, recoding)
    assert any("|S|" in p for p in problems)


def test_a_scheme_that_is_not_injective_is_refused_rather_than_measured():
    """Two states collapsing into one code would make IC3 answer a smaller
    question and the row would report its cost as this question's."""
    system = _system(*UNSOLVABLE)
    collapsing = reencode.Recoding(
        scheme="broken", k=0,
        variables=("pos0",), native_variables=tuple(system.variables),
        definitions=(("var", 0, True),))
    with pytest.raises(reencode.RecodingError, match="not injective"):
        reencode.reencode(system, collapsing)


def test_dual_past_the_variable_count_is_refused():
    system = _system(*UNSOLVABLE)
    with pytest.raises(reencode.RecodingError, match="duplicates"):
        reencode.dual_recoding(system, len(system.variables) + 1)


# ---------------------------------------------------------------- desugaring

@pytest.mark.parametrize("k", (0, 1, 2, 3, 4))
def test_the_native_form_of_a_dual_invariant_holds_on_exactly_the_same_states(k):
    """The claim the recheck column rests on, counted twice.

    A bijection cannot change the size of a set, so the recoded invariant and
    its native form must admit the same number of states.  Both counts are taken
    by the engine's own independent checker, on the two systems, and compared --
    rather than the translation being trusted because it looks right.
    """
    system, recoding, recoded = _recoded(*UNSOLVABLE, reencode.DUAL, k)
    verdict = pdr.ic3(recoded, max_levels=64)
    recoded_result = ic3_check.verify(recoded, verdict.clauses)

    native = reencode.desugar(recoding, verdict.clauses)
    native_result = ic3_check.verify(system, native.clauses)

    assert native_result.holds, "the native form is not an inductive invariant"
    assert native_result.n_satisfying == recoded_result.n_satisfying
    assert native_result.n_states == len(system.states)


def test_desugaring_never_invents_a_variable_the_world_does_not_have():
    system, recoding, recoded = _recoded(*UNSOLVABLE, reencode.DUAL, 4)
    verdict = pdr.ic3(recoded, max_levels=64)
    native = reencode.desugar(recoding, verdict.clauses)
    for clause in native.clauses:
        for index, _ in clause:
            assert 0 <= index < len(system.variables)


def test_a_tautological_clause_is_dropped_and_counted():
    """`(pos0 | free_pos0)` is true of every state.  Dropping it changes
    nothing; not counting it would hide how much of a certificate is filler."""
    system = _system(*UNSOLVABLE)
    recoding = reencode.dual_recoding(system, 4)
    n = len(system.variables)
    tautology = frozenset({(0, True), (n + 0, True)})
    real = frozenset({(1, False), (2, True)})
    native = reencode.desugar(recoding, [tautology, real])
    assert native.tautologies_dropped == 1
    assert native.n_clauses == 1
    assert native.clauses[0] == real


def test_two_names_for_one_half_plane_collapse_into_one_literal():
    system = _system(*UNSOLVABLE)
    recoding = reencode.dual_recoding(system, 4)
    n = len(system.variables)
    # `!pos0` and `free_pos0` are the same half-plane under two names.
    doubled = frozenset({(0, False), (n + 0, True)})
    native = reencode.desugar(recoding, [doubled])
    assert native.n_clauses == 1
    assert native.clauses[0] == frozenset({(0, False)})
    assert native.literals_before == 2 and native.literals_after == 1


@pytest.mark.parametrize("scheme", (reencode.BINARY, reencode.ONEHOT))
def test_a_scheme_that_names_states_has_no_native_form_and_says_so(scheme):
    """The failure shape the item calls 'certificate not recheckable'.

    It is a refusal, not a best effort: a clause over `is_01011010` says nothing
    about the world that a rewriting could recover, and producing an
    approximation would hand `recheck/` an object that is not the certificate.
    """
    system, recoding, recoded = _recoded(*UNSOLVABLE, scheme, 0)
    assert recoding.desugars() is False
    verdict = pdr.ic3(recoded, max_levels=64)
    with pytest.raises(reencode.RecodingError, match="no native form"):
        reencode.desugar(recoding, verdict.clauses)


def test_native_and_dual_do_desugar():
    system = _system(*UNSOLVABLE)
    assert reencode.native_recoding(system).desugars() is True
    assert reencode.dual_recoding(system, 3).desugars() is True


# ----------------------------------------------------------------- the widths

def test_the_binary_scheme_sits_exactly_on_the_information_floor():
    for n in (4, 6, 8):
        system = _system(n, "0" + "1" * (n - 1), "01" + "0" * (n - 2))
        recoding = reencode.binary_recoding(system)
        assert recoding.n_variables == n           # 2^n states need n bits
        assert reencode.encoding_slack(recoding.n_variables,
                                       len(system.states)) == 0


def test_onehot_spends_one_predicate_per_state():
    system = _system(*UNSOLVABLE)
    recoding = reencode.onehot_recoding(system)
    assert recoding.n_variables == len(system.states) == 16
    assert reencode.encoding_slack(16, 16) == 12


def test_dual_spends_exactly_k_predicates_above_the_floor():
    system = _system(*UNSOLVABLE)
    for k in range(5):
        recoding = reencode.dual_recoding(system, k)
        assert recoding.n_variables == len(system.variables) + k
        assert reencode.encoding_slack(recoding.n_variables, 16) == k


# ------------------------------------------------- the inverse, written apart

@pytest.mark.parametrize("scheme,k", SCHEMES)
def test_every_code_reads_back_into_the_state_it_came_from(scheme, k):
    """`decode` is what stops the gate from being `encode` checked against
    itself, so it gets its own round trip rather than being trusted."""
    system, recoding, _ = _recoded(*UNSOLVABLE, scheme, k)
    for state in system.states:
        assert recoding.decode(recoding.encode(state)) == state


@pytest.mark.parametrize("scheme,k", SCHEMES)
def test_decode_does_not_search_the_order_for_a_matching_encode(scheme, k):
    """If it did, the gate would be circular and this would still pass -- so
    the assertion is on the mechanism: `decode` works on a recoding whose
    `_ordinals` lookup has been emptied, which a search could not."""
    system, recoding, _ = _recoded(*UNSOLVABLE, scheme, k)
    state = system.states[3]
    code = recoding.encode(state)
    stripped = reencode.Recoding(
        scheme=recoding.scheme, k=recoding.k, variables=recoding.variables,
        native_variables=recoding.native_variables,
        definitions=recoding.definitions, order=recoding.order)
    object.__setattr__(stripped, "_ordinals", {})
    assert stripped.decode(code) == state


def test_a_code_naming_two_states_at_once_is_refused():
    system = _system(*UNSOLVABLE)
    recoding = reencode.onehot_recoding(system)
    both = tuple(i < 2 for i in range(len(recoding.variables)))
    with pytest.raises(reencode.RecodingError, match="two one-hot"):
        recoding.decode(both)


def test_a_code_of_the_wrong_width_is_refused():
    system = _system(*UNSOLVABLE)
    recoding = reencode.native_recoding(system)
    with pytest.raises(reencode.RecodingError, match="declares 4 predicates"):
        recoding.decode((True, False))


# ------------------------------------------------------- the malformed inputs

def test_an_edge_leaving_the_declared_state_set_is_named_not_a_keyerror():
    """It would otherwise surface as `engine-refused` and blame the engine for
    a fault in whatever built the system."""
    system = _system(*UNSOLVABLE)
    # A state some edge actually points at -- dropping one nothing reaches
    # (peg's full board, which no jump produces) would prove nothing.
    target = next(t for s in system.states for _, t in system.moves(s))
    broken = type(system)(
        name=system.name, variables=system.variables,
        states=tuple(s for s in system.states if s != target),
        init=system.init, bad=system.bad, transitions=system.transitions)
    recoding = reencode.native_recoding(broken)
    with pytest.raises(reencode.RecodingError, match="leaves the declared"):
        reencode.reencode(broken, recoding)


def test_the_floor_width_agrees_with_the_scheme_that_spends_it():
    """`binary_recoding` and `encoding_slack` must not disagree about the floor,
    or 'the floor' scheme reports slack it did not spend."""
    for n_states in (1, 2, 3, 4, 5, 8, 16, 64, 128, 1024, 4096):
        assert reencode.floor_width(n_states) >= 1
        assert 2 ** reencode.floor_width(n_states) >= n_states
    assert reencode.floor_width(1) == 1
    assert reencode.encoding_slack(1, 1) == 0
    assert reencode.floor_width((1 << 49) + 1) == 50      # ceil(log2) is off here


def test_a_literal_naming_no_predicate_is_refused_rather_than_wrapping():
    system = _system(*UNSOLVABLE)
    recoding = reencode.dual_recoding(system, 2)
    with pytest.raises(reencode.RecodingError, match="names predicate"):
        recoding.desugar_literal((-1, True))
    with pytest.raises(reencode.RecodingError, match="names predicate"):
        recoding.desugar_literal((99, True))


# ------------------------------------------- is the vocabulary really foreign?

def test_binary_on_peg_is_the_worlds_own_variables_reversed():
    """The finding that refuted this package's own `adjudicable` column.

    `peg_system` sorts its states as binary strings, so a state's *index* is its
    bit string and `b_i` is exactly `pos_(n-1-i)`. Four rungs had been reported
    as carrying an unreadable certificate on the strength of the scheme's name.
    """
    for n in (4, 6, 8):
        system = _system(n, "0" + "1" * (n - 1), "01" + "0" * (n - 2))
        recoding = reencode.binary_recoding(system)
        renaming = reencode.renaming_map(system, recoding)
        assert renaming is not None
        assert renaming == tuple((n - 1 - i, True) for i in range(n))


def test_onehot_is_genuinely_not_a_renaming():
    system = _system(*UNSOLVABLE)
    assert reencode.renaming_map(system, reencode.onehot_recoding(system)) is None


def test_binary_on_a_world_that_really_compresses_is_not_a_renaming():
    """Seven bits cannot rename nineteen variables, and the measurement says so
    rather than the scheme's name saying it."""
    from ic3bounds import worldgen_system
    system = worldgen_system.build_system("t1-tokens-lock")
    recoding = reencode.binary_recoding(system)
    assert recoding.n_variables == 7 and len(system.variables) == 19
    assert reencode.renaming_map(system, recoding) is None


def test_a_renamed_certificate_desugars_to_the_same_satisfying_set():
    """A renaming is still a bijection on states, so the count cannot move."""
    for n in (4, 6):
        system = _system(n, "0" + "1" * (n - 1), "01" + "0" * (n - 2))
        recoding = reencode.binary_recoding(system)
        recoded = reencode.reencode(system, recoding)
        renaming = reencode.renaming_map(system, recoding)
        verdict = pdr.ic3(recoded, max_levels=64)
        native = reencode.desugar(recoding, verdict.clauses, renaming=renaming)
        assert ic3_check.verify(system, native.clauses).n_satisfying == \
               ic3_check.verify(recoded, verdict.clauses).n_satisfying


def test_desugar_still_refuses_a_scheme_with_no_renaming():
    system = _system(*UNSOLVABLE)
    recoding = reencode.onehot_recoding(system)
    recoded = reencode.reencode(system, recoding)
    verdict = pdr.ic3(recoded, max_levels=64)
    with pytest.raises(reencode.RecodingError, match="no native form"):
        reencode.desugar(recoding, verdict.clauses, renaming=None)


def test_a_recoding_is_hashable_and_serialisable():
    """It is a frozen dataclass with a derived lookup table hidden inside it,
    which is the kind of thing that silently stops being hashable."""
    system = _system(*UNSOLVABLE)
    recoding = reencode.onehot_recoding(system)
    assert isinstance(hash(recoding), int)
    assert recoding == reencode.onehot_recoding(system)
    payload = json.dumps(recoding.as_json(), sort_keys=True)
    assert '"desugars": false' in payload
    assert '"n_variables": 16' in payload
