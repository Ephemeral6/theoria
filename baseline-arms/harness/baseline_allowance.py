"""A28b -- what the baseline arm was *allowed* to spend, beside what it spent.

A28 established that the bare_cc zero is genuinely read and genuinely zero, and
then asked the question that decides whether the paper may report it: was any
run ever allowed enough actions for a non-zero score to be possible? It answered
by reading `budget` out of `runs/bare_cc-*/run.json`, found 20 and 30 against
level-1 baselines of 32 to 78, and concluded that on `g50t` and `sk48` the zero
is a budget artefact.

**That conclusion does not survive the whole archive.** `runs/*/run.json` is not
where the arm's largest allowance is recorded. The approved S1 campaign
(`harness/campaign.py`, `BUDGET_REPORT.md` section 3.4) gave each game an action
budget equal to the sum of its official level baselines -- 748 / 879 / 1070 /
317 -- and handed each episode whatever was left of it (`campaign.py`:
`bare_cc.play(game_id, model, remaining, ...)`). Those 48 episodes have **no**
`runs/` directory: `runs/s1-full-run-not-archived/run.json` records, in the
archive itself, that they were excluded because a concurrent session was still
writing them (INC-BA-003). A28's reader could not see them, so it reported the
pilot's 20 and the envelope's 30 as if they were the arm's ceiling.

So this tool reads allowance from **all three** places it is written, keeps the
provenance of each number attached to it, and separates three claims that the
phrase "the baseline scored zero" runs together:

  * the allowance was below the level-1 baseline    -> a **budget** artefact;
  * the allowance was adequate and the game ended   -> **capability** evidence;
  * the allowance was adequate and the *harness*
    ended the episode first                         -> an **abort** artefact,
    which is a fact about this arm's stop rule and about nothing else.

For the third case it reconstructs, from the ledger's per-step `failed` flags,
the longest run of back-to-back failures in each episode -- because the rule
that killed those episodes (an absolute `actions_failed >= 10`) was replaced by
D-016 with `CONSECUTIVE_FAILURE_ABORT` and a budget-scaled grind cap, and the
archive can therefore say whether today's code would have kept them alive.

    python -m harness.baseline_allowance          # the table
    python -m harness.baseline_allowance --json   # machine-readable

Offline: reads only archived artefacts under baseline-arms. No network, no spend.
Absence is printed as ABSENT and counted separately; it is never rendered as 0.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
from typing import Any, Dict, List, Optional, Tuple

from . import bare_cc
from .audit_zero import scorecard_observations

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Outcomes in which the *game* ended rather than the harness stopping the run.
# Only these make a zero a statement about the arm.
TERMINAL_GAME_OUTCOMES = ("win", "game_over")
TERMINAL_GAME_STATES = ("WIN", "GAME_OVER")


# --------------------------------------------------------------------------
# allowance: three sources, each keeping its own name
# --------------------------------------------------------------------------

def allowance_records() -> List[Dict[str, Any]]:
    """Every run_id for which an action allowance is recorded anywhere.

    One run_id may appear twice (a pilot cell is written both to
    `out/pilot_*.json` and to its `runs/` directory); the caller keeps both
    rather than picking, so a disagreement between sources is visible.
    """
    out: List[Dict[str, Any]] = []

    # (1) archived run directories -- per-run cap, key "budget"
    for d in sorted(glob.glob(os.path.join(HERE, "runs", "bare_cc-*"))):
        p = os.path.join(d, "run.json")
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as fh:
            r = json.load(fh)
        s = r.get("summary") or {}
        out.append({
            "run_id": r.get("id"),
            "game_id": r.get("game_id"),
            "model": r.get("model"),
            "allowance": r.get("budget"),
            "allowance_source": "runs/<id>/run.json:budget",
            "regime": r.get("campaign") or "unattributed",
            "actions_ok": s.get("actions_ok"),
            "actions_failed": s.get("actions_failed"),
            "outcome": r.get("outcome"),
        })

    # (2) pilot output -- same cap, written before the archive existed
    for f in sorted(glob.glob(os.path.join(HERE, "out", "pilot_*.json"))):
        with open(f, encoding="utf-8") as fh:
            rows = json.load(fh)
        for row in rows:
            out.append({
                "run_id": row.get("run_id"),
                "game_id": row.get("game_id"),
                "model": row.get("model"),
                "allowance": row.get("budget"),
                "allowance_source": "out/%s:budget" % os.path.basename(f),
                "regime": "m4-pilot",
                "actions_ok": row.get("actions_ok"),
                "actions_failed": row.get("actions_failed"),
                "outcome": row.get("outcome"),
            })

    # (3) the S1 campaign -- the allowance that A28 could not see. campaign.py
    #     passes `remaining = total_budget - actions_ok_so_far` as the episode's
    #     budget, so that subtraction is reproduced here rather than guessed.
    for f in sorted(glob.glob(os.path.join(HERE, "out", "campaign", "campaign_*.json"))):
        with open(f, encoding="utf-8") as fh:
            d = json.load(fh)
        spent = 0
        for ep in d.get("episodes") or []:
            out.append({
                "run_id": ep.get("run_id"),
                "game_id": d.get("game_id"),
                "model": d.get("model"),
                "allowance": d.get("total_budget") - spent,
                "allowance_source": "out/campaign/%s:total_budget - actions_ok(prior episodes)"
                                    % os.path.basename(f),
                "regime": d.get("scenario") or "S1",
                "actions_ok": ep.get("actions_ok"),
                "actions_failed": ep.get("actions_failed"),
                "outcome": ep.get("outcome"),
                "episode": ep.get("n"),
            })
            spent += ep.get("actions_ok") or 0

    return [r for r in out if r.get("run_id")]


# --------------------------------------------------------------------------
# the abort rule, reconstructed from the ledger
# --------------------------------------------------------------------------

def _ledger_files() -> List[str]:
    fs = [os.path.join(HERE, "ledger.jsonl")]
    fs.extend(sorted(glob.glob(os.path.join(HERE, "out", "shards", "ledger*.jsonl"))))
    return [f for f in fs if os.path.exists(f)]


def failure_shape() -> Dict[str, Dict[str, int]]:
    """Per run_id: how many actions failed, and the longest back-to-back run.

    The distinction is the whole of D-016. `actions_failed >= 10` -- the rule in
    force when the S1 campaign ran -- counts scattered failures; the rule that
    replaced it fires on ten *consecutive* ones. The ledger records every action
    with a `failed` flag and a `step_idx`, so the difference is recoverable
    without re-running anything.
    """
    steps: Dict[str, List[Tuple[int, bool]]] = {}
    for f in _ledger_files():
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if r.get("action") is None or not r.get("run_id"):
                    continue
                steps.setdefault(r["run_id"], []).append(
                    (int(r.get("step_idx") or 0), bool(r.get("failed"))))

    shape: Dict[str, Dict[str, int]] = {}
    for rid, rows in steps.items():
        rows.sort()
        longest = current = failed = 0
        for _, is_failed in rows:
            if is_failed:
                current += 1
                failed += 1
                longest = max(longest, current)
            else:
                current = 0
        shape[rid] = {
            "ledger_steps": len(rows),
            "failed": failed,
            "longest_consecutive_failures": longest,
        }
    return shape


def would_abort_today(allowance: Optional[int], shape: Optional[Dict[str, int]]) -> Optional[bool]:
    """Would the current stop rules have ended this episode? None = unknowable.

    Two rules, both from `bare_cc`, both read from the module so this cannot
    drift away from the code it is judging.
    """
    if not shape or allowance is None:
        return None
    if shape["longest_consecutive_failures"] >= bare_cc.CONSECUTIVE_FAILURE_ABORT:
        return True
    if shape["failed"] >= bare_cc.cumulative_failure_cap(allowance):
        return True
    return False


# --------------------------------------------------------------------------
# the per-game comparison the paper needs
# --------------------------------------------------------------------------

def analyse() -> Dict[str, Any]:
    obs = scorecard_observations()
    recs = allowance_records()
    shape = failure_shape()

    # level-1 baseline, as the API itself reports it on the scorecard body
    baselines: Dict[str, List[int]] = {}
    for o in obs:
        lb = o.get("level_baseline_actions")
        if lb and o.get("game_id"):
            baselines[o["game_id"]] = lb

    # authoritative achieved actions, per run_id
    achieved: Dict[str, int] = {}
    state: Dict[str, str] = {}
    for o in obs:
        rid = o.get("run_id")
        if not rid:
            continue
        achieved[rid] = max(achieved.get(rid, 0), o.get("actions") or 0)
        if o.get("state"):
            state[rid] = o["state"]

    by_game: Dict[str, Dict[str, Any]] = {}
    for game in sorted(baselines):
        l1 = baselines[game][0]
        rows = [r for r in recs if r.get("game_id") == game and r.get("allowance") is not None]
        by_regime: Dict[str, Dict[str, Any]] = {}
        for r in rows:
            reg = by_regime.setdefault(r["regime"], {
                "allowance_max": 0, "achieved_max": 0, "runs": 0,
                "outcomes": {}, "allowance_source": r["allowance_source"],
            })
            reg["runs"] += 1
            reg["allowance_max"] = max(reg["allowance_max"], r["allowance"])
            got = achieved.get(r["run_id"])
            if got is None:
                got = r.get("actions_ok")
            reg["achieved_max"] = max(reg["achieved_max"], got or 0)
            oc = r.get("outcome") or "unrecorded"
            reg["outcomes"][oc] = reg["outcomes"].get(oc, 0) + 1

        allowance_max = max((r["allowance"] for r in rows), default=None)
        allowance_max_run = next((r["run_id"] for r in rows
                                  if r["allowance"] == allowance_max), None)

        # achieved: only the runs whose allowance is on record, so the two
        # columns describe the same population.
        got_pairs = [(achieved.get(r["run_id"], r.get("actions_ok") or 0), r["run_id"])
                     for r in rows]
        achieved_max, achieved_max_run = max(got_pairs, default=(None, None))

        # the only runs whose zero is about the arm: the game ended.
        terminal = sorted({
            r["run_id"] for r in rows
            if (r.get("outcome") in TERMINAL_GAME_OUTCOMES
                or state.get(r["run_id"]) in TERMINAL_GAME_STATES)
        })
        terminal_at_or_over_baseline = sorted(
            rid for rid in terminal if (achieved.get(rid) or 0) >= l1)

        # abort-limited: allowance was adequate, the game never ended.
        adequate = [r for r in rows if r["allowance"] >= l1]
        would_abort = {}
        for r in adequate:
            v = would_abort_today(r["allowance"], shape.get(r["run_id"]))
            key = {True: "yes", False: "no", None: "unknown"}[v]
            would_abort[key] = would_abort.get(key, 0) + 1

        if allowance_max is None:
            verdict = "no_allowance_recorded"
        elif allowance_max < l1:
            verdict = "budget_artefact"
        elif terminal_at_or_over_baseline:
            verdict = "capability_tested"
        else:
            verdict = "abort_artefact"

        by_game[game] = {
            "level_baseline_actions": baselines[game],
            "level_1_baseline": l1,
            "allowance_max": allowance_max,
            "allowance_max_run_id": allowance_max_run,
            "achieved_max": achieved_max,
            "achieved_max_run_id": achieved_max_run,
            "allowance_covers_level_1": (allowance_max is not None and allowance_max >= l1),
            "runs_allowed_at_least_level_1": len(adequate),
            "runs_with_a_recorded_allowance": len(rows),
            "terminal_game_end_run_ids": terminal,
            "terminal_game_end_at_or_over_level_1": terminal_at_or_over_baseline,
            "adequate_runs_that_would_abort_under_current_rules": would_abort,
            "by_regime": by_regime,
            "verdict": verdict,
        }

    # absence, recorded as absence
    with_allowance = {r["run_id"] for r in recs if r.get("allowance") is not None}
    observed = {o["run_id"] for o in obs if o.get("run_id")}
    missing = sorted(observed - with_allowance)

    # the stop rule, across every run whose failure shape is on record
    s1_rows = [r for r in recs if str(r.get("regime", "")).startswith("S1")]
    s1_shapes = [shape.get(r["run_id"]) for r in s1_rows]
    s1_known = [s for s in s1_shapes if s]
    return {
        "per_game": by_game,
        "absence": {
            "observed_run_ids": len(observed),
            "observed_run_ids_with_a_recorded_allowance": len(observed & with_allowance),
            "observed_run_ids_with_no_allowance_anywhere": len(missing),
            "run_ids_with_no_allowance_anywhere": missing,
        },
        "stop_rule": {
            "rule_in_force_when_s1_ran": "actions_failed >= 10 (absolute, cumulative)",
            "rule_today_consecutive_abort": bare_cc.CONSECUTIVE_FAILURE_ABORT,
            "rule_today_grind_cap_at_a_748_action_budget": bare_cc.cumulative_failure_cap(748),
            "s1_episodes": len(s1_rows),
            "s1_episodes_with_a_ledger_failure_shape": len(s1_known),
            "s1_longest_consecutive_failure_run_anywhere":
                max((s["longest_consecutive_failures"] for s in s1_known), default=None),
            "s1_episodes_that_would_abort_under_current_rules":
                sum(1 for r in s1_rows
                    if would_abort_today(r["allowance"], shape.get(r["run_id"])) is True),
            "s1_episodes_whose_recorded_outcome_was_api_unusable":
                sum(1 for r in s1_rows if r.get("outcome") == "api_unusable"),
        },
    }


def _fmt(v: Any) -> str:
    return "ABSENT" if v is None else str(v)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    res = analyse()
    if args.json:
        print(json.dumps(res, indent=2, sort_keys=True))
        return 0

    print("A28b -- baseline arm: the allowance beside the achievement\n")
    print("1. PER GAME -- level-1 baseline vs the most any run was ALLOWED vs what it DID")
    print("   %-16s %9s %10s %10s  %s"
          % ("game", "base_L1", "allowed", "achieved", "verdict"))
    for game, d in res["per_game"].items():
        print("   %-16s %9d %10s %10s  %s"
              % (game, d["level_1_baseline"], _fmt(d["allowance_max"]),
                 _fmt(d["achieved_max"]), d["verdict"]))

    print("\n2. THE SAME NUMBERS SPLIT BY BUDGET REGIME (allowance is per run)")
    for game, d in res["per_game"].items():
        print("   %s  (level-1 baseline %d)" % (game, d["level_1_baseline"]))
        for reg, r in sorted(d["by_regime"].items()):
            print("      %-22s runs=%-3d allowed<=%-5d achieved<=%-4d %s"
                  % (reg, r["runs"], r["allowance_max"], r["achieved_max"],
                     ", ".join("%s=%d" % kv for kv in sorted(r["outcomes"].items()))))

    print("\n3. WHAT ACTUALLY STOPPED THE RUNS THAT HAD ENOUGH ACTIONS")
    sr = res["stop_rule"]
    print("   rule in force for S1 ....................... %s" % sr["rule_in_force_when_s1_ran"])
    print("   today: consecutive-failure abort ........... %s" % sr["rule_today_consecutive_abort"])
    print("   today: grind cap at a 748-action budget .... %s" % sr["rule_today_grind_cap_at_a_748_action_budget"])
    print("   S1 episodes ................................ %d (%d with a ledger failure shape)"
          % (sr["s1_episodes"], sr["s1_episodes_with_a_ledger_failure_shape"]))
    print("   recorded outcome api_unusable .............. %d" % sr["s1_episodes_whose_recorded_outcome_was_api_unusable"])
    print("   longest back-to-back failure run anywhere .. %s" % _fmt(sr["s1_longest_consecutive_failure_run_anywhere"]))
    print("   would abort under today's rules ............ %d" % sr["s1_episodes_that_would_abort_under_current_rules"])

    print("\n4. THE ONLY RUNS WHOSE ZERO IS ABOUT THE ARM (the game ended, the harness did not)")
    any_terminal = False
    for game, d in res["per_game"].items():
        for rid in d["terminal_game_end_at_or_over_level_1"]:
            any_terminal = True
            print("   %-16s %s" % (game, rid))
    if not any_terminal:
        print("   none")

    print("\n5. ABSENCE, RECORDED AS ABSENCE")
    a = res["absence"]
    print("   run_ids with an authoritative scorecard body  %d" % a["observed_run_ids"])
    print("   of those, allowance on record ............... %d" % a["observed_run_ids_with_a_recorded_allowance"])
    print("   of those, allowance ABSENT .................. %d" % a["observed_run_ids_with_no_allowance_anywhere"])
    for rid in a["run_ids_with_no_allowance_anywhere"]:
        print("      %s" % rid)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
