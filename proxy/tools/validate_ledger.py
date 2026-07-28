"""Check any stream against `LEDGER_FORMAT.md` v1.0.

The format document said this file "will check any stream" before it existed.
It exists now, and it is the reader-side half of F-16: `proxy/ledger.py` refuses
to *write* a non-canonical field, and this refuses to *accept* one, so a stream
that arrived from somewhere else -- a migrated v0 ledger, another arm's writer,
a hand-edited file -- is judged by the same rules as one this package produced.

What it checks, and why each one is here rather than left to a reader's good
sense:

  * **the envelope** -- `v`, `event`, `seq`, `ts`, `run_id`, `arm`, right types.
    A reader must reject a version it does not know rather than guess (§8).
  * **the field sets** -- via `proxy/canon.py`, the same code the writer uses.
    One registry, two directions.
  * **`seq` is dense and unique** -- §2 says gaps are impossible and duplicates
    mean a corrupt file. A duplicated `seq` is also what an appended forgery
    looks like when someone tries to make a later record replace an earlier one.
  * **`frame_hash` recomputes from `frames`** -- the unit of replay comparison.
    A record whose hash does not match its own frames would make every replay
    that consulted it meaningless, and nothing else in the system would notice.
  * **`n_frames` matches** -- >1 is what the cascade-semantics ruling turns on.
  * **`level` / `level_boundary` recompute** -- §5's condition for a field
    being derived *and* recorded.

    python -m proxy.tools.validate_ledger proxy/var/ledger.jsonl
    python -m proxy.tools.validate_ledger --json some/other.jsonl
"""

import argparse
import json
import sys
from typing import Any, Dict, List

from .. import LEDGER_VERSION
from ..canon import ENVELOPE, NonCanonicalField, check
from ..ledger import ARMS, EVENTS, frame_hash


def validate_records(records: List[Dict[str, Any]],
                     subset: bool = False) -> List[Dict[str, Any]]:
    """Judge a stream against the canon.

    `subset=True` for one run pulled out of a file that holds many. `seq` is
    dense over the *file*, so a per-run slice legitimately has gaps and
    checking density on it would report a corrupt file on a clean one.
    Duplicates are still an error either way -- a repeated `seq` is a forgery
    signature whether or not you are looking at the whole file.
    """
    problems: List[Dict[str, Any]] = []

    def bad(lineno: int, kind: str, detail: str, **extra: Any) -> None:
        entry = {"line": lineno, "kind": kind, "detail": detail}
        entry.update(extra)
        problems.append(entry)

    seen_seq: Dict[int, int] = {}
    # level derivation is per run, so it is tracked per run
    completed: Dict[str, int] = {}

    for lineno, record in enumerate(records, 1):
        if not isinstance(record, dict):
            bad(lineno, "not_an_object", "a ledger line must be a JSON object")
            continue

        version = record.get("v")
        if version != LEDGER_VERSION:
            bad(lineno, "unknown_version",
                "version %r; this reader knows %r (§8)" % (version, LEDGER_VERSION))
            continue

        event = record.get("event")
        if event not in EVENTS:
            bad(lineno, "unknown_event", "event %r" % (event,))
            continue
        arm = record.get("arm")
        if arm not in ARMS:
            bad(lineno, "unknown_arm", "arm %r" % (arm,))
        if not isinstance(record.get("run_id"), str):
            bad(lineno, "bad_run_id", "run_id must be a string")
        ts = record.get("ts")
        if not isinstance(ts, str) or not ts.endswith("Z"):
            bad(lineno, "bad_ts", "ts must be an ISO-8601 UTC string ending in Z")

        seq = record.get("seq")
        if not isinstance(seq, int) or isinstance(seq, bool):
            bad(lineno, "bad_seq", "seq must be an int")
        elif seq in seen_seq:
            bad(lineno, "duplicate_seq",
                "seq %d already appeared on line %d; duplicates mean a corrupt "
                "file (§2), and are what an appended forgery looks like"
                % (seq, seen_seq[seq]))
        else:
            seen_seq[seq] = lineno

        payload = {k: v for k, v in record.items() if k not in ENVELOPE}
        try:
            check(event, payload)
        except NonCanonicalField as exc:
            bad(lineno, "non_canonical", str(exc))
            continue

        if event == "env_step":
            frames = record.get("frames")
            expected = frame_hash(frames)
            if record.get("frame_hash") != expected:
                bad(lineno, "frame_hash_mismatch",
                    "frame_hash is %r but the frames on this very record hash "
                    "to %r" % (record.get("frame_hash"), expected))

            run_id = record.get("run_id")
            before = completed.get(run_id, 0)
            after = record.get("levels_completed")
            after = before if not isinstance(after, int) or isinstance(after, bool) else after
            if record.get("level") != before:
                bad(lineno, "level_does_not_recompute",
                    "level is %r; the step sequence says %d"
                    % (record.get("level"), before))
            if bool(record.get("level_boundary")) != (after > before):
                bad(lineno, "level_boundary_does_not_recompute",
                    "level_boundary is %r; the step sequence says %r"
                    % (record.get("level_boundary"), after > before))
            completed[run_id] = after

    ordered = sorted(seen_seq)
    if (not subset and ordered
            and ordered != list(range(ordered[0], ordered[0] + len(ordered)))):
        problems.append({"line": None, "kind": "sparse_seq",
                         "detail": "seq has gaps; §2 says gaps are impossible"})
    return problems


def validate_file(path: str) -> Dict[str, Any]:
    records: List[Any] = []
    malformed: List[Dict[str, Any]] = []
    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                malformed.append({"line": lineno, "kind": "not_json",
                                  "detail": str(exc)})
    problems = malformed + validate_records(records)
    return {"path": path, "records": len(records),
            "problems": problems, "verdict": "PASS" if not problems else "FAIL"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("path")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--limit", type=int, default=20)
    args = ap.parse_args(argv)

    report = validate_file(args.path)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("%s: %s (%d records, %d problem(s))"
              % (report["path"], report["verdict"], report["records"],
                 len(report["problems"])))
        for problem in report["problems"][:args.limit]:
            print("  line %s  %s: %s"
                  % (problem["line"], problem["kind"], problem["detail"]))
        if len(report["problems"]) > args.limit:
            print("  ... %d more" % (len(report["problems"]) - args.limit))
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
