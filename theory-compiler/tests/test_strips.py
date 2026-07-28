"""Grounding the task ourselves.

A `deadlock_carver` theorem is a statement about a grounded task, so consuming
one starts by holding a grounded task that did not come from the certificate.
The number this file cares most about is **112** — the ground action count. It is
also the number the producer reports in `evidence.coverage`, and the two being
equal is the whole cross-check: if this track's grounding and theirs disagree,
their theorem is about a world this track has not got.
"""

import hashlib
import json
from pathlib import Path

import pytest

from theory_compiler import strips
from theory_compiler.strips import Atom, StripsError

FIXTURES = Path(__file__).parent / "fixtures" / "strips"
REPO = Path(__file__).resolve().parents[2]
DOMAIN = FIXTURES / "sokoban_domain.pddl"
PROBLEM = FIXTURES / "sokoban_open4far.pddl"


@pytest.fixture(scope="module")
def task():
    return strips.load_task(str(DOMAIN), str(PROBLEM))


class TestProvenance:
    def test_the_transcribed_pddl_has_not_drifted(self):
        """The copies are data, and data that quietly stops matching its source
        is worse than no copy: every downstream number would still look right."""
        manifest = json.loads((FIXTURES / "PROVENANCE.json").read_text(encoding="utf-8"))
        for entry in manifest["files"]:
            here = (FIXTURES / entry["path"]).read_bytes()
            digest = hashlib.sha256(here).hexdigest()
            assert digest == entry["sha256"], entry["path"]
            source = REPO / entry["source"]
            if source.exists():
                assert source.read_bytes() == here, (
                    "%s no longer matches %s" % (entry["path"], entry["source"]))

    def test_nothing_here_imports_engine_rig(self):
        source = (Path(__file__).parents[1] / "src" / "theory_compiler"
                  / "strips.py").read_text(encoding="utf-8")
        assert "engine" not in source.replace("engine-rig's", "").replace(
            "engine-rig", "").replace("engines", ""), "unexpected engine reference"


class TestGrounding:
    def test_the_action_count_is_the_number_the_producer_reports(self, task):
        assert len(task.actions) == 112
        assert sum(1 for a in task.actions if a.name == "move") == 48
        assert sum(1 for a in task.actions if a.name == "push") == 64

    def test_statics_are_derived_from_the_effects_not_declared(self, task):
        """`adj` is static because no action touches it -- read off the domain,
        not asserted by a flag."""
        assert task.static_predicates == ("adj",)
        assert task.fluent_predicates == ("at", "at-player", "clear")

    def test_statics_are_stripped_out_of_the_surviving_preconditions(self, task):
        push = task.action_named("(push c11 c12 c13 b1 right)")
        assert push is not None
        assert set(push.pre) == {Atom("at-player", ("c11",)),
                                 Atom("at", ("b1", "c12")),
                                 Atom("clear", ("c13",))}
        assert set(push.add) == {Atom("at-player", ("c12",)),
                                 Atom("at", ("b1", "c13")),
                                 Atom("clear", ("c11",))}
        assert Atom("at", ("b1", "c12")) in push.dele

    def test_a_wall_removes_the_instance_rather_than_blocking_it(self, task):
        """Pushing a box out of the top-left corner needs a pusher cell that is a
        wall, so `adj` is missing and grounding discards the instance. That is
        what makes a corner provable, and it is a fact about the *count*."""
        assert task.action_named("(push c11 c12 c13 b1 right)") is not None
        assert not [a for a in task.actions
                    if a.name == "push" and a.args[1] == "c11"]

    def test_the_goal_is_the_problem_file_s(self, task):
        assert set(task.goal) == {Atom("at", ("b1", "c42")), Atom("at", ("b2", "c13"))}

    def test_the_reachable_set_is_what_it_is(self, task):
        assert len(strips.reachable(task)) == 3352


class TestRefusals:
    """Everything outside the subset raises. Silently ignoring a construct would
    ground a different task than the file describes."""

    def _domain(self, body):
        return ("(define (domain d) (:requirements :strips :typing) (:types cell)"
                " (:predicates (p ?c - cell) (q ?c - cell)) " + body + ")")

    def _problem(self, goal="(p c1)"):
        return ("(define (problem x) (:domain d) (:objects c1 c2 - cell)"
                " (:init (p c1)) (:goal %s))" % goal)

    def test_a_disjunctive_precondition(self):
        with pytest.raises(StripsError) as exc:
            strips.ground(self._domain(
                "(:action a :parameters (?c - cell) :precondition (or (p ?c) (q ?c))"
                " :effect (q ?c))"), self._problem())
        assert "or" in str(exc.value)

    def test_a_negative_precondition(self):
        with pytest.raises(StripsError) as exc:
            strips.ground(self._domain(
                "(:action a :parameters (?c - cell) :precondition (not (p ?c))"
                " :effect (q ?c))"), self._problem())
        assert "negative" in str(exc.value)

    def test_an_untyped_parameter(self):
        with pytest.raises(StripsError) as exc:
            strips.ground(self._domain(
                "(:action a :parameters (?c) :precondition (p ?c) :effect (q ?c))"),
                self._problem())
        assert "untyped" in str(exc.value).lower()

    def test_an_undeclared_predicate(self):
        with pytest.raises(StripsError) as exc:
            strips.ground(self._domain(
                "(:action a :parameters (?c - cell) :precondition (r ?c)"
                " :effect (q ?c))"), self._problem())
        assert "undeclared predicate" in str(exc.value)

    def test_the_wrong_arity(self):
        with pytest.raises(StripsError) as exc:
            strips.ground(self._domain(
                "(:action a :parameters (?c ?d - cell) :precondition (p ?c ?d)"
                " :effect (q ?c))"), self._problem())
        assert "argument" in str(exc.value)

    def test_a_problem_for_another_domain(self):
        with pytest.raises(StripsError) as exc:
            strips.ground(
                self._domain("(:action a :parameters (?c - cell)"
                             " :precondition (p ?c) :effect (q ?c))"),
                self._problem().replace("(:domain d)", "(:domain other)"))
        assert "declares domain" in str(exc.value)

    def test_a_goal_over_a_static_predicate(self):
        """It is either trivially true or unachievable, and the reader will not
        guess which."""
        with pytest.raises(StripsError) as exc:
            strips.ground(
                self._domain("(:action a :parameters (?c - cell)"
                             " :precondition (p ?c) :effect (q ?c))"),
                self._problem(goal="(p c1)"))
        assert "static" in str(exc.value)

    def test_unbalanced_parentheses(self):
        with pytest.raises(StripsError):
            strips.parse_sexp("(define (domain d)")


class TestAtomRendering:
    def test_the_producer_s_rendering_round_trips(self):
        assert str(Atom.parse("at(b1,c12)")) == "at(b1,c12)"
        assert Atom.parse("at(b1,c12)") == Atom("at", ("b1", "c12"))
        assert Atom.parse("at-player(c11)") == Atom("at-player", ("c11",))

    def test_a_malformed_rendering_raises(self):
        with pytest.raises(StripsError):
            Atom.parse("at(b1,)")
