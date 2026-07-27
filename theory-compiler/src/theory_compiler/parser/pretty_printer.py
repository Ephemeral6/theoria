"""
Pretty-printer for TheoryAST — produces canonical DSL text.
Used for round-trip verification: parse → print → re-parse should yield equivalent AST.
"""

from .ast_nodes import (
    TheoryAST, WordTable, ObjectDecl, Field, ConceptAccount,
    LandmarkDecl, WeightsDecl, DomainDecl, SemanticsSection,
    EventsSection, EventDecl, EventAlt,
    RulesSection, RuleDecl, RuleMeta, Guard, GuardClause,
    GuardAction, GuardPredicate, ActionMatch,
    Expr, NameRef, VarRef, NumberLit, FieldAccess, FuncCall, BinOp, TupleLit,
    Comparison,
    GoalSection, GoalExpr,
    LawsSection, InvariantDecl, TheoremDecl,
    PlaybookAST, OrderStmt, PruneStmt, HeuristicStmt, PreferStmt,
)


def print_theory(ast: TheoryAST) -> str:
    """Pretty-print a TheoryAST back to canonical DSL text."""
    sections = []

    if ast.word_table:
        sections.append(_print_word_table(ast.word_table))
    if ast.semantics:
        sections.append(_print_semantics(ast.semantics))
    if ast.events:
        sections.append(_print_events(ast.events))
    if ast.rules:
        sections.append(_print_rules(ast.rules))
    if ast.goal:
        sections.append(_print_goal(ast.goal))
    if ast.laws:
        sections.append(_print_laws(ast.laws))

    return "\n\n".join(sections) + "\n"


def _print_word_table(wt: WordTable) -> str:
    lines = ["word_table:"]
    if wt.has_board:
        lines.append("  board")
    for obj in wt.objects:
        fields = ", ".join(f"{f.name}: {f.type}" for f in obj.fields)
        lines.append(f"  object {obj.name} {{ {fields} }}")
    for dom in wt.domains:
        lines.append(f"  domain {dom.name} {{ {', '.join(dom.values)} }}")
    for lm in wt.landmarks:
        lines.append(f"  landmark {lm.name}")
    for wd in wt.weights:
        lines.append(f"  weights {wd.name} over {wd.over}")
    for acc in wt.accounts:
        parts = []
        if acc.segment:
            parts.append(f"segment: {acc.segment}")
        if acc.evidence_range:
            parts.append(f"ev: {acc.evidence_range}")
        if acc.compress is not None:
            parts.append(f"compress: {acc.compress}")
        lines.append(f"  {acc.obj_name} [{' '.join(parts)}]")
    return "\n".join(lines)


def _print_semantics(sem: SemanticsSection) -> str:
    conflict = ("exclusive" if sem.conflict == "exclusive"
                else "priority: " + " > ".join(sem.priority))
    return "\n".join([
        "semantics:",
        f"  frame {sem.frame}",
        f"  conflict {conflict}",
        f"  cascade {sem.cascade}",
    ])


def _print_events(es: EventsSection) -> str:
    lines = ["events:"]
    for ev in es.events:
        alts = " | ".join(
            f"{a.name}({', '.join(a.params)})" for a in ev.alternatives
        )
        lines.append(f"  event {alts}")
    return "\n".join(lines)


def _print_rules(rs: RulesSection) -> str:
    lines = ["rules:"]
    for rule in rs.rules:
        meta_str = ""
        if rule.meta:
            parts = []
            if rule.meta.evidence:
                parts.append(f"ev: {rule.meta.evidence}")
            if rule.meta.coverage:
                parts.append(f"cov: {rule.meta.coverage}")
            meta_str = " [" + " ".join(parts) + "]"
        binds = "".join(f" forall ?{v} in {d}" for v, d in rule.bindings.items())
        lines.append(f"  rule {rule.name}{binds}{meta_str}")
        guard_str = _print_guard(rule.guard)
        event_str = _print_expr(rule.event)
        lines.append(f"    when {guard_str} then {event_str}")
    return "\n".join(lines)


def _print_guard(g: Guard) -> str:
    parts = []
    for clause in g.clauses:
        if isinstance(clause, GuardAction):
            args_str = ", ".join(_print_expr(a) for a in clause.action.args)
            parts.append(f"act={clause.action.action_name}({args_str})")
        elif isinstance(clause, GuardPredicate):
            prefix = "not " if clause.negated else ""
            parts.append(prefix + _print_expr(clause.expr))
        else:
            parts.append(str(clause))
    return " and ".join(parts)


def _print_expr(expr: Expr) -> str:
    if isinstance(expr, NameRef):
        return expr.name
    elif isinstance(expr, VarRef):
        return f"?{expr.name}"
    elif isinstance(expr, NumberLit):
        return str(expr.value)
    elif isinstance(expr, FieldAccess):
        return f"{expr.obj}.{expr.field_name}"
    elif isinstance(expr, FuncCall):
        args = ", ".join(_print_expr(a) for a in expr.args)
        return f"{expr.name}({args})"
    elif isinstance(expr, BinOp):
        return f"{_print_expr(expr.left)} {expr.op} {_print_expr(expr.right)}"
    elif isinstance(expr, TupleLit):
        elems = ", ".join(_print_expr(e) for e in expr.elements)
        return f"({elems})"
    elif isinstance(expr, Comparison):
        return f"{_print_expr(expr.left)} {expr.op} {_print_expr(expr.right)}"
    else:
        return str(expr)


def _print_goal(gs: GoalSection) -> str:
    lines = ["goal:"]
    lines.append(f"  goal {_print_expr(gs.goal.expr)}")
    return "\n".join(lines)


def _print_laws(ls: LawsSection) -> str:
    lines = ["laws:"]
    for inv in ls.invariants:
        meta_parts = []
        if inv.status:
            meta_parts.append(f"status: {inv.status}")
        if inv.source:
            meta_parts.append(f"source: {inv.source}")
        meta = f" [{' '.join(meta_parts)}]" if meta_parts else ""
        lines.append(f"  invariant {inv.name} {inv.expr_text} {inv.op} {inv.value}{meta}")
    for thm in ls.theorems:
        meta_parts = []
        if thm.depends:
            meta_parts.append(f"depends: {', '.join(thm.depends)}")
        if thm.probe:
            meta_parts.append(f"probe: {thm.probe}")
        meta = ""
        if meta_parts:
            meta = "\n    [" + "   ".join(meta_parts) + "]"
        lines.append(f"  theorem {thm.name} \"{thm.description}\"{meta}")
    return "\n".join(lines)


def print_playbook(ast: PlaybookAST) -> str:
    """Pretty-print a PlaybookAST back to canonical DSL text."""
    lines = []
    for stmt in ast.statements:
        if isinstance(stmt, OrderStmt):
            meta = f" [proof: {stmt.proof}]" if stmt.proof else ""
            lines.append(f"order {stmt.landmark}{meta}")
        elif isinstance(stmt, PruneStmt):
            meta = f" [proof: {stmt.proof}]" if stmt.proof else ""
            lines.append(f"prune {stmt.condition} => dead{meta}")
        elif isinstance(stmt, HeuristicStmt):
            params = ", ".join(stmt.params)
            meta = f" [admissible: {stmt.admissible}]" if stmt.admissible else ""
            lines.append(f"heuristic {stmt.name}({params}){meta}")
        elif isinstance(stmt, PreferStmt):
            meta = f" [ev: {stmt.evidence}]" if stmt.evidence else ""
            lines.append(f"prefer {stmt.name}{meta}")
    return "\n".join(lines) + "\n"
