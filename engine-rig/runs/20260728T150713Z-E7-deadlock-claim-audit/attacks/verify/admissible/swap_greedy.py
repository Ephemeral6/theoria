"""Find, by hand, a pattern on which the guarded task's PDB proves the initial
state dead -- then evaluate that same pattern on the unguarded task.

This is the test that decides the question the reviewer's systematic(2)/(3)
disposal cannot: if the pattern that gives the guarded task h=infinity gives the
base task h=infinity too, iPDB's 454->0 is a pattern lottery.  If the same
pattern is finite on the base task, the guard put information into the
abstraction that the abstraction could not otherwise have.

The hill climb here maximises "fewest states A* still has to expand", which on
an unsolvable task is exactly "most states the abstraction proves dead", and
reaches 0 precisely when h(init) = infinity.
"""
import json, os, sys
import run as R
import swap_sweep as S

TASK = sys.argv[1] if len(sys.argv) > 1 else "guarded"
if TASK == "guarded":
    D, P, m = S.G_D, S.G_P, S.gmap
else:
    D, P, m = S.BASE_D, S.BASE_P, S.bmap


def h_and_exp(names, tag):
    coll = "[[" + ",".join(str(m[n]) for n in names) + "]]"
    r = R.run(D, P, "astar(cpdbs(patterns=manual_patterns(%s)))" % coll,
              "swap.greedy.%s.%s" % (TASK, tag))
    return r


cur = S.CORE + ["player"]
rest = list(S.CLEARS)
trace = []
r = h_and_exp(cur, "start")
best_exp = r["expanded"]
print("start %s  h=%s exp=%s" % (cur, r["initial_h"], best_exp), flush=True)
for step in range(10):
    scored = []
    for c in rest:
        rr = h_and_exp(cur + [c], "s%d_%s" % (step, c.replace(":", "")))
        if rr["expanded"] is None:
            continue
        scored.append((rr["expanded"], -int(rr["initial_h"]) if rr["initial_h"] != "infinity" else -10**9, c, rr))
    if not scored:
        break
    scored.sort()
    exp, _neg, c, rr = scored[0]
    cur = cur + [c]
    rest.remove(c)
    trace.append({"step": step, "added": c, "pattern": list(cur),
                  "expanded": exp, "initial_h": rr["initial_h"]})
    print("step %d add %-12s -> h=%-9s exp=%s  pattern=%s"
          % (step, c, rr["initial_h"], exp, cur), flush=True)
    best_exp = exp
    if exp == 0:
        break
json.dump({"task": TASK, "trace": trace, "final_pattern": cur},
          open("swap_greedy_%s.json" % TASK, "w"), indent=2)
print("FINAL", TASK, cur)
