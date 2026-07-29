"""a2 family backward-compatibility harness for the v0.3 `writes { ... }` change.

Usage:  python a2fam-driver.py <src_dir> <out_dir>

`src_dir` decides which compiler tree is measured; it is prepended to sys.path
and the import is asserted to have come from there (pyproject declares an
editable install pointing at the MAIN checkout, so without the assert both
sides silently measure the same tree).

Everything under <out_dir> is a measurement, never an input.
"""
import io
import json
import pathlib
import sys
import traceback

SRC = pathlib.Path(sys.argv[1]).resolve()
OUT = pathlib.Path(sys.argv[2]).resolve()
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(SRC))

REPO = pathlib.Path(__file__).resolve().parents[4]   # worktree root

from theory_compiler.parser.theory_parser import parse_theory      # noqa: E402
from theory_compiler.problem import load_problem                   # noqa: E402
from theory_compiler.ir import build_ir                            # noqa: E402
from theory_compiler.generators.gen_python import generate_python  # noqa: E402
from theory_compiler.generators.gen_pddl import generate_pddl      # noqa: E402
from theory_compiler.generators.gen_markdown import generate_markdown  # noqa: E402
from theory_compiler.generators.gen_lean import generate_lean      # noqa: E402
from theory_compiler.conflict import Uniqueness, check_conflict    # noqa: E402

import theory_compiler                                             # noqa: E402
_got = pathlib.Path(theory_compiler.__file__).resolve()
assert _got.is_relative_to(SRC), "wrong tree imported: %s (wanted under %s)" % (
    _got, SRC)
print("measuring:", _got)

A2 = REPO / "cold-start-a2" / "theory"
MANUALS = [
    ("a2",          A2 / "theory.dsl",          A2 / "generated" / "problem.json"),
    ("a2-holed",    A2 / "theory_holed.dsl",    A2 / "generated_holed" / "problem.json"),
    ("a2-repaired", A2 / "theory_repaired.dsl", A2 / "generated_repaired" / "problem.json"),
]

BFS_CAP = 5000


def _write(name, text):
    (OUT / name).write_text(text, encoding="utf-8", newline="\n")


def _err(name, exc):
    _write(name, "ERROR\n" + "".join(
        traceback.format_exception(type(exc), exc, exc.__traceback__)))


def _transition_dump(ns):
    """Full transition table over the reachable set, BFS from initial_state.

    Start at `initial_state()`, breadth-first over `ACTIONS` in declaration
    order, dedup by dataclass repr, up to BFS_CAP states. Then emit
    `state | action -> successor` for EVERY (reachable state, action) pair.
    Both the reachable set and every successor land in the diff.
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
    pairs = 0
    for s in order:
        for a in actions:
            try:
                t = repr(step(s, a))
            except Exception as exc:
                t = "RAISED %s: %s" % (type(exc).__name__, exc)
            buf.write("%r | %r -> %s\n" % (s, a, t))
            pairs += 1
    return "pairs=%d\n" % pairs + buf.getvalue()


def _conflict_dump(ir, ast, problem):
    """check_conflict as PRODUCTION calls it on this side.

    Baseline has no `writes=` parameter; current passes `ir.writes`. Calling
    each side the way `build_ir` calls it is the comparison that matters --
    forcing the baseline signature onto the current tree would measure a code
    path that does not ship.
    """
    kw = dict(strict=False, uniq=Uniqueness(ast, problem))
    if getattr(ir, "writes", None) is not None:
        kw["writes"] = ir.writes
    rep = check_conflict(ir.rules, ast.semantics, problem.background, **kw)
    return json.dumps({
        "policy": rep.policy,
        "green": rep.green,
        "n_rules": len(ir.rules),
        "overlapping": [[a, b, sorted(objs)] for a, b, objs in rep.overlapping],
        "disjoint": [[a, b, why] for a, b, why in rep.disjoint],
        "ordered": [[a, b] for a, b in rep.ordered],
        "undischarged": [[a, b, sorted(objs)] for a, b, objs in rep.undischarged],
        "unclaimable": [[a, b] for a, b in rep.unclaimable],
        "warnings": list(rep.warnings()),
    }, indent=2, ensure_ascii=False, sort_keys=False) + "\n"


for name, dsl, prob in MANUALS:
    src_text = dsl.read_text(encoding="utf-8")

    try:
        ast = parse_theory(src_text)
        problem = load_problem(str(prob))
    except Exception as exc:
        _err("%s.PARSE.txt" % name, exc)
        continue

    ir = None
    try:
        ir = build_ir(ast, load_problem(str(prob)))
        _write("%s.warnings.txt" % name,
               json.dumps(list(ir.warnings), indent=2, ensure_ascii=False) + "\n")
    except Exception as exc:
        _err("%s.warnings.txt" % name, exc)

    # ---- conflict report
    if ir is not None:
        try:
            _write("%s.conflict.json" % name,
                   _conflict_dump(ir, ast, load_problem(str(prob))))
        except Exception as exc:
            _err("%s.conflict.json" % name, exc)

    # ---- python
    py = None
    try:
        py = generate_python(ast, load_problem(str(prob)))
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

    # ---- markdown, both routes
    try:
        _write("%s.md" % name, generate_markdown(ast))
    except Exception as exc:
        _err("%s.md" % name, exc)
    try:
        _write("%s.ir.md" % name,
               generate_markdown(ast, build_ir(ast, load_problem(str(prob)))))
    except Exception as exc:
        _err("%s.ir.md" % name, exc)

    # ---- lean
    for mode in ("computational", "algebraic"):
        try:
            _write("%s.%s.lean" % (name, mode),
                   generate_lean(ast, load_problem(str(prob)), proof=mode))
        except Exception as exc:
            _err("%s.%s.lean" % (name, mode), exc)

print("done", SRC)
