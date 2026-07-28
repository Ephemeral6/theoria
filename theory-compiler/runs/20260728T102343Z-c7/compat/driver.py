"""Generate all four forms for the cold-start-a0 manual family, under either
the pre-change (baseline) or post-change (current) theory_compiler tree.

Usage:  python driver.py <src_dir> <out_dir>

`src_dir` is prepended to sys.path, so it decides which compiler is measured.
Everything written under `out_dir` is a measurement, never an input.
"""
import io
import json
import pathlib
import sys
import traceback

SRC = sys.argv[1]
OUT = pathlib.Path(sys.argv[2])
sys.path.insert(0, SRC)

REPO = pathlib.Path(__file__).resolve().parents[4]   # worktree root

from theory_compiler.parser.theory_parser import parse_theory      # noqa: E402
from theory_compiler.problem import load_problem                   # noqa: E402
from theory_compiler.ir import build_ir                            # noqa: E402
from theory_compiler.generators.gen_python import generate_python  # noqa: E402
from theory_compiler.generators.gen_pddl import generate_pddl      # noqa: E402
from theory_compiler.generators.gen_markdown import generate_markdown  # noqa: E402
from theory_compiler.generators.gen_lean import generate_lean      # noqa: E402

import theory_compiler                                             # noqa: E402
assert pathlib.Path(theory_compiler.__file__).resolve().is_relative_to(
    pathlib.Path(SRC).resolve()), (
        "wrong tree imported: %s" % theory_compiler.__file__)

MANUALS = [
    ("theory",             "cold-start-a0/theory/theory.dsl",
                           "cold-start-a0/artifacts/problem_a0-base.json"),
    ("theory_no_button",   "cold-start-a0/theory/theory_no_button.dsl",
                           "cold-start-a0/artifacts/problem_a0-no-button.json"),
    ("theory_prime",       "cold-start-a0/prime/theory/theory_prime.dsl",
                           "cold-start-a0/prime/theory/generated/problem.json"),
    ("theory_prime_seeded", "cold-start-a0/prime/theory/theory_prime_seeded.dsl",
                            "cold-start-a0/prime/theory/generated_seeded/problem.json"),
]

BFS_CAP = 5000


def _write(name, text):
    (OUT / name).write_text(text, encoding="utf-8", newline="\n")


def _err(name, exc):
    _write(name, "ERROR\n" + "".join(
        traceback.format_exception(type(exc), exc, exc.__traceback__)))


def _transition_dump(ns):
    """Full transition table over the reachable set, BFS from initial_state.

    Sampling, stated exactly: start at `initial_state()`, breadth-first over
    `ACTIONS` in declaration order, deduplicating by the dataclass repr, up to
    BFS_CAP states. Then emit `state | action -> successor` for EVERY
    (reachable state, action) pair, in BFS discovery order and then ACTIONS
    order. Both the reachable set and every successor are therefore in the
    diff, not a random subsample of them.
    """
    step = ns["step"]
    actions = list(ns["ACTIONS"])
    start = ns["initial_state"]()
    order = [start]
    seen = {repr(start)}
    i = 0
    truncated = False
    while i < len(order):
        s = order[i]
        i += 1
        for a in actions:
            try:
                t = step(s, a)
            except Exception:
                continue
            r = repr(t)
            if r not in seen:
                if len(order) >= BFS_CAP:
                    truncated = True
                    continue
                seen.add(r)
                order.append(t)
    buf = io.StringIO()
    buf.write("actions=%r\n" % (actions,))
    buf.write("reachable=%d truncated=%s\n" % (len(order), truncated))
    for s in order:
        for a in actions:
            try:
                t = repr(step(s, a))
            except Exception as exc:
                t = "RAISED %s: %s" % (type(exc).__name__, exc)
            buf.write("%r | %r -> %s\n" % (s, a, t))
    return buf.getvalue()


for name, dsl_rel, prob_rel in MANUALS:
    dsl = REPO / dsl_rel
    prob = REPO / prob_rel
    src_text = dsl.read_text(encoding="utf-8")

    try:
        ast = parse_theory(src_text)
        problem = load_problem(str(prob))
    except Exception as exc:
        _err("%s.PARSE.txt" % name, exc)
        continue

    # ---- IR + warnings
    try:
        ir = build_ir(ast, problem)
        _write("%s.warnings.txt" % name,
               json.dumps(list(ir.warnings), indent=2, ensure_ascii=False) + "\n")
    except Exception as exc:
        _err("%s.warnings.txt" % name, exc)

    # ---- python
    py = None
    try:
        py = generate_python(ast, problem)
        _write("%s.py.txt" % name, py)
    except Exception as exc:
        _err("%s.py.txt" % name, exc)

    # ---- python behaviour
    if py is not None:
        try:
            ns = {}
            exec(compile(py, "<%s>" % name, "exec"), ns)
            _write("%s.trans.txt" % name, _transition_dump(ns))
        except Exception as exc:
            _err("%s.trans.txt" % name, exc)

    # ---- pddl
    try:
        w = problem.width or 9
        h = problem.height or 9
        domain, inst = generate_pddl(ast, problem_name=name,
                                     grid_width=w, grid_height=h)
        _write("%s.domain.pddl" % name, domain)
        _write("%s.problem.pddl" % name, inst)
    except Exception as exc:
        _err("%s.domain.pddl" % name, exc)

    # ---- markdown
    try:
        _write("%s.md" % name, generate_markdown(ast))
    except Exception as exc:
        _err("%s.md" % name, exc)

    # ---- lean
    try:
        _write("%s.lean" % name, generate_lean(ast, problem))
    except Exception as exc:
        _err("%s.lean" % name, exc)

print("done", SRC)
