#!/usr/bin/env bash
# C7 — re-derive everything this run claims. From the repo root:
#
#     bash theory-compiler/runs/20260728T102343Z-c7/verify.sh
#
# Three checks, in the order in which a failure is most informative.
set -eu

cd "$(dirname "$0")/../.."          # theory-compiler/

echo "== 1. the suite =============================================="
python -m pytest -q

echo
echo "== 2. the two ledger numbers, and both driven to zero ========"
# X-1's 376 in its own denominator (39,960 off-wall pairs), X-5's 52 in its own
# (the 7,080 on-wall remainder), and 0/47,040 for the repaired manual. Grades
# against a0-spike/world/sokoban2.py; exits 77 and says so if that is absent.
python -m tools.probe_mentions --out runs/20260728T102343Z-c7

echo
echo "== 3. every manual in the repository still compiles =========="
python - <<'PY'
import glob, os, sys
sys.path.insert(0, "src")
from theory_compiler.ir import build_ir
from theory_compiler.parser.theory_parser import parse_theory
from theory_compiler.problem import load_problem

CASES = [
    ("tests/fixtures/peg_theory.dsl",   "tests/fixtures/peg5_problem.json"),
    ("tests/fixtures/peg4_theory.dsl",  "tests/fixtures/peg4_problem.json"),
    ("tests/fixtures/cart_theory.dsl",  "tests/fixtures/cart_problem.json"),
    ("tests/fixtures/sokoban2_theory.dsl",
     "tests/fixtures/sokoban2_match_problem.json"),
    ("tests/fixtures/sokoban2_x5_theory.dsl",
     "tests/fixtures/sokoban2_match_problem.json"),
    ("../cold-start-a0/theory/theory.dsl",
     "../cold-start-a0/artifacts/problem_a0-base.json"),
    ("../cold-start-a0/theory/theory_no_button.dsl",
     "../cold-start-a0/artifacts/problem_a0-no-button.json"),
    ("../cold-start-a2/theory/theory.dsl",
     "../cold-start-a2/theory/generated/problem.json"),
    ("../cold-start-a2/theory/theory_holed.dsl",
     "../cold-start-a2/theory/generated_holed/problem.json"),
    ("../cold-start-a2/theory/theory_repaired.dsl",
     "../cold-start-a2/theory/generated_repaired/problem.json"),
]

bad = 0
for dsl, problem in CASES:
    if not (os.path.exists(dsl) and os.path.exists(problem)):
        print("   skip  %-46s (not in this checkout)" % dsl)
        continue
    try:
        ast = parse_theory(open(dsl, encoding="utf-8").read())
        ir = build_ir(ast, load_problem(problem))
    except Exception as exc:
        bad += 1
        print("   FAIL  %-46s %s: %s" % (dsl, type(exc).__name__, exc))
        continue
    undischarged = [w for w in ir.warnings if "not discharged" in w]
    print("   ok    %-46s %2d rules, %d warning(s)%s"
          % (dsl, len(ir.rules), len(ir.warnings),
             "  UNDISCHARGED" if undischarged else ""))
    bad += len(undischarged)

# a0-spike's own manual is *expected* to fail, and for a reason that predates
# this work: `dir` is a free name bound by no `forall` (E-02). Asserting the
# failure keeps the claim in §7 of the contract honest — if this ever starts
# compiling, that section is out of date.
spike = "../a0-spike/theory/theory.dsl"
if os.path.exists(spike):
    from theory_compiler.generators.gen_python import generate_python
    try:
        generate_python(parse_theory(open(spike, encoding="utf-8").read()),
                        load_problem("tests/fixtures/sokoban2_match_problem.json"))
        print("   FAIL  %-46s compiled — contract §7 is now wrong" % spike)
        bad += 1
    except Exception as exc:
        print("   ok    %-46s refused as expected: %s"
              % (spike, str(exc)[:52]))

sys.exit(1 if bad else 0)
PY

echo
echo "all green"
