"""C15 — does the R2-2 refusal hold in the fourth form?

The 2026-08-01 run (`20260801T1200Z-R2-2-board-cell-expressivity`) made writing a
cell an error in `build_ir` and, separately, in `gen_markdown`. Its own residue
list, `FINDING.md:207-211`, names the hole this probe measures:

    `gen_pddl` never sees either new check. It does not call `build_ir`. It
    refuses this world class for its own reason, so nothing is currently
    hidden, but a manual that reaches `gen_pddl` and writes a landmark would
    still be compiled by it.

"Refuses for its own reason" is not the same as "refuses". C15 turns the R2-2
adjudication into a contract clause, and a clause one of the four co-derived
forms does not enforce is a clause that is not in force. So the question has to
be *measured* rather than reasoned about: strip the incidental refusal
(`act=key(2)` carries a numeric argument this STRIPS subset has no ground action
for — it lands on the arm's *working* shape exactly as hard, so it is not
evidence about R2-2) and ask what `gen_pddl` does with a landmark write on a
world it can otherwise compile.

Offline. No level data beyond the synthetic 1x8 bar, no network, no model call.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "src"))

from theory_compiler.generators.gen_pddl import generate_pddl  # noqa: E402
from theory_compiler.generators.gen_python import generate_python  # noqa: E402
from theory_compiler.generators.gen_markdown import generate_markdown  # noqa: E402
from theory_compiler.ir import build_ir  # noqa: E402
from theory_compiler.parser.theory_parser import parse_theory  # noqa: E402
from theory_compiler.problem import from_json  # noqa: E402

BOARD = [[9, 9, 9, 9, 9, 9, 9, 9]]


def level(seated, landmarks=None):
    return from_json({
        "name": "burn-bar",
        "grid": [1, 8],
        "background": 0,
        "board": BOARD,
        "objects": [{"name": "Bar_%d" % c, "type": "Bar", "pos": [0, c],
                     "color": 1 if c >= 6 else 9} for c in seated],
        "landmarks": landmarks or {},
        "arena": [[0, c] for c in range(8)],
    })


HEAD = """semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Bar { pos: Coord, color: Int }
"""

TAIL = """
goal:
  goal count(Bar, color = 1) = 8
"""

EVENTS = """
events:
  event recolored(o, c)

rules:
"""


def manual(rules, extra_word_table=""):
    return HEAD + extra_word_table + EVENTS + rules + TAIL


# `act=burn()` rather than `act=key(2)`: a nullary action, so the STRIPS subset
# has a ground action for it and `gen_pddl`'s pre-existing, declared refusal
# (v0.3 §5) does not fire. Everything else is the arm's own shape.
SEATED_OK = """  rule edge_advance forall ?p in Bar
    when act=burn() and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)
"""
LANDMARK_TARGET = """  rule edge_burns
    when act=burn() and colored(edge, 9) then recolored(edge, 1)
"""
CELL_TERM_TARGET = """  rule edge_advance forall ?p in Bar
    when act=burn() and colored(?p, 1) and colored(leftof(?p), 9) then recolored(leftof(?p), 1)
"""
LANDMARK_IN_GUARD = """  rule edge_advance forall ?p in Bar
    when act=burn() and colored(edge, 9) and colored(?p, 1) then recolored(?p, 1)
"""

LM = "  landmark edge  # arc-cell: (0, 5)\n"

CASES = [
    ("seated instance (the arm's working shape)", SEATED_OK, "", [5, 6, 7], {}),
    ("landmark as effect target", LANDMARK_TARGET, LM, [6, 7], {"edge": [0, 5]}),
    ("cell term as effect target", CELL_TERM_TARGET, "", [6, 7], {}),
    ("landmark in the GUARD, instance in the effect",
     LANDMARK_IN_GUARD, LM, [5, 6, 7], {"edge": [0, 5]}),
]

FORMS = ("build_ir", "gen_python", "gen_markdown", "gen_pddl")


def attempt(form, text, problem):
    """Return (verdict, detail). `verdict` is 'compiled' or an exception name."""
    ast = parse_theory(text)
    try:
        if form == "build_ir":
            build_ir(ast, problem)
        elif form == "gen_python":
            generate_python(ast, problem)
        elif form == "gen_markdown":
            generate_markdown(ast)
        elif form == "gen_pddl":
            generate_pddl(ast, "burn-bar", 8, 1, problem=problem)
        else:
            raise AssertionError(form)
    except Exception as exc:  # noqa: BLE001 -- the verdict is the point
        return type(exc).__name__, " ".join(str(exc).split())
    return "compiled", ""


def main():
    rows = []
    for label, rules, extra, seated, landmarks in CASES:
        text = manual(rules, extra_word_table=extra)
        problem = level(seated, landmarks)
        for form in FORMS:
            verdict, detail = attempt(form, text, problem)
            rows.append({"case": label, "form": form, "verdict": verdict,
                         "detail": detail})

    width = max(len(r["case"]) for r in rows)
    print("C15 - the R2-2 refusal across all four co-derived forms\n")
    for label, _r, _e, _s, _l in CASES:
        print(label)
        for row in (r for r in rows if r["case"] == label):
            print("   %-13s %s" % (row["form"], row["verdict"]))
            if row["detail"]:
                print("       %s" % row["detail"][:150])
        print()

    out = os.path.join(HERE, "FOURTH_FORM.json")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"cases": rows}, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print("wrote %s (%d rows, width %d)" % (out, len(rows), width))


if __name__ == "__main__":
    main()
