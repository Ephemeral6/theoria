"""Scratch: two assumptions the C15 test file rests on, checked before it is written.

(1) `appeared(<landmark>)` — allocation. Does an event that brings a thing into
    existence let a manual reach a cell no instance stands on?
(2) Does `gen_pddl` compile the cart world when a landmark appears in a GUARD
    (as opposed to an effect target)? The read/write asymmetry the verdict rests
    on has to hold in the fourth form too, or it is only a three-form claim.

Kept in the run directory rather than deleted: these are the two checks that
decide whether the contract's read/write line is a measurement or a guess.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TC = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(TC, "src"))

from theory_compiler.generators.gen_lean import generate_lean  # noqa: E402
from theory_compiler.generators.gen_markdown import generate_markdown  # noqa: E402
from theory_compiler.generators.gen_pddl import generate_pddl  # noqa: E402
from theory_compiler.generators.gen_python import generate_python  # noqa: E402
from theory_compiler.parser.theory_parser import parse_theory  # noqa: E402
from theory_compiler.problem import load_problem  # noqa: E402

FIXTURES = os.path.join(TC, "tests", "fixtures")
with open(os.path.join(FIXTURES, "cart_theory.dsl"), encoding="utf-8") as fh:
    BASE = fh.read()

_EVENT_OLD = "  event moved(o, dir) | teleported(o, dest)"
_EVENT_NEW = ("  event moved(o, dir) | teleported(o, dest)"
              " | recolored(o, c) | appeared(o)")
_RULE = """
  rule extra [ev: t7 cov: 1/1]
    when act=push(Cart, down) and %s then %s
"""


def variant(guard, effect):
    return (BASE.replace(_EVENT_OLD, _EVENT_NEW)
                .replace("\ngoal:", _RULE % (guard, effect) + "\ngoal:"))


CASES = [
    ("(1) appeared(origin) -- allocation at a cell",
     variant("above(Cart) = wall", "appeared(origin)")),
    ("(2) landmark in the GUARD only, instance in the effect",
     variant("free(origin)", "recolored(Cart, 1)")),
]

FORMS = ("gen_python", "gen_lean", "gen_markdown", "gen_pddl")


def attempt(form, text, problem):
    ast = parse_theory(text)
    try:
        {"gen_python": lambda: generate_python(ast, problem),
         "gen_lean": lambda: generate_lean(ast, problem),
         "gen_markdown": lambda: generate_markdown(ast),
         "gen_pddl": lambda: generate_pddl(ast, "cart-instance", 3, 2,
                                           problem=problem)}[form]()
    except Exception as exc:  # noqa: BLE001
        return type(exc).__name__, " ".join(str(exc).split())
    return "compiled", ""


def main():
    problem = load_problem(os.path.join(FIXTURES, "cart_problem.json"))
    for label, text in CASES:
        print(label)
        for form in FORMS:
            verdict, detail = attempt(form, text, problem)
            print("   %-13s %s" % (form, verdict))
            if detail:
                print("       %s" % detail[:160])
        print()


if __name__ == "__main__":
    main()
