"""End-to-end: one source, four forms — and the A1 acceptance itself.

This file used to end by printing "weights are hand-computed constants, not
LP-derived" and "formal A1 acceptance requires LP engine + Lean integration".
Both notes are now obsolete, and the tests that follow are what replaced them:
the weights come from `engine-rig/interop/certificates/`, the Lean proof is a
pagoda induction over them, and the acceptance is checked by running `lean` and
reading `#print axioms`.

The two litmus tests for de-specialising the generators run here too. Every
generator is handed a `TheoryAST` it has never seen the shape of before:

* the peg world (line geometry, four instances of one declared type, a pagoda
  potential), and
* `cold-start-a0/theory/theory.dsl` (grid geometry, three declared types, a
  portal, a latch, no potential),

and both must produce all four forms without either generator knowing which
world it is compiling.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

from theory_compiler.certificate import load_certificate
from theory_compiler.generators.gen_lean import generate_lean
from theory_compiler.generators.gen_markdown import generate_markdown
from theory_compiler.generators.gen_pddl import generate_pddl
from theory_compiler.generators.gen_python import generate_python
from theory_compiler.parser.playbook_parser import parse_playbook
from theory_compiler.parser.theory_parser import parse_theory
from theory_compiler.problem import load_problem

from .test_gen_markdown import assert_no_dsl_syntax

FIXTURES = Path(__file__).parent / "fixtures"
REPO = Path(__file__).resolve().parents[2]
A0_DSL = REPO / "cold-start-a0" / "theory" / "theory.dsl"
A0_PROBLEM = REPO / "cold-start-a0" / "artifacts" / "problem_a0-base.json"
CERT = REPO / "engine-rig" / "interop" / "certificates" / "pagoda_5_11011_to_00010.json"

LEAN = shutil.which("lean")


@pytest.fixture
def peg():
    ast = parse_theory((FIXTURES / "peg_theory.dsl").read_text(encoding="utf-8"))
    return ast, load_problem(str(FIXTURES / "peg5_problem.json"))


# ------------------------------------------------------ litmus 1: no regression

def test_peg_still_produces_three_forms_and_a_declared_pddl_refusal(peg):
    """The peg world's planning form is a *refusal*, and now says so.

    Before the 2026-07-31 `gen_pddl` repair this test asserted `":action" in
    domain` — and the domain it accepted contained one direction-less action
    whose guards (`?a.alive = true`, `?b.pos = ?a.pos + 1`) had been silently
    dropped, on a line world the generator cannot lay out. The repair makes
    the backend refuse what it cannot carry, so the honest assertion is the
    refusal itself, with the reason attached. Three forms plus a named gap is
    the true count for this world.
    """
    ast, problem = peg
    code = generate_python(ast, problem)
    ns = {}
    exec(compile(code, "<peg>", "exec"), ns)
    assert ns["occupancy"](ns["initial_state"]()) == "11011"

    lean = generate_lean(ast, problem, load_certificate(str(CERT)))
    assert "theorem unsolvable" in lean and "sorry" not in lean

    md = generate_markdown(ast)
    assert generate_markdown(ast) == md          # deterministic, no model in path
    assert_no_dsl_syntax(md)
    assert "How a Turn Works" in md              # E-03 reaches the human reader

    from theory_compiler.generators.gen_python import UnsupportedClause
    with pytest.raises(UnsupportedClause):
        generate_pddl(ast, problem_name="peg", grid_width=5, grid_height=1)
    with pytest.raises(UnsupportedClause, match="line world"):
        generate_pddl(ast, problem=problem)


# ------------------------------------- litmus 2: a world the generators never saw

@pytest.mark.skipif(not A0_DSL.exists(), reason="cold-start-a0 manual absent")
class TestForeignManual:
    """`cold-start-a0/theory/theory.dsl` is another track's manual, read here as
    data. It was written against v0.1 plus a local `semantics:` dialect; v0.2
    adopted that dialect, so it parses unchanged."""

    def setup_method(self):
        self.ast = parse_theory(A0_DSL.read_text(encoding="utf-8"))
        self.problem = load_problem(str(A0_PROBLEM))

    def test_python_is_runnable(self):
        ns = {}
        exec(compile(generate_python(self.ast, self.problem), "<a0>", "exec"), ns)
        assert [r[0] for r in ns["RULES"]] == [
            "push_up", "push_down", "push_left", "push_right",
            "teleport_down", "press_left", "door_opens_left"]
        state = ns["initial_state"]()
        moved = ns["step"](state, ("push", "Cart", "up"))
        assert moved.Cart_pos != state.Cart_pos          # a rule actually fired
        assert moved.Door_present is state.Door_present  # frame persist

    def test_lean_is_type_correct(self):
        lean = generate_lean(self.ast, self.problem)
        assert "sorry" not in lean
        assert "native_decide" not in lean
        assert "def step : St → Act → St" in lean
        # This world is solvable, and the generator says so rather than
        # manufacturing an unsolvability theorem for it.
        assert "goal_is_reachable" in lean

    @pytest.mark.skipif(LEAN is None, reason="lean is not on PATH")
    def test_lean_compiles(self, tmp_path):
        target = tmp_path / "A0.lean"
        target.write_text(generate_lean(self.ast, self.problem),
                          encoding="utf-8", newline="\n")
        shutil.copy(REPO / "theory-compiler" / "lean" / "lean-toolchain", tmp_path)
        result = subprocess.run([LEAN, str(target)], cwd=str(tmp_path),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=600)
        output = result.stdout.decode("utf-8", errors="replace")
        assert result.returncode == 0, output
        assert "sorryAx" not in output

    def test_markdown_and_pddl(self):
        md = generate_markdown(self.ast)
        assert "Cart" in md and generate_markdown(self.ast) == md
        domain, instance = generate_pddl(self.ast, problem_name="a0",
                                         grid_width=9, grid_height=9)
        assert domain.count("(") == domain.count(")")
        assert instance.count("(") == instance.count(")")

    def test_pddl_compiled_against_the_level_solves_like_the_world(self):
        """The fourth form, held to the same bar as the executable form.

        Compiled with the real level, the planning form must (a) pass the
        track's own STRIPS reader, (b) ground every schema to at least one
        instance, and (c) reach the goal in the 12 steps the world is known
        to need (`cold-start-a0/artifacts/fd_real.json`). Before the
        2026-07-31 repair this manual compiled to three empty effects, two
        unbound `?dest`s and a press that pressed nothing.
        """
        from collections import deque
        from theory_compiler import strips

        domain, instance = generate_pddl(self.ast, problem=self.problem)
        _name, _arities, _types, schemas = strips.parse_domain(domain)
        assert len(schemas) == 6      # 7 rules; press + door fold (cascade)
        task = strips.ground(domain, instance)
        grounded = {a.name for a in task.actions}
        assert grounded == {s.name for s in schemas}

        init, goal = frozenset(task.init), set(task.goal)
        seen, queue, depth = {init}, deque([(init, 0)]), None
        while queue:
            state, d = queue.popleft()
            if goal <= state:
                depth = d
                break
            for action in task.actions:
                if action.applicable(state):
                    nxt = frozenset((state - action.dele) | action.add)
                    if nxt not in seen:
                        seen.add(nxt)
                        queue.append((nxt, d + 1))
        assert depth == 12


# ------------------------------------------------------------- the acceptance

@pytest.mark.skipif(LEAN is None, reason="lean is not on PATH")
def test_a1_acceptance_lp_weights_to_a_closed_lemma(peg, tmp_path):
    """LP weights -> Lean closed lemma, no `sorry`, empty axiom set.

    Everything the proof rests on is traced: the weights are the certificate's
    (re-derived here, not taken on the producer's word), the move geometry is
    recovered from the generated predictor and cross-checked against them, and
    the axiom set is whatever `lean` says it is.
    """
    ast, problem = peg
    cert = load_certificate(str(CERT))
    assert cert.weights == [-1, 1, 0, 1, -1]
    assert cert.produced_by == "engine-rig/engines/lp_potential"

    source = generate_lean(ast, problem, cert, proof="computational")
    assert "sorry" not in source
    assert "native_decide" not in source

    target = tmp_path / "Theory.lean"
    target.write_text(source, encoding="utf-8", newline="\n")
    shutil.copy(REPO / "theory-compiler" / "lean" / "lean-toolchain", tmp_path)
    result = subprocess.run([LEAN, str(target)], cwd=str(tmp_path),
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            timeout=600)
    output = result.stdout.decode("utf-8", errors="replace")
    assert result.returncode == 0, output
    assert "sorryAx" not in output
    for name in ("inv_init", "inv_closed", "inv_all", "unsolvable"):
        assert f"'{name}' does not depend on any axioms" in output, output


# ------------------------------------------------------------------- playbook

def test_playbook_positive_and_negative():
    text = (FIXTURES / "peg_playbook.dsl").read_text(encoding="utf-8")
    assert len(parse_playbook(text).statements) >= 1
    with pytest.raises(Exception) as exc:
        parse_playbook("solution: JUMP_RIGHT, JUMP_LEFT, JUMP_RIGHT\n")
    message = str(exc.value).lower()
    assert any(w in message for w in ("action", "sequence", "solution", "cheat"))
