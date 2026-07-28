"""The mechanical proxy for "this gate has an executable negative control".

V11 answered that question 127 times by hand. A human read the entry point, read
whatever tests pointed at it, and decided. That answer cannot be recomputed next
week, which is the whole problem: the census is a photograph of a moving thing.

To make it standing, the judgement has to become a *decidable* predicate. It will
not be the same predicate — no arrangement of ``ast`` nodes knows whether an
input is "bad". So this module states a proxy, and `calibrate.py` measures the
proxy against V11's 127 hand judgements before anybody is asked to trust it.

The proxy
---------

An entry point ``P`` (a Python file that can exit non-zero) has a negative
control iff some test function ``T`` in some ``test_*.py`` in this repository

  1. **targets** ``P`` — a module binding in ``T``'s file resolves to ``P``, and
     ``T``'s body actually mentions that binding; and
  2. contains a **failure assertion** — a syntactic construct that asserts a bad
     outcome: ``pytest.raises``, ``assert f(...) == <nonzero>``, ``assert not
     x``, ``assert x is False``, ``assert problems != []``, and the short list in
     `_failure_assertion` below.

Parsed, never grepped. This is not stylistic. `figures/verify.sh` gate 7 records
what happens otherwise: its first version was a regex, and its first finding was
the phrase ``never ``open()``` inside a docstring. A gate whose findings are
mostly false is a gate people learn to ignore, and the fix there was ``ast``.
Same fix here — a docstring saying "this is the negative control" is invisible to
this module, on purpose.

What the proxy cannot see, stated up front
------------------------------------------

* **Negative controls that are not pytest.** ``figures/check_coverage.py
  --self-test``, ``cold-start-a3/a3pipeline/negctl.py``, ``exam/tools/run_exam.py
  --calibrate``, ``theory-compiler/tools/probe_mentions.py``'s pre-registered
  expectations, the heredoc in a run's own ``verify.sh``. These are among the
  *best* negative controls in the repository and detector B exists to recover
  some of them; measure it in the calibration report before believing it does.
* **Whether the input was actually bad.** ``pytest.raises(FileNotFoundError)``
  around a fixture that has not been written yet is a failure assertion by this
  definition and a negative control by nobody's.
* **Whether the test targets the gate or a second implementation of the same
  rule.** V11's sharpest finding (`theoria-arm/armtools/archive.py`) is exactly
  this shape, and resolution by import binding gets it right only because the two
  implementations live in different files.

Import resolution
-----------------

``import verify`` is ambiguous in this repository — ``ablation-arm/verify.py``,
``exam/verify.py``, ``worldgen/verify.py`` and ``fuzzlab/verify.py`` all exist and
all are reached by a bare name after a ``sys.path`` insert. A binding is resolved
against the *importing file's own ancestry*: the candidate sharing the longest
path prefix with the test file wins. That is what the interpreter does at run
time and it is the single largest false-positive control in this module.
"""

from __future__ import annotations

import ast
import os
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

# --------------------------------------------------------------------------
# Failure assertions
# --------------------------------------------------------------------------

#: Names that, called as a context manager, assert the block must blow up.
_RAISES = {"raises", "assertRaises", "assertRaisesRegex"}

#: String verdicts that only appear on the red side of a comparison.
_RED_WORDS = {
    "FAIL", "FAILED", "MISMATCH", "ABORT", "ABORTED", "REFUSED", "VIOLATED",
    "RED", "DEVIATION", "NO_VERDICT", "INCOMPLETE", "INSUFFICIENT", "drifted",
    "command-failed", "manifest-stale", "unowned_pixel", "render_mismatch",
}


def _is_raises_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    fn = node.func
    if isinstance(fn, ast.Attribute) and fn.attr in _RAISES:
        return True
    if isinstance(fn, ast.Name) and fn.id in _RAISES:
        return True
    return False


def _nonzero_int(node: ast.AST) -> bool:
    return (isinstance(node, ast.Constant)
            and isinstance(node.value, int)
            and not isinstance(node.value, bool)
            and node.value != 0)


#: Callables whose return value is a process exit code by convention here.
_EXIT_CALLS = {"main", "_main", "cli", "run_main", "invoke", "run_cli"}

#: Substrings that mark a name as carrying an exit code rather than a count.
_EXIT_WORDS = ("exit", "returncode", "retcode", "rc", "status", "code")


def _looks_like_exit_code(node: ast.AST) -> bool:
    """Is this expression plausibly a process exit code?

    ``assert main([...]) == 1`` is a negative control. ``assert len(rows) == 6``
    is a count. Both are ``Compare(Eq, <nonzero int>)``, and the second one is
    how ``theoria-arm/harness/run.py`` -- a module V11 judged to have *no*
    negative control, correctly -- was scored ``present`` by the first draft of
    this file.
    """
    if isinstance(node, ast.Call):
        fn = node.func
        if isinstance(fn, ast.Name) and fn.id in _EXIT_CALLS:
            return True
        if isinstance(fn, ast.Attribute) and fn.attr in _EXIT_CALLS:
            return True
        return False
    if isinstance(node, ast.Attribute):
        return node.attr.lower() in _EXIT_WORDS or "exit" in node.attr.lower()
    if isinstance(node, ast.Name):
        low = node.id.lower()
        return any(w == low or low.endswith("_" + w) or low.startswith(w + "_")
                   for w in _EXIT_WORDS)
    if isinstance(node, ast.Subscript):
        key = node.slice
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            low = key.value.lower()
            return any(w in low for w in _EXIT_WORDS)
    return False


#: Keys and attributes that name a verdict, so that ``assert not X`` is a claim
#: about a gate's answer rather than about a list of findings.
#:
#: ``assert not violations`` is a *positive* control -- it says the run found
#: nothing wrong. ``assert not report["pass"]`` is a negative control. Before
#: this distinction, ``fuzzlab/campaign.py`` (gold: no negative control) scored
#: ``present`` off ``test_short_campaign_finds_no_violation``.
_VERDICT_WORDS = {
    "pass", "passed", "ok", "okay", "clean", "holds", "valid", "green",
    "matches", "match", "success", "succeeded", "caught", "all_caught",
    "calibrated", "reproduced", "identical", "deterministic", "sound",
    "complete", "accepted", "allowed", "permitted", "same_answer", "agree",
}


def _is_verdict(node: ast.AST) -> bool:
    if isinstance(node, ast.Attribute):
        return node.attr.lower() in _VERDICT_WORDS
    if isinstance(node, ast.Name):
        return node.id.lower() in _VERDICT_WORDS
    if isinstance(node, ast.Subscript):
        key = node.slice
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            return key.value.lower() in _VERDICT_WORDS
        return _is_verdict(node.value)
    if isinstance(node, ast.Call):
        fn = node.func
        if isinstance(fn, ast.Attribute) and fn.attr.lower() in _VERDICT_WORDS:
            return True
        if isinstance(fn, ast.Name) and fn.id.lower() in _VERDICT_WORDS:
            return True
    return False


def _is_false(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and node.value is False


def _empty_container(node: ast.AST) -> bool:
    if isinstance(node, ast.List) and not node.elts:
        return True
    if isinstance(node, ast.Dict) and not node.keys:
        return True
    if isinstance(node, ast.Set) and not node.elts:
        return True
    return isinstance(node, ast.Constant) and node.value in ("", 0)


def _nonempty_container(node: ast.AST) -> bool:
    if isinstance(node, (ast.List, ast.Set)) and node.elts:
        return True
    return isinstance(node, ast.Dict) and bool(node.keys)


def _red_string(node: ast.AST) -> bool:
    return (isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value in _RED_WORDS)


def _assert_is_failure(test: ast.AST, absence: bool = True) -> Optional[str]:
    """Return a short reason if this ``assert`` expression asserts a bad outcome.

    ``absence`` enables the containment form -- ``assert secret not in blob`` --
    which is how `proxy/` writes most of its redaction red lines. It is measured
    separately in the calibration report because it is the loosest rule here.
    """
    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
        if _is_verdict(test.operand):
            return "assert not <verdict>"
        return None
    if isinstance(test, ast.Compare) and len(test.ops) == 1:
        op, right = test.ops[0], test.comparators[0]
        if isinstance(op, ast.Eq):
            if _nonzero_int(right) and _looks_like_exit_code(test.left):
                return "assert <exit code> == %r" % right.value
            if _is_false(right) and _is_verdict(test.left):
                return "assert <verdict> == False"
            if _red_string(right):
                return "assert ... == %r" % right.value
            if _nonempty_container(right) and _is_problem_bag(test.left):
                return "assert <findings> == <non-empty literal>"
        if isinstance(op, ast.NotEq):
            if isinstance(right, ast.Constant) and right.value == 0 \
                    and _looks_like_exit_code(test.left):
                return "assert <exit code> != 0"
            if _empty_container(right) and _is_problem_bag(test.left):
                return "assert <findings> != <empty>"
        if isinstance(op, ast.Is) and _is_false(right) and _is_verdict(test.left):
            return "assert <verdict> is False"
        if isinstance(op, (ast.Gt, ast.GtE)) and isinstance(right, ast.Constant) \
                and isinstance(right.value, int) and right.value == 0:
            if isinstance(test.left, ast.Call) and isinstance(test.left.func, ast.Name) \
                    and test.left.func.id == "len" and test.left.args \
                    and _is_problem_bag(test.left.args[0]):
                return "assert len(<findings>) > 0"
        if isinstance(op, ast.In) and _is_problem_bag(right):
            return "assert <complaint> in <findings>"
        if absence and isinstance(op, ast.NotIn):
            return "assert <planted bad thing> not in <output>"
    # `assert any(fragment in e for e in errors)` -- the gate produced this
    # specific complaint. engine-rig's 14 parametrised mutant rows are this
    # shape and nothing else in this function sees them.
    if isinstance(test, ast.Call) and isinstance(test.func, ast.Name) \
            and test.func.id in ("any", "all") and test.args:
        arg = test.args[0]
        if isinstance(arg, (ast.GeneratorExp, ast.ListComp, ast.SetComp)):
            for gen in arg.generators:
                if _is_problem_bag(gen.iter):
                    return "assert any(... for ... in <findings>)"
    # `assert errors` / `assert problems` -- bare truthiness of a findings bag.
    if _is_problem_bag(test):
        return "assert <findings>"
    return None


#: Names for "the things this run found wrong".
_PROBLEM_WORDS = {
    "problems", "failures", "failed", "errors", "violations", "violated",
    "offenders", "mismatches", "missing", "bad", "issues", "gaps", "hits",
    "refused", "rejected", "blocked", "incidents", "drifted", "uncaught",
}


def _is_problem_bag(node: ast.AST) -> bool:
    if isinstance(node, ast.Name):
        return node.id.lower() in _PROBLEM_WORDS
    if isinstance(node, ast.Attribute):
        return node.attr.lower() in _PROBLEM_WORDS
    if isinstance(node, ast.Subscript):
        key = node.slice
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            return key.value.lower() in _PROBLEM_WORDS
        return _is_problem_bag(node.value)
    if isinstance(node, ast.Call):
        fn = node.func
        if isinstance(fn, ast.Attribute) and fn.attr.lower() in _PROBLEM_WORDS:
            return True
        if isinstance(fn, ast.Name) and fn.id.lower() in _PROBLEM_WORDS:
            return True
    return False


def _failure_assertion(fn: ast.AST, absence: bool = True) -> Optional[str]:
    """The first failure assertion in ``fn``'s body, or None."""
    for node in ast.walk(fn):
        if isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                if _is_raises_call(item.context_expr):
                    return "pytest.raises"
        if isinstance(node, ast.Call) and _is_raises_call(node):
            return "raises(...)"
        if isinstance(node, ast.Assert):
            why = _assert_is_failure(node.test, absence=absence)
            if why:
                return why
    return None


# --------------------------------------------------------------------------
# Import resolution
# --------------------------------------------------------------------------


def _norm(path: str) -> str:
    return path.replace("\\", "/")


@dataclass
class Index:
    """Every ``.py`` file in the tree, indexed by stem, for import resolution."""

    root: str
    by_stem: Dict[str, List[str]] = field(default_factory=dict)
    files: List[str] = field(default_factory=list)

    @classmethod
    def build(cls, root: str, skip_dirs: Sequence[str] = ()) -> "Index":
        idx = cls(root=_norm(os.path.abspath(root)))
        skip = set(skip_dirs) | {
            ".git", ".worktrees", "__pycache__", ".toolchain", "node_modules",
            ".pytest_cache", ".venv", "venv", ".claude",
        }
        for dirpath, dirnames, filenames in os.walk(idx.root):
            dirnames[:] = [d for d in dirnames if d not in skip]
            for name in filenames:
                if not name.endswith(".py"):
                    continue
                rel = _norm(os.path.relpath(os.path.join(dirpath, name), idx.root))
                idx.files.append(rel)
                idx.by_stem.setdefault(name[:-3], []).append(rel)
        idx.files.sort()
        for v in idx.by_stem.values():
            v.sort()
        return idx

    def resolve(self, dotted: str, importer: str) -> Optional[str]:
        """Resolve a dotted module name as seen from ``importer`` (a rel path)."""
        parts = dotted.split(".")
        cands = self.by_stem.get(parts[-1], [])
        if not cands:
            return None
        if len(parts) > 1:
            tail = "/".join(parts) + ".py"
            narrowed = [c for c in cands if c.endswith(tail)]
            if narrowed:
                cands = narrowed
            else:
                # e.g. `theory_compiler.handover` living under src/theory_compiler
                narrowed = [c for c in cands if parts[-2] in c.split("/")]
                if narrowed:
                    cands = narrowed
        if len(cands) == 1:
            return cands[0]
        imp = importer.split("/")[:-1]

        def shared(c: str) -> int:
            cp = c.split("/")[:-1]
            n = 0
            for a, b in zip(imp, cp):
                if a != b:
                    break
                n += 1
            return n

        best = max(cands, key=lambda c: (shared(c), -len(c.split("/"))))
        return best


def bindings(tree: ast.Module, importer: str, index: Index) -> Dict[str, str]:
    """Map every name bound by an import in ``tree`` to a repo-relative file."""
    out: Dict[str, str] = {}

    def bind(name: str, dotted: str) -> None:
        hit = index.resolve(dotted, importer)
        if hit:
            out[name] = hit

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                local = alias.asname or alias.name.split(".")[0]
                bind(local, alias.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for alias in node.names:
                local = alias.asname or alias.name
                if mod:
                    bind(local, mod + "." + alias.name)   # `from pkg import mod`
                    if local not in out:
                        bind(local, mod)                  # `from mod import func`
                else:
                    bind(local, alias.name)
    return out


def names_used(fn: ast.AST) -> Set[str]:
    used: Set[str] = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Name):
            used.add(node.id)
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            used.add(node.value.id)
    return used


def targets_of(fn: ast.AST, binds: Dict[str, str],
               helpers: Dict[str, Set[str]]) -> Set[str]:
    """Files ``fn`` reaches, directly or through a helper defined in its own file.

    ``proxy/tests/test_redteam.py`` never writes ``EnvProxy`` inside a test; it
    writes ``with env_proxy_over(upstream.url, tmp_path) as proxy``. Without one
    hop through the file's own helpers, every red-team case in this repository's
    best negative-control suite reads as targeting nothing.

    Only helpers defined in the same file are followed, and the closure is
    within-file. Following imports would make every test in a package target
    every module in it, which is the ``theoria-arm/archive.py`` mistake -- a
    negative control aimed at a second implementation of the same rule -- turned
    into a policy.
    """
    seen: Set[str] = set()
    frontier = set(names_used(fn))
    walked: Set[str] = set()
    while frontier:
        name = frontier.pop()
        if name in binds:
            seen.add(binds[name])
        if name in helpers and name not in walked:
            walked.add(name)
            frontier |= helpers[name]
    return seen


def helper_names(tree: ast.Module) -> Dict[str, Set[str]]:
    """Module-level non-test callables in a test file, and the names each uses."""
    out: Dict[str, Set[str]] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                and not node.name.startswith("test"):
            out[node.name] = names_used(node)
        elif isinstance(node, ast.ClassDef):
            out[node.name] = names_used(node)
    return out


# --------------------------------------------------------------------------
# Detector A: a pytest function that targets the gate and asserts a failure
# --------------------------------------------------------------------------


@dataclass
class Hit:
    target: str          #: repo-relative path of the entry point
    test_file: str
    test_func: str
    lineno: int
    why: str

    def as_dict(self) -> Dict[str, object]:
        return {
            "target": self.target, "test_file": self.test_file,
            "test_func": self.test_func, "lineno": self.lineno, "why": self.why,
        }


def is_test_file(rel: str) -> bool:
    base = rel.split("/")[-1]
    return base.startswith("test_") or base.endswith("_test.py")


def scan_tests(index: Index, absence: bool = True) -> Dict[str, List[Hit]]:
    """Every (entry point -> failure-asserting test) edge in the tree."""
    edges: Dict[str, List[Hit]] = {}
    for rel in index.files:
        if not is_test_file(rel):
            continue
        try:
            src = open(os.path.join(index.root, rel), "r", encoding="utf-8").read()
            tree = ast.parse(src, filename=rel)
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue
        binds = bindings(tree, rel, index)
        if not binds:
            continue
        helpers = helper_names(tree)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not node.name.startswith("test"):
                continue
            why = _failure_assertion(node, absence=absence)
            if not why:
                continue
            for target in sorted(targets_of(node, binds, helpers)):
                edges.setdefault(target, []).append(
                    Hit(target, rel, node.name, node.lineno, why))
    return edges


# --------------------------------------------------------------------------
# Detector B: an in-tree negative control the entry point ships itself
# --------------------------------------------------------------------------

#: Function names that, by convention in this repository, name a self-contained
#: negative control. Detector B requires the *name* AND a failure construct in
#: the body; a name alone is a claim, and claims are what this item is about.
_SELFTEST_NAMES = ("self_test", "selftest", "negative_control", "negctl",
                   "assert_calibrated", "calibrate", "control_source",
                   "control_arm", "_control")


def _shape_of_selftest(fn: ast.AST) -> Optional[str]:
    """A self-test body must be able to report a miss, not merely be named one."""
    for node in ast.walk(fn):
        if isinstance(node, ast.Raise):
            return "raise"
        if isinstance(node, ast.Assert):
            return "assert"
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr == "append":
            return "problems.append"
        if isinstance(node, ast.Return) and _nonzero_int(node.value):
            return "return <nonzero>"
    return None


def scan_selftests(index: Index) -> Dict[str, List[Hit]]:
    edges: Dict[str, List[Hit]] = {}
    for rel in index.files:
        if is_test_file(rel):
            continue
        try:
            src = open(os.path.join(index.root, rel), "r", encoding="utf-8").read()
            tree = ast.parse(src, filename=rel)
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            low = node.name.lower()
            if not any(k in low for k in _SELFTEST_NAMES):
                continue
            shape = _shape_of_selftest(node)
            if not shape:
                continue
            edges.setdefault(rel, []).append(
                Hit(rel, rel, node.name, node.lineno, "in-tree self-test (%s)" % shape))
    return edges


# --------------------------------------------------------------------------
# Detector N (the naive one, kept only so the calibration can reject it)
# --------------------------------------------------------------------------

_NAIVE_WORDS = ("neg", "fail", "refus", "reject", "raise", "bad", "invalid",
                "mutant", "catch", "broken", "tamper", "corrupt", "must_")


def scan_naive(index: Index) -> Dict[str, List[Hit]]:
    """Target + a suggestive test-function name. No structural evidence at all.

    This is the criterion a reasonable person writes first, and the calibration
    report exists partly to show what it costs.
    """
    edges: Dict[str, List[Hit]] = {}
    for rel in index.files:
        if not is_test_file(rel):
            continue
        try:
            src = open(os.path.join(index.root, rel), "r", encoding="utf-8").read()
            tree = ast.parse(src, filename=rel)
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue
        binds = bindings(tree, rel, index)
        if not binds:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            low = node.name.lower()
            if not node.name.startswith("test") or not any(w in low for w in _NAIVE_WORDS):
                continue
            for name in sorted(names_used(node) & set(binds)):
                edges.setdefault(binds[name], []).append(
                    Hit(binds[name], rel, node.name, node.lineno, "name looks negative"))
    return edges


# --------------------------------------------------------------------------
# The verdict
# --------------------------------------------------------------------------

PRESENT = "present"
ABSENT = "absent"


@dataclass
class Verdicts:
    """The criterion evaluated over a whole tree, under each detector.

    ``A``  test-side failure assertion, containment form included
    ``A-`` the same without ``assert <bad> not in <output>``
    ``B``  an in-tree self-test the entry point ships itself
    ``AB`` A or B -- the shipped criterion
    ``N``  the naive one: a suggestive test-function name and nothing else
    """

    a: Dict[str, List[Hit]]
    a_strict: Dict[str, List[Hit]]
    b: Dict[str, List[Hit]]
    naive: Dict[str, List[Hit]]

    def _maps(self, detector: str) -> List[Dict[str, List[Hit]]]:
        return {"A": [self.a], "A-": [self.a_strict], "B": [self.b],
                "AB": [self.a, self.b], "A-B": [self.a_strict, self.b],
                "N": [self.naive]}[detector]

    def verdict(self, target: str, detector: str = "AB") -> str:
        return PRESENT if any(target in m for m in self._maps(detector)) else ABSENT

    def evidence(self, target: str, detector: str = "AB") -> List[Hit]:
        out: List[Hit] = []
        for m in self._maps(detector):
            out += m.get(target, [])
        return out


DETECTORS = ("N", "A-", "A", "B", "A-B", "AB")


def evaluate(root: str) -> Tuple[Index, Verdicts]:
    index = Index.build(root)
    return index, Verdicts(a=scan_tests(index, absence=True),
                           a_strict=scan_tests(index, absence=False),
                           b=scan_selftests(index),
                           naive=scan_naive(index))
