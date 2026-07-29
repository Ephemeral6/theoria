"""Confirm the two rows that look like a refutation, before quoting either.

`swap-passage` came out `astar(ipdb())` 454 -> 0 expansions, and `far9` came out
78 -> 30.  Both are the thing E2 says does not exist, so both get the treatment a
positive result deserves rather than the one a negative result gets:

* repeated, to rule out a planner that is not a function of its input;
* the verdict read off Fast Downward's own words, not off an expansion count --
  0 expansions is what an *error* looks like too;
* unsolvability of `swap-passage` established **without the guard**, and without
  Fast Downward, by the rig's own complete bundled search, so that "the guard
  made it unsolvable" is excluded rather than assumed away;
* for `far9`, the optimal plan length compared either side and the guarded plan
  replayed against the original domain.
"""

import os
import sys

from lens import RIG, carve_level, executable        # noqa: E402

sys.path.insert(0, RIG)

from a3_family import HAND, parse                    # noqa: E402
from bench import compile_theorems, fdrun            # noqa: E402
from bench.instances import far_level                # noqa: E402
from engines import fd_adapter                       # noqa: E402
from engines.fd_adapter import backends, search as fd_search   # noqa: E402
from fixtures import sokoban                         # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work", "a5")
LOGS = os.path.join(HERE, "logs", "a5")

VERDICT = ("Solution found", "Completely explored state space",
           "Initial heuristic value", "unsolvable", "Expanded ", "Plan length",
           "Time limit", "Memory limit")


def show(tag, path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    print("  --- %s" % tag)
    for line in text.splitlines():
        if any(word in line for word in VERDICT) and "until last jump" not in line:
            print("      %s" % line.strip())


def one(fd, tag, domain_path, problem_path, heuristic, repeats=5):
    counts, verdicts = [], []
    log = os.path.join(LOGS, tag + ".log")
    for index in range(repeats):
        m = fdrun.measure(fd, domain_path, problem_path,
                          tier=backends.FD_OPTIMAL, heuristic=heuristic,
                          timeout=900, keep_log=log if index == 0 else None)
        counts.append(m.nodes.get("expanded"))
        verdicts.append((m.solved, m.proved_unsolvable, m.plan_length,
                         m.returncode, m.error))
    print("  %-28s expanded %s  verdict %s"
          % (tag, counts, sorted(set(verdicts))))
    show(tag, log)
    return counts, verdicts


def bundled_verdict(level):
    """The rig's own complete BFS, with no guard and no Fast Downward."""
    text = level.problem_text()
    path = os.path.join(WORK, "%s.plain.pddl" % level.name)
    os.makedirs(WORK, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    domain = fd_adapter.parse_domain(fd_adapter.read(sokoban.DOMAIN_PATH))
    problem = fd_adapter.parse_problem(fd_adapter.read(path))
    result = fd_search.search(domain, problem, prune=None, max_expansions=2000000)
    return result


def main():
    fd = executable()
    os.makedirs(LOGS, exist_ok=True)

    print("=== swap-passage: is it really unsolvable, without any guard? ===")
    level = parse("swap-passage", HAND["swap-passage"])
    for line in level.grid:
        print("    %s" % line)
    result = bundled_verdict(level)
    print("  bundled BFS (no guard, no FD): plan=%s expansions=%d exhausted=%s"
          % (result.plan, result.expansions, result.plan is None))

    print()
    print("=== swap-passage: astar(ipdb()), unguarded vs singleton guard ===")
    _p, _d, problem, theorems, _c = carve_level(level, os.path.join(WORK, "swap"))
    gdom, gprob = compile_theorems.write_guarded(
        os.path.join(WORK, "swap", "singleton"), level.name, level.problem_text(),
        theorems, guard="singleton", problem=problem)
    plain = os.path.join(WORK, "swap", "%s.pddl" % level.name)
    for heuristic in ("ipdb", "lmcut", "blind"):
        one(fd, "swap-%s-base" % heuristic, sokoban.DOMAIN_PATH, plain, heuristic)
        one(fd, "swap-%s-singleton" % heuristic, gdom, gprob, heuristic)

    print()
    print("=== far9: astar(ipdb()), unguarded vs singleton guard ===")
    far9 = far_level(9)
    _p9, domain9, problem9, theorems9, _c9 = carve_level(far9, os.path.join(WORK, "far9"))
    g9dom, g9prob = compile_theorems.write_guarded(
        os.path.join(WORK, "far9", "singleton"), "far9", far9.problem_text(),
        theorems9, guard="singleton", problem=problem9)
    plain9 = os.path.join(WORK, "far9", "far9.pddl")
    one(fd, "far9-ipdb-base", sokoban.DOMAIN_PATH, plain9, "ipdb")
    one(fd, "far9-ipdb-singleton", g9dom, g9prob, "ipdb")
    guarded = fdrun.measure(fd, g9dom, g9prob, tier=backends.FD_OPTIMAL,
                            heuristic="ipdb", timeout=900)
    base = fdrun.measure(fd, sokoban.DOMAIN_PATH, plain9, tier=backends.FD_OPTIMAL,
                         heuristic="ipdb", timeout=900)
    print("  plan length: base %s, guarded %s" % (base.plan_length, guarded.plan_length))
    fd_adapter.validate_plan(domain9, problem9,
                             compile_theorems.to_original_plan(guarded.plan, "singleton"))
    print("  guarded plan replayed against the ORIGINAL domain: OK (%d steps)"
          % len(guarded.plan))


if __name__ == "__main__":
    main()
