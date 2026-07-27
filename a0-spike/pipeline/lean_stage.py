"""The proof form: check A0.lean, audit what it rests on, and diff it against Python.

Three things have to hold before a Lean proof means anything about this world:

  1. **it checks** -- `lean A0.lean` is silent;
  2. **it rests on nothing exotic** -- `#print axioms` shows no `sorryAx`, and the
     statement is not vacuous (`Goal` is satisfiable, `Reachable` inhabited).
     A theorem "nothing reachable is a goal" is free if either set is empty;
  3. **it is about the same world as the executable form** -- otherwise it is
     Theoria's A2 exhibit: a theorem that type-checks and is false of the world.

Lean is optional here. It is not on PATH in this sandbox and the only toolchain
in the tree belongs to the other track, so every function degrades to "skipped"
rather than failing when it is absent.
"""

import os
import subprocess
import sys
import tempfile
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

from pipeline.cross_form import (        # noqa: E402
    compare,
    enumerate_cases,
    find_lean,
    lean_probe_source,
    run_lean,
)

LEAN_PATH = os.path.join(HERE, "artifacts", "A0.lean")

AUDIT_SUFFIX = """

#print axioms unsolvable
#print axioms inv_closed
#print axioms inv_init
#print axioms goal_break

-- Non-vacuity. Without these, `unsolvable` could hold because nothing is
-- reachable or nothing is a goal.
example : Goal { pr := 0, pc := 0, br := 3, bc := 2 } := ⟨rfl, rfl⟩
example : Reachable s0 := Reachable.init
"""


def _run(lean: str, source: str, name: str) -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory() as workdir:
        path = os.path.join(workdir, name)
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(source)
        return subprocess.run([lean, path], capture_output=True, text=True, timeout=900)


def check(lean_path: str = LEAN_PATH) -> Dict[str, Any]:
    """Compile the proof and audit its axioms and non-vacuity."""
    lean = find_lean()
    if lean is None:
        return {"available": False, "skipped": "no lean toolchain found"}

    source = open(lean_path, encoding="utf-8").read()
    compiled = _run(lean, source, "A0.lean")
    audited = _run(lean, source + AUDIT_SUFFIX, "A0Audit.lean")
    axiom_lines = [
        line.strip() for line in audited.stdout.splitlines()
        if "depends on axioms" in line or "does not depend" in line
    ]
    return {
        "available": True,
        "lean": lean,
        "theorems": ["inv_init", "inv_closed", "goal_break", "unsolvable"],
        "compiles": compiled.returncode == 0 and not compiled.stdout.strip(),
        "compile_output": (compiled.stdout + compiled.stderr)[:400],
        "axioms": axiom_lines,
        "uses_sorry": "sorryAx" in audited.stdout,
        "non_vacuous": audited.returncode == 0,
        "sorry_in_source": "sorry" in source,
    }


def cross_check(module: Dict[str, Any], height: int, width: int,
                lean_path: str = LEAN_PATH) -> Dict[str, Any]:
    """Diff the Lean `step` against the Python `step`, over the whole board."""
    lean = find_lean()
    if lean is None:
        return {"available": False, "skipped": "no lean toolchain found"}
    source = lean_probe_source(open(lean_path, encoding="utf-8").read(), height, width)
    with tempfile.TemporaryDirectory() as workdir:
        rows = run_lean(source, lean, workdir)
    result = compare(module, enumerate_cases(height, width), rows)
    result["available"] = True
    return result
