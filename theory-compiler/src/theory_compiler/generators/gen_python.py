"""
theory.py generator — produces executable Python simulation code from TheoryAST.

The generated code:
- Defines the board/grid and object types
- Implements rule-based state transitions
- Given an initial state + action sequence, produces next-frame states
- Full-frame responsibility: every cell is accounted for (board or object)
"""

from ..parser.ast_nodes import (
    TheoryAST, ObjectDecl, Field,
    RuleDecl, Guard, GuardClause, GuardAction, GuardPredicate,
    Expr, NameRef, NumberLit, FieldAccess, FuncCall, BinOp, TupleLit, Comparison,
)


def generate_python(ast: TheoryAST, grid_width: int, grid_height: int,
                    initial_state: dict | None = None) -> str:
    """Generate executable Python simulation from TheoryAST.

    Args:
        ast: Parsed theory AST
        grid_width: Width of the board
        grid_height: Height of the board
        initial_state: Optional initial state dict

    Returns:
        Python source code as string
    """
    lines = []
    lines.append('"""Auto-generated simulation from theory.dsl."""')
    lines.append("")
    lines.append("from dataclasses import dataclass, field")
    lines.append("from typing import Optional")
    lines.append("from copy import deepcopy")
    lines.append("")
    lines.append("")

    # Grid constants
    lines.append(f"GRID_WIDTH = {grid_width}")
    lines.append(f"GRID_HEIGHT = {grid_height}")
    lines.append("")

    # Direction helpers
    lines.append("DIRECTIONS = {")
    lines.append("    'up': (0, -1),")
    lines.append("    'down': (0, 1),")
    lines.append("    'left': (-1, 0),")
    lines.append("    'right': (1, 0),")
    lines.append("}")
    lines.append("")

    # Generate object dataclasses
    if ast.word_table:
        for obj in ast.word_table.objects:
            lines.append(_gen_object_class(obj))
            lines.append("")

    # State class
    lines.append("")
    lines.append("@dataclass")
    lines.append("class State:")
    lines.append('    """Full world state."""')
    if ast.word_table:
        for obj in ast.word_table.objects:
            lines.append(f"    {obj.name.lower()}: {obj.name} = field(default_factory={obj.name})")
    lines.append("")
    lines.append("    def render(self) -> list[list[int]]:")
    lines.append('        """Render state to grid. Every cell gets a value (full-frame responsibility)."""')
    lines.append(f"        grid = [[0] * GRID_WIDTH for _ in range(GRID_HEIGHT)]")

    if ast.word_table:
        for obj in ast.word_table.objects:
            obj_lower = obj.name.lower()
            # Check if object has pos and color
            has_pos = any(f.name == "pos" for f in obj.fields)
            has_color = any(f.name == "color" for f in obj.fields)
            if has_pos and has_color:
                lines.append(f"        # Place {obj.name}")
                lines.append(f"        obj = self.{obj_lower}")
                lines.append(f"        x, y = obj.pos")
                lines.append(f"        if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:")
                lines.append(f"            grid[y][x] = obj.color")

    lines.append("        return grid")
    lines.append("")

    # Spatial helpers
    lines.append("")
    lines.append("def _neighbor(pos, direction):")
    lines.append('    """Get neighbor position in given direction."""')
    lines.append("    dx, dy = DIRECTIONS[direction]")
    lines.append("    return (pos[0] + dx, pos[1] + dy)")
    lines.append("")
    lines.append("")
    lines.append("def _in_bounds(pos):")
    lines.append('    """Check if position is within grid bounds."""')
    lines.append("    return 0 <= pos[0] < GRID_WIDTH and 0 <= pos[1] < GRID_HEIGHT")
    lines.append("")
    lines.append("")
    lines.append("def _free(state, pos):")
    lines.append('    """Check if a position is free (in bounds and no object there)."""')
    lines.append("    if not _in_bounds(pos):")
    lines.append("        return False")
    lines.append("    # Check no object occupies this position")

    if ast.word_table:
        for obj in ast.word_table.objects:
            has_pos = any(f.name == "pos" for f in obj.fields)
            if has_pos:
                lines.append(f"    if state.{obj.name.lower()}.pos == pos:")
                lines.append(f"        return False")

    lines.append("    return True")
    lines.append("")

    # Generate rule functions
    if ast.rules:
        for rule in ast.rules.rules:
            lines.append(_gen_rule_function(rule, ast))
            lines.append("")

    # Step function
    lines.append("")
    lines.append("def step(state: State, action: str) -> State:")
    lines.append('    """Apply action to state, return new state. Tries rules in order."""')
    lines.append("    new_state = deepcopy(state)")
    lines.append("    # Parse action")
    lines.append("    parts = action.split('(')")
    lines.append("    action_name = parts[0]")
    lines.append("    action_args = parts[1].rstrip(')').split(', ') if len(parts) > 1 else []")
    lines.append("")

    if ast.rules:
        for rule in ast.rules.rules:
            lines.append(f"    if _try_{rule.name}(new_state, action_name, action_args):")
            lines.append(f"        return new_state")

    lines.append("    # No rule matched — state unchanged")
    lines.append("    return new_state")
    lines.append("")

    # Simulate function
    lines.append("")
    lines.append("def simulate(initial: State, actions: list[str]) -> list[State]:")
    lines.append('    """Run a sequence of actions, return list of states (including initial)."""')
    lines.append("    states = [initial]")
    lines.append("    current = initial")
    lines.append("    for action in actions:")
    lines.append("        current = step(current, action)")
    lines.append("        states.append(current)")
    lines.append("    return states")
    lines.append("")

    return "\n".join(lines)


def _gen_object_class(obj: ObjectDecl) -> str:
    """Generate a dataclass for an object type."""
    lines = []
    lines.append("@dataclass")
    lines.append(f"class {obj.name}:")
    for f in obj.fields:
        py_type = _type_to_python(f.type)
        default = _type_default(f.type)
        lines.append(f"    {f.name}: {py_type} = {default}")
    return "\n".join(lines)


def _type_to_python(t: str) -> str:
    mapping = {"Int": "int", "Bool": "bool", "Coord": "tuple[int, int]", "Str": "str"}
    return mapping.get(t, "object")


def _type_default(t: str) -> str:
    mapping = {"Int": "0", "Bool": "True", "Coord": "(0, 0)", "Str": "''"}
    return mapping.get(t, "None")


def _gen_rule_function(rule: RuleDecl, ast: TheoryAST) -> str:
    """Generate a _try_<rulename> function that tests guard & applies event."""
    lines = []
    lines.append(f"def _try_{rule.name}(state: State, action_name: str, action_args: list[str]) -> bool:")
    lines.append(f'    """Try to apply rule: {rule.name}."""')

    # Parse the guard to generate conditions
    # We generate a series of if-checks; if any fails, return False
    for clause in rule.guard.clauses:
        if isinstance(clause, GuardAction):
            # act=push(Cart, up) → check action_name == 'push' and args match
            act = clause.action
            lines.append(f"    if action_name != '{act.action_name}':")
            lines.append(f"        return False")
            # Check args (by position)
            for i, arg in enumerate(act.args):
                arg_str = _expr_to_check(arg)
                if arg_str:
                    lines.append(f"    if len(action_args) <= {i} or action_args[{i}] != '{_expr_to_str(arg)}':")
                    lines.append(f"        return False")
        elif isinstance(clause, GuardPredicate):
            cond = _guard_predicate_to_python(clause.expr, ast)
            if cond:
                lines.append(f"    if not ({cond}):")
                lines.append(f"        return False")

    # Apply event
    lines.append(f"    # Apply: {rule.event.name}")
    event_code = _gen_event_effect(rule, ast)
    for eline in event_code:
        lines.append(f"    {eline}")

    lines.append("    return True")
    return "\n".join(lines)


def _expr_to_str(expr: Expr) -> str:
    """Convert expr to its string representation for arg matching."""
    if isinstance(expr, NameRef):
        return expr.name
    elif isinstance(expr, NumberLit):
        return str(expr.value)
    return ""


def _expr_to_check(expr: Expr) -> str:
    """Return non-empty if this arg should be checked."""
    if isinstance(expr, NameRef):
        # Object names are structural, direction names need checking
        name = expr.name
        if name in ('up', 'down', 'left', 'right'):
            return name
        # Skip object names (they're implicit)
        return ""
    return ""


def _guard_predicate_to_python(expr: Expr, ast: TheoryAST) -> str:
    """Convert a guard predicate expression to Python condition code."""
    if isinstance(expr, FuncCall):
        if expr.name == "free":
            # free(above(Cart)) → _free(state, _neighbor(state.cart.pos, 'up'))
            if expr.args and isinstance(expr.args[0], FuncCall):
                inner = expr.args[0]
                dir_map = {"above": "up", "below": "down", "left": "left", "right": "right"}
                if inner.name in dir_map:
                    obj_name = _expr_to_str(inner.args[0]) if inner.args else "cart"
                    return f"_free(state, _neighbor(state.{obj_name.lower()}.pos, '{dir_map[inner.name]}'))"
            # free(pos(...))
            if expr.args and isinstance(expr.args[0], FuncCall) and expr.args[0].name == "pos":
                # free(pos(expr)) — position is given directly
                return f"_free(state, {_expr_to_python_val(expr.args[0].args[0])})"
            return "True"  # fallback
        # Generic predicate
        return "True"
    elif isinstance(expr, Comparison):
        # Special case: above(X) = wall  →  not _in_bounds(_neighbor(...))
        if isinstance(expr.right, NameRef) and expr.right.name == "wall":
            if isinstance(expr.left, FuncCall):
                dir_map = {"above": "up", "below": "down", "left": "left", "right": "right"}
                if expr.left.name in dir_map:
                    obj_name = _expr_to_str(expr.left.args[0]) if expr.left.args else "cart"
                    neighbor = f"_neighbor(state.{obj_name.lower()}.pos, '{dir_map[expr.left.name]}')"
                    return f"not _in_bounds({neighbor})"
        left = _expr_to_python_val(expr.left)
        right = _expr_to_python_val(expr.right)
        op = "==" if expr.op == "=" else expr.op
        return f"{left} {op} {right}"
    return "True"


def _expr_to_python_val(expr: Expr) -> str:
    """Convert expression to Python value expression."""
    if isinstance(expr, NameRef):
        name = expr.name
        if name in ('wall', 'origin'):
            return f"'{name}'"
        if name in ('up', 'down', 'left', 'right'):
            return f"'{name}'"
        return f"state.{name.lower()}" if name[0].isupper() else name
    elif isinstance(expr, NumberLit):
        return str(expr.value)
    elif isinstance(expr, FieldAccess):
        return f"state.{expr.obj.lower()}.{expr.field_name}"
    elif isinstance(expr, FuncCall):
        if expr.name in ("above", "below", "left", "right"):
            dir_map = {"above": "up", "below": "down", "left": "left", "right": "right"}
            obj = _expr_to_python_val(expr.args[0]) if expr.args else "state.cart"
            return f"_neighbor({obj}.pos, '{dir_map[expr.name]}')"
        if expr.name == "pos":
            return _expr_to_python_val(expr.args[0])
        args = ", ".join(_expr_to_python_val(a) for a in expr.args)
        return f"{expr.name}({args})"
    elif isinstance(expr, BinOp):
        left = _expr_to_python_val(expr.left)
        right = _expr_to_python_val(expr.right)
        return f"({left} {expr.op} {right})"
    elif isinstance(expr, TupleLit):
        elems = ", ".join(_expr_to_python_val(e) for e in expr.elements)
        return f"({elems})"
    return "None"


def _gen_event_effect(rule: RuleDecl, ast: TheoryAST) -> list[str]:
    """Generate the effect of applying a rule's event."""
    event = rule.event
    lines = []

    if event.name == "moved":
        # moved(Obj, dir) — update obj position by direction
        # Direction comes from action args
        lines.append("direction = action_args[1] if len(action_args) > 1 else ''")
        lines.append("if direction in DIRECTIONS:")
        obj_ref = _expr_to_str(event.args[0]) if event.args else "Cart"
        lines.append(f"    dx, dy = DIRECTIONS[direction]")
        lines.append(f"    obj = state.{obj_ref.lower()}")
        lines.append(f"    obj.pos = (obj.pos[0] + dx, obj.pos[1] + dy)")

    elif event.name == "teleported":
        # teleported(Obj, dest) — move to origin (0,0)
        obj_ref = _expr_to_str(event.args[0]) if event.args else "Cart"
        lines.append(f"state.{obj_ref.lower()}.pos = (0, 0)")

    elif event.name == "jumped":
        # jumped(Peg_a, Peg_b, dir) — move Peg_a over Peg_b, remove Peg_b
        lines.append("# Peg jump: mover jumps over middle, middle is removed")
        lines.append("pass  # Implemented in specific game code")

    else:
        lines.append(f"pass  # Event: {event.name}")

    return lines
