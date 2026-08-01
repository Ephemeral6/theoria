"""Recount, from tracked artefacts only, every live-leg number the 2026-08-01
paper edit puts in the body.

Why a papers-territory script exists at all when `theoria-arm` already published
`runs/20260801T0900Z-R2-frontier-by-generation/MEASUREMENT.json`: that
measurement reads `trace.jsonl`, which `theoria-arm/.gitignore` excludes. A
reader who clones this repository cannot re-run it, and the paper's binding rule
is that a number carries the path a reader can open. So this script reads only
files that `git ls-files` lists, recomputes the subset of the arm's numbers that
those files can support, and prints a per-number AGREES / DIFFERS against the
arm's published figures. Where it cannot see a number at all -- anchor drift is
the important one, since it is a comparison against `trace.before_hash` -- it
records `unmeasurable-here` rather than zero.

Absence is recorded as absence. A leg whose file is missing is `absent`, never 0.

Offline: reads the working tree, makes no network call, no model call, no ARC
action, and touches only development-pile legs (g50t-5849a774, sk48-d8078629).

    python census.py            # writes census.json, prints the table
    python census.py --check    # exit 1 if any comparison DIFFERS
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=HERE,
                      capture_output=True, text=True, check=True).stdout.strip()

#: The four legs of 2026-07-31 that `20260801T0000Z-A-probe-economics` and
#: `20260801T0900Z-R2-frontier-by-generation` both measured.
PROBE_LEGS = [
    "20260731T1240Z-A3-level2-carried",
    "20260731T1310Z-A3-level2-carried-r2",
    "20260731T1430Z-A3-level2-carried-r3",
    "20260731T1500Z-A3-sk48-carried-l1",
]

#: Every live leg of the Theoria arm, in start order. The first six are the ones
#: `battery/artifacts_live/live_arm_readings.json` reads (`n_runs: 6`); R1 and
#: R1b added four more after that artefact was written.
LIVE_LEGS = [
    "20260729T004020Z-leg01",
    "20260729T105729Z-leg01",
    "20260731T1240Z-A3-level2-carried",
    "20260731T1310Z-A3-level2-carried-r2",
    "20260731T1430Z-A3-level2-carried-r3",
    "20260731T1500Z-A3-sk48-carried-l1",
    "20260731T231654Z-R1-g50t-a",
    "20260731T231654Z-R1-sk48-b",
    "20260801T001851Z-R1b-g50t-a",
    "20260801T001851Z-R1b-sk48-b",
]

BATTERY_SIX = LIVE_LEGS[:6]

#: What the arm published, so the comparison is stated rather than eyeballed.
#: Sources: theoria-arm/runs/20260801T0000Z-A-probe-economics/README.md §1 and
#: theoria-arm/runs/20260801T0900Z-R2-frontier-by-generation/MANIFEST.json.
ARM_PUBLISHED = {
    "probes_designed": 56,
    "probes_completed": 52,
    "off_frontier": 47,
    "frontier_monotone_drops": 0,
    "frontier_width_values": [2],
    "on_frontier": 5,
}


def tracked(rel: str) -> bool:
    r = subprocess.run(["git", "ls-files", "--error-unmatch", rel],
                       cwd=REPO, capture_output=True, text=True)
    return r.returncode == 0


def rows(rel: str):
    """Parsed JSONL, or None if the file is not tracked / not present.

    None is not []. A caller that cannot tell them apart reports a leg that was
    never archived as a leg that did nothing."""
    path = os.path.join(REPO, rel)
    if not (os.path.isfile(path) and tracked(rel)):
        return None
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                out.append(json.loads(line))
    return out


def probe_census() -> dict:
    per_leg, designed, completed, off, drops = {}, 0, 0, 0, 0
    widths: set[int] = set()
    for leg in PROBE_LEGS:
        rel = "theoria-arm/runs/%s/probes.jsonl" % leg
        rs = rows(rel)
        if rs is None:
            per_leg[leg] = {"probes": "absent", "why": "%s is not tracked" % rel}
            continue
        des = [r for r in rs if r.get("phase") == "design"]
        res = [r for r in rs if r.get("phase") == "result"]
        # Frontier width = how many DISTINCT successors the frontier predicts.
        # Not the hypothesis count: sixteen hypotheses that predict two frames
        # are a frontier of width two, and the entropy is computed over the
        # partition, not over the list.
        leg_widths = [len(set((r.get("predictions") or {}).values())) for r in des]
        # A "monotone drop" is a probe after which the next design offered
        # strictly fewer hypotheses -- refutation actually narrowing the family.
        sizes = [len(r.get("design", {}).get("hypotheses") or []) for r in des]
        leg_drops = sum(1 for a, b in zip(sizes, sizes[1:]) if b < a)
        leg_off = sum(1 for r in res if not (r.get("survived") or []))
        per_leg[leg] = {
            "designed": len(des),
            "completed": len(res),
            "off_frontier": leg_off,
            "on_frontier": len(res) - leg_off,
            "frontier_width_values": sorted(set(leg_widths)),
            "hypothesis_count_values": sorted(set(sizes)),
            "monotone_drops": leg_drops,
        }
        designed += len(des)
        completed += len(res)
        off += leg_off
        drops += leg_drops
        widths |= set(leg_widths)
    return {
        "per_leg": per_leg,
        "probes_designed": designed,
        "probes_completed": completed,
        "off_frontier": off,
        "on_frontier": completed - off,
        "frontier_monotone_drops": drops,
        "frontier_width_values": sorted(widths),
        "unmeasurable_here": {
            "anchor_drift": "needs trace.jsonl (gitignored): the comparison is "
                            "predictions['inert'] against trace.before_hash. "
                            "Recorded as unmeasurable, not as zero.",
            "virgin_cell_deltas": "needs the grids in trace.jsonl, same reason.",
        },
    }


def cegis_census() -> dict:
    per_leg, disp, ref = {}, 0, 0
    for leg in LIVE_LEGS:
        rel = "theoria-arm/runs/%s/engines_online.json" % leg
        path = os.path.join(REPO, rel)
        if not (os.path.isfile(path) and tracked(rel)):
            per_leg[leg] = {"cegis_miner": "absent",
                            "why": "%s is not tracked" % rel}
            continue
        with open(path, encoding="utf-8") as fh:
            j = json.load(fh)
        c = (j.get("per_engine") or {}).get("cegis_miner")
        if c is None:
            per_leg[leg] = {"cegis_miner": "absent",
                            "why": "no cegis_miner key in %s" % rel}
            continue
        per_leg[leg] = {"dispatches": c.get("dispatches"),
                        "refused_with_reason": c.get("refused_with_reason"),
                        "errored": c.get("errored")}
        disp += c.get("dispatches") or 0
        ref += c.get("refused_with_reason") or 0
    return {"per_leg": per_leg, "dispatches": disp, "refused_with_reason": ref,
            "legs_with_a_reading": sum(
                1 for v in per_leg.values() if "dispatches" in v)}


def level_census() -> dict:
    per_leg = {}
    for leg in LIVE_LEGS:
        rel = "theoria-arm/runs/%s/levels.jsonl" % leg
        rs = rows(rel)
        per_leg[leg] = ("absent" if rs is None else len(rs))
    with_file = {k: v for k, v in per_leg.items() if v != "absent"}
    return {
        "per_leg": per_leg,
        "legs_with_a_levels_file": len(with_file),
        "level_completion_rows_total": sum(with_file.values()),
        "battery_six": {k: per_leg[k] for k in BATTERY_SIX},
        "note": "levels.jsonl carries one row per completed level. An empty "
                "tracked file is a measured zero; a missing file is `absent`.",
    }


def round_census() -> dict:
    """R1/R1b publish `levels_completed` explicitly; read it rather than infer."""
    out = {}
    for rnd in ["20260731T231654Z-R1", "20260801T001851Z-R1b"]:
        rel = "theoria-arm/runs/_rounds/%s/round.json" % rnd
        path = os.path.join(REPO, rel)
        if not (os.path.isfile(path) and tracked(rel)):
            out[rnd] = "absent"
            continue
        with open(path, encoding="utf-8") as fh:
            j = json.load(fh)
        out[rnd] = {
            "legs": [{"slug": l["slug"], "levels_completed": l["levels_completed"],
                      "outcome": l["outcome"]} for l in j["legs"]],
            "totals_levels_completed": j["totals"]["levels_completed"],
            "totals_usd": j["totals"]["usd"],
        }
    return out


def main() -> int:
    census = {
        "what": "papers-territory recount of the live-leg numbers the "
                "2026-08-01 edit puts in the body, from tracked files only",
        "utc": "2026-08-01T12:00:00Z",
        "reads_only_tracked_files": True,
        "spend": {"usd": 0.0, "arc_actions": 0, "model_calls": 0,
                  "network": "none"},
        "sealed_pile_contact": "none (g50t-5849a774, sk48-d8078629 only)",
        "probes": probe_census(),
        "cegis_miner": cegis_census(),
        "levels": level_census(),
        "rounds": round_census(),
    }
    comparisons = []
    for key, want in ARM_PUBLISHED.items():
        got = census["probes"][key]
        comparisons.append({"quantity": key, "arm_published": want,
                            "recounted_here": got,
                            "verdict": "AGREES" if got == want else "DIFFERS"})
    census["comparison_with_the_arms_own_figures"] = comparisons

    with open(os.path.join(HERE, "census.json"), "w", encoding="utf-8",
              newline="\n") as fh:
        fh.write(json.dumps(census, indent=1, sort_keys=True,
                            ensure_ascii=False) + "\n")

    for c in comparisons:
        print("%-26s arm %-8s here %-8s %s" % (
            c["quantity"], c["arm_published"], c["recounted_here"],
            c["verdict"]))
    cg = census["cegis_miner"]
    print("cegis_miner over %d live legs: %d dispatches, %d refused with a reason"
          % (cg["legs_with_a_reading"], cg["dispatches"],
             cg["refused_with_reason"]))
    lv = census["levels"]
    print("levels: %d legs carry levels.jsonl, %d completion rows in total"
          % (lv["legs_with_a_levels_file"], lv["level_completion_rows_total"]))
    bad = [c for c in comparisons if c["verdict"] == "DIFFERS"]
    if "--check" in sys.argv and bad:
        print("DIFFERS: %s" % ", ".join(c["quantity"] for c in bad))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
