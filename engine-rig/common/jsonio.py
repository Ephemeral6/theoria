"""Canonical JSON / JSONL helpers.

Every artefact this rig writes goes through here so that "same seed -> same
bytes" is a property of the whole pipeline and not of each call site:
sorted keys, no incidental whitespace, ASCII only, LF line endings.
"""

import json
import os
from typing import Any, Iterable, List


def dumps(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def write_jsonl(path: str, rows: Iterable[Any]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    # newline="" keeps Python from translating "\n" into "\r\n" on Windows.
    with open(path, "w", encoding="utf-8", newline="") as fh:
        for row in rows:
            fh.write(dumps(row))
            fh.write("\n")


def read_jsonl(path: str) -> List[Any]:
    with open(path, "r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=True))
        fh.write("\n")


def read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def append_jsonl(path: str, rows: Iterable[Any]) -> None:
    """Append-only writer -- the only mode any engine may use on candidates.jsonl."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="") as fh:
        for row in rows:
            fh.write(dumps(row))
            fh.write("\n")
