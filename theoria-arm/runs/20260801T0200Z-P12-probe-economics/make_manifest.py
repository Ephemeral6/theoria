"""Write this run's MANIFEST.json, hashing every delivered artefact.

Deterministic: re-running it over unchanged files reproduces the file byte for
byte, which is what `armtools.verify_provenance` re-checks.
"""

import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

BASE_COMMIT = "73760dc85fb693ea7833e36d8e815982e38e55cd"
BRANCH = "p12/arm-diag"
UTC = "2026-08-01T02:00:00Z"

ARM = os.path.dirname(os.path.dirname(HERE))

DELIVERED = [
    "inner/probe.py",
    "inner/plan.py",
    "inner/loop.py",
    "tests/test_probe_economics.py",
    "tests/test_probe_guard_in_the_loop.py",
]

LOCAL = [
    "RUN_STATE.md",
    "replay_live_probes.py",
    "probe_replay.json",
    "mock_campaign_before.json",
    "mock_campaign_after.json",
    "make_manifest.py",
]


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    files = []
    for rel in LOCAL:
        path = os.path.join(HERE, rel)
        if os.path.exists(path):
            files.append({"path": rel, "sha256": _sha256(path)})
    for rel in DELIVERED:
        path = os.path.join(ARM, rel)
        if os.path.exists(path):
            files.append({"path": "../../" + rel, "sha256": _sha256(path)})

    replay = json.load(open(os.path.join(HERE, "probe_replay.json"),
                            encoding="utf-8"))
    totals = replay["totals"]

    manifest = {
        "base_commit": BASE_COMMIT,
        "branch": BRANCH,
        "cell": "P12",
        "delivered": DELIVERED,
        "files": sorted(files, key=lambda f: f["path"]),
        "lane": "arm",
        "measured": {
            "legs_diagnosed": [
                "20260731T1240Z-A3-level2-carried",
                "20260731T1310Z-A3-level2-carried-r2",
                "20260731T1430Z-A3-level2-carried-r3",
                "20260731T1500Z-A3-sk48-carried-l1"],
            "levels_completed_across_all_four_legs": 0,
            "committed_actions_across_all_four_legs": 0,
            "plan_status_on_every_turn_of_r3": "no_goal_declared (29/29)",
            "probes_resolved": totals["probes_resolved"],
            "probes_vacuous": totals["vacuous"],
            "distinct_experiments": totals["distinct_experiments"],
            "claimed_bits": totals["claimed_bits"],
            "realised_bits": totals["realised_bits"],
            "probes_kept_under_the_new_guards":
                totals["probes_kept_under_guard"],
            "probes_refused_as_repeats": totals["refused_repeat"],
            "probes_refused_on_a_vacuous_streak":
                totals["refused_vacuous_streak"],
            "mock_campaign_delta": ("none: byte-identical before and after. "
                                    "--mock implies offline, offline skips "
                                    "theorize, and with no manual the probe "
                                    "and plan beats are never reached. The "
                                    "specified gate cannot see this change; "
                                    "replay_live_probes.py is the instrument "
                                    "that can."),
        },
        "prompt_id": "P12-theoria-arm-probe-economics",
        "sealed_pile_contact": "none",
        "spend": {"api_calls": 0, "usd": 0.0,
                  "note": "entirely offline: no ARC API call, no model call, "
                          "no network. The four legs are read-only inputs."},
        "territory": "theoria-arm",
        "utc": UTC,
        "what": ("diagnosis of why four live legs and ~$35 completed zero "
                 "levels, plus the cheap-and-certain half of the fix: "
                 "no_goal_declared becomes a heuristic_miss surprise so the "
                 "desk is told planning is dead; probe results carry realised "
                 "information gain beside the design's claim and name a "
                 "vacuous frontier; and three refusals stop the arm buying an "
                 "action for a question it has already asked or cannot "
                 "answer."),
    }

    out = os.path.join(HERE, "MANIFEST.json")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(out)


if __name__ == "__main__":
    main()
