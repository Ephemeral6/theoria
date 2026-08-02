"""C15 — the executable form of a refusal.

`CONTRACTS/dsl_grammar_v0.4.md` refuses to extend the grammar with a form that
lets a rule's **effect** reach a cell no instance stands on. C15's acceptance
line says a written refusal is a contract and silence is not — and that the
refusal has to be *demonstrated* rather than asserted:

    必须先证明今天真的说不出来。一条测试，把 `edge_advance` 形状的规则喂给现语法，
    断言它编译失败**并给出那个失败理由**——「无法命名」要是演示出来的，不是断言
    出来的。

So this file is the clause, executable, and it is permanent: under v0.4's verdict
(b) it never turns green by being fixed. It goes red only if the refusal is lost.

It is deliberately not a copy of `test_write_targets.py`, which pins the
2026-08-01 repair in the three IR-driven forms. What is new here is the part
v0.4 had to be able to claim and nobody had measured:

* **§2 the fourth form.** All four co-derived forms refuse, measured on a world
  `gen_pddl` actually compiles. The previous run predicted the opposite
  (`runs/20260801T1200Z-.../FINDING.md:207-211`, *"a manual that reaches
  `gen_pddl` and writes a landmark would still be compiled by it"*); it is wrong,
  and `runs/20260802T085557Z-C15-unnameable-cell-verdict/PDDL_LEAK.json` is the
  measurement.
* **§3 the pin.** `gen_pddl` agrees by its own route — it never calls `build_ir`,
  so it never runs `_check_write_targets`. Convergent, not derived, and until
  this file nothing held it there.
* **§4 read yes, write no.** The asymmetry the refusal rests on: naming a board
  cell in a *guard* is legal today, and only the *effect* target is refused. If
  this went red the refusal would be far broader than v0.4 claims.
* **§5 allocation.** The remaining escape route — an event that brings a thing
  into existence at a cell — closed by measurement rather than by argument.
"""

import os

import pytest

from theory_compiler.generators.gen_lean import generate_lean
from theory_compiler.generators.gen_markdown import (
    UnrenderableRule, generate_markdown,
)
from theory_compiler.generators.gen_pddl import generate_pddl
from theory_compiler.generators.gen_python import UnsupportedClause, generate_python
from theory_compiler.ir import IRError, build_ir
from theory_compiler.parser.theory_parser import parse_theory
from theory_compiler.problem import from_json, load_problem

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")

# ------------------------------------------------------------------ the bar world
#
# `theoria-arm`'s row-63 meter shrunk to one row of eight, as in
# `test_write_targets.py`: the board paints the bar colour 9, the two rightmost
# cells have burned to colour 1 and so have varied, cols 0-5 have never varied
# and are therefore board with no instance on them. The law is the arm's — one
# command and the cell left of the leftmost burn burns. Its next victim, col 5,
# is a board cell, and that is the whole of GAP R2-2.

BAR_BOARD = [[9, 9, 9, 9, 9, 9, 9, 9]]


def bar_level(seated, landmarks=None):
    return from_json({
        "name": "burn-bar",
        "grid": [1, 8],
        "background": 0,
        "board": BAR_BOARD,
        "objects": [{"name": "Bar_%d" % c, "type": "Bar", "pos": [0, c],
                     "color": 1 if c >= 6 else 9} for c in seated],
        "landmarks": landmarks or {},
        "arena": [[0, c] for c in range(8)],
    })


BAR_HEAD = """semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Bar { pos: Coord, color: Int }
"""
BAR_EVENTS = """
events:
  event recolored(o, c)

rules:
"""
BAR_TAIL = """
goal:
  goal count(Bar, color = 1) = 8
"""
LANDMARK_DECL = "  landmark edge  # arc-cell: (0, 5)\n"


def bar_manual(rules, extra_word_table=""):
    return BAR_HEAD + extra_word_table + BAR_EVENTS + rules + BAR_TAIL


# The law, in the arm's own shape. Nothing here is new grammar. It can only ever
# name a cell the level seats an instance on.
EDGE_ADVANCE_SEATED = """  rule edge_advance forall ?p in Bar
    when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)
"""
# The same law, aimed at the frontier cell. These are the only two spellings that
# reach a cell with no instance on it, and both are refused.
EDGE_ADVANCE_VIA_LANDMARK = """  rule edge_burns
    when act=key(2) and colored(edge, 9) then recolored(edge, 1)
"""
EDGE_ADVANCE_VIA_CELL_TERM = """  rule edge_advance forall ?p in Bar
    when act=key(2) and colored(?p, 1) and colored(leftof(?p), 9) then recolored(leftof(?p), 1)
"""
# Reading the same board cell, writing a seated instance. Legal — §4.
EDGE_LANDMARK_IN_GUARD = """  rule edge_advance forall ?p in Bar
    when act=key(2) and colored(edge, 9) and colored(?p, 1) then recolored(?p, 1)
"""


# ----------------------------------------------------------------- the cart world
#
# The bar world cannot answer anything about the fourth form: `gen_pddl` refuses
# every manual in it, including the working one, because `colored(<cell>, n)` has
# no STRIPS image in this subset. That refusal lands on the arm's *good* shape
# exactly as hard as on the bad ones, so it is not evidence about R2-2 — the
# 2026-08-01 run says so too, and it is right.
#
# The checked-in `cart` fixture is the world where the question is answerable:
# all four forms compile it unedited, and it declares a `landmark origin`.

_EVENT_OLD = "  event moved(o, dir) | teleported(o, dest)"
_EVENT_NEW = ("  event moved(o, dir) | teleported(o, dest)"
              " | recolored(o, c) | appeared(o)")
_EXTRA_RULE = """
  rule paint_the_landmark [ev: t7 cov: 1/1]
    when act=push(Cart, down) and above(Cart) = wall then %s
"""


def cart_manual(effect=None):
    with open(os.path.join(FIXTURES, "cart_theory.dsl"), encoding="utf-8") as fh:
        base = fh.read()
    if effect is None:
        return base
    return (base.replace(_EVENT_OLD, _EVENT_NEW)
                .replace("\ngoal:", _EXTRA_RULE % effect + "\ngoal:"))


def cart_level():
    return load_problem(os.path.join(FIXTURES, "cart_problem.json"))


def compile_with(form, text, problem):
    """Run one co-derived form. Returns None, or raises that form's refusal."""
    ast = parse_theory(text)
    if form == "build_ir":
        build_ir(ast, problem)
    elif form == "gen_python":
        generate_python(ast, problem)
    elif form == "gen_lean":
        generate_lean(ast, problem)
    elif form == "gen_markdown":
        generate_markdown(ast)
    elif form == "gen_pddl":
        generate_pddl(ast, "cart-instance", 3, 2, problem=problem)
    else:  # pragma: no cover -- a typo in a parametrise list, not a world fact
        raise AssertionError(form)


# ================================================================ §1 the negative
# sample C15 asks for: prove that today it really cannot be said, and show the
# reason rather than asserting it.

@pytest.mark.parametrize("form", ["build_ir", "gen_python", "gen_lean"])
@pytest.mark.parametrize("spelling,seated,landmarks,reason", [
    ("landmark", [6, 7], {"edge": [0, 5]}, "landmark"),
    ("cell_term", [6, 7], None, "not an object name"),
])
def test_the_edge_advance_law_is_refused_when_it_reaches_the_unseated_cell(
        form, spelling, seated, landmarks, reason):
    """GAP R2-2's sentence, aimed at the cell it is actually about, refused.

    Both spellings are the arm's law — the same physics as the seated shape in
    §6 — differing only in that the effect target is a cell rather than an
    instance. Parametrised over the entry point rather than over the input
    because "it all goes through `build_ir`" is a fact about today's call graph
    and the refusal is meant to outlive it.
    """
    rules = (EDGE_ADVANCE_VIA_LANDMARK if spelling == "landmark"
             else EDGE_ADVANCE_VIA_CELL_TERM)
    extra = LANDMARK_DECL if spelling == "landmark" else ""
    text = bar_manual(rules, extra_word_table=extra)
    with pytest.raises(IRError) as exc:
        compile_with(form, text, bar_level(seated, landmarks))
    assert reason in str(exc.value)
    # The refusal must name the repair, not merely say no (v0.3's standing rule).
    assert "seat an instance" in str(exc.value) or "stand on it" in str(exc.value)


def test_the_prose_form_refuses_it_too_and_says_why():
    """`theory.md` is the form a human reads and the only one producible with no
    level, so a refusal it does not carry is a refusal the reader never meets."""
    text = bar_manual(EDGE_ADVANCE_VIA_LANDMARK, extra_word_table=LANDMARK_DECL)
    with pytest.raises(UnrenderableRule) as exc:
        generate_markdown(parse_theory(text))
    assert "landmark" in str(exc.value)
    assert "a cell, not an object" in str(exc.value)


# ================================================================ §2 the fourth form

def test_the_cart_world_compiles_in_all_four_forms_unedited():
    """The control without which §2 proves nothing.

    A form that refuses everything is not enforcing anything. This pins that all
    four forms accept this world before a cell is written into it, so the
    refusals below are about the edit and not about the world.
    """
    text, problem = cart_manual(), cart_level()
    for form in ("gen_python", "gen_lean", "gen_markdown", "gen_pddl"):
        compile_with(form, text, problem)  # must not raise


@pytest.mark.parametrize("effect", [
    "recolored(origin, 1)",              # a landmark: a declared cell
    "vanished(origin)",                  # ... reached through a different event
    "recolored(toward(Cart, up), 1)",    # a cell term
])
@pytest.mark.parametrize(
    "form,refusal",
    [("gen_python", IRError), ("gen_lean", IRError),
     ("gen_markdown", UnrenderableRule), ("gen_pddl", UnsupportedClause)])
def test_every_one_of_the_four_forms_refuses_a_written_cell(form, refusal, effect):
    """All four co-derived forms, on a world all four otherwise compile.

    This is the measurement `runs/20260801T1200Z-.../FINDING.md:207-211`
    predicted would fail. It does not: `gen_pddl` refuses as well. Four forms
    that disagree about whether a manual means something is the defect class
    that produced R2-2 in the first place.
    """
    with pytest.raises(refusal):
        compile_with(form, cart_manual(effect), cart_level())


# ================================================================ §3 the pin

@pytest.mark.parametrize("effect,reason", [
    ("recolored(origin, 1)", "is not a declared object type"),
    ("recolored(toward(Cart, up), 1)", "first argument must be an object"),
])
def test_gen_pddl_refuses_by_its_own_route_and_this_is_what_pins_it(effect, reason):
    """`gen_pddl` agrees with the other three for a reason of its own.

    It does not call `build_ir`, so it never runs `_check_write_targets`; it
    arrives at the same verdict through PDDL's typing discipline — only word
    table objects can be parameterised, and an event's first argument must be
    one. The agreement is therefore **convergent, not derived**, and a
    `gen_pddl` that one day parameterised over landmarks would lose it silently
    while the other three still refused.

    `gen_pddl` is deliberately not modified — the 2026-07-31 repair is not worth
    risking for a check that is already passing. Asserting its two exact reasons
    is the cheap alternative: it costs nothing today and goes red the moment the
    fourth form stops agreeing.
    """
    with pytest.raises(UnsupportedClause) as exc:
        compile_with("gen_pddl", cart_manual(effect), cart_level())
    assert reason in str(exc.value)


# ================================================================ §4 read/write

@pytest.mark.parametrize("form", ["build_ir", "gen_python", "gen_markdown"])
def test_reading_a_board_cell_in_a_guard_is_legal(form):
    """The asymmetry the whole refusal rests on: **read yes, write no.**

    v0.4 refuses a cell as an effect *target*. It does not refuse talking about
    board cells, and this is the test that keeps the refusal from being read
    that broadly: the same `edge` landmark, in the guard, with a seated instance
    in the effect, compiles. This is also what r3's thirteen panel rules already
    do with `spawn_probe`.

    `gen_pddl` is absent from the list on purpose and not from oversight: its
    STRIPS subset has no image for `colored(<cell>, n)` at all and refuses this
    world wholesale, including the working manual. That is v0.3 §5's declared,
    pre-existing shortfall for a whole world class, not a fact about R2-2 — so
    quoting it either way here would be quoting noise.
    """
    text = bar_manual(EDGE_LANDMARK_IN_GUARD, extra_word_table=LANDMARK_DECL)
    compile_with(form, text, bar_level([5, 6, 7], {"edge": [0, 5]}))


# ================================================================ §5 allocation

@pytest.mark.parametrize(
    "form,refusal",
    [("gen_python", IRError), ("gen_lean", IRError),
     ("gen_markdown", UnrenderableRule), ("gen_pddl", UnsupportedClause)])
def test_no_event_can_allocate_an_instance_onto_a_cell(form, refusal):
    """The last escape route, closed by measurement.

    If the objection to writing a board cell is "nothing stands there", the
    obvious reply is an event that makes something stand there. `appeared/1` is
    in v0.3 §3's default table and writes `{o}`, so `appeared(origin)` is the
    shortest spelling of it. It is refused by all four forms for the same reason
    every other spelling is: `origin` is a cell, and the argument must be an
    object. `appeared` flips an instance's `present` observation; it does not
    bring an instance into being. Nothing in the language allocates.

    This matters to v0.4's argument rather than to its text: it is why *"seat an
    instance"* is a level's job and cannot be smuggled into the manual.
    """
    with pytest.raises(refusal):
        compile_with(form, cart_manual("appeared(origin)"), cart_level())


# ================================================================ §6 the control
# that makes the refusal honest rather than merely restrictive.

def test_the_law_is_statable_the_moment_the_cell_is_seated():
    """The refusal is about seating, not about the law.

    Unmodified v0.3, the arm's own rule shape, the same bytes refused above when
    aimed at a cell — and here it compiles, fires, and burns exactly the cell
    R2-2 says cannot be reached. A refusal without this control would be
    evidence that the grammar is too small; with it, it is evidence that the
    level seated the wrong cells, which is C15's whole verdict.
    """
    text = bar_manual(EDGE_ADVANCE_SEATED)
    ns = {}
    exec(compile(generate_python(parse_theory(text), bar_level([5, 6, 7])),  # noqa: S102
                 "<theory.py>", "exec"), ns)
    s0 = ns["initial_state"]()
    assert ns["render"](s0)[0] == [9, 9, 9, 9, 9, 9, 1, 1]
    assert ns["render"](ns["step"](s0, ("key", 2)))[0] == [9, 9, 9, 9, 9, 1, 1, 1]
    assert ns["fired"](s0, ("key", 2)) == ["edge_advance__Bar_5"]
