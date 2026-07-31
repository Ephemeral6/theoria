"""Compare two already-archived spot-check reports position by position.

Both halves of the second game's evidence exist as archived JSON:

  * `proxy/runs/20260731T154336Z-P1-replay-spotcheck-2/replay_spotcheck_g50t.json`
    -- 26 sessions from four `baseline-arms` campaign shards, lifted to canon
    and checked on 2026-07-31;
  * `replay_spotcheck_g50t_arm.json` beside this script -- 3 live
    `theoria-arm` legs of the same day, read straight out of the arm's own
    ledgers under `--compact-refusals`.

Comparing the reports rather than re-deriving the union is a deliberate
choice, not a shortcut. The baseline half's inputs are four 37 MB shards
lifted into ~33 MB of canonical ledgers that were never archived; re-running
the union would depend on regenerating those, and the whole point of an
archived report is that the finding survives without them. Both files are
hashed in their run manifests, so this comparison is reproducible from two
small tracked artefacts.

What agreement here means: two harnesses that share no code path into the
environment, run in different campaigns, recorded the same frame bytes for the
same opening commands on `g50t-5849a774`. What it does not mean: that our
proxies can *reproduce* a run. That still needs a live replay through
`proxy/replay.py` and is still owed.

    python crosscheck_baseline.py -o crosscheck_arm_vs_baseline.json
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROXY = os.path.dirname(os.path.dirname(HERE))

BASELINE = os.path.join(
    PROXY, "runs", "20260731T154336Z-P1-replay-spotcheck-2",
    "replay_spotcheck_g50t.json")
ARM = os.path.join(HERE, "replay_spotcheck_g50t_arm.json")


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def crosscheck(baseline, arm):
    if baseline["game_id"] != arm["game_id"]:
        raise SystemExit("different games: %s vs %s"
                         % (baseline["game_id"], arm["game_id"]))
    rows = []
    overlap = min(len(baseline["comparisons"]), len(arm["comparisons"]))
    for position in range(overlap):
        left, right = baseline["comparisons"][position], arm["comparisons"][position]
        rows.append({
            "position": position,
            "baseline_action": left["action"],
            "arm_action": right["action"],
            "baseline_sessions": left["sessions"],
            "arm_sessions": right["sessions"],
            "frame_hash": left["frame_hash"],
            "agree": (left["action"] == right["action"]
                      and left["frame_hash"] == right["frame_hash"]),
        })
    disagreements = [r for r in rows if not r["agree"]]
    return {
        "game_id": baseline["game_id"],
        "left": {"report": os.path.relpath(BASELINE, PROXY),
                 "harness": "baseline-arms campaign shards (lifted to canon)",
                 "n_sessions": baseline["n_sessions"],
                 "steps_compared": baseline["steps_compared"]},
        "right": {"report": os.path.relpath(ARM, PROXY),
                  "harness": "theoria-arm live legs (canon, --compact-refusals)",
                  "n_sessions": arm["n_sessions"],
                  "steps_compared": arm["steps_compared"]},
        "overlap": overlap,
        "rows": rows,
        "disagreements": disagreements,
        # Positions where only one side reached: the arm legs ran further than
        # the baseline sweep's fixed opening, so this is not a gap in the
        # evidence, it is evidence one side alone carries.
        "positions_only_one_side_reached": {
            "baseline": max(0, baseline["steps_compared"] - overlap),
            "arm": max(0, arm["steps_compared"] - overlap),
        },
        "verdict": "PASS" if overlap and not disagreements else (
            "FAIL" if disagreements else "INSUFFICIENT"),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("-o", "--out", default=None)
    args = ap.parse_args(argv)
    report = crosscheck(load(BASELINE), load(ARM))
    blob = json.dumps(report, indent=2, sort_keys=True)
    if args.out:
        path = args.out if os.path.isabs(args.out) else os.path.join(HERE, args.out)
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(blob + "\n")
    print(blob)
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
