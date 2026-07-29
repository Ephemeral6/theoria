"""Every gold-standard row in this lab, with the judge who wrote it.

V11 shipped 127 rows across six territory partials; V15 shipped 126 rows across
nine blinded batches. Neither run recorded a judge id in its merged table, so
attribution is recovered here from the partials themselves (V11) and from the
`批次` column (V15). Nothing is inferred: a row belongs to the judge whose file
it appears in.

    python verify-lab/irr/rows.py            # counts per judge
    python verify-lab/irr/rows.py --json     # the whole corpus

This module reads *only* the two censuses. It never opens `KNOWN_GAPS.json`'s
`verdict` field and never imports `criterion.py`, for the same reason
`reconcile.py` does not: the probe is the thing under test.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Dict, List, Optional, Sequence

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
LAB = os.path.join(REPO, "verify-lab")

V11_RUN = os.path.join(LAB, "runs", "20260728T152000Z-V11-negative-control-census")
V11_TABLE = os.path.join(V11_RUN, "CENSUS_TABLE.md")
V11_PARTIALS = os.path.join(V11_RUN, "partials")
V15_TABLE = os.path.join(LAB, "SUPPLEMENT_TABLE.md")

# V11's merged table carries a `领地` column, and it is exactly the six auditors'
# scopes: 20 / 19 / 14 / 10 / 32 / 32 = 127. So the judge attribution is already
# in the published table and does not have to be recovered from the partials --
# which is the version of this module that was written first, and which lost two
# rows to Markdown-shape drift between the six files. The partials remain the
# place to read an auditor's reasoning; they are not the place to count.
V11_JUDGES = {
    "engine-rig/theory-compiler": "engine-rig-theory-compiler",
    "exam/battery": "exam-battery",
    "worldgen/fuzzlab": "worldgen-fuzzlab",
    "figures/release": "figures-release",
    "proxy/arc-recon": "proxy-arcrecon",
    "arms": "arms",
}


def clean(token: str) -> str:
    """`worldgen/build.py --check` -> `worldgen/build.py`; strip line numbers.

    Transcribed from `frame/reconcile.py::_clean` rather than imported, so this
    module has no dependency on the frame and can be run against either census
    alone.
    """
    tok = token.split()[0]
    tok = tok.split("::")[0]
    tok = re.sub(r":\d+(-\d+)?$", "", tok)
    return tok.replace("\\", "/")


VERDICTS = ("是", "部分", "否", "不适用")


def _cells(line: str, keep: int) -> Optional[List[str]]:
    if not line.startswith("| "):
        return None
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cells) > keep:
        cells = cells[: keep - 1] + ["|".join(cells[keep - 1:])]
    if len(cells) != keep:
        return None
    if set(cells[0]) <= set("-") or not cells[0]:
        return None
    return cells


def _split(line: str) -> Optional[List[str]]:
    """Raw cells of a Markdown row, no column-count assumption."""
    if not line.startswith("| "):
        return None
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cells) < 4 or set(cells[0]) <= set("-") or not cells[0]:
        return None
    return cells


def _head(cell: str) -> str:
    """`是(实测)` / `**是（实测）**` / `不适用（库）` -> `是` / `不适用`.

    The bold-stripping is load-bearing, not cosmetic. Four V11 rows emphasise
    the verdict cell (`**是（实测）**`); without stripping, the column-shape
    sniffer below slides one cell to the right and reads the *second* verdict as
    the first, which silently mis-attributes those rows' 有负控 answers.
    """
    return cell.replace("*", "").split("(")[0].split("（")[0].strip()


def _entry_paths(entry: str) -> List[str]:
    """Paths an entry cell names.

    Five of the six V11 partials wrap paths in backticks;
    `engine-rig-theory-compiler.md` does not, so a backtick-only reader loses all
    20 of its rows' paths. Fall back to whitespace tokens that look like a
    repository-relative file.
    """
    found = [clean(p) for p in re.findall(r"`([^`]+)`", entry)]
    if found:
        return found
    return [clean(tok) for tok in entry.split()
            if "/" in tok and re.search(r"\.(py|sh)\b", tok)]


def v11_rows(path: str = V11_TABLE) -> List[Dict[str, object]]:
    """The 127 rows of V11 section 1, each tagged with the auditor who wrote it.

    Row parsing is `frame/reconcile.py::census_rows` transcribed (one row carries
    pipes inside its evidence cell, so the split keeps six separators and joins
    the rest); the judge is the `领地` column.
    """
    rows: List[Dict[str, object]] = []
    started = False
    for line in open(path, encoding="utf-8"):
        cells = _cells(line, 7)
        if cells is None:
            continue
        if cells[0] == "领地":
            started = True
            continue
        if not started or cells[0] not in V11_JUDGES:
            continue
        rows.append({
            "census": "V11",
            "judge": V11_JUDGES[cells[0]],
            "territory": cells[0],
            "entry": cells[1],
            "paths": _entry_paths(cells[1]),
            "can_red": _head(cells[2]),
            "has_negctl": _head(cells[3]),
            "exit_honest": _head(cells[4]),
            "raw_negctl": cells[3],
        })
    return rows


def v15_rows(path: str = V15_TABLE) -> List[Dict[str, object]]:
    """The 126 supplement rows; the judge is the `批次` column (b1..b9)."""
    rows: List[Dict[str, object]] = []
    for line in open(path, encoding="utf-8"):
        cells = _cells(line, 7)
        if not cells:
            continue
        rel = cells[0].strip().strip("`").split()[0]
        if not re.match(r"^b\d$", cells[6]):
            continue
        rows.append({
            "census": "V15",
            "judge": cells[6],
            "territory": rel.split("/")[0],
            "entry": rel,
            "paths": [clean(rel)],
            "can_red": _head(cells[1]),
            "has_negctl": _head(cells[2]),
            "exit_honest": _head(cells[3]),
            "raw_negctl": cells[2],
        })
    return rows


def corpus() -> List[Dict[str, object]]:
    return v11_rows() + v15_rows()


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    rows = corpus()
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0
    per: Dict[str, int] = {}
    for row in rows:
        per[str(row["judge"])] = per.get(str(row["judge"]), 0) + 1
    print("rows: %d  (V11 %d, V15 %d)" % (
        len(rows),
        sum(1 for r in rows if r["census"] == "V11"),
        sum(1 for r in rows if r["census"] == "V15")))
    for judge, n in per.items():
        cells = [str(r["has_negctl"]) for r in rows if r["judge"] == judge]
        part = sum(1 for c in cells if c == "部分")
        print("  %-28s %3d rows   部分 %2d  (%.0f%%)" % (
            judge, n, part, 100.0 * part / n if n else 0.0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
