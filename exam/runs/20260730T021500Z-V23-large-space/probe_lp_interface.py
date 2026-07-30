"""V23: can `lp_potential` walk the class (ii) path?

Five probes, all offline, all under a second each except where noted:

  A  what `solve()` actually reads off `graph`, established by deletion
  B  cost of materialising a peg1d graph as a function of n_pos (MEASURED)
  C  `solve()` on a geometry-only graph at large n_pos -- is the LP itself
     the bottleneck, or is the graph? (MEASURED)
  D  can an A2 comb transition be written as an `lp_potential` Move at all?
     (algebraic, checked by exhaustive role assignment)
  E  the smallest honest end-to-end: a comb level encoded as a state graph,
     handed to `solve()`.

Run:  python exam/runs/20260730T021500Z-V23-large-space/probe_lp_interface.py
"""

import json
import os
import sys
import time
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
for path in (REPO, os.path.join(REPO, "engine-rig")):
    if path not in sys.path:
        sys.path.insert(0, path)

from engines.lp_potential import potential as lp          # noqa: E402
from interop import peg1d                                  # noqa: E402

OUT = {}


def banner(text):
    print("\n" + "=" * 72)
    print(text)
    print("=" * 72)


# ------------------------------------------------------------------ probe A
def probe_a():
    banner("A. which keys of `graph` does solve() read?")
    full = peg1d.build_graph(6, "111111", goal_states=["100000"])
    keys = sorted(full)
    print("build_graph emits: %s" % keys)

    survived = []
    for key in keys:
        trimmed = {k: v for k, v in full.items() if k != key}
        try:
            lp.solve(trimmed, "111111", goal_states=["100000"])
        except KeyError as exc:
            survived.append(key)
            print("  removing %-18s -> KeyError(%s)  REQUIRED" % (key, exc))
        else:
            print("  removing %-18s -> ok" % key)
    OUT["A_required_keys"] = survived

    # and the granularity: how many LP rows come from how many edges?
    moves = lp.moves_from_graph(full)
    print("\n  n_pos=6: %d edges in the graph -> %d distinct move geometries"
          % (len(full["edges"]), len(moves)))
    print("  LP shape: 2*n = %d variables, %d move rows + %d goal rows + %d box rows"
          % (2 * 6, len(moves), 1, 2 * 6))
    OUT["A_granularity"] = {
        "n_pos": 6, "edges": len(full["edges"]), "distinct_geometries": len(moves),
        "lp_variables": 12, "lp_rows": len(moves) + 1 + 12,
    }


# ------------------------------------------------------------------ probe B
def probe_b():
    banner("B. cost of materialising the input, vs n_pos (MEASURED)")
    rows = []
    for n in range(6, 21):
        initial = "1" * n
        goals = ["1" + "0" * (n - 1)]
        t0 = time.perf_counter()
        states = peg1d.all_states(n)
        insts = peg1d.move_instances(n)
        edges = 0
        for state in states:
            for move in insts:
                if peg1d.legal(state, move):
                    edges += 1
        t1 = time.perf_counter()
        rows.append({"n_pos": n, "states": len(states), "edges": edges,
                     "geometries": len(insts), "enumerate_s": round(t1 - t0, 4)})
        print("  n=%2d  states=%9d  edges=%10d  geometries=%3d  enumerate=%7.3fs"
              % (n, len(states), edges, len(insts), t1 - t0))
        if t1 - t0 > 20:
            print("  (stopping: next n doubles this)")
            break
    OUT["B_materialisation"] = rows


# ------------------------------------------------------------------ probe C
def probe_c():
    banner("C. solve() on a geometry-only graph -- the LP alone (MEASURED)")
    # `moves_from_graph` de-duplicates, so a graph carrying one edge per
    # geometry produces exactly the LP a fully materialised graph produces.
    rows = []
    for n in (6, 12, 25, 50, 100, 250, 500, 1000):
        insts = peg1d.move_instances(n)
        graph = {
            "n_pos": n,
            "goal_states": ["1" + "0" * (n - 1)],
            "edges": [{"positions": [m["src"], m["over"], m["dst"]],
                       "src_state": "", "dst_state": "", "move": ""}
                      for m in insts],
        }
        initial = "1" * n
        t0 = time.perf_counter()
        outcome = lp.solve(graph, initial, goal_states=["1" + "0" * (n - 1)])
        t1 = time.perf_counter()
        rows.append({"n_pos": n, "geometries": len(insts),
                     "status": outcome.status, "solve_s": round(t1 - t0, 4)})
        print("  n_pos=%4d  geometries=%4d  status=%-16s  %6.3fs"
              % (n, len(insts), outcome.status, t1 - t0))
    OUT["C_lp_only"] = rows

    # sanity: does the geometry-only graph agree with the materialised one?
    full = peg1d.build_graph(8, "1" * 8, goal_states=["1" + "0" * 7])
    thin = {"n_pos": 8, "goal_states": ["1" + "0" * 7],
            "edges": [{"positions": [m["src"], m["over"], m["dst"]]}
                      for m in peg1d.move_instances(8)]}
    a = lp.solve(full, "1" * 8, goal_states=["1" + "0" * 7])
    b = lp.solve(thin, "1" * 8, goal_states=["1" + "0" * 7])
    print("\n  materialised graph -> %s ; geometry-only graph -> %s ; agree=%s"
          % (a.status, b.status, a.status == b.status))
    OUT["C_agreement"] = {"materialised": a.status, "geometry_only": b.status,
                          "agree": a.status == b.status}


# ------------------------------------------------------------------ probe D
def probe_d():
    banner("D. can an A2 cart move be written as an lp_potential Move?")
    # lp_potential builds one LP row per Move as:
    #     row[dst] += 1 ; row[src] -= 1 ; row[over] -= 1
    # so the coefficient vector of every expressible transition sums to -1,
    # whatever the three indices are (including collisions).
    sums = set()
    n = 5
    for src in range(n):
        for over in range(n):
            for dst in range(n):
                row = [0.0] * n
                row[dst] += 1.0
                row[src] -= 1.0
                row[over] -= 1.0
                sums.add(sum(row))
    print("  coefficient-sum over all %d role assignments (n=%d): %s"
          % (n ** 3, n, sorted(sums)))
    OUT["D_coefficient_sums"] = sorted(sums)

    # An A2 command changes the occupancy vector by: cart leaves c, cart enters
    # c'; and if c' is an unlatched switch, that latch bit turns on.  Coefficient
    # sums 0 (plain move) or +1 (move that latches).  Neither is -1.
    print("  A2 plain cart move   : coefficient sum = %d" % 0)
    print("  A2 latching move     : coefficient sum = %d" % 1)
    print("  A2 blocked move/self : coefficient sum = %d" % 0)
    print("  lp_potential Move    : coefficient sum = -1, always")
    print("  => no assignment of (src, over, dst) expresses an A2 transition.")
    OUT["D_verdict"] = {
        "lp_move_coefficient_sum": -1,
        "a2_plain_move": 0,
        "a2_latching_move": 1,
        "expressible": False,
    }


# ---------------------------------------------------------- comb encoding
def comb_level(corridor_len, start_col, goal_col):
    """The shipped comb_open geometry, small enough to enumerate."""
    width = corridor_len + 2
    border = "#" * width
    upper = "#" + "s" * corridor_len + "#"
    corridor = list("#" + "." * corridor_len + "#")
    corridor[start_col] = "S"
    corridor[goal_col] = "G"
    rows = [border, upper, "".join(corridor), upper, border]
    switches = ([(1, c) for c in range(1, corridor_len + 1)]
                + [(3, c) for c in range(1, corridor_len + 1)])
    return {"rows": rows, "start": (2, start_col), "goal": (2, goal_col),
            "switches": switches, "width": width, "height": 5}


DELTA = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}


def comb_state_graph(level, forbidden=()):
    """Full (cart, latch-mask) graph of a comb level, in lp_potential's shape.

    Bit layout: cells 0..C-1 are `cart is here`, cells C..C+S-1 are
    `switch j is latched`.  This is the most faithful bitstring encoding
    available -- potential = sum of w over occupied cells, which is what
    `Certificate.potential` computes.
    """
    rows, height, width = level["rows"], level["height"], level["width"]
    cells = [(r, c) for r in range(height) for c in range(width)
             if rows[r][c] != "#"]
    index = {cell: i for i, cell in enumerate(cells)}
    switches = list(level["switches"])
    sw_index = {c: i for i, c in enumerate(switches)}
    C, S = len(cells), len(switches)
    n_pos = C + S
    actions = [a for a in ("UP", "DOWN", "LEFT", "RIGHT") if a not in forbidden]

    def encode(cart, mask):
        bits = ["0"] * n_pos
        bits[index[cart]] = "1"
        for j in range(S):
            if mask >> j & 1:
                bits[C + j] = "1"
        return "".join(bits)

    def step(cart, action):
        dr, dc = DELTA[action]
        nxt = (cart[0] + dr, cart[1] + dc)
        if not (0 <= nxt[0] < height and 0 <= nxt[1] < width):
            return cart
        if rows[nxt[0]][nxt[1]] == "#":
            return cart
        return nxt

    start_mask = 1 << sw_index[level["start"]] if level["start"] in sw_index else 0
    start = (level["start"], start_mask)
    seen = {start}
    stack = [start]
    edges = []
    while stack:
        cart, mask = stack.pop()
        src_text = encode(cart, mask)
        for action in actions:
            nxt = step(cart, action)
            nmask = mask
            if nxt in sw_index:
                nmask |= 1 << sw_index[nxt]
            node = (nxt, nmask)
            if node == (cart, mask):
                continue
            edges.append({"src_state": src_text, "move": action,
                          "positions": [index[cart], index[cart], index[nxt]],
                          "dst_state": encode(*node)})
            if node not in seen:
                seen.add(node)
                stack.append(node)
    full_mask = (1 << S) - 1
    goals = [encode(level["goal"], full_mask)]
    return {
        "n_pos": n_pos, "cells": C, "switches": S,
        "states": sorted(encode(c, m) for c, m in seen),
        "goal_states": goals, "goal": goals[0],
        "edges": edges,
        "initial": encode(*start),
    }


# ------------------------------------------------------------------ probe E
def probe_e():
    banner("E. a real comb level, materialised, handed to solve()")
    rows = []
    for corridor_len in (2, 3, 4, 5, 6, 7, 8, 9, 10):
        level = comb_level(corridor_len, 1, corridor_len)
        t0 = time.perf_counter()
        graph = comb_state_graph(level, forbidden=("LEFT",))
        t1 = time.perf_counter()
        entry = {"corridor_len": corridor_len, "n_pos": graph["n_pos"],
                 "reachable_states": len(graph["states"]),
                 "edges": len(graph["edges"]),
                 "build_s": round(t1 - t0, 4)}
        t2 = time.perf_counter()
        try:
            outcome = lp.solve(graph, graph["initial"])
            entry["status"] = outcome.status
            entry["certificate"] = (outcome.certificate.as_json()
                                    if outcome.certificate else None)
        except Exception as exc:                                  # noqa: BLE001
            entry["status"] = "%s: %s" % (type(exc).__name__, exc)
        entry["solve_s"] = round(time.perf_counter() - t2, 4)
        rows.append(entry)
        print("  len=%2d  n_pos=%3d  states=%8d  edges=%9d  build=%6.3fs  "
              "solve=%6.3fs  -> %s"
              % (corridor_len, graph["n_pos"], len(graph["states"]),
                 len(graph["edges"]), entry["build_s"], entry["solve_s"],
                 entry["status"]))
        if t1 - t0 > 15:
            print("  (stopping: next corridor cell doubles the mask space)")
            break
    OUT["E_comb"] = rows

    # What does the LP claim, and is the claim about the right system?
    last = rows[-1]
    if last.get("certificate"):
        print("\n  a certificate WAS returned; check it against the real system:")
    else:
        print("\n  no certificate at any size tried.")

    # The soundness question: lp_potential's re-check only looks at its own
    # Move list, whose delta is w[dst]-w[src]-w[over].  Compare that against the
    # true potential delta of each edge.
    level = comb_level(4, 1, 4)
    graph = comb_state_graph(level, forbidden=("LEFT",))
    moves = lp.moves_from_graph(graph)
    print("  n_pos=%d, %d edges -> %d distinct (src,over,dst) triples"
          % (graph["n_pos"], len(graph["edges"]), len(moves)))
    weights = [Fraction(i + 1) for i in range(graph["n_pos"])]
    mismatched = 0
    for edge in graph["edges"]:
        src, over, dst = edge["positions"]
        modelled = weights[dst] - weights[src] - weights[over]
        occ_s = sum((weights[i] for i, ch in enumerate(edge["src_state"]) if ch == "1"),
                    Fraction(0))
        occ_d = sum((weights[i] for i, ch in enumerate(edge["dst_state"]) if ch == "1"),
                    Fraction(0))
        if modelled != occ_d - occ_s:
            mismatched += 1
    print("  edges whose lp_potential-modelled delta != the true potential "
          "delta: %d of %d" % (mismatched, len(graph["edges"])))
    OUT["E_delta_mismatch"] = {"n_pos": graph["n_pos"],
                               "edges": len(graph["edges"]),
                               "mismatched": mismatched}


if __name__ == "__main__":
    probe_a()
    probe_b()
    probe_c()
    probe_d()
    probe_e()
    path = os.path.join(HERE, "probe_lp_interface.json")
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(OUT, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("\nwrote %s" % path)
