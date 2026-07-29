"""The arm's completion gate — `DESIGN.md` §12's 不绿不许收工, split honestly.

```bash
bash ablation-arm/verify.sh          # or: python ablation-arm/verify.py
python ablation-arm/verify.py --json
```

§12 sets the gate as *§8 的七条预注册 + §6 的四道影子逐条数出来 + 上游树 0 改动*.
This item is A4a, which is **implementation only** — 标定与对照留给 A4b — and
that splits the seven predictions in two, because four of them are comparisons
against an arm that has not been run:

| | A4a asserts | A4a records, A4b compares |
|---|---|---|
| P-1 replay accuracy | — | the pixel counts |
| P-2 behavioural / held-out | — | the accuracy |
| P-3 seven surprises become six | **yes** | — |
| P-4 this arm is cheaper | — | the cost line |
| P-5 A0 verdict identical **and correct** | the *correct* half | the *identical* half |
| P-6 A2's false theorem is believed | **yes** | — |
| P-7 the U ladder caps at U2 | **yes** | — |

So the gate is green on **three and a half** of seven, all four shadows, and the
read-only pin.  (`BUILD_PLAN.md` first wrote "4 of 7"; that count was loose —
P-5 is one prediction with two halves and only one of them is settleable here.
Corrected in the plan's progress log rather than quietly.)

**A recorded number can never turn this red.**  That is the whole point of the
split: a gate that failed because a comparison was missing would push whoever
runs it toward inventing the second arm's numbers, and a gate that *passed*
while silently skipping four predictions would be worse. They are printed, in
full, under a heading that says nobody has compared them yet.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

ARTIFACTS = os.path.join(HERE, "artifacts")
VERIFY_JSON = os.path.join(ARTIFACTS, "verify.json")


# ------------------------------------------------------------------- stages

def _stage(label: str, argv: List[str]) -> Tuple[str, int]:
    print("\n" + "=" * 78)
    print("== %s" % label)
    print("=" * 78, flush=True)
    return label, subprocess.run(argv, cwd=REPO).returncode


def _run_stages() -> List[Tuple[str, int]]:
    """The stages, in the order the dependency between them requires.

    **`pytest` runs last, and that is the fix rather than a preference.** It
    used to run second, before `run_arm` -- so the suite judged the *previous*
    invocation's `artifacts/`, and the gate could never see its own tests fail
    on its own output. A red left on disk by run N was carried into run N+1's
    verdict, and a fault introduced in run N could not turn run N red at all.
    `verify()` then reads those same artefacts, so the ordering also decides
    whether the assertions below describe the run that just happened.

    Nothing depends on the old order: `build_theory --check` is a pure check and
    stays first because everything downstream reads the built theory;
    `run_arm`, `run_arm --twice` and `run_exhibits` each compute their paths
    from their own `__file__` and share no state with the suite; and the suite
    re-runs the arm itself where it needs to, so it never depended on `pytest`
    preceding the drivers.
    """
    py = sys.executable
    return [
        _stage("build_theory --check", [py, os.path.join(HERE, "build_theory.py"),
                                        "--check"]),
        _stage("run_arm", [py, os.path.join(HERE, "run_arm.py")]),
        _stage("run_arm --twice", [py, os.path.join(HERE, "run_arm.py"), "--twice"]),
        _stage("run_exhibits", [py, os.path.join(HERE, "run_exhibits.py")]),
        _stage("pytest", [py, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                          os.path.join(HERE, "tests")]),
    ]


def _read(name: str) -> Dict[str, Any]:
    path = os.path.join(ARTIFACTS, name)
    if not os.path.exists(path):
        raise FileNotFoundError("%s is missing; the stages above did not run"
                                % path)
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


# ------------------------------------------------ the predictions A4a settles

def _assertions(run_all: Dict[str, Any], exhibits: Dict[str, Any],
                cut: Dict[str, Any]) -> List[Dict[str, Any]]:
    worlds = run_all["worlds"]
    e1 = exhibits["exhibits"]["E1"]
    e2 = exhibits["exhibits"]["E2"]

    out: List[Dict[str, Any]] = []

    def claim(name: str, what: str, holds: bool, evidence: Any) -> None:
        out.append({"name": name, "claim": what, "holds": bool(holds),
                    "evidence": evidence})

    #: The worlds where the certificate question even arises. `plan_abl` writes
    #: `certificate_owed` and `directed_probes_scheduled` only on the UNSAT
    #: branch, because on a SAT plan there is no impossibility claim to certify
    #: -- the witness *is* the answer. So the fields are **absent** on a SAT
    #: world rather than zero, and the first version of this gate read that
    #: absence as a failure. Coercing absent to 0 would have been the wrong
    #: repair: a gate that defaults a missing field to the value it wants would
    #: pass a run in which the field had silently disappeared.
    settled_by_search = [k for k, w in worlds.items()
                         if w["beats"]["plan"].get("status") == "UNSAT"]
    not_applicable = sorted(set(worlds) - set(settled_by_search))

    def probes_and_certificates_are_absent_or_zero() -> bool:
        for key, world in worlds.items():
            plan = world["beats"]["plan"]
            probes = plan.get("directed_probes_scheduled")
            owed = plan.get("certificate_owed")
            if key in settled_by_search:
                if probes != 0 or owed is not False:
                    return False
            elif probes not in (None, 0) or owed not in (None, False):
                return False
        return True

    # -- P-3 / shadow 4 ------------------------------------------------------
    claim("P-3", "seven surprise kinds become six; `proof_failure` is "
                 "impossible by construction, not by convention",
          (run_all["surprise_kinds_in_taxonomy"] == 7
           and run_all["surprise_kinds_available_to_this_arm"] == 6),
          {"in_taxonomy": run_all["surprise_kinds_in_taxonomy"],
           "available": run_all["surprise_kinds_available_to_this_arm"],
           "removed": ["proof_failure"]})

    # -- P-5, the half that does not need a second arm -----------------------
    claim("P-5(correct)", "the A0 verdict is correct -- `unsolvable` on a world "
                          "that really is. The other half of P-5, *identical to "
                          "the full arm*, is A4b's.",
          (e1["verdict"]["ablated_arm"] == "unsolvable"
           and e1["verdict"]["is_correct"] is True),
          {"verdict": e1["verdict"]["ablated_arm"],
           "settled_by": e1["verdict"]["settled_by"],
           "constructive_ground": e1["verdict"]["constructive_ground"][:120]})

    # -- P-6 -----------------------------------------------------------------
    comparison = run_all["exhibits"]
    claim("P-6", "on A2 the false theorem is believed: UNSAT settles bare, the "
                 "bus stays empty, the loop does not turn, and nothing "
                 "distinguishes it from a true impossibility",
          (e2["holds"] is True
           and comparison["indistinguishable"] is True
           and comparison["n_identical"] == comparison["n_fields"]),
          {"verdict": e2["verdict"]["ablated_arm"],
           "world_really_solvable": e2["the_world"]["really_solvable"],
           "surprises": e2["the_loop"]["surprises"],
           "loop_turns": e2["the_loop"]["turns"],
           "decision_fields_identical": "%d/%d" % (comparison["n_identical"],
                                                   comparison["n_fields"])})

    # -- P-7: the U ladder, assembled from what the run already measured -----
    u1 = all(w["beats"]["certify"]["report"]["green"] for w in worlds.values())
    u2 = all(w["beats"]["compile"]["forms_emitted"] == 3 for w in worlds.values())
    u3_blocked = (probes_and_certificates_are_absent_or_zero()
                  and all(w["beats"]["certify"]["layer_omitted"] == "expensive"
                          for w in worlds.values())
                  and cut["summary"]["n_theorems_deleted"] == 4)
    u4_blocked = (run_all["loop_turned_on"] == []
                  and probes_and_certificates_are_absent_or_zero())
    claim("P-7", "the U ladder caps at U2, constructively: U1 and U2 are "
                 "attained, U3 is unreachable because nothing can admit an "
                 "obligation, and U4 is unreachable because nothing can produce "
                 "a refutation to repair from",
          u1 and u2 and u3_blocked and u4_blocked,
          {"U1_replay_green_on_every_manual": u1,
           "U2_three_forms_emitted_and_every_manual_parses": u2,
           "worlds_where_a_certificate_could_be_owed": settled_by_search,
           "worlds_where_the_question_does_not_arise": not_applicable,
           "U3_blocked": {"certificates_owed": 0,
                          "expensive_layer": "omitted, and raises if called",
                          "theorems_surviving_the_cut": 0},
           "U4_blocked": {"loops_turned": run_all["loop_turned_on"],
                          "directed_probes_scheduled": 0,
                          "note": "the repair machinery is intact -- E2's "
                                  "charity control localises correctly when "
                                  "handed a counterexample. U4 is out of reach "
                                  "because the refutation never arrives, not "
                                  "because repair is broken."}})

    # -- §6, the four shadows, counted rather than asserted ------------------
    summary = cut["summary"]
    claim("shadow-1", "directed probes: every deleted theorem is one probe "
                      "target that no longer has a subject",
          (summary["shadow_1_directed_probe_targets_removed"] == 4
           and probes_and_certificates_are_absent_or_zero()),
          {"targets_removed": summary["shadow_1_directed_probe_targets_removed"],
           "theorems": [t["theorem"] for t in summary["theorems_deleted"]],
           # `.get`, not `[...]`: the predicate above already treats a missing
           # field as a failure, and this dict only describes it. Indexing here
           # would raise while *building the evidence for a red claim*, losing
           # the report and every other claim in it -- a gate that cannot
           # explain why it refused is barely better than one that never does.
           "probes_scheduled_where_the_full_arm_would_have_scheduled_them":
               {k: worlds[k]["beats"]["plan"].get("directed_probes_scheduled",
                                                  "MISSING")
                for k in settled_by_search},
           "not_applicable_on": not_applicable})
    claim("shadow-2", "dependency-driven re-proof: the same count, because it "
                      "is the same cut -- there is nothing left to invalidate",
          summary["shadow_2_entries_no_longer_re_provable"] == 4,
          {"entries": summary["shadow_2_entries_no_longer_re_provable"]})
    claim("shadow-3", "`ArenaEscape` fires only during Lean generation, and no "
                      "Lean form is emitted",
          all(w["beats"]["compile"].get("theory.lean") is None
              and w["beats"]["compile"]["forms_emitted"] == 3
              and w["beats"]["compile"]["forms_in_full_arm"] == 4
              for w in worlds.values()),
          {"forms_emitted": 3, "forms_in_full_arm": 4,
           "omitted": "theory.lean"})
    claim("shadow-4", "`proof_failure` is gone -- the same fact as P-3, counted "
                      "here as a shadow because §6 lists it as one",
          run_all["surprise_kinds_available_to_this_arm"] == 6,
          {"kinds_available": run_all["surprise_kinds_available_to_this_arm"]})

    # -- the read-only pin ---------------------------------------------------
    claim("read-only", "a full run leaves every upstream tree byte-identical",
          run_all["upstream_unchanged"] is True,
          {"files_hashed": run_all["upstream_trees_hashed"],
           "changed": run_all["upstream_files_changed"]})

    # -- and the pre-registered replay counts, which caught a wrong trace ----
    claim("P-1(counts)", "the pre-registered pixel counts hold. This is not P-1 "
                         "-- P-1 is an equality with the full arm -- but the "
                         "counts are a fingerprint of which record was "
                         "replayed, and getting them right is a precondition "
                         "for A4b's comparison meaning anything",
          run_all["pre_registered_holds"] is True,
          {k: w["beats"]["certify"]["pre_registered"]["observed_pixels"]
           for k, w in worlds.items()
           if w["beats"]["certify"]["pre_registered"]["expected_pixels"]})
    return out


# ------------------------------------------- the numbers nobody has compared

def _recorded(run_all: Dict[str, Any], exhibits: Dict[str, Any]) -> Dict[str, Any]:
    worlds = run_all["worlds"]
    return {
        "P-1": {
            "what": "replay accuracy, byte-equal to the full arm",
            "status": "RECORDED -- no second arm has been run",
            "numbers": {k: {"pixels_checked":
                            w["beats"]["certify"]["report"]["pixels_checked"],
                            "anomalies":
                            w["beats"]["certify"]["report"]["anomaly_kinds"],
                            "green": w["beats"]["certify"]["report"]["green"]}
                        for k, w in worlds.items()},
        },
        "P-2": {
            "what": "behavioural / held-out accuracy, equal to the full arm",
            "status": "RECORDED -- and the instrument is missing, not just the "
                      "comparison: nothing in this arm computes a held-out "
                      "split. A4b needs one built before P-2 can be read.",
            "numbers": None,
        },
        "P-4": {
            "what": "this arm is cheaper, not dearer",
            "status": "RECORDED -- and there is no cost instrument here either. "
                      "The arm is offline, so its dollar cost is zero and the "
                      "comparison 1.11 wants is about search and proof fuel, "
                      "which nothing measures yet. A4b's largest gap.",
            "numbers": {"api_calls": 0, "model_calls": 0, "usd": 0.0},
        },
        "P-5(identical)": {
            "what": "the A0 verdict is *identical* to the full arm's",
            "status": "RECORDED -- the verdict and its settling are here; the "
                      "equality needs the full arm",
            "numbers": {"verdict": worlds["a0-no-button"]["verdict"],
                        "settled_by":
                            worlds["a0-no-button"]["beats"]["plan"]["settled_by"]},
        },
        "E3": {
            "what": "the charitable exhibit",
            "status": "NOT CONSTRUCTIBLE -- reported as a pre-registered "
                      "falsifier (DESIGN.md §10 item 3), not as a missing "
                      "deliverable. See artifacts/exhibits.json.",
            "numbers": exhibits["exhibits"]["E3"]["measurements"][
                "M1_workaround_is_a_noop"],
        },
    }


def verify(run_stages: bool = True) -> Dict[str, Any]:
    stages = _run_stages() if run_stages else []
    run_all = _read("run_all.json")
    exhibits = _read("exhibits.json")
    with open(os.path.join(HERE, "theory", "DOWNGRADE_REPORT.json"),
              encoding="utf-8") as handle:
        cut = json.load(handle)

    assertions = _assertions(run_all, exhibits, cut)
    failed_stages = [label for label, code in stages if code != 0]
    failed_claims = [a["name"] for a in assertions if not a["holds"]]

    return {
        "what": "ablation-arm completion gate (A4a)",
        "scope": ("implementation only. Four of the seven pre-registered "
                  "predictions are comparisons against an arm that has not "
                  "been run; they are recorded, never asserted, and cannot "
                  "turn this gate red."),
        "stages": [{"stage": label, "returncode": code} for label, code in stages],
        "assertions": assertions,
        "recorded_for_a4b": _recorded(run_all, exhibits),
        "failed_stages": failed_stages,
        "failed_assertions": failed_claims,
        "green": not failed_stages and not failed_claims,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-stages", action="store_true",
                        help="read the artefacts without re-running anything")
    args = parser.parse_args(argv)

    payload = verify(run_stages=not args.no_stages)
    os.makedirs(ARTIFACTS, exist_ok=True)
    with open(VERIFY_JSON, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
        return 0 if payload["green"] else 1

    print("\n" + "=" * 78)
    print("== the gate: what A4a asserts")
    print("=" * 78)
    for claim in payload["assertions"]:
        print("  %-14s %s" % (claim["name"], "ok" if claim["holds"] else "FAILED"))
        if not claim["holds"]:
            print("      %s" % claim["claim"])
            print("      evidence: %s" % json.dumps(claim["evidence"],
                                                    ensure_ascii=False)[:200])

    print("\n" + "=" * 78)
    print("== recorded for A4b -- NOT asserted, and cannot turn this red")
    print("=" * 78)
    for name, entry in payload["recorded_for_a4b"].items():
        print("  %-15s %s" % (name, entry["status"].split(" -- ")[0]))
        print("      %s" % entry["what"])

    print("\n" + "=" * 78)
    print("== stages")
    for stage in payload["stages"]:
        print("  %-22s %s" % (stage["stage"],
                              "ok" if stage["returncode"] == 0
                              else "FAILED(%d)" % stage["returncode"]))
    print("\nwrote %s" % VERIFY_JSON)
    if payload["green"]:
        print("\nGREEN")
        return 0
    print("\nRED: stages %s, assertions %s"
          % (payload["failed_stages"] or "ok", payload["failed_assertions"] or "ok"))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
