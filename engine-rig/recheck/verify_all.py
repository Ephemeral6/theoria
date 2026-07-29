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
from recheck.verify import ACCEPT, REJECT, reachable_states, recheck, shortest_plan

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
    ("keyed-gate", "keyed-gate-pagoda", ACCEPT, None,
     "the pagoda obligation is quantified over moves *legal from the region*. "
     "This world's only potential-raising move needs both keys, and any state "
     "holding both is already over the bound, so the certificate is inductive "
     "and a checker reading deltas straight off the geometry false-rejects it"),
)

# The pagoda claims lp_potential exported, one row per document in
# `interop/certificates/`. The expected verdict is ACCEPT for all three: the
# engine's LP found these weights and `interop/README.md` states independently
# that the underlying claims are true, so a rejection here would be a finding
# about this checker before it was a finding about the certificate.
PAGODA_MATRIX: Tuple[Tuple[str, str, str, Optional[str], str], ...] = tuple(
    (ruleset, name, ACCEPT, None,
     "lp_potential's pagoda for %s, transcribed from %s; the weights and the "
     "bound are the certificate, everything else is re-derived here"
     % (ruleset, document))
    for name, ruleset, _weights, _bound, document in build_cases.PAGODA_CLAIMS
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

# interop/README.md, on the 5-cell board theory-compiler's fixture uses:
# "enumeration confirms `11011` reaches only `{00111, 11100, 01001, 10010}`,
# bottoming out at 2 pegs, never 1". Five states with the start itself, and the
# claim the two pagoda certificates make is about exactly this set.
PEG5_REACHABLE: Tuple[str, ...] = ("00111", "01001", "10010", "11011", "11100")
PEG5_RULESETS = ("peg5-11011-to-01000", "peg5-11011-to-00010")


def _load(name: str, suffix: str):
    return os.path.join(CASES_DIR, "%s.%s.json" % (name, suffix))


def run_matrix() -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    cache: Dict[str, object] = {}

    def ruleset(name: str):
        if name not in cache:
            cache[name] = load_ruleset(_load(name, "rules"))
        return cache[name]

    for rules_name, cert_name, expected, condition, why in MATRIX + PAGODA_MATRIX:
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


def run_pagoda() -> Dict[str, object]:
    """The pass rate over `lp_potential`'s exported certificates, one row each.

    Two independent things are reported per row and both have to hold:

    * the **verdict** -- the three conditions re-derived from the rule set, with
      the move set grounded from the declared rules rather than read out of the
      document's own obligation list;
    * the **differential** -- what the transcription and the producer's document
      say about each other (`anchors.pagoda_differential`).

    A row is a pass only if both agree.  The verdict alone would say nothing if
    the case were a transcription of a different world, and the differential
    alone would say nothing about whether the certificate is any good.
    """
    rows: List[Dict[str, object]] = []
    for name, ruleset_name, _weights, _bound, document in build_cases.PAGODA_CLAIMS:
        ruleset = load_ruleset(_load(ruleset_name, "rules"))
        certificate = load_certificate(_load(name, "cert"))
        verdict = recheck(ruleset, certificate)
        try:
            differential = anchors.pagoda_differential(ruleset, certificate, document)
        except anchors.AnchorUnavailable as exc:
            differential = {"unavailable": str(exc), "agrees": None}
        failed = sorted(key for key, ok in verdict.conditions.items() if not ok)
        rows.append({
            "certificate": name,
            "document": document,
            "ruleset": ruleset_name,
            "expected": ACCEPT,
            "verdict": verdict.verdict,
            "conditions": dict(sorted(verdict.conditions.items())),
            "failed_conditions": failed,
            "n_states": verdict.stats.get("n_states"),
            "n_satisfying": verdict.stats.get("n_satisfying"),
            "n_potential_checks": verdict.stats.get("n_potential_checks"),
            "n_raising_transitions": verdict.stats.get("n_raising_transitions"),
            "potential_bound": verdict.stats.get("potential_bound"),
            "potential_at_init": verdict.stats.get("potential_at_init"),
            "second_opinion": verdict.search.get("says"),
            "goal_reachable": verdict.search.get("goal_reachable"),
            "differential": differential,
            "passed": (verdict.verdict == ACCEPT
                       and differential.get("agrees") is True),
        })
    return {
        "rows": rows,
        "n_certificates": len(rows),
        "n_passed": sum(1 for row in rows if row["passed"]),
        "n_accepted": sum(1 for row in rows if row["verdict"] == ACCEPT),
        "n_differentials_agree": sum(1 for row in rows
                                     if row["differential"].get("agrees") is True),
        "all_passed": all(row["passed"] for row in rows) and bool(rows),
        "method": "the three conditions re-derived from the rule set, with the "
                  "move set grounded from the declared rules; the producer's "
                  "own obligation list is refused as input and compared once, "
                  "as a differential, in anchors.pagoda_differential",
    }


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

    # The 5-cell board, against the reachable set interop/README.md names.
    peg5 = []
    for name in PEG5_RULESETS:
        ruleset = load_ruleset(_load(name, "rules"))
        derived = tuple(sorted(
            "".join(str(value) for value in state)
            for state in reachable_states(ruleset)))
        peg5.append({
            "ruleset": name,
            "stated_reachable": list(PEG5_REACHABLE),
            "derived_reachable": list(derived),
            "why": "interop/README.md: 11011 reaches only {00111, 11100, "
                   "01001, 10010}, bottoming out at 2 pegs",
            "agrees": derived == PEG5_REACHABLE,
        })
    out["peg5_reachable_set"] = peg5

    out["agrees"] = (
        out["a2_episode_replay"].get("agrees") is not False
        and out["a2_lean_step_table"].get("agrees") is not False
        and all(row["agrees"] for row in plans)
        and all(row["agrees"] for row in peg)
        and all(row["agrees"] for row in peg5)
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
    pagoda = run_pagoda()
    attempts = forgeries.run_all()
    forged = forgeries.summary(attempts)

    off_script = [row for row in matrix if not row["as_declared"]]
    green = (
        not drift and not off_script
        and anchor_report["agrees"]
        and pagoda["all_passed"]
        and forged["n_off_script"] == 0
    )

    report = {
        "green": green,
        "drift": drift,
        "matrix": matrix,
        "anchors": anchor_report,
        "pagoda": pagoda,
        "forgeries": forged,
        "counts": {
            "cases": len(build_cases.all_cases()),
            "matrix_rows": len(matrix),
            "matrix_off_script": len(off_script),
            "pagoda_certificates": pagoda["n_certificates"],
            "pagoda_passed": pagoda["n_passed"],
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
    for row in anchor_report["peg5_reachable_set"]:
        print("  %-18s reachable %d states %s"
              % (row["ruleset"], len(row["derived_reachable"]),
                 "ok" if row["agrees"] else "MISMATCH"))
    print("pagoda     %d of %d certificates pass (%d accepted, %d differentials agree)"
          % (pagoda["n_passed"], pagoda["n_certificates"],
             pagoda["n_accepted"], pagoda["n_differentials_agree"]))
    for row in pagoda["rows"]:
        print("  %-8s %-28s %-30s %s"
              % (row["verdict"], row["certificate"], row["document"],
                 "as declared" if row["passed"] else "OFF SCRIPT"))
    print("forgeries  %d attempted, %d behaved as declared, %d accepted"
          % (forged["n_forgeries"], forged["n_as_declared"], forged["n_accepted"]))
    for attempt in attempts:
        if not attempt.as_declared:
            print("  OFF SCRIPT %s -> %s" % (attempt.forgery.name, attempt.verdict))
    print("VERDICT    %s" % ("GREEN" if green else "RED"))

    if args.out:
        os.makedirs(args.out, exist_ok=True)
        # Two files, because the pagoda table is what an importer of
        # `lp_potential`'s certificates wants and the rest of the report is not.
        # Neither carries a timestamp or an absolute path: a run of this script
        # on the same inputs is byte-identical to the last one.
        for filename, payload in (("recheck_report.json", report),
                                  ("pagoda_recheck.json", pagoda)):
            path = os.path.join(args.out, filename)
            with open(path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
            print("report     %s" % path)

    return 0 if green else 1


if __name__ == "__main__":
    raise SystemExit(main())
