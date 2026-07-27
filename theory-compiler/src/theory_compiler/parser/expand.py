"""Grounding pass: turn rule schemas into ground rules (ledger entry E-02).

A rule that binds `?d` over a declared domain is a *schema*. Every backend
wants ground rules, and every backend would otherwise implement substitution
itself, so substitution happens once, here, between the parser and the IR. No
backend ever sees a `VarRef`; if one does, that is a bug in this module rather
than a case the backend has to handle.

This is the compiler doing what A0 did by hand. `cold-start-a0/theory/theory.dsl`
carries four push rules that differ only in a direction, because v0.1 had no way
to say "for each direction". THEORIZE_LOG E-02 records the cost: the engine
mined one lifted rule with 212/212 coverage, and writing it out as four rules
split that evidence into four weaker-looking claims. Expansion here restores the
arithmetic — the schema keeps the coverage it was mined with, and the ground
rules inherit it.
"""

from dataclasses import replace
from typing import Dict, List

from .ast_nodes import (
    ActionMatch, BinOp, Comparison, Expr, FieldAccess, FuncCall, Guard,
    GuardAction, GuardPredicate, NameRef, NumberLit, RuleDecl, RulesSection,
    TheoryAST, TupleLit, VarRef,
)


class ExpansionError(Exception):
    """A rule variable with no declared domain, or a domain with no values."""


def _subst(expr: Expr, env: Dict[str, str]) -> Expr:
    """Replace every `VarRef` by the `NameRef` its binding names."""
    if isinstance(expr, VarRef):
        if expr.name not in env:
            raise ExpansionError(
                f"?{expr.name} is used but never bound. Add "
                f"`forall ?{expr.name} in <domain>` to the rule header."
            )
        return NameRef(env[expr.name])
    if isinstance(expr, FuncCall):
        return FuncCall(expr.name, [_subst(a, env) for a in expr.args])
    if isinstance(expr, Comparison):
        return Comparison(expr.op, _subst(expr.left, env), _subst(expr.right, env))
    if isinstance(expr, BinOp):
        return BinOp(expr.op, _subst(expr.left, env), _subst(expr.right, env))
    if isinstance(expr, TupleLit):
        return TupleLit([_subst(e, env) for e in expr.elements])
    if isinstance(expr, (NameRef, NumberLit, FieldAccess)):
        return expr
    raise ExpansionError(f"cannot substitute into {expr!r}")


def _subst_guard(guard: Guard, env: Dict[str, str]) -> Guard:
    clauses = []
    for clause in guard.clauses:
        if isinstance(clause, GuardAction):
            clauses.append(GuardAction(ActionMatch(
                clause.action.action_name,
                [_subst(a, env) for a in clause.action.args],
            )))
        elif isinstance(clause, GuardPredicate):
            clauses.append(GuardPredicate(_subst(clause.expr, env), clause.negated))
        else:
            raise ExpansionError(f"unknown guard clause {clause!r}")
    return Guard(clauses)


def expand_rule(rule: RuleDecl, domains: Dict[str, List[str]],
                object_types: frozenset = frozenset()) -> List[RuleDecl]:
    """One schema in, `prod(|domain|)` ground rules out. No bindings: identity.

    Ground rules are named `<rule>_<value>...` in binding-declaration order, so
    the A0 manual's hand-written `push_up` is exactly what `push forall ?d in
    dir` produces. That is deliberate: the expansion has to be able to *replace*
    the four hand-written rules without renaming anything downstream.
    """
    # Bindings over declared *object types* are left alone: their values are the
    # level's instances, which this pass cannot see. `ir.build_ir` grounds them
    # once the problem is in hand. Anything that is neither is a typo, and
    # saying so here beats a KeyError three layers down.
    value_bindings = {v: d for v, d in rule.bindings.items() if d in domains}
    unknown = {v: d for v, d in rule.bindings.items()
               if d not in domains and d not in object_types}
    if unknown:
        var, dom = sorted(unknown.items())[0]
        raise ExpansionError(
            f"rule {rule.name} binds ?{var} over {dom!r}, which is neither a "
            f"declared value domain nor a declared object type. Add "
            f"`domain {dom} {{ ... }}` or `object {dom} {{ ... }}` to word_table."
        )
    if not value_bindings:
        return [rule]

    order = list(value_bindings)
    keep = {v: d for v, d in rule.bindings.items() if v not in value_bindings}
    out: List[RuleDecl] = []

    def walk(i: int, env: Dict[str, str]):
        if i == len(order):
            suffix = "_".join(env[v] for v in order)
            out.append(RuleDecl(
                name=f"{rule.name}_{suffix}",
                meta=replace(rule.meta) if rule.meta else None,
                guard=_subst_guard(rule.guard, env),
                event=_subst(rule.event, env),
                bindings=dict(keep),
            ))
            return
        var = order[i]
        for value in domains[value_bindings[var]]:
            walk(i + 1, dict(env, **{var: value}))

    walk(0, {})
    return out


def expand_theory(ast: TheoryAST) -> TheoryAST:
    """Ground every rule schema. Idempotent on an already-ground theory."""
    if ast.rules is None:
        return ast
    wt = ast.word_table
    domains = {d.name: d.values for d in (wt.domains if wt else [])}
    object_types = frozenset(o.name for o in (wt.objects if wt else []))
    rules: List[RuleDecl] = []
    for rule in ast.rules.rules:
        rules.extend(expand_rule(rule, domains, object_types))

    seen = set()
    for rule in rules:
        if rule.name in seen:
            raise ExpansionError(
                f"expansion produced two rules named {rule.name!r}; rename the "
                f"schema or the ground rule it collides with"
            )
        seen.add(rule.name)

    return replace(ast, rules=RulesSection(rules))
