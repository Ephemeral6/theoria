"""Tests for the Markdown generator (M5)."""
from pathlib import Path

import pytest

from theory_compiler.generators.gen_markdown import generate_markdown
from theory_compiler.parser.theory_parser import parse_theory

FIXTURES = Path(__file__).parent / "fixtures"


def _load_ast(name):
    text = (FIXTURES / name).read_text(encoding="utf-8")
    return parse_theory(text)


def test_cart_md_deterministic():
    """Same AST renders to byte-identical Markdown on two calls."""
    ast = _load_ast("cart_theory.dsl")
    md1 = generate_markdown(ast)
    md2 = generate_markdown(ast)
    assert md1 == md2
    assert len(md1) > 100  # non-trivial output


def test_peg_md_deterministic():
    """Same AST renders to byte-identical Markdown on two calls."""
    ast = _load_ast("peg_theory.dsl")
    md1 = generate_markdown(ast)
    md2 = generate_markdown(ast)
    assert md1 == md2
    assert len(md1) > 100


def test_no_dsl_keywords_leaked_cart():
    """No raw DSL keywords appear in the output."""
    assert_no_dsl_syntax(generate_markdown(_load_ast("cart_theory.dsl")))


def test_no_dsl_keywords_leaked_peg():
    """No raw DSL keywords appear in the output."""
    assert_no_dsl_syntax(generate_markdown(_load_ast("peg_theory.dsl")))


def test_cart_md_readable():
    """Spot-check that key concepts are rendered in natural language."""
    ast = _load_ast("cart_theory.dsl")
    md = generate_markdown(ast)
    # Should mention the grid/board
    assert "grid" in md.lower() or "playing surface" in md.lower()
    # Should mention Cart
    assert "Cart" in md
    # Should mention winning condition
    assert "Winning Condition" in md or "solved" in md.lower()


def test_peg_md_readable():
    """Spot-check that peg solitaire concepts are rendered."""
    ast = _load_ast("peg_theory.dsl")
    md = generate_markdown(ast)
    assert "Peg" in md
    assert "Known Truths" in md or "Preserved" in md
    # Should render the theorem explanation
    assert "cannot be reduced" in md.lower() or "1 peg" in md.lower()


# Section headers are unambiguous: they cannot occur in English. Declaration
# keywords are only a leak when they *begin a line*, which is what DSL syntax
# looks like. A bare substring test flagged the sentence "if no rule applies to
# something in a turn" -- which is the natural-language rendering doing its job,
# not the DSL showing through. `test_the_leak_check_actually_catches_a_leak`
# below is the positive control that keeps this from being a weakened check.
DSL_HEADERS = ("word_table:", "semantics:", "events:", "rules:", "goal:", "laws:")
DSL_DECLARATIONS = ("object ", "event ", "rule ", "invariant ", "theorem ",
                    "domain ", "landmark ", "weights ", "when ", "forall ")


def assert_no_dsl_syntax(md: str) -> None:
    for header in DSL_HEADERS:
        assert header not in md, f"DSL section header {header!r} leaked"
    for line in md.splitlines():
        stripped = line.lstrip("-* ").strip()
        for kw in DSL_DECLARATIONS:
            assert not stripped.startswith(kw), (
                f"DSL declaration leaked into markdown: {line!r}")


LEAKS = [
    "# World\n\nrule push_up\n",
    "# World\n\nword_table:\n",
    "# World\n\n- invariant cart_unique holds\n",
    "# World\n\nforall ?d in dir\n",
]


@pytest.mark.parametrize("leaked", LEAKS)
def test_the_leak_check_actually_catches_a_leak(leaked):
    """A check that has never been seen to fail is no evidence of anything."""
    with pytest.raises(AssertionError):
        assert_no_dsl_syntax(leaked)


def test_the_leak_check_does_not_flag_ordinary_prose():
    """The rendering is allowed to use the English word "rule"; the point is
    that the document must not *look like* the DSL, not that it may not name
    what the DSL declares."""
    assert_no_dsl_syntax(
        "## How a Turn Works\n\n"
        "If no rule applies to something in a turn, it is exactly as it was.\n")
