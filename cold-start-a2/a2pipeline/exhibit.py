"""M5 — the exhibit: a theorem that type-checks and is false of the world.

This is A2's first acceptance sentence, "仪器造得出展品".  The run is the ordinary
inner loop, unaltered and unassisted, driven from the holed manual and the play
record:

```
certify (cheap)   replay history_trace.jsonl through theory_holed.dsl
                  -> GREEN.  100%.  The deleted rule owes no frame.
plan              theory.pddl -> fd_adapter -> UNSAT
                  constraint 6: a bare UNSAT is not an answer
certificate       zero_space proposes the occupancy laws; the theorize step
                  picks the coset representative that says something
certify (dear)    Lean: inv_init / inv_closed / goal_break / unsolvable,
                  `decide` only, `#print axioms` empty
```

Every gate is green.  The theorem says the Cart can never reach (2,7).  The Cart
can reach (2,7) — `ground_truth.json` carries an 18-action witness, and M6 runs
it.  Nothing in this file is wrong; the planner is right, the invariant really
is closed under the manual's `step`, Lean really did check it, and the axiom
list really is empty.  The manual is wrong, and no amount of checking the manual
against its own past could have said so.

That gap is the two-layer truth regime (Theoria §1.10a): Lean guarantees *true
relative to the manual*; whether the manual matches the world is settled
somewhere else entirely, by §1.4's refutation loop.  M6 onward is that loop.
"""

import json
import os
import sys
from typing import Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from theory_compiler.parser.theory_parser import parse_theory  # noqa: E402

from a2pipeline import certify_a2  # noqa: E402
from a2pipeline.compile_a2 import compile_manual, observed_region  # noqa: E402
from a2pipeline.plan import run_plan  # noqa: E402
from a2world import a2_world  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACTS = os.path.join(ROOT, "artifacts")
TRACE = os.path.join(ARTIFACTS, "history_trace.jsonl")
DSL = os.path.join(ROOT, "theory", "theory_holed.dsl")
OUT = os.path.join(ROOT, "theory", "generated_holed")


def build() -> Dict[str, object]:
    report: Dict[str, object] = {"manual": "theory_holed.dsl",
                                 "evidence": "history_trace.jsonl"}
    report["constructive_ground"] = (
        "column c5 is solid wall from r1 to r7 and rows r0/r8 are solid, so the "
        "right room touches nothing; every rule left in this manual moves the "
        "Cart to an adjacent cell, so the goal cell (2,7) is unreachable under "
        "the manual.  Known before anything is run — which is what Theoria "
        "Phase 1 layer 2 demands of a variant, and what makes the theorem's "
        "falseness a property of the manual rather than of the prover."
    )

    # 1 — the certificate's raw material, from the engine
    region, law = observed_region(TRACE)
    report["zero_space"] = law
    print("law   :", law["rendering"][:88], "... region of %d cells" % law["region_size"])

    comment = (
        "right_room_locked (THEORIZE_LOG L-03), proposed by zero_space as a GF(2)\n"
        "occupancy law and adjudicated into this form.  w = 0 exactly on the %d\n"
        "cells the Cart was ever observed on in history_trace.jsonl; the goal cell\n"
        "carries w = 1.  I(s) := w(cart) = 0 is 'the potential never rises'.\n"
        "\n"
        "THIS INVARIANT IS TRUE OF THE MANUAL AND FALSE OF THE WORLD.  It is closed\n"
        "under the manual's step because the manual has no rule that moves the Cart\n"
        "more than one cell, and the two rooms are not adjacent.  The world has\n"
        "such a rule.  See A2_REPORT.md." % len(region)
    )
    report["compiled"] = compile_manual(DSL, TRACE, "a2-holed", OUT,
                                        region=region, comment=comment,
                                        unsolvable=True)

    # 2 — certify, cheap.  The headline number of the whole spike.
    cheap = certify_a2.cheap(os.path.join(OUT, "theory.py"), TRACE)
    report["certify_cheap"] = {k: cheap[k] for k in
                               ("frames", "transitions", "pixels_checked",
                                "pixels_unexplained", "anomaly_kinds", "green")}
    print("cheap :", certify_a2.summary(cheap))

    # 2b — the same manual against the full sweep, to bound the claim honestly.
    # The hole is invisible *relative to the play record*, not invisible.  Saying
    # only the first half would be the kind of report this project exists to
    # refuse to write.
    full = certify_a2.cheap(os.path.join(OUT, "theory.py"),
                            os.path.join(ARTIFACTS, "raw_trace.jsonl"))
    first = full["anomalies"][0] if full["anomalies"] else None
    report["certify_cheap_vs_full_sweep"] = {
        "frames": full["frames"],
        "green": full["green"],
        "anomalies": len(full["anomalies"]),
        "anomaly_kinds": full["anomaly_kinds"],
        "first_anomaly": first,
        "reading": "the holed manual is green on the play record and red on the "
                   "sweep; the hole is invisible to the evidence its theorizer "
                   "had, which is exactly Theoria §1.3's claim and exactly its "
                   "limit",
    }
    print("sweep :", certify_a2.summary(full), "(expected RED — see the report)")

    # 3 — plan.  UNSAT is the branch this spike is here for.
    plan = run_plan(OUT, "holed", candidates_path=os.path.join(
        ARTIFACTS, "candidates_holed.jsonl"))
    report["plan"] = plan
    print("plan  :", plan["status"])

    # 4 — certify, expensive
    lean = certify_a2.lean(os.path.join(OUT, "theory.lean"))
    report["certify_lean"] = certify_a2.lean_brief(lean)
    print("lean  :", "GREEN" if lean.get("green") else "RED",
          json.dumps(lean.get("axiom_reports")))
    for line in (lean.get("errors") or [])[:6]:
        print("       ", line)

    # 5 — the theorem, in the manual's own words
    ast = parse_theory(open(DSL, encoding="utf-8").read())
    theorem = ast.laws.theorems[0]
    report["theorem"] = {
        "name": theorem.name,
        "explanation": theorem.description,
        "depends": theorem.depends,
        "lean_target": "unsolvable",
        "axioms": [r for r in (lean.get("axiom_reports") or [])
                   if r["name"] == "unsolvable"],
    }

    # 6 — and the world's answer to it, stated here rather than saved for later
    world = a2_world.A2World(a2_world.BASE)
    solution = world.solve()
    report["world_says"] = {
        "goal_reachable": solution is not None,
        "witness_length": len(solution) if solution else None,
        "note": "the referee's copy; the refutation loop is M6 and it re-derives "
                "this by execution rather than by reading it from here",
    }

    report["exhibit_green"] = bool(
        cheap["green"]
        and plan["status"] == "UNSAT"
        and lean.get("green")
        and not lean.get("axiom_reports", [{}])[0].get("axioms", ["x"])
    )
    report["exhibit_is_false_of_the_world"] = bool(solution is not None)
    return report


def main() -> int:
    os.environ.setdefault("THEORIA_DETERMINISTIC_IDS", "1")
    os.environ.setdefault("THEORIA_FIXED_TIME", "2026-07-28T00:00:00Z")
    report = build()
    with open(os.path.join(ARTIFACTS, "exhibit_report.json"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")

    print()
    print("EXHIBIT:", "GREEN" if report["exhibit_green"] else "RED",
          "— type-checks, axiom-free, and",
          "FALSE of the world" if report["exhibit_is_false_of_the_world"]
          else "(not actually false?!)")
    print(report["theorem"]["explanation"])
    return 0 if (report["exhibit_green"]
                 and report["exhibit_is_false_of_the_world"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
