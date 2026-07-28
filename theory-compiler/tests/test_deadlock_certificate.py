"""Consuming a `deadlock_carver` conditional-unsolvability theorem.

The third certificate schema, and the first that is conditional: it says nothing
about the level as a whole. `sokoban-open4far` is in fact **solvable**, which is
what makes it the right fixture — a dead-region theorem proved on a level that
was lost anyway would be true and would demonstrate nothing.

Both closure forms are under test. `at(b1,c11)` is the degenerate one, where no
ground action deletes a pattern atom at all because grounding already discarded
the pushes a wall makes impossible; `at(b1,c12) AND at(b2,c13)` is the one that
needs the mutex reasoning, where four pushes exist on paper and each is blocked
by the other box.

The certificates are transcribed from candidate rows `engine-rig` has published;
the emitting half of the schema is theirs and is not written here. Every
obligation is re-derived on this side regardless, and the transcription itself is
re-run below so the fixture cannot drift away from the row.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from theory_compiler import deadlock_certificate as dc
from theory_compiler import strips, strips_encoding
from theory_compiler.certificate import CertificateError
from theory_compiler.strips import Atom
from theory_compiler.strips_encoding import EncodingError, PositionalEncoding

FIXTURES = Path(__file__).parent / "fixtures"
STRIPS_DIR = FIXTURES / "strips"
PAIR = FIXTURES / "deadlock_open4far_b1c12_b2c13.json"
CORNER = FIXTURES / "deadlock_open4far_b1c11.json"
REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def task():
    return strips.load_task(str(STRIPS_DIR / "sokoban_domain.pddl"),
                            str(STRIPS_DIR / "sokoban_open4far.pddl"))


@pytest.fixture(scope="module")
def encoding(task):
    return PositionalEncoding(task)


@pytest.fixture(scope="module")
def pair(task, encoding):
    return dc.load_deadlock_certificate(str(PAIR), task, encoding)


@pytest.fixture(scope="module")
def corner(task, encoding):
    return dc.load_deadlock_certificate(str(CORNER), task, encoding)


def mutated(source: Path, **changes):
    doc = json.loads(source.read_text(encoding="utf-8"))
    doc.update(changes)
    path = Path(tempfile.mkdtemp()) / "cert.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    return str(path)


# ------------------------------------------------------------------ the reader

class TestReader:
    def test_both_fixtures_load_and_re_verify(self, pair, corner):
        assert pair.pattern == (Atom("at", ("b1", "c12")), Atom("at", ("b2", "c13")))
        assert pair.closure == "deleting_actions_blocked"
        assert corner.pattern == (Atom("at", ("b1", "c11")),)
        assert corner.closure == "no_deleting_action"

    def test_the_pattern_text_is_rendered_here_not_believed(self, pair):
        assert pair.pattern_text == "at(b1,c12) AND at(b2,c13)"

    def test_a_pattern_text_that_lies_about_the_pattern_is_refused(self, task):
        with pytest.raises(CertificateError) as exc:
            dc.load_deadlock_certificate(
                mutated(PAIR, pattern_text="at(b1,c11)"), task)
        assert "pattern_text" in str(exc.value)

    def test_another_schema_is_refused_rather_than_guessed_at(self, task):
        with pytest.raises(CertificateError) as exc:
            dc.load_deadlock_certificate(
                mutated(PAIR, schema="ic3_pdr/inductive_invariant_certificate@1"), task)
        assert "one schema" in str(exc.value)

    def test_an_empty_pattern_is_refused(self, task):
        """It holds everywhere, so the theorem would call solvable states dead."""
        with pytest.raises(CertificateError) as exc:
            dc.load_deadlock_certificate(mutated(PAIR, pattern=[]), task)
        assert "empty" in str(exc.value)

    def test_the_certificate_supplies_no_transition_relation(self):
        """The same discipline `ic3_certificate` states as "no `moves` field".

        A certificate that carried its own action set would be closed under an
        action set of its own choosing.
        """
        for path in (PAIR, CORNER):
            doc = json.loads(path.read_text(encoding="utf-8"))
            assert "actions" not in doc and "moves" not in doc
            assert "transition" not in json.dumps(doc)


# ------------------------------------------------------- the two obligations

class TestObligations:
    def test_closure_is_recomputed_over_the_well_formed_space(self, pair, encoding):
        pattern = list(pair.pattern)
        holding = [s for s in encoding.states() if encoding.holds(s, pattern)]
        assert len(holding) == 14
        for state in holding:
            for action in encoding.task.actions:
                if encoding.legal(state, action):
                    assert encoding.holds(encoding.apply(state, action), pattern)

    def test_a_pattern_you_can_leave_is_refused(self, task, encoding):
        """One box shifted one cell and the region is no longer closed."""
        with pytest.raises(CertificateError) as exc:
            dc.recheck(dc.DeadlockCertificate(
                claim="tampered", domain=task.domain, problem=task.problem,
                pattern=[Atom("at", ("b1", "c22")), Atom("at", ("b2", "c23"))],
                closure="deleting_actions_blocked", n_deleting_actions=-1,
                blocked_actions=[], goal_conflict=None, coverage="",
                produced_by="test", provenance="test"), encoding)
        assert "closure fails" in str(exc.value)
        assert "not a dead region" in str(exc.value)

    def test_a_pattern_that_admits_a_win_is_refused(self):
        """Calling a win dead is the one mistake that matters, so the second
        obligation gets its own fixture rather than riding on the first.

        Same board, same actions, same (closed) pattern — only the goal moved,
        onto the pattern. Closure still holds; the pattern now contains wins.
        """
        problem = (STRIPS_DIR / "sokoban_open4far.pddl").read_text(encoding="utf-8")
        moved = problem.replace("(:goal (and (at b1 c42) (at b2 c13)))",
                                "(:goal (and (at b1 c12) (at b2 c13)))")
        assert moved != problem
        other = strips.ground(
            (STRIPS_DIR / "sokoban_domain.pddl").read_text(encoding="utf-8"), moved)
        with pytest.raises(CertificateError) as exc:
            dc.recheck(dc.DeadlockCertificate(
                claim="tampered", domain=other.domain, problem=other.problem,
                pattern=[Atom("at", ("b1", "c12")), Atom("at", ("b2", "c13"))],
                closure="deleting_actions_blocked", n_deleting_actions=-1,
                blocked_actions=[], goal_conflict=None, coverage="",
                produced_by="test", provenance="test"),
                PositionalEncoding(other))
        assert "goal exclusion fails" in str(exc.value)

    def test_a_pattern_nothing_satisfies_is_refused(self, task, encoding):
        """Every obligation passes vacuously and the axiom set prints empty. The
        repository has met that failure mode once already."""
        with pytest.raises(CertificateError) as exc:
            dc.recheck(dc.DeadlockCertificate(
                claim="vacuous", domain=task.domain, problem=task.problem,
                pattern=[Atom("at", ("b1", "c11")), Atom("at", ("b2", "c11"))],
                closure="no_deleting_action", n_deleting_actions=-1,
                blocked_actions=[], goal_conflict=None, coverage="",
                produced_by="test", provenance="test"), encoding)
        assert "never met" in str(exc.value)

    def test_the_obligations_do_not_consult_the_producer_s_bookkeeping(self, task, encoding):
        """`recheck` reaches the same verdict with every self-report stripped."""
        doc = json.loads(PAIR.read_text(encoding="utf-8"))
        bare = dc.DeadlockCertificate(
            claim="", domain=task.domain, problem=task.problem,
            pattern=[Atom(a[0], tuple(a[1:])) for a in doc["pattern"]],
            closure="deleting_actions_blocked", n_deleting_actions=-1,
            blocked_actions=[], goal_conflict=None, coverage="",
            produced_by="", provenance="")
        dc.recheck(bare, encoding)


# -------------------------------------------------------------- cross-checking

class TestCrossCheck:
    def test_the_action_counts_have_to_agree(self, task):
        with pytest.raises(CertificateError) as exc:
            dc.load_deadlock_certificate(mutated(PAIR, coverage="96/96"), task)
        assert "same action set" in str(exc.value)

    def test_a_partial_examination_is_not_a_closure_claim(self, task):
        with pytest.raises(CertificateError) as exc:
            dc.load_deadlock_certificate(mutated(PAIR, coverage="100/112"), task)
        assert "skipped" in str(exc.value)

    def test_the_deleting_action_count_is_counted_here_too(self, task):
        with pytest.raises(CertificateError) as exc:
            dc.load_deadlock_certificate(mutated(PAIR, n_deleting_actions=3), task)
        assert "deleting a pattern atom" in str(exc.value)

    def test_no_deleting_action_is_checked_not_believed(self, task):
        with pytest.raises(CertificateError) as exc:
            dc.load_deadlock_certificate(
                mutated(PAIR, closure="no_deleting_action", n_deleting_actions=-1),
                task)
        assert "grounds 4 that do" in str(exc.value)

    def test_a_blocked_action_this_track_never_grounded(self, task):
        blocked = json.loads(PAIR.read_text(encoding="utf-8"))["blocked_actions"]
        blocked[0] = dict(blocked[0], action="(push c11 c12 c13 b9 right)")
        with pytest.raises(CertificateError) as exc:
            dc.load_deadlock_certificate(mutated(PAIR, blocked_actions=blocked), task)
        assert "does not contain" in str(exc.value)

    def test_a_deleting_action_left_standing(self, task):
        blocked = json.loads(PAIR.read_text(encoding="utf-8"))["blocked_actions"][:2]
        with pytest.raises(CertificateError) as exc:
            dc.load_deadlock_certificate(mutated(PAIR, blocked_actions=blocked), task)
        assert "left standing" in str(exc.value)

    def test_a_certificate_about_another_problem(self, task):
        with pytest.raises(CertificateError) as exc:
            dc.load_deadlock_certificate(mutated(PAIR, problem="sokoban-open4"), task)
        assert "the task is" in str(exc.value)

    def test_a_goal_conflict_citing_an_atom_that_is_not_in_the_goal(self, task):
        with pytest.raises(CertificateError) as exc:
            dc.load_deadlock_certificate(
                mutated(PAIR, goal_conflict={"goal_atom": "at(b1,c44)"}), task)
        assert "not in this" in str(exc.value)

    def test_the_four_blocked_pushes_are_the_four_we_ground(self, pair, task):
        ours = {str(a) for a in pair.deleting_actions(task)}
        theirs = {b["action"].strip("()") for b in pair.blocked_actions}
        assert {a.strip("()") for a in ours} == theirs


# --------------------------------------------------------------- transcription

class TestTranscription:
    def test_the_fixtures_still_match_the_candidate_rows(self):
        """Re-runs the transcription and fails on any drift. Without this the
        fixture could quietly become something the producer never said."""
        result = subprocess.run(
            [sys.executable, "-m", "tools.transcribe_deadlock_certificates"],
            cwd=str(Path(__file__).parents[1]), stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, timeout=120)
        assert result.returncode == 0, result.stdout.decode("utf-8", "replace")

    def test_the_fixtures_say_they_are_transcriptions(self):
        for path in (PAIR, CORNER):
            doc = json.loads(path.read_text(encoding="utf-8"))
            assert doc["provenance"]["source"] == "engine-rig/artifacts/candidates.jsonl"
            assert doc["provenance"]["row_id"]

    def test_nothing_is_written_into_the_other_track_s_tree(self):
        interop = REPO / "engine-rig" / "interop" / "certificates"
        if interop.exists():
            assert not list(interop.glob("*deadlock*"))

    def test_the_reader_imports_nothing_from_engine_rig(self):
        for name in ("deadlock_certificate.py", "strips.py", "strips_encoding.py"):
            source = (Path(__file__).parents[1] / "src" / "theory_compiler"
                      / name).read_text(encoding="utf-8")
            for line in source.splitlines():
                assert not line.strip().startswith(("import engine", "from engine"))


# ------------------------------------------------------------------ the report

class TestBite:
    def test_the_theorem_rules_out_reachable_states_of_a_winnable_level(
            self, pair, corner, task, encoding):
        """"True" and "worth having" are different statements, so the consumer
        keeps its own version of the producer's node account."""
        reachable = [encoding.decode(a) for a in strips.reachable(task)]
        pair_report = dc.bite(pair, encoding, reachable)
        corner_report = dc.bite(corner, encoding, reachable)
        assert pair_report["reachable_states"] == 3352
        assert pair_report["reachable_states_covered"] == 14
        assert corner_report["reachable_states_covered"] == 210
        assert pair_report["goal_reachable"] == 1


# ---------------------------------------------------------------- the encoding

class TestEncoding:
    def test_the_encoding_is_checked_against_the_task_by_exhaustion(self, encoding):
        stats = strips_encoding.verify(encoding)
        assert stats["encodable_states"] == 3360
        assert stats["reachable_states"] == 3352
        assert stats["pairs_checked"] == 3360 * 112

    def test_degenerate_states_have_no_atom_set_counterpart(self, encoding):
        """Which is why well-formedness travels into the theorem as a hypothesis
        instead of being quietly assumed."""
        degenerate = ("c12", "c12", "c13")
        assert not encoding.well_formed(degenerate)
        atoms = encoding.atoms(degenerate)
        assert Atom("clear", ("c12",)) not in atoms
        escaped = [a for a in encoding.task.actions
                   if encoding.legal(degenerate, a)
                   and not encoding.holds(encoding.apply(degenerate, a),
                                          [Atom("at", ("b1", "c12")),
                                           Atom("at", ("b2", "c13"))])]
        assert escaped, ("closure would be false without well-formedness; if this "
                         "ever becomes empty the hypothesis can be dropped")

    def test_an_unfamiliar_signature_is_refused_rather_than_approximated(self):
        domain = ("(define (domain d) (:requirements :strips :typing) (:types cell)"
                  " (:predicates (p ?c - cell) (q ?c - cell))"
                  " (:action a :parameters (?c - cell) :precondition (p ?c)"
                  " :effect (and (q ?c) (not (p ?c)))))")
        problem = ("(define (problem x) (:domain d) (:objects c1 - cell)"
                   " (:init (p c1)) (:goal (q c1)))")
        with pytest.raises(EncodingError) as exc:
            PositionalEncoding(strips.ground(domain, problem))
        assert "refuses rather than approximating" in str(exc.value)

    def test_the_level_is_winnable_so_the_theorem_is_conditional(self, encoding):
        plan = strips_encoding.shortest_plan(encoding)
        assert plan is not None and len(plan) == 11
        state = encoding.initial()
        for before, action in plan:
            assert before == state
            assert encoding.legal(state, action)
            state = encoding.apply(state, action)
        assert encoding.is_goal(state)
