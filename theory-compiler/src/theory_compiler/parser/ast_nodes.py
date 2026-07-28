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
    # E-07. `pos: Int unique` — no two *live* instances of this type ever share
    # a value of this field. It is a fact about the world (pegs cannot stack;
    # two ghosts in a corridor might), so it belongs in the per-world manual
    # rather than in any backend, and declaring it is what lets `conflict
    # exclusive` be *entailed* by a manual whose rules quantify over a second
    # instance. It is a claim, not a hint: `certify_uniqueness` proves the
    # initial state satisfies it and that `step` preserves it.
    unique: bool = False


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
class LandmarkDecl:
    """E-04. A cell the domain names but does not locate.

    `portal_exit` is a fact about *this level*; that it exists at all is a fact
    about the world. Declaring the name here is what lets a reader of
    theory.dsl alone tell which free names are problem data.
    """
    name: str


@dataclass
class WeightsDecl:
    """E-05. A weight function whose *values* live in the problem instance.

    The domain declares that a pagoda potential is available over `over`; the
    numbers arrive from the LP certificate. Without this the weight vector had
    nowhere to be named and the invariant could not refer to it.
    """
    name: str
    over: str


@dataclass
class ClausesDecl:
    """E-06. A named propositional invariant whose *clauses* live in a certificate.

    The exact shape of `WeightsDecl`, one level of expressivity over: the domain
    declares that a separating invariant over `over` is available, and `ic3_pdr`
    supplies the clauses. Declared for the same reason the weights are — so a
    reader of `theory.dsl` alone can tell that the manual rests on an
    engine-derived object, and which engine derived it.
    """
    name: str
    over: str


@dataclass
class DomainDecl:
    """E-02. A finite value set a rule variable may range over."""
    name: str
    values: list[str]


@dataclass
class WordTable:
    has_board: bool = True
    objects: list[ObjectDecl] = field(default_factory=list)
    accounts: list[ConceptAccount] = field(default_factory=list)
    landmarks: list[LandmarkDecl] = field(default_factory=list)
    weights: list[WeightsDecl] = field(default_factory=list)
    clauses: list[ClausesDecl] = field(default_factory=list)
    domains: list[DomainDecl] = field(default_factory=list)


@dataclass
class SemanticsSection:
    """E-03 — the frame axiom and its two neighbours, in the manual at last.

    Adopted from cold-start-a0's extension request essentially verbatim. It is
    mandatory: the v0.1 parser skipped unknown lines, so a manual carrying this
    section parsed there silently and to a *different world*. Defaulting it
    would reproduce exactly the hazard it exists to close.
    """
    frame: str                                     # persist | reset
    conflict: str                                  # exclusive | priority
    cascade: str                                   # single_frame | multi_frame
    priority: list[str] = field(default_factory=list)


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
class VarRef(Expr):
    """E-02. `?d` — a rule variable, ground by expansion before any backend."""
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
    negated: bool = False  # E-01: `not free(above(Cart))`


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
    # E-02. Variable name -> declared domain name, e.g. {"d": "dir"}. A rule
    # with bindings is a schema; `expand_rules` grounds it before the IR is
    # built, so no backend ever sees a VarRef.
    bindings: dict[str, str] = field(default_factory=dict)


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
    # E-05. Where the numbers came from. `pagoda(w)` with source `lp_potential`
    # is the whole point of A1: the weights are the engine's, not the author's,
    # and a reader can tell which by looking.
    source: Optional[str] = None


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
    semantics: Optional[SemanticsSection] = None
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
