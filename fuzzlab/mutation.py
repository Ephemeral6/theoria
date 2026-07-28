"""The mutation driver: which invariants can be made to fire, and how cheaply.

```bash
python -m fuzzlab.mutation                                  # every engine, every mutant
python -m fuzzlab.mutation --engine zero_space              # one engine
python -m fuzzlab.mutation --engine zero_space --worlds 60
python -m fuzzlab.mutation --mutant zs-drop-basis-vector -v # one mutant, verbose
```

For each mutant this runs the *same* worlds twice — once clean, once with the
defect injected — and reports, per invariant, whether it noticed.

## The four numbers, and what each is for

* **killed** — worlds where the invariant returned `violated` under the mutant.
  This is the headline. It counts only `violated`, never `raised`.
* **raised_only** — worlds where the property crashed instead of stating what
  was wrong. Detection in the weak sense. Reported apart because a battery
  whose kills are mostly crashes is one refactor away from silence, and because
  a crash carries no description of the defect into the report.
* **worlds_to_first_kill** — how many worlds had to be generated before the
  first kill. This is what licenses the campaign's *size*. If an invariant kills
  on world 1, the standing 500 are not being spent on it; if it needs 300, then
  500 is the number it earned. Both readings are useful and they point opposite
  ways.
* **inert** — worlds where the injected defect could not apply, or applied and
  changed nothing (`repr` identical). Excluded from the denominator. Without
  this column a mutant that silently failed to apply reads as a battery that
  failed to notice, and that is a fabricated finding.

## The baseline is not optional

Before any mutant runs, the same worlds are checked clean. A world that is
already `violated` without the mutant cannot say anything about the mutant, and
is dropped with a loud note rather than quietly counted as a kill. On a green
tree this set is empty — but it is the first thing to look at when it is not.

## Survivors

A mutant no invariant kills is the point of the exercise. It is *not*
automatically a defect report: it can also mean the injected behaviour was
outside anything the engine promised, in which case the mutant is wrong and not
the battery. `Mutant.claim` exists so that this can be adjudicated by reading
rather than by guessing, and `MUTATION.md` is required to say which of the two
it decided and on what evidence.
"""

import argparse
import json
import os
import sys
import time
from collections import Counter
from typing import Any, Dict, List, Optional

from fuzzlab import mutants as mut
from fuzzlab import prng, rig  # noqa: F401  (rig: path bootstrap)
from fuzzlab.props import ENGINES, finding, load
from fuzzlab.worlds import GENERATORS

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

# Smaller than the standing campaign's 500 on purpose: this measures whether an
# invariant *can* fire, and the worlds-to-first-kill column says how much of the
# 500 each one actually needs. Overridable per run.
DEFAULT_WORLDS = 40

# The campaign's seed, so a mutation world and a campaign world with the same
# index are the same world and a finding here replays there.
DEFAULT_SEED = 0x5EED_C1_E4_F0_02


def build_worlds(family: str, campaign_seed: int, n: int) -> List[Any]:
    generate = GENERATORS[family]
    worlds = []
    for index in range(n):
        seed = prng.derive(campaign_seed, family, index)
        try:
            worlds.append(generate(seed))
        except Exception:                                     # noqa: BLE001
            continue          # a generator defect is not this run's subject
    return worlds


def baseline(engine: str, worlds: List[Any]) -> Dict[int, List[str]]:
    """Invariants already violated per world with no mutant applied.

    Returns `{world_index: [invariant, ...]}`, empty on a green tree.
    """
    module = load(engine)
    dirty: Dict[int, List[str]] = {}
    for i, world in enumerate(worlds):
        bad = [f.invariant for f in module.check(world)
               if f.kind == finding.VIOLATED]
        if bad:
            dirty[i] = sorted(set(bad))
    return dirty


def run_mutant(mutant: mut.Mutant, worlds: List[Any],
               dirty: Dict[int, List[str]], verbose: bool = False) -> Dict[str, Any]:
    module = load(mutant.engine)
    invariants = sorted(module.INVARIANTS)

    killed: Counter = Counter()
    raised_only: Counter = Counter()
    first_kill: Dict[str, Optional[int]] = {name: None for name in invariants}
    inert_worlds = 0
    evaluated = 0
    confounded = 0
    started = time.time()

    for i, world in enumerate(worlds):
        if i in dirty:
            confounded += 1
            continue
        record: List[Dict[str, Any]] = []
        with mut.applied(mutant, record):
            findings = module.check(world)
        if not any(r["changed"] for r in record):
            inert_worlds += 1
            continue
        evaluated += 1
        by_kind: Dict[str, set] = {finding.VIOLATED: set(), finding.RAISED: set()}
        for f in findings:
            if f.kind in by_kind:
                by_kind[f.kind].add(f.invariant)
        for name in by_kind[finding.VIOLATED]:
            killed[name] += 1
            if first_kill[name] is None:
                first_kill[name] = evaluated
        for name in by_kind[finding.RAISED] - by_kind[finding.VIOLATED]:
            raised_only[name] += 1
        if verbose and (by_kind[finding.VIOLATED] or by_kind[finding.RAISED]):
            print("    world %3d  violated=%s raised=%s"
                  % (i, sorted(by_kind[finding.VIOLATED]),
                     sorted(by_kind[finding.RAISED])), flush=True)

    kills = {name: killed[name] for name in invariants}
    unexpected = sorted(n for n in invariants
                        if kills[n] and n not in mutant.expect_kill)
    missed = sorted(n for n in mutant.expect_kill if not kills[n])
    return {
        "id": mutant.id,
        "engine": mutant.engine,
        "seam": mutant.seam,
        "kind": mutant.kind,
        "claim": mutant.claim,
        "description": mutant.description,
        "expect_kill": list(mutant.expect_kill),
        "worlds_offered": len(worlds),
        "worlds_evaluated": evaluated,
        "worlds_inert": inert_worlds,
        "worlds_confounded": confounded,
        "killed": kills,
        "raised_only": {name: raised_only[name] for name in invariants},
        "worlds_to_first_kill": first_kill,
        "survived": not any(kills.values()),
        "survived_all_detection": not any(kills.values())
        and not any(raised_only.values()),
        "unexpected_kills": unexpected,
        "predicted_but_missed": missed,
        "elapsed_s": round(time.time() - started, 2),
    }


def run(engines: List[str], n_worlds: int, campaign_seed: int,
        only_mutant: Optional[str] = None, verbose: bool = False) -> Dict[str, Any]:
    catalog = mut.catalog()
    if only_mutant:
        catalog = [m for m in catalog if m.id == only_mutant]
        if not catalog:
            raise SystemExit("no mutant with id %r" % only_mutant)
        engines = sorted({m.engine for m in catalog})

    results: List[Dict[str, Any]] = []
    coverage: Dict[str, Dict[str, Any]] = {}
    for engine in engines:
        here = [m for m in catalog if m.engine == engine]
        module = load(engine)
        invariants = sorted(module.INVARIANTS)
        if not here:
            coverage[engine] = {"invariants": invariants, "mutants": 0,
                               "note": "no mutant catalogue for this engine"}
            print("%-15s  NO MUTANTS -- %d invariants unmeasured"
                  % (engine, len(invariants)), flush=True)
            continue
        worlds = build_worlds(module.FAMILY, campaign_seed, n_worlds)
        dirty = baseline(engine, worlds)
        if dirty:
            print("%-15s  BASELINE NOT CLEAN on %d/%d worlds: %s"
                  % (engine, len(dirty), len(worlds),
                     sorted({n for v in dirty.values() for n in v})), flush=True)
        print("%-15s  %d mutants over %d worlds"
              % (engine, len(here), len(worlds)), flush=True)
        for mutant in here:
            row = run_mutant(mutant, worlds, dirty, verbose)
            results.append(row)
            verdict = ("SURVIVED" if row["survived"] else
                       "killed by %s" % ",".join(
                           n for n, k in sorted(row["killed"].items()) if k))
            print("  %-32s %-12s eval=%-4d inert=%-4d %s"
                  % (mutant.id, mutant.kind, row["worlds_evaluated"],
                     row["worlds_inert"], verdict), flush=True)
        never = [n for n in invariants
                 if not any(r["killed"].get(n) for r in results
                            if r["engine"] == engine)]
        coverage[engine] = {
            "invariants": invariants,
            "mutants": len(here),
            "baseline_dirty_worlds": len(dirty),
            "invariants_no_mutant_kills": never,
        }
    return {
        "campaign_seed": campaign_seed,
        "campaign_seed_hex": "0x%016x" % campaign_seed,
        "worlds_per_engine": n_worlds,
        "engine_rig_head": rig.engine_rig_head(),
        "mutants": results,
        "coverage": coverage,
    }


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--engine", default=None, choices=list(ENGINES))
    ap.add_argument("--mutant", default=None, help="run one mutant by id")
    ap.add_argument("--worlds", type=int, default=DEFAULT_WORLDS)
    ap.add_argument("--seed", type=lambda s: int(s, 0), default=DEFAULT_SEED)
    ap.add_argument("-v", "--verbose", action="store_true")
    ap.add_argument("--out", default=None, help="where to write the JSON report")
    a = ap.parse_args(argv)

    engines = [a.engine] if a.engine else list(ENGINES)
    report = run(engines, a.worlds, a.seed, a.mutant, a.verbose)

    os.makedirs(OUT, exist_ok=True)
    name = a.out or os.path.join(
        OUT, "mutation.%s.json" % (a.engine or "all"))
    with open(name, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print("\nwrote %s" % name)

    survivors = [r for r in report["mutants"] if r["survived"]]
    blind = {e: c.get("invariants_no_mutant_kills", [])
             for e, c in report["coverage"].items()}
    print("mutants: %d   survivors: %d" % (len(report["mutants"]), len(survivors)))
    for engine, names in sorted(blind.items()):
        if names:
            print("  %-15s no mutant kills: %s" % (engine, ", ".join(names)))
    # Exit code is about the run, not the finding: survivors are the result, not
    # a failure. A non-zero here would make a CI hook hide the interesting case.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
