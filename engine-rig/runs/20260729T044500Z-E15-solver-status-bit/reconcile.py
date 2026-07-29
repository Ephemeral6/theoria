"""E15 item 2 -- the row-by-row comparison against E11's hand derivation.

E11 rebuilt the LP outside the engine and read HiGHS's status itself
(`runs/20260729T000000Z-E11-engine-crosscheck-deep/partials/
lp_potential-via-exhaustive.md` §6).  Its claim, per world, is:

  * every one of the 639 silent-and-truly-unreachable worlds is HiGHS status 2
    at `bound=10`;
  * 638 of them stay infeasible at `bound` 100 / 1e4 / 1e6;
  * exactly one becomes feasible in a wider box -- index 2302.

That is a claim about all 639 rows, so it is checked on all 639 rows.  Where the
census and E11 disagree, **E11 wins** and the divergence is written down; the
census is not edited to agree with it.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# E11 §6, transcribed.  The per-world expectation is uniform except for the one
# named world, which is the only place E11 makes an individual claim.
E11_STATUS_AT_BOUND_10 = 2
E11_WIDER_FEASIBLE_INDEX = 2302
E11_WIDER_FEASIBLE_SEED = 17475932563032345095
E11_WIDER_FEASIBLE_WEIGHTS = ["12", "9", "3", "7", "-1", "11", "10", "-4"]
E11_TOTALS = {
    "silent_and_truly_unreachable": 639,
    "status_2_at_bound_10": 639,
    "still_infeasible_when_widened": 638,
    "feasible_when_widened": 1,
    "goal_truly_unreachable": 2189,
    "certificate_issued": 1550,
    "no_certificate": 1450,
    "worlds": 3000,
    "certificate_errors": 0,
}


def main():
    rows = [json.loads(line) for line in
            open(os.path.join(HERE, "census.jsonl"), encoding="utf-8")]
    silent = [r for r in rows if r["silent"] and r["goal_truly_unreachable"]]

    table = []
    disagreements = []
    for row in sorted(silent, key=lambda r: r["index"]):
        widened = {e["bound"]: e["status"] for e in row["wider_box"]}
        feasible_wider = any(s == "certified" for s in widened.values())
        expected_feasible_wider = row["index"] == E11_WIDER_FEASIBLE_INDEX
        agree = (
            row["engine"]["solver_status"] == E11_STATUS_AT_BOUND_10
            and row["engine"]["status"] == "no_linear_pagoda"
            and feasible_wider == expected_feasible_wider
        )
        entry = {
            "index": row["index"],
            "seed": row["seed"],
            "n_pos": row["n_pos"],
            "engine_status": row["engine"]["status"],
            "engine_solver_status": row["engine"]["solver_status"],
            "engine_bound": row["engine"]["bound"],
            "wider_box": widened,
            "feasible_when_widened": feasible_wider,
            "e11_solver_status": E11_STATUS_AT_BOUND_10,
            "e11_feasible_when_widened": expected_feasible_wider,
            "agree": agree,
        }
        table.append(entry)
        if not agree:
            disagreements.append(entry)

    named = next((r for r in silent if r["index"] == E11_WIDER_FEASIBLE_INDEX),
                 None)
    named_check = None
    if named is not None:
        first = next((e for e in named["wider_box"]
                      if e["status"] == "certified"), None)
        named_check = {
            "index": named["index"],
            "seed_matches_e11": named["seed"] == E11_WIDER_FEASIBLE_SEED,
            "census_seed": named["seed"],
            "e11_seed": E11_WIDER_FEASIBLE_SEED,
            "census_weights": first["weights"] if first else None,
            "e11_weights": E11_WIDER_FEASIBLE_WEIGHTS,
            "weights_match_e11": bool(first)
                                 and first["weights"] == E11_WIDER_FEASIBLE_WEIGHTS,
            "exact_recheck": first["exact_recheck"] if first else None,
        }

    summary = json.load(open(os.path.join(HERE, "SUMMARY.json"),
                             encoding="utf-8"))
    census_totals = {
        "silent_and_truly_unreachable": summary["silent_and_truly_unreachable"],
        "status_2_at_bound_10": sum(
            1 for e in table if e["engine_solver_status"] == 2),
        "still_infeasible_when_widened": sum(
            1 for e in table if not e["feasible_when_widened"]),
        "feasible_when_widened": sum(
            1 for e in table if e["feasible_when_widened"]),
        "goal_truly_unreachable": summary["goal_truly_unreachable"],
        "certificate_issued": summary["certificate_issued"],
        "no_certificate": summary["no_certificate"],
        "worlds": summary["worlds"],
        "certificate_errors": summary["certificate_errors"],
    }

    out = {
        "rows_compared": len(table),
        "rows_agreeing": sum(1 for e in table if e["agree"]),
        "rows_disagreeing": len(disagreements),
        "disagreements": disagreements,
        "totals_e11": E11_TOTALS,
        "totals_census": census_totals,
        "totals_agree": census_totals == E11_TOTALS,
        "named_world": named_check,
        "rule": "on any disagreement E11's hand derivation is authoritative; "
                "the census keeps its own number and the divergence is reported",
    }
    with open(os.path.join(HERE, "reconciliation.jsonl"), "w",
              encoding="utf-8", newline="\n") as handle:
        for entry in table:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")
    with open(os.path.join(HERE, "RECONCILIATION.json"), "w",
              encoding="utf-8", newline="\n") as handle:
        json.dump(out, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({k: v for k, v in out.items() if k != "disagreements"},
                     indent=2, sort_keys=True))
    print("disagreements: %d" % len(disagreements))


if __name__ == "__main__":
    main()
