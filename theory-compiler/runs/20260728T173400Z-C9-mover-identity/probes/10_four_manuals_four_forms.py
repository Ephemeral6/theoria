"""C9 non-regression probe: the four cross-track DSL manuals x the four forms.

Usage:
    python 10_four_manuals_four_forms.py <repo-root>

Compiles each of the four manuals named in C9's work order through the
theory-compiler chain and reports, per manual: parse, IR, and each of Lean /
Python / PDDL / Markdown. Output is a JSON document on stdout so two trees
(this branch and the baseline) can be diffed byte-for-byte.

Read-only: nothing is written anywhere.
"""

import json
import os
import sys
import traceback

ROOT = os.path.abspath(sys.argv[1])
TC = os.path.join(ROOT, "theory-compiler")
sys.path.insert(0, os.path.join(TC, "src"))

from theory_compiler.generators.gen_lean import generate_lean       # noqa: E402
from theory_compiler.generators.gen_markdown import generate_markdown  # noqa: E402
from theory_compiler.generators.gen_pddl import generate_pddl       # noqa: E402
from theory_compiler.generators.gen_python import generate_python   # noqa: E402
from theory_compiler.ir import build_ir                             # noqa: E402
from theory_compiler.parser.theory_parser import parse_theory       # noqa: E402
from theory_compiler.problem import load_problem                    # noqa: E402

# (label, dsl, problem json). The a0-spike problem is the one c7's verify.sh
# uses for it -- a0-spike ships no problem json of its own.
CASES = [
    ("peg_theory",
     "theory-compiler/tests/fixtures/peg_theory.dsl",
     "theory-compiler/tests/fixtures/peg5_problem.json"),
    ("cold-start-a0",
     "cold-start-a0/theory/theory.dsl",
     "cold-start-a0/artifacts/problem_a0-base.json"),
    ("a0-spike (refusal expected)",
     "a0-spike/theory/theory.dsl",
     "theory-compiler/tests/fixtures/sokoban2_match_problem.json"),
    ("cold-start-a2",
     "cold-start-a2/theory/theory.dsl",
     "cold-start-a2/theory/generated/problem.json"),
]


def _err(exc):
    return "%s: %s" % (type(exc).__name__, str(exc))


def run(label, dsl_rel, prob_rel):
    out = {"label": label, "dsl": dsl_rel, "problem": prob_rel}
    dsl = os.path.join(ROOT, dsl_rel)
    prob = os.path.join(ROOT, prob_rel)
    if not os.path.exists(dsl):
        out["parse"] = "MISSING dsl"
        return out
    if not os.path.exists(prob):
        out["parse"] = "MISSING problem"
        return out

    try:
        ast = parse_theory(open(dsl, encoding="utf-8").read())
        out["parse"] = "ok"
    except Exception as exc:                                   # noqa: BLE001
        out["parse"] = "FAIL " + _err(exc)
        return out

    spec = load_problem(prob)

    ir = None
    try:
        ir = build_ir(ast, spec)
        out["ir"] = "ok"
        out["ir_rules"] = len(ir.rules)
        out["ir_warnings"] = sorted(ir.warnings)
    except Exception as exc:                                   # noqa: BLE001
        out["ir"] = "FAIL " + _err(exc)

    forms = {}

    try:
        src = generate_python(ast, spec)
        ns = {}
        exec(compile(src, "<%s>" % label, "exec"), ns)         # noqa: S102
        forms["python"] = {
            "status": "ok",
            "chars": len(src),
            "has_step": "step" in ns,
            "has_is_goal": "is_goal" in ns,
        }
    except Exception as exc:                                   # noqa: BLE001
        forms["python"] = {"status": "FAIL", "error": _err(exc)}

    try:
        domain, instance = generate_pddl(ast, problem=spec)
        forms["pddl"] = {"status": "ok",
                         "domain_chars": len(domain),
                         "problem_chars": len(instance)}
    except Exception as exc:                                   # noqa: BLE001
        forms["pddl"] = {"status": "FAIL", "error": _err(exc)}

    try:
        md = generate_markdown(ast, ir)
        forms["markdown"] = {"status": "ok", "chars": len(md)}
    except Exception as exc:                                   # noqa: BLE001
        forms["markdown"] = {"status": "FAIL", "error": _err(exc)}

    try:
        lean = generate_lean(ast, spec)
        forms["lean"] = {"status": "ok", "chars": len(lean)}
    except Exception as exc:                                   # noqa: BLE001
        forms["lean"] = {"status": "FAIL", "error": _err(exc)}

    out["forms"] = forms
    return out


def main():
    results = [run(*c) for c in CASES]
    json.dump({"root": ROOT, "results": results}, sys.stdout,
              indent=2, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    try:
        main()
    except Exception:                                          # noqa: BLE001
        traceback.print_exc()
        sys.exit(2)
