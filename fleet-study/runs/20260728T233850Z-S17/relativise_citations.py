#!/usr/bin/env python3
"""Rewrite absolute `file:` citations as repo-relative, in place.

Why this ran (W-1641, 2026-07-29): an adversarial review of EVIDENCE.md found
115 citations in counterevidence.jsonl of the form
`file:C:/Users/user/Desktop/theoria/monitor/...`.  They resolve only on the one
machine that wrote them, and they point at that machine's *main* checkout
rather than at the tree being verified.  EVIDENCE.md section 0 discipline 1
says "every row can be opened"; an absolute path makes that claim
unfalsifiable for every other reader, so the checker was passing on a promise
it could not test.

Kept as a run artefact rather than a territory tool: it is a one-off repair.
The recurrence guard is the new check in verify.py, not this script.
"""

import json
import re
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "data"
PREFIX = re.compile(r"^[A-Za-z]:[\\/]Users[\\/]user[\\/]Desktop[\\/]theoria[\\/]")


def main() -> int:
    total = 0
    for path in sorted(DATA.glob("*.jsonl")):
        raw = path.read_bytes()
        if b"\r" in raw:
            sys.exit(f"{path}: CRLF")
        rows = [json.loads(l) for l in raw.decode("utf-8").splitlines() if l.strip()]
        changed = 0
        for row in rows:
            out = []
            for item in row.get("evidence") or []:
                if isinstance(item, str) and item.startswith("file:"):
                    p = item[5:].replace("\\", "/")
                    rel = PREFIX.sub("", p)
                    if rel != p:
                        changed += 1
                        item = "file:" + rel
                out.append(item)
            if out:
                row["evidence"] = out
        if changed:
            body = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n"
            path.write_bytes(body.encode("utf-8"))
            print(f"  {path.name:26} {changed} citations relativised")
            total += changed
    print(f"{total} absolute citations rewritten")
    return 0


if __name__ == "__main__":
    sys.exit(main())
