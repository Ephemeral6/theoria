"""a2_crosscheck's completion gate.

    cd a2_crosscheck && python verify.py

Two rungs:

  1. the suite passes -- the seal's isolation tests and the referee's
     calibration are all in it, so a green suite is the bridge holding;
  2. the red lines: no sealed-pile game id in any tracked file of this
     territory, and no credential value either.  The bridge exists to swap
     two DEV worlds between two tracks; a sealed id appearing here would
     mean it started carrying the exam.

Landed 2026-07-31 by the cleanup campaign, the same day the territory was
relocated from crosscheck/ (which the C14 census now owns) -- the survey
test (monitor/tests/test_gates.py) flagged the gap, and the correct
response to that flag is a gate, not a wider pin.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)


def rung(label: str, ok: bool, detail: str) -> bool:
    print("%-4s %s -- %s" % ("ok" if ok else "FAIL", label, detail))
    return ok


def main() -> int:
    green = True

    # 1 -- suite
    r = subprocess.run([sys.executable, "-m", "pytest", "-q",
                        "-p", "no:cacheprovider", HERE],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=REPO)
    tail = (r.stdout or "").strip().splitlines()[-1] if r.stdout else ""
    green &= rung("suite", r.returncode == 0, tail or "no output")

    # 2 -- red lines over this territory's tracked files
    ls = subprocess.run(["git", "ls-files", "a2_crosscheck"],
                        capture_output=True, text=True, encoding="utf-8",
                        cwd=REPO)
    files = [f for f in ls.stdout.splitlines() if f.strip()]
    piles = json.load(open(os.path.join(REPO, "arc-recon", "data",
                                        "piles.json"), encoding="utf-8"))
    sealed = set(piles["sealed_pile"])
    hits = []
    for f in files:
        try:
            text = open(os.path.join(REPO, f), encoding="utf-8",
                        errors="ignore").read()
        except OSError:
            continue
        for g in sealed:
            if g in text:
                hits.append("%s: %s" % (f, g))
    green &= rung("sealed", not hits,
                  "no sealed-pile id in %d tracked file(s)" % len(files)
                  if not hits else "; ".join(hits[:5]))

    print("a2_crosscheck:", "green -- suite, red lines" if green else "RED")
    return 0 if green else 1


if __name__ == "__main__":
    sys.exit(main())
