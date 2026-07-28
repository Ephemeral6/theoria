"""Make the suite test *this* tree, not whatever copy happens to be installed.

`pyproject.toml` declares an editable install, and an editable install records
an absolute path. In a second checkout — a git worktree, a clone, a CI job that
installed from elsewhere — `import theory_compiler` therefore resolves to the
*original* directory, and the tests run green against code the working tree does
not contain. That is not a hypothetical: it happened here, and a full green run
reported nothing about the edits sitting on disk beside it.

Putting this package's own `src/` at the front of `sys.path` makes the answer
"the tree the test file lives in", always. The installed distribution is still
importable for anyone who wants it; it is just no longer what the tests measure.
"""

import os
import shutil
import sys

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)


def pytest_collection_modifyitems(config, items):
    """`THEORIA_REQUIRE_LEAN=1` turns "lean is not on PATH" into a failure.

    The same hazard as the one above, one step over. A default `pytest -q`
    finishes green in half a second having never run `lean` — and the tests it
    skipped are the A1 product check itself: compile the generated development,
    read `#print axioms`, confirm the set is empty. "Green" then means "the
    string manipulation is consistent", which is not the claim anyone reads it
    as.

    Skipping stays the default, because a contributor without a toolchain
    should still be able to run the suite. What this adds is a way to say "this
    run is supposed to have proved something", for the runs that report results.
    """
    if os.environ.get("THEORIA_REQUIRE_LEAN") != "1":
        return
    if shutil.which("lean") or os.environ.get("LEAN"):
        return
    import pytest
    raise pytest.UsageError(
        "THEORIA_REQUIRE_LEAN=1 but no `lean` is on PATH and $LEAN is unset. "
        "The Lean tests would skip, and a run that skips them has not checked "
        "the axiom sets it is about to be quoted for.")
