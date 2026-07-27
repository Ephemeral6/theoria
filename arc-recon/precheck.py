"""确定性预检 -- replay a fixed action sequence twice and compare frame hashes.

Theoria.md Phase 1: "每局固定动作序列跨会话重放两遍,帧哈希须逐一相等——过不了的
关登记并排除(环境不确定,整套推理不成立)". A non-deterministic environment does not
merely make the work harder; it makes the entire framework's reasoning invalid, so
this runs before anything is built on top of a game.

The same two runs also settle three other access-check items for free:

  * **cascade semantics** -- does any single action return more than one frame?
  * **cross-session residue** -- do two fresh RESETs start from the same state?
  * **level reporting** -- are `levels_completed` / `win_levels` maintained?

SAFETY: `assert_playable` refuses any game outside the development pile. A
successful RESET returns the first frame, so running this on a sealed game would
burn it. The guard is in the code path, not in the operator's memory.
"""

import hashlib
import json
import os
import sys
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from client import DATA_DIR, ArcApiError, ArcClient   # noqa: E402

PILES_PATH = os.path.join(DATA_DIR, "piles.json")
REPORT_PATH = os.path.join(DATA_DIR, "precheck.json")

# Fixed, published sequence. Deliberately boring and deterministic: the point is
# reproducibility, not progress through the game.
SEQUENCE_LENGTH = 20


class SealedGameError(Exception):
    """Refused: this game is not in the development pile."""


def dev_pile() -> List[str]:
    with open(PILES_PATH, encoding="utf-8") as fh:
        return json.load(fh)["dev_pile"]


def assert_playable(game_id: str) -> None:
    if game_id not in dev_pile():
        raise SealedGameError(
            "%s is not in the development pile. A successful RESET returns the "
            "first frame, so running this would burn a sealed game." % game_id
        )


def fixed_sequence(available: List[int], length: int = SEQUENCE_LENGTH) -> List[int]:
    """Cycle the available simple actions -- same list every run, by construction."""
    simple = [a for a in sorted(available) if a in (1, 2, 3, 4, 5)]
    if not simple:
        raise RuntimeError("no simple actions available: %r" % available)
    return [simple[i % len(simple)] for i in range(length)]


def hash_frames(frames: Any) -> str:
    canonical = json.dumps(frames, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def play_once(client: ArcClient, game_id: str, card_id: str,
              sequence: Optional[List[int]] = None) -> Dict[str, Any]:
    """RESET, then walk the fixed sequence, hashing every frame batch."""
    assert_playable(game_id)
    _, opening = client.request(
        "POST", "/api/cmd/RESET", body={"game_id": game_id, "card_id": card_id},
        note="precheck RESET %s" % game_id,
    )
    guid = opening["guid"]
    steps = [
        {
            "action": "RESET",
            "hash": hash_frames(opening["frame"]),
            "n_frames": len(opening["frame"]),
            "state": opening.get("state"),
            "levels_completed": opening.get("levels_completed"),
            "score": opening.get("score"),
        }
    ]
    sequence = sequence or fixed_sequence(opening.get("available_actions", [1, 2, 3, 4, 5]))

    for index, action in enumerate(sequence):
        try:
            _, response = client.request(
                "POST", "/api/cmd/ACTION%d" % action,
                body={"game_id": game_id, "card_id": card_id, "guid": guid},
                note="precheck ACTION%d #%d %s" % (action, index, game_id),
            )
        except ArcApiError as exc:
            steps.append({"action": "ACTION%d" % action, "error": str(exc)[:200]})
            break
        frames = response.get("frame", [])
        steps.append(
            {
                "action": "ACTION%d" % action,
                "hash": hash_frames(frames),
                "n_frames": len(frames) if isinstance(frames, list) else None,
                "state": response.get("state"),
                "levels_completed": response.get("levels_completed"),
                "score": response.get("score"),
            }
        )
    return {"guid": guid, "sequence": sequence, "steps": steps,
            "win_levels": opening.get("win_levels"),
            "available_actions": opening.get("available_actions")}


def compare(first: Dict[str, Any], second: Dict[str, Any]) -> Dict[str, Any]:
    a, b = first["steps"], second["steps"]
    mismatches = [
        {"index": i, "action": a[i]["action"],
         "hash_a": a[i].get("hash"), "hash_b": b[i].get("hash")}
        for i in range(min(len(a), len(b)))
        if a[i].get("hash") != b[i].get("hash")
    ]
    multi = [s for s in a if (s.get("n_frames") or 0) > 1]
    return {
        "steps_compared": min(len(a), len(b)),
        "length_match": len(a) == len(b),
        "deterministic": not mismatches and len(a) == len(b),
        "mismatches": mismatches[:10],
        "first_divergence": mismatches[0]["index"] if mismatches else None,
        "cross_session_residue": a[0].get("hash") != b[0].get("hash"),
        "max_frames_per_action": max((s.get("n_frames") or 0) for s in a),
        "actions_returning_multiple_frames": len(multi),
        "cascade_semantics": (
            "action -> frame SEQUENCE (observed >1 frame in one response)"
            if multi else
            "every response carried exactly 1 frame; the field is still a list"
        ),
    }


def run(game_id: str, client: Optional[ArcClient] = None) -> Dict[str, Any]:
    assert_playable(game_id)
    client = client or ArcClient()
    card_a = client.open_scorecard(tags=["precheck", "run-a"])["card_id"]
    first = play_once(client, game_id, card_a)
    card_b = client.open_scorecard(tags=["precheck", "run-b"])["card_id"]
    second = play_once(client, game_id, card_b, sequence=first["sequence"])
    verdict = compare(first, second)
    return {
        "game_id": game_id,
        "sequence": first["sequence"],
        "win_levels": first["win_levels"],
        "available_actions": first["available_actions"],
        "verdict": verdict,
        "run_a": first["steps"],
        "run_b": second["steps"],
    }


def main(argv: List[str]) -> int:
    targets = argv or dev_pile()
    client = ArcClient()
    results, excluded = {}, []
    for game_id in targets:
        try:
            result = run(game_id, client=client)
        except SealedGameError as exc:
            print("  %-18s REFUSED: %s" % (game_id, exc))
            return 2
        except ArcApiError as exc:
            print("  %-18s unplayable: HTTP %s" % (game_id, exc.status))
            excluded.append({"game_id": game_id, "reason": "HTTP %s" % exc.status})
            continue
        verdict = result["verdict"]
        results[game_id] = result
        print("  %-18s determinism=%s  steps=%d  max_frames/action=%d  residue=%s"
              % (game_id, "PASS" if verdict["deterministic"] else "FAIL",
                 verdict["steps_compared"], verdict["max_frames_per_action"],
                 verdict["cross_session_residue"]))
        if not verdict["deterministic"]:
            excluded.append({"game_id": game_id,
                             "reason": "non-deterministic at step %s"
                                       % verdict["first_divergence"]})

    report = {"results": results, "excluded": excluded,
              "note": "games in `excluded` are registered and must not be used: a "
                      "non-deterministic environment invalidates the framework's reasoning"}
    with open(REPORT_PATH, "w", encoding="utf-8", newline="") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print("  report -> %s" % REPORT_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
