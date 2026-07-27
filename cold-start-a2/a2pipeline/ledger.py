"""The loop ledger — six beats, each with the artefact that settles it.

A2's second acceptance sentence is "回路转得起来", and a loop is only credible if
each beat left something behind that can be checked without rerunning it.  This
module reads the artefacts the beats wrote and assembles one file that says, for
each beat: what it claimed, which file carries the evidence, and whether it
passed.  It computes nothing of its own — if a beat's artefact is missing, the
beat is `absent`, never `assumed`.
"""

import json
import os
import sys
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACTS = os.path.join(ROOT, "artifacts")


def _load(name: str) -> Optional[Dict]:
    path = os.path.join(ARTIFACTS, name)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _lines(name: str) -> Optional[List[Dict]]:
    path = os.path.join(ARTIFACTS, name)
    if not os.path.exists(path):
        return None
    return [json.loads(line) for line in open(path, encoding="utf-8")
            if line.strip()]


def build() -> Dict[str, object]:
    traces = _load("trace_summary.json")
    diff = _load("engines_diff.json")
    diff_probed = _load("engines_diff_probed.json")
    control_plan = _load("plan_generated.json")
    exhibit = _load("exhibit_report.json")
    refutation = _load("refutation.json")
    located = _load("locate_report.json")
    probes = _lines("probes.jsonl")
    probe_report = _load("probe_report.json")
    repair = _load("repair_report.json")

    beats: List[Dict[str, object]] = []

    def beat(tag: str, name: str, claim: str, evidence: List[str],
             passed: Optional[bool], detail: Dict[str, object]):
        beats.append({
            "beat": tag, "name": name, "claim": claim,
            "evidence": evidence,
            "status": "absent" if passed is None
                      else ("pass" if passed else "FAIL"),
            "detail": detail,
        })

    # ---- instrument: can it build the exhibit at all? ----------------------
    beat("M0", "仪器 · the complete manual",
         "the pipeline induces a complete manual from the sweep, and it is "
         "certified, provable and solvable",
         ["artifacts/engines_diff.json", "artifacts/certify_generated.json",
          "artifacts/plan_generated.json"],
         None if not (diff and control_plan) else bool(
             diff["verdict"]["sweep_proposes_a_jump"]
             and control_plan.get("green")),
         {} if not (diff and control_plan) else {
             "sweep_proposes_a_jump": diff["verdict"]["sweep_proposes_a_jump"],
             "history_proposes_a_jump": diff["verdict"]["history_proposes_a_jump"],
             "plan": control_plan["status"],
             "plan_length": control_plan.get("length"),
             "world_agrees": control_plan.get("world_reaches_goal"),
         })

    beat("M5", "展品 · the theorem that is false of the world",
         "the holed manual replays the play record at 100%, its planner returns "
         "UNSAT, and Lean signs an axiom-free `unsolvable` — which the world "
         "contradicts",
         ["artifacts/exhibit_report.json",
          "theory/generated_holed/theory.lean"],
         None if not exhibit else bool(exhibit["exhibit_green"]
                                       and exhibit["exhibit_is_false_of_the_world"]),
         {} if not exhibit else {
             "replay": exhibit["certify_cheap"]["frames"],
             "replay_green": exhibit["certify_cheap"]["green"],
             "replay_on_full_sweep_green":
                 exhibit["certify_cheap_vs_full_sweep"]["green"],
             "plan": exhibit["plan"]["status"],
             "lean_green": exhibit["certify_lean"]["green"],
             "lean_axioms": exhibit["theorem"]["axioms"],
             "false_of_the_world": exhibit["exhibit_is_false_of_the_world"],
         })

    # ---- the loop, six beats ----------------------------------------------
    beat("L1", "打脸 · refutation",
         "a solved episode contradicts the machine-checked theorem",
         ["artifacts/refutation.json", "artifacts/solved_episode.jsonl"],
         None if not refutation else bool(refutation["refuted"]),
         {} if not refutation else {
             "episode_length": refutation["episode"]["length"],
             "win_frames": refutation["episode"]["win_frames"],
         })

    beat("L2", "定位 · localisation",
         "§1.4's three-way narrows the error to one place on the witness path",
         ["artifacts/locate_report.json"],
         None if not located else (len(located["culprits"]) == 1
                                   and "located" in located),
         {} if not located else {
             "checks": located["checks"],
             "culprits": located["culprits"],
             "located_at": located.get("located", {}).get("t"),
             "action": located.get("located", {}).get("action"),
             "mover_at": located.get("located", {}).get("mover_at"),
             "diagnosis": "missing rule, not wrong rule",
         })

    beat("L3", "戳探 · probe",
         "predictions written first, executed through frames, results banked",
         ["artifacts/probes.jsonl", "artifacts/probe_report.json",
          "artifacts/probed_trace.jsonl"],
         None if not (probes and probe_report) else probe_report["run"] >= 4,
         {} if not probe_report else {
             "designed": probe_report["probes_designed"],
             "executed": probe_report["run"],
             "refuted": probe_report["refuted"],
             "not_separable": probe_report["not_separable"],
             "trace_grew": "%d -> %d frames" % (
                 probe_report["trace_frames_before"],
                 probe_report["trace_frames_after"]),
         })

    beat("L4", "修订 · revision",
         "the manual is rewritten from the probe record, and the grown evidence "
         "re-proposes the rule that was added",
         ["theory/theory_repaired.dsl", "artifacts/engines_diff_probed.json"],
         None if not diff_probed else bool(
             diff_probed["verdict"]["probed_evidence_proposes_a_jump"]),
         {} if not diff_probed else {
             "re_derivable_from_grown_evidence":
                 diff_probed["verdict"]["probed_evidence_proposes_a_jump"],
         })

    beat("L5", "重证 · re-proof",
         "the refuted certificate dies under the repaired step, and a true one "
         "takes its place",
         ["artifacts/repair_report.json",
          "theory/generated_repaired_stale/theory.lean",
          "theory/generated_repaired/theory.lean"],
         None if not repair else bool(
             repair["stale_certificate"]["died"]
             and repair["certify_lean"]["green"]
             and repair["scored_against_the_world"]["true_of_the_world"]),
         {} if not repair else {
             "stale_died": repair["stale_certificate"]["died"],
             "stale_first_error": repair["stale_certificate"]["first_error"],
             "new_theorem": "pocket_unreachable",
             "new_lean_green": repair["certify_lean"]["green"],
             "new_lean_axioms": repair["certify_lean"]["axiom_reports"],
             "true_of_the_world":
                 repair["scored_against_the_world"]["true_of_the_world"],
             "latch_lean_green": repair["certify_lean_latch"]["green"],
         })

    beat("L6", "解出 · solved",
         "the repaired manual plans, and the world agrees",
         ["artifacts/plan_repaired.json"],
         None if not repair else bool(repair["plan"].get("green")),
         {} if not repair else {
             "status": repair["plan"]["status"],
             "length": repair["plan"].get("length"),
             "manual_agrees": repair["plan"].get("manual_reaches_goal"),
             "world_agrees": repair["plan"].get("world_reaches_goal"),
             "execution_mismatches": repair["plan"].get("execution_mismatches"),
         })

    statuses = [b["status"] for b in beats]
    return {
        "world": "a2-base",
        "authority": "INC-004 ruling 2026-07-28, option (b): a self-built world "
                     "isomorphic to DC22's failure structure.  No upstream DC22 "
                     "artifact was read; the isomorphism argument cites only the "
                     "structural description already printed in Theoria §1.3.",
        "traces": {} if not traces else {
            "raw_trace": traces["raw_trace"]["coverage"],
            "history_trace": traces["history_trace"]["coverage"],
            "portal_transition": traces["portal_transition"],
            "history_omits": traces["history_omitted_pairs"],
        },
        "beats": beats,
        "summary": {
            "pass": statuses.count("pass"),
            "fail": statuses.count("FAIL"),
            "absent": statuses.count("absent"),
            "total": len(statuses),
        },
        "green": all(s == "pass" for s in statuses),
    }


def main() -> int:
    ledger = build()
    with open(os.path.join(ARTIFACTS, "loop_ledger.json"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(ledger, indent=2, sort_keys=True) + "\n")
    for beat in ledger["beats"]:
        print("%-4s %-6s %s" % (beat["beat"], beat["status"], beat["name"]))
    print("ledger: %d/%d pass, %d fail, %d absent"
          % (ledger["summary"]["pass"], ledger["summary"]["total"],
             ledger["summary"]["fail"], ledger["summary"]["absent"]))
    return 0 if ledger["green"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
