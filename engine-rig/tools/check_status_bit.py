"""Standing negative controls: a solver's silence must keep its reason attached.

    python -m tools.check_status_bit [--json]      # exit 1 on a violation

Two controls, both through the engines' **public entry points**, both judged on
what the process does and on the fields of the artifact it writes -- not on the
return value of an internal function.  Each is written so that reverting the fix
it guards makes it exit 1; that non-vacuity is demonstrated in
`runs/20260729T044500Z-E15-solver-status-bit/NONVACUITY.md` rather than asserted
here.

**N1 -- an iteration limit is not a geometric fact.**  `lp_potential` reports
silence when no linear pagoda separates the goal from the start.  That silence is
a documented boundary of the method (`CLAUDE.md`: sound but incomplete) and not a
defect.  What *is* a defect is silence whose cause has been erased: HiGHS status
1 (iteration limit), 3 (unbounded) and 4 (numerical) used to reach the caller
through the same value as status 2 (proved infeasible).  The control drives the
**real** solver into a **real** iteration limit -- `options={"maxiter": 0}`,
no stubbed result object -- on a world that provably *does* admit a pagoda at the
default budget, and requires the engine to refuse rather than to report that no
pagoda exists.  A world with a certificate is chosen deliberately: under the old
collapse the engine would have published the exact opposite of the truth.

**N2 -- a truncated enumeration does not get to say `global`.**  Above
`SUBSET_ENUMERATION_LIMIT` colours per cell, `zero_space` stops enumerating
colour subsets, so a cell-local law can be missed; the missed law stays in the
quotient and used to be published as `scope: "global"`, i.e. as a law about the
world rather than about the encoding.  Ten colours is an ARC palette, so this is
a live path.  The control runs the real `zero_space.run(..., out_path=...)`, then
reads the emitted candidate stream back off disk and requires that no payload
claims `global`, and that every downgraded payload carries the cap that
downgraded it.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import traceback
from typing import Any, Dict, List, Sequence, Tuple

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:                                     # pragma: no cover
    sys.path.insert(0, HERE)

from engines import lp_potential, zero_space                       # noqa: E402
from engines.zero_space import zerospace                           # noqa: E402

# --------------------------------------------------------------------- N1

#: Campaign world `jumpgraph` index 0 under seed 0x00005EEDC1E4F002 -- the corpus
#: E11 and `runs/20260729T044500Z-E15-solver-status-bit/census.jsonl` both use.
#: Transcribed rather than regenerated so this check does not depend on
#: `fuzzlab/`, which lives outside `engine-rig/`.  Its identity is checkable:
#: `fuzzlab.prng.derive(0x00005EEDC1E4F002, "jumpgraph", 0)` is this seed.
N1_SEED = 7400197045430241762
N1_N_POS = 8
N1_TRIPLES: Tuple[Tuple[int, int, int], ...] = (
    (0, 2, 4), (1, 4, 7), (2, 3, 4), (3, 4, 5), (3, 5, 7),
    (4, 2, 0), (5, 3, 1), (6, 4, 2), (7, 5, 3),
)
N1_INITIAL = "00101100"
N1_GOALS = ("00010100",)


def jump_graph(n: int, triples: Sequence[Tuple[int, int, int]],
               goals: Sequence[str], initial: str) -> Dict[str, Any]:
    """The `n_pos`/`edges`/`goal_states` dict `solve_certificate` reads.

    Only the fields the LP needs; `distance_to_goal` is not built because no
    heuristic report is taken here.
    """
    states = [format(i, "0%db" % n) for i in range(1 << n)]
    edges = []
    for state in states:
        for src, over, dst in triples:
            if state[src] == "1" and state[over] == "1" and state[dst] == "0":
                cells = list(state)
                cells[src] = cells[over] = "0"
                cells[dst] = "1"
                edges.append({
                    "src_state": state,
                    "move": "jump(%d,%d,%d)" % (src, over, dst),
                    "positions": [src, over, dst],
                    "dst_state": "".join(cells),
                })
    return {
        "n_pos": n,
        "goal_states": list(goals),
        "states": states,
        "edges": edges,
        "initial_configs": [initial],
    }


def control_iteration_limit() -> Dict[str, Any]:
    graph = jump_graph(N1_N_POS, N1_TRIPLES, N1_GOALS, N1_INITIAL)
    failures: List[str] = []

    # (a) At the default budget this world *has* a linear pagoda.  Without this
    #     line the control would be satisfied by an engine that simply never
    #     certifies anything, and "silence for a reason" would be untested.
    baseline = lp_potential.decide(graph, N1_INITIAL)
    if baseline.status != lp_potential.CERTIFIED:
        failures.append(
            "premise lost: world %d no longer certifies at the default budget "
            "(status %r); this control has nothing to say until it does"
            % (N1_SEED, baseline.status)
        )

    # (b) The same world, the same real solver, one iteration.
    with tempfile.TemporaryDirectory() as tmp:
        sidecar = os.path.join(tmp, "outcome.json")
        starved = lp_potential.decide(
            graph, N1_INITIAL, solver_options={"maxiter": 0},
            outcome_path=sidecar,
        )
        with open(sidecar, encoding="utf-8") as handle:
            published = json.load(handle)

    if starved.solver_status != 1:
        failures.append(
            "this control needs a genuine HiGHS iteration limit; got solver "
            "status %r (%s). Not a violation of the engine's contract -- a "
            "violation of the control's premise, and it must not pass quietly."
            % (starved.solver_status, starved.solver_message)
        )
    if starved.no_linear_pagoda:
        failures.append(
            "an iteration limit was reported as 'no linear pagoda exists'"
        )
    if starved.decided:
        failures.append("an undecided outcome reports decided=True")

    # (c) The published artifact, read back, must carry the same refusal.  A
    #     status bit that exists only in memory is not a status bit a reader has.
    if published.get("status") != lp_potential.BUDGET:
        failures.append(
            "artifact status is %r, expected %r"
            % (published.get("status"), lp_potential.BUDGET)
        )
    if published.get("no_linear_pagoda") is not False:
        failures.append(
            "artifact claims no_linear_pagoda=%r on an iteration limit"
            % (published.get("no_linear_pagoda"),)
        )
    if published.get("decided") is not False:
        failures.append("artifact claims decided=%r" % (published.get("decided"),))

    # (d) The pair-returning entry must refuse, not answer.  `(None, None)` is
    #     read downstream as "no linear pagoda", so returning it here would be
    #     the original defect wearing the new field names.
    try:
        pair = lp_potential.run(graph, N1_INITIAL, solver_options={"maxiter": 0})
    except lp_potential.LpUnavailable as exc:
        pair = None
        if getattr(exc, "outcome", None) is None:
            failures.append("LpUnavailable carries no outcome")
        elif exc.outcome.status != lp_potential.BUDGET:
            failures.append(
                "LpUnavailable carries status %r" % (exc.outcome.status,))
    if pair is not None:
        failures.append(
            "lp_potential.run returned %r under an iteration limit instead of "
            "refusing; a caller cannot tell this from 'no pagoda exists'"
            % (pair,)
        )

    return {
        "control": "N1-iteration-limit-is-not-an-infeasibility",
        "entry_points": ["engines.lp_potential.decide",
                         "engines.lp_potential.run"],
        "world_seed": N1_SEED,
        "baseline_status": baseline.status,
        "starved_status": starved.status,
        "starved_solver_status": starved.solver_status,
        "published": published,
        "failures": failures,
        "held": not failures,
    }


# --------------------------------------------------------------------- N2

#: Ten colours -- one ARC palette -- over two cells, so both cells cross
#: `SUBSET_ENUMERATION_LIMIT`.
N2_COLORS = tuple(chr(ord("a") + i) for i in range(10))
N2_STATES = tuple(
    [N2_COLORS[i % len(N2_COLORS)], N2_COLORS[(i + 1) % len(N2_COLORS)]]
    for i in range(len(N2_COLORS))
)


def control_truncated_scope() -> Dict[str, Any]:
    failures: List[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        out_path = os.path.join(tmp, "candidates.jsonl")
        result = zero_space.run([list(s) for s in N2_STATES], list(N2_COLORS),
                                out_path=out_path)
        emitted = [json.loads(line) for line in
                   open(out_path, encoding="utf-8") if line.strip()]

    if not result.truncated_cells:
        failures.append(
            "premise lost: this palette no longer crosses "
            "SUBSET_ENUMERATION_LIMIT=%d, so nothing here is being tested"
            % zerospace.SUBSET_ENUMERATION_LIMIT
        )

    payloads = [row["payload"] for row in emitted]
    global_rows = [p for p in payloads if p.get("scope") == zerospace.GLOBAL]
    if global_rows:
        failures.append(
            "%d law(s) published scope=%r from a truncated enumeration"
            % (len(global_rows), zerospace.GLOBAL)
        )

    downgraded = [p for p in payloads if p.get("scope") == zerospace.UNDETERMINED]
    if not downgraded:
        failures.append(
            "no law was downgraded, so the run published nothing that could "
            "have been wrong -- check the fixture before believing this"
        )
    for payload in downgraded:
        for key in ("scope_proved", "subset_enumeration_limit",
                    "truncated_cells", "error"):
            if key not in payload:
                failures.append(
                    "a downgraded law omits %r; the budget has to be in the "
                    "product, not only in the engine" % key
                )
        if payload.get("scope_proved") is not False:
            failures.append("a downgraded law claims scope_proved=%r"
                            % (payload.get("scope_proved"),))
        if not payload.get("truncated_cells"):
            failures.append("a downgraded law names no truncated cell")

    run_record = result.as_json()
    if run_record.get("error") is None:
        failures.append("the run-level record carries no error for a "
                        "truncated enumeration")
    if run_record.get("scope_counts", {}).get(zerospace.GLOBAL):
        failures.append("the run-level record counts proved-global laws in a "
                        "truncated run")

    return {
        "control": "N2-truncated-enumeration-is-not-a-global-law",
        "entry_points": ["engines.zero_space.run"],
        "subset_enumeration_limit": zerospace.SUBSET_ENUMERATION_LIMIT,
        "n_colors": len(N2_COLORS),
        "truncated_cells": list(result.truncated_cells),
        "scopes_emitted": sorted({p.get("scope") for p in payloads}),
        "n_downgraded": len(downgraded),
        "example_downgraded": (
            {k: v for k, v in downgraded[0].items() if k != "features"}
            if downgraded else None
        ),
        "run_record": run_record,
        "failures": failures,
        "held": not failures,
    }


CONTROLS = (control_iteration_limit, control_truncated_scope)

#: Names in the same order as `CONTROLS`, so a control that dies before it can
#: name itself still appears in the report under the right heading.
CONTROL_NAMES = ("N1-iteration-limit-is-not-an-infeasibility",
                 "N2-truncated-enumeration-is-not-a-global-law")


def _guarded(control, name: str) -> Dict[str, Any]:
    """Run one control; an exception is a FAILED verdict, not a traceback.

    Found by an adversarial review of E15 and fixed rather than filed.  Under a
    reverted engine `control_iteration_limit` died on `AttributeError:
    'Certificate' object has no attribute 'status'` -- which does exit non-zero,
    so the *gate* was still red, but two things were wrong with it.  An operator
    saw a stack trace instead of `FAILED N1-...`, so the tool's own reporting
    path -- the thing being trusted to describe a regression -- was never
    exercised by the case it exists for.  And `main` built the report list
    eagerly, so N1 crashing meant **N2 never ran**: a simultaneous `zero_space`
    regression would have been invisible behind an unrelated `lp_potential` one.

    A check whose failure mode is "the harness explodes" reports the fact that
    something is broken and nothing about what.  That is a smaller version of
    this item's own complaint, in the instrument rather than in the engine.
    """
    try:
        return control()
    except Exception as exc:                       # noqa: BLE001 -- deliberate
        return {
            "control": name,
            "entry_points": [],
            "failures": ["the control could not complete: %s: %s"
                         % (type(exc).__name__, exc)],
            "raised": "%s: %s" % (type(exc).__name__, exc),
            "traceback": traceback.format_exc(),
            "held": False,
        }


def main(argv: Sequence[str]) -> int:
    as_json = "--json" in argv[1:]
    reports = [_guarded(control, name)
               for control, name in zip(CONTROLS, CONTROL_NAMES)]
    if as_json:
        print(json.dumps({"controls": reports,
                          "held": all(r["held"] for r in reports)},
                         indent=2, sort_keys=True))
    else:
        for report in reports:
            print("%-6s %s" % ("HELD" if report["held"] else "FAILED",
                               report["control"]))
            for failure in report["failures"]:
                print("       - %s" % failure)
    return 0 if all(r["held"] for r in reports) else 1


if __name__ == "__main__":                                   # pragma: no cover
    sys.exit(main(sys.argv))
