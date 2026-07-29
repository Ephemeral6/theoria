"""Does `test_bare_gate.py` actually bite?

The same control P16 built for check E, pointed at check F. A negative-control
suite that has never been watched fail is a suite that might be testing nothing,
and P16 found that the hard way twice: four fixes went in without controls (one
of them inverted), and one mutation had silently gone PATTERN-NOT-FOUND because
the code it was written against had been rewritten.

That last failure mode is why `main` treats a missing pattern as a miss rather
than a skip: a mutation that cannot find its target reports nothing, which reads
exactly like a mutation that was caught.

Run:  python papers/phase1-workshop/runs/20260729T143500Z-P17-bare-filename-citations/mutation_check.py
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve()
PAPER = HERE.parents[2]
GATE = PAPER / "verify_paper.py"
SUITE = PAPER / "test_bare_gate.py"

#: (name, verbatim fragment of verify_paper.py, replacement that breaks it)
MUTATIONS = [
    ("ambiguity stops being an error",
     "                if n <= 1:", "                if False:"),
    ("every bare filename is waved through",
     "                if n <= 1:", "                if True:"),
    ("the check stops gating on what it flagged",
     "    return not flagged and not stale, notes",
     "    return True, notes"),
    # Anchored to `scan_bare()`'s caller: check_uncited has a byte-identical
    # `stale = ...` line and comes first in the file, so the unqualified
    # fragment mutated check E instead and this suite -- correctly -- saw
    # nothing wrong. A mutation aimed at the wrong function is a mutation that
    # proves nothing about the function it names.
    ("stale rulings stop gating",
     "    flagged, hits, seen = scan_bare()\n"
     "    stale = [k for k, n in hits.items() if not n]",
     "    flagged, hits, seen = scan_bare()\n    stale = []"),
    ("a ruling stops being scoped to its section",
     "                key = (section.name, token)", "                key = (token, token)"),
    ("the abstract exemption widens to everything",
     "        if section.name in EXEMPT_SECTIONS:\n            continue\n"
     "        for lineno, line in enumerate(",
     "        for lineno, line in enumerate("),
    ("a path counts as a bare filename",
     '                if "/" in token or not token.lower().endswith(ARTEFACT_SUFFIX):',
     '                if not token.lower().endswith(ARTEFACT_SUFFIX):'),
    ("worktrees come back into the candidate set",
     '    ".git", "__pycache__", ".worktrees", ".toolchain", "node_modules",',
     '    ".git", "__pycache__", ".toolchain", "node_modules",'),
    ("the check stops printing its rulings",
     '            notes.append(f"  ruled     {key[0]} `{key[1]}` ({n}x) -- {ADJUDICATED_BARE[key]}")',
     "            pass"),
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
        print(f"  [{'ok ' if verdict == 'caught' else 'MISS'}] {name}: {verdict}")
    print()
    if missed:
        print(f"mutation_check: FAIL -- {len(missed)}/{len(MUTATIONS)} not caught")
        return 1
    print(f"mutation_check: PASS -- {len(MUTATIONS)}/{len(MUTATIONS)} caught")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
