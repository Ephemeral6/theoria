"""
theory.pddl generator — converts TheoryAST to PDDL domain + problem files.

Actions are parameterized to objects (not raw coordinates), following the
dsl_grammar_v0.1 contract: click(Object) not click(x,y).

Generates STRIPS-compatible PDDL with :typing.
"""
from ..parser.ast_nodes import (
    TheoryAST, ObjectDecl, RuleDecl,
    Guard, GuardPredicate, GuardAction, ActionMatch,
    FuncCall, NameRef, NumberLit, TupleLit, FieldAccess,
    Comparison, BinOp, GoalSection, GoalExpr,
)
from .gen_python import UnsupportedClause

# The subset of `semantics:` this encoding implements. Outside it, raise —
# never approximate. `gen_python` has had this guard since the section landed
# and `gen_lean` inherits it by building the predictor first; this backend
# reads only the AST, so it had none, and would emit a STRIPS encoding that
# assumes `persist` / `exclusive` / `single_frame` for a manual declaring
# something else. That is the `semantics:` hazard reproduced one layer down:
# the manual states the fact, and the compiler ignores it silently.
SUPPORTED_SEMANTICS = {
    "frame": ("persist",),
    "conflict": ("exclusive",),
    "cascade": ("single_frame",),
}


def _check_semantics(ast: TheoryAST) -> None:
    sem = ast.semantics
    if sem is None:
        return                      # `build_ir` is where a missing section is an error
    for field_name, allowed in sorted(SUPPORTED_SEMANTICS.items()):
        value = getattr(sem, field_name)
        if value not in allowed:
            raise UnsupportedClause(
                "the PDDL backend implements `%s %s` only; this manual declares "
                "`%s %s`, and a STRIPS encoding of it would be a different "
                "world, not an approximation of this one"
                % (field_name, allowed[0], field_name, value))


def generate_pddl(ast: TheoryAST, problem_name: str = "instance-1",
                   grid_width: int = 2, grid_height: int = 3,
                   problem: "ProblemSpec | None" = None) -> tuple:
    """Generate (domain_pddl, problem_pddl) strings from a TheoryAST.

    Without a `problem`, the problem half is a **placeholder**: every object
    stands on `cell-0-0`, every cell is free, and the board's walls do not exist.
    That was adequate while the only consumer was a round-trip test of the
    domain, and it is not adequate for anything that reads the problem as a
    board — a handover package shipping it would hand its reader a board that is
    not the board, and the reader could not tell. Passing a `ProblemSpec` emits
    the level's real geometry: its walls, where each instance actually starts,
    and a goal with its landmarks resolved.

    Returns:
        Tuple of (domain_str, problem_str)
    """
    _check_semantics(ast)
    domain_name = "theoria-domain"
    if problem is not None:
        if problem.is_line:
            raise UnsupportedClause(
                "this PDDL encoding lays cells out as a grid; problem %r is a "
                "line world with %d positions" % (problem.name, problem.n_pos))
        grid_height = problem.height if problem.height is not None else grid_height
        grid_width = problem.width if problem.width is not None else grid_width
        problem_name = problem.name
    domain = _gen_domain(ast, domain_name, grid_width, grid_height)
    problem_text = _gen_problem(ast, domain_name, problem_name, grid_width,
                                grid_height, problem)
    return domain, problem_text


def _gen_domain(ast: TheoryAST, domain_name: str, w: int, h: int) -> str:
    lines = []
    lines.append(f"(define (domain {domain_name})")
    lines.append("  (:requirements :strips :typing)")
    lines.append("")

    # Types
    types = ["cell"]
    obj_types = []
    if ast.word_table:
        for obj in ast.word_table.objects:
            obj_types.append(obj.name.lower())
    types.extend(obj_types)
    lines.append(f"  (:types {' '.join(types)} - object)")
    lines.append("    ; direction is implicit in action names")
    lines.append("")

    # Predicates
    lines.append("  (:predicates")
    lines.append("    (at ?o - object ?c - cell)")
    lines.append("    (free ?c - cell)")
    lines.append("    (adjacent-up ?c1 - cell ?c2 - cell)")
    lines.append("    (adjacent-down ?c1 - cell ?c2 - cell)")
    lines.append("    (adjacent-left ?c1 - cell ?c2 - cell)")
    lines.append("    (adjacent-right ?c1 - cell ?c2 - cell)")
    lines.append("    (boundary-up ?c - cell)")
    lines.append("    (boundary-down ?c - cell)")
    lines.append("    (boundary-left ?c - cell)")
    lines.append("    (boundary-right ?c - cell)")
    lines.append("  )")
    lines.append("")

    # Actions — one per rule
    if ast.rules:
        for rule in ast.rules.rules:
            action_str = _rule_to_action(rule, obj_types)
            lines.append(action_str)
            lines.append("")

    lines.append(")")
    return "\n".join(lines)


def _instance_names(ast: TheoryAST, problem) -> "list":
    """(pddl_name, type_name, cell_or_None, present) for every object instance.

    Naming stays `<type>1`, `<type>2`, … in declaration order, which is what
    `_expr_to_pddl_goal` already writes into a goal; a level with one instance
    per type — every level either track has produced — therefore keeps exactly
    the names the placeholder emitted.
    """
    out = []
    if not ast.word_table:
        return out
    for obj in ast.word_table.objects:
        type_name = obj.name.lower()
        instances = problem.instances_of(obj.name) if problem is not None else []
        if not instances:
            out.append((f"{type_name}1", type_name, None, True))
            continue
        for n, inst in enumerate(instances, start=1):
            out.append((f"{type_name}{n}", type_name, tuple(inst.pos), inst.present))
    return out


def _gen_problem(ast: TheoryAST, domain_name: str, problem_name: str,
                 w: int, h: int, problem=None) -> str:
    lines = []
    lines.append(f"(define (problem {problem_name})")
    lines.append(f"  (:domain {domain_name})")
    lines.append("")

    # Objects: cells
    cells = [f"cell-{r}-{c}" for r in range(h) for c in range(w)]
    cell_list = " ".join(cells)
    lines.append(f"  (:objects")
    lines.append(f"    {cell_list} - cell")

    # Object instances
    for pddl_name, type_name, _cell, _present in _instance_names(ast, problem):
        lines.append(f"    {pddl_name} - {type_name}")
    lines.append("  )")
    lines.append("")

    # Init
    lines.append("  (:init")
    # Adjacency facts
    for r in range(h):
        for c in range(w):
            cell = f"cell-{r}-{c}"
            if r > 0:
                lines.append(f"    (adjacent-up {cell} cell-{r-1}-{c})")
            else:
                lines.append(f"    (boundary-up {cell})")
            if r < h - 1:
                lines.append(f"    (adjacent-down {cell} cell-{r+1}-{c})")
            else:
                lines.append(f"    (boundary-down {cell})")
            if c > 0:
                lines.append(f"    (adjacent-left {cell} cell-{r}-{c-1})")
            else:
                lines.append(f"    (boundary-left {cell})")
            if c < w - 1:
                lines.append(f"    (adjacent-right {cell} cell-{r}-{c+1})")
            else:
                lines.append(f"    (boundary-right {cell})")

    # Initial object positions.  Without a level there is nowhere to put them
    # and (0,0) is the placeholder; with one, they stand where the level says.
    placed = _instance_names(ast, problem)
    occupied = set()
    for pddl_name, _type_name, cell, present in placed:
        if not present:
            continue
        where = cell if cell is not None else (0, 0)
        lines.append(f"    (at {pddl_name} cell-{where[0]}-{where[1]})")
        occupied.add(tuple(where))

    # Mark free cells.  A cell is free when the board's own colour there is the
    # background and nothing is standing on it -- the same reading of `free` the
    # executable form compiles.
    for r in range(h):
        for c in range(w):
            if (r, c) in occupied:
                continue
            if problem is not None and problem.board:
                row = problem.board[r] if r < len(problem.board) else []
                colour = row[c] if c < len(row) else problem.background
                if colour != problem.background:
                    continue           # the board itself is not free here
            lines.append(f"    (free cell-{r}-{c})")
    lines.append("  )")
    lines.append("")

    # Goal
    lines.append("  (:goal")
    if ast.goal:
        goal_pddl = _goal_to_pddl(ast.goal, problem)
        lines.append(f"    {goal_pddl}")
    else:
        lines.append("    (and)")
    lines.append("  )")
    lines.append(")")
    return "\n".join(lines)


def _rule_to_action(rule: RuleDecl, obj_types: list) -> str:
    """Convert a rule to a PDDL action."""
    lines = []
    action_name = rule.name.replace("_", "-")

    # Determine parameters from guard
    params, preconditions = _guard_to_pddl(rule.guard, obj_types)
    effects = _event_to_pddl(rule.event, params)

    # Build parameter string
    param_parts = []
    for pname, ptype in params.items():
        param_parts.append(f"?{pname} - {ptype}")
    param_str = " ".join(param_parts)

    lines.append(f"  (:action {action_name}")
    lines.append(f"    :parameters ({param_str})")
    lines.append(f"    :precondition (and")
    for prec in preconditions:
        lines.append(f"      {prec}")
    lines.append(f"    )")
    lines.append(f"    :effect (and")
    for eff in effects:
        lines.append(f"      {eff}")
    lines.append(f"    )")
    lines.append(f"  )")
    return "\n".join(lines)


def _guard_to_pddl(guard, obj_types: list) -> tuple:
    """Convert guard to (params_dict, precondition_list)."""
    params = {}
    preconds = []

    if guard is None:
        return params, preconds

    if not hasattr(guard, 'clauses'):
        return params, preconds

    for clause in guard.clauses:
        if isinstance(clause, GuardAction):
            am = clause.action
            # Add the object being acted on as a parameter
            for arg in am.args:
                if isinstance(arg, NameRef):
                    pname = arg.name.lower()
                    ptype = pname if pname in obj_types else "object"
                    params[pname] = ptype
        elif isinstance(clause, GuardPredicate):
            expr = clause.expr
            _extract_pred_pddl(expr, params, preconds, obj_types)

    # If we found object params but no cell params, add position
    if any(t in obj_types for t in params.values()):
        for pname in list(params.keys()):
            if params[pname] in obj_types:
                pos_name = f"{pname}-pos"
                params[pos_name] = "cell"
                preconds.insert(0, f"(at ?{pname} ?{pos_name})")

    return params, preconds


def _extract_pred_pddl(expr, params: dict, preconds: list, obj_types: list):
    """Extract predicates and parameters from a guard expression."""
    if isinstance(expr, FuncCall):
        if expr.name == "free":
            inner = expr.args[0] if expr.args else None
            # v0.3, ledger X-5. `free(<obj>.pos)` excludes the object from its
            # own occupancy test, and this encoding keeps `free` as a predicate
            # *of a cell* — `(free ?c)`, withheld from every cell an object
            # holds. A per-occurrence exclusion has no image there: the clause
            # would be permanently false in PDDL and satisfiable in Python, so
            # two of the four co-derived forms would encode different worlds.
            # Refuse, per v0.2 revision item 10 — this backend's silent
            # approximations are what that item exists to stop.
            through_object, spelling = None, None
            if isinstance(inner, FieldAccess) and inner.field_name == "pos":
                through_object = inner.obj
                spelling = "%s.pos" % inner.obj
            elif isinstance(inner, NameRef) and inner.name in obj_types:
                through_object = spelling = inner.name
            if through_object is not None:
                raise UnsupportedClause(
                    "free(%s) names its cell through an object, which excludes "
                    "that object from its own occupancy test (v0.3, X-5). This "
                    "STRIPS encoding holds `free` as a property of a cell and "
                    "has no way to say `free except for %s`. Refusing rather "
                    "than dropping the precondition."
                    % (spelling, through_object))
            if isinstance(inner, FuncCall) and inner.name in ("above", "below", "left", "right"):
                # free(above(Cart)) -> need a dest cell that is adjacent and free
                direction = inner.name
                obj_arg = inner.args[0] if inner.args else None
                if isinstance(obj_arg, NameRef):
                    obj_name = obj_arg.name.lower()
                    dest_name = f"dest"
                    if dest_name not in params:
                        params[dest_name] = "cell"
                    preconds.append(f"(adjacent-{direction} ?{obj_name}-pos ?{dest_name})")
                    preconds.append(f"(free ?{dest_name})")
        elif expr.name in ("above", "below", "left", "right"):
            # Spatial reference without free — boundary check
            direction = expr.name
            obj_arg = expr.args[0] if expr.args else None
            if isinstance(obj_arg, NameRef):
                obj_name = obj_arg.name.lower()
                preconds.append(f"(boundary-{direction} ?{obj_name}-pos)")
    elif isinstance(expr, Comparison):
        # e.g., above(Cart) = wall
        if isinstance(expr.left, FuncCall) and isinstance(expr.right, NameRef):
            if expr.right.name == "wall" and expr.left.name in ("above", "below", "left", "right"):
                direction = expr.left.name
                obj_arg = expr.left.args[0] if expr.left.args else None
                if isinstance(obj_arg, NameRef):
                    obj_name = obj_arg.name.lower()
                    preconds.append(f"(boundary-{direction} ?{obj_name}-pos)")


def _event_to_pddl(event, params: dict) -> list:
    """Convert an event expression to PDDL effects."""
    effects = []

    if isinstance(event, FuncCall):
        if event.name == "moved":
            # moved(Obj, dir) -> remove from old pos, add to dest
            obj_arg = event.args[0] if event.args else None
            if isinstance(obj_arg, NameRef):
                obj_name = obj_arg.name.lower()
                pos_name = f"{obj_name}-pos"
                dest_name = "dest"
                effects.append(f"(not (at ?{obj_name} ?{pos_name}))")
                effects.append(f"(at ?{obj_name} ?{dest_name})")
                effects.append(f"(not (free ?{dest_name}))")
                effects.append(f"(free ?{pos_name})")
        elif event.name == "teleported":
            obj_arg = event.args[0] if event.args else None
            dest_arg = event.args[1] if len(event.args) > 1 else None
            if isinstance(obj_arg, NameRef):
                obj_name = obj_arg.name.lower()
                pos_name = f"{obj_name}-pos"
                if dest_arg and isinstance(dest_arg, NameRef):
                    dest_name = dest_arg.name.lower()
                else:
                    dest_name = "dest"
                if dest_name not in params:
                    params[dest_name] = "cell"
                effects.append(f"(not (at ?{obj_name} ?{pos_name}))")
                effects.append(f"(at ?{obj_name} ?{dest_name})")
                effects.append(f"(not (free ?{dest_name}))")
                effects.append(f"(free ?{pos_name})")
    if not effects:
        effects.append("(and)")  # empty effect placeholder
    return effects


def _goal_to_pddl(goal_sec: GoalSection, problem=None) -> str:
    """Convert DSL goal to PDDL goal expression."""
    expr = goal_sec.goal.expr
    return _expr_to_pddl_goal(expr, problem)


def _expr_to_pddl_goal(expr, problem=None) -> str:
    """Recursively convert a goal expression to PDDL."""
    if isinstance(expr, Comparison):
        if isinstance(expr.left, FieldAccess):
            cell = _goal_cell(expr.right, problem)
            if cell is not None:
                # Cart.pos = (0, 0), or Box.pos = target with a level to
                # resolve `target` against -> (at cart1 cell-r-c)
                return f"(at {expr.left.obj.lower()}1 cell-{cell[0]}-{cell[1]})"
        left = _expr_to_pddl_goal(expr.left, problem)
        right = _expr_to_pddl_goal(expr.right, problem)
        return f"(= {left} {right})"
    elif isinstance(expr, BinOp):
        if expr.op == "and":
            left = _expr_to_pddl_goal(expr.left, problem)
            right = _expr_to_pddl_goal(expr.right, problem)
            return f"(and {left} {right})"
    elif isinstance(expr, NameRef):
        return expr.name
    elif isinstance(expr, NumberLit):
        return str(expr.value)
    return "(and)"


def _goal_cell(expr, problem):
    """The cell a goal's right-hand side names, or None if it names no cell.

    A literal `(2, 7)` is a cell whatever the level is.  A bare name is a
    landmark, and only the level knows where it is: without one, this returns
    None and the caller falls through to the generic encoding rather than
    inventing a coordinate.
    """
    if isinstance(expr, TupleLit):
        elems = expr.elements
        if len(elems) == 2 and all(isinstance(e, NumberLit) for e in elems):
            return (elems[0].value, elems[1].value)
        return None
    if isinstance(expr, NameRef) and problem is not None:
        cell = problem.landmarks.get(expr.name)
        if cell is not None and len(cell) == 2:
            return (cell[0], cell[1])
    return None
