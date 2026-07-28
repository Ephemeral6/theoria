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


def _addressable(problem: Problem, special) -> List[Tuple[int, int]]:
    """The PDDL cell universe: the arena, plus every cell the domain **names**.

    `problem.arena` is floor plus the cells the board cannot explain, i.e. the
    cells the Cart can *be in*. That is the right universe for Lean and for
    Python, whose `arena` means exactly that. It is the wrong one for PDDL,
    because a PDDL action can take a parameter typed by a cell the Cart never
    occupies — `teleport-down`'s `?p - markedcell` is the Portal, a *static*
    coloured cell, which is in neither the floor nor the dynamic set and so
    reached the `:objects` block from neither side. With no instance of its
    type the action grounds to nothing and the planner answers UNSAT on a manual
    that contains the teleport rule. Silently: an empty grounding is not an
    error anywhere in the chain.

    Reported by `cold-start-a2` (D-A2-006), which hit it on the first compile of
    its control manual. A0 could not see it: A0's goal is reachable through the
    Door, so no A0 plan ever needed the jump action to ground, and the defect
    returned a correct answer by luck.

    These cells are **addressable, not occupiable** — `_problem` withholds
    `(passable ...)` from them, so a move action still cannot step onto one.
    """
    return sorted(set(tuple(c) for c in problem.arena) | set(special))


def generate_pddl(ast: TheoryAST, problem: Problem) -> Tuple[str, str]:
    special, _colours = _classify(ast, problem)
    cells = _addressable(problem, special)
    cart = next(o for o in problem.objects if o.name == "Cart")

    door = next((o for o in problem.objects if o.name == "Door"), None)
    switch = next((o for o in problem.objects
                   if o.name in ("Button", "Switch")), None)
    portal_cells = [c for c, t in special.items() if t == "markedcell"]

    subtypes = sorted({t for t in special.values()})
    domain = _domain(ast, subtypes, door, switch, portal_cells)
    instance = _problem(ast, problem, cells, special, cart, door, switch)
    return domain, instance


def _domain(ast: TheoryAST, subtypes, door, switch, portal_cells) -> str:
    switch_type = "%scell" % switch.name.lower() if switch is not None else "cell"
    L: List[str] = []
    L.append("; Auto-generated from theory.dsl by compile/gen_pddl_a0.py — DO NOT EDIT.")
    L.append("(define (domain a0)")
    L.append("  (:requirements :strips :typing :negative-preconditions)")
    # `cell` itself must be declared, not just used as a supertype.  The bundled
    # BFS parser is lenient about this and accepted `(:types doorcell - cell)`
    # with `cell` never introduced; the real Fast Downward translator does not,
    # and dies with `KeyError: 'cell'` while building its type dictionary.  The
    # stub was masking a portability bug in this generator — see D-A0-019.
    if subtypes:
        L.append("  (:types cell - object")
        L.append("          %s - cell)" % " ".join(subtypes))
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
    L.append("    (switched)                    ; the Switch/Button state")
    L.append("  )")
    L.append("")

    # A rule that only ever fires together with another (same guard, same
    # transition) is a *cascade*, not an action of its own.  The manual says so
    # by giving them identical guards, so the encoding reads it off rather than
    # being told: the recolour becomes the action and the Door event is folded
    # into its effect.
    cascade_of = _cascades(ast)
    for rule in ast.rules.rules:
        kind = _rule_kind(rule)
        direction = _direction_of(rule)
        if kind == "moved":
            L.append(_action_move(rule.name, direction))
        elif kind == "jumped":
            L.append(_action_jump(rule.name, direction))
        elif kind == "recolored":
            L.append(_action_toggle(rule.name, direction,
                                    cascade_of.get(rule.name), door, switch_type))
        elif kind in ("vanished", "appeared"):
            L.append(";; %s is a cascade of the toggle action with the same "
                     "guard — its effect is folded in there" % rule.name)
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


def _guard_key(rule: RuleDecl):
    """A guard as comparable text, so identical guards are recognisably identical."""
    parts = []
    for clause in rule.guard.clauses:
        if isinstance(clause, GuardAction):
            parts.append("act=%s(%s)" % (
                clause.action.action_name,
                ",".join(getattr(a, "name", str(a)) for a in clause.action.args)))
        elif isinstance(clause, GuardPredicate) and isinstance(clause.expr, FuncCall):
            expr = clause.expr
            parts.append("%s(%s)" % (expr.name, ",".join(
                str(getattr(a, "name", None) or getattr(a, "value", a))
                for a in expr.args)))
    return tuple(sorted(parts))


def _cascades(ast: TheoryAST) -> Dict[str, str]:
    """rule name -> the Door event ('vanished'/'appeared') sharing its guard.

    Two rules with the *same guard* fire on the same transitions: the manual
    itself says they are one event with two consequences (D-A0-004's cascade).
    The encoding reads that off rather than being told, which is why it works
    unchanged for A0's one-way Button and A0′'s two-way Switch.
    """
    by_guard: Dict[tuple, List[RuleDecl]] = {}
    for rule in ast.rules.rules:
        by_guard.setdefault(_guard_key(rule), []).append(rule)
    out: Dict[str, str] = {}
    for rules in by_guard.values():
        kinds = {_rule_kind(r): r for r in rules}
        if "recolored" not in kinds:
            continue
        for door_event in ("vanished", "appeared"):
            if door_event in kinds:
                out[kinds["recolored"].name] = door_event
    return out


def _action_toggle(name: str, direction: str, door_event, door,
                   switch_type: str) -> str:
    """A switch action, with the Door event that shares its guard folded in.

    Which polarity a rule sets is read off the **Door event**, not off the colour
    literal: `vanished` means the Door goes and its cell becomes passable,
    `appeared` means it comes back.  So the encoding never has to be told that
    colour 8 means "on", and A0's one-way Button and A0′'s two-way Switch compile
    through the same function.
    """
    opens = door_event == "vanished"
    has_door = door is not None and door_event is not None
    lines = [
        "  (:action %s" % name.replace("_", "-"),
        "    :parameters (?from - cell ?s - %s%s)"
        % (switch_type, " ?d - doorcell" if has_door else ""),
        "    :precondition (and (at ?from) (adj-%s ?from ?s) %s)"
        % (direction, "(not (switched))" if opens else "(switched)"),
    ]
    effect = ["(switched)"] if opens else ["(not (switched))"]
    if has_door:
        effect.append("(passable ?d)" if opens else "(not (passable ?d))")
    lines.append("    :effect (and %s)" % " ".join(effect))
    lines.append("  )")
    lines.append("")
    return "\n".join(lines)


def _problem(ast: TheoryAST, problem: Problem, cells, special, cart,
             door, switch) -> str:
    """`cells` is `_addressable(...)`, not `problem.arena` — see its docstring."""
    L: List[str] = []
    L.append("; Auto-generated from theory.dsl + the derived problem instance.")
    L.append("(define (problem %s)" % problem.name)
    L.append("  (:domain a0)")
    L.append("")
    L.append("  (:objects")
    by_type: Dict[str, List[str]] = {}
    for cell in cells:
        by_type.setdefault(special.get(cell, "cell"), []).append(_cell_name(cell))
    for type_name in sorted(by_type):
        L.append("    %s - %s" % (" ".join(sorted(by_type[type_name])), type_name))
    L.append("  )")
    L.append("")
    L.append("  (:init")
    cell_set = set(cells)
    for cell in cells:
        for direction, (dr, dc) in sorted(DELTA.items()):
            other = (cell[0] + dr, cell[1] + dc)
            if other in cell_set:
                L.append("    (adj-%s %s %s)" % (direction, _cell_name(cell),
                                                 _cell_name(other)))
    L.append("    (at %s)" % _cell_name(tuple(cart.pos)))
    blocked = {tuple(o.pos) for o in problem.objects if o.name != "Cart"}
    blocked |= {c for c, t in special.items() if t == "markedcell"}
    for cell in cells:
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
