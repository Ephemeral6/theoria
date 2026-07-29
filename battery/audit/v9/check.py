"""The poverty certificate — "did the attacker actually do any work?"

The first thing an adversarial reviewer asks about an anti-gaming audit is
whether the attacks were really cheats.  An attacker who quietly writes a
planner and then reports a good P4 has demonstrated that P4 *works*, not that
it can be gamed, and the two conclusions point in opposite directions.

`PREREG_V9.md` §2 makes that question decidable instead of arguable.  An attack
is a **zero-argument builder** returning a `Run`, and it must survive four
mechanical checks:

* **C1 determinism** — call it twice, the two runs are byte-identical.
* **C2 no external input** — the source names no file, clock, RNG, network or
  battery module.  It cannot read the ledger, the artefacts, or the metric it
  attacks.
* **C3 no search** — no `while`, no self-recursion, and no call to any name
  outside a tiny whitelist.  Laying out data is allowed; computing is not.
* **C4 no world** — nothing smuggled through `Run.notes` under a key that
  would read as ground truth.
* **C5 no closure** — the builder must be a module-level function.  C2 and C3
  read *the builder's* source, so a factory that ran a planner and returned a
  closure laying out its answer would pass everything above having done exactly
  the work this file exists to rule out.  The adversarial review built that
  case and it certified clean, which is why C5 exists.

C3 is the load-bearing one and it is deliberately crude.  Its two known edges
were written into the pre-registration rather than discovered afterwards: it is
too strict for an honest attack that wants `itertools` (rewrite it as data),
and too loose in that `sum`/`sorted` could in principle carry a little
arithmetic.  A checker that could tell "computation" from "layout" in general
would be a solved halting problem; this one is a proxy, declared in advance,
and every result it produces — including the failures — goes into the artefact.

The "in principle" turned out to be in practice.  The adversarial review
demonstrated generate-and-test inside the whitelist:

    candidates = [[a, b, c] for a in range(12) for b in range(12)
                  for c in range(12) if a + b + c == 14]
    best = min(candidates, key=lambda t: abs(t[0] * t[0] - t[2]))

— a constrained optimum found by exhaustive search, certified as "laying out
data".  Two constructs carry that: a filtered comprehension is the *test*, and
a `key=` lambda is the *objective*.  Both are now refused.  None of the 105
delivered attacks uses either, so the rule costs nothing retroactively and the
verdicts do not move; it is written down so the next round cannot use it.
"""

from __future__ import annotations

import ast
import dataclasses
import inspect
import textwrap
from typing import Any, Callable, Dict, List

# C2 — names that would let an attack read something it must not read.
FORBIDDEN_NAMES = frozenset({
    "open", "Path", "os", "io", "random", "requests", "urllib", "subprocess",
    "glob", "time", "datetime", "input", "__import__", "eval", "exec",
    "compile", "globals", "locals", "vars", "getattr", "setattr", "socket",
    "pickle", "shutil", "tempfile", "sys",
})

FORBIDDEN_MODULES = ("battery.adapters", "battery.audit", "battery.metrics",
                     "json", "os", "io", "random", "pathlib", "time")

# C3 — everything an attack is allowed to call.
ALLOWED_CALLS = frozenset({
    # trivial builtins
    "range", "len", "str", "int", "float", "bool", "list", "dict", "tuple",
    "set", "sum", "min", "max", "sorted", "enumerate", "zip", "round", "abs",
    "divmod", "chr", "reversed",
    # battery.model constructors — laying out a Run is the whole point
    "Run", "Step", "Call", "Concept", "Clause", "Theory", "Beat", "Repair",
    "Truth",
})

# Pure container / string assembly.  Not computation.
ALLOWED_METHODS = frozenset({"append", "extend", "join", "format", "keys",
                             "values", "items"})

# C4 — keys that would read as smuggled ground truth.
SUSPECT_NOTE_KEYS = ("truth", "optimal", "solution", "answer", "plan")


def _source_tree(fn: Callable[[], Any]) -> ast.AST:
    return ast.parse(textwrap.dedent(inspect.getsource(fn)))


def _static_violations(fn: Callable[[], Any]) -> List[str]:
    """C2 and C3, read off the builder's own source."""
    try:
        tree = _source_tree(fn)
    except (OSError, TypeError, SyntaxError) as exc:      # pragma: no cover
        return ["C2/C3: source unavailable (%s)" % exc]

    out: List[str] = []
    own_name = getattr(fn, "__name__", "")

    for node in ast.walk(tree):
        if isinstance(node, ast.While):
            out.append("C3: `while` loop (search)")
        elif isinstance(node, ast.Lambda):
            out.append("C3: lambda (an objective function is search's other "
                       "half)")
        elif isinstance(node, ast.comprehension) and node.ifs:
            out.append("C3: filtered comprehension (generate-and-test)")
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            module = getattr(node, "module", None) or ""
            names = [a.name for a in node.names]
            for candidate in [module] + names:
                if any(candidate == m or candidate.startswith(m + ".")
                       for m in FORBIDDEN_MODULES):
                    out.append("C2: imports %r" % candidate)
        elif isinstance(node, ast.Name):
            if node.id in FORBIDDEN_NAMES:
                out.append("C2: names %r" % node.id)
        elif isinstance(node, ast.Attribute):
            if node.attr in FORBIDDEN_NAMES:
                out.append("C2: attribute %r" % node.attr)
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                if func.id == own_name:
                    out.append("C3: recursive call to %r" % own_name)
                elif func.id not in ALLOWED_CALLS:
                    out.append("C3: calls %r (not whitelisted)" % func.id)
            elif isinstance(func, ast.Attribute):
                if func.attr not in ALLOWED_METHODS:
                    out.append("C3: calls method %r (not whitelisted)"
                               % func.attr)
            else:
                out.append("C3: calls a computed expression")
    # Deterministic and de-duplicated: the certificate is an artefact field.
    return sorted(set(out))


def _normalise(run: Any) -> Any:
    """A comparable snapshot of a Run, for C1."""
    return dataclasses.asdict(run)


def certificate(fn: Callable[[], Any]) -> Dict[str, object]:
    """Run C1..C5 over one attack builder.  Never raises."""
    violations: List[str] = []

    # C5 — a builder defined inside another function hides its enclosing scope
    # from C2 and C3, which read only this function's source.
    qualname = getattr(fn, "__qualname__", "")
    if "<locals>" in qualname:
        violations.append(
            "C5: builder %s is a closure; work in the enclosing scope is "
            "invisible to C2/C3" % qualname)

    # C1 — determinism.
    first = second = None
    try:
        first, second = fn(), fn()
        if _normalise(first) != _normalise(second):
            violations.append("C1: two calls differ")
    except Exception as exc:                              # pragma: no cover
        violations.append("C1: builder raised %s: %s" % (type(exc).__name__,
                                                         exc))

    # C2 / C3 — static.
    violations.extend(_static_violations(fn))

    # C4 — no world smuggled through notes.
    if first is not None:
        notes = getattr(first, "notes", None) or {}
        for key in notes:
            lowered = str(key).lower()
            if any(bad in lowered for bad in SUSPECT_NOTE_KEYS):
                violations.append("C4: notes key %r reads as ground truth"
                                  % key)

    violations = sorted(set(violations))
    return {
        "builder": getattr(fn, "__qualname__", repr(fn)),
        "ok": not violations,
        "violations": violations,
    }
