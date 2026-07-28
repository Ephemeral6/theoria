"""The whole recheck, in one command, with the expected verdict written down.

    python -m recheck.verify_all [--out <dir>]

Four sections, and the script is red if any of them deviates:

1. **drift** -- the committed cases are byte-identical to what
   `recheck.build_cases` generates.  Generated artefacts are never hand-edited,
   so a difference means someone did.
2. **anchors** -- the rule sets say what their sources say: A2's own 18-action
   refutation replays frame by frame through `a2-world`, Lean's 592-row `step`
   table agrees with `a2-holed`, and the sokoban optima the fixture states by
   hand (ring 1, open4 6) come back out of the derived relation.
3. **matrix** -- every certificate against every rule set it is meant to be
   checked against, with the verdict declared here in advance.  The two rows
   this item exists for are `a2-holed -> ACCEPT` and `a2-world -> REJECT`: the
   same certificate, one manual apart, and the second must fail because the
   theorem is false of the world.
4. **forgeries** -- the catalogue in `forgeries.py`, each one behaving as
   declared.

The expected verdicts live in this file rather than being read off a previous
run, so a regression cannot re-baseline itself.
"""

import argparse
import json
import os
import sys
from typing import Dict, List, Optional, Sequence, Tuple

from recheck import anchors, build_cases, forgeries
from recheck.certificate import load_certificate
from recheck.ruleset import load_ruleset
from recheck.verify import ACCEPT, REJECT, recheck, shortest_plan

CASES_DIR = build_cases.CASES_DIR

# (rule set, certificate, expected verdict, expected failing condition, why)
MATRIX: Tuple[Tuple[str, str, str, Optional[str], str], ...] = (
    ("peg4-0111", "peg4-0111-ic3", ACCEPT, None,
     "M9's acceptance line: 0111 is unsolvable and this is the invariant "
     "ic3_pdr returns for it"),
    ("peg4-1101", "peg4-0111-ic3", REJECT, "ruleset_binding",
     "the same certificate offered for the solvable configuration, which "
     "ic3_pdr correctly refuses to certify. It is rejected at the binding, "
     "before the invariant is evaluated at all; the forgery catalogue's "
     "`invariant-on-a-solvable-start` strips the binding and shows it fails "
     "`inv_init` on the merits too"),
    ("a2-holed", "a2-right-room-locked", ACCEPT, None,
     "agrees with Lean: generated_holed/theory.lean proves this closed, "
     "axiom-free, and so does this rechecker, over all 148 states"),
    ("a2-world", "a2-right-room-locked", REJECT, "inv_closed",
     "THE ACCEPTANCE LINE. The same certificate against the world's own rules. "
     "The theorem is false of the world, so a rechecker that passed it here "
     "would be wrong, not lenient"),
)

SOKOBAN_LEVELS = ("sokoban-ringstuck", "sokoban-open4far")

# What the fixture says, on grounds this encoding shares nothing with.
SOKOBAN_OPTIMA: Tuple[Tuple[str, Optional[int], str], ...] = (
    ("sokoban-ring", 1, "fixtures/sokoban.py: RING.optimum = 1"),
    ("sokoban-open4", 6, "fixtures/sokoban.py: OPEN4.optimum = 6, argued in "
                         "engines/deadlock_carver/README.md"),
    ("sokoban-ringstuck", None, "unsolvable; STATUS.md M9 and the FD ladder agree"),
    ("sokoban-open4far", 11, "STATUS.md M9: the plan is 11 steps either way"),
)

PEG_REACHABILITY: Tuple[Tuple[str, Optional[int]], ...] = (
    ("1110", None), ("0111", None), ("1011", None), ("1101", 2),
)


def _load(name: str, suffix: str):
    return os.path.join(CASES_DIR, "%s.%s.json" % (name, suffix))


def run_matrix() -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    cache: Dict[str, object] = {}

    def ruleset(name: str):
        if name not in cache:
            cache[name] = load_ruleset(_load(name, "rules"))
        return cache[name]

    for rules_name, cert_name, expected, condition, why in MATRIX:
        verdict = recheck(ruleset(rules_name), load_certificate(_load(cert_name, "cert")))
        failed = sorted(name for name, ok in verdict.conditions.items() if not ok)
        rows.append({
            "ruleset": rules_name,
            "certificate": cert_name,
            "expected": expected,
            "expected_failing_condition": condition,
            "verdict": verdict.verdict,
            "failed_conditions": failed,
            "why": why,
            "witnesses": {k: v[:2] for k, v in sorted(verdict.witnesses.items())},
            "second_opinion": verdict.search.get("says"),
            "witness_plan": verdict.search.get("witness_plan"),
            "n_states": verdict.stats.get("n_states"),
            "as_declared": (
                verdict.verdict == expected
                and (condition is None or condition in failed)
            ),
        })

    for level in SOKOBAN_LEVELS:
        for filename in sorted(os.listdir(CASES_DIR)):
            if not filename.startswith(level + "-dead-"):
                continue
            path = os.path.join(CASES_DIR, filename)
            verdict = recheck(ruleset(level), load_certificate(path))
            rows.append({
                "ruleset": level,
                "certificate": filename[:-len(".cert.json")],
                "expected": ACCEPT,
                "expected_failing_condition": None,
                "verdict": verdict.verdict,
                "failed_conditions": sorted(
                    name for name, ok in verdict.conditions.items() if not ok),
                "why": "a deadlock_carver theorem, rechecked against rules that "
                       "were never grounded for it",
                "witnesses": {},
                "second_opinion": verdict.search.get("says"),
                "n_states": verdict.stats.get("n_states"),
                "n_satisfying": verdict.stats.get("n_satisfying"),
                "as_declared": verdict.verdict == ACCEPT,
            })
    return rows


def run_anchors() -> Dict[str, object]:
    out: Dict[str, object] = {}

    world = load_ruleset(_load("a2-world", "rules"))
    holed = load_ruleset(_load("a2-holed", "rules"))
    try:
        out["a2_episode_replay"] = anchors.a2_replay_episode(world)
    except anchors.AnchorUnavailable as exc:
        out["a2_episode_replay"] = {"unavailable": str(exc), "agrees": None}
    try:
        out["a2_lean_step_table"] = anchors.a2_lean_step_table(holed)
    except anchors.AnchorUnavailable as exc:
        out["a2_lean_step_table"] = {"unavailable": str(exc), "agrees": None}

    plans = []
    for name, optimum, why in SOKOBAN_OPTIMA:
        plan = shortest_plan(load_ruleset(_load(name, "rules")))
        length = len(plan) if plan is not None else None
        plans.append({
            "ruleset": name, "stated_optimum": optimum, "derived": length,
            "why": why, "agrees": length == optimum,
        })
    out["sokoban_optima"] = plans

    peg = []
    for start, optimum in PEG_REACHABILITY:
        plan = shortest_plan(load_ruleset(_load("peg4-%s" % start, "rules"))) \
            if os.path.exists(_load("peg4-%s" % start, "rules")) else "absent"
        if plan == "absent":
            continue
        length = len(plan) if plan is not None else None
        peg.append({
            "start": start, "hand_verified": optimum, "derived": length,
            "why": "peg4.py's docstring, hand-verified by exhaustive expansion",
            "agrees": length == optimum,
        })
    out["peg_reachability"] = peg

    out["agrees"] = (
        out["a2_episode_replay"].get("agrees") is not False
        and out["a2_lean_step_table"].get("agrees") is not False
        and all(row["agrees"] for row in plans)
        and all(row["agrees"] for row in peg)
    )
    out["all_available"] = (
        out["a2_episode_replay"].get("agrees") is True
        and out["a2_lean_step_table"].get("agrees") is True
    )
    return out


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m recheck.verify_all")
    parser.add_argument("--out", default=None, help="write the report here")
    args = parser.parse_args(argv)

    drift = build_cases.check()
    matrix = run_matrix()
    anchor_report = run_anchors()
    attempts = forgeries.run_all()
    forged = forgeries.summary(attempts)

    off_script = [row for row in matrix if not row["as_declared"]]
    green = (
        not drift and not off_script
        and anchor_report["agrees"]
        and forged["n_off_script"] == 0
    )

    report = {
        "green": green,
        "drift": drift,
        "matrix": matrix,
        "anchors": anchor_report,
        "forgeries": forged,
        "counts": {
            "cases": len(build_cases.all_cases()),
            "matrix_rows": len(matrix),
            "matrix_off_script": len(off_script),
            "forgeries": forged["n_forgeries"],
            "forgeries_off_script": forged["n_off_script"],
        },
    }

    print("cases      %d generated, %d drifted" % (len(build_cases.all_cases()), len(drift)))
    for row in matrix:
        print("  %-8s %-22s %-34s %s"
              % (row["verdict"], row["ruleset"], row["certificate"],
                 "as declared" if row["as_declared"] else "OFF SCRIPT"))
    print("anchors    %s" % ("agree" if anchor_report["agrees"] else "DISAGREE"))
    for row in anchor_report["sokoban_optima"] + anchor_report["peg_reachability"]:
        key = row.get("ruleset") or ("peg4-%s" % row.get("start"))
        print("  %-18s stated=%-5s derived=%-5s %s"
              % (key, row.get("stated_optimum", row.get("hand_verified")),
                 row["derived"], "ok" if row["agrees"] else "MISMATCH"))
    replay = anchor_report["a2_episode_replay"]
    print("  a2 replay          %s" % (
        "%d/%d frames agree, world win=%s" % (replay.get("n_frames", 0),
                                              replay.get("n_frames", 0),
                                              replay.get("world_reports_win"))
        if replay.get("agrees") else json.dumps(replay)[:160]))
    lean = anchor_report["a2_lean_step_table"]
    print("  a2 vs lean step    %s" % (
        "%d/%d rows agree" % (lean.get("n_rows", 0), lean.get("n_expected_rows", 0))
        if lean.get("agrees") else json.dumps(lean)[:160]))
    print("forgeries  %d attempted, %d behaved as declared, %d accepted"
          % (forged["n_forgeries"], forged["n_as_declared"], forged["n_accepted"]))
    for attempt in attempts:
        if not attempt.as_declared:
            print("  OFF SCRIPT %s -> %s" % (attempt.forgery.name, attempt.verdict))
    print("VERDICT    %s" % ("GREEN" if green else "RED"))

    if args.out:
        os.makedirs(args.out, exist_ok=True)
        path = os.path.join(args.out, "recheck_report.json")
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print("report     %s" % path)

    return 0 if green else 1


if __name__ == "__main__":
    raise SystemExit(main())
