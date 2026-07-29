"""Emit all four co-derived forms for the peg family, for one src tree.

Usage:  python gen_forms.py <src_dir> <out_dir>

Writes, per manual:
  <manual>.python.py  <manual>.domain.pddl  <manual>.problem.pddl
  <manual>.md         <manual>.computational.lean  <manual>.algebraic.lean
  <manual>.warnings.txt
and, on failure, <manual>.<form>.ERROR.txt holding the traceback.
"""
import json
import os
import sys
import traceback

SRC, OUT = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
sys.path.insert(0, SRC)
os.makedirs(OUT, exist_ok=True)

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
FIX = os.path.join(REPO, "theory-compiler", "tests", "fixtures")

from theory_compiler.parser.theory_parser import parse_theory
from theory_compiler.problem import load_problem
from theory_compiler.ir import build_ir
from theory_compiler.generators.gen_python import generate_python
from theory_compiler.generators.gen_pddl import generate_pddl
from theory_compiler.generators.gen_markdown import generate_markdown
from theory_compiler.generators.gen_lean import generate_lean
from theory_compiler.certificate import load_certificate
from theory_compiler.ic3_certificate import load_ic3_certificate

PAGODA = os.path.join(REPO, "engine-rig", "interop", "certificates",
                      "pagoda_5_11011_to_00010.json")
IC3 = os.path.join(FIX, "ic3_peg4_0111_to_0100.json")

MANUALS = [
    # name, theory dsl, problem json, cert loader+path, pddl grid
    ("peg5", "peg_theory.dsl", "peg5_problem.json", ("pagoda", PAGODA), (5, 1)),
    ("peg4", "peg4_theory.dsl", "peg4_problem.json", ("ic3", IC3), (4, 1)),
]


def write(name, text):
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def attempt(name, fn):
    try:
        return fn()
    except Exception:
        write(name + ".ERROR.txt", traceback.format_exc())
        return None


for label, dsl, pjson, (kind, cpath), (gw, gh) in MANUALS:
    ast = parse_theory(open(os.path.join(FIX, dsl), encoding="utf-8").read())
    problem = load_problem(os.path.join(FIX, pjson))

    # ---- warnings from build_ir (no certificate, the plain route)
    def _warn():
        ir = build_ir(ast, load_problem(os.path.join(FIX, pjson)))
        return json.dumps(list(ir.warnings), indent=2, ensure_ascii=False)
    w = attempt("%s.warnings" % label, _warn)
    if w is not None:
        write("%s.warnings.txt" % label, w + "\n")

    # ---- python
    r = attempt("%s.python" % label,
                lambda: generate_python(ast, load_problem(os.path.join(FIX, pjson))))
    if r is not None:
        write("%s.python.py" % label, r)

    # ---- pddl
    r = attempt("%s.pddl" % label,
                lambda: generate_pddl(ast, problem_name=label,
                                      grid_width=gw, grid_height=gh))
    if r is not None:
        write("%s.domain.pddl" % label, r[0])
        write("%s.problem.pddl" % label, r[1])

    # ---- markdown (both routes: bare, and with an IR)
    r = attempt("%s.markdown" % label, lambda: generate_markdown(ast))
    if r is not None:
        write("%s.md" % label, r)
    r = attempt("%s.markdown_ir" % label, lambda: generate_markdown(
        ast, build_ir(ast, load_problem(os.path.join(FIX, pjson)))))
    if r is not None:
        write("%s.ir.md" % label, r)

    # ---- lean, both proof modes
    for mode in ("computational", "algebraic"):
        def _lean(mode=mode):
            cert = (load_certificate(cpath) if kind == "pagoda"
                    else load_ic3_certificate(cpath))
            return generate_lean(ast, load_problem(os.path.join(FIX, pjson)),
                                 cert, proof=mode)
        r = attempt("%s.lean.%s" % (label, mode), _lean)
        if r is not None:
            write("%s.%s.lean" % (label, mode), r)

print("done:", OUT)
