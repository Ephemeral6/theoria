"""What the shipped class (ii) truth records actually contain, and what it cost
to produce them.  Reads the shipped truth artifact; writes nothing outside this
run directory and never calls `verdict.build()` (which would rewrite specs).
"""

import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from exam.grading.rubrics_verdict import (            # noqa: E402
    Level, check_certificate, components, relaxed_distance, relaxed_edges,
    row_col_deltas,
)
from exam.papers.verdict import positional_states, subset_lower_bound  # noqa: E402

TRUTH = os.path.join(REPO, "exam", "artifacts", "truth", "p15-verdict-a2.truth.json")
doc = json.load(open(TRUTH, encoding="utf-8"))
items = doc["items"] if isinstance(doc, dict) and "items" in doc else doc
if isinstance(items, dict):
    items = list(items.values())

report = []
for item in items:
    truth = item["truth"] if "truth" in item else item
    if truth.get("class") != "large_unsolvable":
        continue
    level_doc = json.loads(truth["level_blob"])
    level = Level(level_doc)
    cert = json.loads(truth["certificate_blob"]) if truth["certificate_blob"] else None

    t0 = time.perf_counter()
    graph = relaxed_edges(level)
    t_graph = time.perf_counter() - t0
    n_nodes = len(graph)
    n_edges = sum(len(v) for v in graph.values()) // 2

    t0 = time.perf_counter()
    rep = components(graph)
    t_comp = time.perf_counter() - t0

    t0 = time.perf_counter()
    result = check_certificate(cert, level) if cert else None
    t_check = time.perf_counter() - t0

    t0 = time.perf_counter()
    pos = positional_states(level)
    t_pos = time.perf_counter() - t0

    t0 = time.perf_counter()
    bound = subset_lower_bound(level)
    t_bound = time.perf_counter() - t0

    dist = None
    t_dist = 0.0
    if cert and cert.get("kind") == "counting":
        t0 = time.perf_counter()
        dist = relaxed_distance(level, level.start, level.goal)
        t_dist = time.perf_counter() - t0

    row = {
        "item_id": item.get("item_id"),
        "variant_id": truth["spec"]["variant_id"],
        "level_id": level_doc["level_id"],
        "board": "%dx%d" % (len(level_doc["rows"]), len(level_doc["rows"][0])),
        "claim": truth["claim"],
        "certificate": cert,
        "certificate_kind": cert["kind"] if cert else None,
        "witness": truth["witness"],
        "witness_source": truth.get("witness_source"),
        "state_space": {k: v for k, v in truth["state_space"].items()
                        if k != "arithmetic"},
        "search_credible": truth["search_credible"],
        "switch_count": len(level_doc.get("switches", ())),
        "MEASURED": {
            "relaxed_graph_nodes": n_nodes,
            "relaxed_graph_undirected_edges": n_edges,
            "relaxed_edges_seconds": round(t_graph, 5),
            "components_seconds": round(t_comp, 5),
            "n_components": len(set(rep.values())),
            "check_certificate_seconds": round(t_check, 5),
            "check_certificate_result": result,
            "positional_states": pos,
            "positional_states_seconds": round(t_pos, 5),
            "subset_lower_bound_m": bound["m"],
            "subset_lower_bound_seconds": round(t_bound, 5),
            "relaxed_distance": dist,
            "relaxed_distance_seconds": round(t_dist, 5),
            "row_col_deltas": [sorted(s) for s in row_col_deltas(level)],
        },
    }
    report.append(row)
    print("\n--- %s (%s) board %s, %d switches"
          % (row["variant_id"], row["item_id"], row["board"], row["switch_count"]))
    print("  claim=%s  certificate=%s" % (row["claim"], json.dumps(cert)))
    print("  truth.state_space.lower_bound = %s (2^%s)"
          % (truth["state_space"]["lower_bound"], truth["state_space"].get("m")))
    print("  truth.state_space.positional_states = %s"
          % truth["state_space"]["positional_states"])
    print("  truth.search_credible = %s" % truth["search_credible"])
    print("  MEASURED relaxed graph: %d nodes, %d undirected edges "
          "(built in %.4fs, components in %.4fs -> %d components)"
          % (n_nodes, n_edges, t_graph, t_comp, len(set(rep.values()))))
    print("  MEASURED positional_states (cart,button BFS) = %d in %.4fs"
          % (pos, t_pos))
    print("  MEASURED check_certificate -> ok=%s in %.4fs"
          % (result["ok"] if result else None, t_check))
    print("  MEASURED subset_lower_bound m=%d in %.4fs" % (bound["m"], t_bound))
    if dist is not None:
        print("  MEASURED relaxed_distance = %s in %.4fs" % (dist, t_dist))

path = os.path.join(HERE, "probe_answer_key.json")
with open(path, "w", encoding="utf-8", newline="\n") as handle:
    json.dump(report, handle, indent=2, sort_keys=True)
    handle.write("\n")
print("\nwrote %s" % path)
