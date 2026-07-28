"""金丝雀重放 -- a fixed action sequence per game, replayed on a schedule.

Theoria.md Phase 1, 接入核查: "game_id 版本后缀之外仍设**金丝雀重放**(每局一条固定
动作序列,定期重跑对哈希,防同 ID 行为漂移;漂移 = incident 并冻结战役)".

The version suffix in a `game_id` is a *declared* fingerprint: it changes when the
operators say the environment changed. The canary is the *observed* fingerprint.
It catches the case the suffix cannot -- the same id quietly behaving differently.
Everything built on a game (a mined rule, a Lean theorem, a campaign's scores)
assumes the environment it was measured on is the environment still being played.
Drift silently invalidates all of it, so the check has to be cheap enough to run
often and loud enough that nobody can miss it.

WHAT MAKES THIS A CHECK RATHER THAN A RITUAL

  * **Expectations are never rewritten by a failing run.** `replay` compares
    against `data/canary.json` and can only *fail*; it never updates the file.
    Re-baselining is a separate, deliberate command (`rebaseline`) that demands a
    reason, files an incident of its own, and keeps the superseded hashes. A
    canary that heals itself on mismatch measures nothing. Same failure mode as
    INC-003, one instrument along.
  * **Drift is not a log line.** A mismatch appends an incident to
    `data/incidents.jsonl` AND writes `data/campaign_freeze.json`. The freeze is
    a file, not a memory: any track can gate on it with
    `python canary.py check-freeze` (exit 1 = frozen) or by reading the JSON, and
    the gate works across sessions and across tracks -- which is precisely what
    INC-BA-003 showed a per-process counter cannot do.
  * **A step that could not run is not a step that agreed.** Missing hashes are
    counted as `unusable`, never as agreement (INC-003), and a replay that could
    not complete its sequence is `INCOMPLETE`, which is neither PASS nor drift.
    Only a present-on-both-sides hash mismatch freezes campaigns; an outage must
    not be able to halt the programme, and must not be able to hide drift either.

BUDGET AND SAFETY. `assert_playable` (shared with precheck.py) refuses anything
outside the development pile -- a successful RESET returns the first frame, so a
canary pointed at a sealed game would burn it. <=6 executed actions per game and
a per-invocation total cap; the whole development pile costs 16 actions. Failed
attempts execute nothing and are not charged (scorecard `total_actions` tracks
successful actions only -- baseline-arms' four-sample measurement, PARTNER_SYNC
2026-07-28). Canary plays open their own scorecard tagged `canary`, so they never
land in a campaign's action or score counts (Theoria.md Phase 1.4).
"""

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from client import DATA_DIR, ArcClient                      # noqa: E402
from precheck import (                                      # noqa: E402
    ACTION_ATTEMPTS,
    RESET_ATTEMPTS,
    SealedGameError,
    assert_playable,
    dev_pile,
    hash_frames,
    send_command,
)

CANARY_PATH = os.path.join(DATA_DIR, "canary.json")
RUNS_PATH = os.path.join(DATA_DIR, "canary_runs.jsonl")
FREEZE_PATH = os.path.join(DATA_DIR, "campaign_freeze.json")
INCIDENTS_PATH = os.path.join(DATA_DIR, "incidents.jsonl")
PRECHECK_PATH = os.path.join(DATA_DIR, "precheck.json")

# Per-game cap. The sequences are deliberately short: a canary is run often, so
# its price is paid over and over. 16 actions covers the whole development pile.
ACTIONS_PER_GAME = 6
# Per-invocation cap, checked before anything is spent.
INVOCATION_CAP = 30

SPEC_VERSION = "v1"


class BudgetExceeded(Exception):
    """The canary's own action cap would be crossed."""


class CampaignFrozen(Exception):
    """A campaign gate consulted the freeze file and it was set."""


# -- files ------------------------------------------------------------------

def _read_json(path: str) -> Optional[Dict[str, Any]]:
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")


def _append_jsonl(path: str, entry: Dict[str, Any]) -> None:
    with open(path, "a", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(entry, sort_keys=True, ensure_ascii=False))
        fh.write("\n")


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def load_spec() -> Dict[str, Any]:
    spec = _read_json(CANARY_PATH)
    if spec is None:
        raise RuntimeError(
            "%s not found. Run `python canary.py seed` to build it from "
            "precheck.json." % CANARY_PATH
        )
    return spec


# -- incidents and the freeze ----------------------------------------------

def next_incident_id() -> str:
    """INC-006, INC-007, ... -- continues arc-recon's own numbering.

    Suffixed ids (INC-001a, INC-002a) are revisions of an existing incident and
    never take a fresh number, so only the numeric stem is counted.
    """
    highest = 0
    if os.path.exists(INCIDENTS_PATH):
        for line in open(INCIDENTS_PATH, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            ident = str(json.loads(line).get("id", ""))
            stem = ident[4:7] if ident.startswith("INC-") else ""
            if stem.isdigit():
                highest = max(highest, int(stem))
    return "INC-%03d" % (highest + 1)


def file_incident(entry: Dict[str, Any]) -> str:
    entry = dict(entry)
    entry.setdefault("id", next_incident_id())
    entry.setdefault("t", _now())
    entry.setdefault("sealed_games_touched", 0)
    _append_jsonl(INCIDENTS_PATH, entry)
    return entry["id"]


def freeze_campaigns(incident_id: str, games: List[str], reason: str,
                     detail: Dict[str, Any]) -> None:
    """Write the cross-track, cross-session campaign gate.

    A file rather than a counter, and read by whoever is about to spend: the
    root cause in INC-BA-003 was two gates that could not see each other.
    """
    existing = _read_json(FREEZE_PATH) or {}
    history = list(existing.get("history", []))
    if existing.get("frozen"):
        history.append({k: existing.get(k) for k in
                        ("since", "incident", "games", "reason")})
    _write_json(FREEZE_PATH, {
        "frozen": True,
        "since": _now(),
        "incident": incident_id,
        "games": sorted(games),
        "reason": reason,
        "detail": detail,
        "how_to_clear": (
            "Do not delete this file. Adjudicate the drift first: either the "
            "environment changed (then the affected games' prior measurements "
            "are void and the canary must be re-baselined with "
            "`canary.py rebaseline --reason ...`), or the canary itself is "
            "wrong (then fix it and record why). Clearing is an owner decision "
            "recorded as an incident, not a housekeeping step."
        ),
        "history": history,
    })


def freeze_state() -> Dict[str, Any]:
    return _read_json(FREEZE_PATH) or {"frozen": False}


def assert_campaigns_unfrozen() -> None:
    """The gate other tracks call before spending anything on a campaign."""
    state = freeze_state()
    if state.get("frozen"):
        raise CampaignFrozen(
            "campaigns are frozen since %s by %s (games: %s): %s"
            % (state.get("since"), state.get("incident"),
               ", ".join(state.get("games") or []), state.get("reason"))
        )


# -- seeding ----------------------------------------------------------------

def seed_from_precheck(length_by_game: Optional[Dict[str, int]] = None
                       ) -> Dict[str, Any]:
    """Build the spec offline from precheck.json. No API calls.

    Only steps whose hash agreed across the precheck's two independent replays
    become expectations: a single observation is a reading, not a baseline.
    """
    report = _read_json(PRECHECK_PATH)
    if report is None:
        raise RuntimeError("%s not found; run the precheck first" % PRECHECK_PATH)
    length_by_game = length_by_game or {}
    games: Dict[str, Any] = {}
    for game_id, result in sorted(report.get("results", {}).items()):
        assert_playable(game_id)
        if result["verdict"]["verdict"] != "PASS":
            continue
        run_a, run_b = result.get("run_a") or [], result.get("run_b") or []
        want = min(length_by_game.get(game_id, ACTIONS_PER_GAME), ACTIONS_PER_GAME)
        steps: List[Dict[str, Any]] = []
        for index, step in enumerate(run_a):
            if index >= len(run_b):
                break
            hash_a, hash_b = step.get("hash"), run_b[index].get("hash")
            if hash_a is None or hash_a != hash_b:
                break
            steps.append({
                "index": index,
                "action": step["action"],
                "hash": hash_a,
                "n_frames": step.get("n_frames"),
                "levels_completed": step.get("levels_completed"),
            })
            if index >= want:            # index 0 is RESET, not an action
                break
        if len(steps) < 2:
            continue
        games[game_id] = {
            "sequence": [int(s["action"][len("ACTION"):]) for s in steps[1:]],
            "expected": steps,
            "actions": len(steps) - 1,
            "source": ("precheck.json run_a/run_b, both replays agreeing "
                       "(verdict PASS)"),
        }
    return {
        "version": SPEC_VERSION,
        "created": _now(),
        "purpose": ("Theoria.md Phase 1 接入核查: detect behaviour drift under an "
                    "unchanged game_id. Drift = incident + campaign freeze."),
        "hash_function": ("sha256 of json.dumps(frame, sort_keys=True, "
                          "separators=(',',':')), first 16 hex chars -- the same "
                          "function the precheck used (precheck.hash_frames)"),
        "budget": {"actions_per_game": ACTIONS_PER_GAME,
                   "invocation_cap": INVOCATION_CAP,
                   "total_actions_for_the_development_pile":
                       sum(g["actions"] for g in games.values())},
        "policy": {
            "id_form": "full id only; short-id 200s are counterfeit (INC-005)",
            "scorecard": "canary plays open their own scorecard tagged `canary`",
            "on_drift": ("append incident to data/incidents.jsonl and write "
                         "data/campaign_freeze.json"),
            "on_incomplete": ("INCOMPLETE: no incident, no freeze -- an outage is "
                              "not drift, and must not be able to mask it either"),
            "rebaseline": ("`canary.py rebaseline --reason ...` only; a replay "
                           "never rewrites an expectation"),
        },
        "games": games,
    }


# -- replay -----------------------------------------------------------------

def play(client: ArcClient, game_id: str, spec: Dict[str, Any],
         card_id: str) -> Dict[str, Any]:
    """RESET, walk the fixed sequence, hash every frame batch."""
    assert_playable(game_id)
    sequence = spec["sequence"]
    if len(sequence) > ACTIONS_PER_GAME:
        raise BudgetExceeded("%s: %d actions > %d per-game cap"
                             % (game_id, len(sequence), ACTIONS_PER_GAME))

    status, opening, stats = send_command(
        client, "/api/cmd/RESET", {"game_id": game_id, "card_id": card_id},
        note="canary RESET %s" % game_id,
        attempts=RESET_ATTEMPTS, delay_base=0.5, delay_cap=5.0)
    http_calls = stats["attempts"]
    if status != 200 or not isinstance(opening, dict):
        return {"game_id": game_id, "observed": [], "actions_executed": 0,
                "http_calls": http_calls,
                "error": "RESET failed after %d attempts: HTTP %s"
                         % (stats["attempts"], status)}

    guid = opening["guid"]
    observed = [{"index": 0, "action": "RESET",
                 "hash": hash_frames(opening["frame"]),
                 "n_frames": len(opening["frame"]),
                 "levels_completed": opening.get("levels_completed"),
                 "attempts": stats["attempts"]}]
    executed = 0
    error = None
    for offset, action in enumerate(sequence):
        status, response, stats = send_command(
            client, "/api/cmd/ACTION%d" % action,
            {"game_id": game_id, "card_id": card_id, "guid": guid},
            note="canary ACTION%d #%d %s" % (action, offset, game_id),
            attempts=ACTION_ATTEMPTS, delay_cap=5.0)
        http_calls += stats["attempts"]
        if status != 200 or not isinstance(response, dict):
            error = ("ACTION%d #%d failed after %d attempts: HTTP %s"
                     % (action, offset, stats["attempts"], status))
            break
        executed += 1
        if executed > ACTIONS_PER_GAME:
            raise BudgetExceeded("%s: executed %d > %d"
                                 % (game_id, executed, ACTIONS_PER_GAME))
        frames = response.get("frame", [])
        observed.append({"index": offset + 1, "action": "ACTION%d" % action,
                         "hash": hash_frames(frames),
                         "n_frames": len(frames) if isinstance(frames, list) else None,
                         "levels_completed": response.get("levels_completed"),
                         "attempts": stats["attempts"]})
    return {"game_id": game_id, "guid": guid, "observed": observed,
            "actions_executed": executed, "http_calls": http_calls,
            "error": error}


def compare(expected: List[Dict[str, Any]],
            observed: List[Dict[str, Any]]) -> Dict[str, Any]:
    """PASS / DRIFT / INCOMPLETE.

    A step with no observation on one side is `unusable`, never agreement
    (INC-003). DRIFT needs a real hash mismatch with both hashes present; an
    incomplete replay is INCOMPLETE even if every step it did reach agreed,
    because the steps it never reached are exactly where drift could hide.
    """
    by_index = {s["index"]: s for s in observed}
    mismatches, unusable, agreed = [], [], 0
    for step in expected:
        seen = by_index.get(step["index"])
        if seen is None or seen.get("hash") is None:
            unusable.append({"index": step["index"], "action": step["action"]})
        elif seen["hash"] != step["hash"]:
            mismatches.append({"index": step["index"], "action": step["action"],
                               "expected": step["hash"], "observed": seen["hash"],
                               "expected_n_frames": step.get("n_frames"),
                               "observed_n_frames": seen.get("n_frames")})
        else:
            agreed += 1
    complete = not unusable
    return {
        "verdict": ("DRIFT" if mismatches
                    else ("PASS" if complete else "INCOMPLETE")),
        "steps_expected": len(expected),
        "steps_agreed": agreed,
        "unusable_steps": unusable,
        "mismatches": mismatches,
        "first_divergence": mismatches[0]["index"] if mismatches else None,
    }


def replay(games: Optional[List[str]] = None,
           client: Optional[ArcClient] = None,
           note: str = "") -> Dict[str, Any]:
    spec = load_spec()
    targets = games or sorted(spec["games"])
    unknown = [g for g in targets if g not in spec["games"]]
    if unknown:
        raise RuntimeError("no canary spec for: %s" % ", ".join(unknown))
    for game_id in targets:
        assert_playable(game_id)

    planned = sum(len(spec["games"][g]["sequence"]) for g in targets)
    if planned > INVOCATION_CAP:
        raise BudgetExceeded("planned %d actions > invocation cap %d"
                             % (planned, INVOCATION_CAP))

    client = client or ArcClient()
    card_id = client.open_scorecard(tags=["canary", SPEC_VERSION])["card_id"]
    results, drifted = {}, []
    for game_id in targets:
        outcome = play(client, game_id, spec["games"][game_id], card_id)
        verdict = compare(spec["games"][game_id]["expected"], outcome["observed"])
        results[game_id] = {**outcome, "verdict": verdict}
        if verdict["verdict"] == "DRIFT":
            drifted.append(game_id)
        print("  %-18s %-10s agreed=%d/%d actions=%d http=%d%s"
              % (game_id, verdict["verdict"], verdict["steps_agreed"],
                 verdict["steps_expected"], outcome["actions_executed"],
                 outcome["http_calls"],
                 ("  " + outcome["error"]) if outcome.get("error") else ""))

    run = {
        "t": _now(),
        "spec_version": spec.get("version"),
        "note": note,
        # The transport is a covariate, not a constant: INC-007 changed it, and a
        # before/after HTTP-amplification comparison is meaningless unless each
        # run says which transport produced it.
        "transport": getattr(client, "transport",
                             {"cookies": False,
                              "description": "pre-INC-007 client: bare urllib, "
                                             "no cookie jar"}),
        "card_id": card_id,
        "targets": targets,
        "planned_actions": planned,
        "actions_executed": sum(r["actions_executed"] for r in results.values()),
        "http_calls": sum(r["http_calls"] for r in results.values()),
        "verdicts": {g: r["verdict"]["verdict"] for g, r in results.items()},
        "results": results,
    }

    if drifted:
        detail = {g: results[g]["verdict"]["mismatches"] for g in drifted}
        incident_id = file_incident({
            "title": "Canary drift: %s behaved differently under an unchanged "
                     "game_id" % ", ".join(drifted),
            "severity": "blocking",
            "detail": ("The canary replayed its published fixed sequence and the "
                       "frame hashes no longer match the baseline in "
                       "data/canary.json. The version suffix in the game_id did "
                       "not change, so the declared fingerprint says the "
                       "environment is the same one every prior measurement was "
                       "taken on. One of those two statements is false."),
            "games": sorted(drifted),
            "mismatches": detail,
            "consequence": ("Campaigns are frozen (data/campaign_freeze.json). "
                            "Every measurement taken on the affected games before "
                            "this run is suspect: mined rules, proofs, scores and "
                            "the determinism precheck verdicts all assume a fixed "
                            "environment."),
            "evidence": ["arc-recon/data/canary.json",
                         "arc-recon/data/canary_runs.jsonl",
                         "arc-recon/data/recon_ledger.jsonl"],
            "filed_by": "arc-recon/canary.py",
        })
        freeze_campaigns(incident_id, drifted,
                         "canary drift on %s" % ", ".join(sorted(drifted)),
                         detail)
        run["incident"] = incident_id
        run["froze_campaigns"] = True

    _append_jsonl(RUNS_PATH, run)
    return run


# -- baselining -------------------------------------------------------------

def record_baseline_confirmation(run: Dict[str, Any]) -> None:
    """Note in the spec that a replay confirmed it. Hashes are never touched."""
    spec = load_spec()
    confirmations = list(spec.get("confirmations", []))
    confirmations.append({
        "t": run["t"],
        "verdicts": run["verdicts"],
        "actions_executed": run["actions_executed"],
        "http_calls": run["http_calls"],
    })
    spec["confirmations"] = confirmations
    _write_json(CANARY_PATH, spec)


def rebaseline(games: List[str], reason: str) -> Dict[str, Any]:
    """Deliberately replace expectations, keeping the superseded ones.

    Separate from `replay` on purpose. If a failing run could rewrite the file
    it compares against, the instrument would report PASS forever.
    """
    if not reason.strip():
        raise RuntimeError("rebaseline requires --reason: why is the old "
                           "expectation no longer the truth?")
    spec = load_spec()
    client = ArcClient()
    card_id = client.open_scorecard(tags=["canary", "rebaseline"])["card_id"]
    superseded = {}
    for game_id in games:
        assert_playable(game_id)
        outcome = play(client, game_id, spec["games"][game_id], card_id)
        if outcome.get("error"):
            raise RuntimeError("%s: %s" % (game_id, outcome["error"]))
        superseded[game_id] = spec["games"][game_id]["expected"]
        spec["games"][game_id]["expected"] = [
            {k: v for k, v in step.items() if k != "attempts"}
            for step in outcome["observed"]
        ]
        spec["games"][game_id]["source"] = "rebaselined %s: %s" % (_now(), reason)
    history = list(spec.get("rebaselines", []))
    history.append({"t": _now(), "games": sorted(games), "reason": reason,
                    "superseded": superseded})
    spec["rebaselines"] = history
    _write_json(CANARY_PATH, spec)
    file_incident({
        "title": "Canary re-baselined on %s" % ", ".join(sorted(games)),
        "severity": "process",
        "detail": reason,
        "games": sorted(games),
        "consequence": ("Expectations replaced; the superseded hashes are kept in "
                        "data/canary.json under `rebaselines`. Measurements taken "
                        "before this point are on the old baseline."),
        "filed_by": "arc-recon/canary.py rebaseline",
    })
    return spec


# -- CLI --------------------------------------------------------------------

def _cmd_seed(args) -> int:
    lengths = {}
    for token in args.length or []:
        game_id, _, value = token.partition("=")
        lengths[game_id] = int(value)
    if os.path.exists(CANARY_PATH) and not args.force:
        print("  %s exists; refusing to overwrite (use --force)" % CANARY_PATH)
        return 3
    spec = seed_from_precheck(lengths)
    _write_json(CANARY_PATH, spec)
    for game_id, game in sorted(spec["games"].items()):
        print("  %-18s actions=%d  sequence=%s"
              % (game_id, game["actions"], game["sequence"]))
    print("  total actions for one full sweep: %d"
          % spec["budget"]["total_actions_for_the_development_pile"])
    print("  spec -> %s" % CANARY_PATH)
    return 0


def _cmd_replay(args) -> int:
    run = replay(args.games or None, note=args.note)
    if args.confirm_baseline:
        record_baseline_confirmation(run)
    print("  actions=%d http=%d  %s"
          % (run["actions_executed"], run["http_calls"],
             json.dumps(run["verdicts"], sort_keys=True)))
    if run.get("froze_campaigns"):
        print("  DRIFT -> incident %s filed; campaigns FROZEN (%s)"
              % (run["incident"], FREEZE_PATH))
        return 1
    if any(v != "PASS" for v in run["verdicts"].values()):
        print("  INCOMPLETE: a replay could not finish. Not drift, not a pass; "
              "re-run when the API is available.")
        return 4
    return 0


def _cmd_status(args) -> int:
    spec = _read_json(CANARY_PATH)
    if spec is None:
        print("  no spec at %s" % CANARY_PATH)
        return 3
    print("  spec %s, %d games, %d actions per sweep"
          % (spec["version"], len(spec["games"]),
             spec["budget"]["total_actions_for_the_development_pile"]))
    for game_id, game in sorted(spec["games"].items()):
        print("    %-18s %s  expected steps=%d"
              % (game_id, game["sequence"], len(game["expected"])))
    last = None
    if os.path.exists(RUNS_PATH):
        for line in open(RUNS_PATH, encoding="utf-8"):
            if line.strip():
                last = json.loads(line)
    print("  last replay: %s" % (json.dumps(
        {"t": last["t"], "verdicts": last["verdicts"]}, sort_keys=True)
        if last else "never"))
    state = freeze_state()
    print("  campaigns: %s" % ("FROZEN by %s since %s"
                               % (state.get("incident"), state.get("since"))
                               if state.get("frozen") else "not frozen"))
    return 0


def _cmd_check_freeze(args) -> int:
    try:
        assert_campaigns_unfrozen()
    except CampaignFrozen as exc:
        print("  %s" % exc)
        return 1
    print("  campaigns are not frozen")
    return 0


def _cmd_rebaseline(args) -> int:
    rebaseline(args.games or sorted(load_spec()["games"]), args.reason)
    print("  re-baselined; superseded hashes kept under `rebaselines`")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="canary.py", description=__doc__.splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Development pile only; <=%d actions per game, <=%d per "
               "invocation." % (ACTIONS_PER_GAME, INVOCATION_CAP))
    sub = parser.add_subparsers(dest="command", required=True)

    seed = sub.add_parser("seed", help="build the spec offline from precheck.json")
    seed.add_argument("--length", action="append", metavar="GAME=N")
    seed.add_argument("--force", action="store_true")
    seed.set_defaults(func=_cmd_seed)

    rep = sub.add_parser("replay", help="run the canary and compare (SPENDS ACTIONS)")
    rep.add_argument("games", nargs="*")
    rep.add_argument("--confirm-baseline", action="store_true",
                     help="record a PASS as a confirmation in canary.json")
    rep.add_argument("--note", default="",
                     help="free text stored with the run; use it to say why "
                          "this replay was made (e.g. 'before the INC-007 fix')")
    rep.set_defaults(func=_cmd_replay)

    sub.add_parser("status", help="offline: spec, last replay, freeze state"
                   ).set_defaults(func=_cmd_status)
    sub.add_parser("check-freeze", help="exit 1 if campaigns are frozen"
                   ).set_defaults(func=_cmd_check_freeze)

    reb = sub.add_parser("rebaseline",
                         help="deliberately replace expectations (SPENDS ACTIONS)")
    reb.add_argument("games", nargs="*")
    reb.add_argument("--reason", required=True)
    reb.set_defaults(func=_cmd_rebaseline)
    return parser


def main(argv: List[str]) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except SealedGameError as exc:
        print("  REFUSED: %s" % exc)
        return 2
    except BudgetExceeded as exc:
        print("  BUDGET: %s" % exc)
        return 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
