"""A typed-STRIPS reader and grounder, owned by this track.

`deadlock_carver` proves *conditional* unsolvability theorems — "this pattern of
ground atoms, plus not-being-the-goal, implies dead" — and a theorem of that
shape is a statement about a **grounded task**: a finite atom set, a finite
action set with add/delete lists, a goal. Consuming one therefore needs a
grounded task on this side of the boundary too.

It has to be *this side's*. The certificate must not be allowed to supply the
transition relation it claims to be closed under; that is the same discipline
`ic3_certificate` states as "no `moves` field, this is deliberate", for the same
reason — a certificate that picks its own action set is closed under an action
set of its own choosing. So the PDDL is parsed and grounded here, by code that
shares nothing with the producer, and the result is cross-checked against the
certificate's own accounting (see `deadlock_certificate.cross_check`).

Scope, stated so it is not mistaken for a PDDL implementation: the subset is the
one `engine-rig`'s fixture domain is written in — `:strips :typing`, flat
(untyped-supertype) type declarations, conjunctive preconditions, conjunctive
effects with `not` for deletes. No `:equality`, no negative preconditions, no
quantifiers, no conditional effects, no numeric fluents, no type hierarchy.
Everything outside that raises `StripsError`. Silently ignoring a construct
would mean grounding a *different* task than the file describes, and the whole
point of this module is that the task is right.
"""

from __future__ import annotations

import itertools
import os
import re
from dataclasses import dataclass
from typing import Dict, FrozenSet, Iterable, List, Optional, Sequence, Tuple


class StripsError(Exception):
    """The PDDL is outside the accepted subset, or is not self-consistent."""


# --------------------------------------------------------------- s-expressions

Sexp = object  # str | List[Sexp]


def _tokenize(text: str) -> List[str]:
    without_comments = re.sub(r";[^\n]*", "", text)
    spaced = without_comments.replace("(", " ( ").replace(")", " ) ")
    return spaced.split()


def parse_sexp(text: str) -> Sexp:
    """The whole file as one s-expression. Trailing junk is an error."""
    tokens = _tokenize(text)
    if not tokens:
        raise StripsError("empty PDDL input")
    value, rest = _parse_one(tokens, 0)
    if rest != len(tokens):
        raise StripsError("trailing tokens after the top-level form: %r"
                          % tokens[rest:rest + 5])
    return value


def _parse_one(tokens: Sequence[str], i: int) -> Tuple[Sexp, int]:
    if i >= len(tokens):
        raise StripsError("unexpected end of input")
    token = tokens[i]
    if token == ")":
        raise StripsError("unbalanced ')' at token %d" % i)
    if token != "(":
        return token.lower(), i + 1
    out: List[Sexp] = []
    i += 1
    while True:
        if i >= len(tokens):
            raise StripsError("unbalanced '(' -- input ended inside a form")
        if tokens[i] == ")":
            return out, i + 1
        value, i = _parse_one(tokens, i)
        out.append(value)


def _head(form: Sexp) -> str:
    if not isinstance(form, list) or not form or not isinstance(form[0], str):
        raise StripsError("expected a form headed by a symbol, got %r" % (form,))
    return form[0]


def _keyword_pairs(body: Sequence[Sexp], where: str) -> Dict[str, Sexp]:
    """`:parameters (...) :precondition (...)` -- a flat alternating list.

    An action body is spelled this way, unlike a domain or problem body whose
    parts are each their own `(:key ...)` form. The two shapes get two readers
    rather than one lenient one.
    """
    out: Dict[str, Sexp] = {}
    i = 0
    while i < len(body):
        key = body[i]
        if not isinstance(key, str) or not key.startswith(":"):
            raise StripsError("expected a `:keyword` in %s, got %r" % (where, key))
        if i + 1 >= len(body):
            raise StripsError("`%s` in %s has no value" % (key, where))
        name = key[1:]
        if name in out:
            raise StripsError("`%s` appears twice in %s" % (key, where))
        out[name] = body[i + 1]
        i += 2
    return out


def _sections(body: Sequence[Sexp]) -> Dict[str, Sexp]:
    """`(:key ...)` sub-forms, keyed without the colon. Duplicates are an error."""
    out: Dict[str, Sexp] = {}
    for form in body:
        key = _head(form)
        if not key.startswith(":"):
            raise StripsError("expected a `:keyword` section, got %r" % (key,))
        name = key[1:]
        if name in out:
            raise StripsError("section `:%s` appears twice" % name)
        out[name] = form[1:]
    return out


# ------------------------------------------------------------------- the task

@dataclass(frozen=True, order=True)
class Atom:
    """A ground atom. `args` are object names; the predicate is `name`."""

    name: str
    args: Tuple[str, ...]

    def __str__(self) -> str:
        return "%s(%s)" % (self.name, ",".join(self.args)) if self.args else self.name

    @staticmethod
    def parse(text: str) -> "Atom":
        """`at(b1,c12)` -> Atom. The rendering `deadlock_carver` emits."""
        match = re.fullmatch(r"\s*([\w-]+)\s*(?:\(\s*([^()]*)\s*\))?\s*", text)
        if not match:
            raise StripsError("not an atom rendering: %r" % text)
        args = match.group(2)
        parts = tuple(a.strip() for a in args.split(",")) if args and args.strip() else ()
        if any(not a for a in parts):
            raise StripsError("empty argument in atom rendering: %r" % text)
        return Atom(match.group(1), parts)


@dataclass(frozen=True)
class GroundAction:
    name: str
    args: Tuple[str, ...]
    pre: FrozenSet[Atom]
    add: FrozenSet[Atom]
    dele: FrozenSet[Atom]

    def __str__(self) -> str:
        return "(%s %s)" % (self.name, " ".join(self.args))

    def applicable(self, state: FrozenSet[Atom]) -> bool:
        return self.pre <= state

    def apply(self, state: FrozenSet[Atom]) -> FrozenSet[Atom]:
        return (state - self.dele) | self.add


@dataclass(frozen=True)
class ActionSchema:
    name: str
    params: Tuple[Tuple[str, str], ...]     # (?var, type)
    pre: Tuple[Tuple[str, Tuple[str, ...]], ...]
    add: Tuple[Tuple[str, Tuple[str, ...]], ...]
    dele: Tuple[Tuple[str, Tuple[str, ...]], ...]


@dataclass(frozen=True)
class StripsTask:
    """A grounded task: actions with the statics stripped out of them."""

    domain: str
    problem: str
    types: Tuple[str, ...]
    objects: Tuple[Tuple[str, str], ...]        # (object, type), sorted
    init: FrozenSet[Atom]                       # statics included
    goal: FrozenSet[Atom]
    actions: Tuple[GroundAction, ...]           # deterministic order
    static_predicates: Tuple[str, ...]
    fluent_predicates: Tuple[str, ...]

    def objects_of(self, type_name: str) -> Tuple[str, ...]:
        return tuple(o for o, t in self.objects if t == type_name)

    def type_of(self, obj: str) -> str:
        for name, type_name in self.objects:
            if name == obj:
                return type_name
        raise StripsError("no such object: %r" % obj)

    @property
    def statics(self) -> FrozenSet[Atom]:
        return frozenset(a for a in self.init if a.name in self.static_predicates)

    @property
    def fluent_init(self) -> FrozenSet[Atom]:
        return frozenset(a for a in self.init if a.name in self.fluent_predicates)

    def action_named(self, rendering: str) -> Optional[GroundAction]:
        """Look one up by `(push c11 c12 c13 b1 right)`, the producer's spelling."""
        wanted = tuple(rendering.strip().strip("()").split())
        for action in self.actions:
            if (action.name,) + action.args == wanted:
                return action
        return None


# ------------------------------------------------------------------- parsing

_REQUIREMENTS_OK = {":strips", ":typing"}


def parse_domain(text: str) -> Tuple[str, Dict[str, int], Tuple[str, ...], Tuple[ActionSchema, ...]]:
    form = parse_sexp(text)
    if not isinstance(form, list) or _head(form) != "define":
        raise StripsError("a domain file must be a `(define ...)` form")
    if not (isinstance(form[1], list) and form[1][:1] == ["domain"]):
        raise StripsError("expected `(domain <name>)` as the first element")
    name = form[1][1]

    # `:action` repeats once per action, so it is walked separately below and kept
    # out of the duplicate-refusing section map.
    sections = _sections([f for f in form[2:] if _head(f) != ":action"])
    unknown = set(sections) - {"requirements", "types", "predicates", "constants"}
    if unknown:
        raise StripsError("unsupported domain section(s): %s" % sorted(unknown))
    if "constants" in sections:
        raise StripsError("`:constants` is outside the accepted subset")

    for requirement in sections.get("requirements", []):
        if requirement not in _REQUIREMENTS_OK:
            raise StripsError("unsupported requirement %r (this reader accepts %s)"
                              % (requirement, sorted(_REQUIREMENTS_OK)))

    types = tuple(t for t in sections.get("types", []))
    for type_name in types:
        if not isinstance(type_name, str):
            raise StripsError("type hierarchies (`- supertype`) are outside the subset")

    arities: Dict[str, int] = {}
    for predicate in sections.get("predicates", []):
        pname, params = _typed_params(predicate)
        for _, type_name in params:
            if type_name not in types:
                raise StripsError("predicate %r uses undeclared type %r" % (pname, type_name))
        arities[pname] = len(params)

    # `:action` appears once per action, so `_sections` (which refuses duplicates)
    # cannot be used for it; walk the body instead.
    schemas: List[ActionSchema] = []
    for sub in form[2:]:
        if _head(sub) == ":action":
            schemas.append(_parse_action(sub, arities, types))
    if not schemas:
        raise StripsError("domain %r declares no actions" % name)
    return name, arities, types, tuple(schemas)


def _typed_params(form: Sexp) -> Tuple[str, Tuple[Tuple[str, str], ...]]:
    """`(at ?b - box ?c - cell)` -> ("at", (("?b","box"), ("?c","cell")))."""
    if not isinstance(form, list) or not form:
        raise StripsError("expected a typed parameter list, got %r" % (form,))
    name = form[0]
    rest = list(form[1:])
    params: List[Tuple[str, str]] = []
    pending: List[str] = []
    while rest:
        token = rest.pop(0)
        if token == "-":
            if not rest:
                raise StripsError("`-` at the end of a parameter list in %r" % name)
            type_name = rest.pop(0)
            if not pending:
                raise StripsError("`- %s` with nothing to type in %r" % (type_name, name))
            params.extend((p, type_name) for p in pending)
            pending = []
        else:
            pending.append(token)
    if pending:
        raise StripsError("untyped parameter(s) %s in %r -- `:typing` requires a type "
                          "on every one" % (pending, name))
    return name, tuple(params)


def _parse_action(form: Sexp, arities: Dict[str, int], types: Tuple[str, ...]) -> ActionSchema:
    name = form[1]
    sections = _keyword_pairs(form[2:], "action %r" % name)
    unknown = set(sections) - {"parameters", "precondition", "effect"}
    if unknown:
        raise StripsError("action %r has unsupported section(s): %s" % (name, sorted(unknown)))
    if "parameters" not in sections or "effect" not in sections:
        raise StripsError("action %r needs `:parameters` and `:effect`" % name)

    _, params = _typed_params(["_"] + list(sections["parameters"]))
    for _, type_name in params:
        if type_name not in types:
            raise StripsError("action %r uses undeclared type %r" % (name, type_name))
    bound = {p for p, _ in params}

    def literals(body: Optional[Sexp], where: str, allow_not: bool):
        out_pos: List[Tuple[str, Tuple[str, ...]]] = []
        out_neg: List[Tuple[str, Tuple[str, ...]]] = []
        for item in _conjuncts(body, name, where):
            negated = _head(item) == "not"
            if negated:
                if not allow_not:
                    raise StripsError("negative %s in action %r -- outside the subset "
                                      "(this reader will not approximate it)" % (where, name))
                if len(item) != 2:
                    raise StripsError("malformed `not` in action %r" % name)
                item = item[1]
            predicate = _head(item)
            args = tuple(item[1:])
            if predicate not in arities:
                raise StripsError("action %r mentions undeclared predicate %r" % (name, predicate))
            if len(args) != arities[predicate]:
                raise StripsError("action %r applies %r to %d argument(s), declared %d"
                                  % (name, predicate, len(args), arities[predicate]))
            for arg in args:
                if not arg.startswith("?"):
                    raise StripsError("action %r mentions the constant %r -- `:constants` "
                                      "is outside the subset" % (name, arg))
                if arg not in bound:
                    raise StripsError("action %r mentions unbound variable %r" % (name, arg))
            (out_neg if negated else out_pos).append((predicate, args))
        return tuple(out_pos), tuple(out_neg)

    pre, _ = literals(sections.get("precondition"), "precondition", allow_not=False)
    add, dele = literals(sections["effect"], "effect", allow_not=True)
    if not add and not dele:
        raise StripsError("action %r has an empty effect" % name)
    return ActionSchema(name, params, pre, add, dele)


def _conjuncts(body: Optional[Sexp], name: str, where: str) -> List[Sexp]:
    if body is None:
        return []
    if not isinstance(body, list):
        raise StripsError("action %r has a malformed %s" % (name, where))
    if _head(body) == "and":
        parts = body[1:]
    else:
        parts = [body]
    for part in parts:
        if not isinstance(part, list):
            raise StripsError("action %r has a malformed %s" % (name, where))
        if _head(part) in ("or", "imply", "forall", "exists", "when"):
            raise StripsError("action %r uses `%s` in its %s -- outside the subset"
                              % (name, _head(part), where))
    return parts


def parse_problem(text: str, arities: Dict[str, int], types: Tuple[str, ...]):
    form = parse_sexp(text)
    if not isinstance(form, list) or _head(form) != "define":
        raise StripsError("a problem file must be a `(define ...)` form")
    if not (isinstance(form[1], list) and form[1][:1] == ["problem"]):
        raise StripsError("expected `(problem <name>)` as the first element")
    name = form[1][1]

    sections = _sections(form[2:])
    unknown = set(sections) - {"domain", "objects", "init", "goal"}
    if unknown:
        raise StripsError("unsupported problem section(s): %s" % sorted(unknown))
    domain = sections["domain"][0]

    _, objects = _typed_params(["_"] + list(sections.get("objects", [])))
    for _, type_name in objects:
        if type_name not in types:
            raise StripsError("problem %r declares an object of undeclared type %r"
                              % (name, type_name))
    names = [o for o, _ in objects]
    if len(set(names)) != len(names):
        raise StripsError("problem %r declares an object twice" % name)

    def ground_atoms(forms: Sequence[Sexp], where: str) -> FrozenSet[Atom]:
        out = []
        for item in forms:
            if not isinstance(item, list):
                raise StripsError("malformed %s in problem %r" % (where, name))
            if _head(item) == "not":
                raise StripsError("negative literal in the %s of problem %r -- outside "
                                  "the subset" % (where, name))
            predicate = _head(item)
            args = tuple(item[1:])
            if predicate not in arities:
                raise StripsError("problem %r mentions undeclared predicate %r"
                                  % (name, predicate))
            if len(args) != arities[predicate]:
                raise StripsError("problem %r applies %r to %d argument(s), declared %d"
                                  % (name, predicate, len(args), arities[predicate]))
            for arg in args:
                if arg not in names:
                    raise StripsError("problem %r mentions undeclared object %r"
                                      % (name, arg))
            out.append(Atom(predicate, args))
        return frozenset(out)

    init = ground_atoms(sections.get("init", []), "init")
    goal_forms = sections.get("goal", [])
    if len(goal_forms) != 1:
        raise StripsError("problem %r has a malformed goal" % name)
    body = goal_forms[0]
    goal = ground_atoms(body[1:] if _head(body) == "and" else [body], "goal")
    if not goal:
        raise StripsError("problem %r has an empty goal" % name)
    return name, domain, tuple(objects), init, goal


# ------------------------------------------------------------------ grounding

def ground(domain_text: str, problem_text: str) -> StripsTask:
    """Domain + problem -> a grounded task, statics stripped from the actions.

    Two things happen here that a reader should know about because they change
    the action *count*, which is the number cross-checked against the producer:

    * an instance whose static preconditions are not in `init` is discarded
      outright — that is what makes a wall a wall, and a corner provable;
    * static atoms are then removed from the surviving preconditions, so the
      atoms an action talks about are exactly the atoms a state contains.

    Parameters are **not** assumed distinct: PDDL does not say they are, and the
    static filter prunes the degenerate bindings on this domain anyway. Assuming
    it would be assuming a fact about the level into the action set.
    """
    domain_name, arities, types, schemas = parse_domain(domain_text)
    problem_name, declared_domain, objects, init, goal = parse_problem(
        problem_text, arities, types)
    if declared_domain != domain_name:
        raise StripsError("problem %r declares domain %r but was grounded against %r"
                          % (problem_name, declared_domain, domain_name))

    effect_predicates = {p for s in schemas for p, _ in tuple(s.add) + tuple(s.dele)}
    static_predicates = tuple(sorted(p for p in arities if p not in effect_predicates))
    fluent_predicates = tuple(sorted(effect_predicates))

    for atom in goal:
        if atom.name in static_predicates:
            raise StripsError("the goal mentions the static predicate %r -- it is either "
                              "trivially true or unachievable, and this reader will not "
                              "guess which" % atom.name)

    by_type: Dict[str, List[str]] = {t: [] for t in types}
    for obj, type_name in objects:
        by_type[type_name].append(obj)
    for type_name in by_type:
        by_type[type_name].sort()

    statics = frozenset(a for a in init if a.name in static_predicates)

    # Static facts indexed by predicate, for the join below.
    static_index: Dict[str, List[Tuple[str, ...]]] = {}
    for atom in sorted(statics):
        static_index.setdefault(atom.name, []).append(atom.args)
    member: Dict[str, set] = {t: set(names) for t, names in by_type.items()}

    actions: List[GroundAction] = []
    for schema in schemas:
        param_types = dict(schema.params)
        static_lits = [(p, args) for p, args in schema.pre
                       if p in set(static_predicates)]

        # Bindings are grown by *joining on the static preconditions* rather
        # than enumerating the full type-consistent product and filtering.
        # The result set is identical — a binding survives iff every static
        # precondition is in `init` — but the cost follows the number of
        # static facts instead of |cells|^arity, which is what makes a
        # four-cell-parameter action (the folded A0 press) groundable at all.
        # Literals are joined most-constrained-first, greedily.
        bindings: List[Dict[str, str]] = [{}]
        remaining = list(static_lits)
        while remaining and bindings:
            def unbound(lit, bound_vars):
                return len({a for a in lit[1] if a not in bound_vars})
            bound_now = set(bindings[0])
            remaining.sort(key=lambda lit: (unbound(lit, bound_now),
                                            len(static_index.get(lit[0], ()))))
            pred, args = remaining.pop(0)
            facts = static_index.get(pred, [])
            grown: List[Dict[str, str]] = []
            for binding in bindings:
                for fact in facts:
                    if len(fact) != len(args):
                        continue
                    extended = dict(binding)
                    ok = True
                    for var, value in zip(args, fact):
                        if extended.get(var, value) != value:
                            ok = False
                            break
                        if var not in extended:
                            if value not in member[param_types[var]]:
                                ok = False
                                break
                            extended[var] = value
                    if ok:
                        grown.append(extended)
            bindings = grown

        # Whatever the statics did not pin ranges over its declared type.
        free_params = [p for p, _t in schema.params
                       if any(p not in b for b in bindings)] if bindings else []
        if bindings and free_params:
            grown = []
            for binding in bindings:
                missing = [p for p, _t in schema.params if p not in binding]
                for values in itertools.product(
                        *[tuple(by_type[param_types[p]]) for p in missing]):
                    extended = dict(binding)
                    extended.update(zip(missing, values))
                    grown.append(extended)
            bindings = grown

        for binding in bindings:
            binding_values = tuple(binding[p] for p, _t in schema.params)

            def instantiate(literals):
                return frozenset(Atom(p, tuple(binding[a] for a in args)) for p, args in literals)

            pre = instantiate(schema.pre)
            if not all(a in statics for a in pre if a.name in static_predicates):
                continue
            add = instantiate(schema.add)
            dele = instantiate(schema.dele)
            if add & dele:
                raise StripsError("action %s both adds and deletes %s"
                                  % (schema.name, sorted(str(a) for a in add & dele)))
            actions.append(GroundAction(
                schema.name, binding_values,
                frozenset(a for a in pre if a.name not in static_predicates),
                add, dele))

    actions.sort(key=lambda a: (a.name, a.args))
    return StripsTask(domain_name, problem_name, types, tuple(sorted(objects)),
                      init, goal, tuple(actions), static_predicates, fluent_predicates)


def load_task(domain_path: str, problem_path: str) -> StripsTask:
    with open(domain_path, encoding="utf-8") as fh:
        domain_text = fh.read()
    with open(problem_path, encoding="utf-8") as fh:
        problem_text = fh.read()
    return ground(domain_text, problem_text)


# ------------------------------------------------------- reachability (referee)

def reachable(task: StripsTask, limit: int = 200000) -> FrozenSet[FrozenSet[Atom]]:
    """Forward closure from `init`, on the fluent atoms. Referee use only.

    Nothing in the compilation path calls this — a conditional unsolvability
    theorem is about *every* state containing the pattern, reachable or not, and
    checking it on the reachable part only would make the closure obligation
    quietly circular in exactly the way `ic3_certificate` refuses.
    """
    start = task.fluent_init
    seen = {start}
    frontier = [start]
    while frontier:
        state = frontier.pop()
        for action in task.actions:
            if action.applicable(state):
                successor = action.apply(state)
                if successor not in seen:
                    if len(seen) >= limit:
                        raise StripsError("reachable set exceeded %d states" % limit)
                    seen.add(successor)
                    frontier.append(successor)
    return frozenset(seen)
