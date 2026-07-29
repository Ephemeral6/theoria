"""Probe 08 -- the C9 acceptance line, run directly.

`worldgen`'s count-lock world through `cold-start-a0`'s engines stage.  Writes
its candidates and report into *this* run directory rather than into worldgen's
tree, so the acceptance is reproducible without any worker writing outside its
territory.

    python .../08_acceptance_pipeline.py [world ...]

Read-only with respect to every tracked tree except this run directory.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RUN = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(RUN, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "cold-start-a0"))
sys.path.insert(0, os.path.join(ROOT, "engine-rig"))

import _bootstrap  # noqa: F401,E402

from pipeline import engines_stage  # noqa: E402

WORLDS = sys.argv[1:] or ["t2-lock-fragile", "t1-tokens-lock", "t1-walk-maze"]
OUT = os.path.join(RUN, "acceptance")
os.makedirs(OUT, exist_ok=True)

summary = {}
for world in WORLDS:
    trace = os.path.join(ROOT, "worldgen", "out", "worlds", world, "raw_trace.jsonl")
    cand = os.path.join(OUT, "candidates.%s.jsonl" % world)
    rep = os.path.join(OUT, "engines_report.%s.json" % world)
    if os.path.exists(cand):
        os.remove(cand)
    try:
        report = engines_stage.run_stage(trace, cand, rep, timestamp="1970-01-01T00:00:00Z")
        rules = report.get("rules") or report.get("n_rules")
        row = {
            "ran": True,
            "mover": report.get("mover"),
            "tracks": report.get("tracks"),
            "rules": rules if isinstance(rules, int) else len(rules or []),
            "operator": report.get("segment_operator"),
        }
    except Exception as exc:  # noqa: BLE001
        row = {"ran": False, "error": "%s: %s" % (type(exc).__name__, exc)}
    summary[world] = row
    print("== %-18s %s" % (world, json.dumps(row, sort_keys=True)))

with open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8", newline="\n") as fh:
    json.dump(summary, fh, indent=2, sort_keys=True)
    fh.write("\n")
