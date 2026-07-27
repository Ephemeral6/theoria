"""
Theory DSL parser — hand-rolled recursive descent.
Parses theory.dsl text into TheoryAST.
"""

import re
from typing import Optional

from .ast_nodes import (
    TheoryAST, WordTable, ObjectDecl, Field, ConceptAccount,
    EventsSection, EventDecl, EventAlt,
    RulesSection, RuleDecl, RuleMeta, Guard, GuardClause,
    GuardAction, GuardPredicate, ActionMatch,
    Expr, NameRef, NumberLit, FieldAccess, FuncCall, BinOp, TupleLit, Comparison,
    GoalSection, GoalExpr,
    LawsSection, InvariantDecl, TheoremDecl,
)


class ParseError(Exception):
    def __init__(self, message: str, line: int = 0):
        self.line = line
        super().__init__(f"Line {line}: {message}" if line else message)


class TheoryParser:
    """Parse theory.dsl text into TheoryAST."""

    def __init__(self, text: str):
        self.lines = text.splitlines()
        self.pos = 0  # current line index

    def parse(self) -> TheoryAST:
        ast = TheoryAST()
        while self.pos < len(self.lines):
            line = self._current_stripped()
            if not line or line.startswith("#"):
                self.pos += 1
                continue
            if line.startswith("word_table:"):
                ast.word_table = self._parse_word_table()
            elif line.startswith("events:"):
                ast.events = self._parse_events()
            elif line.startswith("rules:"):
                ast.rules = self._parse_rules()
            elif line.startswith("goal:"):
                ast.goal = self._parse_goal()
            elif line.startswith("laws:"):
                ast.laws = self._parse_laws()
            else:
                self.pos += 1  # skip unrecognized
        return ast

    # ---- helpers ----

    def _current_stripped(self) -> str:
        if self.pos >= len(self.lines):
            return ""
        return self.lines[self.pos].strip()

    def _current_raw(self) -> str:
        if self.pos >= len(self.lines):
            return ""
        return self.lines[self.pos]

    def _indent_level(self) -> int:
        raw = self._current_raw()
        return len(raw) - len(raw.lstrip())

    def _is_indented(self) -> bool:
        """Check if current line is indented (part of a block)."""
        if self.pos >= len(self.lines):
            return False
        raw = self._current_raw()
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            return True  # blank/comment lines don't break blocks
        return raw[0] in (' ', '\t')

    def _skip_blank_comment(self):
        while self.pos < len(self.lines):
            s = self._current_stripped()
            if s == "" or s.startswith("#"):
                self.pos += 1
            else:
                break

    # ---- word_table ----

    def _parse_word_table(self) -> WordTable:
        self.pos += 1  # skip "word_table:"
        wt = WordTable()
        while self.pos < len(self.lines) and self._is_indented():
            line = self._current_stripped()
            if not line or line.startswith("#"):
                self.pos += 1
                continue
            if line == "board":
                wt.has_board = True
                self.pos += 1
            elif line.startswith("object "):
                wt.objects.append(self._parse_object_decl())
            else:
                # might be concept account: Name [...]
                m = re.match(r'(\w+)\s*\[', line)
                if m:
                    wt.accounts.append(self._parse_concept_account(line))
                    self.pos += 1
                else:
                    self.pos += 1
        return wt

    def _parse_object_decl(self) -> ObjectDecl:
        line = self._current_stripped()
        # object Name { field: Type, ... }
        m = re.match(r'object\s+(\w+)\s*\{([^}]*)\}', line)
        if not m:
            raise ParseError(f"Invalid object declaration: {line}", self.pos + 1)
        name = m.group(1)
        fields_str = m.group(2).strip()
        fields = []
        if fields_str:
            for part in fields_str.split(","):
                part = part.strip()
                fm = re.match(r'(\w+)\s*:\s*(\w+)', part)
                if fm:
                    fields.append(Field(fm.group(1), fm.group(2)))
        self.pos += 1
        return ObjectDecl(name, fields)

    def _parse_concept_account(self, line: str) -> ConceptAccount:
        m = re.match(r'(\w+)\s*\[([^\]]*)\]', line)
        if not m:
            raise ParseError(f"Invalid concept account: {line}", self.pos + 1)
        obj_name = m.group(1)
        attrs_str = m.group(2)
        ca = ConceptAccount(obj_name)
        for attr in re.finditer(r'(\w+):\s*(\S+)', attrs_str):
            key, val = attr.group(1), attr.group(2)
            if key == "segment":
                ca.segment = val
            elif key == "ev":
                ca.evidence_range = val
            elif key == "compress":
                ca.compress = int(val)
        return ca

    # ---- events ----

    def _parse_events(self) -> EventsSection:
        self.pos += 1  # skip "events:"
        section = EventsSection()
        while self.pos < len(self.lines) and self._is_indented():
            line = self._current_stripped()
            if not line or line.startswith("#"):
                self.pos += 1
                continue
            if line.startswith("event "):
                section.events.append(self._parse_event_decl(line))
                self.pos += 1
            else:
                self.pos += 1
        return section

    def _parse_event_decl(self, line: str) -> EventDecl:
        # event name(params) | name(params) | ...
        body = line[len("event "):].strip()
        alts = []
        for part in body.split("|"):
            part = part.strip()
            m = re.match(r'(\w+)\(([^)]*)\)', part)
            if m:
                name = m.group(1)
                params = [p.strip() for p in m.group(2).split(",") if p.strip()]
                alts.append(EventAlt(name, params))
        return EventDecl(alts)

    # ---- rules ----

    def _parse_rules(self) -> RulesSection:
        self.pos += 1  # skip "rules:"
        section = RulesSection()
        while self.pos < len(self.lines) and self._is_indented():
            line = self._current_stripped()
            if not line or line.startswith("#"):
                self.pos += 1
                continue
            if line.startswith("rule "):
                section.rules.append(self._parse_rule_decl())
            else:
                self.pos += 1
        return section

    def _parse_rule_decl(self) -> RuleDecl:
        line = self._current_stripped()
        # rule name [ev: ... cov: .../...]
        m = re.match(r'rule\s+(\w+)\s*(\[.*?\])?\s*$', line)
        if not m:
            raise ParseError(f"Invalid rule header: {line}", self.pos + 1)
        name = m.group(1)
        meta = None
        if m.group(2):
            meta = self._parse_rule_meta(m.group(2))
        self.pos += 1

        # next line: when ... then ...
        self._skip_blank_comment()
        wt_line = self._current_stripped()
        if not wt_line.startswith("when "):
            raise ParseError(f"Expected 'when' clause, got: {wt_line}", self.pos + 1)

        # Split on ' then '
        then_idx = wt_line.rfind(" then ")
        if then_idx == -1:
            raise ParseError(f"Missing 'then' in rule: {wt_line}", self.pos + 1)

        guard_text = wt_line[len("when "):then_idx].strip()
        event_text = wt_line[then_idx + len(" then "):].strip()

        guard = self._parse_guard(guard_text)
        event = self._parse_func_call(event_text)
        self.pos += 1
        return RuleDecl(name, meta, guard, event)

    def _parse_rule_meta(self, text: str) -> RuleMeta:
        # [ev: t1,t2,... cov: k/n]
        meta = RuleMeta()
        ev_m = re.search(r'ev:\s*([^\]]+?)(?:\s+cov:|\])', text)
        if ev_m:
            meta.evidence = ev_m.group(1).strip()
        cov_m = re.search(r'cov:\s*(\d+/\d+)', text)
        if cov_m:
            meta.coverage = cov_m.group(1)
        return meta

    def _parse_guard(self, text: str) -> Guard:
        # Split on ' and ' — but careful of parenthesized content
        clauses = []
        parts = self._split_guard_and(text)
        for part in parts:
            part = part.strip()
            if part.startswith("act="):
                clauses.append(self._parse_action_match(part))
            else:
                clauses.append(GuardPredicate(self._parse_expr(part)))
        return Guard(clauses)

    def _split_guard_and(self, text: str) -> list[str]:
        """Split on ' and ' respecting parentheses."""
        parts = []
        depth = 0
        current = []
        i = 0
        while i < len(text):
            if text[i] == '(':
                depth += 1
                current.append(text[i])
            elif text[i] == ')':
                depth -= 1
                current.append(text[i])
            elif depth == 0 and text[i:i+5] == ' and ':
                parts.append(''.join(current))
                current = []
                i += 5
                continue
            else:
                current.append(text[i])
            i += 1
        if current:
            parts.append(''.join(current))
        return parts

    def _parse_action_match(self, text: str) -> GuardAction:
        # act=name(args)
        m = re.match(r'act=(\w+)\(([^)]*)\)', text)
        if not m:
            raise ParseError(f"Invalid action match: {text}")
        name = m.group(1)
        args = self._parse_arg_list(m.group(2))
        return GuardAction(ActionMatch(name, args))

    def _parse_func_call(self, text: str) -> FuncCall:
        m = re.match(r'(\w+)\(([^)]*)\)', text)
        if not m:
            raise ParseError(f"Invalid function call: {text}")
        name = m.group(1)
        args = self._parse_arg_list(m.group(2))
        return FuncCall(name, args)

    def _parse_arg_list(self, text: str) -> list[Expr]:
        if not text.strip():
            return []
        args = []
        depth = 0
        current = []
        for ch in text:
            if ch == '(':
                depth += 1
                current.append(ch)
            elif ch == ')':
                depth -= 1
                current.append(ch)
            elif ch == ',' and depth == 0:
                args.append(self._parse_expr(''.join(current).strip()))
                current = []
            else:
                current.append(ch)
        if current:
            args.append(self._parse_expr(''.join(current).strip()))
        return args

    def _parse_expr(self, text: str) -> Expr:
        text = text.strip()

        # Comparison: look for op at top level
        comp_op = self._find_comparison_op(text)
        if comp_op:
            idx, op = comp_op
            left = self._parse_expr(text[:idx].strip())
            right = self._parse_expr(text[idx + len(op):].strip())
            return Comparison(op, left, right)

        # Addition/subtraction at top level
        add_idx = self._find_top_level_op(text, ['+', '-'])
        if add_idx is not None:
            idx, op = add_idx
            left = self._parse_expr(text[:idx].strip())
            right = self._parse_expr(text[idx + 1:].strip())
            return BinOp(op, left, right)

        # Tuple: (expr, expr)
        if text.startswith("(") and text.endswith(")"):
            inner = text[1:-1]
            # Check if it's a tuple (has comma at depth 0)
            if ',' in inner:
                parts = []
                depth = 0
                current = []
                for ch in inner:
                    if ch == '(':
                        depth += 1
                        current.append(ch)
                    elif ch == ')':
                        depth -= 1
                        current.append(ch)
                    elif ch == ',' and depth == 0:
                        parts.append(self._parse_expr(''.join(current).strip()))
                        current = []
                    else:
                        current.append(ch)
                parts.append(self._parse_expr(''.join(current).strip()))
                return TupleLit(parts)
            # Otherwise just parenthesized expr
            return self._parse_expr(inner)

        # Function call: name(...)
        m = re.match(r'(\w+)\((.+)\)$', text, re.DOTALL)
        if m:
            name = m.group(1)
            args = self._parse_arg_list(m.group(2))
            return FuncCall(name, args)

        # Field access: obj.field
        if '.' in text and re.match(r'^\w+\.\w+$', text):
            parts = text.split('.', 1)
            return FieldAccess(parts[0], parts[1])

        # Number
        if re.match(r'^\d+$', text):
            return NumberLit(int(text))

        # Name reference
        if re.match(r'^[\w]+$', text):
            return NameRef(text)

        # Fallback: treat as name
        return NameRef(text)

    def _find_comparison_op(self, text: str):
        """Find comparison op at top level (not inside parens)."""
        ops = [">=", "<=", "!=", "=", ">", "<"]
        depth = 0
        i = 0
        while i < len(text):
            if text[i] == '(':
                depth += 1
            elif text[i] == ')':
                depth -= 1
            elif depth == 0:
                for op in ops:
                    if text[i:i+len(op)] == op:
                        # Make sure it's not inside a keyword like act=
                        if op == "=" and i > 0 and text[i-1] in ('!', '<', '>'):
                            continue
                        if op == "=" and i > 0 and re.match(r'\w', text[i-1]):
                            # could be act= or named param, skip
                            continue
                        return (i, op)
            i += 1
        return None

    def _find_top_level_op(self, text: str, ops: list[str]):
        """Find last +/- at top level (left-associative)."""
        depth = 0
        last = None
        for i, ch in enumerate(text):
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
            elif depth == 0 and ch in ops and i > 0:
                last = (i, ch)
        return last

    # ---- goal ----

    def _parse_goal(self) -> GoalSection:
        self.pos += 1  # skip "goal:"
        self._skip_blank_comment()
        line = self._current_stripped()
        if line.startswith("goal "):
            expr_text = line[len("goal "):].strip()
            expr = self._parse_expr(expr_text)
            self.pos += 1
            return GoalSection(GoalExpr(expr))
        raise ParseError(f"Expected 'goal' statement, got: {line}", self.pos + 1)

    # ---- laws ----

    def _parse_laws(self) -> LawsSection:
        self.pos += 1  # skip "laws:"
        section = LawsSection()
        while self.pos < len(self.lines) and self._is_indented():
            line = self._current_stripped()
            if not line or line.startswith("#"):
                self.pos += 1
                continue
            if line.startswith("invariant "):
                section.invariants.append(self._parse_invariant(line))
                self.pos += 1
            elif line.startswith("theorem "):
                section.theorems.append(self._parse_theorem())
            else:
                self.pos += 1
        return section

    def _parse_invariant(self, line: str) -> InvariantDecl:
        # invariant name expr OP value [status: ...]
        # Extract meta bracket first
        meta_m = re.search(r'\[([^\]]*)\]\s*$', line)
        status = None
        if meta_m:
            meta_str = meta_m.group(1)
            sm = re.search(r'status:\s*(\w+)', meta_str)
            if sm:
                status = sm.group(1)
            line = line[:meta_m.start()].strip()

        # invariant name rest
        m = re.match(r'invariant\s+(\w+)\s+(.+)', line)
        if not m:
            raise ParseError(f"Invalid invariant: {line}", self.pos + 1)
        name = m.group(1)
        rest = m.group(2).strip()

        # Find comparison operator
        for op in [">=", "<=", "!=", "=", ">", "<"]:
            idx = rest.rfind(op)
            if idx > 0:
                expr_text = rest[:idx].strip()
                value = rest[idx + len(op):].strip()
                return InvariantDecl(name, expr_text, op, value, status)

        raise ParseError(f"No comparison op in invariant: {rest}", self.pos + 1)

    def _parse_theorem(self) -> TheoremDecl:
        line = self._current_stripped()
        # theorem name "description"
        m = re.match(r'theorem\s+(\w+)\s+"([^"]*)"', line)
        if not m:
            raise ParseError(f"Invalid theorem: {line}", self.pos + 1)
        name = m.group(1)
        desc = m.group(2)
        depends = None
        probe = None

        # Check for meta on same line or next
        meta_m = re.search(r'\[([^\]]*)\]', line[m.end():])
        if not meta_m:
            # Check next line
            self.pos += 1
            if self.pos < len(self.lines):
                next_line = self._current_stripped()
                meta_m2 = re.match(r'\[([^\]]*)\]', next_line)
                if meta_m2:
                    meta_str = meta_m2.group(1)
                    dep_m = re.search(r'depends:\s*([\w,\s]+?)(?:\s+probe:|\]|$)', meta_str)
                    if dep_m:
                        depends = [d.strip() for d in dep_m.group(1).split(",")]
                    prb_m = re.search(r'probe:\s*(\w+)', meta_str)
                    if prb_m:
                        probe = prb_m.group(1)
                    self.pos += 1
            return TheoremDecl(name, desc, depends, probe)
        else:
            meta_str = meta_m.group(1)
            dep_m = re.search(r'depends:\s*([\w,\s]+?)(?:\s+probe:|\]|$)', meta_str)
            if dep_m:
                depends = [d.strip() for d in dep_m.group(1).split(",")]
            prb_m = re.search(r'probe:\s*(\w+)', meta_str)
            if prb_m:
                probe = prb_m.group(1)
            self.pos += 1
            return TheoremDecl(name, desc, depends, probe)


def parse_theory(text: str) -> TheoryAST:
    """Parse theory.dsl text into an AST."""
    parser = TheoryParser(text)
    return parser.parse()
