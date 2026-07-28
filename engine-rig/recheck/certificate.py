"""A certificate: a predicate, a claim, and nothing else.

The list of keys a certificate may **not** carry is the substance of this file.
A certificate that could declare its own variables, actions, rules, initial
state, goal or state space would be checkable against itself, and the check
would mean nothing.  Every one of those names is refused explicitly, with the
reason, rather than falling out of a generic "unknown key" -- because the whole
attack is that they look like reasonable things for a certificate to say.

Two kinds, matching the two engines M9 added:

  `inductive_invariant`  (`ic3_pdr`)         claim: `unsolvable`
      I is a set of states holding at the start, closed under every action, and
      disjoint from the goal.

  `dead_region`  (`deadlock_carver`)         claim: `conditional_unsolvability`
      P is a set of states closed under every action and disjoint from the goal.
      There is no initial obligation -- the theorem is conditional -- so the
      first condition becomes non-vacuity instead: a pattern no state satisfies
      is closed and goal-free for free, and certifies nothing.

      The claim is the carver's own, qualifier included: *every reachable state*
      containing P is dead.  Closure is checked on the states the rule set's
      constraint admits, so the qualifier is doing work whenever P reaches past
      it, and `verify` reports how much.

A certificate may carry its own `tables` and `defs`, because a pagoda weight
table *is* the certificate's content.  It may not shadow a name the rule set
declared: a certificate that redefined the rule set's `free` would be rewriting
the rules under cover of describing a set of states.
"""

import hashlib
import json
import os
from dataclasses import dataclass
from typing import Dict, Mapping, Optional

from recheck.expr import (
    ExprError,
    Macro,
    Scope,
    Table,
    compile_macros,
    compile_predicate,
    names_used,
    parse_macros,
    parse_tables,
    render,
)

SCHEMA = "engine-rig/recheck/certificate-v1"

KINDS = {
    "inductive_invariant": "unsolvable",
    "dead_region": "conditional_unsolvability",
}

_CERTIFICATE_KEYS = {
    "schema", "name", "comment", "provenance", "produced_by",
    "kind", "claim", "ruleset", "tables", "defs", "predicate",
}

# Refused by name, each with the reason it is refused.  These are not typos --
# they are the shapes a forged certificate takes.
_FORBIDDEN = {
    "variables": "the state space comes from the rule set's declared domains",
    "actions": "the action set comes from the rule set",
    "rules": "a certificate that ships rules is checking itself",
    "transitions": "the transition relation is derived here, never read",
    "edges": "the transition relation is derived here, never read",
    "states": "the state space is the product of the declared domains, not a list",
    "init": "the initial state comes from the rule set",
    "goal": "the goal comes from the rule set; a certificate that picks its own "
            "goal proves a different theorem than the one claimed",
    "constraint": "restricting the state space is the rule set's business, and "
                  "only when the restriction is itself proved inductive",
    "conditions": "the conditions are what this rechecker computes",
    "counterexamples": "witnesses are output, not input",
}


class CertificateError(ValueError):
    """A malformed certificate, or one reaching for something it may not have."""


@dataclass
class Certificate:
    name: str
    kind: str
    claim: str
    predicate_src: object
    source: Optional[str]
    sha256: str
    binds_ruleset: Optional[Mapping[str, object]]
    produced_by: Optional[str]
    tables: Mapping[str, Table]
    macros: Mapping[str, Macro]
    spec: Mapping[str, object]

    def rendering(self) -> str:
        return render(self.predicate_src)

    def compile(self, ruleset) -> "object":
        """Compile the predicate in the rule set's vocabulary, plus its own.

        `allow_action=False`: a certificate describes a set of *states*.  One
        that mentioned the action label would be describing the rules.
        """
        clash = set(self.tables) & set(ruleset.tables)
        if clash:
            raise CertificateError(
                "certificate tables %s shadow the rule set's; a certificate may "
                "add data, never redefine the world's" % sorted(clash)
            )
        clash = set(self.macros) & set(ruleset.state_scope.macros)
        if clash:
            raise CertificateError(
                "certificate defs %s shadow the rule set's" % sorted(clash)
            )
        tables = dict(ruleset.tables)
        tables.update(self.tables)
        base = Scope(
            variables=ruleset.var_index, tables=tables,
            macros=dict(ruleset.state_scope.macros),
            macro_arity=dict(ruleset.state_scope.macro_arity),
            allow_action=False,
        )
        try:
            scope = compile_macros(self.macros, base)
            return compile_predicate(self.predicate_src, scope, "predicate")
        except ExprError as exc:
            raise CertificateError("predicate: %s" % exc) from exc

    def summary(self) -> Dict[str, object]:
        variables, tables, defs = names_used(self.predicate_src)
        return {
            "name": self.name,
            "kind": self.kind,
            "claim": self.claim,
            "predicate": self.rendering(),
            "mentions_variables": variables,
            "mentions_tables": tables,
            "mentions_defs": defs,
            "produced_by": self.produced_by,
            "source": os.path.basename(self.source) if self.source else None,
            "sha256": self.sha256,
        }


def parse_certificate(spec: Mapping[str, object], source: Optional[str] = None,
                      sha256: str = "") -> Certificate:
    if not isinstance(spec, dict):
        raise CertificateError("a certificate must be a JSON object")

    trespass = sorted(set(spec) & set(_FORBIDDEN))
    if trespass:
        raise CertificateError(
            "a certificate may not carry %s -- %s"
            % (trespass, "; ".join("%s: %s" % (k, _FORBIDDEN[k]) for k in trespass))
        )
    unknown = set(spec) - _CERTIFICATE_KEYS
    if unknown:
        raise CertificateError("unknown keys %s" % sorted(unknown))
    if spec.get("schema") != SCHEMA:
        raise CertificateError("schema must be %r, got %r" % (SCHEMA, spec.get("schema")))

    kind = spec.get("kind")
    if kind not in KINDS:
        raise CertificateError("kind must be one of %s, got %r" % (sorted(KINDS), kind))
    claim = spec.get("claim")
    if claim != KINDS[kind]:
        raise CertificateError(
            "a %s certificate licenses %r, not %r" % (kind, KINDS[kind], claim))

    if "predicate" not in spec:
        raise CertificateError("a certificate must carry a predicate")

    binds = spec.get("ruleset")
    if binds is not None:
        if not isinstance(binds, dict) or set(binds) - {"name", "sha256"}:
            raise CertificateError("ruleset binding takes `name` and `sha256` only")

    try:
        tables = parse_tables(spec.get("tables"), "certificate")
        macros = parse_macros(spec.get("defs"), "certificate")
    except ExprError as exc:
        raise CertificateError(str(exc)) from exc

    return Certificate(
        name=str(spec.get("name") or "<unnamed>"),
        kind=kind,
        claim=claim,
        predicate_src=spec["predicate"],
        source=source,
        sha256=sha256,
        binds_ruleset=binds,
        produced_by=spec.get("produced_by"),
        tables=tables,
        macros=macros,
        spec=spec,
    )


def load_certificate(path: str) -> Certificate:
    with open(path, "rb") as handle:
        payload = handle.read()
    spec = json.loads(payload.decode("utf-8"))
    return parse_certificate(spec, source=path,
                             sha256=hashlib.sha256(payload).hexdigest())


def certificate_from_spec(spec: Mapping[str, object]) -> Certificate:
    payload = json.dumps(spec, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return parse_certificate(spec, sha256=hashlib.sha256(payload).hexdigest())
