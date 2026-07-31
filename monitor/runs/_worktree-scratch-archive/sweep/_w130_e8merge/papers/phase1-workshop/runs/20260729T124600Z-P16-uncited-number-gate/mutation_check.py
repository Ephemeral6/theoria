"""Does `test_uncited_gate.py` actually bite?

A negative control that passes on the first run is a control that might be
testing nothing. This breaks check E twelve ways, one at a time, and asserts the
suite goes red for each. It restores the file afterwards, including on failure.

Run:  python papers/phase1-workshop/runs/20260729T124600Z-P16-uncited-number-gate/mutation_check.py

Result on 2026-07-29 at base_commit 9bc8c880: 8/8 caught. Two of them were only
caught after the suite was extended -- the first pass left `stale = []` and a
silenced ruling printout both green, which is the whole reason this file exists.

Extended the same day to 12. One of the original eight had gone
PATTERN-NOT-FOUND against its own gate: the fix it was written for got rewritten,
and a mutation that cannot find its target reports nothing rather than failing
loudly, so the drift was invisible until this file was rerun. The four added
mutations are the four defences that had no control on them.
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
     '        return f" {token} "', '        return " "'),
    ("fenced code is scanned as prose",
     'if line.strip().startswith("```"):', "if False:"),
    ("a citation leaks across a heading",
     "out.append(None)  # a heading breaks the merge chain", "pass"),
    ("the abstract exemption widens to everything",
     'EXEMPT_SECTIONS = {"00_abstract.md"}', "EXEMPT_SECTIONS = set()"),
    ("stale rulings stop gating",
     "stale = [k for k, n in hits.items() if not n]", "stale = []"),
    # The four below defend fixes the adversarial pass forced. Each was added
    # without a mutation on it, which is the same "counter nobody gates on"
    # shape the suite already warns about -- one level up.
    ("a ratio cites itself",
     "if not NOT_A_PATH.search(token):", "if True:"),
    ("an invented filename counts as a citation",
     "and _basename_exists(token)", "and True"),
    ("the anchor floor stops holding",
     "if len(key[1]) < MIN_ANCHOR:", "if False:"),
    ("an unclosed fence stops being an error",
     "if fences % 2:", "if False:"),
    # Round two. Six more the second adversarial pass landed, each pinned by a
    # test in `test_uncited_gate.py` and mutated here so the pin is watched.
    ("a line anchor hides a path from check B",
     r"[A-Za-z0-9_.\-/{},]*?)(?::\d+(?:[-–]\d+)?)?`",
     r"[A-Za-z0-9_.\-/{},]*)`"),
    ("a ruling may silence several blocks",
     "        if n > 1:", "        if False:"),
    ("a unit turns a measurement into a name",
     "if MEASURED.fullmatch(token):", "if False:"),
    ("leading-dot decimals go invisible",
     r'r"\.\d+(?![\w.])"', 'r"ZZNOPE"'),
    ("the binary-label exemption widens back",
     r're.fullmatch(r"[01]{5}", token)', r're.fullmatch(r"[01]{5,}", token)'),
    ("frame-index eats numbers after contractions",
     r"""(?<![\w'’])t\s*=\s*\d+\b""", r"\bt\s*=?\s*\d+\b"),
    ("a heading is never scanned",
     "                    out.append([i, head])", "                    pass"),
    ("a heading's own number becomes a quantity",
     r'HEADNUM = re.compile(r"^\s*#+\s*\d+(?:\.\d+)*[a-z]?\s*")',
     r'HEADNUM = re.compile(r"^\s*#+\s*")'),
    ("fractions and multipliers stop being quantities",
     'r"|\\b(?:a half|halves|a third|two thirds|a quarter|three quarters|"\n'
     '    r"doubles?|triples?|a factor of)\\b",',
     'r"|\\b(?:ZZNOPE)\\b",'),
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
