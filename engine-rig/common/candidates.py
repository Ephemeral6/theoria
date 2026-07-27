"""Writer for candidates.jsonl, bound to CONTRACTS/candidates_schema.md (frozen v0.1).

Every engine proposes through here; nothing else in this rig writes to a
candidates file.  Two rules from the contract are enforced structurally rather
than by convention:

  * append-only -- the file is opened in "a" mode, never "w";
  * status is always "candidate" -- it is not a parameter of `make_candidate`.

Determinism note: the contract mandates a uuid `id` and an ISO8601 `timestamp`,
both of which are inherently non-reproducible.  For tests and for byte-stable
integration runs, set THEORIA_FIXED_TIME (ISO8601) and THEORIA_DETERMINISTIC_IDS=1;
ids then become uuid5 of the candidate content.  See DECISIONS.md D-004.
"""

import hashlib
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence

from common.jsonio import append_jsonl, dumps

ENGINES = (
    "mdl_segmenter",
    "cegis_miner",
    "zero_space",
    "lp_potential",
    "fd_adapter",
    "probe_frontier",
)

KINDS = (
    "object_hypothesis",
    "rule_hypothesis",
    "invariant",
    "heuristic",
    "plan",
    "probe_design",
)

# Fixed namespace for deterministic ids (uuid5). Arbitrary but frozen.
_NS = uuid.UUID("6ba7b812-9dad-11d1-80b4-00c04fd430c8")


def _now_iso() -> str:
    fixed = os.environ.get("THEORIA_FIXED_TIME")
    if fixed:
        return fixed
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _make_id(engine: str, kind: str, payload: Any, evidence: Any) -> str:
    if os.environ.get("THEORIA_DETERMINISTIC_IDS") == "1":
        digest = hashlib.sha256(
            dumps([engine, kind, payload, evidence]).encode("utf-8")
        ).hexdigest()
        return str(uuid.uuid5(_NS, digest))
    return str(uuid.uuid4())


def make_candidate(
    engine: str,
    kind: str,
    payload: Dict[str, Any],
    transitions: Sequence[int],
    coverage: str,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """Build one contract-shaped candidate object.

    `coverage` is the literal "<k>/<n>" string the contract asks for: k supporting
    transitions out of n transitions where the proposal's guard applies.
    """
    if engine not in ENGINES:
        raise ValueError("unknown engine: %r" % (engine,))
    if kind not in KINDS:
        raise ValueError("unknown kind: %r" % (kind,))
    if not isinstance(payload, dict):
        raise TypeError("payload must be an object")
    transitions = [int(t) for t in transitions]
    evidence = {"transitions": transitions, "coverage": str(coverage)}
    return {
        "id": _make_id(engine, kind, payload, evidence),
        "engine": engine,
        "kind": kind,
        "payload": payload,
        "evidence": evidence,
        "status": "candidate",
        "timestamp": timestamp or _now_iso(),
    }


def emit(path: str, candidates: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Append candidates to `path` (append-only) and return them."""
    rows = list(candidates)
    append_jsonl(path, rows)
    return rows
