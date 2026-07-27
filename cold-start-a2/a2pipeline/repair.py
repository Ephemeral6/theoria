"""M9–M11 — 修订 → 重证 → 解出.  The last three beats of the loop.

**修订** is the one step a script cannot do, and it is not done here:
`theory/theory_repaired.dsl` is a hand-written artefact adjudicated from
`probes.jsonl`, and this module consumes it.  Same discipline as A0's M3.

**重证** is two obligations, not one, and skipping the first would be the
interesting kind of dishonesty:

* *the old certificate has to die.*  A repaired manual that quietly stops
  mentioning its refuted theorem has not been corrected, it has been edited.  So
  the holed manual's invariant — the 0/1 weight that is 0 only on the left room
  — is regenerated **against the repaired `step`** and handed to Lean, which must
  now report an error.  `generated_repaired_stale/` exists to hold a red
  artefact, and its redness is the evidence.
* *a true certificate has to replace it.*  The repaired manual proves
  `unsolvable` for the sealed pocket (7,1): same generator, same `decide`-only
  tactic, same empty axiom list, opposite truth value.  A2's headline is that
  pair of files.

The certificate's region is derived differently from the exhibit's, and the
difference is itself a result.  `zero_space` proposes the set of cells the Cart
was *observed* on; for the holed manual that set is already closed under the
manual's `step`, and it was used as-is.  For the repaired manual it is **not** —
the probe only ever put the Cart on (7,6), so the engine's law would fail
`inv_closed` at the first move inside the right room.  The theorize step widens
it by closing the observed set under the manual's own executable form.  That
uses no world access: the manual is a program, and asking a program where it
says the Cart can go is reading the manual, not peeking at the answer.

**解出** is the plan, and then the same two independent checks as everywhere
else: does the manual agree, and does the world agree.
"""

import json
import os
import sys
from typing import Dict, List, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from certify.replay import ACTION_NAMES, load_theory  # noqa: E402
from compile import problem as problem_mod  # noqa: E402
from compile.compile_a0 import _write  # noqa: E402
from compile.dialect import parse_semantics  # noqa: E402
from compile.gen_lean_a0 import generate_lean, weight_invariant  # noqa: E402
from theory_compiler.parser.theory_parser import parse_theory  # noqa: E402

from a2pipeline import certify_a2  # noqa: E402
from a2pipeline.compile_a2 import compile_manual, observed_region  # noqa: E402
from a2pipeline.plan import run_plan  # noqa: E402
from a2world import a2_world  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACTS = os.path.join(ROOT, "artifacts")
TRACE = os.path.join(ARTIFACTS, "probed_trace.jsonl")
DSL = os.path.join(ROOT, "theory", "theory_repaired.dsl")
OUT = os.path.join(ROOT, "theory", "generated_repaired")
STALE = os.path.join(ROOT, "theory", "generated_repaired_stale")

POCKET: Tuple[int, int] = a2_world.POCKET_CELL


def manual_closure(theory_py: str) -> List[Tuple[int, int]]:
    """Every cell the MANUAL says the Cart can occupy, by running the manual.

    A reachability closure over `theory.py`'s own state space.  No world access:
    this is the manual answering a question about itself.
    """
    theory = load_theory(theory_py)
    start = theory.initial_state()
    seen = {start.key(): start}
    frontier = [start]
    cells = {tuple(start.Cart_pos)}
    while frontier:
        state = frontier.pop()
        for action in ACTION_NAMES.values():
            nxt = theory.step(state, action)
            if nxt.key() in seen:
                continue
            seen[nxt.key()] = nxt
            cells.add(tuple(nxt.Cart_pos))
            frontier.append(nxt)
    return sorted(cells)


def reprove_stale(region: Sequence[Tuple[int, int]]) -> Dict[str, object]:
    """Regenerate the EXHIBIT's invariant against the REPAIRED step, expect red."""
    text = open(DSL, encoding="utf-8").read()
    ast = parse_theory(text)
    semantics = parse_semantics(text)
    prob = problem_mod.derive(TRACE, "a2-repaired")
    os.makedirs(STALE, exist_ok=True)

    # theory.py must exist here too: the Lean backend transcribes `step` by
    # executing it, so the stale file has to be built on the repaired dynamics.
    from compile.gen_python_a0 import generate_python
    _write(os.path.join(STALE, "theory.py"), generate_python(ast, prob, semantics))

    comment = (
        "STALE ON PURPOSE.  This is the exhibit's certificate — w = 0 only on the\n"
        "%d cells of the left room — regenerated against the REPAIRED step.  It is\n"
        "kept as a red artefact: `inv_closed` is now false, because teleport_down\n"
        "carries the Cart from a w = 0 cell to a w = 1 cell in one move.  A manual\n"
        "that dropped its refuted theorem silently would leave no trace of this."
        % len(region)
    )
    lean_src = generate_lean(
        ast, prob, os.path.join(STALE, "theory.py"),
        invariant_builder=weight_invariant(region, [tuple(c) for c in prob.arena],
                                           comment),
        unsolvable=True,
        semantics=semantics,
    )
    path = os.path.join(STALE, "theory.lean")
    _write(path, lean_src)
    report = certify_a2.lean(path)
    return {
        "file": os.path.relpath(path, ROOT),
        "region_size": len(region),
        "lean": certify_a2.lean_brief(report),
        "died": not report.get("green"),
        "first_error": (report.get("errors") or [None])[0],
        "reading": "the exhibit's invariant is no longer closed under the manual's "
                   "step; the pagoda is broken by exactly the rule the probe added, "
                   "and Lean says so",
    }


def build() -> Dict[str, object]:
    report: Dict[str, object] = {"manual": "theory_repaired.dsl",
                                 "evidence": "probed_trace.jsonl"}

    # ---- the certificate's region, and why the engine's proposal is not it --
    engine_region, law = observed_region(TRACE)
    # A throwaway compile first, purely to have an executable form to close over.
    compile_manual(DSL, TRACE, "a2-repaired", OUT)
    closure = manual_closure(os.path.join(OUT, "theory.py"))
    region = [c for c in closure if tuple(c) != POCKET]
    report["region"] = {
        "zero_space_proposed": [list(c) for c in engine_region],
        "zero_space_size": len(engine_region),
        "zero_space_rendering": law["rendering"][:120],
        "manual_closure": [list(c) for c in closure],
        "manual_closure_size": len(closure),
        "adopted": [list(c) for c in region],
        "adopted_size": len(region),
        "pocket_in_closure": list(POCKET) in [list(c) for c in closure],
        "why": "zero_space proposes the cells the Cart was OBSERVED on; the probe "
               "only ever put it on (7,6), so that law is not closed under the "
               "repaired step and would fail inv_closed one move into the right "
               "room.  The theorize step widens it to the manual's own "
               "reachability closure — computed by running theory.py, not by "
               "reading the world — and removes the pocket, which the closure "
               "does not contain anyway.",
    }
    print("region: engine proposed %d cells, manual closure %d, adopted %d"
          % (len(engine_region), len(closure), len(region)))

    # ---- 修订: compile the repaired manual for real -------------------------
    comment = (
        "pocket_unreachable (THEORIZE_LOG L-05).  w = 0 on the %d cells the\n"
        "manual's own reachability closure contains; the sealed pocket (7,1)\n"
        "carries w = 1.  I(s) := w(cart) = 0 is 'the potential never rises'.\n"
        "\n"
        "Same generator, same tactic and same empty axiom list as the exhibit in\n"
        "theory/generated_holed/theory.lean.  This one is TRUE of the world.  The\n"
        "instrument cannot tell the difference; only the probes can." % len(region)
    )
    report["compiled"] = compile_manual(DSL, TRACE, "a2-repaired", OUT,
                                        region=region, comment=comment,
                                        goal_cell=POCKET, unsolvable=True)

    # The latch law, on a second Lean file, so the repaired manual does not
    # quietly drop an invariant it still declares.
    text = open(DSL, encoding="utf-8").read()
    ast = parse_theory(text)
    semantics = parse_semantics(text)
    prob = problem_mod.derive(TRACE, "a2-repaired")
    latch_path = os.path.join(OUT, "theory_latch.lean")
    _write(latch_path, generate_lean(ast, prob, os.path.join(OUT, "theory.py"),
                                     semantics=semantics))

    # ---- certify, cheap ----------------------------------------------------
    cheap = certify_a2.cheap(os.path.join(OUT, "theory.py"), TRACE)
    report["certify_cheap"] = {k: cheap[k] for k in
                               ("frames", "transitions", "pixels_checked",
                                "anomaly_kinds", "green")}
    print("cheap :", certify_a2.summary(cheap))

    # ---- 重证 (a): the old certificate dies --------------------------------
    report["stale_certificate"] = reprove_stale(engine_region_for_stale())
    print("stale :", "DIED (as it must)" if report["stale_certificate"]["died"]
          else "STILL GREEN — that would be a bug")

    # ---- 重证 (b): a true certificate takes its place ----------------------
    lean = certify_a2.lean(os.path.join(OUT, "theory.lean"))
    report["certify_lean"] = certify_a2.lean_brief(lean)
    print("lean  :", "GREEN" if lean.get("green") else "RED",
          json.dumps(lean.get("axiom_reports")))
    for line in (lean.get("errors") or [])[:6]:
        print("       ", line)

    latch = certify_a2.lean(latch_path)
    report["certify_lean_latch"] = certify_a2.lean_brief(latch)
    print("latch :", "GREEN" if latch.get("green") else "RED",
          json.dumps(latch.get("axiom_reports")))

    # ---- and is the new theorem actually true of the world? ----------------
    # The referee's check, run here and nowhere earlier: the theorem is about
    # the pocket, and the world is asked whether any reachable state puts the
    # Cart there.  This is scoring, not theorizing.
    world = a2_world.A2World(a2_world.BASE)
    occupied = [s for s in world.reachable() if s.cart == POCKET]
    report["scored_against_the_world"] = {
        "theorem": "pocket_unreachable",
        "world_states_with_cart_in_pocket": len(occupied),
        "true_of_the_world": not occupied,
        "contrast": "the exhibit's theorem had the same shape, the same tactic "
                    "and the same empty axiom list, and was false of the world",
    }

    # ---- 解出 ---------------------------------------------------------------
    plan = run_plan(OUT, "repaired", candidates_path=os.path.join(
        ARTIFACTS, "candidates_repaired.jsonl"))
    report["plan"] = plan
    print("plan  :", plan["status"], plan.get("length"),
          "manual_agrees=%s world_agrees=%s" % (plan.get("manual_reaches_goal"),
                                                plan.get("world_reaches_goal")))

    report["green"] = bool(
        cheap["green"]
        and report["stale_certificate"]["died"]
        and lean.get("green")
        and latch.get("green")
        and report["scored_against_the_world"]["true_of_the_world"]
        and plan.get("green")
    )
    return report


_STALE_REGION_CACHE: Dict[str, List[Tuple[int, int]]] = {}


def engine_region_for_stale() -> List[Tuple[int, int]]:
    """The exhibit's region, read back from the exhibit's own report.

    Read from `exhibit_report.json` rather than recomputed, so the stale
    certificate is provably the same one Lean signed off on in M5.
    """
    if "region" not in _STALE_REGION_CACHE:
        exhibit = json.load(open(os.path.join(ARTIFACTS, "exhibit_report.json"),
                                 encoding="utf-8"))
        _STALE_REGION_CACHE["region"] = [
            tuple(c) for c in exhibit["zero_space"]["region"]]
    return _STALE_REGION_CACHE["region"]


def main() -> int:
    os.environ.setdefault("THEORIA_DETERMINISTIC_IDS", "1")
    os.environ.setdefault("THEORIA_FIXED_TIME", "2026-07-28T00:00:00Z")
    report = build()
    with open(os.path.join(ARTIFACTS, "repair_report.json"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print()
    print("REPAIR:", "GREEN" if report["green"] else "RED")
    return 0 if report["green"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
