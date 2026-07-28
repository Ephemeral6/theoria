"""Dump whichever forms succeed, so baseline and current can be diffed as bytes.

Usage: python dump_forms.py <package-root> <theory.dsl> <problem.json> <outdir>
"""
import os
import sys
import traceback

root, dsl_path, problem_path, outdir = sys.argv[1:5]
sys.path.insert(0, root)
os.makedirs(outdir, exist_ok=True)

from theory_compiler.parser.theory_parser import parse_theory
from theory_compiler.problem import load_problem
from theory_compiler.ir import build_ir
from theory_compiler.generators.gen_python import generate_python
from theory_compiler.generators.gen_pddl import generate_pddl
from theory_compiler.generators.gen_markdown import generate_markdown
from theory_compiler.generators.gen_lean import generate_lean


def write(name, text):
    with open(os.path.join(outdir, name), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print("wrote %s (%d chars)" % (name, len(text)))


def attempt(name, fn):
    try:
        return fn()
    except BaseException:
        write(name + ".ERROR.txt", traceback.format_exc())
        return None


ast = parse_theory(open(dsl_path, encoding="utf-8").read())
problem = load_problem(problem_path)
ir = attempt("ir", lambda: build_ir(ast, problem))
if ir is not None:
    write("warnings.txt", "\n".join(getattr(ir, "warnings", []) or []) + "\n")

py = attempt("theory.py", lambda: generate_python(ast, problem))
if py is not None:
    write("theory.py", py)

pd = attempt("domain.pddl", lambda: generate_pddl(ast, "sokoban2-match",
                                                  problem.width, problem.height))
if pd is not None:
    write("domain.pddl", pd[0])
    write("problem.pddl", pd[1])

md = attempt("theory.md", lambda: generate_markdown(ast, ir))
if md is not None:
    write("theory.md", md)

ln = attempt("theory.lean", lambda: generate_lean(ast, problem))
if ln is not None:
    write("theory.lean", ln)
