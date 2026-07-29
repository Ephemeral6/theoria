"""Compile one manual against one level under a chosen theory_compiler root.

Usage:  python probe_compat.py <package-root> <theory.dsl> <problem.json> <label>

`package-root` is the directory that CONTAINS the `theory_compiler` package, so
the baseline copy and the working tree can be driven by the same script.
Every stage is caught separately: a backend that raises must not hide whether
the backends after it would have succeeded.
"""
import io
import json
import sys
import traceback

root, dsl_path, problem_path, label = sys.argv[1:5]
sys.path.insert(0, root)

import theory_compiler  # noqa: E402
print("== %s ==" % label)
print("package file: %s" % theory_compiler.__file__)

from theory_compiler.parser.theory_parser import parse_theory  # noqa: E402
from theory_compiler.problem import load_problem  # noqa: E402
from theory_compiler.ir import build_ir  # noqa: E402
from theory_compiler.generators.gen_python import generate_python  # noqa: E402
from theory_compiler.generators.gen_pddl import generate_pddl  # noqa: E402
from theory_compiler.generators.gen_markdown import generate_markdown  # noqa: E402
from theory_compiler.generators.gen_lean import generate_lean  # noqa: E402

results = {}


def stage(name, fn):
    print("\n--- stage: %s ---" % name)
    try:
        out = fn()
    except BaseException as exc:
        tb = traceback.format_exc()
        print("RAISED %s.%s: %s" % (type(exc).__module__, type(exc).__name__, exc))
        print(tb)
        results[name] = {"ok": False,
                         "exc": "%s.%s" % (type(exc).__module__, type(exc).__name__),
                         "msg": str(exc),
                         "traceback": tb}
        return None
    print("OK")
    results[name] = {"ok": True}
    if isinstance(out, str):
        results[name]["chars"] = len(out)
        print("(%d chars)" % len(out))
    return out


text = open(dsl_path, encoding="utf-8").read()
problem = load_problem(problem_path)

ast = stage("parse_theory", lambda: parse_theory(text))
ir = None
if ast is not None:
    ir = stage("build_ir", lambda: build_ir(ast, problem))
    if ir is not None:
        warns = list(getattr(ir, "warnings", []) or [])
        print("ir.warnings (%d): %r" % (len(warns), warns))
        results["build_ir"]["warnings"] = warns

    py = stage("gen_python", lambda: generate_python(ast, problem))
    if py is not None:
        # A generated predictor is only "working" if it imports and steps.
        def _exec():
            ns = {}
            exec(compile(py, "<predictor>", "exec"), ns)
            return ns
        ns = stage("exec_predictor", _exec)
        if ns is not None:
            print("predictor names: %s"
                  % sorted(k for k in ns if not k.startswith("_"))[:40])
            open("%s.predictor.py" % label, "w", encoding="utf-8").write(py)

    stage("gen_pddl", lambda: generate_pddl(ast, "sokoban2-match",
                                            problem.width, problem.height))
    stage("gen_markdown", lambda: generate_markdown(ast, ir))
    stage("gen_lean", lambda: generate_lean(ast, problem))

print("\n== RESULT JSON %s ==" % label)
print(json.dumps(results, ensure_ascii=False, indent=1))
