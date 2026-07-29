"""Independent recomputation of the lp_potential held-out numbers.

The state space, the move geometry and the BFS ground truth are re-derived here
rather than imported from `heldout/peg.py`, so agreement is evidence.  Only the
engine itself (`solve_certificate`) is shared -- it is the thing under test.

It also runs the call the delivered harness does NOT run: `candidates(cert, h,
reduced_graph)` -- the emit gate handed the same partial evidence the LP was fitted
on, which is what a caller who only ever saw part of the geometry would pass.
"""
import json
import os
import sys
from collections import deque
from fractions import Fraction

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from engines import lp_potential
from engines.lp_potential.potential import (
    CertificateError, LpUnavailable, Move, heuristic_from, solve_certificate,
)

N_POSITIONS = (4, 5, 6, 7)


def states_of(n):
    return sorted("".join(bits) for bits in _tuples(n))


def _tuples(n):
    out = [()]
    for _ in range(n):
        out = [t + (b,) for t in out for b in ("0", "1")]
    return out


def geoms(n):
    out = []
    for i in range(n):
        for step in (1, -1):
            over, dst = i + step, i + 2 * step
            if 0 <= dst < n:
                out.append((i, over, dst))
    return sorted(out, key=lambda m: (m[0], m[2]))


def legal(s, m):
    return s[m[0]] == "1" and s[m[1]] == "1" and s[m[2]] == "0"


def apply(s, m):
    c = list(s)
    c[m[0]] = "0"
    c[m[1]] = "0"
    c[m[2]] = "1"
    return "".join(c)


def bfs_dist(n, goal):
    """Backwards BFS from the goal over reversed edges -> distance of every state."""
    ms = geoms(n)
    preds = {}
    for s in states_of(n):
        for m in ms:
            if legal(s, m):
                preds.setdefault(apply(s, m), []).append(s)
    dist = {goal: 0}
    q = deque([goal])
    while q:
        cur = q.popleft()
        for p in preds.get(cur, ()):
            if p not in dist:
                dist[p] = dist[cur] + 1
                q.append(p)
    return {s: dist.get(s) for s in states_of(n)}


def build_graph(n, goal, drop=None):
    ms = geoms(n)
    edges = []
    for s in states_of(n):
        for m in ms:
            if legal(s, m):
                if drop is not None and m == drop:
                    continue
                edges.append({"src_state": s,
                              "move": "jump(%d,%d,%d)" % m,
                              "positions": list(m),
                              "dst_state": apply(s, m)})
    return {"n_pos": n, "goal": goal, "goal_states": [goal],
            "states": states_of(n), "move_instances": [
                {"src": m[0], "over": m[1], "dst": m[2]} for m in ms],
            "edges": edges,
            "distance_to_goal": bfs_dist(n, goal)}


def geometries_in(graph):
    seen = []
    for e in graph["edges"]:
        key = tuple(e["positions"])
        if key not in seen:
            seen.append(key)
    return sorted(seen)


def admissibility(cert, dist):
    h = heuristic_from(cert)
    excluded = {cert.initial, *cert.goal_states}
    viol = tested = 0
    for s in sorted(dist):
        d = dist[s]
        if d is None or s in excluded:
            continue
        tested += 1
        if h.value(s) > d:
            viol += 1
    return viol, tested


def main():
    n_instances = cases = silent = errors = certs = 0
    inv_hits = false_certs = 0
    gate_full_withheld = gate_full_let_through = 0
    gate_reduced_let_through = 0          # <-- the production-shaped call
    arith = 0
    ho_viol = 0
    base_certs = base_silent = base_false = base_viol = base_tested = 0
    empty_geometry_holdouts = 0
    witness = None

    for n in N_POSITIONS:
        for gi in range(1, n - 1):
            goal = "".join("1" if i == gi else "0" for i in range(n))
            full = build_graph(n, goal)
            dist = full["distance_to_goal"]
            gs = geometries_in(full)
            for s in full["states"]:
                if s.count("1") not in (n - 1, n - 2) or s == goal:
                    continue
                n_instances += 1
                reachable = dist[s] is not None
                # baseline
                try:
                    bc = solve_certificate(full, s, goal_states=[goal])
                except (LpUnavailable, CertificateError):
                    bc = "err"
                if bc == "err":
                    pass
                elif bc is None:
                    base_silent += 1
                else:
                    base_certs += 1
                    if reachable:
                        base_false += 1
                    v, t = admissibility(bc, dist)
                    base_viol += v
                    base_tested += t
                # held-out
                for g in gs:
                    cases += 1
                    reduced = build_graph(n, goal, drop=g)
                    if not [e for e in full["edges"] if tuple(e["positions"]) == g]:
                        empty_geometry_holdouts += 1
                    try:
                        c = solve_certificate(reduced, s, goal_states=[goal])
                    except (LpUnavailable, CertificateError):
                        errors += 1
                        continue
                    if c is None:
                        silent += 1
                        continue
                    certs += 1
                    mv = Move(*g)
                    ok = mv.delta(c.weights) <= 0
                    inv_hits += int(ok)
                    if reachable:
                        false_certs += 1
                        if witness is None and n == 4 and goal == "0100" and s == "0011":
                            witness = (g, [str(w) for w in c.weights])
                    h = heuristic_from(c)
                    if lp_potential.candidates(c, h, full) == []:
                        gate_full_withheld += 1
                    else:
                        gate_full_let_through += 1
                    if lp_potential.candidates(c, h, reduced) != []:
                        gate_reduced_let_through += 1
                    pr = lp_potential.premises_against_graph(c, full)
                    if pr["moves_raising_potential"]:
                        arith += 1
                    v, t = admissibility(c, dist)
                    ho_viol += v

    got = {
        "instances": n_instances, "cases": cases, "silent": silent,
        "errors": errors, "certificates": certs, "inv_closed_hits": inv_hits,
        "inv_rate_pct": "%.1f" % (100.0 * inv_hits / certs),
        "false_certificates": false_certs,
        "emit_gate_let_through_FULL_graph": gate_full_let_through,
        "emit_gate_let_through_REDUCED_graph": gate_reduced_let_through,
        "caught_by_raised_potential": arith,
        "heldout_admissibility_violations": ho_viol,
        "baseline_certificates": base_certs, "baseline_silent": base_silent,
        "baseline_false": base_false,
        "baseline_states_tested": base_tested,
        "baseline_violations": base_viol,
        "vacuous_geometry_holdouts": empty_geometry_holdouts,
        "peg4_0100_0011_witness": witness,
    }
    print(json.dumps(got, indent=2))

    with open("runs/20260729T034043Z-E17-held-out-validation/results.json",
              encoding="utf-8") as fh:
        d = json.load(fh)["lp_potential"]
    print("\n--- results.json ---")
    print(json.dumps({"corpus": d["corpus"],
                      "held_out_L1": d["held_out_L1"],
                      "baseline": d["baseline_complete_graph"]}, indent=2))


if __name__ == "__main__":
    main()
