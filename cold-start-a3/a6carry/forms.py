"""Compile a **carried** domain against a rebuilt problem, honestly.

`a3pipeline/compile_a3.compile_instance` is the ancestor and three of its four
workarounds are imported from it unchanged (D-A3-004 `bind_goal`, D-A3-005
`patch_pddl_landmarks`, D-A3-006 `pddl_addressable`).  Two things are new, and
both are refusals rather than features:

**A form that cannot be emitted honestly is not emitted.**  `compile_instance`
always writes four files.  Here the pack declares which forms its domain may be
rendered as (`pack.emittable_forms`), and a withheld form leaves *no file* and a
reason in the report.  The case that forced it is D-A6-002 — a Lean certificate
about a manual whose second moving object is not in the Lean state type would be
green, axiom-free, and about something else.

**The Lean invariant builder must be supplied, not defaulted.**  `generate_lean`
falls back to `door_latch_invariant`, which is keyed on an axis literally named
`Button_colour`; anything else gets `I := true`, every theorem green and an empty
`#print axioms` (D-A3-007, reference trap T4).  A3 passes a builder explicitly
and keeps the vacuous artefact next to the real one so the pair can be diffed.
A driver that can be handed *any* pack cannot rely on the caller remembering, so
`compile_forms` treats "lean requested, no builder" as a withheld form with the
trap named — the fallback is reachable only by asking for it
(`allow_vacuous_lean=True`), which A3's `generated_l1_vacuous` does.
"""

import json
import os
import sys
from typing import Callable, Dict, List, Optional, Sequence

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from theory_compiler.parser.theory_parser import parse_theory  # noqa: E402

from compile.compile_a0 import _write, render_markdown  # noqa: E402  (a0)
from compile.dialect import parse_semantics  # noqa: E402
from compile.gen_lean_a0 import generate_lean  # noqa: E402
from compile.gen_pddl_a0 import generate_pddl  # noqa: E402
from compile.gen_python_a0 import generate_python  # noqa: E402
from compile.problem import Problem  # noqa: E402

from a3pipeline.compile_a3 import (  # noqa: E402
    bind_goal, patch_pddl_landmarks, pddl_addressable,
)
from a6carry import pddl_push  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def compile_forms(dsl_path: str, problem: Problem, out_dir: str,
                  requires: Dict[str, object],
                  invariant_builder: Optional[Callable] = None,
                  allow_vacuous_lean: bool = False,
                  unsolvable: bool = False) -> Dict[str, object]:
    """One carried domain + one rebuilt problem -> the forms the pack allows.

    `requires` is a carrypack's `requires` block; only `mover`, `forms` and
    `forms_withheld` are read, so a caller with an equivalent dict can drive this
    without building a pack.
    """
    text = open(dsl_path, encoding="utf-8").read()
    ast = parse_theory(text)
    semantics = parse_semantics(text)      # raises if the manual does not declare
    bound = bind_goal(ast, problem)        # D-A3-004
    mover = str(requires.get("mover", "Cart"))
    allowed = set(requires.get("forms") or ("python", "markdown", "pddl", "lean"))
    withheld: Dict[str, str] = dict(requires.get("forms_withheld") or {})

    os.makedirs(out_dir, exist_ok=True)
    written: Dict[str, object] = {
        "dsl": os.path.relpath(dsl_path, ROOT).replace(os.sep, "/"),
        "problem": problem.name,
        "mover": mover,
        "goal_bound": (list(problem.goal_cell) if ast.goal is None
                       else "the manual states its own goal"),
    }

    # --- the executable form: the only predictor in the system ---------------
    theory_py = os.path.join(out_dir, "theory.py")
    written["theory.py"] = _write(theory_py,
                                  generate_python(bound, problem, semantics,
                                                  mover=mover))

    # --- the human form ------------------------------------------------------
    written["theory.md"] = _write(os.path.join(out_dir, "theory.md"),
                                  render_markdown(bound, semantics))

    # --- the planning form ---------------------------------------------------
    if "pddl" in allowed:
        pushed = pddl_push.pushed_objects(bound, mover)
        pddl_prob, pushed_cells = pddl_push.strip_pushables(problem, pushed)
        pddl_prob, added = pddl_addressable(bound, pddl_prob)         # D-A3-006
        domain, instance = generate_pddl(bound, pddl_prob)
        domain, instance, landmark_report = patch_pddl_landmarks(     # D-A3-005
            domain, instance, bound, pddl_prob)
        domain, instance, push_report = pddl_push.patch(              # D-A6-001
            domain, instance, bound, mover, pushed_cells)
        written["pddl_cells_added"] = [list(c) for c in added]
        written["pddl_landmarks"] = landmark_report
        written["pddl_pushables"] = push_report
        written["domain.pddl"] = _write(os.path.join(out_dir, "domain.pddl"),
                                        domain)
        written["problem.pddl"] = _write(os.path.join(out_dir, "problem.pddl"),
                                         instance)

    # The problem.json records the *unaugmented* problem — what was rebuilt, not
    # what the PDDL backend had to be told.  Keeping the two apart is what makes
    # D-A3-006 and D-A6-001 auditable rather than merely mentioned.
    written["problem.json"] = _write(
        os.path.join(out_dir, "problem.json"),
        json.dumps(problem.as_json(), indent=2, sort_keys=True) + "\n")

    # --- the proof form ------------------------------------------------------
    if "lean" not in allowed:
        written["lean_withheld"] = withheld.get(
            "lean", "the pack does not list `lean` among its emittable forms")
    elif invariant_builder is None and not allow_vacuous_lean:
        written["lean_withheld"] = (
            "no invariant builder was supplied.  `generate_lean` would fall back "
            "to `door_latch_invariant`, which is keyed on an axis literally named "
            "`Button_colour`; on anything else it returns None and the Lean file "
            "gets `I := true` — every theorem green, `#print axioms` empty, "
            "nothing proved (D-A3-007, trap T4).  Pass a builder, or ask for the "
            "vacuous form on purpose with allow_vacuous_lean=True.")
    else:
        lean = generate_lean(
            bound, problem, theory_py,
            invariant_builder=invariant_builder,
            goal_cell=tuple(problem.goal_cell) if problem.goal_cell else None,
            unsolvable=unsolvable,
            semantics=semantics,
        )
        written["theory.lean"] = _write(os.path.join(out_dir, "theory.lean"), lean)
        written["lean_invariant"] = ("supplied builder" if invariant_builder
                                     else "A0 default, requested explicitly "
                                          "(vacuous unless a Button latch is "
                                          "found — trap T4)")

    written["forms_emitted"] = sorted(
        f for f, key in (("python", "theory.py"), ("markdown", "theory.md"),
                         ("pddl", "domain.pddl"), ("lean", "theory.lean"))
        if key in written)
    written["forms_withheld"] = {
        k: v for k, v in (("lean", written.get("lean_withheld")),) if v}
    return written


def clean_stale(out_dir: str, keep: Sequence[str]) -> List[str]:
    """Delete generated forms this compile did not produce.

    Without this a withheld form is invisible: a `theory.lean` left over from an
    earlier run of the same directory would be picked up by the certify step and
    reported green, and the reason it was withheld would be in a JSON field
    nobody reads.  A withheld form has to be **absent**.
    """
    removed = []
    for name in ("theory.py", "theory.md", "theory.lean", "domain.pddl",
                 "problem.pddl", "problem.json"):
        path = os.path.join(out_dir, name)
        if name not in keep and os.path.exists(path):
            os.remove(path)
            removed.append(name)
    return removed
