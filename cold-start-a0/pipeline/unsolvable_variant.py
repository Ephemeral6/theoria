"""M5 — the unsolvable variant, and the full certificate obligation.

**The variant, and its constructive ground.** `a0-no-button` is `a0-base` with
the Button removed. The Door is the only opening in the wall that separates the
Cart's room from the goal's room; the only rule that ever removed the Door was
`door_opens_left`, whose guard tests for the Button's colour; with no Button that
guard can never hold. So the goal is unreachable **by construction** — known
before anything is run, which is what Theoria Phase 1 layer 2 demands of a
variant ("每个变体必须随附构造性依据…不靠跑来确认").

**The loop this file drives**, in the order the framework specifies:

```
certify (cheap)   replay the variant's own trace through the variant manual
plan              theory.pddl -> fd_adapter  ->  UNSAT
                  constraint 6: a bare UNSAT is not an answer
certificate       zero_space proposes; the theorize step picks the coset
                  representative that says something about the world
certify (dear)    Lean: inv_init / inv_closed / goal_break / unsolvable,
                  `decide` only, `#print axioms` empty
explain           the theorem, in the manual's own vocabulary
```

The certificate step is worth spelling out, because it is the division of labour
in miniature. `zero_space` hands back a whole *space* of GF(2) conservation laws
— every vector in it is equally a law, and most of them say nothing. Choosing the
representative that reads as *"the Cart never leaves the left room"* is a
semantic act, and it is the only step here a machine does not do.
"""

import json
import os
import sys
from typing import Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from engines import zero_space  # noqa: E402
from theory_compiler.parser.theory_parser import parse_theory  # noqa: E402

from certify import lean_check, replay  # noqa: E402
from compile import problem as problem_mod  # noqa: E402
from compile.compile_a0 import _write, render_markdown  # noqa: E402
from compile.dialect import parse_semantics  # noqa: E402
from compile.gen_lean_a0 import generate_lean, weight_invariant  # noqa: E402
from compile.gen_pddl_a0 import generate_pddl  # noqa: E402
from compile.gen_python_a0 import generate_python  # noqa: E402
from pipeline import segment_operators  # noqa: E402
from pipeline.board import extract_board, object_layer  # noqa: E402
from pipeline.engines_stage import (  # noqa: E402
    background_color, zero_space_cells, zero_space_states,
)
from pipeline.plan_stage import run_plan  # noqa: E402
from theory_compiler.generators.gen_markdown import generate_markdown  # noqa: E402
from world import a0_world  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACTS = os.path.join(ROOT, "artifacts")
TRACE = os.path.join(ARTIFACTS, "raw_trace_no_button.jsonl")
DSL = os.path.join(ROOT, "theory", "theory_no_button.dsl")
OUT = os.path.join(ROOT, "theory", "generated_no_button")


def recovered_region(trace_path: str) -> Tuple[List[Tuple[int, int]], Dict]:
    """Ask `zero_space` where the Cart can be, and pick the readable law.

    Every global law is a subset of arena cells whose Cart-occupancy parity is
    conserved. The one that means something is the one whose support is the set
    of cells the Cart is ever seen on — read as *"exactly one of these cells
    holds the Cart, always"*, i.e. the Cart never leaves that region.
    """
    from world.ground_truth import read_trace

    frames, _actions, _wins = read_trace(trace_path)
    board = extract_board(frames)
    background = background_color(board, frames)
    layer = object_layer(frames, board, background=background)
    cells = zero_space_cells(board, background)
    states = zero_space_states(layer, cells, background)
    colours = sorted({v for s in states for v in s if v != "."})
    result = zero_space.analyse(states, colours)
    if not zero_space.verify(result, states):
        raise AssertionError("a recovered law does not hold on the trajectory")

    mover_colour = "6"
    best = None
    for law in result.global_laws():
        support = law.support()
        if any(f.color != mover_colour for f in support):
            continue
        if law.value != 1:
            continue
        if best is None or len(support) < len(best.support()):
            best = law
    if best is None:
        raise AssertionError("zero_space found no single-colour occupancy law")

    region = sorted(cells[f.cell] for f in best.support())

    # The engine's own soundness check, re-run on the representative we picked.
    vector = best.vector
    detail = {
        "rendering": best.rendering(),
        "value": best.value,
        "region": [list(c) for c in region],
        "region_size": len(region),
        "space_dimension": result.dimension,
        "difference_rank": result.difference_rank,
        "in_recovered_space": result.contains(vector),
        "arena": len(cells),
    }
    return region, detail


def compile_variant(region: Sequence[Tuple[int, int]]) -> Dict[str, int]:
    text = open(DSL, encoding="utf-8").read()
    ast = parse_theory(text)
    semantics = parse_semantics(text)
    prob = problem_mod.derive(TRACE, "a0-no-button")
    os.makedirs(OUT, exist_ok=True)

    written = {}
    written["theory.py"] = _write(os.path.join(OUT, "theory.py"),
                                  generate_python(ast, prob, semantics))
    written["theory.md"] = _write(os.path.join(OUT, "theory.md"),
                                  render_markdown(ast, semantics))
    domain, instance = generate_pddl(ast, prob)
    written["domain.pddl"] = _write(os.path.join(OUT, "domain.pddl"), domain)
    written["problem.pddl"] = _write(os.path.join(OUT, "problem.pddl"), instance)
    written["problem.json"] = _write(
        os.path.join(OUT, "problem.json"),
        json.dumps(prob.as_json(), indent=2, sort_keys=True) + "\n")

    comment = (
        "right_room_locked (THEORIZE_LOG L-04), proposed by zero_space as a GF(2)\n"
        "occupancy law over %d arena cells and adjudicated into this form.\n"
        "w = 0 exactly on the %d cells the Cart was ever observed on; the goal cell\n"
        "carries w = 1.  I(s) := w(cart) = 0 is 'the potential never rises'."
        % (len(prob.arena), len(region))
    )
    lean = generate_lean(
        ast, prob, os.path.join(OUT, "theory.py"),
        invariant_builder=weight_invariant(region, [tuple(c) for c in prob.arena],
                                           comment),
        unsolvable=True,
        semantics=semantics,
    )
    written["theory.lean"] = _write(os.path.join(OUT, "theory.lean"), lean)
    return written


def main() -> int:
    os.environ.setdefault("THEORIA_DETERMINISTIC_IDS", "1")
    os.environ.setdefault("THEORIA_FIXED_TIME", "2026-07-28T00:00:00Z")

    report: Dict[str, object] = {"variant": "a0-no-button"}
    report["constructive_ground"] = (
        "the Door is the only opening in the dividing wall, and the only rule "
        "that removes it (door_opens_left) tests for the Button's colour; with "
        "no Button in the instance that guard can never hold, so the goal room "
        "is unreachable by construction"
    )

    # 1 — the certificate's raw material, from the engine
    region, law = recovered_region(TRACE)
    report["zero_space"] = law
    print("law:", law["rendering"][:90], "... region of %d cells" % law["region_size"])

    # 2 — compile
    written = compile_variant(region)
    report["compiled"] = written

    # 3 — certify, cheap
    cheap = replay.certify(os.path.join(OUT, "theory.py"), TRACE)
    report["certify_cheap"] = {k: cheap[k] for k in
                               ("frames", "pixels_checked", "anomaly_kinds", "green")}
    print("cheap :", replay.contested_summary(cheap))

    # 4 — plan; UNSAT is the branch we are here for
    plan = run_plan(OUT, a0_world.NO_BUTTON,
                    out_path=os.path.join(ARTIFACTS, "candidates_no_button.jsonl"))
    report["plan"] = plan
    print("plan  :", plan["status"])

    # 5 — certify, expensive
    lean = lean_check.check(os.path.join(OUT, "theory.lean"))
    report["certify_lean"] = {k: lean.get(k) for k in
                              ("available", "returncode", "errors", "sorries",
                               "axiom_reports", "green")}
    print("lean  :", "GREEN" if lean.get("green") else "RED",
          json.dumps(lean.get("axiom_reports")))

    # 6 — the theorem, in the manual's own words
    ast = parse_theory(open(DSL, encoding="utf-8").read())
    theorem = ast.laws.theorems[0]
    report["theorem"] = {
        "name": theorem.name,
        "explanation": theorem.description,
        "depends": theorem.depends,
        "probe": theorem.probe,
        "lean_target": "unsolvable",
        "axioms": [r for r in (lean.get("axiom_reports") or [])
                   if r["name"] == "unsolvable"],
    }

    report["green"] = bool(
        cheap["green"] and plan["status"] == "UNSAT" and lean.get("green")
    )
    with open(os.path.join(ARTIFACTS, "unsolvable_report.json"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("M5    :", "GREEN" if report["green"] else "RED")
    print()
    print(theorem.description)
    return 0 if report["green"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
