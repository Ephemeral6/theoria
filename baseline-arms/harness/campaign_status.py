"""Where is the full run up to? Reads checkpoints only -- never the 4 MB ledger.

    python -m harness.campaign_status
"""

import glob
import json
import os
import sys

TRACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAMPAIGN_DIR = os.path.join(TRACK, "out", "campaign")


def main(argv=None) -> int:
    paths = sorted(glob.glob(os.path.join(CAMPAIGN_DIR, "campaign_*.json")))
    if not paths:
        print("no campaign checkpoints in %s" % CAMPAIGN_DIR)
        return 1

    print("%-18s %-18s %6s %8s %7s %8s %9s %8s" % (
        "game", "status", "eps", "actions", "budget", "levels", "cost$", "ceiling$"))
    tot_cost = tot_ok = tot_budget = tot_http = 0
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            s = json.load(fh)
        # Episode totals only land when an episode ends, and an episode here can
        # run for hours. Reporting those alone shows $0.00 while money is being
        # spent -- so fold in the in-flight episode's live checkpoint.
        live = s.get("live_episode") or {}
        cost = s.get("cost_usd", 0.0) + (live.get("cost_usd") or 0.0)
        ok = s.get("actions_ok", 0) + (live.get("actions_ok") or 0)
        tot_cost += cost
        tot_ok += ok
        tot_budget += s.get("total_budget", 0)
        tot_http += s.get("http_calls", 0)
        print("%-18s %-18s %6d %8d %7d %8s %9.2f %8.2f%s" % (
            s["game_id"], s.get("status", "?"), len(s.get("episodes", [])),
            ok, s.get("total_budget", 0),
            "%s/%s" % (max(s.get("best_levels_completed", 0),
                           live.get("levels_completed") or 0), s.get("win_levels")),
            cost, s.get("ceiling_usd", 0.0), "  (ep in flight)" if live else ""))

    pct = (100.0 * tot_ok / tot_budget) if tot_budget else 0.0
    print("\ntotal: %d/%d actions (%.1f%%) | %d HTTP | $%.2f"
          % (tot_ok, tot_budget, pct, tot_http, tot_cost))
    print("approved extrapolation was $103 for 3014 actions (BUDGET_REPORT.md 3.4)")

    wins = [json.load(open(p, encoding="utf-8")) for p in paths]
    won = [s["game_id"] for s in wins if s.get("wins")]
    print("games won: %s" % (", ".join(won) if won else "none yet"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
