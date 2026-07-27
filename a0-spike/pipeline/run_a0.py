"""A0 cold start, end to end.

    perceive -> mine -> certify -> prove -> plan -> win

and, on the sibling level, the thing a searcher cannot say: *why* it is
impossible. Run with `python -m pipeline.run_a0` from `a0-spike/`.
"""

import json
import os
import sys
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "engine-rig"))

from engines import fd_adapter                                  # noqa: E402
from pipeline import explore, gen_exec, pddl_gen, stages        # noqa: E402
from world import levels, sokoban2                              # noqa: E402

ARTIFACTS = os.path.join(HERE, "artifacts")


def _plan_actions_to_world(plan_actions: List[str]) -> List[str]:
    """PDDL step -> world action. `(walk c3_5 c3_4 left)` -> `LEFT`."""
    return [action.strip("()").split()[-1].upper() for action in plan_actions]


def run() -> Dict[str, Any]:
    report: Dict[str, Any] = {}
    level = levels.MATCH

    # 1. explore -- prefix replay to reach discriminating situations
    evidence = explore.evidence_set(level, per_class=4)
    transitions = stages.transitions_from_episodes(evidence["episodes"])
    report["explore"] = {
        "episodes": evidence["n_episodes"],
        "actions_spent": evidence["action_budget_spent"],
        "transitions": len(transitions),
        "witnessed": evidence["witnessed"],
    }

    # 2. perceive -- on the longest episode: a two-frame clip cannot show the
    # edit script beating a pixel dump, because the object declarations alone
    # cost more than two frames of diff.
    longest = max(evidence["episodes"], key=lambda e: len(e["frames"]))
    perception = stages.perceive(longest["frames"])
    report["perceive"] = {
        "tracks": len(perception["tracks"]),
        "movers": len(perception["movers"]),
        "board": len(perception["board"]),
        "script_bits": perception["script_bits"],
        "baseline_bits": perception["baseline_bits"],
        "ratio": round(perception["ratio"], 4),
    }

    # 3. mine
    rules = stages.mine(transitions)
    report["mine"] = {
        "n_rules": len(rules),
        "rules": [r.as_json() for r in sorted(rules, key=lambda r: r.name)],
    }

    # 4. certify -- full-history replay through the rules alone
    certificate = stages.certify(rules, transitions)
    report["certify"] = certificate

    # 4b. certify through the EXECUTABLE FORM compiled from theory.dsl.
    # The mined rules are engine output; the manual is what we are accountable
    # for, and the only predictor allowed is the one compiled from it.
    dsl_path = os.path.join(HERE, "theory", "theory.dsl")
    module = gen_exec.compile_module(
        open(dsl_path, encoding="utf-8").read(),
        level.height, level.width, level.walls,
        out_path=os.path.join(ARTIFACTS, "theory_exec.py"),
    )
    report["certify_generated"] = stages.certify_generated(module, evidence["episodes"])
    report["certify_generated"]["source"] = "theory/theory.dsl -> artifacts/theory_exec.py"

    # 5. prove -- the conservation law, recovered from the trajectory
    percepts = [t[0] for t in transitions] + [transitions[-1][2]]
    law = stages.prove_parity(percepts)
    report["prove"] = law

    # 6. plan and win, and refuse the impossible with a reason
    report["levels"] = {}
    for name, lvl in levels.LEVELS.items():
        theorem = stages.unsolvability_certificate(lvl)
        entry: Dict[str, Any] = {"theorem": theorem}
        if theorem["unsolvable"]:
            entry["planner_consulted"] = False
            entry["verdict"] = "unsolvable, by the conservation law"
        else:
            domain, problem = pddl_gen.write_files(
                os.path.join(ARTIFACTS, "pddl"), name, lvl.height, lvl.width,
                lvl.walls, lvl.player, lvl.box, lvl.target,
            )
            plan = fd_adapter.solve(domain, problem, prefer="stub")
            actions = _plan_actions_to_world(plan.actions)
            state = sokoban2.initial_state(lvl)
            for action in actions:
                state, _ = sokoban2.step(lvl, state, action)
            entry.update(
                {
                    "planner_consulted": True,
                    "plan": plan.actions,
                    "plan_length": plan.length,
                    "world_actions": actions,
                    "executed_box_at": list(state.box),
                    "won": state.box == lvl.target,
                    "verdict": "solved",
                }
            )
        report["levels"][name] = entry

    # grading, against ground truth we hold only because we built the world
    truth = levels.ground_truth()
    report["grading"] = {
        name: {
            "predicted_solvable": not report["levels"][name]["theorem"]["unsolvable"],
            "actually_solvable": truth[name]["solvable"],
            "agrees": (not report["levels"][name]["theorem"]["unsolvable"])
                      == truth[name]["solvable"],
            "plan_optimal": (
                report["levels"][name].get("plan_length")
                == truth[name]["optimal_plan_length"]
            ),
        }
        for name in levels.LEVELS
    }
    return report


def main() -> int:
    report = run()
    os.makedirs(ARTIFACTS, exist_ok=True)
    path = os.path.join(ARTIFACTS, "a0_report.json")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        json.dump(report, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")

    print("A0 cold start")
    print("-" * 72)
    e = report["explore"]
    print("  explore   %d episodes, %d actions, %d transitions"
          % (e["episodes"], e["actions_spent"], e["transitions"]))
    p = report["perceive"]
    print("  perceive  %d objects (%d move, %d settle into the board); %d vs %d bits"
          % (p["tracks"], p["movers"], p["board"], p["script_bits"], p["baseline_bits"]))
    print("  mine      %d rules" % report["mine"]["n_rules"])
    for rule in report["mine"]["rules"]:
        print("              %-16s %-8s %s"
              % (rule["name"], rule["coverage"], " and ".join(rule["guard"])))
    c = report["certify"]
    print("  certify   %d transitions replayed; exactly-one-successor=%s, exact=%s"
          % (c["transitions"], c["exactly_one_successor"], c["replay_exact"]))
    g = report["certify_generated"]
    print("  certify*  %d frames replayed through theory.dsl -> theory_exec.py; exact=%s"
          % (g["frames_checked"], g["replay_exact"]))
    print("  prove     %s  (conserved: %s)"
          % (report["prove"]["rendering"], report["prove"]["row_plus_col_is_conserved"]))
    for name, entry in sorted(report["levels"].items()):
        if entry["planner_consulted"]:
            print("  %-9s solved in %d actions -> box on target: %s"
                  % (name, entry["plan_length"], entry["won"]))
        else:
            print("  %-9s unsolvable: box parity %d, target parity %d -- the box "
                  "never leaves its own colour"
                  % (name, entry["theorem"]["inv_init"], entry["theorem"]["goal_parity"]))
    print("-" * 72)
    grading = report["grading"]
    ok = (all(x["agrees"] for x in grading.values())
          and report["certify"]["replay_exact"]
          and report["certify_generated"]["replay_exact"])
    for name, g in sorted(grading.items()):
        print("  grade %-9s solvable predicted=%s actual=%s  optimal_plan=%s"
              % (name, g["predicted_solvable"], g["actually_solvable"], g["plan_optimal"]))
    print("  report -> %s" % path)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
