"""A28 -- what the bare_cc arm actually achieved, and whether the zero is real.

The paper's left-hand column says "baseline scored zero". Three separate
questions hide inside that sentence, and they have different consequences:

  1. Is the score *read* from the field the API populates?
  2. Is the score genuinely 0, or is 0 what a missing read looks like?
  3. If it is genuinely 0, was the run given enough actions for a non-zero
     score to have been *possible*?

The authoritative number is `score` on the scorecard body, which the API
returns only in the response to `POST /api/scorecard/open`-then-GET or to a
successful `POST /api/scorecard/close`. The gameplay response (`RESET`,
`ACTIONn`) carries **no `score` field at all** -- it carries `state`,
`levels_completed` and `win_levels`. So a harness that reads gameplay
responses can never see the score; it can only see `levels_completed`, which
is a different (if correlated) quantity.

This tool reads the archived scorecard bodies out of probe_log.jsonl and the
out/shards/ copies, and reports the three questions separately. It makes no
network call and reads nothing outside baseline-arms.

    python -m harness.audit_zero            # the table
    python -m harness.audit_zero --json     # machine-readable

Denominators are printed beside every number on purpose: the arm has more
archived scorecard bodies than it has runs/ directories, and more runs/
directories than it has runs that ever reached the API.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Where scorecard bodies were archived. Both are append-only probe logs.
PROBE_GLOBS = ("probe_log.jsonl", os.path.join("out", "shards", "probe_log*.jsonl"))

# Gameplay responses carry these; note the absence of "score".
GAMEPLAY_FIELDS = ("state", "levels_completed", "win_levels")


def _probe_files() -> List[str]:
    out: List[str] = []
    for pat in PROBE_GLOBS:
        out.extend(sorted(glob.glob(os.path.join(HERE, pat))))
    return out


def scorecard_observations() -> List[Dict[str, Any]]:
    """Every (card, environment, run) triple for which an authoritative body
    was archived. One run_id can appear more than once: a card was sometimes
    fetched mid-run and again at close."""
    obs: List[Dict[str, Any]] = []
    for fp in _probe_files():
        with open(fp, encoding="utf-8") as fh:
            for line in fh:
                # A33: skip lines that cannot contain a score key before paying
                # for json.loads.  The filter below requires `"score" in body`,
                # so a line without the substring `"score"` anywhere in it
                # cannot survive it -- the prefilter is exactly implied by the
                # test two lines down, not a heuristic.  Measured on this
                # territory's 9 MB of probe logs: 38.0s -> 18.7s, and the 63
                # observations returned are `==`-identical either way.
                if '"score"' not in line:
                    continue
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                body = rec.get("response_summary")
                if not isinstance(body, dict) or "score" not in body:
                    continue
                run_id = (body.get("opaque") or {}).get("run_id")
                for env in body.get("environments", []) or []:
                    for run in env.get("runs", []) or []:
                        obs.append({
                            "source": os.path.basename(fp),
                            "note": rec.get("note"),
                            "run_id": run_id,
                            "card_id": body.get("card_id"),
                            "game_id": env.get("id"),
                            "card_score": body.get("score"),
                            "env_score": env.get("score"),
                            "run_score": run.get("score"),
                            "level_scores": run.get("level_scores"),
                            "level_actions": run.get("level_actions"),
                            "level_baseline_actions": run.get("level_baseline_actions"),
                            "levels_completed": run.get("levels_completed"),
                            "actions": run.get("actions"),
                            "resets": run.get("resets"),
                            "state": run.get("state"),
                            "total_actions": body.get("total_actions"),
                        })
    return obs


def baselines(obs: List[Dict[str, Any]]) -> Dict[str, List[int]]:
    """level_baseline_actions per game, as the API itself reports it."""
    out: Dict[str, List[int]] = {}
    for o in obs:
        lb = o.get("level_baseline_actions")
        if lb and o.get("game_id"):
            out[o["game_id"]] = lb
    return out


def archived_runs() -> List[Dict[str, Any]]:
    """runs/bare_cc-*/run.json -- what the harness itself persisted."""
    rows: List[Dict[str, Any]] = []
    for d in sorted(glob.glob(os.path.join(HERE, "runs", "bare_cc-*"))):
        p = os.path.join(d, "run.json")
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as fh:
            r = json.load(fh)
        s = r.get("summary") or {}
        rows.append({
            "run_id": r.get("id"),
            "game_id": r.get("game_id"),
            "model": r.get("model"),
            "budget": r.get("budget"),
            "actions_ok": s.get("actions_ok"),
            "levels_completed": s.get("levels_completed"),
            "final_state": s.get("final_state"),
            "outcome": r.get("outcome"),
            "campaign": r.get("campaign"),
            # The question that matters for question (1):
            "persists_score": "score" in s,
        })
    return rows


def analyse() -> Dict[str, Any]:
    obs = scorecard_observations()
    base = baselines(obs)
    runs = archived_runs()

    # -- question 1: is the score read and persisted? ---------------------
    persisted = sum(1 for r in runs if r["persists_score"])

    # -- question 2: is it genuinely zero? --------------------------------
    nonzero_card = [o for o in obs if o["card_score"]]
    nonzero_run = [o for o in obs if o["run_score"]]
    nonzero_level = [o for o in obs if any(o["level_scores"] or [])]
    completed = [o for o in obs if (o["levels_completed"] or 0) > 0]

    # -- question 3: was the budget enough for level 1? -------------------
    per_game: Dict[str, Any] = {}
    for game, lb in sorted(base.items()):
        l1 = lb[0]
        g_obs = [o for o in obs if o["game_id"] == game]
        reach = [o["actions"] or 0 for o in g_obs]
        # A run only tests capability on level 1 if it was allowed to spend
        # at least as many actions as the level's own baseline.
        adequate = [o for o in g_obs if (o["actions"] or 0) >= l1]
        per_game[game] = {
            "level_baseline_actions": lb,
            "level_1_baseline": l1,
            "observations": len(g_obs),
            "best_actions": max(reach) if reach else 0,
            "best_pct_of_level_1": round(100.0 * max(reach) / l1, 1) if reach else 0.0,
            "median_actions": sorted(reach)[len(reach) // 2] if reach else 0,
            "obs_reaching_level_1_baseline": len(adequate),
            "terminal_states": sorted({o["state"] for o in g_obs if o["state"]}),
        }

    g_runs = [r for r in runs if r["budget"]]
    budget_under = [
        r for r in g_runs
        if base.get(r["game_id"]) and r["budget"] < base[r["game_id"]][0]
    ]

    return {
        "question_1_score_is_read": {
            "gameplay_response_has_score_field": False,
            "gameplay_response_fields": list(GAMEPLAY_FIELDS),
            "authoritative_source": "scorecard body (open-GET / close)",
            "archived_run_dirs": len(runs),
            "run_dirs_persisting_a_score_field": persisted,
        },
        "question_2_score_is_zero": {
            "authoritative_observations": len(obs),
            "distinct_run_ids": len({o["run_id"] for o in obs if o["run_id"]}),
            "observations_with_nonzero_card_score": len(nonzero_card),
            "observations_with_nonzero_run_score": len(nonzero_run),
            "observations_with_any_nonzero_level_score": len(nonzero_level),
            "observations_with_levels_completed_gt_0": len(completed),
        },
        "question_3_budget": {
            "per_game": per_game,
            "runs_with_a_budget": len(g_runs),
            "runs_whose_budget_is_below_level_1_baseline": len(budget_under),
            "budgets_seen": sorted({r["budget"] for r in g_runs}),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    res = analyse()
    if args.json:
        print(json.dumps(res, indent=2, sort_keys=True))
        return 0

    q1, q2, q3 = res["question_1_score_is_read"], res["question_2_score_is_zero"], res["question_3_budget"]

    print("A28 -- baseline arm, the zero examined\n")
    print("1. IS THE SCORE READ?")
    print("   gameplay response carries a score field .... %s" % q1["gameplay_response_has_score_field"])
    print("   it carries instead ......................... %s" % ", ".join(q1["gameplay_response_fields"]))
    print("   authoritative source ....................... %s" % q1["authoritative_source"])
    print("   run dirs that persist a score .............. %d of %d"
          % (q1["run_dirs_persisting_a_score_field"], q1["archived_run_dirs"]))

    print("\n2. IS IT GENUINELY ZERO?")
    print("   authoritative observations ................. %d (%d distinct run_ids)"
          % (q2["authoritative_observations"], q2["distinct_run_ids"]))
    print("   with nonzero card score .................... %d" % q2["observations_with_nonzero_card_score"])
    print("   with nonzero run score ..................... %d" % q2["observations_with_nonzero_run_score"])
    print("   with any nonzero level_score ............... %d" % q2["observations_with_any_nonzero_level_score"])
    print("   with levels_completed > 0 .................. %d" % q2["observations_with_levels_completed_gt_0"])

    print("\n3. WAS THE BUDGET ENOUGH FOR LEVEL 1?")
    print("   %-16s %8s %8s %8s %8s %7s  %s"
          % ("game", "base_L1", "best", "pct", "median", "n>=L1", "terminal states"))
    for game, d in q3["per_game"].items():
        print("   %-16s %8d %8d %7.1f%% %8d %7d  %s"
              % (game, d["level_1_baseline"], d["best_actions"], d["best_pct_of_level_1"],
                 d["median_actions"], d["obs_reaching_level_1_baseline"],
                 ",".join(d["terminal_states"])))
    print("\n   budgets configured ......................... %s" % q3["budgets_seen"])
    print("   runs whose budget < level-1 baseline ....... %d of %d"
          % (q3["runs_whose_budget_is_below_level_1_baseline"], q3["runs_with_a_budget"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
