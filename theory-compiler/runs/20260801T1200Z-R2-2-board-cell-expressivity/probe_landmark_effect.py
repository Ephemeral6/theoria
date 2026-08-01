"""What `recolored(<landmark>, 1)` compiled to, printed rather than described.

This is GAP R2-2's trap. `probe_grammar.py` S3 first measured it: the spelling
compiled in `gen_python`, the rule fired, and the cell did not change. That
combination is worse than a refusal, and a claim about a silent miscompile has
to be readable to be believed.

**The fix that came out of this run destroys the evidence for it** —
`ir._check_write_targets` now refuses the manual before a predictor exists. So
this script runs the case twice: once with that check disabled, which is what
the compiler did up to 2026-08-01 and is the defect report; and once as
shipped, which is the refusal. Reproducing a fixed bug requires saying which
version you are reproducing, and the alternative is a defect claim nobody can
re-run.

Offline; no network, no model, no ARC.
"""

from __future__ import annotations

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TC = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(TC, "src"))

from theory_compiler.generators.gen_python import generate_python  # noqa: E402
from theory_compiler.parser.theory_parser import parse_theory  # noqa: E402
from theory_compiler.problem import from_json  # noqa: E402
from theory_compiler.writes import WriteSets  # noqa: E402
from theory_compiler.ir import build_ir  # noqa: E402

MANUAL = """semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Spent { pos: Coord, color: Int }
  landmark edge  # arc-cell: (0, 5)

events:
  event recolored(o, c)

rules:
  rule edge_burns
    when act=key(2) and colored(edge, 9) then recolored(edge, 1)

goal:
  goal count(Spent, color = 1) = 8
"""

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


def main() -> int:
    ast = parse_theory(MANUAL)
    problem = from_json(PROBLEM)

    # ---- as shipped: the refusal ----------------------------------------
    print("=" * 72)
    print("AS SHIPPED (2026-08-01 onward)")
    print("=" * 72)
    try:
        build_ir(ast, problem)
        print("   NO REFUSAL -- the check is not in this build.")
    except Exception as exc:  # noqa: BLE001
        print("   %s" % type(exc).__name__)
        for line in _wrap(str(exc)):
            print("   " + line)
    print()

    # ---- before the check: the defect ------------------------------------
    # Disabled deliberately and locally, so the defect report re-runs. This is
    # the one place in the repository that turns a check off, and it does it to
    # show what the check is for.
    import theory_compiler.ir as ir_mod
    original = ir_mod._check_write_targets
    ir_mod._check_write_targets = lambda *a, **k: []
    try:
        return _show_the_defect(ast, problem)
    finally:
        ir_mod._check_write_targets = original


def _wrap(text: str, width: int = 68):
    words, line, out = text.split(), "", []
    for word in words:
        if len(line) + len(word) + 1 > width:
            out.append(line)
            line = word
        else:
            line = (line + " " + word).strip()
    if line:
        out.append(line)
    return out


def _show_the_defect(ast, problem) -> int:
    ir = build_ir(ast, problem)
    text = generate_python(ast, problem)

    print("=" * 72)
    print("BEFORE THE CHECK (the defect, with ir._check_write_targets disabled)")
    print("=" * 72)
    print("the manual says: when key(2) and cell (0,5) reads 9, it becomes 1")
    print()
    print("`writes(edge_burns)` per CONTRACTS/dsl_grammar_v0.3.md section 1:")
    print("   %r" % (sorted(WriteSets(ast).of_rule(ir.rules[0])),))
    print("   -- `edge` is a LANDMARK, not an object instance. The definition")
    print("      says `the set of object instances whose observations the event")
    print("      assigns`, and nothing checks that the name is one.")
    print()
    print("the compiled effect:")
    for block in re.findall(r"def _effect_edge_burns\(state\):\n(?:.+\n)+?\n",
                            text):
        print("   " + block.strip().replace("\n", "\n   "))
    print()
    print("the State dataclass it assigns into:")
    body = re.search(r"class State:\n((?:    .*\n|\n)+?)    def copy", text)
    for line in body.group(1).strip().splitlines():
        print("   " + line.strip())
    print("   -- there is no `edge_color` field. `State` is a plain dataclass,")
    print("      so the assignment SUCCEEDS and creates an attribute nothing")
    print("      reads. `key()` does not include it, so two states differing")
    print("      only in it compare equal.")
    print()
    print("and `render` rebuilds the board fresh every call:")
    grid_line = next(ln for ln in text.splitlines()
                     if ln.strip().startswith("grid = "))
    print("   " + grid_line.strip())
    print("   -- BOARD is a compile-time constant of the level. A cell no")
    print("      instance stands on renders BOARD's colour, always.")
    print()

    ns: dict = {}
    exec(compile(text, "<theory.py>", "exec"), ns)  # noqa: S102
    s0 = ns["initial_state"]()
    s1 = ns["step"](s0, ("key", 2))
    print("run it:")
    print("   rules fired   %s" % (ns["fired"](s0, ("key", 2)),))
    print("   row before    %s" % (ns["render"](s0)[0],))
    print("   row after     %s" % (ns["render"](s1)[0],))
    print("   states equal  %s" % (s0.key() == s1.key(),))
    print("   the leaked attribute: state.edge_color = %r"
          % (getattr(s1, "edge_color", "<absent>"),))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
