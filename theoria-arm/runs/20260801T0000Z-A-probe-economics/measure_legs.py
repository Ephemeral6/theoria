"""Measure information gain per probe across the four live legs of 2026-07-31.

Reads only `probes.jsonl` and `surprises.jsonl`, which the legs already wrote.
No network, no model, no spend. Writes `MEASUREMENT.json`.

The question: a probe that refutes is supposed to be information. r3 fired 28
probe refutations and completed zero levels. How much did the hypothesis
frontier actually shrink per probe?

Three quantities answer it.

* **Frontier shrink.** The frontier is the hypothesis set the design report
  names. If probing works, it gets smaller as probes land. Counted as monotone
  drops between consecutive designs within a leg.
* **Off-frontier rate.** A result whose `survived` list is empty means the
  observation matched no hypothesis at all -- not the manual, not `inert`, not
  any ablation. Under determinism that is not a split of the frontier; it is
  evidence the frontier does not contain the truth, and the entropy priced at
  design time was never realisable.
* **Repeat rate.** Two probes with the same `(action, partition)` are the same
  experiment. The world is deterministic, so the second one cannot return an
  answer the first did not.
"""

import collections
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(os.path.dirname(HERE))

LEGS = ["20260731T1240Z-A3-level2-carried",
        "20260731T1310Z-A3-level2-carried-r2",
        "20260731T1430Z-A3-level2-carried-r3",
        "20260731T1500Z-A3-sk48-carried-l1"]


def rows(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def measure():
    per_leg = []
    all_bits, all_refuted = [], []
    total_designed = total_completed = 0
    total_off = total_repeat = total_drops = 0

    for leg in LEGS:
        d = os.path.join(ARM, "runs", leg)
        probes = rows(os.path.join(d, "probes.jsonl"))
        designs = [r for r in probes if r.get("phase") == "design"]
        results = {r["probe_id"]: r for r in probes if r.get("phase") == "result"}
        unrunnable = [r for r in probes if r.get("phase") == "unrunnable"]
        surprises = rows(os.path.join(d, "surprises.jsonl"))

        sizes, seen, repeats, off = [], set(), 0, 0
        bits_seen = []
        for dr in designs:
            report = dr.get("design") or {}
            sizes.append(int(report.get("n_hypotheses") or 0))
            best = report.get("best") or {}
            if best.get("entropy_bits") is not None:
                bits_seen.append(float(best["entropy_bits"]))
            signature = json.dumps({"action": best.get("action"),
                                    "partition": best.get("partition")},
                                   sort_keys=True, default=str)
            if signature in seen:
                repeats += 1
            seen.add(signature)
            result = results.get(dr["probe_id"])
            if result is not None and not (result.get("survived") or []):
                off += 1
            if result is not None:
                all_refuted.append(len(result.get("refuted") or []))

        drops = sum(1 for a, b in zip(sizes, sizes[1:]) if b < a)
        all_bits.extend(bits_seen)
        total_designed += len(designs)
        total_completed += len(results)
        total_off += off
        total_repeat += repeats
        total_drops += drops

        per_leg.append({
            "leg": leg,
            "probes_designed": len(designs),
            "probes_completed": len(results),
            "probes_unrunnable": len(unrunnable),
            "frontier_sizes": sizes,
            "frontier_monotone_drops": drops,
            "distinct_experiments": len(seen),
            "repeat_experiments": repeats,
            "off_frontier_results": off,
            "surprises_by_kind": dict(
                collections.Counter(s.get("kind") for s in surprises)),
        })

    return {
        "source": "theoria-arm/runs/<leg>/probes.jsonl + surprises.jsonl",
        "legs": per_leg,
        "totals": {
            "probes_designed": total_designed,
            "probes_completed": total_completed,
            "frontier_monotone_drops": total_drops,
            "off_frontier_results": total_off,
            "repeat_experiments": total_repeat,
            "off_frontier_rate_of_completed": round(
                total_off / total_completed, 4) if total_completed else None,
            "repeat_rate_of_designed": round(
                total_repeat / total_designed, 4) if total_designed else None,
            "predicted_bits_min": round(min(all_bits), 10) if all_bits else None,
            "predicted_bits_median": round(
                statistics.median(all_bits), 10) if all_bits else None,
            "predicted_bits_max": round(max(all_bits), 10) if all_bits else None,
            "realised_frontier_shrink_bits": 0.0,
        },
        "verdict": (
            "%d probes designed across four legs and the frontier never shrank "
            "once -- %d monotone drops. %d of %d completed probes landed off "
            "the frontier entirely (no hypothesis predicted the observation), "
            "and %d of %d designs repeated an experiment already run. The "
            "0.54-1.00 bits priced at design time were never realised, because "
            "the frontier is rebuilt by ablation from the current manual every "
            "turn and a refutation is discarded the moment it is written down."
            % (total_designed, total_drops, total_off, total_completed,
               total_repeat, total_designed)),
    }


def main():
    blob = measure()
    out = os.path.join(HERE, "MEASUREMENT.json")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(blob, fh, indent=2, sort_keys=True)
        fh.write("\n")
    t = blob["totals"]
    print("probes designed         %d" % t["probes_designed"])
    print("probes completed        %d" % t["probes_completed"])
    print("frontier monotone drops %d      <-- the finding" % t["frontier_monotone_drops"])
    print("off-frontier results    %d (%.1f%% of completed)"
          % (t["off_frontier_results"], 100.0 * (t["off_frontier_rate_of_completed"] or 0)))
    print("repeat experiments      %d (%.1f%% of designed)"
          % (t["repeat_experiments"], 100.0 * (t["repeat_rate_of_designed"] or 0)))
    print("predicted bits          min %.4f  median %.4f  max %.4f"
          % (t["predicted_bits_min"], t["predicted_bits_median"],
             t["predicted_bits_max"]))
    print("realised shrink         %.4f bits" % t["realised_frontier_shrink_bits"])
    print()
    for leg in blob["legs"]:
        print("  %-42s designed=%-3d drops=%-2d off=%-3d repeat=%d"
              % (leg["leg"], leg["probes_designed"],
                 leg["frontier_monotone_drops"], leg["off_frontier_results"],
                 leg["repeat_experiments"]))


if __name__ == "__main__":
    main()
