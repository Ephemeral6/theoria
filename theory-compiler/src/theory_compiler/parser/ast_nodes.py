"""AST node definitions for theory.dsl and playbook.dsl."""

from dataclasses import dataclass, field
from typing import Optional


# ============================================================
# theory.dsl AST
# ============================================================

@dataclass
class Field:
    name: str
    type: str


@dataclass
class ObjectDecl:
    name: str
    fields: list[Field]


@dataclass
class ConceptAccount:
    obj_name: str
    segment: Optional[str] = None
    evidence_range: Optional[str] = None
    compress: Optional[int] = None


@dataclass
class WordTable:
    has_board: bool = True
    objects: list[ObjectDecl] = field(default_factory=list)
    accounts: list[ConceptAccount] = field(default_factory=list)


@dataclass
class EventAlt:
    name: str
    params: list[str]


@dataclass
class EventDecl:
    alternatives: list[EventAlt]


@dataclass
class EventsSection:
    events: list[EventDecl] = field(default_factory=list)


@dataclass
class Expr:
    """Base expression node."""
    pass


@dataclass
class NameRef(Expr):
    name: str


@dataclass
class NumberLit(Expr):
    value: int


@dataclass
class FieldAccess(Expr):
    obj: str
    field_name: str


@dataclass
class FuncCall(Expr):
    name: str
    args: list[Expr]


@dataclass
class BinOp(Expr):
    op: str
    left: Expr
    right: Expr


@dataclass
class TupleLit(Expr):
    elements: list[Expr]


@dataclass
class Comparison(Expr):
    op: str
    left: Expr
    right: Expr


@dataclass
class ActionMatch:
    action_name: str
    args: list[Expr]


@dataclass
class GuardClause:
    """One clause in a guard conjunction."""
    pass


@dataclass
class GuardAction(GuardClause):
    action: ActionMatch


@dataclass
class GuardPredicate(GuardClause):
    expr: Expr  # FuncCall or Comparison


@dataclass
class Guard:
    clauses: list[GuardClause]


@dataclass
class RuleMeta:
    evidence: Optional[str] = None
    coverage: Optional[str] = None


@dataclass
class RuleDecl:
    name: str
    meta: Optional[RuleMeta]
    guard: Guard
    event: FuncCall


@dataclass
class RulesSection:
    rules: list[RuleDecl] = field(default_factory=list)


@dataclass
class GoalExpr:
    expr: Expr


@dataclass
class GoalSection:
    goal: GoalExpr


@dataclass
class InvariantDecl:
    name: str
    expr_text: str  # Keep raw text for the expression
    op: str
    value: str
    status: Optional[str] = None


@dataclass
class TheoremDecl:
    name: str
    description: str
    depends: Optional[list[str]] = None
    probe: Optional[str] = None


@dataclass
class LawsSection:
    invariants: list[InvariantDecl] = field(default_factory=list)
    theorems: list[TheoremDecl] = field(default_factory=list)


@dataclass
class TheoryAST:
    word_table: Optional[WordTable] = None
    events: Optional[EventsSection] = None
    rules: Optional[RulesSection] = None
    goal: Optional[GoalSection] = None
    laws: Optional[LawsSection] = None


# ============================================================
# playbook.dsl AST
# ============================================================

@dataclass
class OrderStmt:
    landmark: str
    proof: Optional[str] = None


@dataclass
class PruneStmt:
    condition: str
    proof: Optional[str] = None


@dataclass
class HeuristicStmt:
    name: str
    params: list[str]
    admissible: Optional[str] = None


@dataclass
class PreferStmt:
    name: str
    evidence: Optional[str] = None


@dataclass
class PlaybookAST:
    statements: list = field(default_factory=list)
    # list of OrderStmt | PruneStmt | HeuristicStmt | PreferStmt
