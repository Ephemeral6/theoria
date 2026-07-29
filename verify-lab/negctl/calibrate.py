"""Measure the mechanical criterion against V11's 127 hand judgements.

The census auditors' ``有负控`` column is the gold standard. It is not perfect —
it is six people reading code — but it is the only independent answer that
exists, and it was produced before this criterion was written, which is the
property that matters.

Usage::

    python -m verify_lab_negctl.calibrate            # from verify-lab/
    python verify-lab/negctl/calibrate.py --json     # from the repo root

Everything is derived from `CENSUS_TABLE.md` §1 by parsing the table. Nothing is
transcribed by hand, so the gold standard cannot drift away from the document it
claims to come from.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
VERIFY_LAB = os.path.dirname(HERE)
REPO = os.path.dirname(VERIFY_LAB)

sys.path.insert(0, HERE)
import criterion  # noqa: E402

CENSUS = os.path.join(
    VERIFY_LAB, "runs", "20260728T152000Z-V11-negative-control-census",
    "CENSUS_TABLE.md")

YES, PARTIAL, NO, NA = "yes", "partial", "no", "n/a"

_GOLD = {"是": YES, "部分": PARTIAL, "否": NO, "不适用": NA, "—": NA}


def parse_census(path: str = CENSUS) -> List[Dict[str, str]]:
    """§1 of the census table, one dict per row. 7 columns, evidence may hold `|`."""
    rows: List[Dict[str, str]] = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            if not line.startswith("| "):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 7:
                continue           # the §2 sub-total table, 6 wide
            if len(cells) > 7:     # a pipe inside the evidence cell
                cells = cells[:6] + ["|".join(cells[6:])]
            if cells[0] in ("领地",) or set(cells[0]) <= set("- "):
                continue
            rows.append({
                "territory": cells[0], "entry": cells[1], "can_fail": cells[2],
                "has_negctl": cells[3], "exit_honest": cells[4],
                "strength": cells[5], "evidence": cells[6],
            })
    return rows


def gold_of(cell: str) -> str:
    """The 有负控 cell -> yes / partial / no / n/a."""
    for token, value in _GOLD.items():
        if cell.startswith(token):
            return value
    return NA


_PATH = re.compile(r"^([A-Za-z0-9_./-]+\.(?:py|sh))")


def entry_path(entry: str, repo: str = REPO) -> Optional[str]:
    """First backticked token in the 入口 cell that names a file that exists."""
    for tick in re.findall(r"`([^`]+)`", entry):
        m = _PATH.match(tick)
        if not m:
            continue
        rel = m.group(1)
        if os.path.exists(os.path.join(repo, rel)):
            return rel
    return None


def build(repo: str = REPO) -> Dict[str, object]:
    rows = parse_census()
    index, verdicts = criterion.evaluate(repo)

    resolved, unresolvable, out_of_scope = [], [], []
    for row in rows:
        rel = entry_path(row["entry"], repo)
        gold = gold_of(row["has_negctl"])
        rec = dict(row, path=rel, gold=gold)
        if rel is None:
            # A pytest suite, a glob, or a gate that does not exist. There is no
            # single file to ask the question of.
            unresolvable.append(rec)
            continue
        if not rel.endswith(".py"):
            rec["why_out_of_scope"] = "shell entry point; this criterion parses Python"
            out_of_scope.append(rec)
            continue
        if criterion.is_test_file(rel):
            rec["why_out_of_scope"] = "the entry point is itself a test file"
            out_of_scope.append(rec)
            continue
        for det in criterion.DETECTORS:
            rec[det] = verdicts.verdict(rel, det)
        rec["evidence"] = [h.as_dict() for h in verdicts.evidence(rel, "AB")][:4]
        resolved.append(rec)

    # Rows that name the same file twice with different verdicts. The criterion
    # is file-granular and the census is function-granular; where they disagree
    # with themselves, no file-granular criterion can be right about both.
    by_path: Dict[str, set] = {}
    for row in resolved:
        by_path.setdefault(row["path"], set()).add(row["gold"])
    collapsed = sorted(p for p, g in by_path.items() if len(g) > 1)
    for row in resolved:
        row["granularity_conflict"] = row["path"] in collapsed

    clean = [r for r in resolved if not r["granularity_conflict"]]

    return {
        "rows_total": len(rows),
        "resolved": resolved,
        "unresolvable": unresolvable,
        "out_of_scope": out_of_scope,
        "granularity_conflicts": collapsed,
        "matrices": {d: matrix(resolved, d) for d in criterion.DETECTORS},
        "matrices_no_granularity_conflict":
            {d: matrix(clean, d) for d in criterion.DETECTORS},
    }


def matrix(resolved: List[Dict[str, object]], detector: str) -> Dict[str, object]:
    """Confusion matrix, on the rows whose gold verdict is yes / partial / no.

    Two binarisations, because `partial` is a real answer and folding it either
    way is a choice, not a fact:

    * ``strict``  -- partial counts as *has* a negative control (the census's own
      reading: `部分` means some executable demonstration exists, just not for
      every branch).
    * ``harsh``   -- partial counts as *lacks* one.
    """
    cells = {"yes": {"present": 0, "absent": 0},
             "partial": {"present": 0, "absent": 0},
             "no": {"present": 0, "absent": 0}}
    for row in resolved:
        gold = row["gold"]
        if gold == NA:
            continue
        cells[gold][row[detector]] += 1

    def binar(positive_golds: Tuple[str, ...]) -> Dict[str, object]:
        tp = sum(cells[g]["present"] for g in positive_golds)
        fn = sum(cells[g]["absent"] for g in positive_golds)
        neg = [g for g in ("yes", "partial", "no") if g not in positive_golds]
        fp = sum(cells[g]["present"] for g in neg)
        tn = sum(cells[g]["absent"] for g in neg)
        total = tp + fn + fp + tn
        return {
            "TP": tp, "FN": fn, "FP": fp, "TN": tn, "n": total,
            "false_positive_rate": round(fp / (fp + tn), 4) if (fp + tn) else None,
            "false_negative_rate": round(fn / (fn + tp), 4) if (fn + tp) else None,
            "precision": round(tp / (tp + fp), 4) if (tp + fp) else None,
            "recall": round(tp / (tp + fn), 4) if (tp + fn) else None,
            "accuracy": round((tp + tn) / total, 4) if total else None,
        }

    return {
        "three_way": cells,
        "strict": binar(("yes", "partial")),
        "harsh": binar(("yes",)),
    }


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("--detector", default="AB")
    ap.add_argument("--disagreements", action="store_true",
                    help="list every row where the criterion and the census differ")
    args = ap.parse_args(argv)

    report = build(args.repo)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    print("census rows: %d   in scope: %d   out of scope: %d   unresolvable: %d"
          % (report["rows_total"], len(report["resolved"]),
             len(report["out_of_scope"]), len(report["unresolvable"])))
    print("rows whose file is shared with a differently-judged row: %d (%s)"
          % (len(report["granularity_conflicts"]),
             ", ".join(report["granularity_conflicts"])))
    for det in criterion.DETECTORS:
        m = report["matrices"][det]
        s, h = m["strict"], m["harsh"]
        print("\ndetector %s" % det)
        print("  three-way (gold -> predicted):")
        for g in ("yes", "partial", "no"):
            print("    %-8s present=%-3d absent=%-3d" % (g, m["three_way"][g]["present"],
                                                         m["three_way"][g]["absent"]))
        c = report["matrices_no_granularity_conflict"][det]
        for label, b in (("strict (partial=has)   ", s), ("harsh  (partial=lacks) ", h),
                         ("strict, no file shared ", c["strict"])):
            print("  %s: TP=%d FN=%d FP=%d TN=%d  FPR=%s FNR=%s prec=%s acc=%s"
                  % (label, b["TP"], b["FN"], b["FP"], b["TN"],
                     b["false_positive_rate"], b["false_negative_rate"],
                     b["precision"], b["accuracy"]))

    if args.disagreements:
        det = args.detector
        print("\n--- disagreements under detector %s ---" % det)
        for row in report["resolved"]:
            if row["gold"] == NA:
                continue
            pred = row[det]
            agree = (pred == "present") == (row["gold"] in (YES, PARTIAL))
            if agree:
                continue
            kind = "FALSE POSITIVE" if pred == "present" else "FALSE NEGATIVE"
            print("%-15s %-55s gold=%-8s" % (kind, row["path"], row["gold"]))
            for h in row["evidence"][:2]:
                print("      via %s::%s:%s  (%s)"
                      % (h["test_file"], h["test_func"], h["lineno"], h["why"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
