"""Does `test_uncited_gate.py` actually bite?

A negative control that passes on the first run is a control that might be
testing nothing. This breaks check E eight ways, one at a time, and asserts the
suite goes red for each. It restores the file afterwards, including on failure.

Run:  python papers/phase1-workshop/runs/20260729T124600Z-P16-uncited-number-gate/mutation_check.py

Result on 2026-07-29 at base_commit 9bc8c880: 8/8 caught. Two of them were only
caught after the suite was extended -- the first pass left `stale = []` and a
silenced ruling printout both green, which is the whole reason this file exists.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve()
PAPER = HERE.parents[2]
GATE = PAPER / "verify_paper.py"
SUITE = PAPER / "test_uncited_gate.py"

#: (name, verbatim fragment of verify_paper.py, replacement that breaks it)
MUTATIONS = [
    ("digit vocabulary: spelled-out numerals",
     "(?:zero|eleven|twelve", "(?:ZZNOPE|eleven|twelve"),
    ("structural class: metric/claim ids",
     r"[A-Z]{1,4}(?:-[A-Z0-9]{1,4})*-?\d{1,4}",
     r"ZZ[A-Z]{1,4}(?:-[A-Z0-9]{1,4})*-?\d{1,4}"),
    ("structural class: grid coordinates",
     r"\(\s*-?\d+\s*,\s*-?\d+\s*\)", r"ZZ\(\s*-?\d+\s*,\s*-?\d+\s*\)"),
    ("backticks stop hiding a digit",
     'return " " if any(c.isalpha() for c in token) else f" {token} "',
     'return " "'),
    ("fenced code is scanned as prose",
     'if line.strip().startswith("```"):', "if False:"),
    ("a citation leaks across a heading",
     "out.append(None)  # a heading breaks the merge chain", "pass"),
    ("the abstract exemption widens to everything",
     'EXEMPT_SECTIONS = {"00_abstract.md"}', "EXEMPT_SECTIONS = set()"),
    ("stale rulings stop gating",
     "stale = [k for k, n in hits.items() if not n]", "stale = []"),
]


def main() -> int:
    original = GATE.read_text(encoding="utf-8")
    missed, results = [], []
    try:
        for name, old, new in MUTATIONS:
            if old not in original:
                results.append((name, "PATTERN NOT FOUND -- this file has drifted"))
                missed.append(name)
                continue
            GATE.write_text(original.replace(old, new, 1), encoding="utf-8")
            r = subprocess.run(
                [sys.executable, "-m", "pytest", str(SUITE), "-q"],
                capture_output=True, text=True,
            )
            caught = r.returncode != 0
            results.append((name, "caught" if caught else "SLIPPED PAST THE SUITE"))
            if not caught:
                missed.append(name)
    finally:
        GATE.write_text(original, encoding="utf-8")

    for name, verdict in results:
        print(f"  [{'ok ' if 'caught' == verdict else 'MISS'}] {name}: {verdict}")
    print()
    if missed:
        print(f"mutation_check: FAIL -- {len(missed)}/{len(MUTATIONS)} not caught")
        return 1
    print(f"mutation_check: PASS -- {len(MUTATIONS)}/{len(MUTATIONS)} caught")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
