"""Run every E18 recomputation and write one JSON per number.

    cd engine-rig
    python -m tools.survey_numbers.run_all --out runs/<id>/counts
    python -m tools.survey_numbers.run_all --out runs/<id>/counts --check

`--check` re-runs everything and compares against what is already on disk.  It
is the determinism rung: a recomputation that gives a different answer on a
second run is not evidence either, it is just a fresher kind of prose.

What this driver does **not** do is fail because a recomputed number disagrees
with the E11 report.  Disagreement is the finding.  The recomputed value is the
number of record and the prose is the thing under suspicion, so the driver
prints the disagreement loudly and exits 0.  It exits non-zero only when a
script errors, when a rerun drifts, or when `--check` finds a number on disk
that no script produces any more.
"""

from __future__ import annotations

import argparse
import importlib
import json
import pkgutil
import sys
import traceback
from pathlib import Path

from . import _common

PACKAGE = "tools.survey_numbers"

# Modules that are plumbing, not a number.
SKIP = {"_common", "run_all"}


def discover() -> list[str]:
    pkg_dir = Path(__file__).resolve().parent
    names = [
        m.name
        for m in pkgutil.iter_modules([str(pkg_dir)])
        if not m.ispkg and m.name not in SKIP
    ]
    return sorted(names)


def run_one(name: str) -> dict:
    mod = importlib.import_module(f"{PACKAGE}.{name}")
    if not hasattr(mod, "compute"):
        raise AttributeError(f"{PACKAGE}.{name} has no compute()")
    res = mod.compute()
    res["module"] = f"{PACKAGE}.{name}"
    return res


def dumps(obj) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def write(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # newline="" so the LF the .gitattributes pins survives on Windows.
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(dumps(obj))


def fmt(value) -> str:
    if isinstance(value, dict) and "numerator" in value:
        n, d = value.get("numerator"), value.get("denominator")
        pct = value.get("pct")
        s = f"{n} / {d}"
        if pct is not None:
            s += f" = {pct} %"
        return s
    return str(value)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True, help="directory for counts/<key>.json")
    ap.add_argument("--check", action="store_true",
                    help="compare a fresh run against what is on disk")
    ap.add_argument("--only", action="append", default=None,
                    help="run only this module (repeatable)")
    args = ap.parse_args(argv)

    out = Path(args.out)
    names = discover()
    if args.only:
        names = [n for n in names if n in set(args.only)]
    if not names:
        # An empty sweep is not a pass -- verify.py's own rule, applied here.
        print("FAIL  no recomputation modules found; an empty sweep is not a pass")
        return 1

    problems: list[str] = []
    results: dict[str, dict] = {}

    for name in names:
        try:
            res = run_one(name)
        except Exception:
            problems.append(f"{name}: raised\n{traceback.format_exc()}")
            print(f"  ERROR  {name}")
            continue
        key = res.get("key") or name
        results[key] = res
        path = out / f"{key}.json"
        fresh = dumps(res)

        if args.check:
            if not path.exists():
                problems.append(f"{key}: no committed counts at {path}")
                print(f"  ERROR  {key}: nothing on disk to check against")
                continue
            on_disk = path.read_text(encoding="utf-8")
            if on_disk != fresh:
                problems.append(
                    f"{key}: rerun differs from {path} -- the recomputation is "
                    f"not deterministic, so it is not reproducible either")
                print(f"  DRIFT  {key}")
                continue
        else:
            write(path, res)

        agrees = res.get("agrees_with_e11")
        mark = {True: "ok    ", False: "DIFFER", None: "new   "}[agrees]
        print(f"  {mark} {key:28s} {fmt(res.get('value'))}"
              + ("" if agrees is not False
                 else f"   (E11 prose: {fmt(res.get('e11_prose'))})"))

    if args.check:
        stale = sorted(
            p.name for p in out.glob("*.json")
            if p.stem not in results and p.name != "SUMMARY.json"
        )
        for s in stale:
            problems.append(f"{s} is on disk but no script produces it any more")
            print(f"  STALE  {s}")

    summary = {
        "numbers": sorted(results),
        "disagreements": sorted(
            k for k, r in results.items() if r.get("agrees_with_e11") is False),
        "python": sys.version.split()[0],
        "repo_root": str(_common.repo_root()),
    }
    if not args.check:
        write(out / "SUMMARY.json", summary)

    print()
    if problems:
        print(f"survey_numbers: RED ({len(problems)} problem(s))")
        for p in problems:
            print(f"  - {p}")
        return 1
    n_diff = len(summary["disagreements"])
    print(f"survey_numbers: green -- {len(results)} number(s) recomputed from "
          f"script, {n_diff} disagree(s) with the E11 prose")
    if n_diff:
        print("  (disagreement is the finding, not a failure: the recomputed "
              "value is the number of record)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
