"""Re-derive the adversarial reviewer's two severe claims against this run's own work.

R1: excluding the button from `passable()` broke `row_col_deltas`, which uses
    `passable(entry)` to ask a different question -- "can the cart be STANDING
    here", not "can the cart REST here". Where the cart starts on the button and
    the button is the portal's only entry, the teleport's row delta is dropped
    and `cart_row` looks monotone on a level solvable in one command.

R2: deriving `search_credible` from the `(cart, button)` quotient is wrong,
    because the quotient is not a sound abstraction: it ignores `step_limit`
    entirely and carries no latch state on a `require_all_switches` board.

Run from the repo root:
    PYTHONPATH=. python exam/runs/<this run>/verify_review_claims.py
"""

from exam.grading.rubrics_verdict import (
    Level, check_certificate, enumerate_states, grade_verdict, replay,
    row_col_deltas,
)
from exam.model import Item, canonical
from exam.papers.verdict import comb_open, comb_room, positional_states, variant_of

SHAPE = {"button": None, "door": None, "portal": None, "portal_dest": None,
         "switches": [], "require_all_switches": False, "forbidden": [],
         "remap": {}, "step_limit": None, "lost_cells": [],
         "win_score_required": 1}


def level(level_id, rows, start, goal, **extra):
    doc = dict(SHAPE, level_id=level_id, rows=list(rows), start=list(start),
               goal=list(goal))
    doc.update(extra)
    return doc


def main():
    print("=== R1: the cart starts on the button, which is the portal's only entry ===")
    doc = level("review-button-start", ["####", "#..#", "##.#", "####"],
                (1, 1), (2, 2), button=[1, 1], portal=[1, 2], portal_dest=[2, 2],
                forbidden=["UP", "DOWN"])
    lvl = Level(doc)
    cert = {"kind": "invariant", "invariant": "cart_row",
            "initial_value": 1, "goal_value": 2}
    print("  wellformed_problems :", lvl.wellformed_problems())
    print("  replay(['RIGHT'])   :", replay(lvl, ["RIGHT"]))
    print("  row_col_deltas      :", row_col_deltas(lvl))
    result = check_certificate(cert, lvl)
    print("  check_certificate ok:", result["ok"], "--", result["why"][:88])
    truth = {"claim": "unsolvable", "level_blob": canonical(doc),
             "search_credible": False, "state_space": {}}
    item = Item("probe", "verdict.a2.claim_and_certificate", 2.0, {}, truth,
                leak_probes=("probe-x",))
    score = grade_verdict({"claim": "unsolvable", "certificate": cert}, truth, item)
    print("  MARKER AWARDS       : %.1f / %.1f reason=%s"
          % (score.awarded, score.possible, score.detail.get("reason")))
    print("  ==> UNSOUND" if result["ok"] else "  ==> refused")

    print("\n=== R2a: the quotient ignores step_limit ===")
    for corridor, budget in ((6, 12), (6, 40), (8, 20)):
        base = comb_open("review-spindle", corridor, 1, corridor)
        lvl = Level(variant_of(base, "review-spindle", step_limit=budget))
        full = enumerate_states(lvl, cap=200_000)
        # what a (cart, pressed) search would conclude about goal reachability
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
        quotient_says = any(c == lvl.goal for c, _ in seen)
        truth = "solvable" if full["solution"] else "unsolvable"
        flag = "  *** DISAGREES ***" if (quotient_says and truth == "unsolvable") else ""
        print("  corridor=%d budget=%-3d quotient=%d goal-reachable=%s | full=%d "
              "truth=%s%s" % (corridor, budget, positional_states(lvl),
                              quotient_says, full["states"], truth, flag))

    print("\n=== R2b: the quotient carries no latch state ===")
    base = comb_room("review-lattice", 5, 2)
    lvl = Level(variant_of(base, "review-lattice", lost_cells=[[1, 3]]))
    full = enumerate_states(lvl, cap=200_000)
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
    print("  require_all_switches:", lvl.require_all_switches,
          " switches:", len(lvl.switches), " hazard on a switch cell: [1,3]")
    print("  positional_states   :", positional_states(lvl))
    print("  quotient reaches goal cell:", any(c == lvl.goal for c, _ in seen))
    print("  full enumeration    : %d states, solution=%s"
          % (full["states"], full["solution"] is not None))
    print("  ==> the quotient says SOLVABLE and the level is %s"
          % ("SOLVABLE" if full["solution"] else "UNSOLVABLE"))


if __name__ == "__main__":
    main()
