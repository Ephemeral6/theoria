"""Independent recompute of E17's L-L1 lp_potential numbers, plus the crux test.

Crux test: each of the 58 "false" certificates is false against BFS over the
COMPLETE move set.  Is it also false against BFS over the REDUCED move set --
the transition system the engine was actually handed?  If 0/58 are false there,
the certificates are true statements about the handed system.

Own state space, own BFS, own counters.  Only `solve_certificate` and
`candidates` are imported (they are the objects under test).
"""
import json
import os
import sys
from collections import deque

ENGINE_RIG = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..", "engine-rig"))
sys.path.insert(0, ENGINE_RIG)

from engines import lp_potential
from engines.lp_potential.potential import (
    CertificateError, LpUnavailable, Move, heuristic_from, solve_certificate,
)
from heldout import peg

N_POSITIONS = (4, 5, 6, 7)


def geoms(n):
    out = []
    for i in range(n):
        for step in (1, -1):
            over, dst = i + step, i + 2 * step
            if 0 <= dst < n:
                out.append((i, over, dst))
    return sorted(out)


def all_states(n):
    return ["".join(("1" if (m >> (n - 1 - k)) & 1 else "0") for k in range(n))
            for m in range(2 ** n)]


def legal(s, g):
    return s[g[0]] == "1" and s[g[1]] == "1" and s[g[2]] == "0"


def step(s, g):
    c = list(s)
    c[g[0]] = "0"; c[g[1]] = "0"; c[g[2]] = "1"
    return "".join(c)


def reachable(start, goal, gs):
    if start == goal:
        return True
    seen = {start}
    q = deque([start])
    while q:
        s = q.popleft()
        for g in gs:
            if legal(s, g):
                t = step(s, g)
                if t not in seen:
                    if t == goal:
                        return True
                    seen.add(t)
                    q.append(t)
    return False


tot = dict(cases=0, silent=0, errors=0, certs=0, inv=0,
           false_complete=0, false_reduced=0,
           emit_reduced=0, emit_full=0, false_emitted_reduced=0)
false_but_true_over_reduced = []

for n in N_POSITIONS:
    gs_all = geoms(n)
    states = all_states(n)
    for gi in range(1, n - 1):
        goal = "".join("1" if i == gi else "0" for i in range(n))
        full = peg.graph(n, goal)
        # instance set: same rule as heldout/lp_potential_heldout.instances
        insts = [s for s in states
                 if s.count("1") in (n - 1, n - 2) and s != goal]
        for init in insts:
            for wh in gs_all:
                reduced = peg.graph_minus_geometry(full, wh)
                tot["cases"] += 1
                try:
                    cert = solve_certificate(reduced, init, goal_states=[goal])
                except (LpUnavailable, CertificateError):
                    tot["errors"] += 1
                    continue
                if cert is None:
                    tot["silent"] += 1
                    continue
                tot["certs"] += 1
                if Move(*wh).delta(cert.weights) <= 0:
                    tot["inv"] += 1
                r_full = reachable(init, goal, gs_all)
                r_red = reachable(init, goal, [g for g in gs_all if g != wh])
                if r_full:
                    tot["false_complete"] += 1
                if r_red:
                    tot["false_reduced"] += 1
                h = heuristic_from(cert)
                e_red = lp_potential.candidates(cert, h, reduced)
                e_full = lp_potential.candidates(cert, h, full)
                if e_red:
                    tot["emit_reduced"] += 1
                    if r_full:
                        tot["false_emitted_reduced"] += 1
                if e_full:
                    tot["emit_full"] += 1
                if r_full and not r_red and len(false_but_true_over_reduced) < 60:
                    false_but_true_over_reduced.append(
                        {"n": n, "goal": goal, "initial": init,
                         "withheld": "jump(%d,%d,%d)" % wh,
                         "weights": [str(w) for w in cert.weights]})

pct = lambda a, b: "n/a" if not b else "%.1f %%" % (100.0 * a / b)
print("cases                                    %d" % tot["cases"])
print("silent                                   %d" % tot["silent"])
print("errors                                   %d" % tot["errors"])
print("certificates                             %d" % tot["certs"])
print("inv_closed still holds on withheld geom  %d  (%s)"
      % (tot["inv"], pct(tot["inv"], tot["certs"])))
print("FALSE vs BFS over COMPLETE move set      %d  (%s)"
      % (tot["false_complete"], pct(tot["false_complete"], tot["certs"])))
print("FALSE vs BFS over REDUCED move set       %d  <-- the handed system"
      % tot["false_reduced"])
print("emitted when gated on the REDUCED graph  %d" % tot["emit_reduced"])
print("  of which false vs complete move set    %d" % tot["false_emitted_reduced"])
print("emitted when gated on the COMPLETE graph %d" % tot["emit_full"])
print()
print("certificates false-over-complete but TRUE-over-reduced: %d"
      % tot["false_complete"])
with open(os.path.join(os.path.dirname(__file__), "recompute.json"),
          "w", encoding="utf-8", newline="\n") as fh:
    json.dump({"totals": tot,
               "false_over_complete_true_over_reduced_sample":
                   false_but_true_over_reduced},
              fh, indent=2, sort_keys=True)
    fh.write("\n")
