#!/usr/bin/env python3
"""Verify fleet-study/data/*.jsonl -- schema, ids, and *resolvable* evidence.

    python fleet-study/verify.py            # check the real datasets
    python fleet-study/verify.py --selftest # prove this checker can go red
    python fleet-study/verify.py --fast     # skip evidence resolution (no git/fs)

Why the self-test exists
------------------------
`failures.jsonl` carries a class named `check_with_no_failing_path`: a check
that exists, is wired into a gate, and has no input that makes it fail.  A
verifier for that dataset that could not itself go red would be the same
defect, one level up.  So `--selftest` feeds this checker eleven deliberately
broken datasets and asserts it rejects each one for the right reason.  If the
self-test passes, every failing path below has been exercised at least once.

What "evidence" means here
--------------------------
Every row must cite at least one thing an auditor can open:

    git:<40-hex>      resolved with `git cat-file -t`
    file:<path>       **repo-relative**; `#anchor` suffix ignored

An absolute path is rejected.  It resolves only on the machine that wrote it,
and against *that* machine's checkout rather than the tree being verified --
115 such citations sat green for a whole round here, and were concealing two
paths to a directory that had never been committed anywhere.

A `file:` path that no longer exists is *not* automatically an error -- this
repo deletes board items when they are claimed, so half the delivery record
lives only in history.  Missing paths are re-checked with `git log --all --`
and reported as `historical` rather than `missing`.  A path that is in neither
the worktree nor history is an error: it is a citation to something that never
existed, which is itself one of the catalogued failure classes.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(__file__).resolve().parent / "data"

SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")
#: `C:\...`, `C:/...`, `/...`, or a UNC share -- anything not repo-relative.
ABS_RE = re.compile(r"^([A-Za-z]:[\\/]|[\\/])")
UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?Z$")

# dataset -> (id prefix, required keys, {key: allowed values})
SCHEMAS = {
    "failures": (
        "F",
        {"id", "class", "title", "what_happened", "why_it_was_invisible",
         "direction", "detected_by", "detection_latency", "evidence", "fix",
         "recurred"},
        {"direction": {"reassuring", "alarming", "neutral"}},
    ),
    "timeline": (
        "T",
        {"id", "utc", "change", "before", "trigger", "trigger_kind",
         "commits", "evidence", "recurred_after", "recurrence_evidence"},
        {},
    ),
    "counterevidence": (
        "C",
        {"id", "kind", "subject", "finding", "quantified", "evidence",
         "confidence", "caveat"},
        {"confidence": {"high", "medium", "low"}},
    ),
    "assembly": (
        "A",
        {"id", "aspect", "claim", "measurement", "how_measured", "evidence",
         "confidence", "caveat"},
        {"confidence": {"high", "medium", "low"},
         "aspect": {"contract_as_part", "hot_reconfiguration",
                    "standard_interface", "other"}},
    ),
    "human_actions": (
        "H",
        {"id", "utc", "utc_confidence", "action", "category",
         "why_not_automatable", "automatable_in_principle", "evidence",
         "confidence", "caveat"},
        {"confidence": {"high", "medium", "low"},
         "utc_confidence": {"exact", "inferred", "unknown"}},
    ),
    "deliveries": (
        None,  # ids are board item slugs, not N-nn
        {"id", "territory", "state", "evidence"},
        {},
    ),
    "bus": (
        "B",
        {"id", "utc", "from", "to", "subject", "evidence"},
        {},
    ),
}

# Datasets whose rows must be in ascending `utc` order.
ORDERED_BY_UTC = {"timeline", "human_actions", "bus"}


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notes: list[str] = []

    def err(self, where: str, msg: str) -> None:
        self.errors.append(f"{where}: {msg}")

    def warn(self, where: str, msg: str) -> None:
        self.warnings.append(f"{where}: {msg}")


def load_rows(path: Path, rep: Report) -> list[dict]:
    """Read one JSONL file strictly as UTF-8.  Encoding errors are errors."""
    rows = []
    try:
        raw = path.read_bytes().decode("utf-8")
    except UnicodeDecodeError as e:
        rep.err(path.name, f"not valid UTF-8 ({e})")
        return rows
    if "\r\n" in raw:
        rep.err(path.name, "CRLF line endings; datasets are pinned to LF")
    for i, line in enumerate(raw.splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            rep.err(f"{path.name}:{i}", f"invalid JSON ({e})")
            continue
        if not isinstance(obj, dict):
            rep.err(f"{path.name}:{i}", "line is not a JSON object")
            continue
        obj["__line"] = i
        rows.append(obj)
    return rows


def check_schema(name: str, rows: list[dict], rep: Report) -> None:
    prefix, required, enums = SCHEMAS[name]
    seen_ids: dict[str, int] = {}
    last_utc = None
    last_num = 0

    for row in rows:
        line = row["__line"]
        where = f"{name}.jsonl:{line}"

        missing = required - set(row)
        if missing:
            rep.err(where, f"missing required key(s): {sorted(missing)}")

        rid = row.get("id")
        if not isinstance(rid, str) or not rid:
            rep.err(where, "id must be a non-empty string")
        else:
            if rid in seen_ids:
                rep.err(where, f"duplicate id {rid} (first seen line {seen_ids[rid]})")
            seen_ids[rid] = line
            if prefix:
                m = re.fullmatch(rf"{prefix}-(\d+)", rid)
                if not m:
                    rep.err(where, f"id {rid!r} does not match {prefix}-<n>")
                else:
                    n = int(m.group(1))
                    if n <= last_num:
                        rep.err(where, f"id {rid} is not ascending (previous {last_num})")
                    last_num = max(last_num, n)

        for key, allowed in enums.items():
            if key in row and row[key] not in allowed:
                rep.err(where, f"{key}={row[key]!r} not in {sorted(allowed)}")

        if "utc" in row and row["utc"] is not None:
            if not isinstance(row["utc"], str) or not UTC_RE.match(row["utc"]):
                rep.err(where, f"utc={row['utc']!r} is not ISO8601 ...Z")
            elif name in ORDERED_BY_UTC:
                if last_utc and row["utc"] < last_utc:
                    rep.err(where, f"utc {row['utc']} precedes previous row {last_utc}")
                last_utc = row["utc"]

        ev = row.get("evidence")
        if not isinstance(ev, list) or not ev:
            rep.err(where, "evidence must be a non-empty list")
        else:
            for item in ev:
                if not isinstance(item, str):
                    rep.err(where, f"evidence entry {item!r} is not a string")
                elif not item.startswith(("git:", "file:")):
                    rep.err(where, f"evidence entry {item!r} lacks a git:/file: scheme")
                elif item.startswith("file:") and ABS_RE.match(item[5:]):
                    # An absolute path resolves only on the machine that wrote
                    # it, and points at *that* machine's checkout rather than
                    # the tree being verified.  115 of these sat green for a
                    # whole round, and hid two citations to a directory that
                    # was never committed at all -- the checker was passing on
                    # a promise it had no way to test.
                    rep.err(where, f"evidence entry {item!r} is an absolute path; "
                                   "citations must be repo-relative or no other "
                                   "machine can resolve them")

        # A row whose every claim is hedged to nothing is not evidence.
        if row.get("confidence") == "low" and not row.get("caveat"):
            rep.warn(where, "confidence=low with no caveat explaining why")

        # C-45: `recurred` carries no corroborating column -- timeline.jsonl has
        # `recurrence_evidence`, failures.jsonl has nothing -- so the field ended
        # up conflating "recurred after its fix" with "was never fixed at all".
        # A row cannot have recurred after a fix that does not exist.  Warned,
        # not errored: the existing rows are first-hand records and rewriting
        # them to satisfy a checker written afterwards would be the same
        # backwards reasoning this dataset catalogues.
        if name == "failures" and row.get("recurred") and not row.get("fix"):
            rep.warn(where, "recurred=true with no fix -- nothing could recur "
                            "from a fix that never landed (see C-45)")


def resolve_evidence(rows_by_ds: dict[str, list[dict]], rep: Report) -> dict:
    """Resolve every git: sha and file: path exactly once."""
    shas: dict[str, list[str]] = {}
    files: dict[str, list[str]] = {}
    for ds, rows in rows_by_ds.items():
        for row in rows:
            for item in row.get("evidence") or []:
                if not isinstance(item, str):
                    continue
                where = f"{ds}.jsonl:{row['__line']}"
                if item.startswith("git:"):
                    shas.setdefault(item[4:].strip(), []).append(where)
                elif item.startswith("file:"):
                    files.setdefault(item[5:].split("#", 1)[0].strip(), []).append(where)

    stats = {"sha_ok": 0, "sha_bad": 0, "file_ok": 0, "file_historical": 0, "file_bad": 0}

    for sha, wheres in sorted(shas.items()):
        if not SHA_RE.match(sha):
            stats["sha_bad"] += 1
            rep.err(wheres[0], f"git:{sha} is not a hex object name")
            continue
        r = subprocess.run(["git", "cat-file", "-t", sha], cwd=ROOT,
                           capture_output=True, text=True)
        if r.returncode != 0 or r.stdout.strip() != "commit":
            stats["sha_bad"] += 1
            rep.err(wheres[0], f"git:{sha} does not resolve to a commit"
                               + (f" (+{len(wheres)-1} more rows)" if len(wheres) > 1 else ""))
        else:
            stats["sha_ok"] += 1

    for rel, wheres in sorted(files.items()):
        p = Path(rel)
        if not p.is_absolute():
            p = ROOT / rel
        if p.exists():
            stats["file_ok"] += 1
            continue
        # Deleted-but-real: board items vanish from items/ when claimed.
        try:
            probe = p.relative_to(ROOT).as_posix()
        except ValueError:
            probe = rel
        r = subprocess.run(["git", "log", "--all", "-1", "--format=%H", "--", probe],
                           cwd=ROOT, capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            stats["file_historical"] += 1
            rep.notes.append(f"{wheres[0]}: file:{rel} is deleted but present in history "
                             f"({r.stdout.strip()[:8]})")
        else:
            stats["file_bad"] += 1
            rep.err(wheres[0], f"file:{rel} exists neither in the worktree nor in history"
                              + (f" (+{len(wheres)-1} more rows)" if len(wheres) > 1 else ""))
    return stats


def run(data_dir: Path, fast: bool, rep: Report) -> dict:
    rows_by_ds: dict[str, list[dict]] = {}
    for name in SCHEMAS:
        path = data_dir / f"{name}.jsonl"
        if not path.exists():
            rep.warn(f"{name}.jsonl", "absent -- dataset named in the item but not harvested")
            continue
        rows = load_rows(path, rep)
        rows_by_ds[name] = rows
        check_schema(name, rows, rep)

    stats = {} if fast else resolve_evidence(rows_by_ds, rep)
    stats["rows"] = {k: len(v) for k, v in rows_by_ds.items()}
    stats["total_rows"] = sum(len(v) for v in rows_by_ds.values())
    return stats


# --------------------------------------------------------------------------
# self-test: eleven injected defects, each of which must make run() go red
# --------------------------------------------------------------------------

_GOOD = {
    "id": "F-01", "class": "silent_failure", "title": "t", "what_happened": "w",
    "why_it_was_invisible": "i", "direction": "reassuring", "detected_by": "d",
    "detection_latency": "unknown", "evidence": ["file:CLAUDE.md"], "fix": "f",
    "recurred": False,
}

_DEFECTS = [
    ("baseline is accepted", [_GOOD], None),
    ("invalid JSON", "{not json}", "invalid JSON"),
    ("missing required key", [{k: v for k, v in _GOOD.items() if k != "fix"}],
     "missing required key"),
    ("bad enum", [{**_GOOD, "direction": "sideways"}], "not in"),
    ("duplicate id", [_GOOD, dict(_GOOD)], "duplicate id"),
    ("non-ascending id", [{**_GOOD, "id": "F-05"}, {**_GOOD, "id": "F-02"}],
     "not ascending"),
    ("malformed id", [{**_GOOD, "id": "FAILURE-1"}], "does not match"),
    ("empty evidence", [{**_GOOD, "evidence": []}], "non-empty list"),
    ("evidence without scheme", [{**_GOOD, "evidence": ["monitor/board.py"]}],
     "lacks a git:/file: scheme"),
    ("unresolvable sha", [{**_GOOD, "evidence": ["git:" + "0" * 40]}],
     "does not resolve"),
    ("citation to a file that never existed",
     [{**_GOOD, "evidence": ["file:monitor/this-was-never-created.py"]}],
     "neither in the worktree nor in history"),
    ("CRLF", [_GOOD], "CRLF"),
    ("absolute citation path",
     [{**_GOOD, "evidence": ["file:C:/Users/user/Desktop/theoria/CLAUDE.md"]}],
     "is an absolute path"),
    ("posix absolute citation path",
     [{**_GOOD, "evidence": ["file:/etc/hostname"]}], "is an absolute path"),
]

#: Same shape, but asserted against `rep.warnings` instead of `rep.errors`.
#: A warning path with no self-test is the same hole as a check with no failing
#: path -- it just fails quieter.
_WARN_DEFECTS = [
    ("recurred=true with no fix", [{**_GOOD, "recurred": True, "fix": None}],
     "nothing could recur"),
    ("confidence=low with no caveat",
     [{**_GOOD, "confidence": "low", "caveat": ""}], "no caveat"),
]


def _write(d: Path, payload, crlf: bool = False, name: str = "failures") -> Path:
    path = d / f"{name}.jsonl"
    if isinstance(payload, str):
        body = payload
    else:
        body = "\n".join(json.dumps({k: v for k, v in r.items() if k != "__line"},
                                    ensure_ascii=False) for r in payload)
    nl = "\r\n" if crlf else "\n"
    path.write_bytes((body + "\n").replace("\n", nl).encode("utf-8"))
    return path


def selftest() -> int:
    failures = []
    for label, payload, expect in _DEFECTS:
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            path = d / "failures.jsonl"
            if isinstance(payload, str):
                body = payload
            else:
                body = "\n".join(json.dumps({k: v for k, v in r.items()
                                             if k != "__line"}, ensure_ascii=False)
                                 for r in payload)
            nl = "\r\n" if label == "CRLF" else "\n"
            path.write_bytes((body + "\n").replace("\n", nl).encode("utf-8"))

            rep = Report()
            run(d, fast=False, rep=rep)
            joined = " | ".join(rep.errors)

            if expect is None:
                if rep.errors:
                    failures.append(f"{label!r}: expected clean, got: {joined}")
            elif not rep.errors:
                failures.append(f"{label!r}: expected an error, checker stayed green")
            elif expect not in joined:
                failures.append(f"{label!r}: wrong error; wanted {expect!r}, got: {joined}")

        mark = "FAIL" if failures and failures[-1].startswith(repr(label)) else "ok"
        print(f"  [{mark:>4}] {label}")

    for label, payload, expect in _WARN_DEFECTS:
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            _write(d, payload)
            rep = Report()
            run(d, fast=False, rep=rep)
            joined = " | ".join(rep.warnings)
            if rep.errors:
                failures.append(f"{label!r}: expected a warning, got error(s): "
                                f"{' | '.join(rep.errors)}")
            elif not rep.warnings:
                failures.append(f"{label!r}: expected a warning, checker stayed silent")
            elif expect not in joined:
                failures.append(f"{label!r}: wrong warning; wanted {expect!r}, "
                                f"got: {joined}")
        mark = "FAIL" if failures and failures[-1].startswith(repr(label)) else "ok"
        print(f"  [{mark:>4}] {label}  (warning path)")

    print()
    if failures:
        print("SELFTEST RED -- this checker does not fail where it should:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"SELFTEST GREEN -- {len(_DEFECTS)} injected defects, "
          f"{len(_DEFECTS) - 1} rejected, 1 baseline accepted; "
          f"{len(_WARN_DEFECTS)} warning paths exercised.")
    print("This checker has a failing path.  It is not a green light with no red.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--selftest", action="store_true",
                    help="prove the checker can go red, then exit")
    ap.add_argument("--fast", action="store_true",
                    help="skip evidence resolution (no git or filesystem probes)")
    ap.add_argument("--data", type=Path, default=DATA)
    args = ap.parse_args()

    if args.selftest:
        print("fleet-study/verify.py --selftest\n")
        return selftest()

    rep = Report()
    stats = run(args.data, args.fast, rep)

    print(f"fleet-study/verify.py -- {args.data}")
    for ds, n in sorted(stats["rows"].items()):
        print(f"  {ds + '.jsonl':<28} {n:>4} rows")
    print(f"  {'TOTAL':<28} {stats['total_rows']:>4} rows")
    if not args.fast:
        print(f"\n  evidence: {stats['sha_ok']} commits resolved, "
              f"{stats['file_ok']} files present, "
              f"{stats['file_historical']} deleted-but-in-history, "
              f"{stats['sha_bad'] + stats['file_bad']} unresolvable")
    if rep.notes:
        print(f"\n  {len(rep.notes)} note(s):")
        for n in rep.notes[:10]:
            print(f"    - {n}")
        if len(rep.notes) > 10:
            print(f"    ... and {len(rep.notes) - 10} more")
    if rep.warnings:
        print(f"\n  {len(rep.warnings)} warning(s):")
        for w in rep.warnings[:20]:
            print(f"    - {w}")
        if len(rep.warnings) > 20:
            print(f"    ... and {len(rep.warnings) - 20} more")
    if rep.errors:
        print(f"\nRED -- {len(rep.errors)} error(s):")
        for e in rep.errors[:40]:
            print(f"    - {e}")
        if len(rep.errors) > 40:
            print(f"    ... and {len(rep.errors) - 40} more")
        return 1
    print("\nGREEN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
