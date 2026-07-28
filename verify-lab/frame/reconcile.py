"""Audit V11's 127 rows and negctl's 141 pinned paths against the V15 frame.

Neither prior count was drawn from a population, so neither can be described as
covering one until somebody says what the population is. `frame.py` says it.
This says what each prior count did and did not reach.

    python verify-lab/frame/reconcile.py            # the four numbers
    python verify-lab/frame/reconcile.py --missing  # frame units V11 never judged
    python verify-lab/frame/reconcile.py --extra    # V11/negctl entries outside the frame

**This module reads paths only.** It never opens `KNOWN_GAPS.json`'s `verdict`
field and never runs `criterion.py`. That is load-bearing: the manual judging of
the difference set had to happen without any exposure to the probe's answers, and
the difference set is computed here.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Dict, List, Optional, Sequence, Set, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import frame  # noqa: E402

REPO = frame.REPO
CENSUS = os.path.join(
    REPO, "verify-lab", "runs", "20260728T152000Z-V11-negative-control-census",
    "CENSUS_TABLE.md")
PIN = os.path.join(REPO, "verify-lab", "negctl", "KNOWN_GAPS.json")


def census_rows() -> List[Dict[str, object]]:
    """The 127 rows of V11 section 1, with the paths each row names.

    One row (`engine-rig/bench/verify.py`) carries pipes inside a cell, so the
    split is on the first six separators and the remainder is the evidence cell.
    """
    rows: List[Dict[str, object]] = []
    started = False
    for line in open(CENSUS, encoding="utf-8"):
        if not line.startswith("| "):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) > 7:
            cells = cells[:6] + ["|".join(cells[6:])]
        if len(cells) != 7:
            continue
        if cells[0] in ("领地",) or set(cells[0]) <= set("-"):
            started = True
            continue
        if not started:
            continue
        if cells[1].startswith("入口") or cells[1] == "入口数":
            continue
        paths = re.findall(r"`([^`]+)`", cells[1])
        rows.append({
            "territory": cells[0], "entry": cells[1], "paths": paths,
            "can_red": cells[2], "has_negctl": cells[3],
            "exit_honest": cells[4], "strength": cells[5],
        })
    return rows


def _clean(token: str) -> str:
    """`worldgen/build.py --check` -> `worldgen/build.py`; strip line numbers."""
    tok = token.split()[0]
    tok = tok.split("::")[0]
    tok = re.sub(r":\d+(-\d+)?$", "", tok)
    return tok.replace("\\", "/")


def census_paths(rows: Sequence[Dict[str, object]],
                 frame_paths: Set[str]) -> Tuple[Set[str], List[Dict[str, object]]]:
    """Frame paths a census row names, and the rows that name none."""
    hit: Set[str] = set()
    unresolved: List[Dict[str, object]] = []
    for row in rows:
        mine = {_clean(p) for p in row["paths"]}
        mine = {p for p in mine if p in frame_paths}
        if not mine:
            mine = _suite_row(row, frame_paths)
        if mine:
            hit |= mine
        else:
            unresolved.append(row)
    return hit, unresolved


def _suite_row(row: Dict[str, object], frame_paths: Set[str]) -> Set[str]:
    """`engine-rig` `python -m pytest` -> the stratum-C unit `engine-rig/tests`.

    12 of V11's 127 rows name a *suite* and no file. They are population members
    -- `verify.sh` steps read their exit codes -- so they are matched rather than
    counted as unresolved, and the match is written here in the open so a reader
    can see it is a lookup and not a judgement.
    """
    cell = str(row["entry"])
    if "pytest" not in cell:
        return set()
    out: Set[str] = set()
    words = [w for token in row["paths"] for w in str(token).split()]
    for word in words:
        tok = _clean(word)
        for candidate in (tok, tok + "/tests", tok.split("/")[0] + "/tests"):
            if candidate in frame_paths:
                out.add(candidate)
    return out


def pin_paths() -> List[str]:
    """Paths only. The `verdict` field is deliberately not read."""
    with open(PIN, encoding="utf-8") as handle:
        return sorted(json.load(handle)["entries"].keys())


def report(root: str = REPO) -> Dict[str, object]:
    units = frame.build(root)
    fpaths = {u["path"] for u in units}
    rows = census_rows()
    v11_hit, v11_unresolved = census_paths(rows, fpaths)
    pinned = pin_paths()
    pin_in = {p for p in pinned if p in fpaths}
    pin_out = [p for p in pinned if p not in fpaths]

    by_path = {u["path"]: u for u in units}
    missing = sorted(fpaths - v11_hit)

    # Coverage measured against V14's OWN membership rule, not V15's.
    #
    # "negctl covers 58% of the population" is true and rhetorically loaded: the
    # V15 frame is drawn deliberately wider than the rule negctl enumerates by,
    # so measuring the probe against it charges the probe for a population it
    # never claimed. Under V14's rule -- invocable, can fail, not frozen, no
    # stratum B, no stratum C -- the probe covers most of what it claims. Both
    # numbers are published; quoting only the first is the move this item exists
    # to criticise.
    v14_rule = {u["path"] for u in units
                if u["stratum"] == frame.STRATUM_A and u["can_refuse"]
                and not u["frozen"] and u["kind"] == "python"}
    pin_v14 = {p for p in pinned if p in v14_rule}
    v11_v14 = v11_hit & v14_rule

    return {
        "v14_rule_population": len(v14_rule),
        "negctl_coverage_of_v14_rule_pct":
            round(100.0 * len(pin_v14) / len(v14_rule), 1) if v14_rule else None,
        "v11_coverage_of_v14_rule_pct":
            round(100.0 * len(v11_v14) / len(v14_rule), 1) if v14_rule else None,
        "frame_total": len(units),
        "frame_counts": frame.counts(units),
        "v11_rows": len(rows),
        "v11_rows_naming_no_frame_path": len(v11_unresolved),
        "v11_frame_paths_covered": len(v11_hit),
        "v11_coverage_pct": round(100.0 * len(v11_hit) / len(units), 1),
        "negctl_pinned": len(pinned),
        "negctl_in_frame": len(pin_in),
        "negctl_outside_frame": len(pin_out),
        "negctl_coverage_pct": round(100.0 * len(pin_in) / len(units), 1),
        "difference_set": len(missing),
        "difference_set_paths": missing,
        "difference_by_stratum": {
            s: sum(1 for p in missing if by_path[p]["stratum"] == s)
            for s in ("A", "B")},
        "negctl_outside_frame_paths": pin_out,
        "v11_unresolved_rows": [r["entry"] for r in v11_unresolved],
        "in_v11_not_in_negctl": sorted(v11_hit - set(pinned)),
        "in_negctl_not_in_v11": sorted(pin_in - v11_hit),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=REPO)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--missing", action="store_true")
    ap.add_argument("--extra", action="store_true")
    args = ap.parse_args(argv)

    rep = report(args.root)
    if args.missing:
        for p in rep["difference_set_paths"]:
            print(p)
        return 0
    if args.extra:
        for p in rep["negctl_outside_frame_paths"]:
            print(p)
        return 0
    if args.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    print("frame                       %3d units" % rep["frame_total"])
    print("V11 census                  %3d rows -> %d frame units (%.1f%%)"
          % (rep["v11_rows"], rep["v11_frame_paths_covered"], rep["v11_coverage_pct"]))
    print("  rows naming no frame unit %3d" % rep["v11_rows_naming_no_frame_path"])
    print("negctl pin                  %3d paths -> %d in frame (%.1f%%), %d outside"
          % (rep["negctl_pinned"], rep["negctl_in_frame"],
             rep["negctl_coverage_pct"], rep["negctl_outside_frame"]))
    print("  -- and against V14's OWN membership rule (%d units) --"
          % rep["v14_rule_population"])
    print("  negctl covers             %.1f%%   V11 covers %.1f%%"
          % (rep["negctl_coverage_of_v14_rule_pct"],
             rep["v11_coverage_of_v14_rule_pct"]))
    print("difference set (frame minus V11) %3d   (stratum A %d, stratum B %d)"
          % (rep["difference_set"], rep["difference_by_stratum"]["A"],
             rep["difference_by_stratum"]["B"]))
    print("in V11 but not pinned by negctl  %3d" % len(rep["in_v11_not_in_negctl"]))
    print("pinned by negctl but not in V11  %3d" % len(rep["in_negctl_not_in_v11"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
