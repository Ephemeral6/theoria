"""Re-check a run directory without re-running the search.

    cd engine-rig
    python -m ic3bounds.verify runs/<id> [runs/<other> ...]

E8's tables are an argument about where an engine stops, and the argument is
only worth the artefacts behind it.  This re-derives them.  The expensive half
-- IC3 itself -- is deliberately *not* re-run: a quarter of an hour of search
would make this a thing nobody runs, and re-running the search would in any case
only prove the search agrees with itself.  What is re-run is the part that
matters, which is cheaper by orders of magnitude:

**1. Every published invariant is re-verified from the artefact.**  The row
carries `cnf_text`.  This parses it back into clauses, rebuilds the system from
the spec, and hands both to `engines.ic3_pdr.check.verify` -- the checker that
shares no code with the search -- then compares its three conditions and its
satisfying-state count against the numbers the row published.  A row whose
invariant does not re-verify is a false claim on the table, not a stale one.

**2. Every derived column is recomputed.**  `abstraction`, `encoding_slack`,
`coverage_ratio` and the block structure of axis B are pure functions of the
record and the spec, so they are recomputed and compared exactly.  A column
edited by hand after the run fails here.

**3. Timings are checked for presence and ordering, never for equality**
(`bench/README.md` rule 3).  A `timeout` row is flagged `machine_dependent` and
is compared on its verdict and its budget alone: a faster machine finishing what
this one could not is news, not a defect.

**4. The Markdown is regenerated from the JSON and diffed.**  `IC3_BOUNDS.md`
quotes tables; if a table in it was edited rather than regenerated, the numbers
in the document and the numbers on disk have parted company and only the
document is read.

Exit codes follow the rig's convention (`heldout/run.py`):

    0   every check passed
    1   a check failed -- a published number is not what the artefact says
    3   could not run at all: no artefact, unreadable JSON, missing spec fields
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional, Sequence

from ic3bounds import harness, recheck_column, reencode

AXIS_FILES = ("axis_size.json", "axis_predicates.json", "axis_compose.json")

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_COULD_NOT_RUN = 3


class CouldNotRun(Exception):
    """Distinguished from a failed check on purpose.

    "The artefact is missing" and "the artefact is wrong" are different
    sentences, and a verifier that returned the same code for both would let a
    run that produced nothing pass for a run that produced something bad -- or
    the reverse, which is worse.
    """


# ------------------------------------------------------------------ the systems

def _system_for(axis: str, step: Dict[str, Any]):
    """Rebuild the system a row was measured on, from the row alone.

    Each axis knows how to do this for itself and none of them is allowed to
    read anything but the spec -- if a row cannot name the world it was taken
    on, the row is not evidence.
    """
    spec = step["spec"]
    if axis == "size":
        return harness.build_system(harness.StepSpec.from_json(spec)), None
    if axis == "predicates":
        from ic3bounds import axis_predicates
        parsed = axis_predicates.PredicateSpec.from_json(spec)
        system, recoding, recoded = axis_predicates.build_recoded(parsed)
        return recoded, recoding
    if axis == "compose":
        from ic3bounds import worldgen_system
        return worldgen_system.build_system(spec["world_id"]), None
    raise CouldNotRun("unknown axis %r" % axis)


# ------------------------------------------------------------- the four checks

def recheck_invariants(axis: str, payload: Dict[str, Any]) -> List[str]:
    """Hand every published clause set back to the independent checker."""
    from engines.ic3_pdr import check as ic3_check

    problems: List[str] = []
    for step in payload.get("steps", []):
        det = step["deterministic"]
        label = step["spec"]["label"]
        if det.get("verdict") != harness.INVARIANT:
            continue
        try:
            system, _ = _system_for(axis, step)
            clauses = recheck_column.parse_cnf(det.get("cnf_text"),
                                               system.variables)
        except Exception as exc:                       # noqa: BLE001
            problems.append("%s: the row's invariant could not be read back "
                            "against its own system: %s" % (label, exc))
            continue

        if len(clauses) != det.get("n_clauses"):
            problems.append(
                "%s: cnf_text parses to %d clause(s), the row says %s"
                % (label, len(clauses), det.get("n_clauses")))
        literals = sum(len(clause) for clause in clauses)
        if literals != det.get("n_literals"):
            problems.append(
                "%s: cnf_text parses to %d literal(s), the row says %s"
                % (label, literals, det.get("n_literals")))

        result = ic3_check.verify(system, clauses)
        if not result.holds:
            problems.append(
                "%s: the PUBLISHED invariant does not re-verify -- %s"
                % (label, json.dumps({k: sorted(v) for k, v
                                      in sorted(result.witnesses.items())},
                                     sort_keys=True)))
        if result.n_satisfying != det.get("n_satisfying"):
            problems.append(
                "%s: re-counted %d satisfying state(s), the row says %s"
                % (label, result.n_satisfying, det.get("n_satisfying")))
        if result.n_states != det.get("n_states"):
            problems.append(
                "%s: the system has %d states, the row says %s"
                % (label, result.n_states, det.get("n_states")))
        if dict(sorted(result.conditions.items())) != det.get("checker_conditions"):
            problems.append(
                "%s: the checker's three conditions differ from the recorded "
                "ones" % label)
    return problems


def recheck_native_forms(payload: Dict[str, Any]) -> List[str]:
    """Axis B only: the desugared certificate must count the same set.

    The recheck column's whole claim is that a padded certificate has an exact
    native form.  A bijection cannot change the size of a set, so re-deriving
    the native form and re-counting it is a check that can only fail if the
    rewriting is wrong.
    """
    from engines.ic3_pdr import check as ic3_check
    from ic3bounds import axis_predicates

    problems: List[str] = []
    for step in payload.get("steps", []):
        det, spec = step["deterministic"], step["spec"]
        if det.get("verdict") != harness.INVARIANT:
            continue
        if spec.get("scheme") not in (reencode.NATIVE, reencode.DUAL):
            continue
        if spec.get("family") != axis_predicates.PEG_FAMILY:
            continue
        parsed = axis_predicates.PredicateSpec.from_json(spec)
        system, recoding, recoded = axis_predicates.build_recoded(parsed)
        clauses = recheck_column.parse_cnf(det["cnf_text"], recoded.variables)
        native = reencode.desugar(recoding, clauses)
        result = ic3_check.verify(system, native.clauses)
        if not result.holds:
            problems.append(
                "%s: the native form of its invariant is not inductive on the "
                "native system -- the rewriting is wrong" % spec["label"])
        if result.n_satisfying != det.get("n_satisfying"):
            problems.append(
                "%s: the native form holds on %d state(s) and the recoded one "
                "on %s; a bijection cannot change a count"
                % (spec["label"], result.n_satisfying, det.get("n_satisfying")))
    return problems


def recompute_derived(axis: str, payload: Dict[str, Any]) -> List[str]:
    problems: List[str] = []
    if axis != "predicates":
        return problems
    from ic3bounds import axis_predicates

    for step in payload.get("steps", []):
        recorded = step.get("derived")
        if recorded is None:
            problems.append("%s: no derived columns on the row"
                            % step["spec"]["label"])
            continue
        parsed = axis_predicates.PredicateSpec.from_json(step["spec"])
        fresh = axis_predicates.derived(step, parsed)
        for key in sorted(set(fresh) | set(recorded)):
            if fresh.get(key) != recorded.get(key):
                problems.append(
                    "%s: derived.%s is %r on disk and %r when recomputed"
                    % (step["spec"]["label"], key, recorded.get(key),
                       fresh.get(key)))

    blocks = axis_predicates.held_fixed(payload["steps"])
    for block, recorded in zip(blocks, payload.get("held_fixed", [])):
        if block["n_states"] != recorded.get("n_states"):
            problems.append("block %s: |S| is %s on disk and %s when recomputed"
                            % (block["board"], recorded.get("n_states"),
                               block["n_states"]))
        sizes = {row["n_predicates"] for row in block["rows"]}
        if len(block["rows"]) > 1 and len(sizes) < 2:
            problems.append(
                "block %s: every rung declares the same number of predicates, "
                "so the block varies nothing and measures nothing"
                % block["board"])
    return problems


def check_timings(payload: Dict[str, Any]) -> List[str]:
    problems: List[str] = []
    for step in payload.get("steps", []):
        problems.extend(harness.timing_problems(step))
    return problems


def check_state_space_is_held_fixed(payload: Dict[str, Any]) -> List[str]:
    """Axis B's premise, re-asserted against the artefact.

    Every rung of a block must report the same `n_states`.  If one does not,
    the block compared two different worlds and every ratio taken inside it is
    meaningless -- which would not show up in any other check here, because
    each row is individually perfectly valid.
    """
    from ic3bounds import axis_predicates

    problems: List[str] = []
    for block in axis_predicates.held_fixed(payload.get("steps", [])):
        counts = {row["label"]: None for row in block["rows"]}
        for step in payload["steps"]:
            if step["spec"]["label"] in counts:
                counts[step["spec"]["label"]] = step["deterministic"]["n_states"]
        distinct = set(counts.values())
        if len(distinct) > 1:
            problems.append(
                "block %s does not hold its state space fixed: %s"
                % (block["board"], json.dumps(counts, sort_keys=True)))
    return problems


def check_markdown(axis: str, payload: Dict[str, Any],
                   run_dir: str) -> List[str]:
    from ic3bounds import __main__ as entry

    table = entry._ADAPTERS[axis]["markdown"](payload)
    path = os.path.join(run_dir, "AXIS_%s.md" % axis.upper())
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as handle:
        on_disk = handle.read()
    if table.strip() not in on_disk:
        return ["%s: the committed table is not what the JSON renders -- it was "
                "edited rather than regenerated" % os.path.basename(path)]
    return []


# --------------------------------------------------------------------- the run

def verify_axis(run_dir: str, filename: str) -> List[str]:
    path = os.path.join(run_dir, filename)
    axis = filename[len("axis_"):-len(".json")]
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, ValueError) as exc:
        raise CouldNotRun("%s: %s" % (path, exc))

    if payload.get("axis") != axis:
        raise CouldNotRun("%s declares axis %r" % (path, payload.get("axis")))
    if not payload.get("steps"):
        raise CouldNotRun("%s has no steps" % path)
    for field in ("prompt_id", "branch", "base_commit", "utc"):
        if not (payload.get("provenance") or {}).get(field):
            raise CouldNotRun("%s: provenance is missing %r" % (path, field))

    problems: List[str] = []
    problems.extend(recheck_invariants(axis, payload))
    problems.extend(check_timings(payload))
    if axis == "predicates":
        problems.extend(recheck_native_forms(payload))
        problems.extend(recompute_derived(axis, payload))
        problems.extend(check_state_space_is_held_fixed(payload))
    problems.extend(check_markdown(axis, payload, run_dir))
    return problems


def verify(run_dir: str) -> Dict[str, Any]:
    present = [name for name in AXIS_FILES
               if os.path.exists(os.path.join(run_dir, name))]
    if not present:
        raise CouldNotRun("%s holds none of %s" % (run_dir, ", ".join(AXIS_FILES)))
    out: Dict[str, Any] = {"run": run_dir, "axes": {}, "problems": []}
    for name in present:
        problems = verify_axis(run_dir, name)
        out["axes"][name] = len(problems)
        out["problems"].extend(problems)
    return out


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="ic3bounds.verify")
    parser.add_argument("run_dirs", nargs="+", help="run directories to check")
    args = parser.parse_args(argv)

    failed = False
    for run_dir in args.run_dirs:
        try:
            result = verify(os.path.abspath(run_dir))
        except CouldNotRun as exc:
            print("COULD NOT RUN  %s" % exc)
            return EXIT_COULD_NOT_RUN
        for name, count in sorted(result["axes"].items()):
            print("  %-24s %s" % (name, "ok" if not count
                                  else "%d problem(s)" % count))
        for line in result["problems"]:
            print("    - %s" % line)
        failed = failed or bool(result["problems"])
        print("%s  %s" % ("FAIL" if result["problems"] else "OK  ", run_dir))
    return EXIT_FAILED if failed else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
