"""Is `ipdb`'s dividend information, or is it the pattern generator being jogged?

`astar(ipdb())` moves under the guard where `astar(lmcut())` does not, and it
moves non-monotonically across board sizes (far8 27->24, far9 78->30, far10
93->93).  That is the signature of a *perturbation* as much as of a dividend:
iPDB picks its pattern collection by hill climbing over sampled states, so
deleting sixteen operators changes what it samples and therefore which patterns
it builds -- with no implication that it learned anything from the theorems.

The discriminator: carry k of the 8 corner theorems, k = 0..8, and watch the
count.  Information is monotone -- a superset of theorems removes a superset of
transitions, so a search that was using them cannot get worse.  A lottery is not.

Two orders (the carver's own, and its reverse) so the answer does not depend on
which theorem happens to be dropped first.
"""

import itertools
import json
import os
import sys

from lens import RIG, carve_level, executable, dump  # noqa: E402

sys.path.insert(0, RIG)

from a3_family import HAND, parse                    # noqa: E402
from bench import compile_theorems, fdrun            # noqa: E402
from bench.instances import far_level                # noqa: E402
from engines.fd_adapter import backends              # noqa: E402
from fixtures import sokoban                         # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work", "a6")


def sweep(fd, level, name, heuristics=("ipdb", "lmcut")):
    plain_path, domain, problem, theorems, _ = carve_level(level, os.path.join(WORK, name))
    singles = [t for t in theorems if t.size == 1]
    print("== %s: %d singleton theorems" % (name, len(singles)))
    rows = []
    for order_name, ordered in (("carver", singles), ("reversed", singles[::-1])):
        for k in range(len(singles) + 1):
            subset = ordered[:k]
            gdir = os.path.join(WORK, name, "%s-%d" % (order_name, k))
            if subset:
                gdom, gprob = compile_theorems.write_guarded(
                    gdir, name, level.problem_text(), subset,
                    guard="singleton", problem=problem)
            else:
                gdom, gprob = sokoban.DOMAIN_PATH, plain_path
            entry = {"order": order_name, "k": k}
            for heuristic in heuristics:
                m = fdrun.measure(fd, gdom, gprob, tier=backends.FD_OPTIMAL,
                                  heuristic=heuristic, timeout=900)
                entry[heuristic] = m.nodes.get("expanded")
                entry["%s_len" % heuristic] = m.plan_length
                entry["operators"] = m.translator.get("operators")
            rows.append(entry)
            print("   %-8s k=%d  ops=%s  %s"
                  % (order_name, k, entry["operators"],
                     "  ".join("%s=%s(len %s)" % (h, entry[h], entry["%s_len" % h])
                               for h in heuristics)))
    for order_name in ("carver", "reversed"):
        for heuristic in heuristics:
            series = [r[heuristic] for r in rows if r["order"] == order_name]
            monotone = all(b <= a for a, b in zip(series, series[1:])
                           if a is not None and b is not None)
            print("   %-8s %-5s series %s  monotone-non-increasing=%s"
                  % (order_name, heuristic, series, monotone))
    return rows


def main():
    fd = executable()
    out = {}
    for name, level in (("far9", far_level(9)),
                        ("far8", far_level(8)),
                        ("three-far", parse("three-far", HAND["three-far"])),
                        ("swap-passage", parse("swap-passage", HAND["swap-passage"]))):
        out[name] = sweep(fd, level, name)
        dump(out, os.path.join(HERE, "a6_subsets.json"))


if __name__ == "__main__":
    main()
