"""Consuming an `ic3_pdr` separating invariant.

E-06 was discharged by exhausting the reachable set, which works because that
set has five states and does not survive a larger board. `ic3_pdr` is the engine
that exists because `lp_potential` is infeasible on some unsolvable
configurations, and consuming its certificate buys a proof whose size tracks the
**invariant** rather than the state space.

The certificate under test is transcribed from the candidate row `engine-rig`
has already published (`artifacts/candidates.jsonl`), not invented here, and not
written into that track's tree — the emitting half of this interop is theirs.
Every obligation is re-derived on this side regardless.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from theory_compiler.certificate import CertificateError
from theory_compiler.generators.gen_lean import (
    CertificateGapError, LeanGenError, generate_lean,
)
from theory_compiler.ic3_certificate import (
    SCHEMA, InductiveInvariantCertificate, apply_move, covers, legal,
    load_ic3_certificate, recheck,
)
from theory_compiler.parser.theory_parser import parse_theory
from theory_compiler.problem import load_problem

FIXTURES = Path(__file__).parent / "fixtures"
CERT = FIXTURES / "ic3_peg4_0111_to_0100.json"
REPO = Path(__file__).resolve().parents[2]

LEAN = shutil.which("lean")
needs_lean = pytest.mark.skipif(LEAN is None, reason="lean is not on PATH")


@pytest.fixture
def cert():
    return load_ic3_certificate(str(CERT))


@pytest.fixture
def peg4():
    ast = parse_theory((FIXTURES / "peg4_theory.dsl").read_text(encoding="utf-8"))
    return ast, load_problem(str(FIXTURES / "peg4_problem.json"))


def mutated(**changes):
    """The fixture certificate with fields replaced, written to a temp file."""
    import tempfile
    doc = json.loads(CERT.read_text(encoding="utf-8"))
    doc.update(changes)
    path = Path(tempfile.mkdtemp()) / "cert.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    return str(path)


def run_lean(source: str, tmp_path: Path) -> str:
    target = tmp_path / "Theory.lean"
    target.write_text(source, encoding="utf-8", newline="\n")
    shutil.copy(REPO / "theory-compiler" / "lean" / "lean-toolchain", tmp_path)
    result = subprocess.run([LEAN, str(target)], cwd=str(tmp_path),
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            timeout=600)
    output = result.stdout.decode("utf-8", errors="replace")
    assert result.returncode == 0, f"lean failed:\n{output}"
    return output


# ------------------------------------------------------ the certificate itself

class TestReader:
    def test_the_fixture_loads_and_re_verifies(self, cert):
        assert cert.n_pos == 4
        assert cert.initial_state == "0111"
        assert cert.goal_states == ["0100"]
        assert cert.clause_text() == "(!pos1 | pos2) & (pos1 | !pos2)"

    def test_the_invariant_separates_start_from_goal(self, cert):
        assert cert.holds("0111")
        assert not cert.holds("0100")

    def test_another_schema_is_refused_rather_than_guessed_at(self):
        with pytest.raises(CertificateError) as exc:
            load_ic3_certificate(mutated(schema="lp_potential/pagoda_certificate@1"))
        assert "one schema" in str(exc.value)

    def test_the_move_geometry_is_re_derived_not_read(self, cert):
        """An invariant is inductive only w.r.t. a transition relation, so the
        relation must not come from the document asserting the induction."""
        assert cert.moves() == [(0, 1, 2), (1, 2, 3), (2, 1, 0), (3, 2, 1)]
        assert "moves" not in json.loads(CERT.read_text(encoding="utf-8"))

    def test_the_obligations_are_recomputed_over_the_whole_state_space(self, cert):
        """Independently, here, rather than read off the candidate row."""
        states = cert.states()
        assert len(states) == 16
        assert sum(1 for s in states if cert.holds(s)) == 8
        escapes = [(s, m) for s in states for m in cert.moves()
                   if cert.holds(s) and legal(s, m) and not cert.holds(apply_move(s, m))]
        assert escapes == []


class TestRefusals:
    """The producer's `conditions` block is its opinion; these are the checks."""

    def test_an_invariant_that_fails_at_the_start_is_refused(self):
        with pytest.raises(CertificateError) as exc:
            load_ic3_certificate(mutated(initial_state="0100"))
        assert "inv_init fails" in str(exc.value)

    def test_a_non_inductive_invariant_is_refused_with_a_witness(self):
        """Drop one clause: `pos1 -> pos2` alone is not closed under moves."""
        one_clause = [[["pos1", False], ["pos2", True]]]
        with pytest.raises(CertificateError) as exc:
            load_ic3_certificate(mutated(cnf=one_clause))
        message = str(exc.value)
        assert "inv_closed fails" in message
        assert "jump(" in message, "a refusal without a witness is just a complaint"

    def test_an_invariant_that_admits_the_goal_is_refused(self):
        """`pos0 -> pos0` is inductive and true everywhere, and separates
        nothing — the degenerate way to pass two obligations out of three."""
        trivial = [[["pos0", False], ["pos0", True]]]
        with pytest.raises(CertificateError) as exc:
            load_ic3_certificate(mutated(cnf=trivial))
        assert "goal_break fails" in str(exc.value)

    def test_an_empty_clause_set_is_refused(self):
        with pytest.raises(CertificateError) as exc:
            load_ic3_certificate(mutated(cnf=[]))
        assert "no clauses" in str(exc.value)

    def test_an_empty_clause_is_refused(self):
        with pytest.raises(CertificateError) as exc:
            load_ic3_certificate(mutated(cnf=[[]]))
        assert "empty clause" in str(exc.value)

    def test_an_undeclared_variable_is_refused(self):
        with pytest.raises(CertificateError) as exc:
            load_ic3_certificate(mutated(cnf=[[["pos9", True]]]))
        assert "not one of the certificate's declared variables" in str(exc.value)

    def test_a_bitstring_of_the_wrong_length_is_refused(self):
        with pytest.raises(CertificateError) as exc:
            load_ic3_certificate(mutated(initial_state="011"))
        assert "not 4 positions long" in str(exc.value)

    def test_covers_reports_what_the_certificate_does_not_exclude(self, cert):
        assert covers(cert, ["0100"]) == []
        assert covers(cert, ["0100", "0001"]) == ["0001"]


# ------------------------------------------------------------ the Lean route

class TestDevelopment:
    def test_the_clauses_reach_the_lean_file(self, peg4, cert):
        ast, problem = peg4
        source = generate_lean(ast, problem, cert)
        assert "def Inv (s : St) : Bool" in source
        assert "(!s.p1 || s.p2) && (s.p1 || !s.p2)" in source
        assert "sorry" not in source and "native_decide" not in source
        assert cert.produced_by in source

    def test_the_algebraic_form_splits_on_moves_not_on_the_board(self, peg4, cert):
        """The whole reason to consume this rather than exhaust.

        The inner split is over the cells the *invariant* names — two of four
        here, which saves little; on a board where the invariant names two cells
        out of thirty-three it is the entire difference.
        """
        ast, problem = peg4
        source = generate_lean(ast, problem, cert, proof="algebraic")
        assert "cases m <;>" in source
        # A precise count, not a substring one: `rcases hg` in `unsolvable`
        # also contains "cases h", and the first version of this assertion
        # counted it.
        import re as _re
        splits = _re.findall(r"cases h\d+ : s\.p(\d+)", source)
        assert sorted(splits) == ["1", "2"], (
            "the inner split must be over the invariant's variables (p1, p2), "
            "not over the board; got %r" % (splits,))

    def test_a_certificate_with_no_declared_invariant_is_refused(self, cert):
        """The peg5 manual declares `pagoda(w)`, not `cnf(...)`."""
        ast = parse_theory((FIXTURES / "peg_theory.dsl").read_text(encoding="utf-8"))
        problem = load_problem(str(FIXTURES / "peg5_problem.json"))
        with pytest.raises(LeanGenError) as exc:
            generate_lean(ast, problem, cert)
        assert "declares no `cnf(...)` invariant" in str(exc.value)

    def test_goals_outside_the_certificate_are_refused(self, peg4, cert):
        """`ic3_pdr` is a different method, not an omniscient one."""
        ast, problem = peg4
        problem.goal_states = ["0100", "1000"]
        with pytest.raises(CertificateGapError) as exc:
            generate_lean(ast, problem, cert)
        assert "1000" in str(exc.value)

    def test_a_certificate_about_another_start_is_refused(self, peg4, cert):
        ast, problem = peg4
        problem.instances[0].pos = (0,)
        with pytest.raises(LeanGenError) as exc:
            generate_lean(ast, problem, cert)
        assert "the level starts at" in str(exc.value)


@needs_lean
class TestCompiles:
    def test_computational_form_has_an_empty_axiom_set(self, peg4, cert, tmp_path):
        ast, problem = peg4
        output = run_lean(generate_lean(ast, problem, cert,
                                        proof="computational"), tmp_path)
        for name in ("inv_init", "inv_closed", "inv_all", "unsolvable"):
            assert f"'{name}' does not depend on any axioms" in output, output
        assert "sorryAx" not in output

    def test_algebraic_form_costs_exactly_propext(self, peg4, cert, tmp_path):
        """Cheaper than the algebraic pagoda route, which also pays `Quot.sound`.

        `simp` rewrites propositions, so `propext` is unavoidable for any proof
        that reasons rather than computes. What must never appear is `sorryAx`
        or `Lean.ofReduceBool`.
        """
        ast, problem = peg4
        output = run_lean(generate_lean(ast, problem, cert,
                                        proof="algebraic"), tmp_path)
        assert "'inv_closed' depends on axioms: [propext]" in output, output
        assert "sorryAx" not in output
        assert "ofReduceBool" not in output
        assert "Classical.choice" not in output

    def test_several_goal_states_compile(self, peg4, cert, tmp_path):
        """The single-goal fixture does not exercise the `rcases` alternation."""
        two = load_ic3_certificate(mutated(goal_states=["0100", "0010"]))
        ast, problem = peg4
        problem.goal_states = ["0100", "0010"]
        output = run_lean(generate_lean(ast, problem, two), tmp_path)
        assert "'unsolvable' does not depend on any axioms" in output, output


class TestProvenance:
    def test_the_fixture_matches_the_row_engine_rig_published(self):
        """Transcribed, not invented — and checkable against their stream.

        If engine-rig's candidate stream ever disagrees with this fixture, one
        of the two moved and the interop is not what this test suite claims.
        """
        stream = REPO / "engine-rig" / "artifacts" / "candidates.jsonl"
        if not stream.exists():
            pytest.skip("engine-rig's candidate stream is not present")
        rows = [json.loads(line) for line in
                stream.read_text(encoding="utf-8").splitlines() if line.strip()]
        published = [r for r in rows
                     if r.get("payload", {}).get("producer") == "ic3_pdr"
                     and r["kind"] == "invariant"]
        assert len(published) == 1
        payload = published[0]["payload"]
        doc = json.loads(CERT.read_text(encoding="utf-8"))
        assert doc["cnf"] == payload["cnf"]
        assert doc["initial_state"] == payload["initial"]
        assert doc["goal_states"] == payload["goal_states"]
        assert doc["variables"] == payload["variables"]
        assert doc["provenance"]["candidate_id"] == published[0]["id"]

    def test_the_fixture_lives_on_this_side_of_the_boundary(self):
        """The emitting half belongs to engine-rig and is not written here."""
        assert CERT.parent == FIXTURES
        interop = REPO / "engine-rig" / "interop" / "certificates"
        assert not list(interop.glob("ic3*")), (
            "an ic3 certificate has appeared in engine-rig's tree; this track "
            "does not write there and the schema is still a draft")

    def test_nothing_here_imports_engine_rig(self):
        source = (Path(__file__).parent.parent / "src" / "theory_compiler"
                  / "ic3_certificate.py").read_text(encoding="utf-8")
        assert "engine_rig" not in source and "engine-rig" not in source.replace(
            "engine-rig/engines/ic3_pdr", "").replace(
            "`engine-rig`", "").replace("engine-rig's", "")
