"""(i) Re-run D-035's claim: "Exhaustive search over integer weights in [-4,4]
finds no such vector against the complete move list."

"Such a vector" = one whose Certificate (complete move list, peg4's own goal set)
passes all three exact conditions AND whose heuristic overestimates -- i.e.
`admissibility_report` finds a counterexample.
"""
import itertools
import json
import os
import sys
from fractions import Fraction

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from engines import lp_potential
from engines.lp_potential.potential import Certificate

GRAPH = json.load(open("fixtures/data/peg4_graph.json"))
FULL = lp_potential.moves_from_graph(GRAPH)
print("distinct move geometries in the complete list:", [m.name() for m in FULL])

hits = []
holding = 0
for w in itertools.product(range(-4, 5), repeat=4):
    weights = [Fraction(x) for x in w]
    for initial in GRAPH["states"]:
        if initial in GRAPH["goal_states"]:
            continue
        cert = Certificate(weights=weights, initial=initial,
                           goal_states=list(GRAPH["goal_states"]),
                           moves=list(FULL), margin=Fraction(1))
        cert.conditions = lp_potential.check_exactly(cert)
        if not cert.holds:
            continue
        holding += 1
        h = lp_potential.heuristic_from(cert)
        rows = lp_potential.admissibility_report(h, GRAPH)
        bad = [r for r in rows if not r["admissible"]]
        if bad:
            hits.append((w, initial, bad))

print("weight vectors x initial states searched:", 9 ** 4 * (len(GRAPH["states"]) - 1))
print("certificates that hold over the complete move list:", holding)
print("of those, heuristics with an admissibility counterexample:", len(hits))
for row in hits[:5]:
    print("   ", row)

# The same sweep over every 3-of-4 sub-list, for contrast.
sub_hits = 0
sub_hold = 0
for subset in itertools.combinations(FULL, 3):
    for w in itertools.product(range(-4, 5), repeat=4):
        weights = [Fraction(x) for x in w]
        for initial in GRAPH["states"]:
            if initial in GRAPH["goal_states"]:
                continue
            cert = Certificate(weights=weights, initial=initial,
                               goal_states=list(GRAPH["goal_states"]),
                               moves=list(subset), margin=Fraction(1))
            cert.conditions = lp_potential.check_exactly(cert)
            if not cert.holds:
                continue
            sub_hold += 1
            h = lp_potential.heuristic_from(cert)
            rows = lp_potential.admissibility_report(h, GRAPH)
            if any(not r["admissible"] for r in rows):
                sub_hits += 1
print("\n3-of-4 sub-lists: %d holding certificates, %d with a counterexample"
      % (sub_hold, sub_hits))
