"""A small PDDL front end: the STRIPS subset with typing.

Enough to express the minimal gripper instance and to ground it.  Deliberately
not a general PDDL implementation -- no ADL, no quantifiers, no conditional
effects, no numeric fluents.  Anything outside the subset raises rather than
being silently mis-parsed.
"""

import itertools
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Set, Tuple

Atom = Tuple[str, ...]           # (predicate, arg, arg, ...)


class PddlError(Exception):
    """The input is outside the supported STRIPS subset, or malformed."""


# ------------------------------------------------------------------ s-expressions

def tokenize(text: str) -> List[str]:
    text = re.sub(r";[^\n]*", " ", text)                 # strip comments
    return text.replace("(", " ( ").replace(")", " ) ").split()


def parse_sexp(tokens: Sequence[str]) -> List:
    stack: List[List] = [[]]
    for token in tokens:
        if token == "(":
            stack.append([])
        elif token == ")":
            done = stack.pop()
            if not stack:
                raise PddlError("unbalanced parentheses")
            stack[-1].append(done)
        else:
            stack[-1].append(token.lower())
    if len(stack) != 1:
        raise PddlError("unbalanced parentheses")
    return stack[0]


def _typed_list(items: Sequence) -> List[Tuple[str, str]]:
    """`a b - t c - u` -> [(a,t), (b,t), (c,u)]; untyped entries get `object`."""
    out: List[Tuple[str, str]] = []
    pending: List[str] = []
    index = 0
    while index < len(items):
        token = items[index]
        if token == "-":
            type_name = items[index + 1]
            out.extend((name, type_name) for name in pending)
            pending = []
            index += 2
            continue
        pending.append(token)
        index += 1
    out.extend((name, "object") for name in pending)
    return out


def _section(body: Sequence, key: str) -> Optional[Sequence]:
    for item in body:
        if isinstance(item, list) and item and item[0] == key:
            return item
    return None


def _conjuncts(expression) -> Tuple[List[Atom], List[Atom]]:
    """Split a precondition/effect into (positive atoms, negative atoms)."""
    if not expression:
        return [], []
    if expression[0] == "and":
        parts = expression[1:]
    else:
        parts = [expression]
    positive: List[Atom] = []
    negative: List[Atom] = []
    for part in parts:
        if not isinstance(part, list) or not part:
            raise PddlError("unsupported formula element: %r" % (part,))
        if part[0] == "not":
            inner = part[1]
            if not isinstance(inner, list):
                raise PddlError("unsupported negation: %r" % (part,))
            negative.append(tuple(inner))
        elif part[0] in ("or", "forall", "exists", "imply", "when"):
            raise PddlError("%s is outside the supported STRIPS subset" % part[0])
        else:
            positive.append(tuple(part))
    return positive, negative


# ---------------------------------------------------------------------- model

@dataclass
class ActionSchema:
    name: str
    parameters: List[Tuple[str, str]]              # (?var, type)
    pre_positive: List[Atom]
    pre_negative: List[Atom]
    add_effects: List[Atom]
    del_effects: List[Atom]


@dataclass
class Domain:
    name: str
    types: Dict[str, str]                          # type -> parent type
    predicates: List[str]
    actions: List[ActionSchema]

    def subtypes_of(self, type_name: str) -> Set[str]:
        out = {type_name}
        changed = True
        while changed:
            changed = False
            for child, parent in self.types.items():
                if parent in out and child not in out:
                    out.add(child)
                    changed = True
        return out


@dataclass
class Problem:
    name: str
    domain_name: str
    objects: List[Tuple[str, str]]                 # (object, type)
    init: List[Atom]
    goal_positive: List[Atom]
    goal_negative: List[Atom]

    def objects_of(self, domain: Domain, type_name: str) -> List[str]:
        allowed = domain.subtypes_of(type_name)
        if type_name == "object":
            return [name for name, _ in self.objects]
        return [name for name, kind in self.objects if kind in allowed]


@dataclass(frozen=True)
class GroundAction:
    name: str
    args: Tuple[str, ...]
    pre_positive: Tuple[Atom, ...]
    pre_negative: Tuple[Atom, ...]
    add_effects: Tuple[Atom, ...]
    del_effects: Tuple[Atom, ...]
    cost: int = 1

    def text(self) -> str:
        return "(%s%s)" % (self.name, "".join(" " + a for a in self.args))


# --------------------------------------------------------------------- parsing

def parse_domain(text: str) -> Domain:
    forms = parse_sexp(tokenize(text))
    if len(forms) != 1 or forms[0][0] != "define":
        raise PddlError("expected a single (define ...) form")
    body = forms[0][1:]
    header = body[0]
    if header[0] != "domain":
        raise PddlError("expected (domain <name>)")
    name = header[1]

    requirements = _section(body, ":requirements") or []
    for requirement in requirements[1:]:
        if requirement not in (":strips", ":typing", ":negative-preconditions"):
            raise PddlError("unsupported requirement %s" % requirement)

    types: Dict[str, str] = {}
    types_section = _section(body, ":types")
    if types_section:
        for child, parent in _typed_list(types_section[1:]):
            types[child] = parent

    predicates: List[str] = []
    predicates_section = _section(body, ":predicates")
    if predicates_section:
        predicates = [item[0] for item in predicates_section[1:]]

    actions: List[ActionSchema] = []
    for item in body:
        if not (isinstance(item, list) and item and item[0] == ":action"):
            continue
        action_name = item[1]
        rest = item[2:]
        fields = {rest[i]: rest[i + 1] for i in range(0, len(rest) - 1, 2)}
        parameters = _typed_list(fields.get(":parameters", []))
        pre_positive, pre_negative = _conjuncts(fields.get(":precondition", []))
        add_effects, del_effects = _conjuncts(fields.get(":effect", []))
        actions.append(
            ActionSchema(
                name=action_name,
                parameters=parameters,
                pre_positive=pre_positive,
                pre_negative=pre_negative,
                add_effects=add_effects,
                del_effects=del_effects,
            )
        )
    return Domain(name=name, types=types, predicates=predicates, actions=actions)


def parse_problem(text: str) -> Problem:
    forms = parse_sexp(tokenize(text))
    body = forms[0][1:]
    name = body[0][1]
    domain_section = _section(body, ":domain")
    domain_name = domain_section[1] if domain_section else ""

    objects_section = _section(body, ":objects")
    objects = _typed_list(objects_section[1:]) if objects_section else []

    init_section = _section(body, ":init") or []
    init = [tuple(atom) for atom in init_section[1:]]

    goal_section = _section(body, ":goal")
    if goal_section is None:
        raise PddlError("problem has no :goal")
    goal_positive, goal_negative = _conjuncts(goal_section[1])

    return Problem(
        name=name,
        domain_name=domain_name,
        objects=objects,
        init=init,
        goal_positive=goal_positive,
        goal_negative=goal_negative,
    )


# -------------------------------------------------------------------- grounding

def _substitute(atom: Atom, binding: Dict[str, str]) -> Atom:
    return tuple(binding.get(part, part) for part in atom)


def ground_actions(domain: Domain, problem: Problem) -> List[GroundAction]:
    """Every ground instance, in a deterministic order."""
    out: List[GroundAction] = []
    for schema in sorted(domain.actions, key=lambda a: a.name):
        domains = [
            sorted(problem.objects_of(domain, type_name))
            for _, type_name in schema.parameters
        ]
        for combination in itertools.product(*domains) if domains else [()]:
            binding = {
                var: value
                for (var, _), value in zip(schema.parameters, combination)
            }
            out.append(
                GroundAction(
                    name=schema.name,
                    args=tuple(combination),
                    pre_positive=tuple(_substitute(a, binding) for a in schema.pre_positive),
                    pre_negative=tuple(_substitute(a, binding) for a in schema.pre_negative),
                    add_effects=tuple(_substitute(a, binding) for a in schema.add_effects),
                    del_effects=tuple(_substitute(a, binding) for a in schema.del_effects),
                )
            )
    return sorted(out, key=lambda a: a.text())
