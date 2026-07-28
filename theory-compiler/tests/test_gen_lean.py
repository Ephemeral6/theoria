"""theory.lean generator — A1 acceptance.

The M8 rehearsal asserted `"allReachable" in code`, which pinned the *BFS
implementation* rather than the claim. Those assertions are gone on purpose:
the peg world no longer gets a proof by enumerating its reachable set, it gets
one from the LP certificate's pagoda weights. What must not regress is the
product — a Lean file that compiles, contains no `sorry`, uses no
`native_decide`, and proves the manual's `unsolvable` — and that is what these
tests check, by running `lean` on the output and reading `#print axioms`.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from theory_compiler.certificate import load_certificate
from theory_compiler.generators.gen_lean import (
    CertificateGapError, LeanGenError, generate_lean,
)
from theory_compiler.ir import IRError
from theory_compiler.parser.theory_parser import parse_theory
from theory_compiler.problem import from_json, load_problem

FIXTURES = Path(__file__).parent / "fixtures"
REPO = Path(__file__).resolve().parents[2]
CERTS = REPO / "engine-rig" / "interop" / "certificates"
CERT_00010 = CERTS / "pagoda_5_11011_to_00010.json"

LEAN = shutil.which("lean")
needs_lean = pytest.mark.skipif(LEAN is None, reason="lean is not on PATH")


@pytest.fixture
def peg():
    ast = parse_theory((FIXTURES / "peg_theory.dsl").read_text(encoding="utf-8"))
    return ast, load_problem(str(FIXTURES / "peg5_problem.json"))


@pytest.fixture
def cert():
    return load_certificate(str(CERT_00010))


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


# ------------------------------------------------------------------ structure

@pytest.mark.parametrize("mode", ["computational", "algebraic"])
def test_weights_come_from_the_certificate(peg, cert, mode):
    ast, problem = peg
    src = generate_lean(ast, problem, cert, proof=mode)
    assert "sorry" not in src
    assert "native_decide" not in src
    assert "theorem unsolvable" in src
    # The weight vector in the Lean file is the certificate's, position by
    # position. This is the whole difference between A1 and the M8 rehearsal,
    # where the weights were hand-computed constants.
    for i, weight in enumerate(cert.weights):
        assert f"| .p{i} => {weight}" in src
    assert cert.produced_by in src


def test_move_geometry_is_recovered_from_the_predictor(peg, cert):
    """The Lean `Move` type must match what the generated Python actually does."""
    ast, problem = peg
    src = generate_lean(ast, problem, cert)
    for src_i, over, dst in cert.moves():
        assert f"jump({src_i},{over},{dst})" in src


# ------------------------------------------------------- the acceptance itself

@needs_lean
def test_computational_proof_has_no_axioms(peg, cert, tmp_path):
    """A1: LP weights -> a closed Lean lemma, no sorry, empty axiom set."""
    ast, problem = peg
    output = run_lean(generate_lean(ast, problem, cert,
                                    proof="computational"), tmp_path)
    assert "sorryAx" not in output
    for name in ("inv_init", "inv_closed", "inv_all", "unsolvable"):
        assert f"'{name}' does not depend on any axioms" in output, output


@needs_lean
def test_algebraic_proof_costs_exactly_two_axioms(peg, cert, tmp_path):
    """The algebraic route is linear in the board and pays for it, but only in
    Lean's two structural axioms — never in `sorryAx` or `Lean.ofReduceBool`.

    `propext` is unavoidable here: in Lean 4.9 every core `Int` lemma is proved
    with it, so any proof that reasons rather than computes inherits it.
    """
    ast, problem = peg
    output = run_lean(generate_lean(ast, problem, cert,
                                    proof="algebraic"), tmp_path)
    assert "sorryAx" not in output
    assert "ofReduceBool" not in output
    assert "Classical.choice" not in output
    assert "'unsolvable' depends on axioms: [propext, Quot.sound]" in output, output


@needs_lean
def test_algebraic_proof_is_smaller_than_the_state_space(peg, cert, tmp_path):
    """The point of the pagoda route: the proof scales with the board, not with
    the reachable set. `inv_closed` splits on moves, of which there are 2(n-2).
    """
    ast, problem = peg
    src = generate_lean(ast, problem, cert, proof="algebraic")
    assert src.count("  | m") == len(cert.moves())


# ---------------------------------------------------------------- overclaiming

def test_goals_the_certificate_does_not_cover_go_to_the_other_method(peg, cert):
    """This used to assert a refusal, and the change is the point (E-06).

    `lp_potential` is sound but incomplete: three of the five single-peg goals
    on this board admit no linear pagoda at all. While the pagoda route was the
    only route, refusing was the honest answer — emitting `unsolvable` would
    have meant less than it read. It is no longer the only route, so refusing
    would now be *withholding a proof the compiler can produce*, which is its
    own kind of dishonesty.

    What must not regress is that the generator never emits a claim no method
    licenses; `test_an_unenumerable_world_is_still_refused` is that assertion
    now, and it is the one that keeps this from being a quiet weakening.
    """
    ast, _problem = peg
    doc = {
        "name": "peg5-any-single", "n_pos": 5, "background": 0,
        "objects": [{"name": f"Peg_{i}", "type": "Peg", "pos": i, "color": 1}
                    for i in (0, 1, 3, 4)],
        "weights": {"w": cert.weights},
        "goal_states": ["10000", "01000", "00100", "00010", "00001"],
    }
    source = generate_lean(ast, from_json(doc), cert)
    assert "theorem unsolvable" in source
    for uncovered in ("10000", "00100", "00001"):
        assert uncovered in source, "the header must name what it could not cover"
    assert "exhausting the" in source


def test_refuses_a_pagoda_invariant_with_no_certificate(peg):
    ast, problem = peg
    with pytest.raises(LeanGenError) as exc:
        generate_lean(ast, problem, certificate=None)
    assert "will not invent them" in str(exc.value)


def test_refuses_weights_that_disagree_with_the_certificate(peg, cert):
    """Still refused, now one layer down.

    The check moved from this backend into `build_ir`, so it fires for every
    form rather than only for the one that happened to hold the certificate —
    hence `IRError` and not `LeanGenError`. The message is unchanged.
    """
    ast, problem = peg
    problem.weights["w"] = [0, 0, 0, 0, 0]
    with pytest.raises(IRError) as exc:
        generate_lean(ast, problem, cert)
    assert "stale" in str(exc.value)


# ------------------------------------------------------- the enumerative route

def test_enumerative_route_for_a_manual_with_no_potential():
    """A0's manual declares no `pagoda(...)`, so it gets the other development.

    It is also a *solvable* world, and the generator reports that instead of
    manufacturing an unsolvability theorem.
    """
    ast = parse_theory((FIXTURES / "cart_theory.dsl").read_text(encoding="utf-8"))
    problem = load_problem(str(FIXTURES / "cart_problem.json"))
    src = generate_lean(ast, problem)
    assert "sorry" not in src
    assert "native_decide" not in src
    assert "def step : St → Act → St" in src
    assert "goal_is_reachable" in src
    assert "theorem unsolvable" not in src


@needs_lean
def test_enumerative_route_compiles_axiom_free(tmp_path):
    ast = parse_theory((FIXTURES / "cart_theory.dsl").read_text(encoding="utf-8"))
    problem = load_problem(str(FIXTURES / "cart_problem.json"))
    output = run_lean(generate_lean(ast, problem), tmp_path)
    assert "sorryAx" not in output
    assert "does not depend on any axioms" in output


# ------------------------------------------------- more than one goal state

def _two_goal_certificate(cert):
    """A certificate may carry several goal states — `goal_states` is a list and
    the producer emits one `goal_break` witness per entry. None of the three
    certificates on disk uses more than one, so the multi-goal path would
    otherwise ship untested.

    Both `01000` and `00010` have potential 1 under these weights, so a single
    certificate excluding both is sound; this reconstructs it rather than
    asserting it, and `recheck` is what says the reconstruction holds.
    """
    from theory_compiler.certificate import PagodaCertificate, recheck
    two = PagodaCertificate(
        claim="unsolvable_11011_to_01000_or_00010", n_pos=5,
        initial_state="11011", goal_states=["01000", "00010"],
        weights=list(cert.weights), initial_potential=0,
        produced_by=cert.produced_by, path=cert.path)
    two.declared_witnesses = two.moves()
    recheck(two)
    return two


def _two_goal_problem(cert):
    return from_json({
        "name": "peg5-two-goals", "n_pos": 5, "background": 0,
        "objects": [{"name": f"Peg_{i}", "type": "Peg", "pos": i, "color": 1}
                    for i in (0, 1, 3, 4)],
        "weights": {"w": list(cert.weights)},
        "goal_states": ["01000", "00010"],
    })


@pytest.mark.parametrize("mode", ["computational", "algebraic"])
def test_several_goal_states_in_one_theorem(peg, cert, mode):
    ast, _ = peg
    two = _two_goal_certificate(cert)
    src = generate_lean(ast, _two_goal_problem(cert), two, proof=mode)
    assert "sorry" not in src
    assert _lean_bits("01000") in src and _lean_bits("00010") in src


def _lean_bits(bits: str) -> str:
    return "⟨%s⟩" % ", ".join("true" if b == "1" else "false" for b in bits)


@needs_lean
@pytest.mark.parametrize("mode", ["computational", "algebraic"])
def test_several_goal_states_still_compile(peg, cert, tmp_path, mode):
    ast, _ = peg
    two = _two_goal_certificate(cert)
    output = run_lean(generate_lean(ast, _two_goal_problem(cert), two,
                                    proof=mode), tmp_path)
    assert "sorryAx" not in output
    assert "'unsolvable'" in output


def test_the_committed_lean_artifact_is_not_stale():
    """`lean/TheoriaLean.lean` is tracked, generated, and nothing regenerates it
    on its own — so it drifts silently. It did: it sat at the M8 rehearsal's BFS
    enumeration long after the generator had moved to the pagoda argument, and
    a reader of the repository would have found a superseded proof presented as
    the current one. This test is the thing that would have caught it.
    """
    ast = parse_theory((FIXTURES / "peg_theory.dsl").read_text(encoding="utf-8"))
    problem = load_problem(str(FIXTURES / "peg5_problem.json"))
    expected = generate_lean(ast, problem, load_certificate(str(CERT_00010)),
                             proof="computational")
    committed = (REPO / "theory-compiler" / "lean" / "TheoriaLean.lean")
    actual = committed.read_text(encoding="utf-8")
    assert actual == expected, (
        "lean/TheoriaLean.lean is out of date. Regenerate it — see README."
    )


# ----------------------------------------------- E-06 · the second method

ANY_SINGLE_PEG = {
    "name": "peg5-any-single", "n_pos": 5, "background": 0,
    "objects": [{"name": f"Peg_{i}", "type": "Peg", "pos": i, "color": 1}
                for i in (0, 1, 3, 4)],
    "goal_states": ["10000", "01000", "00100", "00010", "00001"],
}


def test_the_uncovered_goals_are_closed_by_exhaustion(peg, cert):
    """E-06's proof half.

    `goal count(Peg, alive) = 1` was unproven for one revision: the certificate
    excludes one of the five single-peg terminals and `lp_potential` admits no
    linear pagoda for some of the rest, so the compiler refused. Refusing was
    right while there was one method. There are two, and exhausting the
    reachable set closes what the certificate cannot.
    """
    ast, _ = peg
    source = generate_lean(ast, from_json(ANY_SINGLE_PEG), cert)
    assert "theorem unsolvable" in source
    assert "theorem inv_all" in source
    assert "sorry" not in source and "native_decide" not in source


def test_the_two_methods_stay_attributed(peg, cert):
    """A blended claim would be worse than either half.

    A reader has to be able to see which goal each argument carried, and the
    file must not say more than is known: that a goal is *not covered by this
    certificate* is a fact about the certificate, while "no linear pagoda
    exists" is a fact about the method that only `lp_potential` can report.
    Conflating them would libel `01000`, which has a certificate of its own in
    `interop/`.
    """
    ast, _ = peg
    source = generate_lean(ast, from_json(ANY_SINGLE_PEG), cert)
    assert "not excluded by this certificate" in source
    assert "no linear pagoda function at all" not in source, (
        "the header claims non-existence of a pagoda for goals this "
        "certificate merely does not cover")
    assert "00010" in source and "excludes 1 of them algebraically" in source


def test_a_reachable_goal_is_refused_rather_than_proved(peg, cert):
    """The soundness edge: exhaustion must not 'prove' a false theorem."""
    doc = dict(ANY_SINGLE_PEG)
    doc["goal_states"] = ["11011"]          # the initial state itself
    with pytest.raises(LeanGenError) as exc:
        generate_lean(peg[0], from_json(doc), cert)
    assert "reachable" in str(exc.value)


def test_an_unenumerable_world_is_still_refused(peg, cert, monkeypatch):
    """The refusal stays for the case neither method reaches.

    Exhaustion is O(reachable set), so it discharges this configuration and not
    the method gap. A board whose reachable set is astronomical must come back
    as `CertificateGapError`, not as a file nobody can compile.
    """
    from theory_compiler.generators import gen_lean as module
    monkeypatch.setattr(module, "MAX_ENUMERATED_STATES", 2)
    with pytest.raises(CertificateGapError) as exc:
        generate_lean(peg[0], from_json(ANY_SINGLE_PEG), cert)
    message = str(exc.value)
    assert "exceeds 2 states" in message
    assert "no method it has can license" in message


@needs_lean
def test_the_hybrid_development_compiles_with_an_empty_axiom_set(peg, cert, tmp_path):
    """The claim is only worth what `lean` says about it."""
    ast, _ = peg
    output = run_lean(generate_lean(ast, from_json(ANY_SINGLE_PEG), cert), tmp_path)
    for name in ("inv_all", "unsolvable"):
        assert f"'{name}' does not depend on any axioms" in output, output
    assert "sorryAx" not in output
