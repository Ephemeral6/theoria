"""`Invariant` -> a `recheck` certificate, so that "an independent checker
accepts this invariant" becomes a column with a number in it.

`engines.ic3_pdr` speaks boolean CNF: a `Literal` is `(variable index, required
value)`, a `Clause` is a frozenset of them read as a disjunction, and the state
space is `2^n` tuples of bools.  `recheck` speaks a multi-valued symbolic
language: variables carry explicit finite domains, the state space is the full
Cartesian product of those domains, and every edge is *derived* by grounding
guarded rules.  This module is the one place the two vocabularies meet.

    ["and", ["or", ["=", ["var", "pos1"], ["lit", 0]],
                   ["=", ["var", "pos2"], ["lit", 1]]],
            ...]

**This module may import `engines/`.  Nothing in `recheck/` may import this
module.**  That is the direction the whole exercise depends on: the emitter is
allowed to know what the engine found, the checker is not.
`tests/test_ic3bounds_emit.py` enforces the second half the same way
`test_recheck_never_imports_the_engines` enforces the first.

Two rules govern what is here, both load-bearing.

**The two-transcriptions rule.**  This module converts the *invariant* and
nothing else.  The rule set the rechecker reads is `recheck.build_cases`'
independent transcription of the same world, written from the geometry rather
than from the `System` IC3 ran on.  If one module emitted both, "the independent
checker agreed" would be a statement about one program agreeing with itself --
the failure `recheck/README.md` opens by naming.  The two transcriptions are
tied together by an anchor outside both (`interop.peg1d`), never by
construction.

**The count cross-check (`cross_check`, and it raises).**  A verdict alone does
not establish that the translation is faithful.  A translation that drops a
literal from a clause denotes a *different* set of states, and on peg-6 one such
drop still passes all three conditions -- ACCEPT, green column, wrong object.
So the engine's own `check.verify(...).n_satisfying`, counted over the boolean
space, must equal `recheck`'s `stats["n_satisfying"]`, counted over the
multi-valued product.  They are two enumerations of two encodings of what is
supposed to be one set; if the numbers differ the translation is wrong whatever
the verdict says, and this module refuses to emit rather than reporting a green
it has no right to.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from engines.ic3_pdr.check import verify as engine_verify
from engines.ic3_pdr.pdr import Invariant
from engines.ic3_pdr.system import Clause, System, clause_key
from recheck.certificate import SCHEMA as CERTIFICATE_SCHEMA
from recheck.certificate import certificate_from_spec
from recheck.ruleset import RuleSet
from recheck.verify import ACCEPT, recheck

# How a boolean variable's two values are written in a multi-valued domain.
# `(value for False, value for True)`.  The peg rule sets declare `[0, 1]`.
BOOLEAN_VALUES: Tuple[Any, Any] = (0, 1)

KIND = "inductive_invariant"
CLAIM = "unsolvable"


class EmitError(RuntimeError):
    """The translation is not the invariant, or cannot be made into one."""


# ------------------------------------------------------------------ the shape

def ordered_clauses(clauses: Sequence[Clause]) -> Tuple[Clause, ...]:
    """The one order clauses are ever written in: `clause_key`, shortest first.

    Determinism is a requirement here, not a nicety -- the emitted document is
    committed and byte-checked, so a set iteration order would make the same
    invariant produce two different files.
    """
    return tuple(sorted(clauses, key=clause_key))


def literal_to_predicate(system: System, literal: Tuple[int, bool],
                         values: Sequence[Any] = BOOLEAN_VALUES) -> list:
    index, value = literal
    if not 0 <= index < len(system.variables):
        raise EmitError(
            "literal %r names variable index %d, and the system declares %d"
            % (literal, index, len(system.variables)))
    return ["=", ["var", system.variables[index]], ["lit", values[1 if value else 0]]]


def clause_to_predicate(system: System, clause: Clause,
                        values: Sequence[Any] = BOOLEAN_VALUES) -> list:
    """One clause, as an `["or", ...]`.  Literals in `sorted()` order.

    An empty clause becomes `["or"]`, which `recheck` evaluates to false -- the
    honest reading of the empty disjunction.  It is not silently dropped: a CNF
    containing the empty clause is unsatisfiable, and an invariant no state
    satisfies fails `inv_init` on the merits, which is where it should fail.
    """
    return ["or"] + [literal_to_predicate(system, literal, values)
                     for literal in sorted(clause)]


def predicate_of(system: System, clauses: Sequence[Clause],
                 values: Sequence[Any] = BOOLEAN_VALUES) -> list:
    """The whole CNF as a `recheck` predicate.

    An empty clause set becomes `["and"]`, which evaluates to true -- again the
    honest reading, and again not hidden: a predicate every state satisfies
    accepts the goal and fails `goal_break`.
    """
    return ["and"] + [clause_to_predicate(system, clause, values)
                      for clause in ordered_clauses(clauses)]


def render_cnf(system: System, clauses: Sequence[Clause]) -> str:
    """The engine's own rendering, in the emitted order."""
    return system.render_cnf(list(ordered_clauses(clauses)))


# ------------------------------------------------------------ the certificate

def certificate_spec(system: System, clauses: Sequence[Clause], *,
                     name: str,
                     ruleset_name: Optional[str] = None,
                     ruleset_sha256: Optional[str] = None,
                     produced_by: str = "engines/ic3_pdr, via ic3bounds/emit.py",
                     comment: Optional[str] = None,
                     provenance: Optional[Mapping[str, object]] = None,
                     values: Sequence[Any] = BOOLEAN_VALUES) -> Dict[str, object]:
    """A `certificate-v1` document carrying the predicate and nothing else.

    Deliberately thin.  `recheck.certificate._FORBIDDEN` refuses a certificate
    that carries `states`, `edges`, `transitions`, `goal`, `init` or
    `constraint`, and this emitter must not go looking for a way around that:
    everything about the *world* comes from the rule set, and everything here is
    about a set of states.
    """
    spec: Dict[str, object] = {
        "schema": CERTIFICATE_SCHEMA,
        "name": name,
        "kind": KIND,
        "claim": CLAIM,
        "produced_by": produced_by,
        "comment": comment if comment is not None else render_cnf(system, clauses),
        "predicate": predicate_of(system, clauses, values),
    }
    if ruleset_name is not None:
        binding: Dict[str, object] = {"name": ruleset_name}
        if ruleset_sha256:
            binding["sha256"] = ruleset_sha256
        spec["ruleset"] = binding
    if provenance is not None:
        spec["provenance"] = dict(provenance)
    return spec


# -------------------------------------------------------------- the crosscheck

@dataclass
class CrossCheck:
    """Two enumerations of one set of states, and whether they agree."""

    engine_n_states: int
    engine_n_satisfying: int
    engine_conditions: Dict[str, bool] = field(default_factory=dict)
    recheck_n_states: Optional[int] = None
    recheck_n_satisfying: Optional[int] = None
    recheck_conditions: Dict[str, bool] = field(default_factory=dict)
    verdict: Optional[str] = None
    reasons: List[str] = field(default_factory=list)

    @property
    def counts_agree(self) -> bool:
        return (self.recheck_n_satisfying == self.engine_n_satisfying
                and self.recheck_n_states == self.engine_n_states)

    @property
    def accepted(self) -> bool:
        return self.verdict == ACCEPT

    def as_json(self) -> Dict[str, object]:
        return {
            "engine_n_states": self.engine_n_states,
            "engine_n_satisfying": self.engine_n_satisfying,
            "engine_conditions": dict(sorted(self.engine_conditions.items())),
            "recheck_n_states": self.recheck_n_states,
            "recheck_n_satisfying": self.recheck_n_satisfying,
            "recheck_conditions": dict(sorted(self.recheck_conditions.items())),
            "recheck_verdict": self.verdict,
            "counts_agree": self.counts_agree,
            "reasons": list(self.reasons),
            "method": "the engine counts over 2^n boolean tuples; the rechecker "
                      "counts over the product of the declared domains. Two "
                      "encodings of one set of states, enumerated twice.",
        }


def _domain_check(ruleset: RuleSet, system: System,
                  values: Sequence[Any]) -> List[str]:
    """Every variable the predicate can name exists, with both values in range."""
    problems: List[str] = []
    for variable in system.variables:
        index = ruleset.var_index.get(variable)
        if index is None:
            problems.append(
                "the rule set declares no variable %r, so the predicate cannot "
                "denote the set the engine found" % variable)
            continue
        domain = ruleset.domains[index]
        for value in values:
            if value not in domain:
                problems.append(
                    "%s: %r is not in the declared domain %s, so a literal "
                    "translated to it is unsatisfiable rather than false"
                    % (variable, value, sorted(map(str, domain))))
    return problems


def cross_check(system: System, clauses: Sequence[Clause], ruleset: RuleSet,
                spec: Mapping[str, object],
                values: Sequence[Any] = BOOLEAN_VALUES,
                strict: bool = True) -> CrossCheck:
    """Count the invariant twice, in two encodings, and refuse a disagreement.

    This is the guard against a *lenient* translation.  A predicate that drops a
    literal from a clause denotes a strictly smaller set of states; one that
    drops a clause denotes a strictly larger one.  Either can still satisfy all
    three conditions -- on peg-6, dropping `pos5` from the first clause is
    ACCEPTed with 27 states instead of 30 -- and the resulting green column
    would be about a different object than the one the engine converged on.

    The verdict is reported, never enforced: a certificate the rechecker
    *rejects* is a finding about the invariant or the rule set, and it is not
    this function's business to convert it into an exception.  A count mismatch
    is different in kind: it says the two sides are not talking about the same
    set at all, so nothing either of them concluded transfers.
    """
    engine = engine_verify(system, list(clauses))
    result = CrossCheck(
        engine_n_states=engine.n_states,
        engine_n_satisfying=engine.n_satisfying,
        engine_conditions=dict(engine.conditions),
    )

    problems = _domain_check(ruleset, system, values)
    if problems:
        result.reasons.extend(problems)
        if strict:
            raise EmitError("; ".join(problems))
        return result

    verdict = recheck(ruleset, certificate_from_spec(dict(spec)))
    result.verdict = verdict.verdict
    result.recheck_conditions = dict(verdict.conditions)
    result.recheck_n_states = verdict.stats.get("n_states")
    result.recheck_n_satisfying = verdict.stats.get("n_satisfying")
    result.reasons.extend(verdict.reasons)

    if result.recheck_n_satisfying is None:
        message = (
            "the rechecker never counted the states satisfying the predicate "
            "(verdict %s: %s), so the translation is unchecked -- an unchecked "
            "translation is not a weaker result, it is no result"
            % (verdict.verdict, "; ".join(verdict.reasons) or "no reason given"))
        result.reasons.append(message)
        if strict:
            raise EmitError(message)
        return result

    # The rechecker's `n_satisfying` is counted on the subspace the rule set's
    # well-formedness constraint admits.  The peg rule sets declare no
    # constraint, so the two counts are over the same space; if a rule set ever
    # does declare one, the comparison below would be between different spaces
    # and must not be made silently.
    anywhere = verdict.stats.get("n_satisfying_anywhere")
    if anywhere is not None and anywhere != result.recheck_n_satisfying:
        message = (
            "the rule set declares a well-formedness constraint: %d states "
            "satisfy the predicate, %d of them inside the constraint. The "
            "engine counted over the whole boolean space, so the two numbers "
            "are not comparable and the cross-check is refused rather than "
            "answered" % (anywhere, result.recheck_n_satisfying))
        result.reasons.append(message)
        if strict:
            raise EmitError(message)
        return result

    if result.recheck_n_states != result.engine_n_states:
        message = (
            "state spaces differ: the engine enumerated %d states, the "
            "rechecker %d. The two are not describing the same world"
            % (result.engine_n_states, result.recheck_n_states))
        result.reasons.append(message)
        if strict:
            raise EmitError(message)
        return result

    if result.recheck_n_satisfying != result.engine_n_satisfying:
        message = (
            "TRANSLATION MISMATCH: the engine's invariant holds on %d of %d "
            "states, the emitted predicate on %d of %d. The predicate denotes a "
            "%s set than the invariant, so any verdict about it -- including "
            "ACCEPT -- is a verdict about a different object"
            % (result.engine_n_satisfying, result.engine_n_states,
               result.recheck_n_satisfying, result.recheck_n_states,
               "smaller" if result.recheck_n_satisfying < result.engine_n_satisfying
               else "larger"))
        result.reasons.append(message)
        if strict:
            raise EmitError(message)
    return result


def emit(system: System, invariant: Invariant, ruleset: RuleSet, *,
         name: str,
         ruleset_name: Optional[str] = None,
         ruleset_sha256: Optional[str] = None,
         produced_by: str = "engines/ic3_pdr, via ic3bounds/emit.py",
         comment: Optional[str] = None,
         provenance: Optional[Mapping[str, object]] = None,
         values: Sequence[Any] = BOOLEAN_VALUES,
         strict: bool = True) -> Tuple[Dict[str, object], CrossCheck]:
    """Translate, then prove the translation faithful before handing it back.

    Returns `(certificate spec, cross-check)`.  Raises `EmitError` if the two
    counts disagree, which is the only failure mode this function treats as
    fatal.
    """
    clauses = ordered_clauses(invariant.clauses)
    spec = certificate_spec(
        system, clauses, name=name,
        ruleset_name=ruleset_name if ruleset_name is not None else ruleset.name,
        ruleset_sha256=ruleset_sha256,
        produced_by=produced_by, comment=comment, provenance=provenance,
        values=values,
    )
    checked = cross_check(system, clauses, ruleset, spec, values=values, strict=strict)
    return spec, checked
