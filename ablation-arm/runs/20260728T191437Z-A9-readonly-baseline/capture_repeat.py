"""Is the rebuilt criterion stable, or did it pass once by luck?

    python ablation-arm/runs/20260728T191437Z-A9-readonly-baseline/capture_repeat.py [n]

The single controlled observation in `02-real-run.json` reports zero escapes.
One green is weak evidence for a check whose whole failure mode is intermittency
-- the criterion it replaces was rewritten *because* of one intermittent red.
So this runs the same controlled observation N times (default 10) and records
every reported path from every trial.

Also worth having: the criterion the audit falsified was tightened to silence a
flake.  If this one flakes at a measurable rate, that has to be a number in the
run directory rather than a surprise for whoever sees the first red.

Offline: `run_arm.run_all(['a0-base'])` only. No network, no API.
"""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(os.path.dirname(HERE))
if ARM not in sys.path:
    sys.path.insert(0, ARM)

import _bootstrap  # noqa: F401,E402

from ablcore import outside  # noqa: E402


def main(trials: int = 10):
    def run_a0():
        import run_arm
        run_arm.run_all(["a0-base"])

    rows = []
    for i in range(trials):
        obs = outside.observe(run_a0)
        rows.append({
            "trial": i,
            "background": len(obs.background),
            "observed": len(obs.observed),
            "reported": obs.reported,
            "aligned": obs.aligned,
            "idle_seconds": round(obs.idle_seconds, 3),
            "run_seconds": round(obs.run_seconds, 3),
            "makeup_seconds": round(obs.makeup_seconds, 3),
        })
        print("trial %2d: background=%d observed=%d reported=%d aligned=%s"
              % (i, len(obs.background), len(obs.observed),
                 len(obs.reported), obs.aligned))

    reds = [r for r in rows if r["reported"]]
    payload = {
        "what": "N controlled observations of the same offline run, to put a "
                "number on the criterion's flake rate instead of inferring it "
                "from one green",
        "trials": trials,
        "trials_red": len(reds),
        "every_path_ever_reported": sorted({p for r in rows
                                            for p in r["reported"]}),
        "all_aligned": all(r["aligned"] for r in rows),
        "rows": rows,
    }
    out = os.path.join(HERE, "07-repeat-trials.json")
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")
    print("\n%d/%d trials red; paths ever reported: %s"
          % (len(reds), trials, payload["every_path_ever_reported"]))
    print("wrote 07-repeat-trials.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 10))
