"""The 22 rows re-judged in V17, and why each one is in.

Re-judging only the `部分` rows would answer the wrong question. If a criterion
is allowed to move rows *out* of `部分` and nothing is ever allowed to move *in*,
any criterion whatsoever improves agreement, because agreement on an empty cell
is trivially perfect. The V17 work order names that failure mode explicitly:
「不要为了让一致率好看，把「部分」定义成一个几乎没人会选的窄格」.

So the sample is stratified, and the two control strata are the point:

  ``partial``   14 rows the V15 judges graded `部分`. Ten of them are the ten
                `部分` rows that carry a pinned false negative -- the rows the
                whole V15 headline rests on. All ten are in.
  ``present``   4 rows graded `是`. If the criterion is sound these should
                mostly stay `是`; if some fall to `部分`, the cell is being fed
                as well as drained, which is the only honest way for it to stay
                narrow.
  ``absent``    4 rows graded `否`. Same test in the other direction.

Every row `PARTIAL_CRITERION.md` uses as a worked example is held out. A judge
who has read the criterion has been told those answers, and scoring a judge on an
example is scoring a lookup. The criterion works through **seven** rows: four are
V11 rows, which this sample never draws from, and three are V15 rows -- of which
`figures/fig02_bill_shape.py` is the one `部分` row excluded here, and
`cold-start-a3/a3pipeline/transfer.py` (是) and `cold-start-a2/a2pipeline/
ledger.py` (否) are barred from the control strata below.

    python verify-lab/irr/sample.py --json <out>
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, List, Optional, Sequence

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import rows as rowsmod  # noqa: E402

#: Held out: `PARTIAL_CRITERION.md` works this row through in full.
EXAMPLES = ("figures/fig02_bill_shape.py",)

#: Also worked through in the criterion, and so barred from the control strata:
#: `cold-start-a3/a3pipeline/transfer.py` (是) and
#: `cold-start-a2/a2pipeline/ledger.py` (否). The remaining four examples are V11
#: rows, which this sample never draws from.
PRESENT = (
    "monitor/quota.py",
    "cold-start-a0/certify/replay.py",
    "engine-rig/engines/fd_adapter/validate.py",
    "exam/model.py",
)

#: The `否` control stratum.
ABSENT = (
    "monitor/ci_merge.py",
    "cold-start-a0/pipeline/engines_stage.py",
    "engine-rig/fixtures/pair_flip.py",
    "papers/phase1-workshop/figures/fig2_coverage_accuracy.py",
)


def build() -> Dict[str, object]:
    v15 = {str(r["entry"]): r for r in rowsmod.v15_rows()}
    out: List[Dict[str, object]] = []
    for path, row in sorted(v15.items()):
        if row["has_negctl"] != "部分" or path in EXAMPLES:
            continue
        out.append({"path": path, "stratum": "partial", "batch": row["judge"],
                    "v15_negctl": row["has_negctl"], "v15_can_red": row["can_red"]})
    for stratum, paths in (("present", PRESENT), ("absent", ABSENT)):
        for path in paths:
            row = v15[path]
            out.append({"path": path, "stratum": stratum, "batch": row["judge"],
                        "v15_negctl": row["has_negctl"],
                        "v15_can_red": row["can_red"]})
    out.sort(key=lambda r: str(r["path"]))
    return {"rows": out, "n": len(out), "held_out_as_examples": list(EXAMPLES)}


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", metavar="OUT")
    ap.add_argument("--paths", action="store_true", help="paths only, no verdicts")
    args = ap.parse_args(argv)
    rep = build()
    if args.paths:
        for row in rep["rows"]:  # type: ignore[union-attr]
            print(row["path"])
        return 0
    for row in rep["rows"]:  # type: ignore[union-attr]
        print("%-9s %-8s %-4s %s" % (row["stratum"], row["batch"],
                                     row["v15_negctl"], row["path"]))
    print("n = %d" % rep["n"])
    if args.json:
        with open(args.json, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(rep, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
