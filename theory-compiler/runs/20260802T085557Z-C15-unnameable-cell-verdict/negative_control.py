"""C15 — was the refusal ever seen to say no?

This track's standing convention (D-TC-033's `负控制被看见说过「不」`, and both
`verify.py` files) is that a check nobody has watched refuse has not been shown
to check anything. So: disable the two checks, re-run C15's test file, and
record how many of its 30 tests go red and which survive.

The survivors must be exactly the tests that do not depend on the refusal —
`gen_pddl`'s own refusals (which come from PDDL's typing discipline and not from
`_check_write_targets`, so they must survive, and their surviving is itself the
evidence for v0.4 §4's "convergent, not derived"), the guard-side legality
controls, and the seated positive control. Anything else surviving would mean a
test that asserts a refusal it cannot actually feel.

Restores the sources on the way out, in a `finally`, and verifies the restore.

    python negative_control.py
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TC = os.path.normpath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(TC, "src", "theory_compiler")

TARGETS = [
    (os.path.join(SRC, "ir.py"),
     r"(def _check_write_targets\([^)]*\)[^:]*:\n(?:\s*(?:\"\"\".*?\"\"\")?\n?))",
     "    return []  # NEGATIVE CONTROL\n"),
    (os.path.join(SRC, "generators", "gen_markdown.py"),
     r"(def _check_effects_are_writable\([^)]*\)[^:]*:\n(?:\s*(?:\"\"\".*?\"\"\")?\n?))",
     "    return  # NEGATIVE CONTROL\n"),
]


def mutate(path, pattern, injection):
    with open(path, encoding="utf-8") as fh:
        original = fh.read()
    match = re.search(pattern, original, re.S)
    if not match:
        raise SystemExit("could not find the function to disable in %s" % path)
    mutated = original[:match.end()] + injection + original[match.end():]
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(mutated)
    return original


def main():
    backups = {}
    tmp = tempfile.mkdtemp(prefix="c15-negctl-")
    try:
        for path, pattern, injection in TARGETS:
            backups[path] = mutate(path, pattern, injection)
            shutil.copy(path, os.path.join(tmp, os.path.basename(path) + ".mutated"))
            print("disabled the check in %s" % os.path.relpath(path, TC))

        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q",
             "tests/test_c15_unnameable_cell.py"],
            # The refusal messages carry em-dashes and typographic quotes, and
            # this box's locale codec is gbk -- without an explicit utf-8 the
            # capture thread dies on the very text being measured.
            cwd=TC, capture_output=True, text=True,
            encoding="utf-8", errors="replace")
        tail = [ln for ln in proc.stdout.splitlines() if ln.strip()][-1:]
        print("\n---- with both checks disabled ----")
        print("\n".join(tail))
        survivors = sorted(set(re.findall(r"(test_\w+)", proc.stdout)))
        failed = sorted(set(re.findall(r"FAILED [\w/\\.]+::(\w+)", proc.stdout)))
        print("\ndistinct test functions that FAILED (%d):" % len(failed))
        for name in failed:
            print("   %s" % name)
        print("\n(all test function names seen: %d)" % len(survivors))
    finally:
        for path, original in backups.items():
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(original)
        print("\nrestored %d source file(s)" % len(backups))
        check = subprocess.run(["git", "status", "--short", "src"],
                               # The refusal messages carry em-dashes and typographic quotes, and
            # this box's locale codec is gbk -- without an explicit utf-8 the
            # capture thread dies on the very text being measured.
            cwd=TC, capture_output=True, text=True,
            encoding="utf-8", errors="replace")
        print("git status src/ after restore: %r" % check.stdout.strip())


if __name__ == "__main__":
    main()
