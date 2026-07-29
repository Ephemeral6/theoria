"""Is `astar(ipdb())` deterministic on this build?

far9 came out 78 -> 30 under the singleton guard, which would be a 62% dividend
on an admissible heuristic -- the thing E2 says does not exist.  Before it can be
quoted it has to survive the obvious alternative explanation: `ipdb` is
`cpdbs(hillclimbing())` and hill climbing takes a random seed.  If the same argv
on the same file gives a different count twice, the 78 and the 30 are two rolls
of the same die and there is no dividend in them.

Run each configuration N times and print every count.
"""

import os
import sys

from lens import RIG, executable                      # noqa: E402

sys.path.insert(0, RIG)

from bench import fdrun                               # noqa: E402
from engines.fd_adapter import backends               # noqa: E402
from fixtures import sokoban                          # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    fd = executable()
    cases = []
    for side in (8, 9, 10):
        work = os.path.join(HERE, "work", "a2", "far%d" % side)
        cases.append(("far%d base" % side, sokoban.DOMAIN_PATH,
                      os.path.join(work, "far%d.pddl" % side)))
        cases.append(("far%d singleton" % side,
                      os.path.join(work, "singleton", "sokoban_guarded_singleton_domain.pddl"),
                      os.path.join(work, "singleton", "far%d_guarded_singleton.pddl" % side)))
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    for heuristic in ("ipdb", "lmcut"):
        for tag, dom, prob in cases:
            counts = []
            for _ in range(n):
                m = fdrun.measure(fd, dom, prob, tier=backends.FD_OPTIMAL,
                                  heuristic=heuristic, timeout=900)
                counts.append(m.nodes.get("expanded"))
            print("%-6s %-18s expanded over %d runs: %s%s"
                  % (heuristic, tag, n, counts,
                     "   <-- NOT DETERMINISTIC" if len(set(counts)) > 1 else ""))


if __name__ == "__main__":
    main()
