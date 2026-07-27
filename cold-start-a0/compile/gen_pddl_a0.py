"""theory.pddl generator for A0 — domain + problem, in `fd_adapter`'s subset.

The subset `engine-rig/fd_adapter` accepts is `:strips :typing
:negative-preconditions` with conjunctive preconditions and effects.  Anything
else raises there rather than being mis-parsed, so this generator stays inside
it deliberately.

Two things shape the encoding:

* **Actions are parameterised to objects, never to raw coordinates** — the
  contract's rule, and the reason cells are PDDL objects rather than numbers.
* **Grounding is not pruned by static preconditions** in that adapter (it takes
  the full type-consistent product), so parameter *types* are the only lever on
  instance size.  Giving the Door, the Button and the Portal entry their own
  subtypes of `cell` keeps every schema at 2–3 parameters over a 38-cell arena
  instead of exploding.

One honest gap is recorded rather than papered over: the manual's `press_left`
rule fires only on a leftward push (THEORIZE_LOG R-05), and the PDDL says so —
`press` requires the Cart to be on the Button's *right*.  A planner that cannot
find a plan under that restriction is telling the truth about the manual.
"""

from typing import Dict, List, Tuple

from theory_compiler.parser.ast_nodes import (
    FuncCall, GuardAction, GuardPredicate, NameRef, NumberLit, RuleDecl,
    TheoryAST, Comparison, FieldAccess, TupleLit,
)

from compile.problem import Problem

SPATIAL = {"above": "up", "below": "down", "leftof": "left", "rightof": "right"}
DELTA = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}
OPPOSITE = {"up": "down", "down": "up", "left": "right", "right": "left"}


class UnsupportedClause(Exception):
    pass


def _cell_name(cell) -> str:
    return "c%d-%d" % (cell[0], cell[1])


def _classify(ast: TheoryAST, problem: Problem):
    """Which arena cells get their own PDDL subtype, and why.

    A cell is special exactly when some rule's guard tests it by colour: those
    are the cells whose identity the domain needs to name.
    """
    colours = set()
    for rule in ast.rules.rules:
        for clause in rule.guard.clauses:
            if isinstance(clause, GuardPredicate) and isinstance(clause.expr, FuncCall):
                if clause.expr.name == "colored":
                    colours.add(clause.expr.args[1].value)

    # Every non-mover object's cell gets its own subtype, whether or not a guard
    # tests its colour: an action that has to *name* the Door in its effect —
    # `press` opens it — needs a parameter type with exactly one inhabitant, or
    # the grounder produces nothing at all.
    special: Dict[Tuple[int, int], str] = {}
    for obj in problem.objects:
        if obj.name != "Cart":
            special[tuple(obj.pos)] = "%scell" % obj.name.lower()
    for r in range(problem.height):
        for c in range(problem.width):
            if problem.board[r][c] in colours:
                special.setdefault((r, c), "markedcell")
    return special, sorted(colours)


def _rule_kind(rule: RuleDecl) -> str:
    return rule.event.name if isinstance(rule.event, FuncCall) else "?"


def _direction_of(rule: RuleDecl) -> str:
    for clause in rule.guard.clauses:
        if isinstance(clause, GuardAction):
            return clause.action.args[1].name
    raise UnsupportedClause("rule %s has no action clause" % rule.name)


def generate_pddl(ast: TheoryAST, problem: Problem) -> Tuple[str, str]:
    special, _colours = _classify(ast, problem)
    arena = [tuple(c) for c in problem.arena]
    cart = next(o for o in problem.objects if o.name == "Cart")

    door = next((o for o in problem.objects if o.name == "Door"), None)
    button = next((o for o in problem.objects if o.name == "Button"), None)
    portal_cells = [c for c, t in special.items() if t == "markedcell"]

    subtypes = sorted({t for t in special.values()})
    domain = _domain(ast, subtypes, door, button, portal_cells)
    instance = _problem(ast, problem, arena, special, cart, door, button)
    return domain, instance


def _domain(ast: TheoryAST, subtypes, door, button, portal_cells) -> str:
    L: List[str] = []
    L.append("; Auto-generated from theory.dsl by compile/gen_pddl_a0.py — DO NOT EDIT.")
    L.append("(define (domain a0)")
    L.append("  (:requirements :strips :typing :negative-preconditions)")
    if subtypes:
        L.append("  (:types %s - cell)" % " ".join(subtypes))
    else:
        L.append("  (:types cell - object)")
    L.append("")
    L.append("  (:predicates")
    L.append("    (at ?c - cell)                ; where the Cart is")
    L.append("    (passable ?c - cell)          ; the Cart may stand here")
    L.append("    (adj-up ?a - cell ?b - cell)")
    L.append("    (adj-down ?a - cell ?b - cell)")
    L.append("    (adj-left ?a - cell ?b - cell)")
    L.append("    (adj-right ?a - cell ?b - cell)")
    L.append("    (portal-exit ?c - cell)")
    L.append("    (pressed)")
    L.append("  )")
    L.append("")

    for rule in ast.rules.rules:
        kind = _rule_kind(rule)
        direction = _direction_of(rule)
        if kind == "moved":
            L.append(_action_move(rule.name, direction))
        elif kind == "jumped":
            L.append(_action_jump(rule.name, direction))
        elif kind == "recolored":
            L.append(_action_press(rule.name, direction, door, button))
        elif kind == "vanished":
            L.append(";; %s is a cascade of the press action above — its effect "
                     "is folded into it" % rule.name)
            L.append("")
        else:
            raise UnsupportedClause("no PDDL encoding for event %r" % kind)
    L.append(")")
    return "\n".join(L) + "\n"


def _action_move(name: str, direction: str) -> str:
    return "\n".join([
        "  (:action %s" % name.replace("_", "-"),
        "    :parameters (?from - cell ?to - cell)",
        "    :precondition (and (at ?from) (adj-%s ?from ?to) (passable ?to))" % direction,
        "    :effect (and (not (at ?from)) (at ?to))",
        "  )",
        "",
    ])


def _action_jump(name: str, direction: str) -> str:
    return "\n".join([
        "  (:action %s" % name.replace("_", "-"),
        "    :parameters (?from - cell ?p - markedcell ?dest - cell)",
        "    :precondition (and (at ?from) (adj-%s ?from ?p) (portal-exit ?dest))" % direction,
        "    :effect (and (not (at ?from)) (at ?dest))",
        "  )",
        "",
    ])


def _action_press(name: str, direction: str, door, button) -> str:
    """The press, with the Door's opening folded in as its cascade (D-A0-004)."""
    lines = [
        "  (:action %s" % name.replace("_", "-"),
        "    :parameters (?from - cell ?b - buttoncell ?d - doorcell)"
        if door is not None else
        "    :parameters (?from - cell ?b - buttoncell)",
        "    :precondition (and (at ?from) (adj-%s ?from ?b) (not (pressed)))" % direction,
    ]
    effect = ["(pressed)"]
    if door is not None:
        effect.append("(passable ?d)")
    lines.append("    :effect (and %s)" % " ".join(effect))
    lines.append("  )")
    lines.append("")
    return "\n".join(lines)


def _problem(ast: TheoryAST, problem: Problem, arena, special, cart,
             door, button) -> str:
    L: List[str] = []
    L.append("; Auto-generated from theory.dsl + the derived problem instance.")
    L.append("(define (problem %s)" % problem.name)
    L.append("  (:domain a0)")
    L.append("")
    L.append("  (:objects")
    by_type: Dict[str, List[str]] = {}
    for cell in arena:
        by_type.setdefault(special.get(cell, "cell"), []).append(_cell_name(cell))
    for type_name in sorted(by_type):
        L.append("    %s - %s" % (" ".join(sorted(by_type[type_name])), type_name))
    L.append("  )")
    L.append("")
    L.append("  (:init")
    arena_set = set(arena)
    for cell in arena:
        for direction, (dr, dc) in sorted(DELTA.items()):
            other = (cell[0] + dr, cell[1] + dc)
            if other in arena_set:
                L.append("    (adj-%s %s %s)" % (direction, _cell_name(cell),
                                                 _cell_name(other)))
    L.append("    (at %s)" % _cell_name(tuple(cart.pos)))
    blocked = {tuple(o.pos) for o in problem.objects if o.name != "Cart"}
    blocked |= {c for c, t in special.items() if t == "markedcell"}
    for cell in arena:
        if cell not in blocked:
            L.append("    (passable %s)" % _cell_name(cell))
    for name, cell in sorted(problem.landmarks.items()):
        if name == "portal_exit":
            L.append("    (portal-exit %s)" % _cell_name(tuple(cell)))
    L.append("  )")
    L.append("")
    L.append("  (:goal")
    goal_cell = _goal_cell(ast, problem)
    L.append("    (at %s)" % _cell_name(goal_cell))
    L.append("  )")
    L.append(")")
    return "\n".join(L) + "\n"


def _goal_cell(ast: TheoryAST, problem: Problem):
    if ast.goal is not None:
        expr = ast.goal.goal.expr
        if (isinstance(expr, Comparison) and isinstance(expr.left, FieldAccess)
                and isinstance(expr.right, TupleLit)):
            return tuple(e.value for e in expr.right.elements)
    if problem.goal_cell is not None:
        return tuple(problem.goal_cell)
    raise UnsupportedClause("no goal to translate")
