"""Adversarial harness for the E2 speed-up-is-zero result.

Nothing here is imported by the rig.  It drives `bench/`'s own compiler and
`bench/fdrun.py`'s own parser -- deliberately, so that a refutation cannot be an
artefact of a second implementation -- and adds only the instances and the sizes
E2 did not run.

Usage:
    python -m attacks.lens <subcommand> ...
from the run directory, or via the thin wrappers beside this file.
"""

import json
import os
import sys
import time
from typing import Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
RIG = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
if RIG not in sys.path:
    sys.path.insert(0, RIG)

from bench import compile_theorems, fdrun            # noqa: E402
from bench.instances import far_level                # noqa: E402
from engines import deadlock_carver as dc            # noqa: E402
from engines import fd_adapter                       # noqa: E402
from engines.fd_adapter import backends              # noqa: E402
from fixtures import sokoban                         # noqa: E402

RUNGS = (
    ("blind", backends.FD_OPTIMAL, "blind"),
    ("lmcut", backends.FD_OPTIMAL, "lmcut"),
    ("ipdb", backends.FD_OPTIMAL, "ipdb"),
)


def executable() -> str:
    found = backends.find_fast_downward()
    if found is None:
        raise SystemExit("no Fast Downward on this machine; set FAST_DOWNWARD")
    return found


def carve_level(level: sokoban.Level, work: str) -> Tuple[str, object, object, list, float]:
    """Write the plain problem, carve it, return everything downstream needs."""
    os.makedirs(work, exist_ok=True)
    problem_path = os.path.join(work, "%s.pddl" % level.name)
    text = level.problem_text()
    with open(problem_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    domain = fd_adapter.parse_domain(fd_adapter.read(sokoban.DOMAIN_PATH))
    problem = fd_adapter.parse_problem(fd_adapter.read(problem_path))
    started = time.perf_counter()
    task = dc.Task.build(domain, problem)
    theorems = dc.carve(task)
    carve_seconds = time.perf_counter() - started
    compile_theorems.guardable(domain, theorems)
    return problem_path, domain, problem, theorems, carve_seconds


def row(measurement: fdrun.FdMeasurement) -> Dict[str, object]:
    return {
        "expanded": measurement.nodes.get("expanded"),
        "evaluated": measurement.nodes.get("evaluated"),
        "generated": measurement.nodes.get("generated"),
        "operators": measurement.translator.get("operators"),
        "task_size": measurement.translator.get("task_size"),
        "plan_length": measurement.plan_length,
        "config": measurement.config,
        "returncode": measurement.returncode,
        "solved": measurement.solved,
        "proved_unsolvable": measurement.proved_unsolvable,
        "error": measurement.error,
        "search_seconds": measurement.search_seconds,
        "wall_seconds": round(measurement.wall_seconds, 3),
    }


def measure_level(level: sokoban.Level, work: str, log_dir: str,
                  guards: Sequence[str] = ("singleton",),
                  rungs=RUNGS, timeout: int = 900,
                  repeats: int = 1) -> Dict[str, object]:
    """Baseline and guarded, every rung, one level.  Validation included."""
    fd = executable()
    problem_path, domain, problem, theorems, carve_seconds = carve_level(level, work)
    os.makedirs(log_dir, exist_ok=True)

    out: Dict[str, object] = {
        "instance": level.name,
        "cells": len(level.floors()),
        "boxes": len(level.boxes),
        "n_theorems": len(theorems),
        "n_singleton": sum(1 for t in theorems if t.size == 1),
        "n_pair": sum(1 for t in theorems if t.size == 2),
        "carve_seconds": round(carve_seconds, 3),
        "problem_path": problem_path,
        "rows": [],
    }

    baselines = {}
    for name, tier, heuristic in rungs:
        baselines[name] = fdrun.repeat(
            fd, sokoban.DOMAIN_PATH, problem_path, tier=tier, heuristic=heuristic,
            repeats=repeats, timeout=timeout,
            keep_log=os.path.join(log_dir, "%s.%s.base.log" % (level.name, name)),
        )

    available = compile_theorems.guardable_guards(theorems)
    for guard in guards:
        if guard not in available:
            out["rows"].append({"guard": guard, "skipped": "no pair theorems"})
            continue
        gdir = os.path.join(work, guard)
        gdom, gprob = compile_theorems.write_guarded(
            gdir, level.name, level.problem_text(), theorems, guard=guard, problem=problem
        )
        for name, tier, heuristic in rungs:
            guarded = fdrun.repeat(
                fd, gdom, gprob, tier=tier, heuristic=heuristic, repeats=repeats,
                timeout=timeout,
                keep_log=os.path.join(log_dir, "%s.%s.%s.log" % (level.name, name, guard)),
            )
            base = baselines[name]
            replayed = None
            if guarded.plan:
                try:
                    fd_adapter.validate_plan(
                        domain, problem,
                        compile_theorems.to_original_plan(guarded.plan, guard),
                    )
                    replayed = True
                except Exception as exc:                       # pragma: no cover
                    replayed = "FAILED: %s" % exc
            out["rows"].append({
                "guard": guard,
                "rung": name,
                "before": row(base),
                "after": row(guarded),
                "replayed_on_original_domain": replayed,
            })
    return out


def dump(obj, path: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=2, sort_keys=True)
        fh.write("\n")


def brief(entry: Dict[str, object]) -> None:
    print("== %(instance)s  cells=%(cells)s boxes=%(boxes)s theorems=%(n_theorems)s "
          "(%(n_singleton)s/%(n_pair)s) carve=%(carve_seconds)ss" % entry)
    for r in entry["rows"]:
        if "skipped" in r:
            print("   %-9s SKIP %s" % (r["guard"], r["skipped"]))
            continue
        b, a = r["before"], r["after"]
        def fmt(m):
            if m["error"]:
                return "ERR(%s)" % m["error"][:40]
            if m["expanded"] is None:
                return "?"
            return str(m["expanded"])
        print("   %-9s %-6s exp %8s -> %-8s  ops %s->%s  size %s->%s  len %s->%s  "
              "search %ss->%ss  replay=%s"
              % (r["guard"], r["rung"], fmt(b), fmt(a),
                 b["operators"], a["operators"], b["task_size"], a["task_size"],
                 b["plan_length"], a["plan_length"],
                 b["search_seconds"], a["search_seconds"],
                 r["replayed_on_original_domain"]))
