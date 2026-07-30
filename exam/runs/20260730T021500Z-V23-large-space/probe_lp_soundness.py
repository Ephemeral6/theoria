"""Follow-up to probe E: is the certificate lp_potential minted actually true?

The comb level in probe E is *solvable* -- LEFT is forbidden, but the corridor
runs left-to-right, every alcove is an out-and-back dip, and the goal is the
corridor's right end.  If `solve()` returned `certified` on it, the engine has
published an unreachability proof for a reachable goal.

This script checks three things:
  1. the goal state is in the forward closure from the start (so it IS reachable);
  2. what the certificate says, verbatim;
  3. whether the engine's own cross-checks (`check_exactly`,
     `premises_against_graph`, `heuristic.entitlement`) catch it.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
for path in (REPO, os.path.join(REPO, "engine-rig")):
    if path not in sys.path:
        sys.path.insert(0, path)

from engines.lp_potential import potential as lp          # noqa: E402
from probe_lp_interface import comb_level, comb_state_graph   # noqa: E402

level = comb_level(4, 1, 4)
graph = comb_state_graph(level, forbidden=("LEFT",))
goal = graph["goal_states"][0]

print("n_pos=%d  cells=%d  switches=%d" % (graph["n_pos"], graph["cells"],
                                           graph["switches"]))
reachable = goal in set(graph["states"])
print("goal state present in the forward closure from the start: %s" % reachable)
print("  -> the level is %s" % ("SOLVABLE" if reachable else "unsolvable"))

outcome = lp.solve(graph, graph["initial"])
print("\nsolve() status: %s" % outcome.status)
cert = outcome.certificate
report = {"reachable": reachable, "status": outcome.status}
if cert is not None:
    doc = cert.as_json()
    print("certificate.holds          : %s" % doc["holds"])
    print("certificate.conditions     : %s" % doc["conditions"])
    print("certificate.claim          : %s" % doc["claim"])
    print("weights                    : %s" % doc["weights"])
    prem = lp.premises_against_graph(cert, graph)
    print("premises_against_graph.sound_over_graph: %s" % prem["sound_over_graph"])
    print("  move_list_complete=%s  moves_raising_potential=%d"
          % (prem["move_list_complete"], len(prem["moves_raising_potential"])))
    heur = lp.heuristic_from(cert)
    ent = heur.entitlement(None)
    print("heuristic.entitlement.admissible: %s" % ent["admissible"])
    report["certificate"] = doc
    report["premises"] = prem
    report["entitlement"] = ent

    # The independent check the engine never runs: does the *real* potential
    # (sum of w over occupied cells) actually fall along every edge?
    bad = 0
    for edge in graph["edges"]:
        if cert.potential(edge["dst_state"]) > cert.potential(edge["src_state"]):
            bad += 1
    print("\nedges on which the REAL potential rises: %d of %d"
          % (bad, len(graph["edges"])))
    print("potential(start)=%s  potential(goal)=%s"
          % (cert.potential(graph["initial"]), cert.potential(goal)))
    report["real_potential_rising_edges"] = bad
    report["real_potential_start"] = str(cert.potential(graph["initial"]))
    report["real_potential_goal"] = str(cert.potential(goal))

path = os.path.join(HERE, "probe_lp_soundness.json")
with open(path, "w", encoding="utf-8", newline="\n") as handle:
    json.dump(report, handle, indent=2, sort_keys=True, default=str)
    handle.write("\n")
print("\nwrote %s" % path)
