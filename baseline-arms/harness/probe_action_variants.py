"""Attempt 2 and 3 at the INC-002 blocker: can any ACTION shape get through?

arc-recon already ruled out (INC-002): four request-body shapes, stale
sessions, unclosed scorecards, card_id handling. This tries the hypotheses it
did *not*:

  H-A  the id on ACTION wants no version suffix (`g50t` not `g50t-5849a774`)
  H-B  ACTION wants guid alone, with no game_id at all
  H-C  the 400 is a load-balancer artefact -- some backend instances have the
       game loaded, some do not -- so an immediate retry storm should
       eventually land on a good instance
  H-D  the path casing / RESET-as-ACTION0 convention differs

Development pile only. Sealed games raise before any socket opens.

    python -m harness.probe_action_variants [--game g50t-5849a774] [--resets 6]
"""

import argparse
import json
import sys
import time

from . import arc_client, ledger


def variants(game_id: str, card_id: str, guid: str):
    """(label, path, body) triples. Each is a distinct structural hypothesis."""
    short = game_id.split("-")[0]
    return [
        ("H-A short id",   "/api/cmd/ACTION1", {"game_id": short, "card_id": card_id, "guid": guid}),
        ("H-B guid only",  "/api/cmd/ACTION1", {"guid": guid}),
        ("H-B guid+card",  "/api/cmd/ACTION1", {"guid": guid, "card_id": card_id}),
        ("H-D lowercase",  "/api/cmd/action1", {"game_id": game_id, "card_id": card_id, "guid": guid}),
        ("H-D ACTION0",    "/api/cmd/ACTION0", {"game_id": game_id, "card_id": card_id, "guid": guid}),
        ("baseline",       "/api/cmd/ACTION1", {"game_id": game_id, "card_id": card_id, "guid": guid}),
    ]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default="g50t-5849a774")
    ap.add_argument("--resets", type=int, default=8,
                    help="RESET attempts to find an availability window")
    ap.add_argument("--storm", type=int, default=10,
                    help="H-C: consecutive identical ACTION retries per window")
    args = ap.parse_args(argv)

    client = arc_client.ArcClient()
    client.assert_playable(args.game)          # sealed-pile guard, fails closed

    card_id = client.open_scorecard(tags=["baseline-arms", "inc-002-retry"],
                                    opaque={"purpose": "ACTION shape hypotheses"})["card_id"]
    findings = {"game": args.game, "windows": 0, "variant_results": {}, "storm_results": []}

    for attempt in range(args.resets):
        status, body = client.reset(args.game, card_id, raise_on_error=False)
        if status != 200 or not isinstance(body, dict):
            time.sleep(1.0)
            continue
        findings["windows"] += 1
        guid = body.get("guid")
        print("window %d open (guid %s)" % (findings["windows"], guid))

        for label, path, vbody in variants(args.game, card_id, guid):
            st, rb = client.request("POST", path, body=vbody,
                                    note="INC-002 variant %s" % label,
                                    raise_on_error=False)
            msg = rb.get("message") if isinstance(rb, dict) else str(rb)[:80]
            findings["variant_results"].setdefault(label, []).append([st, msg])
            print("   %-16s -> %s %s" % (label, st, msg))
            if st == 200:
                print("   *** %s SUCCEEDED ***" % label)

        # H-C: retry storm on the plain shape
        storm = []
        for _ in range(args.storm):
            st, rb = client.request(
                "POST", "/api/cmd/ACTION1",
                body={"game_id": args.game, "card_id": card_id, "guid": guid},
                note="INC-002 H-C storm", raise_on_error=False)
            storm.append(st)
            if st == 200:
                print("   *** H-C storm SUCCEEDED on retry ***")
                break
        findings["storm_results"].append(storm)
        print("   H-C storm statuses:", storm)
        break                                   # one good window is enough

    client.close_scorecard(card_id)
    ledger.probe("inc002_retry_experiment", findings)

    any_ok = any(st == 200 for runs in findings["variant_results"].values() for st, _ in runs) \
        or any(200 in s for s in findings["storm_results"])
    print()
    print(json.dumps(findings, indent=2, sort_keys=True))
    print("VERDICT:", "some ACTION shape works" if any_ok else "no ACTION shape works")
    return 0 if any_ok else 1


if __name__ == "__main__":
    sys.exit(main())
