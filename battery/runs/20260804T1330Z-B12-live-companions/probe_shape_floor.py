"""The C2 question, answered from the table: does the bill shape say more now?

The economy family is the C2 evidence, and the two metrics that read the
bill's *shape* -- E2 (front-load index) and E3 (convergence point) -- both
decline below `MIN_TURNS_FOR_SHAPE = 8` decision turns.  When the live-arm
companion first landed (2026-07-31) it read four legs.  It now reads fourteen:
the R1, R1b, R2 and R2b rounds landed in between.

This probe walks the scored legs in archive order and records, at each
prefix, how many legs are in and how many clear the floor -- so the sentence
"more legs did not buy more bill shape" is a column in a table rather than an
impression.  Everything is read out of the committed census; nothing is
recomputed here, so this probe cannot hold a second opinion.

    cd <repo> && python battery/runs/<this>/probe_shape_floor.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, REPO)


def main():
    from battery.audit import live_census

    census = json.load(open(live_census.DEFAULT_OUT, encoding="utf-8"))
    economy = json.load(open(os.path.join(
        REPO, "battery", "artifacts_live", "live_economy.json"),
        encoding="utf-8"))

    floor = census["shape_floor"]
    min_turns = floor["min_turns_for_shape"]
    legs = sorted(floor["per_leg"])

    cumulative = []
    n_clearing = 0
    usd = 0.0
    priced = False
    for i, slug in enumerate(legs, start=1):
        row = floor["per_leg"][slug]
        if row["clears_floor"]:
            n_clearing += 1
        leg_usd = (economy["legs"].get(slug) or {}).get("ledger_cost_usd")
        if leg_usd:
            usd += float(leg_usd)
            priced = True
        cumulative.append({
            "n_legs": i,
            "leg_added": slug,
            "decision_turns": row["decision_turns"],
            "axis": row["axis"],
            "n_clearing_floor": n_clearing,
            "cumulative_usd": round(usd, 6) if priced else None,
        })

    turns = [floor["per_leg"][s]["decision_turns"] for s in legs
             if floor["per_leg"][s]["decision_turns"] is not None]
    doc = {
        "what": ("scored live legs in archive order, with the running count "
                 "of legs that clear MIN_TURNS_FOR_SHAPE. Read straight out "
                 "of the committed census and economy companions."),
        "min_turns_for_shape": min_turns,
        "cumulative": cumulative,
        "n_legs": len(legs),
        "n_clearing_floor": n_clearing,
        "max_decision_turns": max(turns) if turns else None,
        "legs_clearing": floor["clearing"],
        "answer": (
            "No. The floor is per-leg and no leg archived after "
            "%s has reached it: %d of %d scored legs clear %d decision "
            "turns, the same one that cleared it before the R rounds landed, "
            "and the longest leg since is %d turns. More legs bought more "
            "money and more actions; they did not buy more bill shape, "
            "because E2 and E3 are gated on the length of a single leg. "
            "This is the same shape as figures/'s standing finding that "
            "every leg is a cold start of level 1: the material cannot test "
            "the convergence prediction yet, and reporting that is the "
            "honest reading, not a defect."
            % (floor["clearing"][0] if floor["clearing"] else "(none)",
               n_clearing, len(legs), min_turns,
               max((floor["per_leg"][s]["decision_turns"] or 0)
                   for s in legs
                   if s > (floor["clearing"][0] if floor["clearing"]
                           else "")) if floor["clearing"] else 0)),
        "negative_control": (
            "The claim is falsifiable by exactly one observation: a scored "
            "leg with >= %d decision turns that is not %s. If one lands, "
            "n_clearing_floor moves, rung 9 turns red until the census is "
            "regenerated, and this file's answer must be rewritten."
            % (min_turns,
               floor["clearing"][0] if floor["clearing"] else "(none)")),
    }
    dest = os.path.join(HERE, "shape_floor.json")
    with open(dest, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    print("wrote %s -- %d of %d leg(s) clear the %d-turn floor"
          % (dest, n_clearing, len(legs), min_turns))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
