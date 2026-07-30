"""Count the enumerated rows in each citecheck slice, under a stated rule.

P18. `MANIFEST.json` used a row count as the checked property behind
`state: complete`. A count asserted in prose, which nobody can re-derive, is
the exact defect this run was commissioned to fix -- so the count needs a
script, and this is it. Run it; do not trust the number beside it.

    python count_rows.py            # print the table
    python count_rows.py --check    # exit 1 if MANIFEST.json disagrees

**The rule**, stated because the original numbers were produced by three
different ones:

  a row is a line whose stripped form starts with `|`, EXCLUDING
    - lines inside a fenced code block (``` ... ```), which are examples of
      table syntax, not rows of this audit, and
    - GitHub-Flavored-Markdown separator lines (`|---|---|`), which are
      punctuation.

  Header rows ARE counted. That is a choice, not a discovery: it is the rule
  under which two of the four original numbers reproduce, so adopting it
  changes the fewest recorded figures. `data_rows` (header excluded, one per
  table) is printed alongside for anyone who wants the other convention -- the
  point is that the convention is written down, not which one won.
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEPARATOR = re.compile(r"\|[\s:|-]+\|?")


def count(path: Path) -> dict:
    in_fence = False
    rows = 0
    separators = 0
    for line in path.read_text(encoding="utf-8").split("\n"):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not stripped.startswith("|"):
            continue
        if SEPARATOR.fullmatch(stripped):
            separators += 1          # one per table, so also the table count
        else:
            rows += 1
    return {"rows": rows, "tables": separators, "data_rows": rows - separators}


def main(argv: list[str]) -> int:
    slices = sorted(HERE.glob("citecheck-*.md"))
    measured = {p.name: count(p) for p in slices}

    width = max(len(n) for n in measured)
    print(f"{'slice':<{width}}  {'rows':>5} {'tables':>7} {'data_rows':>10}")
    for name, m in measured.items():
        print(f"{name:<{width}}  {m['rows']:>5} {m['tables']:>7} {m['data_rows']:>10}")

    if "--check" not in argv:
        return 0

    manifest = json.loads((HERE / "MANIFEST.json").read_text(encoding="utf-8"))
    bad = []
    for entry in manifest["citation_slices"]:
        claimed = entry.get("rows")
        if claimed is None:
            continue
        actual = measured[entry["file"]]["rows"]
        if claimed != actual:
            bad.append(f"  {entry['file']}: manifest says {claimed}, rule gives {actual}")

    if bad:
        print("\nROW COUNTS DISAGREE WITH THE MANIFEST:")
        print("\n".join(bad))
        return 1
    print("\nok -- every manifest row count reproduces under the stated rule")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
