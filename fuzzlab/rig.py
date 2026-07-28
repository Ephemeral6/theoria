"""Read-only bootstrap onto engine-rig.

engine-rig's packages (`common`, `engines`, `fixtures`) are top-level imports
rooted at the `engine-rig/` directory, so that directory goes on `sys.path`.
Importing is the *only* thing fuzzlab does to it: no writes, no monkey-patching,
no sys.modules surgery.  If a property fails, the finding lands in `BUGS.md`.

The path is resolved from this file's location rather than the working
directory, so a test run from anywhere picks up the engine-rig sitting in the
same checkout -- which matters in a worktree, where a stale absolute path would
silently test the wrong tree.
"""

import os
import sys

FUZZLAB_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(FUZZLAB_DIR)
ENGINE_RIG = os.path.join(REPO_ROOT, "engine-rig")


def bootstrap() -> str:
    """Put engine-rig on `sys.path` (idempotent) and return its path."""
    if not os.path.isdir(ENGINE_RIG):
        raise RuntimeError(
            "engine-rig not found at %s -- fuzzlab must sit beside it" % ENGINE_RIG
        )
    if ENGINE_RIG not in sys.path:
        sys.path.insert(0, ENGINE_RIG)
    return ENGINE_RIG


bootstrap()


def engine_rig_head() -> str:
    """Short git description of the engine-rig tree under test, for provenance."""
    import subprocess

    try:
        out = subprocess.run(
            ["git", "-C", REPO_ROOT, "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=30, check=False,
        )
        return out.stdout.strip() or "unknown"
    except Exception:                                    # pragma: no cover
        return "unknown"
