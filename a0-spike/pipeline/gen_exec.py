"""theory.dsl -> executable Python, for the A0 subset.

"预测无侧门": the only prediction machine is the executable form compiled from
the manual. certify must replay history through *this*, not through the miner's
in-memory rule objects, or it is grading the engine rather than the theory.

This is a stopgap. The theory-compiler track owns the real generator; its
`gen_python` cannot yet compile the A0 manual, and the way it fails is the reason
this exists (see the report in `../GENERATOR_REPORT.md`): a guard it does not
understand becomes `True`, and an event it does not understand becomes `pass`.
The generated module then walks the player off the board and reports no error.

The rule here is the opposite one, and it is the only thing that makes a
generated predictor trustworthy:

    **anything this compiler does not understand is a hard error.**

Never `True`, never `pass`. A theory that cannot be compiled is a finding, not a
silently weakened simulation.
"""

import os
import sys
from typing import Any, Dict, List, Sequence, Tuple

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "theory-compiler", "src"))

from theory_compiler.parser.theory_parser import parse_theory   # noqa: E402


class UncompilableTheory(Exception):
    """The manual uses something this generator cannot express -- refuse loudly."""


# ---------------------------------------------------------------- semantics

# What this generator actually implements, as opposed to what it accepts.
#
# `persist` is the frame axiom the RULE_TEMPLATE encodes: a rule mutates the
# fields its event names and leaves the rest of `state` alone, so an object no
# firing rule mentions carries through unchanged. `exclusive` is what STEP_TEMPLATE
# encodes: it evaluates every rule against the pre-state and **raises** if more
# than one fires, so the declaration is enforced at run time rather than merely
# assumed. `single_frame` is what `step` encodes: one call, one successor, every
# guard read against the pre-state.
#
# The other branch of each is *parseable* and unimplemented. Compiling one of
# those to this encoding is the defect `CONTRACTS/dsl_grammar_v0.2.md` revision
# item 10 records against `gen_pddl`: the manual states the semantic fact and the
# compiler ignores it, emitting a STRIPS encoding of `persist` + `single_frame`
# "without a word of complaint". This generator's standing rule is the opposite
# one -- never `True`, never `pass` -- so an unimplemented value is a hard error,
# named, and never a silent approximation. That is `fd_adapter`'s rule applied
# here, and v0.2 §semantics requires it of *every* backend.
IMPLEMENTED_SEMANTICS = {
    "frame": {"persist"},
    "conflict": {"exclusive"},
    "cascade": {"single_frame"},
}


def _check_semantics(theory: Any) -> None:
    """Refuse a declared value this generator does not implement."""
    semantics = getattr(theory, "semantics", None)
    if semantics is None:
        raise UncompilableTheory(
            "the manual carries no `semantics:` section, or this parser is too "
            "old to surface one. Under dsl_grammar v0.2 the frame axiom, the "
            "conflict policy and the cascade shape are mandatory facts about "
            "the world; compiling without them picks a world by accident."
        )
    for statement, implemented in sorted(IMPLEMENTED_SEMANTICS.items()):
        declared = getattr(semantics, statement, None)
        if declared not in implemented:
            raise UncompilableTheory(
                "manual declares `%s %s`; this generator implements only %s. "
                "Refusing rather than emitting an encoding of a world the "
                "manual did not declare (dsl_grammar v0.2, section `semantics`)."
                % (statement, declared, " | ".join(sorted(implemented)))
            )


# --------------------------------------------------------------- expressions

def _node(kind: str, node: Any) -> bool:
    return type(node).__name__ == kind


def _name_of(node: Any) -> str:
    return getattr(node, "name", "")


def _compile_cell(node: Any) -> str:
    """A cell-valued expression: `ahead(O, dir)`, `beyond(O, dir)`, `O.pos`."""
    if _node("FuncCall", node):
        name = node.name
        if name in ("ahead", "beyond"):
            if len(node.args) != 2:
                raise UncompilableTheory("%s takes (object, dir)" % name)
            obj = _name_of(node.args[0]).lower()
            steps = 1 if name == "ahead" else 2
            return "_step_from(state.%s, direction, %d)" % (obj, steps)
        raise UncompilableTheory("unknown cell function %r" % name)
    if _node("FieldAccess", node):
        if node.field_name != "pos":
            raise UncompilableTheory("unknown field %r" % node.field_name)
        return "state.%s" % node.obj.lower()
    raise UncompilableTheory("not a cell expression: %r" % (node,))


def _compile_predicate(node: Any) -> str:
    """A boolean guard clause, **positive**. Raises on anything unrecognised.

    Negation is not handled here. Under dsl_grammar v0.2 it is a property of the
    enclosing `GuardPredicate` (`negated`, ledger E-01), not of the expression,
    and `_compile_clause` is the only place allowed to read it. Folding it back
    in here would give two places that can each think the other did it.
    """
    if _node("NameRef", node):
        raise UncompilableTheory("bare name in a guard: %r" % _name_of(node))

    if _node("FuncCall", node):
        if node.name == "free":
            if len(node.args) != 1:
                raise UncompilableTheory("free takes one cell")
            return "_free(state, %s)" % _compile_cell(node.args[0])
        raise UncompilableTheory("unknown predicate %r" % node.name)

    if _node("Comparison", node):
        if node.op != "=":
            raise UncompilableTheory("unsupported comparison %r" % node.op)
        return "(%s == %s)" % (_compile_cell(node.left), _compile_cell(node.right))

    raise UncompilableTheory("unsupported guard clause: %r" % (node,))


def _compile_clause(clause: Any) -> str:
    """A `GuardPredicate`, negation included.

    The negation lives on the clause under v0.2 (`not <predicate>`, E-01,
    revision item 2). Under v0.1 the parser folded it into a `NameRef` holding
    the text `"not free(...)"`, and this generator read only `clause.expr`.
    When the parser moved, nothing here broke loudly: the negation simply
    stopped arriving, and every `not` in the manual compiled to its own
    opposite. `blocked_wall` became "the way ahead is clear **and** the box is
    there" -- an unsatisfiable guard where the manual had written the exact
    complement.

    That is this module's own rule violated (`never True, never pass`), so the
    absence of the attribute is a hard error rather than a default of False: a
    parser too old to carry the negation must stop the build, not quietly
    compile a different world.
    """
    if not hasattr(clause, "negated"):
        raise UncompilableTheory(
            "guard clause carries no `negated` flag -- this is a pre-v0.2 "
            "parser, whose negations this generator would silently drop. "
            "Refusing rather than compiling a different world."
        )
    text = _compile_predicate(clause.expr)
    return "(not %s)" % text if clause.negated else text


# ------------------------------------------------------------------- effects

def _compile_effect(node: Any) -> List[str]:
    """An event, as statements mutating `state`.

    `slid(Box, dir)` is compound on purpose: the box travels two cells and the
    pusher takes the cell it left. The frozen grammar gives a rule one event
    (`when <guard> then <event>`), while a push visibly does two things, so the
    compound is named in the manual's own event vocabulary. That is a real limit
    of the v1 event language and is recorded in the expressiveness ledger.
    """
    if not _node("FuncCall", node):
        raise UncompilableTheory("effect must be an event call: %r" % (node,))
    obj = _name_of(node.args[0]).lower() if node.args else ""
    if node.name == "moved":
        return ["state.%s = _step_from(state.%s, direction, 1)" % (obj, obj)]
    if node.name == "stayed":
        return ["pass  # nothing happens"]
    if node.name == "slid":
        return [
            "pusher = state.player",
            "state.%s = _step_from(state.%s, direction, 2)" % (obj, obj),
            "state.player = _step_from(pusher, direction, 1)",
        ]
    raise UncompilableTheory("unknown event %r" % node.name)


# ----------------------------------------------------------------- generator

PRELUDE = '''"""Auto-generated from theory.dsl by a0-spike/pipeline/gen_exec.py.

Do not edit. The manual is the source; this is one of its forms.
"""

from dataclasses import dataclass, replace
from typing import List, Optional, Tuple

GRID_HEIGHT = %(height)d
GRID_WIDTH = %(width)d
WALLS = frozenset(%(walls)r)

DELTA = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}

PLAYER_COLOR = %(player_color)d
BOX_COLOR = %(box_color)d
WALL_COLOR = %(wall_color)d


@dataclass
class State:
    player: Tuple[int, int]
    box: Tuple[int, int]

    def render(self) -> List[List[int]]:
        """Full-frame responsibility: every cell is accounted for."""
        grid = [[0] * GRID_WIDTH for _ in range(GRID_HEIGHT)]
        for (r, c) in WALLS:
            grid[r][c] = WALL_COLOR
        grid[self.box[0]][self.box[1]] = BOX_COLOR
        grid[self.player[0]][self.player[1]] = PLAYER_COLOR
        return grid


def _step_from(cell, direction, times):
    dr, dc = DELTA[direction]
    return (cell[0] + dr * times, cell[1] + dc * times)


def _on_board(cell):
    return 0 <= cell[0] < GRID_HEIGHT and 0 <= cell[1] < GRID_WIDTH


def _free(state, cell):
    return _on_board(cell) and cell not in WALLS and cell != state.box
'''

RULE_TEMPLATE = '''
def _rule_%(name)s(state, direction):
    """%(name)s -- compiled from theory.dsl"""
    if not (%(guard)s):
        return False
%(effect)s
    return True
'''

STEP_TEMPLATE = '''
RULES = [%(names)s]


def step(state, direction):
    """Apply one action. Exactly one rule must fire (constraint 9).

    `semantics: conflict exclusive` says **at most one rule per object per
    transition**, and `frame persist` plus a total rule set says at least one.
    So the check is on the number of rules that fired, not on the number of
    distinct successors they produced. An earlier version compared outcomes and
    let two rules through whenever they happened to agree -- which reads like
    enforcement, passes every test while the guards really are disjoint, and
    stops being true the moment a rule is added. Two rules firing is a violation
    of the declared semantics whether or not they agree about the answer.
    """
    fired = []
    for name, rule in RULES:
        trial = replace(state)
        if rule(trial, direction):
            fired.append((name, trial))
    if len(fired) > 1:
        raise RuntimeError(
            "conflict exclusive violated for %%s: %%r fired together"
            %% (direction, [n for n, _ in fired])
        )
    if not fired:
        raise RuntimeError(
            "no rule fired for %%s in %%r -- the rule set is not total, so the "
            "manual determines no successor here" %% (direction, state)
        )
    return fired[0][1]


def simulate(initial, actions):
    states = [initial]
    current = initial
    for action in actions:
        current = step(current, action)
        states.append(current)
    return states
'''


def generate(dsl_text: str, height: int, width: int, walls: Sequence[Tuple[int, int]],
             player_color: int = 2, box_color: int = 4, wall_color: int = 8) -> str:
    theory = parse_theory(dsl_text)
    _check_semantics(theory)
    parts = [PRELUDE % {
        "height": height, "width": width, "walls": sorted(tuple(w) for w in walls),
        "player_color": player_color, "box_color": box_color, "wall_color": wall_color,
    }]

    names: List[str] = []
    for rule in theory.rules.rules:
        conditions: List[str] = []
        for clause in rule.guard.clauses:
            if _node("GuardAction", clause):
                continue                    # every A0 action is a directional move
            if _node("GuardPredicate", clause):
                conditions.append(_compile_clause(clause))
            else:
                raise UncompilableTheory("unsupported clause %r" % (clause,))
        guard = " and ".join(conditions) if conditions else "True"
        effect = "\n".join("    " + line for line in _compile_effect(rule.event))
        parts.append(RULE_TEMPLATE % {"name": rule.name, "guard": guard, "effect": effect})
        names.append(rule.name)

    parts.append(STEP_TEMPLATE % {
        "names": ", ".join('("%s", _rule_%s)' % (n, n) for n in names)
    })
    return "".join(parts)


def compile_module(dsl_text: str, height: int, width: int,
                   walls: Sequence[Tuple[int, int]], out_path: str = None) -> Dict[str, Any]:
    """Generate, optionally write, and load the executable form."""
    source = generate(dsl_text, height, width, walls)
    if out_path:
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        with open(out_path, "w", encoding="utf-8", newline="") as fh:
            fh.write(source)
    namespace: Dict[str, Any] = {}
    exec(compile(source, out_path or "<theory.py>", "exec"), namespace)
    namespace["__source__"] = source
    return namespace
