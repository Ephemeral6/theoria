"""Recompute negctl's confusion matrix on the supplemented gold standard.

V14 measured `criterion.py` against V11's census and got FP 3 / FN 20. That
matrix is computed over the 103 census rows naming a single Python file — 47% of
the frame. This recomputes it over V11's rows **plus** the V15 supplement, which
hand-judges the difference set, and reports the two side by side.

    python verify-lab/frame/matrix.py

Three restrictions are printed, because "the confusion matrix" is not one object:

  ``v14``   V11 gold only, rows naming a single existing ``.py``. This is the
            **closest approach** to V14's published numbers, not a reproduction:
            it agrees on TP 43 / FN 20 / FP 3 and disagrees on n (95 vs 97),
            TN (29 vs 31) and therefore FPR (0.094 vs 0.088).

            **The first version of this docstring set a tripwire — "if it does
            not land on FP 3 / FN 20 then every other number here is suspect" —
            over exactly the cells that agree.** A self-check written across the
            matching half of a result is not a self-check. The adversarial pass
            ran V14's own ``calibrate.py`` at this HEAD and found the gap. The
            tripwire now covers all four cells and is expected to *fail*, which
            is the honest state: see ``reproduction_gap()``.
  ``v15``   V11 gold + V15 supplement, same rule.
  ``pinned`` V11 gold + V15 supplement, restricted to files ``probe.py``
            actually enumerates -- the population the standing probe reports on.

Gold folding follows V14's ``strict``: ``部分`` counts as *has a negative
control*, which is the census's own reading. ``harsh`` (``部分`` counts as *has
none*) is printed alongside, because that is where the two definitions genuinely
diverge and neither folding is free.
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
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "negctl"))

import frame        # noqa: E402
import reconcile    # noqa: E402

REPO = frame.REPO
RUN = os.path.join(REPO, "verify-lab", "runs",
                   "20260729T120000Z-V15-census-sampling-frame")
SUPPLEMENT = os.path.join(REPO, "verify-lab", "SUPPLEMENT_TABLE.md")

PRESENT = "present"
ABSENT = "absent"
NA = "n/a"


def _fold(cell: str, harsh: bool = False) -> str:
    """V11's 有负控 cell -> present / absent / n/a."""
    head = cell.split("(")[0].split("（")[0].strip()
    if head.startswith("是"):
        return PRESENT
    if head.startswith("部分"):
        return ABSENT if harsh else PRESENT
    if head.startswith("否"):
        return ABSENT
    return NA


def gold_v11(root: str, harsh: bool = False) -> List[Tuple[str, str]]:
    """V14's in-scope rule, transcribed: one row, one existing ``.py``.

    Per **row**, not per file, and deliberately so. V14's matrix is row-scored,
    and 8 of its rows share a file with another row it judged differently --
    ``worldgen/build.py --check`` is 是 while ``worldgen/build.py::
    check_determinism`` is 否. Collapsing to one verdict per file silently
    resolves those conflicts and, when this module first did exactly that, the
    published FP of 3 became 0. Those 3 *are* the conflicts. A protocol that
    deletes the disagreement it is measuring reproduces the wrong number for a
    flattering reason, so the row is the unit here.
    """
    out: List[Tuple[str, str]] = []
    for row in reconcile.census_rows():
        verdict = _fold(str(row["has_negctl"]), harsh)
        if verdict == NA:
            continue
        py = sorted({reconcile._clean(p) for p in row["paths"]
                     if reconcile._clean(p).endswith(".py")
                     and os.path.exists(os.path.join(root, reconcile._clean(p)))})
        if len(py) != 1:
            continue
        if frame.is_test_file(py[0]):
            # V14's scope rule, transcribed. `CALIBRATION.md` line 29 declares
            # it independently and before V15 existed: out of scope = "4 shell
            # entry points ... and 4 rows whose 'entry point' is itself a test
            # file". Those 4 rows are exactly `fuzzlab/tests/test_battery.py`
            # (x2), `fuzzlab/tests/test_oracles.py`, `theory-compiler/
            # conftest.py`.
            #
            # An earlier version of this comment justified the rule by the
            # number it produced ("dropping them puts FN at 20, which is V14's
            # published number"). That reads as fitting even though it is not,
            # and the adversarial pass had to go and check the citation to clear
            # it. Justify a rule by its source, never by its result: keeping the
            # rows gives n=99, TP 43 / FN 22 / FP 3 / TN 31 -- which recovers
            # V14's TN and loses its FN, so no setting of this switch reproduces
            # V14 cell-for-cell either way.
            continue
        out.append((py[0], verdict))
    return out


def gold_v15(frame_paths: Set[str], harsh: bool = False,
             path: str = SUPPLEMENT) -> List[Tuple[str, str]]:
    """The V15 supplement's 有负控 column, same folding, one row per file."""
    out: List[Tuple[str, str]] = []
    if not os.path.exists(path):
        return out
    for line in open(path, encoding="utf-8"):
        if not line.startswith("| "):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 6 or set(cells[0]) <= set("-"):
            continue
        rel = cells[0].strip().strip("`").split()[0]
        if rel not in frame_paths or not rel.endswith(".py"):
            continue
        verdict = _fold(cells[2], harsh)
        if verdict != NA:
            out.append((rel, verdict))
    return out


def measured(root: str = REPO, detector: str = "A-B") -> Tuple[Dict[str, str], Set[str]]:
    """`criterion.py`'s verdict per path, and what `probe.py` enumerates."""
    import criterion  # noqa: E402
    import probe      # noqa: E402
    index = criterion.Index.build(root)
    verdicts = criterion.Verdicts(
        a=criterion.scan_tests(index, absence=True),
        a_strict=criterion.scan_tests(index, absence=False),
        b=criterion.scan_selftests(index),
        naive=criterion.scan_naive(index))
    enumerated = set(probe.enumerate_entry_points(index))
    universe = set(index.files) | enumerated
    return ({rel: verdicts.verdict(rel, detector) for rel in universe},
            enumerated)


def confusion(gold: Sequence[Tuple[str, str]], meas: Dict[str, str],
              restrict: Optional[Set[str]] = None) -> Dict[str, object]:
    tp = fn = fp = tn = 0
    fp_paths: List[str] = []
    fn_paths: List[str] = []
    scored: List[str] = []
    for path, want in sorted(gold):
        if restrict is not None and path not in restrict:
            continue
        got = meas.get(path)
        if got is None:
            continue
        scored.append(path)
        if want == PRESENT and got == PRESENT:
            tp += 1
        elif want == PRESENT and got == ABSENT:
            fn += 1
            fn_paths.append(path)
        elif want == ABSENT and got == PRESENT:
            fp += 1
            fp_paths.append(path)
        else:
            tn += 1
    gold_pos = tp + fn
    gold_neg = fp + tn
    return {
        "n": len(scored), "TP": tp, "FN": fn, "FP": fp, "TN": tn,
        "FNR": round(fn / gold_pos, 3) if gold_pos else None,
        "FPR": round(fp / gold_neg, 3) if gold_neg else None,
        "FP_paths": fp_paths, "FN_paths": fn_paths,
    }


def _fmt(name: str, m: Dict[str, object]) -> str:
    return ("%-28s n=%-4d TP %-3d FN %-3d FP %-3d TN %-3d  FNR %-6s FPR %-6s"
            % (name, m["n"], m["TP"], m["FN"], m["FP"], m["TN"],
               m["FNR"], m["FPR"]))


def run(root: str = REPO) -> Dict[str, object]:
    units = frame.build(root)
    fpaths = {u["path"] for u in units}
    meas, enumerated = measured(root)

    out: Dict[str, object] = {"detector": "A-B",
                              "frame_total": len(units),
                              "enumerated_by_probe": len(enumerated)}
    for harsh in (False, True):
        tag = "harsh" if harsh else "strict"
        g11 = gold_v11(root, harsh)
        g15 = [(p, v) for p, v in gold_v15(fpaths, harsh)
               if p not in {q for q, _ in g11}]
        merged = g11 + g15
        out[tag] = {
            "gold_v11": len(g11), "gold_v15_new": len(g15),
            "v14": confusion(g11, meas),
            "v15": confusion(merged, meas),
            "pinned": confusion(merged, meas, restrict=enumerated),
            "pinned_v11_only": confusion(g11, meas, restrict=enumerated),
        }
    return out


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=REPO)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--sensitivity", action="store_true",
                    help="the same gold standard under four membership rules")
    ap.add_argument("--reproduction", action="store_true",
                    help="every cell of the v14 row against V14's published "
                         "numbers, including the cells that do not match")
    args = ap.parse_args(argv)
    if args.reproduction:
        print(json.dumps(reproduction_gap(args.root), ensure_ascii=False,
                         indent=2, sort_keys=True))
        return 0
    if args.sensitivity:
        for name, m in sensitivity(args.root):
            print(_fmt(name, m))
        return 0
    rep = run(args.root)
    if args.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    print("frame %d units; probe enumerates %d"
          % (rep["frame_total"], rep["enumerated_by_probe"]))
    for tag in ("strict", "harsh"):
        blob = rep[tag]
        print("\n-- gold folding: %s   (V11 %d files, V15 adds %d) --"
              % (tag, blob["gold_v11"], blob["gold_v15_new"]))
        print(_fmt("V11 gold only (V14 repro)", blob["v14"]))
        print(_fmt("V11+V15 gold", blob["v15"]))
        print(_fmt("V11 gold, probe-enumerated", blob["pinned_v11_only"]))
        print(_fmt("V11+V15 gold, enumerated", blob["pinned"]))
    return 0


#: V14's published A-B strict/harsh cells, from CALIBRATION.md section 2.
V14_PUBLISHED = {"strict": {"n": 97, "TP": 43, "FN": 20, "FP": 3, "TN": 31},
                 "harsh": {"n": 97, "TP": 34, "FN": 12, "FP": 12, "TN": 39}}

#: The two census rows V15 drops and V14 kept: each names two existing .py files,
#: and `gold_v11` requires exactly one. Named here so the gap is attributable
#: rather than mysterious.
V14_ROWS_DROPPED = (
    ("theoria-arm/armtools/salvage.py", "theoria-arm/armtools/timeline.py",
     "gold 否, both measured absent -- these are the 2 missing TN"),
    ("proxy/canon.py", "proxy/ledger.py",
     "gold 是(实测), both measured present"),
)


def reproduction_gap(root: str = REPO) -> Dict[str, Dict[str, object]]:
    """Every cell of the `v14` row against V14's published numbers.

    Deliberately reports a gap rather than asserting agreement. Three cells
    match and two do not, and no setting of this module's two protocol switches
    reproduces V14 cell-for-cell: keeping the 4 test-file rows recovers TN 31
    and loses FN 20 (n=99, FN 22). The FP 3 / FN 20 landing is two protocol
    differences partially cancelling.
    """
    out: Dict[str, Dict[str, object]] = {}
    for tag, harsh in (("strict", False), ("harsh", True)):
        mine = confusion(gold_v11(root, harsh), measured(root)[0])
        want = V14_PUBLISHED[tag]
        out[tag] = {
            "cells_agreeing": sorted(k for k in want if mine[k] == want[k]),
            "cells_differing": {k: {"v15": mine[k], "v14": want[k]}
                                for k in want if mine[k] != want[k]},
            "rows_v15_drops": [list(r) for r in V14_ROWS_DROPPED],
        }
    return out


def sensitivity(root: str = REPO) -> List[Tuple[str, Dict[str, object]]]:
    """The same gold standard under four membership rules, strictest last.

    "Did you draw the frame to make the numbers look good" is the right question
    to ask of this item, so it is answered with a measurement rather than a
    paragraph. Swapping membership for progressively stricter rules -- including
    V14's own (`can_refuse` required) -- moves FNR between 0.369 and 0.507 and
    never below V14's published 0.318. The conclusion does not rest on where
    V15 drew the line; it rests on the gold standard going from 43% of the
    population to 90%.

    FPR *does* move with the denominator, and in the direction that flatters
    V15's frame, so the false-positive number to quote is the strictest row.
    """
    units = frame.build(root)
    fpaths = {u["path"] for u in units}
    can_red = {u["path"] for u in units if u["can_refuse"]}
    stratum_a = {u["path"] for u in units if u["stratum"] == frame.STRATUM_A}
    meas, enumerated = measured(root)
    g11 = gold_v11(root)
    seen = {p for p, _ in g11}
    merged = g11 + [(p, v) for p, v in gold_v15(fpaths) if p not in seen]
    return [
        ("full frame (V15's definition)", confusion(merged, meas)),
        ("can_refuse only (V14's own rule)", confusion(merged, meas, can_red)),
        ("stratum A only", confusion(merged, meas, stratum_a)),
        ("stratum A and can_refuse", confusion(merged, meas, stratum_a & can_red)),
        ("what probe.py enumerates", confusion(merged, meas, enumerated)),
    ]


if __name__ == "__main__":
    raise SystemExit(main())
