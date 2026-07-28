"""Lift the baseline-arms v0 ledger into canonical LEDGER_FORMAT v1.0.

Monitor finding F-16 ruled `proxy/LEDGER_FORMAT.md` the canonical spelling and
this track's existing ledger the one that has to move. Section 7 of that
document already anticipated the lift and named the two spellings that differ
(`frame` -> `frames`, `timestamp` -> `ts`), and describes `upgrade_ledger.py` in
the present tense -- but `proxy/tools/` does not exist, so the tool it names has
never been written. This is that lift, on the baseline-arms side, for the
baseline-arms ledger only.

**Originals are not touched.** This reads `ledger.jsonl` and writes new files
elsewhere. An append-only record that a migrator rewrote in place would no
longer be one. The source hash is taken before the read and re-checked after,
and a source that moved underneath the migration aborts it.

The rule the whole module follows: **prefer a recorded gap to a plausible
value.** Every field says which of four grades it came from, and every record
carries its own `lift` block saying so:

  * *carried*    -- the v0 record held it, possibly under another name.
  * *derived*    -- computable from the v0 record (`n_frames`, `frame_hash`,
                    `http.path`), or from the run's own record sequence (`level`).
  * *joined*     -- from another file this track wrote, on a key that is unique
                    (`card_id` and `arm` by run_id; `guid` by card_id). Recorded
                    with its source, because a join is weaker than a field.
  * *unfillable* -- null, and listed in the report with the reason.

Nothing is dropped silently. Any v0 key with no canonical home is copied whole
into `lift_unmapped`, and the fuzz suite asserts that every key of every input
record is either mapped or present there. The one exception is the dollar
figure: `LEDGER_FORMAT.md` section 5 forbids a cost field anywhere in a
`model_call`, and `proxy/ledger.py` raises on one, so `total_cost_usd` goes to a
sidecar file keyed by `seq` rather than travelling inside the record. Its key
name is listed in `lift_dropped_to_sidecar` so the omission is visible from the
record itself.

    python -m harness.migrate_ledger                 # -> runs/_migrations/...
    python -m harness.migrate_ledger --report-only
"""

import argparse
import hashlib
import json
import os
import re
import sys
from typing import Any, Dict, Iterable, List, Optional, Tuple

from . import arc_client, ledger

MIGRATOR_VERSION = "baseline-arms/migrate_ledger/1.1.0"
TARGET_FORMAT = "1.0"
LIFT_TAG = "baseline-arms/v0"                     # LEDGER_FORMAT.md section 7

TRACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(TRACK)
DEFAULT_SOURCE = os.path.join(TRACK, "ledger.jsonl")
DEFAULT_PROBE = os.path.join(TRACK, "probe_log.jsonl")
MIGRATIONS_DIR = os.path.join(TRACK, "runs", "_migrations")

# LEDGER_FORMAT.md section 1, and `proxy/ledger.py::canonical` verbatim. All four
# settings are load-bearing: sort_keys applies recursively, and the tight
# separators are what make a line byte-determined by its content. The v0 writer
# used json.dumps' *default* separators (", " / ": "), so no v0 line can be
# copied through even when every field maps -- every line is re-serialised here.
CANON = {"sort_keys": True, "ensure_ascii": True, "separators": (",", ":")}

# `proxy/ledger.py` accepts only these on the envelope.
CANON_EVENTS = ("env_step", "model_call", "run_start", "run_end", "env_meta",
                "guard_block", "incident")

# The command path the canonical guard recognises. ACTION0 is outside it; 46 v0
# records have action.id == 0 because the arm's regex accepts any integer and
# the model occasionally emitted one. They are kept and flagged -- the record is
# of what crossed the wire, not of what should have.
CANON_ACTION_PATH = re.compile(r"^/api/cmd/(RESET|ACTION([1-9][0-9]?))$")

COST_KEYS = ("total_cost_usd",)


class MigrationError(RuntimeError):
    """Aborts the migration. Never downgraded to a warning."""


def canonical(obj: Any) -> str:
    return json.dumps(obj, **CANON)


def sha256_of(obj: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical(obj).encode("utf-8")).hexdigest()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return "sha256:" + h.hexdigest()


# --------------------------------------------------- what v0 records look like
V0_ENV_STEP_KEYS = {"game_id", "run_id", "arm", "action", "frame", "step_idx",
                    "timestamp"}
V0_MODEL_CALL_KEYS = {"run_id", "provider", "model", "usage", "timestamp"}

_ENV_STEP_CONSUMED = {"game_id", "run_id", "arm", "action", "frame", "step_idx",
                      "timestamp", "state", "levels_completed", "http_status",
                      "http_tries", "failed"}
_MODEL_CALL_CONSUMED = {"run_id", "provider", "model", "usage", "timestamp",
                        "step_idx", "duration_ms", "attempt"}


def classify(record: Dict[str, Any]) -> str:
    if V0_ENV_STEP_KEYS <= set(record):
        return "env_step"
    if V0_MODEL_CALL_KEYS <= set(record):
        return "model_call"
    return "unknown"


def canonical_ts(v0_timestamp: Any) -> Optional[str]:
    """Second-resolution v0 stamp -> the millisecond form the canon requires.

    `LEDGER_FORMAT.md` section 2 specifies millisecond precision. v0 wrote whole
    seconds (`time.strftime`, no sub-second field). Rendering `.000` conforms to
    the required shape without claiming a measurement: every record also carries
    `lift.ts_precision: "second"` and the source string verbatim, so a reader
    cannot mistake the zeros for observed milliseconds.
    """
    if not isinstance(v0_timestamp, str) or len(v0_timestamp) != 20:
        return v0_timestamp if isinstance(v0_timestamp, str) else None
    return v0_timestamp[:19] + ".000Z"


# ---------------------------------------------------------------- side tables
def run_side_table(paths: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
    """`run_id` -> facts the ledger did not record but the run summary did.

    Only run-level properties are taken from here: `card_id`, `arm`, and
    `reset_attempts` (there is exactly one RESET per run, so it is that RESET's
    attempt count and nothing else). Anything that varies per step is not
    joinable this way and stays unfillable rather than approximated.
    """
    if paths is None:
        out_dir = os.path.join(TRACK, "out")
        paths = []
        if os.path.isdir(out_dir):
            paths = [os.path.join(out_dir, n) for n in sorted(os.listdir(out_dir))
                     if n.startswith("pilot_") and n.endswith(".json")]
            cells = os.path.join(out_dir, "campaign_cells.jsonl")
            if os.path.exists(cells):
                paths.append(cells)

    out: Dict[str, Dict[str, Any]] = {}
    for path in paths:
        if not os.path.exists(path):
            continue
        summaries: List[Dict[str, Any]] = []
        if path.endswith(".jsonl"):
            for line in open(path, encoding="utf-8"):
                line = line.strip()
                if line:
                    summaries.append(json.loads(line))
        else:
            with open(path, encoding="utf-8") as fh:
                loaded = json.load(fh)
            summaries = loaded if isinstance(loaded, list) else [loaded]
        for s in summaries:
            rid = s.get("run_id")
            if rid:
                out.setdefault(rid, {
                    "card_id": s.get("card_id"),
                    "arm": s.get("arm"),
                    "reset_attempts": s.get("reset_attempts"),
                    "source": os.path.relpath(path, REPO).replace(os.sep, "/"),
                })
    return out


def guid_by_card(probe_path: str = DEFAULT_PROBE) -> Dict[str, Dict[str, Any]]:
    """`card_id` -> the session guid(s) seen against that card.

    The probe log holds every request body, and a gameplay body is
    `{game_id, card_id, guid}`. `card_id` is unique per run -- `bare_cc` opens
    one scorecard per episode -- so this join is sound where a join on
    `(game_id, model, step_idx)` would be three-way ambiguous under the
    concurrent repeats. Where a card shows more than one guid the field stays
    null and the set is reported: `bare_cc` does re-read `guid` from each
    response, so more than one is possible and guessing which step had which is
    not.
    """
    seen: Dict[str, set] = {}
    if not os.path.exists(probe_path):
        return {}
    with open(probe_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            body = rec.get("request_body")
            if not isinstance(body, dict):
                continue
            card, guid = body.get("card_id"), body.get("guid")
            if card and guid:
                seen.setdefault(card, set()).add(guid)
    return {card: {"guid": (list(guids)[0] if len(guids) == 1 else None),
                   "candidates": sorted(guids)}
            for card, guids in seen.items()}


# --------------------------------------------------------------------- lifting
def _action_of(raw: Any) -> Tuple[Dict[str, Any], Optional[str], Optional[str]]:
    """(canonical action object, http path, the raw form when it was neither)."""
    if raw == "RESET":
        return {"name": "RESET", "id": None, "data": None}, "/api/cmd/RESET", None
    if isinstance(raw, dict) and raw.get("id") is not None:
        aid = raw["id"]
        return ({"name": "ACTION%d" % aid, "id": aid, "data": raw.get("data")},
                "/api/cmd/ACTION%d" % aid, None)
    # The arm ended the step without sending anything: "gave up",
    # "unparseable: ...". The canonical vocabulary has no name for that, so the
    # slot is null and the original text is kept verbatim beside it.
    return ({"name": None, "id": None, "data": None}, None,
            raw if isinstance(raw, str) else canonical(raw))


ENV_STEP_GAPS = {
    "guid": "RESET's session id was never written to the v0 ledger. It is "
            "recoverable from probe_log.jsonl request bodies via card_id where "
            "exactly one guid was used for that card; otherwise null.",
    "score": "the upstream response has no score field at all -- v0 recorded "
             "levels_completed, which is what the API returns.",
    "http.elapsed_ms": "per-call timing is in probe_log.jsonl, which carries no "
                       "run_id; under concurrent repeats of one cell the "
                       "step-level join is ambiguous.",
    "http.request_sha256": "the request body was never written to the ledger. "
                           "Hashing a reconstruction would produce a digest of "
                           "something that did not cross the wire.",
}

MODEL_CALL_GAPS = {
    "request": "v0 recorded prompt_chars, not the prompt. LEDGER_FORMAT.md "
               "makes the verbatim body the substitute for replay on the model "
               "side, so every lifted model_call is permanently non-replayable. "
               "This gap cannot be closed retroactively -- only by the proxy, "
               "for future runs.",
    "response": "v0 recorded is_error and usage, nothing of the body.",
    "pricing_ref": "no price table existed in v0; the Claude Code CLI reported "
                   "a dollar figure directly and did not name its table. The "
                   "canonical null means 'the table failed to load', which is "
                   "adjacent to but not the same as 'there was none'.",
    "http.method/path/status/request_sha256": "this arm reaches the model by "
        "running the `claude -p` CLI as a subprocess. There was no HTTP request, "
        "so there is no method, path or status. Mapping is_error to 500 would "
        "invent a status line that never existed.",
    "http.stream": "whether the CLI streamed upstream is not observable from "
                   "anything v0 wrote.",
}


def lift_env_step(rec: Dict[str, Any], seq: int, src: Dict[str, Any],
                  state: Dict[str, Any], side: Dict[str, Any],
                  guid_info: Dict[str, Any]) -> Dict[str, Any]:
    action, path, raw_action = _action_of(rec.get("action"))
    frames = rec.get("frame")
    frames_ok = isinstance(frames, list)
    failed = bool(rec.get("failed"))
    is_reset = action["name"] == "RESET"

    # `level` follows the reconciliation rule proxy/reconcile.py re-checks:
    # carry the previous value when this record has no levels_completed (failed
    # steps have none), and mark a boundary only where it actually increased.
    raw_levels = rec.get("levels_completed")
    levels = raw_levels if isinstance(raw_levels, int) else state.get("level")
    boundary = (isinstance(raw_levels, int) and state.get("level") is not None
                and raw_levels > state["level"])
    state["level"] = levels

    # bare_cc writes a non-failed env_step only after the response was 200, and a
    # failed one only after recording the status it got, so the status here is
    # entailed by which branch wrote the record rather than guessed.
    status = rec.get("http_status") if failed else 200

    if is_reset:
        attempts = side.get("reset_attempts")
        attempts_grade = ("joined:%s" % side["source"] if attempts
                          else "unfillable")
    else:
        attempts = rec.get("http_tries")
        attempts_grade = "carried" if attempts else "unfillable"

    card_id = side.get("card_id")
    guid = guid_info.get("guid") if card_id else None

    gaps = {k: v for k, v in ENV_STEP_GAPS.items()}
    if guid:
        gaps.pop("guid")
    if not frames_ok:
        gaps["frames/frame_hash"] = ("this record is a refusal or an arm-side "
                                     "stop; v0 wrote frame=null (D-006) and "
                                     "there is nothing to hash.")
    if not card_id:
        gaps["card_id"] = "no run summary carries this run_id."

    out: Dict[str, Any] = {
        "v": TARGET_FORMAT,
        "event": "env_step",
        "seq": seq,
        "ts": canonical_ts(rec.get("timestamp")),
        "run_id": rec.get("run_id"),
        "arm": rec.get("arm"),
        "game_id": rec.get("game_id"),
        "card_id": card_id,
        "guid": guid,
        "step_idx": rec.get("step_idx"),
        "action": action,
        "frames": frames if frames_ok else None,
        "frame_hash": sha256_of(frames) if frames_ok else None,
        "n_frames": len(frames) if frames_ok else 0,
        "state": rec.get("state"),
        "score": None,
        "levels_completed": raw_levels if isinstance(raw_levels, int) else None,
        "level": levels,
        "level_boundary": bool(boundary),
        "variant": None,
        "guard": {"decision": "allow"},
        "http": {
            "method": "POST" if path else None,
            "path": path,
            "status": status,
            "elapsed_ms": None,
            "request_sha256": None,
            "attempts": attempts,
        },
        "lifted_from": LIFT_TAG,
        "lift": {
            "migrator": MIGRATOR_VERSION,
            "src": src,
            "ts_precision": "second",
            "ts_source": rec.get("timestamp"),
            "card_id": "joined:%s" % side["source"] if card_id else "unfillable",
            "guid": ("joined:probe_log.jsonl via card_id" if guid else
                     "unfillable"),
            "guard": "inferred: the record exists, so assert_playable() let it "
                     "through -- a v0 refusal raised before any write, so it "
                     "would leave no record at all",
            "http_status": "carried" if failed else
                           "entailed: written only after a 200",
            "http_attempts": attempts_grade,
            "level": "derived: carry-forward over the run's levels_completed "
                     "sequence, matching proxy/reconcile.py",
            "unfillable": _gap_list(gaps),
        },
        "lift_unmapped": {},
        "lift_dropped_to_sidecar": [],
    }

    if guid_info.get("candidates") and len(guid_info["candidates"]) > 1:
        out["lift"]["guid_candidates"] = guid_info["candidates"]
    if raw_action is not None:
        out["lift"]["action_raw"] = raw_action
    if path and not CANON_ACTION_PATH.match(path):
        out["lift"]["nonconforming_action"] = (
            "%s is outside the canonical command vocabulary "
            "(RESET | ACTION1..ACTION99). The arm's parser accepts any integer "
            "and the model emitted this one; the request was really made, so "
            "the record is kept and flagged rather than dropped or renamed."
            % path)
    if frames_ok and rec.get("frames_returned") not in (None, len(frames)):
        out["lift"]["frames_returned_mismatch"] = (
            "v0 recorded frames_returned=%r but the frame list has %d entries"
            % (rec.get("frames_returned"), len(frames)))

    for key, value in rec.items():
        if key not in _ENV_STEP_CONSUMED:
            out["lift_unmapped"][key] = value
    return out


def lift_model_call(rec: Dict[str, Any], seq: int, call_idx: int,
                    src: Dict[str, Any], side: Dict[str, Any],
                    arm_from_ledger: Optional[str]) -> Tuple[Dict[str, Any],
                                                             Optional[Dict[str, Any]]]:
    """Returns (record, sidecar row). The sidecar carries the dollar figure."""
    arm = arm_from_ledger or side.get("arm")
    arm_grade = ("derived: the env_step records of this run_id carry it"
                 if arm_from_ledger else
                 ("joined:%s" % side["source"] if side.get("arm") else "unfillable"))

    gaps = dict(MODEL_CALL_GAPS)
    if not arm:
        gaps["arm"] = "no env_step and no run summary carries this run_id."

    out: Dict[str, Any] = {
        "v": TARGET_FORMAT,
        "event": "model_call",
        "seq": seq,
        "ts": canonical_ts(rec.get("timestamp")),
        "run_id": rec.get("run_id"),
        "arm": arm,
        "call_idx": call_idx,
        "provider": rec.get("provider"),
        "model": rec.get("model"),
        "request": None,
        "response": None,
        "usage": dict(rec.get("usage") or {}),
        "pricing_ref": None,
        "step_idx": rec.get("step_idx"),
        "http": {
            "method": None,
            "path": None,
            "status": None,
            "elapsed_ms": rec.get("duration_ms"),
            "stream": None,
            "attempts": rec.get("attempt") or 1,
        },
        "lifted_from": LIFT_TAG,
        "lift": {
            "migrator": MIGRATOR_VERSION,
            "src": src,
            "ts_precision": "second",
            "ts_source": rec.get("timestamp"),
            "arm": arm_grade,
            "transport": "subprocess (`claude -p` CLI), not HTTP -- the whole "
                         "http block is partial by nature here, not by loss",
            "unfillable": _gap_list(gaps),
        },
        "lift_unmapped": {},
        "lift_dropped_to_sidecar": [],
    }

    if "attempt" not in rec:
        # 160 records predate the retry counter. Defaulting silently would make
        # an assumption indistinguishable from an observation.
        out["lift"]["attempts_defaulted"] = (
            "this record predates the `attempt` key (added with the model-call "
            "retry); attempts=1 is the default, not an observation")

    sidecar = None
    for key in COST_KEYS:
        if key in rec:
            sidecar = sidecar or {"seq": seq, "run_id": rec.get("run_id"),
                                  "step_idx": rec.get("step_idx"),
                                  "source": src}
            sidecar[key] = rec[key]
            out["lift_dropped_to_sidecar"].append(key)
    if sidecar:
        out["lift"]["cost"] = (
            "total_cost_usd is in costs.sidecar.jsonl keyed by seq. "
            "LEDGER_FORMAT.md section 5 forbids a dollar figure anywhere in a "
            "model_call -- cost is derived later from usage and a named price "
            "table -- and proxy/ledger.py raises on one. Deleting the figure "
            "would lose the only per-call cost this track has, so it is moved "
            "out of the record rather than out of existence.")

    for key, value in rec.items():
        if key not in _MODEL_CALL_CONSUMED and key not in COST_KEYS:
            out["lift_unmapped"][key] = value
    return out, sidecar


def _gap_list(gaps: Dict[str, str]) -> List[str]:
    return ["%s: %s" % (k, v) for k, v in sorted(gaps.items())]


# ----------------------------------------------------------------- the migrator
def arm_by_run(records: Iterable[Dict[str, Any]]) -> Dict[str, str]:
    """`run_id` -> arm, from the run's own env_step records.

    Stronger than the run-summary join: it is the same file, written by the same
    call, for the same run. v0 put `arm` on env_step and not on model_call.
    """
    out: Dict[str, str] = {}
    for rec in records:
        rid, arm = rec.get("run_id"), rec.get("arm")
        if rid and arm and rid not in out:
            out[rid] = arm
    return out


def assert_dev_pile(records: Iterable[Dict[str, Any]]) -> None:
    """Fail closed on a sealed game id. Never a warning.

    G7's discipline applied to the migration: a sealed id in the input would
    mean the guard failed at run time, and copying it into a new file would
    spread it. Cheaper to refuse the whole migration.
    """
    dev = {g.split("-")[0] for g in arc_client.dev_pile()}
    for rec in records:
        gid = rec.get("game_id")
        if gid and gid.split("-")[0] not in dev:
            raise MigrationError(
                "record names %r, which is not in the development pile. The "
                "migration stops here: see run_campaign.py G7." % gid)


def migrate(records: List[Dict[str, Any]],
            source_label: str = "ledger.jsonl",
            side_table: Optional[Dict[str, Dict[str, Any]]] = None,
            guid_table: Optional[Dict[str, Dict[str, Any]]] = None,
            ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """Returns (lifted records, cost sidecar rows, report).

    `seq` is assigned in **file order**, not by sorting on `timestamp`. The v0
    writer appended under a lock, so file order is the true happens-before;
    `timestamp` has one-second precision and hundreds of records share a second,
    so sorting on it would invent an order the data does not have. Canonical
    `seq` is defined as monotonic within the file, which file order satisfies
    and a timestamp sort would not improve on.
    """
    assert_dev_pile(records)
    side_table = run_side_table() if side_table is None else side_table
    guid_table = guid_by_card() if guid_table is None else guid_table
    arms = arm_by_run(records)

    lifted: List[Dict[str, Any]] = []
    sidecar: List[Dict[str, Any]] = []
    report: Dict[str, Any] = {
        "migrator": MIGRATOR_VERSION,
        "target_format": TARGET_FORMAT,
        "counts": {"env_step": 0, "model_call": 0, "unknown": 0},
        "runs": {},
        "unmapped_keys": {},
        "unfillable_fields": {},
        "grades": {"joined_card_id": 0, "joined_guid": 0, "joined_arm": 0,
                   "attempts_defaulted": 0, "nonconforming_action": 0},
        "warnings": [],
    }

    per_run_level: Dict[str, Dict[str, Any]] = {}
    per_run_calls: Dict[str, int] = {}

    for line_no, rec in enumerate(records, start=1):
        seq = line_no                       # dense, 1-based, == the source line
        src = {"path": source_label, "line": line_no}
        kind = classify(rec)
        report["counts"][kind] = report["counts"].get(kind, 0) + 1
        rid = rec.get("run_id") or "<no run_id>"
        side = side_table.get(rid, {})

        if kind == "env_step":
            state = per_run_level.setdefault(rid, {})
            guid_info = guid_table.get(side.get("card_id") or "", {})
            out = lift_env_step(rec, seq, src, state, side, guid_info)
            if out["card_id"]:
                report["grades"]["joined_card_id"] += 1
            if out["guid"]:
                report["grades"]["joined_guid"] += 1
            if "nonconforming_action" in out["lift"]:
                report["grades"]["nonconforming_action"] += 1
        elif kind == "model_call":
            idx = per_run_calls.get(rid, 0)          # 0-based, as proxy does it
            per_run_calls[rid] = idx + 1
            out, row = lift_model_call(rec, seq, idx, src, side, arms.get(rid))
            if row:
                sidecar.append(row)
            if out["arm"]:
                report["grades"]["joined_arm"] += 1
            if "attempts_defaulted" in out["lift"]:
                report["grades"]["attempts_defaulted"] += 1
        else:
            # An unrecognised shape is carried through whole, marked and counted.
            # Refusing it would lose it; guessing its meaning would be worse.
            out = {"v": TARGET_FORMAT, "event": "unknown", "seq": seq,
                   "ts": canonical_ts(rec.get("timestamp")),
                   "run_id": rec.get("run_id"), "arm": side.get("arm"),
                   "lifted_from": LIFT_TAG,
                   "lift": {"migrator": MIGRATOR_VERSION, "src": src,
                            "unfillable": ["every canonical field: this v0 "
                                           "record matches no known shape"]},
                   "lift_unmapped": dict(rec),
                   "lift_dropped_to_sidecar": []}
            report["warnings"].append(
                "line %d matches no known v0 shape; carried through as "
                "event=unknown with every key preserved" % line_no)

        lifted.append(out)
        bucket = report["runs"].setdefault(rid, {"env_step": 0, "model_call": 0,
                                                 "unknown": 0})
        bucket[kind] = bucket.get(kind, 0) + 1
        for key in out.get("lift_unmapped") or {}:
            report["unmapped_keys"][key] = report["unmapped_keys"].get(key, 0) + 1
        for gap in (out.get("lift") or {}).get("unfillable") or []:
            head = gap.split(":")[0]
            report["unfillable_fields"][head] = \
                report["unfillable_fields"].get(head, 0) + 1

    report["records"] = len(lifted)
    report["runs_seen"] = len(report["runs"])
    report["side_table_misses"] = sorted(r for r in report["runs"]
                                         if r not in side_table)
    report["cost_rows"] = len(sidecar)
    return lifted, sidecar, report


def read_v0(path: str) -> List[Dict[str, Any]]:
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def write_jsonl(rows: Iterable[Dict[str, Any]], path: str) -> Dict[str, Any]:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    digest = hashlib.sha256()
    count = 0
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            line = canonical(row) + "\n"
            fh.write(line)
            digest.update(line.encode("utf-8"))
            count += 1
    return {"path": os.path.relpath(path, REPO).replace(os.sep, "/"),
            "records": count, "bytes": os.path.getsize(path),
            "sha256": "sha256:" + digest.hexdigest()}


def run(source: str = DEFAULT_SOURCE, out_dir: Optional[str] = None,
        probe_path: str = DEFAULT_PROBE) -> Dict[str, Any]:
    out_dir = out_dir or os.path.join(MIGRATIONS_DIR,
                                      "ledger-v0-to-v%s" % TARGET_FORMAT)
    # The source must not move underneath the migration. The S1 campaign writes
    # to out/shards/, not here, but "should not be writing" is not a check.
    before = sha256_file(source)
    records = read_v0(source)
    if sha256_file(source) != before:
        raise MigrationError(
            "%s changed while it was being read. A migration of a moving "
            "append-only file records a hash that is true of nothing; snapshot "
            "it first." % source)

    label = os.path.relpath(source, REPO).replace(os.sep, "/")
    lifted, sidecar, report = migrate(records, source_label=label,
                                      guid_table=guid_by_card(probe_path))

    report["output"] = write_jsonl(lifted, os.path.join(out_dir,
                                                        "ledger.canon.jsonl"))
    report["sidecar"] = write_jsonl(sidecar, os.path.join(out_dir,
                                                          "costs.sidecar.jsonl"))
    report["source"] = {"path": label, "bytes": os.path.getsize(source),
                        "sha256": before, "records": len(records)}
    report["joins"] = {
        "run_summaries": sorted({v["source"] for v in run_side_table().values()}),
        "probe_log": os.path.relpath(probe_path, REPO).replace(os.sep, "/")
                     if os.path.exists(probe_path) else None,
    }
    report["generated_at"] = ledger.utcnow()
    with open(os.path.join(out_dir, "report.json"), "w", encoding="utf-8",
              newline="\n") as fh:
        fh.write(json.dumps(report, indent=2, sort_keys=True,
                            ensure_ascii=True) + "\n")
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=DEFAULT_SOURCE)
    ap.add_argument("--probe", default=DEFAULT_PROBE)
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args(argv)

    if args.report_only:
        _, _, report = migrate(read_v0(args.source),
                               guid_table=guid_by_card(args.probe))
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    report = run(args.source, args.out_dir, args.probe)
    print("migrated %d records %s" % (report["records"], report["counts"]))
    print("  runs %d | summary-join misses %d"
          % (report["runs_seen"], len(report["side_table_misses"])))
    print("  joins: card_id %d | guid %d | arm %d"
          % (report["grades"]["joined_card_id"], report["grades"]["joined_guid"],
             report["grades"]["joined_arm"]))
    print("  flagged: attempts defaulted %d | non-canonical action names %d"
          % (report["grades"]["attempts_defaulted"],
             report["grades"]["nonconforming_action"]))
    print("  v0 keys parked in lift_unmapped: %s" % report["unmapped_keys"])
    print("  -> %s  %s" % (report["output"]["path"], report["output"]["sha256"]))
    print("  -> %s  %d cost rows"
          % (report["sidecar"]["path"], report["sidecar"]["records"]))
    for w in report["warnings"][:5]:
        print("  WARNING: %s" % w)
    return 0


if __name__ == "__main__":
    sys.exit(main())
