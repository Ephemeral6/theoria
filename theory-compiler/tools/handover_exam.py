"""Mark a fresh reader of a handover package — the C8 acceptance test.

    python -m tools.handover_exam sheet  <package_dir> <sheet.json>
    python -m tools.handover_exam mark   <package_dir> <sheet.json> <answers.json>

Three questions, the three C8 names: what one action does and which rule
accounts for it; which of these names are level data; and what to do next from a
given position. All three truths are computed **from the package itself** — from
the executable form it ships, grounded on the boards it ships — and never from
the repository the package was cut out of. That is the right oracle for this
test: the question is whether the package can be read, not whether the manual
inside it is true of some world the reader was never shown.

--------------------------------------------------------------------------
Why the level-data family is built rather than written
--------------------------------------------------------------------------

A hand-written list of "these are level data" is an answer key, and an answer key
is a place for the builder's belief to hide. Instead every candidate name is a
**probe**: a function of one grounded predictor. A probe is asked of both boards,
and the pair of answers decides which family the name belongs to:

  * the probe reads a constant the *board* supplies and the two boards **differ**
    → the name is level data, demonstrated;
  * the probe reads something the *manual* fixes — a rule name, a semantics
    setting, the displacement a rule applies — and the two boards agree, as they
    must → the name is world law.

A name that is board-supplied but happens to read the same on both boards is
**dropped from the sheet, not guessed at**. `board_shape` is the standing
example: both boards here are the same size, so this package cannot demonstrate
that size varies, and asking would be marking a reader against something the
package does not show. Dropped names are listed in the sheet's `excluded` field
with the reason, so the coverage this exam does not have is legible instead of
being quietly absent.

--------------------------------------------------------------------------
What is deliberately not measured
--------------------------------------------------------------------------

Nothing here scores the manual. If a rule of the manual is wrong about the world
`a0-spike` simulates, a reader who reproduces the manual faithfully scores full
marks — correctly. Conflating the two would mean a package could fail because its
manual was wrong, and the thing under test is the package.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
from collections import deque
from typing import Any, Dict, List, Optional, Sequence, Tuple

ABSTAIN = "abstain"


def _digest(*parts: str) -> str:
    """A short id derived from the question and never from the answer."""
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:8]


class ExamError(RuntimeError):
    pass


# =========================================================================
# loading a package's executable forms
# =========================================================================

def load_levels(package_dir: str) -> Dict[str, Dict[str, Any]]:
    """Every board's predictor, executed under a private module name."""
    levels_dir = os.path.join(package_dir, "levels")
    if not os.path.isdir(levels_dir):
        raise ExamError("no levels/ in %s" % package_dir)
    out: Dict[str, Dict[str, Any]] = {}
    for level_id in sorted(os.listdir(levels_dir)):
        path = os.path.join(levels_dir, level_id, "predictor.py")
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        # A real module object, registered: `@dataclass` resolves annotations
        # through `sys.modules[cls.__module__]`, and a bare exec namespace makes
        # that lookup return None.
        module_name = "handover_exam._pkg_%s_%s" % (
            os.path.basename(os.path.abspath(package_dir)).replace("-", "_"),
            level_id.replace("-", "_"))
        spec = importlib.util.spec_from_loader(module_name, loader=None)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        exec(compile(source, path, "exec"), module.__dict__)      # noqa: S102
        namespace: Dict[str, Any] = module.__dict__
        namespace["__source__"] = source
        namespace["__declared_rules__"] = declared_rules(package_dir)
        out[level_id] = namespace
    if not out:
        raise ExamError("no predictor.py under %s" % levels_dir)
    return out


def _fields(namespace: Dict[str, Any]) -> List[str]:
    return sorted(namespace["State"].__dataclass_fields__)


def _state_text(state: Any, fields: Sequence[str]) -> str:
    parts = []
    for name in fields:
        value = getattr(state, name)
        parts.append("%s=%s" % (name, _value_text(value)))
    return "; ".join(parts)


def _value_text(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, tuple):
        return "(%s)" % ",".join(str(v) for v in value)
    return str(value)


def _state_from_text(text: str, fields: Sequence[str],
                     namespace: Dict[str, Any]) -> Optional[Any]:
    state = namespace["State"]()
    seen = set()
    for chunk in text.split(";"):
        chunk = chunk.strip()
        if not chunk or "=" not in chunk:
            continue
        key, raw = chunk.split("=", 1)
        key, raw = key.strip(), raw.strip()
        if key not in fields:
            return None
        seen.add(key)
        setattr(state, key, _parse_value(raw))
    if seen != set(fields):
        return None
    return state


def _parse_value(raw: str) -> Any:
    low = raw.lower()
    if low in ("true", "false"):
        return low == "true"
    if raw.startswith("(") and raw.endswith(")"):
        inner = raw[1:-1].replace(" ", "")
        if not inner:
            return ()
        return tuple(int(v) for v in inner.split(","))
    try:
        return int(raw)
    except ValueError:
        return raw


def _fire(namespace: Dict[str, Any], state: Any, action: Any) -> Tuple[Any, List[str]]:
    """The successor, and every rule whose guard held.

    The list is returned rather than the single name the manual promises, so a
    manual that fires two rules is visible here as two rather than silently
    collapsing to the first.
    """
    fired = []
    result = state.copy()
    for name, guard, effect, _objs in namespace["RULES"]:
        if guard(state, action):
            fired.append(name)
    if fired:
        result = namespace["step"](state, action)
    return result, fired


_RULE_HEADER = re.compile(r"^\s*rule\s+([A-Za-z_][A-Za-z0-9_]*)", re.M)


def declared_rules(package_dir: str) -> List[str]:
    """The rule names the manual itself writes.

    Needed because a schema rule grounds to one compiled rule per direction —
    `walk` becomes `walk_up`, `walk_down`, … — while a rule that merely *ends*
    in a direction word does not. Stripping a trailing `_left` from every
    compiled name turns `door_opens_left`, a rule of the cart manual, into
    `door_opens`, a rule of nothing; the manual is the only thing that knows
    which is which.
    """
    path = os.path.join(package_dir, "manual", "MANUAL.dsl")
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    body = "\n".join(line.split("#", 1)[0] for line in text.split("\n"))
    return sorted(set(_RULE_HEADER.findall(body)), key=len, reverse=True)


def _schema_name(grounded: str, namespace: Dict[str, Any]) -> str:
    """The compiled rule's name in the manual's own words."""
    declared = namespace.get("__declared_rules__") or []
    if grounded in declared:
        return grounded
    for name in declared:
        if grounded.startswith(name + "_"):
            suffix = grounded[len(name) + 1:]
            if suffix in namespace.get("DIRECTIONS", {}):
                return name
    return grounded


def _reachable(namespace: Dict[str, Any], limit: int = 60000) -> List[Any]:
    start = namespace["State"]()
    seen = {start.key(): start}
    queue = deque([start])
    order = [start]
    while queue and len(seen) < limit:
        current = queue.popleft()
        for action in namespace["ACTIONS"]:
            nxt = namespace["step"](current, action)
            if nxt.key() in seen:
                continue
            seen[nxt.key()] = nxt
            order.append(nxt)
            queue.append(nxt)
    return order


def _distance(namespace: Dict[str, Any], state: Any,
              limit: int = 60000) -> Optional[int]:
    if namespace["is_goal"](state):
        return 0
    seen = {state.key()}
    queue = deque([(state, 0)])
    while queue and len(seen) < limit:
        current, depth = queue.popleft()
        for action in namespace["ACTIONS"]:
            nxt = namespace["step"](current, action)
            if nxt.key() in seen:
                continue
            if namespace["is_goal"](nxt):
                return depth + 1
            seen.add(nxt.key())
            queue.append((nxt, depth + 1))
    return None


def _optimal_actions(namespace: Dict[str, Any], state: Any) -> List[str]:
    here = _distance(namespace, state)
    if here is None or here == 0:
        return []
    out = []
    for action in namespace["ACTIONS"]:
        nxt = namespace["step"](state, action)
        if nxt.key() == state.key():
            continue
        there = _distance(namespace, nxt)
        if there is not None and there == here - 1:
            out.append(_action_text(action))
    return out


def _action_text(action: Any) -> str:
    if isinstance(action, tuple) and len(action) >= 2:
        return "%s(%s)" % (action[0], ", ".join(str(a) for a in action[1:]))
    return str(action)


def _action_of_text(text: str, namespace: Dict[str, Any]) -> Optional[Any]:
    wanted = " ".join(text.split()).replace(" ", "")
    for action in namespace["ACTIONS"]:
        if _action_text(action).replace(" ", "") == wanted:
            return action
    return None


# =========================================================================
# family 2 -- probes
# =========================================================================

def _probes(namespace: Dict[str, Any]) -> Dict[str, Tuple[str, str, str]]:
    """name -> (origin, value, definition).

    `origin` is where the value comes from: `board` for something a level file
    supplies, `manual` for something the manual fixes.  It is assigned by *which
    part of the compiled form the probe reads*, never by what the answer ought
    to be.
    """
    out: Dict[str, Tuple[str, str, str]] = {}
    background = namespace["BACKGROUND"]
    board = namespace.get("BOARD") or []

    out["wall_cells"] = (
        "board",
        json.dumps(sorted([r, c] for r, row in enumerate(board)
                          for c, v in enumerate(row) if v != background)),
        "which cells of the `board` array carry a colour other than the "
        "background — the cells `free` refuses for that reason. (The package "
        "does not use the word `wall_cells`; this item names the thing, not a "
        "term of art.)")
    out["board_shape"] = ("board", json.dumps(list(namespace["GRID"] or [])),
                          "how many rows the board has and how many columns")
    out["background_colour"] = ("board", str(background),
                                "which colour counts as an empty cell")
    for name in sorted(namespace.get("LANDMARKS", {})):
        out["landmark_" + name] = (
            "board", _value_text(namespace["LANDMARKS"][name]),
            "which cell the name `%s` refers to" % name)

    defaults = namespace["State"]()
    for field in _fields(namespace):
        out["start_" + field] = (
            "board", _value_text(getattr(defaults, field)),
            "the value of `%s` before any action has been taken" % field)

    out["rule_names"] = (
        "manual",
        json.dumps(sorted({_schema_name(n, namespace)
                           for n, _g, _e, _o in namespace["RULES"]})),
        "the set of rules that account for what happens")
    for key in sorted(namespace["SEMANTICS"]):
        out["semantics_" + key] = (
            "manual", str(namespace["SEMANTICS"][key]),
            "the world's `%s` setting — how a turn is put together" % key)
    out["direction_vocabulary"] = (
        "manual", json.dumps(sorted(namespace.get("DIRECTIONS", {}))),
        "which directions exist at all")
    out["action_vocabulary"] = (
        "manual", json.dumps(sorted(_action_text(a) for a in namespace["ACTIONS"])),
        "the actions that can be taken")
    out["goal_form"] = (
        "manual", _goal_source(namespace),
        "the *shape* of the winning condition — which object has to be where — "
        "as opposed to the particular cell, which is a separate name")
    for rule_name, (origin, displacement) in sorted(
            _effect_signature(namespace).items()):
        out["effect_of_" + rule_name] = (
            origin, displacement,
            "what the rule `%s` does to each thing it touches, in cells "
            "travelled" % rule_name)
    return out


_EFFECT_HEADER = "def _effect_%s(state):"


def _effect_origin(rule_name: str, namespace: Dict[str, Any]) -> str:
    """`manual` unless the rule's effect reads something a board supplies.

    A rule is world law; *what it does* need not be. `teleport_down` puts the
    Cart on the cell `portal_exit` names, and only the board says which cell
    that is — so the displacement it applies is board data wearing a rule's
    name. Classifying it `manual` because two boards happened to place the
    landmark identically would mark a reader wrong for noticing, which is what
    it did before this function existed.
    """
    source = namespace["__source__"]
    header = _EFFECT_HEADER % rule_name
    start = source.find(header)
    if start == -1:
        return "manual"
    end = source.find("\ndef ", start + len(header))
    body = source[start:end if end != -1 else len(source)]
    return "board" if "LANDMARKS[" in body else "manual"


def _goal_source(namespace: Dict[str, Any]) -> str:
    lines = namespace["__source__"].split("\n")
    for n, line in enumerate(lines):
        if line.startswith("def is_goal"):
            return " ".join(" ".join(lines[n + 1:n + 4]).split())
    raise ExamError("the shipped predictor states no goal")


def _effect_signature(namespace: Dict[str, Any]) -> Dict[str, Tuple[str, str]]:
    """What each rule *does*, measured by applying its effect to a probe state.

    Read off the compiled effect rather than off the source text: a rule's
    displacement is the fact a step-semantics question turns on, and measuring it
    cannot drift out of step with the rule the way a transcription can.
    """
    out: Dict[str, Tuple[str, str]] = {}
    for name, _guard, effect, _objs in namespace["RULES"]:
        origin = _effect_origin(name, namespace)
        before = namespace["State"]()
        after = before.copy()
        try:
            effect(after)
        except Exception:                          # noqa: BLE001
            # A rule the level cannot even *apply* -- `gen_python` emits rules
            # for object types the level does not instantiate, so the effect
            # assigns a field this board's `State` has not got. Board-dependent
            # by definition, which is what the origin says.
            out[_schema_name(name, namespace)] = ("board", "unmeasurable")
            continue
        changes = []
        for field in _fields(namespace):
            a, b = getattr(before, field), getattr(after, field)
            if a == b:
                continue
            if isinstance(a, tuple) and isinstance(b, tuple) and len(a) == len(b):
                changes.append("%s moves by (%s)"
                               % (field, ",".join(str(y - x) for x, y in zip(a, b))))
            else:
                changes.append("%s becomes %s" % (field, _value_text(b)))
        out.setdefault(_schema_name(name, namespace),
                       (origin,
                        "; ".join(changes) if changes else "nothing changes"))
    return out


# =========================================================================
# the sheet
# =========================================================================

def build_sheet(package_dir: str) -> Dict[str, Any]:
    levels = load_levels(package_dir)
    level_ids = sorted(levels)
    if len(level_ids) < 2:
        raise ExamError("the level-data family needs two boards; found %d"
                        % len(level_ids))
    probe_a, probe_b = (_probes(levels[level_ids[0]]),
                        _probes(levels[level_ids[1]]))

    items: List[Dict[str, Any]] = []
    excluded: List[Dict[str, str]] = []

    # ---- family 1: step semantics ---------------------------------------
    for level_id in level_ids:
        namespace = levels[level_id]
        fields = _fields(namespace)
        seen_rules = set()
        for state in _reachable(namespace, limit=4000):
            for action in namespace["ACTIONS"]:
                nxt, fired = _fire(namespace, state, action)
                if len(fired) != 1:
                    continue
                schema = _schema_name(fired[0], namespace)
                if schema in seen_rules:
                    continue
                seen_rules.add(schema)
                items.append({
                    # Stable across sheet revisions and answer-free. Keying on
                    # the rule would put the answer in the item id; keying on
                    # position renumbers every later item when one is dropped,
                    # and a set of answers that stops lining up reads as the
                    # reader having been wrong. The question decides the id.
                    "item_id": "step-%s-%s" % (
                        level_id,
                        _digest(level_id, _state_text(state, fields),
                                _action_text(action))),
                    "kind": "step_semantics",
                    "level": level_id,
                    "before": _state_text(state, fields),
                    "action": _action_text(action),
                    "prompt": ("The action %s is taken from the situation given "
                               "in `before`. Give the situation afterwards and "
                               "name the rule that accounts for it."
                               % _action_text(action)),
                    "truth": {"after": _state_text(nxt, fields),
                              "rule": schema,
                              "grounded_rule": fired[0]},
                })
        if seen_rules:
            continue

    # ---- family 2: level data vs world law ------------------------------
    for name in sorted(set(probe_a) & set(probe_b)):
        origin, value_a, definition = probe_a[name]
        _origin_b, value_b, _def_b = probe_b[name]
        if origin == "board":
            if value_a == value_b:
                excluded.append({
                    "name": name,
                    "why": ("supplied by a board, but the two boards in this "
                            "package happen to agree, so the package cannot "
                            "demonstrate that it varies")})
                continue
            truth = "level_data"
        else:
            if value_a != value_b:
                # Not necessarily a defect: the two boards need not instantiate
                # the same objects, and a rule touching an object one board does
                # not have has nothing to do there. Either way the package
                # cannot demonstrate that this name is fixed, so it is dropped
                # and the disagreement is written down rather than resolved by
                # the builder's opinion.
                excluded.append({
                    "name": name,
                    "why": ("fixed by the manual, but the two grounded forms "
                            "read differently (%s: %s / %s: %s) — most often "
                            "because the boards instantiate different objects"
                            % (level_ids[0], value_a, level_ids[1], value_b))})
                continue
            truth = "world_law"
        items.append({
            # Keyed by the probe, not by position. A positional id renumbers
            # every item after the one that gets dropped, so a set of answers
            # stops lining up with the sheet it was written for and the
            # mismatch reads as the reader having been wrong.
            "item_id": "name-%s" % name,
            "kind": "name_class",
            "name": name,
            "definition": definition,
            "prompt": ("Is `%s` — %s — supplied by each individual board, or "
                       "fixed by the world for every board?" % (name, definition)),
            "truth": {"class": truth},
        })

    # ---- family 3: optimal action ---------------------------------------
    for level_id in level_ids:
        namespace = levels[level_id]
        fields = _fields(namespace)
        picked = 0
        for state in _reachable(namespace, limit=4000):
            if picked >= 2:
                break
            actions = _optimal_actions(namespace, state)
            if not actions:
                continue
            distance = _distance(namespace, state)
            if distance is None or distance < 2:
                continue
            picked += 1
            items.append({
                "item_id": "opt-%s-%s" % (
                    level_id, _digest(level_id, _state_text(state, fields))),
                "kind": "optimal_action",
                "level": level_id,
                "state": _state_text(state, fields),
                "prompt": ("Name one action that begins a shortest sequence of "
                           "actions ending in a won game."),
                "truth": {"optimal_actions": actions, "distance": distance},
            })

    return {
        "package": os.path.basename(os.path.abspath(package_dir)),
        "levels": level_ids,
        "state_fields": {lid: _fields(levels[lid]) for lid in level_ids},
        "action_vocabulary": {lid: sorted(_action_text(a)
                                          for a in levels[lid]["ACTIONS"])
                              for lid in level_ids},
        "rule_vocabulary": {lid: sorted({_schema_name(n, levels[lid])
                                         for n, _g, _e, _o in levels[lid]["RULES"]})
                            for lid in level_ids},
        "excluded": excluded,
        "items": items,
    }


def reader_sheet(sheet: Dict[str, Any]) -> Dict[str, Any]:
    """The sheet minus the answers.  What the reader is actually handed."""
    # A per-board block for something every board agrees on is a cue that the
    # thing is per-board data -- which is the exact mistake one family of items
    # exists to detect. Collapse anything identical across boards into one
    # entry, so the sheet stops arguing with its own questions.
    def _collapse(block):
        values = list(block.values())
        if values and all(v == values[0] for v in values[1:]):
            return {"every board": values[0]}
        return block

    return {
        "levels": sheet["levels"],
        "state_fields": _collapse(sheet["state_fields"]),
        "action_vocabulary": _collapse(sheet["action_vocabulary"]),
        "rule_vocabulary": _collapse(sheet["rule_vocabulary"]),
        "answer_grammar": {
            "step_semantics": ("`<field>=<value>; …; rule=<name>` — every field "
                               "listed in `state_fields` for that level, in any "
                               "order, plus `rule`. A cell is written `(row,col)` "
                               "and a true/false value `true` or `false`. The "
                               "rule name must be one from `rule_vocabulary`."),
            "name_class": ("exactly one word: `level_data` if a board supplies "
                           "it, `world_law` if no board can change it. There "
                           "are only these two words, so something fixed by the "
                           "language the manual is written in — rather than by "
                           "this particular world — is still `world_law`: no "
                           "board supplies it."),
            "optimal_action": ("exactly one action, written as it appears in "
                               "`action_vocabulary`"),
            "any": ("`abstain` is allowed anywhere; it scores nothing and is "
                    "recorded as an abstention rather than as a wrong answer"),
        },
        "items": [{k: v for k, v in item.items() if k != "truth"}
                  for item in sheet["items"]],
    }


# =========================================================================
# marking
# =========================================================================

def mark(package_dir: str, sheet: Dict[str, Any],
         answers: Dict[str, str]) -> Dict[str, Any]:
    levels = load_levels(package_dir)
    scores = []
    for item in sheet["items"]:
        given = answers.get(item["item_id"])
        scores.append(_mark_one(item, given, levels))
    by_kind: Dict[str, Dict[str, int]] = {}
    for score in scores:
        bucket = by_kind.setdefault(score["kind"],
                                    {"right": 0, "wrong": 0, "abstain": 0,
                                     "unparsed": 0, "unanswered": 0})
        bucket[score["verdict"]] += 1
    total = len(scores)
    right = sum(1 for s in scores if s["verdict"] == "right")
    return {
        "package": sheet["package"],
        "items": total,
        "right": right,
        "fraction": round(right / total, 6) if total else 0.0,
        "by_kind": dict(sorted(by_kind.items())),
        "failed": [s for s in scores if s["verdict"] != "right"],
        "scores": scores,
    }


def _mark_one(item: Dict[str, Any], given: Optional[str],
              levels: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    base = {"item_id": item["item_id"], "kind": item["kind"], "given": given}
    if given is None:
        return dict(base, verdict="unanswered", why="no answer submitted")
    text = " ".join(str(given).split())
    if text.lower() == ABSTAIN:
        return dict(base, verdict="abstain", why="abstained")

    kind = item["kind"]
    if kind == "name_class":
        if text not in ("level_data", "world_law"):
            return dict(base, verdict="unparsed",
                        why="not one of level_data / world_law")
        return dict(base,
                    verdict="right" if text == item["truth"]["class"] else "wrong",
                    why="expected %s" % item["truth"]["class"])

    namespace = levels[item["level"]]
    if kind == "optimal_action":
        if _action_of_text(text, namespace) is None:
            return dict(base, verdict="unparsed", why="not an action of this world")
        accepted = [a.replace(" ", "") for a in item["truth"]["optimal_actions"]]
        return dict(base,
                    verdict="right" if text.replace(" ", "") in accepted else "wrong",
                    why="accepted: %s" % ", ".join(item["truth"]["optimal_actions"]))

    if kind == "step_semantics":
        fields = _fields(namespace)
        rule = None
        state_parts = []
        for chunk in text.split(";"):
            chunk = chunk.strip()
            if chunk.lower().startswith("rule="):
                rule = chunk.split("=", 1)[1].strip()
            elif chunk:
                state_parts.append(chunk)
        state = _state_from_text("; ".join(state_parts), fields, namespace)
        if state is None or rule is None:
            return dict(base, verdict="unparsed",
                        why="expected every field of %s plus rule=" % fields)
        want_state = _state_from_text(item["truth"]["after"], fields, namespace)
        state_ok = state.key() == want_state.key()
        rule_ok = rule in (item["truth"]["rule"], item["truth"]["grounded_rule"])
        return dict(base,
                    verdict="right" if (state_ok and rule_ok) else "wrong",
                    why="expected %s; rule=%s (state %s, rule %s)"
                        % (item["truth"]["after"], item["truth"]["rule"],
                           "ok" if state_ok else "wrong",
                           "ok" if rule_ok else "wrong"))
    raise ExamError("unknown item kind %r" % kind)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tools.handover_exam")
    sub = parser.add_subparsers(dest="command", required=True)
    make = sub.add_parser("sheet")
    make.add_argument("package")
    make.add_argument("out")
    make.add_argument("--reader-out", help="where to write the answer-free sheet")
    grade = sub.add_parser("mark")
    grade.add_argument("package")
    grade.add_argument("sheet")
    grade.add_argument("answers")
    grade.add_argument("--out")
    args = parser.parse_args(argv)

    if args.command == "sheet":
        sheet = build_sheet(args.package)
        _write_json(args.out, sheet)
        if args.reader_out:
            _write_json(args.reader_out, reader_sheet(sheet))
        print("%d items (%d excluded names) from %s"
              % (len(sheet["items"]), len(sheet["excluded"]), args.package))
        return 0

    with open(args.sheet, encoding="utf-8") as handle:
        sheet = json.load(handle)
    with open(args.answers, encoding="utf-8") as handle:
        answers = json.load(handle)
    report = mark(args.package, sheet, answers)
    if args.out:
        _write_json(args.out, report)
    print("%s: %d/%d right (%s)"
          % (report["package"], report["right"], report["items"],
             json.dumps(report["by_kind"], sort_keys=True)))
    for score in report["failed"]:
        print("  %-22s %-9s given=%r  %s"
              % (score["item_id"], score["verdict"], score["given"], score["why"]))
    return 0 if report["right"] == report["items"] else 1


def _write_json(path: str, doc: Any) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(doc, indent=2, sort_keys=True,
                                ensure_ascii=False) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
