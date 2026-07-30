#!/usr/bin/env python3
"""P19 · Measure the anchor exposure: citations that name a line, and whether it resolves.

Gate B (`verify_paper.py:250-251`) is two `.exists()` calls. It certifies that a
reader can follow a link and says nothing about what is at the other end. `OPEN_ITEMS`
B4 named the sharper half of that gap -- "check F resolves the file, nothing resolves
the anchor inside it" -- and P18's adversarial round then produced the instance:
`TheoriaLean.lean:148` cited for a line that is at `:149`, in the one citation carrying
that ruling's refusal.

This script is the executable measurement, in the shape P16 and P17 used: prose
becomes a reproducible census before anything becomes a gate.

Three verdicts per line-anchored citation:

  NOFILE     the cited file does not resolve at all -- gate B's own failure, listed
             here because a line anchor into a missing file is a stronger defect
  OUTOFRANGE the file resolves and has fewer lines than the anchor names. Mechanically
             certain, zero judgement, and the cheapest gate available.
  INRANGE    the anchor lands inside the file. NOT the same as correct -- P18's :148
             was in range and wrong. Reported with the line's actual text so a human
             can see what the anchor hits.

The last point is the finding, not a limitation: a range check cannot catch an
off-by-one, so counting how many citations are INRANGE measures what a cheap gate
would still miss.

Usage:  python census.py [--json]
"""

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAPER = HERE.parent.parent            # papers/phase1-workshop
ROOT = PAPER.parent.parent            # repo root
SECTIONS = PAPER / "sections"

# A citation that names a line: `path.ext:N` or `path.ext:N-M`.
ANCHOR = re.compile(
    r"(?P<path>[A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:py|lean|json|jsonl|md|dsl|txt|sh|yml|yaml))"
    r":(?P<start>\d+)(?:-(?P<end>\d+))?"
)


def resolve(path: str) -> Path | None:
    """Gate B's own rule: repo root, then beside PAPER.md."""
    for base in (ROOT, PAPER):
        candidate = base / path
        if candidate.is_file():
            return candidate
    # A bare filename may still be locatable if exactly one file in the tree carries
    # it. Gate F rules on ambiguity; here we only need to know whether the anchor
    # could be checked at all.
    if "/" not in path:
        try:
            out = subprocess.run(
                ["git", "ls-files", f"*/{path}", path],
                cwd=ROOT, capture_output=True, text=True, timeout=60,
            ).stdout.split()
        except Exception:
            return None
        if len(out) == 1:
            return ROOT / out[0]
    return None


def census() -> list[dict]:
    rows: list[dict] = []
    for section in sorted(SECTIONS.glob("*.md")):
        text = section.read_text(encoding="utf-8")
        for m in ANCHOR.finditer(text):
            path, start = m.group("path"), int(m.group("start"))
            end = int(m.group("end")) if m.group("end") else start
            # Which line of the section the citation sits on, so a human can find it.
            cited_at = text[: m.start()].count("\n") + 1
            target = resolve(path)
            row = {
                "section": section.name,
                "section_line": cited_at,
                "citation": m.group(0),
                "path": path,
                "start": start,
                "end": end,
            }
            if target is None:
                row["verdict"] = "NOFILE"
                row["detail"] = "does not resolve from the repo root, from beside PAPER.md, or as a unique bare filename"
            else:
                lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
                row["resolved_to"] = str(target.relative_to(ROOT)).replace("\\", "/")
                row["file_lines"] = len(lines)
                if end > len(lines):
                    row["verdict"] = "OUTOFRANGE"
                    row["detail"] = f"anchor names line {end}; the file has {len(lines)}"
                else:
                    row["verdict"] = "INRANGE"
                    row["at_start"] = lines[start - 1].strip()[:110]
            rows.append(row)
    return rows


def main() -> int:
    rows = census()
    if "--json" in sys.argv:
        # Written by the script, not by a shell redirect: this repo is on Windows and
        # stdout is cp1252, which mangles every CJK line of a SURVEY file it touches.
        out = HERE / "census.json"
        out.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8")
        print(f"wrote {out.name}: {len(rows)} rows")
        return 0

    counts: dict[str, int] = {}
    for r in rows:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1

    print(f"P19 anchor census -- {len(rows)} line-anchored citations "
          f"across {len(set(r['section'] for r in rows))} sections")
    print(f"  NOFILE     {counts.get('NOFILE', 0):3d}   the file itself does not resolve")
    print(f"  OUTOFRANGE {counts.get('OUTOFRANGE', 0):3d}   resolves; the line does not exist")
    print(f"  INRANGE    {counts.get('INRANGE', 0):3d}   the line exists -- which is not the same as correct")
    print()

    for verdict in ("NOFILE", "OUTOFRANGE", "INRANGE"):
        group = [r for r in rows if r["verdict"] == verdict]
        if not group:
            continue
        print(f"--- {verdict} ({len(group)}) ---")
        for r in group:
            print(f"  {r['citation']}")
            print(f"      cited at {r['section']}:{r['section_line']}")
            if verdict == "INRANGE":
                print(f"      line {r['start']} of {r['resolved_to']} ({r['file_lines']} lines) reads:")
                print(f"        {r['at_start']}")
            else:
                print(f"      {r['detail']}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
