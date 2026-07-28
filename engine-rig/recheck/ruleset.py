"""A rule set: finite variables, guarded rules, and the transition relation
this rechecker derives from them.

The single most important line in this file is that **the transition relation is
never read**.  A rule set declares variables with explicit finite domains and a
list of guarded rules; the state space is the full Cartesian product of those
domains and every edge is computed here, by grounding the rules.  A world
description that shipped its own edge list would let the same program produce
the answer and the check on the answer, which is the failure this whole package
exists to make impossible.

Semantics, taken verbatim from the DSL contract the two books compile through
(`frame persist`, `conflict exclusive`, `cascade single_frame`):

* **frame persist** -- a variable no firing rule writes is unchanged.  That is
  what makes `step` total, so every state has exactly one successor per action
  and "the certificate forgot to mention that transition" is not expressible.
* **conflict exclusive** -- two rules firing on the same action and writing the
  same variable is an *error*, not a precedence question.  Checked over the
  whole product, not spot-checked.
* **cascade single_frame** -- every guard and every effect expression reads the
  pre-state.  Effects apply together.

Three obligations are discharged on the rule set alone, before any certificate
is looked at:

  `step_single_valued`  no (state, action) has two rules claiming one variable
  `effects_in_domain`   no rule can drive a variable outside its declared domain
  `constraint_sound`    the declared well-formedness constraint, if any, holds
                        at the initial state and is closed under every action

The third is what makes it safe to restrict the checks to a subspace.  A rule
set may say "the player and the boxes are on distinct cells" -- without which
the sokoban deadlock theorems would be rejected on states the grounded task
cannot represent -- but it may not *assume* it.  A constraint that is not
inductive is refused, so shrinking the state space to hide an escaping
transition fails here rather than passing quietly downstream.
"""

import hashlib
import itertools
import json
import os
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from recheck.expr import (
    Compiled,
    ExprError,
    Macro,
    Scope,
    State,
    Table,
    Value,
    compile_expr,
    compile_guard,
    compile_macros,
    compile_predicate,
    parse_macros,
    parse_tables,
    render,
)

SCHEMA = "engine-rig/recheck/ruleset-v1"

# A product bigger than this is refused rather than attempted.  Every case this
# rig carries is under 5 000 states; the cap exists so that a mistyped domain
# fails in a second with a legible message instead of paging the machine out.
MAX_STATES = 1_000_000

_RULESET_KEYS = {
    "schema", "name", "comment", "provenance", "variables", "actions",
    "tables", "defs", "constraint", "init", "goal", "rules",
}
_RULE_KEYS = {"name", "comment", "action", "guard", "owns", "effects"}


class RuleSetError(ValueError):
    """A malformed rule set, or one whose own obligations do not hold."""


@dataclass(frozen=True)
class Variable:
    name: str
    domain: Tuple[Value, ...]


@dataclass(frozen=True)
class Rule:
    name: str
    owns: Tuple[str, ...]
    guard_src: object
    effects_src: Mapping[str, object]
    guard: Compiled
    effects: Tuple[Tuple[int, Compiled], ...]        # (variable index, expression)

    def rendering(self) -> str:
        writes = ", ".join(
            "%s := %s" % (name, render(src))
            for name, src in sorted(self.effects_src.items())
        )
        return "%s: when %s then %s" % (self.name, render(self.guard_src), writes)


@dataclass
class Obligations:
    """What the rule set owes about itself, and the witnesses if it defaults."""

    conditions: Dict[str, bool] = field(default_factory=dict)
    witnesses: Dict[str, List[str]] = field(default_factory=dict)

    @property
    def holds(self) -> bool:
        return bool(self.conditions) and all(self.conditions.values())

    def as_json(self) -> Dict[str, object]:
        return {
            "conditions": dict(sorted(self.conditions.items())),
            "counterexamples": {k: list(v) for k, v in sorted(self.witnesses.items())},
        }


class RuleSet:
    """A grounded, fully enumerated world.  Built from JSON, never from code."""

    def __init__(self, spec: Mapping[str, object], source: Optional[str] = None,
                 max_states: int = MAX_STATES) -> None:
        self.source = source
        self.spec = spec
        self.sha256 = ""
        self._parse(spec, max_states)
        self._transitions: Optional[Tuple[Tuple[int, ...], ...]] = None
        self._obligations: Optional[Obligations] = None

    # ------------------------------------------------------------- parsing

    def _parse(self, spec: Mapping[str, object], max_states: int) -> None:
        if not isinstance(spec, dict):
            raise RuleSetError("a rule set must be a JSON object")
        unknown = set(spec) - _RULESET_KEYS
        if unknown:
            raise RuleSetError("unknown top-level keys %s" % sorted(unknown))
        if spec.get("schema") != SCHEMA:
            raise RuleSetError("schema must be %r, got %r" % (SCHEMA, spec.get("schema")))

        self.name = str(spec.get("name") or "<unnamed>")
        self.provenance = spec.get("provenance") or {}

        raw_vars = spec.get("variables")
        if not isinstance(raw_vars, list) or not raw_vars:
            raise RuleSetError("variables must be a non-empty list")
        variables: List[Variable] = []
        for entry in raw_vars:
            if not isinstance(entry, dict) or set(entry) - {"name", "domain", "comment"}:
                raise RuleSetError("variable entry %r is malformed" % (entry,))
            name = entry.get("name")
            domain = entry.get("domain")
            if not isinstance(name, str) or not name:
                raise RuleSetError("variable name must be a non-empty string")
            if not isinstance(domain, list) or not domain:
                raise RuleSetError("variable %s: domain must be a non-empty list" % name)
            values = tuple(domain)
            for value in values:
                if not isinstance(value, (str, int, bool)):
                    raise RuleSetError("variable %s: %r is not a scalar" % (name, value))
            if len(set(values)) != len(values):
                raise RuleSetError("variable %s: duplicate value in the domain" % name)
            variables.append(Variable(name=name, domain=values))
        names = [v.name for v in variables]
        if len(set(names)) != len(names):
            raise RuleSetError("duplicate variable name")
        self.variables: Tuple[Variable, ...] = tuple(variables)
        self.var_index: Dict[str, int] = {v.name: i for i, v in enumerate(self.variables)}
        self.domains: Tuple[frozenset, ...] = tuple(frozenset(v.domain) for v in self.variables)

        size = 1
        for variable in self.variables:
            size *= len(variable.domain)
        if size > max_states:
            raise RuleSetError(
                "the declared domains make %d states, over the %d cap; this "
                "rechecker enumerates, so a world that large needs a solver "
                "behind it rather than a bigger loop" % (size, max_states)
            )
        self.n_states = size

        actions = spec.get("actions")
        if not isinstance(actions, list) or not actions:
            raise RuleSetError("actions must be a non-empty list")
        if not all(isinstance(a, str) for a in actions):
            raise RuleSetError("action labels must be strings")
        if len(set(actions)) != len(actions):
            raise RuleSetError("duplicate action label")
        self.actions: Tuple[str, ...] = tuple(actions)

        try:
            tables: Dict[str, Table] = parse_tables(spec.get("tables"), "rule set")
            macros: Dict[str, Macro] = parse_macros(spec.get("defs"), "rule set")
        except ExprError as exc:
            raise RuleSetError(str(exc)) from exc
        self.tables = tables

        base = Scope(variables=self.var_index, tables=tables, macros={},
                     macro_arity={}, allow_action=True)
        try:
            self.scope = compile_macros(macros, base)
        except ExprError as exc:
            raise RuleSetError("defs: %s" % exc) from exc
        # Certificates read states only: no `act`, but the same tables and defs.
        self.state_scope = Scope(
            variables=self.var_index, tables=tables, macros=self.scope.macros,
            macro_arity=self.scope.macro_arity, allow_action=False,
        )

        self.init_src = spec.get("init")
        self.init: Tuple[State, ...] = self._parse_init(self.init_src)

        if "goal" not in spec:
            raise RuleSetError("a rule set must state its goal")
        self.goal_src = spec["goal"]
        try:
            self.goal = compile_predicate(self.goal_src, self.state_scope, "goal")
        except ExprError as exc:
            raise RuleSetError("goal: %s" % exc) from exc

        self.constraint_src = spec.get("constraint")
        if self.constraint_src is None:
            self.constraint: Callable[[State], bool] = lambda state: True
        else:
            try:
                self.constraint = compile_predicate(
                    self.constraint_src, self.state_scope, "constraint")
            except ExprError as exc:
                raise RuleSetError("constraint: %s" % exc) from exc

        self.rules: Tuple[Rule, ...] = self._parse_rules(spec.get("rules"))

    def _parse_init(self, raw: object) -> Tuple[State, ...]:
        if isinstance(raw, dict):
            raw = [raw]
        if not isinstance(raw, list) or not raw:
            raise RuleSetError("init must be an assignment or a non-empty list of them")
        out: List[State] = []
        for entry in raw:
            if not isinstance(entry, dict):
                raise RuleSetError("init entry %r is not an assignment" % (entry,))
            missing = set(self.var_index) - set(entry)
            extra = set(entry) - set(self.var_index)
            if missing or extra:
                raise RuleSetError(
                    "init must assign exactly the declared variables "
                    "(missing %s, unknown %s)" % (sorted(missing), sorted(extra))
                )
            state = []
            for variable in self.variables:
                value = entry[variable.name]
                if value not in self.domains[self.var_index[variable.name]]:
                    raise RuleSetError(
                        "init: %s = %r is outside its declared domain"
                        % (variable.name, value)
                    )
                state.append(value)
            out.append(tuple(state))
        if len(set(out)) != len(out):
            raise RuleSetError("duplicate initial state")
        return tuple(out)

    def _parse_rules(self, raw: object) -> Tuple[Rule, ...]:
        if not isinstance(raw, list) or not raw:
            raise RuleSetError("rules must be a non-empty list")
        rules: List[Rule] = []
        seen: set = set()
        for entry in raw:
            if not isinstance(entry, dict):
                raise RuleSetError("rule entry %r is malformed" % (entry,))
            unknown = set(entry) - _RULE_KEYS
            if unknown:
                raise RuleSetError("rule: unknown keys %s" % sorted(unknown))
            name = entry.get("name")
            if not isinstance(name, str) or not name:
                raise RuleSetError("rule name must be a non-empty string")
            if name in seen:
                raise RuleSetError("duplicate rule name %r" % name)
            seen.add(name)

            effects_src = entry.get("effects")
            if not isinstance(effects_src, dict) or not effects_src:
                raise RuleSetError("rule %s: effects must be a non-empty object" % name)
            for target in effects_src:
                if target not in self.var_index:
                    raise RuleSetError(
                        "rule %s: writes %r, which is not a declared variable"
                        % (name, target))

            owns = entry.get("owns")
            if owns is None:
                owns = sorted(effects_src)
            if not isinstance(owns, list) or not all(isinstance(o, str) for o in owns):
                raise RuleSetError("rule %s: owns must be a list of variable names" % name)
            if sorted(owns) != sorted(effects_src):
                raise RuleSetError(
                    "rule %s: owns %s but writes %s -- under `conflict exclusive` a "
                    "rule owns exactly what it writes, and a mismatch would let two "
                    "rules write one variable without either declaring it"
                    % (name, sorted(owns), sorted(effects_src))
                )

            guard_src = entry.get("guard")
            if guard_src is None:
                raise RuleSetError("rule %s: no guard" % name)
            action = entry.get("action")
            if action is not None:
                if action not in self.actions:
                    raise RuleSetError("rule %s: action %r is not declared" % (name, action))
                guard_src = ["and", ["=", ["act"], ["lit", action]], guard_src]

            try:
                guard = compile_guard(guard_src, self.scope, "rule %s guard" % name)
            except ExprError as exc:
                raise RuleSetError("rule %s: %s" % (name, exc)) from exc
            compiled_effects: List[Tuple[int, Compiled]] = []
            for target in sorted(effects_src):
                try:
                    compiled_effects.append(
                        (self.var_index[target],
                         compile_expr(effects_src[target], self.scope))
                    )
                except ExprError as exc:
                    raise RuleSetError("rule %s effect %s: %s" % (name, target, exc)) from exc

            rules.append(Rule(
                name=name, owns=tuple(sorted(owns)), guard_src=guard_src,
                effects_src=dict(effects_src), guard=guard,
                effects=tuple(compiled_effects),
            ))
        return tuple(rules)

    # ----------------------------------------------------------- the world

    def states(self) -> List[State]:
        """The whole product, in a fixed order.  Not a list anyone supplied."""
        return [
            tuple(combo)
            for combo in itertools.product(*[v.domain for v in self.variables])
        ]

    def fired(self, state: State, action: str) -> List[str]:
        return [rule.name for rule in self.rules
                if rule.guard(state, action, ())]

    def step(self, state: State, action: str) -> State:
        """One action, one successor.  Total by `frame persist`."""
        result = list(state)
        claimed: Dict[int, str] = {}
        for rule in self.rules:
            if not rule.guard(state, action, ()):
                continue
            for index, effect in rule.effects:
                owner = claimed.get(index)
                if owner is not None and owner != rule.name:
                    raise RuleSetError(
                        "conflict exclusive violated: rules %s and %s both write "
                        "%s on action %s in state %s"
                        % (owner, rule.name, self.variables[index].name, action,
                           self.render_state(state))
                    )
                claimed[index] = rule.name
                result[index] = effect(state, action, ())
        return tuple(result)

    def transitions(self) -> Tuple[Tuple[int, ...], ...]:
        """Successor index per (state index, action index).  Computed once."""
        if self._transitions is not None:
            return self._transitions
        states = self.states()
        index_of = {state: i for i, state in enumerate(states)}
        rows: List[Tuple[int, ...]] = []
        for state in states:
            row: List[int] = []
            for action in self.actions:
                successor = self.step(state, action)
                target = index_of.get(successor)
                if target is None:
                    # Caught properly by `effects_in_domain`; this is the guard
                    # that keeps the table well-typed while that runs.
                    target = -1
                row.append(target)
            rows.append(tuple(row))
        self._transitions = tuple(rows)
        return self._transitions

    # ------------------------------------------------------- its own dues

    def obligations(self, max_witnesses: int = 6) -> Obligations:
        """`step_single_valued`, `effects_in_domain`, `constraint_sound`."""
        if self._obligations is not None:
            return self._obligations

        result = Obligations()
        single: List[str] = []
        in_domain: List[str] = []
        states = self.states()

        for state in states:
            for action in self.actions:
                claimed: Dict[int, str] = {}
                for rule in self.rules:
                    if not rule.guard(state, action, ()):
                        continue
                    for index, effect in rule.effects:
                        owner = claimed.get(index)
                        if owner is not None and owner != rule.name:
                            if len(single) < max_witnesses:
                                single.append(
                                    "%s on %s: %s and %s both write %s"
                                    % (self.render_state(state), action, owner,
                                       rule.name, self.variables[index].name))
                        claimed[index] = rule.name
                        value = effect(state, action, ())
                        if value not in self.domains[index]:
                            if len(in_domain) < max_witnesses:
                                in_domain.append(
                                    "%s on %s: rule %s sets %s := %r, outside its "
                                    "declared domain"
                                    % (self.render_state(state), action, rule.name,
                                       self.variables[index].name, value))

        result.conditions["step_single_valued"] = not single
        result.conditions["effects_in_domain"] = not in_domain
        if single:
            result.witnesses["step_single_valued"] = single
        if in_domain:
            result.witnesses["effects_in_domain"] = in_domain

        if self.constraint_src is not None:
            init_bad = [self.render_state(s) for s in self.init if not self.constraint(s)]
            closed_bad: List[str] = []
            # Only derive the relation once the step is known to be a function
            # into the product; otherwise `step` would raise on the way past.
            if not in_domain and not single:
                rows = self.transitions()
                inside = [self.constraint(s) for s in states]
                for i, state in enumerate(states):
                    if not inside[i]:
                        continue
                    for a, action in enumerate(self.actions):
                        j = rows[i][a]
                        if j < 0 or not inside[j]:
                            if len(closed_bad) < max_witnesses:
                                closed_bad.append(
                                    "%s -%s-> %s leaves the declared constraint"
                                    % (self.render_state(state), action,
                                       self.render_state(states[j]) if j >= 0 else "<off-domain>"))
            result.conditions["constraint_init"] = not init_bad
            result.conditions["constraint_closed"] = not closed_bad
            if init_bad:
                result.witnesses["constraint_init"] = init_bad
            if closed_bad:
                result.witnesses["constraint_closed"] = closed_bad

        self._obligations = result
        return result

    # ------------------------------------------------------------ rendering

    def render_state(self, state: State) -> str:
        return "{%s}" % ", ".join(
            "%s=%s" % (variable.name, state[i])
            for i, variable in enumerate(self.variables)
        )

    def summary(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "n_variables": len(self.variables),
            "n_states": self.n_states,
            "n_actions": len(self.actions),
            "n_rules": len(self.rules),
            "constraint": render(self.constraint_src) if self.constraint_src else None,
            "goal": render(self.goal_src),
            "rules": [rule.rendering() for rule in self.rules],
            "source": os.path.basename(self.source) if self.source else None,
            "sha256": self.sha256,
        }


def canonical_text(spec: Mapping[str, object]) -> str:
    """The one serialisation a rule set's digest is taken over.

    `load_ruleset` hashes the file's own bytes, because "the certificate is
    bound to *this file*" is what the binding means.  An in-memory rule set has
    no file, so it is hashed over this form -- which is exactly the form
    `build_cases` writes, so a spec loaded from a committed case and hashed here
    gives the same digest the file does.  If the two forms drifted, a binding
    check would start failing for a reason that had nothing to do with the
    binding.
    """
    return json.dumps(spec, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def sha256_of(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def load_ruleset(path: str, max_states: int = MAX_STATES) -> RuleSet:
    with open(path, "r", encoding="utf-8") as handle:
        spec = json.load(handle)
    rules = RuleSet(spec, source=path, max_states=max_states)
    rules.sha256 = sha256_of(path)
    return rules


def ruleset_from_spec(spec: Mapping[str, object]) -> RuleSet:
    """For tests and forgeries: a rule set with no file behind it."""
    rules = RuleSet(spec)
    rules.sha256 = hashlib.sha256(canonical_text(spec).encode("utf-8")).hexdigest()
    return rules
