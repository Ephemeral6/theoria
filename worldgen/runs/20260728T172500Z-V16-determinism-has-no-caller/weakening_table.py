"""Does the negative control bite?  Weaken the gate and see what gets past.

    python worldgen/runs/<this dir>/weakening_table.py

A negative control that fires is not yet evidence that the *gate* is awake — it
could be firing because the sandbox is broken.  The discriminating experiment is
to leave the injection exactly where it is and weaken `check_determinism`
instead: if the same defect now walks through, the red was the gate's.

Three weakenings, each one a change a reviewer could plausibly wave through, and
one of them (`shared_hashseed`) is the gate as it actually stood before C1's F7.

**Every cell is a rate, not a verdict.**  Two of them are genuinely
probabilistic and the first version of this script published both as settled
facts:

* `mechanism_order` binds three mechanisms on `t3-latch-maze`, so set iteration
  has six orders and roughly one parent seed in six agrees with the gate's
  hardcoded `271828` and cannot see the defect at all.
* `unseeded_rng` under `size_only` depends on whether two random floats happen
  to have the same `repr` length, which they do about half the time.

So each cell is sampled over several distinct parent seeds and reported as
`RED (n/m seeds)`.  Prose calling this "reproducible rather than guaranteed" is
not enough: the table is the artefact people copy.

**A cell counts as RED only if the gate named a differing artefact.**  Not
merely a non-zero exit, and not merely the banner: `build.py:251-253` prints
`NOT DETERMINISTIC:` for a comparison subprocess that *failed to build*, so a
crash wearing the banner would otherwise be scored as a catch — the exact
confusion this experiment exists to rule out.  The first version of this script
scored on `returncode != 0 and banner in out` and had that hole.

Writes `weakening_table.md` and `weakening_table.json` next to this file.  No
wall-clock timing is recorded: this is an artefact about byte determinism.
"""

import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)

from worldgen.tests import determinism_sandbox as ds  # noqa: E402

COLUMNS = ("none",) + tuple(ds.WEAKENINGS)

#: Parent seeds each cell is sampled at.  `271828` is deliberately absent: the
#: gate pins its comparison build there, so that seed makes parent and child
#: agree by construction and is not a case this table is about.
SEEDS = tuple(str(s) for s in range(1, 31))
SEEDS_PER_CELL = {"none": 30}
DEFAULT_SEEDS_PER_CELL = 10


def one_run(injection, weakening, seed):
    root = tempfile.mkdtemp(prefix="v16-weak-")
    try:
        ds.make_sandbox(root, injection.name,
                        None if weakening == "none" else weakening)
        proc = ds.run_gate(root, injection.world, seed=seed)
        out = ds.text(proc)
        named = sorted(line.split("/")[-1].split(" differs")[0].strip()
                       for line in out.splitlines() if "differs between runs" in line)
        crashed = "the comparison build failed" in out
        # RED requires a *named artefact*, not just the banner.  See docstring.
        red = proc.returncode != 0 and ds.RED_BANNER in out and bool(named)
        return {"seed": seed, "returncode": proc.returncode, "red": red,
                "banner": ds.RED_BANNER in out,
                "comparison_build_crashed": crashed, "artefacts": named}
    finally:
        shutil.rmtree(root, ignore_errors=True)


def cell(injection, weakening):
    n = SEEDS_PER_CELL.get(weakening, DEFAULT_SEEDS_PER_CELL)
    runs = [one_run(injection, weakening, seed) for seed in SEEDS[:n]]
    reds = sum(1 for r in runs if r["red"])
    crashes = sum(1 for r in runs if r["comparison_build_crashed"])
    artefacts = sorted({name for r in runs for name in r["artefacts"]})
    return {"runs": runs, "red": reds, "total": len(runs),
            "comparison_build_crashes": crashes, "artefacts": artefacts,
            "verdict": "RED" if reds == len(runs) else
                       ("MISSED" if reds == 0 else "MIXED")}


def render(reds, total):
    if reds == total:
        return "**RED** (%d/%d)" % (reds, total)
    if reds == 0:
        return "MISSED (0/%d)" % total
    return "**RED (%d/%d seeds)**" % (reds, total)


def main() -> int:
    grid = {}
    for injection in ds.INJECTIONS:
        for weakening in COLUMNS:
            got = cell(injection, weakening)
            grid["%s/%s" % (injection.name, weakening)] = got
            print("%-18s %-16s %-6s %d/%d  crashes=%d  %s"
                  % (injection.name, weakening, got["verdict"], got["red"],
                     got["total"], got["comparison_build_crashes"],
                     ",".join(got["artefacts"])))

    lines = [
        "# V16 — the negative control, weakened", "",
        "Each cell is `n/m` over `m` distinct parent `PYTHONHASHSEED` values "
        "(1..m); the gate pins its own comparison build at `271828`.", "",
        "**RED** = `build --check` exited non-zero, printed `NOT DETERMINISTIC:` "
        "**and named at least one artefact as differing**. The third condition "
        "is not redundant: `build.py:251-253` prints the same banner when the "
        "comparison subprocess merely failed to build, so without it a crash "
        "scores as a catch.  **MISSED** = the injected defect got past.", "",
        "| injection | class | " + " | ".join(COLUMNS) + " |",
        "|---" * (len(COLUMNS) + 2) + "|",
    ]
    for injection in ds.INJECTIONS:
        klass = "A" if injection.klass == ds.CLASS_A else "B"
        row = ["`%s`" % injection.name, klass]
        for weakening in COLUMNS:
            got = grid["%s/%s" % (injection.name, weakening)]
            row.append(render(got["red"], got["total"]))
        lines.append("| " + " | ".join(row) + " |")

    lines += [
        "", "## The two classes are not the same claim", "",
        "`CLAUDE.md` states the requirement as *\"byte-reproducible for a fixed "
        "seed\"*.  **Only class A breaks that.**", "",
        "* **class A** — %s: `%s`" % (ds.CLASS_A,
                                      "`, `".join(i.name for i in ds.INJECTIONS
                                                  if i.klass == ds.CLASS_A)),
        "* **class B** — %s: `%s`" % (ds.CLASS_B,
                                      "`, `".join(i.name for i in ds.INJECTIONS
                                                  if i.klass == ds.CLASS_B)),
        "",
        "Class B is byte-identical on two runs at one seed — verified by "
        "`determinism_sandbox.classify`, which builds twice at the same seed.  "
        "It is a real defect and the `shared_hashseed` column is the evidence "
        "that catching it is worth something; but a reader who takes it for a "
        "`CLAUDE.md` violation has been told something this repository does not "
        "promise.  A note has gone to `monitor/inbox/` proposing the charter say "
        "which of the two it means.",
        "", "## Weakenings", "",
    ]
    for name, (why, _) in ds.WEAKENINGS.items():
        lines.append("* `%s` — %s" % (name, why))
    lines += ["", "## Injections", ""]
    for injection in ds.INJECTIONS:
        lines.append("* `%s` (on `%s`, class %s) — %s"
                     % (injection.name, injection.world,
                        "A" if injection.klass == ds.CLASS_A else "B",
                        injection.why))
    lines.append("")

    with open(os.path.join(HERE, "weakening_table.md"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines))
    with open(os.path.join(HERE, "weakening_table.json"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(grid, indent=2, sort_keys=True) + "\n")
    print("\nwrote weakening_table.md / .json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
