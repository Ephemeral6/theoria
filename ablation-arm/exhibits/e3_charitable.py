"""E3 — the charitable variant, and why it can no longer be built here.

`DESIGN.md` §E3 exists to answer a punch the review will certainly throw: *你没
给它反例,当然它修不好*.  Its construction was:

> 拿**完整**手册(有 teleport,step 无缺陷),关掉 D-A2-006 的绕开
> (`pddl_addressable`),编译 → 规划器返回 UNSAT → 消融臂定案"不可解"。
> 再把世界的解路白送给它:三查**全绿**,`culprits == []`。
> **三选一回来一个空集。定位退化成"不知道"。**

**That construction no longer exists in this repository, and this module says so
with measurements rather than with a substitute.**  `DESIGN.md` §10 pre-registers
this kind of outcome as a falsifier — *E3 的三查没有全绿 ⇒ 我对 D-A2-006 的理解
错了,§9 的论证要撤回* — so reporting it is the designed behaviour, not a
failure to deliver.  What is refuted is narrower and more specific than §10
anticipated: not the reading of D-A2-006, but its **continued existence**.

Five measurements, all performed here:

    M1  the workaround is a no-op: `pddl_addressable(enabled=False)` and
        `enabled=True` emit byte-identical `problem.pddl` and `domain.pddl`
    M2  and why: the generator names more cell objects than `prob.arena` holds,
        so the Portal entry cell is grounded with the patch off. D-A2-006's gap
        was closed upstream, which makes `compile_abl.pddl_addressable` dead
        code on this input
    M3  so the complete manual plans **SAT** either way, with `teleport-down`
        in the plan -- there is no UNSAT to exhibit
    M4  the nearest live UNSAT on a manual with nothing wrong with it: the
        complete manual compiled from the *truncated* evidence. Cheap layer
        green over 184 frames, planner UNSAT. But its `theory.py` **raises**
        `KeyError('portal_exit')` on the witness path -- the landmark is derived
        from evidence that stops before the portal exit is ever seen -- so
        `locate` cannot return a culprit set at all
    M5  and the empty culprit set does exist, on the complete manual with the
        full evidence: `culprits == []`, zero step diffs. But that manual plans
        SAT, so there is no false impossibility for the empty set to be empty
        *about*

E3 needs the **conjunction**: a planner UNSAT on a manual that is correct and
executable, so that the three-way comes back empty against a claim that is
false.  M3/M4/M5 are the three ways that conjunction comes apart here, and no
two of them can be brought together on this repository's material.

## What survives, and where it went

The point E3 was defending survives intact, and it is stronger for being
measured somewhere else: **handed a counterexample, the ablated arm localises
correctly.**  That is `e2_a2.charity_control`, which gives the holed manual the
world's solved episode and gets `culprits = ['mispredicted_step']` with exactly
one disagreeing step.  So the reviewer's punch is answered — the ablation did
not remove the ability to repair, it removed the thing that produces the
counterexample — and it is answered on the exhibit it threatens rather than in a
separate construction that no longer stands up.

What is genuinely lost is E3's *other* half: the demonstration that a planner's
UNSAT can be a fact about the encoding rather than about the world, so that
`Theoria.md:43`'s three-way is not exhaustive without a proof. M4 is evidence
for it — a manual with nothing wrong with it, green on its evidence, declared
impossible — but it is weaker evidence than a clean E3, because that manual is
not executable on the witness path and a reader can fairly say the fault is in
the truncated evidence rather than in the encoding. Recorded as a gap for A4b
rather than papered over.
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import _bootstrap                                                  # noqa: F401,E402

from ablcore import certify_abl, compile_abl, plan_abl             # noqa: E402

EXHIBIT = "E3"
FULL_TRACE = "cold-start-a2/artifacts/raw_trace.jsonl"
TRUNCATED_TRACE = "cold-start-a2/artifacts/history_trace.jsonl"
SOLVED_EPISODE = "cold-start-a2/artifacts/solved_episode.jsonl"
COMPLETE_MANUAL = "a2_base.dsl"


def _compile(trace: str, addressable: bool) -> str:
    out = tempfile.mkdtemp(prefix="e3-")
    compile_abl.compile_ablated(os.path.join(HERE, "theory", COMPLETE_MANUAL),
                                os.path.join(REPO, trace), "e3", out,
                                addressable=addressable)
    return out


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def run() -> Dict[str, Any]:
    measurements: Dict[str, Any] = {}

    # -- M1 / M2: is the workaround still a workaround? ----------------------
    patched, unpatched = _compile(FULL_TRACE, True), _compile(FULL_TRACE, False)
    identical = {}
    for name in ("problem.pddl", "domain.pddl"):
        identical[name] = (_read(os.path.join(patched, name))
                           == _read(os.path.join(unpatched, name)))
    problem_pddl = _read(os.path.join(unpatched, "problem.pddl"))
    arena = json.loads(_read(os.path.join(unpatched, "problem.json")))["arena"]
    named_cells = set(re.findall(r"\bc\d+-\d+\b", problem_pddl))
    measurements["M1_workaround_is_a_noop"] = {
        "pddl_byte_identical_with_patch_on_and_off": identical,
        "holds": all(identical.values()),
    }
    measurements["M2_why"] = {
        "cell_objects_named_in_problem_pddl": len(named_cells),
        "cells_in_derived_arena": len(arena),
        "portal_entry_grounded_without_the_patch": "c7-4" in problem_pddl,
        "reading": ("the generator emits cell objects from something wider than "
                    "`prob.arena`, so the Portal entry cell is an object with "
                    "the patch off. D-A2-006's gap is closed upstream and "
                    "`compile_abl.pddl_addressable` is dead code on this input."),
    }

    # -- M3: so there is no UNSAT to exhibit ---------------------------------
    plans = {}
    for label, out in (("patched", patched), ("unpatched", unpatched)):
        report = plan_abl.run_plan(out, "e3-%s" % label)
        plans[label] = {"status": report["status"],
                        "length": report.get("length"),
                        "teleport_in_plan": any("teleport" in a for a in
                                                report.get("actions", []))}
    measurements["M3_complete_manual_full_evidence"] = {
        "plans": plans,
        "holds": all(p["status"] == "SAT" for p in plans.values()),
        "reading": "SAT with the patch on and off, teleport in the plan both "
                   "times. The construction E3 asked for cannot start.",
    }

    # -- M4: the nearest live UNSAT on a manual with nothing wrong with it ---
    truncated = _compile(TRUNCATED_TRACE, True)
    cheap = certify_abl.cheap(os.path.join(truncated, "theory.py"),
                              os.path.join(REPO, TRUNCATED_TRACE))
    plan_truncated = plan_abl.run_plan(truncated, "e3-truncated")
    locate_raised: Optional[str] = None
    locate_truncated: Optional[Dict[str, Any]] = None
    from a2pipeline.locate import locate                           # noqa: E402
    try:
        result = locate(os.path.join(truncated, "theory.py"),
                        os.path.join(REPO, SOLVED_EPISODE))
        locate_truncated = {"culprits": result["culprits"],
                            "n_step_diffs": result["n_step_diffs"]}
    except Exception as exc:                        # noqa: BLE001 -- reported
        locate_raised = "%s: %s" % (type(exc).__name__, exc)
    measurements["M4_complete_manual_truncated_evidence"] = {
        "cheap_layer": {"green": cheap["green"], "frames": cheap["frames"],
                        "pixels_checked": cheap["pixels_checked"]},
        "plan_status": plan_truncated["status"],
        "locate": locate_truncated,
        "locate_raised": locate_raised,
        "reading": ("a manual with nothing wrong with it, green on its own "
                    "evidence, declared impossible -- but `locate` cannot "
                    "answer, because the manual is not executable on the "
                    "witness path: the `portal_exit` landmark is derived from "
                    "evidence that stops before that cell is ever seen."),
    }

    # -- M5: the empty culprit set exists, with nothing false to be about ----
    result = locate(os.path.join(patched, "theory.py"),
                    os.path.join(REPO, SOLVED_EPISODE))
    measurements["M5_empty_culprit_set"] = {
        "culprits": result["culprits"],
        "n_step_diffs": result["n_step_diffs"],
        "checks": result["checks"],
        "but_the_plan_was": plans["patched"]["status"],
        "reading": ("the three-way does come back empty on the complete "
                    "manual -- correctly, because nothing is wrong with it. "
                    "There is no false impossibility for the empty set to be "
                    "empty about, so this is not E3's testimony either."),
    }

    constructible = False
    return {
        "exhibit": EXHIBIT,
        "class": "the adversarial-review control, not a verdict class",
        "designed_construction": (
            "complete manual + `pddl_addressable(enabled=False)` -> UNSAT -> "
            "hand it the solution path -> three checks green, culprits == []"),
        "constructible": constructible,
        "measurements": measurements,
        "holds": constructible,
        "falsifier": ("DESIGN.md §10 item 3 pre-registers `E3 的三查没有全绿` as "
                      "a falsifier requiring §9's argument to be withdrawn. What "
                      "is refuted is narrower: not the reading of D-A2-006 but "
                      "its continued existence. The workaround it needed is now "
                      "dead code."),
        "what_survives": (
            "the point E3 defended is measured in `e2_a2.charity_control`: "
            "handed the world's solved episode, the ablated arm localises the "
            "holed manual correctly (`culprits = ['mispredicted_step']`, one "
            "step). The reviewer's punch -- 你没给它反例,当然它修不好 -- is "
            "answered on the exhibit it threatens."),
        "what_is_lost": (
            "E3's other half: a clean demonstration that a planner's UNSAT can "
            "be a fact about the encoding rather than about the world, which is "
            "what makes Theoria.md:43's three-way non-exhaustive without a "
            "proof. M4 is weaker evidence for it and is recorded as a gap for "
            "A4b rather than presented as E3."),
    }


def main() -> int:
    report = run()
    print("%s -- %s" % (EXHIBIT, report["class"]))
    print("  designed construction is constructible: %s" % report["constructible"])
    m = report["measurements"]
    print("  M1 workaround is a no-op        : %s"
          % m["M1_workaround_is_a_noop"]["holds"])
    print("  M2 cells named %d vs arena %d, portal entry grounded unpatched=%s"
          % (m["M2_why"]["cell_objects_named_in_problem_pddl"],
             m["M2_why"]["cells_in_derived_arena"],
             m["M2_why"]["portal_entry_grounded_without_the_patch"]))
    print("  M3 complete manual + full trace : %s"
          % {k: v["status"] for k, v in
             m["M3_complete_manual_full_evidence"]["plans"].items()})
    m4 = m["M4_complete_manual_truncated_evidence"]
    print("  M4 complete + truncated         : cheap green=%s, plan=%s, "
          "locate=%s" % (m4["cheap_layer"]["green"], m4["plan_status"],
                         m4["locate_raised"] or m4["locate"]))
    print("  M5 empty culprit set            : %s (plan was %s)"
          % (m["M5_empty_culprit_set"]["culprits"] or "[] EMPTY",
             m["M5_empty_culprit_set"]["but_the_plan_was"]))
    print("  holds: %s -- reported as a falsifier, not worked around"
          % report["holds"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
