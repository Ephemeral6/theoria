"""Lift a `baseline-arms` v0 ledger into canonical v1.0 (`LEDGER_FORMAT.md` §7).

F-16 ruled `proxy/LEDGER_FORMAT.md` the canon and the v0 spelling the dialect.
This is the translator. **The original file is never touched**: the tool reads
it, writes a new file, and reports what it did.

The interface this exposes is documented for the other track in
`proxy/CANON_MIGRATION.md`; the migration of the stock ledgers themselves is
P-12's, not this track's.

## What is carried, and the two things that are not

Nothing in a v0 record is thrown away silently. Most of it moves:

    frame                -> frames (already a list of grids in v0)
    timestamp            -> ts (".000" appended; v0 is second-precision)
    frames_returned      -> n_frames
    win_levels           -> response.win_levels
    available_actions    -> response.available_actions
    http_status/tries    -> http.status / http.attempts
    reason               -> http.error
    failed               -> falls out of http.status; v0's single flag
                            conflated "the server refused" with "the guard
                            refused", and canon separates them
    duration_ms          -> http.elapsed_ms
    attempt              -> http.attempts
    prompt_chars         -> http.request_chars
    model/arm            -> the synthesised run_start (they are run properties)

Two do not survive as fields, and both are recorded in the `run_start` as
totals so the number itself is not lost:

  * **`total_cost_usd`** -- §5 rules cost a derived quantity and `canon.py`
    refuses it. The v0 harness's own figure is kept in `run_start.lifted.dropped`
    as `total_cost_usd_v0`, labelled as the old harness's arithmetic rather than
    canon. Recomputing it properly needs a `pricing_ref`, which v0 never wrote.
  * **the model request and response bodies** -- v0 recorded neither, only
    `usage` and `prompt_chars`. `request`/`response` are therefore `null`, and
    that is a real hole in the lifted stream, not a lossy conversion: the bits
    were never written down. §4 says the full text is the substitute for a
    model call being unreplayable, so a lifted model_call is *less* than a
    canonical one and should not be read as equal to it.

## Provenance

§7 said to mark each lifted record `"lifted_from": "baseline-arms/v0"`. That was
written before the two shapes' field sets were closed, and a closed shape cannot
carry a marker. So provenance moves to the synthesised `run_start`, whose
payload is open (§6) -- and it says strictly more there: the source path, the
source's sha256, this tool's version, the record counts, and what was dropped.
Every lifted record belongs to a run, so nothing is unattributed.

    python -m proxy.tools.upgrade_ledger baseline-arms/ledger.jsonl -o out.jsonl
    python -m proxy.tools.upgrade_ledger in.jsonl -o out.jsonl \
        --scorecards baseline-arms/probe_log.jsonl
"""

import argparse
import hashlib
import json
import os
import sys
from typing import Any, Dict, Iterable, List, Optional

from .. import LEDGER_VERSION
from ..canon import check
from ..ledger import canonical, frame_hash
from ..redact import VAULT

MIGRATOR = "proxy.tools.upgrade_ledger"
MIGRATOR_VERSION = "1.0.0"
SOURCE_DIALECT = "baseline-arms/v0"


class UnknownDialect(ValueError):
    """A record that is neither v0 nor v1.0.

    The tool refuses rather than guessing. A migrator that guessed would write
    a canonical-looking record with invented meaning, and the invention would
    be indistinguishable from a recording afterwards.
    """


def sha256_file(path: str) -> str:
    with open(path, "rb") as fh:
        return "sha256:" + hashlib.sha256(fh.read()).hexdigest()


def _ts(value: Any) -> str:
    """v0 stamps to the second; canon wants milliseconds. The added ".000" is
    padding, not precision, and is documented as such."""
    if not isinstance(value, str) or not value:
        return "1970-01-01T00:00:00.000Z"
    if value.endswith("Z") and "." not in value:
        return value[:-1] + ".000Z"
    return value


def _action(raw: Any) -> Dict[str, Any]:
    if raw == "RESET":
        return {"name": "RESET", "id": None, "data": None}
    if isinstance(raw, dict):
        action_id = raw.get("id")
        return {"name": "ACTION%s" % action_id, "id": action_id,
                "data": raw.get("data")}
    raise UnknownDialect("unrecognised v0 action %r" % (raw,))


def is_v0_env(record: Dict[str, Any]) -> bool:
    return "action" in record and "run_id" in record


def is_v0_model(record: Dict[str, Any]) -> bool:
    return "usage" in record and "action" not in record


def scorecards_by_run(path: str) -> Dict[str, Any]:
    """Pull closed scorecards out of a v0 probe log, keyed by the run they
    name in `opaque.run_id`. A lifted run that has its card can actually be
    reconciled; one that has not is honestly `UNDETERMINED`."""
    cards: Dict[str, Any] = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("note") != "close scorecard" or record.get("status") != 200:
                continue
            body = record.get("response_summary") or record.get("response_body")
            if not isinstance(body, dict):
                continue
            run_id = (body.get("opaque") or {}).get("run_id")
            if run_id:
                cards[run_id] = body
    return cards


def lift(records: Iterable[Dict[str, Any]], *,
         source: str = "<memory>",
         source_sha256: Optional[str] = None,
         arm_override: Optional[str] = None,
         scorecards: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """v0 records in, canonical v1.0 records out, in the original order.

    `seq` is assigned over the whole output; `ts` is the original timestamp,
    not the migration time. A lifted stream is a record of when things
    happened, not of when they were translated.
    """
    scorecards = scorecards or {}
    runs: Dict[str, Dict[str, Any]] = {}
    body: List[Dict[str, Any]] = []

    def run_state(run_id: str) -> Dict[str, Any]:
        if run_id not in runs:
            runs[run_id] = {"levels": 0, "steps": 0, "model_calls": 0,
                            "cost_v0": 0.0, "arm": None, "model": None,
                            "game_id": None, "first_ts": None, "last_ts": None,
                            "step_idx": -1, "call_idx": -1}
        return runs[run_id]

    for record in records:
        if record.get("v") == LEDGER_VERSION:
            raise UnknownDialect(
                "this record is already v1.0; the migrator would double-lift it")
        run_id = record.get("run_id")
        if not isinstance(run_id, str):
            raise UnknownDialect("a v0 record without a run_id: %r"
                                 % (sorted(record),))
        state = run_state(run_id)
        ts = _ts(record.get("timestamp"))
        state["first_ts"] = state["first_ts"] or ts
        state["last_ts"] = ts

        if is_v0_env(record):
            state["arm"] = record.get("arm") or state["arm"] or arm_override
            state["model"] = record.get("model") or state["model"]
            state["game_id"] = record.get("game_id") or state["game_id"]
            state["step_idx"] += 1
            state["steps"] += 1

            frames = record.get("frame")
            if frames is not None and not isinstance(frames, list):
                frames = [frames]
            n_frames = record.get("frames_returned")
            if not isinstance(n_frames, int) or isinstance(n_frames, bool):
                n_frames = 0 if frames is None else len(frames)

            before = state["levels"]
            after = record.get("levels_completed")
            after = before if not isinstance(after, int) or isinstance(after, bool) else after
            state["levels"] = after

            http: Dict[str, Any] = {
                "method": "POST",
                "path": "/api/cmd/%s" % _action(record.get("action"))["name"],
                "status": record.get("http_status", 200 if not record.get("failed") else None),
                "attempts": record.get("http_tries", 1),
                "elapsed_ms": None,
                "forwarded": True,
            }
            if record.get("reason"):
                http["error"] = record["reason"]

            response: Optional[Dict[str, Any]] = {}
            for field in ("win_levels", "available_actions"):
                if record.get(field) is not None:
                    response[field] = record[field]
            response = response or None

            body.append({
                "event": "env_step", "run_id": run_id, "ts": ts,
                "arm": state["arm"] or "bare_cc",
                "payload": {
                    "game_id": record.get("game_id"),
                    "card_id": record.get("card_id"),
                    "guid": record.get("guid"),
                    "step_idx": state["step_idx"],
                    "action": _action(record.get("action")),
                    "frames": frames,
                    "n_frames": n_frames,
                    "frame_hash": frame_hash(frames),
                    "state": record.get("state"),
                    "score": None,          # the live API returns no score field
                    "levels_completed": record.get("levels_completed"),
                    "level": before,
                    "level_boundary": after > before,
                    "variant": None,
                    "guard": {"decision": "allow"},
                    "response": response,
                    "http": http,
                }})
            continue

        if is_v0_model(record):
            state["call_idx"] += 1
            state["model_calls"] += 1
            state["model"] = record.get("model") or state["model"]
            state["game_id"] = record.get("game_id") or state["game_id"]
            cost = record.get("total_cost_usd")
            if isinstance(cost, (int, float)) and not isinstance(cost, bool):
                state["cost_v0"] += float(cost)

            http = {"method": "POST", "path": None,
                    "status": None if record.get("is_error") else 200,
                    "attempts": record.get("attempt", 1),
                    "elapsed_ms": record.get("duration_ms"),
                    "stream": None}
            if record.get("is_error"):
                http["error"] = True
            if record.get("prompt_chars") is not None:
                http["request_chars"] = record["prompt_chars"]

            body.append({
                "event": "model_call", "run_id": run_id, "ts": ts,
                "arm": state["arm"] or arm_override or "bare_cc",
                "payload": {
                    "call_idx": state["call_idx"],
                    "provider": record.get("provider"),
                    "model": record.get("model"),
                    # v0 recorded neither. §4 says the full text is what stands
                    # in for a model call being unreplayable, so this is a hole
                    # in the record, not a lossy conversion.
                    "request": None,
                    "response": None,
                    "usage": dict(record.get("usage") or {}),
                    "pricing_ref": None,
                    "step_idx": record.get("step_idx"),
                    # fall back to the run's game: one run is one game, and a
                    # model_call without one is the gap the battery raised
                    "game_id": record.get("game_id") or state["game_id"],
                    "http": http,
                }})
            continue

        raise UnknownDialect(
            "a v0 record that is neither an env step nor a model call: %r"
            % (sorted(record),))

    # -- the synthesised run_start / run_end pair per run -------------------
    out: List[Dict[str, Any]] = []
    for run_id, state in runs.items():
        out.append({
            "event": "run_start", "run_id": run_id,
            "ts": state["first_ts"] or "1970-01-01T00:00:00.000Z",
            "arm": state["arm"] or arm_override or "bare_cc",
            "payload": {
                "game_id": state["game_id"],
                "model": state["model"],
                "lifted": {
                    "lifted_from": SOURCE_DIALECT,
                    "source": source,
                    "source_sha256": source_sha256,
                    "migrator": MIGRATOR,
                    "migrator_version": MIGRATOR_VERSION,
                    "records": {"env_step": state["steps"],
                                "model_call": state["model_calls"]},
                    "dropped": {
                        "total_cost_usd_v0": round(state["cost_v0"], 7),
                        "_note": "the v0 harness's own arithmetic, kept here so "
                                 "the number is not lost. It is NOT canon: §5 "
                                 "rules cost derived, and recomputing it needs a "
                                 "pricing_ref v0 never wrote.",
                    },
                    "holes": ["model_call.request", "model_call.response",
                              "env_step.card_id", "env_step.guid",
                              "http.elapsed_ms on env steps"],
                },
            }})

    out.extend(body)

    for run_id, state in runs.items():
        card = scorecards.get(run_id)
        out.append({
            "event": "run_end", "run_id": run_id,
            "ts": state["last_ts"] or "1970-01-01T00:00:00.000Z",
            "arm": state["arm"] or arm_override or "bare_cc",
            "payload": {
                "outcome": "lifted",
                "steps": state["steps"],
                "model_calls": state["model_calls"],
                "levels_completed": state["levels"],
                "scorecard": card,
                "_note": "synthesised by the migrator. v0 had no run_end; "
                         "`outcome` says 'lifted' rather than inventing one."
                         + ("" if card else " No scorecard was found for this "
                            "run, so its score cannot be reconciled -- which "
                            "the frozen scorer reports as UNDETERMINED, not "
                            "PASS."),
            }})

    # -- serialise: envelope, canon check, redaction, dense seq -------------
    #
    # This does not go through `Ledger.append`, and the reason is narrow: that
    # writer stamps `ts` with the current time, and a migration must preserve
    # when things happened. Everything else it does -- the canon check, the
    # redaction, the canonical spelling -- is done here explicitly.
    final: List[Dict[str, Any]] = []
    for seq, entry in enumerate(out, 1):
        payload = VAULT.scrub(entry["payload"])
        check(entry["event"], payload)
        record = {"v": LEDGER_VERSION, "event": entry["event"],
                  "run_id": entry["run_id"], "arm": entry["arm"]}
        record.update(payload)
        record["seq"] = seq
        record["ts"] = entry["ts"]
        final.append(record)
    return final


def upgrade_file(path: str, out_path: str, *,
                 arm_override: Optional[str] = None,
                 scorecard_path: Optional[str] = None) -> Dict[str, Any]:
    records = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    cards = scorecards_by_run(scorecard_path) if scorecard_path else {}
    lifted = lift(records, source=path, source_sha256=sha256_file(path),
                  arm_override=arm_override, scorecards=cards)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as fh:
        for record in lifted:
            fh.write(canonical(record))
            fh.write("\n")

    runs = sorted({r["run_id"] for r in lifted})
    return {
        "source": path, "source_sha256": sha256_file(path),
        "out": out_path, "out_sha256": sha256_file(out_path),
        "records_in": len(records), "records_out": len(lifted),
        "runs": len(runs),
        "runs_with_scorecard": sum(1 for r in runs if r in cards),
        "migrator": MIGRATOR, "migrator_version": MIGRATOR_VERSION,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("path")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--arm", default=None,
                    help="arm to use when a v0 record does not name one")
    ap.add_argument("--scorecards", default=None,
                    help="a v0 probe log; closed scorecards found in it are "
                         "attached to the synthesised run_end records")
    args = ap.parse_args(argv)

    report = upgrade_file(args.path, args.out, arm_override=args.arm,
                          scorecard_path=args.scorecards)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
