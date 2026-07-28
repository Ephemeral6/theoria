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
import subprocess
import sys
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
    corr = truth_blob["rule_correspondence"]
    return {
        "world_id": spec.world_id,
        "tier": spec.tier,
        "rule_correspondence_agrees": corr["agrees"],
        "declared_never_fires": corr["declared_never_fires"],
        "fired_undeclared": corr["fired_undeclared"],
        "dormant_clauses": corr["dormant_clauses"],
        "intended_solvable": spec.intended_solvable,
        "frame_determines_state": truth_blob["frame_determines_state"]["injective"],
        "distinct_frames": truth_blob["frame_determines_state"]["distinct_frames"],
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
        # The name says "never witnessed" and the value is the rules that still
        # have *uncovered firing pairs* at this budget — a rule can be witnessed
        # forty times and still appear here.  Kept under both names for one
        # release: the old key so nothing downstream breaks on the rename, the
        # accurate one because the old one reads as a defect report and is not.
        "rules_never_witnessed": sorted(coverage["rules_never_witnessed"]),
        "rules_with_uncovered_pairs": sorted(coverage["rules_never_witnessed"]),
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
            "rule_correspondence_failures": sorted(
                r["world_id"] for r in rows if not r["rule_correspondence_agrees"]),
            "frame_collisions": sorted(
                r["world_id"] for r in rows if not r["frame_determines_state"]),
            "solvability_intent_failures": sorted(
                r["world_id"] for r in rows
                if r["intended_solvable"] is not None
                and r["intended_solvable"] != r["solvable"]),
        },
    }
    if ids is None:
        with open(os.path.join(root, "INDEX.json"), "w",
                  encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


GATES = (
    ("frame_collisions",
     "two distinct reachable states render to the same frame — the world is not "
     "learnable from its own trace"),
    ("solvability_intent_failures",
     "a world's measured solvability contradicts the spec's `intended_solvable`"),
    ("rule_correspondence_failures",
     "a declared primary rule never fires, or a fired tag is undeclared"),
    ("invariant_failures", "a declared invariant is violated on a reachable state"),
    ("claim_disagreements",
     "a mechanism's `reversible` claim contradicts the measured stamp"),
)


def gate_failures(manifest: Dict[str, Any]) -> List[str]:
    """The build's own acceptance conditions, as blocking checks.

    Every one of these was already *computed* and printed by the previous
    version, which then returned 0. Seven of twenty worlds shipped with
    `claim_disagreements` and one with a violated invariant, and because the
    noise was constant nobody could have told a real disagreement from it. A
    measurement nothing can fail is a decoration.
    """
    out: List[str] = []
    totals = manifest["totals"]
    for key, why in GATES:
        for world_id in totals.get(key, ()):
            out.append("%-24s %s (%s)" % (world_id, why, key))
    return out


def check_determinism(ids: Optional[Sequence[str]] = None) -> List[str]:
    """Rebuild in a **fresh interpreter** and diff every byte.

    The earlier version built the comparison copy in this same process, so
    `PYTHONHASHSEED` was shared with the build it was checking against and the
    one class of nondeterminism it exists to find — set and dict iteration order
    reaching an output — was invisible to it. It also diffed against the module
    constant `OUT` rather than the root it had been asked to build.

    A subprocess with a different seed fixes both. Determinism here is real
    (verified across three seeds), but a gate that cannot fail is not a gate.
    """
    scratch = tempfile.mkdtemp(prefix="worldgen-check-")
    try:
        env = dict(os.environ, PYTHONHASHSEED="271828")
        command = [sys.executable, "-m", "worldgen.build", "--into", scratch, "--quiet"]
        if ids:
            command.extend(ids)
        proc = subprocess.run(command, cwd=os.path.dirname(HERE), env=env,
                              capture_output=True)
        if proc.returncode != 0:
            tail = (proc.stdout + proc.stderr).decode("utf-8", "replace").strip()
            return ["the comparison build failed:\n" + tail[-2000:]]

        differences: List[str] = []
        for spec in ([BY_ID[i] for i in ids] if ids else CATALOGUE):
            for name in ("raw_trace.jsonl", "spec.json", "coverage.json",
                         "ground_truth.json", "GROUND_TRUTH.md",
                         "reversibility.json"):
                a = os.path.join(OUT, spec.world_id, name)
                b = os.path.join(scratch, spec.world_id, name)
                if not os.path.exists(b):
                    differences.append("%s/%s missing from the comparison build"
                                       % (spec.world_id, name))
                    continue
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
                        help="also rebuild in a fresh interpreter and diff every byte")
    parser.add_argument("--into", default=OUT,
                        help="build root (used by --check's comparison build)")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    into_default = os.path.abspath(args.into) == os.path.abspath(OUT)
    if into_default:
        write_catalogue(os.path.join(HERE, "catalog"))
    ids = args.worlds or None
    manifest = build_all(args.into, ids=ids, quiet=args.quiet)
    if not args.quiet:
        print()
        print(json.dumps(manifest["totals"], indent=2, sort_keys=True))

    failures = gate_failures(manifest)
    if failures:
        print()
        print("BUILD GATE FAILED:")
        for line in failures:
            print("  " + line)
        return 1

    if args.check and into_default:
        differences = check_determinism(ids)
        print()
        if differences:
            print("NOT DETERMINISTIC:")
            for line in differences:
                print("  " + line)
            return 1
        print("determinism: every artefact byte-identical across two builds "
              "in separate interpreters at different PYTHONHASHSEED")
    if not args.quiet:
        print("build gate: %d world(s) green" % len(manifest["worlds"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
