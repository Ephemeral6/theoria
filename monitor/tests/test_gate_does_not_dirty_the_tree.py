"""The gate's own suite must not write into the tree it is gating.

`monitor/verify.py`'s module docstring carries a section headed *"The gate does
not dirty the workspace"*, and it explains why the property matters: `state.json`,
`index.html` and `history.jsonl` are all rewritten by a scan, so a gate that ran
one in place *"would report its own output as a change and could turn the next
territory's gate red for a reason that has nothing to do with the branch being
merged."*

The paragraph was true of the stage it was written about. It was false of the
gate. `verify.py` has three stages and the **first** one is `pytest monitor/tests`
— and `test_verdict_reconcile.py` called `scan.build()` with no `out_dir`, which
writes into `monitor/` itself. So every single run of `monitor/verify.py` left
`monitor/index.html` and `monitor/state.json` modified in the working tree.
Measured on 2026-07-29: `git checkout -- ...` then `python -m pytest
monitor/tests` was enough on its own, without the scan stage running at all.

That is this lane's standing shape twice over. The safety property was **stated
in prose and enforced in one of the two places that needed it** — the same
"true of the module, false of the package" split that R3 was named after. And it
failed in the reassuring direction: a dirty tree after a gate run reads as *"my
branch changed something"*, so the natural reaction is to commit the noise, which
is how two generated artefacts nearly rode into an unrelated board-fix branch.

This file is the guard. It is a source-level check rather than a behavioural one
on purpose: catching it by observing the filesystem would require running the
whole suite from inside the suite, and the thing worth pinning is the *rule* —
a test that scans must scan into a temporary directory.
"""

import ast
import os

HERE = os.path.dirname(os.path.abspath(__file__))

#: Functions that write into `monitor/` unless told otherwise. `out_dir` exists
#: on `scan.build` precisely so a gate can run a real scan without dirtying the
#: workspace it is gating; the parameter is only worth having if it is used.
MUST_PASS_OUT_DIR = {"build"}


def _scan_build_calls(path):
    """Every `scan.build(...)` in `path`, as `(lineno, passes_out_dir)`."""
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read(), filename=path)
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr not in MUST_PASS_OUT_DIR:
            continue
        if not (isinstance(func.value, ast.Name) and func.value.id == "scan"):
            continue
        passes = any(kw.arg == "out_dir" for kw in node.keywords)
        out.append((node.lineno, passes))
    return out


def test_no_test_scans_into_the_repository():
    """`scan.build()` with no `out_dir` writes state.json and index.html into monitor/.

    The failure this pins is not hypothetical and not old: it was live until
    2026-07-29, in `test_verdict_reconcile.py`, and it made `monitor/verify.py`
    dirty the tree on every run while the gate's own docstring asserted it did
    not.
    """
    offenders = []
    for name in sorted(os.listdir(HERE)):
        if not (name.startswith("test_") and name.endswith(".py")):
            continue
        for lineno, passes in _scan_build_calls(os.path.join(HERE, name)):
            if not passes:
                offenders.append("%s:%d" % (name, lineno))

    assert not offenders, (
        "these call scan.build() without out_dir, so running the suite rewrites "
        "monitor/state.json and monitor/index.html in place: %s"
        % ", ".join(offenders))


def test_the_check_can_actually_see_a_violation():
    """The positive control. A guard that cannot fail is not a guard.

    Written because the check above is a source scan: if the AST matching were
    wrong -- an attribute renamed, a call shape unhandled -- it would find
    nothing and pass forever, which looks exactly like compliance.
    """
    bad = os.path.join(HERE, "_probe_violation.py")
    with open(bad, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("import scan\n\n\ndef f():\n    return scan.build()\n")
    try:
        calls = _scan_build_calls(bad)
        assert calls == [(5, False)], calls
    finally:
        os.remove(bad)

    good = os.path.join(HERE, "_probe_compliant.py")
    with open(good, "w", encoding="utf-8", newline="\n") as fh:
        # real-scan-exempt: a string literal fed to this file's own AST matcher.
        # Nothing here calls anything.
        fh.write("import scan\n\n\ndef f(d):\n    return scan.build(False, out_dir=d)\n")
    try:
        assert _scan_build_calls(good) == [(5, True)]
    finally:
        os.remove(good)
