"""Has any acceptance entry point in this lab ever been judged twice?

Inter-rater reliability needs rows two judges both answered. V11 partitioned the
repository into six territories and V15 built its 126 rows as the frame *minus*
V11's paths, so the two censuses were designed to be disjoint and the six
auditors were designed not to meet. Whether that leaves literally zero overlap is
a fact about the tables, not an assumption, so it is measured here.

    python verify-lab/irr/overlap.py
    python verify-lab/irr/overlap.py --json <out>

Output distinguishes three things that get conflated:

  inter-judge overlap    same path, two different judges  -> reliability evidence
  intra-judge repeat     same path, same judge, two rows  -> granularity, not
                         reliability (V11 scores per row, and deliberately: see
                         ``matrix.py::gold_v11``)
  no overlap             the gold standard has never been checked against itself
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


def index(corpus: Sequence[Dict[str, object]]) -> Dict[str, List[Dict[str, object]]]:
    """path -> the rows naming it. A multi-path row is indexed under each."""
    out: Dict[str, List[Dict[str, object]]] = {}
    for row in corpus:
        for path in set(str(p) for p in row["paths"]):  # type: ignore[arg-type]
            if not (path.endswith(".py") or path.endswith(".sh")):
                continue
            out.setdefault(path, []).append(row)
    return out


def report(corpus: Optional[Sequence[Dict[str, object]]] = None) -> Dict[str, object]:
    corpus = list(corpus if corpus is not None else rowsmod.corpus())
    idx = index(corpus)
    inter: List[Dict[str, object]] = []
    intra: List[Dict[str, object]] = []
    for path, hits in sorted(idx.items()):
        judges = sorted({str(h["judge"]) for h in hits})
        if len(judges) > 1:
            bucket, key = inter, judges
        elif len(hits) > 1:
            bucket, key = intra, judges
        else:
            continue
        bucket.append({
            "path": path,
            "judges": key,
            "verdicts": [{"judge": str(h["judge"]), "census": str(h["census"]),
                          "entry": str(h["entry"]),
                          "can_red": str(h["can_red"]),
                          "has_negctl": str(h["has_negctl"]),
                          "exit_honest": str(h["exit_honest"])}
                         for h in hits],
            "agree_negctl": len({str(h["has_negctl"]) for h in hits}) == 1,
        })
    return {
        "rows": len(corpus),
        "judges": sorted({str(r["judge"]) for r in corpus}),
        "paths_indexed": len(idx),
        "inter_judge_overlap": inter,
        "intra_judge_repeat": intra,
        "n_inter": len(inter),
        "n_intra": len(intra),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", metavar="OUT")
    args = ap.parse_args(argv)
    rep = report()
    print("corpus            %d rows, %d judges, %d distinct .py/.sh paths"
          % (rep["rows"], len(rep["judges"]), rep["paths_indexed"]))
    print("inter-judge overlap  %d paths" % rep["n_inter"])
    for item in rep["inter_judge_overlap"]:  # type: ignore[union-attr]
        print("   %-60s %s  agree(有负控)=%s"
              % (item["path"], ",".join(item["judges"]), item["agree_negctl"]))
    print("intra-judge repeat   %d paths" % rep["n_intra"])
    for item in rep["intra_judge_repeat"]:  # type: ignore[union-attr]
        cells = [v["has_negctl"] for v in item["verdicts"]]
        print("   %-60s %s  %s" % (item["path"], item["judges"][0], "/".join(cells)))
    if rep["n_inter"] == 0:
        print()
        print("NO INTER-JUDGE OVERLAP.  Neither census ever put two judges on one")
        print("entry point, so no reliability coefficient can be computed from the")
        print("253 published rows. That is a property of the design, not a bug in")
        print("this reader: V11 partitioned by territory, V15 took the complement.")
    if args.json:
        with open(args.json, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(rep, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
