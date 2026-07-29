"""**D-A6-001** — `gen_pddl_a0`'s state is one cell and one boolean.

The planning form models a level as `(at ?c)` — where the Cart is — plus a single
propositional `(switched)`.  Every `moved(o, dir)` rule, whatever `o` is,
compiles through `_action_move`, which moves *the Cart*:

```lisp
  (:action block-right
    :parameters (?from - cell ?to - cell)
    :precondition (and (at ?from) (adj-right ?from ?to) (passable ?to))
    :effect (and (not (at ?from)) (at ?to)))
```

So a manual with a pushable block compiles to a domain in which the block never
moves, and `_problem` withholds `(passable …)` from every non-mover object's
cell — the block becomes a permanent wall.  On `t1-push-open` the only route to
the goal runs through the block's cell, which is the only gap in a divider, so
the planner returns **UNSAT for a manual that is correct**, silently and with
confidence.  That is D-A3-005's failure family — a confident wrong answer from a
backend that was written for a world with one fewer moving part — reached from a
different direction, and A3 could not have seen it: A3's Cart is the only thing
in A3's world that moves.

`cold-start-a0/` is the theory-compiler track's directory, so this is a
workaround in A6's tree rather than a fix, on the model of A3's three.  It is a
post-hoc rewrite of generated text and it is coupled to that text; every
substitution is counted and a miscount **raises**, because a silent no-op here
does not fail — it produces a plan, and a wrong plan that type-checks is the most
expensive thing this module could emit.

## What it emits

For each pushable object `X` (colour-guarded, moved by a rule that shares its
guard with a mover-move rule — the same "same guard means one event" reading
`gen_pddl_a0._cascades` already uses for the Door):

* a predicate `(x-at ?c - cell)`, initialised at the object's cell;
* `X`'s own move actions **deleted** — they were duplicate Cart moves;
* the mover's *push* action rewritten to three cells: stand at `?from`, `X` on the
  adjacent `?p`, `?beyond` beyond it and clear.  Both objects move in one action,
  which is what the manual's two same-guard rules say;
* every plain mover move given `(not (x-at ?to))`, because the manual's `free()`
  reads the *rendered* frame and the block is on it.

`free(c)` in the executable form is `render(state)[c] == BACKGROUND`.  In PDDL
that is `(passable c)` — arena, no static object — conjoined with `(not (x-at c))`
for each pushable.  The two agree exactly when the board is static under the
pushables, which is the case this encoding is for; `plan.run_plan` replays every
plan through the executable form regardless, so a divergence is caught rather
than trusted.
"""

import re
import sys
import os
from typing import Dict, List, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from dataclasses import replace as _dc_replace  # noqa: E402

from theory_compiler.parser.ast_nodes import (  # noqa: E402
    FuncCall, NameRef, TheoryAST,
)

from compile.gen_pddl_a0 import _guard_key  # noqa: E402  (a0, read-only)
from compile.problem import Problem  # noqa: E402


class PushPatchError(Exception):
    """The generated text is not the text this rewrite was written for."""


def _event(rule) -> Tuple[str, str]:
    ev = rule.event
    obj = ev.args[0].name if ev.args and isinstance(ev.args[0], NameRef) else ""
    return ev.name, obj


def cascades(ast: TheoryAST, mover: str) -> Dict[str, Dict[str, object]]:
    """mover-move rule name -> `{object, object_rule, direction, entry_colour}`.

    Read off the guards, never off the rule names: two rules with the same guard
    fire on the same transitions, so a manual that moves the Cart and the Block
    under one guard has said they are one event with two consequences.  That is
    exactly the criterion `gen_pddl_a0._cascades` applies to the Door, reused
    rather than re-invented so the two cannot drift.
    """
    by_guard: Dict[tuple, List] = {}
    for rule in ast.rules.rules:
        by_guard.setdefault(_guard_key(rule), []).append(rule)

    out: Dict[str, Dict[str, object]] = {}
    for key, rules in by_guard.items():
        moves = [(r, _event(r)) for r in rules]
        mover_rules = [r for r, (ev, obj) in moves
                       if ev == "moved" and obj == mover]
        other_rules = [(r, obj) for r, (ev, obj) in moves
                       if ev == "moved" and obj and obj != mover]
        if not mover_rules or not other_rules:
            continue
        if len(mover_rules) != 1 or len(other_rules) != 1:
            raise PushPatchError(
                "guard %r moves %d mover rules and %d other rules; carrypack v1 "
                "encodes one pushed object per guard"
                % (key, len(mover_rules), len(other_rules)))
        rule = mover_rules[0]
        other, obj_name = other_rules[0]
        direction = None
        colours: List[int] = []
        for clause in rule.guard.clauses:
            action = getattr(clause, "action", None)
            if action is not None and len(action.args) > 1:
                direction = action.args[1].name
            expr = getattr(clause, "expr", None)
            if isinstance(expr, FuncCall) and expr.name == "colored":
                colours.append(int(expr.args[1].value))
        if direction is None:
            raise PushPatchError("rule %s has no action clause" % rule.name)
        if len(colours) != 1:
            raise PushPatchError(
                "rule %s must name exactly one colour for the object it pushes; "
                "found %r" % (rule.name, colours))
        out[rule.name] = {"object": obj_name, "object_rule": other.name,
                          "direction": direction, "entry_colour": colours[0]}

    # one object, one colour — or the encoding cannot tell two pushables apart
    by_object: Dict[str, set] = {}
    for entry in out.values():
        by_object.setdefault(str(entry["object"]), set()).add(entry["entry_colour"])
    for name, seen in sorted(by_object.items()):
        if len(seen) != 1:
            raise PushPatchError(
                "%s is guarded by %d different colours %r; one `%s-at` predicate "
                "cannot separate them" % (name, len(seen), sorted(seen), name.lower()))
    return out


def pushed_objects(ast: TheoryAST, mover: str) -> List[str]:
    return sorted({str(e["object"]) for e in cascades(ast, mover).values()})


def strip_pushables(problem: Problem, pushed: Sequence[str]
                    ) -> Tuple[Problem, Dict[str, Tuple[int, int]]]:
    """Hand `generate_pddl` a problem with the pushables removed, and their cells.

    Two things happen inside `gen_pddl_a0` to a non-mover object, and both are
    wrong for something that moves:

    * `_classify` gives its cell a subtype of its own (`blockcell`) with exactly
      one inhabitant — a *static* type for a *moving* thing, so after one push
      every parameter typed that way grounds to the wrong cell;
    * `_problem` withholds `(passable …)` from it — but the Cart stands there the
      instant the push succeeds.

    Removing the object from `problem.objects` before generation avoids both, and
    the facts come back in the patch.  The returned `Problem` is a copy;
    `problem.json` still records the real one, so the delta stays auditable — the
    same discipline `compile_a3.pddl_addressable` uses for D-A3-006.
    """
    keep, cells = [], {}
    for obj in problem.objects:
        if obj.name in set(pushed):
            cells[obj.name] = tuple(obj.pos)
        else:
            keep.append(obj)
    missing = sorted(set(pushed) - set(cells))
    if missing:
        raise PushPatchError(
            "the manual pushes %r and the problem instance places none of them"
            % missing)
    return _dc_replace(problem, objects=keep), cells


def _predicate(obj: str) -> str:
    return "%s-at" % obj.lower().replace("_", "-")


def patch(domain: str, instance: str, ast: TheoryAST, mover: str,
          object_cells: Dict[str, Tuple[int, int]]) -> Tuple[str, str, Dict[str, object]]:
    """Rewrite a generated PDDL pair so its pushable objects actually move."""
    table = cascades(ast, mover)
    if not table:
        return domain, instance, {"pushables": 0, "note": "no push cascades"}

    objects = sorted({str(e["object"]) for e in table.values()})

    # A jump lands the mover on a landmark, and whether that cell is clear of a
    # pushable is a question this encoding has no fact for.  Refuse rather than
    # emit a domain that is right about pushes and quiet about jumps.
    jumps = [r.name for r in ast.rules.rules if _event(r)[0] == "jumped"]
    if jumps:
        raise PushPatchError(
            "this manual has both pushable objects %r and jump rules %r; "
            "carrypack v1 does not encode the interaction (a jump could land the "
            "mover on the pushable) and will not guess at it" % (objects, jumps))

    # ------------------------------------------------------------- predicates
    anchor = "    (switched)"
    if sum(1 for line in domain.splitlines() if line.startswith(anchor)) != 1:
        raise PushPatchError(
            "expected exactly one `(switched)` predicate line to anchor the "
            "insertion; gen_pddl_a0's output has changed")
    lines = domain.splitlines()
    at = next(i for i, line in enumerate(lines) if line.startswith(anchor))
    lines[at + 1:at + 1] = ["    (%s ?c - cell)          ; where %s is"
                            % (_predicate(o), o) for o in objects]
    domain = "\n".join(lines) + "\n"

    # ---------------------------------------------------------------- actions
    kinds = {r.name: _event(r) for r in ast.rules.rules}
    drop = {e["object_rule"] for e in table.values()}
    action_of = {name.replace("_", "-"): name for name in kinds}

    marker = "  (:action "
    head, _, rest = domain.partition(marker)
    blocks = [marker + part for part in rest.split(marker)] if rest else []

    rewritten = deleted = guarded = 0
    out_blocks: List[str] = []
    for block in blocks:
        action = block[len(marker):].split()[0].strip()
        rule = action_of.get(action)
        if rule is None:                      # the trailing `)` of the domain
            out_blocks.append(block)
            continue
        if rule in drop:
            deleted += 1
            out_blocks.append(
                ";; %s was a duplicate mover move — its object is carried by the "
                "%s action's effect instead (D-A6-001)\n\n"
                % (action, _predicate(str(kinds[rule][1]))))
            continue
        if rule in table:
            entry = table[rule]
            out_blocks.append(_push_action(action, str(entry["direction"]),
                                           str(entry["object"]), objects))
            rewritten += 1
            continue
        if kinds[rule][0] == "moved" and kinds[rule][1] == mover:
            out_blocks.append(_guard_move(action, block, objects))
            guarded += 1
            continue
        out_blocks.append(block)
    domain = head + "".join(out_blocks)

    if rewritten != len(table) or deleted != len(drop):
        raise PushPatchError(
            "expected %d push rewrites and %d deletions, made %d and %d"
            % (len(table), len(drop), rewritten, deleted))

    # --------------------------------------------------------------- instance
    facts = ["    (%s c%d-%d)" % (_predicate(o), *object_cells[o])
             for o in objects]
    ilines = instance.splitlines()
    try:
        init_at = ilines.index("  (:init")
    except ValueError:                        # pragma: no cover - shape changed
        raise PushPatchError("no `  (:init` line in the generated problem")
    close_at = next(i for i in range(init_at + 1, len(ilines))
                    if ilines[i] == "  )")
    ilines[close_at:close_at] = facts
    instance = "\n".join(ilines) + "\n"

    # Every cell a new fact names must be a declared object, or the fact is about
    # nothing — the same closing check D-A3-005's patch makes, for the same
    # reason: `(:objects)` is built from the arena and a fact naming a cell
    # outside it is silently inert.
    declared = instance.split("(:init")[0]
    for fact in facts:
        token = fact.rstrip(")").split()[-1]
        if re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(token), declared) is None:
            raise PushPatchError(
                "%s names %s, which is not in (:objects)" % (fact.strip(), token))

    return domain, instance, {
        "pushables": len(objects),
        "objects": objects,
        "predicates": [_predicate(o) for o in objects],
        "push_actions_rewritten": rewritten,
        "duplicate_actions_deleted": deleted,
        "moves_guarded": guarded,
        "init_facts": [f.strip() for f in facts],
        "object_cells": {o: list(object_cells[o]) for o in objects},
    }


def _push_action(action: str, direction: str, obj: str,
                 objects: Sequence[str]) -> str:
    """Two objects, one action — the manual's two same-guard rules, encoded once."""
    clear = " ".join("(not (%s ?beyond))" % _predicate(o) for o in objects)
    return "\n".join([
        "  (:action %s" % action,
        "    :parameters (?from - cell ?p - cell ?beyond - cell)",
        "    :precondition (and (at ?from) (adj-%s ?from ?p) (%s ?p)"
        % (direction, _predicate(obj)),
        "                       (adj-%s ?p ?beyond) (passable ?p) "
        "(passable ?beyond) %s)" % (direction, clear),
        "    :effect (and (not (at ?from)) (at ?p)",
        "                 (not (%s ?p)) (%s ?beyond))"
        % (_predicate(obj), _predicate(obj)),
        "  )",
        "",
        "",
    ])


def _guard_move(action: str, block: str, objects: Sequence[str]) -> str:
    """`free(?to)` reads the rendered frame, and a pushable is drawn on it."""
    old = "(passable ?to))"
    if block.count(old) != 1:
        raise PushPatchError(
            "action %s: expected exactly one `%s`, found %d"
            % (action, old, block.count(old)))
    extra = " ".join("(not (%s ?to))" % _predicate(o) for o in objects)
    return block.replace(old, "(passable ?to) %s)" % extra)
