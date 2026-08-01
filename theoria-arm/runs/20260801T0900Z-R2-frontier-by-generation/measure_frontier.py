"""Before building a better frontier, measure whether a better frontier is reachable.

`20260801T0000Z-A-probe-economics/measure_legs.py` measured what the probes
cost. This measures something the earlier pass could not see, because it reads
the grids and not only their hashes: **where the observed successor sits
relative to anything the arm could have hypothesised.**

Three questions, in the order that matters.

1. **Is the frontier anchored to the world?** Every hypothesis in
   `inner/probe.build_hypotheses` predicts a successor of the *manual's*
   rolled-forward state. `inert` predicts that state rendered unchanged, so
   `predictions["inert"]` is the frontier's anchor. The world's own pre-state
   is `trace.before_hash`. If those two disagree the frontier is not a set of
   hypotheses about the next frame at all -- it is a set of hypotheses about a
   frame the world left behind, and *no* hypothesis in it, generated or
   ablated, can name the observed successor. This is a precondition on the
   whole probe beat and nothing in the arm checks it.

2. **How wide is the frontier really?** `n_hypotheses` counts hypotheses;
   what partitions an experiment is the number of *distinct predictions*. 16
   hypotheses that emit 2 hashes are a 2-way experiment.

3. **What did the world actually do, and could the DSL have said it?** For
   each completed probe, the exact cell delta from the world's pre-state to the
   world's observed successor, split into cells that had varied earlier in the
   run (an object instance can exist there, so a rule can name them) and cells
   changing for the first time (board -- the arm seats instances only on
   colours the board cannot explain, so no rule in this grammar can reach
   them).

Offline. Reads `probes.jsonl` (tracked) and `trace.jsonl` (gitignored, so a
clone without the traces gets a stated refusal rather than a silent zero).
No model call, no ARC action, no network. Development-pile games only.

    python measure_frontier.py [--legs-root <dir>] [--out MEASUREMENT.json]
"""

import argparse
import json
import os
import sys

LEGS = [
    "20260731T1240Z-A3-level2-carried",
    "20260731T1310Z-A3-level2-carried-r2",
    "20260731T1430Z-A3-level2-carried-r3",
    "20260731T1500Z-A3-sk48-carried-l1",
]

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_LEGS_ROOT = os.path.dirname(HERE)


def _read_jsonl(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _cells_changed(before, after):
    """Every (r, c, from, to) where two grids differ. Shapes may differ."""
    out = []
    rows = max(len(before), len(after))
    for r in range(rows):
        rb = before[r] if r < len(before) else []
        ra = after[r] if r < len(after) else []
        for c in range(max(len(rb), len(ra))):
            vb = rb[c] if c < len(rb) else None
            va = ra[c] if c < len(ra) else None
            if vb != va:
                out.append((r, c, vb, va))
    return out


def measure_leg(leg_dir):
    """One leg's probes, joined to its trace. Returns (summary, rows)."""
    probes_path = os.path.join(leg_dir, "probes.jsonl")
    trace_path = os.path.join(leg_dir, "trace.jsonl")
    if not os.path.exists(probes_path):
        return {"leg": os.path.basename(leg_dir), "status": "no probes.jsonl"}, []
    probes = _read_jsonl(probes_path)
    designs = {r["probe_id"]: r for r in probes if r.get("phase") == "design"}
    results = {r["probe_id"]: r for r in probes if r.get("phase") == "result"}

    have_trace = os.path.exists(trace_path)
    trace = _read_jsonl(trace_path) if have_trace else []
    by_note = {r.get("note"): r for r in trace if r.get("note")}
    by_step = {r["step_idx"]: r for r in trace}

    # A cell is "board so far" until the first step at which it changes. Walk
    # the trace once and record, per cell, the first step index at which it
    # took a different value from the step before.
    first_change = {}
    prev_grid = None
    for row in trace:
        frames = row.get("frames") or []
        grid = frames[-1] if frames else None
        if grid is not None and prev_grid is not None:
            for (r, c, _vb, _va) in _cells_changed(prev_grid, grid):
                first_change.setdefault((r, c), row["step_idx"])
        if grid is not None:
            prev_grid = grid

    rows = []
    for probe_id, design in sorted(designs.items()):
        result = results.get(probe_id)
        if result is None:
            continue                                   # designed, never resolved
        predictions = design.get("predictions") or {}
        distinct = sorted(set(predictions.values()))
        observed = result.get("observed")
        row = {
            "leg": os.path.basename(leg_dir),
            "probe_id": probe_id,
            "action": design.get("action"),
            "step_idx": design.get("step_idx"),
            "n_hypotheses": len(predictions),
            "frontier_width_distinct": len(distinct),
            "observed": observed,
            "off_frontier": observed not in set(predictions.values()),
            "expected_bits": ((design.get("design") or {}).get("best") or {}
                              ).get("entropy_bits"),
            "realised_bits": result.get("information_gain_bits"),
        }

        step = by_note.get(probe_id)
        if step is not None:
            before_hash = step.get("before_hash")
            row["anchor_hash"] = predictions.get("inert")
            row["world_before_hash"] = before_hash
            row["anchored"] = (predictions.get("inert") == before_hash)
            row["n_frames"] = step.get("n_frames")
            prev = by_step.get(step["step_idx"] - 1)
            after = (step.get("frames") or [None])[-1]
            before = (prev.get("frames") or [None])[-1] if prev else None
            if before is not None and after is not None:
                delta = _cells_changed(before, after)
                virgin = [d for d in delta
                          if first_change.get((d[0], d[1])) == step["step_idx"]]
                row["observed_delta_cells"] = len(delta)
                row["delta_cells_first_ever_change"] = len(virgin)
                row["delta_cells_previously_dynamic"] = len(delta) - len(virgin)
                row["delta_colour_transitions"] = sorted(
                    {"%s->%s" % (d[2], d[3]) for d in delta})
                row["virgin_cells"] = sorted((d[0], d[1]) for d in virgin)[:8]
        rows.append(row)

    completed = rows
    anchored = [r for r in completed if r.get("anchored") is True]
    unanchored = [r for r in completed if r.get("anchored") is False]
    summary = {
        "leg": os.path.basename(leg_dir),
        "trace_available": have_trace,
        "probes_designed": len(designs),
        "probes_completed": len(completed),
        "off_frontier": sum(1 for r in completed if r["off_frontier"]),
        "frontier_width_distinct_values": sorted(
            {r["frontier_width_distinct"] for r in completed}),
        "anchored_to_world": len(anchored),
        "anchor_drifted": len(unanchored),
        "anchor_unknown": len(completed) - len(anchored) - len(unanchored),
        "off_frontier_while_anchored": sum(
            1 for r in anchored if r["off_frontier"]),
        "probes_with_virgin_delta_cells": sum(
            1 for r in completed
            if r.get("delta_cells_first_ever_change", 0) > 0),
        "probes_with_delta_measured": sum(
            1 for r in completed if "observed_delta_cells" in r),
    }
    return summary, rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--legs-root", default=DEFAULT_LEGS_ROOT)
    ap.add_argument("--out", default=os.path.join(HERE, "MEASUREMENT.json"))
    args = ap.parse_args(argv)

    per_leg, all_rows = [], []
    for leg in LEGS:
        summary, rows = measure_leg(os.path.join(args.legs_root, leg))
        per_leg.append(summary)
        all_rows.extend(rows)

    missing = [s["leg"] for s in per_leg if not s.get("trace_available")]
    completed = all_rows
    anchored = [r for r in completed if r.get("anchored") is True]
    unanchored = [r for r in completed if r.get("anchored") is False]
    with_delta = [r for r in completed if "observed_delta_cells" in r]
    virgin = [r for r in with_delta
              if r.get("delta_cells_first_ever_change", 0) > 0]

    totals = {
        "probes_completed": len(completed),
        "off_frontier": sum(1 for r in completed if r["off_frontier"]),
        "frontier_width_distinct_values": sorted(
            {r["frontier_width_distinct"] for r in completed}),
        "frontier_width_max": max(
            (r["frontier_width_distinct"] for r in completed), default=0),
        "anchored_to_world": len(anchored),
        "anchor_drifted": len(unanchored),
        "off_frontier_while_anchored": sum(
            1 for r in anchored if r["off_frontier"]),
        "off_frontier_while_drifted": sum(
            1 for r in unanchored if r["off_frontier"]),
        "probes_with_delta_measured": len(with_delta),
        "probes_whose_delta_touches_a_never_before_changed_cell": len(virgin),
        "traces_missing": missing,
    }
    payload = {"legs": per_leg, "totals": totals, "probes": all_rows}
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(json.dumps(totals, indent=1, sort_keys=True))
    for leg in per_leg:
        print(json.dumps(leg, sort_keys=True))
    if missing:
        print("REFUSED to measure deltas for %d leg(s): trace.jsonl is "
              "gitignored and absent here -- %s" % (len(missing), missing),
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
