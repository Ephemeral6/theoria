"""Attack 2 -- does the zero survive at sizes E2 did not run?

E2 stopped at far7 (49 cells, blind 7196).  G5 says so itself: the dividend was
measured on instances small enough for a blind search to finish.  This pushes the
same construction to far8/far9/far10 and measures `astar(lmcut())` and
`astar(ipdb())` before and after the singleton guard.

Per-run timeout, and a timeout is reported rather than dropped.
"""

import os
import sys

from lens import brief, dump, measure_level          # noqa: E402
from bench.instances import far_level                # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work", "a2")
LOGS = os.path.join(HERE, "logs", "a2")


def main(sides=(8, 9, 10)):
    out = []
    for side in sides:
        entry = measure_level(far_level(side), os.path.join(WORK, "far%d" % side),
                              LOGS, guards=("singleton",), timeout=900, repeats=1)
        brief(entry)
        out.append(entry)
        dump(out, os.path.join(HERE, "a2_ladder.json"))


if __name__ == "__main__":
    sides = tuple(int(x) for x in sys.argv[1:]) or (8, 9, 10)
    main(sides)
