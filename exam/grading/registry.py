"""The rubric registry, and the digest that freezes it.

Every question type contributes one module named `rubrics_<type>.py`, each
exposing `RUBRICS: Sequence[Rubric]`.  The registry imports them, refuses
duplicate ids, and hashes the *source text* of every contributing module.

Hashing the source rather than the ids is the point.  An id list is stable while
the marking behind it changes; the source is not.  The digest travels onto every
sheet at build time and onto every report at grading time, so "the rubric was
loosened after the answers came in" is a mismatch the tooling prints rather than
an accusation someone has to make.  It is the same move as the battery's
pre-registered directions, one layer down.

The digest deliberately covers docstrings and comments too.  A tighter digest
over the code alone would be less noisy, and would also let the *justification*
for a mark drift away from the mark -- which is the failure this project cares
about most.
"""

from __future__ import annotations

import hashlib
import importlib
import inspect
import os
from typing import Dict, List, Sequence, Tuple

from ..model import ExamError, Rubric

HERE = os.path.dirname(os.path.abspath(__file__))

#: Frozen order.  Adding a module changes the digest, which is intended.
RUBRIC_MODULES: Tuple[str, ...] = (
    "exam.grading.rubrics_heldout",
    "exam.grading.rubrics_handover",
    "exam.grading.rubrics_adaptation",
    "exam.grading.rubrics_verdict",
)


def _load() -> Tuple[Dict[str, Rubric], str, Dict[str, str]]:
    rubrics: Dict[str, Rubric] = {}
    per_module: Dict[str, str] = {}
    hasher = hashlib.sha256()
    for name in RUBRIC_MODULES:
        module = importlib.import_module(name)
        source = inspect.getsource(module)
        digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
        per_module[name] = digest
        hasher.update(("%s:%s\n" % (name, digest)).encode("utf-8"))
        for rubric in getattr(module, "RUBRICS", ()):
            if rubric.rubric_id in rubrics:
                raise ExamError(
                    "two modules define rubric %r; a rubric id must name exactly "
                    "one marking rule or a report cannot be read"
                    % rubric.rubric_id)
            rubrics[rubric.rubric_id] = rubric
    return rubrics, hasher.hexdigest(), per_module


_RUBRICS: Dict[str, Rubric] = {}
_DIGEST = ""
_PER_MODULE: Dict[str, str] = {}


def _ensure() -> None:
    global _RUBRICS, _DIGEST, _PER_MODULE
    if not _RUBRICS:
        _RUBRICS, _DIGEST, _PER_MODULE = _load()


def rubric(rubric_id: str) -> Rubric:
    _ensure()
    if rubric_id not in _RUBRICS:
        raise ExamError("no rubric %r; registered: %s"
                        % (rubric_id, sorted(_RUBRICS)))
    return _RUBRICS[rubric_id]


def all_rubrics() -> Dict[str, Rubric]:
    _ensure()
    return dict(_RUBRICS)


def digest() -> str:
    """sha256 over the source of every rubric module, in frozen order."""
    _ensure()
    return _DIGEST


def module_digests() -> Dict[str, str]:
    _ensure()
    return dict(_PER_MODULE)


def manifest() -> Dict[str, object]:
    _ensure()
    return {
        "rubric_digest": _DIGEST,
        "modules": dict(sorted(_PER_MODULE.items())),
        "rubrics": {rid: r.description for rid, r in sorted(_RUBRICS.items())},
    }
