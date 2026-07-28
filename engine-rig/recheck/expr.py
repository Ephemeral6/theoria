"""The expression language rule sets and certificates are written in.

Total, pure, first-order, and deliberately small.  Every form terminates in a
bounded number of steps on every input, there is no `eval`, no attribute access,
no arithmetic that can overflow a domain, and no way to name anything that was
not declared.  A rule set that cannot be said in this language is a rule set
this rechecker declines to check, which is the honest failure mode: the
alternative -- letting the world description carry executable Python -- would
mean the certificate and the rules could be produced by the same program again.

Forms (JSON arrays, head is the operator):

    ["lit", v]                  a scalar: string, int, or bool
    ["var", name]               a declared state variable
    ["act"]                     the action label; legal only inside a rule guard
    ["param", name]             a parameter, legal only inside a `def` body
    ["=", a, b]  ["!=", a, b]   scalar equality
    ["and", ...]  ["or", ...]   n-ary, short-circuiting; identity on zero args
    ["not", a]
    ["in", a, [v, ...]]         membership in a literal set
    ["if", c, a, b]
    ["table", name, key, ...]   lookup in a declared constant table
    ["call", name, arg, ...]    a declared macro; macros may not recurse

Compilation turns an expression into a closure over `(state, action, args)`,
because the checker evaluates the same handful of expressions across every
state in the product and an AST walk per evaluation is the difference between
a second and a minute.
"""

from dataclasses import dataclass
from typing import Callable, Dict, List, Mapping, Sequence, Tuple

Value = object                       # str | int | bool, and nothing else
State = Tuple[Value, ...]
Compiled = Callable[[State, object, Tuple[Value, ...]], Value]


class ExprError(ValueError):
    """A malformed expression, or one naming something that was not declared."""


SCALAR_TYPES = (str, int, bool)


def check_scalar(value: object, where: str) -> Value:
    if isinstance(value, bool) or isinstance(value, int) or isinstance(value, str):
        return value
    raise ExprError("%s: %r is not a scalar (string, int or bool)" % (where, value))


# ------------------------------------------------------------------- tables

@dataclass(frozen=True)
class Table:
    """A constant finite map, `arity` keys to one scalar."""

    name: str
    arity: int
    entries: Mapping[Tuple[Value, ...], Value]
    default: Value
    has_default: bool

    def lookup(self, key: Tuple[Value, ...]) -> Value:
        if key in self.entries:
            return self.entries[key]
        if self.has_default:
            return self.default
        raise ExprError(
            "table %s has no entry for %r and no default" % (self.name, key)
        )


def parse_table(name: str, spec: object) -> Table:
    if not isinstance(spec, dict):
        raise ExprError("table %s: expected an object" % name)
    unknown = set(spec) - {"arity", "entries", "default", "comment"}
    if unknown:
        raise ExprError("table %s: unknown keys %s" % (name, sorted(unknown)))
    arity = spec.get("arity")
    if not isinstance(arity, int) or isinstance(arity, bool) or arity < 1:
        raise ExprError("table %s: arity must be a positive integer" % name)
    raw = spec.get("entries")
    if not isinstance(raw, list):
        raise ExprError("table %s: entries must be a list" % name)
    entries: Dict[Tuple[Value, ...], Value] = {}
    for row in raw:
        if not isinstance(row, list) or len(row) != arity + 1:
            raise ExprError(
                "table %s: every entry needs %d keys and one value, got %r"
                % (name, arity, row)
            )
        key = tuple(check_scalar(k, "table %s key" % name) for k in row[:arity])
        if key in entries:
            raise ExprError("table %s: duplicate entry for %r" % (name, list(key)))
        entries[key] = check_scalar(row[arity], "table %s value" % name)
    has_default = "default" in spec
    default = check_scalar(spec["default"], "table %s default" % name) if has_default else None
    return Table(name=name, arity=arity, entries=entries,
                 default=default, has_default=has_default)


def parse_tables(spec: object, where: str) -> Dict[str, Table]:
    if spec is None:
        return {}
    if not isinstance(spec, dict):
        raise ExprError("%s: tables must be an object" % where)
    return {name: parse_table(name, body) for name, body in spec.items()}


# -------------------------------------------------------------------- macros

@dataclass(frozen=True)
class Macro:
    name: str
    params: Tuple[str, ...]
    body: object                       # unresolved AST; compiled in order


def parse_macros(spec: object, where: str) -> Dict[str, Macro]:
    """Defs are a *list*, not an object, because their order is load-bearing.

    A def may only call one declared before it -- that is what makes recursion
    impossible -- so the declaration order has to survive serialisation.  A JSON
    object would have it depend on how the writer happened to sort its keys.
    """
    if spec is None:
        return {}
    if not isinstance(spec, list):
        raise ExprError("%s: defs must be a list (their order is load-bearing)" % where)
    out: Dict[str, Macro] = {}
    for body in spec:
        if not isinstance(body, dict):
            raise ExprError("%s: every def must be an object" % where)
        unknown = set(body) - {"name", "params", "body", "comment"}
        if unknown:
            raise ExprError("%s: def has unknown keys %s" % (where, sorted(unknown)))
        name = body.get("name")
        if not isinstance(name, str) or not name:
            raise ExprError("%s: every def needs a name" % where)
        if name in out:
            raise ExprError("%s: duplicate def %r" % (where, name))
        params = body.get("params", [])
        if not isinstance(params, list) or not all(isinstance(p, str) for p in params):
            raise ExprError("def %s: params must be a list of names" % name)
        if len(set(params)) != len(params):
            raise ExprError("def %s: duplicate parameter name" % name)
        if "body" not in body:
            raise ExprError("def %s: no body" % name)
        out[name] = Macro(name=name, params=tuple(params), body=body["body"])
    return out


# ---------------------------------------------------------------- the compiler

@dataclass(frozen=True)
class Scope:
    """Everything a compiling expression is allowed to name."""

    variables: Mapping[str, int]
    tables: Mapping[str, Table]
    macros: Mapping[str, Compiled]           # already compiled, so no recursion
    macro_arity: Mapping[str, int]
    allow_action: bool
    params: Tuple[str, ...] = ()

    def with_params(self, params: Tuple[str, ...]) -> "Scope":
        return Scope(
            variables=self.variables, tables=self.tables, macros=self.macros,
            macro_arity=self.macro_arity, allow_action=self.allow_action,
            params=params,
        )


def _as_bool(value: Value, op: str) -> bool:
    if isinstance(value, bool):
        return value
    raise ExprError("%s: expected a boolean, got %r" % (op, value))


def compile_expr(node: object, scope: Scope) -> Compiled:
    if not isinstance(node, list) or not node or not isinstance(node[0], str):
        raise ExprError("expression must be a non-empty array headed by an "
                        "operator name, got %r" % (node,))
    op, args = node[0], node[1:]

    if op == "lit":
        if len(args) != 1:
            raise ExprError("lit takes exactly one argument")
        value = check_scalar(args[0], "lit")
        return lambda state, action, params, _v=value: _v

    if op == "var":
        if len(args) != 1 or not isinstance(args[0], str):
            raise ExprError("var takes exactly one name")
        if args[0] not in scope.variables:
            raise ExprError("var: %r is not a declared state variable" % args[0])
        index = scope.variables[args[0]]
        return lambda state, action, params, _i=index: state[_i]

    if op == "act":
        if args:
            raise ExprError("act takes no arguments")
        if not scope.allow_action:
            raise ExprError(
                "act is legal only inside a rule guard -- a certificate that "
                "mentions the action is describing the rules, not a set of states"
            )
        return lambda state, action, params: action

    if op == "param":
        if len(args) != 1 or not isinstance(args[0], str):
            raise ExprError("param takes exactly one name")
        if args[0] not in scope.params:
            raise ExprError("param: %r is not a parameter here" % args[0])
        index = scope.params.index(args[0])
        return lambda state, action, params, _i=index: params[_i]

    if op in ("=", "!="):
        if len(args) != 2:
            raise ExprError("%s takes exactly two arguments" % op)
        left = compile_expr(args[0], scope)
        right = compile_expr(args[1], scope)
        if op == "=":
            return lambda s, a, p: left(s, a, p) == right(s, a, p)
        return lambda s, a, p: left(s, a, p) != right(s, a, p)

    if op == "and":
        parts = [compile_expr(arg, scope) for arg in args]

        def _and(s, a, p, _parts=tuple(parts)):
            for part in _parts:
                if not _as_bool(part(s, a, p), "and"):
                    return False
            return True

        return _and

    if op == "or":
        parts = [compile_expr(arg, scope) for arg in args]

        def _or(s, a, p, _parts=tuple(parts)):
            for part in _parts:
                if _as_bool(part(s, a, p), "or"):
                    return True
            return False

        return _or

    if op == "not":
        if len(args) != 1:
            raise ExprError("not takes exactly one argument")
        inner = compile_expr(args[0], scope)
        return lambda s, a, p: not _as_bool(inner(s, a, p), "not")

    if op == "in":
        if len(args) != 2 or not isinstance(args[1], list):
            raise ExprError("in takes an expression and a literal list")
        inner = compile_expr(args[0], scope)
        members = tuple(check_scalar(v, "in") for v in args[1])
        if len(set(members)) != len(members):
            raise ExprError("in: duplicate member in the literal list")
        return lambda s, a, p, _m=frozenset(members): inner(s, a, p) in _m

    if op == "if":
        if len(args) != 3:
            raise ExprError("if takes a condition and two branches")
        cond = compile_expr(args[0], scope)
        then = compile_expr(args[1], scope)
        other = compile_expr(args[2], scope)
        return lambda s, a, p: (then if _as_bool(cond(s, a, p), "if") else other)(s, a, p)

    if op == "table":
        if len(args) < 2 or not isinstance(args[0], str):
            raise ExprError("table takes a name and at least one key")
        table = scope.tables.get(args[0])
        if table is None:
            raise ExprError("table: %r is not declared" % args[0])
        if len(args) - 1 != table.arity:
            raise ExprError(
                "table %s has arity %d, given %d keys" % (args[0], table.arity, len(args) - 1)
            )
        keys = [compile_expr(arg, scope) for arg in args[1:]]
        return lambda s, a, p, _t=table, _k=tuple(keys): _t.lookup(
            tuple(k(s, a, p) for k in _k)
        )

    if op == "call":
        if not args or not isinstance(args[0], str):
            raise ExprError("call takes a def name and its arguments")
        name = args[0]
        macro = scope.macros.get(name)
        if macro is None:
            raise ExprError(
                "call: %r is not a declared def (defs may not recurse, and a "
                "def may only call one declared before it)" % name
            )
        arity = scope.macro_arity[name]
        if len(args) - 1 != arity:
            raise ExprError("def %s takes %d arguments, given %d"
                            % (name, arity, len(args) - 1))
        actuals = [compile_expr(arg, scope) for arg in args[1:]]
        return lambda s, a, p, _m=macro, _x=tuple(actuals): _m(
            s, a, tuple(x(s, a, p) for x in _x)
        )

    raise ExprError("unknown operator %r" % op)


def compile_macros(macros: Mapping[str, Macro], scope: Scope) -> Scope:
    """Compile defs in declaration order; a def may only call earlier ones.

    That rule is what makes recursion impossible rather than merely discouraged:
    at the moment a body is compiled, its own name is not yet in scope, so
    `["call", self, ...]` fails to resolve.  Termination is then structural and
    does not depend on a depth counter anyone could raise.
    """
    compiled: Dict[str, Compiled] = {}
    arity: Dict[str, int] = {}
    current = scope
    for name, macro in macros.items():
        body_scope = Scope(
            variables=current.variables, tables=current.tables,
            macros=dict(compiled), macro_arity=dict(arity),
            allow_action=current.allow_action, params=macro.params,
        )
        compiled[name] = compile_expr(macro.body, body_scope)
        arity[name] = len(macro.params)
    return Scope(
        variables=scope.variables, tables=scope.tables,
        macros=compiled, macro_arity=arity,
        allow_action=scope.allow_action, params=(),
    )


def compile_guard(node: object, scope: Scope, where: str) -> Compiled:
    """Compile a rule guard: reads the action as well, must return a boolean."""
    inner = compile_expr(node, scope)

    def guard(state, action, params):
        value = inner(state, action, params)
        if not isinstance(value, bool):
            raise ExprError("%s: guard returned %r, not a boolean" % (where, value))
        return value

    return guard


def compile_predicate(node: object, scope: Scope, where: str) -> Callable[[State], bool]:
    """Compile an expression that must evaluate to a boolean on every state."""
    inner = compile_expr(node, scope)

    def predicate(state: State) -> bool:
        value = inner(state, None, ())
        if not isinstance(value, bool):
            raise ExprError("%s: predicate returned %r, not a boolean" % (where, value))
        return value

    return predicate


def names_used(node: object) -> Tuple[List[str], List[str], List[str]]:
    """(variables, tables, defs) an expression mentions -- for reporting."""
    variables: List[str] = []
    tables: List[str] = []
    defs: List[str] = []

    def walk(item: object) -> None:
        if not isinstance(item, list) or not item or not isinstance(item[0], str):
            return
        head = item[0]
        if head == "var" and len(item) == 2 and isinstance(item[1], str):
            variables.append(item[1])
            return
        if head == "table" and len(item) >= 2 and isinstance(item[1], str):
            tables.append(item[1])
        if head == "call" and len(item) >= 2 and isinstance(item[1], str):
            defs.append(item[1])
        for child in item[1:]:
            walk(child)

    walk(node)
    return sorted(set(variables)), sorted(set(tables)), sorted(set(defs))


def render(node: object) -> str:
    """A readable one-line rendering, for witnesses and reports."""
    if not isinstance(node, list) or not node or not isinstance(node[0], str):
        return repr(node)
    op, args = node[0], node[1:]
    if op == "lit":
        return repr(args[0])
    if op == "var":
        return str(args[0])
    if op == "act":
        return "act"
    if op == "param":
        return "?" + str(args[0])
    if op in ("=", "!="):
        return "(%s %s %s)" % (render(args[0]), op, render(args[1]))
    if op in ("and", "or"):
        if not args:
            return "true" if op == "and" else "false"
        return "(%s)" % (" %s " % op).join(render(a) for a in args)
    if op == "not":
        return "!%s" % render(args[0])
    if op == "in":
        members = args[1] if isinstance(args[1], list) else []
        shown = ", ".join(repr(m) for m in members[:6])
        if len(members) > 6:
            shown += ", ... (%d total)" % len(members)
        return "%s in {%s}" % (render(args[0]), shown)
    if op == "if":
        return "(if %s then %s else %s)" % tuple(render(a) for a in args[:3])
    if op == "table":
        return "%s[%s]" % (args[0], ", ".join(render(a) for a in args[1:]))
    if op == "call":
        return "%s(%s)" % (args[0], ", ".join(render(a) for a in args[1:]))
    return repr(node)
