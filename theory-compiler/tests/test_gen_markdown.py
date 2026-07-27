"""Tests for the Markdown generator (M5)."""
from pathlib import Path

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
    ast = _load_ast("cart_theory.dsl")
    md = generate_markdown(ast)
    # These DSL structural keywords should not appear literally
    for kw in ["word_table:", "events:", "rules:", "goal:", "laws:",
               "object ", "event ", "rule ", "invariant ", "theorem "]:
        assert kw not in md, f"DSL keyword '{kw}' leaked into markdown"


def test_no_dsl_keywords_leaked_peg():
    """No raw DSL keywords appear in the output."""
    ast = _load_ast("peg_theory.dsl")
    md = generate_markdown(ast)
    for kw in ["word_table:", "events:", "rules:", "goal:", "laws:",
               "object ", "event ", "rule ", "invariant ", "theorem "]:
        assert kw not in md, f"DSL keyword '{kw}' leaked into markdown"


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
