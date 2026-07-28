"""Pre-flight: prove the whole live chain works before spending an action.

RESET is not billed -- `baseline-arms` compared four scorecards against their
ledgers and `scorecard.total_actions` equalled the count of successful
*actions* every time, with RESET counted separately. So opening a scorecard,
sending one RESET and closing again exercises every link in the live chain for
zero quota:

    arm -> env proxy -> key injection -> sealed-pile guard -> ARC -> ledger

and answers the questions that can only be answered live: does the key work,
does the guard let the dev-pile game through, does the 400 wave need the long
envelope today, what shape is the frame really, and what does the scorecard say
about an action count of zero.

    python -m armtools.preflight --game g50t-5849a774
"""

import argparse
import json
import os
import sys
import time

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap                                     # noqa: F401  (sys.path)

from harness.arc import ArcThroughProxy, frames_of
from harness.budget import Budget
from harness.run import Run


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--game", default="g50t-5849a774")
    ap.add_argument("--slug", default=None)
    args = ap.parse_args(argv)

    slug = args.slug or ("preflight-" + time.strftime("%Y%m%dT%H%M%SZ",
                                                      time.gmtime()))
    out = {}
    with Run(args.game, slug) as run:
        run.start_record(note="pre-flight: RESET only, zero billed actions")
        budget = Budget(actions=0, commands=120)       # no action may be spent
        arc = ArcThroughProxy(run.env_base, args.game, budget)

        started = time.time()
        card_id = arc.open_scorecard(tags=["theoria", "p8", "preflight"],
                                     opaque={"run_id": run.run_id})
        out["card_id"] = card_id
        out["scorecard_opened"] = bool(card_id)

        status, envelope = arc.reset()
        out["reset_status"] = status
        out["reset_attempts"] = arc.attempt_log[-1]["attempts"] if arc.attempt_log else None

        if status == 200 and isinstance(envelope, dict):
            frames = frames_of(envelope)
            grid = frames[-1] if frames else None
            out["envelope_keys"] = sorted(envelope)
            out["has_score_field"] = "score" in envelope
            out["n_frames"] = len(frames)
            out["grid_shape"] = [len(grid), len(grid[0])] if grid else None
            out["colours_in_frame"] = sorted({v for row in (grid or []) for v in row})
            out["available_actions"] = envelope.get("available_actions")
            out["win_levels"] = envelope.get("win_levels")
            out["state"] = envelope.get("state")
            out["levels_completed"] = envelope.get("levels_completed")
            out["guid_present"] = bool(envelope.get("guid"))
        else:
            out["reset_body"] = envelope

        out["scorecard_on_close"] = arc.close_scorecard()
        out["budget"] = budget.as_json()
        out["elapsed_s"] = round(time.time() - started, 1)
        out["attempt_log"] = arc.attempt_log
        out["env_proxy"] = run.proxy.summary() if run.proxy else None
        run.end_record(outcome="preflight", steps=1)
        run.write_run_json(out)

    print(json.dumps(out, indent=1, sort_keys=True, default=str))
    return 0 if out.get("reset_status") == 200 else 1


if __name__ == "__main__":
    sys.exit(main())
