"""Check a v1.0 ledger against LEDGER_FORMAT.md, because nothing else does.

`LEDGER_FORMAT.md` section 1 says "`proxy/tools/validate_ledger.py` will check
any stream against it", in the present tense. That file does not exist -- there
is no `proxy/tools/` directory at all -- and `proxy/ledger.py` enforces only
three enum memberships at write time (`event`, `arm`, incident `kind`),
accepting any set of fields silently. So the format has been normative and
unchecked at the same time, and F-16's migration would have shipped an output
nobody could test for conformance.

This is a reader-side checker for the invariants the format actually states. It
is deliberately in `baseline-arms/`: the canonical implementation belongs to
the proxy track and this track may not write there. If proxy later ships its
own, that one wins and this becomes a second opinion -- which for a format two
tracks must agree on is not a bad thing to have.

What it checks, and what it deliberately does not:

  * **Byte form.** A line must equal `canonical(json.loads(line))` exactly:
    sorted keys at every depth, `ensure_ascii`, no space after separators, LF.
    This is the invariant the whole format exists for -- two writers cannot
    produce different bytes for the same content -- and it is the one most
    easily lost by a migrator that copies a line through.
  * **Envelope.** `v`, `event`, `seq`, `ts`, `run_id`, `arm`, with `seq` dense
    from 1 and `ts` non-decreasing in `seq` order.
  * **Per-event required fields**, from the section 3 and 4 tables.
  * **Derived-field consistency**: `n_frames` against `frames`, `frame_hash`
    against a recomputation, `level`/`level_boundary` against the carry-forward
    rule `proxy/reconcile.py` re-checks.
  * **The prohibitions**: no dollar figure in a `model_call`, no credential
    header anywhere, no sealed-pile game id anywhere.

It does *not* check that a null field ought to have had a value. A lifted
record is full of honest nulls (LEDGER_FORMAT section 7 blesses partial lifts),
and a validator that treated those as errors would be checking provenance, not
conformance. `--strict` additionally requires every field to be non-null, which
is the right setting for a stream a live proxy wrote and the wrong one for a lift.

    python -m harness.validate_canon runs/_migrations/ledger-v0-to-v1.0/ledger.canon.jsonl
"""

import argparse
import hashlib
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional

from . import arc_client

CANON = {"sort_keys": True, "ensure_ascii": True, "separators": (",", ":")}
FORMAT_VERSION = "1.0"

EVENTS = ("env_step", "model_call", "run_start", "run_end", "env_meta",
          "guard_block", "incident")
ARMS = ("bare_cc", "schema_repro", "theoria", "probe", "replay", "mock_arm")

ENVELOPE = ("v", "event", "seq", "ts", "run_id", "arm")

REQUIRED = {
    "env_step": ("game_id", "card_id", "guid", "step_idx", "action", "frames",
                 "frame_hash", "n_frames", "state", "score", "levels_completed",
                 "level", "level_boundary", "variant", "guard", "http"),
    "model_call": ("provider", "model", "request", "response", "usage",
                   "pricing_ref", "call_idx", "step_idx", "http"),
}

TS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")
HASH = re.compile(r"^sha256:[0-9a-f]{64}$")

# LEDGER_FORMAT section 5 and proxy/ledger.py: cost is derived from usage and a
# named price table, never recorded. proxy's own guard rejects the literal keys
# `cost` and `cost_usd` only, which `total_cost_usd` slips past -- so this
# checks for the substring instead.
COST_SUBSTRING = "cost"

CREDENTIAL_KEYS = ("authorization", "x-api-key", "x_api_key", "api_key")


def canonical(obj: Any) -> str:
    return json.dumps(obj, **CANON)


def sha256_of(obj: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical(obj).encode("utf-8")).hexdigest()


def _keys_recursive(obj: Any):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _keys_recursive(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _keys_recursive(v)


def validate_line(raw: str, line_no: int, strict: bool) -> List[str]:
    problems = []

    def bad(msg):
        problems.append("line %d: %s" % (line_no, msg))

    if raw.endswith("\r\n") or "\r" in raw:
        bad("carriage return in the line; the format is LF-terminated")
    body = raw.rstrip("\n")
    if not raw.endswith("\n"):
        bad("line is not newline-terminated")
    if not body.isascii():
        bad("non-ASCII byte; the format is ensure_ascii")

    try:
        rec = json.loads(body)
    except json.JSONDecodeError as exc:
        bad("not JSON: %s" % exc)
        return problems
    if not isinstance(rec, dict):
        bad("top level is %s, not an object" % type(rec).__name__)
        return problems
    if body != canonical(rec):
        bad("not byte-canonical: keys unsorted, or separators/spacing differ "
            "from json.dumps(sort_keys=True, ensure_ascii=True, "
            "separators=(',',':'))")

    for field in ENVELOPE:
        if field not in rec:
            bad("missing envelope field %r" % field)
    if rec.get("v") != FORMAT_VERSION:
        bad("v is %r, not %r -- a reader must reject an unknown version rather "
            "than guess (section 8)" % (rec.get("v"), FORMAT_VERSION))
    event = rec.get("event")
    if event not in EVENTS:
        bad("event %r is not one of %s" % (event, ", ".join(EVENTS)))
    if not isinstance(rec.get("seq"), int) or isinstance(rec.get("seq"), bool):
        bad("seq is %r, not an int" % (rec.get("seq"),))
    if rec.get("arm") is not None and rec["arm"] not in ARMS:
        bad("arm %r is not one of %s" % (rec["arm"], ", ".join(ARMS)))
    if strict and rec.get("arm") is None:
        bad("arm is null")
    ts = rec.get("ts")
    if not isinstance(ts, str) or not TS.match(ts):
        bad("ts %r is not ISO-8601 UTC at millisecond precision" % (ts,))

    for field in REQUIRED.get(event, ()):
        if field not in rec:
            bad("%s is missing required field %r" % (event, field))
        elif strict and rec[field] is None:
            bad("%s field %r is null under --strict" % (event, field))

    if event == "env_step":
        problems += _check_env_step(rec, line_no)
    elif event == "model_call":
        problems += _check_model_call(rec, line_no)

    for key in _keys_recursive(rec):
        if key.lower() in CREDENTIAL_KEYS:
            bad("a credential header key %r appears in the record; the format "
                "stores no request headers anywhere" % key)
    return problems


def _check_env_step(rec: Dict[str, Any], line_no: int) -> List[str]:
    problems = []

    def bad(msg):
        problems.append("line %d: %s" % (line_no, msg))

    frames = rec.get("frames")
    n = rec.get("n_frames")
    h = rec.get("frame_hash")
    if frames is None:
        if n != 0:
            bad("frames is null but n_frames is %r; must be 0" % (n,))
        if h is not None:
            bad("frames is null but frame_hash is set")
    elif not isinstance(frames, list):
        bad("frames is %s, not a list" % type(frames).__name__)
    else:
        if n != len(frames):
            bad("n_frames %r != len(frames) %d" % (n, len(frames)))
        if h != sha256_of(frames):
            bad("frame_hash does not match a recomputation over frames")
    if h is not None and not HASH.match(str(h)):
        bad("frame_hash %r is not 'sha256:' + 64 lowercase hex" % (h,))

    action = rec.get("action")
    if not isinstance(action, dict) or set(action) != {"name", "id", "data"}:
        bad("action must be an object with exactly name, id, data; got %r"
            % (sorted(action) if isinstance(action, dict) else action,))
    else:
        if action["name"] == "RESET" and action["id"] is not None:
            bad("RESET carries an action id")
        if isinstance(action["name"], str) and action["name"].startswith("ACTION") \
                and action["id"] is None:
            bad("%s carries no action id" % action["name"])

    guard = rec.get("guard")
    if not isinstance(guard, dict) or "decision" not in guard:
        bad("guard must be an object carrying a decision")
    elif guard["decision"] not in ("allow", "deny"):
        bad("guard decision %r is neither allow nor deny" % (guard["decision"],))
    elif guard["decision"] == "deny" and frames is not None:
        bad("a denied step carries frames; a refusal has frames null")

    http = rec.get("http")
    if not isinstance(http, dict):
        bad("http must be an object")
    else:
        path = http.get("path")
        if path is not None and not str(path).startswith("/api/cmd/"):
            bad("env_step http.path %r is not a command path; a request "
                "carrying no game command is an env_meta record" % (path,))
    return problems


def _check_model_call(rec: Dict[str, Any], line_no: int) -> List[str]:
    problems = []

    def bad(msg):
        problems.append("line %d: %s" % (line_no, msg))

    if not isinstance(rec.get("usage"), dict):
        bad("usage must be an object, copied through verbatim")
    for key in _keys_recursive(rec):
        if COST_SUBSTRING in key.lower():
            bad("model_call carries the key %r. Section 5: no dollar figure "
                "appears in the ledger; cost is derived later from usage and a "
                "named price table." % key)
    ref = rec.get("pricing_ref")
    if ref is not None:
        if not isinstance(ref, dict) or "table" not in ref or "sha256" not in ref:
            bad("pricing_ref must name a table and its sha256")
    return problems


def validate_file(path: str, strict: bool = False) -> Dict[str, Any]:
    problems: List[str] = []
    seqs: List[int] = []
    stamps: List[str] = []
    games: List[str] = []
    levels: Dict[str, Optional[int]] = {}
    count = 0

    with open(path, encoding="utf-8", newline="") as fh:
        for line_no, raw in enumerate(fh, start=1):
            if not raw.strip():
                continue
            count += 1
            problems += validate_line(raw, line_no, strict)
            try:
                rec = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(rec.get("seq"), int):
                seqs.append(rec["seq"])
            if isinstance(rec.get("ts"), str):
                stamps.append(rec["ts"])
            if rec.get("game_id"):
                games.append(rec["game_id"])
            if rec.get("event") == "env_step":
                problems += _check_level_carry(rec, line_no, levels)

    if seqs and seqs != list(range(1, len(seqs) + 1)):
        problems.append("seq is not dense and 1-based over the file "
                        "(first %r, last %r, %d records)"
                        % (seqs[0], seqs[-1], len(seqs)))
    if stamps != sorted(stamps):
        problems.append("ts is not non-decreasing in seq order")

    dev = set(arc_client.dev_pile())
    off = sorted({g for g in games if g not in dev})
    if off:
        problems.append("SEALED-PILE CONTACT: game ids outside the development "
                        "pile appear in this stream: %s" % ", ".join(off))

    return {"path": path, "records": count, "problems": problems,
            "ok": not problems, "strict": strict}


def _check_level_carry(rec: Dict[str, Any], line_no: int,
                       state: Dict[str, Optional[int]]) -> List[str]:
    """The rule proxy/reconcile.py re-checks: walk a run's env_steps carrying
    the previous level forward when this record has no levels_completed, and
    the recorded level and level_boundary must come out the same."""
    rid = rec.get("run_id")
    raw = rec.get("levels_completed")
    before = state.get(rid)
    expect = raw if isinstance(raw, int) else before
    boundary = bool(isinstance(raw, int) and before is not None and raw > before)
    state[rid] = expect
    out = []
    if rec.get("level") != expect:
        out.append("line %d: level %r does not follow from the run's "
                   "levels_completed sequence (expected %r)"
                   % (line_no, rec.get("level"), expect))
    if bool(rec.get("level_boundary")) != boundary:
        out.append("line %d: level_boundary %r does not follow from the "
                   "sequence (expected %r)"
                   % (line_no, rec.get("level_boundary"), boundary))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?",
                    default=os.path.join(
                        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "runs", "_migrations", "ledger-v0-to-v1.0",
                        "ledger.canon.jsonl"))
    ap.add_argument("--strict", action="store_true",
                    help="also require every field to be non-null. Right for a "
                         "stream a live proxy wrote; wrong for a lift, whose "
                         "nulls are recorded gaps (LEDGER_FORMAT section 7).")
    ap.add_argument("--max-problems", type=int, default=25)
    args = ap.parse_args(argv)

    result = validate_file(args.path, args.strict)
    print("%s: %d records, %s%s"
          % (os.path.basename(result["path"]), result["records"],
             "CONFORMS" if result["ok"] else "%d PROBLEMS" % len(result["problems"]),
             " (strict)" if args.strict else ""))
    for p in result["problems"][:args.max_problems]:
        print("  %s" % p)
    if len(result["problems"]) > args.max_problems:
        print("  ... and %d more" % (len(result["problems"]) - args.max_problems))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
