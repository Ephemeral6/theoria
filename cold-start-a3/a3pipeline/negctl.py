"""**The negative controls.**  Would a carried domain that is wrong be caught?

A transfer result is worth nothing without this.  "The books worked on level 2"
is only informative if books that *should* fail do fail — otherwise the green
column might just mean the checks cannot see anything.

**The controls run the transfer arm unmodified.**  `negctl.run_all` calls
`transfer.run` with a different level name and a different output directory and
changes nothing else: same domain file, same problem builder, same compile
path, same certify calls, same executor.  A negative control implemented by a
separate code path would be testing a separate code path.

Both controls render **byte-identical first frames** to level 2
(`tests/test_world.py::test_the_negative_controls_are_pixel_identical_to
_level_2`).  The edit is in the transition function.  So the static certify —
the cheap layer on frame 0 — *cannot* catch either of them, and it is expected
to come back GREEN.  That is not a weakness of the valve; it is the reason
there are two halves to it, and it makes the boundary between them measurable:

| | 渲染失配 (static, frame 0) | 重放失配 (replay, after acting) |
|---|---|---|
| what it sees | the board | the world's answers to the plan |
| cost to run | 0 actions | plan-length actions |
| catches L2_ONEWAY | no | **yes** |
| catches L2_REWIRED | no | **yes** |

**The two controls are not the same test.**

* **`a3-l2-oneway`** deletes the portal's B → exit_b leg.  Level 2 becomes
  unsolvable.  A manual that fails to notice does not merely mis-predict one
  step — it produces a plan, executes it, and the arm would report a **win that
  never happened**.  This is the dangerous failure, and it is the one Theoria
  §1.3 is about: every gate green, and the conclusion false.
* **`a3-l2-rewired`** keeps the leg but lands the Cart on a different cell.
  Level 2 stays solvable in 15.  Here the valve is tested against a *wrong
  prediction* rather than against unsolvability, which separates two things one
  control alone would conflate.

What a caught control produces is a **theorize trigger**, not a repair: the arm
stops with `theorize_triggered: true` and the mismatching frame on the record.
Turning that into a corrected manual is the 定位 → 戳探 → 修订 loop, and A2 ran
it end to end on a different defect.  A3 does not re-run it; A3's claim is
about the valve, and `A3_REPORT.md` §5 says exactly that rather than implying a
repair happened here.
"""

import json
import os
import sys
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from a3pipeline import transfer  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACTS = os.path.join(ROOT, "artifacts")

CONTROLS = (
    {
        "level": "a3-l2-oneway",
        "frame_name": "l2neg_frame0.json",
        "out_name": "generated_l2neg",
        "tag": "l2neg",
        "arm": "l2_negctl_oneway",
        "edit": "the portal's B -> exit_b leg is deleted",
        "world_is_solvable": False,
        "note": "negative control 1: carried domain, one mechanism deleted",
    },
    {
        "level": "a3-l2-rewired",
        "frame_name": "l2rew_frame0.json",
        "out_name": "generated_l2rew",
        "tag": "l2rew",
        "arm": "l2_negctl_rewired",
        "edit": "the portal's B leg lands the Cart on a different cell",
        "world_is_solvable": True,
        "note": "negative control 2: carried domain, one mechanism rewired",
    },
)


def run_all() -> Dict[str, object]:
    results: List[Dict[str, object]] = []

    for control in CONTROLS:
        report = transfer.run(
            level=control["level"],
            frame_name=control["frame_name"],
            out_name=control["out_name"],
            tag=control["tag"],
            arm=control["arm"],
            note=control["note"],
        )

        static_green = report.get("certify_static", {}).get("green")
        replay = report.get("certify_replay") or {}
        replay_green = replay.get("green")
        planned = report.get("plan", {}).get("status") == "SAT"
        won = bool(report.get("execution", {}).get("win"))

        # The valve fires iff the arm ends up refusing to claim a win.  Two
        # ways to fire: the replay disagreed, or the plan never appeared.
        caught = (report.get("outcome") != "win")

        results.append({
            "arm": control["arm"],
            "level": control["level"],
            "edit": control["edit"],
            "world_is_solvable": control["world_is_solvable"],
            "static_certify_green": static_green,
            "planned": planned,
            "replay_certify_green": replay_green,
            "claimed_a_win": won and replay_green,
            "theorize_triggered": bool(report.get("theorize_triggered")),
            "caught": caught,
            "outcome": report.get("outcome"),
            "first_mismatch": (replay.get("anomalies") or [None])[0],
            "anomaly_kinds": replay.get("anomaly_kinds"),
        })

    verdict = {
        "controls": results,
        "all_caught": all(r["caught"] for r in results),
        "none_claimed_a_win": not any(r["claimed_a_win"] for r in results),
        "static_layer_caught_any": any(r["static_certify_green"] is False
                                       for r in results),
        "reading": (
            "Both controls are invisible on the board and visible in the "
            "replay. The static layer is free but blind to a transition-"
            "function edit; the replay layer costs plan-length actions and "
            "catches both. That boundary is the honest statement of what the "
            "carried-domain safety valve does."
        ),
    }

    out = os.path.join(ARTIFACTS, "negative_controls.json")
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(verdict, indent=2, sort_keys=True) + "\n")
    return verdict


def main() -> int:
    verdict = run_all()
    for row in verdict["controls"]:
        print("%-22s static=%-5s plan=%-5s replay=%-5s caught=%-5s outcome=%s"
              % (row["arm"], row["static_certify_green"], row["planned"],
                 row["replay_certify_green"], row["caught"], row["outcome"]))
    print("all caught: %s | none claimed a win: %s"
          % (verdict["all_caught"], verdict["none_claimed_a_win"]))
    return 0 if verdict["all_caught"] and verdict["none_claimed_a_win"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
