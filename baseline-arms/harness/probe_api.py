"""Is the live ARC API usable at all?

arc-recon logged INC-001/INC-001a/INC-002 on 2026-07-27: RESET succeeded on
4 of 48 attempts for one development-pile game, and every ACTION that followed
returned 400. If that still holds, the bare-CC arm has no environment to run in
and the pilot cannot happen on the live API.

This re-checks the claim rather than inheriting it, on **development-pile games
only**. The sealed pile is unreachable from here by construction (arc_client
raises before the socket opens).

    python -m harness.probe_api [--rounds N]
"""

import argparse
import json
import sys

from . import arc_client, key_proxy, ledger


def main(argv=None) -> int:
    """The credential child wraps the probe; `_probe` is the probe.

    Split so the body keeps its indentation. A live probe spends real ARC
    calls, so it is a spending entry point like the two runners and gets the
    same treatment (STATUS.md GAP-5, DECISIONS.md D-026).
    """
    with key_proxy.sealed_upstream(run_id="probe-api") as proxy:
        return _probe(argv, base_url=proxy.base_url)


def _probe(argv=None, base_url=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=2,
                    help="RESET attempts per development-pile game")
    args = ap.parse_args(argv)

    client = arc_client.ArcClient(base_url=base_url)
    dev = arc_client.dev_pile()
    print("development pile:", ", ".join(dev))
    print("sealed pile: %d games, unreachable from this module" % len(client.sealed))

    listed = client.list_games()
    listed_ids = {g["game_id"] for g in listed}
    print("GET /api/games -> %d games" % len(listed))

    card_id = client.open_scorecard(tags=["baseline-arms", "viability-probe"],
                                    opaque={"purpose": "check whether INC-002 still holds"})["card_id"]
    print("scorecard:", card_id)

    results = {}
    for game_id in dev:
        rec = {"listed": game_id in listed_ids, "reset_ok": 0, "reset_attempts": 0,
               "action_ok": 0, "action_attempts": 0, "messages": []}
        for _ in range(args.rounds):
            rec["reset_attempts"] += 1
            status, body = client.reset(game_id, card_id, raise_on_error=False)
            if status == 200 and isinstance(body, dict):
                rec["reset_ok"] += 1
                guid = body.get("guid")
                actions = body.get("available_actions") or [1]
                rec["available_actions"] = actions
                rec["state"] = body.get("state")
                rec["frames"] = len(body.get("frame") or [])
                # one action, to see whether the session survives the RESET
                rec["action_attempts"] += 1
                st2, b2 = client.action(game_id, card_id, guid, int(actions[0]),
                                        raise_on_error=False)
                if st2 == 200:
                    rec["action_ok"] += 1
                    rec["state_after_action"] = b2.get("state") if isinstance(b2, dict) else None
                else:
                    rec["messages"].append("ACTION%s -> %s %s" % (
                        actions[0], st2, (b2 or {}).get("message") if isinstance(b2, dict) else b2))
            else:
                msg = body.get("message") if isinstance(body, dict) else str(body)[:80]
                rec["messages"].append("RESET -> %s %s" % (status, msg))
        results[game_id] = rec
        print("  %-18s reset %d/%d  action %d/%d  %s" % (
            game_id, rec["reset_ok"], rec["reset_attempts"],
            rec["action_ok"], rec["action_attempts"],
            rec["messages"][0] if rec["messages"] else "ok"))

    client.close_scorecard(card_id)
    ledger.probe("viability_verdict", {"results": results, "rounds": args.rounds})

    playable = [g for g, r in results.items() if r["action_ok"] > 0]
    print()
    print("PLAYABLE (RESET + at least one ACTION):", playable or "NONE")
    print(json.dumps(results, indent=2, sort_keys=True))
    return 0 if playable else 1


if __name__ == "__main__":
    sys.exit(main())
