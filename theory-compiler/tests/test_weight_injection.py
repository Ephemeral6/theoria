"""E-06's half that was in reach: the weights are never written down twice.

Ledger entry E-05 gave a potential a name. What stayed broken after it is where
the *numbers* come from: `gen_lean` read them out of the certificate, and the
other three backends read them only out of the problem instance. So a level file
either repeated the engine's vector by hand — the transcription step A1 exists to
delete, and the way a proof comes to rest on weights nobody re-solved — or the
`theory.md` a human reads named a potential it could not show.

`build_ir(ast, problem, certificate)` is now the one place a `weights` name
acquires numbers. These tests pin the four things that must hold there:
the certificate fills an unfilled declaration; a level copy is allowed but must
agree; an ambiguous fill is refused rather than guessed; and every form sees the
same vector with its provenance attached.

What this does **not** close is E-06 proper — `goal count(Peg, alive) = 1` is
still unproven, because three of the five single-peg goals admit no linear
pagoda at all. `test_gen_lean.py::test_refuses_goals_the_certificate_does_not_cover`
is where that stays recorded.
"""

from pathlib import Path

import pytest

from theory_compiler.certificate import load_certificate
from theory_compiler.generators.gen_markdown import generate_markdown
from theory_compiler.ir import IRError, build_ir
from theory_compiler.parser.theory_parser import parse_theory
from theory_compiler.problem import from_json, load_problem

FIXTURES = Path(__file__).parent / "fixtures"
REPO = Path(__file__).resolve().parents[2]
CERT = REPO / "engine-rig" / "interop" / "certificates" / "pagoda_5_11011_to_00010.json"


@pytest.fixture
def peg():
    ast = parse_theory((FIXTURES / "peg_theory.dsl").read_text(encoding="utf-8"))
    problem = load_problem(str(FIXTURES / "peg5_problem.json"))
    return ast, problem


@pytest.fixture
def cert():
    return load_certificate(str(CERT))


# ------------------------------------------------------------- the injection

def test_the_level_file_carries_no_weights_at_all(peg):
    """The fixture is the claim: nothing was hand-copied into it."""
    _ast, problem = peg
    assert problem.weights == {}


def test_the_certificate_fills_the_declared_potential(peg, cert):
    ast, problem = peg
    ir = build_ir(ast, problem, cert)
    assert ir.weights["w"] == list(cert.weights)
    assert ir.weight_sources["w"].startswith("certificate")


def test_the_provenance_is_repo_relative_so_the_record_travels(peg, cert):
    ast, problem = peg
    ir = build_ir(ast, problem, cert)
    source = ir.weight_sources["w"]
    assert "engine-rig/interop/certificates" in source
    assert ":\\" not in source and ":/" not in source, (
        "an absolute path names this machine, not the artefact: %r" % source)


def test_without_a_certificate_the_declaration_stays_unfilled(peg):
    """And the compile warns, rather than inventing a vector."""
    ast, problem = peg
    ir = build_ir(ast, problem)
    assert "w" not in ir.weights
    assert any("weights w" in w for w in ir.warnings)


def test_the_warning_disappears_once_the_certificate_fills_it(peg, cert):
    """A warning about a hole that is not there is how a log stops being read."""
    ast, problem = peg
    ir = build_ir(ast, problem, cert)
    assert not [w for w in ir.warnings if "weights w" in w], ir.warnings


# ------------------------------------------------------ the two sources agree

def test_a_matching_level_copy_is_allowed_and_recorded_as_corroboration(peg, cert):
    """A self-contained problem file is sometimes worth having."""
    ast, problem = peg
    problem.weights["w"] = list(cert.weights)
    ir = build_ir(ast, problem, cert)
    assert ir.weights["w"] == list(cert.weights)
    assert "agrees with certificate" in ir.weight_sources["w"]


def test_a_stale_level_copy_is_an_error_not_a_preference(peg, cert):
    ast, problem = peg
    problem.weights["w"] = [0, 0, 0, 0, 0]
    with pytest.raises(IRError) as exc:
        build_ir(ast, problem, cert)
    assert "stale" in str(exc.value)


def test_the_check_fires_for_every_caller_that_supplies_a_certificate(peg, cert):
    """The point of moving it into the IR — stated no wider than it is true.

    Before, the check lived inside `gen_lean`, so `generate_markdown` could be
    handed an IR built from a stale level copy and would render it. Now it
    fires in `build_ir`, which is upstream of every form.

    It does **not** fire for `generate_python` or `generate_pddl`, and that is
    not a gap: neither takes a certificate, because neither form's output
    depends on the weights. A predictor is a `step` function; the pagoda
    potential is not part of it, so there is nothing there to be stale.
    """
    ast, problem = peg
    problem.weights["w"] = [9, 9, 9, 9, 9]
    with pytest.raises(IRError):
        build_ir(ast, problem, cert)
    with pytest.raises(IRError):
        from theory_compiler.generators.gen_lean import generate_lean
        generate_lean(ast, problem, cert)

    # The negative half: the weight-free forms compile from the same stale
    # level without complaint, because the number never reaches their output.
    from theory_compiler.generators.gen_python import generate_python
    assert generate_python(ast, problem)


# ----------------------------------------------------------- refusing to guess

def test_a_certificate_with_no_declaration_to_land_on_is_refused(cert):
    ast = parse_theory((FIXTURES / "cart_theory.dsl").read_text(encoding="utf-8"))
    problem = load_problem(str(FIXTURES / "cart_problem.json"))
    with pytest.raises(IRError) as exc:
        build_ir(ast, problem, cert)
    assert "no name to land on" in str(exc.value)


def test_two_unfilled_declarations_and_one_certificate_is_refused(peg, cert):
    """One vector cannot fill two names, and alphabetical order is not an answer."""
    ast, problem = peg
    extra = type(ast.word_table.weights[0])(name="v", over=ast.word_table.weights[0].over)
    ast.word_table.weights.append(extra)
    with pytest.raises(IRError) as exc:
        build_ir(ast, problem, cert)
    message = str(exc.value)
    assert "One vector cannot fill two names" in message
    assert "'v'" in message and "'w'" in message


# --------------------------------------------------- every form sees the same

def test_markdown_shows_the_numbers_and_says_where_they_came_from(peg, cert):
    ast, problem = peg
    ir = build_ir(ast, problem, cert)
    md = generate_markdown(ast, ir)
    assert ", ".join(str(v) for v in cert.weights) in md
    assert "engine-rig/interop/certificates" in md


def test_markdown_without_an_ir_is_byte_identical_to_before(peg):
    """The parameter is additive; existing callers get exactly what they got."""
    ast, _problem = peg
    assert generate_markdown(ast) == generate_markdown(ast, None)
    assert "The Numbers Behind" not in generate_markdown(ast)


def test_the_lean_and_markdown_forms_read_the_same_vector(peg, cert):
    from theory_compiler.generators.gen_lean import generate_lean
    ast, problem = peg
    ir = build_ir(ast, problem, cert)
    lean = generate_lean(ast, problem, cert)
    md = generate_markdown(ast, ir)
    for i, weight in enumerate(cert.weights):
        assert "| .p%d => %d" % (i, weight) in lean
    assert ", ".join(str(v) for v in cert.weights) in md
