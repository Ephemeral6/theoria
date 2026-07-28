"""Hash every upstream file this arm reads, and check that a run changed none.

Two obligations, one module.

**Pin** — `cold-start-a2/a2pipeline/concepts.py` carries a manifest of the
upstream files it depends on and sha256s each one into `upstream_pin.json` on
every run, because those trees have work in flight from another session while
this one runs.  Same reason here, one tree further along.

**Verify** — `cold-start-a2/tools/verify_readonly.py` hashes the upstream trees,
runs the pipeline, hashes again, and diffs.  A2 reports 258 files, 0 changed.
That is the executable form of "reuse is read-only": the claim is checked rather
than asserted.  `verify.sh` runs it as a gate.

It is a function and a script rather than a pytest case for the reason A2 states:
two sessions work this repo concurrently, so the other track's files legitimately
change while this arm runs, and a test would be flaky for a reason that has
nothing to do with this arm's correctness.
"""

import hashlib
import os
from typing import Dict, Iterable, List

import _bootstrap  # noqa: F401
from _bootstrap import REPO  # noqa: E402

SKIP_DIRS = {".toolchain", "__pycache__", ".pytest_cache", ".git", ".claude",
             "artifacts", "runs", ".lake"}

#: The trees this arm imports from and must not touch.  `artifacts/` and `runs/`
#: are skipped: they are the upstream tracks' own outputs, they are regenerated
#: by their own drivers, and this arm reads a handful of committed files out of
#: them for comparison without ever writing there.
UPSTREAM_TREES = ("engine-rig", "theory-compiler", "cold-start-a0",
                  "cold-start-a2", "CONTRACTS", "proxy")


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_tree(trees: Iterable[str] = UPSTREAM_TREES,
              root: str = REPO) -> Dict[str, str]:
    """path (repo-relative, forward slashes) -> sha256, sorted by construction."""
    out: Dict[str, str] = {}
    for tree in trees:
        base = os.path.join(root, tree)
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
            for name in sorted(filenames):
                full = os.path.join(dirpath, name)
                rel = os.path.relpath(full, root).replace(os.sep, "/")
                try:
                    out[rel] = sha256_file(full)
                except OSError:
                    continue
    return dict(sorted(out.items()))


def changed(before: Dict[str, str], after: Dict[str, str]) -> List[str]:
    return sorted(key for key in set(before) | set(after)
                  if before.get(key) != after.get(key))


def pin(paths: Iterable[str], root: str = REPO) -> Dict[str, str]:
    """sha256 of a named list of files — the manifest form."""
    out = {}
    for rel in sorted(paths):
        full = os.path.join(root, rel.replace("/", os.sep))
        if os.path.exists(full):
            out[rel] = sha256_file(full)
    return out
