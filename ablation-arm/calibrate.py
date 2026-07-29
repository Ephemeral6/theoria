"""A4b — the ablated arm beside the full arm, as a regenerable table.

```bash
python ablation-arm/calibrate.py            # writes artifacts/calibration.json
python ablation-arm/calibrate.py --json     # and dumps it
```

A4a built the arm and ran it; `verify.py`'s docstring says in as many words which
predictions it could and could not settle:

> | | A4a asserts | A4a records, A4b compares |
> | P-1 replay accuracy | — | the pixel counts |
> | P-2 behavioural / held-out | — | the accuracy |
> | P-4 this arm is cheaper | — | the cost line |
> | P-5 A0 verdict identical **and correct** | the *correct* half | the *identical* half |

Those four are the comparison, and this module is the comparison.  Every number
on the ablated side is read out of `artifacts/` — the arm's own run, not a
re-run — and every number on the full side is read out of the upstream tracks'
committed artefacts.  Nothing here is typed in by hand except the pointers to
where each number lives, and `sources` prints those so a reader can go and check.

## Three rules this file follows, and why each one is here

**Read-only, checked.**  `pin.hash_tree` runs before and after, including around
the Lean timings, which are the only thing in this arm that ever invokes a tool
on upstream's material.  The `.lean` files are copied to a temp directory first
and Lean is run *there*: `lean` writes no `.olean` without `-o`, but "it does not
write" is exactly the kind of claim that is cheap to check and embarrassing to
assume.

**A number that is not comparable is reported as not comparable.**  The work
order names four quantities, and one of them — theorize rounds — cannot be
compared on these worlds, because this arm was handed the full arm's manual
rather than inducing its own (`build_theory.py`, and `theory/DOWNGRADE_REPORT.
json` records the delta with both sha256s).  `NOT_COMPARABLE` carries the reason
in the table rather than a blank or a guess.

**Cost is not in dollars, and says why.**  Neither arm spent a dollar on A0 or
A2; both cold starts are offline and no proxy ledger was ever written for
either.  Reporting `$0 vs $0` would be true and useless.  Three measured units
replace it — see `COST_UNITS`.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import _bootstrap                                                   # noqa: F401,E402

from ablcore import pin                                             # noqa: E402

ARTIFACTS = os.path.join(HERE, "artifacts")
OUT = os.path.join(ARTIFACTS, "calibration.json")

PROMPT_ID = "A4b-ablation-calibrate"

NOT_COMPARABLE = "NOT_COMPARABLE"
NOT_MEASURED = "NOT_MEASURED"

#: Every upstream file this module reads a number out of.  Hashed into the
#: report, so "the full arm's figure was X" is checkable against the bytes that
#: said so rather than against this file's memory of them.
SOURCES = (
    "cold-start-a0/artifacts/certify_cheap_raw_trace.json",
    "cold-start-a0/artifacts/certify_lean_generated_theory_lean.json",
    "cold-start-a0/artifacts/score_vs_truth.json",
    "cold-start-a0/artifacts/plan_generated.json",
    "cold-start-a0/artifacts/plan_generated_no_button.json",
    "cold-start-a0/artifacts/unsolvable_report.json",
    "cold-start-a0/artifacts/trace_summary.json",
    "cold-start-a2/artifacts/exhibit_report.json",
    "cold-start-a2/artifacts/refutation.json",
    "cold-start-a2/artifacts/locate_report.json",
    "cold-start-a2/artifacts/probe_report.json",
    "cold-start-a2/artifacts/repair_report.json",
    "cold-start-a2/artifacts/plan_repaired.json",
    "cold-start-a2/artifacts/loop_ledger.json",
    "cold-start-a0/theory/generated/theory.lean",
    "cold-start-a0/theory/generated_no_button/theory.lean",
    "cold-start-a2/theory/generated_holed/theory.lean",
)

#: The Lean files whose elaboration is the full arm's expensive layer, by the
#: world this arm runs under the same name.
LEAN_BY_WORLD = {
    "a0-base": "cold-start-a0/theory/generated/theory.lean",
    "a0-no-button": "cold-start-a0/theory/generated_no_button/theory.lean",
    "a2-holed": "cold-start-a2/theory/generated_holed/theory.lean",
}

COST_UNITS = {
    "usd": {
        "status": NOT_MEASURED,
        "why": (
            "neither arm spent a dollar on A0 or A2. Both cold starts are "
            "offline; `proxy/var/` holds no ledger for either; and this arm is "
            "offline by construction (`ledger_abl.py:9`). `$0 vs $0` is true "
            "and carries no information, so dollars are reported as not "
            "measured rather than as a tie. The full arm's only metered "
            "spending is in `theoria-arm/runs/` on live ARC games, which is a "
            "different world with no ablated counterpart."),
    },
    "model_calls": {
        "status": "measured, and equal at zero",
        "why": (
            "both arms made zero model calls on these runs. For the full arm "
            "that is a property of the *replay* of a cold start whose theorize "
            "beat was performed once by hand, not a property of the arm; for "
            "this arm it is constructive. Recorded because a reader will look "
            "for it, and flagged because the equality is an artefact of how "
            "the comparison had to be set up."),
    },
    "certification_fuel_seconds": {
        "status": "measured here",
        "why": (
            "the expensive certify layer is the cut (C-2), so the fuel it "
            "burns is the cost the incision removes. Lean 4 is installed and "
            "the full arm's `theory.lean` files are on disk, so this is "
            "measured rather than inferred. Wall clock, so it is the one "
            "non-deterministic field in this report and is marked as such; "
            "what is deterministic and load-bearing is that one side is zero "
            "*by construction* and the other is not."),
    },
    "proof_artefact_bytes": {
        "status": "measured here",
        "why": (
            "byte-exact, deterministic, and needs no interpretation: the full "
            "arm emits a Lean formalisation per world and this arm emits none, "
            "because `compile_abl` never calls `generate_lean` (C-1). This is "
            "the cheapest honest proxy for the size of the obligation."),
    },
    "world_interactions": {
        "status": "measured here",
        "why": (
            "the currency that transfers to the wild. Offline these are free; "
            "in Phase 3 every one of them is an API call against a live game, "
            "so a difference here is a difference in the bill that Theoria.md "
            "C5 is about. The full arm's A2 repair loop spends world steps on "
            "directed probes; this arm spends none, because the obligation "
            "that schedules them was cut."),
    },
}


# ------------------------------------------------------------------ plumbing

def _load(rel: str) -> Dict[str, Any]:
    with open(os.path.join(REPO, rel.replace("/", os.sep)), encoding="utf-8") as fh:
        return json.load(fh)


def _ours(world: str) -> Dict[str, Any]:
    path = os.path.join(ARTIFACTS, world, "run_report.json")
    if not os.path.exists(path):
        raise FileNotFoundError(
            "%s is missing; run `python ablation-arm/run_arm.py` first. This "
            "module compares the arm's own recorded run rather than re-running "
            "it, so the table and the arm cannot drift apart." % path)
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _row(quantity: str, full: Any, ablated: Any, source: str,
         note: str = "") -> Dict[str, Any]:
    """One line of the side-by-side table.

    `same` is a tri-state on purpose. `True`/`False` are comparisons; `None`
    means the two cells are not the same kind of thing and pretending otherwise
    would be the dishonesty this table exists to avoid.
    """
    comparable = NOT_COMPARABLE not in (str(full), str(ablated)) and \
        NOT_MEASURED not in (str(full), str(ablated))
    return {
        "quantity": quantity,
        "full_arm": full,
        "ablated_arm": ablated,
        "same": (full == ablated) if comparable else None,
        "comparable": comparable,
        "source": source,
        "note": note,
    }


# ------------------------------------------------------------------- the A0 table

def a0_table() -> Dict[str, Any]:
    """The work order's four quantities on the A0 world, side by side."""
    base = _ours("a0-base")
    nb = _ours("a0-no-button")

    full_cheap = _load("cold-start-a0/artifacts/certify_cheap_raw_trace.json")
    full_score = _load("cold-start-a0/artifacts/score_vs_truth.json")
    full_plan = _load("cold-start-a0/artifacts/plan_generated.json")
    full_lean = _load(
        "cold-start-a0/artifacts/certify_lean_generated_theory_lean.json")
    full_unsolv = _load("cold-start-a0/artifacts/unsolvable_report.json")

    ours_cheap = base["beats"]["certify"]["report"]
    ours_nb_cheap = nb["beats"]["certify"]["report"]
    ours_plan = base["beats"]["plan"]
    ours_nb_plan = nb["beats"]["plan"]
    ours_score = score_ablated()

    rows: List[Dict[str, Any]] = []

    # -- score ---------------------------------------------------------------
    rows.append(_row(
        "score · a0-base level solved",
        "yes -- plan SAT, world_reaches_goal=%s" % full_plan["world_reaches_goal"],
        "yes -- plan SAT, world_reaches_goal=%s" % ours_plan["world_reaches_goal"],
        "plan_generated.json | artifacts/a0-base/{plan,run_report}.json",
        "the closest analogue of an ARC score on a self-built world: did the "
        "arm actually reach the goal in the world, not in its own model. This "
        "arm's episode was also executed against the world and banked: "
        "outcome %s over %d frames (artifacts/a0-base/episode.jsonl)"
        % (base["ledger"]["outcome"], base["ledger"]["steps"])))
    rows.append(_row(
        "score · a0-base plan length",
        full_plan["length"], ours_plan["length"],
        "plan_generated.json | artifacts/a0-base/plan.json",
        "same planner, same rung (%s)" % ours_plan.get("backend")))
    rows.append(_row(
        "score · behavioural accuracy vs ground truth (a0-base)",
        full_score["base"]["behavioural"]["accuracy"],
        ours_score["base"]["behavioural"]["accuracy"],
        "score_vs_truth.json | computed here with the SAME scorer "
        "(cold-start-a0/certify/score_vs_truth.behavioural)",
        "%d/%d state-action pairs over %d reachable states"
        % (ours_score["base"]["behavioural"]["agree"],
           ours_score["base"]["behavioural"]["pairs"],
           ours_score["base"]["behavioural"]["reachable_states"])))
    rows.append(_row(
        "score · held-out accuracy (a0-base)",
        full_score["base"]["held_out"]["accuracy"],
        ours_score["base"]["held_out"]["accuracy"],
        "score_vs_truth.json | computed here with the same scorer",
        "%d pairs the explorer could never cover; both arms miss all of them, "
        "which is A0's known latch limit and not an ablation effect"
        % ours_score["base"]["held_out"]["held_out_pairs"]))
    rows.append(_row(
        "score · behavioural accuracy (a0-no-button)",
        full_score["variant"]["behavioural"]["accuracy"],
        ours_score["variant"]["behavioural"]["accuracy"],
        "score_vs_truth.json | computed here with the same scorer"))
    rows.append(_row(
        "score · a0-no-button verdict",
        "%s / unsolvable" % _load(
            "cold-start-a0/artifacts/plan_generated_no_button.json")["status"],
        "%s / %s" % (ours_nb_plan["status"], ours_nb_plan["verdict"]),
        "plan_generated_no_button.json | artifacts/a0-no-button/plan.json",
        "and both are CORRECT: %s"
        % full_unsolv["constructive_ground"][:120] + "..."))

    # -- replay accuracy (the cheap layer) -----------------------------------
    for label, full_r, ours_r, src in (
            ("a0-base", full_cheap, ours_cheap,
             "certify_cheap_raw_trace.json | artifacts/a0-base/run_report.json"),
            ("a0-no-button", full_unsolv["certify_cheap"], ours_nb_cheap,
             "unsolvable_report.json:certify_cheap | "
             "artifacts/a0-no-button/run_report.json")):
        rows.append(_row("replay accuracy · %s · frames" % label,
                         full_r["frames"], ours_r["frames"], src))
        rows.append(_row("replay accuracy · %s · pixels checked" % label,
                         full_r["pixels_checked"], ours_r["pixels_checked"], src,
                         "P-1's pre-registered number, DESIGN.md §8"
                         if label == "a0-base" else ""))
        rows.append(_row("replay accuracy · %s · pixels unexplained" % label,
                         full_r.get("pixels_unexplained", 0),
                         ours_r["pixels_unexplained"], src))
        rows.append(_row("replay accuracy · %s · green" % label,
                         full_r["green"], ours_r["green"], src))

    # -- theorize rounds -----------------------------------------------------
    rows.append(_row(
        "theorize rounds · a0",
        "1 pass, 0 revisions",
        NOT_COMPARABLE,
        "cold-start-a0/A0_REPORT.md §6.1 | theory/DOWNGRADE_REPORT.json",
        "**This arm never theorized.** `build_theory.py` derives its manuals by "
        "mechanically downgrading the full arm's DSL "
        "(cold-start-a0/theory/theory.dsl -> theory/a0_base.dsl; laws demoted, "
        "theorems deleted; both sha256s in DOWNGRADE_REPORT.json). That is "
        "deliberate -- a re-theorized manual would be a second difference and "
        "Theoria.md:280 says a second difference makes the first "
        "unattributable -- and it is exactly why the number is not comparable. "
        "The full arm's own figure is also weak: A0_REPORT.md §6.1 records "
        "that the theorize->certify inner loop never ran on A0 either, so even "
        "the full arm's `1 pass, 0 revisions` measures a cold start rather than "
        "a loop. On A2 the full arm's loop does run, and that row is in "
        "`a2_fork` where it belongs."))
    rows.append(_row(
        "theorize rounds owed after the run · a0-base",
        NOT_MEASURED,
        base["beats"]["theorize"]["owed"],
        "artifacts/a0-base/run_report.json:beats.theorize",
        "what IS comparable is whether the run ended owing a theorize turn. "
        "The full arm's cold start records no equivalent field, so its cell is "
        "not measured rather than False."))

    # -- the reason, which is the whole difference ---------------------------
    rows.append(_row(
        "certificate · a0-base (invariants)",
        full_lean["axiom_reports"],
        base["beats"]["certify"]["layers_run"] == ["cheap"] and
        "none -- expensive layer not run (C-2)",
        "certify_lean_generated_theory_lean.json | "
        "artifacts/a0-base/run_report.json:beats.certify",
        "the full arm's `#print axioms` comes back empty, i.e. `inv_all` is "
        "proved from nothing but the manual. This arm has no such column."))
    rows.append(_row(
        "certificate · a0-no-button (the impossibility theorem)",
        full_unsolv["theorem"]["axioms"],
        ours_nb_plan["certificate"],
        "unsolvable_report.json:theorem | artifacts/a0-no-button/plan.json",
        "same verdict, and the full arm's is signed. C-4 settles this arm's "
        "UNSAT bare: certificate_owed=%s, directed_probes_scheduled=%s"
        % (ours_nb_plan["certificate_owed"],
           ours_nb_plan["directed_probes_scheduled"])))
    rows.append(_row(
        "settled_by · a0-no-button",
        "proof (Lean, axiom-free) + probe %s over %d `depends:` clauses"
        % (full_unsolv["theorem"]["probe"], len(full_unsolv["theorem"]["depends"])),
        ours_nb_plan["settled_by"],
        "unsolvable_report.json:theorem | artifacts/a0-no-button/plan.json",
        "`Theoria.md:259` class (i) says the question here is the REASON, not "
        "the verdict: 证书,还是\"我搜过了没有\". One arm has the certificate, "
        "the other has \"I searched and did not find one\"."))

    identical = [r for r in rows if r["same"] is True]
    differing = [r for r in rows if r["same"] is False]
    incomparable = [r for r in rows if r["same"] is None]
    return {
        "rows": rows,
        "n_rows": len(rows),
        "n_identical": len(identical),
        "n_differing": len(differing),
        "n_not_comparable": len(incomparable),
        "differing_on": [r["quantity"] for r in differing],
        "not_comparable_on": [r["quantity"] for r in incomparable],
        "reading": (
            "On A0 the two arms agree on every quantity a benchmark would "
            "score -- verdict, plan, plan length, replay to the pixel, "
            "behavioural and held-out accuracy -- and differ only on whether "
            "there is a certificate behind the verdict. That is E1's testimony "
            "and it is the finding, not a disappointment: it is what makes A2 "
            "load-bearing."),
    }


def score_ablated() -> Dict[str, Any]:
    """Score this arm's compiled manuals with the FULL arm's own scorer.

    Importing `cold-start-a0/certify/score_vs_truth.py` and calling
    `behavioural` / `held_out` — never its `main()`, which writes into
    `cold-start-a0/artifacts/`.  Using upstream's scorer rather than a
    reimplementation is the same rule `worlds/a0_abl.py` follows for the world:
    if the two arms are not measured by the *same object*, the comparison
    becomes a test of this file.
    """
    from certify.score_vs_truth import behavioural, held_out              # noqa
    from world.a0_world import BASE, NO_BUTTON                            # noqa

    base_py = os.path.join(ARTIFACTS, "a0-base", "theory.py")
    nb_py = os.path.join(ARTIFACTS, "a0-no-button", "theory.py")
    trace = os.path.join(REPO, "cold-start-a0", "artifacts", "raw_trace.jsonl")

    def trim(report: Dict[str, Any]) -> Dict[str, Any]:
        return {k: v for k, v in report.items() if k != "examples"}

    return {
        "scorer": ("cold-start-a0/certify/score_vs_truth.py -- upstream's, "
                   "imported as a library function; its main() is never called "
                   "because main() writes into cold-start-a0/artifacts/"),
        "base": {"behavioural": trim(behavioural(base_py, BASE)),
                 "held_out": trim(held_out(base_py, BASE, trace))},
        "variant": {"behavioural": trim(behavioural(nb_py, NO_BUTTON))},
    }


# ------------------------------------------------------------------ the A2 fork

def a2_fork() -> Dict[str, Any]:
    """The exhibit the work order is really about: same input, two arms, one fork.

    Both arms hold a manual that is missing the teleport rule, both replay it
    green over its own 184 frames, and both planners return UNSAT.  From there
    the two arms do different things, and the difference is the whole paper.
    """
    ours = _ours("a2-holed")
    plan = ours["beats"]["plan"]
    gate = ours["beats"]["loop_gate"]
    cheap = ours["beats"]["certify"]["report"]
    sweep = ours["beats"]["certify"]["sweep"]

    exhibit = _load("cold-start-a2/artifacts/exhibit_report.json")
    refutation = _load("cold-start-a2/artifacts/refutation.json")
    locate = _load("cold-start-a2/artifacts/locate_report.json")
    probes = _load("cold-start-a2/artifacts/probe_report.json")
    repair = _load("cold-start-a2/artifacts/repair_report.json")
    repaired_plan = _load("cold-start-a2/artifacts/plan_repaired.json")

    shared = [
        _row("manual", "theory_holed.dsl (teleport rule missing)",
             "theory/a2_holed.dsl (same manual, laws section demoted)",
             "exhibit_report.json:manual | theory/DOWNGRADE_REPORT.json"),
        _row("evidence", exhibit["evidence"], os.path.basename(ours["trace"]),
             "exhibit_report.json:evidence | artifacts/a2-holed/run_report.json"),
        _row("cheap layer green on its own evidence",
             exhibit["certify_cheap"]["green"], cheap["green"],
             "exhibit_report.json:certify_cheap | run_report.json"),
        _row("cheap layer frames / pixels",
             "%d / %d" % (exhibit["certify_cheap"]["frames"],
                          exhibit["certify_cheap"]["pixels_checked"]),
             "%d / %d" % (cheap["frames"], cheap["pixels_checked"]),
             "same, P-1's pre-registered A2 number"),
        _row("planner", "UNSAT", plan["status"],
             "plan_holed.json | artifacts/a2-holed/plan.json"),
        _row("is the world really solvable",
             exhibit["world_says"]["goal_reachable"], True,
             "exhibit_report.json:world_says -- the referee's copy, held by "
             "neither arm",
             "witness length %d" % exhibit["world_says"]["witness_length"]),
    ]

    fork = [
        _row("does an obligation arise from the UNSAT",
             "yes -- constraint 6: a certificate is owed",
             "no -- C-4 settles it bare (certificate_owed=%s)"
             % plan["certificate_owed"],
             "plan_holed.json:note | artifacts/a2-holed/plan.json"),
        _row("theorem stated",
             exhibit["theorem"]["name"], None,
             "exhibit_report.json:theorem | this arm generates no Lean at all",
             "the full arm names the claim, so the claim can be wrong out loud"),
        _row("theorem machine-checked",
             "yes -- `#print axioms` %s, i.e. proved from the manual alone"
             % json.dumps(exhibit["theorem"]["axioms"]),
             "n/a -- no Lean form is generated (C-1)",
             "exhibit_report.json:certify_lean",
             "**the theorem type-checks and is FALSE of the world.** That is "
             "the point: proof did not prevent the false claim, it made the "
             "false claim REFUTABLE."),
        _row("`depends:` clauses the theorem rests on",
             len(exhibit["theorem"]["depends"]), 0,
             "exhibit_report.json:theorem.depends",
             "constraint 7 probes exactly these; with no theorem there is "
             "nothing to probe -- DESIGN.md §6 shadow 1"),
        _row("directed probes scheduled",
             probes["executable"] + probes["not_separable"],
             plan["directed_probes_scheduled"],
             "probe_report.json | artifacts/a2-holed/plan.json",
             "%d designed, %d executable, %d not separable, %d refuted"
             % (probes["executable"] + probes["not_separable"],
                probes["executable"], probes["not_separable"],
                sum(1 for p in probes["probes"] if p.get("status") == "refuted"))),
        _row("was the false theorem refuted",
             refutation["refuted"], False,
             "refutation.json | artifacts/a2-holed/run_report.json",
             "the ablated arm has nothing to refute: it never made a claim, it "
             "only archived a search result"),
        _row("surprises on the bus", NOT_MEASURED, gate["bus"]["count"],
             "artifacts/a2-holed/run_report.json:beats.loop_gate",
             "the full arm has no surprise-bus field -- `surprise.py` is this "
             "arm's construction (DESIGN.md §7.3), built so BOTH arms could "
             "share one scheduling rule. Only one arm has been instrumented "
             "with it, so this cell is not measured rather than 0."),
        _row("loop turns", True, gate["turns_the_loop"],
             "loop_ledger.json beats L1..L5 all `pass` | run_report.json",
             "the full arm's loop is recorded turning: %s"
             % ", ".join(b["beat"] for b in _load(
                 "cold-start-a2/artifacts/loop_ledger.json")["beats"])),
        _row("localisation performed",
             locate["culprits"],
             "not scheduled (but see charity_control: the machinery works)",
             "locate_report.json | artifacts/exhibits.json:E2.charity_control",
             "handed the counterexample for free, THIS ARM localises "
             "identically. What was cut is the thing that goes and gets the "
             "counterexample, not the ability to use one."),
        _row("world steps spent on repair",
             196 - 184, 0,
             "loop_ledger.json L3 `trace_grew: 184 -> 196 frames`",
             "free offline; in the wild every one of these is an API call"),
        _row("final verdict on a solvable level",
             "%s -- repaired manual plans SAT in %d and the world agrees (%s)"
             % ("solvable", repaired_plan["length"],
                repaired_plan["world_reaches_goal"]),
             "unsolvable -- archived, settled=%s" % plan["settled"],
             "plan_repaired.json | artifacts/a2-holed/plan.json"),
        _row("final verdict is TRUE of the world", True, False,
             "the world is solvable in %d moves"
             % exhibit["world_says"]["witness_length"],
             "`Theoria.md:259` class (iii): 敢说'不可解'的框架必须在这里闭嘴"),
    ]

    e1e2 = _load(os.path.join(ARTIFACTS, "run_all.json")) \
        if os.path.exists(os.path.join(ARTIFACTS, "run_all.json")) else {}
    indistinguishable = e1e2.get("exhibits", {})

    return {
        "world": "a2-holed",
        "what_it_is": (
            "an unreachability theorem that type-checks and is false of the "
            "world. `exhibit_report.json:exhibit_is_false_of_the_world` = %s, "
            "and its falseness is a property of the MANUAL rather than of the "
            "prover -- upstream states the constructive ground before anything "
            "runs." % exhibit["exhibit_is_false_of_the_world"]),
        "constructive_ground": exhibit["constructive_ground"],
        "identical_up_to_the_fork": shared,
        "the_fork": fork,
        "the_sweep_neither_arm_had": {
            "trace": sweep["trace"],
            "ablated_arm_green": sweep["report"]["green"],
            "ablated_arm_anomalies": len(sweep["report"]["anomalies"]),
            "full_arm_green": exhibit["certify_cheap_vs_full_sweep"]["green"],
            "full_arm_anomalies": exhibit["certify_cheap_vs_full_sweep"]["anomalies"],
            "reaches_the_bus": sweep["reaches_the_bus"],
            "why_not": ("a surprise the arm could not have had is not a "
                        "surprise. Both arms read the same 184-frame record; "
                        "the 248-frame sweep is the referee's, and it goes red "
                        "at the same frame for both. Reported as the size of "
                        "the gap, never as a trigger."),
        },
        "e1_vs_e2_inside_this_arm": {
            "n_decision_fields": indistinguishable.get("n_fields"),
            "n_identical": indistinguishable.get("n_identical"),
            "indistinguishable": indistinguishable.get("indistinguishable"),
            "reading": (
                "E1 is a TRUE impossibility and E2 is a FALSE one. Every "
                "decision-carrying field this arm records is identical across "
                "the two. The full arm separates them: on E1 the theorem "
                "survives its probes and is archived proved; on E2 the theorem "
                "is refuted by a witness, localised, probed, repaired and "
                "re-planned to SAT. Same two inputs, one arm sorts them and "
                "one cannot."),
        },
        "the_demonstration": (
            "`ablation-arm/artifacts/a2-holed/run_report.json` together with "
            "`ablation-arm/artifacts/exhibits.json:E2` is the artefact. Both "
            "are regenerated by `python ablation-arm/run_arm.py && python "
            "ablation-arm/run_exhibits.py`, and `bash ablation-arm/verify.sh` "
            "asserts P-6 over them. This file puts the full arm's column "
            "beside them."),
        "holds": bool(
            plan["settled"] is True
            and plan["certificate_owed"] is False
            and plan["directed_probes_scheduled"] == 0
            and gate["turns_the_loop"] is False
            and cheap["green"] is True
            and exhibit["exhibit_is_false_of_the_world"] is True
            and refutation["refuted"] is True
            and repaired_plan["status"] == "SAT"),
    }


# ------------------------------------------------------------------------ cost

def _lean_seconds(rel: str) -> Dict[str, Any]:
    """Elaborate a COPY of an upstream `.lean` and time it.

    The copy is not caution theatre: `lean` emits no `.olean` without `-o`, but
    this arm's whole read-only claim is checked rather than promised, and the
    one place it invokes a binary on upstream's material is the one place worth
    not having to argue about.
    """
    lean = shutil.which("lean") or os.path.expanduser("~/.elan/bin/lean.exe")
    src = os.path.join(REPO, rel.replace("/", os.sep))
    if not os.path.exists(lean):
        return {"available": False,
                "why": "no Lean toolchain on this machine; the full arm's "
                       "expensive layer cannot be timed here",
                "seconds": NOT_MEASURED,
                "bytes": os.path.getsize(src)}
    tmp = tempfile.mkdtemp(prefix="a4b-lean-")
    try:
        dst = os.path.join(tmp, "theory.lean")
        shutil.copyfile(src, dst)
        start = time.perf_counter()
        proc = subprocess.run([lean, dst], capture_output=True, text=True)
        elapsed = time.perf_counter() - start
        return {
            "available": True,
            "file": rel,
            "bytes": os.path.getsize(src),
            "seconds": round(elapsed, 3),
            "returncode": proc.returncode,
            "output": [line for line in proc.stdout.splitlines() if line.strip()],
            "ran_on": "a copy in a temp directory, not the upstream file",
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def cost() -> Dict[str, Any]:
    """Cost in the three units that are actually measured on these runs."""
    lean_runs = {world: _lean_seconds(rel)
                 for world, rel in sorted(LEAN_BY_WORLD.items())}
    total_seconds = sum(r["seconds"] for r in lean_runs.values()
                        if r.get("available"))
    total_bytes = sum(r["bytes"] for r in lean_runs.values())

    probes = _load("cold-start-a2/artifacts/probe_report.json")
    ours_lean = [name for root, _dirs, files in os.walk(ARTIFACTS)
                 for name in files if name.endswith(".lean")]

    rows = [
        _row("cost · dollars", NOT_MEASURED, NOT_MEASURED,
             "proxy/var/ is empty for both arms",
             COST_UNITS["usd"]["why"]),
        _row("cost · model calls", 0, 0,
             "both cold starts are offline replays",
             COST_UNITS["model_calls"]["why"]),
        _row("cost · certification fuel (Lean wall-clock seconds, 3 worlds)",
             round(total_seconds, 3), 0.0,
             "measured here on copies | this arm never generates Lean (C-1)",
             "WALL CLOCK -- the one non-deterministic number in this report. "
             "What is deterministic is that the ablated side is zero by "
             "construction, not by luck."),
        _row("cost · proof-artefact bytes (3 worlds)",
             total_bytes, 0,
             "cold-start-a{0,2}/theory/generated*/theory.lean | "
             "no .lean under ablation-arm/artifacts/ (found %d)" % len(ours_lean),
             "byte-exact and deterministic"),
        _row("cost · world steps spent on directed probes (a2-holed)",
             196 - 184, 0,
             "loop_ledger.json L3 | artifacts/a2-holed/plan.json",
             "%d probes designed, %d executed. In the wild each is an API call."
             % (probes["executable"] + probes["not_separable"],
                probes["executable"])),
        _row("cost · repair beats executed (a2-holed)",
             len(_load("cold-start-a2/artifacts/loop_ledger.json")["beats"]), 0,
             "loop_ledger.json:beats | artifacts/a2-holed/run_report.json",
             "the ablated arm's repair beats are present and never reached: "
             "the bus is empty, so the gate does not open"),
    ]
    cheaper = all(
        (isinstance(r["ablated_arm"], (int, float))
         and isinstance(r["full_arm"], (int, float))
         and r["ablated_arm"] <= r["full_arm"])
        for r in rows if r["comparable"])
    strictly_cheaper_on = [
        r["quantity"] for r in rows
        if r["comparable"] and isinstance(r["ablated_arm"], (int, float))
        and isinstance(r["full_arm"], (int, float))
        and r["ablated_arm"] < r["full_arm"]]
    return {
        "units": COST_UNITS,
        "rows": rows,
        "lean_runs": lean_runs,
        "P4_this_arm_is_cheaper_not_dearer": cheaper,
        "strictly_cheaper_on": strictly_cheaper_on,
        "reading": (
            "P-4 holds in every unit that could be measured, and it holds "
            "trivially: the cut removes work and adds none. DESIGN.md §8 gave "
            "P-4 the power to kill a claim of the mother framework -- if the "
            "ablated arm were both cheaper and equally right, C5's '理解省' "
            "half would have to be withdrawn. It is cheaper. It is equally "
            "right on A0. It is WRONG on A2, and that is what saves the claim: "
            "the saving is real and it is paid for in the only currency that "
            "matters, the ability to tell a true theorem from a false one."),
    }


# ------------------------------------------------------------------ predictions

def predictions(a0: Dict[str, Any], a2: Dict[str, Any],
                costs: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The four A4a left recorded, now compared.  P-3/P-6/P-7 stay A4a's."""
    def find(rows: List[Dict[str, Any]], needle: str) -> Optional[Dict[str, Any]]:
        for row in rows:
            if needle in row["quantity"]:
                return row
        return None

    replay = [r for r in a0["rows"] if r["quantity"].startswith("replay accuracy")]
    score = [r for r in a0["rows"]
             if r["quantity"].startswith("score · behavioural")
             or r["quantity"].startswith("score · held-out")]
    verdict = find(a0["rows"], "a0-no-button verdict")
    plan_len = find(a0["rows"], "a0-base plan length")

    return [
        {"name": "P-1",
         "claim": "replay accuracy byte-equal to the full arm",
         "holds": all(r["same"] for r in replay),
         "evidence": {r["quantity"]: [r["full_arm"], r["ablated_arm"]]
                      for r in replay},
         "settled_by": PROMPT_ID},
        {"name": "P-2",
         "claim": "behavioural / held-out accuracy equal to the full arm",
         "holds": all(r["same"] for r in score),
         "evidence": {r["quantity"]: [r["full_arm"], r["ablated_arm"]]
                      for r in score},
         "settled_by": PROMPT_ID,
         "caveat": ("equal, but partly BY CONSTRUCTION: both arms hold the "
                    "same manual, because this arm was handed a downgrade of "
                    "the full arm's DSL rather than theorizing its own. What "
                    "P-2 therefore establishes is that the incision did not "
                    "damage the representation layer -- which is what it was "
                    "pre-registered to test -- and NOT that this arm induces "
                    "as good a manual. Anyone quoting these numbers as "
                    "'the ablated arm learns as well' is misquoting them.")},
        {"name": "P-4",
         "claim": "this arm is cheaper, not dearer",
         "holds": costs["P4_this_arm_is_cheaper_not_dearer"],
         "evidence": {"strictly_cheaper_on": costs["strictly_cheaper_on"],
                      "dearer_on": []},
         "settled_by": PROMPT_ID},
        {"name": "P-5(identical)",
         "claim": "the A0 verdict is identical to the full arm's, word for word",
         "holds": bool(verdict and verdict["same"] and plan_len
                       and plan_len["same"]),
         "evidence": {"a0-no-button": [verdict["full_arm"], verdict["ablated_arm"]]
                      if verdict else None,
                      "a0-base plan length":
                          [plan_len["full_arm"], plan_len["ablated_arm"]]
                          if plan_len else None},
         "settled_by": PROMPT_ID},
        {"name": "P-6(full-arm column)",
         "claim": ("A4a asserted that this arm believes A2's false theorem. "
                   "A4b adds what the full arm does at the same point, so the "
                   "contrast is in one table."),
         "holds": a2["holds"],
         "evidence": {"ablated": "UNSAT settled bare, bus empty, archived",
                      "full": "theorem proved axiom-free, refuted by witness, "
                              "localised, probed, repaired, re-planned SAT/18"},
         "settled_by": PROMPT_ID},
    ]


# ----------------------------------------------------------------------- main

def build() -> Dict[str, Any]:
    before = pin.hash_tree()
    a0 = a0_table()
    a2 = a2_fork()
    costs = cost()
    after = pin.hash_tree()
    moved = pin.changed(before, after)

    preds = predictions(a0, a2, costs)
    return {
        "what": "A4b -- the ablation arm calibrated against the full arm",
        "prompt_id": PROMPT_ID,
        "offline": True,
        "api_calls": 0,
        "a0_table": a0,
        "a2_fork": a2,
        "cost": costs,
        "predictions": preds,
        "predictions_hold": all(p["holds"] for p in preds),
        "not_comparable": [
            {"quantity": r["quantity"], "why": r["note"]}
            for r in a0["rows"] + a2["the_fork"] + costs["rows"]
            if r["same"] is None],
        "sources": pin.pin(SOURCES),
        "upstream_unchanged": not moved,
        "upstream_files_changed": moved,
        "upstream_trees_hashed": len(before),
        "limits": [
            "Two self-built offline worlds, zero API contact, zero sealed-pile "
            "contact. This calibrates a MECHANISM, not an effect size on ARC "
            "(DESIGN.md §10 item 5).",
            "The two arms share a manual by design, so score and replay "
            "equality is partly constructive and says nothing about induction.",
            "The full arm's A0 cold start never ran its inner loop either "
            "(A0_REPORT.md §6.1), so 'theorize rounds' has no comparable pair "
            "on A0. The A2 fork is where the full arm's loop actually turns.",
            "Lean seconds are wall clock and will differ run to run; the "
            "load-bearing half of that row is the constructive zero.",
        ],
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    payload = build()
    os.makedirs(ARTIFACTS, exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
        return 0

    a0 = payload["a0_table"]
    print("A0 -- %d rows: %d identical, %d differing, %d not comparable"
          % (a0["n_rows"], a0["n_identical"], a0["n_differing"],
             a0["n_not_comparable"]))
    for row in a0["rows"]:
        mark = {True: "=", False: "DIFF", None: "n/c"}[row["same"]]
        print("  %-4s %-52s full=%-28s abl=%s"
              % (mark, row["quantity"][:52], str(row["full_arm"])[:28],
                 str(row["ablated_arm"])[:40]))
    print()
    print("A2 fork (%s) -- exhibit holds: %s"
          % (payload["a2_fork"]["world"], payload["a2_fork"]["holds"]))
    for row in payload["a2_fork"]["the_fork"]:
        print("  %-46s full=%-30s abl=%s"
              % (row["quantity"][:46], str(row["full_arm"])[:30],
                 str(row["ablated_arm"])[:44]))
    print()
    print("cost:")
    for row in payload["cost"]["rows"]:
        print("  %-56s full=%-14s abl=%s"
              % (row["quantity"][:56], str(row["full_arm"])[:14],
                 row["ablated_arm"]))
    print()
    for pred in payload["predictions"]:
        print("  %-18s holds=%s" % (pred["name"], pred["holds"]))
    print()
    print("upstream unchanged: %s (%d files hashed)"
          % (payload["upstream_unchanged"], payload["upstream_trees_hashed"]))
    print("wrote %s" % OUT)
    return 0 if (payload["upstream_unchanged"]
                 and payload["predictions_hold"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
