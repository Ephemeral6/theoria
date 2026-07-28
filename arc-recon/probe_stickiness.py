"""Is `400 game not found` a wave of outages, or our own missing cookie jar?

INC-001b diagnosed the API's intermittent `400 "game <id> not found"` as a
transient fault arriving in waves of 1-3 minutes, most likely a multi-instance
backend where only some replicas hold the game/session. The retry envelope built
on that diagnosis costs 2.5-10x HTTP calls per executed action, and that
amplification is the multiplier in every quota, cost and wall-clock extrapolation
on this project.

The official REST docs state the server sets `AWSALB`/`AWSALBCORS` cookies and
that they must be echoed on subsequent requests or game state and routing break.
`client.ArcClient` uses bare `urllib.request` with no cookie jar, so it echoes
nothing and every request is load-balanced afresh. That predicts the same
symptom as the wave hypothesis -- intermittent "not found" from a replica that
does not hold your session -- but a completely different cure, and a completely
different price.

The two hypotheses differ in a way one experiment separates:

  * **Wave** -- unavailability is a property of *time*. A cookie-carrying client
    and a cookie-less client, interleaved, fail together.
  * **Stickiness** -- unavailability is a property of *routing*. Interleaved, the
    cookie-carrying client succeeds while the cookie-less one still misses.

Interleaving matters: run one arm then the other and a wave passing between them
produces exactly the result the stickiness hypothesis predicts, which is how the
original misdiagnosis happened in the first place.

COST: zero actions. RESET is a command, not an action, and the scorecard counts
only successful ACTIONs (baseline-arms' four-sample measurement, PARTNER_SYNC
2026-07-28). Development pile only, via the same `assert_playable` guard.
"""

import argparse
import http.cookiejar
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from client import BASE_URL, DATA_DIR, load_api_key   # noqa: E402
from precheck import assert_playable                  # noqa: E402

REPORT_PATH = os.path.join(DATA_DIR, "stickiness_probe.json")
LEDGER_PATH = os.path.join(DATA_DIR, "recon_ledger.jsonl")


class Arm:
    """One HTTP client. `sticky=True` keeps a cookie jar across requests."""

    def __init__(self, name: str, key: str, sticky: bool):
        self.name = name
        self.sticky = sticky
        self._key = key
        self.jar = http.cookiejar.CookieJar()
        self.opener = (urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar))
            if sticky else urllib.request.build_opener())
        self.attempts = 0

    def post(self, path: str, body: Dict[str, Any], note: str) -> Dict[str, Any]:
        payload = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            BASE_URL + path, data=payload, method="POST",
            headers={"X-API-Key": self._key, "Accept": "application/json",
                     "Content-Type": "application/json"})
        started = time.time()
        try:
            with self.opener.open(request, timeout=30) as response:
                status, text = response.status, response.read().decode("utf-8")
                headers = dict(response.headers)
        except urllib.error.HTTPError as exc:
            status, text = exc.code, exc.read().decode("utf-8", "replace")
            headers = dict(exc.headers)
        except Exception as exc:                       # transport
            status, text, headers = -1, str(exc), {}
        self.attempts += 1
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = text
        record = {
            "t": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started)),
            "elapsed_ms": int((time.time() - started) * 1000),
            "note": "stickiness probe %s %s" % (self.name, note),
            "method": "POST", "url": BASE_URL + path,
            "request_headers": {"X-API-Key": "<redacted>",
                                "Accept": "application/json",
                                "Content-Type": "application/json"},
            "request_body": body, "status": status,
            "response_body": parsed,
            # The point of the probe: did the server hand us a routing cookie,
            # and did this arm send one back?
            "set_cookie": headers.get("Set-Cookie", ""),
            "cookies_held": sorted(c.name for c in self.jar),
        }
        with open(LEDGER_PATH, "a", encoding="utf-8", newline="") as fh:
            fh.write(json.dumps(record, sort_keys=True, ensure_ascii=True))
            fh.write("\n")
        return {"status": status, "body": parsed,
                "set_cookie": record["set_cookie"],
                "cookies_held": record["cookies_held"]}


def open_scorecard(arm: Arm) -> str:
    for _ in range(20):
        result = arm.post("/api/scorecard/open", {"tags": ["stickiness-probe"]},
                          "open scorecard")
        if result["status"] == 200 and isinstance(result["body"], dict):
            return result["body"]["card_id"]
        time.sleep(1.0)
    raise RuntimeError("could not open a scorecard for arm %s" % arm.name)


def run(game_id: str, rounds: int, key: str,
        control_game: str = None, sticky_game: str = None) -> Dict[str, Any]:
    """Interleaved A/B. Each round: one RESET on each arm, order alternating.

    Alternating the order within each round keeps a wave that starts mid-round
    from landing on the same arm every time.

    CONFOUND, and the reason for `--control-game`/`--sticky-game`. Run both arms
    against the SAME game and a second explanation fits the data just as well:
    INC-001a recorded that the API answers "a live session is already open on
    this game" with the identical `400 game <id> not found` message. The arm
    that resets first would then be starving the other, and the cookie jar would
    get credit for a race it merely won. Pointing the arms at two different
    development-pile games removes the interaction entirely; swapping which arm
    gets which game across two runs removes the game as an explanation too.
    """
    control_game = control_game or game_id
    sticky_game = sticky_game or game_id
    assert_playable(control_game)
    assert_playable(sticky_game)
    control = Arm("no-cookies", key, sticky=False)
    sticky = Arm("cookie-jar", key, sticky=True)
    games = {control.name: control_game, sticky.name: sticky_game}
    card_control = open_scorecard(control)
    card_sticky = open_scorecard(sticky)
    cards = {control.name: card_control, sticky.name: card_sticky}

    rows: List[Dict[str, Any]] = []
    for index in range(rounds):
        order = [control, sticky] if index % 2 == 0 else [sticky, control]
        for arm in order:
            target = games[arm.name]
            result = arm.post("/api/cmd/RESET",
                              {"game_id": target, "card_id": cards[arm.name]},
                              "RESET %s round %d" % (target, index))
            body = result["body"]
            message = body.get("message", "") if isinstance(body, dict) else ""
            rows.append({
                "round": index, "arm": arm.name, "status": result["status"],
                "not_found": result["status"] == 400 and "not found" in message,
                "got_set_cookie": bool(result["set_cookie"]),
                "cookies_held": result["cookies_held"],
            })
            print("    round %-2d %-11s HTTP %-4s set-cookie=%-5s held=%s"
                  % (index, arm.name, result["status"],
                     bool(result["set_cookie"]),
                     ",".join(result["cookies_held"]) or "-"))
            time.sleep(0.4)

    def score(name: str) -> Dict[str, Any]:
        mine = [r for r in rows if r["arm"] == name]
        ok = [r for r in mine if r["status"] == 200]
        return {"attempts": len(mine), "ok": len(ok),
                "success_rate": round(len(ok) / len(mine), 3) if mine else None,
                "not_found": sum(1 for r in mine if r["not_found"]),
                "ever_got_set_cookie": any(r["got_set_cookie"] for r in mine),
                "cookies_at_end": mine[-1]["cookies_held"] if mine else []}

    control_score, sticky_score = score(control.name), score(sticky.name)
    # Rounds where the two arms disagree are the discriminating evidence: a wave
    # is a property of time and should hit both arms in the same round.
    by_round: Dict[int, Dict[str, Any]] = {}
    for row in rows:
        by_round.setdefault(row["round"], {})[row["arm"]] = row["status"] == 200
    disagreements = [r for r, arms in by_round.items()
                     if len(arms) == 2 and len(set(arms.values())) == 2]
    sticky_won = [r for r in disagreements
                  if by_round[r]["cookie-jar"] and not by_round[r]["no-cookies"]]

    verdict = "INCONCLUSIVE"
    if not sticky_score["ever_got_set_cookie"]:
        verdict = ("NO COOKIE ISSUED -- the server never sent Set-Cookie on these "
                   "calls, so routing stickiness cannot be the mechanism here")
    elif control_score["ok"] == sticky_score["ok"]:
        verdict = ("NO DIFFERENCE -- both arms fared identically; the wave "
                   "diagnosis stands and the cookie jar buys nothing")
    elif sticky_score["ok"] > control_score["ok"] and len(sticky_won) >= 2:
        verdict = ("STICKINESS IMPLICATED -- the cookie-carrying arm succeeded "
                   "in rounds where the cookie-less arm failed, %d times"
                   % len(sticky_won))
    elif sticky_score["ok"] > control_score["ok"]:
        verdict = ("SUGGESTIVE, UNDERPOWERED -- the cookie arm did better but on "
                   "too few discriminating rounds to separate it from noise")
    else:
        verdict = ("AGAINST STICKINESS -- the cookie-less arm did at least as "
                   "well")

    return {
        "t": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "game_id": game_id, "rounds": rounds,
        "control_game": control_game, "sticky_game": sticky_game,
        "arms_share_a_game": control_game == sticky_game,
        "design": ("interleaved A/B, one RESET per arm per round, arm order "
                   "alternating; RESET is a command not an action, so this "
                   "costs zero action quota"
                   + ("" if control_game == sticky_game else
                      "; arms on different games, so neither can starve the "
                      "other of a live session")),
        "hypotheses": {
            "wave": "unavailability is a property of time; arms fail together",
            "stickiness": ("unavailability is a property of routing; the arm "
                           "echoing AWSALB cookies keeps hitting the replica "
                           "that holds the session"),
        },
        "control": control_score, "sticky": sticky_score,
        "rounds_where_arms_disagreed": sorted(disagreements),
        "rounds_where_only_the_cookie_arm_succeeded": sorted(sticky_won),
        "verdict": verdict,
        "rows": rows,
        "caveat": ("RESET availability is not identical to mid-session ACTION "
                   "availability: a RESET can be served by any replica that can "
                   "start the game, while an ACTION needs the one holding the "
                   "guid. If anything that makes this probe CONSERVATIVE -- "
                   "stickiness should matter more for ACTIONs, not less."),
    }


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(prog="probe_stickiness.py",
                                     description=__doc__.splitlines()[0])
    parser.add_argument("--game", default="g50t-5849a774")
    parser.add_argument("--control-game", default=None,
                        help="run the cookie-less arm on a different game, so "
                             "the two arms cannot compete for one live session")
    parser.add_argument("--sticky-game", default=None)
    parser.add_argument("--rounds", type=int, default=8)
    args = parser.parse_args(argv)

    report = run(args.game, args.rounds, load_api_key(),
                 control_game=args.control_game, sticky_game=args.sticky_game)
    print("  control  %s" % json.dumps(report["control"], sort_keys=True))
    print("  sticky   %s" % json.dumps(report["sticky"], sort_keys=True))
    print("  %s" % report["verdict"])
    existing = []
    if os.path.exists(REPORT_PATH):
        with open(REPORT_PATH, encoding="utf-8") as fh:
            existing = json.load(fh).get("probes", [])
    existing.append(report)
    with open(REPORT_PATH, "w", encoding="utf-8", newline="") as fh:
        json.dump({"probes": existing}, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print("  report -> %s" % REPORT_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
