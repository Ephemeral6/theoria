"""The level-1 cold-start arm, end to end — and A3's acceptance test.

One driver, five beats, no branches:

    1. problem   `from_trace(l1_sweep.jsonl)` — the cold start pays for a full
                 sweep, 333 frames and 332 actions, and gets everything the
                 pixels hold.  `goal_cell`, `exit_a` and `exit_b` are supplied,
                 on this arm exactly as on the transfer arm, so the two are
                 comparable (see `problem_frame`).
    2. compile   `theory/domain.dsl` + that problem -> the four co-derived
                 forms, through A0's generators and A3's three workarounds
                 (D-A3-004/005/006).
    2b. compile  the **same** instance again with `invariant_builder=None`,
                 into `theory/generated_l1_vacuous/`.  Kept, not deleted: it is
                 the evidence for trap T4, a Lean certificate that is green,
                 axiom-free, and vacuous.
    3. certify   the cheap layer, against the sweep it was compiled from.
    4. lean      the expensive layer, on both the real and the vacuous form.
    5. plan      `fd_adapter` on the PDDL pair, replayed through `theory.py`.

Required results, which this script asserts nothing about and simply reports,
because a driver that decides what counts as a pass is a driver that can be
argued with:

    cheap   GREEN, 333 frames, 0 anomalies
    plan    SAT, and the plan replayed in the generated theory reaches the goal
    lean    green with an empty axiom list, **if** a toolchain is available;
            otherwise `available: False`, reported as red, never faked

Determinism: `THEORIA_DETERMINISTIC_IDS` and `THEORIA_FIXED_TIME` are set with
`setdefault` before any candidate is made, so ids and timestamps are stable and
two clean runs produce byte-identical artefacts.
"""

import json
import os
import sys
from typing import Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from a3pipeline import certify_a3, plan as plan_mod  # noqa: E402
from a3pipeline.compile_a3 import (  # noqa: E402
    compile_instance, switch_latch_invariant, write_report,
)
from a3pipeline.meter import Meter  # noqa: E402
from a3pipeline.problem_frame import from_trace, write_provenance  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACTS = os.path.join(ROOT, "artifacts")
THEORY = os.path.join(ROOT, "theory")

FIXED_TIME = "2026-07-28T00:00:00Z"

NAME = "a3-l1"
TRACE = os.path.join(ARTIFACTS, "l1_sweep.jsonl")
DSL = os.path.join(THEORY, "domain.dsl")
OUT = os.path.join(THEORY, "generated_l1")
OUT_VACUOUS = os.path.join(THEORY, "generated_l1_vacuous")

GOAL_CELL = (7, 7)
EXIT_A = (1, 6)
EXIT_B = (3, 2)

#: What the arm is expected to produce.  Stated here so the printed summary can
#: be read against it without opening another file, and *not* used as an
#: assertion: the numbers below are observations.
EXPECTED = {
    "cheap_frames": 333,
    "cheap_anomalies": 0,
    "plan_status": "SAT",
}


def run(meter: Meter = None) -> Dict[str, object]:
    os.environ.setdefault("THEORIA_DETERMINISTIC_IDS", "1")
    os.environ.setdefault("THEORIA_FIXED_TIME", FIXED_TIME)
    os.makedirs(ARTIFACTS, exist_ok=True)

    if meter is None:
        meter = Meter(
            arm="l1_cold_start", level="a3-l1", carries_books=False,
            note="the cold start: mines level 1 from its own sweep and writes "
                 "the two books from scratch",
        )

    # ------------------------------------------------------------- 1. problem
    meter.charge_trace(TRACE, "l1_sweep.jsonl — the cold start's whole evidence")
    problem, provenance = from_trace(TRACE, NAME, GOAL_CELL, EXIT_A, EXIT_B)
    write_provenance(os.path.join(ARTIFACTS, "problem_provenance_l1.json"),
                     provenance)

    # ------------------------------------------------------------- 2. compile
    written = compile_instance(DSL, problem, OUT,
                               invariant_builder=switch_latch_invariant)
    meter.charge("compile_runs", 1, "domain.dsl + a3-l1 -> generated_l1")

    # 2b. The same instance, with the invariant builder withheld.  This is the
    # T4 exhibit and it is compiled every run so it cannot go stale against the
    # real one.  It is charged to the meter too — pretending the evidence was
    # free would be the same kind of accounting this whole spike exists to
    # avoid.
    written_vacuous = compile_instance(DSL, problem, OUT_VACUOUS,
                                       invariant_builder=None)
    meter.charge("compile_runs", 1,
                 "the same instance with no invariant builder — the T4 exhibit")

    # ------------------------------------------------------------- 3. certify
    cheap = certify_a3.cheap(os.path.join(OUT, "theory.py"), TRACE)
    meter.charge("certify_runs", 1, "cheap replay of generated_l1 over l1_sweep")

    # ---------------------------------------------------------------- 4. lean
    lean = certify_a3.lean(os.path.join(OUT, "theory.lean"))
    meter.charge("certify_runs", 1, "lean on generated_l1")
    lean_vacuous = certify_a3.lean(os.path.join(OUT_VACUOUS, "theory.lean"))
    meter.charge("certify_runs", 1, "lean on the vacuous T4 exhibit")

    certify_a3.write_report(
        os.path.join(ARTIFACTS, "certify_generated_l1.json"),
        {"cheap": cheap,
         "lean": certify_a3.lean_brief(lean),
         "lean_vacuous": certify_a3.lean_brief(lean_vacuous)})

    # ---------------------------------------------------------------- 5. plan
    plan = plan_mod.run_plan(
        OUT, "generated_l1", meter=meter,
        candidates_path=os.path.join(ARTIFACTS,
                                     "candidates_plan_generated_l1.jsonl"),
        timestamp=FIXED_TIME)

    meter.write(os.path.join(ARTIFACTS, "meter_l1_cold_start.json"))

    report = {
        "arm": "l1_cold_start",
        "expected": EXPECTED,
        "problem_provenance": provenance,
        "compile": written,
        "compile_vacuous": written_vacuous,
        "cheap": certify_a3.cheap_brief(cheap),
        "cheap_anomalies": (cheap.get("anomalies") or [])[:8],
        "lean": certify_a3.lean_brief(lean),
        "lean_vacuous": certify_a3.lean_brief(lean_vacuous),
        "plan": {k: v for k, v in plan.items() if k != "manual_trail"},
        "meter": meter.as_json()["counts"],
        "green": bool(cheap.get("green")) and bool(plan.get("green")),
    }
    write_report(os.path.join(ARTIFACTS, "run_l1.json"), report)
    return report


def main() -> int:
    report = run()
    cheap, lean, lean_v, plan = (report["cheap"], report["lean"],
                                 report["lean_vacuous"], report["plan"])

    print("== A3 level-1 cold start ==")
    prov = report["problem_provenance"]
    print("problem  %s: %d fields derived, %d supplied (%s); read %d frames, "
          "%d actions"
          % (prov["route"], prov["derived_fields"], prov["supplied_fields"],
             ", ".join(f for f, how in sorted(prov["fields"].items())
                       if how == "supplied"),
             prov["inputs_read"]["frames"], prov["inputs_read"]["actions"]))
    print("compile  %s" % ", ".join(
        "%s %d B" % (k, v) for k, v in sorted(report["compile"].items())
        if isinstance(v, int)))
    print("         PDDL cells added (D-A3-006): %s | landmark predicates "
          "(D-A3-005): %s | goal bound (D-A3-004): %s"
          % (report["compile"]["pddl_cells_added"],
             report["compile"]["pddl_landmarks"]["predicates"],
             report["compile"]["goal_bound"]))

    print("cheap    %-5s %d frames, %d transitions, %d anomalies %s"
          % ("GREEN" if cheap["green"] else "RED", cheap["frames"],
             cheap["transitions"], cheap["anomaly_count"],
             cheap["anomaly_kinds"] or ""))
    for anomaly in report["cheap_anomalies"]:
        print("         ", json.dumps(anomaly, sort_keys=True))

    if not lean["available"]:
        print("lean     UNAVAILABLE — %s" % lean["reason"])
    else:
        print("lean     %-5s rc=%s axioms=%s errors=%d sorries=%d  (%s)"
              % ("GREEN" if lean["green"] else "RED", lean["returncode"],
                 json.dumps(lean["axiom_reports"]), len(lean["errors"]),
                 len(lean["sorries"]), lean["lean"]))
        for line in lean["errors"][:8]:
            print("         ", line)
        print("lean(T4) %-5s axioms=%s  <- the VACUOUS exhibit: green, "
              "axiom-free, and it proves nothing"
              % ("GREEN" if lean_v["green"] else "RED",
                 json.dumps(lean_v["axiom_reports"])))

    if plan["status"] == "UNSAT":
        print("plan     UNSAT — %s" % plan.get("note"))
    else:
        print("plan     %-5s %s length %d via %s; manual reaches goal: %s"
              % ("SAT" if plan["status"] == "SAT" else plan["status"],
                 "GREEN" if plan["green"] else "RED",
                 plan["length"], plan["backend"], plan["manual_reaches_goal"]))
        print("         %s" % " ".join(plan["world_actions"]))

    print("meter    %s" % json.dumps(report["meter"], sort_keys=True))
    print("overall  %s (cheap + plan; the Lean layer is reported separately "
          "because a missing toolchain is not a failed manual)"
          % ("GREEN" if report["green"] else "RED"))
    return 0 if report["green"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
