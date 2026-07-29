"""Attack (a): the gate reads the WRONG distance table.

`admissibility_report(heuristic, graph)` iterates `graph["distance_to_goal"]`,
which is the distance to the GRAPH's goal set.  `heuristic` is about
`certificate.goal_states`, which `solve_certificate(graph, initial, goal_states=...)`
and `lp_potential.run(..., goal_states=...)` let the caller choose freely.

When they differ, the empirical half of `entitlement()` measures a different
claim than the one the headline makes -- and the D-035 hazard the gate was
installed to catch (an incomplete move list) walks straight through it.
"""
import json
import os
import sys
from collections import deque
from fractions import Fraction

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from engines import lp_potential
from engines.lp_potential.potential import Certificate

GRAPH = json.load(open("fixtures/data/peg4_graph.json"))
EDGES = [(e["src_state"], e["dst_state"]) for e in GRAPH["edges"]]
BACK = {}
for s, d in EDGES:
    BACK.setdefault(d, []).append(s)
FULL = lp_potential.moves_from_graph(GRAPH)


def true_distance(goals):
    dist = {g: 0 for g in goals}
    q = deque(goals)
    while q:
        s = q.popleft()
        for p in BACK.get(s, ()):
            if p not in dist:
                dist[p] = dist[s] + 1
                q.append(p)
    return dist


print("graph goal_states:", GRAPH["goal_states"])
print("states with a finite distance_to_goal:",
      [s for s, v in GRAPH["distance_to_goal"].items() if v is not None])

# --- 1. a custom goal set, straight through the public entry point ------------
CUSTOM = ["1010"]
cert, heur = lp_potential.run(GRAPH, "0111", goal_states=CUSTOM)
print("\nlp_potential.run(graph, '1110', goal_states=%r) -> certificate holds=%s"
      % (CUSTOM, cert.holds))
rows = lp_potential.candidates(cert, heur, GRAPH, timestamp="2026-07-27T00:00:00Z")
p = rows[1]["payload"]
print("  heuristic payload goal_states:", p["goal_states"])
print("  admissible:", p["admissible"], "|", p["admissible_basis"]["empirical_check"])
print("  rows the check actually looked at:",
      [(r["state"], r["true_distance"]) for r in p["admissibility_check"]])
d = true_distance(CUSTOM)
print("  ...but the TRUE distances to %r are:" % CUSTOM,
      sorted((s, v) for s, v in d.items()))
print("  -> not one state in the check is measured against the heuristic's own goal.")

# --- 2. the D-035 hazard, now invisible to the gate ---------------------------
# Same shape as tests/test_lp_potential.py::_certificate_missing_one_move, but
# with a custom goal set.  The certificate passes all three exact conditions over
# a 3-of-4 move list; h claims `inf` for a state one move from its own goal.
for dropped in FULL:
    subset = [m for m in FULL if m != dropped]
    for w in [(a, b, c, e) for a in range(-4, 5) for b in range(-4, 5)
              for c in range(-4, 5) for e in range(-4, 5)]:
        c2 = Certificate(weights=[Fraction(x) for x in w], initial="0111",
                         goal_states=list(CUSTOM), moves=subset, margin=Fraction(1))
        c2.conditions = lp_potential.check_exactly(c2)
        if not c2.holds:
            continue
        h2 = lp_potential.heuristic_from(c2)
        rep = lp_potential.admissibility_report(h2, GRAPH)
        pay = h2.as_json(rep)
        if not pay["admissible"]:
            continue
        bad = [(s, h2.value(s), dist) for s, dist in d.items() if h2.value(s) > dist]
        if bad:
            print("\nCOUNTEREXAMPLE through the gate:")
            print("  weights      :", list(w))
            print("  moves        :", [m.name() for m in subset], "(dropped %s)" % dropped.name())
            print("  goal_states  :", CUSTOM)
            print("  conditions   :", c2.conditions, "-> holds =", c2.holds)
            print("  payload says : admissible =", pay["admissible"],
                  "|", pay["admissible_basis"]["empirical_check"])
            for s, hv, dist in bad[:4]:
                print("  BUT h(%s) = %s while the true distance to %r is %d"
                      % (s, hv, CUSTOM, dist))
            emitted = lp_potential.candidates(c2, h2, GRAPH, timestamp="2026-07-27T00:00:00Z")
            print("  emitted heuristic row admissible:", emitted[1]["payload"]["admissible"])
            print("  emitted invariant row claim     :", emitted[0]["payload"]["claim"])
            sys.exit(0)
print("\nno counterexample found")
