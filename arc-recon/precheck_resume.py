"""Resume interrupted precheck runs from the ledger.

The ledger is complete by construction, so an interrupted precheck loses
nothing: every executed step's frame is in `data/recon_ledger.jsonl`, and a
step that died mid-retry never advanced the game state, which means the live
session (guid) can legitimately continue from exactly where it stopped -- the
replayed sequence stays intact, only the wall-clock gap grows (and a hash
mismatch caused by that gap would itself be a determinism finding).

This exists because the 2026-07-27 four-game run was killed by a 10-minute
harness timeout mid sk48 run-b. Everything it does is reconstructable from
ledger notes of the form `precheck ACTION<k> #<i> <game> <run> attempt <n>`.

    python precheck_resume.py reconstruct          # show runs, spend, no API calls
    python precheck_resume.py resume <game> <run-a|run-b> <card_id> <guid> A,A,A [#start]
    python precheck_resume.py score <game>         # compare + merge into precheck.json
"""

import hashlib
import json
import os
import re
import sys
from typing import Any, Dict, List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import precheck                                     # noqa: E402
from client import DATA_DIR, ArcClient              # noqa: E402

LEDGER_PATH = os.path.join(DATA_DIR, "recon_ledger.jsonl")
NOTE_RE = re.compile(
    r"precheck (RESET|ACTION(\d+))(?: #(\d+))? (\S+) (run-[ab]) attempt (\d+)$")


def reconstruct() -> Dict[Tuple[str, str], Dict[str, Any]]:
    """Rebuild every precheck run (steps, card, guid, spend) from the ledger."""
    runs: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for line in open(LEDGER_PATH, encoding="utf-8"):
        entry = json.loads(line)
        match = NOTE_RE.match(entry.get("note", ""))
        if not match or entry.get("status") != 200:
            continue
        cmd, _, index, game, label, _ = match.groups()
        response = entry.get("response_body") or {}
        key = (game, label)
        run = runs.setdefault(key, {"steps": [], "card_id": None, "guid": None})
        frames = response.get("frame")
        run["steps"].append({
            "action": cmd,
            "index": int(index) if index is not None else -1,
            "hash": precheck.hash_frames(frames),
            "n_frames": len(frames) if isinstance(frames, list) else None,
            "state": response.get("state"),
            "levels_completed": response.get("levels_completed"),
            "t": entry.get("t"),
        })
        if cmd == "RESET":
            run["guid"] = response.get("guid")
            run["card_id"] = (entry.get("request_body") or {}).get("card_id")
    return runs


def spent_actions(runs, game: str) -> int:
    return sum(1 for (g, _), run in runs.items() if g == game
               for s in run["steps"] if s["action"] != "RESET")


def resume(game: str, label: str, card_id: str, guid: str,
           actions: List[int], start_index: int) -> None:
    """Continue a live session from sequence position `start_index`."""
    precheck.assert_playable(game)
    runs = reconstruct()
    already = spent_actions(runs, game)
    planned = already + len(actions)
    assert planned <= precheck.BUDGET_PER_GAME, \
        "planned %d > %d" % (planned, precheck.BUDGET_PER_GAME)
    client = ArcClient()
    for offset, action in enumerate(actions):
        index = start_index + offset
        status, response, stats = precheck.send_command(
            client, "/api/cmd/ACTION%d" % action,
            {"game_id": game, "card_id": card_id, "guid": guid},
            note="precheck ACTION%d #%d %s %s" % (action, index, game, label),
            attempts=precheck.ACTION_ATTEMPTS, delay_cap=5.0)
        if status != 200 or not isinstance(response, dict):
            print("  ACTION%d #%d FAILED after %d attempts: HTTP %s"
                  % (action, index, stats["attempts"], status))
            return
        print("  ACTION%d #%d ok  hash=%s att=%d"
              % (action, index, precheck.hash_frames(response.get("frame")),
                 stats["attempts"]))


def steps_for_compare(run: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Ledger steps -> compare() shape. Keeps the LAST RESET, drops earlier
    ones (a re-RESET restarts the run; only g50t's invalidated runs had that,
    and those are excluded before this is called)."""
    last_reset = max(i for i, s in enumerate(run["steps"]) if s["action"] == "RESET")
    ordered = run["steps"][last_reset:]
    return [{k: v for k, v in s.items() if k != "index"} for s in ordered]


def score(game: str, sequence: List[int]) -> Dict[str, Any]:
    """Compare run-a vs run-b from the ledger and merge into precheck.json."""
    runs = reconstruct()
    first = {"steps": steps_for_compare(runs[(game, "run-a")]),
             "sequence": sequence}
    second = {"steps": steps_for_compare(runs[(game, "run-b")])}
    verdict = precheck.compare(first, second, expected_steps=len(sequence) + 1)
    result = {
        "game_id": game,
        "id_map": {game.split("-")[0]: game},
        "sequence": sequence,
        "actions_executed": spent_actions(runs, game),
        "actions_already_spent": 0,
        "budget_per_game": precheck.BUDGET_PER_GAME,
        "resumed_from_ledger": True,
        "verdict": verdict,
        "run_a": first["steps"],
        "run_b": second["steps"],
    }
    report = {"results": {}}
    if os.path.exists(precheck.REPORT_PATH):
        with open(precheck.REPORT_PATH, encoding="utf-8") as fh:
            report = json.load(fh)
    report.setdefault("results", {})[game] = result
    with open(precheck.REPORT_PATH, "w", encoding="utf-8", newline="") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print("  %-18s %s  steps=%d/%d usable=%d" % (
        game, verdict["verdict"], verdict["steps_compared"],
        verdict["steps_expected"], verdict["steps_with_a_usable_hash"]))
    return result


def main(argv: List[str]) -> int:
    if not argv or argv[0] == "reconstruct":
        runs = reconstruct()
        for key in sorted(runs):
            run = runs[key]
            print(key, "card", (run["card_id"] or "")[:8],
                  "guid", (run["guid"] or "")[:8])
            for s in run["steps"]:
                print("   ", s["action"], "#", s["index"], s["hash"],
                      "att-logged", s["t"])
        for game in sorted({g for g, _ in runs}):
            print("spent(%s) = %d" % (game, spent_actions(runs, game)))
        return 0
    if argv[0] == "resume":
        game, label, card_id, guid = argv[1:5]
        actions = [int(a) for a in argv[5].split(",")]
        start = int(argv[6]) if len(argv) > 6 else 0
        resume(game, label, card_id, guid, actions, start)
        return 0
    if argv[0] == "score":
        game = argv[1]
        sequence = [int(a) for a in argv[2].split(",")]
        score(game, sequence)
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
