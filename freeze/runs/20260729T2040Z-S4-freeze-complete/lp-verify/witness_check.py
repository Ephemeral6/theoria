"""Independent re-derivation of the E17 peg4 witness (S4 verification, read-only wrt engine-rig).

Own state space, own BFS, own exact-rational re-check.  Then the real engine.
"""
import os
import sys
from collections import deque
from fractions import Fraction

ENGINE_RIG = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..", "engine-rig"))
sys.path.insert(0, ENGINE_RIG)

N = 4
GOAL = "0100"

# ---- my own geometry, written from the rules, not imported ----
GEOMS = []
for i in range(N):
    for step in (1, -1):
        over, dst = i + step, i + 2 * step
        if 0 <= dst < N:
            GEOMS.append((i, over, dst))
GEOMS.sort()

def states(n):
    return ["".join(("1" if (m >> (n - 1 - k)) & 1 else "0") for k in range(n))
            for m in range(2 ** n)]

def legal(s, g):
    src, over, dst = g
    return s[src] == "1" and s[over] == "1" and s[dst] == "0"

def apply_(s, g):
    src, over, dst = g
    c = list(s)
    c[src] = "0"; c[over] = "0"; c[dst] = "1"
    return "".join(c)

def bfs(start, goal, geoms):
    if start == goal:
        return 0, []
    seen = {start: (None, None)}
    q = deque([start])
    while q:
        s = q.popleft()
        for g in geoms:
            if legal(s, g):
                t = apply_(s, g)
                if t not in seen:
                    seen[t] = (s, g)
                    if t == goal:
                        path = []
                        cur = t
                        while seen[cur][0] is not None:
                            path.append((seen[cur][0], seen[cur][1], cur))
                            cur = seen[cur][0]
                        return len(path), list(reversed(path))
                    q.append(t)
    return None, None

print("=== 1. My own BFS over the FULL geometry set ===")
print("geometries:", ["jump(%d,%d,%d)" % g for g in GEOMS])
d, path = bfs("0011", GOAL, GEOMS)
print("distance 0011 -> 0100 (full moves):", d)
for a, g, b in (path or []):
    print("    %s --jump(%d,%d,%d)--> %s" % (a, g[0], g[1], g[2], b))

WITHHELD = (3, 2, 1)
reduced_geoms = [g for g in GEOMS if g != WITHHELD]
d2, _ = bfs("0011", GOAL, reduced_geoms)
print("distance 0011 -> 0100 with jump(3,2,1) withheld:", d2)

print()
print("=== 2. Cross-check against the committed fixture's own table ===")
from fixtures import peg4
ref = peg4.generate()
print("fixture distance_to_goal['0011'] =", ref["distance_to_goal"]["0011"])
print("fixture solvable['1101']        =", ref["solvable"]["1101"])
print("my geoms == fixture positions   :",
      sorted(GEOMS) == sorted(tuple(m["positions"]) for m in
                             [{"positions": [m["src"], m["over"], m["dst"]]}
                              for m in peg4.move_instances()]))

print()
print("=== 3. The real engine, jump(3,2,1) withheld ===")
from engines.lp_potential.potential import (
    Move, check_exactly, moves_from_graph, premises_against_graph, solve,
)
from engines import lp_potential
from heldout import peg

full = peg.graph(N, GOAL)
ok, probs = peg.matches_fixture_peg4()
print("heldout/peg.py matches committed Fixture C:", ok, probs)

reduced = peg.graph_minus_geometry(full, WITHHELD)
print("moves the engine is handed (reduced):",
      [m.name() for m in moves_from_graph(reduced)])

outcome = solve(reduced, "0011", goal_states=[GOAL])
print("outcome.status  :", outcome.status)
cert = outcome.certificate
print("weights         :", [str(w) for w in cert.weights])
print("conditions      :", cert.conditions)
print("holds           :", cert.holds)
print("claim           :", cert.as_json()["claim"])
print("rendering       :", cert.as_json()["rendering"])

print()
print("--- my own exact re-check of the three conditions ---")
w = [Fraction(x) for x in cert.weights]
def pot(s):
    return sum((w[i] for i, c in enumerate(s) if c == "1"), Fraction(0))
print("pot(0011) =", pot("0011"), "  pot(0100) =", pot(GOAL))
for g in GEOMS:
    delta = w[g[2]] - w[g[0]] - w[g[1]]
    tag = "  <== WITHHELD" if g == WITHHELD else ""
    print("  jump(%d,%d,%d): delta = %s  %s%s"
          % (g[0], g[1], g[2], delta, "OK(<=0)" if delta <= 0 else "RAISES",  tag))

print()
print("=== 4. The emit gate, both graphs ===")
h = lp_potential.heuristic_from(cert)
emitted_full = lp_potential.candidates(cert, h, full)
emitted_reduced = lp_potential.candidates(cert, h, reduced)
print("candidates(..., graph=FULL)    -> %d rows" % len(emitted_full))
print("candidates(..., graph=REDUCED) -> %d rows" % len(emitted_reduced))
print("premises_against_graph(cert, FULL)   :", premises_against_graph(cert, full))
print("premises_against_graph(cert, REDUCED):", premises_against_graph(cert, reduced))
if emitted_reduced:
    inv = emitted_reduced[0]
    print()
    print("the invariant row that a partial-evidence caller emits:")
    for k in ("engine", "kind", "status"):
        print("   %-12s %r" % (k, inv.get(k)))
    p = inv["payload"]
    for k in ("claim", "holds", "conditions", "move_instances"):
        print("   payload.%-16s %r" % (k, p.get(k)))
    print("   payload.premise_check.sound_over_graph %r"
          % p["premise_check"]["sound_over_graph"])
