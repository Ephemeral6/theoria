"""The executable form of LEDGER_FORMAT.md v1.0.

Append-only by construction: there is no update, rewrite or delete path in this
module. Corrections are new `incident` records.

Every record goes through `redact.VAULT.scrub()` on its way to disk, so a
credential cannot reach the file even if an arm put one in a request body.
"""

import hashlib
import json
import os
import threading
import time
from typing import Any, Dict, List, Optional

from . import LEDGER_VERSION
from .paths import LEDGER_PATH
from .redact import VAULT

EVENTS = frozenset({
    "env_step", "model_call", "run_start", "run_end",
    "env_meta", "guard_block", "incident",
})

ARMS = frozenset({
    "bare_cc", "schema_repro", "theoria", "probe", "replay", "mock_arm",
})

INCIDENT_KINDS = frozenset({
    "score_mismatch", "replay_mismatch", "nondeterminism",
    "credential_in_body", "bypass_attempt", "sealed_pile_request",
})

_LOCKS: Dict[str, threading.Lock] = {}
_LOCKS_GUARD = threading.Lock()


def canonical(obj: Any) -> str:
    """One JSON spelling per value, so a line's bytes are determined by its
    content and two writers cannot disagree."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def sha256(obj: Any) -> str:
    blob = obj if isinstance(obj, (bytes, bytearray)) else canonical(obj).encode("utf-8")
    return "sha256:" + hashlib.sha256(blob).hexdigest()


def utcnow() -> str:
    seconds = time.time()
    base = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(seconds))
    return "%s.%03dZ" % (base, int((seconds % 1) * 1000))


def frame_hash(frames: Optional[List[Any]]) -> Optional[str]:
    """The unit of replay comparison. Hashes the frame list whole, so a command
    that returns seven frames is one hash, not seven."""
    if frames is None:
        return None
    return sha256(frames)


def _lock_for(path: str) -> threading.Lock:
    key = os.path.abspath(path)
    with _LOCKS_GUARD:
        if key not in _LOCKS:
            _LOCKS[key] = threading.Lock()
        return _LOCKS[key]


def _last_seq(path: str) -> int:
    if not os.path.exists(path):
        return 0
    last = 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                last = max(last, int(json.loads(line).get("seq", 0)))
            except (ValueError, AttributeError):
                continue
    return last


class Ledger:
    """One ledger file. Thread-safe; `seq` is assigned under the lock so it is
    dense and monotonic even with several proxy threads writing."""

    def __init__(self, path: str = LEDGER_PATH):
        self.path = path
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self._lock = _lock_for(path)
        with self._lock:
            self._seq = _last_seq(path)

    def append(self, event: str, run_id: str, arm: str, **fields: Any) -> Dict[str, Any]:
        if event not in EVENTS:
            raise ValueError("unknown event %r (LEDGER_FORMAT.md §3, §4, §6)" % event)
        if arm not in ARMS:
            raise ValueError("unknown arm %r; register it in ledger.ARMS" % (arm,))
        record: Dict[str, Any] = {
            "v": LEDGER_VERSION,
            "event": event,
            "run_id": run_id,
            "arm": arm,
        }
        record.update(VAULT.scrub(fields))
        with self._lock:
            self._seq += 1
            record["seq"] = self._seq
            record["ts"] = utcnow()
            line = canonical(record)
            with open(self.path, "a", encoding="utf-8", newline="") as fh:
                fh.write(line)
                fh.write("\n")
        return record

    # -- reading -----------------------------------------------------------
    def read(self) -> List[Dict[str, Any]]:
        return read_ledger(self.path)


def read_ledger(path: str = LEDGER_PATH) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    out = []
    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError("%s:%d is not JSON: %s" % (path, lineno, exc))
            version = record.get("v")
            if version != LEDGER_VERSION:
                raise ValueError(
                    "%s:%d has ledger version %r, this reader knows %r. A reader "
                    "must reject what it does not know rather than guess "
                    "(LEDGER_FORMAT.md §8)." % (path, lineno, version, LEDGER_VERSION)
                )
            out.append(record)
    return out


def records_for(run_id: str, path: str = LEDGER_PATH, event: Optional[str] = None):
    return [r for r in read_ledger(path)
            if r.get("run_id") == run_id and (event is None or r.get("event") == event)]


class RunLedger:
    """A ledger bound to one run: keeps the step and call counters, and derives
    the level boundaries that LEDGER_FORMAT.md §3 assigns to the ledger."""

    def __init__(self, ledger: Ledger, run_id: str, arm: str):
        self.ledger = ledger
        self.run_id = run_id
        self.arm = arm
        self._step_idx = -1
        self._call_idx = -1
        self._levels_completed = 0
        self._counter_lock = threading.Lock()

    def _next_step(self) -> int:
        with self._counter_lock:
            self._step_idx += 1
            return self._step_idx

    def _next_call(self) -> int:
        with self._counter_lock:
            self._call_idx += 1
            return self._call_idx

    def _append(self, event: str, **fields: Any) -> Dict[str, Any]:
        return self.ledger.append(event, self.run_id, self.arm, **fields)

    # -- the two shapes ----------------------------------------------------
    def env_step(self, game_id: str, action: Dict[str, Any],
                 frames: Optional[List[Any]] = None, *,
                 card_id: Optional[str] = None, guid: Optional[str] = None,
                 state: Optional[str] = None, score: Optional[int] = None,
                 levels_completed: Optional[int] = None,
                 variant: Optional[Dict[str, Any]] = None,
                 guard: Optional[Dict[str, Any]] = None,
                 http: Optional[Dict[str, Any]] = None,
                 step_idx: Optional[int] = None,
                 **extra: Any) -> Dict[str, Any]:
        idx = self._next_step() if step_idx is None else step_idx

        # Level derivation. `levels_completed` before the step is the level the
        # step happened on; an increase means the step ended a level.
        before = self._levels_completed
        after = before if levels_completed is None else int(levels_completed)
        boundary = after > before
        self._levels_completed = after

        return self._append(
            "env_step",
            game_id=game_id,
            card_id=card_id,
            guid=guid,
            step_idx=idx,
            action=action,
            frames=frames,
            n_frames=0 if frames is None else len(frames),
            frame_hash=frame_hash(frames),
            state=state,
            score=score,
            levels_completed=levels_completed,
            level=before,
            level_boundary=boundary,
            variant=variant,
            guard=guard or {"decision": "allow"},
            http=http or {},
            **extra,
        )

    def model_call(self, provider: str, model: str, *,
                   request: Any = None, response: Any = None,
                   usage: Optional[Dict[str, Any]] = None,
                   pricing_ref: Optional[Dict[str, Any]] = None,
                   step_idx: Optional[int] = None,
                   http: Optional[Dict[str, Any]] = None,
                   **extra: Any) -> Dict[str, Any]:
        if "cost" in extra or "cost_usd" in extra:
            raise ValueError(
                "cost does not belong in the ledger: it is a conversion from "
                "usage x a versioned price table (LEDGER_FORMAT.md §4, §5)."
            )
        return self._append(
            "model_call",
            call_idx=self._next_call(),
            provider=provider,
            model=model,
            request=request,
            response=response,
            usage=dict(usage or {}),
            pricing_ref=pricing_ref,
            step_idx=step_idx,
            http=http or {},
            **extra,
        )

    # -- auxiliaries -------------------------------------------------------
    def run_start(self, **fields: Any) -> Dict[str, Any]:
        return self._append("run_start", **fields)

    def run_end(self, **fields: Any) -> Dict[str, Any]:
        return self._append("run_end", **fields)

    def env_meta(self, **fields: Any) -> Dict[str, Any]:
        return self._append("env_meta", **fields)

    def guard_block(self, **fields: Any) -> Dict[str, Any]:
        return self._append("guard_block", **fields)

    def incident(self, kind: str, detail: Any, **fields: Any) -> Dict[str, Any]:
        if kind not in INCIDENT_KINDS:
            raise ValueError("unknown incident kind %r" % kind)
        return self._append("incident", kind=kind, detail=detail, **fields)
