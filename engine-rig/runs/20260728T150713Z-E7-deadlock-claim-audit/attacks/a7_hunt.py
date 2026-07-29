"""Attack 3, second pass -- a screened hunt instead of a blind sweep.

The first random sweep spent most of its budget on instances Fast Downward's
translator settles before search (a box starts in a corner, the goal is relaxed-
unreachable, task size 4, zero expansions on every rung).  Those rows cannot
carry a dividend in either direction and they are most of what a uniform random
generator produces.

So: screen first.  Run the unguarded `astar(lmcut())` once and keep only the
instances where it actually expands something.  Then measure the guards on the
survivors.  Same measurement, a hundredth of the wasted budget.
"""

import os
import random
import sys
from typing import List, Optional

from lens import brief, carve_level, dump, executable, measure_level   # noqa: E402



from bench import fdrun                               # noqa: E402
from engines.fd_adapter import backends               # noqa: E402
from fixtures import sokoban                          # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work", "a7")
LOGS = os.path.join(HERE, "logs", "a7")

FLOOR_MIN = 12


def random_level(rng: random.Random, index: int) -> Optional[sokoban.Level]:
    side = rng.choice((5, 5, 6, 6, 7))
    n_walls = rng.choice((0, 1, 2, 3, 4, 5))
    n_boxes = rng.choice((2, 2, 2, 3))
    cells = [(r, c) for r in range(1, side + 1) for c in range(1, side + 1)]
    walls = set(rng.sample(cells, n_walls))
    floor = [cell for cell in cells if cell not in walls]
    if len(floor) < max(FLOOR_MIN, 2 * n_boxes + 1):
        return None
    grid = ["#" * (side + 2)]
    for r in range(1, side + 1):
        grid.append("#" + "".join(
            "#" if (r, c) in walls else "." for c in range(1, side + 1)) + "#")
    grid.append("#" * (side + 2))
    picks = rng.sample(floor, 2 * n_boxes + 1)
    return sokoban.Level(
        name="hunt%04d" % index, grid=tuple(grid), player=picks[0],
        boxes=tuple(("b%d" % (i + 1), picks[1 + i]) for i in range(n_boxes)),
        goals=tuple(("b%d" % (i + 1), picks[1 + n_boxes + i]) for i in range(n_boxes)),
        optimum=None, path="")


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    floor = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    fd = executable()
    rng = random.Random(seed)
    os.makedirs(WORK, exist_ok=True)

    kept, screened, results, hits = 0, 0, [], []
    for index in range(count):
        level = random_level(rng, index)
        if level is None:
            continue
        screened += 1
        work = os.path.join(WORK, level.name)
        os.makedirs(work, exist_ok=True)
        path = os.path.join(work, "%s.pddl" % level.name)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(level.problem_text())
        probe = fdrun.measure(fd, sokoban.DOMAIN_PATH, path,
                              tier=backends.FD_OPTIMAL, heuristic="lmcut", timeout=300)
        expanded = probe.nodes.get("expanded") or 0
        if expanded < floor:
            continue
        kept += 1
        try:
            entry = measure_level(level, work, LOGS,
                                  guards=("singleton", "indexed"),
                                  timeout=600, repeats=1)
        except Exception as exc:
            print("== %s FAILED: %s" % (level.name, exc))
            continue
        entry["art"] = list(level.grid)
        brief(entry)
        results.append(entry)
        for r in entry["rows"]:
            if "skipped" in r or r["rung"] == "blind":
                continue
            b, a = r["before"]["expanded"], r["after"]["expanded"]
            if b and a is not None and a < b:
                hits.append({"instance": level.name, "guard": r["guard"],
                             "rung": r["rung"], "before": b, "after": a,
                             "cut": round((b - a) / b, 3),
                             "plan_before": r["before"]["plan_length"],
                             "plan_after": r["after"]["plan_length"],
                             "replayed": r["replayed_on_original_domain"],
                             "art": list(level.grid)})
                print("   *** HIT %s %s %s: %d -> %d (%.0f%%)"
                      % (level.name, r["guard"], r["rung"], b, a, 100 * (b - a) / b))
        dump({"screened": screened, "kept": kept, "floor": floor,
              "hits": hits, "results": results},
             os.path.join(HERE, "a7_hunt.json"))
    print()
    print("screened %d, kept %d (lmcut baseline >= %d), hits %d"
          % (screened, kept, floor, len(hits)))
    for hit in hits:
        print("   %(instance)s %(guard)s %(rung)s %(before)d -> %(after)d "
              "(%(cut).0%%) plan %(plan_before)s->%(plan_after)s replay=%(replayed)s"
              % hit if False else "   %s" % hit)


if __name__ == "__main__":
    main()
