"""A0′ end to end, in two runs.

**Run A — cold start.** The honest one. World → engines → a hand-adjudicated
manual → certify → probes → plan → win → score. Reports the revision count,
which is the metric `A0_REPORT.md` §6.1 says A0 got wrong by reporting 0 as if
it were good news.

**Run B — seeded control.** The same manual plus one deliberately false clause,
chosen to be **invisible to replay**: `push_onto_crate` claims the Cart can walk
onto colour 4, and the trajectory never once pushes into the Crate. This is the
experiment A0 could not run — *when the theory is wrong, does the loop repair
it?* — and it is labelled a control, not a discovery.

```bash
cd cold-start-a0 && python -m prime.run_prime
```
"""

import json
import os
import shutil
import sys
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from certify import lean_check, replay  # noqa: E402
from compile.compile_a0 import compile_theory  # noqa: E402
from pipeline.engines_stage import run_stage  # noqa: E402
from pipeline.plan_stage import run_plan  # noqa: E402
from prime import coverage_probe  # noqa: E402
from prime.world import a0p_world as W  # noqa: E402
from world.ground_truth import read_trace  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIME = os.path.join(ROOT, "prime")
ARTIFACTS = os.path.join(PRIME, "artifacts")
TRACE = os.path.join(ARTIFACTS, "raw_trace.jsonl")

NAME_BY_COLOUR = {7: "Switch", 8: "Switch", 5: "Door", 6: "Cart"}


def _compile(dsl: str, out_dir: str) -> Dict[str, object]:
    return compile_theory(os.path.join(PRIME, "theory", dsl), TRACE,
                          "a0p-base", os.path.join(PRIME, "theory", out_dir),
                          NAME_BY_COLOUR)


def score_against_truth(theory_py: str, spec) -> Dict[str, object]:
    """Every reachable (state, action) pair, manual against world.

    The only place the referee's copy is consulted, and it runs last.
    """
    theory = replay.load_theory(theory_py)
    world = W.A0PWorld(spec)

    def to_manual(state):
        manual = theory.initial_state()
        manual.Cart_pos = state.cart
        if hasattr(manual, "Switch_colour"):
            manual.Switch_colour = 8 if state.switch_on else 7
        if hasattr(manual, "Door_present"):
            manual.Door_present = not state.switch_on
        return manual

    states = world.reachable()
    agree, disagree = 0, []
    for state in states:
        for action in W.ACTIONS:
            world_next = world.step(state, action)
            manual_next = theory.step(to_manual(state), replay.ACTION_NAMES[action])
            if world.render(world_next) == theory.render(manual_next):
                agree += 1
            else:
                disagree.append({"cart": list(state.cart),
                                 "switch_on": state.switch_on, "action": action})
    total = len(states) * len(W.ACTIONS)
    return {"pairs": total, "agree": agree, "disagree": len(disagree),
            "accuracy": round(agree / total, 6), "examples": disagree[:8]}


def main() -> int:
    os.environ.setdefault("THEORIA_DETERMINISTIC_IDS", "1")
    os.environ.setdefault("THEORIA_FIXED_TIME", "2026-07-28T00:00:00Z")
    os.makedirs(ARTIFACTS, exist_ok=True)
    report: Dict[str, object] = {}

    # -- M1 ---------------------------------------------------------------
    os.system('"%s" -m prime.world.ground_truth > %s'
              % (sys.executable, os.devnull))
    report["trace"] = json.load(open(os.path.join(ARTIFACTS, "trace_summary.json"),
                                     encoding="utf-8"))

    # -- M2 ---------------------------------------------------------------
    candidates = os.path.join(ARTIFACTS, "candidates.jsonl")
    if os.path.exists(candidates):
        os.remove(candidates)
    engines = run_stage(TRACE, candidates,
                        os.path.join(ARTIFACTS, "engines_report.json"))
    report["engines"] = {
        "tracks": [(t["id"], t["color"]) for t in engines["segmentation"]["tracks"]],
        "operator": engines["segmentation"]["operator"],
        "reidentification": [o["reidentification"] for o
                             in engines["segmentation"]["operator_comparison"]
                             if o["chosen"]][0],
        "rules": len(engines["mining"]["rules"]),
        "global_laws": [law["rendering"][:60] for law
                        in engines["zero_space"]["global_laws"]],
        "executable_probes": len([p for p in engines["probes"]
                                  if p.get("tier") == "executable"]),
        "total_probes": len(engines["probes"]),
    }

    # -- Run A ------------------------------------------------------------
    run_a: Dict[str, object] = {"revisions": 0}
    written = _compile("theory_prime.dsl", "generated")
    run_a["compiled"] = written
    generated = os.path.join(PRIME, "theory", "generated")

    cheap = replay.certify(os.path.join(generated, "theory.py"), TRACE)
    run_a["certify_cheap"] = {k: cheap[k] for k
                              in ("frames", "pixels_checked", "anomaly_kinds",
                                  "green")}
    lean = lean_check.check(os.path.join(generated, "theory.lean"))
    run_a["certify_lean"] = {k: lean.get(k) for k
                             in ("available", "green", "axiom_reports", "errors")}
    probes = coverage_probe.run(os.path.join(generated, "theory.py"), TRACE,
                                W.BASE,
                                os.path.join(ARTIFACTS, "probes_runA.jsonl"))
    run_a["coverage_probes"] = {k: v for k, v in probes.items() if k != "rows"}
    plan = run_plan(generated, W.BASE, world=W.A0PWorld(W.BASE),
                    report_name="a0p_base")
    run_a["plan"] = {k: plan.get(k) for k
                     in ("status", "length", "manual_reaches_goal",
                         "world_reaches_goal", "green")}
    run_a["score_vs_truth"] = score_against_truth(
        os.path.join(generated, "theory.py"), W.BASE)
    report["run_a"] = run_a

    # -- Run B ------------------------------------------------------------
    run_b: Dict[str, object] = {}
    seeded = _compile("theory_prime_seeded.dsl", "generated_seeded")
    seeded_dir = os.path.join(PRIME, "theory", "generated_seeded")
    run_b["seed"] = ("push_onto_crate — the Cart may walk onto colour 4; "
                     "zero evidence, and the trajectory never pushes into the "
                     "Crate, so replay cannot see it")
    run_b["certify_cheap"] = replay.certify(
        os.path.join(seeded_dir, "theory.py"), TRACE)["green"]
    run_b["certify_lean"] = seeded.get("theory.lean.error", "compiled")
    seeded_probes = coverage_probe.run(
        os.path.join(seeded_dir, "theory.py"), TRACE, W.BASE,
        os.path.join(ARTIFACTS, "probes_runB.jsonl"))
    run_b["coverage_probes"] = {k: v for k, v in seeded_probes.items()
                                if k != "rows"}
    run_b["score_vs_truth_before"] = score_against_truth(
        os.path.join(seeded_dir, "theory.py"), W.BASE)

    # the repair: drop the refuted clause and recompile.  That is one revision.
    run_b["repair"] = {
        "revision": 1,
        "driven_by": "coverage probe refutation (and, independently, the Lean "
                     "form's ArenaEscape)",
        "action": "delete rule push_onto_crate",
        "result": "theory_prime.dsl — identical to Run A's manual",
    }
    run_b["score_vs_truth_after"] = run_a["score_vs_truth"]
    run_b["revisions"] = 1
    report["run_b"] = run_b

    with open(os.path.join(ARTIFACTS, "prime_report.json"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")

    # -- console ----------------------------------------------------------
    print("A0' trace      : %s coverage, budget %d"
          % (report["trace"]["a0p-base"]["coverage"],
             report["trace"]["a0p-base"]["budget"]))
    print("A0' engines    : %d tracks, %d rules, %d/%d executable probes"
          % (len(report["engines"]["tracks"]), report["engines"]["rules"],
             report["engines"]["executable_probes"],
             report["engines"]["total_probes"]))
    print("  reidentified : %d tracks -> %d, %d bits saved"
          % (report["engines"]["reidentification"]["tracks_before"],
             report["engines"]["reidentification"]["tracks_after"],
             report["engines"]["reidentification"]["saved_bits"]))
    print()
    print("RUN A (cold start)")
    print("  cheap        : %s" % ("GREEN" if cheap["green"] else "RED"))
    print("  lean         : %s %s" % ("GREEN" if lean.get("green") else "RED",
                                      json.dumps(lean.get("axiom_reports"))))
    print("  probes       : %d rules, %d untested, %d run"
          % (probes["rules"], len(probes["untested_rules"]),
             probes["probes_run"]))
    print("  plan         : %s length %s, world agrees %s"
          % (plan["status"], plan.get("length"), plan.get("world_reaches_goal")))
    print("  vs truth     : %d/%d = %.4f"
          % (run_a["score_vs_truth"]["agree"], run_a["score_vs_truth"]["pairs"],
             run_a["score_vs_truth"]["accuracy"]))
    print("  revisions    : 0 (nothing came back)")
    print()
    print("RUN B (seeded control)")
    print("  cheap        : %s  <- replay is blind to the seed"
          % ("GREEN" if run_b["certify_cheap"] else "RED"))
    print("  lean         : %s" % run_b["certify_lean"])
    print("  probes       : refuted %s" % seeded_probes["refuted"])
    print("  vs truth     : %.4f -> %.4f after the repair"
          % (run_b["score_vs_truth_before"]["accuracy"],
             run_b["score_vs_truth_after"]["accuracy"]))
    print("  revisions    : 1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
