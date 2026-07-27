"""Tests for the Lean 4 generator (M4)."""
import subprocess
import sys
import os
from pathlib import Path
import pytest

from theory_compiler.generators.gen_lean import generate_lean
from theory_compiler.parser.theory_parser import parse_theory

FIXTURES = Path(__file__).parent / "fixtures"
LEAN_DIR = Path(__file__).parent.parent / "lean"


@pytest.fixture
def peg_ast():
    text = (FIXTURES / "peg_theory.dsl").read_text(encoding="utf-8")
    return parse_theory(text)


def test_generate_lean_produces_code(peg_ast):
    code = generate_lean(
        peg_ast,
        board_size=5,
        initial_config=[True, True, False, True, True],
        pagoda_weights=[1, 2, 3, 2, 1],
        goal_count=1,
    )
    assert "theorem unsolvable" in code
    assert "sorry" not in code
    assert "allReachable" in code


def test_lean_builds_no_sorry(peg_ast):
    """Generate Lean, build with lake, verify 0 sorry."""
    code = generate_lean(
        peg_ast,
        board_size=5,
        initial_config=[True, True, False, True, True],
        pagoda_weights=[1, 2, 3, 2, 1],
        goal_count=1,
    )
    lean_file = LEAN_DIR / "TheoriaLean.lean"
    lean_file.write_text(code, encoding="utf-8")

    # Find elan/lake
    elan_bin = Path.home() / ".elan" / "bin"
    env = os.environ.copy()
    env["PATH"] = str(elan_bin) + os.pathsep + env.get("PATH", "")

    result = subprocess.run(
        f'"{elan_bin / "lake"}" build',
        cwd=str(LEAN_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        timeout=300,
        shell=True,
    )
    output = result.stdout.decode("utf-8", errors="replace")
    assert result.returncode == 0, f"Lean build failed:\n{output}"
    assert "sorryAx" not in output, f"sorry found in axioms:\n{output}"
    # Standard axioms are acceptable
    assert "propext" in output or "Lean.ofReduceBool" in output


def test_bfs_reachable_correct():
    """BFS should find exactly 5 reachable states for [1,1,0,1,1]."""
    from theory_compiler.generators.gen_lean import _bfs_reachable
    init = (True, True, False, True, True)
    reachable = _bfs_reachable(5, init)
    assert len(reachable) == 5
    assert init in reachable
    # No single-peg state should be reachable
    for s in reachable:
        assert sum(s) != 1, f"Goal state {s} is reachable!"
