"""Did this leg complete a level, or do we not know? Two different answers.

    cd theoria-arm && python -m armtools.level_evidence runs

**The finding this file was written from (A34, following A31).** Twenty-two
`runs/*/levels.jsonl` were zero bytes -- every one on disk, including the mock
legs -- and no instrument in the territory could tell the reader why. The
possibilities were three and they are not the same claim:

* nothing ever incremented the counter in front of this leg (**measured
  absence**: the arm looked at every envelope and the number never moved);
* nothing ever looked (**unmeasured**: no trace, or a trace whose envelopes
  never carried the field at all);
* something incremented the counter and the record of it is not on disk
  (**evidence missing**: the leg's own counter says a level was completed and
  `levels.jsonl` has no row saying so).

Every downstream reader collapsed all three into `levels_completed: 0`.
`armtools/round.py`'s round total did it in one character -- `or 0` -- so a leg
whose completion record had been lost contributed exactly what a leg that
genuinely completed nothing contributed. A34's negative control is that exact
case, built deliberately: a leg that **did** cross a boundary, with its
`levels.jsonl` truncated to zero bytes. Before this module every instrument in
the territory reported it as zero completions. That is the state in which the
sentence "no arm has ever completed a level" is unfalsifiable, because winning
and losing the record produce the same bytes.

**What this module is not.** It does not decide anything, fetch anything or
adjudicate. It reads a finished run directory and returns which of the five
answers below the disk supports.

**The five verdicts.**

``observed``
    `levels.jsonl` carries at least one row. `levels_completed` is a number.
``measured_absent``
    Envelopes carried the counter, it never rose, and `levels.jsonl` is
    correctly empty. `levels_completed` is `0` -- and this is the **only**
    verdict under which a zero is honest.
``unmeasured``
    No envelope in this leg ever carried `levels_completed`, so the counter was
    never read. `levels_completed` is `None`.
``evidence_missing``
    Some source says a level was completed and `levels.jsonl` does not carry a
    row for it. `levels_completed` is `None`, never the number: a count taken
    from a source whose event record has been lost is a count nobody can audit.
``no_run``
    Neither `levels.jsonl` nor `trace.jsonl` nor `RUN_STATE.json` is there.

`levels_completed` is `None` in three of the five, and that is the point. A
caller that writes `evidence["levels_completed"] or 0` has reintroduced the
defect; `total()` below is the shape that does not.
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

#: The rows `levels.jsonl` may carry. `game_won` is the winning increment,
#: which is not a segmenting boundary -- see `inner/levels.LevelLog.finals`.
COMPLETION_EVENTS = ("level_boundary", "game_won")


def _read_jsonl(path: str) -> Optional[List[Dict[str, Any]]]:
    if not os.path.exists(path):
        return None
    rows: List[Dict[str, Any]] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def _read_json(path: str) -> Optional[Any]:
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except ValueError:
        return None


def read_leg(run_dir: str) -> Dict[str, Any]:
    """One run directory's level evidence, with the verdict and its sources.

    Every number in the result is accompanied by where it came from, because
    the whole failure mode here is a number whose provenance was dropped.
    """
    levels_path = os.path.join(run_dir, "levels.jsonl")
    trace_path = os.path.join(run_dir, "trace.jsonl")
    state_path = os.path.join(run_dir, "RUN_STATE.json")

    rows = _read_jsonl(levels_path)
    trace = _read_jsonl(trace_path)
    state = _read_json(state_path)

    out: Dict[str, Any] = {
        "run_dir": run_dir,
        "slug": os.path.basename(os.path.normpath(run_dir)),
        "levels_jsonl": ("absent" if rows is None
                         else "empty" if not rows else "rows"),
        "levels_jsonl_bytes": (os.path.getsize(levels_path)
                               if os.path.exists(levels_path) else None),
        "rows": 0 if rows is None else len(rows),
        "boundaries_in_file": 0,
        "game_won_in_file": 0,
        # From the raw envelopes: the highest count any command ever carried.
        # `None` means no envelope carried the field, which is not zero.
        "counter_max_in_trace": None,
        "envelopes_carrying_counter": 0,
        "envelopes": 0 if trace is None else len(trace),
        # From the leg's own summary of itself.
        "counter_in_run_state": None,
        "boundaries_in_run_state": None,
    }

    if rows:
        out["boundaries_in_file"] = sum(
            1 for r in rows if r.get("event") == "level_boundary")
        out["game_won_in_file"] = sum(
            1 for r in rows if r.get("event") == "game_won")

    if trace is not None:
        seen = [r.get("levels_completed") for r in trace
                if isinstance(r.get("levels_completed"), int)]
        out["envelopes_carrying_counter"] = len(seen)
        if seen:
            out["counter_max_in_trace"] = max(seen)

    if isinstance(state, dict):
        levels = state.get("levels")
        if isinstance(levels, dict):
            if isinstance(levels.get("levels_completed"), int):
                out["counter_in_run_state"] = levels["levels_completed"]
            if isinstance(levels.get("boundaries"), int):
                out["boundaries_in_run_state"] = levels["boundaries"]

    if rows is None and trace is None and state is None:
        out["verdict"] = "no_run"
        out["levels_completed"] = None
        out["detail"] = ("no `levels.jsonl`, no `trace.jsonl` and no "
                         "`RUN_STATE.json` under %s -- this is not a finished "
                         "run directory." % run_dir)
        return out

    # The highest completion count any source claims, and which source said it.
    claims = [("trace.jsonl", out["counter_max_in_trace"]),
              ("RUN_STATE.json", out["counter_in_run_state"])]
    claimed = [(name, n) for name, n in claims if isinstance(n, int) and n > 0]

    in_file = out["rows"]
    if in_file:
        out["verdict"] = "observed"
        out["levels_completed"] = out["boundaries_in_file"] + out["game_won_in_file"]
        out["detail"] = (
            "`levels.jsonl` carries %d row(s): %d boundary and %d win."
            % (in_file, out["boundaries_in_file"], out["game_won_in_file"]))
        # Even with rows, the file can be short of what the counter claims.
        for name, n in claimed:
            if n > out["levels_completed"]:
                out["verdict"] = "evidence_missing"
                out["levels_completed"] = None
                out["detail"] = (
                    "%s says %d level(s) were completed and `levels.jsonl` "
                    "carries only %d completion row(s). The count is withheld: "
                    "a completion whose event record is not on disk cannot be "
                    "audited, and reporting the higher number would publish a "
                    "figure no artefact supports."
                    % (name, n, in_file))
                break
        return out

    if claimed:
        name, n = claimed[0]
        out["verdict"] = "evidence_missing"
        out["levels_completed"] = None
        out["detail"] = (
            "%s says %d level(s) were completed and `levels.jsonl` is %s. This "
            "leg's completion record is missing, which is NOT the same claim as "
            "zero completions and must never be summed as one."
            % (name, n, out["levels_jsonl"]))
        return out

    if out["envelopes_carrying_counter"] == 0:
        out["verdict"] = "unmeasured"
        out["levels_completed"] = None
        out["detail"] = (
            "no envelope in this leg carried `levels_completed` (%d step(s) "
            "recorded), so the counter was never read. Absence of a completion "
            "here is absence of a measurement."
            % out["envelopes"])
        return out

    out["verdict"] = "measured_absent"
    out["levels_completed"] = 0
    out["detail"] = (
        "%d envelope(s) carried `levels_completed` and it never rose above 0, "
        "and `levels.jsonl` is correctly empty. This is a measured absence: "
        "the instrument looked and the world did not move."
        % out["envelopes_carrying_counter"])
    return out


def total(legs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Sum the legs that reported, and count the legs that did not.

    This is the shape `armtools/round.py`'s `sum(... or 0)` did not have. A
    round of six legs in which one won a level and five lost their records
    summed to 1 and read as "six legs, one level"; here it reads as "one leg
    reported 1, five legs could not be read", which is a different sentence and
    the true one.
    """
    counted = [l for l in legs if isinstance(l.get("levels_completed"), int)]
    by_verdict: Dict[str, int] = {}
    for leg in legs:
        by_verdict[leg.get("verdict", "?")] = by_verdict.get(
            leg.get("verdict", "?"), 0) + 1
    unreadable = [l["slug"] for l in legs
                  if not isinstance(l.get("levels_completed"), int)]
    return {
        "legs": len(legs),
        "legs_counted": len(counted),
        "levels_completed": sum(l["levels_completed"] for l in counted),
        "legs_not_counted": len(unreadable),
        "not_counted_slugs": sorted(unreadable),
        "by_verdict": dict(sorted(by_verdict.items())),
        "reading": (
            "%d of %d leg(s) carry a readable completion record, and they sum "
            "to %d. The other %d are not zeros; they are %s."
            % (len(counted), len(legs),
               sum(l["levels_completed"] for l in counted), len(unreadable),
               ", ".join("%s=%d" % kv for kv in sorted(by_verdict.items())
                         if kv[0] != "measured_absent" and kv[0] != "observed")
               or "none")),
    }


def sweep(runs_root: str) -> Dict[str, Any]:
    legs = []
    for name in sorted(os.listdir(runs_root)):
        path = os.path.join(runs_root, name)
        if not os.path.isdir(path):
            continue
        leg = read_leg(path)
        if leg["verdict"] == "no_run":
            continue
        legs.append(leg)
    return {"runs_root": runs_root, "legs": legs, "total": total(legs)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("path", help="a run directory, or a runs/ root to sweep")
    ap.add_argument("--json", action="store_true", help="machine-readable")
    args = ap.parse_args(argv)

    path = os.path.abspath(args.path)
    if os.path.exists(os.path.join(path, "RUN_STATE.json")) or \
            os.path.exists(os.path.join(path, "trace.jsonl")):
        report = {"legs": [read_leg(path)]}
        report["total"] = total(report["legs"])
    else:
        report = sweep(path)

    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True))
        return 0
    for leg in report["legs"]:
        print("%-52s %-16s %s" % (
            leg["slug"][:52], leg["verdict"],
            "levels_completed=%s" % leg["levels_completed"]))
    print()
    print(report["total"]["reading"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
