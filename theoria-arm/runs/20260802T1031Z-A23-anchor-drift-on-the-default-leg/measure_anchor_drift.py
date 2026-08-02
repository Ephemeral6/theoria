"""Take the drift triple for eight archived legs, and check it against R2's.

Four of the eight (`R1-*`, `R1b-*`) have never had an anchor number taken at
all. The other four are the ones `20260801T0900Z-R2-frontier-by-generation`
measured, and recomputing them is the only reason to believe the first four:
two independently written readers of the same two files must land on the same
52 probes and the same 35 drifts, row for row, or this tool is measuring
something else that also produces integers.

Writes, into this directory and nowhere else:

* `ANCHOR_DRIFT.json`             -- all eight legs, per probe and in total
* `ANCHOR_DRIFT.<leg>.json`       -- one file per leg, so a leg's triple is
                                     addressable without reading the aggregate
* `CROSSCHECK.json`               -- this module against R2's `MEASUREMENT.json`

**Why the per-leg files are here rather than in each leg's own directory.**
The ticket asked for a new file inside the measured leg's `runs/` directory, on
the reasoning that a new file changes no byte the published manifest covers.
Measured, it does: `armtools.backfill._files_the_clone_carries` re-derives
`files[]` by walking the directory, so dropping `ANCHOR_DRIFT.json` into
`runs/20260731T1240Z-A3-level2-carried/` takes its list from 37 entries to 38,
`backfill.render(build(...))` stops matching the manifest on disk, and
`armtools.verify_provenance` check 8 -- "re-deriving every manifest reproduces
it byte for byte" -- goes red for a live-spend archive record. See
`GAPS.md` GAP A23-1. The triple is still per leg and still in `runs/`; it is
filed under the run that took it rather than inside the run it describes.

Offline. Reads `probes.jsonl` (tracked) and `trace.jsonl` (gitignored, so a
clone gets a stated per-leg refusal and a `null` triple, never a zero). No
model call, no ARC action, no network. Development-pile games only, by name.

    python measure_anchor_drift.py [--legs-root DIR]
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ARM)

import _bootstrap                                       # noqa: E402,F401

from armtools import anchor_drift                       # noqa: E402

R2_MEASUREMENT = os.path.join(
    "20260801T0900Z-R2-frontier-by-generation", "MEASUREMENT.json")


def _write(path, payload):
    with open(path, "wb") as fh:
        fh.write((json.dumps(payload, indent=1, sort_keys=True, default=str)
                  + "\n").encode("utf-8"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--legs-root", default=os.path.dirname(HERE))
    args = ap.parse_args(argv)

    report = anchor_drift.measure(anchor_drift.DEFAULT_LEGS, args.legs_root)
    _write(os.path.join(HERE, "ANCHOR_DRIFT.json"), report)
    for leg in report["legs"]:
        _write(os.path.join(HERE, "ANCHOR_DRIFT.%s.json" % leg["leg"]), leg)

    measurement = os.path.join(args.legs_root, R2_MEASUREMENT)
    if os.path.exists(measurement):
        check = anchor_drift.crosscheck(report, measurement)
    else:
        check = {"source": R2_MEASUREMENT, "equal": None,
                 "status": "R2's MEASUREMENT.json is not at the given "
                           "legs-root; nothing crosschecked"}
    _write(os.path.join(HERE, "CROSSCHECK.json"), check)

    for leg in report["legs"]:
        triple = leg["triple"]
        print("%-42s probes=%-5s drifted=%-5s drifted_and_off=%-5s %s" % (
            leg["leg"], triple["probes"], triple["drifted"],
            triple["drifted_and_off_frontier"],
            "" if leg["status"] == anchor_drift.MEASURED else leg["status"]))
    print(json.dumps(report["totals"], sort_keys=True))
    print("crosscheck vs R2 MEASUREMENT.json: %s (%s probes)" % (
        check.get("equal"), check.get("probes_compared")))

    for leg in report["refused"]:
        print("REFUSED %s -- %s" % (leg["leg"], leg["status"]),
              file=sys.stderr)

    if check.get("equal") is False:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
