"""Attack (a), classified.  Same exhaustive sweep, but bucketed:

  bucket A: goal_states == the graph's own goal  -> the check was aimed right
  bucket B: goal_states != the graph's own goal  -> `admissibility_report` read
            `graph["distance_to_goal"]`, i.e. distance to a DIFFERENT goal set
            than the one h is about
  and separately, whether the move list was complete (answers D-035 claim (i)).
"""
import itertools
import json
import os
import sys
from collections import deque
from fractions import Fraction

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from engines import lp_potential
from engines.lp_potential.potential import Certificate

GRAPH = json.load(open("fixtures/data/peg4_graph.json"))
STATES = list(GRAPH["states"])
EDGES = [(e["src_state"], e["dst_state"]) for e in GRAPH["edges"]]
GEOMS = lp_potential.moves_from_graph(GRAPH)
GRAPH_GOALS = tuple(GRAPH["goal_states"])
BACK = {}
for src, dst in EDGES:
    BACK.setdefault(dst, []).append(src)


def true_distance(goals):
    dist = {g: 0 for g in goals if g in STATES}
    q = deque(dist)
    while q:
        s = q.popleft()
        for p in BACK.get(s, ()):
            if p not in dist:
                dist[p] = dist[s] + 1
                q.append(p)
    return dist


def main(bound=2):
    rng = range(-bound, bound + 1)
    subsets = [s for r in range(len(GEOMS) + 1)
               for s in itertools.combinations(GEOMS, r)]
    goalsets = [g for r in (1, 2) for g in itertools.combinations(STATES, r)]
    buckets = {"A_right_goalset": [], "B_wrong_goalset": []}
    full_move_hits = []
    for w in itertools.product(rng, repeat=4):
        weights = [Fraction(x) for x in w]
        for subset in subsets:
            for initial in STATES:
                for goals in goalsets:
                    if initial in goals:
                        continue
                    cert = Certificate(weights=weights, initial=initial,
                                       goal_states=list(goals), moves=list(subset),
                                       margin=Fraction(1))
                    cert.conditions = lp_potential.check_exactly(cert)
                    if not cert.holds:
                        continue
                    h = lp_potential.heuristic_from(cert)
                    report = lp_potential.admissibility_report(h, GRAPH)
                    if not h.as_json(report)["admissible"]:
                        continue
                    dist = true_distance(goals)
                    bad = [(s, h.value(s), d) for s, d in dist.items() if h.value(s) > d]
                    if not bad:
                        continue
                    key = ("A_right_goalset" if tuple(sorted(goals)) == tuple(sorted(GRAPH_GOALS))
                           else "B_wrong_goalset")
                    buckets[key].append((w, len(subset), initial, goals, bad[0]))
                    if len(subset) == len(GEOMS):
                        full_move_hits.append((w, initial, goals, bad[0]))
    for k, v in buckets.items():
        print("%s: %d" % (k, len(v)))
        for row in v[:3]:
            print("   ", row)
    print("counterexamples with the COMPLETE move list:", len(full_move_hits))
    for row in full_move_hits[:5]:
        print("   ", row)
    # the sharpest single witness, reachable via the public `run()` signature
    if buckets["B_wrong_goalset"]:
        w, nsub, initial, goals, bad = buckets["B_wrong_goalset"][0]
        print("\nsharpest B witness: w=%s |moves|=%d initial=%s goals=%s "
              "state=%s h=%s true=%s" % (w, nsub, initial, goals, bad[0], bad[1], bad[2]))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 2)
