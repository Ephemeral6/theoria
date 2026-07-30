"""The BEFORE measurement, run against unmodified `fuzzlab/` at base commit.

What it establishes, in numbers rather than in prose:

1. `LpUnavailable` is not caught anywhere in `props/lp_potential.py`, so it
   escapes to `finding.run_invariants` and is recorded as `raised`;
2. `campaign.json`'s `invariant_worlds_evaluated` subtracts only `skipped`, so
   every such world is counted as **evaluated** -- byte-identical in that column
   to a world the invariant checked and found clean;
3. `finding.failures()` returns only `VIOLATED`, so none of it fails anything.

Together: "the solver could not compute" and "I checked and it was fine" are the
same result. That is the item.

The lever is a **real** HiGHS iteration limit (`maxiter=0`) handed to the real
`scipy.optimize.linprog` through E15's `solver_options`, injected at fuzzlab's
own seam (`props/lp_potential._solve`) so `engine-rig` is untouched -- the same
seam and the same house rule the mutation battery uses.

    python -m fuzzlab.runs...before_probe        # or just: python before_probe.py
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fuzzlab import campaign                                    # noqa: E402
from fuzzlab.props import finding                               # noqa: E402
import fuzzlab.props.lp_potential as props                      # noqa: E402

WORLDS = 12
SOLVER_OPTIONS = {"maxiter": 0}


def starved(world):
    """The engine, on the real graph, with a real zero-iteration budget."""
    from engines import lp_potential as engine
    return engine.run(world.graph, world.initial,
                      goal_states=list(world.goal_states),
                      solver_options=SOLVER_OPTIONS)


def main() -> int:
    live = campaign.run_engine("lp_potential", campaign.DEFAULT_SEED, WORLDS,
                               quiet=True)

    original = props._solve
    props._solve = starved
    try:
        starved_run = campaign.run_engine("lp_potential", campaign.DEFAULT_SEED,
                                          WORLDS, quiet=True)
    finally:
        props._solve = original

    kinds = {}
    for f in starved_run["findings"]:
        kinds[f.kind] = kinds.get(f.kind, 0) + 1

    report = {
        "worlds": WORLDS,
        "solver_options": SOLVER_OPTIONS,
        "live": {
            "kinds": {k: sum(1 for f in live["findings"] if f.kind == k)
                      for k in ("violated", "raised", "skipped")},
            "invariant_worlds_evaluated":
                live["report"]["invariant_worlds_evaluated"],
        },
        "starved": {
            "kinds": kinds,
            "invariant_worlds_evaluated":
                starved_run["report"]["invariant_worlds_evaluated"],
            "first_finding": str(starved_run["findings"][0])
                             if starved_run["findings"] else None,
            "failures_len": len(finding.failures(starved_run["findings"])),
        },
    }
    ev = report["starved"]["invariant_worlds_evaluated"]
    report["verdict"] = {
        "every_world_still_counted_as_evaluated":
            all(v == WORLDS for v in ev.values()),
        "nothing_fails": report["starved"]["failures_len"] == 0,
        "reading": (
            "with the solver starved of every iteration, the battery reports "
            "%d evaluated worlds per invariant -- the same number as a clean "
            "run would -- and %d failures. The unavailability is invisible in "
            "the coverage column and inert in the gate."
            % (max(ev.values()), report["starved"]["failures_len"])),
    }

    out = os.path.join(HERE, "before.json")
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
