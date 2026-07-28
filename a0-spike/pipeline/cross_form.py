"""Differential test: does the Lean form agree with the Python form?

Both are compiled from the same `theory.dsl`, and "同源多形态" is only a claim
until it is checked. A Lean proof about a `step` that differs from the executable
`step` proves something true about a world nobody is playing -- the A2 exhibit in
miniature, a theorem that type-checks and is false of the world.

So every (state, direction) on the board is run through both and compared.
"""

import os
import re
import shutil
import subprocess
import sys
from typing import Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

DIRECTIONS = ("UP", "DOWN", "LEFT", "RIGHT")
LEAN_DIR = {"UP": "Dir.up", "DOWN": "Dir.down", "LEFT": "Dir.left", "RIGHT": "Dir.right"}

# Lean is not on PATH here; the only toolchain in the tree belongs to the other
# track. Used read-only, and treated as optional: absent means skip, never fail.
FALLBACK_LEAN = os.path.join(
    REPO, "cold-start-a0", ".toolchain", "lean-4.9.0-windows", "bin", "lean.exe"
)


def _lean_runs(path: str) -> bool:
    """Does this binary actually elaborate, or does it only exist?

    `elan` installs a **shim** named `lean` on PATH which dispatches to whichever
    toolchain is configured as default. With toolchains installed but no default
    set, the shim is on PATH, is executable, and fails every invocation with
    `no default toolchain configured`. `shutil.which` cannot tell the two apart,
    so presence was never the right question -- this asks the binary.
    """
    try:
        completed = subprocess.run(
            [path, "--version"], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return False
    return completed.returncode == 0


def _elan_toolchain_leans() -> List[str]:
    """Concrete per-toolchain binaries, bypassing the shim and its default."""
    root = os.path.join(os.path.expanduser("~"), ".elan", "toolchains")
    if not os.path.isdir(root):
        return []
    out = []
    for entry in sorted(os.listdir(root)):
        for name in ("lean.exe", "lean"):
            candidate = os.path.join(root, entry, "bin", name)
            if os.path.isfile(candidate):
                out.append(candidate)
                break
    return out


def find_lean() -> Optional[str]:
    """The first Lean on this machine that actually runs, or None.

    Absent means skip, never fail -- the standing rule for this dependency. But
    "absent" has to mean *unusable*, not *unlisted*: an earlier revision returned
    the first name `shutil.which` found, which on a machine with `elan` installed
    and no default toolchain is a shim that errors on every call. The Lean stage
    then reported a hard `RuntimeError` where the honest answers were either a
    working Lean (there was one, one directory over) or a clean skip.

    An explicit `LEAN` is tried first and **verified like every other candidate**.
    A path a human set deliberately still gets to be wrong, and finding that out
    here beats finding it out 900 seconds into an elaboration.
    """
    candidates: List[str] = []

    env = os.environ.get("LEAN")
    if env and os.path.isfile(env):
        candidates.append(env)

    for name in ("lean", "lean.exe"):
        found = shutil.which(name)
        if found:
            candidates.append(found)

    candidates.extend(_elan_toolchain_leans())

    if os.path.isfile(FALLBACK_LEAN):
        candidates.append(FALLBACK_LEAN)

    seen = set()
    for candidate in candidates:
        key = os.path.normcase(os.path.abspath(candidate))
        if key in seen:
            continue
        seen.add(key)
        if _lean_runs(candidate):
            return candidate
    return None


def enumerate_cases(height: int, width: int) -> List[Tuple[int, int, int, int, str]]:
    cases = []
    for pr in range(height):
        for pc in range(width):
            for br in range(height):
                for bc in range(width):
                    if (pr, pc) == (br, bc):
                        continue        # player and box never share a cell
                    for direction in DIRECTIONS:
                        cases.append((pr, pc, br, bc, direction))
    return cases


def lean_probe_source(base_source: str, height: int, width: int) -> str:
    """Append an #eval printing every successor, one line per case.

    The cases are enumerated *inside* Lean. Passing them in as a literal list
    makes the elaborator time out on `isDefEq` at a few thousand entries.
    """
    probe = '''

def probeDirs : List Dir := [Dir.up, Dir.down, Dir.left, Dir.right]

def runOne (pr pc br bc : Int) (d : Dir) : String :=
  let s := step { pr := pr, pc := pc, br := br, bc := bc } d
  toString s.pr ++ "," ++ toString s.pc ++ "," ++ toString s.br ++ "," ++ toString s.bc

def rowsFor (pr pc br bc : Int) : List String :=
  if pr == br && pc == bc then [] else probeDirs.map (runOne pr pc br bc)

def probeRows : List String :=
  (List.range %(h)d).bind (fun pr =>
  (List.range %(w)d).bind (fun pc =>
  (List.range %(h)d).bind (fun br =>
  (List.range %(w)d).bind (fun bc =>
    rowsFor (Int.ofNat pr) (Int.ofNat pc) (Int.ofNat br) (Int.ofNat bc)))))

#eval String.intercalate "\\n" probeRows
''' % {"h": height, "w": width}
    return base_source + probe


def run_lean(source: str, lean: str, workdir: str) -> List[str]:
    path = os.path.join(workdir, "CrossForm.lean")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(source)
    completed = subprocess.run(
        [lean, path], capture_output=True, text=True, timeout=900
    )
    if completed.returncode != 0:
        raise RuntimeError("lean failed: %s" % (completed.stderr or completed.stdout)[:400])
    out = completed.stdout.strip()
    if out.startswith('"') and out.endswith('"'):
        out = out[1:-1]
    out = out.replace("\\n", "\n")
    return [line.strip() for line in out.splitlines() if line.strip()]


def compare(module: Dict, cases: Sequence, lean_rows: Sequence[str]) -> Dict:
    """Run the same cases through the Python form and diff."""
    State, step = module["State"], module["step"]
    mismatches = []
    for index, (pr, pc, br, bc, direction) in enumerate(cases):
        result = step(State(player=(pr, pc), box=(br, bc)), direction)
        python_row = "%d,%d,%d,%d" % (result.player[0], result.player[1],
                                      result.box[0], result.box[1])
        lean_row = lean_rows[index] if index < len(lean_rows) else "<missing>"
        if python_row != lean_row:
            mismatches.append(
                {"case": [pr, pc, br, bc, direction],
                 "python": python_row, "lean": lean_row}
            )
    return {
        "cases": len(cases),
        "lean_rows": len(lean_rows),
        "mismatches": mismatches[:10],
        "n_mismatches": len(mismatches),
        "forms_agree": not mismatches and len(lean_rows) == len(cases),
    }
