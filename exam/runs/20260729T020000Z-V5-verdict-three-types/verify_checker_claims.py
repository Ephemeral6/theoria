"""Re-derive the two soundness claims independently, from the shipped modules.

Claim A (certificate checker): `relaxed_edges` is documented as an
over-approximation -- "it can never make a solvable level look unsolvable, which
would hand out points for a false theorem". If that is false, the marker pays
full marks for a proof of a falsehood, which is the worst thing this instrument
can do.

Claim B (class (ii) bound): `subset_lower_bound` ships `exhaustive_feasible:
False` and a 2^m lower bound on a level built from a shipped constructor and a
shipped operator whose true reachable-state count is small enough to enumerate.

Run from the repo root:
    PYTHONPATH=. python exam/runs/<this run>/verify_checker_claims.py
"""

import json

from exam.grading.rubrics_verdict import (
    Level, check_certificate, enumerate_states, replay,
)
from exam.model import Item, canonical
from exam.papers.verdict import (
    _large_space, comb_open, subset_lower_bound, variant_of,
)

LEVEL_SHAPE = {
    "button": None, "door": None, "portal": None, "portal_dest": None,
    "switches": [], "require_all_switches": False, "forbidden": [],
    "remap": {}, "step_limit": None, "lost_cells": [], "win_score_required": 1,
}


def level(level_id, rows, start, goal, **extra):
    doc = dict(LEVEL_SHAPE, level_id=level_id, rows=list(rows),
               start=list(start), goal=list(goal))
    doc.update(extra)
    return doc


def grade_as_marker_would(doc, cert):
    """Run the real rubric, not a reimplementation of it."""
    from exam.grading.rubrics_verdict import grade_verdict
    truth = {"claim": "unsolvable", "level_blob": canonical(doc),
             "search_credible": False, "state_space": {}}
    item = Item(item_id="probe", rubric_id="verdict.a2.claim_and_certificate",
                points=2.0, paper={}, truth=truth, leak_probes=("probe-x",))
    return grade_verdict({"claim": "unsolvable", "certificate": cert}, truth, item)


def report(name, doc, cert):
    lvl = Level(doc)
    result = check_certificate(cert, lvl)
    found = enumerate_states(lvl, cap=200_000)
    print("\n--- %s ---" % name)
    print("  check_certificate ok :", result["ok"])
    print("  why                  :", result["why"][:110])
    print("  truly solvable       :", found["solution"] is not None,
          "  plan:", found["solution"])
    if found["solution"] is not None:
        print("  replay of that plan  :", replay(lvl, found["solution"]))
        score = grade_as_marker_would(doc, cert)
        print("  MARKER AWARDS        : %.1f / %.1f  reason=%s"
              % (score.awarded, score.possible, score.detail.get("reason")))
    return result["ok"] and found["solution"] is not None


def main():
    unsound = []

    # -- A1: portal set, portal_dest left at the shipped default of None ------
    # `_level()` in verdict.py defaults portal_dest to None, so this is inside
    # the level shape the paper itself uses.
    doc = level("probe-portal-none",
                ["#######", "#..#..#", "#.SP.G#", "#..#..#", "#######"],
                (2, 2), (2, 5), portal=[2, 3], portal_dest=None)
    if report("A1  portal_dest is None (step falls through, graph drops the edge)",
              doc, {"kind": "invariant", "invariant": "cart_region",
                    "initial_value": [1, 1], "goal_value": [1, 4]}):
        unsound.append("A1")

    # -- A2: door and portal on the same cell; every field well-formed --------
    # `step` tests the door before the portal; `_neighbours` has no door branch
    # at all. No degenerate value anywhere in this level.
    doc = level("probe-door-portal",
                ["########", "#..#.#.#", "#....###", "#.#....#", "#.#...##",
                 "########"],
                (3, 4), (3, 3), button=[1, 4], door=[3, 3], portal=[3, 3],
                portal_dest=[2, 4], lost_cells=[[2, 3], [3, 6]])
    if report("A2  door == portal, all fields well-formed",
              doc, {"kind": "cut_set", "cells": [[2, 3]]}):
        unsound.append("A2")

    print("\n=== CLAIM A: unsound accepts reproduced:", unsound or "NONE", "===")

    # -- B: a shipped constructor + a shipped operator ------------------------
    print("\n--- B  comb_open(30) + observation_loss on the corridor right of S ---")
    base = comb_open("probe-comb", 30, 1, 30)
    hazards = [[2, c] for c in range(2, 31)]
    lvl = variant_of(base, "probe-comb", lost_cells=hazards)
    try:
        bound = subset_lower_bound(Level(lvl))
        print("  subset_lower_bound   : m=%d dippable=%d lower_bound=2^%d"
              % (bound["m"], bound["dippable_switches"], bound["m"]))
    except AssertionError as exc:
        print("  subset_lower_bound REFUSES:", str(exc).split(". The bound")[0])
        found = enumerate_states(Level(lvl), cap=200_000)
        print("  TRUE reachable states: %d (truncated=%s)"
              % (found["states"], found["truncated"]))
        bound = None
    try:
        if bound is None:
            raise AssertionError("refused upstream by the lane precondition")
        recorded = _large_space(lvl)
        print("  _large_space ACCEPTS : exhaustive_feasible=%s lower_bound=%d"
              % (recorded["exhaustive_feasible"], recorded["lower_bound"]))
        accepted = True
    except AssertionError as exc:
        print("  _large_space refuses :", exc)
        accepted = False
    found = enumerate_states(Level(lvl), cap=200_000)
    print("  TRUE reachable states: %d (truncated=%s)"
          % (found["states"], found["truncated"]))
    if accepted and bound is not None and not found["truncated"]:
        print("  ==> a level stamped `exhaustive_feasible: False` enumerates in "
              "%d states; overstatement factor %.3e"
              % (found["states"], (2 ** bound["m"]) / found["states"]))

    # -- B2: the shipped class (ii) items, quotiented ------------------------
    print("\n--- B2  the shipped class (ii) levels: positional state count ---")
    from exam.papers.verdict import comb_room
    for name, doc in (
            ("gantry(sealed)", variant_of(comb_room("gantry", 60, None), "gantry",
                                          remap={"LEFT": "RIGHT", "RIGHT": "LEFT"})),
            ("lattice(bridge cut)", variant_of(comb_room("lattice", 60, 2),
                                               "lattice", lost_cells=[[4, 2]]))):
        lvl = Level(doc)
        seen, frontier = {(lvl.start, False)}, [(lvl.start, False)]
        while frontier:
            nxt = []
            for cart, pressed in frontier:
                for command in lvl.commands():
                    state = lvl.step(cart, pressed, lvl.world_action(command))
                    if state[0] in lvl.lost_cells or state in seen:
                        continue
                    seen.add(state)
                    nxt.append(state)
            frontier = nxt
        print("  %-20s reachable (cart, pressed) pairs = %d   claimed bound = 2^%d"
              % (name, len(seen), subset_lower_bound(lvl)["m"]))


if __name__ == "__main__":
    main()
