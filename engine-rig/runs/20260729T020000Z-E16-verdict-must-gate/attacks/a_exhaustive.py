"""Attack (a): find a Heuristic whose payload says admissible=true but which
overestimates the true shortest distance on the peg4 graph.

Exhaustive over: integer weights in [-B,B]^4, every subset of the distinct move
geometries, every initial state, every non-empty goal set of size <= 2.

Ground truth is recomputed here from the graph's FULL edge list by BFS, against
the certificate's OWN goal set -- which is the claim h actually makes.
"""
import itertools
import json
import math
import os
import sys
from collections import deque
from fractions import Fraction

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from engines import lp_potential
from engines.lp_potential.potential import Certificate, Heuristic, Move

GRAPH = json.load(open("fixtures/data/peg4_graph.json"))
STATES = list(GRAPH["states"])
EDGES = [(e["src_state"], e["dst_state"]) for e in GRAPH["edges"]]
GEOMS = lp_potential.moves_from_graph(GRAPH)


def true_distance(goals):
    """BFS backwards over the full edge list: state -> min moves to any goal."""
    dist = {g: 0 for g in goals if g in STATES}
    q = deque(dist)
    back = {}
    for src, dst in EDGES:
        back.setdefault(dst, []).append(src)
    while q:
        s = q.popleft()
        for p in back.get(s, ()):
            if p not in dist:
                dist[p] = dist[s] + 1
                q.append(p)
    return dist


def main(bound=4):
    rng = range(-bound, bound + 1)
    found = []
    n_holding = 0
    n_gated_true = 0
    subsets = [s for r in range(len(GEOMS) + 1)
               for s in itertools.combinations(GEOMS, r)]
    goalsets = [g for r in (1, 2) for g in itertools.combinations(STATES, r)]
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
                    n_holding += 1
                    h = lp_potential.heuristic_from(cert)
                    report = lp_potential.admissibility_report(h, GRAPH)
                    payload = h.as_json(report)
                    if not payload["admissible"]:
                        continue
                    n_gated_true += 1
                    # ground truth against the certificate's own goals
                    dist = true_distance(goals)
                    for s, d in dist.items():
                        if h.value(s) > d:
                            found.append((w, [m.name() for m in subset], initial,
                                          goals, s, h.value(s), d))
                            break
    print("certificates that hold:", n_holding)
    print("payload admissible=true:", n_gated_true)
    print("COUNTEREXAMPLES:", len(found))
    for row in found[:20]:
        print(row)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 2)
