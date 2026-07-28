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


def generate_markdown(ast: TheoryAST, ir=None) -> str:
    """Generate a human-readable Markdown document from a TheoryAST.

    `ir` is optional and adds nothing the AST already says; it carries the
    *resolved* weight vectors and their provenance (`WorldIR.weights` /
    `weight_sources`). Without it a manual that declares `weights w` and proves
    `pagoda(w) <= 0` renders a document naming a potential it cannot show — the
    numbers exist, in a certificate, and only the Lean backend ever saw them.
    Passing the IR is what makes `theory.md` a form of the *same* fact rather
    than a summary of it (E-05, and the hand-copying E-06 set out to remove).

    Output is byte-identical to the previous behaviour when `ir` is omitted.
    """
    sections = []

    sections.append("# World Description\n")

    # Word table
    if ast.word_table:
        sections.append(_render_word_table(ast.word_table))

    # How a turn works (E-03). The frame axiom is the most important semantic
    # fact about `step`, and theory.md is the form a human actually reads —
    # leaving it out here would put the axiom back in the same blind spot the
    # `semantics:` section exists to close.
    if ast.semantics:
        sections.append(_render_semantics(ast.semantics))

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

    if ir is not None and getattr(ir, "weights", None):
        sections.append(_render_weights(ir))

    return "\n".join(sections) + "\n"


def _render_weights(ir) -> str:
    """The numbers behind a named potential, and who solved for them.

    The provenance line is not decoration. `source: lp_potential` in the manual
    says an engine derived the weights rather than the author; a reader of
    `theory.md` alone could not check that, and "an engine solved for these"
    is precisely the claim A1 turns on.
    """
    lines = ["## The Numbers Behind the Named Quantities\n"]
    for name in sorted(ir.weights):
        vector = ir.weights[name]
        source = ir.weight_sources.get(name, "unstated")
        lines.append("- **%s**: %s" % (_name_to_natural(name),
                                       ", ".join(str(v) for v in vector)))
        lines.append("  (one value per position, in order; from %s)" % source)
    lines.append("")
    return "\n".join(lines)


def _render_semantics(sem) -> str:
    """Three closed value sets, three sentences. A lookup, not a paraphrase.

    No model is in this path and none may be: Theoria 1.8's "不过 LLM，不许润色".
    A generated rendering that varied run to run would stop being a rendering of
    the manual and start being a second opinion about it.
    """
    lines = ["## How a Turn Works\n"]
    lines.append(
        "If no rule applies to something in a turn, it is exactly as it was.\n"
        if sem.frame == "persist" else
        "If no rule applies to something in a turn, it returns to how it "
        "started.\n")
    lines.append(
        "At most one rule may apply to any one thing in any one turn; the "
        "rules are written so that this cannot fail.\n"
        if sem.conflict == "exclusive" else
        "If several rules apply to one thing, the earlier one in this order "
        "wins: " + " then ".join(sem.priority) + ".\n")
    lines.append(
        "One move produces one new situation. Every rule reads the situation "
        "as it was before the move, and all of their effects happen "
        "together.\n"
        if sem.cascade == "single_frame" else
        "One move may produce a run of situations, each rule reacting to the "
        "one before it, until nothing more changes.\n")
    return "\n".join(lines)


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
    # A rule that binds `?d in direction` is unreadable without the domain it
    # binds over, and a landmark is the manual's own flag that a name in its
    # clauses is supplied from outside. Neither was rendered, so the human form
    # named things the human form never introduced.
    if getattr(wt, "domains", None):
        lines.append("These names each stand for a fixed set of values:\n")
        for dom in wt.domains:
            members = ", ".join(f"`{m}`" for m in dom.values)
            lines.append(f"- **{dom.name}**: one of {members}.")
        lines.append("")
    if getattr(wt, "landmarks", None):
        lines.append("These names appear in the rules and are **not** fixed by "
                     "this description — each individual level says which cell "
                     "each one is:\n")
        for lm in wt.landmarks:
            lines.append(f"- **{lm.name}**")
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

        # A schema rule stands for one rule per member of the domain it binds
        # over. Without this the reader meets `?d` with nothing saying what it
        # ranges over, and the rule looks like it mentions a name nobody
        # declared.
        binding = ""
        bindings = getattr(rule, "bindings", None) or {}
        if bindings:
            binding = " — for every %s" % " and every ".join(
                "?%s in %s" % (var, domain)
                for var, domain in sorted(bindings.items()))

        lines.append(f"- **{_name_to_natural(rule.name)}**{confidence}{binding}: "
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
        text = _expr_to_natural(clause.expr)
        # `negated` used to be read by nobody here, and a guard written
        # `not free(ahead(Player, ?d))` rendered as "ahead is free" — the
        # opposite of the manual, in the form a human reader is handed. The
        # wording is deliberately blunt rather than idiomatic: negating each
        # phrasing in place ("is free" -> "is not free", "the pos of Box is X"
        # -> "the pos of Box is not X") needs a rule per phrasing, and the one
        # that gets missed reads as an assertion of what it denies.
        if getattr(clause, "negated", False):
            return "it is **not** the case that %s" % text
        return text
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
    elif type(expr).__name__ == "VarRef":
        # A `forall ?d in direction` variable. With no branch here it fell to
        # `str(expr)` and the human form of every schema rule read
        # "moved(Player, VarRef(name='d'))" — a repr, in the document whose
        # entire job is to be readable.
        return "?%s" % expr.name
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

    # v0.3, ledger X-5. `free(<obj>.pos)` excludes the object from its own
    # occupancy test, so the plain wording — "Box.pos is free (unoccupied)" —
    # would tell a human reader the opposite of what the clause means, about a
    # cell the Box is standing on. The human form is one of the four
    # co-derived forms; it is allowed to be prose and not allowed to be wrong.
    if name == "free" and len(fc.args) == 1:
        inner = fc.args[0]
        holder = None
        if isinstance(inner, FieldAccess) and inner.field_name == "pos":
            holder = _name_to_natural(inner.obj)
        elif isinstance(inner, NameRef):
            holder = _name_to_natural(inner.name)
        if holder is not None:
            return ("the cell %s stands on is a legal empty one (on the board, "
                    "not a wall, nothing but %s there)" % (holder, holder))

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
