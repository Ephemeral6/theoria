"""先算后花 -- the arithmetic that has to exist before a live run is launched.

Two jobs, and they are separate on purpose.

**The gate.** `monitor/prompts/S3-spend-gate.md` specifies `proxy/spend_gate.py`
as a shared, cross-session, fail-closed register of what has been spent against
one ARC key and one Anthropic bill. E3's brief says the gate is mandatory *once
S3 has landed*. So this module looks for it and uses it if it is there; if it is
not, it says so in the plan with the reason, and the plan itself carries the
`campaign` field the gate will want, so adopting it later is a wiring change and
not a rewrite. What this module will not do is silently proceed as though the
question had not been asked.

**The projection.** The binding constraint on this arm is not the action budget.
On the first live contact the arm spent 7 actions and $6.32: every action is
cheap and every desk call costs about a dollar and a quarter and takes about
nine minutes. So a run's cost is set by how many times the desk is called, which
is set by the evidence gate (`inner/loop.MIN_NEW_FRAMES_BETWEEN_THEORIZE`), not
by `--budget`. The projection here computes, from a prior run's *measured*
per-call cost, how many actions the cost ceiling actually permits -- so the
number in `--cost-ceiling` is chosen against arithmetic rather than against
optimism, and the gap between the projection and the outturn is itself the C2
bill-shape datum E3 is asking for.

The basis is read from a prior run's `cost_curve.json` rather than hardcoded,
because a hardcoded price is a number nobody re-derives when the model changes.
"""

import argparse
import importlib.util
import json
import os
import statistics
import sys
from typing import Any, Dict, List, Optional

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap                                       # noqa: F401  (sys.path)

#: Where S3's gate will live when it lands. Checked, never imported blind.
SPEND_GATE = os.path.join(_bootstrap.REPO, "proxy", "spend_gate.py")

#: The campaign name every record of this run carries. S3's `reserve(campaign,
#: usd_cap, action_cap)` takes one of these; writing it now means the ledger
#: rows are already partitioned when the gate arrives.
CAMPAIGN = "theoria-arm"


def gate_status() -> Dict[str, Any]:
    """Is the shared spend gate available, and what does it say?

    Fail-closed is S3's rule for the gate's *own* callers: a gate that cannot
    read its ledger refuses to let anyone out to the network. That rule cannot
    bind a caller that runs before the gate exists -- there is nothing to fail
    closed -- so what this returns is a status the plan records and a human
    reads, and the honest label for the situation is `absent`, not `ok`.
    """
    if not os.path.exists(SPEND_GATE):
        return {
            "available": False,
            "status": "absent",
            "path": SPEND_GATE,
            "detail": ("proxy/spend_gate.py does not exist on this commit. "
                       "S3-spend-gate is the item that creates it and it has "
                       "not landed: branch agent/s3-spend-gate carries no file "
                       "under proxy/ matching *spend*. Until it does, this run "
                       "budgets against its own arithmetic only and CANNOT see "
                       "what a concurrent session has spent against the same "
                       "key and the same bill -- which is precisely the "
                       "exposure S3 was raised to close (INC-BA-003)."),
            "campaign": CAMPAIGN,
        }
    spec = importlib.util.spec_from_file_location("proxy_spend_gate", SPEND_GATE)
    if spec is None or spec.loader is None:
        return {"available": False, "status": "unloadable", "path": SPEND_GATE,
                "detail": "the file exists but is not importable",
                "campaign": CAMPAIGN}
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)                  # noqa: S102
    except Exception as exc:                             # noqa: BLE001
        return {"available": False, "status": "raised", "path": SPEND_GATE,
                "detail": "%s: %s" % (type(exc).__name__, exc),
                "campaign": CAMPAIGN}
    return {"available": True, "status": "present", "path": SPEND_GATE,
            "campaign": CAMPAIGN,
            "exports": sorted(n for n in dir(module) if not n.startswith("_")),
            "_module": module}


def reserve(gate: Dict[str, Any], *, usd_cap: float,
            action_cap: int) -> Dict[str, Any]:
    """Hold a reservation if the gate is there. A refusal is returned, not raised.

    The caller decides what a refusal means; this module's contract is that it
    never spends and never pretends. When the gate is absent the reservation is
    `null` and the plan says so, which is the state E3 launched in.
    """
    module = gate.get("_module")
    if module is None or not hasattr(module, "reserve"):
        return {"held": False, "reason": gate.get("status", "absent")}
    try:
        handle = module.reserve(CAMPAIGN, usd_cap, action_cap)  # type: ignore[attr-defined]
    except Exception as exc:                             # noqa: BLE001
        return {"held": False, "reason": "%s: %s" % (type(exc).__name__, exc)}
    return {"held": True, "handle": str(handle), "usd_cap": usd_cap,
            "action_cap": action_cap}


# ------------------------------------------------------------------ the basis
def basis_from_run(run_dir: str) -> Dict[str, Any]:
    """Measured per-call cost and duration, read off a prior run's cost curve."""
    path = os.path.join(run_dir, "cost_curve.json")
    if not os.path.exists(path):
        return {"available": False,
                "detail": "no cost_curve.json under %s" % run_dir}
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    # Two shapes exist and both are legitimate: `armtools/archive.py` writes a
    # flat per-call list rebuilt from the ledger, and `inner/loop.py` writes the
    # per-turn view under a "calls" key. Read either; the per-call cost is the
    # same number in both, under two names.
    calls: List[Dict[str, Any]] = (raw if isinstance(raw, list)
                                   else raw.get("calls") or [])
    usd = [float(c.get("usd", c.get("cli_cost_usd")) or 0.0) for c in calls]
    secs = [float(c.get("elapsed_ms") or 0) / 1000.0 for c in calls]
    out_tokens = [int((c.get("usage") or {}).get("output_tokens") or 0)
                  for c in calls]
    if not usd:
        return {"available": False, "detail": "cost_curve.json is empty"}
    return {
        "available": True,
        "source_run": os.path.basename(os.path.abspath(run_dir)),
        "calls": len(usd),
        "usd_total": round(sum(usd), 6),
        "usd_per_call_mean": round(statistics.fmean(usd), 6),
        "usd_per_call_max": round(max(usd), 6),
        "seconds_per_call_mean": round(statistics.fmean(secs), 1),
        "seconds_per_call_max": round(max(secs), 1),
        "output_tokens_per_call_mean": round(statistics.fmean(out_tokens), 1),
        "note": ("cost is dominated by output tokens: input is cache-creation "
                 "only and two orders of magnitude smaller"),
    }


# ------------------------------------------------------------- the projection
def project(basis: Dict[str, Any], *, action_cap: int, usd_ceiling: float,
            wall_clock_s: float, legal_actions: int,
            frames_per_theorize: int,
            max_theorize_per_turn: int) -> Dict[str, Any]:
    """What the ceiling actually buys, in calls, actions and hours.

    The chain: the evidence gate holds the desk back until `frames_per_theorize`
    new transitions have arrived, and one turn may burn up to
    `max_theorize_per_turn` calls repairing. So one *cycle* is roughly
    `frames_per_theorize` actions and somewhere between one and
    `max_theorize_per_turn` calls, and the number of cycles the money buys is
    what decides how far into the action budget a run can reach.

    Both ends are reported, because which one obtains is a real property of the
    run -- a manual that certifies clean after one call costs half of one that
    needs the repair round every time.
    """
    if not basis.get("available"):
        return {"available": False, "detail": basis.get("detail")}

    per_call = basis["usd_per_call_mean"]
    per_call_max = basis["usd_per_call_max"]
    secs = basis["seconds_per_call_mean"]

    calls_affordable = int(usd_ceiling // per_call) if per_call else 0
    calls_affordable_worst = int(usd_ceiling // per_call_max) if per_call_max else 0
    calls_in_wall_clock = int(wall_clock_s // secs) if secs else 0

    def actions_for(calls: int, calls_per_cycle: int) -> int:
        cycles = calls // max(1, calls_per_cycle)
        return legal_actions + cycles * frames_per_theorize

    best = actions_for(calls_affordable, 1)
    worst = actions_for(calls_affordable_worst, max_theorize_per_turn)

    binding = min(
        [("cost_ceiling", calls_affordable),
         ("wall_clock", calls_in_wall_clock)],
        key=lambda pair: pair[1])[0]
    if min(best, worst) >= action_cap:
        binding = "action_budget"

    return {
        "available": True,
        "inputs": {"action_cap": action_cap, "usd_ceiling": usd_ceiling,
                   "wall_clock_s": wall_clock_s,
                   "legal_actions_opening_sweep": legal_actions,
                   "frames_per_theorize": frames_per_theorize,
                   "max_theorize_per_turn": max_theorize_per_turn},
        "desk_calls_the_ceiling_buys": calls_affordable,
        "desk_calls_the_ceiling_buys_at_worst_observed_price": calls_affordable_worst,
        "desk_calls_the_wall_clock_allows": calls_in_wall_clock,
        "actions_reachable_best_case": min(best, action_cap),
        "actions_reachable_worst_case": min(worst, action_cap),
        "binding_constraint": binding,
        "projected_usd_if_action_cap_were_reached": round(
            per_call * max(1, (action_cap - legal_actions) // max(1, frames_per_theorize)),
            2),
        "reading": (
            "the action budget is NOT the binding constraint: reaching %d "
            "actions would take about $%.0f of desk time, so the run will stop "
            "on %s at roughly %d-%d actions. That gap is the measurement, not a "
            "shortfall -- E3 asks for the bill shape, and this is its predicted "
            "shape stated before the money is spent."
            % (action_cap,
               per_call * max(1, (action_cap - legal_actions) // max(1, frames_per_theorize)),
               binding, min(worst, action_cap), min(best, action_cap))),
    }


def build_plan(*, basis_run: str, action_cap: int, usd_ceiling: float,
               wall_clock_s: float, legal_actions: int,
               game_id: str, carried_from: Optional[str] = None) -> Dict[str, Any]:
    from inner.loop import (MAX_THEORIZE_PER_TURN,       # noqa: PLC0415
                            MIN_NEW_FRAMES_BETWEEN_THEORIZE)

    gate = gate_status()
    basis = basis_from_run(basis_run)
    projection = project(
        basis, action_cap=action_cap, usd_ceiling=usd_ceiling,
        wall_clock_s=wall_clock_s, legal_actions=legal_actions,
        frames_per_theorize=MIN_NEW_FRAMES_BETWEEN_THEORIZE,
        max_theorize_per_turn=MAX_THEORIZE_PER_TURN)
    return {
        "campaign": CAMPAIGN,
        "game_id": game_id,
        "carried_books_from": carried_from,
        "spend_gate": {k: v for k, v in gate.items() if not k.startswith("_")},
        "reservation": reserve(gate, usd_cap=usd_ceiling, action_cap=action_cap),
        "basis": basis,
        "projection": projection,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--basis-run", required=True,
                    help="a prior run directory with a cost_curve.json")
    ap.add_argument("--out", required=True, help="where to write BUDGET_PLAN.json")
    ap.add_argument("--game", required=True)
    ap.add_argument("--actions", type=int, default=120)
    ap.add_argument("--ceiling", type=float, default=18.0)
    # Follows the arm's own default rather than keeping a fourth copy: this
    # tool projects whether a configuration fits, so a default that disagrees
    # with the one the arm actually runs projects a configuration nobody runs.
    from harness.spend import DEFAULT_WALL_CLOCK_S    # noqa: PLC0415
    ap.add_argument("--wall-clock", type=float, default=DEFAULT_WALL_CLOCK_S)
    ap.add_argument("--legal-actions", type=int, default=4)
    ap.add_argument("--carried-from", default=None)
    args = ap.parse_args(argv)

    plan = build_plan(basis_run=args.basis_run, action_cap=args.actions,
                      usd_ceiling=args.ceiling, wall_clock_s=args.wall_clock,
                      legal_actions=args.legal_actions, game_id=args.game,
                      carried_from=args.carried_from)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(plan, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(json.dumps(plan, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
