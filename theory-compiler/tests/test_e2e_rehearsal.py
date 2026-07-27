"""
M8 — End-to-end A1 rehearsal.

Takes the peg solitaire素材 B through ALL four generation paths:
  1. theory.py  — executable simulation
  2. theory.lean — formal proof (0 sorry)
  3. theory.md  — natural language rendering (deterministic, no DSL keywords)
  4. theory.pddl — syntactically valid PDDL

Plus playbook.dsl parsing with negative test.

This is a structural rehearsal of the compile chain, NOT the formal A1
acceptance (which requires LP-derived weights and Lean↔engine integration).
Here the pagoda weights are hand-computed constants.
"""
import subprocess
import sys
from pathlib import Path

import pytest

from theory_compiler.parser.theory_parser import parse_theory
from theory_compiler.parser.playbook_parser import parse_playbook
from theory_compiler.generators.gen_python import generate_python
from theory_compiler.generators.gen_lean import generate_lean
from theory_compiler.generators.gen_markdown import generate_markdown
from theory_compiler.generators.gen_pddl import generate_pddl

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def peg_theory_ast():
    text = (FIXTURES / "peg_theory.dsl").read_text(encoding="utf-8")
    return parse_theory(text)


@pytest.fixture
def peg_playbook_text():
    return (FIXTURES / "peg_playbook.dsl").read_text(encoding="utf-8")


# ---------- Path 1: Python generation ----------

def test_e2e_python_simulation(peg_theory_ast):
    """Generated Python code compiles and has expected structure."""
    code = generate_python(peg_theory_ast, grid_width=5, grid_height=1)
    ns = {}
    exec(compile(code, "<e2e_peg>", "exec"), ns)

    # Should define State and simulation functions
    assert "State" in ns
    assert "step" in ns or "simulate" in ns


# ---------- Path 2: Lean generation ----------

def test_e2e_lean_zero_sorry(peg_theory_ast):
    """Generated Lean has 0 sorry and correct structure."""
    # 1D peg solitaire: 5 cells, pegs at 0,1,3,4, center=2 empty
    initial_config = [True, True, False, True, True]
    pagoda_weights = [1, 2, 3, 2, 1]
    lean_code = generate_lean(peg_theory_ast, board_size=5,
                               initial_config=initial_config,
                               pagoda_weights=pagoda_weights, goal_count=1)
    assert "sorry" not in lean_code
    assert "theorem unsolvable" in lean_code
    assert "allReachable" in lean_code
    assert "#print axioms unsolvable" in lean_code
    # Actual compilation verified in test_gen_lean.py::test_lean_builds_no_sorry


# ---------- Path 3: Markdown generation ----------

def test_e2e_markdown_deterministic(peg_theory_ast):
    """Markdown is deterministic and contains no DSL keywords."""
    md1 = generate_markdown(peg_theory_ast)
    md2 = generate_markdown(peg_theory_ast)
    assert md1 == md2, "Non-deterministic markdown output"
    assert len(md1) > 100

    # No DSL keywords
    for kw in ["word_table:", "events:", "rules:", "goal:", "laws:",
               "object ", "event ", "rule ", "invariant ", "theorem "]:
        assert kw not in md1, f"DSL keyword '{kw}' leaked"


# ---------- Path 4: PDDL generation ----------

def test_e2e_pddl_syntax(peg_theory_ast):
    """Generated PDDL is syntactically valid (balanced parens, required sections)."""
    domain, problem = generate_pddl(peg_theory_ast, problem_name="peg-rehearsal",
                                     grid_width=5, grid_height=1)

    # Balanced parentheses
    for name, text in [("domain", domain), ("problem", problem)]:
        depth = 0
        for ch in text:
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
                assert depth >= 0, f"Unbalanced ')' in {name}"
        assert depth == 0, f"Unclosed '(' in {name}"

    # Required sections
    assert "(define (domain" in domain
    assert ":action" in domain
    assert "(define (problem" in problem
    assert ":init" in problem
    assert ":goal" in problem
    assert ":parameters" in domain  # actions are parameterized


# ---------- Path 5: Playbook parsing ----------

def test_e2e_playbook_positive(peg_playbook_text):
    """Playbook parses successfully."""
    ast = parse_playbook(peg_playbook_text)
    assert ast is not None
    # Should have at least one statement
    assert len(ast.statements) >= 1


def test_e2e_playbook_negative():
    """Playbook with literal action sequence is rejected."""
    bad_playbook = 'solution: JUMP_RIGHT, JUMP_LEFT, JUMP_RIGHT\n'
    with pytest.raises(Exception) as exc_info:
        parse_playbook(bad_playbook)
    # Error should mention action sequence / anti-cheat
    err_msg = str(exc_info.value).lower()
    assert "action" in err_msg or "sequence" in err_msg or "solution" in err_msg or "cheat" in err_msg


# ---------- Summary ----------

def test_e2e_all_paths_summary(peg_theory_ast, peg_playbook_text, capsys):
    """Summarize: all four generation paths + playbook produce valid output."""
    # This test just confirms all paths run without error
    code = generate_python(peg_theory_ast, grid_width=5, grid_height=1)
    assert "def apply_event" in code or "class State" in code

    initial_config = [True, True, False, True, True]
    pagoda_weights = [1, 2, 3, 2, 1]
    lean = generate_lean(peg_theory_ast, board_size=5,
                          initial_config=initial_config,
                          pagoda_weights=pagoda_weights, goal_count=1)
    assert "theorem unsolvable" in lean

    md = generate_markdown(peg_theory_ast)
    assert "Peg" in md

    domain, problem = generate_pddl(peg_theory_ast, problem_name="peg-e2e",
                                     grid_width=5, grid_height=1)
    assert "(define" in domain

    pb_ast = parse_playbook(peg_playbook_text)
    assert pb_ast is not None

    print("\n=== A1 COMPILE CHAIN REHEARSAL: ALL PATHS PASS ===")
    print(f"  Python generator: OK ({len(code)} chars)")
    print(f"  Lean generator:   OK ({len(lean)} chars, 'sorry' absent)")
    print(f"  Markdown:         OK ({len(md)} chars, deterministic)")
    print(f"  PDDL:            OK (domain {len(domain)} + problem {len(problem)} chars)")
    print(f"  Playbook parser:  OK (positive + negative)")
    print("=== NOTE: weights are hand-computed constants, not LP-derived ===")
    print("=== Formal A1 acceptance requires LP engine + Lean integration ===")
