"""The decisive counter-test: is R2-2 a GRAMMAR hole or an ARM hole?

`theoria-arm`'s r3 manual blames its own instance seating —
*"the arm offers exactly one lever, `arc-instances: all`, and its documented
behaviour is to instance every cell OF THAT COLOUR THE BOARD CANNOT EXPLAIN"*.
If that is the whole story, then a level that simply seats an instance on the
virgin cell makes the existing grammar say the edge advance with no extension
at all, and GAP R2-2 belongs to `theoria-arm` rather than to `theory-compiler`.

This script runs that experiment. Same manual, three levels, differing only in
which cells carry an instance. Offline; no network, no model, no ARC.

    python probe_seating.py            # human-readable
    python probe_seating.py --json     # SEATING.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TC = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(TC, "src"))

from theory_compiler.generators.gen_python import generate_python  # noqa: E402
from theory_compiler.parser.theory_parser import parse_theory  # noqa: E402
from theory_compiler.problem import from_json  # noqa: E402

# One manual. It is the arm's own shape (S1 of `probe_grammar.py`) written to
# advance an edge: the burned cell's left neighbour, itself still colour 9,
# becomes colour 1. Nothing here is new grammar.
MANUAL = """semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Bar { pos: Coord, color: Int }   # arc-colour: 9/1

events:
  event recolored(o, c)

rules:
  rule edge_advance forall ?p in Bar
    when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

goal:
  goal count(Bar, color = 1) = 8
"""

BOARD = [[9, 9, 9, 9, 9, 9, 9, 9]]


def level(name: str, seated: list[int]) -> dict:
    """`seated` names the columns the level puts an instance on."""
    return {
        "name": name,
        "grid": [1, 8],
        "background": 0,
        "board": BOARD,
        "objects": [{"name": "Bar_%d" % c, "type": "Bar", "pos": [0, c],
                     "color": 1 if c >= 6 else 9} for c in seated],
        "arena": [[0, c] for c in range(8)],
    }


LEVELS = [
    ("L1-varied-only",
     "what the arm actually builds: an instance only where a cell has already "
     "varied, i.e. the two burned cells",
     [6, 7]),
    ("L2-varied-plus-edge",
     "the arm's seating plus ONE instance on the next virgin cell",
     [5, 6, 7]),
    ("L3-every-cell",
     "an instance on every cell of the bar, varied or not",
     [0, 1, 2, 3, 4, 5, 6, 7]),
]


def run_level(seated: list[int], name: str) -> dict:
    ast = parse_theory(MANUAL)
    problem = from_json(level(name, seated))
    try:
        text = generate_python(ast, problem)
    except Exception as exc:  # noqa: BLE001
        return {"compiles": False, "error": "%s: %s" % (type(exc).__name__, exc)}
    ns: dict = {}
    exec(compile(text, "<theory.py>", "exec"), ns)  # noqa: S102
    s0 = ns["initial_state"]()
    row0 = ns["render"](s0)[0]
    s1 = ns["step"](s0, ("key", 2))
    row1 = ns["render"](s1)[0]
    return {
        "compiles": True,
        "error": None,
        "ground_rules": [r[0] for r in ns["RULES"]],
        "fired": ns["fired"](s0, ("key", 2)),
        "row_before": row0,
        "row_after": row1,
        # The law says exactly one more cell burns, and it is col 5.
        "edge_advanced": row1[5] == 1,
        "only_the_edge_moved": (row1 == row0[:5] + [1] + row0[6:]),
    }


def run() -> dict:
    return {
        "question": "is R2-2 a grammar hole or an instance-seating hole?",
        "manual": MANUAL,
        "results": [dict(level=k, why=w, seated=s, **run_level(s, k))
                    for k, w, s in LEVELS],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    report = run()
    if args.json:
        path = os.path.join(HERE, "SEATING.json")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report, fh, indent=2, sort_keys=True)
            fh.write("\n")
        print("wrote", path)
        return 0
    for r in report["results"]:
        print("== %s  (instances on cols %s)" % (r["level"], r["seated"]))
        print("   %s" % r["why"])
        if not r["compiles"]:
            print("   REFUSED  %s\n" % r["error"])
            continue
        print("   ground rules  %s" % (r["ground_rules"],))
        print("   fired         %s" % (r["fired"],))
        print("   row before    %s" % (r["row_before"],))
        print("   row after     %s" % (r["row_after"],))
        print("   edge advanced %s   only the edge moved %s"
              % (r["edge_advanced"], r["only_the_edge_moved"]))
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
