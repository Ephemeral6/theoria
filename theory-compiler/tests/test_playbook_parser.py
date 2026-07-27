"""
Tests for playbook.dsl parser — positive (素材 B) and negative (violation sample).
"""

from pathlib import Path
import pytest

from theory_compiler.parser.playbook_parser import parse_playbook, PlaybookParseError
from theory_compiler.parser.pretty_printer import print_playbook
from theory_compiler.parser.ast_nodes import (
    OrderStmt, PruneStmt, HeuristicStmt, PreferStmt,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _read_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class TestPlaybookPositive:
    """素材 B playbook: should parse successfully."""

    def setup_method(self):
        self.text = _read_fixture("peg_playbook.dsl")
        self.ast = parse_playbook(self.text)

    def test_all_four_types_parsed(self):
        stmts = self.ast.statements
        assert len(stmts) == 4
        assert isinstance(stmts[0], OrderStmt)
        assert isinstance(stmts[1], PruneStmt)
        assert isinstance(stmts[2], HeuristicStmt)
        assert isinstance(stmts[3], PreferStmt)

    def test_order(self):
        s = self.ast.statements[0]
        assert s.landmark == "center_first"
        assert s.proof == "none"

    def test_prune(self):
        s = self.ast.statements[1]
        assert "isolated_peg" in s.condition
        assert s.proof == "lean"

    def test_heuristic(self):
        s = self.ast.statements[2]
        assert s.name == "peg_count"
        assert s.params == ["board"]
        assert s.admissible == "none"

    def test_prefer(self):
        s = self.ast.statements[3]
        assert s.name == "edge_jumps_last"
        assert s.evidence == "3/5"

    def test_round_trip(self):
        """Parse → print → re-parse: structurally equivalent."""
        printed = print_playbook(self.ast)
        ast2 = parse_playbook(printed)
        assert len(ast2.statements) == len(self.ast.statements)
        for s1, s2 in zip(self.ast.statements, ast2.statements):
            assert type(s1) == type(s2)
            if isinstance(s1, OrderStmt):
                assert s1.landmark == s2.landmark
            elif isinstance(s1, PruneStmt):
                assert s1.condition == s2.condition
            elif isinstance(s1, HeuristicStmt):
                assert s1.name == s2.name
                assert s1.params == s2.params
            elif isinstance(s1, PreferStmt):
                assert s1.name == s2.name
                assert s1.evidence == s2.evidence


class TestPlaybookNegative:
    """Violation sample: must be REJECTED by the parser."""

    def test_violation_rejected(self):
        text = _read_fixture("playbook_violation.dsl")
        with pytest.raises(PlaybookParseError) as exc_info:
            parse_playbook(text)
        # Should mention anti-cheat or literal action sequence
        assert "action sequence" in str(exc_info.value).lower() or \
               "anti-cheat" in str(exc_info.value).lower()

    def test_inline_solution_rejected(self):
        """Inline solution: keyword triggers anti-cheat."""
        text = 'solution: UP, DOWN, LEFT, RIGHT\n'
        with pytest.raises(PlaybookParseError):
            parse_playbook(text)

    def test_comma_separated_moves_rejected(self):
        """Comma-separated direction list triggers anti-cheat."""
        text = 'prefer fast [ev: 1/1]\njump(0,right), jump(3,left), jump(0,right)\n'
        with pytest.raises(PlaybookParseError):
            parse_playbook(text)
