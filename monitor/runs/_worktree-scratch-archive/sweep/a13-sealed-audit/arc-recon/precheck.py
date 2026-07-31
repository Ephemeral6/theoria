"""确定性预检 -- replay a fixed action sequence twice and compare frame hashes.

Theoria.md Phase 1: "每局固定动作序列跨会话重放两遍,帧哈希须逐一相等——过不了的
关登记并排除(环境不确定,整套推理不成立)". A non-deterministic environment does not
merely make the work harder; it makes the entire framework's reasoning invalid, so
this runs before anything is built on top of a game.

The same two runs also settle three other access-check items for free:

  * **cascade semantics** -- does any single action return more than one frame?
  * **cross-session residue** -- do two fresh RESETs start from the same state?
  * **level reporting** -- are `levels_completed` / `win_levels` maintained?

RETRY STRATEGY (supersedes the assumptions behind INC-002). The API's
`400 "game <id> not found"` is a *transient* fault, not an entitlement boundary:
the baseline-arms track showed the identical request succeeds on retry
(probe_log.jsonl: storm [400x7, 200]; pilots drove 13-15 successful actions on
every development-pile game). Policy here:

  * Every command sends the FULL id, always. The version suffix is the
    environment version fingerprint, and -- decisively -- SHORT-ID 200s ARE
    COUNTERFEIT: every short-id ACTION that returned 200 in the 2026-07-27
    g50t runs carried the pristine initial frame (hash 801726dc499f3f52,
    n_frames=1, levels_completed=0, 6 of 6 in recon_ledger.jsonl), regardless
    of the session's actual progress. A short-id 200 is served from something
    that is not the live session, so treating it as an executed action
    corrupts the trajectory. Short ids are banned from requests; the
    short<->full mapping is still recorded in the report because operators
    and other tracks use the short form as a handle.
  * Only `400 ... not found` (and transport failures / 429) are retried.
    Any other error is treated as permanent for that step: ACTION6 on
    tn36-ef4dde99 returns 500 on every attempt (88/88 in baseline-arms'
    probe log), and burning the retry budget on a deterministic error would
    just be a slower way of failing.

ACTION BUDGET: <=20 executed ACTIONs per game (RESETs are commands, not
actions, and are logged but not counted), spent as
2 runs x SEQUENCE_LENGTH actions = 16 for the standard length-8 sequence.
Failed attempts do not advance the game state; the ~5x HTTP amplification the
retries cost is recorded per step. A hard guard stops the run before action 21
regardless.

SAFETY: `assert_playable` refuses any game outside the development pile. A
successful RESET returns the first frame, so running this on a sealed game would
burn it. Short ids are additionally checked against sealed-pile prefixes. The
guard is in the code path, not in the operator's memory.
"""

import hashlib
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from client import DATA_DIR, ArcClient   # noqa: E402

PILES_PATH = os.path.join(DATA_DIR, "piles.json")
REPORT_PATH = os.path.join(DATA_DIR, "precheck.json")

# Fixed, published sequence. Deliberately boring and deterministic: the point is
# reproducibility, not progress through the game. Length 8 is set by the budget:
# two replays of (RESET + 8 actions) = 18 executed commands, under the 20 cap.
SEQUENCE_LENGTH = 8
BUDGET_PER_GAME = 20

# Retry envelope. Per-attempt success ran ~20-30% in baseline-arms' data, but
# unavailability arrives in WAVES: ar25's run-a died when 24 attempts (~60s)
# all landed inside one ~90s outage, and the very same action succeeded on
# attempt 2 a minute later. The envelope therefore has to outlast a wave, not
# just beat the per-attempt odds: 40 attempts with the backoff capped at 5s
# rides out ~3 minutes.
RESET_ATTEMPTS = 40
ACTION_ATTEMPTS = 40
# The backoff schedule itself, named rather than written at the call sites. It
# used to be four magic numbers repeated in two modules, which was harmless
# while nothing read them -- but `rate_budget.py` computes this track's request
# rate *from* the schedule, and a rate budget derived from a stale copy of the
# envelope is worse than none. Delay before attempt k+1 is
# `min(base * (k + 1), cap)` seconds.
RESET_DELAY_BASE = 0.5
RESET_DELAY_CAP = 5.0
ACTION_DELAY_BASE = 0.4
ACTION_DELAY_CAP = 5.0
# After this many consecutive failures, drop the ALB routing cookies so the
# next attempt is a fresh replica draw. See send_command's REDRAW note.
REDRAW_EVERY = 5


class SealedGameError(Exception):
    """Refused: this game is not in the development pile."""


class BudgetExceeded(Exception):
    """The 20-executed-commands-per-game cap would be crossed."""


def _piles() -> Dict[str, Any]:
    with open(PILES_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def dev_pile() -> List[str]:
    return _piles()["dev_pile"]


def assert_playable(game_id: str) -> None:
    piles = _piles()
    if game_id not in piles["dev_pile"]:
        raise SealedGameError(
            "%s is not in the development pile. A successful RESET returns the "
            "first frame, so running this would burn a sealed game." % game_id
        )
    # Defence in depth: the short form must not collide with a sealed game.
    # A13 converged the stem rule onto `sealed.py` -- this used to be the third
    # of three implementations of "is this id sealed", and they had drifted.
    import sealed as sealed_mod
    short = sealed_mod.stem(game_id)
    for sealed_id in piles["sealed_pile"]:
        if sealed_mod.stem(sealed_id) == short:
            raise SealedGameError(
                "short id %s collides with sealed game %s" % (short, sealed_id)
            )


def fixed_sequence(available: List[int], length: int = SEQUENCE_LENGTH) -> List[int]:
    """Cycle the available simple actions -- same list every run, by construction.

    Fallback: tn36-ef4dde99 advertises available_actions=[6] only, but ACTION6
    fails 500 on every attempt server-side while ACTION1..5 are accepted
    (baseline-arms probe log). The precheck needs *any* accepted deterministic
    actions, not the game's nominal action space, so with no simple action
    advertised it falls back to [1,2,3,4] and records that in the report.
    """
    simple = [a for a in sorted(available) if a in (1, 2, 3, 4, 5)]
    if not simple:
        simple = [1, 2, 3, 4]
    return [simple[i % len(simple)] for i in range(length)]


def hash_frames(frames: Any) -> str:
    canonical = json.dumps(frames, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def _retryable(status: int, body: Any) -> bool:
    """Only the known-transient failures are worth another attempt."""
    if status < 0 or status == 429:
        return True
    if status == 400:
        message = body.get("message", "") if isinstance(body, dict) else str(body)
        return "not found" in message
    return False


def send_command(client: ArcClient, path: str, body: Dict[str, Any],
                 note: str, attempts: int,
                 delay_base: float = 0.4, delay_cap: float = 3.0
                 ) -> Tuple[int, Any, Dict[str, Any]]:
    """One command with the retry policy. Returns (status, body, stats).

    Full id only. Short-id 200s are counterfeit (see module docstring), so the
    request body never varies across attempts: same body, same session, until
    a live replica answers or the envelope is exhausted.

    REDRAW (INC-007a). This envelope was designed against a transport that was
    re-routed on every attempt -- 40 identical retries worked precisely because
    each was a fresh draw at a replica that might hold the session. The cookie
    jar removes that: once pinned, all 40 attempts go to the same replica, so if
    THAT replica is the broken one, retrying is only waiting. Every
    `REDRAW_EVERY` failures the routing cookies are dropped (the session cookie
    is kept) to force a new draw. In practice this almost never fires -- the
    measured amplification after the fix is 1.00 attempt per command -- but the
    envelope must not have become weaker than the thing it replaced.
    """
    status, parsed = -1, None
    for k in range(attempts):
        try:
            status, parsed = client.request(
                "POST", path, body=body, note="%s attempt %d" % (note, k))
        except Exception as exc:                     # ArcApiError or transport
            status = getattr(exc, "status", -1)
            raw = getattr(exc, "body", str(exc))
            try:
                parsed = json.loads(raw)
            except (TypeError, ValueError):
                parsed = raw
            if _retryable(status, parsed) and k < attempts - 1:
                if (k + 1) % REDRAW_EVERY == 0:
                    redraw = getattr(client, "clear_routing_cookies", None)
                    if callable(redraw):
                        redraw()
                time.sleep(min(delay_base * (k + 1), delay_cap))
                continue
            return status, parsed, {"attempts": k + 1}
        return status, parsed, {"attempts": k + 1}
    return status, parsed, {"attempts": attempts}


def play_once(client: ArcClient, game_id: str, card_id: str,
              sequence: Optional[List[int]] = None,
              label: str = "",
              length: int = SEQUENCE_LENGTH,
              actions_already_spent: int = 0) -> Dict[str, Any]:
    """RESET, then walk the fixed sequence, hashing every frame batch."""
    assert_playable(game_id)
    actions_executed = 0     # successful ACTIONs only; the hard budget guard

    def spend() -> None:
        nonlocal actions_executed
        actions_executed += 1
        if actions_already_spent + actions_executed > BUDGET_PER_GAME:
            raise BudgetExceeded("%s: executed action %d > %d"
                                 % (game_id,
                                    actions_already_spent + actions_executed,
                                    BUDGET_PER_GAME))

    status, opening, reset_stats = send_command(
        client, "/api/cmd/RESET", {"game_id": game_id, "card_id": card_id},
        note="precheck RESET %s %s" % (game_id, label),
        attempts=RESET_ATTEMPTS,
        delay_base=RESET_DELAY_BASE, delay_cap=RESET_DELAY_CAP)
    if status != 200 or not isinstance(opening, dict):
        return {"reset_failed": True, "reset_status": status,
                "reset_attempts": reset_stats["attempts"],
                "reset_error": str(opening)[:200], "steps": [],
                "sequence": sequence or [], "actions_executed": 0,
                "http_calls": reset_stats["attempts"],
                "win_levels": None, "available_actions": None}
    guid = opening["guid"]
    http_calls = reset_stats["attempts"]
    steps = [
        {
            "action": "RESET",
            "hash": hash_frames(opening["frame"]),
            "n_frames": len(opening["frame"]),
            "state": opening.get("state"),
            "levels_completed": opening.get("levels_completed"),
            "attempts": reset_stats["attempts"],
        }
    ]
    sequence = sequence or fixed_sequence(opening.get("available_actions") or [],
                                          length)

    for index, action in enumerate(sequence):
        status, response, stats = send_command(
            client, "/api/cmd/ACTION%d" % action,
            {"game_id": game_id, "card_id": card_id, "guid": guid},
            note="precheck ACTION%d #%d %s %s" % (action, index, game_id, label),
            attempts=ACTION_ATTEMPTS,
            delay_base=ACTION_DELAY_BASE, delay_cap=ACTION_DELAY_CAP)
        http_calls += stats["attempts"]
        if status != 200 or not isinstance(response, dict):
            steps.append({"action": "ACTION%d" % action,
                          "error": "HTTP %s after %d attempts: %s"
                                   % (status, stats["attempts"], str(response)[:160])})
            break
        spend()
        frames = response.get("frame", [])
        steps.append(
            {
                "action": "ACTION%d" % action,
                "hash": hash_frames(frames),
                "n_frames": len(frames) if isinstance(frames, list) else None,
                "state": response.get("state"),
                "levels_completed": response.get("levels_completed"),
                "attempts": stats["attempts"],
            }
        )
    return {"guid": guid, "sequence": sequence, "steps": steps,
            "actions_executed": actions_executed, "http_calls": http_calls,
            "win_levels": opening.get("win_levels"),
            "available_actions": opening.get("available_actions")}


def compare(first: Dict[str, Any], second: Dict[str, Any],
            expected_steps: Optional[int] = None) -> Dict[str, Any]:
    """Compare two replays.

    A step that errored carries no hash. Comparing two such steps would find
    `None == None` and call it agreement, which is how the first version of this
    function reported PASS for two runs that had both died on their first action
    (INC-003). Hashes are therefore only counted as agreeing when both are
    present, and the verdict additionally requires that the full sequence ran.

    Verdicts: PASS (complete, all hashes equal), FAIL (a real hash mismatch --
    the environment is non-deterministic), UNPLAYABLE (the sequence could not
    be completed even with the retry policy, so determinism is unestablished
    and the game cannot host a campaign either way).
    """
    a, b = first.get("steps", []), second.get("steps", [])
    compared = min(len(a), len(b))
    mismatches = []
    unusable = []
    for i in range(compared):
        hash_a, hash_b = a[i].get("hash"), b[i].get("hash")
        if hash_a is None or hash_b is None:
            unusable.append({"index": i, "action": a[i].get("action"),
                             "error_a": a[i].get("error"), "error_b": b[i].get("error")})
        elif hash_a != hash_b:
            mismatches.append({"index": i, "action": a[i]["action"],
                               "hash_a": hash_a, "hash_b": hash_b})
    expected = expected_steps if expected_steps is not None else compared
    complete = len(a) == len(b) == expected and not unusable
    multi = [s for s in a if (s.get("n_frames") or 0) > 1]
    return {
        "steps_compared": compared,
        "steps_with_a_usable_hash": compared - len(unusable),
        "steps_expected": expected,
        "complete": complete,
        "unusable_steps": unusable[:10],
        "length_match": len(a) == len(b),
        # PASS requires the whole sequence to have run and every compared step to
        # carry a real hash on both sides. Anything less is not PASS.
        "deterministic": complete and not mismatches,
        "verdict": (
            "PASS" if (complete and not mismatches)
            else ("FAIL" if mismatches else "UNPLAYABLE")
        ),
        "mismatches": mismatches[:10],
        "first_divergence": mismatches[0]["index"] if mismatches else None,
        "cross_session_residue": (a[0].get("hash") != b[0].get("hash"))
                                 if (a and b) else None,
        "max_frames_per_action": max(((s.get("n_frames") or 0) for s in a), default=0),
        "actions_returning_multiple_frames": len(multi),
        "cascade_semantics": (
            "action -> frame SEQUENCE (observed >1 frame in one response)"
            if multi else
            "every response carried exactly 1 frame; the field is still a list"
        ),
    }


def run(game_id: str, client: Optional[ArcClient] = None,
        length: int = SEQUENCE_LENGTH,
        actions_already_spent: int = 0) -> Dict[str, Any]:
    """`actions_already_spent` charges prior spend on this game against the
    budget (g50t's 16 actions from the invalidated 2026-07-27 runs are charged
    this way; its re-check uses length=2, 16 + 2x2 = 20)."""
    assert_playable(game_id)
    client = client or ArcClient()
    # Budget, computed before it is spent: 2 runs x `length` actions.
    planned = actions_already_spent + 2 * length
    assert planned <= BUDGET_PER_GAME, "planned %d > %d" % (planned, BUDGET_PER_GAME)

    card_a = client.open_scorecard(tags=["precheck", "run-a"])["card_id"]
    first = play_once(client, game_id, card_a, label="run-a", length=length,
                      actions_already_spent=actions_already_spent)
    if first.get("reset_failed"):
        second: Dict[str, Any] = {"steps": [], "skipped": "run-a RESET never opened"}
    else:
        card_b = client.open_scorecard(tags=["precheck", "run-b"])["card_id"]
        second = play_once(client, game_id, card_b,
                           sequence=first["sequence"], label="run-b",
                           actions_already_spent=(actions_already_spent
                                                  + first["actions_executed"]))
    verdict = compare(first, second,
                      expected_steps=len(first.get("sequence") or []) + 1)
    if first.get("reset_failed"):
        verdict["verdict"] = "UNPLAYABLE"
        verdict["reason"] = ("RESET never succeeded in %d attempts (last HTTP %s)"
                             % (first["reset_attempts"], first["reset_status"]))
    return {
        "game_id": game_id,
        "id_map": {game_id.split("-")[0]: game_id},
        "sequence": first.get("sequence"),
        "win_levels": first.get("win_levels"),
        "available_actions": first.get("available_actions"),
        "actions_executed": (first.get("actions_executed", 0)
                             + second.get("actions_executed", 0)),
        "actions_already_spent": actions_already_spent,
        "budget_per_game": BUDGET_PER_GAME,
        "http_calls": (first.get("http_calls", 0) + second.get("http_calls", 0)),
        "verdict": verdict,
        "run_a": first.get("steps"),
        "run_b": second.get("steps"),
    }


# ASCII only: this is the smoke gate, and a GBK console turns a CJK print into a
# UnicodeEncodeError on some machines (cold-start-a2 D-A2-007, same root cause).
USAGE = """precheck.py -- determinism precheck: replay a fixed action sequence
twice and compare frame hashes. SPENDS ACTIONS. Development pile only.

    python precheck.py                       every development-pile game
    python precheck.py <game_id>             one game
    python precheck.py <game_id>:<length>    shorten the sequence
    python precheck.py <game_id>:<length>:<already_spent>

Targets are `game_id[:length[:actions_already_spent]]`; `already_spent` charges
prior spend on that game against its %d-action cap. The report is merged per
game into data/precheck.json, so a partial rerun does not clobber other games.

Anything that is not a development-pile game is REFUSED (exit 2) -- a
successful RESET returns the first frame, so a precheck pointed at a sealed
game would burn it.

Related: `canary.py` (cheap periodic drift check built from this report),
`contamination.py` (the register and the sealed claim set).
""" % BUDGET_PER_GAME


def main(argv: List[str]) -> int:
    """Targets are `game_id[:length[:actions_already_spent]]`. The report is
    merged per game into any existing precheck.json, so partial reruns do not
    clobber other games' results."""
    if argv and argv[0] in ("-h", "--help", "help"):
        print(USAGE)
        return 0
    tokens = argv or dev_pile()
    client = ArcClient()
    results: Dict[str, Any] = {}
    if os.path.exists(REPORT_PATH):
        with open(REPORT_PATH, encoding="utf-8") as fh:
            results = json.load(fh).get("results", {})
    for token in tokens:
        parts = token.split(":")
        game_id = parts[0]
        length = int(parts[1]) if len(parts) > 1 else SEQUENCE_LENGTH
        spent = int(parts[2]) if len(parts) > 2 else 0
        try:
            result = run(game_id, client=client, length=length,
                         actions_already_spent=spent)
        except SealedGameError as exc:
            print("  %-18s REFUSED: %s" % (game_id, exc))
            return 2
        except BudgetExceeded as exc:
            print("  %-18s BUDGET: %s" % (game_id, exc))
            return 3
        verdict = result["verdict"]
        results[game_id] = result
        print("  %-18s %s  steps=%d/%d usable=%d  actions=%d+%d/%d http=%d  "
              "max_frames/action=%d  residue=%s"
              % (game_id, verdict["verdict"], verdict["steps_compared"],
                 verdict["steps_expected"], verdict["steps_with_a_usable_hash"],
                 result["actions_already_spent"], result["actions_executed"],
                 BUDGET_PER_GAME, result["http_calls"],
                 verdict["max_frames_per_action"],
                 verdict["cross_session_residue"]))

    excluded = []
    for game_id, result in sorted(results.items()):
        verdict = result["verdict"]
        if verdict["verdict"] == "FAIL":
            excluded.append({"game_id": game_id,
                             "reason": "non-deterministic at step %s"
                                       % verdict["first_divergence"]})
        elif verdict["verdict"] == "UNPLAYABLE":
            excluded.append({"game_id": game_id,
                             "reason": verdict.get("reason",
                                       "sequence could not be completed; "
                                       "determinism unestablished")})

    report = {"results": results, "excluded": excluded,
              "id_map": {g.split("-")[0]: g for g in sorted(results)},
              "retry_policy": {
                  "id_form": "full id only; short-id 200s are counterfeit "
                             "(pristine initial frame regardless of session "
                             "state) and are banned from requests",
                  "reset": "up to %d attempts" % RESET_ATTEMPTS,
                  "action": "up to %d attempts" % ACTION_ATTEMPTS,
                  "retryable": "400 'not found' / 429 / transport only",
              },
              "note": "games in `excluded` are registered and must not be used: a "
                      "non-deterministic environment invalidates the framework's reasoning"}
    with open(REPORT_PATH, "w", encoding="utf-8", newline="") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print("  report -> %s" % REPORT_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
