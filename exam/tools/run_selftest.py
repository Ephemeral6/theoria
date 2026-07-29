"""Run the marker's self-test and write the two matrices.

    python -m exam.tools.run_selftest              # mutants + faults + matrix
    python -m exam.tools.run_selftest --quick      # mutants + matrix, no faults
    python -m exam.tools.run_selftest --render     # print the tables

Three artefacts, all deterministic:

    artifacts/selftest.json                 mutants, fault matrix, digests
    artifacts/matrix/verdict_confusion.json sensitivity/specificity, per class
    artifacts/matrix/verdict_confusion.md   the same, as a table

The fault half is the slow one -- it re-runs every check once per injected
fault, which is eight full calibrations -- so `--quick` exists for the loop and
the full run is what gets archived.

Exit status is 0 when the run is clean, 1 when a mutant failed or the baseline
was already dirty.  An **uncaught fault is not a failure**: a run that discovers
a hole in the checks is a run that did its job, and it says so in the summary
rather than in the exit code.  A dirty baseline is a failure, because it means a
check was firing before anything was injected and the matrix underneath it means
nothing.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(HERE)
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from exam import guard                                              # noqa: E402
from exam.grading.confusion_matrix import (render_matrix,           # noqa: E402
                                           verdict_matrix)
from exam.grading.registry import digest                            # noqa: E402
from exam.grading.selftest import (fault_matrix, mutant_battery_all,  # noqa: E402
                                   protocol_digest,
                                   protocol_module_digests)
from exam.model import ARTIFACTS, write_json                        # noqa: E402

SELFTEST_PATH = os.path.join(ARTIFACTS, "selftest.json")
MATRIX_DIR = os.path.join(ARTIFACTS, "matrix")
CONFUSION_JSON = os.path.join(MATRIX_DIR, "verdict_confusion.json")
CONFUSION_MD = os.path.join(MATRIX_DIR, "verdict_confusion.md")


def _write_text(path: str, text: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return path


def run(*, faults: bool = True, cap: int = 8, fault_cap: int = 4) -> Dict[str, Any]:
    with guard.no_network():
        battery = mutant_battery_all(cap=cap)
        matrix = verdict_matrix()
        payload: Dict[str, Any] = {
            "rubric_digest": digest(),
            "protocol_digest": protocol_digest(),
            "protocol_modules": protocol_module_digests(),
            "mutants": battery,
        }
        if faults:
            payload["fault_matrix"] = fault_matrix(cap=fault_cap)

    write_json(SELFTEST_PATH, payload)
    write_json(CONFUSION_JSON, matrix)
    _write_text(CONFUSION_MD, render_matrix(matrix))
    payload["confusion_matrix"] = matrix
    return payload


def summarise(payload: Dict[str, Any]) -> List[str]:
    lines: List[str] = []
    battery = payload["mutants"]
    lines.append("mutants: %s" % ("all passed" if battery["passed"]
                                  else "%d FAILED" % len(battery["failures"])))
    for failure in battery["failures"]:
        lines.append("  FAIL %s" % failure)
    matrix = payload.get("fault_matrix")
    if matrix:
        lines.append("faults: %d injected, %d uncaught, baseline %s"
                     % (matrix["n_faults"], matrix["n_uncaught"],
                        "clean" if matrix["baseline_clean"] else "DIRTY"))
        for name, row in matrix["faults"].items():
            lines.append("  %-24s %s" % (name, ", ".join(row["caught_by"])
                                         or "UNCAUGHT -- a hole in the checks"))
        for name in matrix["uncaught"]:
            lines.append("  HOLE: nothing catches `%s` (%s)"
                         % (name, matrix["faults"][name]["what_it_does"]))
    lines.append("protocol digest: %s" % payload["protocol_digest"])
    return lines


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--quick", action="store_true",
                        help="skip fault injection (the slow half)")
    parser.add_argument("--render", action="store_true",
                        help="print the confusion matrix table")
    args = parser.parse_args(argv)

    payload = run(faults=not args.quick)
    for line in summarise(payload):
        print(line)
    if args.render:
        print()
        print(render_matrix(payload["confusion_matrix"]))
    print("wrote %s" % SELFTEST_PATH)
    print("wrote %s" % CONFUSION_JSON)
    print("wrote %s" % CONFUSION_MD)

    ok = payload["mutants"]["passed"]
    matrix = payload.get("fault_matrix")
    if matrix and not matrix["baseline_clean"]:
        ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
