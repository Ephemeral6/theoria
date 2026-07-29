"""Attack (b): the SIBLING row in the very same emit is still ungated.

`lp_potential.candidates()` builds two rows from one weight vector.  The E16 fix
gates row 1 (heuristic).  Row 0 (invariant) is `certificate.as_json()`, which has
no `holds` key at all and publishes `claim: "goal unreachable from ..."` plus
`rendering: "every legal move leaves it non-increasing"` unconditionally.

The worker's own new test (tests/test_lp_potential.py:288) reaches a state where
the heuristic row carries counterexamples that PROVE `inv_closed` is false over
the real move set -- and asserts nothing about row 0.
"""
import json
import os
import sys
from fractions import Fraction

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from engines import lp_potential

GRAPH = json.load(open("fixtures/data/peg4_graph.json"))

# the exact fixture the new test uses
HOLES_WEIGHTS = None
import re
src = open("tests/test_lp_potential.py").read()
HOLES_WEIGHTS = eval(re.search(r"HOLES_WEIGHTS\s*=\s*(\[[^\]]*\])", src).group(1))
DROPPED_MOVE = re.search(r'DROPPED_MOVE\s*=\s*"([^"]*)"', src).group(1)
UNSOLVABLE = re.search(r'^UNSOLVABLE\s*=\s*"([^"]*)"', src, re.M).group(1)
print("HOLES_WEIGHTS", HOLES_WEIGHTS, "DROPPED", DROPPED_MOVE, "UNSOLVABLE", UNSOLVABLE)

moves = [m for m in lp_potential.moves_from_graph(GRAPH) if m.name() != DROPPED_MOVE]
cert = lp_potential.Certificate(
    weights=[Fraction(w) for w in HOLES_WEIGHTS],
    initial=UNSOLVABLE,
    goal_states=list(GRAPH["goal_states"]),
    moves=moves,
    margin=Fraction(1),
)
cert.conditions = lp_potential.check_exactly(cert)
h = lp_potential.heuristic_from(cert)
report = lp_potential.admissibility_report(h, GRAPH)
rows = lp_potential.candidates(cert, h, GRAPH, timestamp="2026-07-27T00:00:00Z")

print("\n--- row 1 (heuristic), GATED:")
print("  admissible:", rows[1]["payload"]["admissible"])
print("  counterexamples:", [c["state"] for c in rows[1]["payload"]["admissible_basis"]["counterexamples"]])

print("\n--- row 0 (invariant), UNGATED:")
p = rows[0]["payload"]
print("  keys:", sorted(p))
print("  has 'holds'?", "holds" in p, " has 'refuted'?", "refuted" in p)
print("  conditions:", p["conditions"])
print("  claim:", p["claim"])
print("  rendering:", p["rendering"])
print("  move_instances:", p["move_instances"])

# Is inv_closed actually true over the REAL move set?
full = lp_potential.moves_from_graph(GRAPH)
bad = [m.name() for m in full if m.delta(cert.weights) > 0]
print("\n  moves that RAISE the potential over the full move list:", bad)
print("  -> the invariant row's conditions.inv_closed=True is a false statement")
print("     about 'every legal move', and the sibling row proves it.")

# And the ungated headline for a certificate nobody checked at all:
unchecked = lp_potential.Certificate(
    weights=[Fraction(w) for w in HOLES_WEIGHTS], initial=UNSOLVABLE,
    goal_states=list(GRAPH["goal_states"]), moves=full, margin=Fraction(1),
)   # conditions left {} -- holds is False
print("\n--- a certificate with conditions={} (holds=False):")
print("  holds:", unchecked.holds)
j = unchecked.as_json()
print("  payload claim:", j["claim"])
print("  payload conditions:", j["conditions"])
print("  all(conditions.values()) as a naive reader computes it:",
      all(j["conditions"].values()))
