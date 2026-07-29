"""Build the blinded attacker trees for V9.

Strips every docstring and every comment from the battery code the attackers
are allowed to see, by round-tripping through `ast.unparse`.  What survives is
the computation and the registered `definition=` strings -- the metric's
definition and its code, which is exactly what PREREG_V9 §"blind" says an
attacker may have.  What does not survive is the prose: design intent, known
weaknesses, defence notes.
"""
import ast
import io
import os
import shutil
import sys

SRC = r"C:\Users\user\Desktop\theoria\.worktrees\v9-battery-gaming-audit"
OUT_ROOT = os.path.dirname(os.path.abspath(__file__))

COPY = [
    "battery/__init__.py",
    "battery/model.py",
    "battery/metrics/__init__.py",
    "battery/metrics/economy.py",
    "battery/metrics/epistemic.py",
    "battery/metrics/exploration.py",
    "battery/metrics/mechanism.py",
    "battery/metrics/planning.py",
]


def strip(path):
    with io.open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            body = node.body
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                rest = body[1:]
                node.body = rest if rest else [ast.Pass()]
    return ast.unparse(ast.fix_missing_locations(tree)) + "\n"


# Runtime reason strings that survive docstring-stripping and give away design
# intent (why a guard exists, what confound it fights).  Replaced with terse
# equivalents in the blinded tree; status and value are untouched, only the
# human-readable reason.  Recorded in battery/BLINDING.md.
NEUTRALISE = [
    ("this trace is a coverage walk, not an attempt to win; scoring it for "
     "path efficiency would measure the trace's purpose rather than the arm",
     "run intent is not 'solve'"),
    ("this run never reached the goal, and path efficiency has no floor -- a "
     "run that gives up on step one scores better than any solve, so scoring "
     "a loss would rank failure as excellence",
     "no step is marked won"),
    ("this arm records no repair episode; an arm with no manual cannot be "
     "refuted by one, so the absence is structural",
     "the run records no repair episode"),
    ("no step in this run failed, so there is no failure to respond to",
     "the run records no failed step"),
    ("multi-level runs exist but the cross-level annotation schema is not yet "
     "defined; see STATUS.md",
     "no cross-level mechanism annotation"),
    ("fewer than %d turns; the same early-exit confound as E2",
     "fewer than %d turns"),
    ("fewer than eight transitions; quartiles meaningless",
     "fewer than eight transitions"),
]


def build(dest):
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    for rel in COPY:
        target = os.path.join(dest, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with io.open(target, "w", encoding="utf-8", newline="\n") as fh:
            text = strip(os.path.join(SRC, rel.replace("/", os.sep)))
            for old, new in NEUTRALISE:
                text = text.replace(old, new)
            fh.write(text)
    # empty package shims -- the real battery.audit imports the audit under test
    for rel in ("battery/audit/__init__.py", "battery/audit/v9/__init__.py"):
        target = os.path.join(dest, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with io.open(target, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("")
    # check.py, docstring-stripped: the protocol, not the intent
    for rel in ("battery/audit/v9/check.py", "battery/audit/v9/attack.py"):
        target = os.path.join(dest, rel.replace("/", os.sep))
        with io.open(target, "w", encoding="utf-8", newline="\n") as fh:
            text = strip(os.path.join(SRC, rel.replace("/", os.sep)))
            for old, new in NEUTRALISE:
                text = text.replace(old, new)
            fh.write(text)


if __name__ == "__main__":
    for name in sys.argv[1:]:
        build(os.path.join(OUT_ROOT, "v9-blind", name))
        print("built", name)
