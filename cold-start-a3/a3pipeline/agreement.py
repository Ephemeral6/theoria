"""Do two independently induced domains say the same thing?

The transfer arm's result is only as good as the answer to one objection: *the
person who carried the books to level 2 is the person who wrote them for level
1, and they already knew the answer.*  A2 faced the same objection about its
repair and answered it with three checks rather than with "trust us".  A3's
answer is the control arm, and this module is what turns the control arm into
evidence.

`theory/domain_l2_scratch.dsl` was written **blind**: from level 2's own
candidate stream, by a worker with no access to `theory/domain.dsl`, to
`THEORIZE_LOG.md`, to `A3_REPORT.md`, to the world's source, or to the
referee's copy.  If a manual induced that way agrees clause for clause with the
manual induced from level 1, then the clauses level 1 produced were not a
private convention — the same adjudication was reachable twice, from disjoint
evidence, by different hands.  That is a *result* and not an assumption, and it
is the strongest available answer to the objection.

**Two comparisons are reported, and both belong in the record.**

`strict` compares the rules as written: action, sorted guard atoms, effect.  On
the first run this came back **0 % — zero rules in common out of 27** — and the
reason is the point of running it.  The blind author called the mover `Agent`
and the door `Gate`, called the landmarks `warp_a_exit` / `warp_b_exit`, and
wrote **seven `?dir`-lifted rules** where level 1's manual writes twenty ground
ones.  None of that is disagreement about the world.

`canonical` therefore compares meaning, by quotienting out the three things
that are not the manual's content:

| quotiented | how |
|---|---|
| object names | by **role**, read off the effects: the object that `moved`/`jumped` is `MOVER`, the one that is `recolored` is `TOGGLE`, the one that `vanished`/`appeared` is `BARRIER` |
| landmark names | by the **guard colour** that reaches them, so `exit_a` and `warp_a_exit` are both `LM@3` |
| direction, ground vs lifted | every direction function (`above`, `below`, `leftof`, `rightof`, `toward`) collapses to `target`, and a `?dir` rule **expands** into its four ground instances |

What survives that is exactly what the manual claims about the world, and it is
the only thing the two arms can be fairly asked to agree on.

Reporting `strict` as well as `canonical` is deliberate.  The gap between them
is not noise: it measures **how much of a manual is convention** — naming and
the ground/lifted choice — rather than content, and that number matters to
anyone who wants to compare two manuals mechanically in future.

A disagreement that survives canonicalisation is not a failure of the tool.  It
is either a real difference in what two evidence sets license — a finding — or
a defect in one of the manuals, a bigger one.  The module reports it and takes
no position on which.
"""

import json
import os
import re
import sys
from typing import Dict, List, Set, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from theory_compiler.parser.theory_parser import parse_theory  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACTS = os.path.join(ROOT, "artifacts")
THEORY = os.path.join(ROOT, "theory")


def _text(node) -> str:
    """A stable rendering of a guard clause or an effect."""
    for attr in ("rendering", "text"):
        if hasattr(node, attr):
            value = getattr(node, attr)
            return value() if callable(value) else str(value)

    name = getattr(node, "name", None)
    if hasattr(node, "action") and getattr(node, "action", None) is not None:
        action = node.action
        args = ",".join(str(getattr(a, "name", getattr(a, "value", a)))
                        for a in getattr(action, "args", []))
        return "act=%s(%s)" % (getattr(action, "action_name", "?"), args)
    if hasattr(node, "expr"):
        return _text(node.expr)
    if name is not None:
        args = ",".join(str(getattr(a, "name", getattr(a, "value", a)))
                        for a in getattr(node, "args", []))
        return "%s(%s)" % (name, args)
    return str(node)


DIRECTIONS = ("up", "down", "left", "right")

#: Every spelling of "the cell this action points at".  `toward` is the blind
#: author's; the other four are the ground forms level 1's manual uses.
DIRECTION_FUNCS = ("above", "below", "leftof", "rightof", "toward", "strip")

DIR_OF_FUNC = {"above": "up", "below": "down",
               "leftof": "left", "rightof": "right"}


def normalise_rule(rule) -> Tuple[str, Tuple[str, ...], str]:
    guard = tuple(sorted(_text(clause) for clause in rule.guard.clauses))
    return ("", guard, _text(rule.event))


def _roles(ast) -> Dict[str, str]:
    """Object name -> role, read off what the rules *do* to each object.

    Names are the author's choice; roles are the world's.  `Cart`/`Agent` both
    become `MOVER` because both are what `moved` and `jumped` act on.
    """
    roles: Dict[str, str] = {}
    for rule in (ast.rules.rules if ast.rules else []):
        event = rule.event
        name = getattr(event, "name", "")
        args = getattr(event, "args", [])
        if not args:
            continue
        obj = str(getattr(args[0], "name", args[0]))
        if name in ("moved", "jumped"):
            roles[obj] = "MOVER"
        elif name == "recolored":
            roles[obj] = "TOGGLE"
        elif name in ("vanished", "appeared"):
            roles[obj] = "BARRIER"
    return roles


def _landmark_roles(ast) -> Dict[str, str]:
    """Landmark name -> the guard colour that reaches it.

    `exit_a` and `warp_a_exit` are the same landmark if the same colour sends
    the mover there, and nothing else about the name matters.
    """
    marks: Dict[str, str] = {}
    for rule in (ast.rules.rules if ast.rules else []):
        event = rule.event
        if getattr(event, "name", "") != "jumped":
            continue
        args = getattr(event, "args", [])
        if len(args) < 2:
            continue
        target = str(getattr(args[1], "name", args[1]))
        colour = None
        for clause in rule.guard.clauses:
            text = _text(clause)
            if text.startswith("colored("):
                colour = text.rsplit(",", 1)[-1].rstrip(")").strip()
        if colour is not None:
            marks[target] = "LM@%s" % colour
    return marks


def _canonical_atom(text: str, direction: str, roles, marks) -> str:
    # A direction function shows up two ways in the rendered guard: applied,
    # `below(Cart)`, and bare, `colored(below,3)`.  Both mean "the cell this
    # action points at" and both collapse to `target`.
    for func in DIRECTION_FUNCS:
        text = re.sub(r"\b%s\b" % func, "target", text)
    # `target(Cart)` and `target` are the same cell; drop any argument.
    while "target(" in text:
        head, _, rest = text.partition("target(")
        depth, i = 1, 0
        while i < len(rest) and depth:
            depth += {"(": 1, ")": -1}.get(rest[i], 0)
            i += 1
        text = head + "target" + rest[i:]
    for name, role in list(roles.items()) + list(marks.items()):
        text = text.replace(name, role)
    for token in ("?dir", "d", "dir"):
        text = text.replace("(%s)" % token, "(DIR)").replace(",%s)" % token, ",DIR)")
    return text.replace("DIR", direction).replace(" ", "")


def canonical_rules(ast) -> Set[Tuple[str, Tuple[str, ...], str]]:
    """Every rule as (direction, canonical guard, canonical effect).

    A `?dir`-lifted rule expands into its four ground instances, so a manual
    that used the miner's better lifted form and one that spelled out four
    clauses come out identical — which is what they mean.
    """
    roles = _roles(ast)
    marks = _landmark_roles(ast)
    out: Set[Tuple[str, Tuple[str, ...], str]] = set()

    for rule in (ast.rules.rules if ast.rules else []):
        raw_guard = [_text(c) for c in rule.guard.clauses]
        raw_effect = _text(rule.event)

        # Which direction is this rule about?  A ground rule names one in its
        # `act=push(o, <dir>)` clause or in its direction function; a lifted
        # rule names a variable, and stands for all four.
        found = None
        for text in raw_guard:
            for direction in DIRECTIONS:
                if ("," + direction + ")") in text.replace(" ", ""):
                    found = direction
            for func, direction in DIR_OF_FUNC.items():
                if func + "(" in text:
                    found = direction
        directions = [found] if found else list(DIRECTIONS)

        for direction in directions:
            guard = tuple(sorted(
                _canonical_atom(t, direction, roles, marks) for t in raw_guard))
            out.add((direction,
                     guard,
                     _canonical_atom(raw_effect, direction, roles, marks)))
    return out


def _canonical_invariants(dsl_path: str, roles: Dict[str, str]) -> Set[str]:
    """Invariant *statements*, read off the source, renamed by role.

    Taken from the text rather than from the AST because the parser keeps an
    invariant's body as structure the backends consume and not as anything with
    a stable rendering, and because the comparison only needs the sentence.
    The terms of a sum are sorted, so `count(Switch,8) + count(Door) = 1` and
    `count(Gate) + count(Switch,8) = 1` are recognised as the same law once the
    names are quotiented away.
    """
    out: Set[str] = set()
    for raw in open(dsl_path, encoding="utf-8").read().splitlines():
        line = raw.strip()
        if not line.startswith("invariant "):
            continue
        body = line[len("invariant "):]
        body = body.split("[")[0].strip()             # drop [status: ...]
        parts = body.split(None, 1)                   # drop the law's name
        if len(parts) < 2:
            continue
        statement = parts[1]
        for name, role in roles.items():
            statement = re.sub(r"\b%s\b" % re.escape(name), role, statement)
        statement = statement.replace(" ", "")
        if "=" in statement:
            lhs, _, rhs = statement.rpartition("=")
            lhs = "+".join(sorted(lhs.split("+")))
            statement = "%s=%s" % (lhs, rhs)
        out.add(statement)
    return out


def normalise(dsl_path: str) -> Dict[str, object]:
    ast = parse_theory(open(dsl_path, encoding="utf-8").read())
    rules = {normalise_rule(r) for r in (ast.rules.rules if ast.rules else [])}

    laws: Set[str] = set()
    if getattr(ast, "laws", None) is not None:
        for inv in getattr(ast.laws, "invariants", []) or []:
            laws.add("invariant %s" % _text(inv))
        for thm in getattr(ast.laws, "theorems", []) or []:
            laws.add("theorem %s" % getattr(thm, "name", "?"))

    canonical_laws = _canonical_invariants(dsl_path, _roles(ast))

    objects = {o.name for o in (ast.word_table.objects
                                if ast.word_table else [])}
    landmarks = {getattr(l, "name", str(l))
                 for l in (getattr(ast.word_table, "landmarks", []) or [])}
    semantics = {}
    if getattr(ast, "semantics", None) is not None:
        for key in ("frame", "conflict", "cascade"):
            semantics[key] = str(getattr(ast.semantics, key, None))

    return {
        "path": os.path.relpath(dsl_path, ROOT).replace("\\", "/"),
        "rules": rules,
        "canonical": canonical_rules(ast),
        "canonical_laws": canonical_laws,
        "roles": _roles(ast),
        "landmark_roles": _landmark_roles(ast),
        "written_clauses": len(ast.rules.rules) if ast.rules else 0,
        "laws": laws,
        "objects": objects,
        "landmarks": landmarks,
        "semantics": semantics,
        "has_goal_section": ast.goal is not None,
    }


def compare(left_path: str, right_path: str) -> Dict[str, object]:
    left = normalise(left_path)
    right = normalise(right_path)

    shared = left["rules"] & right["rules"]
    only_left = left["rules"] - right["rules"]
    only_right = right["rules"] - left["rules"]

    def render(rules) -> List[str]:
        return sorted("%s => %s" % (" & ".join(g), e) for _, g, e in rules)

    def render_canon(rules) -> List[str]:
        return sorted("%-5s %s => %s" % (d, " & ".join(g), e)
                      for d, g, e in rules)

    c_left, c_right = left["canonical"], right["canonical"]
    c_shared = c_left & c_right
    c_total = len(c_left | c_right)

    total = len(left["rules"] | right["rules"])
    return {
        "left": left["path"],
        "right": right["path"],
        "clauses_written_left": left["written_clauses"],
        "clauses_written_right": right["written_clauses"],

        "strict_rules_left": len(left["rules"]),
        "strict_rules_right": len(right["rules"]),
        "strict_agreed": len(shared),
        "strict_agreement": round(len(shared) / total, 4) if total else 1.0,

        "canonical_rules_left": len(c_left),
        "canonical_rules_right": len(c_right),
        "canonical_agreed": len(c_shared),
        "canonical_agreement": (round(len(c_shared) / c_total, 4)
                                if c_total else 1.0),
        "canonical_only_in_left": render_canon(c_left - c_right),
        "canonical_only_in_right": render_canon(c_right - c_left),
        "canonical_agreed_rules": render_canon(c_shared),

        "roles_left": left["roles"],
        "roles_right": right["roles"],
        "landmark_roles_left": left["landmark_roles"],
        "landmark_roles_right": right["landmark_roles"],

        "only_in_left": render(only_left),
        "only_in_right": render(only_right),
        "agreed": render(shared),
        "canonical_laws_agreed": sorted(left["canonical_laws"]
                                        & right["canonical_laws"]),
        "canonical_laws_only_left": sorted(left["canonical_laws"]
                                           - right["canonical_laws"]),
        "canonical_laws_only_right": sorted(right["canonical_laws"]
                                            - left["canonical_laws"]),

        "laws_agreed": sorted(left["laws"] & right["laws"]),
        "laws_only_left": sorted(left["laws"] - right["laws"]),
        "laws_only_right": sorted(right["laws"] - left["laws"]),
        "objects_left": sorted(left["objects"]),
        "objects_right": sorted(right["objects"]),
        "landmarks_left": sorted(left["landmarks"]),
        "landmarks_right": sorted(right["landmarks"]),
        "semantics_agree": left["semantics"] == right["semantics"],
        "semantics_left": left["semantics"],
        "semantics_right": right["semantics"],
        "neither_has_a_goal_section": not (left["has_goal_section"]
                                           or right["has_goal_section"]),
        "reading": (
            "A rule is 'agreed' when its action, its sorted guard atoms and "
            "its effect match. Names, evidence annotations and comments are "
            "discarded: they are not the manual's content. Any difference "
            "below is either a real difference in what two evidence sets "
            "license, or a defect in one of the manuals."
        ),
    }


#: The blind manual exists in two states and both are compared, because they
#: answer different questions.
#:
#: `as_written` is the manual the blind arm produced from level 2's evidence
#: alone, before it was told anything.  It named the mover `Agent` and the
#: barrier `Gate` and used `?dir`-lifted schemas.  This is the comparison that
#: measures **convergence**: two arms, disjoint evidence, no contact.
#:
#: `after_conformance` is the same manual after two rounds of being told what
#: the toolchain requires — ground the rules, call the mover `Cart`, call the
#: barrier `Door`.  Its agreement with level 1's is naturally higher, and the
#: *difference* between the two comparisons is the honest measure of how much
#: of the convergence was found in the evidence and how much was imposed by
#: the tool.  Quoting only the second would overstate the result.
BLIND_STATES = (
    ("as_written",
     os.path.join(ARTIFACTS, "finding_r09_blind",
                  "domain_l2_scratch_lifted.dsl"),
     "the blind manual before it was told anything about the toolchain"),
    ("after_conformance",
     os.path.join(THEORY, "domain_l2_scratch.dsl"),
     "the same manual after grounding and the Cart/Door rename"),
)


def main() -> int:
    left = os.path.join(THEORY, "domain.dsl")

    report: Dict[str, object] = {}
    for key, path, note in BLIND_STATES:
        if not os.path.exists(path):
            continue
        entry = compare(left, path)
        entry["note"] = note
        report[key] = entry

    if not report:
        print("no blind manual to compare against yet")
        return 0

    out = os.path.join(ARTIFACTS, "domain_agreement.json")
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")

    for key, _path, note in BLIND_STATES:
        if key not in report:
            continue
        entry = report[key]
        print("\n-- %s: %s" % (key, note))
        print("   clauses written   L1 %d | blind %d"
              % (entry["clauses_written_left"], entry["clauses_written_right"]))
        print("   strict agreement    %.1f%%   canonical agreement  %.1f%%"
              % (100 * entry["strict_agreement"],
                 100 * entry["canonical_agreement"]))
        print("   every L1 clause present: %s"
              % (entry["canonical_only_in_left"] == []))
        print("   blind-only clauses: %d" % len(entry["canonical_only_in_right"]))
        print("   laws agree: %s | semantics agree: %s | neither has a goal: %s"
              % (not (entry["canonical_laws_only_left"]
                      or entry["canonical_laws_only_right"]),
                 entry["semantics_agree"], entry["neither_has_a_goal_section"]))
        print("   roles  L1 %s" % entry["roles_left"])
        print("          blind %s" % entry["roles_right"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
