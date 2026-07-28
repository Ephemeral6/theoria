"""Standing check: a solver's failure state turned straight into a verdict.

    python -m tools.check_solver_status [path ...]      # exit 1 on a finding

C11.  Theoria's constraint 6: a universal claim needs a proof, and a bare UNSAT
is not one -- "the search said no" does not count, a certificate does.  The way
that rule gets broken in practice is small and specific, and it has happened in
this repository more than once:

    unsolvable = done.returncode == 12          # tools/p13_fd_dividend.py:129

An exit code, a solver status, a `success` flag -- a fact about the *tool* --
compared to a literal and bound, in one expression, to a name that asserts
something about the *world*.  The adjudicating predicate for that exact
comparison already existed twenty lines away in
`engines/fd_adapter/backends.proves_unsolvable`, and the file already imported
it.  Written and never called is worse than never written, because it reads as
though the discipline is in place.

## What this check does and does not look for

It flags exactly one shape: **a comparison over a tool-status expression whose
result is bound to a verdict-bearing name.**  Nothing else.

That is narrow on purpose, and the narrowness is the finding of the calibration
(`runs/*-C11-tool-failure-as-truth/CALIBRATION.md`): of the eleven sites this
work item corrected, this shape covers the ones that can be recognised from
syntax alone.  The rest -- a witness list truncated by a display budget and then
read as a verdict, a `not result.success` folded into the same `None` a
geometric fact returns, an enumeration cap that silently reclassifies a law --
are *semantic*, and every predicate wide enough to catch them fired on dozens of
correct `if proc.returncode != 0: raise` lines.  A check with a false-positive
rate nobody will read is not a check, so those stay with the negative-control
tests in `tests/test_tool_failure_is_not_truth.py`, which catch them by
behaviour instead.  This module says what it covers rather than implying it
covers the family.

## Why `ast` and not a regex

`figures/verify.sh`'s seventh gate lost its first regex draft to exactly this:
comparisons wrap across lines, appear inside f-strings, and are spelled a dozen
ways.  The parse also gives the two things a regex cannot: whether the
comparison's value is *bound* to anything, and what it is bound to.

## What a caller should do about a finding

Route the comparison through a predicate that adjudicates it, the way
`backends.proves_unsolvable` does -- rung, log and exit code together, refusing
in the direction that can only ever decline a real proof.  Then the verdict is
a call, not a comparison, and this check is silent because the question is being
asked somewhere a reader can find it.
"""

from __future__ import annotations

import ast
import os
import sys
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Set, Tuple

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: Identifiers naming a fact about a *tool*: how it exited, whether it
#: succeeded, whether it ran out of time.  Matched on whole `_`-separated tokens
#: of the trailing name, never as substrings -- `status` must not be found
#: inside `statustext`, and `rc` must not be found inside `src`.
TOOL_STATUS_TOKENS: Set[str] = {
    "returncode", "return_code", "returnstatus",
    "exit", "exitcode", "exit_code", "exitstatus", "exit_status",
    "retcode", "ret_code",
    "success", "succeeded", "failed", "failure",
    "timedout", "timed_out",
    "killed", "crashed",
}

#: The same idea, spelled with words this repository also uses for its **own**
#: verdicts: `Reachability.status` is an engine's answer, not a planner's exit
#: code, and `probe.reach.status == UNREACHABLE` is the correct reading of a
#: proof rather than a defect.  Calibration flagged both of those and nothing
#: else, so these tokens count only when the comparison is against an *integer
#: literal* -- the shape exit codes and solver status codes actually take
#: (`== 12`, `!= 2`).  A comparison against a named constant is the engine
#: talking about itself and is left alone.
WEAK_STATUS_TOKENS: Set[str] = {
    "status", "statuscode", "status_code", "rc", "code",
    "signal", "timeout", "error",
}

#: Identifiers asserting something about the *world* -- the object under study.
#: A tool-status comparison bound to one of these is the defect.
VERDICT_TOKENS: Set[str] = {
    "unsolvable", "solvable", "unsat", "sat", "satisfiable", "unsatisfiable",
    "infeasible", "feasible", "unreachable", "reachable",
    "proved", "proven", "prove", "proves", "disproved", "refuted",
    "holds", "hold", "valid", "invalid", "sound", "unsound",
    "verified", "certified", "certificate", "theorem",
    "violated", "violation", "contradiction",
    "deadlock", "equivalent", "same_answer",
}

#: Words this repository uses for *"the thing I ran came back fine"* --
#: `ok = proc.returncode == 0`, `"green": not failed`.  Reading an exit code
#: into one of these is usually the correct thing to do, and the calibration
#: measured it: 22 of the 26 repo-wide hits under the wider vocabulary were of
#: this shape and 20 of those were correct code.  So they are reported as notes
#: and never fail the check.  The distinction that earns the split is real --
#: `ok` names a fact about the process, `unsolvable` names a fact about the
#: world -- but it is a naming convention, so the notes are worth reading and
#: not worth gating on.
SOFT_VERDICT_TOKENS: Set[str] = {
    "ok", "green", "pass", "passed", "clean", "safe", "healthy", "alive",
    "success", "successful", "good", "fine", "complete", "done",
    "correct", "incorrect", "true", "false", "agree", "agrees", "disagree",
    "matches", "same", "exists", "empty", "live", "dead", "possible",
    "impossible",
}

#: Comparison operators that turn a status into a boolean.
_BOOL_OPS = (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
             ast.In, ast.NotIn, ast.Is, ast.IsNot)


def tokens(identifier: str) -> Set[str]:
    """`fd_exit_code` -> {fd, exit, code, exit_code, fd_exit_code}.

    Both the parts and the whole, so `exit_code` matches as a compound while
    `code` alone -- far too common -- never has to be in the vocabulary.
    """
    lowered = identifier.lower()
    parts = [p for p in lowered.split("_") if p]
    out: Set[str] = set(parts) | {lowered}
    for i in range(len(parts) - 1):
        out.add("_".join(parts[i:i + 2]))
    return out


def _trailing_name(node: ast.AST) -> Optional[str]:
    """The identifier a status expression is spelled with, if there is one."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        key = node.slice
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            return key.value
        return _trailing_name(node.value)
    if isinstance(node, ast.Call):
        return _trailing_name(node.func)
    return None


def _is_tool_status(node: ast.AST, weak_ok: bool = False) -> bool:
    name = _trailing_name(node)
    if not name:
        return False
    found = tokens(name)
    if found & TOOL_STATUS_TOKENS:
        return True
    return weak_ok and bool(found & WEAK_STATUS_TOKENS)


def _is_int_literal(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant) and isinstance(node.value, int) \
            and not isinstance(node.value, bool):
        return True
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return bool(node.elts) and all(_is_int_literal(e) for e in node.elts)
    return False


ERROR, NOTE = "error", "note"


def _verdict_level(name: Optional[str]) -> Optional[str]:
    """`error` for a claim about the world, `note` for one about the process."""
    if not name:
        return None
    found = tokens(name)
    if found & VERDICT_TOKENS:
        return ERROR
    if found & SOFT_VERDICT_TOKENS:
        return NOTE
    return None


def _mentions_tool_status(node: ast.AST) -> bool:
    """Does this expression read a tool-status value anywhere inside it?"""
    for child in ast.walk(node):
        if isinstance(child, (ast.Name, ast.Attribute, ast.Subscript)) \
                and _is_tool_status(child):
            return True
    return False


def _adjudicated(node: ast.AST) -> bool:
    """Is the status read inside a call -- i.e. handed to a predicate?

    `proves_unsolvable(rung, done.returncode, log)` is the shape the fix takes,
    and it is not a finding: the question is being decided somewhere a reader
    can find it, by something that can also see the rung and the log.
    """
    return any(isinstance(child, ast.Call) and _mentions_tool_status(child)
               for child in ast.walk(node))


def _status_comparisons(node: ast.AST) -> bool:
    """Does this expression *decide* a boolean from a tool status, unaided?"""
    if _adjudicated(node):
        return False
    for child in ast.walk(node):
        if isinstance(child, ast.Compare):
            operands = [child.left] + list(child.comparators)
            if any(_is_tool_status(o) for o in operands):
                return True
            # A weakly-named status counts only against an integer literal.
            if any(_is_tool_status(o, weak_ok=True) for o in operands) \
                    and any(_is_int_literal(o) for o in operands):
                return True
        if isinstance(child, ast.UnaryOp) and isinstance(child.op, ast.Not):
            if _is_tool_status(child.operand):
                return True
    return False


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    target: str
    source: str
    level: str = ERROR

    def render(self, root: str = HERE) -> str:
        rel = os.path.relpath(self.path, root).replace(os.sep, "/")
        return "%-5s %s:%d: `%s` is decided by a tool's status\n      %s" % (
            self.level.upper(), rel, self.line, self.target,
            self.source.strip())


class _Visitor(ast.NodeVisitor):
    """Bindings only.  A comparison nobody stores decides nothing."""

    def __init__(self, path: str, lines: Sequence[str]):
        self.path = path
        self.lines = lines
        self.findings: List[Finding] = []

    def _record(self, target: str, node: ast.AST, level: str) -> None:
        line = getattr(node, "lineno", 0)
        source = self.lines[line - 1] if 0 < line <= len(self.lines) else ""
        self.findings.append(Finding(self.path, line, target, source, level))

    def _check(self, target: Optional[str], value: Optional[ast.AST]) -> None:
        if value is None:
            return
        level = _verdict_level(target)
        if level is None:
            return
        if _status_comparisons(value):
            self._record(target or "?", value, level)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            self._check(_trailing_name(target), node.value)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self._check(_trailing_name(node.target), node.value)
        self.generic_visit(node)

    def visit_keyword(self, node: ast.keyword) -> None:
        self._check(node.arg, node.value)
        self.generic_visit(node)

    def visit_Dict(self, node: ast.Dict) -> None:
        for key, value in zip(node.keys, node.values):
            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                self._check(key.value, value)
        self.generic_visit(node)

    def _visit_function(self, node) -> None:
        if _verdict_level(node.name) is not None:
            for child in ast.walk(node):
                if isinstance(child, ast.Return):
                    self._check(node.name, child.value)
        self.generic_visit(node)

    visit_FunctionDef = _visit_function
    visit_AsyncFunctionDef = _visit_function


def check_source(text: str, path: str) -> List[Finding]:
    tree = ast.parse(text, filename=path)
    visitor = _Visitor(path, text.splitlines())
    visitor.visit(tree)
    return visitor.findings


def python_files(roots: Sequence[str]) -> Iterable[str]:
    skip = {"__pycache__", ".git", ".worktrees", ".toolchain", ".pytest_cache",
            "node_modules", ".venv", "runs"}
    for root in roots:
        if os.path.isfile(root):
            yield root
            continue
        for base, dirs, names in os.walk(root):
            dirs[:] = sorted(d for d in dirs if d not in skip)
            for name in sorted(names):
                if name.endswith(".py"):
                    yield os.path.join(base, name)


def check_paths(roots: Sequence[str]) -> List[Finding]:
    findings: List[Finding] = []
    for path in python_files(roots):
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            text = handle.read()
        try:
            findings += check_source(text, path)
        except SyntaxError:
            # A file this interpreter cannot parse is not a file this check has
            # cleared.  Reported, never skipped into silence -- that would be
            # the same defect one level up.
            findings.append(Finding(path, 0, "<unparsed>",
                                    "file could not be parsed; not checked",
                                    ERROR))
    return findings


def main(argv: Sequence[str]) -> int:
    args = list(argv[1:])
    show_notes = "--notes" in args
    roots = [a for a in args if not a.startswith("-")] or [HERE]
    findings = check_paths(roots)
    errors = [f for f in findings if f.level == ERROR]
    notes = [f for f in findings if f.level == NOTE]

    for finding in errors:
        print(finding.render())
    if show_notes:
        for finding in notes:
            print(finding.render())

    if errors:
        print("")
        print("%d place(s) decide a claim about the world from a tool's exit "
              "status.  Route each through a predicate that weighs the status "
              "against what the run was entitled to conclude -- "
              "`engines/fd_adapter/backends.proves_unsolvable` is the worked "
              "example." % len(errors))
        if notes and not show_notes:
            print("(%d further note-level hit(s); pass --notes to list them)"
                  % len(notes))
        return 1
    print("no claim about the world is decided by a bare tool status "
          "(%d files scanned, %d note-level hit(s))"
          % (sum(1 for _ in python_files(roots)), len(notes)))
    return 0


if __name__ == "__main__":       # pragma: no cover
    sys.exit(main(sys.argv))
