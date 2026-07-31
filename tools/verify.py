"""tools/' completion gate -- the location gate polices everyone, so it owes
a gate of its own.

    cd tools && python verify.py

Two rungs:

  1. the suite passes (the negative controls that prove check_locations can
     say no are in it);
  2. the scanner itself runs clean over the current tree -- the gate's own
     standing verdict, not a copy of it.

Landed 2026-07-31 by the cleanup campaign after the survey test
(monitor/tests/test_gates.py) flagged the territory as tests-without-a-gate.
"""

from __future__ import annotations

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

    r = subprocess.run([sys.executable, "-m", "pytest", "-q",
                        "-p", "no:cacheprovider",
                        os.path.join(HERE, "tests")],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=REPO)
    tail = (r.stdout or "").strip().splitlines()[-1] if r.stdout else ""
    green &= rung("suite", r.returncode == 0, tail or "no output")

    s = subprocess.run([sys.executable, os.path.join(HERE,
                                                     "check_locations.py")],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=REPO)
    last = (s.stdout or "").strip().splitlines()[-1] if s.stdout else ""
    green &= rung("locations", s.returncode == 0, last or "no output")

    print("tools:", "green -- suite, live scan" if green else "RED")
    return 0 if green else 1


if __name__ == "__main__":
    sys.exit(main())
