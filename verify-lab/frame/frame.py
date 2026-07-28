"""The sampling frame: what counts as an acceptance entry point, decidably.

Why this file exists
--------------------

V11 surveyed 127 acceptance entry points by hand and found 35 with no executable
demonstration that they can fail. V14 built a standing probe over 141 entry
points and calibrated its criterion against V11's rows. Then V14's adversarial
pass found a parse defect that produced both a false positive and a false
negative, fixed it, and the confusion matrix did not move by one cell.

The reason it could not move: **74 of the probe's 141 entry points were never in
V11's survey**, and the confirmed false positive was one of them. A gold standard
covering 47% of the population cannot falsify a defect concentrated in the other
53%.

Neither number was drawn from a population. V11's 127 is the *union of what six
auditors happened to find*. V14's 141 is the output of a heuristic that its own
report measures as missing 26% of V11's locatable gates and admitting at least 17
things that are not gates. Two overlapping convenience samples, no frame.

This module is the frame: a written, executable, re-runnable definition of the
population, against which both prior counts can be audited.

The definition
--------------

An **acceptance entry point** is a unit of this repository that

  (i)  is *shipped* -- tracked by git, so it is part of what the repository
       publishes rather than scratch on somebody's disk; and
  (ii) is a *unit of acceptance* -- something a person or a harness can invoke,
       or something whose refusal reaches such an invocation.

That is the whole definition. In particular it does **not** require the unit to
be able to fail.

Why "can it fail" is not a membership test
------------------------------------------

Because it is question 1 of the three the census asks. A frame that admits only
units answering `yes` can never count a `no`, and `no` is the answer V11 gave 15
times -- ``release/checklist.py``, ``release/reproduce.py``,
``cold-start-a3/run_all.py``, ``theoria-arm/harness/run.py``, all of them gates in
name whose verdict cannot reach an exit code. Those rows are among V11's most
cited findings.

V14's enumerator requires a non-zero exit path (``probe.py:enumerate_entry_points``
= ``has_main_block and can_exit_nonzero``). So the entire class of dead gates is
structurally invisible to it: the probe cannot report the gate that *stopped*
being able to fail, only the one that never had a negative control. That is the
same defect as the 74 unsurveyed entry points, one level up, and repeating it here
would make the frame unable to audit the thing it was written to audit.

Here ``can_refuse`` is a **column**, computed and published, never a filter.

The three strata
----------------

No single rule covers the shapes this repository actually uses, so the frame is
stratified rather than pretending to one number.

  **Stratum A -- invocable.** A tracked, non-test ``.py`` with an
  ``if __name__ == "__main__"`` block, or a tracked, non-test ``.sh``.
  Invocability alone; the exit-path question is answered in ``can_refuse``.

  **Stratum B -- terminal-refusal libraries.** A tracked, non-test file that is
  not in stratum A, which raises an ``Exception`` subclass this repository
  defines, where
    * some stratum-A file imports it (so its refusal reaches an invocation), and
    * that exception is not caught by any non-test file other than its own
      (so the refusal is *terminal*: nothing downgrades it to a warning).
  This stratum exists because it is the class V11's sharpest findings live in --
  ``proxy/guard.py``, ``exam/leakage.py``, ``battery/guard.py`` refuse by raising
  and have no ``__main__`` at all -- and V14's enumerator is blind to all of it.
  A frame that omitted stratum B would be a frame drawn to make the enumerator
  look calibrated.

  **Stratum C -- test suites.** One unit per directory directly containing at
  least one ``test_*.py``. V11 counted these: 12 of its 127 rows are
  ``python -m pytest`` or ``pytest <dir>`` and name no file at all. They are
  acceptance entry points by this repository's own reckoning --
  ``arc-recon/verify.sh``, ``monitor/verify.sh`` and ``exam/verify.py`` each
  invoke a suite as a step and read its exit code. Dropping them would silently
  discard 12 rows of the gold standard being audited.

Marks, not exclusions
---------------------

The frame **marks** rather than removes, because every exclusion is a place a
defect can hide from the audit, and the finding of V15 is that an unexamined
exclusion is exactly where the defect was.

  ``frozen``     -- the unit lives under a ``runs/<id>/`` provenance directory.
                    One-off scripts beside a MANIFEST. They are real entry points
                    (``a0-spike/runs/.../make_manifest.py --verify`` is in V11's
                    census and is a genuine byte-level gate) but they do not
                    accumulate obligations: a standing probe that reddens on every
                    new run directory gets switched off. Report, do not gate.
  ``generated``  -- the unit is a compiler output. Its ability to raise is
                    inherited from its generator; the gate is the generator.
  ``unparseable``-- the file is tracked and does not parse. **Admitted, not
                    skipped.** ``release/checklist.py`` has carried a raw newline
                    inside a string literal since commit ``fa59795`` and raises
                    ``SyntaxError`` on import; V11's census records running it to
                    a green ``exit 0``. ``criterion.py`` and ``probe.py`` both
                    swallow the parse failure in a bare ``except`` and the file
                    silently leaves their population. That is how a frame
                    acquires a hole nobody can see, so this one is a column.

Every count is reported with and without the markers, so a reader can see what
each qualification buys and check it was not drawn to move a number.

What this frame still cannot see, stated up front
-------------------------------------------------

* **Function granularity.** The unit is a file. ``worldgen/build.py`` holds a
  gate with a negative control and a gate without one; the frame counts it once.
  V14's ``_a_file_level_present_is_not_a_promise`` limitation, inherited whole.
* **Import resolution is by stem.** Stratum B's "some stratum-A file imports it"
  test matches module stems, which over-connects in a repository with four files
  named ``verify.py``. Deliberately the *permissive* direction: the error V15 is
  repairing was an exclusion, so stratum B errs towards including.
* **Verdict-computing modules that never refuse at all.**
  ``theoria-arm/armtools/archive.py`` computes four obligations and writes every
  one into a MANIFEST without raising and without a non-zero return. It is in
  stratum A only because it happens to have a ``__main__``. A module of that
  shape *without* a ``__main__`` would be invisible to every stratum here, and
  V11 found that shape by hand. No mechanical rule offered so far catches it.
* **Reachability is syntactic.** A ``return 1`` behind a condition that can never
  hold still counts as ``can_refuse``. V11 answered that by hand, per row.
* **Shell is judged by ``set -e`` or a literal ``exit``.** Exact on the 7 files
  here; it would not survive a repository with build scripts.

Usage
-----

    python verify-lab/frame/frame.py            # counts
    python verify-lab/frame/frame.py --json     # the frame, one record per unit
    python verify-lab/frame/frame.py --list     # paths only, no verdicts

``--list`` exists for a reason that is the point of this item: the blind manual
judging of the difference set had to be able to obtain *paths* without obtaining
anybody's verdict about them. Nothing in this module computes or reads a
negative-control verdict.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import subprocess
import sys
from typing import Dict, List, Optional, Sequence, Set, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))

STRATUM_A = "A"
STRATUM_B = "B"
STRATUM_C = "C"

_MAIN_FUNCS = {"main", "_main", "cli", "run_main"}
_EXIT_FUNCS = {"exit", "_exit"}

_GENERATED_MARKERS = ("/generated", "/artifacts/", "/handover_packages/",
                      "/books/generated/")


# --------------------------------------------------------------------------
# tracked files
# --------------------------------------------------------------------------

#: The tree as V11 and V14 left it -- the merge of both prior branches, before
#: V15 committed a single instrument of its own.
#:
#: Without a pin the population is measured on the working tree, and V15's own
#: `frame.py` / `reconcile.py` / `matrix.py` / `leakage.py` are members of it: a
#: frame that exempted its own tooling would be the disease it is looking for.
#: The consequence is that every commit V15 makes enlarges the denominator and
#: therefore *lowers* V11's measured coverage -- 241 -> 243 -> 244 across one run
#: directory, always in the direction that flatters V15's argument. The
#: adversarial pass found three mutually inconsistent totals in the artefacts.
#:
#: So every published number is taken at this revision. Pass `--rev HEAD` to see
#: the live tree, and expect it to differ.
BASELINE_REV = "3fa7170"


def tracked_files(root: str, rev: Optional[str] = None) -> List[str]:
    if rev:
        out = subprocess.run(["git", "-C", root, "ls-tree", "-r",
                              "--name-only", rev],
                             capture_output=True, text=True, check=True).stdout
    else:
        out = subprocess.run(["git", "-C", root, "ls-files"],
                             capture_output=True, text=True, check=True).stdout
    return [line for line in out.replace("\\", "/").split("\n") if line]


#: rev -> {path: bytes}. One `git archive` per revision instead of one
#: `git show` per file: the naive version spawned ~650 processes per build and
#: took the whole run past two minutes.
_TREE_CACHE: Dict[str, Dict[str, bytes]] = {}


def _tree(root: str, rev: str) -> Dict[str, bytes]:
    if rev not in _TREE_CACHE:
        import io
        import tarfile
        blob = subprocess.run(["git", "-C", root, "archive", rev],
                              capture_output=True, check=True).stdout
        out: Dict[str, bytes] = {}
        with tarfile.open(fileobj=io.BytesIO(blob)) as tar:
            for member in tar.getmembers():
                if not member.isfile():
                    continue
                handle = tar.extractfile(member)
                if handle is not None:
                    out[member.name.replace("\\", "/")] = handle.read()
        _TREE_CACHE[rev] = out
    return _TREE_CACHE[rev]


def read_file(root: str, rel: str, rev: Optional[str] = None) -> str:
    if rev:
        data = _tree(root, rev).get(rel)
        if data is None:
            raise OSError("%s not in %s" % (rel, rev))
        return data.decode("utf-8")
    with open(os.path.join(root, rel), "r", encoding="utf-8") as handle:
        return handle.read()


def is_test_file(rel: str) -> bool:
    base = rel.split("/")[-1]
    return (base.startswith("test_") or base.endswith("_test.py")
            or base == "conftest.py" or "/tests/" in rel)


def is_frozen(rel: str) -> bool:
    parts = rel.split("/")
    return "runs" in parts[:-1]


def is_generated(rel: str) -> bool:
    return any(m in "/" + rel for m in _GENERATED_MARKERS)


# --------------------------------------------------------------------------
# (i) can it refuse
# --------------------------------------------------------------------------

def _nonzero_int(node: ast.AST) -> bool:
    return (isinstance(node, ast.Constant) and isinstance(node.value, int)
            and not isinstance(node.value, bool) and node.value != 0)


def _returns_nonzero(value: Optional[ast.AST]) -> bool:
    if value is None:
        return False
    if _nonzero_int(value):
        return True
    if isinstance(value, ast.IfExp):
        return _returns_nonzero(value.body) or _returns_nonzero(value.orelse)
    if isinstance(value, ast.BoolOp):
        return any(_returns_nonzero(v) for v in value.values)
    return False


def has_main_block(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and isinstance(node.test, ast.Compare):
            left = node.test.left
            if isinstance(left, ast.Name) and left.id == "__name__":
                return True
    return False


def can_exit_nonzero(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            name = (fn.id if isinstance(fn, ast.Name)
                    else fn.attr if isinstance(fn, ast.Attribute) else None)
            if name in _EXIT_FUNCS and node.args and _nonzero_int(node.args[0]):
                return True
        if isinstance(node, ast.Raise):
            exc = node.exc
            if isinstance(exc, ast.Call) and isinstance(exc.func, ast.Name) \
                    and exc.func.id == "SystemExit":
                return True
            if isinstance(exc, ast.Name) and exc.id == "SystemExit":
                return True
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                and node.name in _MAIN_FUNCS:
            for inner in ast.walk(node):
                if isinstance(inner, ast.Return) and _returns_nonzero(inner.value):
                    return True
    return False


def repo_exception_classes(trees: Dict[str, ast.Module]) -> Set[str]:
    """Every Exception subclass *this repository* defines, anywhere."""
    out: Set[str] = set()
    for tree in trees.values():
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    nm = (base.id if isinstance(base, ast.Name)
                          else base.attr if isinstance(base, ast.Attribute) else "")
                    if nm.endswith("Error") or nm.endswith("Exception") \
                            or nm in {"Exception", "BaseException"}:
                        out.add(node.name)
    return out


def custom_exceptions_raised(tree: ast.Module, known: Set[str]) -> List[str]:
    """Repository-defined exceptions this module raises.

    Defined *anywhere* in the repository, not only in this file. The narrower
    rule -- defined and raised in the same file -- silently dropped
    ``exam/leakage.py``, whose ``LeakageError`` is declared one directory up in
    ``exam/model.py``. That file is the leakage gate for the whole exam battery
    and V11 credits it with a real negative control. Losing it would have been a
    stratum-shaped hole of exactly the kind this frame is being written to
    audit, so the rule follows the repository's layout rather than a
    convenience.
    """
    raised: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Raise) and node.exc is not None:
            exc = node.exc
            nm = None
            if isinstance(exc, ast.Call) and isinstance(exc.func, ast.Name):
                nm = exc.func.id
            elif isinstance(exc, ast.Name):
                nm = exc.id
            elif isinstance(exc, ast.Call) and isinstance(exc.func, ast.Attribute):
                nm = exc.func.attr
            if nm and nm in known:
                raised.add(nm)
    return sorted(raised)


def shell_can_exit_nonzero(text: str) -> bool:
    """``exit <nonzero>``, an ``exit "$var"``, or ``set -e``.

    ``set -e`` has to count. ``ablation-arm/verify.sh`` and ``monitor/verify.sh``
    contain no ``exit`` statement at all -- they are ``set -euo pipefail`` and a
    chain of commands, so *any* failing step leaves the process non-zero. A rule
    that only looked for a literal ``exit 1`` would drop two of the seven shell
    gates, and both are named as completion gates in their own territory's
    design document. That is precisely the kind of silent stratum-shaped hole
    this frame exists to stop having.
    """
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("set -") and "e" in s.split()[1].lstrip("-").split("o")[0]:
            return True
        if s.startswith("exit ") or s.startswith("sys.exit("):
            arg = s.split("(", 1)[1].rstrip(")") if s.startswith("sys.exit(") \
                else s[5:].strip()
            if arg.strip('"').strip("'") not in ("0", ""):
                return True
    return False


# --------------------------------------------------------------------------
# imports, for stratum B
# --------------------------------------------------------------------------

def imported_names(tree: ast.Module) -> Set[str]:
    names: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[-1])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                for part in node.module.split("."):
                    names.add(part)
            for alias in node.names:
                names.add(alias.name)
    return names


def caught_names(tree: ast.Module) -> Set[str]:
    names: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is not None:
            for sub in ast.walk(node.type):
                if isinstance(sub, ast.Name):
                    names.add(sub.id)
                elif isinstance(sub, ast.Attribute):
                    names.add(sub.attr)
    return names


# --------------------------------------------------------------------------
# the frame
# --------------------------------------------------------------------------

def build(root: str = REPO,
          rev: Optional[str] = BASELINE_REV) -> List[Dict[str, object]]:
    rels = tracked_files(root, rev)
    trees: Dict[str, ast.Module] = {}
    unparseable: List[Tuple[str, str]] = []
    for rel in rels:
        if not rel.endswith(".py"):
            continue
        try:
            src = read_file(root, rel, rev)
        except (OSError, subprocess.CalledProcessError, UnicodeDecodeError):
            continue
        try:
            trees[rel] = ast.parse(src, filename=rel)
        except (SyntaxError, UnicodeDecodeError, ValueError) as exc:
            # NOT `continue`. A tracked entry point that does not parse is a
            # finding, not a file to skip. `negctl/criterion.py` swallows these
            # in a bare `except` and `release/checklist.py` -- which V11's
            # census records running to a green exit 0 -- has been unparseable
            # on the mainline since commit fa59795. Silently dropping it is how
            # a frame acquires a hole nobody can see.
            unparseable.append((rel, "%s: %s" % (type(exc).__name__, exc)))

    units: List[Dict[str, object]] = []
    for rel, why in unparseable:
        if is_test_file(rel):
            continue
        try:
            src = read_file(root, rel, rev)
        except (OSError, subprocess.CalledProcessError, UnicodeDecodeError):
            continue
        if "__main__" not in src:
            continue
        units.append({"path": rel, "stratum": STRATUM_A, "kind": "python",
                      "frozen": is_frozen(rel), "generated": is_generated(rel),
                      "can_refuse": False, "unparseable": why,
                      "why": "textual `__main__`; DOES NOT PARSE (%s)" % why})
    known_excs = repo_exception_classes(trees)

    # ---- stratum A: python. Membership is INVOCABILITY ALONE.
    #
    # `can_refuse` is recorded as a column and is deliberately NOT a membership
    # test. Making it one would be circular: "can it go red?" is question 1 of
    # the three the census asks, so a frame that admits only files answering
    # `yes` cannot ever count a `no`. V11 answered `no` fifteen times --
    # `release/checklist.py`, `release/reproduce.py`, `cold-start-a3/run_all.py`,
    # `theoria-arm/harness/run.py` -- and those rows are among its most cited
    # findings. V14's enumerator required a non-zero exit path, so all fifteen
    # were structurally invisible to it. That is the same defect as the 74, one
    # level up, and it is not repeated here.
    a_paths: List[str] = []
    for rel, tree in sorted(trees.items()):
        if is_test_file(rel):
            continue
        if has_main_block(tree):
            a_paths.append(rel)
            units.append({"path": rel, "stratum": STRATUM_A, "kind": "python",
                          "frozen": is_frozen(rel), "generated": is_generated(rel),
                          "can_refuse": can_exit_nonzero(tree),
                          "why": "tracked, non-test, has an `if __name__` block"})

    # ---- stratum A: shell
    for rel in sorted(rels):
        if not rel.endswith(".sh") or is_test_file(rel):
            continue
        try:
            text = read_file(root, rel, rev)
        except (OSError, subprocess.CalledProcessError, UnicodeDecodeError):
            continue
        units.append({"path": rel, "stratum": STRATUM_A, "kind": "shell",
                      "frozen": is_frozen(rel), "generated": is_generated(rel),
                      "can_refuse": shell_can_exit_nonzero(text),
                      "why": "tracked shell script"})

    # ---- stratum B
    a_set = set(a_paths)
    a_imports = {rel: imported_names(trees[rel]) for rel in a_set}
    caught_elsewhere: Dict[str, Set[str]] = {}
    for rel, tree in trees.items():
        if is_test_file(rel):
            continue
        for name in caught_names(tree):
            caught_elsewhere.setdefault(name, set()).add(rel)

    for rel, tree in sorted(trees.items()):
        if is_test_file(rel) or rel in a_set:
            continue
        excs = custom_exceptions_raised(tree, known_excs)
        if not excs:
            continue
        stem = rel.split("/")[-1][:-3]
        reached_by = sorted(g for g in a_set
                            if stem in a_imports[g]
                            or any(e in a_imports[g] for e in excs))
        if not reached_by:
            continue
        terminal = [e for e in excs
                    if not (caught_elsewhere.get(e, set()) - {rel})]
        if not terminal:
            continue
        units.append({"path": rel, "stratum": STRATUM_B, "kind": "python",
                      "frozen": is_frozen(rel), "generated": is_generated(rel),
                      "can_refuse": True,
                      "why": "raises %s, terminal, reached from %d invocable file(s)"
                             % ("/".join(terminal), len(reached_by))})

    # ---- stratum C: test suites
    #
    # V11 counted these -- 12 of its 127 rows are `python -m pytest` or
    # `pytest <dir>` and name no file at all. They are acceptance entry points by
    # this repository's own reckoning: `arc-recon/verify.sh`, `monitor/verify.sh`
    # and `exam/verify.py` all invoke a suite as a step and read its exit code.
    # A frame that dropped them would be a frame that quietly discarded 12 rows
    # of the very gold standard it is auditing.
    suites: Dict[str, int] = {}
    for rel in rels:
        base = rel.split("/")[-1]
        if base.startswith("test_") and base.endswith(".py"):
            suites["/".join(rel.split("/")[:-1])] = suites.get(
                "/".join(rel.split("/")[:-1]), 0) + 1
    for d, n in sorted(suites.items()):
        units.append({"path": d, "stratum": STRATUM_C, "kind": "suite",
                      "frozen": is_frozen(d), "generated": False,
                      "can_refuse": True,
                      "why": "%d test_*.py; pytest exits non-zero on failure" % n})

    units.sort(key=lambda u: (u["stratum"], u["path"]))
    return units


def counts(units: Sequence[Dict[str, object]]) -> Dict[str, int]:
    def n(pred) -> int:
        return sum(1 for u in units if pred(u))
    return {
        "total": len(units),
        "A": n(lambda u: u["stratum"] == STRATUM_A),
        "B": n(lambda u: u["stratum"] == STRATUM_B),
        "C": n(lambda u: u["stratum"] == STRATUM_C),
        "A_python": n(lambda u: u["stratum"] == STRATUM_A and u["kind"] == "python"),
        "A_shell": n(lambda u: u["stratum"] == STRATUM_A and u["kind"] == "shell"),
        "frozen": n(lambda u: u["frozen"]),
        "generated": n(lambda u: u["generated"]),
        "live": n(lambda u: not u["frozen"] and not u["generated"]),
        "live_A": n(lambda u: u["stratum"] == STRATUM_A
                    and not u["frozen"] and not u["generated"]),
        "live_B": n(lambda u: u["stratum"] == STRATUM_B
                    and not u["frozen"] and not u["generated"]),
        "can_refuse": n(lambda u: u["can_refuse"]),
        "cannot_refuse": n(lambda u: not u["can_refuse"]),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="the V15 acceptance-entry-point frame")
    ap.add_argument("--root", default=REPO)
    ap.add_argument("--rev", default=BASELINE_REV,
                    help="enumerate the tree at this revision (default: the "
                         "pinned baseline, the merge of V11 and V14). Pass HEAD "
                         "for the live tree.")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--list", action="store_true",
                    help="paths only -- no verdicts, safe for a blind judge")
    ap.add_argument("--stratum", choices=[STRATUM_A, STRATUM_B, STRATUM_C])
    args = ap.parse_args(argv)

    units = build(args.root, args.rev)
    if args.stratum:
        units = [u for u in units if u["stratum"] == args.stratum]

    if args.list:
        for unit in units:
            print(unit["path"])
        return 0
    if args.json:
        print(json.dumps({"counts": counts(units), "units": units},
                         ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    c = counts(units)
    print("frame: %d acceptance entry points   (rev %s)"
          % (c["total"], args.rev or "working tree"))
    print("  stratum A (invocable)          %3d   (%d python, %d shell)"
          % (c["A"], c["A_python"], c["A_shell"]))
    print("  stratum B (terminal refusal)   %3d" % c["B"])
    print("  stratum C (test suites)        %3d" % c["C"])
    print("  marked frozen (under runs/)    %3d" % c["frozen"])
    print("  marked generated               %3d" % c["generated"])
    print("  live (neither marker)          %3d   (A %d, B %d)"
          % (c["live"], c["live_A"], c["live_B"]))
    print("  -- measured, not a filter --")
    print("  can refuse (non-zero path)     %3d" % c["can_refuse"])
    print("  cannot refuse                  %3d" % c["cannot_refuse"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
