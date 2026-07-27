"""theory.py generator for A0.

Why this exists rather than `theory_compiler.generators.gen_python`: the upstream
generator hard-codes the `moved` and `teleported` events, assumes exactly one
instance per object type and renders only objects that carry both `pos` and
`colour`.  It cannot express a vanish, a recolour, or a rule whose guard mentions
a second object.  See DECISIONS.md D-A0-011 — the parser is reused, the backend
is not.

The generated module is the world's **only** predictor (Theoria 1.10a, "预测无侧
门"): the replay in `certify/replay.py`, the state enumeration the Lean generator
walks, and the plan validator all go through it.

Supported subset, and it raises on anything else rather than guessing:

  guards   `act=push(<Obj>, <dir>)`, `free(<spatial>)`, `colored(<spatial>, k)`
  spatial  `above|below|leftof|rightof(<Obj>)`
  events   `moved(o, dir)`, `jumped(o, <landmark>)`, `recolored(o, k)`,
           `vanished(o)`, `appeared(o)`
"""

from typing import Dict, List

from theory_compiler.parser.ast_nodes import (
    Comparison, FieldAccess, FuncCall, GuardAction, GuardPredicate,
    NameRef, NumberLit, RuleDecl, TheoryAST, TupleLit,
)

from compile.dialect import Semantics, check_backend_support
from compile.problem import Problem

DIRECTIONS = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}
SPATIAL = {"above": "up", "below": "down", "leftof": "left", "rightof": "right"}


class UnsupportedClause(Exception):
    """Outside the subset this backend implements — raised, never guessed at."""


def _obj_fields(ast: TheoryAST) -> Dict[str, List[str]]:
    return {o.name: [f.name for f in o.fields] for o in ast.word_table.objects}


def _spatial(expr) -> str:
    if not isinstance(expr, FuncCall) or expr.name not in SPATIAL:
        raise UnsupportedClause("not a spatial reference: %r" % (expr,))
    if len(expr.args) != 1 or not isinstance(expr.args[0], NameRef):
        raise UnsupportedClause("spatial reference takes one object: %r" % (expr,))
    return "_neighbour(state.%s_pos, '%s')" % (
        expr.args[0].name, SPATIAL[expr.name]
    )


def _guard_code(rule: RuleDecl) -> List[str]:
    """Each clause becomes one early-return test."""
    lines = []
    for clause in rule.guard.clauses:
        if isinstance(clause, GuardAction):
            action = clause.action
            if action.action_name != "push" or len(action.args) != 2:
                raise UnsupportedClause("only push(<Obj>, <dir>) is supported")
            obj, direction = action.args
            if not isinstance(obj, NameRef) or not isinstance(direction, NameRef):
                raise UnsupportedClause("push takes two names")
            if direction.name not in DIRECTIONS:
                raise UnsupportedClause("unknown direction %r" % direction.name)
            lines.append("if action != ('push', %r, %r): return False"
                         % (obj.name, direction.name))
            continue
        if not isinstance(clause, GuardPredicate):
            raise UnsupportedClause("unknown guard clause %r" % (clause,))
        expr = clause.expr
        if isinstance(expr, FuncCall) and expr.name == "free":
            lines.append("if not _free(state, %s): return False" % _spatial(expr.args[0]))
        elif isinstance(expr, FuncCall) and expr.name == "colored":
            if len(expr.args) != 2 or not isinstance(expr.args[1], NumberLit):
                raise UnsupportedClause("colored(<spatial>, <int>) expected")
            lines.append("if _cell_colour(state, %s) != %d: return False"
                         % (_spatial(expr.args[0]), expr.args[1].value))
        else:
            raise UnsupportedClause("unsupported guard predicate %r" % (expr,))
    return lines


def _effect_code(rule: RuleDecl) -> (str, List[str]):
    """(object touched, mutation lines).  One rule touches exactly one object."""
    event = rule.event
    if not isinstance(event, FuncCall):
        raise UnsupportedClause("event must be a call")
    args = event.args
    if not args or not isinstance(args[0], NameRef):
        raise UnsupportedClause("event's first argument must be an object")
    obj = args[0].name

    if event.name == "moved":
        if len(args) != 2 or not isinstance(args[1], NameRef):
            raise UnsupportedClause("moved(o, dir)")
        direction = args[1].name
        if direction not in DIRECTIONS:
            raise UnsupportedClause("unknown direction %r" % direction)
        return obj, ["state.%s_pos = _neighbour(state.%s_pos, %r)"
                     % (obj, obj, direction)]
    if event.name == "jumped":
        if len(args) != 2 or not isinstance(args[1], NameRef):
            raise UnsupportedClause("jumped(o, <landmark>)")
        return obj, ["state.%s_pos = LANDMARKS[%r]" % (obj, args[1].name)]
    if event.name == "recolored":
        if len(args) != 2 or not isinstance(args[1], NumberLit):
            raise UnsupportedClause("recolored(o, <int>)")
        return obj, ["state.%s_colour = %d" % (obj, args[1].value)]
    if event.name == "vanished":
        return obj, ["state.%s_present = False" % obj]
    if event.name == "appeared":
        return obj, ["state.%s_present = True" % obj]
    raise UnsupportedClause("unknown event %r" % event.name)


def _goal_code(ast: TheoryAST) -> str:
    if ast.goal is None:
        return "    return False"
    expr = ast.goal.goal.expr
    if (isinstance(expr, Comparison) and expr.op == "="
            and isinstance(expr.left, FieldAccess)
            and isinstance(expr.right, TupleLit)
            and len(expr.right.elements) == 2
            and all(isinstance(e, NumberLit) for e in expr.right.elements)):
        r, c = (e.value for e in expr.right.elements)
        return "    return state.%s_%s == (%d, %d)" % (
            expr.left.obj, expr.left.field_name, r, c
        )
    raise UnsupportedClause("unsupported goal %r" % (expr,))


HEADER = '''"""Auto-generated from theory.dsl by compile/gen_python_a0.py — DO NOT EDIT.

Constraint 4: generated forms are never hand-edited.  Change theory.dsl and
recompile.

This module is the only predictor in the system.  `step` implements the manual's
rules under the semantics the manual **declares** in its `semantics:` section --
see SEMANTICS below.  Nothing about the frame axiom, the conflict policy or the
cascade shape is assumed by this backend; a manual that does not say is rejected
at compile time.
"""

from dataclasses import dataclass, replace
from typing import Dict, List, Optional, Tuple

Cell = Tuple[int, int]

DIRECTIONS: Dict[str, Cell] = {
    "up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1),
}
ACTIONS = [("push", "%(mover)s", d) for d in ("up", "down", "left", "right")]
'''


def generate_python(ast: TheoryAST, problem: Problem, semantics: Semantics,
                    mover: str = "Cart") -> str:
    check_backend_support(semantics)
    fields = _obj_fields(ast)
    names = sorted(fields)

    L: List[str] = [HEADER % {"mover": mover}]
    L.append("SEMANTICS = %r" % (semantics.as_json(),))
    L.append("GRID = (%d, %d)" % (problem.height, problem.width))
    L.append("BACKGROUND = %d" % problem.background)
    L.append("LANDMARKS: Dict[str, Cell] = %r" % (
        {k: tuple(v) for k, v in sorted(problem.landmarks.items())},))
    L.append("BOARD: List[List[int]] = [")
    for row in problem.board:
        L.append("    %r," % (row,))
    L.append("]")
    L.append("")
    L.append("")

    # ------------------------------------------------------------- state
    L.append("@dataclass")
    L.append("class State:")
    L.append('    """One state.  Field per object per observation in the word table."""')
    for name in names:
        for f in fields[name]:
            if f == "pos":
                L.append("    %s_pos: Cell = (0, 0)" % name)
            elif f == "color":
                L.append("    %s_colour: int = 0" % name)
            elif f == "present":
                L.append("    %s_present: bool = True" % name)
            else:
                raise UnsupportedClause("unsupported field %r on %r" % (f, name))
    L.append("")
    L.append("    def copy(self) -> 'State':")
    L.append("        return replace(self)")
    L.append("")
    L.append("    def key(self):")
    L.append("        return (%s)" % ", ".join(
        "self.%s_%s" % (n, "colour" if f == "color" else f)
        for n in names for f in fields[n]
    ))
    L.append("")
    L.append("")

    # ----------------------------------------------------------- rendering
    L.append("def render(state: State) -> List[List[int]]:")
    L.append('    """The manual drawn back onto a frame (constraint 2, cheap layer)."""')
    L.append("    grid = [list(row) for row in BOARD]")
    for name in names:
        present = "present" in fields[name]
        guard = "    if state.%s_present:" % name if present else "    if True:"
        L.append(guard)
        L.append("        r, c = state.%s_pos" % name)
        L.append("        grid[r][c] = state.%s_colour" % name)
    L.append("    return grid")
    L.append("")
    L.append("")
    L.append("def responsibility(state: State):")
    L.append('    """Which object owns each pixel; `None` means the board owns it.')
    L.append("")
    L.append("    Returns (owner_grid, contested).  `contested` is non-empty exactly")
    L.append("    when two objects claim the same pixel, which the manual forbids.")
    L.append('    """')
    L.append("    owner: List[List[Optional[str]]] = "
             "[[None] * GRID[1] for _ in range(GRID[0])]")
    L.append("    contested = []")
    for name in names:
        present = "present" in fields[name]
        L.append("    if %s:" % ("state.%s_present" % name if present else "True"))
        L.append("        r, c = state.%s_pos" % name)
        L.append("        if owner[r][c] is not None:")
        L.append("            contested.append(((r, c), owner[r][c], %r))" % name)
        L.append("        owner[r][c] = %r" % name)
    L.append("    return owner, contested")
    L.append("")
    L.append("")

    # ------------------------------------------------------------ helpers
    L.append("def _neighbour(cell: Cell, direction: str) -> Cell:")
    L.append("    dr, dc = DIRECTIONS[direction]")
    L.append("    return (cell[0] + dr, cell[1] + dc)")
    L.append("")
    L.append("")
    L.append("def _in_bounds(cell: Cell) -> bool:")
    L.append("    return 0 <= cell[0] < GRID[0] and 0 <= cell[1] < GRID[1]")
    L.append("")
    L.append("")
    L.append("def _cell_colour(state: State, cell: Cell) -> Optional[int]:")
    L.append('    """Read the colour off the rendered frame — no side door."""')
    L.append("    if not _in_bounds(cell):")
    L.append("        return None")
    L.append("    return render(state)[cell[0]][cell[1]]")
    L.append("")
    L.append("")
    L.append("def _free(state: State, cell: Cell) -> bool:")
    L.append("    return _cell_colour(state, cell) == BACKGROUND")
    L.append("")
    L.append("")

    # -------------------------------------------------------------- rules
    # Guard and effect are separate functions on purpose.  A rule's guard must
    # be read against the state *before* this transition: `press_left` recolours
    # the Button, and if `door_opens_left` then re-read its guard on the updated
    # state it would find colour 8 and silently not fire.  Simultaneous
    # semantics is what the manual means and what the Lean transcription assumes.
    touched: Dict[str, str] = {}
    for rule in ast.rules.rules:
        obj, effect = _effect_code(rule)
        touched[rule.name] = obj
        L.append("def _guard_%s(state: State, action) -> bool:" % rule.name)
        L.append('    """%s  [ev: %s  cov: %s]"""' % (
            rule.name,
            rule.meta.evidence if rule.meta else "-",
            rule.meta.coverage if rule.meta else "-",
        ))
        for line in _guard_code(rule):
            L.append("    " + line)
        L.append("    return True")
        L.append("")
        L.append("")
        L.append("def _effect_%s(state: State) -> None:" % rule.name)
        for line in effect:
            L.append("    " + line)
        L.append("")
        L.append("")

    L.append("RULES = [")
    for rule in ast.rules.rules:
        L.append("    (%r, _guard_%s, _effect_%s, %r),"
                 % (rule.name, rule.name, rule.name, touched[rule.name]))
    L.append("]")
    L.append("")
    L.append("")

    # --------------------------------------------------------------- step
    L.append("class AmbiguousTransition(Exception):")
    L.append('    """Two rules claimed the same object: constraint 9 is violated."""')
    L.append("")
    L.append("")
    L.append("def step(state: State, action) -> State:")
    L.append('    """One action, one successor, per the manual\'s `semantics:`.')
    L.append("")
    L.append("    frame persist     -- an object no firing rule touches is unchanged,")
    L.append("                         which is what makes this function total.")
    L.append("    conflict exclusive -- two rules claiming one object is an error,")
    L.append("                         not a precedence question.")
    L.append("    cascade single_frame -- every guard reads `state`, never the")
    L.append("                         partially updated result, and all effects")
    L.append("                         apply together.")
    L.append('    """')
    L.append("    result = state.copy()")
    L.append("    claimed = {}")
    L.append("    for name, guard, effect, obj in RULES:")
    L.append("        if not guard(state, action):")
    L.append("            continue")
    L.append("        if obj in claimed:")
    L.append("            raise AmbiguousTransition(")
    L.append("                '%s and %s both fire on %s for %s'")
    L.append("                % (claimed[obj], name, action, obj))")
    L.append("        claimed[obj] = name")
    L.append("        effect(result)")
    L.append("    return result")
    L.append("")
    L.append("")
    L.append("def fired(state: State, action) -> List[str]:")
    L.append("    return [name for name, guard, _e, _o in RULES if guard(state, action)]")
    L.append("")
    L.append("")
    L.append("def is_goal(state: State) -> bool:")
    L.append(_goal_code(ast))
    L.append("")
    L.append("")
    L.append("def simulate(initial: State, actions) -> List[State]:")
    L.append("    states = [initial]")
    L.append("    current = initial")
    L.append("    for action in actions:")
    L.append("        current = step(current, action)")
    L.append("        states.append(current)")
    L.append("    return states")
    L.append("")
    L.append("")
    L.append("def initial_state() -> State:")
    L.append("    return State(")
    for obj in problem.objects:
        if obj.name not in fields:
            continue
        L.append("        %s_pos=%r," % (obj.name, tuple(obj.pos)))
        if "color" in fields[obj.name]:
            L.append("        %s_colour=%d," % (obj.name, obj.color))
        if "present" in fields[obj.name]:
            L.append("        %s_present=%r," % (obj.name, obj.present))
    L.append("    )")
    L.append("")
    return "\n".join(L)
