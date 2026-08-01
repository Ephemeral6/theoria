"""GAP R2-2 — what an event is allowed to write, and what happens when it is not.

`theoria-arm` filed R2-2 as a DSL expressivity hole: *"the arm can PREDICT the
edge-advance hypothesis and still cannot WRITE IT DOWN in theory.dsl"*, because
a cell that has never varied is sedimented into the board, gets no object
instance, and so no `forall ?p in <Type>` rule can name it
(`theoria-arm/GAPS.md` R2-2; `theoria-arm/runs/20260731T1430Z-A3-level2-carried-
r3/books/theory.dsl`, theorem `i_cannot_manufacture_an_instance_on_a_cell_that_
has_never_changed`).

Measured, it is not an expressivity hole. The v0.3 grammar states the law
correctly the moment the level seats an instance there — same manual, byte for
byte, three levels differing only in seating
(`runs/20260801T1200Z-R2-2-board-cell-expressivity/`). What made it look like
one was this compiler: `recolored(<landmark>, 1)` — the first thing anyone
reaching for a board cell writes — compiled, fired, and changed nothing.

The whole file is that pair of claims held down:

* the positive control, `test_the_grammar_can_say_the_edge_advance*`: unmodified
  v0.3, the arm's own rule shape, burns exactly the right cell;
* the negative controls, `test_*_is_refused`: each malformed spelling is
  *seen* to be refused, by name, in every form that can see it. A check never
  observed saying no has not been shown to check anything.
"""

import pytest

from theory_compiler.generators.gen_markdown import (
    UnrenderableRule, generate_markdown,
)
from theory_compiler.generators.gen_python import generate_python
from theory_compiler.ir import IRError, build_ir
from theory_compiler.parser.theory_parser import parse_theory
from theory_compiler.problem import from_json

# --------------------------------------------------------------------- the world
#
# `theoria-arm`'s row-63 meter, shrunk to one row of eight. The board paints the
# whole bar colour 9; the two rightmost cells have already burned to colour 1
# and so have varied. Cols 0-5 have never varied — board, no instance.
# The world's law: one command, and the cell left of the leftmost burn burns.

BOARD = [[9, 9, 9, 9, 9, 9, 9, 9]]


def level(seated, landmarks=None):
    return from_json({
        "name": "burn-bar",
        "grid": [1, 8],
        "background": 0,
        "board": BOARD,
        "objects": [{"name": "Bar_%d" % c, "type": "Bar", "pos": [0, c],
                     "color": 1 if c >= 6 else 9} for c in seated],
        "landmarks": landmarks or {},
        "arena": [[0, c] for c in range(8)],
    })


HEAD = """semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Bar { pos: Coord, color: Int }
"""

TAIL = """
goal:
  goal count(Bar, color = 1) = 8
"""

EVENTS = """
events:
  event recolored(o, c)

rules:
"""

# The sentence under test, in the arm's own shape. Nothing here is new grammar.
EDGE_ADVANCE = """  rule edge_advance forall ?p in Bar
    when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)
"""


def manual(rules, extra_word_table=""):
    return HEAD + extra_word_table + EVENTS + rules + TAIL


def run_one_key2(text, problem):
    """Compile, execute, and return (row before, row after one `key(2)`)."""
    ns = {}
    exec(compile(generate_python(parse_theory(text), problem),  # noqa: S102
                 "<theory.py>", "exec"), ns)
    s0 = ns["initial_state"]()
    return ns["render"](s0)[0], ns["render"](ns["step"](s0, ("key", 2)))[0], ns


# ------------------------------------------------------- the positive control

def test_the_grammar_can_say_the_edge_advance_when_the_cell_is_seated():
    """R2-2's law, in v0.3 as it stands, predicting exactly the right cell.

    This is the counter-example to R2-2 being a grammar gap, and it is the whole
    finding: the manual is unchanged from the one that fails below. Only the
    level differs, by one instance.
    """
    text = manual(EDGE_ADVANCE)
    before, after, ns = run_one_key2(text, level([5, 6, 7]))
    assert before == [9, 9, 9, 9, 9, 9, 1, 1]
    assert after == [9, 9, 9, 9, 9, 1, 1, 1], "the edge did not advance"
    assert ns["fired"](ns["initial_state"](), ("key", 2)) == ["edge_advance__Bar_5"]


def test_seating_every_cell_gives_the_same_answer_as_seating_the_edge():
    """The law is a law, not a coincidence of which cells carry an instance."""
    text = manual(EDGE_ADVANCE)
    _b1, edge_only, _ = run_one_key2(text, level([5, 6, 7]))
    _b2, all_cells, _ = run_one_key2(text, level(range(8)))
    assert edge_only == all_cells == [9, 9, 9, 9, 9, 1, 1, 1]


def test_the_same_manual_is_silent_when_the_level_seats_only_varied_cells():
    """And the negative half of the same control: it is the *seating* that
    decides, so with the arm's own seating the identical manual says nothing.

    Not a defect of the manual. The rule grounds over the instances the level
    supplies, none of them is the edge, so no rule fires and the frame holds —
    which is exactly the 12-of-47 `theoria-arm` measured.
    """
    text = manual(EDGE_ADVANCE)
    before, after, ns = run_one_key2(text, level([6, 7]))
    assert before == after == [9, 9, 9, 9, 9, 9, 1, 1]
    assert ns["fired"](ns["initial_state"](), ("key", 2)) == []


# ------------------------------------------------------- the negative controls

LANDMARK_TARGET = """  rule edge_burns
    when act=key(2) and colored(edge, 9) then recolored(edge, 1)
"""
CELL_TERM_TARGET = """  rule edge_advance forall ?p in Bar
    when act=key(2) and colored(?p, 1) and colored(leftof(?p), 9) then recolored(leftof(?p), 1)
"""
FIELD_ACCESS_TARGET = """  rule edge_advance forall ?p in Bar
    when act=key(2) and colored(?p, 1) then recolored(?p.pos, 1)
"""


def test_writing_a_landmark_is_refused_by_the_ir():
    """The R2-2 trap. Before this check it compiled, fired, and did nothing.

    `edge` is a `NameRef`, so `WriteSets.of_rule` accepted it; the declaration
    and the compiled effect both said `{edge}`, so `check_backend_agreement`
    accepted it too; the emitted `state.edge_color = 1` landed on a dataclass
    with no such field, succeeded, and was read by nothing.
    """
    text = manual(LANDMARK_TARGET,
                  extra_word_table="  landmark edge  # arc-cell: (0, 5)\n")
    with pytest.raises(IRError) as exc:
        build_ir(parse_theory(text), level([6, 7], {"edge": [0, 5]}))
    assert "landmark" in str(exc.value)
    assert "seat an instance" in str(exc.value)


@pytest.mark.parametrize("form", ["build_ir", "gen_python", "gen_lean"])
def test_writing_a_landmark_is_refused_by_every_ir_driven_form(form):
    """Each entry point separately, because "it goes through `build_ir`" is a
    fact about today's call graph and the refusal is supposed to outlive it."""
    from theory_compiler.generators.gen_lean import generate_lean

    text = manual(LANDMARK_TARGET,
                  extra_word_table="  landmark edge  # arc-cell: (0, 5)\n")
    ast, problem = parse_theory(text), level([6, 7], {"edge": [0, 5]})
    call = {"build_ir": lambda: build_ir(ast, problem),
            "gen_python": lambda: generate_python(ast, problem),
            "gen_lean": lambda: generate_lean(ast, problem)}[form]
    with pytest.raises(IRError):
        call()


def test_writing_a_landmark_is_refused_by_the_prose_form_too():
    """theory.md is allowed to be prose. It is not allowed to be the only form
    that says the manual means something."""
    text = manual(LANDMARK_TARGET,
                  extra_word_table="  landmark edge  # arc-cell: (0, 5)\n")
    with pytest.raises(UnrenderableRule) as exc:
        generate_markdown(parse_theory(text))
    assert "landmark" in str(exc.value)


@pytest.mark.parametrize("rules,what", [
    (CELL_TERM_TARGET, "leftof"),
    (FIELD_ACCESS_TARGET, "pos"),
])
def test_writing_a_cell_term_is_refused_by_the_ir_and_by_the_prose_form(rules,
                                                                       what):
    """A cell term denotes a location, and a location is not a thing a manual
    owns. `gen_python` and `gen_lean` already refused these; `gen_markdown`
    rendered them as *"then leftof(?p)'s colour becomes 1"*.
    """
    text = manual(rules)
    with pytest.raises(IRError):
        build_ir(parse_theory(text), level([6, 7]))
    with pytest.raises(UnrenderableRule):
        generate_markdown(parse_theory(text))
    assert what  # the spelling under test is named in the parametrisation


# ------------------------------------------------- the shortfall, as a number

def test_an_unseated_instance_warns_rather_than_refusing():
    """The case that is NOT the R2-2 trap, kept separate on purpose.

    `theory.dsl` is the domain and travels between levels, so a manual naming an
    object a level does not supply is legal — `a0-cart`'s `press_left` writes
    `Button` and its `no-button` level is entitled to have none. Refusing would
    delete a working level from a checked-in handover package. The effect still
    compiles to an assignment nothing reads, so it is reported, and the report
    is pinned here rather than left to be rediscovered (v0.3 section 5's own
    precedent).
    """
    text = manual("""  rule ghost forall ?p in Bar
    when act=key(2) and colored(?p, 1) then recolored(?p, 1)

  rule absent_writer
    when act=key(3) then recolored(Ghost, 1)
""", extra_word_table="  object Ghost { pos: Coord, color: Int }\n")
    ir = build_ir(parse_theory(text), level([6, 7]))
    hits = [w for w in ir.warnings if "absent_writer" in w and "Ghost" in w]
    assert len(hits) == 1, ir.warnings
    assert "cannot fire here" in hits[0]


def test_the_a0_cart_no_button_level_is_the_real_instance_of_that_warning():
    """The shortfall as it actually occurs, not as a fixture invents it."""
    from pathlib import Path

    repo = Path(__file__).resolve().parents[2]
    manual_path = (repo / "theory-compiler" / "handover_packages" / "a0-cart"
                   / "manual" / "MANUAL.dsl")
    level_path = (repo / "theory-compiler" / "handover_packages" / "a0-cart"
                  / "levels" / "no-button" / "LEVEL.json")
    if not (manual_path.exists() and level_path.exists()):
        pytest.skip("the a0-cart handover package is not in this checkout")
    from theory_compiler.problem import load_problem

    ir = build_ir(parse_theory(manual_path.read_text(encoding="utf-8")),
                  load_problem(str(level_path)))
    named = sorted({w.split("'")[1] for w in ir.warnings
                    if "seats no instance of" in w})
    assert named == ["door_opens_left", "press_left"], ir.warnings
