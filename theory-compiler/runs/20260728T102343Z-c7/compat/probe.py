"""Compile the cold-start-a2 manual family with one `theory_compiler` tree.

Run once per tree (baseline / current), into separate output directories, then
diff the directories. Runs in a subprocess so the two trees never share a module
cache -- `theory_compiler` is imported by absolute name in both, and an
in-process second import would silently reuse the first tree's modules.
"""

import argparse
import json
import os
import sys
import traceback

REPO = None  # set from argv


def _manuals():
    return [
        ("a2", "cold-start-a2/theory/theory.dsl",
         "cold-start-a2/theory/generated/problem.json"),
        ("a2-holed", "cold-start-a2/theory/theory_holed.dsl",
         "cold-start-a2/theory/generated_holed/problem.json"),
        ("a2-repaired", "cold-start-a2/theory/theory_repaired.dsl",
         "cold-start-a2/theory/generated_repaired/problem.json"),
    ]


def _report_dict(report):
    """Everything the ConflictReport holds, in a diffable shape."""
    return {
        "policy": report.policy,
        "green": report.green,
        "summary": report.summary(),
        "overlapping": [[a, b, list(objs)] for a, b, objs in report.overlapping],
        "disjoint": [[a, b, why] for a, b, why in report.disjoint],
        "ordered": [list(p) for p in report.ordered],
        "undischarged": [[a, b, list(objs)] for a, b, objs in report.undischarged],
        "unclaimable": [[n, why] for n, why in report.unclaimable],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--repo", required=True)
    args = ap.parse_args()

    sys.path.insert(0, os.path.abspath(args.src))
    os.makedirs(args.out, exist_ok=True)

    import inspect

    from theory_compiler.parser.theory_parser import parse_theory
    from theory_compiler.ir import build_ir
    from theory_compiler.problem import load_problem
    from theory_compiler.conflict import Uniqueness, check_conflict
    from theory_compiler.generators.gen_python import generate_python
    from theory_compiler.generators.gen_pddl import generate_pddl
    from theory_compiler.generators.gen_markdown import generate_markdown
    from theory_compiler.generators.gen_lean import generate_lean

    import theory_compiler.generators.gen_python as gp
    provenance = {
        "src": os.path.abspath(args.src),
        "resolved_package": os.path.dirname(gp.__file__),
        "check_conflict_params": list(
            inspect.signature(check_conflict).parameters),
    }

    summary = {"provenance": provenance, "manuals": {}}

    for name, dsl_rel, prob_rel in _manuals():
        dsl = os.path.join(args.repo, dsl_rel)
        prob = os.path.join(args.repo, prob_rel)
        entry = {"dsl": dsl_rel, "problem": prob_rel, "forms": {}}
        summary["manuals"][name] = entry

        try:
            ast = parse_theory(open(dsl, encoding="utf-8").read())
            problem = load_problem(prob)
            ir = build_ir(ast, problem)
        except Exception:
            entry["fatal"] = traceback.format_exc()
            continue

        entry["warnings"] = list(ir.warnings)

        # ---- conflict, called exactly as this tree's `build_ir` calls it
        try:
            uniq = Uniqueness(ast, ir.problem)
            kwargs = {}
            if "writes" in provenance["check_conflict_params"]:
                kwargs["writes"] = ir.writes
            report = check_conflict(ir.rules, ir.semantics,
                                    ir.problem.background, strict=False,
                                    uniq=uniq, **kwargs)
            entry["conflict"] = _report_dict(report)
            entry["conflict"]["ground_rules"] = [r.name for r in ir.rules]
        except Exception:
            entry["conflict_error"] = traceback.format_exc()

        # ---- the four forms
        def emit(form, fname, fn):
            try:
                text = fn()
            except Exception:
                entry["forms"][form] = {"status": "ERROR",
                                        "traceback": traceback.format_exc()}
                return
            path = os.path.join(args.out, "%s.%s" % (name, fname))
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
            entry["forms"][form] = {"status": "OK", "file": os.path.basename(path),
                                    "bytes": len(text.encode("utf-8"))}

        emit("gen_python", "theory.py", lambda: generate_python(ast, problem))
        emit("gen_markdown", "theory.md", lambda: generate_markdown(ast, ir))
        emit("gen_pddl_domain", "domain.pddl",
             lambda: generate_pddl(ast, problem_name=name)[0])
        emit("gen_pddl_problem", "problem.pddl",
             lambda: generate_pddl(ast, problem_name=name)[1])
        emit("gen_lean", "theory.lean", lambda: generate_lean(ast, problem))

    with open(os.path.join(args.out, "summary.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False, sort_keys=True)
    print(json.dumps(provenance, indent=2))


if __name__ == "__main__":
    main()
