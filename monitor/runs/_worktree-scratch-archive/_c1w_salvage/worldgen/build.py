"""Build the catalogue: every world, every artefact, byte-reproducibly.

```bash
python -m worldgen.build                     # all 20
python -m worldgen.build t1-switch-latch     # one
python -m worldgen.build --check             # rebuild into a temp dir and diff
```

Each world lands in `worldgen/out/worlds/<world_id>/`:

| file | who may read it |
|---|---|
| `raw_trace.jsonl` | **anyone** — this is the discovery input, same format as cold-start-a0 |
| `spec.json` | anyone; the picture and the legend, already parsed |
| `ground_truth.json`, `GROUND_TRUTH.md` | **scoring only** |
| `coverage.json` | scoring only — it names the rules the walk never witnessed |
| `reversibility.json` | scoring only — the A0′ stamp |

The split is cold-start-a0's and it is the only thing standing between this
catalogue and a rigged evaluation, so the directory layout puts the two classes
of file next to each other with the licence written down rather than assumed.

`--check` is the determinism gate: build twice, compare bytes.  A world whose
artefacts move between runs is a bug in a mechanism (a `set` reaching an output,
usually) and it is cheaper to catch here than in a diff three commits later.
"""

import argparse
import json
import os
import shutil
import tempfile
from typing import Any, Dict, List, Optional, Sequence

from .core import explorer, trace, truth
from .core.spec import WorldSpec
from .core.world import GridWorld
from .generate import CATALOGUE, BY_ID, write_catalogue

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "worlds")


def build_world(spec: WorldSpec, root: str,
                fraction: float = explorer.BUDGET_FRACTION) -> Dict[str, Any]:
    world = GridWorld(spec)
    dirname = os.path.join(root, spec.world_id)
    os.makedirs(dirname, exist_ok=True)

    states, actions = explorer.explore(world, fraction=fraction)
    trace.write_trace(os.path.join(dirname, "raw_trace.jsonl"), world, states, actions)
    coverage = explorer.coverage_report(world, states, actions)

    with open(os.path.join(dirname, "spec.json"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write(spec.dumps())
    with open(os.path.join(dirname, "coverage.json"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(coverage, indent=2, sort_keys=True) + "\n")

    truth_blob = truth.write(dirname, world)
    with open(os.path.join(dirname, "reversibility.json"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(truth_blob["reversibility"], indent=2,
                                sort_keys=True) + "\n")

    stamp = truth_blob["reversibility"]
    solve = truth_blob["solvability"]
    return {
        "world_id": spec.world_id,
        "tier": spec.tier,
        "families": list(spec.families),
        "variant_of": spec.variant_of,
        "variant_delta": spec.variant_delta,
        "grid": [spec.height, spec.width],
        "entities": len(spec.entities),
        "reachable_states": coverage["reachable_states"],
        "trace_frames": coverage["frames"],
        "budget": coverage["budget"],
        "coverage": coverage["coverage"],
        "coverage_fraction": coverage["coverage_fraction"],
        "rules_total": stamp["rules_total"],
        "rules_re_witnessable": stamp["rules_re_witnessable"],
        "rules_single_witness": stamp["rules_single_witness"],
        "reversibility_score": stamp["reversibility_score"],
        "claim_disagreements": stamp["claim_disagreements"],
        "rules_never_witnessed": sorted(coverage["rules_never_witnessed"]),
        "invariants_all_hold": truth_blob["invariants_all_hold"],
        "solvable": solve["solvable"],
        "optimal_length": solve.get("optimal_length"),
        "win_in_trace": bool(coverage["win_frames"]),
    }


def build_all(root: str = OUT, ids: Optional[Sequence[str]] = None,
              quiet: bool = False) -> Dict[str, Any]:
    specs = [BY_ID[i] for i in ids] if ids else list(CATALOGUE)
    rows: List[Dict[str, Any]] = []
    for spec in specs:
        row = build_world(spec, root)
        rows.append(row)
        if not quiet:
            print("%-24s tier=%d states=%-5d cov=%-9s rev=%.2f %s%s"
                  % (row["world_id"], row["tier"], row["reachable_states"],
                     row["coverage"], row["reversibility_score"],
                     "solvable(%s)" % row["optimal_length"] if row["solvable"]
                     else "UNSOLVABLE",
                     "  DISAGREE:%s" % ",".join(row["claim_disagreements"])
                     if row["claim_disagreements"] else ""))

    manifest = {
        "prompt_id": "C1-worldgen",
        "worlds": rows,
        "totals": {
            "worlds": len(rows),
            "tiers": {str(t): sum(1 for r in rows if r["tier"] == t) for t in (1, 2, 3)},
            "variant_pairs": sorted(r["world_id"] for r in rows if r["variant_of"]),
            "unsolvable": sorted(r["world_id"] for r in rows if not r["solvable"]),
            "mean_reversibility": round(
                sum(r["reversibility_score"] for r in rows) / max(1, len(rows)), 4),
            "invariant_failures": sorted(r["world_id"] for r in rows
                                         if not r["invariants_all_hold"]),
            "claim_disagreements": sorted(r["world_id"] for r in rows
                                          if r["claim_disagreements"]),
        },
    }
    if ids is None:
        with open(os.path.join(root, "INDEX.json"), "w",
                  encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def check_determinism(ids: Optional[Sequence[str]] = None) -> List[str]:
    """Build once more into a scratch directory and diff every byte."""
    scratch = tempfile.mkdtemp(prefix="worldgen-check-")
    try:
        build_all(scratch, ids=ids, quiet=True)
        differences: List[str] = []
        for spec in ([BY_ID[i] for i in ids] if ids else CATALOGUE):
            for name in ("raw_trace.jsonl", "spec.json", "coverage.json",
                         "ground_truth.json", "GROUND_TRUTH.md",
                         "reversibility.json"):
                a = os.path.join(OUT, spec.world_id, name)
                b = os.path.join(scratch, spec.world_id, name)
                if not os.path.exists(a):
                    differences.append("%s/%s missing from the committed build"
                                       % (spec.world_id, name))
                    continue
                with open(a, "rb") as fa, open(b, "rb") as fb:
                    if fa.read() != fb.read():
                        differences.append("%s/%s differs between runs"
                                           % (spec.world_id, name))
        return differences
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="build the worldgen catalogue")
    parser.add_argument("worlds", nargs="*")
    parser.add_argument("--check", action="store_true",
                        help="rebuild into a temp dir and diff every byte")
    args = parser.parse_args()

    write_catalogue(os.path.join(HERE, "catalog"))
    ids = args.worlds or None
    manifest = build_all(OUT, ids=ids)
    print()
    print(json.dumps(manifest["totals"], indent=2, sort_keys=True))

    if args.check:
        differences = check_determinism(ids)
        print()
        if differences:
            print("NOT DETERMINISTIC:")
            for line in differences:
                print("  " + line)
            return 1
        print("determinism: every artefact byte-identical across two builds")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
