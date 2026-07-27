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

def test_refuses_goals_the_certificate_does_not_cover(peg, cert):
    """`lp_potential` is sound but incomplete. Three of the five single-peg
    goals on this board admit no linear pagoda at all, and the generator must
    say so rather than emit a theorem that means less than it reads.
    """
    ast, problem = peg
    doc = {
        "name": "peg5-any-single", "n_pos": 5, "background": 0,
        "objects": [{"name": f"Peg_{i}", "type": "Peg", "pos": i, "color": 1}
                    for i in (0, 1, 3, 4)],
        "weights": {"w": cert.weights},
        "goal_states": ["10000", "01000", "00100", "00010", "00001"],
    }
    with pytest.raises(CertificateGapError) as exc:
        generate_lean(ast, from_json(doc), cert)
    message = str(exc.value)
    for uncovered in ("10000", "00100", "00001"):
        assert uncovered in message
    assert "incompleteness" in message


def test_refuses_a_pagoda_invariant_with_no_certificate(peg):
    ast, problem = peg
    with pytest.raises(LeanGenError) as exc:
        generate_lean(ast, problem, certificate=None)
    assert "will not invent them" in str(exc.value)


def test_refuses_weights_that_disagree_with_the_certificate(peg, cert):
    ast, problem = peg
    problem.weights["w"] = [0, 0, 0, 0, 0]
    with pytest.raises(LeanGenError) as exc:
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
