"""A certificate: a predicate, a claim, and nothing else.

The list of keys a certificate may **not** carry is the substance of this file.
A certificate that could declare its own variables, actions, rules, initial
state, goal or state space would be checkable against itself, and the check
would mean nothing.  Every one of those names is refused explicitly, with the
reason, rather than falling out of a generic "unknown key" -- because the whole
attack is that they look like reasonable things for a certificate to say.

Three kinds, matching the three engines that emit one:

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

  `potential_bound`  (`lp_potential`)        claim: `unsolvable`
      A pagoda.  The certificate declares an integer weight per state variable,
      the value that counts as *occupied*, and a bound; the potential of a state
      is the sum of the weights of its occupied variables, and the set of states
      is `potential(s) <= bound` -- **derived**, not written.  The obligation is
      arithmetic rather than set-theoretic: no legal move may raise the
      potential.

      That is why this kind carries no `predicate` and is refused if it does.  A
      certificate that shipped both a weight table and a predicate could be
      checked on one set while claiming about the other, and the two would look
      identical in the verdict.

A certificate may carry its own `tables` and `defs`, because a weight table *is*
the certificate's content.  It may not shadow a name the rule set declared: a
certificate that redefined the rule set's `free` would be rewriting the rules
under cover of describing a set of states.

**What a certificate may not carry is the substance of `_FORBIDDEN`, and
`obligations` is on that list for a reason.**  `lp_potential`'s exported
document ships one, listing every move instance with its delta already
evaluated, and the checker in `interop/certificate_export.py` iterates it.  A
document that simply omits an inconvenient move instance therefore passes that
checker.  Here the producer's own obligation list is refused at load: it is not
input, it is a claim about the answer.  The move set is re-derived from the rule
set's declared geometry instead (`recheck.verify`), and the producer's witness
list is compared against that derivation exactly once, in `anchors.py`, where a
disagreement is a finding rather than a rejection.
"""

import hashlib
import json
import os
from dataclasses import dataclass
from typing import Callable, Dict, Mapping, Optional, Tuple

from recheck.expr import (
    ExprError,
    Macro,
    Scope,
    State,
    Table,
    Value,
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
    "potential_bound": "unsolvable",
}

# The kinds whose set of states is *written*, as a predicate, and the one whose
# set of states is *derived*, from a weight table and a bound.  The split is
# worth naming because every key below is required of one group and refused of
# the other: a certificate that could pick either would be two certificates.
PREDICATE_KINDS = ("inductive_invariant", "dead_region")
POTENTIAL_KINDS = ("potential_bound",)

_CERTIFICATE_KEYS = {
    "schema", "name", "comment", "provenance", "produced_by",
    "kind", "claim", "ruleset", "tables", "defs", "predicate",
    "weights", "bound", "occupied",
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
    "obligations": "the obligations are what this rechecker discharges. "
                   "lp_potential's exported document ships its own, with every "
                   "delta pre-evaluated, and a checker that iterates that list "
                   "can be defeated by omitting an entry from it -- so it is "
                   "refused as input here and the move set is re-derived from "
                   "the rule set instead",
    "witnesses": "witnesses are output, not input",
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
    weights: Optional[Mapping[str, int]] = None
    bound: Optional[int] = None
    occupied: Value = None

    def rendering(self) -> str:
        if self.kind in POTENTIAL_KINDS:
            terms = ", ".join("%s: %d" % (name, self.weights[name])
                              for name in sorted(self.weights))
            return "potential(s) <= %d, w = {%s}, occupied = %r" % (
                self.bound, terms, self.occupied)
        return render(self.predicate_src)

    def potential(self, ruleset) -> Callable[[State], int]:
        """The declared weights, resolved against the rule set's variables.

        The certificate supplies numbers and a name for each; **which state
        variables exist, and which values they can hold, come from the rule
        set**.  A weight on a name the world does not declare, or on a value the
        variable can never take, is refused rather than quietly counted as zero
        -- a weight that can never contribute is how a potential is made
        constant, and a constant potential satisfies every closure obligation
        there is.

        Variables the certificate does not weigh contribute nothing.  That is
        the ordinary case: `lp_potential` weighs occupancy, and a world may hold
        state that occupancy does not describe.
        """
        terms: list = []
        for name in sorted(self.weights):
            index = ruleset.var_index.get(name)
            if index is None:
                raise CertificateError(
                    "the weight table names %r, which is not a declared state "
                    "variable of rule set %r" % (name, ruleset.name))
            domain = ruleset.variables[index].domain
            if not any(value == self.occupied
                       and isinstance(value, bool) == isinstance(self.occupied, bool)
                       for value in domain):
                raise CertificateError(
                    "%s is weighted %d when it holds %r, which is not in its "
                    "declared domain %s -- a weight that can never be counted "
                    "makes the potential constant, and a constant potential is "
                    "closed under everything"
                    % (name, self.weights[name], self.occupied, list(domain)))
            terms.append((index, self.weights[name]))
        occupied = self.occupied
        pairs: Tuple[Tuple[int, int], ...] = tuple(terms)

        def potential(state: State, _pairs=pairs, _occupied=occupied) -> int:
            total = 0
            for index, weight in _pairs:
                if state[index] == _occupied:
                    total += weight
            return total

        return potential

    def compile(self, ruleset) -> "object":
        """Compile the predicate in the rule set's vocabulary, plus its own.

        `allow_action=False`: a certificate describes a set of *states*.  One
        that mentioned the action label would be describing the rules.

        A `potential_bound` certificate has no predicate to compile: its set of
        states is `potential(s) <= bound`, built from the weights above, and the
        rest of the rechecker never has to know which kind produced it.
        """
        if self.kind in POTENTIAL_KINDS:
            potential = self.potential(ruleset)
            bound = self.bound
            return lambda state, _p=potential, _b=bound: _p(state) <= _b

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
        if self.kind in POTENTIAL_KINDS:
            variables = sorted(self.weights)
        out: Dict[str, object] = {
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
        if self.kind in POTENTIAL_KINDS:
            out["weights"] = dict(sorted(self.weights.items()))
            out["bound"] = self.bound
            out["occupied"] = self.occupied
        return out


def _parse_weights(raw: object) -> Dict[str, int]:
    """A weight per state variable, and integers only.

    Floats are refused rather than rounded.  `interop/certificate_export.py`
    scales the LP's exact rationals to integers precisely so that the closure
    obligation is decided in integer arithmetic; accepting a float here would
    put a rounding decision between the certificate and its verdict, and
    `delta <= 0` is exactly the comparison that decision would land on.
    """
    if not isinstance(raw, dict) or not raw:
        raise CertificateError(
            "weights must be a non-empty object mapping state variables to "
            "integers, got %r" % (raw,))
    out: Dict[str, int] = {}
    for name, value in raw.items():
        if not isinstance(name, str) or not name:
            raise CertificateError("weights: %r is not a variable name" % (name,))
        if isinstance(value, bool) or not isinstance(value, int):
            raise CertificateError(
                "weights: %s is %r, which is not an integer" % (name, value))
        out[name] = value
    return out


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

    weights: Optional[Dict[str, int]] = None
    bound: Optional[int] = None
    occupied: Value = None
    if kind in POTENTIAL_KINDS:
        if "predicate" in spec:
            raise CertificateError(
                "a %s certificate may not carry a predicate: its set of states "
                "is `potential(s) <= bound`, derived from the weights. One that "
                "carried both could be checked on one set and claim about the "
                "other" % kind)
        stray = sorted({"tables", "defs"} & set(spec))
        if stray:
            raise CertificateError(
                "a %s certificate may not carry %s: its content is the weight "
                "table, and a table or def with no predicate to appear in would "
                "be a key nothing reads -- which is where a blind spot starts"
                % (kind, stray))
        weights = _parse_weights(spec.get("weights"))
        bound = spec.get("bound")
        if not isinstance(bound, int) or isinstance(bound, bool):
            raise CertificateError(
                "bound must be an integer, got %r -- the weights are exact "
                "integers (interop/certificate_export.py scales the rationals) "
                "and the comparison has to be exact too" % (bound,))
        if "occupied" not in spec:
            raise CertificateError(
                "a %s certificate must say which value counts as occupied; "
                "assuming 1 would make the potential depend on a convention "
                "this rechecker invented" % kind)
        occupied = spec["occupied"]
        if not isinstance(occupied, (str, int, bool)):
            raise CertificateError("occupied must be a scalar, got %r" % (occupied,))
    else:
        if "predicate" not in spec:
            raise CertificateError("a certificate must carry a predicate")
        stray = sorted({"weights", "bound", "occupied"} & set(spec))
        if stray:
            raise CertificateError(
                "only a potential certificate carries %s; a %s certificate "
                "states its set of states as a predicate" % (stray, kind))

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
        predicate_src=spec.get("predicate"),
        source=source,
        sha256=sha256,
        binds_ruleset=binds,
        produced_by=spec.get("produced_by"),
        tables=tables,
        macros=macros,
        spec=spec,
        weights=weights,
        bound=bound,
        occupied=occupied,
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
