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
    """A boolean guard clause. Raises on anything unrecognised."""
    # The parser swallows `not <pred>` into a NameRef holding the whole text.
    if _node("NameRef", node):
        text = _name_of(node).strip()
        if text.startswith("not "):
            return "(not %s)" % _compile_text(text[4:].strip())
        raise UncompilableTheory("bare name in a guard: %r" % text)

    if _node("FuncCall", node):
        if node.name == "free":
            if len(node.args) != 1:
                raise UncompilableTheory("free takes one cell")
            return "_free(state, %s)" % _compile_cell(node.args[0])
        raise UncompilableTheory("unknown predicate %r" % node.name)

    if _node("Comparison", node):
        left, right = node.left, node.right
        negated = False
        if _node("NameRef", left) and _name_of(left).startswith("not "):
            negated = True
            left = _reparse_field(_name_of(left)[4:].strip())
        if node.op != "=":
            raise UncompilableTheory("unsupported comparison %r" % node.op)
        expr = "(%s == %s)" % (_compile_cell(left), _compile_cell(right))
        return "(not %s)" % expr if negated else expr

    raise UncompilableTheory("unsupported guard clause: %r" % (node,))


class _Field:
    def __init__(self, obj: str, field_name: str):
        self.obj = obj
        self.field_name = field_name


def _reparse_field(text: str) -> Any:
    if "." not in text:
        raise UncompilableTheory("expected <Object>.<field>, got %r" % text)
    obj, field = text.split(".", 1)
    node = _Field(obj.strip(), field.strip())
    node.__class__.__name__ = "FieldAccess"
    return node


def _compile_text(text: str) -> str:
    """Compile a predicate the parser handed back as raw text."""
    text = text.strip()
    if text.startswith("free(") and text.endswith(")"):
        inner = text[5:-1].strip()
        for name, steps in (("ahead", 1), ("beyond", 2)):
            prefix = name + "("
            if inner.startswith(prefix) and inner.endswith(")"):
                args = inner[len(prefix):-1].split(",")
                if len(args) != 2:
                    raise UncompilableTheory("%s takes (object, dir)" % name)
                return "_free(state, _step_from(state.%s, direction, %d))" % (
                    args[0].strip().lower(), steps
                )
        raise UncompilableTheory("unsupported argument to free: %r" % inner)
    raise UncompilableTheory("cannot compile predicate text %r" % text)


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
    """Apply one action. Exactly one rule must fire (constraint 9)."""
    fired = []
    for name, rule in RULES:
        trial = replace(state)
        if rule(trial, direction):
            fired.append((name, trial))
    if len(fired) != 1:
        outcomes = {(s.player, s.box) for _, s in fired}
        if len(outcomes) != 1:
            raise RuntimeError(
                "ambiguous successor for %%s: %%r" %% (direction, [n for n, _ in fired])
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
                # v0.2 moved negation out of the expression and onto the clause
                # (`GuardPredicate.negated`). A generator that reads only `.expr`
                # compiles `not free(x)` as `free(x)` -- silently, to a different
                # world. That is the very failure GENERATOR_REPORT.md indicts
                # gen_python for, and it happened here the moment the parser
                # changed under us. Unknown *attributes* are as dangerous as
                # unknown nodes, so the flag is read explicitly and its absence
                # (v0.1 parsers) falls back to the old in-expression form.
                compiled = _compile_predicate(clause.expr)
                if getattr(clause, "negated", False):
                    compiled = "(not %s)" % compiled
                conditions.append(compiled)
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
