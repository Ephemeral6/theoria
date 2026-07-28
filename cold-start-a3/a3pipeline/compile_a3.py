"""M4 — one manual, one problem instance, four co-derived forms.

Every generator called here belongs to `cold-start-a0` and is imported
unmodified: the frozen parser, `gen_python_a0`, `gen_pddl_a0`, `gen_lean_a0`,
`compile_a0.render_markdown`, and the `semantics:` dialect reader.  **A3 writes
no generator.**  That is not thrift; it is the only way the result says anything
about the instrument.  A compiler written for A3's exhibit would prove that A3
can write a compiler.

What A3 does write is three workarounds, because reusing the backends honestly
means meeting their defects honestly.  All three are worked around **in this
tree** — `cold-start-a0/` belongs to the theory-compiler track and A3 does not
edit it — and each is numbered, explained, and costed:

| id | defect | where the workaround lives | what it costs |
|---|---|---|---|
| D-A3-004 | a domain with no `goal:` compiles to three forms that cannot win | `bind_goal` | the AST the backends see is not the AST on disk |
| D-A3-005 | PDDL honours one global `portal-exit` and the literal name `portal_exit` | `patch_pddl_landmarks` | a post-hoc text rewrite of a generated artefact |
| D-A3-006 | marked cells are addressable but absent from the arena | `pddl_addressable` | the PDDL form runs on a different arena from the other three |

Plus one trap that is not a defect but is just as fatal if unnoticed:
`generate_lean` falls back to a **vacuous** `I := true` when it cannot find a
latch it recognises (reference trap T4), and a vacuous certificate is fully
green.  `switch_latch_invariant` is the real one, and
`theory/generated_l1_vacuous/` is the fallback compiled on purpose and kept, so
the report can put a green-and-empty certificate next to a green-and-meaningful
one and let a reader see that `#print axioms` alone does not distinguish them.
"""

import json
import os
import re
import sys
from dataclasses import replace as _dc_replace
from typing import Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from theory_compiler.parser.ast_nodes import (  # noqa: E402
    Comparison, FieldAccess, FuncCall, GoalExpr, GoalSection, GuardPredicate,
    NameRef, NumberLit, TheoryAST, TupleLit,
)
from theory_compiler.parser.theory_parser import parse_theory  # noqa: E402

from compile.compile_a0 import _write, render_markdown  # noqa: E402  (a0, read-only)
from compile.dialect import parse_semantics  # noqa: E402
from compile.gen_lean_a0 import generate_lean  # noqa: E402
from compile.gen_pddl_a0 import _classify, generate_pddl  # noqa: E402
from compile.gen_python_a0 import generate_python  # noqa: E402
from compile.problem import Problem  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

Cell = Tuple[int, int]


# ============================================================== D-A3-004
def bind_goal(ast: TheoryAST, problem: Problem) -> TheoryAST:
    """Bind the problem's goal cell into the AST, as a synthesized `goal:`.

    **D-A3-004 — the goal leak: three of the four backends cannot honour the
    domain/problem split the contract mandates.**

    `theory/domain.dsl` has no `goal:` section, deliberately: a goal cell is
    level data, PDDL puts it in the problem file, and `CONTRACTS/
    dsl_grammar_v0.2.md` says landmarks and layout are the problem.  Exactly one
    backend agrees.  `gen_pddl_a0._goal_cell` falls back to
    `problem.goal_cell` when `ast.goal is None` (`gen_pddl_a0.py:292-293`) —
    correct.  The other two do not:

    * `gen_python_a0._goal_code` returns the literal string
      `"    return False"` when `ast.goal is None` (`gen_python_a0.py:118-120`).
      No warning.  The generated `theory.py` compiles, runs, replays — and can
      never win.  Against a trace that does win, the cheap layer reports it as
      a pile of `goal_mismatch` anomalies, i.e. as evidence that the *manual* is
      wrong about the world, which it is not.
    * `gen_lean_a0._goal_cell` (`gen_lean_a0.py:352-358`) then scans that module
      for an arena cell where `is_goal` holds, finds none, and raises
      `ValueError("no arena cell satisfies the manual's goal")`.  The Lean form
      is not produced at all.

    So the coordinate-free domain is not compilable by three of four backends,
    and the failure mode of the worst of them is silence.  That is a finding
    about the backends, recorded as one, and not a reason to put a coordinate in
    the manual.

    **The fix.** A pure function from `(domain AST, Problem)` to a new AST
    carrying `goal Cart.pos = (r, c)`, built out of the parser's own node
    classes.  Three properties are load-bearing:

    * it is **pure** — `dataclasses.replace` on the AST, so the caller's AST is
      untouched and two instances of the same domain cannot contaminate each
      other;
    * it does **no string surgery on the .dsl** — the on-disk domain stays
      coordinate-free and byte-identical across levels, which is the thing
      `tests/test_transfer.py` measures;
    * the node shape is exactly what the parser produces for
      `goal Cart.pos = (2, 7)`, so the backends cannot tell a bound goal from a
      parsed one.  If they could, this would be testing a different manual.

    **What it costs.**  The AST the backends see is not the AST on disk.  Anyone
    reading `theory/generated_*/theory.py` will find a goal that is in no `.dsl`
    file, and the only place that is explained is here and in the compile
    report's `goal_bound` field.  The alternative — a `goal:` section per level —
    costs the domain its level-independence, which is the entire claim.

    Raises rather than guessing if the problem has no goal cell: a manual that
    cannot win is a real thing (A2 compiles one on purpose) but it has to be
    asked for, not arrived at.
    """
    if ast.goal is not None:
        # The domain already states a goal.  Leave it: overriding a manual's own
        # clause with an instance value would be the compiler adjudicating, and
        # engines propose while the LLM adjudicates.
        return ast
    if problem.goal_cell is None:
        raise ValueError(
            "cannot bind a goal: %s has no goal_cell, and the domain declares "
            "none either" % problem.name)
    r, c = (int(v) for v in problem.goal_cell)
    section = GoalSection(goal=GoalExpr(expr=Comparison(
        op="=",
        left=FieldAccess(obj="Cart", field_name="pos"),
        right=TupleLit(elements=[NumberLit(value=r), NumberLit(value=c)]),
    )))
    return _dc_replace(ast, goal=section)


# ============================================================== D-A3-006
def pddl_addressable(ast: TheoryAST, prob: Problem) -> Tuple[Problem, List[Cell]]:
    """The derived arena, plus every cell some guard names by colour.

    **D-A3-006 — marked cells are addressable but not occupiable.**  This is
    A2's D-A2-006, re-derived here rather than imported: `cold-start-a2` is a
    sibling experiment and is deliberately off A3's `sys.path`
    (`_bootstrap.py`).  The diagnosis is A2's, quoted rather than paraphrased
    (`cold-start-a2/a2pipeline/compile_a2.py:121-151`):

        `gen_pddl_a0._problem` emits a cell object, and its adjacency facts,
        only for cells in `problem.arena` — and `problem.derive` builds the
        arena out of floor and dynamic cells, so a *static, coloured* cell like
        the Portal entry is not in it.  The `teleport-down` action's
        precondition is `(adj-down ?from ?p)` with `?p - markedcell`, so with no
        `c7-4` object the action never grounds and the planner reports UNSAT on
        a manual that has the teleport rule in it.

    A3 hits it twice as hard: both of A3's portals are static coloured cells, on
    both levels, and on level 2 the *only* winning path goes through one.

    The fix is narrow and PDDL-only.  These cells are addressable, not
    occupiable — `_problem` already withholds `(passable ...)` from every
    markedcell, so no move action can step onto one.  Python and Lean keep the
    unaugmented arena on purpose: their arena means "cells the Cart can be in",
    and the Cart is never on a portal.

    **What it costs.**  The four co-derived forms are no longer derived from
    one arena.  `theory.lean` enumerates 33 cells on level 1 and the PDDL
    enumerates 35, and nothing in either file says why.  The compile report's
    `pddl_cells_added` is the only trace of it.
    """
    special, _colours = _classify(ast, prob)
    marked = {cell for cell, kind in special.items() if kind == "markedcell"}
    existing = {tuple(c) for c in prob.arena}
    arena = sorted(existing | marked)
    return _dc_replace(prob, arena=arena), sorted(marked - existing)


# ============================================================== D-A3-005
def jump_bindings(ast: TheoryAST) -> Dict[str, Dict[str, object]]:
    """action name -> `{"landmark": str, "entry_colour": int}`, read off the AST.

    Derived from the rules themselves — each jump rule's `jumped(Cart, <name>)`
    effect for the destination, and its `colored(<spatial>, k)` guard for the
    entry — and never from the rule's *name*.  `teleport_a_up` is called that
    because a human named it that; the AST is what the four forms are compiled
    from and it is the only thing entitled to a vote.
    """
    out: Dict[str, Dict[str, object]] = {}
    for rule in ast.rules.rules:
        event = rule.event
        if not isinstance(event, FuncCall) or event.name != "jumped":
            continue
        if len(event.args) != 2 or not isinstance(event.args[1], NameRef):
            raise ValueError("rule %s: jumped(o, <landmark>) expected, got %r"
                             % (rule.name, event))
        landmark = event.args[1].name

        colours = [
            clause.expr.args[1].value
            for clause in rule.guard.clauses
            if isinstance(clause, GuardPredicate)
            and isinstance(clause.expr, FuncCall)
            and clause.expr.name == "colored"
            and len(clause.expr.args) == 2
            and isinstance(clause.expr.args[1], NumberLit)
        ]
        if len(colours) != 1:
            raise ValueError(
                "rule %s: a jump rule must name exactly one entry colour in its "
                "guard; found %r" % (rule.name, colours))
        out[rule.name.replace("_", "-")] = {
            "landmark": landmark,
            "entry_colour": int(colours[0]),
        }

    # One landmark reached through two different colours would mean the two
    # portals are not distinguishable by the guard the encoding is about to
    # trust.  Better a loud stop than a plan built on it.
    by_landmark: Dict[str, set] = {}
    for binding in out.values():
        by_landmark.setdefault(str(binding["landmark"]), set()).add(
            binding["entry_colour"])
    for landmark, colours_seen in sorted(by_landmark.items()):
        if len(colours_seen) != 1:
            raise ValueError(
                "landmark %s is reached from cells of %d different colours %r; "
                "the PDDL encoding cannot separate them"
                % (landmark, len(colours_seen), sorted(colours_seen)))
    return out


def _cell_name(cell: Cell) -> str:
    """`gen_pddl_a0._cell_name`, restated so the rewrite cannot drift from it."""
    return "c%d-%d" % (cell[0], cell[1])


def _predicate(prefix: str, landmark: str) -> str:
    """`exit_a` -> `exit-exit-a`.

    Redundant-looking, and kept that way.  The prefix says what kind of fact it
    is and the suffix is the landmark's own name from the manual; collapsing
    them would make `exit-a` look like a name the domain chose rather than one
    it inherited.  Underscores become hyphens for house style — the bundled
    PDDL reader tokenises on whitespace and parens and would accept either.
    """
    return "%s-%s" % (prefix, landmark.replace("_", "-"))


def patch_pddl_landmarks(domain: str, instance: str, ast: TheoryAST,
                         prob: Problem) -> Tuple[str, str, Dict[str, object]]:
    """Give every landmark its own PDDL predicate, on both ends of the jump.

    **D-A3-005 — two landmarks, one predicate, no facts.**  `gen_pddl_a0` was
    written for a world with a single portal and it says so in two places:

    * `_action_jump` (`gen_pddl_a0.py:167-175`) hard-codes the precondition
      `(portal-exit ?dest)` — one global predicate for every jump rule in the
      manual, whatever landmark the rule's effect actually names;
    * `_problem` (`:273-275`) emits a `(portal-exit ...)` fact only for a
      landmark **literally named `portal_exit`**, and silently drops every other
      name.

    With `exit_a` and `exit_b` this is wrong twice over.  No init fact is
    emitted at all, so `(portal-exit ?dest)` is unsatisfiable, every jump action
    grounds to nothing, and `fd_adapter.solve` reports a confident UNSAT for a
    manual that is correct — trap T2, and on A3's level 2 the goal is reachable
    *only* through a jump, so the confident-wrong answer is the answer.  And
    even with the facts emitted, one shared predicate would let
    `teleport-a-left` deliver the Cart to `exit_b`: the planner would return a
    plan the manual does not agree with.

    **The fix**, PDDL-only and post-hoc, in three parts.  Parts 1 and 2 are the
    destination; part 3 is the entry, and it is A3's addition to the brief
    rather than a restatement of it:

    1. each jump action's `(portal-exit ?dest)` becomes `(exit-<landmark> ?dest)`
       for the landmark **that rule's own effect names**;
    2. `(exit-<landmark> c<r>-<c>)` init facts, one per landmark, from
       `problem.landmarks`;
    3. each jump action additionally requires `(entry-<landmark> ?p)` of its
       source marked cell, with init facts for every board cell carrying that
       rule's guard colour.  Without this the source stays typed only as
       `markedcell` and `teleport-a-up` can ground on portal **B**, which is
       unsound.  On A3's level 1 no *shortest* plan happens to exploit it, which
       is precisely why it has to be closed rather than observed.

    Both mappings come from `jump_bindings`, i.e. from the AST, never from the
    rule's name.

    Every substitution is counted and a miscount **raises**.  A silent no-op
    here does not fail; it produces a plan, and a wrong plan that type-checks is
    the single most expensive thing this module could emit.

    **What it costs.**  A generated artefact is rewritten by regular expression
    after the generator has finished with it.  The rewrite is coupled to
    `gen_pddl_a0`'s exact output text — the parameter list `?p - markedcell`,
    the precondition spelling `(portal-exit ?dest)`, the predicate declaration
    line — and upstream is another track's tree, free to change any of them.
    The asserts are what turns that coupling from a silent hazard into a build
    failure, and they are the reason this is a workaround and not a fix.
    """
    bindings = jump_bindings(ast)
    if not bindings:
        return domain, instance, {"jump_actions": 0, "note": "no jump rules"}

    landmarks = sorted({str(b["landmark"]) for b in bindings.values()})
    missing = [lm for lm in landmarks if lm not in prob.landmarks]
    if missing:
        raise ValueError(
            "the manual jumps to %r but the problem instance locates none of "
            "them; `LANDMARKS[...]` would KeyError at the first step (trap T1)"
            % missing)

    entry_colour_of = {str(b["landmark"]): int(b["entry_colour"])
                       for b in bindings.values()}
    entry_cells: Dict[str, List[Cell]] = {}
    for landmark in landmarks:
        colour = entry_colour_of[landmark]
        cells = [(r, c)
                 for r in range(prob.height)
                 for c in range(prob.width)
                 if prob.board[r][c] == colour]
        if not cells:
            raise ValueError(
                "no board cell carries colour %d, so nothing can enter the "
                "portal that leads to %s" % (colour, landmark))
        entry_cells[landmark] = sorted(cells)

    # ---------------------------------------------------------------- domain
    declaration = "    (portal-exit ?c - cell)\n"
    if domain.count(declaration) != 1:
        raise AssertionError(
            "expected exactly one `(portal-exit ?c - cell)` declaration in the "
            "generated domain, found %d — gen_pddl_a0's output has changed and "
            "this rewrite is no longer safe" % domain.count(declaration))
    replacement = "".join(
        "    (%s ?c - cell)\n    (%s ?c - cell)\n"
        % (_predicate("exit", lm), _predicate("entry", lm))
        for lm in landmarks
    )
    domain = domain.replace(declaration, replacement)

    # `  (:action ` starts every action block and appears nowhere else in the
    # generated text; splitting on it is exact rather than approximate.
    marker = "  (:action "
    head, _, rest = domain.partition(marker)
    blocks = [marker + part for part in rest.split(marker)] if rest else []
    patched_blocks: List[str] = []
    for block in blocks:
        action = block[len(marker):].split()[0].strip()
        binding = bindings.get(action)
        if binding is None:
            patched_blocks.append(block)
            continue
        landmark = str(binding["landmark"])

        old_dest = "(portal-exit ?dest)"
        if block.count(old_dest) != 1:
            raise AssertionError(
                "action %s: expected exactly one %s, found %d"
                % (action, old_dest, block.count(old_dest)))
        block = block.replace(old_dest,
                              "(%s ?dest)" % _predicate("exit", landmark))

        entry = re.findall(r"\(adj-(?:up|down|left|right) \?from \?p\)", block)
        if len(entry) != 1:
            raise AssertionError(
                "action %s: expected exactly one `(adj-<dir> ?from ?p)`, found "
                "%d" % (action, len(entry)))
        block = block.replace(
            entry[0],
            "%s (%s ?p)" % (entry[0], _predicate("entry", landmark)))
        patched_blocks.append(block)
    domain = head + "".join(patched_blocks)

    if "portal-exit" in domain:
        raise AssertionError(
            "`portal-exit` survives in the patched domain; the rewrite is "
            "incomplete and the planner would see a predicate with no facts")

    # -------------------------------------------------------------- instance
    if "(portal-exit" in instance:
        raise AssertionError(
            "the generated problem already emits a `(portal-exit ...)` fact; "
            "gen_pddl_a0 only does that for a landmark named `portal_exit`, so "
            "this manual is not the one this rewrite was written for")

    facts: List[str] = []
    for landmark in landmarks:
        facts.append("    (%s %s)" % (_predicate("exit", landmark),
                                      _cell_name(tuple(prob.landmarks[landmark]))))
    for landmark in landmarks:
        for cell in entry_cells[landmark]:
            facts.append("    (%s %s)" % (_predicate("entry", landmark),
                                          _cell_name(cell)))

    lines = instance.splitlines()
    try:
        init_at = lines.index("  (:init")
    except ValueError:                       # pragma: no cover - shape changed
        raise AssertionError("no `  (:init` line in the generated problem")
    close_at = next(i for i in range(init_at + 1, len(lines))
                    if lines[i] == "  )")
    lines[close_at:close_at] = facts
    instance = "\n".join(lines) + "\n"

    # Every cell a new fact mentions must be a declared object, or the fact is
    # about nothing.  Cheap to check, and it is exactly what D-A3-006 exists to
    # guarantee, so checking it here closes the loop between the two.
    for fact in facts:
        cell_token = fact.rstrip(")").split()[-1]
        if re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(cell_token),
                     instance.split("(:init")[0]) is None:
            raise AssertionError(
                "%s names %s, which is not declared in (:objects) — the arena "
                "patch (D-A3-006) did not reach it" % (fact.strip(), cell_token))

    report = {
        "jump_actions": len(bindings),
        "landmarks": landmarks,
        "predicates": sorted(
            [_predicate("exit", lm) for lm in landmarks]
            + [_predicate("entry", lm) for lm in landmarks]),
        "entry_colour": {lm: entry_colour_of[lm] for lm in landmarks},
        "entry_cells": {lm: [list(c) for c in entry_cells[lm]]
                        for lm in landmarks},
        "exit_cells": {lm: list(prob.landmarks[lm]) for lm in landmarks},
        "facts_added": len(facts),
    }
    return domain, instance, report


# ================================================================ trap T4
def switch_latch_invariant(axes: Sequence[object]) -> Optional[Tuple[str, str]]:
    """`switch_door_latch` — exactly one of "the Switch shows 8" and "the Door
    exists" holds, in every reachable state.

    **Why A3 cannot use the default.**  `generate_lean(..., invariant_builder=
    None)` calls `gen_lean_a0.door_latch_invariant`, which looks for an axis
    named literally `Button_colour` (`gen_lean_a0.py:174`).  A3's object is a
    `Switch`, so the lookup returns `None`, and `generate_lean` falls through
    to `("true", "this instance has no latch; the invariant is vacuous")`.  The
    result is a Lean file whose `I` is `true`, whose `inv_init`, `inv_closed`
    and `inv_all` all pass by `decide`, and whose `#print axioms inv_all` comes
    back **empty**.  Fully green.  Proves nothing.  That is reference trap T4,
    and it is the most dangerous thing in the reused stack, because the
    acceptance criterion the whole repo uses — an empty axiom list — cannot
    tell it apart from a real certificate.

    So A3 compiles it too, once, into `theory/generated_l1_vacuous/`, and keeps
    it.  `A3_REPORT` puts the two `theory.lean` files side by side.  A claim
    that a certificate means something is worth exactly as much as the reader's
    ability to see the version that does not.

    **The law itself** is the manual's `switch_door_latch`
    (`theory/domain.dsl`, `laws:`), which `zero_space` proposed as
    `count(Switch, 8) + count(Door) = 1`.  Rendered in Lean as an XOR over the
    two axes, exactly as `door_latch_invariant` does — same return contract,
    same `!=`-on-`Bool` idiom, so the two are diffable.

    Returns `None` if the axes do not carry both components, which is what the
    caller must handle: A3's drivers pass the builder explicitly and a `None`
    here would silently reinstate the vacuous fallback.  `generate_lean` does
    **not** guard against a builder returning `None` — it unpacks `built[0]`
    and would raise `TypeError` — so a `None` from here is loud, and that is on
    purpose.
    """
    switch = next((a for a in axes if getattr(a, "field", None)
                   == "Switch_colour"), None)
    door = next((a for a in axes if getattr(a, "field", None)
                 == "Door_present"), None)
    if switch is None or door is None or 8 not in switch.values:
        return None
    return (
        "(s.%s == %s) != (s.%s == %s)"
        % (switch.accessor, switch.ctor(8), door.accessor, door.ctor(True)),
        "switch_door_latch (THEORIZE_LOG L-02, zero_space): exactly one of\n"
        "'the Switch shows 8' and 'the Door exists' holds, in every reachable\n"
        "state.  A0's Button was a latch and could only witness one polarity;\n"
        "A3's Switch toggles, so both directions of this law have witnesses in\n"
        "the level-1 sweep and neither half is an analogy from the other.\n"
        "cart_unique (L-01) is NOT proved here: representing the state as the\n"
        "Cart's cell already assumes there is exactly one Cart, so a Lean proof\n"
        "would be discharged by the representation.  It is checked where it can\n"
        "actually fail — per frame, by the cheap layer's responsibility pass.",
    )


# ==================================================================== driver
def compile_instance(dsl_path: str, problem: Problem, out_dir: str,
                     invariant_builder=None,
                     unsolvable: bool = False) -> Dict[str, object]:
    """One domain + one problem instance -> theory.{py,md,lean} + {domain,problem}.pddl + problem.json.

    A3's own driver rather than A0's `compile_theory`, for four reasons, three
    of which are the defects above and the fourth of which is the point of the
    whole spike: **A0's driver takes a trace and derives the problem itself**
    (`compile_a0.py:41-46`).  A3 must be able to hand it a problem that came
    from one frame, so the problem is a parameter, not a derivation.

    Note also that A0's driver swallows `ArenaEscape` into a report field
    (`compile_a0.py:64-70`, trap T14): no `theory.lean` is written and the
    caller learns about it only by inspecting the returned dict.  Here it
    propagates.  A manual whose `step` leaves its own declared state space is
    not a missing artefact, it is a failed compile.
    """
    text = open(dsl_path, encoding="utf-8").read()
    ast = parse_theory(text)
    semantics = parse_semantics(text)     # raises if the manual does not declare
    bound = bind_goal(ast, problem)       # D-A3-004

    os.makedirs(out_dir, exist_ok=True)
    written: Dict[str, object] = {
        "dsl": os.path.relpath(dsl_path, ROOT).replace(os.sep, "/"),
        "problem": problem.name,
        "goal_bound": (list(problem.goal_cell) if ast.goal is None
                       else "the manual states its own goal"),
    }

    # --- the executable form: the only predictor in the system ---------------
    theory_py = os.path.join(out_dir, "theory.py")
    written["theory.py"] = _write(theory_py,
                                  generate_python(bound, problem, semantics))

    # --- the human form -----------------------------------------------------
    # Rendered from the *bound* AST, not the on-disk one.  Everything under
    # `theory/generated_*/` is a compiled instance — `theory.py` has this
    # level's board in it — so a `theory.md` that omitted the goal would be the
    # only one of the four forms describing a different object.
    written["theory.md"] = _write(os.path.join(out_dir, "theory.md"),
                                  render_markdown(bound, semantics))

    # --- the planning form --------------------------------------------------
    pddl_prob, added = pddl_addressable(bound, problem)          # D-A3-006
    domain, instance = generate_pddl(bound, pddl_prob)
    domain, instance, landmark_report = patch_pddl_landmarks(   # D-A3-005
        domain, instance, bound, pddl_prob)
    written["pddl_cells_added"] = [list(c) for c in added]
    written["pddl_landmarks"] = landmark_report
    written["domain.pddl"] = _write(os.path.join(out_dir, "domain.pddl"), domain)
    written["problem.pddl"] = _write(os.path.join(out_dir, "problem.pddl"),
                                     instance)

    # The problem.json records the *unaugmented* problem — what was derived,
    # not what the PDDL backend had to be told.  `pddl_cells_added` above is
    # the delta, and keeping the two apart is what makes D-A3-006 auditable.
    written["problem.json"] = _write(
        os.path.join(out_dir, "problem.json"),
        json.dumps(problem.as_json(), indent=2, sort_keys=True) + "\n")

    # --- the proof form -----------------------------------------------------
    # `goal_cell` is passed explicitly even though `_goal_cell` could recover it
    # by scanning the module: the scan returns the *first* arena cell where
    # `is_goal` holds, which is only unambiguous because our goal is a single
    # cell.  Passing it keeps the Lean file's `Goal` and the PDDL file's
    # `(:goal ...)` provably the same coordinate.
    lean = generate_lean(
        bound, problem, theory_py,
        invariant_builder=invariant_builder,
        goal_cell=tuple(problem.goal_cell) if problem.goal_cell else None,
        unsolvable=unsolvable,
        semantics=semantics,
    )
    written["theory.lean"] = _write(os.path.join(out_dir, "theory.lean"), lean)
    written["lean_invariant"] = ("supplied builder" if invariant_builder
                                 else "A0 default (vacuous unless a Button "
                                      "latch is found — trap T4)")
    return written


def write_report(path: str, payload: Dict[str, object]) -> str:
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return path
