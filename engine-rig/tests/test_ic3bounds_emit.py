"""`ic3bounds.emit`: the IC3 invariant, as an object an independent checker can
refuse.

Three things are under test here and they are not the same thing.

1. **The translation is faithful.**  `engines.ic3_pdr` counts states as boolean
   tuples; `recheck` counts them over the product of declared finite domains.
   If the two counts differ, the predicate denotes a different set than the
   invariant and every verdict about it is about the wrong object.  The
   demonstration is `test_a_dropped_literal_is_caught_although_it_verifies`:
   on peg-6 there is a one-literal weakening that the rechecker **ACCEPTs** --
   all three conditions hold -- while denoting 27 states instead of 30.  A
   column that only recorded the verdict would be green and vacuous.

2. **The two transcriptions stay two.**  `recheck.build_cases` writes the rule
   sets from the geometry and knows nothing about IC3; this module writes only
   the invariant and never a rule; and the two are tied together by
   `interop.peg1d`, which predates both.  `test_recheck_never_imports_the_emitter`
   is the same enforcement `test_recheck_never_imports_the_engines` applies one
   layer down.

3. **The transcribed literals are still the engine's answer.**
   `recheck.build_cases.PEG_IC3_INVARIANTS` holds the clauses as data, because a
   file inside `recheck/` may not import the engine that produced them.  A
   transcription nobody re-derives is a rumour, so this file re-runs the search
   and compares clause by clause.

Everything here is offline: peg boards up to eight positions, no network, no
Lean, no toolchain.
"""

import copy
import json
import os
from typing import Dict, List, Tuple

import pytest

from engines import ic3_pdr
from engines.ic3_pdr import check as ic3_check
from engines.ic3_pdr.system import clause_key, peg_system
from ic3bounds import emit
from interop import certificate_export as ce
from interop import peg1d
from recheck import build_cases, verify_all
from recheck.certificate import certificate_from_spec, load_certificate
from recheck.ruleset import load_ruleset
from recheck.verify import ACCEPT, recheck

CASES_DIR = build_cases.CASES_DIR

# peg4 from 0111 with goal 0100 -- STATUS.md's M9 line, and the one point the
# whole E8 gradient is anchored on.
M9 = (4, "0111", "0100")
M9_RENDERING = "(!pos1 | pos2) & (pos1 | !pos2)"

_SOLVED: Dict[Tuple[int, str, str], tuple] = {}


def solved(n: int, start: str, goal: str):
    """(system, invariant, engine check) for one gradient step, computed once."""
    key = (n, start, goal)
    if key not in _SOLVED:
        graph = peg1d.build_graph(n, start, [goal])
        system = peg_system(graph, start, [goal], name="peg%d" % n)
        verdict = ic3_pdr.ic3(system)
        assert isinstance(verdict, ic3_pdr.Invariant), (
            "peg%d from %s is meant to be unsolvable; the engine returned %r"
            % (n, start, verdict))
        _SOLVED[key] = (system, verdict, ic3_check.verify(system, verdict.clauses))
    return _SOLVED[key]


def gradient() -> List[Tuple[int, str, str]]:
    return [tuple(step) for step in build_cases.PEG_GRADIENT]


def case_paths(n: int, start: str) -> Tuple[str, str]:
    name = build_cases.peg_name(start, n)
    return (os.path.join(CASES_DIR, "%s.rules.json" % name),
            os.path.join(CASES_DIR, "%s-ic3.cert.json" % name))


# ------------------------------------------------------------------ the anchor

def test_the_m9_anchor_is_where_it_was():
    n, start, goal = M9
    system, invariant, check = solved(n, start, goal)
    assert invariant.n_clauses == 2
    assert emit.render_cnf(system, invariant.clauses) == M9_RENDERING
    assert (check.n_satisfying, check.n_states) == (8, 16)
    assert check.holds


def test_the_m9_predicate_is_the_committed_one():
    """The emitter reproduces the certificate M9 shipped, literal for literal."""
    n, start, goal = M9
    system, invariant, _ = solved(n, start, goal)
    _, cert_path = case_paths(n, start)
    with open(cert_path, "r", encoding="utf-8") as handle:
        committed = json.load(handle)
    assert emit.predicate_of(system, invariant.clauses) == committed["predicate"]
    assert committed["predicate"] == [
        "and",
        ["or", ["=", ["var", "pos1"], ["lit", 0]],
               ["=", ["var", "pos2"], ["lit", 1]]],
        ["or", ["=", ["var", "pos1"], ["lit", 1]],
               ["=", ["var", "pos2"], ["lit", 0]]],
    ]


# ------------------------------------------------- the transcription, checked

@pytest.mark.parametrize("n,start,goal", gradient())
def test_the_transcribed_clauses_are_what_the_engine_converges_on(n, start, goal):
    """`build_cases` holds literals because it may not import the engine.

    So the literals are re-derived here instead, in the emitter's own order.
    """
    system, invariant, _ = solved(n, start, goal)
    derived = tuple(
        tuple((system.variables[i], 1 if value else 0) for i, value in sorted(clause))
        for clause in emit.ordered_clauses(invariant.clauses)
    )
    assert derived == build_cases.PEG_IC3_INVARIANTS[(n, start, goal)]["clauses"]


@pytest.mark.parametrize("n,start,goal", gradient())
def test_the_emitted_certificate_is_the_committed_case(n, start, goal):
    system, invariant, _ = solved(n, start, goal)
    _, cert_path = case_paths(n, start)
    with open(cert_path, "r", encoding="utf-8") as handle:
        committed = json.load(handle)
    spec = emit.certificate_spec(
        system, invariant.clauses,
        name=committed["name"],
        ruleset_name=committed["ruleset"]["name"],
        ruleset_sha256=committed["ruleset"]["sha256"],
        produced_by=committed["produced_by"],
        comment=committed["comment"],
    )
    assert spec == committed


def test_the_emitted_predicate_is_byte_stable():
    """Two runs, one file.  Clause sets are sets; the output may not be."""
    system, invariant, _ = solved(*M9)
    first = json.dumps(emit.predicate_of(system, invariant.clauses), sort_keys=True)
    second = json.dumps(emit.predicate_of(system, invariant.clauses), sort_keys=True)
    assert first == second


# --------------------------------------------------------- the count crosscheck

@pytest.mark.parametrize("n,start,goal", gradient())
def test_the_two_counts_agree_on_every_gradient_step(n, start, goal):
    """THE cross-check: one set of states, counted in two encodings."""
    system, invariant, check = solved(n, start, goal)
    rules_path, cert_path = case_paths(n, start)
    ruleset = load_ruleset(rules_path)
    with open(cert_path, "r", encoding="utf-8") as handle:
        committed = json.load(handle)

    crossed = emit.cross_check(system, invariant.clauses, ruleset, committed)
    assert crossed.counts_agree
    assert crossed.accepted
    assert crossed.recheck_n_satisfying == check.n_satisfying
    assert crossed.recheck_n_states == check.n_states == 2 ** n
    assert crossed.engine_conditions == {
        "inv_init": True, "inv_closed": True, "goal_break": True}


@pytest.mark.parametrize("n,start,goal", gradient())
def test_the_declared_counts_in_verify_all_are_the_engines(n, start, goal):
    """`verify_all` writes the numbers down; this is where they come from.

    `recheck/` cannot compute them -- it imports nothing from `engines/` -- so
    the loop is closed here rather than there.
    """
    _, _, check = solved(n, start, goal)
    name = "%s-ic3" % build_cases.peg_name(start, n)
    assert verify_all.IC3_N_SATISFYING[name] == (check.n_satisfying, check.n_states)


def test_emit_returns_the_spec_and_the_crosscheck_together():
    n, start, goal = M9
    system, invariant, check = solved(n, start, goal)
    rules_path, _ = case_paths(n, start)
    ruleset = load_ruleset(rules_path)
    spec, crossed = emit.emit(
        system, invariant, ruleset,
        name="%s-ic3-invariant" % build_cases.peg_name(start, n),
        ruleset_sha256=ruleset.sha256,
    )
    assert spec["ruleset"] == {"name": "peg4-0111", "sha256": ruleset.sha256}
    assert crossed.counts_agree and crossed.accepted
    assert crossed.engine_n_satisfying == check.n_satisfying


# ------------------------------------------------------------------- trap 8

def _weakenings(system, clauses):
    """Every one-literal drop, as (label, mutated clause list)."""
    ordered = list(emit.ordered_clauses(clauses))
    for position, clause in enumerate(ordered):
        for literal in sorted(clause):
            mutated = list(ordered)
            mutated[position] = frozenset(x for x in clause if x != literal)
            yield ("drop %s from clause %d"
                   % (system.render_literal(literal), position), mutated)


def test_a_dropped_literal_is_caught_although_it_verifies():
    """The whole reason the count column exists.

    On peg-6 there is a one-literal weakening the rechecker ACCEPTs: all three
    conditions hold on it.  It denotes 27 states where the invariant denotes 30,
    so accepting it is accepting something else.  The verdict cannot tell; the
    count can, and `cross_check` refuses to emit.
    """
    n, start, goal = 6, "011111", "010000"
    system, invariant, check = solved(n, start, goal)
    rules_path, cert_path = case_paths(n, start)
    ruleset = load_ruleset(rules_path)
    with open(cert_path, "r", encoding="utf-8") as handle:
        honest = json.load(handle)

    vacuously_green = []
    for label, mutated in _weakenings(system, invariant.clauses):
        forged = copy.deepcopy(honest)
        forged["predicate"] = emit.predicate_of(system, mutated)
        verdict = recheck(ruleset, certificate_from_spec(forged))
        if verdict.verdict != ACCEPT:
            continue                      # caught on the merits; not the trap
        if verdict.stats["n_satisfying"] == check.n_satisfying:
            continue                      # a redundant literal: the same set
        vacuously_green.append((label, verdict.stats["n_satisfying"], forged))

    assert vacuously_green, (
        "peg-6 is in this suite because a weakening of its invariant passes all "
        "three conditions. If none does any more, this test is no longer "
        "demonstrating anything and the case must be re-chosen -- do not delete "
        "the assertion")

    for label, n_satisfying, forged in vacuously_green:
        assert n_satisfying != check.n_satisfying
        with pytest.raises(emit.EmitError) as raised:
            emit.cross_check(system, invariant.clauses, ruleset, forged)
        assert "TRANSLATION MISMATCH" in str(raised.value), label
        # And the same call, asked not to raise, reports it rather than hiding it.
        soft = emit.cross_check(system, invariant.clauses, ruleset, forged,
                                strict=False)
        assert soft.verdict == ACCEPT and not soft.counts_agree


def test_a_dropped_clause_is_caught():
    """The other direction: fewer clauses, a larger set, a weaker claim."""
    n, start, goal = M9
    system, invariant, _ = solved(n, start, goal)
    rules_path, cert_path = case_paths(n, start)
    ruleset = load_ruleset(rules_path)
    with open(cert_path, "r", encoding="utf-8") as handle:
        forged = json.load(handle)
    forged["predicate"] = emit.predicate_of(
        system, list(emit.ordered_clauses(invariant.clauses))[1:])
    with pytest.raises(emit.EmitError) as raised:
        emit.cross_check(system, invariant.clauses, ruleset, forged)
    assert "larger" in str(raised.value)


def test_a_predicate_that_never_gets_counted_is_not_a_pass():
    """A rejection before the count is an unchecked translation, not a green."""
    n, start, goal = M9
    system, invariant, _ = solved(n, start, goal)
    rules_path, cert_path = case_paths(n, start)
    ruleset = load_ruleset(rules_path)
    with open(cert_path, "r", encoding="utf-8") as handle:
        forged = json.load(handle)
    forged["ruleset"] = {"name": "peg4-0111", "sha256": "0" * 64}
    with pytest.raises(emit.EmitError) as raised:
        emit.cross_check(system, invariant.clauses, ruleset, forged)
    assert "never counted" in str(raised.value)


def test_a_value_outside_the_declared_domain_is_refused():
    """`["lit", 2]` against a `[0, 1]` domain is unsatisfiable, not false."""
    n, start, goal = M9
    system, invariant, _ = solved(n, start, goal)
    rules_path, cert_path = case_paths(n, start)
    ruleset = load_ruleset(rules_path)
    with open(cert_path, "r", encoding="utf-8") as handle:
        spec = json.load(handle)
    with pytest.raises(emit.EmitError) as raised:
        emit.cross_check(system, invariant.clauses, ruleset, spec, values=(0, 2))
    assert "declared domain" in str(raised.value)


# --------------------------------------------------- the two-transcriptions rule

def test_recheck_never_imports_the_emitter():
    """`ic3bounds.emit` may read `recheck`. `recheck` may not read it.

    If the rechecker built its predicates from the same converter the engine's
    output goes through, "an independent checker accepted it" would be one
    program agreeing with itself.
    """
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    package = os.path.join(here, "recheck")
    offenders = []
    for name in sorted(os.listdir(package)):
        if not name.endswith(".py"):
            continue
        with open(os.path.join(package, name), "r", encoding="utf-8") as handle:
            for line in handle.read().splitlines():
                stripped = line.strip()
                if stripped.startswith(("import ", "from ")) and "ic3bounds" in stripped:
                    offenders.append("%s: %s" % (name, stripped))
    assert not offenders, offenders


def test_the_rule_sets_are_not_built_from_the_system_ic3_ran_on():
    """The anchor, not construction, is what ties the two transcriptions.

    `peg1d` is the third party: `build_cases` derives its rules from the same
    geometry by hand, `peg_system` derives IC3's edge list from `peg1d`'s graph,
    and here the rule set's *derived* relation is compared against `peg1d` edge
    by edge.  If the rule set were built from the system, this would be vacuous.
    """
    for n, start, goal in gradient():
        rules_path, _ = case_paths(n, start)
        ruleset = load_ruleset(rules_path)
        anchor = verify_all.peg_relation_anchor(ruleset, n)
        assert anchor["agrees"], anchor
        assert anchor["n_compared"] == 2 ** n * len(peg1d.move_instances(n))


@pytest.mark.parametrize("n,start,goal", gradient())
def test_every_gradient_case_has_an_anchor(n, start, goal):
    """"A case with no anchor can only tell you this package is self-consistent."""
    name = build_cases.peg_name(start, n)
    rules_path, cert_path = case_paths(n, start)
    assert os.path.exists(rules_path) and os.path.exists(cert_path)
    assert load_certificate(cert_path).binds_ruleset["name"] == name
    assert name in {row[0] for row in verify_all.MATRIX}
    assert any(row[0] == name for row in verify_all.peg_cases())
    # The anchor itself: an outside opinion on whether this board is solvable.
    assert peg1d.distance_to(start, [goal]) is None


# ----------------------------------------------- the cross-track ic3 document

IC3_DOC = os.path.join(ce.OUT_DIR, "ic3_4_0111_to_0100.json")

# CONTRACTS/ic3_certificate_v0.1.md, the required half of the field table.
CONTRACT_REQUIRED = ("schema", "n_pos", "variables", "initial_state",
                     "goal_states", "cnf")


def built_document():
    system, invariant, check = solved(*M9)
    return ce.build_ic3(system, invariant, check)


def test_the_committed_ic3_document_is_what_the_engine_produces():
    with open(IC3_DOC, "r", encoding="utf-8") as handle:
        committed = json.load(handle)
    assert committed == built_document()


def test_the_ic3_document_follows_the_contract():
    document = built_document()
    assert document["schema"] == "ic3_pdr/inductive_invariant_certificate@1"
    for field in CONTRACT_REQUIRED:
        assert field in document
    assert document["n_pos"] == 4
    assert document["variables"] == ["pos0", "pos1", "pos2", "pos3"]
    assert document["initial_state"] == "0111"
    assert document["goal_states"] == ["0100"]
    assert document["cnf"] == [[["pos1", False], ["pos2", True]],
                               [["pos1", True], ["pos2", False]]]
    assert set(document["obligations"]) == {"inv_init", "inv_closed", "goal_break"}


def test_the_ic3_document_carries_no_move_set():
    """The omission is the contract's substance, so it is under test.

    An invariant is inductive only with respect to a transition relation; a
    document that shipped its own would be closed under a move set it chose for
    itself.
    """
    document = built_document()
    assert "moves" not in document
    assert "edges" not in document
    assert "transitions" not in document
    forged = dict(document)
    forged["moves"] = [{"src": 0, "over": 1, "dst": 2}]
    assert any("moves" in error for error in ce.verify_ic3(forged))


def test_the_ic3_document_reverifies_from_its_own_contents():
    assert ce.verify_ic3(built_document()) == []
    with open(IC3_DOC, "r", encoding="utf-8") as handle:
        assert ce.verify_ic3(json.load(handle)) == []


def test_verify_ic3_recomputes_rather_than_believing_the_flags():
    """`verified: true` is the producer's opinion. Tamper under it."""
    document = built_document()

    dropped = copy.deepcopy(document)
    dropped["cnf"] = dropped["cnf"][:1]
    for key in ("n_clauses", "n_satisfying"):
        dropped.pop(key, None)
    errors = ce.verify_ic3(dropped)
    assert errors and any("inv_closed" in error for error in errors)
    assert dropped["verified"] is True                # the flag still says so

    admits_goal = copy.deepcopy(document)
    admits_goal["goal_states"] = ["1111"]
    assert any("goal_break" in error for error in ce.verify_ic3(admits_goal))

    empty = copy.deepcopy(document)
    empty["cnf"] = []
    assert any("identically true" in error for error in ce.verify_ic3(empty))

    empty_clause = copy.deepcopy(document)
    empty_clause["cnf"] = [[]]
    assert any("identically false" in error for error in ce.verify_ic3(empty_clause))

    unknown = copy.deepcopy(document)
    unknown["cnf"] = [[["pos9", True]]]
    assert any("not a declared variable" in error for error in ce.verify_ic3(unknown))

    miscounted = copy.deepcopy(document)
    miscounted["n_satisfying"] = 9
    assert any("n_satisfying" in error for error in ce.verify_ic3(miscounted))


def test_a_tautological_clause_fails_where_the_contract_says_it_should():
    """`pos0 | !pos0` passes two of the three, and dies on `goal_break`."""
    document = copy.deepcopy(built_document())
    document["cnf"] = [[["pos0", True], ["pos0", False]]]
    for key in ("n_clauses", "n_satisfying"):
        document.pop(key, None)
    errors = ce.verify_ic3(document)
    assert errors == ["goal_break: the invariant admits the goal state 0100"]


def test_the_document_agrees_with_the_recheck_certificate():
    """One invariant, two export formats, and they had better be the same set.

    `interop` writes for the theory-compiler track; `ic3bounds.emit` writes for
    the rechecker.  The two orderings and the two counts are compared here so a
    change to one cannot silently drift from the other.
    """
    system, invariant, check = solved(*M9)
    document = built_document()
    ordered = emit.ordered_clauses(invariant.clauses)
    assert document["cnf"] == [system.clause_as_json(c) for c in ordered]
    assert document["n_satisfying"] == check.n_satisfying
    predicate = emit.predicate_of(system, invariant.clauses)
    assert len(predicate) - 1 == len(document["cnf"])
