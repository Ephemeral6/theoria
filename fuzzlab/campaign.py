"""The battery: N random worlds per family, every invariant, ranked findings.

```bash
python -m fuzzlab.campaign                     # the standing campaign, 500 worlds
python -m fuzzlab.campaign --worlds 40         # a quick pass
python -m fuzzlab.campaign --engine zero_space --worlds 200
python -m fuzzlab.campaign --replay 0x9e3779b97f4a7c15 --family gridworld
```

Three things this driver refuses to do, each because the opposite makes a green
campaign meaningless:

* **it does not stop at the first failure.** A property run returns findings, not
  assertions (`props/finding.py`), so 500 worlds always finish and the report
  ranks what was seen. One loud world hiding four quiet ones is the normal way a
  fuzz campaign lies;
* **it does not silently drop a world its oracle cannot handle.** Those are
  `skipped` findings with a reason, and the report counts them separately from
  passes. A campaign that quietly narrows to the cases it can check reports
  coverage it did not earn;
* **it does not count a world as covered unless an invariant actually ran on
  it.** `worlds_generated` and `worlds_checked` are reported separately, per
  engine, and they are allowed to differ.

The seed table is the whole point of the exercise: every world's `(family, seed,
fingerprint, spec)` goes to `out/seeds.jsonl`, so any row replays with
`--replay`. If a replay regenerates a *different* world the fingerprint catches
it, rather than a property mysteriously flipping.
"""

import argparse
import json
import os
import sys
import time
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional, Sequence

from fuzzlab import prng, rig
from fuzzlab.props import ENGINES, finding, load
from fuzzlab.worlds import GENERATORS

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

# The standing campaign. 500 worlds is the item's floor, and it is spent per
# *engine* rather than per family so that the two engines sharing `gridworld`
# each get a full budget rather than half of one.
DEFAULT_WORLDS = 500
DEFAULT_SEED = 0x5EED_C1_E4_F0_02


def engines_for(only: Optional[str]) -> List[str]:
    if only is None:
        return list(ENGINES)
    if only not in ENGINES:
        raise SystemExit("unknown engine %r; known: %s" % (only, ", ".join(ENGINES)))
    return [only]


def run_engine(engine: str, campaign_seed: int, n_worlds: int,
               quiet: bool = False) -> Dict[str, Any]:
    module = load(engine)
    family = module.FAMILY
    generate = GENERATORS[family]

    findings: List[finding.Finding] = []
    rows: List[Dict[str, Any]] = []
    checked = 0
    generator_errors: List[Dict[str, Any]] = []
    started = time.time()

    for index in range(n_worlds):
        seed = prng.derive(campaign_seed, family, index)
        try:
            world = generate(seed)
        except Exception as exc:                              # noqa: BLE001
            # A generator that cannot build its own world is a fuzzlab defect,
            # not an engine one, and must not be filed as an engine finding.
            generator_errors.append({"family": family, "seed": seed,
                                     "error": "%s: %s" % (type(exc).__name__, exc)})
            continue
        rows.append(dict(world.row(), engine=engine, index=index))
        findings.extend(module.check(world))
        checked += 1

    kinds = Counter(f.kind for f in findings)
    by_invariant: Dict[str, Counter] = {}
    for f in findings:
        by_invariant.setdefault(f.invariant, Counter())[f.kind] += 1

    invariants = sorted(module.INVARIANTS)

    # --- worlds, counted as worlds
    #
    # These columns are named `..._worlds_...` and they must therefore count
    # *worlds*, which means counting distinct seeds and not findings.  Until an
    # adversarial pass on V-21 this subtracted the skip **finding** count, and
    # the two are equal only if no invariant ever files two skips for one world.
    # `props/cegis_miner.py:frontier_is_complete_to_size` files one per rule
    # inside a loop, so they are not equal: forcing that budget low enough to
    # fire produced `invariant_worlds_evaluated: -56` over 12 worlds. The
    # arithmetic had been right since V-13 only because the one property that
    # can file several skips per world had never been made to.
    skipped_seeds: Dict[str, set] = {name: set() for name in invariants}
    unavailable_seeds: Dict[str, set] = {name: set() for name in invariants}
    for f in findings:
        if f.kind != finding.SKIPPED:
            continue
        skipped_seeds.setdefault(f.invariant, set()).add(f.seed)
        if f.cause_class == finding.UNAVAILABLE:
            unavailable_seeds.setdefault(f.invariant, set()).add(f.seed)
    ran = {name: n_worlds - len(skipped_seeds.get(name, ())) for name in invariants}

    # --- why the unevaluated worlds were unevaluated (V-21)
    #
    # `invariant_worlds_evaluated` says how many worlds an invariant judged.  It
    # cannot say *why* it judged the rest -- and the two reasons point opposite
    # ways.  "The engine looked and correctly declined" is the battery working;
    # "HiGHS ran out of iterations" is nobody knowing.  Summed into one `skipped`
    # they cancel, which is how a solver failure spent one release looking like
    # coverage.  So the breakdown is published per invariant, by cause and by
    # cause-class, and `invariant_worlds_unavailable` is lifted out as its own
    # column because it is the one that should always be zero.
    #
    # `skips_by_cause` and `skips_by_cause_class` count **findings** -- they are
    # a breakdown of `skipped`, and their name says so. `invariant_worlds_*`
    # count **worlds**. The two are equal whenever a property files at most one
    # skip per world, which is true of everything except
    # `cegis_miner.frontier_is_complete_to_size`, and relying on it silently is
    # what produced a negative coverage column. `skip_worlds_by_cause_class` is
    # published alongside so a reader can see where the two differ instead of
    # assuming they do not.
    by_cause: Dict[str, Dict[str, int]] = {name: {} for name in invariants}
    by_cause_class: Dict[str, Dict[str, int]] = {name: {} for name in invariants}
    class_seeds: Dict[str, Dict[str, set]] = {name: {} for name in invariants}
    for f in findings:
        if f.kind != finding.SKIPPED:
            continue
        bucket = by_cause.setdefault(f.invariant, {})
        bucket[f.cause] = bucket.get(f.cause, 0) + 1
        klass = by_cause_class.setdefault(f.invariant, {})
        klass[f.cause_class] = klass.get(f.cause_class, 0) + 1
        class_seeds.setdefault(f.invariant, {}).setdefault(
            f.cause_class, set()).add(f.seed)
    unavailable = {name: len(unavailable_seeds.get(name, ()))
                   for name in invariants}

    report = {
        "engine": engine,
        "family": family,
        "invariants": invariants,
        "n_invariants": len(invariants),
        "worlds_generated": len(rows),
        "worlds_checked": checked,
        "worlds_requested": n_worlds,
        "generator_errors": generator_errors,
        "violated": kinds[finding.VIOLATED],
        "raised": kinds[finding.RAISED],
        "skipped": kinds[finding.SKIPPED],
        "unavailable": sum(unavailable.values()),
        "invariant_worlds_evaluated": ran,
        "invariant_worlds_unavailable": unavailable,
        "invariant_worlds_skipped": {name: len(skipped_seeds.get(name, ()))
                                     for name in invariants},
        "skips_by_cause": {k: dict(sorted(v.items()))
                           for k, v in sorted(by_cause.items())},
        "skips_by_cause_class": {k: dict(sorted(v.items()))
                                 for k, v in sorted(by_cause_class.items())},
        "skip_worlds_by_cause_class": {
            k: {klass: len(seeds) for klass, seeds in sorted(v.items())}
            for k, v in sorted(class_seeds.items())},
        "elapsed_s": round(time.time() - started, 2),
    }
    if not quiet:
        print("%-15s %-12s %3d inv  %4d worlds  violated=%-4d raised=%-4d "
              "skipped=%-5d unavail=%-4d %5.1fs"
              % (engine, family, len(invariants), checked, report["violated"],
                 report["raised"], report["skipped"], report["unavailable"],
                 report["elapsed_s"]),
              flush=True)
    return {"report": report, "findings": findings, "rows": rows}


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="fuzzlab property campaign")
    parser.add_argument("--worlds", type=int, default=DEFAULT_WORLDS,
                        help="worlds per engine (default %d)" % DEFAULT_WORLDS)
    parser.add_argument("--seed", type=lambda s: int(s, 0), default=DEFAULT_SEED)
    parser.add_argument("--engine", default=None)
    parser.add_argument("--out", default=OUT)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    os.makedirs(args.out, exist_ok=True)
    engines = engines_for(args.engine)
    if not args.quiet:
        print("campaign seed 0x%016x, %d worlds per engine, engine-rig %s"
              % (args.seed, args.worlds, rig.engine_rig_head()))
        print()

    reports: List[Dict[str, Any]] = []
    all_findings: List[finding.Finding] = []
    seed_rows: List[Dict[str, Any]] = []
    for engine in engines:
        result = run_engine(engine, args.seed, args.worlds, quiet=args.quiet)
        reports.append(result["report"])
        all_findings.extend(result["findings"])
        seed_rows.extend(result["rows"])

    with open(os.path.join(args.out, "seeds.jsonl"), "w",
              encoding="utf-8", newline="\n") as handle:
        for row in seed_rows:
            handle.write(json.dumps(row, sort_keys=True,
                                    separators=(",", ":")) + "\n")
    with open(os.path.join(args.out, "findings.jsonl"), "w",
              encoding="utf-8", newline="\n") as handle:
        for f in all_findings:
            handle.write(json.dumps(f.json(), sort_keys=True,
                                    separators=(",", ":")) + "\n")

    violated = [f for f in all_findings if f.kind == finding.VIOLATED]
    raised = [f for f in all_findings if f.kind == finding.RAISED]
    summary = {
        "prompt_id": "E4-property-fuzz",
        "campaign_seed": "0x%016x" % args.seed,
        "worlds_per_engine": args.worlds,
        "engine_rig_head": rig.engine_rig_head(),
        "engines": reports,
        "totals": {
            "worlds_checked": sum(r["worlds_checked"] for r in reports),
            "invariants": sum(r["n_invariants"] for r in reports),
            "violated": len(violated),
            "raised": len(raised),
            "skipped": sum(r["skipped"] for r in reports),
            # The number this item exists to make readable: worlds that went
            # unjudged because a tool could not compute.  It is not `skipped`
            # (most skips are the engine correctly declining) and it is not zero
            # by construction -- when it is non-zero the run measured less than
            # it claims to, and `tests/test_battery.py` fails on it.
            "unavailable": sum(r["unavailable"] for r in reports),
            "generator_errors": sum(len(r["generator_errors"]) for r in reports),
        },
        "violations_by_invariant": _tally(violated),
        "raises_by_invariant": _tally(raised),
        "skips_by_cause": _tally_causes(all_findings),
    }
    with open(os.path.join(args.out, "campaign.json"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    if not args.quiet:
        print()
        print(json.dumps(summary["totals"], indent=2, sort_keys=True))
        for label, group in (("VIOLATED", violated), ("RAISED", raised)):
            if not group:
                continue
            print()
            print("%s (%d), first of each kind:" % (label, len(group)))
            seen = set()
            for f in group:
                key = (f.engine, f.invariant)
                if key in seen:
                    continue
                seen.add(key)
                print("  " + str(f))
        print()
        print("-> %s" % os.path.relpath(os.path.join(args.out, "campaign.json"), HERE))

    # A violation is the campaign's *product*, not its failure: "失败是战利品".
    # The exit code is about whether the battery ran — about the instrument, not
    # the reading — so a violation exits 0.
    #
    # `unavailable` is on the instrument side of that line and therefore exits
    # non-zero (V-21). A world that went unjudged because a tool could not
    # compute is not a reading at all: the campaign reports coverage it did not
    # earn, and every downstream number is drawn from a smaller sample than it
    # says. An adversarial pass found the previous arrangement — the number
    # printed, nothing failing — reproducing this item's own defect at the level
    # of the report: three docstrings claimed "the suite fails on it" and only a
    # 25-world pytest run did, while the 500-world artifact anyone actually reads
    # could carry `unavailable > 0` past a green `verify`.
    totals = summary["totals"]
    return 1 if (totals["generator_errors"] or totals["unavailable"]) else 0


def _tally(findings: Iterable[finding.Finding]) -> Dict[str, int]:
    counter = Counter("%s.%s" % (f.engine, f.invariant) for f in findings)
    return dict(sorted(counter.items()))


def _tally_causes(findings: Iterable[finding.Finding]) -> Dict[str, int]:
    """`{engine.invariant.cause: n}` over every skip, cause-class first.

    Keyed by class so the file sorts the interesting rows together: every
    `unavailable.*` line is a world nobody judged and nobody can attribute, and
    scanning for the prefix is the whole audit.
    """
    counter = Counter(
        "%s.%s.%s.%s" % (f.cause_class, f.engine, f.invariant, f.cause)
        for f in findings if f.kind == finding.SKIPPED)
    return dict(sorted(counter.items()))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:] or None))
