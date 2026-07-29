"""Front (b) for lp_potential: does 26.4 % survive a different cut?

Three cuts:
  * the registered one, disaggregated per `n` (the corpus dimension the run
    pooled over);
  * leave-TWO-geometries-out, n in {4,5};
  * hold out by STATE rather than by geometry -- and the question of whether
    that is even a hold-out for this engine.
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from engines.lp_potential.potential import (
    CertificateError, LpUnavailable, Move, moves_from_graph, solve_certificate,
)
from heldout import peg
from heldout import lp_potential_heldout as lph


def drop_geoms(g, gs):
    out = dict(g)
    out["edges"] = [e for e in g["edges"] if tuple(e["positions"]) not in gs]
    return out


def main():
    print("== registered cut (one geometry withheld), disaggregated per n ==")
    per = Counter()
    for n in (4, 5, 6, 7):
        for gi in range(1, n - 1):
            goal = "".join("1" if i == gi else "0" for i in range(n))
            full = peg.graph(n, goal)
            gs = peg.geometries(full)
            for inst in lph.instances(n, full, goal):
                for g in gs:
                    c = lph.held_out_case(inst, full, g)
                    per["n%d/cases" % n] += 1
                    if c.outcome == "silent":
                        per["n%d/silent" % n] += 1
                    elif c.outcome == "certificate":
                        per["n%d/certs" % n] += 1
                        per["n%d/inv" % n] += int(bool(c.heldout_inv_closed))
                        per["n%d/false" % n] += int(c.claim_true is False)
    for n in (4, 5, 6, 7):
        certs = per["n%d/certs" % n]
        goal1 = "".join("1" if i == 1 else "0" for i in range(n))
        n_geoms = len(peg.geometries(peg.graph(n, goal1)))
        print("  n=%d  geometries=%-3d cases=%-5d silent=%-5d certs=%-5d "
              "inv_closed=%-8s false=%d"
              % (n, n_geoms, per["n%d/cases" % n], per["n%d/silent" % n], certs,
                 "n/a" if not certs else "%.1f %%" % (100.0 * per["n%d/inv" % n] / certs),
                 per["n%d/false" % n]))

    print()
    print("== leave-TWO-geometries-out, n in {4,5} ==")
    t = Counter()
    for n in (4, 5):
        for gi in range(1, n - 1):
            goal = "".join("1" if i == gi else "0" for i in range(n))
            full = peg.graph(n, goal)
            gs = peg.geometries(full)
            for inst in lph.instances(n, full, goal):
                for i in range(len(gs)):
                    for j in range(i + 1, len(gs)):
                        pair = {tuple(gs[i]), tuple(gs[j])}
                        reduced = drop_geoms(full, pair)
                        if not reduced["edges"]:
                            t["degenerate"] += 1
                            continue
                        try:
                            c = solve_certificate(reduced, inst.initial,
                                                  goal_states=[goal])
                        except (LpUnavailable, CertificateError):
                            t["errors"] += 1
                            continue
                        t["cases"] += 1
                        if c is None:
                            t["silent"] += 1
                            continue
                        t["certs"] += 1
                        ok = all(Move(*m).delta(c.weights) <= 0 for m in pair)
                        t["inv"] += int(ok)
                        t["false"] += int(inst.truly_reachable)
    print("  cases=%d silent=%d certs=%d  inv_closed on BOTH withheld=%s  false=%d"
          % (t["cases"], t["silent"], t["certs"],
             "n/a" if not t["certs"] else "%.1f %%" % (100.0 * t["inv"] / t["certs"]),
             t["false"]))

    print()
    print("== hold out by STATE: is it a hold-out at all for this engine? ==")
    changed = same = 0
    for n in (4, 5, 6, 7):
        for gi in range(1, n - 1):
            goal = "".join("1" if i == gi else "0" for i in range(n))
            full = peg.graph(n, goal)
            base = {m.name() for m in moves_from_graph(full)}
            for s in full["states"]:
                reduced = dict(full)
                reduced["edges"] = [e for e in full["edges"] if e["src_state"] != s]
                if not reduced["edges"]:
                    continue
                if {m.name() for m in moves_from_graph(reduced)} == base:
                    same += 1
                else:
                    changed += 1
    print("  dropping one state's outgoing edges leaves the LP's constraint set "
          "UNCHANGED in %d of %d cases (%.1f %%)"
          % (same, same + changed, 100.0 * same / (same + changed)))
    print("  -- where the constraint set is unchanged the LP, the certificate and")
    print("     every metric are bit-identical, so a state-level hold-out is")
    print("     vacuous for this engine by construction.")


if __name__ == "__main__":
    main()
