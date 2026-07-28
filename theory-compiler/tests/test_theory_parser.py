"""
Tests for theory.dsl parser — covers 素材 A (Cart) and 素材 B (Peg Solitaire).
Verifies parsing + round-trip (parse → print → re-parse → structural equality).
"""

import os
from pathlib import Path

import pytest

from theory_compiler.parser.theory_parser import parse_theory, ParseError
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
        # E-02: the four pushes are now one schema over `dir`, plus teleport.
        assert len(rs.rules) == 2
        assert rs.rules[0].name == "push"
        assert rs.rules[0].bindings == {"d": "dir"}

        r0 = rs.rules[0]
        # The lifted rule carries the evidence the engine actually mined,
        # instead of four rules each claiming a slice of it (E-02).
        assert r0.meta.coverage == "10/10"
        assert len(r0.guard.clauses) == 2
        assert isinstance(r0.guard.clauses[0], GuardAction)
        assert r0.guard.clauses[0].action.action_name == "push"
        assert r0.event.name == "moved"

        assert rs.rules[1].name == "teleport"
        assert rs.rules[1].meta.coverage == "1/1"

    def test_expansion_reproduces_the_hand_written_rules(self):
        """E-02. The schema must be a drop-in replacement: same names, same
        guards, same events as the four rules it replaces."""
        from theory_compiler.parser.expand import expand_theory
        ground = expand_theory(self.ast).rules.rules
        assert [r.name for r in ground] == [
            "push_up", "push_down", "push_left", "push_right", "teleport"]
        up = ground[0]
        assert up.bindings == {}
        assert up.guard.clauses[0].action.args[1].name == "up"
        assert up.event.args[1].name == "up"

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
        # E-07: `pos` carries the `unique` modifier, which is what makes this
        # manual entail its own `conflict exclusive`.
        assert wt.objects[0].fields[0] == Field("pos", "Int", unique=True)
        assert wt.objects[0].fields[1] == Field("alive", "Bool")
        assert wt.objects[0].fields[1].unique is False

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
        assert ls.invariants[0].name == "pagoda_potential"
        assert ls.invariants[0].expr_text == "pagoda(w)"
        assert ls.invariants[0].op == "<="
        assert ls.invariants[0].value == "0"
        # E-05: provenance is what separates A1 from the M8 rehearsal.
        assert ls.invariants[0].source == "lp_potential"
        assert len(ls.theorems) == 1
        assert ls.theorems[0].name == "unsolvable"
        assert ls.theorems[0].depends == ["jump_right", "jump_left"]
        assert ls.theorems[0].probe == "passed"

    def test_round_trip(self):
        """Parse → print → re-parse: ASTs should be structurally equivalent."""
        printed = print_theory(self.ast)
        ast2 = parse_theory(printed)
        assert ast2.word_table.objects[0].name == "Peg"
        # E-07. This assertion is the whole reason to compare fields and not
        # just names: the printer used to emit `pos: Int`, so a round trip
        # produced a manual that no longer entailed its own `conflict
        # exclusive` — and looked completely normal.
        assert ast2.word_table.objects[0].fields == self.ast.word_table.objects[0].fields
        assert len(ast2.rules.rules) == len(self.ast.rules.rules)
        for r1, r2 in zip(self.ast.rules.rules, ast2.rules.rules):
            assert r1.name == r2.name
        assert ast2.laws.invariants[0].name == self.ast.laws.invariants[0].name
        assert ast2.laws.theorems[0].name == self.ast.laws.theorems[0].name


class TestNestedParensInEventArgs:
    """D-A0-013 — the argument list used to be matched with `([^)]*)`, which
    stops at the *first* close paren. A nested call or a tuple argument in a
    rule's `then` clause parsed its second argument as a truncated name and
    raised nothing, so the AST was silently wrong. These pin both halves: the
    well-formed nesting now parses, and the malformed nesting now raises.
    """

    SEMANTICS = ("semantics:\n  frame persist\n  conflict exclusive\n"
                 "  cascade single_frame\n\n")

    def _rule(self, when_then: str):
        return parse_theory(
            self.SEMANTICS
            + "rules:\n  rule r [ev: t1 cov: 1/1]\n    when %s\n" % when_then
        )

    def test_tuple_argument_survives(self):
        ast = self._rule("act=push(Cart, down) then jumped(Cart, (1, 1))")
        event = ast.rules.rules[0].event
        assert event.name == "jumped"
        assert len(event.args) == 2
        assert isinstance(event.args[0], NameRef)
        assert event.args[0].name == "Cart"
        assert isinstance(event.args[1], TupleLit)
        assert [e.value for e in event.args[1].elements] == [1, 1]

    def test_nested_call_argument_survives(self):
        ast = self._rule("act=push(Cart, left) then recolored(colorof(Button), 8)")
        event = ast.rules.rules[0].event
        assert len(event.args) == 2
        assert isinstance(event.args[0], FuncCall)
        assert event.args[0].name == "colorof"
        assert event.args[0].args[0].name == "Button"
        assert isinstance(event.args[1], NumberLit)

    def test_nested_call_in_guard_still_parses(self):
        """The greedy guard path already worked; keep it working."""
        ast = self._rule("act=push(Cart, left) and colored(leftof(Cart), 7) "
                         "then moved(Cart, left)")
        pred = ast.rules.rules[0].guard.clauses[1]
        assert isinstance(pred.expr, FuncCall)
        assert pred.expr.name == "colored"
        assert pred.expr.args[0].name == "leftof"

    def test_unbalanced_event_raises(self):
        with pytest.raises(ParseError) as exc:
            self._rule("act=push(Cart, down) then jumped(Cart, (1, 1)")
        assert "unbalanced" in str(exc.value).lower()

    def test_unbalanced_nested_call_raises(self):
        with pytest.raises(ParseError) as exc:
            self._rule("act=push(Cart, down) then moved(leftof(Cart, down)")
        assert "unbalanced" in str(exc.value).lower()

    def test_unbalanced_action_match_raises(self):
        with pytest.raises(ParseError) as exc:
            self._rule("act=push(Cart, down then moved(Cart, down)")
        assert "unbalanced" in str(exc.value).lower()

    def test_unbalanced_guard_predicate_raises(self):
        with pytest.raises(ParseError) as exc:
            self._rule("act=push(Cart, up) and free(above(Cart) "
                       "then moved(Cart, up)")
        assert "unbalanced" in str(exc.value).lower()


# ------------------------------------------------------- E-07 · the modifier

def test_unique_is_parsed_and_defaults_off():
    from theory_compiler.parser.theory_parser import parse_theory as _p
    src = ("word_table:\n  board\n  object Peg { pos: Int unique, alive: Bool }\n"
           "semantics:\n  frame persist\n  conflict exclusive\n"
           "  cascade single_frame\n"
           "events:\n  event removed(p)\n"
           "rules:\n  rule r\n    when act=jump(Peg, left) then removed(Peg)\n"
           "goal:\n  goal count(Peg, alive = true) = 1\n")
    fields = _p(src).word_table.objects[0].fields
    assert fields[0].unique is True and fields[1].unique is False


def test_an_unknown_field_modifier_is_refused_not_dropped():
    """The regex used to be unanchored, so `pos: Int unique` parsed as a plain
    `pos: Int` and the modifier vanished silently — the v0.1-parser hazard
    (skip what you do not recognise, compile a different world) reproduced
    inside a single line. A dropped `unique` is worse than a rejected one: the
    manual reads as though it entails `conflict exclusive` and does not."""
    from theory_compiler.parser.theory_parser import parse_theory as _p, ParseError
    src = ("word_table:\n  board\n  object Peg { pos: Int frobnicate, alive: Bool }\n"
           "semantics:\n  frame persist\n  conflict exclusive\n"
           "  cascade single_frame\n"
           "events:\n  event removed(p)\n"
           "rules:\n  rule r\n    when act=jump(Peg, left) then removed(Peg)\n"
           "goal:\n  goal count(Peg, alive = true) = 1\n")
    with pytest.raises(ParseError) as exc:
        _p(src)
    assert "frobnicate" in str(exc.value)
