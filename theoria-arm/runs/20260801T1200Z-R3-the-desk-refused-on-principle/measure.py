"""Re-derive this run's two measurements from the archive. No network, no call.

Writes `REPLY_LOSS.json` and `GOAL_FORENSICS.json` next to this file, from the
tracked records of every leg under `theoria-arm/runs/`. Both tools are in
`armtools/` and are what the suite tests; nothing is computed here that the
suite does not also check.

    python measure.py
"""

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ARM)

import _bootstrap                                       # noqa: E402,F401

from armtools import goal_forensics, replyloss          # noqa: E402

RUNS = os.path.join(ARM, "runs")


def _write(name, doc):
    path = os.path.join(HERE, name)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)
        fh.write("\n")
    return path


def main():
    loss = replyloss.sweep(RUNS)
    _write("REPLY_LOSS.json", loss)
    print(loss["reading"])
    print()

    forensics = goal_forensics.sweep(RUNS)
    _write("GOAL_FORENSICS.json", forensics)
    print(forensics["reading"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
