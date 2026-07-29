"""F7: is any `invariant_sandbox.WEAKENINGS` entry observationally a no-op?

Runs each `(prose_only, weakening)` pair the tests use and compares the full
subprocess output against the *unweakened* `prose_only` run.  A weakening whose
output is identical cannot be distinguished from its own control by any
assertion the paired test makes, so that test would pass unchanged if the patch
silently failed to apply.

**Unlike the other probes, this one runs against the working tree**, because it
imports `worldgen.tests.invariant_sandbox` rather than patching a source blob.
So its output tracks repairs, and that is the point of keeping it.

Result at review time, against commit `23ec179`:

    boolean_default            rc=1 (unweakened rc=1)  gate_lines_equal=True   stdout_equal=True
    pre_v19                    rc=0 (unweakened rc=1)  gate_lines_equal=False  stdout_equal=False
    unverified_sinks_to_holds  rc=0 (unweakened rc=1)  gate_lines_equal=False  stdout_equal=False
    drop_unverified_gate       rc=0 (unweakened rc=1)  gate_lines_equal=False  stdout_equal=False

`boolean_default` was byte-identical to the control.  The finding that test
reports (the conjunction is not what catches the defect) is true, but it was
established by the identity of these outputs, which the test never read.

A repaired tree should show `stdout_equal=False` on every row — a weakening
whose run is distinguishable from its control is a weakening its test can
actually assert on.  To see the original result, run this against the reviewed
commit in a worktree or `git stash` first; `git show 23ec179` is the reference.

Runnable from anywhere:

    python worldgen/runs/*-V19-*/adversarial/probe_weakening_is_a_noop.py
"""

import os
import sys
import tempfile

# Four up from `adversarial/` is the checkout root, whatever the cwd is.
sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))

from worldgen.tests import invariant_sandbox as ivs


def run(injection, weakening):
    root = tempfile.mkdtemp(prefix="v19-weakening-")
    ivs.make_sandbox(root, injection, weakening)
    into = tempfile.mkdtemp(prefix="v19-weakening-out-")
    proc = ivs.run_build(root, into)
    return proc.returncode, ivs.text(proc), ivs.gate_lines(proc)


base_rc, base_text, base_lines = run("prose_only", None)

for name in ("boolean_default", "pre_v19", "unverified_sinks_to_holds",
             "drop_unverified_gate"):
    rc, text, lines = run("prose_only", name)
    print("%-26s rc=%d (unweakened rc=%d)  gate_lines_equal=%s  stdout_equal=%s"
          % (name, rc, base_rc, lines == base_lines, text == base_text))
