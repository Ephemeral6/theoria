"""N1 -- a real HiGHS iteration limit is not a proof that no linear pagoda exists.

E15 item P4, first negative control.  Run it from `engine-rig/`:

    python runs/20260729T044500Z-E15-solver-status-bit/controls/n1_iteration_limit.py

Exit **0** iff the property holds, exit **1** on any violation.  The verdict is
also written to `artifacts/n1-iteration-limit.json` (`--out-dir` to relocate),
because the pre-registration judges this control on its exit code *and* on
fields of the artifact it writes -- never on the return value of an internal
function, which is the thing under test.

## What makes this a control rather than a demonstration

The peg4 configuration `0111` genuinely has **no linear pagoda** inside the box:
called normally, HiGHS proves the LP infeasible (status 2) and
`lp_potential.run` correctly returns `(None, None)`.  This control calls the
**same engine on the same configuration** and changes exactly one thing -- a
genuine `maxiter` solver option, passed through to `scipy.optimize.linprog`, so
that a real HiGHS run stops on its iteration limit (status 1).

Nothing is stubbed, mocked or monkeypatched.  `potential.linprog` is the real
one; the only lever is a budget, which is what the defect was about.  A test
that substitutes a fake result object proves the branch is reachable, not that
HiGHS ever reaches it -- `tests/test_tool_failure_is_not_truth.py` has that
version, and it is the weaker half.

Before E15 both runs above returned the identical bare `None`, so a reader could
not tell "this configuration admits no linear pagoda" from "HiGHS ran out of
iterations".  Both readings arrive at the caller as the same value, and the
caller's docstring reads that value as the geometric fact.  So this control
asserts the two are now distinguishable:

  * the budgeted run is **not** `no_linear_pagoda` (it is `budget`),
  * its `decided` is **false**,
  * `lp_potential.run` **refuses** it -- raises `LpUnavailable` -- rather than
    returning `(None, None)`,
  * while the unbudgeted run on the same configuration still returns
    `(None, None)`, so the refusal is a distinction and not a blanket "no".

That last check is what keeps the control from being satisfiable by an engine
that has simply stopped answering.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
RIG = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
if RIG not in sys.path:
    sys.path.insert(0, RIG)

from common.jsonio import read_json                       # noqa: E402
from engines import lp_potential                          # noqa: E402
from engines.lp_potential import potential                # noqa: E402
from fixtures import peg4                                 # noqa: E402

CONTROL = "N1"
TITLE = "a real HiGHS iteration limit is not an infeasibility"

#: The configuration is chosen so that the *honest* answer here is the one the
#: iteration limit used to counterfeit: `0111` is infeasible at `bound=10`.
INITIAL = "0111"

#: A real solver option, handed to `linprog` unchanged.  Zero iterations is the
#: cheapest way to a genuine HiGHS status 1 and needs no giant instance.
SOLVER_OPTIONS = {"maxiter": 0}

HIGHS_ITERATION_LIMIT = 1
HIGHS_INFEASIBLE = 2


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=TITLE)
    parser.add_argument("--out-dir", default=os.path.join(HERE, "artifacts"),
                        help="where the verdict artifact is written")
    args = parser.parse_args(argv)

    out_dir = os.path.abspath(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, "n1-iteration-limit.json")
    sidecar_path = os.path.join(out_dir, "n1-outcome.json")
    if os.path.exists(sidecar_path):
        os.remove(sidecar_path)

    checks = []

    def check(name, condition, detail=""):
        # `is True`, never truthiness: under a collapsed engine the observed
        # value is `None`, and `not None` would sail through a laxer test.
        passed = condition is True
        checks.append({"name": name, "passed": passed, "detail": str(detail)})
        print(("  PASS  " if passed else "  FAIL  ") + name
              + (" -- " + str(detail) if detail else ""))
        return passed

    print("%s: %s" % (CONTROL, TITLE))
    print("  fixture      %s" % os.path.relpath(peg4.GRAPH_PATH, RIG).replace(os.sep, "/"))
    print("  initial      %s" % INITIAL)
    print("  options      %r  (passed straight to scipy.optimize.linprog)" % SOLVER_OPTIONS)
    print("  solver       %s  (not stubbed, not monkeypatched)" % potential.linprog)

    graph = read_json(peg4.GRAPH_PATH)
    observed = {}

    # ---------------------------------------------- 1. the budgeted engine call
    outcome = None
    try:
        outcome = lp_potential.decide(graph, INITIAL,
                                      solver_options=SOLVER_OPTIONS,
                                      outcome_path=sidecar_path)
    except Exception as exc:                      # noqa: BLE001 -- reported, not swallowed
        observed["decide_raised"] = "%s: %s" % (type(exc).__name__, exc)
        traceback.print_exc()

    status = getattr(outcome, "status", None)
    solver_status = getattr(outcome, "solver_status", None)
    decided = getattr(outcome, "decided", None)
    no_pagoda = getattr(outcome, "no_linear_pagoda", None)
    observed["outcome_type"] = type(outcome).__name__
    observed["status"] = status
    observed["solver_status"] = solver_status
    observed["decided"] = decided
    observed["no_linear_pagoda"] = no_pagoda

    check("the budgeted call really reached a HiGHS iteration limit",
          solver_status == HIGHS_ITERATION_LIMIT,
          "solver_status=%r (want %d); %r"
          % (solver_status, HIGHS_ITERATION_LIMIT,
             getattr(outcome, "solver_message", None)))
    check("the engine hands back a structured outcome, not a bare value",
          isinstance(outcome, potential.LpOutcome),
          "got %r" % (type(outcome).__name__,))
    check("its status word names the budget",
          status == potential.BUDGET, "status=%r" % (status,))
    check("it is NOT no_linear_pagoda",
          status != potential.NO_LINEAR_PAGODA and no_pagoda is False,
          "status=%r no_linear_pagoda=%r" % (status, no_pagoda))
    check("decided is false", decided is False, "decided=%r" % (decided,))

    # ------------------------------------------- 2. the public entry point
    refused = None
    try:
        returned = lp_potential.run(graph, INITIAL, solver_options=SOLVER_OPTIONS)
        refused = False
        observed["run_returned"] = repr(returned)
    except potential.LpUnavailable as exc:
        refused = True
        observed["run_raised"] = "LpUnavailable: %s" % exc
        observed["run_raised_status"] = getattr(
            getattr(exc, "outcome", None), "status", None)
    except Exception as exc:                      # noqa: BLE001
        refused = False
        observed["run_raised"] = "%s: %s" % (type(exc).__name__, exc)
        traceback.print_exc()

    check("the public entry refuses instead of returning (None, None)",
          refused is True,
          observed.get("run_returned", observed.get("run_raised", "")))
    check("the refusal carries the specific status word",
          observed.get("run_raised_status") == potential.BUDGET,
          "exception.outcome.status=%r" % (observed.get("run_raised_status"),))

    # ------------------------- 3. the contrast: the real answer is still reachable
    #
    # Without this the control is satisfiable by an engine that refuses
    # everything, which would be a different defect wearing the fix's clothes.
    baseline_status = None
    baseline_returned = None
    try:
        baseline = lp_potential.decide(graph, INITIAL)
        baseline_status = getattr(baseline, "status", None)
        baseline_returned = lp_potential.run(graph, INITIAL)
    except Exception as exc:                      # noqa: BLE001
        observed["baseline_raised"] = "%s: %s" % (type(exc).__name__, exc)
        traceback.print_exc()
    observed["baseline_status"] = baseline_status
    observed["baseline_solver_status"] = getattr(baseline_returned, "solver_status", None)
    observed["baseline_run_returned"] = repr(baseline_returned)

    check("unbudgeted, the SAME configuration is a proved infeasibility",
          baseline_status == potential.NO_LINEAR_PAGODA,
          "status=%r" % (baseline_status,))
    check("and (None, None) is still what that returns",
          baseline_returned == (None, None),
          "run(...) -> %r" % (baseline_returned,))

    # ------------------------------------------------- 4. the engine's own sidecar
    sidecar = None
    if os.path.exists(sidecar_path):
        with open(sidecar_path, "r", encoding="utf-8") as handle:
            sidecar = json.load(handle)
    observed["sidecar"] = sidecar
    required = ("status", "solver_status", "bound", "margin", "decided")
    check("the engine wrote a sidecar a consumer can read the classification off",
          isinstance(sidecar, dict) and all(k in sidecar for k in required),
          "keys=%r" % (sorted(sidecar) if isinstance(sidecar, dict) else None,))
    check("and the sidecar says budget, undecided",
          isinstance(sidecar, dict)
          and sidecar.get("status") == potential.BUDGET
          and sidecar.get("solver_status") == HIGHS_ITERATION_LIMIT
          and sidecar.get("decided") is False
          and sidecar.get("no_linear_pagoda") is False,
          json.dumps({k: (sidecar or {}).get(k) for k in
                      ("status", "solver_status", "decided", "no_linear_pagoda")},
                     sort_keys=True))

    failures = [c["name"] for c in checks if not c["passed"]]
    exit_code = 1 if failures else 0
    report = {
        "control": CONTROL,
        "item": "E15-solver-status-bit",
        "property": TITLE,
        "fixture": os.path.relpath(peg4.GRAPH_PATH, RIG).replace(os.sep, "/"),
        "initial": INITIAL,
        "solver_options": dict(SOLVER_OPTIONS),
        "solver_is_real": "%s.%s" % (potential.linprog.__module__,
                                     getattr(potential.linprog, "__name__", "?")),
        "checks": checks,
        "failures": failures,
        "observed": observed,
        "verdict": "violated" if failures else "hold",
        "exit_code": exit_code,
    }
    with open(report_path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2, sort_keys=True, default=str)
        handle.write("\n")

    print("")
    print("  artifact     %s" % report_path)
    if failures:
        print("VIOLATED: " + ", ".join(failures))
    else:
        print("HOLD: an iteration limit is reported as a budget, not as a "
              "geometric fact, and the public entry refuses it.")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
