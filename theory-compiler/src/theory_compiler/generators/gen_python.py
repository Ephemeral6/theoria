"""theory.py generator — the world's one predictor, compiled from the AST.

What changed, and why it had to (DECISIONS.md D-A0-011 is the bug report this
answers): the previous generator hard-coded the `moved` and `teleported` events,
assumed exactly one instance per declared object type, and rendered only objects
carrying both `pos` and `color`. It could not express a vanish, a recolour, a
rule whose guard mentions a second object, or a board with four pegs on it — so
the peg world's two rules compiled to `pass  # Implemented in specific game
code`, and the "generated simulation" simulated nothing.

This generator drives off the IR, which is the AST plus the level. It knows no
event names, no object names and no geometry in advance; it knows a *vocabulary*,
and it raises `UnsupportedClause` on anything outside it rather than guessing.
That last rule is `fd_adapter`'s and it is the important one: a backend that
quietly approximates a clause it does not understand produces a predictor that
disagrees with the manual, and every layer downstream then certifies the wrong
world.

Supported vocabulary
--------------------

geometry  a declared `pos: Int` makes a line world, `pos: Coord` a grid world;
          both share one `_free` and one `_neighbour`
guards    `act=<name>(...)`, `free(<cell>)`, `colored(<cell>, <int>)`,
          `adjacent(<inst>, <inst>)`, comparisons and integer arithmetic over
          `<inst>.<field>`, and `not <predicate>` (ledger entry E-01)
cells     `above|below|leftof|rightof(<inst>)`, `toward(<inst>, <dir>)`,
          `pos(<arith>)`, a declared landmark name
events    `moved(o, dir)`, `jumped(o, <landmark>)`, `jumped(o, over, dir)`,
          `recolored(o, <int>)`, `vanished(o)`, `appeared(o)`, `removed(o)`

Events are dispatched on **name and arity**, taken from the manual's own
`events:` declaration — `jumped(o, dest)` and `jumped(p, over, dir)` are
different events that two different manuals both chose to call `jumped`, and
the declaration is what says which one a rule means.
"""

from typing import Dict, List, Optional, Tuple

from ..ir import WorldIR, build_ir
from ..parser.ast_nodes import (
    BinOp, Comparison, FieldAccess, FuncCall, GuardAction, GuardPredicate,
    NameRef, NumberLit, RuleDecl, TheoryAST, TupleLit,
)
from ..problem import ProblemSpec

GRID_DIRECTIONS = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}
LINE_DIRECTIONS = {"left": -1, "right": 1}
SPATIAL = {"above": "up", "below": "down", "leftof": "left", "rightof": "right"}


class UnsupportedClause(Exception):
    """Outside the subset this backend implements — raised, never approximated."""


class _Ctx:
    def __init__(self, ir: WorldIR):
        self.ir = ir
        self.line = _is_line(ir)
        self.directions = LINE_DIRECTIONS if self.line else GRID_DIRECTIONS
        self.instances = {i.name for i in ir.problem.instances}
        self.landmarks = set(ir.landmarks)

    def field(self, inst: str, obs: str) -> str:
        if inst not in self.instances:
            raise UnsupportedClause(
                f"{inst!r} is not an instance in this problem; the level has "
                f"{sorted(self.instances)}")
        return f"state.{inst}_{'color' if obs == 'colour' else obs}"


def _is_line(ir: WorldIR) -> bool:
    """`pos: Int` is a line world, `pos: Coord` a grid. The manual decides."""
    for obj in ir.ast.word_table.objects:
        for f in obj.fields:
            if f.name == "pos":
                return f.type == "Int"
    return ir.problem.is_line


# ------------------------------------------------------------------ expressions

def _cell(expr, ctx: _Ctx) -> str:
    """A cell-valued expression, as Python."""
    if isinstance(expr, NameRef):
        if expr.name in ctx.landmarks:
            return f"LANDMARKS[{expr.name!r}]"
        if expr.name in ctx.instances:
            return ctx.field(expr.name, "pos")
        raise UnsupportedClause(
            f"{expr.name!r} is neither an instance nor a declared landmark. If "
            f"it is level data, declare it: `landmark {expr.name}` (E-04).")
    if isinstance(expr, FuncCall):
        if expr.name in SPATIAL:
            if len(expr.args) != 1:
                raise UnsupportedClause(f"{expr.name}(<instance>) takes one argument")
            return f"_neighbour({_cell(expr.args[0], ctx)}, {SPATIAL[expr.name]!r})"
        if expr.name == "toward":
            if len(expr.args) != 2 or not isinstance(expr.args[1], NameRef):
                raise UnsupportedClause("toward(<instance>, <direction>)")
            d = expr.args[1].name
            if d not in ctx.directions:
                raise UnsupportedClause(
                    f"unknown direction {d!r}; this world has "
                    f"{sorted(ctx.directions)}")
            return f"_neighbour({_cell(expr.args[0], ctx)}, {d!r})"
        if expr.name == "pos":
            if len(expr.args) != 1:
                raise UnsupportedClause("pos(<expression>) takes one argument")
            return _value(expr.args[0], ctx)
    raise UnsupportedClause(f"not a cell expression: {expr!r}")


def _value(expr, ctx: _Ctx) -> str:
    """A scalar- or tuple-valued expression, as Python."""
    if isinstance(expr, NumberLit):
        return str(expr.value)
    if isinstance(expr, NameRef):
        if expr.name in ("true", "false"):
            return "True" if expr.name == "true" else "False"
        if expr.name in ctx.landmarks:
            return f"LANDMARKS[{expr.name!r}]"
        if expr.name in ctx.directions:
            return repr(expr.name)
        if expr.name in ctx.instances:
            return ctx.field(expr.name, "pos")
        raise UnsupportedClause(
            f"free name {expr.name!r} has no value. Declare it as a landmark, "
            f"or use an instance name the level supplies.")
    if isinstance(expr, FieldAccess):
        return ctx.field(expr.obj, expr.field_name)
    if isinstance(expr, BinOp):
        if expr.op not in "+-":
            raise UnsupportedClause(f"operator {expr.op!r} is outside the "
                                    f"invariant language (linear arithmetic)")
        return f"({_value(expr.left, ctx)} {expr.op} {_value(expr.right, ctx)})"
    if isinstance(expr, TupleLit):
        return "(" + ", ".join(_value(e, ctx) for e in expr.elements) + ")"
    if isinstance(expr, FuncCall):
        return _cell(expr, ctx)
    raise UnsupportedClause(f"cannot evaluate {expr!r}")


def _predicate(expr, ctx: _Ctx) -> str:
    if isinstance(expr, FuncCall):
        if expr.name == "free":
            if len(expr.args) != 1:
                raise UnsupportedClause("free(<cell>) takes one argument")
            return f"_free(state, {_cell(expr.args[0], ctx)})"
        if expr.name == "colored":
            if len(expr.args) != 2 or not isinstance(expr.args[1], NumberLit):
                raise UnsupportedClause("colored(<cell>, <int>) expected")
            return (f"_cell_colour(state, {_cell(expr.args[0], ctx)}) "
                    f"== {expr.args[1].value}")
        if expr.name == "adjacent":
            if len(expr.args) != 2:
                raise UnsupportedClause("adjacent(<a>, <b>) takes two arguments")
            return (f"_adjacent({_cell(expr.args[0], ctx)}, "
                    f"{_cell(expr.args[1], ctx)})")
        raise UnsupportedClause(f"unknown predicate {expr.name!r}")
    if isinstance(expr, Comparison):
        # `above(Cart) = wall` — `wall` is the one reserved cell value, and it
        # means "off the board", not "a cell that happens to hold a wall". It
        # has to be reserved rather than declared as a landmark because it is
        # not a cell at all.
        for side, other in ((expr.right, expr.left), (expr.left, expr.right)):
            if isinstance(side, NameRef) and side.name == "wall":
                negate = "" if expr.op == "=" else "not "
                return f"{negate}not _in_bounds({_cell(other, ctx)})"
        op = "==" if expr.op == "=" else expr.op
        return f"({_value(expr.left, ctx)} {op} {_value(expr.right, ctx)})"
    raise UnsupportedClause(f"not a guard predicate: {expr!r}")


# ----------------------------------------------------------------- guards/events

def _guard_lines(rule: RuleDecl, ctx: _Ctx) -> List[str]:
    lines = []
    for clause in rule.guard.clauses:
        if isinstance(clause, GuardAction):
            act = clause.action
            args = ", ".join(_action_arg(a, ctx) for a in act.args)
            lines.append(f"if action != ({act.action_name!r}, {args}): return False")
        elif isinstance(clause, GuardPredicate):
            cond = _predicate(clause.expr, ctx)
            lines.append(f"if {'' if clause.negated else 'not '}({cond}): "
                         f"return False")
        else:
            raise UnsupportedClause(f"unknown guard clause {clause!r}")
    return lines


def _action_arg(expr, ctx: _Ctx) -> str:
    if isinstance(expr, NameRef):
        return repr(expr.name)
    if isinstance(expr, NumberLit):
        return str(expr.value)
    raise UnsupportedClause(f"action arguments must be names or numbers: {expr!r}")


def _effect(rule: RuleDecl, ctx: _Ctx) -> Tuple[List[str], List[str]]:
    """(instances touched, mutation lines). Dispatch is on name *and* arity."""
    event = rule.event
    if not isinstance(event, FuncCall) or not event.args:
        raise UnsupportedClause(f"event must be a call on an object: {event!r}")
    if not isinstance(event.args[0], NameRef):
        raise UnsupportedClause("an event's first argument must be an object")
    obj = event.args[0].name
    key = (event.name, len(event.args))
    a = event.args

    if key == ("moved", 2):
        d = _direction(a[1], ctx)
        return [obj], [f"state.{obj}_pos = _neighbour(state.{obj}_pos, {d!r})"]
    if key in (("jumped", 2), ("teleported", 2)):
        # Same shape, two words. Which word a manual uses is its business; the
        # backend implements shapes, and the `events:` declaration is what ties
        # the two together.
        if not isinstance(a[1], NameRef) or a[1].name not in ctx.landmarks:
            raise UnsupportedClause(
                f"{event.name}(o, <landmark>) needs a declared landmark as its "
                "destination; a bare coordinate would be level data wearing a "
                "domain rule's clothes (E-04)")
        return [obj], [f"state.{obj}_pos = LANDMARKS[{a[1].name!r}]"]
    if key == ("jumped", 3):
        # The peg jump: the mover travels two cells and the jumped peg dies.
        if not isinstance(a[1], NameRef):
            raise UnsupportedClause("jumped(o, over, dir): `over` must be an object")
        over, d = a[1].name, _direction(a[2], ctx)
        return [obj, over], [
            f"state.{obj}_pos = _neighbour("
            f"_neighbour(state.{obj}_pos, {d!r}), {d!r})",
            f"state.{over}_alive = False",
        ]
    if key == ("recolored", 2):
        if not isinstance(a[1], NumberLit):
            raise UnsupportedClause("recolored(o, <int>)")
        return [obj], [f"state.{obj}_color = {a[1].value}"]
    if key == ("vanished", 1):
        return [obj], [f"state.{obj}_present = False"]
    if key == ("appeared", 1):
        return [obj], [f"state.{obj}_present = True"]
    if key == ("removed", 1):
        return [obj], [f"state.{obj}_alive = False"]
    raise UnsupportedClause(
        f"unknown event {event.name}/{len(event.args)}. The manual declares it "
        f"in `events:`; this backend implements moved/2, jumped/2, jumped/3, "
        f"recolored/2, vanished/1, appeared/1, removed/1.")


def _direction(expr, ctx: _Ctx) -> str:
    if not isinstance(expr, NameRef) or expr.name not in ctx.directions:
        raise UnsupportedClause(
            f"expected a direction from {sorted(ctx.directions)}, got {expr!r}")
    return expr.name


def _goal_body(ir: WorldIR, ctx: _Ctx) -> List[str]:
    if ir.ast.goal is None:
        return ["    return False"]
    expr = ir.ast.goal.goal.expr
    # `count(<Type>, <field> = <value>) = <n>` — how many instances are still in
    # a given condition. This is the peg goal, and v0.1's generator could not
    # read it at all.
    if (isinstance(expr, Comparison) and expr.op == "="
            and isinstance(expr.left, FuncCall) and expr.left.name == "count"):
        args = expr.left.args
        if not args or not isinstance(args[0], NameRef):
            raise UnsupportedClause("count(<Type>, ...) needs a type first")
        type_name = args[0].name
        names = [i.name for i in ir.problem.instances if i.type == type_name]
        if len(args) == 1:
            terms = ["1" for _ in names]
        elif len(args) == 2 and isinstance(args[1], Comparison):
            cond = args[1]
            if not isinstance(cond.left, NameRef):
                raise UnsupportedClause("count's condition must be `<field> = <value>`")
            obs, want = cond.left.name, _value(cond.right, ctx)
            terms = [f"(1 if state.{n}_{obs} == {want} else 0)" for n in names]
        else:
            raise UnsupportedClause(f"unsupported count(): {expr.left!r}")
        total = " + ".join(terms) if terms else "0"
        return [f"    return ({total}) == {_value(expr.right, ctx)}"]
    if isinstance(expr, Comparison) and expr.op == "=":
        return [f"    return {_predicate(expr, ctx)}"]
    raise UnsupportedClause(f"unsupported goal {expr!r}")


# ---------------------------------------------------------------------- driver

def generate_python(ast: TheoryAST, problem: ProblemSpec) -> str:
    """Compile the manual and the level into the module that predicts the world."""
    ir = build_ir(ast, problem)
    sem = ir.semantics
    if sem.frame != "persist":
        raise UnsupportedClause(
            f"this backend implements `frame persist` only; {sem.frame!r} means "
            f"an untouched object does not carry over, which is a different step")
    if sem.cascade != "single_frame":
        raise UnsupportedClause(
            "this backend implements `cascade single_frame` only; `multi_frame` "
            "makes one action yield a frame *sequence*, changing the shape of "
            "step, of the replay comparison and of the PDDL encoding")
    if sem.conflict != "exclusive":
        raise UnsupportedClause(
            "this backend implements `conflict exclusive` only; a declared "
            "priority order would have to be compiled into the rule dispatch")

    ctx = _Ctx(ir)
    L: List[str] = []
    L.append('"""Auto-generated from theory.dsl — DO NOT EDIT.')
    L.append("")
    L.append("Change the manual and recompile. This module is the only predictor")
    L.append("in the system: certify's replay, the Lean generator's transition")
    L.append("table and the plan validator all read the world through `step`.")
    L.append("")
    L.append("`step` implements the semantics the manual *declares*; nothing")
    L.append("about the frame axiom, the conflict policy or the cascade shape is")
    L.append("assumed here, and a manual that does not say is refused.")
    L.append('"""')
    L.append("")
    L.append("from dataclasses import dataclass, replace")
    L.append("")
    L.append("SEMANTICS = %r" % ({"frame": sem.frame, "conflict": sem.conflict,
                                  "cascade": sem.cascade},))
    L.append("GEOMETRY = %r" % ("line" if ctx.line else "grid",))
    L.append("DIRECTIONS = %r" % (ctx.directions,))
    L.append("LANDMARKS = %r" % ({k: v if not ctx.line else v[0]
                                  for k, v in sorted(ir.landmarks.items())},))
    L.append("BACKGROUND = %d" % problem.background)
    if ctx.line:
        L.append("N_POS = %d" % (problem.n_pos if problem.n_pos is not None
                                 else len(problem.cells())))
        L.append("BOARD = None")
    else:
        L.append("N_POS = None")
        L.append("GRID = (%d, %d)" % (problem.height, problem.width))
        L.append("BOARD = [")
        for row in problem.board:
            L.append("    %r," % (row,))
        L.append("]")
    L.append("ACTIONS = %r" % (_action_alphabet(ir, ctx),))
    L.append("")
    L.append("")

    # ------------------------------------------------------------------ state
    L.append("@dataclass")
    L.append("class State:")
    L.append('    """One field per instance per observation the word table names."""')
    for inst in ir.problem.instances:
        for obs in ir.fields_by_type.get(inst.type, []):
            L.append(f"    {inst.name}_{obs}: object = {_default(inst, obs, ctx)!r}")
    L.append("")
    L.append("    def copy(self):")
    L.append("        return replace(self)")
    L.append("")
    L.append("    def key(self):")
    keys = [f"self.{i.name}_{o}" for i in ir.problem.instances
            for o in ir.fields_by_type.get(i.type, [])]
    L.append("        return (%s,)" % ", ".join(keys) if keys else "        return ()")
    L.append("")
    L.append("")

    # ---------------------------------------------------------------- helpers
    L.extend(_helpers(ir, ctx))

    # ------------------------------------------------------------------ rules
    # Guard and effect are separate functions because the manual declares
    # `cascade single_frame`: every guard reads the pre-state. Reading a
    # partially updated state instead is a real bug that a real sprint hit --
    # a rule recoloured a button and the next rule then failed its own guard.
    touched: Dict[str, List[str]] = {}
    for rule in ir.rules:
        objs, effect = _effect(rule, ctx)
        touched[rule.name] = objs
        L.append(f"def _guard_{rule.name}(state, action):")
        L.append('    """%s  [ev: %s  cov: %s]"""' % (
            rule.name,
            rule.meta.evidence if rule.meta else "-",
            rule.meta.coverage if rule.meta else "-"))
        for line in _guard_lines(rule, ctx):
            L.append("    " + line)
        L.append("    return True")
        L.append("")
        L.append("")
        L.append(f"def _effect_{rule.name}(state):")
        for line in effect:
            L.append("    " + line)
        L.append("")
        L.append("")

    L.append("RULES = [")
    for rule in ir.rules:
        L.append("    (%r, _guard_%s, _effect_%s, %r),"
                 % (rule.name, rule.name, rule.name, touched[rule.name]))
    L.append("]")
    L.append("")
    L.append("")

    # ------------------------------------------------------------------- step
    L.extend(_step(ir))

    L.append("def is_goal(state):")
    L.extend(_goal_body(ir, ctx))
    L.append("")
    L.append("")
    L.append("def simulate(initial, actions):")
    L.append("    states = [initial]")
    L.append("    current = initial")
    L.append("    for action in actions:")
    L.append("        current = step(current, action)")
    L.append("        states.append(current)")
    L.append("    return states")
    L.append("")
    L.append("")
    L.append("def initial_state():")
    L.append("    return State(")
    for inst in ir.problem.instances:
        for obs in ir.fields_by_type.get(inst.type, []):
            L.append(f"        {inst.name}_{obs}={_default(inst, obs, ctx)!r},")
    L.append("    )")
    L.append("")
    return "\n".join(L)


def _default(inst, obs: str, ctx: _Ctx):
    if obs == "pos":
        return inst.pos[0] if ctx.line else tuple(inst.pos)
    if obs in ("color", "colour"):
        return inst.color if inst.color is not None else 0
    if obs == "present":
        return inst.present
    if obs == "alive":
        return bool(inst.extra.get("alive", True))
    return inst.extra.get(obs)


def _action_alphabet(ir: WorldIR, ctx: _Ctx) -> List[tuple]:
    """Every ground action any rule can match, in declaration order."""
    out = []
    for rule in ir.rules:
        for clause in rule.guard.clauses:
            if isinstance(clause, GuardAction):
                try:
                    args = tuple(eval(_action_arg(a, ctx), {}, {})
                                 for a in clause.action.args)
                except UnsupportedClause:
                    continue
                item = (clause.action.action_name,) + args
                if item not in out:
                    out.append(item)
    return out


def _helpers(ir: WorldIR, ctx: _Ctx) -> List[str]:
    L: List[str] = []
    if ctx.line:
        L.append("def _neighbour(cell, direction):")
        L.append("    return cell + DIRECTIONS[direction]")
        L.append("")
        L.append("")
        L.append("def _in_bounds(cell):")
        L.append("    return 0 <= cell < N_POS")
    else:
        L.append("def _neighbour(cell, direction):")
        L.append("    dr, dc = DIRECTIONS[direction]")
        L.append("    return (cell[0] + dr, cell[1] + dc)")
        L.append("")
        L.append("")
        L.append("def _in_bounds(cell):")
        L.append("    return 0 <= cell[0] < GRID[0] and 0 <= cell[1] < GRID[1]")
    L.append("")
    L.append("")
    L.append("def _adjacent(a, b):")
    if ctx.line:
        L.append("    return abs(a - b) == 1")
    else:
        L.append("    return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1")
    L.append("")
    L.append("")

    # `render` and `_cell_colour` exist so guards read the world off the frame
    # rather than through a side door into the state -- one predictor, one view.
    L.append("def render(state):")
    L.append('    """The manual drawn back onto a frame."""')
    if ctx.line:
        L.append("    grid = [BACKGROUND] * N_POS")
    else:
        L.append("    grid = [list(row) for row in BOARD]")
    for inst in ir.problem.instances:
        obs = ir.fields_by_type.get(inst.type, [])
        if "pos" not in obs:
            continue
        conds = []
        if "present" in obs:
            conds.append(f"state.{inst.name}_present")
        if "alive" in obs:
            conds.append(f"state.{inst.name}_alive")
        L.append("    if %s:" % (" and ".join(conds) if conds else "True"))
        colour = (f"state.{inst.name}_color" if "color" in obs
                  else f"state.{inst.name}_colour" if "colour" in obs else "1")
        if ctx.line:
            L.append(f"        grid[state.{inst.name}_pos] = {colour}")
        else:
            L.append(f"        r, c = state.{inst.name}_pos")
            L.append(f"        grid[r][c] = {colour}")
    L.append("    return grid")
    L.append("")
    L.append("")
    L.append("def _cell_colour(state, cell):")
    L.append("    if not _in_bounds(cell):")
    L.append("        return None")
    if ctx.line:
        L.append("    return render(state)[cell]")
    else:
        L.append("    return render(state)[cell[0]][cell[1]]")
    L.append("")
    L.append("")
    L.append("def _free(state, cell):")
    L.append("    return _cell_colour(state, cell) == BACKGROUND")
    L.append("")
    L.append("")
    L.append("def occupancy(state):")
    L.append('    """The frame as a bitstring — the view a pagoda weight sees."""')
    if ctx.line:
        L.append("    cells = render(state)")
        L.append("    return ''.join('0' if v == BACKGROUND else '1' for v in cells)")
    else:
        L.append("    return ''.join('0' if v == BACKGROUND else '1'")
        L.append("                   for row in render(state) for v in row)")
    L.append("")
    L.append("")
    return L


def _step(ir: WorldIR) -> List[str]:
    L: List[str] = []
    L.append("class AmbiguousTransition(Exception):")
    L.append('    """Two rules claimed one object: `conflict exclusive` is violated."""')
    L.append("")
    L.append("")
    L.append("def step(state, action):")
    L.append('    """One action, one successor, per the manual\'s `semantics:`.')
    L.append("")
    L.append("    frame persist        -- an object no firing rule touches is")
    L.append("                            unchanged, which is what makes this total.")
    L.append("    conflict exclusive   -- two rules claiming one object is an error,")
    L.append("                            not a precedence question.")
    L.append("    cascade single_frame -- every guard reads `state`, never the")
    L.append("                            partially updated result.")
    L.append('    """')
    L.append("    result = state.copy()")
    L.append("    claimed = {}")
    L.append("    for name, guard, effect, objs in RULES:")
    L.append("        if not guard(state, action):")
    L.append("            continue")
    L.append("        for obj in objs:")
    L.append("            if obj in claimed:")
    L.append("                raise AmbiguousTransition(")
    L.append("                    '%s and %s both fire on %s for %s'")
    L.append("                    % (claimed[obj], name, action, obj))")
    L.append("            claimed[obj] = name")
    L.append("        effect(result)")
    L.append("    return result")
    L.append("")
    L.append("")
    L.append("def fired(state, action):")
    L.append("    return [n for n, g, _e, _o in RULES if g(state, action)]")
    L.append("")
    L.append("")
    return L
