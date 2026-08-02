"""C15 — the fourth form, in a world `gen_pddl` can actually compile.

`probe_fourth_form.py` measured the 1x8 bar and found `gen_pddl` refusing every
case, including the arm's *working* shape, for a reason that has nothing to do
with R2-2: `colored(<cell>, n)` has no STRIPS image in this subset. A refusal
that lands equally hard on the good manual is not enforcement of anything, so it
cannot be quoted as "the fourth form agrees".

`FINDING.md:207-211` predicted this precisely:

    a manual that reaches `gen_pddl` and writes a landmark would still be
    compiled by it. Named, not fixed.

This probe tests that prediction where it is testable: the checked-in `cart`
world, which `gen_pddl` compiles today (`tests/test_gen_pddl.py`), carrying a
declared `landmark origin`. Three manuals, each a one-line edit of the fixture:

* **BASE**    — the fixture unchanged. All four forms compile it. The control.
* **WRITES_LANDMARK** — an event declared `writes {c}`, applied to `origin`. The
  write set is a *cell*. This is the R2-2 trap, in a world PDDL can reach.
* **WRITES_CELL_TERM** — the same, applied to `toward(Cart, up)`.

If `gen_pddl` compiles either of the last two while the other three refuse, the
refusal is not in force in the fourth form, and a contract clause resting on it
would be false as written.

Offline. Reads only `tests/fixtures/`; no network, no model call, no level data
from any game.
"""

import json
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

# The events must be ones `gen_pddl` actually implements, or it refuses on the
# event name before it ever reaches the write target and the probe measures
# nothing. A first draft used `painted(c) writes { c }` and got exactly that:
# *"no STRIPS encoding for event painted/1"* -- a true refusal, of the wrong
# thing. `recolored/2` and `vanished/1` are both in this backend's table and
# both take their write set from v0.3 §3, `{o}`, so passing a landmark as
# argument 0 puts a *cell* in the write set through a door PDDL can reach.
_EVENT_OLD = "  event moved(o, dir) | teleported(o, dest)"
_EVENT_NEW = ("  event moved(o, dir) | teleported(o, dest)"
              " | recolored(o, c) | vanished(o)")

_RULE = """
  rule paint_the_landmark [ev: t7 cov: 1/1]
    when act=push(Cart, down) and above(Cart) = wall then %s
"""


def _variant(effect):
    return (BASE.replace(_EVENT_OLD, _EVENT_NEW)
                .replace("\ngoal:", _RULE % effect + "\ngoal:"))


WRITES_LANDMARK = _variant("recolored(origin, 1)")
VANISHES_LANDMARK = _variant("vanished(origin)")
WRITES_CELL_TERM = _variant("recolored(toward(Cart, up), 1)")

CASES = [("BASE (the fixture, unedited)", BASE),
         ("WRITES_LANDMARK   then recolored(origin, 1)", WRITES_LANDMARK),
         ("VANISHES_LANDMARK then vanished(origin)", VANISHES_LANDMARK),
         ("WRITES_CELL_TERM  then recolored(toward(Cart, up), 1)",
          WRITES_CELL_TERM)]

FORMS = ("gen_python", "gen_lean", "gen_markdown", "gen_pddl")


def attempt(form, text, problem):
    ast = parse_theory(text)
    try:
        if form == "gen_python":
            generate_python(ast, problem)
        elif form == "gen_lean":
            generate_lean(ast, problem)
        elif form == "gen_markdown":
            generate_markdown(ast)
        elif form == "gen_pddl":
            generate_pddl(ast, "cart-instance", 3, 2, problem=problem)
        else:
            raise AssertionError(form)
    except Exception as exc:  # noqa: BLE001 -- the verdict is the point
        return type(exc).__name__, " ".join(str(exc).split())
    return "compiled", ""


def main():
    problem = load_problem(os.path.join(FIXTURES, "cart_problem.json"))
    rows = []
    print("C15 - writing a cell in a world `gen_pddl` compiles\n")
    for label, text in CASES:
        print(label)
        for form in FORMS:
            verdict, detail = attempt(form, text, problem)
            rows.append({"case": label, "form": form, "verdict": verdict,
                         "detail": detail})
            print("   %-13s %s" % (form, verdict))
            if detail:
                print("       %s" % detail[:130])
        print()

    leaks = [r for r in rows
             if r["form"] == "gen_pddl" and r["verdict"] == "compiled"
             and r["case"] != CASES[0][0]]
    print("LEAK: gen_pddl compiled %d manual(s) that write a cell" % len(leaks))
    for r in leaks:
        print("   %s" % r["case"])

    out = os.path.join(HERE, "PDDL_LEAK.json")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"cases": rows, "leaks": [r["case"] for r in leaks]},
                  fh, indent=2, sort_keys=True)
        fh.write("\n")
    print("\nwrote %s" % out)


if __name__ == "__main__":
    main()
