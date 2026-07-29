"""Two targeted attacks.

1. The emit gate.  RESULTS.md credits it with withholding 1408/1408.  The harness
   hands it the COMPLETE graph while the certificate was fitted on the reduced
   one, i.e. it hands the gate the ground truth the hold-out premise says the
   caller does not have.  Re-run the gate with the graph the caller would
   actually hold, and count the false certificates that get out.

2. L-L2's "0 admissibility violations in 506 held-out states".  Is that an
   empirical pass or a theorem?  Cross-tabulate held-out violations against
   `inv_closed` on the withheld geometry.
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from engines import lp_potential
from engines.lp_potential.potential import (
    CertificateError, LpUnavailable, Move, heuristic_from, solve_certificate,
)
from heldout import peg
from heldout import lp_potential_heldout as lph


def main():
    tab = Counter()
    false_emitted_reduced = 0
    false_total = 0
    demo_done = False

    for n in lph.N_POSITIONS:
        for gi in range(1, n - 1):
            goal = "".join("1" if i == gi else "0" for i in range(n))
            full = peg.graph(n, goal)
            gs = peg.geometries(full)
            for inst in lph.instances(n, full, goal):
                for g in gs:
                    reduced = peg.graph_minus_geometry(full, g)
                    try:
                        c = solve_certificate(reduced, inst.initial,
                                              goal_states=[goal])
                    except (LpUnavailable, CertificateError):
                        continue
                    if c is None:
                        continue
                    h = heuristic_from(c)
                    inv = Move(*g).delta(c.weights) <= 0
                    viol, tested, _ = lph._admissibility_on_heldout(c, full)
                    tab["inv=%s viol>0=%s" % (inv, viol > 0)] += 1
                    tab["inv=%s violations" % inv] += viol

                    out_full = lp_potential.candidates(c, h, full)
                    out_reduced = lp_potential.candidates(c, h, reduced)
                    tab["emitted_full"] += int(bool(out_full))
                    tab["emitted_reduced"] += int(bool(out_reduced))
                    if inst.truly_reachable:
                        false_total += 1
                        false_emitted_reduced += int(bool(out_reduced))
                        if (not demo_done and n == 4 and goal == "0100"
                                and inst.initial == "0011" and tuple(g) == (3, 2, 1)):
                            demo_done = True
                            print("--- the smallest witness, through the emit gate ---")
                            print("weights            :", [str(w) for w in c.weights])
                            print("conditions         :", c.conditions)
                            print("claim              :", c.as_json()["claim"])
                            print("true distance 0011->0100:",
                                  full["distance_to_goal"]["0011"])
                            print("candidates(full graph)   ->", len(out_full), "rows")
                            print("candidates(reduced graph)->", len(out_reduced), "rows")
                            if out_reduced:
                                p = out_reduced[0]["payload"]
                                print("  emitted claim :", p["claim"])
                                print("  emitted holds :", p["holds"])
                                print("  premise_check :", p["premise_check"]["sound_over_graph"],
                                      "missing:", p["premise_check"]["missing_moves"],
                                      "raising:", p["premise_check"]["moves_raising_potential"])

    print()
    print("--- cross-tab over all held-out certificates ---")
    for k in sorted(tab):
        print("  %-28s %d" % (k, tab[k]))
    print()
    print("false certificates: %d, of which emitted when the gate is handed the "
          "SAME partial graph the LP was fitted on: %d"
          % (false_total, false_emitted_reduced))


if __name__ == "__main__":
    main()
