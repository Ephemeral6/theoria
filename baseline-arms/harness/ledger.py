"""Append-only ledger for the baseline-arms track.

Two record types, fixed by the ticket so that this file can later be merged
verbatim with whatever `arc-gateway` produces:

    env_step    {"game_id","run_id","arm","model","action","frame","step_idx","timestamp"}
    model_call  {"run_id","provider","model","usage",...,"timestamp"}

Everything else this track records (API viability probes, harness diagnostics)
goes to a *separate* file, so `ledger.jsonl` stays exactly two shapes and stays
mergeable. See DECISIONS.md D-003.

The ledger is append-only by construction: there is no update or rewrite path
in this module, only `append`.
"""

import json
import os
import threading
import time
from typing import Any, Dict

HERE = os.path.dirname(os.path.abspath(__file__))
TRACK = os.path.dirname(HERE)

SHARD_DIR = os.path.join(TRACK, "out", "shards")
SHARD_ENV = "BASELINE_ARMS_SHARD"

ARMS = ("bare_cc", "schema_repro")


def utcnow() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _resolve(basename: str) -> str:
    """Where this process writes.

    The full run puts one *process* per game, all appending to one file. A
    single env_step carrying a 64x64 frame is tens of kilobytes -- many times
    what any OS appends atomically -- so concurrent writers will eventually
    interleave mid-record, and an append-only ledger cannot be repaired
    afterwards. A lock does not help: these are separate processes.

    So each writer gets its own shard, and `merge_ledger.py` concatenates the
    shards in timestamp order. Sharding preserves append-only (nothing is ever
    rewritten) while making interleaving structurally impossible.
    Unsharded callers -- single-process runs, tests -- keep the plain path.
    """
    shard = os.environ.get(SHARD_ENV)
    if not shard:
        return os.path.join(TRACK, basename)
    stem, ext = os.path.splitext(basename)
    return os.path.join(SHARD_DIR, "%s.%s%s" % (stem, shard, ext))


LEDGER_PATH = _resolve("ledger.jsonl")
PROBE_PATH = _resolve("probe_log.jsonl")

_WRITE_LOCK = threading.Lock()


def _append(path: str, entry: Dict[str, Any]) -> None:
    # Serialise fully before opening, and hold the lock across the write, so a
    # threaded caller inside one process cannot interleave either.
    line = json.dumps(entry, sort_keys=True, ensure_ascii=True) + "\n"
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with _WRITE_LOCK:
        with open(path, "a", encoding="utf-8", newline="") as fh:
            fh.write(line)


def env_step(game_id: str, run_id: str, arm: str, model: str, action: Any,
             frame: Any, step_idx: int, path: str = LEDGER_PATH,
             **extra: Any) -> Dict[str, Any]:
    """One environment interaction. `frame` is stored raw, as returned."""
    if arm not in ARMS:
        raise ValueError("arm must be one of %s, got %r" % (ARMS, arm))
    entry = {
        "game_id": game_id,
        "run_id": run_id,
        "arm": arm,
        "model": model,
        "action": action,
        "frame": frame,
        "step_idx": step_idx,
        "timestamp": utcnow(),
    }
    entry.update(extra)
    _append(path, entry)
    return entry


def model_call(run_id: str, provider: str, model: str, usage: Dict[str, Any],
               path: str = LEDGER_PATH, **extra: Any) -> Dict[str, Any]:
    """One model invocation. `usage` is copied through verbatim, no reshaping."""
    entry = {
        "run_id": run_id,
        "provider": provider,
        "model": model,
        "usage": dict(usage),
        "timestamp": utcnow(),
    }
    entry.update(extra)
    _append(path, entry)
    return entry


def probe(kind: str, detail: Dict[str, Any], path: str = PROBE_PATH) -> Dict[str, Any]:
    """Anything that is not a game step or a model call."""
    entry = {"kind": kind, "timestamp": utcnow()}
    entry.update(detail)
    _append(path, entry)
    return entry
