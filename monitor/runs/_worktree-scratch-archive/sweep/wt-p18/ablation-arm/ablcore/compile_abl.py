"""C-1 and C-3: compile a manual into three co-derived forms instead of four.

`Theoria.md:239` constraint 1 asks for 同源多形态 — one source, four forms:

    theory.lean + playbook.lean   # 证明形态——机器读者
    theory.py                     # 执行形态——重放与在线执行
    theory.pddl                   # 规划形态
    theory.md + playbook.md       # 自然语言渲染——人类读者

This arm emits the last three and **not** the Lean one.  Three of the four
readers are still served; the machine reader is not, because there is nothing
left for it to check.

The cut is made here rather than in the DSL for a reason that took a survey of
the generators to establish, and that inverts the obvious guess:
`gen_lean_a0.generate_lean` **never reads `ast.laws`**.  A grep across
`cold-start-a0` finds `ast.laws` only in `unsolvable_variant.py:197`,
`concept_account.py` and the tests.  The DSL's `invariant` and `theorem` clauses
render to Markdown prose and nothing else — they *declare* an obligation, they do
not *create* one.  What creates it is this call:

    generate_lean(ast, prob, theory_py,
                  invariant_builder=weight_invariant(region, arena, comment),
                  goal_cell=goal_cell,
                  unsolvable=unsolvable,        # <- emits `theorem unsolvable`
                  semantics=semantics)

So the incision is: never make that call, and never pass `region`, `goal_cell`
or `unsolvable` anywhere (DESIGN.md §4, C-1 and C-3).  Deleting the `laws:`
section instead would have removed prose and left every obligation standing.

A fourth check goes with it, and it is worth naming because the arm losing it
would never notice: `gen_lean_a0` raises `ArenaEscape` when the manual's `step`
leaves the state space the manual itself declares.  That fires during Lean
*generation*, so the cheap layer cannot see it and an arm that generates no Lean
has silently given it up.  DESIGN.md §6 shadow 3.

Every generator called here is `cold-start-a0`'s, unmodified.
"""

import json
import os
from dataclasses import replace as _replace
from typing import Dict, Tuple

import _bootstrap  # noqa: F401

from compile import problem as problem_mod          # noqa: E402  (read-only)
from compile.compile_a0 import _write, render_markdown  # noqa: E402
from compile.dialect import parse_semantics         # noqa: E402
from compile.gen_pddl_a0 import _classify, generate_pddl  # noqa: E402
from compile.gen_python_a0 import generate_python   # noqa: E402
from theory_compiler.parser.theory_parser import parse_theory  # noqa: E402

Cell = Tuple[int, int]

#: The form this arm does not emit, named so that reports can say so positively
#: rather than by omission.
OMITTED_FORM = "theory.lean"


def pddl_addressable(ast, prob, enabled: bool = True):
    """The derived arena, plus every cell some guard names by colour.

    **Copied from `cold-start-a2/a2pipeline/compile_a2.py::pddl_addressable`,
    not imported** — importing anything from `a2pipeline` would pull in modules
    whose `ROOT` is pinned to `cold-start-a2/`, and calling one writes into that
    track's `artifacts/`.  A2 copied A0's `recovered_region` for the same reason
    and said so; this is that convention applied one tree further along.  The
    algorithm is unchanged and the credit is A2's.

    It is the workaround for **D-A2-006**: `gen_pddl_a0._problem` emits a cell
    object only for cells in `problem.arena`, and a static coloured cell like the
    Portal entry is not in it, so `teleport-down`'s `?p - markedcell` parameter
    has no inhabitant and the planner returns UNSAT **on a manual that has the
    teleport rule**.

    `enabled=False` puts that defect back on purpose.  It is the whole mechanism
    of exhibit E3 (DESIGN.md §9): a planner UNSAT that is a fact about the
    encoding and not about the manual, which is the fourth branch that
    `Theoria.md:43`'s three-way does not cover once the proof is gone.
    """
    if not enabled:
        return prob, []
    special, _colours = _classify(ast, prob)
    marked = {cell for cell, kind in special.items() if kind == "markedcell"}
    arena = sorted(set(tuple(c) for c in prob.arena) | marked)
    return (_replace(prob, arena=arena),
            sorted(marked - set(tuple(c) for c in prob.arena)))


def compile_ablated(dsl_path: str, trace_path: str, problem_name: str,
                    out_dir: str, addressable: bool = True) -> Dict[str, object]:
    """One manual -> theory.{py,md} + {domain,problem}.pddl + problem.json.

    No `theory.lean`, no `invariant_builder`, no `goal_cell`, no `unsolvable`.
    """
    text = open(dsl_path, encoding="utf-8").read()
    ast = parse_theory(text)
    semantics = parse_semantics(text)     # raises if the manual does not say
    prob = problem_mod.derive(trace_path, problem_name)
    pddl_prob, added = pddl_addressable(ast, prob, enabled=addressable)
    os.makedirs(out_dir, exist_ok=True)

    written: Dict[str, object] = {
        "pddl_cells_added": [list(c) for c in added],
        "pddl_addressability_patch": bool(addressable),
    }
    written["theory.py"] = _write(os.path.join(out_dir, "theory.py"),
                                  generate_python(ast, prob, semantics))
    written["theory.md"] = _write(os.path.join(out_dir, "theory.md"),
                                  render_markdown(ast, semantics))
    domain, instance = generate_pddl(ast, pddl_prob)
    written["domain.pddl"] = _write(os.path.join(out_dir, "domain.pddl"), domain)
    written["problem.pddl"] = _write(os.path.join(out_dir, "problem.pddl"), instance)
    written["problem.json"] = _write(
        os.path.join(out_dir, "problem.json"),
        json.dumps(prob.as_json(), indent=2, sort_keys=True) + "\n")

    written[OMITTED_FORM] = None
    written["forms_emitted"] = 3
    written["forms_in_full_arm"] = 4
    written["omitted_because"] = (
        "constraint 1's proof form is a proof obligation; this arm has none "
        "(DESIGN.md §4 C-1).  ArenaEscape goes with it (§6 shadow 3).")
    return written
