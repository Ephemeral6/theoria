"""
Tests for theory.dsl parser — covers 素材 A (Cart) and 素材 B (Peg Solitaire).
Verifies parsing + round-trip (parse → print → re-parse → structural equality).
"""

import os
from pathlib import Path

from theory_compiler.parser.theory_parser import parse_theory
from theory_compiler.parser.pretty_printer import print_theory
from theory_compiler.parser.ast_nodes import (
    TheoryAST, WordTable, ObjectDecl, Field,
    EventsSection, RulesSection, GoalSection, LawsSection,
    NameRef, NumberLit, FieldAccess, FuncCall, Comparison, TupleLit,
    GuardAction, GuardPredicate,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _read_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


# ==============================================================
# 素材 A: Cart world
# ==============================================================

class TestCartTheory:
    def setup_method(self):
        self.text = _read_fixture("cart_theory.dsl")
        self.ast = parse_theory(self.text)

    def test_word_table_parsed(self):
        wt = self.ast.word_table
        assert wt is not None
        assert wt.has_board is True
        assert len(wt.objects) == 1
        assert wt.objects[0].name == "Cart"
        assert len(wt.objects[0].fields) == 2
        assert wt.objects[0].fields[0] == Field("pos", "Coord")
        assert wt.objects[0].fields[1] == Field("color", "Int")

    def test_events_parsed(self):
        es = self.ast.events
        assert es is not None
        assert len(es.events) == 1
        ev = es.events[0]
        assert len(ev.alternatives) == 2
        assert ev.alternatives[0].name == "moved"
        assert ev.alternatives[0].params == ["o", "dir"]
        assert ev.alternatives[1].name == "teleported"
        assert ev.alternatives[1].params == ["o", "dest"]

    def test_rules_parsed(self):
        rs = self.ast.rules
        assert rs is not None
        assert len(rs.rules) == 5  # push_up, down, left, right, teleport

        # Check first rule
        r0 = rs.rules[0]
        assert r0.name == "push_up"
        assert r0.meta is not None
        assert r0.meta.evidence == "t1,t2,t3"
        assert r0.meta.coverage == "3/3"

        # Guard should have: act=push(Cart, up) and free(above(Cart))
        assert len(r0.guard.clauses) == 2
        assert isinstance(r0.guard.clauses[0], GuardAction)
        assert r0.guard.clauses[0].action.action_name == "push"

        # Event: moved(Cart, up)
        assert r0.event.name == "moved"

        # Teleport rule
        r4 = rs.rules[4]
        assert r4.name == "teleport"
        assert r4.meta.coverage == "1/1"

    def test_goal_parsed(self):
        gs = self.ast.goal
        assert gs is not None
        # Cart.pos = (0, 0)
        expr = gs.goal.expr
        assert isinstance(expr, Comparison)
        assert expr.op == "="

    def test_laws_parsed(self):
        ls = self.ast.laws
        assert ls is not None
        assert len(ls.invariants) == 1
        inv = ls.invariants[0]
        assert inv.name == "conservation"
        assert inv.op == "="
        assert inv.value == "6"
        assert inv.status == "proven"

    def test_round_trip(self):
        """Parse → print → re-parse: ASTs should be structurally equivalent."""
        printed = print_theory(self.ast)
        ast2 = parse_theory(printed)
        # Compare key structural properties
        assert ast2.word_table.has_board == self.ast.word_table.has_board
        assert len(ast2.word_table.objects) == len(self.ast.word_table.objects)
        assert ast2.word_table.objects[0].name == self.ast.word_table.objects[0].name
        assert len(ast2.events.events) == len(self.ast.events.events)
        assert len(ast2.rules.rules) == len(self.ast.rules.rules)
        for r1, r2 in zip(self.ast.rules.rules, ast2.rules.rules):
            assert r1.name == r2.name
            assert len(r1.guard.clauses) == len(r2.guard.clauses)
            assert r1.event.name == r2.event.name
        assert ast2.laws.invariants[0].name == self.ast.laws.invariants[0].name
        assert ast2.laws.invariants[0].op == self.ast.laws.invariants[0].op
        assert ast2.laws.invariants[0].value == self.ast.laws.invariants[0].value


# ==============================================================
# 素材 B: Peg Solitaire
# ==============================================================

class TestPegTheory:
    def setup_method(self):
        self.text = _read_fixture("peg_theory.dsl")
        self.ast = parse_theory(self.text)

    def test_word_table_parsed(self):
        wt = self.ast.word_table
        assert wt is not None
        assert wt.has_board is True
        assert len(wt.objects) == 1
        assert wt.objects[0].name == "Peg"
        assert wt.objects[0].fields[0] == Field("pos", "Int")
        assert wt.objects[0].fields[1] == Field("alive", "Bool")

    def test_events_parsed(self):
        es = self.ast.events
        assert es is not None
        assert len(es.events) == 1
        ev = es.events[0]
        assert len(ev.alternatives) == 2
        assert ev.alternatives[0].name == "jumped"
        assert ev.alternatives[1].name == "removed"

    def test_rules_parsed(self):
        rs = self.ast.rules
        assert rs is not None
        assert len(rs.rules) == 2  # jump_right, jump_left
        assert rs.rules[0].name == "jump_right"
        assert rs.rules[1].name == "jump_left"

    def test_goal_parsed(self):
        gs = self.ast.goal
        assert gs is not None

    def test_laws_parsed(self):
        ls = self.ast.laws
        assert ls is not None
        assert len(ls.invariants) == 1
        assert ls.invariants[0].name == "pagoda_weight"
        assert ls.invariants[0].op == ">="
        assert ls.invariants[0].value == "4"
        assert len(ls.theorems) == 1
        assert ls.theorems[0].name == "unsolvable"
        assert ls.theorems[0].depends == ["jump_right", "jump_left"]
        assert ls.theorems[0].probe == "passed"

    def test_round_trip(self):
        """Parse → print → re-parse: ASTs should be structurally equivalent."""
        printed = print_theory(self.ast)
        ast2 = parse_theory(printed)
        assert ast2.word_table.objects[0].name == "Peg"
        assert len(ast2.rules.rules) == len(self.ast.rules.rules)
        for r1, r2 in zip(self.ast.rules.rules, ast2.rules.rules):
            assert r1.name == r2.name
        assert ast2.laws.invariants[0].name == self.ast.laws.invariants[0].name
        assert ast2.laws.theorems[0].name == self.ast.laws.theorems[0].name
