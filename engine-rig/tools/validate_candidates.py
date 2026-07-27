"""Validator for candidates.jsonl against CONTRACTS/candidates_schema.md (frozen v0.1).

The contract is a text file, so it cannot enforce itself; this is its executable
form.  It is deliberately strict about the things the contract states outright --
the exact key set, the enum values, `status == "candidate"`, the "<k>/<n>"
coverage syntax -- and says nothing about payload internals, which the contract
leaves to each engine's README.

Usage:
    python -m tools.validate_candidates <path> [<path> ...]
"""

import json
import re
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, Iterable, List

REQUIRED_KEYS = {"id", "engine", "kind", "payload", "evidence", "status", "timestamp"}

ENGINES = {
    "mdl_segmenter",
    "cegis_miner",
    "zero_space",
    "lp_potential",
    "fd_adapter",
    "probe_frontier",
}

KINDS = {
    "object_hypothesis",
    "rule_hypothesis",
    "invariant",
    "heuristic",
    "plan",
    "probe_design",
}

COVERAGE_RE = re.compile(r"^\d+/\d+$")


def _is_json_object(value: Any) -> bool:
    return isinstance(value, dict)


def _valid_timestamp(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        datetime.fromisoformat(text)
        return True
    except ValueError:
        return False


def validate_row(row: Any, where: str = "") -> List[str]:
    prefix = ("%s: " % where) if where else ""
    errors: List[str] = []
    if not _is_json_object(row):
        return [prefix + "line is not a JSON object"]

    keys = set(row)
    for missing in sorted(REQUIRED_KEYS - keys):
        errors.append(prefix + "missing key %r" % missing)
    for extra in sorted(keys - REQUIRED_KEYS):
        errors.append(prefix + "unexpected key %r" % extra)

    if "id" in row:
        try:
            uuid.UUID(str(row["id"]))
        except (ValueError, AttributeError, TypeError):
            errors.append(prefix + "id is not a uuid: %r" % (row["id"],))

    if "engine" in row and row["engine"] not in ENGINES:
        errors.append(prefix + "engine not in the frozen enum: %r" % (row["engine"],))
    if "kind" in row and row["kind"] not in KINDS:
        errors.append(prefix + "kind not in the frozen enum: %r" % (row["kind"],))
    if "payload" in row and not _is_json_object(row["payload"]):
        errors.append(prefix + "payload is not an object")
    if "status" in row and row["status"] != "candidate":
        errors.append(prefix + "status must be 'candidate', got %r" % (row["status"],))
    if "timestamp" in row and not _valid_timestamp(row["timestamp"]):
        errors.append(prefix + "timestamp is not ISO8601: %r" % (row["timestamp"],))

    evidence = row.get("evidence")
    if not _is_json_object(evidence):
        errors.append(prefix + "evidence is not an object")
    else:
        for extra in sorted(set(evidence) - {"transitions", "coverage"}):
            errors.append(prefix + "unexpected evidence key %r" % extra)
        transitions = evidence.get("transitions")
        if not isinstance(transitions, list) or not all(
            isinstance(t, int) and not isinstance(t, bool) for t in transitions
        ):
            errors.append(prefix + "evidence.transitions must be a list of ints")
        coverage = evidence.get("coverage")
        if not isinstance(coverage, str) or not COVERAGE_RE.match(coverage):
            errors.append(prefix + "evidence.coverage must be '<k>/<n>', got %r" % (coverage,))
        else:
            k, n = (int(x) for x in coverage.split("/"))
            if n == 0:
                errors.append(prefix + "evidence.coverage denominator is zero")
            elif k > n:
                errors.append(prefix + "evidence.coverage k > n: %r" % (coverage,))
    return errors


def validate_rows(rows: Iterable[Dict[str, Any]]) -> List[str]:
    errors: List[str] = []
    for i, row in enumerate(rows):
        errors.extend(validate_row(row, "row %d" % i))
    return errors


def validate_file(path: str) -> List[str]:
    errors: List[str] = []
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            if not line.strip():
                errors.append("%s:%d: blank line (the stream is one object per line)" % (path, lineno))
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append("%s:%d: not valid JSON (%s)" % (path, lineno, exc))
                continue
            errors.extend(validate_row(row, "%s:%d" % (path, lineno)))
    return errors


def main(argv: List[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    total = 0
    for path in argv:
        errors = validate_file(path)
        with open(path, "r", encoding="utf-8") as fh:
            n_rows = sum(1 for line in fh if line.strip())
        if errors:
            total += len(errors)
            print("FAIL %s (%d rows, %d errors)" % (path, n_rows, len(errors)))
            for error in errors:
                print("  " + error)
        else:
            print("OK   %s (%d rows)" % (path, n_rows))
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
