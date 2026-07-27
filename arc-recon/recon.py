"""接入核查 -- read-only survey of the ARC API, per Theoria.md Phase 1.

Answers only the questions that can be answered *without playing*, because a
game that has been played is burned for the sealed pile and the pile cut has not
been made yet. Concretely this run:

  * enumerates the public set (how many games, their version-suffixed ids, tags,
    baseline action counts);
  * verifies the scorecard lifecycle (open -> card_id -> retrieve -> close);
  * writes every request and response to the append-only ledger.

Deliberately NOT done here -- each of these burns action quota and touches a
game's mechanics, so each waits for the pile cut:

  * RESET semantics and cross-session residue;
  * whether one action returns one frame or several (the cascade-semantics
    question that decides the shape of `step`);
  * whether `level` is a response field or must be inferred from score jumps;
  * the determinism precheck (replay a fixed action sequence twice, compare
    frame hashes).
"""

import json
import os
import sys
from collections import Counter
from typing import Any, Dict, List

from client import DATA_DIR, ArcClient, load_api_key, mask

GAMES_PATH = os.path.join(DATA_DIR, "games.json")
FINDINGS_PATH = os.path.join(DATA_DIR, "recon_findings.json")


def survey_games(client: ArcClient) -> List[Dict[str, Any]]:
    games = client.list_games()
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(GAMES_PATH, "w", encoding="utf-8", newline="") as fh:
        json.dump(games, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return games


def describe_games(games: List[Dict[str, Any]]) -> Dict[str, Any]:
    tags = Counter(tag for game in games for tag in game.get("tags", []))
    untagged = [g["game_id"] for g in games if not g.get("tags")]
    suffixed = [g for g in games if "-" in g.get("game_id", "")]
    baselines = {
        g["game_id"]: g.get("baseline_actions") for g in games if g.get("baseline_actions")
    }
    level_counts = {gid: len(actions) for gid, actions in baselines.items()}
    return {
        "n_games": len(games),
        "fields_present": sorted({k for g in games for k in g}),
        "tag_histogram": dict(sorted(tags.items())),
        "untagged_games": sorted(untagged),
        "all_ids_version_suffixed": len(suffixed) == len(games),
        "levels_per_game": dict(sorted(level_counts.items())),
        "total_baseline_actions": sum(sum(a) for a in baselines.values()),
    }


def probe_scorecard(client: ArcClient) -> Dict[str, Any]:
    """Open, retrieve and close one scorecard. No game is played, no quota burnt.

    Each step is isolated: a failure in one is itself a finding about the API's
    semantics and must not hide the others.
    """
    out: Dict[str, Any] = {}
    opened = client.open_scorecard(
        tags=["recon", "read-only"],
        opaque={"purpose": "Phase 1 access check, no gameplay"},
    )
    card_id = opened.get("card_id") if isinstance(opened, dict) else None
    out["open_response_fields"] = sorted(opened) if isinstance(opened, dict) else None
    out["card_id_returned"] = bool(card_id)

    for label, call in (
        ("retrieve", lambda: client.get_scorecard(card_id)),
        ("close", lambda: client.close_scorecard(card_id)),
    ):
        if not card_id:
            out["%s_result" % label] = "skipped: no card_id"
            continue
        try:
            response = call()
            out["%s_response_fields" % label] = (
                sorted(response) if isinstance(response, dict) else None
            )
            out["%s_result" % label] = "ok"
        except Exception as exc:
            out["%s_result" % label] = "%s: %s" % (type(exc).__name__, exc)
    return out


def main() -> int:
    key = load_api_key()
    print("ARC-AGI-3 access check")
    print("  credential: %s (from gitignored .env, never logged)" % mask(key))

    client = ArcClient(api_key=key)
    games = survey_games(client)
    summary = describe_games(games)

    print("  games available: %d" % summary["n_games"])
    print("  per-game fields: %s" % ", ".join(summary["fields_present"]))
    print("  tags: %s; untagged: %d" % (summary["tag_histogram"], len(summary["untagged_games"])))
    print("  every id carries a version suffix: %s" % summary["all_ids_version_suffixed"])
    print("  total baseline actions across the public set: %d"
          % summary["total_baseline_actions"])

    try:
        scorecard = probe_scorecard(client)
        print("  scorecard lifecycle: open->%s retrieve->%s close->%s"
              % (
                  "card_id" if scorecard["card_id_returned"] else "NO card_id",
                  "ok" if scorecard["retrieve_response_fields"] else "n/a",
                  "ok" if scorecard["close_response_fields"] else "n/a",
              ))
    except Exception as exc:                     # recorded in the ledger regardless
        scorecard = {"error": "%s: %s" % (type(exc).__name__, exc)}
        print("  scorecard lifecycle: FAILED (%s)" % exc)

    findings = {
        "base_url": client.base_url,
        "auth_header": "X-API-Key",
        "api_calls_made": client.calls,
        "games": summary,
        "scorecard": scorecard,
        "not_yet_checked": [
            "RESET semantics and cross-session residue",
            "single action -> one frame or many (cascade semantics)",
            "level as a response field vs inferred from score jumps",
            "rate limits and action quota",
            "determinism precheck (fixed sequence replayed twice, frame hashes equal)",
        ],
        "blocked_on": "the pile cut -- everything above touches a game's mechanics, "
                      "and a touched game is burnt for the sealed pile",
    }
    with open(FINDINGS_PATH, "w", encoding="utf-8", newline="") as fh:
        json.dump(findings, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print("  findings -> %s" % FINDINGS_PATH)
    return 0


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.exit(main())
