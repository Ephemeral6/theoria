#!/usr/bin/env python3
"""P19 · The check a range test cannot be: does the quoted text sit at the cited line?

`census.py` establishes that all 22 line-anchored citations in the sections are
INRANGE, so a range check has **zero yield** on this paper. P18's defect proves why
that is not reassuring: `TheoriaLean.lean:148` was in range and wrong -- the quote
belonged to `:149`.

This is the check with actual yield. When a section quotes a string next to a line
anchor, the quote is a **content anchor**: it is already in the paper, costs no
maintenance, and pins the citation to text rather than to a coordinate. For each
line-anchored citation, take the backtick-quoted spans near it and ask whether any
appears inside the cited line range.

Verdicts:
  HIT      a nearby quoted span is found inside the cited range -- the anchor is
           pinned by content, and a gate could enforce it
  MISS     quoted spans are present near the citation and NONE appears in the range.
           This is the P18 shape and the only red a gate should raise.
  NOQUOTE  no quoted span near the citation. Nothing to anchor against; a gate must
           be silent here rather than guess, and the count of these is the honest
           measure of the check's ceiling.

Normalisation is deliberately loose -- markdown emphasis stripped, whitespace
collapsed -- because the paper bolds inside quotations (`kept **separate and
attributed**`) and a strict comparison would fire on formatting, and a gate with
false reds gets turned off. P16 already paid that tuition.

Usage:  python anchor_content.py
"""

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAPER = HERE.parent.parent
ROOT = PAPER.parent.parent
SECTIONS = PAPER / "sections"

WINDOW = 400          # characters either side of the citation to look for quotes
MIN_QUOTE = 12        # shorter spans are tokens, not content anchors

QUOTED = re.compile(r"`([^`\n]{%d,})`" % MIN_QUOTE)
ANCHORISH = re.compile(r"^[A-Za-z0-9_./-]+\.[a-z]+:\d+(-\d+)?$")
# Any span that names a file -- with or without a line -- is a citation, not content.
FENCE = re.compile(r"^```.*?^```", re.S | re.M)
FILEISH = re.compile(r"[A-Za-z0-9_-]+\.(py|lean|json|jsonl|md|dsl|txt|sh|yml|yaml)\b|/")


def norm(s: str) -> str:
    s = s.replace("**", "").replace("*", "").replace("_", "")
    return re.sub(r"\s+", " ", s).strip().lower()


def main() -> int:
    rows = json.loads((HERE / "census.json").read_text(encoding="utf-8"))
    out = []
    for r in rows:
        if r["verdict"] != "INRANGE":
            continue
        section = (SECTIONS / r["section"]).read_text(encoding="utf-8")
        idx = section.find(r["citation"])
        if idx < 0:
            continue
        # Pair backticks over the WHOLE section, then keep the spans near the
        # citation. Slicing a window first splits a quoted span and makes every
        # subsequent pairing wrong -- the first version of this script did that and
        # produced 14 reds of which none were real.
        # Fenced blocks contain backticks and shift every pairing after them, which
        # is what put junk like " and unsafe at " in the MISS list. Blank them out
        # (preserving offsets) before pairing.
        lexed = FENCE.sub(lambda m: " " * len(m.group(0)), section)
        quotes = [m.group(1) for m in QUOTED.finditer(lexed)
                  if abs(m.start() - idx) <= WINDOW]
        # A quoted span naming a file is a citation, not content to anchor against.
        quotes = [q for q in quotes
                  if not ANCHORISH.match(q.strip()) and not FILEISH.search(q.strip())]

        target = ROOT / r["resolved_to"]
        lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
        span = norm(" ".join(lines[r["start"] - 1: r["end"]]))

        row = {"citation": r["citation"], "section": r["section"],
               "section_line": r["section_line"], "n_quotes": len(quotes)}
        if not quotes:
            row["verdict"] = "NOQUOTE"
        else:
            hits = [q for q in quotes if norm(q) and norm(q) in span]
            if hits:
                row["verdict"] = "HIT"
                row["matched"] = hits[0][:80]
            else:
                row["verdict"] = "MISS"
                row["quotes_tried"] = [q[:70] for q in quotes[:3]]
        out.append(row)

    counts: dict[str, int] = {}
    for r in out:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1

    print(f"P19 content-anchor probe -- {len(out)} in-range citations examined")
    print(f"  HIT     {counts.get('HIT', 0):3d}   a quoted span near the citation is inside the cited range")
    print(f"  MISS    {counts.get('MISS', 0):3d}   quotes present, none inside the range  <-- the P18 shape")
    print(f"  NOQUOTE {counts.get('NOQUOTE', 0):3d}   nothing quoted nearby; a gate must stay silent")
    print()
    for verdict in ("MISS", "HIT", "NOQUOTE"):
        group = [r for r in out if r["verdict"] == verdict]
        if not group:
            continue
        print(f"--- {verdict} ({len(group)}) ---")
        for r in group:
            print(f"  {r['citation']}   ({r['section']}:{r['section_line']}, {r['n_quotes']} quotes nearby)")
            if verdict == "HIT":
                print(f"      matched: {r['matched']}")
            elif verdict == "MISS":
                for q in r["quotes_tried"]:
                    print(f"      tried:   {q}")
        print()

    (HERE / "anchor_content.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote anchor_content.json: {len(out)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
