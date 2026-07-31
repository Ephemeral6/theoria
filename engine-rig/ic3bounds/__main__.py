"""Walk an axis and write the run directory.

    cd engine-rig
    python -m ic3bounds --out runs/<UTC>-E8-ic3-bounds
    python -m ic3bounds --out runs/<id> --axis size       --timeout 300
    python -m ic3bounds --out runs/<id> --axis predicates --timeout 300
    python -m ic3bounds --out runs/<id> --axis compose    --timeout 180
    python -m ic3bounds --out runs/<id> --only 4,6          # the cheap rungs

**Three axes, one entry point.**  Until this was written the entry point knew
only about axis A, and axes B and C were reachable only by running their modules
directly -- so the documented command was quietly a third of the package, and a
reader following `README`/`RUN_STATE` would have concluded the other two did not
exist.  The per-axis differences that made that easy to leave alone are real but
small, and they live in `_ADAPTERS` below rather than being smeared through
`main`: which keyword the axis's `run` takes its rungs under, how `--only` reads
(board sizes are integers, world ids are not), which key its boundary block uses
for "the largest rung that answered", and which renderer draws its table.

Writes `axis_size.json` **after every rung**, not at the end.  The top of this
ladder costs minutes per step and the whole run costs a quarter of an hour, so an
interrupted run leaving nothing on disk would be the normal outcome rather than
the exceptional one.  Every write is a whole document: the file is rebuilt from
the rungs finished so far, with `complete: false` until the last one lands.

Exit codes carry the distinction the taxonomy exists for:

    0   the axis ran.  A rung that timed out is a **result** -- it is the
        boundary this item was asked to find -- and does not fail the run.
    1   something escalated: `engine-refused` (the engine's own checker refused
        the engine's own output) or `adapter-mismatch` (the transition system was
        not the world it claimed to be), or the recheck column found something --
        an independent REJECT, a certificate that would not load, a crashed
        recheck, or the two state counts disagreeing.  All of them mean the
        numbers are wrong rather than the problem is hard, and none may be
        quietly tabulated.
    2   `AnchorDrift` -- the n=4 rung stopped being the M9 invariant, so the
        ladder is no longer anchored to the point it was built to extend.

**MANIFEST.json.**  Written only if the run directory does not already have one.
Several agents write into this E8 directory concurrently and a manifest lists the
files of whoever wrote it; overwriting one would destroy provenance rather than
record it.  `axis_size.json` therefore carries its own copy of the four required
fields in `provenance`, where nothing else can clobber them.
"""

import argparse
import datetime
import hashlib
import json
import os
import sys
from typing import Any, Dict, List, Optional, Sequence

from ic3bounds import axis_compose, axis_predicates, axis_size, recheck_column
from ic3bounds.harness import AnchorDrift


def _size_run(only, timeout, max_levels, on_step, command):
    return axis_size.run(ns=only or list(axis_size.LADDER),
                         timeout_seconds=timeout, max_levels=max_levels,
                         on_step=on_step, command=command)


def _compose_run(only, timeout, max_levels, on_step, command):
    return axis_compose.run(worlds=only or list(axis_compose.LADDER),
                            timeout_seconds=timeout, max_levels=max_levels,
                            on_step=on_step, command=command)


def _predicates_run(only, timeout, max_levels, on_step, command):
    return axis_predicates.run(
        timeout_seconds=timeout, max_levels=max_levels, on_step=on_step,
        command=command, boards=only or list(axis_predicates.PEG_BOARDS))


# One entry per axis.  `rungs` says how `--only` reads: `int` for a ladder
# indexed by board size, `str` for one indexed by world id.  `largest` is the
# key each axis's `boundary_of` uses for the last rung that answered -- axis A
# says `largest_answered_n` because its rungs are numbers and B and C say
# `largest_answered` because theirs are not, and reading the wrong one is a
# KeyError rather than a wrong number, which is the good failure but still one.
_ADAPTERS = {
    "size": {
        "run": _size_run, "rungs": int, "markdown": axis_size.markdown,
        "timeout": axis_size.DEFAULT_TIMEOUT_SECONDS,
        "largest": "largest_answered_n",
    },
    "predicates": {
        "run": _predicates_run, "rungs": int,
        "markdown": axis_predicates.markdown,
        "timeout": axis_predicates.DEFAULT_TIMEOUT_SECONDS,
        "largest": "largest_answered",
    },
    "compose": {
        "run": _compose_run, "rungs": str, "markdown": axis_compose.markdown,
        "timeout": axis_compose.DEFAULT_TIMEOUT_SECONDS,
        "largest": "largest_answered",
    },
}

AXES = tuple(_ADAPTERS)


def _write_json(path: str, payload: Any) -> None:
    """Atomic-ish and LF-pinned: the reader of a half-written artefact is the
    next agent, and a truncated JSON file is worse than a missing one."""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=2, sort_keys=False)
        fh.write("\n")
    os.replace(tmp, path)


def _sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_only(text: Optional[str], kind: type = int) -> Optional[List[Any]]:
    """`--only` for whichever axis is running.

    Axis A and axis B index their ladders by board size and axis C by world id,
    so the same flag has to parse as integers on two axes and as strings on the
    third.  Sorted on the numeric axes, left in the given order on the string
    one: a world-id ladder has a deliberate order (cheap first, stretch last)
    and alphabetising it would silently reorder the run.
    """
    if not text:
        return None
    parts = [part.strip() for part in text.split(",") if part.strip()]
    if kind is int:
        return sorted(int(part) for part in parts)
    return parts


def _maybe_manifest(out_dir: str, written: Sequence[str],
                    payload: Dict[str, Any]) -> Optional[str]:
    path = os.path.join(out_dir, "MANIFEST.json")
    if os.path.exists(path):
        return None
    prov = dict(payload["provenance"])
    manifest = {
        "prompt_id": prov["prompt_id"],
        "branch": prov["branch"],
        "base_commit": prov["base_commit"],
        "utc": prov["utc"],
        "command": prov["command"],
        "host": prov["host"],
        "note": "written by ic3bounds because this directory had no manifest "
                "yet; other agents write here too and may extend it.",
        "files": [
            {"path": name, "sha256": _sha256(os.path.join(out_dir, name))}
            for name in sorted(written)
            if os.path.isfile(os.path.join(out_dir, name))
        ],
    }
    _write_json(path, manifest)
    return path


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="ic3bounds")
    parser.add_argument("--out", required=True, help="run directory to write")
    parser.add_argument("--axis", default="size", choices=AXES,
                        help="which axis to walk: size (A), predicates (B), "
                             "compose (C)")
    parser.add_argument("--timeout", type=float, default=None,
                        help="wall-clock budget per rung, in seconds; the "
                             "default is the axis's own")
    parser.add_argument("--only", default=None,
                        help="comma-separated rungs -- board sizes on size and "
                             "predicates, world ids on compose -- for a smoke "
                             "run that does not cost a quarter of an hour")
    parser.add_argument("--max-levels", type=int, default=64,
                        help="the engine's own level cap; 64 does not bind on "
                             "the peg-N family")
    args = parser.parse_args(argv)

    adapter = _ADAPTERS[args.axis]
    if args.timeout is None:
        args.timeout = adapter["timeout"]

    out_dir = os.path.abspath(args.out)
    os.makedirs(out_dir, exist_ok=True)
    only = _parse_only(args.only, adapter["rungs"])

    command = "python -m ic3bounds --out %s --axis %s --timeout %g%s" % (
        args.out, args.axis, args.timeout,
        " --only %s" % args.only if args.only else "",
    )
    artefact = os.path.join(out_dir, "axis_%s.json" % args.axis)
    started = datetime.datetime.now(datetime.timezone.utc)

    def on_step(payload: Dict[str, Any]) -> None:
        _write_json(artefact, payload)
        step = payload["steps"][-1]
        det = step["deterministic"]
        wall = (step.get("timing") or {}).get("wall_seconds")
        # `recheck` is per-step on axes A and B and a single report-level
        # constant on axis C, so a missing key here is that axis saying "no
        # independent rechecker speaks this world", not a dropped column.
        print("  %-28s |S|=%-6d %-16s clauses=%-4s literals=%-5s frame=%-4s "
              "coverage=%-12s %-10s recheck=%s"
              % (step["spec"]["label"], det["n_states"], det["verdict"],
                 det["n_clauses"], det["n_literals"], det["converged_at_frame"],
                 det["coverage"],
                 "-" if wall is None else "%.3fs" % wall,
                 recheck_column.cell(step.get("recheck"))),
              flush=True)

    print("axis %s: %sbudget %.0fs per rung -> %s"
          % (args.axis,
             "" if only is None else "%d rung(s), " % len(only),
             args.timeout, artefact), flush=True)
    try:
        payload = adapter["run"](only, args.timeout, args.max_levels,
                                 on_step, command)
    except AnchorDrift as exc:
        print("\nANCHOR DRIFT -- the ladder is not on its own anchor:\n  %s" % exc)
        return 2

    _write_json(artefact, payload)
    manifest = _maybe_manifest(out_dir, ["axis_%s.json" % args.axis], payload)

    elapsed = (datetime.datetime.now(datetime.timezone.utc) - started).total_seconds()
    print("\n" + adapter["markdown"](payload))
    boundary = payload["boundary"]
    if boundary:
        print("\nboundary: %s (|S|=%d) -- %s; largest answered %s"
              % (boundary["label"], boundary["n_states"], boundary["verdict"],
                 boundary.get(adapter["largest"])))
    else:
        print("\nno boundary reached: every rung answered within the budget.")
    if payload.get("stopped_early"):
        print("stopped early: %s" % payload["stopped_early"])
    print("wrote %s (%d rung(s), %.1fs total)%s"
          % (artefact, len(payload["steps"]), elapsed,
             "" if manifest is None else "\nwrote %s" % manifest))

    rechecked = [step for step in payload["steps"]
                 if recheck_column.is_pass(step.get("recheck"))]
    print("recheck: %d of %d rung(s) ACCEPTed with both counts agreeing; "
          "%d row(s) had no invariant to check"
          % (len(rechecked), len(payload["steps"]),
             sum(1 for step in payload["steps"]
                 if (step.get("recheck") or {}).get("status")
                 == recheck_column.NO_INVARIANT)))

    # `.get` rather than `[...]`: axis C has no `recheck_findings` key, because
    # it has no per-rung rechecker to produce one.  Absent and empty mean the
    # same thing to the exit code, and neither means "checked and clean" -- the
    # line above is where a reader learns how many rows were actually checked.
    payload.setdefault("recheck_findings", [])
    if payload["escalations"] or payload["recheck_findings"]:
        if payload["escalations"]:
            print("\nESCALATIONS (%d) -- these are defects, not boundaries:"
                  % len(payload["escalations"]))
            for line in payload["escalations"]:
                print("  - %s" % line)
        if payload["recheck_findings"]:
            print("\nRECHECK FINDINGS (%d) -- an independent checker disagreed, "
                  "or the two counts did:" % len(payload["recheck_findings"]))
            for line in payload["recheck_findings"]:
                print("  - %s" % line)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
