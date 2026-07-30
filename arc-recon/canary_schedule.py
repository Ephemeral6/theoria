"""金丝雀常态化 -- the canary as a standing instrument rather than a one-off.

`canary.py` built the check: a fixed sequence per game, stored hashes, and a
mismatch that files an incident and freezes campaigns. What it did not have is
the word Theoria.md Phase 1 actually uses -- **定期**. A baseline taken once is
a photograph. This module is the clock.

WHAT IS NEW HERE, AND WHY EACH PIECE EXISTS

  * **A profile that fits a daily budget without losing power.** INC-009 showed
    that only 11 of the full sweep's 16 expected ACTION hashes can discriminate
    at all: the rest either repeat their game's RESET hash or land on the known
    counterfeit fingerprint, so a forged response would match them as well as a
    genuine one. `plan_profile` derives the cheapest sweep that still buys
    every discriminating step -- it is not a hardcoded game list, it is
    recomputed from `canary.json` every run, so re-baselining cannot silently
    leave it pointing at the wrong prefix. RESET is a command rather than an
    action (ACCESS_CHECK.md 6b), so a game reduced to RESET-only still checks a
    real hash for **zero** action cost.

  * **A due-check that is free.** `due` touches no network and spends nothing.
    That is what lets the scheduler run often and the canary run rarely: the
    5-minute reflex can ask the cheap question every time and the expensive one
    once a day.

  * **A blindness criterion, which the one-off canary did not need.** An
    outage yields INCOMPLETE -- deliberately neither a pass nor drift, so that
    a bad afternoon cannot halt the programme and cannot fake a clean bill of
    health either. Run on a schedule, that verdict acquires a failure mode of
    its own: a canary that is INCOMPLETE every day has *stopped measuring*,
    silently, while its log fills with entries. So consecutive INCOMPLETE runs
    are counted, and at `blind_after` the module files an incident. It does not
    freeze campaigns -- being unable to look is not evidence of drift -- but it
    refuses to let the silence go unrecorded.

  * **Fail-closed gating.** A frozen programme does not buy more replays: the
    freeze means drift is awaiting adjudication, and another sweep answers a
    question nobody asked. If `proxy.spend_gate` is importable it is used, and
    any refusal from it stops the sweep; the ARC preview is free of charge but
    the gate also counts outbound requests, which is the quantity the 600 rpm
    limit is charged against.

EXIT CODES (the scheduler reads these; they are the interface)

    0  PASS -- every planned step agreed
    1  DRIFT -- incident filed, campaigns frozen
    2  refused on safety grounds (sealed game, budget)
    3  nothing to do (not due, disabled, no spec)
    4  INCOMPLETE -- could not finish; not drift, not a pass
    5  gated -- frozen, or the shared spend gate refused

Usage:

    python canary_schedule.py due          # free; exit 0 = a sweep is due
    python canary_schedule.py run          # SPENDS ACTIONS if due
    python canary_schedule.py run --dry-run    # plans and gates, spends nothing
    python canary_schedule.py status       # offline summary
    python canary_schedule.py install      # prints the schtasks command
"""

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import canary                                              # noqa: E402
from client import DATA_DIR                                # noqa: E402
from precheck import SealedGameError, assert_playable      # noqa: E402

CONFIG_PATH = os.path.join(DATA_DIR, "canary_schedule.json")
STATE_PATH = os.path.join(DATA_DIR, "canary_schedule_state.json")

#: The hash `precheck.py` names as the counterfeit-short-id fingerprint
#: (INC-005). A step expecting it cannot tell a genuine response from a forged
#: one, so it is not counted as discriminating.
COUNTERFEIT_HASH = "801726dc499f3f52"

#: Written into `data/canary_schedule.json` the first time the module runs, so
#: that the schedule is a tracked, human-editable file rather than a constant
#: buried in code. Changing the cadence is then a reviewable diff.
DEFAULT_CONFIG: Dict[str, Any] = {
    "v": "1",
    "enabled": True,
    "purpose": ("Theoria.md Phase 1 接入核查: 定期重跑对哈希. Cadence lives here "
                "so that changing it is a diff, not a habit."),
    "profiles": {
        "quick": {
            "interval_hours": 24,
            "action_budget": 12,
            "mode": "discriminating",
            "note": ("The daily sweep. Cheapest plan that still buys every "
                     "discriminating step (INC-009); games with no "
                     "discriminating step are reduced to a RESET-only check, "
                     "which costs no actions."),
        },
        "full": {
            "interval_hours": 168,
            "action_budget": canary.INVOCATION_CAP,
            "mode": "complete",
            "note": ("The weekly sweep: every game, every stored step. It buys "
                     "the steps `quick` skips on purpose -- tn36's four "
                     "accepted no-ops discriminate nothing against forgery, "
                     "but their invariance is itself a property of the "
                     "environment, and a canary that never checks it would not "
                     "notice if those actions started doing something."),
        },
    },
    "blind_after": 3,
    "blind_after_note": ("Consecutive INCOMPLETE runs before the inability to "
                         "measure is itself filed as an incident. Not a "
                         "freeze: an outage is not drift."),
}


# -- files -------------------------------------------------------------------

def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _parse(stamp: Optional[str]) -> Optional[float]:
    if not stamp:
        return None
    try:
        return time.mktime(time.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ")) - time.timezone
    except ValueError:
        return None


def load_config() -> Dict[str, Any]:
    """Read the cadence, creating the tracked default on first use."""
    existing = canary._read_json(CONFIG_PATH)
    if existing is None:
        canary._write_json(CONFIG_PATH, DEFAULT_CONFIG)
        return json.loads(json.dumps(DEFAULT_CONFIG))
    return existing


def load_state() -> Dict[str, Any]:
    return canary._read_json(STATE_PATH) or {
        "v": "1", "profiles": {}, "consecutive_incomplete": 0,
    }


def save_state(state: Dict[str, Any]) -> None:
    canary._write_json(STATE_PATH, state)


# -- planning ----------------------------------------------------------------

def discriminating(game: Dict[str, Any]) -> List[int]:
    """Indices of the steps in `game` that could actually catch a forgery.

    A step whose expected hash equals its own game's RESET hash is matched by a
    response that merely replayed the opening frame; a step expecting
    COUNTERFEIT_HASH is matched by the exact response INC-005 caught being
    served for a short id. Neither discriminates. Everything else does.
    """
    expected = game["expected"]
    if not expected:
        return []
    reset_hash = expected[0].get("hash")
    out = []
    for step in expected[1:]:
        h = step.get("hash")
        if h is None or h == reset_hash or h == COUNTERFEIT_HASH:
            continue
        out.append(step["index"])
    return out


def plan_profile(spec: Dict[str, Any], action_budget: int,
                 mode: str = "discriminating") -> Dict[str, Any]:
    """Choose how many actions to buy per game, under a total action budget.

    Two modes, and the difference between them is the whole reason there are
    two profiles:

    `complete` buys every stored step of every game. It is the sweep that also
    checks the steps which cannot catch a forgery but can still catch a change
    -- tn36's accepted no-ops are invariant today, and that invariance is a
    fact about the environment that nothing else in this repository watches.
    It refuses rather than silently truncating if the budget cannot cover it.

    `discriminating` buys the cheapest plan that still funds every step which
    could tell a genuine response from a forged one, greedy on steps per
    action with ties broken by game id so the plan is deterministic.

    Prefixes, not subsets, in both: the sequences are paths through a game, so
    step 4 is only meaningful if steps 1..3 are the ones that led to it. The
    unit of purchase is a prefix length. Every game not funded is still present
    at zero actions -- a RESET-only check, free, and still a hash the server
    has to produce from real state.
    """
    games = spec.get("games", {})
    plan: Dict[str, int] = {g: 0 for g in games}

    if mode == "complete":
        needed = sum(len(g["sequence"]) for g in games.values())
        if needed > action_budget:
            raise canary.BudgetExceeded(
                "the complete sweep needs %d actions, budget is %d -- raise "
                "action_budget in %s or use mode 'discriminating'"
                % (needed, action_budget, CONFIG_PATH))
        plan = {g: len(games[g]["sequence"]) for g in games}
    elif mode == "discriminating":
        candidates = []
        for game_id, game in games.items():
            disc = discriminating(game)
            # Buying past a game's last discriminating step buys nothing, so
            # the prefix worth funding ends exactly there. Step index i is
            # reached by i actions (index 0 is the RESET frame).
            candidates.append((game_id, max(disc) if disc else 0, len(disc)))
        remaining = action_budget
        for game_id, want, gained in sorted(
                candidates,
                key=lambda c: (-(c[2] / c[1]) if c[1] else 0.0, -c[2], c[0])):
            if want and want <= remaining:
                plan[game_id] = want
                remaining -= want
    else:
        raise RuntimeError("unknown profile mode %r" % mode)

    total_disc = sum(len(discriminating(g)) for g in games.values())
    bought = sum(len([d for d in discriminating(games[g]) if d <= n])
                 for g, n in plan.items())
    total_steps = sum(len(g["sequence"]) for g in games.values())
    return {
        "mode": mode,
        "plan": plan,
        "actions": sum(plan.values()),
        "action_budget": action_budget,
        "discriminating_bought": bought,
        "discriminating_total": total_disc,
        "steps_bought": sum(plan.values()),
        "steps_total": total_steps,
        "reset_checks": len(plan),
    }


# -- the schedule ------------------------------------------------------------

def due(profile: str = "quick", config: Optional[Dict[str, Any]] = None,
        state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Is a sweep due? Free: no network, no files written."""
    config = config if config is not None else load_config()
    state = state if state is not None else load_state()
    if not config.get("enabled", True):
        return {"due": False, "reason": "disabled in %s" % CONFIG_PATH,
                "blocked": True}
    spec = config.get("profiles", {}).get(profile)
    if spec is None:
        return {"due": False, "reason": "no profile %r" % profile,
                "blocked": True}
    last = (state.get("profiles", {}).get(profile) or {}).get("last_attempt")
    interval = float(spec.get("interval_hours", 24)) * 3600.0
    last_ts = _parse(last)
    if last_ts is None:
        return {"due": True, "reason": "never run", "last": None,
                "interval_hours": spec.get("interval_hours")}
    age = time.time() - last_ts
    return {
        "due": age >= interval,
        "reason": ("%.1fh since the last attempt, interval %.1fh"
                   % (age / 3600.0, interval / 3600.0)),
        "last": last,
        "age_hours": round(age / 3600.0, 2),
        "interval_hours": spec.get("interval_hours"),
    }


# -- the shared spend gate ---------------------------------------------------

def open_spend_gate(campaign: str, actions: int) -> Tuple[Any, Any, Dict[str, Any]]:
    """Reserve headroom if the shared gate exists. Absence is recorded, not assumed away.

    The repository rule is 存在即必须用 -- if `proxy/spend_gate.py` is on disk it
    is on the spending path, no flag, no opt-out. It is not yet on master, so
    `ImportError` is a real state and is written into the run record as
    `absent` rather than silently treated as approval. Every other failure --
    a gate that exists but will not reserve -- refuses the sweep.
    """
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    try:
        from proxy.spend_gate import SpendGate           # type: ignore
    except ImportError:
        return None, None, {
            "spend_gate": "absent",
            "detail": ("proxy/spend_gate.py not importable at this commit; the "
                       "canary spent under its own per-invocation cap only"),
        }
    gate = SpendGate()
    reservation = gate.reserve(campaign, usd_cap=0.0, action_cap=int(actions))
    return gate, reservation, {"spend_gate": "reserved",
                               "reservation": getattr(reservation,
                                                      "reservation_id", None)}


# -- the run -----------------------------------------------------------------

def run_scheduled(profile: str = "quick", force: bool = False,
                  dry_run: bool = False, note: str = "") -> Dict[str, Any]:
    """The scheduled entry point. Returns a record; the caller maps it to an exit code."""
    config = load_config()
    state = load_state()
    stamp = _now()
    record: Dict[str, Any] = {"t": stamp, "profile": profile, "dry_run": dry_run}

    verdict = due(profile, config, state)
    record["due"] = verdict
    if not verdict["due"] and not force:
        record["outcome"] = "not-due"
        return record

    # The freeze is consulted before anything is planned, not after: a frozen
    # programme is waiting on a human, and another sweep cannot resolve that.
    freeze = canary.freeze_state()
    if freeze.get("frozen") and not force:
        record["outcome"] = "gated"
        record["gate"] = {"campaign_freeze": freeze.get("incident"),
                          "since": freeze.get("since"),
                          "games": freeze.get("games")}
        return record

    try:
        spec = canary.load_spec()
    except RuntimeError as exc:
        record["outcome"] = "no-spec"
        record["error"] = str(exc)
        return record

    settings = config["profiles"][profile]
    budget = int(settings.get("action_budget", canary.INVOCATION_CAP))
    plan = plan_profile(spec, budget, settings.get("mode", "discriminating"))
    record["plan"] = plan
    for game_id in plan["plan"]:
        assert_playable(game_id)           # raises SealedGameError; never caught here

    if plan["discriminating_bought"] < plan["discriminating_total"]:
        record["coverage_warning"] = (
            "%d of %d discriminating steps are unfunded at a budget of %d "
            "actions -- drift on the rest cannot be seen by this profile"
            % (plan["discriminating_total"] - plan["discriminating_bought"],
               plan["discriminating_total"], budget))

    if dry_run:
        record["outcome"] = "dry-run"
        return record

    gate, reservation, gate_note = open_spend_gate(
        "arc-recon-canary-%s" % profile, plan["actions"])
    record["gate"] = gate_note
    try:
        run = canary.replay(plan=plan["plan"],
                            note=(note or "scheduled %s sweep" % profile),
                            tags=["scheduled", profile])
    finally:
        if gate is not None and reservation is not None:
            gate.release(reservation, reason="canary sweep finished")

    # Settle in the SAME unit the reservation was made in, and do not let a
    # refusal at settlement time destroy the sweep's own bookkeeping.
    #
    # Both halves of this were wrong, and the `full` profile's first ever run
    # (2026-07-30, S22 item 1) is what showed it -- it had been configured,
    # scheduled and documented as a standing instrument without once executing.
    #
    # WRONG UNIT.  `open_spend_gate` reserves `plan["actions"]`; this line used
    # to charge `run["http_calls"]`.  RESET is a command, not an action
    # (ACCESS_CHECK.md 6b), so http_calls exceeds actions by exactly the number
    # of games swept -- 20 > 16 on `full`, 16 > 12 on `quick`.  **Every sweep of
    # either profile therefore tripped its own reservation**, and the daily one
    # had been doing so unnoticed.  Which unit is right is not a matter of taste:
    # S22's other half measured it and put it in README.md item 6 -- ARC's
    # `total_actions` counts SUCCESSFUL ACTIONS ONLY, failed 400s and retry
    # amplification do not bill.  So charging http_calls also over-charged the
    # shared pool by the RESET count on every sweep.
    #
    # NO SILENT ZERO.  The old default `run.get("http_calls", 0)` turned an
    # absent measurement into a free sweep.  There is a ledger line that looks
    # exactly like that outcome (spend_gate.jsonl seq 12487, a canary-quick
    # settlement of `actions: 0`), and while its cause is not established, a
    # default that prices a missing number at zero is not something to keep
    # while wondering.  A missing count is now an error.
    settlement_error = None
    if gate is not None and reservation is not None:
        if "actions_executed" not in run:
            raise RuntimeError(
                "the sweep returned no actions_executed, so there is nothing "
                "honest to charge the pool -- refusing to settle at zero")
        try:
            gate.record(reservation, usd=0.0,
                        actions=int(run["actions_executed"]))
            record["gate"] = dict(gate_note, settlement="recorded",
                                  charged_actions=int(run["actions_executed"]))
        except Exception as exc:
            # The actions are ALREADY SPENT by the time this runs -- replay has
            # returned.  Refusing to write the record does not un-spend them; it
            # only makes the next invocation repeat the spend, because `due`
            # reads the state file this function is on its way to updating.
            # That is precisely what happened on the first `full` run: 16
            # actions gone, all four games PASS, and the scheduler still
            # reporting "full: never run".  A standing task in that state
            # re-spends on every wake-up and can never record progress.
            # So the refusal is recorded and re-raised AFTER the state is
            # written, not instead of writing it.
            record["gate"] = dict(gate_note, settlement="refused",
                                  error="%s: %s" % (type(exc).__name__, exc),
                                  charged_actions=None)
            # Held in a local, never in `record`: the record is JSON-dumped by
            # `_cmd_run` and an exception object in it would turn a reporting
            # step into a crash.
            settlement_error = exc

    record["run"] = {k: run[k] for k in
                     ("t", "verdicts", "actions_executed", "http_calls",
                      "card_id", "plan")
                     if k in run}
    verdicts = set(run["verdicts"].values())
    if "DRIFT" in verdicts:
        record["outcome"] = "drift"
        record["incident"] = run.get("incident")
    elif verdicts == {"PASS"}:
        record["outcome"] = "pass"
    else:
        record["outcome"] = "incomplete"

    _record_outcome(config, state, profile, record)

    # Now that the state file knows this sweep happened, a settlement refusal
    # may surface.  Ordering is the whole point: `main()` maps SpendGate* to
    # exit 5, so the operator still sees it, but `due` will no longer claim the
    # sweep never ran.  The caller reads the detail from
    # `record["gate"]["settlement"]`.
    if settlement_error is not None:
        raise settlement_error
    return record


def _record_outcome(config: Dict[str, Any], state: Dict[str, Any],
                    profile: str, record: Dict[str, Any]) -> None:
    """Update the state file, and file the blindness incident if it is time."""
    profiles = dict(state.get("profiles", {}))
    entry = dict(profiles.get(profile, {}))
    entry["last_attempt"] = record["t"]
    entry["last_outcome"] = record["outcome"]
    entry["last_plan"] = record.get("plan", {}).get("plan")
    if record["outcome"] == "pass":
        entry["last_pass"] = record["t"]
    profiles[profile] = entry
    state["profiles"] = profiles

    streak = int(state.get("consecutive_incomplete", 0))
    if record["outcome"] == "incomplete":
        streak += 1
    else:
        streak = 0
    state["consecutive_incomplete"] = streak

    blind_after = int(config.get("blind_after", 3))
    if streak and streak >= blind_after and streak != state.get("blind_filed_at"):
        incident_id = canary.file_incident({
            "title": "Canary blind: %d consecutive INCOMPLETE sweeps" % streak,
            "severity": "process",
            "detail": ("The scheduled canary has been unable to complete its "
                       "sequence %d times running. INCOMPLETE is correctly not "
                       "drift -- an outage is not evidence that the environment "
                       "changed -- but a canary that cannot finish is not "
                       "measuring anything, and on a schedule that failure is "
                       "silent: the log keeps filling. Drift arriving during "
                       "this window would not be detected."
                       % streak),
            "consequence": ("Campaigns are NOT frozen. Measurements taken since "
                            "the last PASS (%s) are not covered by a canary."
                            % (entry.get("last_pass") or "never")),
            "evidence": ["arc-recon/data/canary_runs.jsonl",
                         "arc-recon/data/canary_schedule_state.json"],
            "filed_by": "arc-recon/canary_schedule.py",
        })
        state["blind_filed_at"] = streak
        state["blind_incident"] = incident_id
        record["blind_incident"] = incident_id
    elif not streak:
        state.pop("blind_filed_at", None)
        state.pop("blind_incident", None)

    state["updated"] = record["t"]
    state["last"] = {"profile": profile, "outcome": record["outcome"],
                     "t": record["t"],
                     "verdicts": record.get("run", {}).get("verdicts")}
    save_state(state)


OUTCOME_EXIT = {
    "pass": 0,
    "drift": 1,
    "not-due": 3,
    "no-spec": 3,
    "dry-run": 0,
    "incomplete": 4,
    "gated": 5,
}


# -- CLI ---------------------------------------------------------------------

def _cmd_due(args) -> int:
    verdict = due(args.profile)
    print("  %s: %s (%s)" % (args.profile,
                             "DUE" if verdict["due"] else "not due",
                             verdict["reason"]))
    if verdict.get("blocked"):
        return 3
    return 0 if verdict["due"] else 3


def _cmd_run(args) -> int:
    record = run_scheduled(args.profile, force=args.force,
                           dry_run=args.dry_run, note=args.note)
    plan = record.get("plan")
    if plan:
        print("  plan (%s, budget %d): %s"
              % (args.profile, plan["action_budget"],
                 json.dumps(plan["plan"], sort_keys=True)))
        print("  %d actions, %d RESET checks, %d/%d discriminating steps"
              % (plan["actions"], plan["reset_checks"],
                 plan["discriminating_bought"], plan["discriminating_total"]))
    if record.get("coverage_warning"):
        print("  WARNING: %s" % record["coverage_warning"])
    if record.get("gate"):
        print("  gate: %s" % json.dumps(record["gate"], sort_keys=True))
    print("  outcome: %s" % record["outcome"])
    if record.get("outcome") == "not-due":
        print("  %s" % record["due"]["reason"])
    if record.get("incident"):
        print("  DRIFT -> incident %s; campaigns FROZEN" % record["incident"])
    if record.get("blind_incident"):
        print("  BLIND -> incident %s filed (no freeze)" % record["blind_incident"])
    return OUTCOME_EXIT.get(record["outcome"], 2)


def _cmd_status(args) -> int:
    config = load_config()
    state = load_state()
    print("  schedule: %s" % ("enabled" if config.get("enabled", True)
                              else "DISABLED"))
    try:
        spec = canary.load_spec()
    except RuntimeError as exc:
        print("  %s" % exc)
        return 3
    for name, profile in sorted(config.get("profiles", {}).items()):
        plan = plan_profile(spec,
                            int(profile.get("action_budget",
                                            canary.INVOCATION_CAP)),
                            profile.get("mode", "discriminating"))
        verdict = due(name, config, state)
        entry = state.get("profiles", {}).get(name, {})
        print("    %-6s every %sh  %2d actions  %d/%d discriminating  %s"
              % (name, profile.get("interval_hours"), plan["actions"],
                 plan["discriminating_bought"], plan["discriminating_total"],
                 "DUE" if verdict["due"] else "next in %.1fh"
                 % max(0.0, float(profile.get("interval_hours", 24))
                       - float(verdict.get("age_hours") or 0))))
        print("           last %s (%s), last pass %s"
              % (entry.get("last_attempt") or "never",
                 entry.get("last_outcome") or "-",
                 entry.get("last_pass") or "never"))
    streak = state.get("consecutive_incomplete", 0)
    if streak:
        print("  consecutive INCOMPLETE: %d (blind_after=%s)"
              % (streak, config.get("blind_after")))
    freeze = canary.freeze_state()
    print("  campaigns: %s"
          % ("FROZEN by %s since %s" % (freeze.get("incident"),
                                        freeze.get("since"))
             if freeze.get("frozen") else "not frozen"))
    return 0


INSTALL_TEMPLATE = r"""schtasks /Create /TN TheoriaCanary /SC DAILY /ST {time} ^
  /TR "cmd /c cd /d {repo} && python arc-recon\canary_schedule.py run --profile quick" ^
  /F"""


def _cmd_install(args) -> int:
    print("  Daily, from the Task Scheduler (survives session death; the reflex")
    print("  layer runs every 5 minutes and must NOT carry this):")
    print()
    print(INSTALL_TEMPLATE.format(time=args.time, repo=REPO))
    print()
    print("  Or from the 5-minute reflex, which is free to ask the cheap question:")
    print()
    print("      python arc-recon/canary_schedule.py due --profile quick "
          "&& python arc-recon/canary_schedule.py run --profile quick")
    print()
    print("  `due` exits 3 when it is not time, so the expensive half runs once")
    print("  a day even when the cheap half is asked 288 times.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="canary_schedule.py", description=__doc__.splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    d = sub.add_parser("due", help="offline: exit 0 if a sweep is due, 3 if not")
    d.add_argument("--profile", default="quick")
    d.set_defaults(func=_cmd_due)

    r = sub.add_parser("run", help="the scheduled sweep (SPENDS ACTIONS if due)")
    r.add_argument("--profile", default="quick")
    r.add_argument("--force", action="store_true",
                   help="run even if not due, or if campaigns are frozen")
    r.add_argument("--dry-run", action="store_true",
                   help="plan and gate, spend nothing")
    r.add_argument("--note", default="")
    r.set_defaults(func=_cmd_run)

    s = sub.add_parser("status", help="offline: cadence, plans, last outcomes")
    s.set_defaults(func=_cmd_status)

    i = sub.add_parser("install", help="print the scheduled-task command")
    i.add_argument("--time", default="03:30")
    i.set_defaults(func=_cmd_install)
    return parser


def main(argv: List[str]) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except SealedGameError as exc:
        print("  REFUSED: %s" % exc)
        return 2
    except canary.BudgetExceeded as exc:
        print("  BUDGET: %s" % exc)
        return 2
    except Exception as exc:                       # the spend gate fails closed
        if type(exc).__name__.startswith("SpendGate") or \
                type(exc).__name__ == "NoReservation":
            print("  GATED: %s: %s" % (type(exc).__name__, exc))
            return 5
        raise


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
