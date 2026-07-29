"""E-08 — a counting predicate in a guard, and what it must not quietly become.

The forcing world is `worldgen`'s `t2-lock-fragile`: a gate that opens once k
tokens have been collected, where collecting a token only makes it stop being
drawn. A manual for that world has to be able to say "passable once k are gone",
and the v0.3 guard language could not — `count` existed only inside a `goal:`
clause and only under `=`, and a guard reaching it got
`unknown predicate 'count'`.

Two things are tested here and the second matters more than the first: that the
clause works, and that it stayed **one rung**. A counting predicate is one step
from a quantifier, and the ledger discipline is that each step needs its own
forcing world.
"""

import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")

from theory_compiler.parser.theory_parser import parse_theory          # noqa: E402
from theory_compiler.problem import load_problem                       # noqa: E402
from theory_compiler.generators import gen_python                      # noqa: E402
from theory_compiler.generators.gen_python import (UnsupportedClause,  # noqa: E402
                                                   generate_python)


def _load(theory, problem):
    with open(os.path.join(FIXTURES, theory), encoding="utf-8") as handle:
        ast = parse_theory(handle.read())
    return ast, load_problem(os.path.join(FIXTURES, problem))


def _compiled(theory="countlock_theory.dsl", problem="countlock_problem.json"):
    ast, spec = _load(theory, problem)
    namespace = {}
    exec(compile(generate_python(ast, spec), "<countlock>", "exec"),  # noqa: S102
         namespace)
    return namespace


@pytest.fixture(scope="module")
def world():
    return _compiled()


# =========================================================================
# the clause does what it says
# =========================================================================

def _take(world, state, *names):
    for name in names:
        state = world["step"](state, ("take", name))
    return state


@pytest.mark.parametrize("taken,expected_gate", [
    ((), True),
    (("T1",), True),
    (("T1", "T2"), True),
    (("T1", "T2", "T3"), False),
])
def test_gate_opens_only_at_the_threshold(world, taken, expected_gate):
    """Below, approaching, and at the threshold.

    The boundary is the whole content of the clause: a guard that fired at two
    tokens, or never fired at three, would be a different world and both are
    reachable by an off-by-one in the compiled comparison.
    """
    state = _take(world, world["State"](), *taken)
    after = world["step"](state, ("open", "Gate"))
    assert after.Gate_present is expected_gate


def test_the_count_reads_the_state_not_the_level(world):
    """Taking tokens in a different order reaches the same verdict.

    A count compiled as a constant off the level — which is what the goal
    compiler used to emit for `count(<Type>)` — would pass the threshold test
    above and fail this one.
    """
    for order in (("T3", "T1", "T2"), ("T2", "T3", "T1")):
        state = _take(world, world["State"](), *order)
        assert world["step"](state, ("open", "Gate")).Gate_present is False


def test_count_of_present_instances_respects_vanishing(world):
    """`count(<Type>)` with no condition counts the ones still present.

    It used to compile to a literal `1` per declared instance — a constant, so
    `count(Door)` stayed 1 after the Door vanished. No shipped goal exercised a
    vanish, which is why nothing caught it; a guard does.
    """
    state = _take(world, world["State"](), "T1", "T2")
    assert state.T1_present is False and state.T3_present is True


# =========================================================================
# it stayed one rung
# =========================================================================

_PRELUDE = (
    "word_table:\n"
    "  board\n"
    "  object Agent { pos: Coord }\n"
    "  object Token { pos: Coord, present: Bool }\n"
    # the level fixture is shared, so every mini-manual has to declare the types
    # that level supplies: `check_against_theory` refuses otherwise, and that
    # refusal is not the one under test here
    "  object Gate { pos: Coord, present: Bool }\n"
    "semantics:\n"
    "  frame persist\n"
    "  conflict exclusive\n"
    "  cascade single_frame\n"
    "events:\n"
    "  event vanished(o) writes {o} | stayed(o) writes {}\n"
    "rules:\n"
)
_TAIL = "goal:\n  goal Agent.pos = (0, 0)\n"


def _refuses(guard, match):
    manual = _PRELUDE + ("  rule r\n    when %s then stayed(Agent)\n" % guard) + _TAIL
    ast = parse_theory(manual)
    spec = load_problem(os.path.join(FIXTURES, "countlock_problem.json"))
    with pytest.raises(UnsupportedClause, match=match):
        generate_python(ast, spec)


def test_a_second_condition_is_refused():
    """Two conditions is the first step toward a quantifier and is not taken."""
    _refuses("act=open(Agent) and count(Token, present = false, pos = (0,0)) >= 1",
             "One rung only")


def test_a_condition_that_is_not_an_equality_is_refused():
    _refuses("act=open(Agent) and count(Token, present >= 1) >= 1",
             "must be `<field> = <value>`")


def test_counting_a_type_the_level_does_not_supply_is_refused():
    """A manual counting a type with no instances decides nothing, silently.

    Compiling it to the constant 0 would give a guard that never fires and a
    manual that looks like it has a rule for a case it has no rule for.
    """
    manual = (
        "word_table:\n"
        "  board\n"
        "  object Agent { pos: Coord }\n"
        "  object Token { pos: Coord, present: Bool }\n"
        "  object Gate { pos: Coord, present: Bool }\n"
        "  object Ghost { pos: Coord, present: Bool }\n"
        "semantics:\n  frame persist\n  conflict exclusive\n"
        "  cascade single_frame\n"
        "events:\n  event stayed(o) writes {}\n"
        "rules:\n  rule r\n"
        "    when act=open(Agent) and count(Ghost) >= 1 then stayed(Agent)\n"
        + _TAIL)
    ast = parse_theory(manual)
    spec = load_problem(os.path.join(FIXTURES, "countlock_problem.json"))
    with pytest.raises(UnsupportedClause, match="declares no instance"):
        generate_python(ast, spec)


def test_bare_count_is_not_a_predicate():
    """`count(...)` on its own is an integer, not a truth value.

    Accepting it would make `when act=... and count(Token)` mean "at least one",
    by Python's truthiness rather than by anything the manual says.
    """
    _refuses("act=open(Agent) and count(Token)", "unknown predicate")


# =========================================================================
# the four manuals already in the tree
# =========================================================================

EXISTING = [
    ("cart_theory.dsl", "cart_problem.json"),
    ("peg_theory.dsl", "peg5_problem.json"),
    ("sokoban2_theory.dsl", "sokoban2_match_problem.json"),
    ("sokoban2_x5_theory.dsl", "sokoban2_match_problem.json"),
]


@pytest.mark.parametrize("theory,problem", EXISTING)
def test_existing_manuals_still_compile(theory, problem):
    """No regression on what was already in the tree.

    The widening touched `_value` and the goal compiler, both of which every one
    of these goes through.
    """
    if not os.path.exists(os.path.join(FIXTURES, theory)):
        pytest.skip("%s is not in this tree" % theory)
    ast, spec = _load(theory, problem)
    source = generate_python(ast, spec)
    namespace = {}
    exec(compile(source, "<%s>" % theory, "exec"), namespace)  # noqa: S102
    assert "step" in namespace and "is_goal" in namespace


def test_the_peg_goal_still_counts_the_way_it_did():
    """`count(Peg, alive = true) = 1` is the one shipped goal that counts.

    It is the clause the shared implementation could most plausibly have moved
    under it, so it is checked against the number rather than against itself.
    """
    theory = os.path.join(FIXTURES, "peg_theory.dsl")
    if not os.path.exists(theory):
        pytest.skip("peg fixture is not in this tree")
    with open(theory, encoding="utf-8") as handle:
        ast = parse_theory(handle.read())
    spec = load_problem(os.path.join(FIXTURES, "peg5_problem.json"))
    source = generate_python(ast, spec)
    assert "def is_goal" in source
    namespace = {}
    exec(compile(source, "<peg>", "exec"), namespace)  # noqa: S102
    assert namespace["is_goal"](namespace["State"]()) is False
