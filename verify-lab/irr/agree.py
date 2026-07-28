"""Inter-rater agreement, before and against the criterion.

Six judges, none of whom saw the V11 or V15 verdicts, judged the same 22 entry
points from the same stripped tree. Three had V11's question verbatim and no
definition of `部分` (arm ``old``); three had `PARTIAL_CRITERION.md` (arm
``new``). Both arms also answered 能红, which the criterion says nothing about.

    python verify-lab/irr/agree.py --dir <judgements> --sample <sample.json>

**能红 is the placebo and the whole design rests on it.** If the `new` arm agrees
more on 有负控 *and* on 能红, the extra agreement is not the criterion: it is six
agents converging because three of them read the same document, and a document
that makes judges agree about a question it never addresses has not defined
anything. If agreement rises on 有负控 and not on 能红, the criterion did the
work. The criterion does couple the two columns slightly -- test D0 asks whether
E can refuse at all -- so a small placebo rise is expected and is reported rather
than argued away.

Two coefficients, because they answer different questions:

  ``po``      mean pairwise percent agreement over the 3 judge pairs. Raw and
              readable; inflated when one category dominates.
  ``kappa``   Fleiss' kappa, chance-corrected against the arm's own marginals.
              This is the number that punishes a criterion for winning agreement
              by emptying a cell: drain `部分` and the marginals concentrate, so
              expected agreement rises and kappa does not move.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Dict, List, Optional, Sequence, Tuple

CATS = ("是", "部分", "否")
ARMS = {"old": ("O1", "O2", "O3"), "new": ("N1", "N2", "N3")}


def read_table(path: str) -> Dict[str, Dict[str, str]]:
    """path -> {'can_red':..., 'has_negctl':..., 'reason':...} from a judge file."""
    out: Dict[str, Dict[str, str]] = {}
    for line in open(path, encoding="utf-8"):
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4 or set(cells[0]) <= set("-"):
            continue
        rel = cells[0].strip().strip("`").split()[0]
        if not (rel.endswith(".py") or rel.endswith(".sh")) or "/" not in rel:
            continue
        red = _head(cells[1])
        neg = _head(cells[2])
        if red not in CATS or neg not in CATS:
            continue
        reason = cells[3].strip() if len(cells) > 4 else ""
        out[rel] = {"can_red": red, "has_negctl": neg,
                    "reason": reason if re.match(r"^(D[0-3]|C|—|-)$", reason) else ""}
    return out


def _head(cell: str) -> str:
    return cell.replace("*", "").replace("`", "").split("(")[0].split("（")[0].strip()


def _pairwise(cols: Sequence[Sequence[str]]) -> float:
    """Mean percent agreement over all judge pairs. `cols[i]` = judge i's column."""
    n = len(cols)
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    if not pairs or not cols[0]:
        return float("nan")
    total = 0.0
    for i, j in pairs:
        hit = sum(1 for a, b in zip(cols[i], cols[j]) if a == b)
        total += hit / len(cols[i])
    return total / len(pairs)


def _fleiss(cols: Sequence[Sequence[str]]) -> Optional[float]:
    """Fleiss' kappa for a fixed panel of `n` raters over `N` items."""
    n = len(cols)
    if n < 2 or not cols[0]:
        return None
    items = len(cols[0])
    counts = []
    for k in range(items):
        row = [sum(1 for c in cols if c[k] == cat) for cat in CATS]
        counts.append(row)
    p_j = [sum(row[c] for row in counts) / (items * n) for c in range(len(CATS))]
    p_i = [(sum(v * v for v in row) - n) / (n * (n - 1)) for row in counts]
    p_bar = sum(p_i) / items
    p_e = sum(p * p for p in p_j)
    if abs(1 - p_e) < 1e-12:
        return None
    return (p_bar - p_e) / (1 - p_e)


def score(tables: Dict[str, Dict[str, Dict[str, str]]], judges: Sequence[str],
          paths: Sequence[str], field: str) -> Dict[str, object]:
    cols = [[tables[j][p][field] for p in paths] for j in judges]
    dist: Dict[str, int] = {c: 0 for c in CATS}
    for col in cols:
        for v in col:
            dist[v] += 1
    unanimous = sum(1 for k in range(len(paths))
                    if len({col[k] for col in cols}) == 1)
    return {
        "n_items": len(paths),
        "po": round(_pairwise(cols), 3),
        "kappa": (None if _fleiss(cols) is None else round(_fleiss(cols), 3)),
        "unanimous": unanimous,
        "unanimous_pct": round(unanimous / len(paths), 3) if paths else None,
        "distribution": dist,
    }


def run(dirpath: str, sample: str) -> Dict[str, object]:
    blob = json.load(open(sample, encoding="utf-8"))
    rows = blob["rows"]
    stratum = {r["path"]: r["stratum"] for r in rows}
    v15 = {r["path"]: r["v15_negctl"] for r in rows}
    all_paths = sorted(stratum)
    partial_paths = sorted(p for p in all_paths if stratum[p] == "partial")

    tables: Dict[str, Dict[str, Dict[str, str]]] = {}
    missing: List[str] = []
    for arm, judges in ARMS.items():
        for judge in judges:
            path = os.path.join(dirpath, judge + ".md")
            if not os.path.exists(path):
                missing.append(judge)
                continue
            tables[judge] = read_table(path)
    if missing:
        return {"missing_judges": missing}

    incomplete = {j: sorted(set(all_paths) - set(t))
                  for j, t in tables.items() if set(all_paths) - set(t)}

    rep: Dict[str, object] = {
        "sample_n": len(all_paths), "partial_n": len(partial_paths),
        "incomplete_judges": incomplete,
    }
    for arm, judges in ARMS.items():
        rep[arm] = {
            "judges": list(judges),
            "has_negctl_all": score(tables, judges, all_paths, "has_negctl"),
            "has_negctl_partial_stratum": score(tables, judges, partial_paths,
                                                "has_negctl"),
            "can_red_all_PLACEBO": score(tables, judges, all_paths, "can_red"),
        }

    # Re-judgement outcome: what the new arm's majority says about the 14 rows
    # V15 called `部分`, and how often that differs from V15.
    changed: List[Dict[str, object]] = []
    for path in partial_paths:
        votes = [tables[j][path]["has_negctl"] for j in ARMS["new"]]
        top = max(CATS, key=lambda c: (votes.count(c), -CATS.index(c)))
        changed.append({
            "path": path, "v15": v15[path], "new_majority": top,
            "votes": votes, "split": len(set(votes)) > 1,
            "changed": top != v15[path],
        })
    rep["rejudgement"] = {
        "rows": changed,
        "n": len(changed),
        "changed": sum(1 for c in changed if c["changed"]),
        "change_rate": round(sum(1 for c in changed if c["changed"]) / len(changed), 3)
        if changed else None,
        "split_panels": sum(1 for c in changed if c["split"]),
    }

    # Where did the drained `部分` rows land, and did they carry a reason code?
    reasons: Dict[str, int] = {}
    for judge in ARMS["new"]:
        for path in all_paths:
            code = tables[judge][path].get("reason") or "(none)"
            reasons[code] = reasons.get(code, 0) + 1
    rep["reason_codes_new_arm"] = reasons
    rep["per_row"] = {
        p: {j: tables[j][p]["has_negctl"] for j in list(ARMS["old"]) + list(ARMS["new"])}
        for p in all_paths}
    return rep


def _fmt(tag: str, blob: Dict[str, object]) -> str:
    return ("  %-34s n=%-3d  po=%.3f  kappa=%s  unanimous %d/%d  %s"
            % (tag, blob["n_items"], blob["po"],
               "n/a" if blob["kappa"] is None else "%.3f" % blob["kappa"],
               blob["unanimous"], blob["n_items"], blob["distribution"]))


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--sample", required=True)
    ap.add_argument("--json", metavar="OUT")
    args = ap.parse_args(argv)
    rep = run(args.dir, args.sample)
    if "missing_judges" in rep:
        print("missing judge files: %s" % ", ".join(rep["missing_judges"]))  # type: ignore[arg-type]
        return 1
    if rep["incomplete_judges"]:
        print("INCOMPLETE: %s" % json.dumps(rep["incomplete_judges"], ensure_ascii=False))
    for arm in ("old", "new"):
        blob = rep[arm]
        print("-- arm %s  (%s)" % (arm, ", ".join(blob["judges"])))  # type: ignore[index]
        print(_fmt("有负控, all 22", blob["has_negctl_all"]))        # type: ignore[index]
        print(_fmt("有负控, 部分 stratum", blob["has_negctl_partial_stratum"]))  # type: ignore[index]
        print(_fmt("能红 (PLACEBO)", blob["can_red_all_PLACEBO"]))   # type: ignore[index]
    rj = rep["rejudgement"]
    print("-- re-judgement of the %d rows V15 graded 部分" % rj["n"])  # type: ignore[index]
    print("   changed %d (%.0f%%), split panels %d"
          % (rj["changed"], 100 * rj["change_rate"], rj["split_panels"]))  # type: ignore[index]
    for row in rj["rows"]:  # type: ignore[index]
        print("   %-58s %s -> %-4s %s%s"
              % (row["path"], row["v15"], row["new_majority"],
                 "/".join(row["votes"]), "  SPLIT" if row["split"] else ""))
    print("-- reason codes, new arm: %s"
          % json.dumps(rep["reason_codes_new_arm"], ensure_ascii=False))
    if args.json:
        with open(args.json, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(rep, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
