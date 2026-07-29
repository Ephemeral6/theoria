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
from pipeline import cross_form, explore, gen_exec, lean_stage, pddl_gen, stages  # noqa: E402
from world import levels, sokoban2                              # noqa: E402

ARTIFACTS = os.path.join(HERE, "artifacts")


def _plan_actions_to_world(plan_actions: List[str]) -> List[str]:
    """PDDL step -> world action. `(walk c3_5 c3_4 left)` -> `LEFT`."""
    return [action.strip("()").split()[-1].upper() for action in plan_actions]


def run() -> Dict[str, Any]:
    report: Dict[str, Any] = {}
    level = levels.MATCH

    # 1. explore -- prefix replay to reach discriminating situations
    # Evidence is pooled across levels: the manual is a DOMAIN, and one level
    # cannot force every domain rule (THEORIZE_LOG T-9).
    transitions = []
    episodes = []
    by_level = {}
    actions_spent = 0
    for evidence_level in levels.EVIDENCE_LEVELS:
        evidence = explore.evidence_set(evidence_level, per_class=4)
        by_level[evidence_level.name] = (evidence_level, evidence["episodes"])
        episodes.extend(evidence["episodes"])
        actions_spent += evidence["action_budget_spent"]
        transitions.extend(stages.transitions_from_episodes(evidence["episodes"]))
    evidence = {"episodes": episodes}
    report["explore"] = {
        "levels": [lv.name for lv in levels.EVIDENCE_LEVELS],
        "episodes": len(episodes),
        "actions_spent": actions_spent,
        "transitions": len(transitions),
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
    # E14: the account travels with the rule set. `n_rules` and the guards below
    # cannot distinguish a world that is genuinely disjunctive from a miner that
    # fell over, so the thing that can is published beside them.
    rules, mine_account = stages.mine_with_account(transitions)
    report["mine"] = {
        "n_rules": len(rules),
        "rules": [r.as_json() for r in sorted(rules, key=lambda r: r.name)],
        "account": mine_account.as_json(),
        "synthesis_crashes": len(mine_account.crashes),
        "all_guards_searched": mine_account.all_guards_searched,
        "n_rules_unsound_after_crash": sum(1 for r in rules
                                           if r.unsound_after_crash),
    }

    # 4. certify -- full-history replay through the rules alone.
    # The account goes in because these claims are ABOUT the mined rules: a
    # crash artefact that replays exactly is still a crash artefact. The three
    # blocks that follow (4b, 4c, 4d) deliberately do NOT take the account --
    # `certify_generated`, `held_out` and the Lean stage all predict through
    # `theory_exec.py` compiled from `theory/theory.dsl`, never through `rules`,
    # so gating them on a mining crash would be a false attribution: it would
    # report a defect at a site that has none. Checked, not assumed --
    # `certify_generated(module, episodes)` and the held-out loop take a
    # compiled module, and `unsolvability_certificate(level)` takes only a
    # level. (Adversarial review, correction 6, partially declined with this
    # reason.)
    certificate = stages.certify(rules, transitions, mine_account)
    report["certify"] = certificate

    # 4b. certify through the EXECUTABLE FORM compiled from theory.dsl.
    # The mined rules are engine output; the manual is what we are accountable
    # for, and the only predictor allowed is the one compiled from it.
    # Walls are problem data, so the executable form is compiled per level and
    # each level's episodes are replayed through its own module.
    dsl_path = os.path.join(HERE, "theory", "theory.dsl")
    dsl_text = open(dsl_path, encoding="utf-8").read()
    module = gen_exec.compile_module(
        dsl_text, level.height, level.width, level.walls,
        out_path=os.path.join(ARTIFACTS, "theory_exec.py"),
    )
    generated = {"episodes": 0, "frames_checked": 0, "n_render_mismatches": 0,
                 "errors": [], "per_level": {}}
    for name, (lvl, level_episodes) in sorted(by_level.items()):
        level_module = gen_exec.compile_module(
            dsl_text, lvl.height, lvl.width, lvl.walls)
        outcome = stages.certify_generated(level_module, level_episodes)
        generated["per_level"][name] = {
            "frames_checked": outcome["frames_checked"],
            "replay_exact": outcome["replay_exact"],
        }
        generated["episodes"] += outcome["episodes"]
        generated["frames_checked"] += outcome["frames_checked"]
        generated["n_render_mismatches"] += outcome["n_render_mismatches"]
        generated["errors"].extend(outcome["errors"])
    generated["replay_exact"] = (
        generated["n_render_mismatches"] == 0 and not generated["errors"]
    )
    generated["source"] = "theory/theory.dsl -> artifacts/theory_exec.py (per level)"
    report["certify_generated"] = generated

    # 4c. held-out: does the theory match the world on states never observed?
    # Replay-exactness does not imply this, which is the entire point.
    held_out = {}
    for check_level in (level,) + levels.CROSSING_LEVELS:
        checked = gen_exec.compile_module(
            dsl_text, check_level.height, check_level.width, check_level.walls)
        wall_set = set(check_level.walls)
        cases = mismatches = 0
        for pr, pc, br, bc, direction in cross_form.enumerate_cases(
                check_level.height, check_level.width):
            if (pr, pc) in wall_set or (br, bc) in wall_set:
                continue                     # not a well-formed state
            cases += 1
            predicted = checked["step"](
                checked["State"](player=(pr, pc), box=(br, bc)), direction)
            actual, _ = sokoban2.step(
                check_level, sokoban2.State(player=(pr, pc), box=(br, bc)), direction)
            if (predicted.player, predicted.box) != (actual.player, actual.box):
                mismatches += 1
        held_out[check_level.name] = {"cases": cases, "mismatches": mismatches}
    report["held_out"] = {
        "per_level": held_out,
        "total_cases": sum(v["cases"] for v in held_out.values()),
        "total_mismatches": sum(v["mismatches"] for v in held_out.values()),
        "exact": all(v["mismatches"] == 0 for v in held_out.values()),
    }

    # 4d. the proof form
    report["lean"] = lean_stage.check()
    report["lean_cross_form"] = lean_stage.cross_check(module, level.height, level.width)

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
    m = report["mine"]
    print("  mine      %d rules; synthesis crashes=%d; all_guards_searched=%s"
          % (m["n_rules"], m["synthesis_crashes"], m["all_guards_searched"]))
    if not m["all_guards_searched"]:
        print("            !! %d rule(s) are disjunctive because synthesis "
              "CRASHED, not because the class needs a disjunction:"
              % m["n_rules_unsound_after_crash"])
        for crash in m["account"]["crashes"][:8]:
            print("               %s on action %s: %s"
                  % (crash.get("type"), crash.get("action"),
                     str(crash.get("message"))[:90]))
    for rule in m["rules"]:
        print("              %-16s %-8s %s%s"
              % (rule["name"], rule["coverage"], " and ".join(rule["guard"]),
                 "   <-- UNSOUND (synthesis crashed)"
                 if rule["unsound_after_crash"] else ""))
    c = report["certify"]
    print("  certify   %d transitions replayed; exactly-one-successor=%s, exact=%s"
          % (c["transitions"], c["exactly_one_successor"], c["replay_exact"]))
    g = report["certify_generated"]
    print("  certify*  %d frames replayed through theory.dsl -> theory_exec.py; exact=%s"
          % (g["frames_checked"], g["replay_exact"]))
    h = report["held_out"]
    print("  held-out  %d unobserved-inclusive states across %d levels; mismatches=%d"
          % (h["total_cases"], len(h["per_level"]), h["total_mismatches"]))
    lean = report["lean"]
    if lean.get("available"):
        print("  lean      %s; sorry=%s; axioms=%s"
              % ("compiles" if lean["compiles"] else "FAILED",
                 lean["uses_sorry"], lean["axioms"][0].split(": ")[-1] if lean["axioms"] else "?"))
        print("  lean=py   %d/%d cases agree" % (
            report["lean_cross_form"]["cases"] - report["lean_cross_form"]["n_mismatches"],
            report["lean_cross_form"]["cases"]))
    else:
        print("  lean      skipped (%s)" % lean.get("skipped"))
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
          # E14: a run whose miner crashed does not get to be green, however
          # well the rules it happened to emit replay. The crash count is a
          # conjunct of the verdict, not a footnote under it.
          and report["mine"]["all_guards_searched"]
          and report["certify"]["replay_exact"]
          and report["certify_generated"]["replay_exact"]
          and report["held_out"]["exact"]
          and (not report["lean"].get("available")
               or (report["lean"]["compiles"] and not report["lean"]["uses_sorry"]
                   and report["lean_cross_form"]["forms_agree"])))
    for name, g in sorted(grading.items()):
        print("  grade %-9s solvable predicted=%s actual=%s  optimal_plan=%s"
              % (name, g["predicted_solvable"], g["actually_solvable"], g["plan_optimal"]))
    print("  report -> %s" % path)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
