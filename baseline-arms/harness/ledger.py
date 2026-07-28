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

#: Which campaign this process's lines belong to.
#:
#: PARTNER_SYNC.md:456 recorded the cost of not having this: one `ledger.jsonl`
#: ended up holding two campaigns and **no line could say which was which**, so
#: battery had to reverse-derive it from `out/campaign_cells.jsonl` (D-B-013).
#: An append-only file cannot be repaired afterwards, which is what makes an
#: absent attribution field permanently expensive rather than merely untidy.
#:
#: Read from the environment for the same reason the shard is: the full run
#: puts one process per game, and the campaign is a property of the launch, not
#: of any one call site.
CAMPAIGN_ENV = "BASELINE_ARMS_CAMPAIGN"

#: What a line says when nobody declared a campaign. Written explicitly, never
#: omitted and never guessed: "we do not know" and "the field is missing" look
#: identical to a later reader, and only one of them is honest.
UNKNOWN_CAMPAIGN = "unknown"

#: Where the decidable historical attribution comes from. One row per campaign
#: cell, carrying both `run_id` and `campaign`.
CAMPAIGN_CELLS = os.path.join(TRACK, "out", "campaign_cells.jsonl")


def utcnow() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def current_campaign() -> str:
    """This process's campaign, or an explicit `unknown`."""
    return os.environ.get(CAMPAIGN_ENV) or UNKNOWN_CAMPAIGN


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
             campaign: str = None, **extra: Any) -> Dict[str, Any]:
    """One environment interaction. `frame` is stored raw, as returned."""
    if arm not in ARMS:
        raise ValueError("arm must be one of %s, got %r" % (ARMS, arm))
    entry = {
        "game_id": game_id,
        "run_id": run_id,
        "arm": arm,
        "campaign": campaign or current_campaign(),
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
               path: str = LEDGER_PATH, campaign: str = None,
               **extra: Any) -> Dict[str, Any]:
    """One model invocation. `usage` is copied through verbatim, no reshaping."""
    entry = {
        "run_id": run_id,
        "campaign": campaign or current_campaign(),
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


# -- historical attribution, without rewriting the past ----------------------
#
# Lines written before `campaign` existed do not have it, and `ledger.jsonl` is
# append-only, so they cannot be given it in place. Rewriting it would be the
# INC-008 manoeuvre -- a deliberate, incident-recorded exception -- and there is
# no cause for one here: nothing is *wrong* in those lines, they are merely
# silent, and the attribution can be recovered at read time from a file that
# already exists. So the backfill is a **view**, not an edit.
#
# The rule is exact and has exactly one source: `out/campaign_cells.jsonl` pairs
# `run_id` with `campaign`. A line whose `run_id` is in that file is decidable.
# Everything else is `unknown` -- and stays `unknown`, because the alternative
# on offer (guess from the timestamp, or from which games ran together) is
# precisely the kind of reconstruction that would make a spend figure
# unfalsifiable.


def campaign_index(path: str = None) -> Dict[str, str]:
    """`run_id` -> `campaign`, from the campaign cell records. Empty if absent."""
    path = path or CAMPAIGN_CELLS
    index: Dict[str, str] = {}
    if not os.path.exists(path):
        return index
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                cell = json.loads(line)
            except json.JSONDecodeError:
                continue
            run_id, campaign = cell.get("run_id"), cell.get("campaign")
            if run_id and campaign:
                index[run_id] = campaign
    return index


def campaign_of(entry: Dict[str, Any], index: Dict[str, str] = None) -> str:
    """The campaign a ledger line belongs to, or an explicit `unknown`.

    Order: what the line says, then what the cell records say, then `unknown`.
    A line that carries its own campaign is never overridden -- the writer knew
    and the index is a reconstruction.
    """
    stated = entry.get("campaign")
    if stated:
        return str(stated)
    index = campaign_index() if index is None else index
    return index.get(entry.get("run_id"), UNKNOWN_CAMPAIGN)


def attribution_report(path: str = LEDGER_PATH,
                       cells: str = None) -> Dict[str, Any]:
    """How much of a ledger can be attributed, and how much cannot.

    A number rather than an assurance. `undecidable` is the count this ticket
    could not fix and did not pretend to.
    """
    index = campaign_index(cells)
    counts: Dict[str, int] = {}
    stated = decided = undecidable = total = 0
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                total += 1
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    undecidable += 1
                    counts[UNKNOWN_CAMPAIGN] = counts.get(UNKNOWN_CAMPAIGN, 0) + 1
                    continue
                if entry.get("campaign"):
                    stated += 1
                elif entry.get("run_id") in index:
                    decided += 1
                else:
                    undecidable += 1
                name = campaign_of(entry, index)
                counts[name] = counts.get(name, 0) + 1
    return {"ledger": path, "lines": total,
            "stated_in_line": stated,
            "decided_from_campaign_cells": decided,
            "undecidable": undecidable,
            "by_campaign": counts,
            "rule": ("a line's own `campaign` wins; otherwise `run_id` is looked "
                     "up in out/campaign_cells.jsonl; otherwise `unknown`. "
                     "Nothing is inferred from timestamps or co-occurrence."),
            "note": ("this is a read-time view. `ledger.jsonl` is append-only "
                     "and is not rewritten by anything in this module.")}


if __name__ == "__main__":
    print(json.dumps(attribution_report(), indent=2, sort_keys=True))
