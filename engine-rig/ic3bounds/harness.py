"""One gradient step, measured in a subprocess, split into two halves.

E8 asks where IC3 stops.  Answering that honestly needs three things this module
provides and nothing else in the rig does.

**1. A wall-clock budget the engine does not have.**  `engines.ic3_pdr.ic3` has
exactly one limit, `max_levels`, and on the peg-N family it does not bind: the
search converges at frame 12 while the clock runs for a hundred seconds.  So the
only way to bound a step is from outside it, and the only portable way to bound a
Python computation from outside is another process.  `signal.alarm` is POSIX-only
and this repo is run on Windows and under WSL, so the budget is
`subprocess.run(..., timeout=)` -- the same precedent `bench/fdrun.py` set, for
the same reason.  The child is `python -m ic3bounds.harness --spec <json>`; it
prints one sentinel-prefixed JSON line and exits.

**2. A failure taxonomy that does not flatter the engine.**  Six verdicts, and
the distinctions between them are the point of the table:

    invariant         IC3 converged and its own independent checker re-verified
                      the clause set.  An answer.
    counterexample    IC3 found a real path to the goal, and `check.replay`
                      replayed it.  Also an answer -- the property was false.
    timeout           *We* stopped it, after `budget_seconds` on *this machine*.
                      This says nothing about the problem and everything about
                      the afternoon; rows carrying it are flagged
                      `machine_dependent` and a verify pass must not compare
                      them for equality.
    level-cap         `Ic3Error("no verdict within N levels")`.  A knob we set,
                      not a capability limit: raise `max_levels` and the same
                      run may well converge.  Recorded separately from `timeout`
                      because conflating a budget with a boundary is how a
                      benchmark starts lying.
    engine-refused    The engine's own `check.py` refused the engine's own
                      output, or an internal `Ic3Error` fired, or the child died.
                      This is an ENGINE DEFECT.  It is escalated, never
                      tabulated as a boundary -- a row like this means the number
                      next to it is worthless, not that the problem was hard.
    adapter-mismatch  The `System` handed to IC3 is not the peg world it claims
                      to transcribe, checked against a second, independent
                      transcription written in this file.  Also escalated: it
                      would make every other column measure the wrong world.

**There is no "generalisation failure" mode, and this module refuses to invent
one.**  `pdr._Run.generalise` iterates over a finite sorted literal set, drops a
literal only when the smaller clause is still relative-inductive, and stops at
`len(current) <= 1`.  It always terminates and it always returns a clause; the
worst case is that it drops nothing and returns the full negated cube it was
handed.  So generalisation cannot *fail* here -- it can only fail to *help*, and
that is a continuous quantity, not a category.  It is recorded as one:
`n_literals`, `widest_clause`, and `literal_saturation` (mean clause width over
the number of variables, so 1.0 is "every clause is a full negated cube and the
engine generalised nothing").  A ladder whose saturation climbs toward 1.0 is
watching IC3 degrade into state enumeration, which is the interesting failure and
the one a category called "generalisation failed" would have hidden.

**3. The deterministic / timing split** (`bench/README.md` rule 3).  Every record
is two dicts.  `deterministic` is a function of the spec and the engine and
nothing else -- verdict, clause and literal counts, frame of convergence, the
counters, the rendered CNF, the coverage fraction; a verify pass re-derives it
and compares exactly.  `timing` is a function of this machine on this afternoon;
it is checked for presence and ordering (the engine's own clock fits inside the
subprocess wall clock) and never for equality.  The one place the two touch is a
`timeout` row, whose *verdict* is machine-dependent -- so it says so, in the
deterministic half, rather than pretending to a reproducibility it cannot have.

**Vacuity.**  Every row carries `n_satisfying / n_states`.  An invariant is only
interesting insofar as it excludes something: the M9 anchor holds on 8 of 16
states, and a clause set holding on 15 of 16 would be near-vacuous however many
levels it took to find.  The fraction is on every row, `near_vacuous` flags the
ones past `NEAR_VACUOUS_RATIO`, and no row is reported without it.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

# Sentinel-prefixed, because a child process shares stdout with anything its
# imports decide to print.  The parent reads the last line carrying the prefix.
SENTINEL = "IC3BOUNDS-RECORD "

DEFAULT_TIMEOUT_SECONDS = 300.0
DEFAULT_MAX_LEVELS = 64

# Past this, an invariant is holding on so much of the state space that it is
# barely a statement.  A threshold, not a truth: the fraction itself is on every
# row so a reader can pick their own.
NEAR_VACUOUS_RATIO = 0.9

INVARIANT = "invariant"
COUNTEREXAMPLE = "counterexample"
TIMEOUT = "timeout"
LEVEL_CAP = "level-cap"
ENGINE_REFUSED = "engine-refused"
ADAPTER_MISMATCH = "adapter-mismatch"

VERDICTS = (INVARIANT, COUNTEREXAMPLE, TIMEOUT, LEVEL_CAP, ENGINE_REFUSED,
            ADAPTER_MISMATCH)

# The two that are defects in something other than the problem.  They are
# escalated by the caller; they are never the boundary a table reports.
ESCALATING = (ENGINE_REFUSED, ADAPTER_MISMATCH)

# The two that are answers.  Everything else stopped short of one.
ANSWERS = (INVARIANT, COUNTEREXAMPLE)

# Every key in the deterministic half, in the order they are written.  Present on
# every row, `None` where the verdict makes them inapplicable -- a missing key and
# a null are different claims and a diff should not have to guess which it saw.
DETERMINISTIC_FIELDS = (
    "verdict",
    "machine_dependent",
    "escalate",
    "n_states",
    "n_satisfying",
    "coverage",
    "coverage_ratio",
    "near_vacuous",
    "n_clauses",
    "n_literals",
    "widest_clause",
    "narrowest_clause",
    "cube_limit",
    "literal_saturation",
    "converged_at_frame",
    "states_blocked",
    "literals_dropped",
    "clauses_dropped",
    "counterexample_length",
    "cnf_text",
    "checker_conditions",
    "detail",
)

TIMING_FIELDS = ("wall_seconds", "ic3_seconds", "check_seconds", "build_seconds")


class AnchorDrift(Exception):
    """The n=4 row is no longer the invariant M9 published.

    Raised rather than warned.  The whole ladder is an argument that one point
    extends to a line; if the point moved, every step above it is measuring some
    other family and the table is worse than no table.
    """


# --------------------------------------------------------------------- the spec


@dataclass(frozen=True)
class StepSpec:
    """One rung: which peg world, which start, which goal, which level cap.

    Deliberately serialisable and deliberately free of paths -- it crosses a
    process boundary as JSON on a command line, and an absolute path in it would
    put this machine's directory layout into a deterministic field.
    """

    axis: str
    label: str
    n: int
    initial: str
    goal_states: Tuple[str, ...]
    max_levels: int = DEFAULT_MAX_LEVELS

    def as_json(self) -> Dict[str, Any]:
        return {
            "axis": self.axis,
            "label": self.label,
            "n": self.n,
            "initial": self.initial,
            "goal_states": list(self.goal_states),
            "max_levels": self.max_levels,
        }

    @classmethod
    def from_json(cls, payload: Dict[str, Any]) -> "StepSpec":
        return cls(
            axis=str(payload["axis"]),
            label=str(payload["label"]),
            n=int(payload["n"]),
            initial=str(payload["initial"]),
            goal_states=tuple(str(g) for g in payload["goal_states"]),
            max_levels=int(payload.get("max_levels", DEFAULT_MAX_LEVELS)),
        )


# ------------------------------------------------- the second transcription

def _jump_instances(n: int) -> List[Tuple[int, int, int]]:
    """(src, over, dst) for every 1D peg jump on an n-cell board.

    Written here from the rule rather than imported from `interop.peg1d`, and
    that is the entire point of it: the gate below compares the `System` IC3 will
    actually search against a transcription that shares no code with the one that
    built it.  If both were the same function the gate would only ever confirm
    that the function equals itself.
    """
    out: List[Tuple[int, int, int]] = []
    for src in range(n):
        for step in (1, -1):
            over, dst = src + step, src + 2 * step
            if 0 <= dst < n:
                out.append((src, over, dst))
    return sorted(out, key=lambda m: (m[0], m[2]))


def _independent_moves(text: str) -> List[Tuple[str, str]]:
    """Every (label, successor) legal in `text`, derived from the rule directly."""
    out: List[Tuple[str, str]] = []
    for src, over, dst in _jump_instances(len(text)):
        if text[src] == "1" and text[over] == "1" and text[dst] == "0":
            cells = list(text)
            cells[src] = "0"
            cells[over] = "0"
            cells[dst] = "1"
            out.append(("jump(%d,%d,%d)" % (src, over, dst), "".join(cells)))
    return sorted(out)


def transcription_mismatches(system, n: int, initial: str,
                             goal_states: Sequence[str],
                             limit: int = 8) -> List[str]:
    """Is the `System` the peg world it claims to be?  Re-derived, not trusted.

    Checks the state set, the initial state, the goal set and the whole labelled
    transition relation.  Returns the first `limit` disagreements; an empty list
    is the gate passing.
    """
    problems: List[str] = []

    expected_states = sorted(
        format(index, "0%db" % n) for index in range(2 ** n)
    )
    actual_states = [system.render_state(s) for s in system.states]
    if actual_states != expected_states:
        problems.append(
            "state set: %d states, expected %d, sorted-equal=%s"
            % (len(actual_states), len(expected_states),
               sorted(actual_states) == expected_states)
        )

    actual_init = [system.render_state(s) for s in system.init]
    if actual_init != [initial]:
        problems.append("init: %r, expected %r" % (actual_init, [initial]))

    actual_bad = sorted(system.render_state(s) for s in system.bad)
    if actual_bad != sorted(goal_states):
        problems.append("bad: %r, expected %r" % (actual_bad, sorted(goal_states)))

    for state in system.states:
        text = system.render_state(state)
        actual = sorted(
            (label, system.render_state(target))
            for label, target in system.moves(state)
        )
        expected = _independent_moves(text)
        if actual != expected:
            problems.append(
                "transitions from %s: %r, re-derived %r" % (text, actual, expected)
            )
            if len(problems) >= limit:
                break
    return problems[:limit]


# ------------------------------------------------------------- the measurement

def _blank_deterministic(n: int) -> Dict[str, Any]:
    """Every key present.  `n_states` and `cube_limit` are known from the spec
    alone, so they are filled even on rows where nothing else could be."""
    out: Dict[str, Any] = {key: None for key in DETERMINISTIC_FIELDS}
    out["machine_dependent"] = False
    out["escalate"] = False
    out["n_states"] = 2 ** n
    out["cube_limit"] = n
    return out


def _record(spec: StepSpec, deterministic: Dict[str, Any],
            timing: Dict[str, Any], budget: Optional[float]) -> Dict[str, Any]:
    ordered = {key: deterministic.get(key) for key in DETERMINISTIC_FIELDS}
    timings = {key: timing.get(key) for key in TIMING_FIELDS}
    return {
        "spec": spec.as_json(),
        "budget_seconds": budget,
        "deterministic": ordered,
        "timing": timings,
    }


def build_system(spec: StepSpec):
    """The peg world for this rung, as `engines.ic3_pdr` wants it.

    Imported inside the function so the parent process can drive the ladder
    without dragging the engine into its address space, and so `--spec` failures
    surface in the child where their traceback belongs.
    """
    from engines.ic3_pdr.system import peg_system
    from interop import peg1d

    graph = peg1d.build_graph(spec.n, spec.initial, list(spec.goal_states))
    return peg_system(graph, spec.initial, list(spec.goal_states),
                      name="peg%d" % spec.n)


def measure_in_process(spec: StepSpec) -> Dict[str, Any]:
    """Run one rung here and now, with no budget.  This is the child's body.

    Calls `ic3()` and `verify()` separately rather than `ic3_pdr.run()`, because
    `run()` raises when the independent checker refuses -- which is the correct
    call for an engine and the wrong one for a measurement.  A refusal is the
    single most important thing this ladder could discover, and it has to be
    recorded, escalated and rendered, not turned into a traceback.
    """
    from engines.ic3_pdr import check as ic3_check
    from engines.ic3_pdr import pdr

    deterministic = _blank_deterministic(spec.n)
    timing: Dict[str, Any] = {}

    started = time.perf_counter()
    system = build_system(spec)
    timing["build_seconds"] = round(time.perf_counter() - started, 6)

    mismatches = transcription_mismatches(
        system, spec.n, spec.initial, spec.goal_states
    )
    if mismatches:
        deterministic["verdict"] = ADAPTER_MISMATCH
        deterministic["escalate"] = True
        deterministic["detail"] = (
            "the System is not the peg world it claims to transcribe: %s"
            % "; ".join(mismatches)
        )
        return _record(spec, deterministic, timing, None)

    started = time.perf_counter()
    try:
        verdict = pdr.ic3(system, max_levels=spec.max_levels)
    except pdr.Ic3Error as exc:
        timing["ic3_seconds"] = round(time.perf_counter() - started, 6)
        message = str(exc)
        if message.startswith("no verdict within"):
            deterministic["verdict"] = LEVEL_CAP
            deterministic["detail"] = (
                "%s -- a cap this harness set, not a limit of the engine; "
                "raising max_levels may well change it" % message
            )
        else:
            # The search broke one of its own internal invariants.  `Ic3Error`'s
            # own docstring says this is "never a property verdict", so it is not
            # recorded as one.
            deterministic["verdict"] = ENGINE_REFUSED
            deterministic["escalate"] = True
            deterministic["detail"] = "internal Ic3Error, an engine defect: %s" % message
        return _record(spec, deterministic, timing, None)
    timing["ic3_seconds"] = round(time.perf_counter() - started, 6)

    started = time.perf_counter()
    if isinstance(verdict, pdr.Invariant):
        result = ic3_check.verify(system, verdict.clauses)
        timing["check_seconds"] = round(time.perf_counter() - started, 6)

        widths = sorted(len(clause) for clause in verdict.clauses)
        # The engine reports `n_clauses` and nothing about literals; there is no
        # `n_literals` on `Invariant` to read, and the test suite pins that.  It
        # is summed here, from the clause set the engine actually returned.
        n_literals = sum(widths)
        n_clauses = len(verdict.clauses)

        deterministic.update({
            "n_clauses": n_clauses,
            "n_literals": n_literals,
            "widest_clause": widths[-1] if widths else None,
            "narrowest_clause": widths[0] if widths else None,
            "literal_saturation": (
                round(n_literals / float(n_clauses * spec.n), 6)
                if n_clauses and spec.n else None
            ),
            "converged_at_frame": verdict.level,
            "states_blocked": verdict.blocked,
            "literals_dropped": verdict.generalised_literals,
            "clauses_dropped": verdict.clauses_dropped,
            "cnf_text": system.render_cnf(verdict.clauses),
            "checker_conditions": dict(sorted(result.conditions.items())),
            "n_satisfying": result.n_satisfying,
            "coverage": "%d/%d" % (result.n_satisfying, result.n_states),
            "coverage_ratio": round(result.n_satisfying / float(result.n_states), 6),
        })
        deterministic["near_vacuous"] = bool(
            deterministic["coverage_ratio"] >= NEAR_VACUOUS_RATIO
        )
        if result.holds:
            deterministic["verdict"] = INVARIANT
        else:
            deterministic["verdict"] = ENGINE_REFUSED
            deterministic["escalate"] = True
            deterministic["detail"] = (
                "engines.ic3_pdr.check.verify REFUSED the invariant the search "
                "returned -- an engine defect, not a boundary: %s"
                % json.dumps({k: sorted(v) for k, v in sorted(result.witnesses.items())},
                             sort_keys=True)
            )
        return _record(spec, deterministic, timing, None)

    replayed = ic3_check.replay(system, verdict.states, verdict.moves)
    timing["check_seconds"] = round(time.perf_counter() - started, 6)
    deterministic["counterexample_length"] = verdict.length
    deterministic["checker_conditions"] = {"replayed": bool(replayed)}
    if replayed:
        deterministic["verdict"] = COUNTEREXAMPLE
        deterministic["detail"] = "%s reaches %s in %d move(s)" % (
            system.render_state(verdict.states[0]),
            system.render_state(verdict.states[-1]),
            verdict.length,
        )
    else:
        deterministic["verdict"] = ENGINE_REFUSED
        deterministic["escalate"] = True
        deterministic["detail"] = (
            "engines.ic3_pdr.check.replay REFUSED the counterexample the search "
            "returned -- an engine defect, not a boundary"
        )
    return _record(spec, deterministic, timing, None)


# --------------------------------------------------------------- the subprocess

def _engine_rig_dir() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _child_environment() -> Dict[str, str]:
    env = dict(os.environ)
    # Belt and braces: every loop in the engine is explicitly sorted, so hash
    # randomisation cannot reorder anything -- but a measurement that leans on
    # that should say so out loud rather than rely on it silently.
    env["PYTHONHASHSEED"] = "0"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def run_step(spec: StepSpec,
             timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
             python: Optional[str] = None) -> Dict[str, Any]:
    """One rung, in a child process, under a wall-clock budget.

    The budget is the only thing here the engine cannot do for itself, and it is
    the reason this runs out of process at all.  `subprocess.run(timeout=)` kills
    the child on expiry on every platform this rig runs on; `signal.alarm` would
    not work on Windows and a thread could not interrupt a tight Python loop.
    """
    command = [
        python or sys.executable, "-m", "ic3bounds.harness",
        "--spec", json.dumps(spec.as_json(), sort_keys=True),
    ]
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            cwd=_engine_rig_dir(),
            env=_child_environment(),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        wall = time.perf_counter() - started
        deterministic = _blank_deterministic(spec.n)
        deterministic["verdict"] = TIMEOUT
        # The one deterministic field that is not.  Said here rather than left
        # for a reader to work out, because a verify pass that compared this row
        # for equality on a faster machine would report a defect that is not one.
        deterministic["machine_dependent"] = True
        deterministic["detail"] = (
            "killed after %.1fs of wall clock by this harness, on this machine. "
            "This is a statement about the budget and the hardware, NOT about "
            "the problem: a longer budget or a faster machine may finish it. "
            "Nothing is claimed about whether max_levels=%d would have bound -- "
            "a killed child reports no frame, so that is not knowable from this "
            "row, and an earlier version of this message asserted it anyway."
            % (timeout_seconds, spec.max_levels)
        )
        return _record(spec, deterministic, {"wall_seconds": round(wall, 6)},
                       timeout_seconds)

    wall = time.perf_counter() - started
    payload = _parse_child_output(completed.stdout or "")
    if payload is None:
        deterministic = _blank_deterministic(spec.n)
        deterministic["verdict"] = ENGINE_REFUSED
        deterministic["escalate"] = True
        tail = ((completed.stderr or "") or (completed.stdout or ""))[-400:]
        deterministic["detail"] = (
            "the child produced no record (exit %d) -- a crash, an OOM or an "
            "import failure, all of which are defects in the engine or the rig "
            "rather than boundaries of the problem: %s"
            % (completed.returncode, tail.strip())
        )
        return _record(spec, deterministic, {"wall_seconds": round(wall, 6)},
                       timeout_seconds)

    payload["budget_seconds"] = timeout_seconds
    payload["timing"]["wall_seconds"] = round(wall, 6)
    return payload


def _parse_child_output(stdout: str) -> Optional[Dict[str, Any]]:
    for line in reversed(stdout.splitlines()):
        if line.startswith(SENTINEL):
            return json.loads(line[len(SENTINEL):])
    return None


# ------------------------------------------------------------- the verify side

def deterministic_differences(recorded: Dict[str, Any],
                              fresh: Dict[str, Any]) -> List[str]:
    """Field-by-field diff of two records' deterministic halves.

    The contract a verify pass runs on: everything here is re-derived and
    compared exactly, with one carve-out.  A `timeout` row is flagged
    `machine_dependent`, and for those only the verdict and the budget are
    compared -- the counters behind a killed run do not exist to compare, and a
    faster machine finishing what this one could not is news, not a failure.
    """
    left = recorded.get("deterministic", {})
    right = fresh.get("deterministic", {})
    problems: List[str] = []

    if left.get("verdict") != right.get("verdict"):
        problems.append(
            "verdict: recorded %r, re-derived %r"
            % (left.get("verdict"), right.get("verdict"))
        )
        return problems

    if left.get("machine_dependent"):
        if recorded.get("budget_seconds") != fresh.get("budget_seconds"):
            problems.append(
                "budget_seconds: recorded %r, re-derived %r (a machine-dependent "
                "row is only comparable under the same budget)"
                % (recorded.get("budget_seconds"), fresh.get("budget_seconds"))
            )
        return problems

    for field in DETERMINISTIC_FIELDS:
        if field == "detail":
            continue        # prose, and the counterexample branch renders states
        if left.get(field) != right.get(field):
            problems.append(
                "%s: recorded %r, re-derived %r"
                % (field, left.get(field), right.get(field))
            )
    return problems


def timing_problems(record: Dict[str, Any]) -> List[str]:
    """Presence and ordering.  Never equality -- see `bench/README.md` rule 3."""
    timing = record.get("timing") or {}
    wall = timing.get("wall_seconds")
    problems: List[str] = []
    if wall is None:
        problems.append("%s: no wall clock recorded" % record["spec"]["label"])
        return problems
    inner = sum(
        value for key, value in timing.items()
        if key != "wall_seconds" and isinstance(value, (int, float))
    )
    if inner > wall + 1e-6:
        problems.append(
            "%s: the engine's own clocks sum to %.6fs, more than the %.6fs the "
            "caller waited around the subprocess -- impossible, so one is misread"
            % (record["spec"]["label"], inner, wall)
        )
    return problems


# ------------------------------------------------------------------- the child

def _child_main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="ic3bounds.harness")
    parser.add_argument("--spec", required=True, help="a StepSpec as JSON")
    args = parser.parse_args(argv)
    spec = StepSpec.from_json(json.loads(args.spec))
    record = measure_in_process(spec)
    sys.stdout.write(SENTINEL + json.dumps(record, sort_keys=False) + "\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(_child_main())
