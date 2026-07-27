"""M4 — compile each manual into its four co-derived forms.

The backends are A0's, imported unmodified (`cold-start-a0/compile/`): the v0.1
parser, `gen_python_a0`, `gen_pddl_a0`, `gen_lean_a0`, `gen_markdown`, and the
`semantics:` dialect reader.  A2 writes no generator.  That is the point of
reusing them — if the exhibit came out of a compiler written for the exhibit it
would prove nothing about the instrument.

Three manuals, three output directories, and the *only* thing that differs
between the first two is the .dsl they are compiled from:

    theory.dsl          + raw_trace.jsonl      -> generated/           (control)
    theory_holed.dsl    + history_trace.jsonl  -> generated_holed/     (exhibit)
    theory_repaired.dsl + probed_trace.jsonl   -> generated_repaired/  (the fix)

Each manual is paired with the evidence its theorizer actually had.  The holed
manual is compiled against the play record because that is the whole claim: the
theorizer who saw only the history writes this manual, and it is green on
everything they can check.

The Lean invariant is chosen per target, because the three targets are asking
three different questions:

  * control    — `door_latch`, the latch law.  TRUE, and provable.
  * holed      — a 0/1 pagoda weight, 0 on the region the Cart was seen in.
                 `unsolvable` for the goal cell.  Provable, axiom-free, **false
                 of the world**.
  * repaired   — the same 0/1 weight shape, now 0 on both rooms, `unsolvable`
                 for the sealed pocket (7,1).  Provable, axiom-free, **true of
                 the world**.

Same generator, same tactic, same empty axiom list, opposite truth values.  That
is Theoria §1.10a's two-layer regime as two files you can diff.
"""

import json
import os
import sys
from typing import Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from engines import zero_space  # noqa: E402

from compile import problem as problem_mod  # noqa: E402  (cold-start-a0, read-only)
from compile.compile_a0 import _write, render_markdown  # noqa: E402
from compile.dialect import parse_semantics  # noqa: E402
from compile.gen_lean_a0 import generate_lean, weight_invariant  # noqa: E402
from compile.gen_pddl_a0 import _classify, generate_pddl  # noqa: E402
from compile.gen_python_a0 import generate_python  # noqa: E402
from pipeline.board import extract_board, object_layer  # noqa: E402
from pipeline.engines_stage import (  # noqa: E402
    background_color, zero_space_cells, zero_space_states,
)
from theory_compiler.parser.theory_parser import parse_theory  # noqa: E402

from a2world.ground_truth import read_trace  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACTS = os.path.join(ROOT, "artifacts")
THEORY = os.path.join(ROOT, "theory")

Cell = Tuple[int, int]


def observed_region(trace_path: str) -> Tuple[List[Cell], Dict]:
    """Ask `zero_space` where the Cart can be, and pick the readable law.

    Lifted from A0's `unsolvable_variant.recovered_region` (M5) and rewritten
    here rather than imported, because importing that module would drag in
    `pipeline.plan_stage`, which writes its report into cold-start-a0's own
    artifacts directory.  The algorithm is unchanged and the credit is A0's.

    Every global law `zero_space` returns is a subset of arena cells whose
    Cart-occupancy parity is conserved.  The one that means something is the one
    whose support is the set of cells the Cart is ever seen on -- read as
    "exactly one of these cells holds the Cart, always", i.e. the Cart never
    leaves that region.  Choosing that representative out of the whole coset is
    the semantic act, and it is the only step here a machine does not do.
    """
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
    detail = {
        "rendering": best.rendering(),
        "value": best.value,
        "region": [list(c) for c in region],
        "region_size": len(region),
        "space_dimension": result.dimension,
        "difference_rank": result.difference_rank,
        "in_recovered_space": result.contains(best.vector),
        "arena": len(cells),
    }
    return region, detail


def pddl_addressable(ast, prob):
    """The derived arena, plus every cell some guard names by colour.

    **A defect in the reused PDDL backend, surfaced by A2 and worked around
    here rather than fixed upstream** (`cold-start-a0/` is another track's
    territory; reported in DECISIONS D-A2-006 and on PARTNER_SYNC).

    `gen_pddl_a0._problem` emits a cell object, and its adjacency facts, only
    for cells in `problem.arena` — and `problem.derive` builds the arena out of
    floor and dynamic cells, so a *static, coloured* cell like the Portal entry
    is not in it.  The `teleport-down` action's precondition is
    `(adj-down ?from ?p)` with `?p - markedcell`, so with no `c7-4` object the
    action never grounds and the planner reports UNSAT on a manual that has the
    teleport rule in it.

    A0 could not see this: its goal was reachable through the Door, so nothing
    in A0 ever needed the jump action to ground.  A2's goal is reachable *only*
    through the teleport, which turns the latent bug into a wrong answer.

    The fix is narrow and PDDL-only.  These cells are addressable, not
    occupiable — `_problem` already withholds `(passable ...)` from every
    markedcell, so the move actions still cannot step onto one.  The Lean and
    Python forms are left on the unaugmented arena on purpose: their arena is
    "states the Cart can be in", and the Cart is never on the Portal.
    """
    special, _colours = _classify(ast, prob)
    marked = {cell for cell, kind in special.items() if kind == "markedcell"}
    arena = sorted(set(tuple(c) for c in prob.arena) | marked)
    from dataclasses import replace as _replace
    return _replace(prob, arena=arena), sorted(marked - set(
        tuple(c) for c in prob.arena))


def compile_manual(dsl_path: str, trace_path: str, problem_name: str,
                   out_dir: str,
                   region: Optional[Sequence[Cell]] = None,
                   comment: str = "",
                   goal_cell: Optional[Cell] = None,
                   unsolvable: bool = False) -> Dict[str, object]:
    """One manual -> theory.{py,md,pddl,lean} + problem.{pddl,json}.

    A2's own driver rather than A0's `compile_theory`, for two reasons: the PDDL
    form needs the addressability patch above, and the Lean form needs its
    invariant and its goal chosen per target.  Every generator called here is
    A0's, unmodified.
    """
    text = open(dsl_path, encoding="utf-8").read()
    ast = parse_theory(text)
    semantics = parse_semantics(text)          # raises if the manual does not say
    prob = problem_mod.derive(trace_path, problem_name)
    pddl_prob, added = pddl_addressable(ast, prob)
    os.makedirs(out_dir, exist_ok=True)

    written: Dict[str, object] = {"pddl_cells_added": [list(c) for c in added]}
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

    builder = None
    if region is not None:
        builder = weight_invariant(region, [tuple(c) for c in prob.arena], comment)
    lean = generate_lean(
        ast, prob, os.path.join(out_dir, "theory.py"),
        invariant_builder=builder,
        goal_cell=goal_cell,
        unsolvable=unsolvable,
        semantics=semantics,
    )
    written["theory.lean"] = _write(os.path.join(out_dir, "theory.lean"), lean)
    return written


def compile_control(dsl: str = None, trace: str = None,
                    out: str = None) -> Dict[str, object]:
    """The complete manual.  Default invariant (`door_latch`), no unsolvability."""
    return compile_manual(
        dsl or os.path.join(THEORY, "theory.dsl"),
        trace or os.path.join(ARTIFACTS, "raw_trace.jsonl"),
        "a2-base",
        out or os.path.join(THEORY, "generated"),
    )


def main() -> int:
    os.environ.setdefault("THEORIA_DETERMINISTIC_IDS", "1")
    os.environ.setdefault("THEORIA_FIXED_TIME", "2026-07-28T00:00:00Z")
    written = compile_control()
    for name in sorted(written):
        value = written[name]
        print("%-18s %s" % (name, "%6d bytes" % value
                            if isinstance(value, int) else value))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
