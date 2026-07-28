"""Shrink a failing world, then archive it.  失败是战利品.

```bash
python -m fuzzlab.minimize --engine zero_space --invariant laws_hold_on_trajectory
python -m fuzzlab.minimize --engine mdl_segmenter --invariant covers_every_pixel --pool 4000
```

**This is minimisation by search, and it is called that rather than
delta-debugging, because it is not delta-debugging.** A world here is a pure
function of a 64-bit seed — `generate(seed)` draws every parameter from the
stream — so there is no handle to shrink: perturbing a seed does not perturb a
world, it replaces it. Classic shrinking needs `generate(spec)`, and the
generators do not offer one.

What is available is cheap and, for this purpose, enough: draw a large pool of
seeds, keep every one that reproduces **the same `(engine, invariant)`
finding**, and return the one whose world is smallest under a stated size
metric. That yields a small, exactly-replayable reproducer, which is what a bug
report needs. What it does *not* yield is a *minimal* one, and the archive says
so in as many words rather than implying a guarantee the method cannot make.

The size metric is per family and deliberately crude — the number of things a
reader has to hold in their head. It is recorded with the reproducer so that a
future run can rank against the same ruler.
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional, Sequence

from fuzzlab import campaign, prng
from fuzzlab.props import finding, load
from fuzzlab.worlds import GENERATORS

HERE = os.path.dirname(os.path.abspath(__file__))
ARCHIVE = os.path.join(HERE, "archive")

DEFAULT_POOL = 2000


def size_of(world: Any) -> int:
    """How much world a reader has to hold in their head.

    Crude on purpose: a reproducer is useful when it is small enough to read,
    and any monotone proxy for that gets there. Falls back to the length of the
    canonical spec so a family added later still ranks without editing this.
    """
    spec = world.spec_json()
    family = world.family
    if family == "gridworld":
        return (spec["height"] * spec["width"]
                + 4 * len(spec.get("obstacles") or ())
                + 2 * spec.get("n_frames", 0))
    if family == "parityworld":
        return (spec["n_cells"] * len(spec.get("colors") or ())
                + 2 * len(spec.get("operations") or ())
                + len(spec.get("script") or ()))
    if family == "jumpgraph":
        return 4 * spec["n_pos"] + len(spec.get("triples") or ())
    if family == "blockworld":
        detail = spec.get("detail") or {}
        return (detail.get("height", 0) * detail.get("width", 0)
                + 4 * len(detail.get("boxes") or ())
                + 4 * len(detail.get("goals") or ())
                + 3 * len(detail.get("atoms") or ())
                + 3 * len(detail.get("actions") or ()))
    if family == "hypset":
        return (3 * len(spec.get("hypothesis_ids") or ())
                + 2 * len(spec.get("actions") or ())
                + len(spec.get("observations") or ()))
    return len(json.dumps(spec, sort_keys=True))


def signature(f: finding.Finding) -> str:
    return "%s.%s.%s" % (f.engine, f.invariant, f.kind)


def search(engine: str, invariant: str, kind: str, pool: int,
           campaign_seed: int, quiet: bool = False) -> Dict[str, Any]:
    module = load(engine)
    family = module.FAMILY
    generate = GENERATORS[family]
    want = "%s.%s.%s" % (engine, invariant, kind)

    hits: List[Dict[str, Any]] = []
    scanned = 0
    for index in range(pool):
        seed = prng.derive(campaign_seed, family, index)
        try:
            world = generate(seed)
        except Exception:                                     # noqa: BLE001
            continue
        scanned += 1
        matching = [f for f in finding.run_invariants(engine, world,
                                                      module.INVARIANTS,
                                                      only=[invariant])
                    if signature(f) == want]
        if matching:
            hits.append({"seed": seed, "size": size_of(world), "world": world,
                         "index": index, "finding": matching[0]})
            if not quiet and len(hits) <= 3:
                print("  hit at index %d (seed 0x%016x, size %d)"
                      % (index, seed, hits[-1]["size"]), flush=True)

    if not hits:
        return {"found": False, "scanned": scanned, "signature": want}

    best = min(hits, key=lambda h: (h["size"], h["seed"]))
    return {
        "found": True,
        "signature": want,
        "scanned": scanned,
        "reproducers": len(hits),
        "rate": round(len(hits) / max(1, scanned), 6),
        "smallest": {
            "family": family,
            "seed": "0x%016x" % best["seed"],
            "seed_int": best["seed"],
            "index": best["index"],
            "size": best["size"],
            "size_metric": "fuzzlab.minimize.size_of, family %s" % family,
            "fingerprint": best["world"].fingerprint(),
            "spec": best["world"].spec_json(),
            "finding": best["finding"].json(),
        },
        "method": "minimisation by search over a pool of %d seeds — the smallest "
                  "world that reproduces this signature, NOT a proven minimum; "
                  "worlds are pure functions of a seed so there is no parameter "
                  "to shrink" % pool,
        "replay": "python -m fuzzlab.minimize --replay 0x%016x --family %s "
                  "--engine %s --invariant %s" % (best["seed"], family, engine,
                                                  invariant),
    }


def replay(family: str, seed: int, engine: str,
           invariant: Optional[str] = None) -> Dict[str, Any]:
    world = GENERATORS[family](seed)
    module = load(engine)
    found = finding.run_invariants(engine, world, module.INVARIANTS,
                                   only=[invariant] if invariant else None)
    return {
        "family": family,
        "seed": "0x%016x" % seed,
        "fingerprint": world.fingerprint(),
        "spec": world.spec_json(),
        "findings": [f.json() for f in found],
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="shrink and archive a failing world")
    parser.add_argument("--engine", required=True)
    parser.add_argument("--invariant", required=True)
    parser.add_argument("--kind", default=finding.VIOLATED,
                        choices=(finding.VIOLATED, finding.RAISED, finding.SKIPPED))
    parser.add_argument("--pool", type=int, default=DEFAULT_POOL)
    parser.add_argument("--seed", type=lambda s: int(s, 0),
                        default=campaign.DEFAULT_SEED)
    parser.add_argument("--replay", type=lambda s: int(s, 0), default=None)
    parser.add_argument("--family", default=None)
    parser.add_argument("--archive", default=ARCHIVE)
    args = parser.parse_args(argv)

    if args.replay is not None:
        family = args.family or load(args.engine).FAMILY
        print(json.dumps(replay(family, args.replay, args.engine, args.invariant),
                         indent=2, sort_keys=True))
        return 0

    print("searching %d seeds for %s.%s.%s"
          % (args.pool, args.engine, args.invariant, args.kind), flush=True)
    result = search(args.engine, args.invariant, args.kind, args.pool, args.seed)
    if not result["found"]:
        print("no world in %d reproduced %s" % (result["scanned"],
                                                result["signature"]))
        return 1

    os.makedirs(args.archive, exist_ok=True)
    name = "%s.%s.%s.json" % (args.engine, args.invariant, args.kind)
    path = os.path.join(args.archive, name)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "smallest"},
                     indent=2, sort_keys=True))
    print("smallest: size %d, seed %s" % (result["smallest"]["size"],
                                          result["smallest"]["seed"]))
    print("-> %s" % os.path.relpath(path, HERE))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:] or None))
