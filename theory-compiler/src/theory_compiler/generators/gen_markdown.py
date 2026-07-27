"""
theory.md generator — deterministic natural-language rendering of TheoryAST.

Pure template/rule-based. No LLM calls. Same AST always produces byte-identical output.
DSL keywords (object, event, rule, goal, invariant, theorem, board) are rendered
as their natural-language equivalents, never as raw syntax.
"""
import re
from ..parser.ast_nodes import (
    TheoryAST, ObjectDecl, EventDecl, EventAlt, RuleDecl,
    InvariantDecl, TheoremDecl, WordTable, GoalSection, GoalExpr,
    LawsSection, EventsSection, RulesSection,
    Guard, GuardPredicate, GuardAction, ActionMatch,
    FuncCall, NameRef, NumberLit, TupleLit, FieldAccess,
    Comparison, BinOp,
)


def generate_markdown(ast: TheoryAST) -> str:
    """Generate a human-readable Markdown document from a TheoryAST."""
    sections = []

    sections.append("# World Description\n")

    # Word table
    if ast.word_table:
        sections.append(_render_word_table(ast.word_table))

    # Events
    if ast.events and ast.events.events:
        sections.append(_render_events(ast.events))

    # Rules
    if ast.rules and ast.rules.rules:
        sections.append(_render_rules(ast.rules))

    # Goal
    if ast.goal:
        sections.append(_render_goal(ast.goal))

    # Laws
    if ast.laws:
        sections.append(_render_laws(ast.laws))

    return "\n".join(sections) + "\n"


def _render_word_table(wt: WordTable) -> str:
    lines = ["## Things in This World\n"]
    if wt.has_board:
        lines.append("This world takes place on a **grid** (a fixed playing surface "
                     "that does not change between turns).\n")
    if wt.objects:
        lines.append("The following kinds of entities exist:\n")
        for obj in wt.objects:
            fields_desc = ", ".join(
                f"{f.name} ({_type_to_natural(f.type)})" for f in obj.fields
            )
            lines.append(f"- **{obj.name}**: characterized by {fields_desc}.")
        lines.append("")
    return "\n".join(lines)


def _render_events(es: EventsSection) -> str:
    lines = ["## What Can Happen\n"]
    lines.append("The following types of changes can occur:\n")
    for ev in es.events:
        alternatives = []
        for alt in ev.alternatives:
            params_str = ", ".join(alt.params) if alt.params else ""
            if params_str:
                alternatives.append(f"{_name_to_natural(alt.name)} (involving {params_str})")
            else:
                alternatives.append(_name_to_natural(alt.name))
        lines.append(f"- {' or '.join(alternatives)}.")
    lines.append("")
    return "\n".join(lines)


def _render_rules(rs: RulesSection) -> str:
    lines = ["## How Things Change\n"]
    for rule in rs.rules:
        confidence = ""
        if rule.meta and rule.meta.coverage:
            cov = rule.meta.coverage
            if "/" in cov:
                k, n = cov.split("/")
                k, n = int(k), int(n)
                if k < n:
                    confidence = f" (observed in {k} out of {n} cases — low confidence)"
                else:
                    confidence = f" (observed in all {n} cases)"

        guard_text = _guard_to_natural(rule.guard)
        event_text = _expr_to_natural(rule.event)

        lines.append(f"- **{_name_to_natural(rule.name)}**{confidence}: "
                     f"When {guard_text}, then {event_text}.")
    lines.append("")
    return "\n".join(lines)


def _render_goal(goal_sec: GoalSection) -> str:
    lines = ["## Winning Condition\n"]
    expr_text = _expr_to_natural(goal_sec.goal.expr)
    lines.append(f"The puzzle is solved when: {expr_text}.\n")
    return "\n".join(lines)


def _render_laws(laws: LawsSection) -> str:
    lines = ["## Known Truths\n"]
    if laws.invariants:
        lines.append("### Preserved Quantities\n")
        for inv in laws.invariants:
            status_text = ""
            if inv.status == "proven":
                status_text = " (mathematically verified)"
            elif inv.status == "open":
                status_text = " (conjectured, not yet proven)"
            op_natural = {"=": "always equals", ">=": "is always at least",
                          "<=": "is always at most"}.get(inv.op, inv.op)
            lines.append(f"- **{_name_to_natural(inv.name)}**: "
                         f"The quantity {inv.expr_text} {op_natural} {inv.value}"
                         f"{status_text}.")
        lines.append("")
    if laws.theorems:
        lines.append("### Derived Facts\n")
        for thm in laws.theorems:
            probe_text = ""
            if thm.probe == "passed":
                probe_text = " (verified by testing)"
            elif thm.probe == "pending":
                probe_text = " (awaiting verification)"
            depends_text = ""
            if thm.depends:
                depends_text = (f" This follows from: "
                                f"{', '.join(_name_to_natural(d) for d in thm.depends)}.")
            lines.append(f"- **{_name_to_natural(thm.name)}**: "
                         f"{thm.description}{probe_text}.{depends_text}")
        lines.append("")
    return "\n".join(lines)


# --- Helper functions ---

def _type_to_natural(t: str) -> str:
    mapping = {
        "Int": "a whole number",
        "Pos": "a position",
        "Bool": "true or false",
        "Color": "a color",
        "Shape": "a shape",
        "Direction": "a direction",
        "Coord": "a coordinate",
    }
    return mapping.get(t, t.lower())


def _name_to_natural(name: str) -> str:
    result = name.replace("_", " ")
    result = re.sub(r'([a-z])([A-Z])', r'\1 \2', result)
    return result.lower()


def _guard_to_natural(guard) -> str:
    if guard is None:
        return "always"
    if isinstance(guard, Guard):
        parts = [_guard_clause_to_natural(c) for c in guard.clauses]
        return " and ".join(parts)
    return str(guard)


def _guard_clause_to_natural(clause) -> str:
    if isinstance(clause, GuardPredicate):
        return _expr_to_natural(clause.expr)
    elif isinstance(clause, GuardAction):
        am = clause.action
        args_text = ", ".join(_expr_to_natural(a) for a in am.args)
        return f"the action is {_name_to_natural(am.action_name)}({args_text})"
    return str(clause)


def _expr_to_natural(expr) -> str:
    if isinstance(expr, FuncCall):
        return _func_to_natural(expr)
    elif isinstance(expr, NameRef):
        name = expr.name
        if name == "wall":
            return "a wall (out of bounds)"
        if name == "empty":
            return "empty"
        return name
    elif isinstance(expr, NumberLit):
        return str(expr.value)
    elif isinstance(expr, TupleLit):
        elems = ", ".join(_expr_to_natural(e) for e in expr.elements)
        return f"({elems})"
    elif isinstance(expr, FieldAccess):
        return f"the {expr.field_name} of {expr.obj}"
    elif isinstance(expr, Comparison):
        left = _expr_to_natural(expr.left)
        right = _expr_to_natural(expr.right)
        op_map = {"=": "is", "!=": "is not", "<": "is less than",
                  ">": "is greater than", "<=": "is at most", ">=": "is at least"}
        op_text = op_map.get(expr.op, expr.op)
        return f"{left} {op_text} {right}"
    elif isinstance(expr, BinOp):
        left = _expr_to_natural(expr.left)
        right = _expr_to_natural(expr.right)
        op_map = {"+": "plus", "-": "minus", "*": "times"}
        op_text = op_map.get(expr.op, expr.op)
        return f"{left} {op_text} {right}"
    else:
        return str(expr)


def _func_to_natural(fc: FuncCall) -> str:
    name = fc.name
    args = [_expr_to_natural(a) for a in fc.args]

    spatial_map = {
        "above": "the cell above {}",
        "below": "the cell below {}",
        "left": "the cell to the left of {}",
        "right": "the cell to the right of {}",
        "free": "{} is free (unoccupied)",
        "adjacent": "{} is adjacent to {}",
        "occupied": "{} is occupied",
        "count": "the number of {}",
        "peg_count": "the number of pegs",
    }

    if name in spatial_map:
        try:
            return spatial_map[name].format(*args)
        except (IndexError, KeyError):
            return f"{_name_to_natural(name)}({', '.join(args)})"
    if name == "moved":
        if len(args) == 2:
            return f"{args[0]} moves {args[1]}"
        return f"{args[0]} moves"
    if name == "teleported":
        if len(args) == 2:
            return f"{args[0]} teleports to {args[1]}"
        return f"{args[0]} teleports"
    if name == "vanished":
        return f"{args[0]} vanishes"
    if name == "jumped":
        return f"a peg jumps from {args[0]} over {args[1]} to {args[2]}" if len(args) >= 3 else f"a peg jumps"
    return f"{_name_to_natural(name)}({', '.join(args)})"
