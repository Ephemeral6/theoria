"""Shared plumbing for the E18 recomputation scripts.

Three jobs, and nothing else:

* `repo_root()` / `add_repo_root()` — let a module import `fuzzlab.*` without
  assuming a particular working directory.
* `input_digests()` — the sha256 of every file the script *read to get its
  answer*.  A recomputation whose inputs are not pinned is only marginally
  better than prose: the number could move because a fixture moved.
* `emit()` — one output shape for every module, so `run_all` can aggregate and
  a reader can diff two runs byte-for-byte.

Determinism rules for anything in this package: no wall-clock, no
`random` without an explicit seed, no dict iteration order dependence that
is not sorted first.  `engine-rig/.gitattributes` pins LF, so the JSON these
scripts write is byte-stable across platforms.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Callable, Iterable

# tools/survey_numbers/_common.py -> tools/survey_numbers -> tools -> engine-rig -> repo
ENGINE_RIG = Path(__file__).resolve().parents[2]
REPO_ROOT = ENGINE_RIG.parent


def repo_root() -> Path:
    return REPO_ROOT


def add_repo_root() -> None:
    """Put the repo root on `sys.path` so `import fuzzlab...` works.

    The cross-checks deliberately draw their worlds from `fuzzlab`, which is a
    different territory.  We read it; we never write it.
    """
    root = str(REPO_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    rig = str(ENGINE_RIG)
    if rig not in sys.path:
        sys.path.insert(0, rig)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def input_digests(paths: Iterable[str | Path]) -> list[dict[str, Any]]:
    """sha256 every named input, repo-relative, sorted, missing files flagged."""
    out = []
    for p in sorted({str(p) for p in paths}):
        path = Path(p)
        if not path.is_absolute():
            path = REPO_ROOT / path
        rel = path.resolve().relative_to(REPO_ROOT).as_posix()
        if path.exists():
            out.append({"path": rel, "sha256": sha256_file(path)})
        else:
            out.append({"path": rel, "sha256": None, "missing": True})
    return sorted(out, key=lambda d: d["path"])


def result(
    *,
    key: str,
    question: str,
    value: Any,
    e11_prose: Any,
    counts: dict[str, Any],
    inputs: list[dict[str, Any]],
    method: str,
    caveats: list[str] | None = None,
) -> dict[str, Any]:
    """The one output shape.

    `key` matches the `ENGINE_TABLE.md` number-registry key where one exists, so
    the registry can be re-pointed from a prose regex to this script.
    `e11_prose` is what the 2026-07-29 report claimed, recorded verbatim so the
    comparison is in the artefact rather than in somebody's memory.
    """
    agrees = _agrees(value, e11_prose)
    return {
        "key": key,
        "question": question,
        "value": value,
        "e11_prose": e11_prose,
        "agrees_with_e11": agrees,
        "counts": counts,
        "inputs": inputs,
        "method": method,
        "caveats": caveats or [],
    }


def _agrees(value: Any, prose: Any) -> bool | None:
    if prose is None:
        return None
    if isinstance(value, float) and isinstance(prose, (int, float)):
        return abs(value - prose) < 5e-2
    return value == prose


def main(compute: Callable[[], dict[str, Any]]) -> None:
    """Print one module's result as sorted JSON on stdout."""
    json.dump(compute(), sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
