"""probe_yield -- read-only measurement of what the probe beat actually bought.

Two numbers the Phase 3 scoreboard (Theoria.md:351) does not currently carry:

  frontier_width : how many DISTINCT outcomes the probe's hypothesis set
                   predicts for the chosen action. This is the ceiling on the
                   split entropy of Theoria.md:208 -- width 2 means the probe
                   can buy at most one bit, width 1 means it buys nothing.
  probe_yield    : the fraction of probes whose OBSERVED outcome was among the
                   candidate predictions. This is the disambiguator the seven
                   surprise kinds lack: a probe_refutation with the truth
                   inside the set narrows the frontier (informative), one with
                   the truth outside it eliminates every hypothesis at once and
                   selects nothing (uninformative).

Reads theoria-arm/runs/*/surprises.jsonl only. No network, no API, no writes
outside this run directory. Development-pile legs only.
"""

import collections
import json
import os
import sys

LEGS = [
    "20260731T1240Z-A3-level2-carried",
    "20260731T1310Z-A3-level2-carried-r2",
    "20260731T1430Z-A3-level2-carried-r3",
    "20260731T1500Z-A3-sk48-carried-l1",
]


def leg_report(runs_root, leg):
    path = os.path.join(runs_root, leg, "surprises.jsonl")
    if not os.path.exists(path):
        return {"leg": leg, "error": "no surprises.jsonl"}
    with open(path, encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh if line.strip()]

    kinds = collections.Counter(r["kind"] for r in rows)
    probes = [r for r in rows if r["kind"] == "probe_refutation"]

    widths, sizes, hits, families = [], [], 0, set()
    for r in probes:
        preds = r["payload"]["predictions"]
        widths.append(len(set(preds.values())))
        sizes.append(len(preds))
        families |= set(preds)
        if r["payload"]["observed"] in set(preds.values()):
            hits += 1

    rep = {
        "leg": leg,
        "surprises_total": len(rows),
        "by_kind": dict(sorted(kinds.items())),
        "unhandled": sum(1 for r in rows if r.get("handled_by") is None),
        "probes": len(probes),
        "probe_yield_hits": hits,
        "probe_yield": (hits / len(probes)) if probes else None,
    }
    if probes:
        rep["candidates_per_probe"] = {"min": min(sizes), "max": max(sizes)}
        rep["frontier_width"] = {"min": min(widths), "max": max(widths)}
        rep["hypothesis_families"] = {
            "named": sorted(f for f in families if not f.startswith("without_")),
            "ablation_count": len([f for f in families if f.startswith("without_")]),
        }
    return rep


def main():
    runs_root = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "theoria-arm", "runs")
    runs_root = os.path.abspath(runs_root)

    legs = [leg_report(runs_root, leg) for leg in LEGS]
    scored = [l for l in legs if l.get("probes")]
    doc = {
        "source": "theoria-arm/runs/<leg>/surprises.jsonl",
        "legs": legs,
        "pooled": {
            "probes": sum(l["probes"] for l in scored),
            "probe_yield_hits": sum(l["probe_yield_hits"] for l in scored),
            "frontier_width_max": max(l["frontier_width"]["max"] for l in scored),
            "frontier_width_min": min(l["frontier_width"]["min"] for l in scored),
        },
    }
    doc["pooled"]["probe_yield"] = (
        doc["pooled"]["probe_yield_hits"] / doc["pooled"]["probes"])
    print(json.dumps(doc, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
