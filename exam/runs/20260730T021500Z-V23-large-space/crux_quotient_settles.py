"""The crux measurement behind this run's ruling on `exhaustive_feasible`.

Class (ii) items claim exhaustive search is infeasible on their board. This
script measures the size and cost of the exhaustive computation that *actually
settles them* -- the one the shipped answer key already performs.

Each of the four is settled by a different cheap computation, and they are
measured separately rather than lumped -- an earlier draft of this script
assumed all four fell to the same connected-components pass, and the
measurement refuted it for three of them:

  ii1  connected components of `relaxed_edges` -- start and goal land in
       different components (this is what `_region_rep`, verdict.py:1345, does)
  ii2  the same pass with the cut cell deleted; the plain pass does NOT
       separate them, because `relaxed_edges` deliberately ignores the
       wrapper's `observation_loss`
  ii3  a relaxed shortest distance against the step budget
  ii4  a scan of the surviving action set for a monotone column

`relaxed_edges` is an OVER-approximation of the cart's moves: it adds edges
rather than removing them, so a goal in a different component from the start is
unreachable in the real game too. That one-sidedness is what makes it a sound
*unsolvability* proof, and it is the opposite of the direction D-EX-022's
disclaimer warns about.

Emits `crux_quotient_settles.json`. Every field is stable across runs except
those under "timing_seconds", which are rounded to 4 places and are the only
non-deterministic content.
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, REPO)

from exam.grading.rubrics_verdict import (  # noqa: E402
    Level, components, relaxed_edges, enumerate_states)
from exam.papers.verdict import (  # noqa: E402
    DELTA,
    comb_room, comb_open, variant_of, positional_states, subset_lower_bound,
    relaxed_distance, CART_COLOUR)


def _timed(fn):
    start = time.perf_counter()
    value = fn()
    return value, round(time.perf_counter() - start, 4)


def measure(item_id, level_doc, note):
    level = Level(level_doc)

    (edges, comps), t_settle = _timed(
        lambda: (lambda e: (e, components(e)))(relaxed_edges(level)))
    start_rep, goal_rep = comps[level.start], comps[level.goal]

    bound, t_bound = _timed(lambda: subset_lower_bound(level))
    quotient, t_quotient = _timed(lambda: positional_states(level))

    return {
        "item": item_id,
        "level_id": level_doc["level_id"],
        "note": note,
        # --- what the item CLAIMS a searcher must cover
        "m": bound["m"],
        "claimed_lower_bound": bound["lower_bound"],
        # --- what actually settles it
        "relaxed_graph_nodes": len(edges),
        "relaxed_graph_edges": sum(len(v) for v in edges.values()),
        "components_total": len(set(map(tuple, comps.values()))),
        "start_component": list(start_rep),
        "goal_component": list(goal_rep),
        "settled_by_partition": list(start_rep) != list(goal_rep),
        # --- the intermediate quotient, for scale
        "positional_states": quotient,
        "ratio_bound_over_relaxed_nodes": (
            "%.3e" % (bound["lower_bound"] / max(1, len(edges)))),
        "timing_seconds": {
            "settle_via_components": t_settle,
            "compute_lower_bound": t_bound,
            "enumerate_quotient": t_quotient,
        },
    }


def main():
    rows = []

    lvl = variant_of(comb_room("gantry", 60, None), "gantry",
                     remap={"LEFT": "RIGHT", "RIGHT": "LEFT"})
    rows.append(measure("ii1", lvl, "goal room sealed by a solid separator row"))

    # ii2 is NOT settled by the plain partition and the probe must not pretend
    # otherwise: `relaxed_edges` deliberately ignores the wrapper's
    # `observation_loss`, so start and goal stay in one component. Its
    # certificate is a cut set, and the exhaustive computation that settles it
    # is the same components pass with the cut cell deleted. Measured here so
    # the claim covers all four items rather than the one that was convenient.
    lvl = variant_of(comb_room("lattice", 60, 2), "lattice", lost_cells=[[4, 2]])
    row = measure("ii2", lvl, "cut set of size one at (4,2)")
    cut = (4, 2)
    base = relaxed_edges(Level(lvl))
    severed = {node: [n for n in nbrs if n != cut]
               for node, nbrs in base.items() if node != cut}
    (comps_cut, t_cut) = _timed(lambda: components(severed))
    level = Level(lvl)
    row["cut_cell"] = list(cut)
    row["cut_graph_nodes"] = len(severed)
    row["cut_components_total"] = len(set(map(tuple, comps_cut.values())))
    row["cut_start_component"] = list(comps_cut[level.start])
    row["cut_goal_component"] = list(comps_cut[level.goal])
    row["settled_by_cut_set"] = (
        list(comps_cut[level.start]) != list(comps_cut[level.goal]))
    row["timing_seconds"]["settle_via_cut_set"] = t_cut
    rows.append(row)

    # ii3 is settled by a budget argument, not a partition: its start and goal
    # ARE in one component. Measured here precisely so the negative case is on
    # the record and the ruling is not overstated to cover it.
    long_comb = comb_open("spindle", 200, 1, 200)
    lvl = variant_of(long_comb, "spindle", step_limit=150)
    row = measure("ii3", lvl, "step budget 150 against a relaxed distance")
    row["relaxed_distance_start_to_goal"] = relaxed_distance(
        Level(long_comb), (2, 1), (2, 200))
    row["step_limit"] = 150
    row["settled_by_budget"] = (
        row["relaxed_distance_start_to_goal"] > row["step_limit"])
    rows.append(row)

    # ii4 is settled by a monotone coordinate, not by a graph pass at all: with
    # LEFT forbidden no surviving displacement has a negative column component,
    # the cart starts at column 2 and the goal is at column 1. The settling
    # computation is a scan of the action set, so it is measured as one.
    lvl = variant_of(comb_open("orchard", 60, 2, 1), "orchard",
                     forbidden=["LEFT"])
    row = measure("ii4", lvl, "monotone cart column under a forbidden action")
    level = Level(lvl)
    deltas, t_mono = _timed(
        lambda: sorted({DELTA[level.world_action(c)][1]
                        for c in level.commands()}))
    row["surviving_column_deltas"] = deltas
    row["start_column"] = level.start[1]
    row["goal_column"] = level.goal[1]
    row["settled_by_monotone_column"] = (
        min(deltas) >= 0 and level.goal[1] < level.start[1])
    row["timing_seconds"]["settle_via_monotone_column"] = t_mono
    rows.append(row)

    payload = {
        "what": "size and cost of the exhaustive computation that settles each "
                "shipped class (ii) item, against the search it claims is "
                "infeasible",
        "sound_direction": (
            "relaxed_edges over-approximates the cart's moves, so "
            "start-component != goal-component is a sound unsolvability proof; "
            "the converse is not sound and is not used"),
        "items": rows,
    }
    out = os.path.join(HERE, "crux_quotient_settles.json")
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(payload, indent=2, sort_keys=True))
    print("\nwrote %s" % out)


if __name__ == "__main__":
    main()
