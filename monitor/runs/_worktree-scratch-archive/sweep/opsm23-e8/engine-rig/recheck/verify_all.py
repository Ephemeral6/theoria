"""The whole recheck, in one command, with the expected verdict written down.

    python -m recheck.verify_all [--out <dir>]

Four sections, and the script is red if any of them deviates:

1. **drift** -- the committed cases are byte-identical to what
   `recheck.build_cases` generates.  Generated artefacts are never hand-edited,
   so a difference means someone did.
2. **anchors** -- the rule sets say what their sources say: A2's own 18-action
   refutation replays frame by frame through `a2-world`, Lean's 592-row `step`
   table agrees with `a2-holed`, the sokoban optima the fixture states by
   hand (ring 1, open4 6) come back out of the derived relation, and every peg
   board's derived relation is compared edge by edge against `interop.peg1d`.
3. **matrix** -- every certificate against every rule set it is meant to be
   checked against, with the verdict declared here in advance.  The two rows
   this item exists for are `a2-holed -> ACCEPT` and `a2-world -> REJECT`: the
   same certificate, one manual apart, and the second must fail because the
   theorem is false of the world.
4. **forgeries** -- the catalogue in `forgeries.py`, each one behaving as
   declared.

The expected verdicts live in this file rather than being read off a previous
run, so a regression cannot re-baseline itself.

**The count column.**  A verdict on its own does not establish that the
certificate under test denotes the set of states the engine converged on.  A
translation that drops one literal denotes a smaller set, and on peg-6 one such
drop is ACCEPTed -- a green column about the wrong object.  So every IC3 row
also carries the number of states the invariant holds on, counted here over the
product of the declared domains, and compares it with `IC3_N_SATISFYING` below,
which is what the engine counted over its own boolean space.  A row whose
verdict is right and whose count is wrong is `OFF SCRIPT`.
"""

import argparse
import json
import os
import sys
from typing import Dict, List, Optional, Sequence, Tuple

# `interop.peg1d` is the peg geometry as another part of the rig writes it --
# built for lp_potential, before this package existed, and sharing no code with
# either the rechecker or IC3. It is imported for the anchors only: the point of
# an anchor is that it comes from somewhere else. It is not part of `engines/`,
# and the independence rule this package lives under is unchanged.
from interop import peg1d
from recheck import anchors, build_cases, forgeries
from recheck.certificate import load_certificate
<<<<<<< HEAD
from recheck.ruleset import load_ruleset
from recheck.verify import ACCEPT, REJECT, reachable_states, recheck, shortest_plan
=======
from recheck.ruleset import RuleSet, load_ruleset
from recheck.verify import ACCEPT, REJECT, recheck, shortest_plan
>>>>>>> origin/agent/e8-ic3-scale

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
    ("peg5-01111", "peg5-01111-ic3", ACCEPT, None,
     "E8 axis A, step 2: the same configuration one position wider, 32 states"),
    ("peg6-011111", "peg6-011111-ic3", ACCEPT, None,
     "E8 axis A, step 3: 64 states, and the first step where the invariant "
     "stops being two clauses -- eight, over four of the six positions"),
    ("peg7-0111111", "peg7-0111111-ic3", ACCEPT, None,
     "E8 axis A, step 4: 128 states"),
    ("peg8-01111111", "peg8-01111111-ic3", ACCEPT, None,
     "E8 axis A, step 5: 256 states, eleven clauses"),
    ("peg10-0111111111", "peg10-0111111111-ic3", ACCEPT, None,
     "E8 axis A, ladder rung 4: 1024 states, twenty clauses. The first rung "
     "added for the ladder rather than for the one-position-at-a-time gradient"),
    ("peg12-011111111111", "peg12-011111111111-ic3", ACCEPT, None,
     "E8 axis A, ladder rung 5: 4096 states, twenty-nine clauses -- the widest "
     "invariant on the ladder, found in ~100s"),
    ("peg13-0111111111111", "peg13-0111111111111-ic3", ACCEPT, None,
     "E8 axis A, ladder rung 6: 8192 states, and the LAST rung IC3 answers "
     "inside the 300s budget. n=14 times out, so there is no invariant above "
     "this row for anyone to recheck"),
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

# certificate -> (states the invariant holds on, states in the space), as
# `engines.ic3_pdr.check.verify` counted them over 2^n boolean tuples.
#
# Declared here, in advance, exactly like the verdicts above: this package
# cannot compute these numbers -- it imports nothing from the engine that
# produced them -- so they are written down and the rechecker's own count, taken
# over the product of the declared domains, has to match.  Two enumerations, two
# encodings, one set of states.  `tests/test_ic3bounds_emit.py` is the other
# half of the loop: it re-runs the engine and fails if what it counts is no
# longer what is written here.
IC3_N_SATISFYING: Dict[str, Tuple[int, int]] = {
    "peg4-0111-ic3": (8, 16),
    "peg5-01111-ic3": (24, 32),
    "peg6-011111-ic3": (30, 64),
    "peg7-0111111-ic3": (98, 128),
    "peg8-01111111-ic3": (176, 256),
    "peg10-0111111111-ic3": (766, 1024),
    "peg12-011111111111-ic3": (3466, 4096),
    "peg13-0111111111111-ic3": (7780, 8192),
}

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


def peg_cases() -> List[Tuple[str, int, str, str, Optional[int]]]:
    """(case name, n, start, goal, the hand-verified distance, if there is one).

    The four four-position starts carry `peg4.py`'s docstring numbers; the wider
    boards of the E8 gradient have no hand-verified literal to carry, which is
    exactly why `interop.peg1d` is consulted for every row below rather than
    only for the ones without one.
    """
    hand = dict(PEG_REACHABILITY)
    rows = [
        (build_cases.peg_name(start, build_cases.PEG_N), build_cases.PEG_N,
         start, build_cases.PEG_GOAL, hand[start])
        for start, _ in PEG_REACHABILITY
    ]
    rows += [
        (build_cases.peg_name(start, n), n, start, goal, None)
        for n, start, goal in build_cases.PEG_GRADIENT
        if n != build_cases.PEG_N
    ]
    return rows


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
        row = {
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
            "n_satisfying": verdict.stats.get("n_satisfying"),
            "as_declared": (
                verdict.verdict == expected
                and (condition is None or condition in failed)
            ),
        }

        # The count column.  A row that is rejected at the binding never gets as
        # far as counting anything, so the comparison is made only where the
        # certificate was actually evaluated -- and a missing count where one was
        # expected is a failure, not a skip.
        declared = IC3_N_SATISFYING.get(cert_name)
        if declared is not None and expected == ACCEPT:
            engine_satisfying, engine_states = declared
            row["engine_n_satisfying"] = engine_satisfying
            row["engine_n_states"] = engine_states
            row["counts_agree"] = (
                verdict.stats.get("n_satisfying") == engine_satisfying
                and verdict.stats.get("n_states") == engine_states
            )
            row["as_declared"] = bool(row["as_declared"]) and row["counts_agree"]
        rows.append(row)

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


<<<<<<< HEAD
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
=======
def peg_relation_anchor(ruleset: RuleSet, n: int,
                        max_witnesses: int = 6) -> Dict[str, object]:
    """The derived relation of a peg rule set against `interop.peg1d`'s.

    The same shape of check as `anchors.a2_lean_step_table`, and there for the
    same reason: a rule set is a transcription, and a transcription is only worth
    what an outside artefact says about it.  Every `(state, jump)` pair is
    compared -- `2^n * 2(n-2)` of them -- and an illegal jump has to come back as
    the self-loop `frame persist` makes it, not as a missing edge.  A single
    reversed guard or misindexed effect shows up here and not in any verdict.
    """
    states = ruleset.states()
    rows = ruleset.transitions()
    index_of = {state: i for i, state in enumerate(states)}
    moves = peg1d.move_instances(n)
    labels = ["jump(%d,%d,%d)" % (m["src"], m["over"], m["dst"]) for m in moves]

    action_index = {action: i for i, action in enumerate(ruleset.actions)}
    missing = sorted(set(labels) - set(ruleset.actions))
    extra = sorted(set(ruleset.actions) - set(labels))
    mismatches: List[str] = []
    n_compared = 0

    if not missing and not extra:
        for state in states:
            text = "".join(str(int(value)) for value in state)
            source = index_of[state]
            for move, label in zip(moves, labels):
                n_compared += 1
                target = rows[source][action_index[label]]
                got = ("<off-domain>" if target < 0 else
                       "".join(str(int(value)) for value in states[target]))
                want = peg1d.apply(text, move) if peg1d.legal(text, move) else text
                if got != want and len(mismatches) < max_witnesses:
                    mismatches.append("%s -%s-> peg1d %s, rules %s"
                                      % (text, label, want, got))

    return {
        "ruleset": ruleset.name,
        "n_pos": n,
        "n_compared": n_compared,
        "n_expected": len(states) * len(moves),
        "missing_actions": missing,
        "undeclared_actions": extra,
        "mismatches": mismatches,
        "why": "interop/peg1d.py -- the same geometry transcribed for "
               "lp_potential, sharing no code with this package",
        "agrees": (not missing and not extra and not mismatches
                   and n_compared == len(states) * len(moves)),
>>>>>>> origin/agent/e8-ic3-scale
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
    relations = []
    for name, n, start, goal, hand in peg_cases():
        if not os.path.exists(_load(name, "rules")):
            continue
        rules = load_ruleset(_load(name, "rules"))
        plan = shortest_plan(rules)
        length = len(plan) if plan is not None else None
        # `peg1d.distance_to` is the independent number. The hand-verified
        # literals only exist for the four-position board, so they are checked
        # when present and never stood in for: a gradient step with no hand
        # number still has an outside opinion, which is the whole requirement.
        independent = peg1d.distance_to(start, [goal])
        peg.append({
            "ruleset": name, "start": start, "n_pos": n, "goal": goal,
            "hand_verified": hand, "peg1d": independent, "derived": length,
            "why": "interop.peg1d.distance_to, plus peg4.py's docstring where it "
                   "has one -- both hand-verified by exhaustive expansion",
            "agrees": length == independent and (hand is None or length == hand),
        })
        relations.append(peg_relation_anchor(rules, n))
    out["peg_reachability"] = peg
    out["peg_relation"] = relations

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
<<<<<<< HEAD
        and all(row["agrees"] for row in peg5)
=======
        and all(row["agrees"] for row in relations)
>>>>>>> origin/agent/e8-ic3-scale
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
<<<<<<< HEAD
            "pagoda_certificates": pagoda["n_certificates"],
            "pagoda_passed": pagoda["n_passed"],
=======
            "counts_compared": sum(1 for row in matrix if "counts_agree" in row),
            "counts_disagreeing": sum(1 for row in matrix
                                      if row.get("counts_agree") is False),
>>>>>>> origin/agent/e8-ic3-scale
            "forgeries": forged["n_forgeries"],
            "forgeries_off_script": forged["n_off_script"],
        },
    }

    print("cases      %d generated, %d drifted" % (len(build_cases.all_cases()), len(drift)))
    for row in matrix:
        # The count column: what the engine counted, what this package counted.
        # A blank means the certificate was refused before anything was counted,
        # which is a different statement from "the counts agree".
        if "counts_agree" in row:
            counts = "%s=%s %s" % (row["n_satisfying"], row["engine_n_satisfying"],
                                   "ok" if row["counts_agree"] else "MISMATCH")
        else:
            counts = "-"
        print("  %-8s %-22s %-34s %-14s %s"
              % (row["verdict"], row["ruleset"], row["certificate"], counts,
                 "as declared" if row["as_declared"] else "OFF SCRIPT"))
    print("anchors    %s" % ("agree" if anchor_report["agrees"] else "DISAGREE"))
    for row in anchor_report["sokoban_optima"]:
        print("  %-18s stated=%-5s derived=%-5s %s"
              % (row["ruleset"], row["stated_optimum"], row["derived"],
                 "ok" if row["agrees"] else "MISMATCH"))
    for row in anchor_report["peg_reachability"]:
        print("  %-18s peg1d=%-5s derived=%-5s hand=%-5s %s"
              % (row["ruleset"], row["peg1d"], row["derived"],
                 row["hand_verified"], "ok" if row["agrees"] else "MISMATCH"))
    for row in anchor_report["peg_relation"]:
        print("  %-18s %d/%d edges agree with peg1d %s"
              % (row["ruleset"], row["n_compared"] - len(row["mismatches"]),
                 row["n_expected"], "ok" if row["agrees"] else "MISMATCH"))
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
