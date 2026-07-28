"""Tests for the PDDL generator (M6)."""
import re
from pathlib import Path

from theory_compiler.generators.gen_pddl import generate_pddl
from theory_compiler.parser.theory_parser import parse_theory

FIXTURES = Path(__file__).parent / "fixtures"


def _load_ast(name):
    text = (FIXTURES / name).read_text(encoding="utf-8")
    return parse_theory(text)


def _check_pddl_syntax(text: str) -> list:
    """Basic PDDL syntax validator: balanced parens, required sections."""
    errors = []
    # Check balanced parentheses
    depth = 0
    for i, ch in enumerate(text):
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth < 0:
                errors.append(f"Unbalanced ')' at position {i}")
                return errors
    if depth != 0:
        errors.append(f"Unbalanced parentheses: {depth} unclosed '('")
    return errors


def test_cart_pddl_domain_syntax():
    """Generated PDDL domain is syntactically valid."""
    ast = _load_ast("cart_theory.dsl")
    domain, problem = generate_pddl(ast, problem_name="cart-instance")
    errors = _check_pddl_syntax(domain)
    assert errors == [], f"Domain syntax errors: {errors}"
    # Must contain define and domain
    assert "(define (domain" in domain
    assert ":action" in domain


def test_cart_pddl_problem_syntax():
    """Generated PDDL problem is syntactically valid."""
    ast = _load_ast("cart_theory.dsl")
    domain, problem = generate_pddl(ast, problem_name="cart-instance")
    errors = _check_pddl_syntax(problem)
    assert errors == [], f"Problem syntax errors: {errors}"
    assert "(define (problem" in problem
    assert ":init" in problem
    assert ":goal" in problem


def test_cart_pddl_actions_parameterized():
    """Actions use object parameters, not raw coordinates."""
    ast = _load_ast("cart_theory.dsl")
    domain, problem = generate_pddl(ast, problem_name="cart-instance")
    # Should not contain bare coordinate patterns like (at 1 2)
    # Actions should reference object-typed parameters
    assert ":parameters" in domain
    # No numeric coordinate literals in action preconditions
    action_section = domain[domain.index(":action"):]
    # Coordinates should be represented as objects (cell-0-0 etc), not numbers
    assert not re.search(r'\(at \d+ \d+\)', action_section), \
        "Actions use raw coordinates instead of object parameters"


def test_cart_pddl_domain_structure():
    """Domain has expected PDDL structure."""
    ast = _load_ast("cart_theory.dsl")
    domain, problem = generate_pddl(ast, problem_name="cart-instance")
    # Required PDDL keywords
    assert ":predicates" in domain
    assert ":types" in domain or "- object" in domain


def test_cart_pddl_problem_has_objects():
    """Problem declares objects and initial state."""
    ast = _load_ast("cart_theory.dsl")
    domain, problem = generate_pddl(ast, problem_name="cart-instance")
    assert ":objects" in problem
    assert ":domain" in problem


def test_cart_pddl_goal_present():
    """Problem has a goal condition derived from the DSL goal."""
    ast = _load_ast("cart_theory.dsl")
    domain, problem = generate_pddl(ast, problem_name="cart-instance")
    # Goal should reference Cart's position
    assert "cart" in problem.lower() or "Cart" in problem


# ------------------------------------- the semantics values this backend has

def test_the_pddl_backend_refuses_semantics_it_does_not_implement():
    """`fd_adapter`'s rule: outside the supported subset is an error, never a
    silent approximation.

    `gen_python` has carried this guard since `semantics:` landed, and
    `gen_lean` inherits it by building the predictor first. This backend reads
    only the AST, so it had none — a manual declaring `frame reset` or
    `cascade multi_frame` got a STRIPS encoding of a *different* world, with
    the declared value printed nowhere. That is the hazard the `semantics:`
    section exists to close, reappearing one layer below it.
    """
    import pytest
    from theory_compiler.generators.gen_pddl import generate_pddl
    from theory_compiler.generators.gen_python import UnsupportedClause
    from theory_compiler.parser.theory_parser import parse_theory
    from pathlib import Path

    source = (Path(__file__).parent / "fixtures" / "cart_theory.dsl").read_text(
        encoding="utf-8")
    generate_pddl(parse_theory(source))          # the supported combination

    for old, new, word in (("frame persist", "frame reset", "frame persist"),
                           ("cascade single_frame", "cascade multi_frame",
                            "cascade single_frame")):
        ast = parse_theory(source.replace(old, new))
        with pytest.raises(UnsupportedClause) as exc:
            generate_pddl(ast)
        assert word in str(exc.value)
