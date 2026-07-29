"""How much of the answer key was in the blind judges' tree anyway.

The V15 supplement was judged by nine agents working from a `git archive` export
with `verify-lab/` deleted. `verify-lab/` is where the probe, its criterion, its
pin and both prior reports live, so the export removed every per-file verdict.

It did not remove `PARTNER_SYNC.md`. That file is tracked, sits at the repository
root, is in every checkout, and carries — by the repository's own delivery
discipline, one appended paragraph per finished item — V11's aggregate answer
(`有负控「否」35`), V14's headline (`FNR 32%`), and at least one per-file probe
verdict (`worldgen/build.py` 被判 present), which is the single false positive in
the pinned matrix.

This module measures the exposure instead of asserting it was harmless.

    python verify-lab/frame/leakage.py

Two populations are compared: judged paths whose name appears in a tracked
non-`verify-lab` text file that *also* discusses negative controls, and the rest.
If the leak steered the judges, the exposed group should look different.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
from typing import Dict, List, Optional, Sequence, Set, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import frame        # noqa: E402
import matrix       # noqa: E402

REPO = frame.REPO
SUPPLEMENT = os.path.join(REPO, "verify-lab", "SUPPLEMENT_TABLE.md")

#: A file discussing these is a file that could tell a judge what the answer is.
_TOPIC_WORDS = ("负控", "negative control", "negative-control", "FNR",
                "混淆矩阵", "confusion matrix", "KNOWN_GAPS", "有负控")

_TEXT_EXT = (".md", ".json", ".txt", ".jsonl")


def supplement_rows() -> List[Tuple[str, str]]:
    """(path, 有负控 cell) for every row of the V15 supplement."""
    out: List[Tuple[str, str]] = []
    for line in open(SUPPLEMENT, encoding="utf-8"):
        if not line.startswith("| "):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 6 or set(cells[0]) <= set("-") or cells[0] == "入口":
            continue
        out.append((cells[0].strip().strip("`").split()[0], cells[2]))
    return out


def leaky_files(root: str) -> Dict[str, str]:
    """Tracked, outside verify-lab, text, and discussing negative controls."""
    tracked = frame.tracked_files(root)
    out: Dict[str, str] = {}
    for rel in tracked:
        if rel.startswith("verify-lab/") or not rel.endswith(_TEXT_EXT):
            continue
        try:
            text = open(os.path.join(root, rel), "r", encoding="utf-8",
                        errors="replace").read()
        except OSError:
            continue
        if any(w in text for w in _TOPIC_WORDS):
            out[rel] = text
    return out


def _binom_tail(k: int, n: int, p: float) -> float:
    """P(X >= k) for X ~ Bin(n, p). One-sided, exact."""
    total = 0.0
    for i in range(k, n + 1):
        total += math.comb(n, i) * (p ** i) * ((1 - p) ** (n - i))
    return total


def run(root: str = REPO) -> Dict[str, object]:
    rows = supplement_rows()
    leaks = leaky_files(root)
    exposed: List[Tuple[str, str, List[str]]] = []
    clean: List[Tuple[str, str]] = []
    for path, cell in rows:
        where = sorted(rel for rel, text in leaks.items() if path in text)
        if where:
            exposed.append((path, cell, where))
        else:
            clean.append((path, cell))

    def present_rate(cells: Sequence[str]) -> Tuple[int, int, float]:
        pres = sum(1 for c in cells if matrix._fold(c) == matrix.PRESENT)
        n = sum(1 for c in cells if matrix._fold(c) != matrix.NA)
        return pres, n, (round(pres / n, 3) if n else 0.0)

    e_pres, e_n, e_rate = present_rate([c for _, c, _ in exposed])
    c_pres, c_n, c_rate = present_rate([c for _, c in clean])
    pool = (e_pres + c_pres) / (e_n + c_n) if (e_n + c_n) else 0.0

    sources: Dict[str, int] = {}
    for _, _, where in exposed:
        for rel in where:
            sources[rel] = sources.get(rel, 0) + 1

    return {
        "judged": len(rows),
        "exposed": len(exposed),
        "unexposed": len(clean),
        "exposed_present_rate": e_rate,
        "unexposed_present_rate": c_rate,
        "pool_present_rate": round(pool, 3),
        "p_one_sided": round(_binom_tail(e_pres, e_n, pool), 3),
        "top_sources": sorted(sources.items(), key=lambda kv: -kv[1])[:8],
        "exposed_paths": [(p, sorted(w)) for p, _, w in exposed],
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=REPO)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    rep = run(args.root)
    if args.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    print("judged paths                    %d" % rep["judged"])
    print("named in a tracked file that also discusses negative controls: %d (%.0f%%)"
          % (rep["exposed"], 100.0 * rep["exposed"] / rep["judged"]))
    print("  present rate, exposed         %.2f" % rep["exposed_present_rate"])
    print("  present rate, unexposed       %.2f" % rep["unexposed_present_rate"])
    print("  pool                          %.2f" % rep["pool_present_rate"])
    print("  one-sided binomial p          %.3f" % rep["p_one_sided"])
    print("top sources:")
    for rel, n in rep["top_sources"]:
        print("  %-56s %d" % (rel, n))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
