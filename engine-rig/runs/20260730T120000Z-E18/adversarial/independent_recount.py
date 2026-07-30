"""Adversarial recount of lp.incomplete, with every methodological choice flipped.

Run:  cd engine-rig && python runs/20260730T120000Z-E18/adversarial/independent_recount.py

Deliberate differences from tools/survey_numbers/lp_incomplete.py:

* Ground truth successors are built from `graph["edges"]` -- the table the
  *engine* reads -- not from `spec.triples`.  If the two disagree on any world,
  the module's "independent oracle" claim is worth something; if they agree
  everywhere, 2189 does not depend on the choice and the independence is
  cosmetic.  Also computed: `moves_from_graph`-derived successors, i.e. the
  engine's own deduped/sorted move list.
* BFS written here, not `fuzzlab.oracles.search`.
* The engine's verdict is taken from `potential.solve(...).status` by name
  (`no_linear_pagoda` / `certified` / anything else), never from
  `certificate is None` and never from `certificate_issued`.  The module's
  numerator uses `not certificate_issued`, which is the *collapsed* predicate
  2a1c30d exists to remove; this recount reports both so the difference is
  visible if it is ever nonzero.
* One solve per world instead of two.
"""

import json
import os
import sys
from collections import Counter, deque

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE_RIG = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
REPO = os.path.dirname(ENGINE_RIG)
for p in (REPO, ENGINE_RIG):
    if p not in sys.path:
        sys.path.insert(0, p)

from engines.lp_potential import potential          # noqa: E402
from fuzzlab import prng                            # noqa: E402
from fuzzlab.worlds import jumpgraph                # noqa: E402

SEED = 0x00005EEDC1E4F002
N = int(os.environ.get("ADV_N", "3000"))


def succ_from_edges(state, by_src):
    return sorted(e["dst_state"] for e in by_src.get(state, ()))


def succ_from_moves(state, moves):
    out = []
    for m in moves:
        if state[m.src] == "1" and state[m.over] == "1" and state[m.dst] == "0":
            cells = list(state)
            cells[m.src] = "0"
            cells[m.over] = "0"
            cells[m.dst] = "1"
            out.append("".join(cells))
    return sorted(out)


def reach(start, succ):
    seen = {start}
    q = deque([start])
    while q:
        s = q.popleft()
        for t in succ(s):
            if t not in seen:
                seen.add(t)
                q.append(t)
    return seen


def main():
    rows = []
    oracle_mismatch = []
    for i in range(N):
        seed = prng.derive(SEED, "jumpgraph", i)
        w = jumpgraph.generate(seed)
        spec, graph = w.spec, w.graph

        by_src = {}
        for e in graph["edges"]:
            by_src.setdefault(e["src_state"], []).append(e)
        moves = potential.moves_from_graph(graph)

        r_edges = reach(spec.initial, lambda s: succ_from_edges(s, by_src))
        r_moves = reach(spec.initial, lambda s: succ_from_moves(s, moves))
        r_trips = reach(spec.initial,
                        lambda s: succ_from_moves(
                            s, [potential.Move(*t) for t in spec.triples]))

        goals = set(spec.goal_states)
        reach_edges = bool(goals & r_edges)
        reach_moves = bool(goals & r_moves)
        reach_trips = bool(goals & r_trips)
        if not (reach_edges == reach_moves == reach_trips
                and r_edges == r_moves == r_trips):
            oracle_mismatch.append(
                {"i": i, "seed": seed,
                 "edges": len(r_edges), "moves": len(r_moves),
                 "triples": len(r_trips),
                 "goal_edges": reach_edges, "goal_moves": reach_moves,
                 "goal_triples": reach_trips})

        try:
            out = potential.solve(graph, spec.initial)
            status = out.status
            solver_status = out.solver_status
            err = False
        except potential.CertificateError:
            status, solver_status, err = "certificate_error", None, True
        except potential.LpUnavailable as exc:
            got = getattr(exc, "outcome", None)
            status = "lp_unavailable"
            solver_status = None if got is None else got.solver_status
            err = False

        rows.append({
            "i": i, "seed": seed, "n_pos": spec.n_pos,
            "reachable": reach_edges,
            "solvable_flag": spec.solvable,
            "status": status, "solver_status": solver_status,
            "certificate_error": err,
            "reach_size": len(r_edges),
        })

    unreach = [r for r in rows if not r["reachable"]]
    # two readings of "silent": the collapsed one the module uses, and the
    # status-word one 2a1c30d's rule implies.
    silent_collapsed = [r for r in unreach if r["status"] != "certified"]
    silent_by_name = [r for r in unreach if r["status"] == "no_linear_pagoda"]

    out = {
        "n": N,
        "campaign_seed": "0x%016X" % SEED,
        "goal_truly_unreachable": len(unreach),
        "goal_truly_reachable": len(rows) - len(unreach),
        "certificates": sum(1 for r in rows if r["status"] == "certified"),
        "no_certificate_collapsed": sum(1 for r in rows if r["status"] != "certified"),
        "no_linear_pagoda_by_name": sum(
            1 for r in rows if r["status"] == "no_linear_pagoda"),
        "certificate_error": sum(1 for r in rows if r["certificate_error"]),
        "numerator_collapsed": len(silent_collapsed),
        "numerator_by_status_word": len(silent_by_name),
        "denominator": len(unreach),
        "pct_collapsed": round(100.0 * len(silent_collapsed) / len(unreach), 1),
        "status_histogram": dict(sorted(Counter(r["status"] for r in rows).items())),
        "solver_status_histogram": dict(sorted(
            Counter(str(r["solver_status"]) for r in rows).items())),
        "oracle_edges_vs_triples_vs_movetable_mismatches": len(oracle_mismatch),
        "oracle_mismatch_sample": oracle_mismatch[:10],
        "generator_solvable_flag_vs_bfs_mismatches": sum(
            1 for r in rows if r["solvable_flag"] != r["reachable"]),
        "prefix_500": {
            "no_certificate_total": sum(
                1 for r in rows[:500] if r["status"] != "certified"),
            "no_certificate_pct": round(
                100.0 * sum(1 for r in rows[:500] if r["status"] != "certified") / 500, 1),
            "unreachable": sum(1 for r in rows[:500] if not r["reachable"]),
            "silent_and_unreachable": sum(
                1 for r in rows[:500]
                if not r["reachable"] and r["status"] != "certified"),
            "silent_and_reachable": sum(
                1 for r in rows[:500]
                if r["reachable"] and r["status"] != "certified"),
        },
        "silent_unreachable_indices_sha_input_count": len(silent_collapsed),
    }
    with open(os.path.join(HERE, "independent_indices.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump({"silent_unreachable_indices":
                   sorted(r["i"] for r in silent_collapsed),
                   "unreachable_indices": sorted(r["i"] for r in unreach)},
                  fh, sort_keys=True)
        fh.write("\n")
    json.dump(out, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
