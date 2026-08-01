"""What, exactly, can the v0.3 grammar not say about a cell that has never varied?

GAP R2-2 (`theoria-arm/GAPS.md`) says the arm can now *predict* an edge advance
and cannot *write it down*. `theoria-arm`'s own manual
(`runs/20260731T1430Z-A3-level2-carried-r3/books/theory.dsl`, theorem
`i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed`) blames the
arm's instance seating. This script asks the compiler instead, because the arm
compiles through `theory_compiler.generators.gen_python.generate_python`
(`theoria-arm/inner/books.py`) — so whatever the compiler refuses, the arm cannot
write regardless of how it seats instances.

Nine spellings of one sentence — *the cell left of the leftmost burned cell
burns* — put through the real parser and the real four backends. Offline; no
network, no model, no ARC.

    python probe_grammar.py            # human-readable
    python probe_grammar.py --json     # PROBE.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
TC = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(TC, "src"))

from theory_compiler.generators.gen_lean import generate_lean  # noqa: E402
from theory_compiler.generators.gen_markdown import generate_markdown  # noqa: E402
from theory_compiler.generators.gen_pddl import generate_pddl  # noqa: E402
from theory_compiler.generators.gen_python import generate_python  # noqa: E402
from theory_compiler.ir import build_ir  # noqa: E402
from theory_compiler.parser.theory_parser import parse_theory  # noqa: E402
from theory_compiler.problem import from_json  # noqa: E402

# The four forms do not share a signature, and calling one with another's
# argument list is how a probe comes to report a refusal it invented. Each is
# wrapped here once, by name, so the call site is checkable.
#   generate_python(ast, problem)      -> str
#   generate_pddl(ast, problem_name, grid_w, grid_h, problem=...)  -> (str, str)
#   generate_markdown(ast, ir=None)    -> str        <- an IR, NOT a problem
#   generate_lean(ast, problem, ...)   -> str
FORMS = (
    ("gen_python", lambda ast, p: generate_python(ast, p)),
    ("gen_pddl", lambda ast, p: generate_pddl(ast, problem_name=p.name,
                                              problem=p)),
    ("gen_markdown", lambda ast, p: generate_markdown(ast, build_ir(ast, p))),
    ("gen_lean", lambda ast, p: generate_lean(ast, p)),
)

# --------------------------------------------------------------------- the world
#
# The smallest world that reproduces `theoria-arm`'s row-63 meter. One row of
# eight cells, all painted colour 9 on the board. The two rightmost have already
# burned to colour 1, so they have varied and the arm seats an instance on each.
# Cols 0-5 have never varied: they are board, and no instance exists on them.
#
# The law is the arm's: one command, and the cell left of the leftmost burn
# burns. Its next victim is col 5 — a board cell.

PROBLEM = {
    "name": "burn-bar",
    "grid": [1, 8],
    "background": 0,
    "board": [[9, 9, 9, 9, 9, 9, 9, 9]],
    "objects": [
        {"name": "Spent_6", "type": "Spent", "pos": [0, 6], "color": 1},
        {"name": "Spent_7", "type": "Spent", "pos": [0, 7], "color": 1},
    ],
    "landmarks": {"edge": [0, 5]},
    "arena": [[0, c] for c in range(8)],
}

PREAMBLE = """semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Spent { pos: Coord, color: Int }   # arc-colour: 1  arc-instances: all
  landmark edge  # arc-cell: (0, 5)

events:
  event recolored(o, c) | stayed(o) writes {}

rules:
"""

GOAL = "\n\ngoal:\n  goal count(Spent, color = 1) = 8\n"


def manual(rules: str) -> str:
    return PREAMBLE + rules + GOAL


# ------------------------------------------------------- the nine spellings
#
# Each is one attempt to say: *the cell left of the leftmost burned cell burns*.

SPELLINGS = [
    (
        "S1-bound-object-target",
        "the shape the arm actually writes: quantify over the type, recolour the "
        "bound variable. Correct, and it can only ever name a cell that has "
        "already varied.",
        """  rule edge_advance forall ?s in Spent
    when act=key(2) and colored(?s, 1) then recolored(?s, 1)
""",
    ),
    (
        "S2-cell-term-target",
        "recolour a CELL TERM: `leftof(?s)` denotes the virgin cell exactly. This "
        "is the sentence GAP R2-2 says cannot be written.",
        """  rule edge_advance forall ?s in Spent
    when act=key(2) and colored(?s, 1) and colored(leftof(?s), 9) then recolored(leftof(?s), 1)
""",
    ),
    (
        "S3-landmark-target",
        "recolour a declared LANDMARK. Landmarks are cells and the level locates "
        "them, so `edge` names the board cell (0,5) with no instance needed.",
        """  rule edge_advance
    when act=key(2) and colored(edge, 9) then recolored(edge, 1)
""",
    ),
    (
        "S4-landmark-guard-object-target",
        "control: a landmark in the GUARD and an object in the effect. This is "
        "what r3's thirteen panel rules do with `spawn_probe`.",
        """  rule edge_advance forall ?s in Spent
    when act=key(2) and colored(edge, 9) and colored(?s, 1) then recolored(?s, 1)
""",
    ),
    (
        "S5-appeared-on-cell-term",
        "a different event, same question: can any event's first argument be a "
        "cell term rather than an object name?",
        """  rule edge_advance forall ?s in Spent
    when act=key(2) and colored(?s, 1) then appeared(leftof(?s))
""",
    ),
    (
        "S6-moved-onto-board-cell",
        "sidestep the colour: MOVE an existing instance onto the virgin cell "
        "instead of recolouring it.",
        """  rule edge_advance forall ?s in Spent
    when act=key(2) and colored(?s, 1) and colored(leftof(?s), 9) then moved(?s, left)
""",
    ),
    (
        "S7-forall-over-domain-not-type",
        "bind over a declared VALUE domain rather than an object type, so the "
        "rule is not tied to seated instances.",
        """  rule edge_advance forall ?d in dir
    when act=key(2) and colored(edge, 9) then recolored(edge, 1)
""",
    ),
    (
        "S8-field-access-target",
        "name the target the long way: `?s.pos` is a cell, so is the effect "
        "argument allowed to be one?",
        """  rule edge_advance forall ?s in Spent
    when act=key(2) and colored(?s, 1) then recolored(?s.pos, 1)
""",
    ),
    (
        "S9-second-type-on-same-colour",
        "the workaround r3 rejects in prose: declare a SECOND type on colour 9 "
        "and hope the arm seats an instance on the virgin cell. Compiled here "
        "with the level supplying no instance of it, which is the honest case.",
        """  rule edge_advance forall ?p in Bar
    when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)
""",
    ),
]

# S7 needs a value domain; S9 needs a second declared type. Both are word_table
# additions, so they get their own preamble rather than a mutated shared one.
PREAMBLE_OVERRIDE = {
    "S7-forall-over-domain-not-type": PREAMBLE.replace(
        "  landmark edge", "  landmark edge  # arc-cell: (0, 5)\n"
        "  domain dir { up, down, left, right }"),
    "S9-second-type-on-same-colour": PREAMBLE.replace(
        "  landmark edge",
        "  object Bar   { pos: Coord, color: Int }   # arc-colour: 9\n"
        "  landmark edge"),
}


def _outcome(fn, ast, problem) -> dict:
    try:
        out = fn(ast, problem)
    except Exception as exc:  # noqa: BLE001 — the refusal IS the measurement
        return {"ok": False, "error": type(exc).__name__,
                "message": str(exc).strip(), "text": None}
    return {"ok": True, "error": None, "message": "",
            "text": out if isinstance(out, str) else None}


def _burns(module_text: str) -> dict:
    """Execute the generated predictor and ask the only question that matters:
    after one `key(2)`, does cell (0,5) — the virgin one — read colour 1?

    A form that compiles and does not burn is worse than one that refuses: it is
    a manual that says something and means nothing.
    """
    ns: dict = {}
    try:
        exec(compile(module_text, "<theory.py>", "exec"), ns)  # noqa: S102
        s0 = ns["initial_state"]()
        before = ns["render"](s0)[0]
        after = ns["render"](ns["step"](s0, ("key", 2)))[0]
        return {"ran": True,
                "row_before": before,
                "row_after": after,
                "cell_0_5_after": after[5],
                # The law burns col 5 and touches nothing else. A spelling that
                # changes col 5 by *un*-changing another cell has not said the
                # law; it has said a different one that happens to agree here.
                "only_the_edge_moved": after == before[:5] + [1] + before[6:],
                "fired": ns["fired"](s0, ("key", 2))}
    except Exception as exc:  # noqa: BLE001
        return {"ran": False, "error": "%s: %s" % (type(exc).__name__, exc)}


def compile_all(text: str) -> dict:
    """Parse, then drive each co-derived form **independently**.

    Independently and not first-refusal-wins, because `gen_pddl` refuses this
    whole world class before it reaches the question: `act=key(2)` carries a
    numeric argument and the STRIPS backend has no ground action for it. That
    refusal lands on the arm's own working shape (S1) exactly as hard as on the
    ones under test, so it says nothing about R2-2 and must not be allowed to
    mask the forms that do.
    """
    problem = from_json(PROBLEM)
    out = {name: None for name, _ in FORMS}
    try:
        ast = parse_theory(text)
    except Exception as exc:  # noqa: BLE001
        out["parser"] = {"ok": False, "error": type(exc).__name__,
                         "message": str(exc).strip()}
        out["predictor"] = None
        return out
    out["parser"] = {"ok": True, "error": None, "message": ""}
    for name, fn in FORMS:
        out[name] = _outcome(fn, ast, problem)
    py = out["gen_python"]
    out["predictor"] = _burns(py["text"]) if py["ok"] and py["text"] else None
    for name, _ in FORMS:
        out[name].pop("text", None)
    return out


def run() -> dict:
    results = []
    for key, why, rules in SPELLINGS:
        pre = PREAMBLE_OVERRIDE.get(key, PREAMBLE)
        text = pre + rules + GOAL
        verdict = compile_all(text)
        verdict.update({"spelling": key, "intent": why, "rules": rules})
        results.append(verdict)
    import theory_compiler.ir as ir_mod
    return {
        "what": "nine spellings of `the cell left of the leftmost burn burns`, "
                "against the v0.3 parser and the four co-derived forms",
        "gap": "R2-2",
        # Self-describing, because this run both measured a defect and fixed it.
        # Without this field a reader cannot tell whether a refusal below is the
        # pre-existing grammar or the check this run added, and those are the two
        # things the whole finding is about telling apart.
        "compiler_state": ("with ir._check_write_targets (added by this run)"
                           if hasattr(ir_mod, "_check_write_targets")
                           else "before ir._check_write_targets"),
        "world": "burn-bar, 1x8, cols 0-5 never varied (board), cols 6-7 varied "
                 "(instances Spent_6 / Spent_7)",
        "results": results,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    report = run()
    if args.json:
        path = os.path.join(HERE, "PROBE.json")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report, fh, indent=2, sort_keys=True)
            fh.write("\n")
        print("wrote", path)
        return 0
    for r in report["results"]:
        print("== %s" % r["spelling"])
        print("   %s" % r["intent"])
        for form in ("parser",) + tuple(n for n, _ in FORMS):
            got = r[form]
            if got is None:
                print("   %-13s -" % form)
                continue
            if got["ok"]:
                print("   %-13s compiles" % form)
            else:
                print("   %-13s REFUSED  %s: %s"
                      % (form, got["error"], got["message"]))
        p = r["predictor"]
        if p is not None:
            if p["ran"]:
                verdict = "BURNS" if p["cell_0_5_after"] == 1 else "DOES NOT BURN"
                print("   predictor     ran; (0,5) reads %s after key(2) -> %s"
                      % (p["cell_0_5_after"], verdict))
                print("   row before    %s" % (p["row_before"],))
                print("   row after     %s   only the edge moved: %s"
                      % (p["row_after"], p["only_the_edge_moved"]))
                print("   rules fired   %s" % (p["fired"],))
            else:
                print("   predictor     CRASHED  %s" % p["error"])
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
