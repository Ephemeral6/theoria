"""ADVERSARIAL re-derivation of the E15 census -- independent of engines/lp_potential.

Builds the LP from `spec.triples` with scipy directly and reads `result.status`
off HiGHS.  Nothing here imports `engines.lp_potential`.  Ground truth is my own
forward BFS.  Output: rederived.jsonl + REDERIVED.json, then a diff against
census.jsonl.
"""

import json
import os
import sys
import time
from collections import Counter, deque
from fractions import Fraction

import numpy as np
from scipy.optimize import linprog

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE_RIG = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ENGINE_RIG)
for path in (ENGINE_RIG, REPO):
    if path not in sys.path:
        sys.path.insert(0, path)

from fuzzlab import prng                                           # noqa: E402
from fuzzlab.worlds import jumpgraph                               # noqa: E402

CAMPAIGN_SEED = 0x00005EEDC1E4F002
FAMILY = "jumpgraph"
N_WORLDS = 3000
WIDER = (100, 10 ** 4, 10 ** 6)


def bfs(initial, triples):
    seen = {initial}
    q = deque([initial])
    while q:
        st = q.popleft()
        for s, o, d in triples:
            if st[s] == "1" and st[o] == "1" and st[d] == "0":
                c = list(st)
                c[s] = c[o] = "0"
                c[d] = "1"
                nxt = "".join(c)
                if nxt not in seen:
                    seen.add(nxt)
                    q.append(nxt)
    return seen


def lp_status(n, triples, initial, goals, margin=1, bound=10):
    """Return (highs_status, x) building the LP from the TRIPLES, not the graph."""
    rows, rhs = [], []
    geoms = sorted(set(triples), key=lambda t: (t[0], t[2]))
    for s, o, d in geoms:
        row = [0.0] * (2 * n)
        row[d] += 1.0
        row[s] -= 1.0
        row[o] -= 1.0
        rows.append(row)
        rhs.append(0.0)
    start = [1 if c == "1" else 0 for c in initial]
    for g in goals:
        row = [0.0] * (2 * n)
        occ = [1 if c == "1" else 0 for c in g]
        for i in range(n):
            row[i] += start[i] - occ[i]
        rows.append(row)
        rhs.append(-float(margin))
    for i in range(n):
        r = [0.0] * (2 * n)
        r[i], r[n + i] = 1.0, -1.0
        rows.append(r)
        rhs.append(0.0)
        r = [0.0] * (2 * n)
        r[i], r[n + i] = -1.0, -1.0
        rows.append(r)
        rhs.append(0.0)
    c = [0.0] * n + [1.0] * n
    bounds = [(-bound, bound)] * n + [(0, bound)] * n
    res = linprog(c=c, A_ub=np.array(rows, dtype=float),
                  b_ub=np.array(rhs, dtype=float), bounds=bounds, method="highs")
    return int(res.status), (list(res.x[:n]) if res.x is not None else None)


def exact_holds(weights, triples, initial, goals, margin=1):
    w = [Fraction(x).limit_denominator(1000) for x in weights]

    def pot(state):
        return sum((w[i] for i, ch in enumerate(state) if ch == "1"), Fraction(0))

    start = pot(initial)
    inv = all(w[d] - w[s] - w[o] <= 0 for s, o, d in triples)
    gb = all(pot(g) - start >= Fraction(margin) for g in goals)
    return {"inv_closed": inv, "goal_break": gb, "holds": inv and gb,
            "weights": [str(x) for x in w],
            "initial_potential": str(start),
            "goal_gaps": [str(pot(g) - start) for g in goals]}


def main():
    t0 = time.time()
    rows = []
    triple_set_mismatch = []
    for i in range(N_WORLDS):
        seed = prng.derive(CAMPAIGN_SEED, FAMILY, i)
        world = jumpgraph.generate(seed)
        spec, graph = world.spec, world.graph
        n = spec.n_pos

        # independence check: does the engine's move set (from graph edges) equal
        # the spec's triple set?
        from_edges = sorted({tuple(e["positions"]) for e in graph["edges"]})
        if from_edges != sorted(set(spec.triples)):
            triple_set_mismatch.append(
                {"index": i, "seed": seed,
                 "only_in_spec": [list(t) for t in
                                  sorted(set(spec.triples) - set(from_edges))],
                 "only_in_edges": [list(t) for t in
                                   sorted(set(from_edges) - set(spec.triples))]})

        reach = bfs(spec.initial, spec.triples)
        unreachable = not any(g in reach for g in spec.goal_states)

        st, x = lp_status(n, spec.triples, spec.initial, spec.goal_states)
        row = {"index": i, "seed": seed, "n_pos": n,
               "goal_truly_unreachable": unreachable,
               "highs_status_bound10": st,
               "reachable_size": len(reach)}
        if st == 0:
            row["exact"] = exact_holds(x, spec.triples, spec.initial,
                                       spec.goal_states)
        if st != 0 and unreachable:
            wide = []
            for b in WIDER:
                s2, x2 = lp_status(n, spec.triples, spec.initial,
                                   spec.goal_states, bound=b)
                e = {"bound": b, "highs_status": s2}
                if s2 == 0:
                    e["exact"] = exact_holds(x2, spec.triples, spec.initial,
                                             spec.goal_states)
                wide.append(e)
            row["wider"] = wide
        rows.append(row)

    with open(os.path.join(HERE, "rederived.jsonl"), "w", encoding="utf-8",
              newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")

    unreach = [r for r in rows if r["goal_truly_unreachable"]]
    silent = [r for r in rows if r["highs_status_bound10"] != 0]
    silent_unreach = [r for r in unreach if r["highs_status_bound10"] != 0]
    st2 = [r for r in silent_unreach if r["highs_status_bound10"] == 2]
    widened_ok = [r for r in silent_unreach
                        if any(e["highs_status"] == 0 for e in r.get("wider", []))]
    summary = {
        "worlds": len(rows),
        "highs_status_counts": dict(sorted(Counter(
            r["highs_status_bound10"] for r in rows).items())),
        "n_rows_status0": sum(
            1 for r in rows if r["highs_status_bound10"] == 0),
        "n_status0_exact_recheck_bad": sum(
            1 for r in rows if r["highs_status_bound10"] == 0
            and not r["exact"]["holds"]),
        "no_certificate": len(silent),
        "goal_truly_unreachable": len(unreach),
        "silent_and_truly_unreachable": len(silent_unreach),
        "status_2_at_bound_10": len(st2),
        "incompleteness_rate_pct": round(
            100.0 * len(silent_unreach) / len(unreach), 1),
        "still_infeasible_when_widened": len(silent_unreach) - len(widened_ok),
        "feasible_when_widened": len(widened_ok),
        "widened_box_rows": [
            {"index": r["index"], "seed": r["seed"],
             "first": next(e for e in r["wider"] if e["highs_status"] == 0)}
            for r in widened_ok],
        "triple_set_mismatch_count": len(triple_set_mismatch),
        "triple_set_mismatch_sample": triple_set_mismatch[:3],
        "wall_seconds": round(time.time() - t0, 1),
    }
    with open(os.path.join(HERE, "REDERIVED.json"), "w", encoding="utf-8",
              newline="\n") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
