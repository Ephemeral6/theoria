"""
theory.pddl generator — converts TheoryAST to PDDL domain + problem files.

Actions are parameterized to objects (not raw coordinates), following the
dsl_grammar_v0.1 contract: click(Object) not click(x,y).

Generates STRIPS-compatible PDDL with :typing.

Repaired 2026-07-31 (C14's census measured 0 of 303 usable actions; root cause
in crosscheck's ROOT_CAUSE.md). The repair holds this backend to the same two
disciplines the other three backends already had:

* **No silent approximation.** Every guard clause and every event either has a
  STRIPS image or raises `UnsupportedClause` naming what it cannot carry. The
  `(and)` empty-effect placeholder and the drop-on-unrecognised guard path are
  gone.
* **The generator may not return a domain its own reader refuses.** The last
  step of `generate_pddl` is `strips.parse_domain` — the exact front end
  `handover.check_pddl` uses — so an undeclared predicate, an unbound variable
  or an empty effect can no longer be shipped, only refused.

Encoding notes (the parts that were previously wrong or absent):

* DSL spatial spellings (`above`/`below`/`leftof`/`rightof`, `toward`) are
  translated through `gen_python`'s `SPATIAL` table to the declared predicate
  names `adjacent-up`/`-down`/`-left`/`-right`. The old code interpolated the
  DSL spelling into the predicate name (`adjacent-above`) and never recognised
  `leftof`/`rightof` at all.
* Direction constants in `act=push(Cart, up)` are **not** parameters. The old
  code emitted `?up - object`; no object of type `object` is ever declared, so
  every such action grounded to zero instances.
* `moved(o, dir)` binds its own destination: if the guard did not already bind
  `?dest`, the event adds it with an `(adjacent-<dir> ?o-pos ?dest)` link.
* `jumped(o, L)` / `teleported(o, L)` resolve the landmark to a
  `(landmark-<L> ?dest)` precondition whose fact the problem half emits from
  the level's `landmarks` table — not a free cell parameter the plan may bind
  anywhere.
* `colored(<cell>, k)` compiles to `(colour-k ?via)` over a rendered-colour
  fact table; `recolored(o, k)` rewrites the colour at the object's cell.
  Colours are mutually exclusive per cell, so the rewrite deletes every other
  tracked colour there.
* `vanished(o)` / `appeared(o)` toggle `(present ?o)` and the freeness of the
  object's cell; position is kept as memory so an `appeared` lands where the
  object stood.
* Rules with **identical guards** fire on the same transition (`cascade
  single_frame`, enforced by `_check_semantics`) and are folded into one
  action, exactly as `cold-start-a0/compile/gen_pddl_a0.py` does for the
  press/door cascade. Compiled separately, the A0 press would falsify the door
  rule's guard and the door could never open in the planning form of a world
  where it does.
* `GuardPredicate.negated` is refused: `:strips` has no negative
  preconditions, and an inverted or dropped negation is a different world.
"""
from ..parser.ast_nodes import (
    TheoryAST, ObjectDecl, RuleDecl,
    Guard, GuardPredicate, GuardAction, ActionMatch,
    FuncCall, NameRef, NumberLit, TupleLit, FieldAccess,
    Comparison, BinOp, GoalSection, GoalExpr,
)
from ..parser.expand import expand_theory
from .gen_python import SPATIAL, UnsupportedClause

DIRECTIONS = ("up", "down", "left", "right")

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

    The returned domain has passed `strips.parse_domain` — this track's own
    STRIPS reader, the one `handover.check_pddl` runs — so every predicate an
    action mentions is declared, every variable is bound, and no effect is
    empty. With a `problem`, the pair has also been grounded and produces at
    least one applicable action. A manual this encoding cannot carry raises
    `UnsupportedClause` instead; a refusal is a result.

    Returns:
        Tuple of (domain_str, problem_str)
    """
    _check_semantics(ast)
    ast = expand_theory(ast)        # ground value-domain schemas (E-02), as
                                    # every other backend gets via `build_ir`
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

    # A form generated is not a form checked (`handover.py`): the generator may
    # not return a domain its own STRIPS reader refuses. `parse_domain` refuses
    # an undeclared predicate, an unbound variable, a wrong arity and an empty
    # effect — the four defect classes C14 counted 303 instances of.
    from .. import strips
    strips.parse_domain(domain)
    if problem is not None:
        task = strips.ground(domain, problem_text)
        if not task.actions:
            raise UnsupportedClause(
                "the domain and the level ground to no applicable action; the "
                "encoding and the board do not meet")
    return domain, problem_text


# ------------------------------------------------------------------ vocabulary

def _obj_types(ast: TheoryAST) -> list:
    if not ast.word_table:
        return []
    return [obj.name.lower() for obj in ast.word_table.objects]


class _Vocabulary:
    """What the rules make the domain say — one scan, read by both halves.

    * `colours` — every literal a `colored(...)` guard tests or a
      `recolored(...)` event writes; each becomes a `(colour-k ?c)` predicate
      and a rendered-colour fact table.
    * `landmarks` — every `jumped`/`teleported` destination; each becomes a
      `(landmark-<name> ?c)` predicate located by the problem half.
    * `has_present` — whether any object vanishes or appears.
    * `movers` — object types some event moves. A mover's position is the
      fluent `(at ...)`; everything else referenced by a rule is **anchored**:
      `frame persist` plus the absence of any moving event makes its position
      a theorem of the manual, so the encoding may state it as the static
      `(anchored ?o ?c)` — which is also what lets `strips.ground` pin the
      parameter instead of enumerating every cell for it.
    * `anchored` — the referenced non-mover types, if any.
    """

    def __init__(self, ast: TheoryAST, obj_types: list):
        self.colours, self.landmarks = set(), set()
        self.has_present = False
        self.movers, referenced = set(), set()
        if not ast.rules:
            self.anchored = set()
            return
        for rule in ast.rules.rules:
            guard = rule.guard
            if guard is not None and hasattr(guard, "clauses"):
                for clause in guard.clauses:
                    if not isinstance(clause, GuardPredicate):
                        continue
                    expr = clause.expr
                    if not isinstance(expr, FuncCall):
                        continue
                    if (expr.name == "colored" and len(expr.args) == 2
                            and isinstance(expr.args[1], NumberLit)):
                        self.colours.add(expr.args[1].value)
                    for term in [expr] + list(expr.args):
                        step = _spatial_step(term, obj_types)
                        if step is not None:
                            referenced.add(step[0].lower())
            event = rule.event
            if not isinstance(event, FuncCall) or not event.args:
                continue
            if isinstance(event.args[0], NameRef):
                referenced.add(event.args[0].name.lower())
            key = (event.name, len(event.args))
            if key == ("recolored", 2) and isinstance(event.args[1], NumberLit):
                self.colours.add(event.args[1].value)
            elif key in (("vanished", 1), ("appeared", 1)):
                self.has_present = True
            elif key in (("moved", 2), ("jumped", 2), ("teleported", 2)):
                if isinstance(event.args[0], NameRef):
                    self.movers.add(event.args[0].name.lower())
                if key != ("moved", 2):
                    dest = event.args[1]
                    if (isinstance(dest, NameRef)
                            and dest.name.lower() not in obj_types
                            and dest.name not in DIRECTIONS):
                        self.landmarks.add(dest.name)
        self.anchored = {t for t in referenced
                         if t in obj_types and t not in self.movers}


def _vocabulary(ast: TheoryAST, obj_types: list) -> _Vocabulary:
    return _Vocabulary(ast, obj_types)


def _landmark_pred(name: str) -> str:
    return "landmark-%s" % name.replace("_", "-")


# ---------------------------------------------------------------------- domain

def _gen_domain(ast: TheoryAST, domain_name: str, w: int, h: int) -> str:
    obj_types = _obj_types(ast)
    vocab = _vocabulary(ast, obj_types)
    colours, landmarks, has_present = (vocab.colours, vocab.landmarks,
                                       vocab.has_present)

    lines = []
    lines.append(f"(define (domain {domain_name})")
    lines.append("  (:requirements :strips :typing)")
    lines.append("")

    # Types
    types = ["cell"] + obj_types
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
    for k in sorted(colours):
        lines.append(f"    (colour-{k} ?c - cell)")
    for lm in sorted(landmarks):
        lines.append(f"    ({_landmark_pred(lm)} ?c - cell)")
    if landmarks:
        # A jump whose mover already stands on the landmark would add and
        # delete the same `(at ...)` atom, which `strips.ground` refuses as
        # ambiguous. `distinct` is the static inequality that prunes that
        # binding; the problem half emits its facts only against landmark
        # cells, the sole pairs any action reads.
        lines.append("    (distinct ?c1 - cell ?c2 - cell)")
    if has_present:
        lines.append("    (present ?o - object)")
    if vocab.anchored:
        # A referenced object no event ever moves stands still by `frame
        # persist`; saying so statically is what lets the grounder pin its
        # position instead of enumerating every cell for it.
        lines.append("    (anchored ?o - object ?c - cell)")
    lines.append("  )")
    lines.append("")

    # Actions — one per *guard*, not one per rule. Rules with identical guards
    # fire on the same transition (`cascade single_frame`), so they are one
    # action with a union effect; compiled separately, a plan could take half
    # a cascade, which no play of the world can do.
    if ast.rules:
        groups, order = {}, []
        for rule in ast.rules.rules:
            key = _guard_signature(rule)
            if key not in groups:
                groups[key] = []
                order.append(key)
            groups[key].append(rule)
        for key in order:
            group = groups[key]
            action_str = _rule_to_action(group[0], group, obj_types, vocab)
            lines.append(action_str)
            lines.append("")

    lines.append(")")
    return "\n".join(lines)


def _guard_signature(rule: RuleDecl):
    """A guard as comparable text, so identical guards are recognisably so.

    The AST nodes are dataclasses, so `repr` is structural equality in text
    form. Same trick as `gen_pddl_a0._guard_key`, generalised to any clause.
    """
    guard = rule.guard
    if guard is None or not hasattr(guard, "clauses"):
        return ("<no-guard>", id(rule))
    parts = []
    for clause in guard.clauses:
        if isinstance(clause, GuardAction):
            parts.append("act=%s(%s)" % (clause.action.action_name,
                                         ",".join(repr(a) for a in clause.action.args)))
        elif isinstance(clause, GuardPredicate):
            negated = "not " if getattr(clause, "negated", False) else ""
            parts.append(negated + repr(clause.expr))
        else:
            parts.append(repr(clause))
    return tuple(sorted(parts))


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


# --------------------------------------------------------------------- problem

def _gen_problem(ast: TheoryAST, domain_name: str, problem_name: str,
                 w: int, h: int, problem=None) -> str:
    obj_types = _obj_types(ast)
    vocab = _vocabulary(ast, obj_types)
    colours, landmarks, has_present = (vocab.colours, vocab.landmarks,
                                       vocab.has_present)

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
    # Position is emitted for absent instances too — it is the memory an
    # `appeared` lands on — but only a *present* instance occupies its cell.
    placed = _instance_names(ast, problem)
    occupied = set()
    for pddl_name, _type_name, cell, present in placed:
        where = cell if cell is not None else (0, 0)
        lines.append(f"    (at {pddl_name} cell-{where[0]}-{where[1]})")
        if present:
            occupied.add(tuple(where))
    if has_present:
        for pddl_name, _type_name, _cell, present in placed:
            if present:
                lines.append(f"    (present {pddl_name})")
    for pddl_name, type_name, cell, _present in placed:
        if type_name in vocab.anchored:
            where = cell if cell is not None else (0, 0)
            lines.append(f"    (anchored {pddl_name} cell-{where[0]}-{where[1]})")

    # Landmark facts. A landmark a rule jumps to must be located by the level;
    # without a level the placeholder omits the fact and the jump grounds to
    # nothing, which is the placeholder being a placeholder.
    if problem is not None:
        for lm in sorted(landmarks):
            cell = problem.landmarks.get(lm)
            if cell is None or len(cell) != 2:
                raise UnsupportedClause(
                    "a rule jumps to landmark %r and problem %r does not "
                    "locate it; the destination would become a free cell "
                    "parameter and the plan could land anywhere"
                    % (lm, problem.name))
            lines.append(f"    ({_landmark_pred(lm)} cell-{cell[0]}-{cell[1]})")
            lm_cell = f"cell-{cell[0]}-{cell[1]}"
            for r in range(h):
                for c in range(w):
                    other = f"cell-{r}-{c}"
                    if other != lm_cell:
                        lines.append(f"    (distinct {other} {lm_cell})")

    # Rendered-colour facts, for the colours the rules actually read or write:
    # the board's own paint, overlaid by every present instance's colour —
    # the same rendering `free` and the executable form use.
    if colours and problem is not None:
        rendered = {}
        for r, row in enumerate(problem.board[:h]):
            for c, colour in enumerate(row[:w]):
                if colour != problem.background:
                    rendered[(r, c)] = colour
        for inst in problem.instances:
            if inst.present and inst.color is not None and len(inst.pos) == 2:
                rendered[tuple(inst.pos)] = inst.color
        for (r, c), colour in sorted(rendered.items()):
            if colour in colours:
                lines.append(f"    (colour-{colour} cell-{r}-{c})")

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


# --------------------------------------------------------------------- actions

def _rule_to_action(rule: RuleDecl, group: list, obj_types: list,
                    vocab: "_Vocabulary") -> str:
    """Convert one guard-group of rules to a PDDL action.

    `group` is every rule sharing this guard, `rule` the first of them: the
    action carries its name, and the others' effects are folded in with a
    comment saying so.
    """
    lines = []
    action_name = rule.name.replace("_", "-")

    params, preconds = _guard_to_pddl(rule.guard, obj_types)

    # The colours this guard itself tests: what a `recolored` in this group
    # overwrites. Deleting only these keeps every colour no rule ever writes
    # static, which the grounder prunes walls and portals with.
    guard_colours = set()
    if rule.guard is not None and hasattr(rule.guard, "clauses"):
        for clause in rule.guard.clauses:
            if (isinstance(clause, GuardPredicate)
                    and isinstance(clause.expr, FuncCall)
                    and clause.expr.name == "colored"
                    and len(clause.expr.args) == 2
                    and isinstance(clause.expr.args[1], NumberLit)):
                guard_colours.add(clause.expr.args[1].value)

    effects = []
    for member in group:
        for lit in _event_to_pddl(member.event, params, preconds, obj_types,
                                  guard_colours):
            if lit in effects:
                continue
            complement = ("(not %s)" % lit if not lit.startswith("(not ")
                          else lit[5:-1])
            if complement in effects:
                raise UnsupportedClause(
                    "rules %s share a guard and write conflicting effects "
                    "%r / %r; they cannot be one transition, so the manual "
                    "and this encoding disagree"
                    % ([m.name for m in group], lit, complement))
            effects.append(lit)

    if not effects:
        # Every rule in the group writes nothing (`stayed`). A no-op action
        # adds no reachability; say so instead of emitting an empty effect.
        return ("  ;; %s: writes nothing by declaration (`stayed`, X-3); "
                "no PDDL action emitted" % ", ".join(m.name for m in group))

    _add_position_params(params, preconds, obj_types, vocab.movers)

    # Build parameter string
    param_parts = []
    for pname, ptype in params.items():
        param_parts.append(f"?{pname} - {ptype}")
    param_str = " ".join(param_parts)

    lines.append(f"  (:action {action_name}")
    lines.append(f"    :parameters ({param_str})")
    lines.append(f"    :precondition (and")
    for prec in preconds:
        lines.append(f"      {prec}")
    lines.append(f"    )")
    lines.append(f"    :effect (and")
    for eff in effects:
        lines.append(f"      {eff}")
    lines.append(f"    )")
    lines.append(f"  )")
    for member in group[1:]:
        lines.append("  ;; rule %s shares this guard and is folded into %s "
                     "(cascade single_frame)" % (member.name, action_name))
    return "\n".join(lines)


def _add_position_params(params: dict, preconds: list, obj_types: list,
                         movers: set) -> None:
    """Every object parameter stands somewhere: add `?<o>-pos` and its literal.

    A mover's position is the fluent `(at ...)`. A non-mover's is the static
    `(anchored ...)` — same cell, but stated as the theorem it is (`frame
    persist`, no moving event), so the grounder pins the parameter instead of
    enumerating 81 cells for it.
    """
    at_literals = []
    for pname in list(params.keys()):
        if params[pname] in obj_types:
            pos_name = f"{pname}-pos"
            if pos_name not in params:
                params[pos_name] = "cell"
            pred = "at" if params[pname] in movers else "anchored"
            lit = f"({pred} ?{pname} ?{pos_name})"
            if lit not in preconds:
                at_literals.append(lit)
    preconds[:0] = at_literals


def _require_object(name: str, params: dict, obj_types: list) -> str:
    """The lower-case parameter for a declared object, created on first use."""
    pname = name.lower()
    if pname not in params:
        if pname not in obj_types:
            raise UnsupportedClause(
                "%r is not a declared object type; this backend can only "
                "parameterise over the word table's objects" % (name,))
        params[pname] = pname
    return pname


def _fresh(params: dict, stem: str) -> str:
    if stem not in params:
        return stem
    n = 2
    while f"{stem}{n}" in params:
        n += 1
    return f"{stem}{n}"


def _refuse_count(expr) -> None:
    """A counting guard has no STRIPS encoding in this subset — say so.

    E-08 added `count(<Type>, <field> = <value>) >= k` to the guard language.
    `:strips :typing` has no numeric fluent and no aggregate, so the condition
    can only be encoded by inventing a chain of `collected-1`/`collected-2`/…
    predicates and threading them through every rule that consumes a token.
    That encoding may be worth building; **silently dropping the clause is not
    the same thing**, and dropping is what this backend did — it emitted a
    domain whose gate opens unconditionally and reported success.
    """
    stack = [expr]
    while stack:
        node = stack.pop()
        if isinstance(node, FuncCall) and node.name == "count":
            raise UnsupportedClause(
                "a counting guard (`count(...)`) has no encoding in this "
                "STRIPS subset: `:strips :typing` has no numeric fluent, and "
                "the condition would have to become a chain of threshold "
                "predicates threaded through every rule that changes the "
                "count. Refusing rather than dropping the precondition — a "
                "dropped one yields a domain whose gate opens unconditionally "
                "(expressivity ledger E-08).")
        for attr in ("left", "right", "expr"):
            child = getattr(node, attr, None)
            if child is not None:
                stack.append(child)
        stack.extend(getattr(node, "args", []) or [])


# ---------------------------------------------------------------------- guards

def _guard_to_pddl(guard, obj_types: list) -> tuple:
    """Convert guard to (params_dict, precondition_list).

    Position parameters (`?<o>-pos` and their `(at ...)` literals) are added
    after the event compiler has run — see `_add_position_params` — because
    events may introduce objects the guard never names (`recolored(Button, 8)`
    under a guard about the Cart).
    """
    params = {}
    preconds = []

    if guard is None:
        return params, preconds

    if not hasattr(guard, 'clauses'):
        return params, preconds

    for clause in guard.clauses:
        if isinstance(clause, GuardAction):
            am = clause.action
            for arg in am.args:
                if isinstance(arg, NameRef):
                    pname = arg.name.lower()
                    if pname in obj_types:
                        params[pname] = pname
                    elif pname in DIRECTIONS:
                        # The direction names *which* player action fires this
                        # rule, and it is already in the action's name.
                        # Parameterising it produced `?up - object`, a
                        # parameter no problem ever declares an instance for,
                        # so every such action grounded to zero (C14,
                        # REPAIR_DISTANCE.md correction 2).
                        continue
                    else:
                        raise UnsupportedClause(
                            "act=%s(... %s ...): neither a declared object "
                            "type nor a direction; this backend cannot type "
                            "the parameter" % (am.action_name, arg.name))
                else:
                    raise UnsupportedClause(
                        "act=%s(...): argument %r is not a name; a "
                        "type-quantified schema must be grounded before this "
                        "backend can read it" % (am.action_name, arg))
        elif isinstance(clause, GuardPredicate):
            if getattr(clause, "negated", False):
                raise UnsupportedClause(
                    "negated guard `not %r`: `:strips` has no negative "
                    "preconditions. Refusing rather than dropping the clause "
                    "— and rather than inverting it, which is what fixing "
                    "the spelling table without reading `negated` would "
                    "silently have done" % (clause.expr,))
            expr = clause.expr
            _refuse_count(expr)
            _extract_pred_pddl(expr, params, preconds, obj_types)
        else:
            raise UnsupportedClause(
                "guard clause %r has no STRIPS image in this subset"
                % (clause,))

    return params, preconds


def _spatial_step(expr, obj_types: list):
    """(object_name, pddl_direction, steps) for a spatial cell term.

    Recognises the one-step spellings `above/below/left/right/leftof/rightof`
    and the explicit-direction forms `toward(o, d)` / `ahead(o, d)` (one step)
    and `beyond(o, d)` (two). Returns None for anything else; the caller
    decides whether that is a refusal.
    """
    if not isinstance(expr, FuncCall):
        return None
    name = expr.name
    if (name in ("above", "below", "left", "right", "leftof", "rightof")
            and len(expr.args) == 1):
        obj = expr.args[0]
        if isinstance(obj, NameRef):
            return obj.name, _pddl_direction(name), 1
        return None
    if name in ("toward", "ahead", "beyond") and len(expr.args) == 2:
        obj, direction = expr.args
        if isinstance(obj, NameRef) and isinstance(direction, NameRef):
            steps = 2 if name == "beyond" else 1
            return obj.name, _pddl_direction(direction.name), steps
    return None


def _pddl_direction(name: str) -> str:
    """DSL spelling -> the direction the predicate block declares.

    The old code interpolated the DSL spelling straight into the predicate
    name — `adjacent-above` against a block declaring `adjacent-up` — which
    was C14's 45-action undeclared-predicate class. `gen_python` has carried
    the translation table since v0.2; this backend now reads the same one.
    """
    direction = SPATIAL.get(name, name)
    if direction not in DIRECTIONS:
        raise UnsupportedClause("no such direction: %r" % (name,))
    return direction


def _steps_to(params: dict, preconds: list, pname: str, direction: str,
              steps: int) -> str:
    """Chain `steps` adjacency hops from `?<pname>-pos`; return the source var
    of the final hop (the caller appends the final adjacency itself)."""
    src = f"?{pname}-pos"
    for _hop in range(steps - 1):
        mid = _fresh(params, "mid")
        params[mid] = "cell"
        preconds.append(f"(adjacent-{direction} {src} ?{mid})")
        src = f"?{mid}"
    return src


def _extract_pred_pddl(expr, params: dict, preconds: list, obj_types: list):
    """Compile one guard predicate into parameters and precondition literals.

    Everything unrecognised **raises**. The old else-less fall-through
    silently dropped `colored(...)`, field comparisons and arithmetic, which
    is a domain whose gate opens where the manual says it does not (D-TC-031).
    """
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
            step = _spatial_step(inner, obj_types)
            if step is None:
                raise UnsupportedClause(
                    "free(%r): this cell term has no STRIPS image in this "
                    "subset. Refusing rather than dropping the precondition."
                    % (inner,))
            obj_name, direction, steps = step
            pname = _require_object(obj_name, params, obj_types)
            src = _steps_to(params, preconds, pname, direction, steps)
            dest = _fresh(params, "dest")
            params[dest] = "cell"
            preconds.append(f"(adjacent-{direction} {src} ?{dest})")
            preconds.append(f"(free ?{dest})")
        elif expr.name == "colored" and len(expr.args) == 2:
            cell_expr, colour = expr.args
            if not isinstance(colour, NumberLit):
                raise UnsupportedClause(
                    "colored(<cell>, <colour>): the colour must be a literal "
                    "for a STRIPS fact table; got %r" % (colour,))
            step = _spatial_step(cell_expr, obj_types)
            if step is None:
                raise UnsupportedClause(
                    "colored(%r, %d): this cell term has no STRIPS image in "
                    "this subset. Refusing rather than dropping the "
                    "precondition." % (cell_expr, colour.value))
            obj_name, direction, steps = step
            pname = _require_object(obj_name, params, obj_types)
            src = _steps_to(params, preconds, pname, direction, steps)
            via = _fresh(params, "via")
            params[via] = "cell"
            preconds.append(f"(adjacent-{direction} {src} ?{via})")
            preconds.append(f"(colour-{colour.value} ?{via})")
        elif _spatial_step(expr, obj_types) is not None:
            # Spatial reference without free — boundary check
            obj_name, direction, _steps = _spatial_step(expr, obj_types)
            pname = _require_object(obj_name, params, obj_types)
            preconds.append(f"(boundary-{direction} ?{pname}-pos)")
        else:
            raise UnsupportedClause(
                "guard predicate %r has no STRIPS image in this subset. "
                "Refusing rather than dropping the precondition (D-TC-031)."
                % (expr,))
    elif isinstance(expr, Comparison):
        # e.g., above(Cart) = wall
        step = _spatial_step(expr.left, obj_types)
        if (step is not None and isinstance(expr.right, NameRef)
                and expr.right.name == "wall"):
            obj_name, direction, _steps = step
            pname = _require_object(obj_name, params, obj_types)
            preconds.append(f"(boundary-{direction} ?{pname}-pos)")
        else:
            raise UnsupportedClause(
                "guard comparison %r has no STRIPS image in this subset. "
                "Refusing rather than dropping the precondition (D-TC-031)."
                % (expr,))
    else:
        raise UnsupportedClause(
            "guard expression %r has no STRIPS image in this subset. "
            "Refusing rather than dropping the precondition (D-TC-031)."
            % (expr,))


# ---------------------------------------------------------------------- events

def _event_to_pddl(event, params: dict, preconds: list, obj_types: list,
                   guard_colours: set) -> list:
    """Compile an event into effect literals; may add parameters and
    preconditions (a destination cell, a landmark binding, a `(present ...)`
    for a vanish).

    Dispatch is on (name, arity), the same table `gen_python._effect` and
    `gen_markdown` carry. Anything outside it **raises** — the `(and)`
    placeholder this function used to emit was an action that does nothing,
    shipped as if it did something (C14's 190 empty effects).
    """
    if not isinstance(event, FuncCall) or not event.args:
        raise UnsupportedClause(f"event must be a call on an object: {event!r}")
    if not isinstance(event.args[0], NameRef):
        raise UnsupportedClause("an event's first argument must be an object")
    key = (event.name, len(event.args))
    a = event.args
    effects = []

    if key == ("moved", 2):
        if not isinstance(a[1], NameRef):
            raise UnsupportedClause("moved(o, dir): dir must be a direction name")
        direction = _pddl_direction(a[1].name)
        obj = _require_object(a[0].name, params, obj_types)
        pos = f"{obj}-pos"
        # The guard usually bound `?dest` through `free(<dir>(o))`; when it
        # did not — a rule that moves without testing freeness — the event
        # binds its own destination. Either way the destination is the
        # adjacent cell in the event's direction, never an unbound variable
        # (C14's 57-action undeclared-`?dest` class).
        if "dest" not in params:
            params["dest"] = "cell"
        adj = f"(adjacent-{direction} ?{pos} ?dest)"
        if adj not in preconds:
            preconds.append(adj)
        effects.append(f"(not (at ?{obj} ?{pos}))")
        effects.append(f"(at ?{obj} ?dest)")
        effects.append("(not (free ?dest))")
        effects.append(f"(free ?{pos})")
    elif key in (("jumped", 2), ("teleported", 2)):
        dest_arg = a[1]
        if (not isinstance(dest_arg, NameRef)
                or dest_arg.name.lower() in obj_types
                or dest_arg.name in DIRECTIONS):
            raise UnsupportedClause(
                f"{event.name}(o, <landmark>) needs a declared landmark as its "
                "destination; a bare coordinate would be level data wearing a "
                "domain rule's clothes (E-04)")
        obj = _require_object(a[0].name, params, obj_types)
        pos = f"{obj}-pos"
        dest = _fresh(params, "dest")
        params[dest] = "cell"
        # The landmark resolves to a fact the problem half emits — not a free
        # cell parameter the plan may bind anywhere. `distinct` statically
        # prunes the self-jump binding, whose add/delete of one `(at ...)`
        # atom `strips.ground` refuses.
        preconds.append(f"({_landmark_pred(dest_arg.name)} ?{dest})")
        preconds.append(f"(distinct ?{pos} ?{dest})")
        effects.append(f"(not (at ?{obj} ?{pos}))")
        effects.append(f"(at ?{obj} ?{dest})")
        effects.append(f"(not (free ?{dest}))")
        effects.append(f"(free ?{pos})")
    elif key == ("recolored", 2):
        if not isinstance(a[1], NumberLit):
            raise UnsupportedClause("recolored(o, <int>)")
        colour = a[1].value
        obj = _require_object(a[0].name, params, obj_types)
        pos = f"{obj}-pos"
        effects.append(f"(colour-{colour} ?{pos})")
        # A recolour overwrites the colour the guard of this same transition
        # tested — delete exactly that, and the latch (`door_latch`) latches:
        # the guard's `(colour-7 ?via)` is gone the moment the press fires.
        # Colours no rule writes are never deleted, so they stay static and
        # the grounder prunes with them (walls, portals).
        for other in sorted(guard_colours - {colour}):
            effects.append(f"(not (colour-{other} ?{pos}))")
    elif key == ("vanished", 1):
        obj = _require_object(a[0].name, params, obj_types)
        pos = f"{obj}-pos"
        present = f"(present ?{obj})"
        if present not in preconds:
            preconds.append(present)
        effects.append(f"(not (present ?{obj}))")
        effects.append(f"(free ?{pos})")
    elif key == ("appeared", 1):
        obj = _require_object(a[0].name, params, obj_types)
        pos = f"{obj}-pos"
        effects.append(f"(present ?{obj})")
        effects.append(f"(not (free ?{pos}))")
    elif key == ("stayed", 1):
        # Writes nothing, and says so (X-3). The caller drops the action.
        return []
    else:
        raise UnsupportedClause(
            f"no STRIPS encoding for event {event.name}/{len(event.args)}. "
            "This backend implements moved/2, jumped/2, teleported/2, "
            "recolored/2, vanished/1, appeared/1, stayed/1; `gen_python` "
            "additionally implements jumped/3, slid/3 and removed/1, whose "
            "STRIPS images are still owed (expressivity ledger).")
    return effects


# ------------------------------------------------------------------------ goal

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
