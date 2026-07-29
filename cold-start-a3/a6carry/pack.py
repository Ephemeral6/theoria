"""**carrypack v1** — what "carrying the two books" is, as a file format.

A3 carried a domain by passing a path to it.  That works when the same session
wrote it an hour earlier and every upstream file is the one it compiled against.
It is not a form anything online can be handed, for three reasons, and each one
is a section of `PACK.json`:

1. **The books alone do not say what they need.**  `theory/domain.dsl` names
   `landmark exit_a` but not that a level must supply a coordinate for it; it
   guards on `colored(above(Cart), 7)` but not that colour 7 is the Switch.  A
   receiver that has to work those out by reading the manual is a receiver that
   can get them wrong silently.  → `requires`.

2. **A playbook entry that is a theorem is not the same kind of thing as a
   heuristic**, and only the first kind is worth carrying without re-earning.
   → `theorems`, lifted out of the parsed AST rather than retyped, so a claim
   cannot enter the pack that is not in the book.

3. **A domain compiled against a different backend is a different domain.**
   `_bootstrap.upstream_pin()` already hashes every upstream file into every A3
   manifest, and `monitor/inbox/20260728T082700Z-W-1521-…` reports what that is
   worth in practice: *nothing in the repository ever compares two of them.*  A
   contract change arrived on a commit that track had never touched and the
   first thing that noticed was a paid model call being thrown away.  A
   fingerprint with no consumer is not a check.  → `fingerprint`, and
   `protocol.carry` **refuses to run** when it drifts.

## The layout on disk

```
<pack>/
  PACK.json      the manifest below
  domain.dsl     verbatim, byte-identical to the file the source level produced
  playbook.dsl   verbatim
```

Nothing generated goes in the pack.  A compiled form belongs to one level and
the whole point of the pack is that it belongs to none.

## What is derived and what is declared

Almost all of `requires` is read off the parsed AST, because a field a human
retypes is a field that can disagree with the book:

| field | source |
|---|---|
| `objects[].fields`, `landmarks` | the `word_table` |
| `objects[].movable` | does any rule's event move or jump it |
| `objects[].colours` | declared, **then checked** against every `recolored` literal |
| `guard_colours` | every `colored(_, k)` literal in every rule |
| `mover` | the object every `act=push(<obj>, _)` names |
| `directions` | the direction literals the rules actually use |
| `semantics` | the `semantics:` section |
| `supplied_constants` | `goal_cell` when there is no `goal:` section, plus every landmark |
| `forms` | which backends can honestly render this domain (see `emittable_forms`) |

The one genuinely declared thing is an object's **base colour**, and it is
declared because it is not in the book: A0's word table gives an object a
`color: Int` field and never a value.  It is checked rather than trusted — every
colour a `recolored` effect can produce must be in the object's colour set, or
`build` raises.
"""

import hashlib
import json
import os
import platform
import re
import sys
from typing import Dict, List, Optional, Sequence, Set, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from theory_compiler.parser.ast_nodes import (  # noqa: E402
    FuncCall, GuardAction, GuardPredicate, NameRef, NumberLit, TheoryAST,
)
from theory_compiler.parser.playbook_parser import (  # noqa: E402
    PlaybookParseError, parse_playbook,
)
from theory_compiler.parser.theory_parser import parse_theory  # noqa: E402

from compile.dialect import parse_semantics  # noqa: E402  (cold-start-a0)

FORMAT = "carrypack/1"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(ROOT)

#: Every upstream file the compile/certify/plan path executes, relative to the
#: repository root.  Three tracks and one contract directory: a change to any of
#: them changes what a carried domain compiles to, and none of them is ours.
#:
#: Listed as explicit paths rather than a directory walk on purpose — a walk
#: would silently absorb a new file (drift the fingerprint cannot attribute) and
#: would also pick up `__pycache__`.  A file that disappears is reported as
#: `missing` rather than dropped, for the same reason.
FINGERPRINT_FILES: Tuple[str, ...] = (
    "CONTRACTS/dsl_grammar_v0.2.md",
    "CONTRACTS/candidates_schema.md",
    "theory-compiler/src/theory_compiler/parser/ast_nodes.py",
    "theory-compiler/src/theory_compiler/parser/theory_parser.py",
    "cold-start-a0/compile/compile_a0.py",
    "cold-start-a0/compile/dialect.py",
    "cold-start-a0/compile/gen_lean_a0.py",
    "cold-start-a0/compile/gen_pddl_a0.py",
    "cold-start-a0/compile/gen_python_a0.py",
    "cold-start-a0/compile/problem.py",
    "cold-start-a0/certify/lean_check.py",
    "cold-start-a0/certify/replay.py",
    "engine-rig/common/candidates.py",
    "engine-rig/engines/fd_adapter/__init__.py",
)

#: The four co-derived forms, and the backend that produces each.
ALL_FORMS: Tuple[str, ...] = ("python", "markdown", "pddl", "lean")


class PackError(Exception):
    """The pack cannot be built or is not usable as declared."""


# --------------------------------------------------------------------- hashing

def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def sha256_file(path: str) -> str:
    with open(path, "rb") as handle:
        return sha256_bytes(handle.read())


# ----------------------------------------------------------------- AST reading

def _rule_event(rule) -> Tuple[str, Optional[str], List[object]]:
    """`(event name, first argument's object name, the remaining arguments)`."""
    event = rule.event
    if not isinstance(event, FuncCall):
        raise PackError("rule %s: the event must be a call" % rule.name)
    obj = event.args[0].name if event.args and isinstance(event.args[0], NameRef) \
        else None
    return event.name, obj, list(event.args[1:])


def _guard_facts(rule) -> Dict[str, object]:
    """One rule's guard, flattened into the three things a receiver must know.

    `action`/`direction` come from the `act=` clause, `colours` from every
    `colored(_, k)` literal, and `shape` is the whole guard as sorted text — the
    same normal form `gen_pddl_a0._guard_key` uses to recognise a cascade, so a
    reader comparing the pack against the generated PDDL is comparing like with
    like.
    """
    action = direction = None
    colours: List[int] = []
    parts: List[str] = []
    for clause in rule.guard.clauses:
        if isinstance(clause, GuardAction):
            act = clause.action
            names = [getattr(a, "name", str(a)) for a in act.args]
            action = names[0] if names else None
            direction = names[1] if len(names) > 1 else None
            parts.append("act=%s(%s)" % (act.action_name, ",".join(names)))
            continue
        if isinstance(clause, GuardPredicate) and isinstance(clause.expr, FuncCall):
            expr = clause.expr
            args = []
            for arg in expr.args:
                if isinstance(arg, NumberLit):
                    args.append(str(arg.value))
                    if expr.name == "colored":
                        colours.append(int(arg.value))
                elif isinstance(arg, FuncCall):
                    inner = ",".join(getattr(a, "name", "?") for a in arg.args)
                    args.append("%s(%s)" % (arg.name, inner))
                else:
                    args.append(getattr(arg, "name", "?"))
            parts.append("%s(%s)" % (expr.name, ",".join(args)))
            continue
        raise PackError("rule %s: guard clause %r is outside carrypack's "
                        "vocabulary" % (rule.name, clause))
    return {"action_object": action, "direction": direction,
            "colours": sorted(set(colours)), "shape": sorted(parts)}


def _mover(ast: TheoryAST) -> str:
    movers = set()
    for rule in ast.rules.rules:
        for clause in rule.guard.clauses:
            if isinstance(clause, GuardAction) and clause.action.args:
                movers.add(getattr(clause.action.args[0], "name", None))
    movers.discard(None)
    if len(movers) != 1:
        raise PackError(
            "carrypack v1 carries a domain with exactly one acted-on object; "
            "this one names %r.  The backends agree with that restriction — "
            "`gen_pddl_a0.generate_pddl` looks the mover up by the literal name "
            "`Cart` — so relaxing it here would only move the failure."
            % sorted(movers))
    return sorted(movers)[0]


def emittable_forms(ast: TheoryAST, mover: str) -> Tuple[List[str], Dict[str, str]]:
    """Which of the four co-derived forms this domain may honestly be compiled to.

    **D-A6-002 — `gen_lean_a0` cannot see a second object's position.**
    `build_axes` (`gen_lean_a0.py:126-133`) collects state axes from the fields
    of every non-mover object whose name ends `_colour` or `_present`, and from
    nothing else.  A `Block_pos` is not a candidate, so it is not an axis, so it
    is not in the state type, so the transition table `_states`/`_term` transcribe
    is the manual's `step` *with that object frozen at its initial cell*.

    The result is not a compile error.  It is a Lean file that compiles, whose
    `inv_init`/`inv_closed`/`inv_all` pass, and whose `#print axioms` comes back
    empty — a green certificate about a **projection** of the manual, presented as
    a certificate about the manual.  That is D-A3-007's failure mode (a vacuous
    certificate that no acceptance criterion can distinguish from a real one)
    arriving from a different direction, and it is worse in one respect: the
    vacuous invariant at least proved a true thing (`True`).

    So a pack whose domain moves any object other than the mover declares `lean`
    **withheld**, with the reason recorded, and `protocol.carry` emits three
    forms and says so.  Fixing it means rewriting another track's generator,
    which is outside this item and is reported to that track instead.
    """
    withheld: Dict[str, str] = {}
    moved_others = sorted({
        obj for rule in ast.rules.rules
        for name, obj, _rest in [_rule_event(rule)]
        if name in ("moved", "jumped") and obj is not None and obj != mover
    })
    if moved_others:
        withheld["lean"] = (
            "D-A6-002: gen_lean_a0.build_axes admits only non-mover `_colour` "
            "and `_present` fields as state axes, so the position of %s is not "
            "in the Lean state type.  The file would compile green and "
            "axiom-free about a projection of this manual.  Withheld rather "
            "than emitted." % ", ".join(moved_others))
    forms = [f for f in ALL_FORMS if f not in withheld]
    return forms, withheld


def domain_laws(ast: TheoryAST) -> List[Dict[str, object]]:
    """The `laws:` section of a domain, lifted from its AST.

    A `theorem` carries a natural-language statement, a `depends:` list naming
    the rules it rests on, and a `probe:` verdict.  All three travel: the
    statement so a receiver knows what was claimed, the dependency list so the
    pack can check those rules are still in the domain it is carrying
    (`requires.theorem_dependencies`), and the probe verdict so a claim that was
    never probed cannot be mistaken for one that was.

    `invariant` entries travel too, tagged `kind: "invariant"`.  They are the
    cheaper half — an invariant is machine-checkable against the state space and
    a theorem generally is not — and keeping them apart is what stops a pack from
    reporting "3 theorems carried" when two of them were counting laws.
    """
    out: List[Dict[str, object]] = []
    laws = ast.laws
    for inv in (getattr(laws, "invariants", None) or []):
        out.append({
            "book": "domain", "kind": "invariant", "name": inv.name,
            "statement": "%s %s %s" % (inv.expr_text, inv.op, inv.value),
            "depends": [], "probe": None,
            "status": inv.status, "source": inv.source,
        })
    for thm in (getattr(laws, "theorems", None) or []):
        out.append({
            "book": "domain", "kind": "theorem", "name": thm.name,
            "statement": thm.description,
            "depends": list(thm.depends or []), "probe": thm.probe,
            "status": None, "source": None,
        })
    return out


def _parse_playbook_lenient(text: str) -> Tuple[object, List[Dict[str, object]]]:
    """Parse what the grammar accepts; name, by line, what it rejects.

    `parse_playbook` is all-or-nothing, and on this repository's own books that
    is a wall rather than a check.  **A3's `theory/playbook.dsl` does not parse**
    — line 81 writes `[ev: 2/2 levels, n=2 — indicative only]` where
    `_parse_prefer` accepts only `[ev: k/n]` — and nothing in A3 ever found out,
    because A3 compiles its *domain* and never once hands its playbook to a
    parser.  "Carrying the two books" was, in A3, carrying one book and a file.
    → D-A6-003.

    Refusing outright would be defensible and is the wrong call here: it would
    make the A3 negative controls unrunnable through this protocol, which is the
    one thing the item asks the controls to prove.  A rejected line is an entry
    that **does not travel**, and this function treats it as exactly that — the
    line is dropped, recorded verbatim with the parser's own message, and lands
    in the manifest under `entries_unparsed`.  A receiver reading `PACK.json`
    learns that the book was carried in part and which part was left; a receiver
    of a pack that had refused would learn nothing at all.
    """
    lines = text.splitlines()
    dead: Set[int] = set()
    unparsed: List[Dict[str, object]] = []
    for _ in range(len(lines) + 1):
        attempt = "\n".join("" if i in dead else line
                            for i, line in enumerate(lines))
        try:
            return parse_playbook(attempt), unparsed
        except PlaybookParseError as exc:
            match = re.match(r"Line (\d+):\s*(.*)", str(exc), re.S)
            if match is None:
                raise
            index = int(match.group(1)) - 1
            if index in dead or not (0 <= index < len(lines)):
                raise
            dead.add(index)
            unparsed.append({"line": index + 1, "text": lines[index].strip(),
                             "error": match.group(2).strip()})
    raise PackError("the playbook could not be parsed even one line at a time")


def playbook_entries(text: str) -> List[Dict[str, object]]:
    """The playbook's **theorem-grade** entries, and only those.

    The item asks for "playbook 定理级条目", and the playbook grammar draws that
    line itself: `order` and `prune` may carry a `proof:`, a `heuristic` may carry
    an `admissible:` justification, and a `prefer` carries only `evidence:`.  The
    first three kinds are claims that were *argued*; a preference is a claim that
    was *observed*, and observations are the part of a playbook that does not
    survive a change of level.

    So `prefer` statements are counted and dropped, and the count is in the
    manifest — a receiver can see that something was left behind rather than
    having to notice its absence.

    The literal `none` is a *refusal*, not a justification.  Both playbooks in
    this repository write `heuristic … [admissible: none]` to record that
    admissibility was considered and not claimed; reading that as theorem-grade
    would turn the most careful line in the file into the strongest one.
    """
    book, unparsed = _parse_playbook_lenient(text)
    kept: List[Dict[str, object]] = []
    dropped: List[str] = ["unparsed:line %d" % u["line"] for u in unparsed]
    for stmt in book.statements:
        kind = type(stmt).__name__.replace("Stmt", "").lower()
        justification = getattr(stmt, "proof", None) or \
            getattr(stmt, "admissible", None)
        if isinstance(justification, str) and justification.strip().lower() == "none":
            justification = None
        if justification is None:
            dropped.append("%s:%s" % (kind, getattr(stmt, "name", None)
                                      or getattr(stmt, "landmark", None)
                                      or getattr(stmt, "condition", None)))
            continue
        kept.append({
            "book": "playbook",
            "kind": kind,
            "name": (getattr(stmt, "name", None) or getattr(stmt, "landmark", None)
                     or getattr(stmt, "condition", None)),
            "statement": justification,
            "depends": list(getattr(stmt, "params", None) or []),
            "probe": None, "status": None, "source": None,
        })
    return kept, dropped, unparsed


# ------------------------------------------------------------------ fingerprint

def fingerprint(repo: str = REPO) -> Dict[str, object]:
    """sha256 every upstream file the carried domain will be compiled by.

    `interpreter` is in here for the same reason the files are: the Lean state
    enumeration and the PDDL grounding both run under it, and a minor-version
    change to the interpreter is a change to what "the same domain" compiles to.
    Only `major.minor` is recorded — a patch release is not a difference this
    check is entitled to have an opinion about, and pinning it would make every
    pack drift on every box.
    """
    files: Dict[str, str] = {}
    for rel in FINGERPRINT_FILES:
        path = os.path.join(repo, rel.replace("/", os.sep))
        files[rel] = sha256_file(path) if os.path.exists(path) else "missing"
    digest = sha256_bytes(
        json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    return {
        "files": files,
        "sha256": digest,
        "interpreter": "python%d.%d" % sys.version_info[:2],
        "platform_note": platform.system(),
    }


def compare_fingerprint(recorded: Dict[str, object],
                        current: Optional[Dict[str, object]] = None
                        ) -> Dict[str, object]:
    """Recorded against current, per file — **the consumer W-1521 asked for**.

    The inbox note is precise about why this function has to exist and not merely
    the data it reads: *"仓库里没有任何东西会去比这两个数 … 这条检查连'可选'都不是,
    它根本没有消费者."*  So the verdict is a structured object with the drifted
    paths in it, and `protocol.carry` treats `match: False` as a stop rather than
    a log line.

    `platform_note` is **not** compared.  It is recorded so a reader can see
    which box a pack was built on, but a domain that compiled on Linux and is
    carried on Windows is the situation this format is for, not a drift.
    """
    current = current or fingerprint()
    old = dict(recorded.get("files") or {})
    new = dict(current.get("files") or {})

    drifted = sorted(k for k in set(old) & set(new) if old[k] != new[k])
    removed = sorted(set(old) - set(new))
    added = sorted(set(new) - set(old))
    interpreter_changed = recorded.get("interpreter") != current.get("interpreter")

    return {
        "match": not (drifted or removed or added or interpreter_changed),
        "drifted": drifted,
        "removed": removed,
        "added": added,
        "interpreter_changed": interpreter_changed,
        "recorded_interpreter": recorded.get("interpreter"),
        "current_interpreter": current.get("interpreter"),
        "recorded_sha256": recorded.get("sha256"),
        "current_sha256": current.get("sha256"),
        "detail": {k: {"recorded": old[k], "current": new[k]} for k in drifted},
    }


# ---------------------------------------------------------------------- build

def build(pack_dir: str, domain_path: str, playbook_path: str,
          pack_id: str, origin: Dict[str, object],
          object_colours: Dict[str, Sequence[int]],
          colour_roles: Optional[Dict[int, str]] = None,
          repo: str = REPO) -> Dict[str, object]:
    """Write a carrypack.  Everything derivable is derived; the rest is checked.

    `object_colours` is the one declared input — see the module docstring on why
    a word table has a `color` field and no value.  Two checks make it a claim
    rather than a convention:

    * every object in the word table that carries a `color` field must appear,
      and nothing else may;
    * every colour some `recolored(o, k)` effect can produce must be listed for
      that object, or the rebuilder would fail to recognise the object on a level
      that starts in the other polarity.  A3's Switch is 7 up and 8 down and its
      level 2 starts up; a level that started it down would have been an object
      the rebuilder could not find, and nothing would have said so.
    """
    domain_text = open(domain_path, encoding="utf-8").read()
    playbook_text = open(playbook_path, encoding="utf-8").read()

    ast = parse_theory(domain_text)
    semantics = parse_semantics(domain_text)
    mover = _mover(ast)

    fields = {o.name: [f.name for f in o.fields] for o in ast.word_table.objects}
    landmarks = sorted(lm.name for lm in
                       (getattr(ast.word_table, "landmarks", None) or []))

    # --- what each rule does, as data -------------------------------------
    contexts: List[Dict[str, object]] = []
    movable = set()
    recolour_targets: Dict[str, List[int]] = {}
    guard_colours: List[int] = []
    directions: List[str] = []
    for rule in ast.rules.rules:
        event, obj, rest = _rule_event(rule)
        guard = _guard_facts(rule)
        guard_colours.extend(guard["colours"])
        if guard["direction"]:
            directions.append(str(guard["direction"]))
        if event in ("moved", "jumped") and obj:
            movable.add(obj)
        if event == "recolored" and obj and rest and isinstance(rest[0], NumberLit):
            recolour_targets.setdefault(obj, []).append(int(rest[0].value))
        contexts.append({
            "rule": rule.name,
            "event": event,
            "target": obj,
            "direction": guard["direction"],
            "guard_colours": guard["colours"],
            "guard": guard["shape"],
            "evidence": getattr(rule.meta, "evidence", None) if rule.meta else None,
            "coverage": getattr(rule.meta, "coverage", None) if rule.meta else None,
        })

    # --- the declared half, checked ---------------------------------------
    want_colour = sorted(n for n, fs in fields.items() if "color" in fs)
    declared = sorted(object_colours)
    if declared != want_colour:
        raise PackError(
            "object_colours must name exactly the word-table objects carrying a "
            "`color` field.  word table: %r, declared: %r" % (want_colour, declared))
    for obj, produced in sorted(recolour_targets.items()):
        listed = set(int(c) for c in object_colours.get(obj, ()))
        missing = sorted(set(produced) - listed)
        if missing:
            raise PackError(
                "the domain can recolour %s to %r, which object_colours does not "
                "list.  A level starting %s in that polarity would be invisible "
                "to the rebuilder and nothing would say so." % (obj, missing, obj))

    objects = [{
        "name": name,
        "fields": fields[name],
        "colours": sorted(int(c) for c in object_colours.get(name, ())),
        "movable": name in movable,
        "is_mover": name == mover,
    } for name in sorted(fields)]

    forms, withheld = emittable_forms(ast, mover)

    supplied = list(landmarks)
    if ast.goal is None:
        supplied.append("goal_cell")

    laws = domain_laws(ast)
    play_kept, play_dropped, play_unparsed = playbook_entries(playbook_text)
    carried = laws + play_kept

    manifest: Dict[str, object] = {
        "format": FORMAT,
        "pack_id": pack_id,
        "origin": dict(origin),
        "books": {
            "domain": {
                "file": "domain.dsl",
                "sha256": sha256_bytes(domain_text.encode("utf-8")),
                "bytes": len(domain_text.encode("utf-8")),
                "rules": len(ast.rules.rules),
                # `LawsSection` has `invariants` and `theorems`; it has no
                # `laws`, so the obvious spelling of this line reported 0 for
                # every domain ever packed -- including one with two invariants
                # and a theorem.  A count that is always zero is not a count.
                "laws": (len(getattr(ast.laws, "invariants", []) or [])
                         + len(getattr(ast.laws, "theorems", []) or [])
                         if ast.laws is not None else 0),
            },
            "playbook": {
                "file": "playbook.dsl",
                "sha256": sha256_bytes(playbook_text.encode("utf-8")),
                "bytes": len(playbook_text.encode("utf-8")),
                "entries_carried": len(play_kept),
                "entries_left_behind": play_dropped,
                "parsed": "partial" if play_unparsed else "whole",
                "entries_unparsed": play_unparsed,
            },
        },
        "theorems": carried,
        "requires": {
            "semantics": semantics.as_json(),
            "mover": mover,
            "directions": sorted(set(directions)),
            "action_vocabulary": {w: ["push", mover, d] for w, d in (
                ("UP", "up"), ("DOWN", "down"),
                ("LEFT", "left"), ("RIGHT", "right")) if d in set(directions)},
            "objects": objects,
            "guard_colours": sorted(set(guard_colours)),
            "colour_roles": {str(k): v for k, v in
                             sorted((colour_roles or {}).items())},
            "landmarks": landmarks,
            "supplied_constants": sorted(set(supplied)),
            "goal_in_domain": ast.goal is not None,
            "forms": forms,
            "forms_withheld": withheld,
            "guard_contexts": contexts,
            "theorem_dependencies": sorted({
                dep for entry in laws for dep in (entry.get("depends") or [])}),
        },
        "fingerprint": fingerprint(repo),
    }

    # every rule a theorem leans on must still be in the domain being carried
    rule_names = {r.name for r in ast.rules.rules}
    orphan = sorted(set(manifest["requires"]["theorem_dependencies"]) - rule_names)
    if orphan:
        raise PackError(
            "a theorem depends on %r, which this domain does not contain — the "
            "pack would carry a claim whose support it does not carry" % orphan)

    os.makedirs(pack_dir, exist_ok=True)
    _write(os.path.join(pack_dir, "domain.dsl"), domain_text)
    _write(os.path.join(pack_dir, "playbook.dsl"), playbook_text)
    _write(os.path.join(pack_dir, "PACK.json"),
           json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    return manifest


def _write(path: str, text: str) -> str:
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return path


# ----------------------------------------------------------------------- load

class Pack:
    """A loaded carrypack.  Read-only; every path it exposes is inside itself."""

    def __init__(self, pack_dir: str):
        self.dir = os.path.abspath(pack_dir)
        with open(os.path.join(self.dir, "PACK.json"), encoding="utf-8") as handle:
            self.manifest: Dict[str, object] = json.load(handle)
        if self.manifest.get("format") != FORMAT:
            raise PackError("not a %s: %r" % (FORMAT, self.manifest.get("format")))

    # -- the books ------------------------------------------------------
    @property
    def domain_path(self) -> str:
        return os.path.join(self.dir, self.manifest["books"]["domain"]["file"])

    @property
    def playbook_path(self) -> str:
        return os.path.join(self.dir, self.manifest["books"]["playbook"]["file"])

    @property
    def requires(self) -> Dict[str, object]:
        return self.manifest["requires"]

    @property
    def pack_id(self) -> str:
        return str(self.manifest["pack_id"])

    # -- the two checks --------------------------------------------------
    def check_books(self) -> Dict[str, object]:
        """The books on disk against the hashes the manifest recorded.

        A pack whose `domain.dsl` was edited after the manifest was written is
        not the pack that was validated, and this is the only thing standing
        between "carrying a domain" and "carrying a filename".
        """
        rows = {}
        for key in ("domain", "playbook"):
            entry = self.manifest["books"][key]
            path = os.path.join(self.dir, entry["file"])
            actual = sha256_file(path) if os.path.exists(path) else "missing"
            rows[key] = {"recorded": entry["sha256"], "actual": actual,
                         "match": actual == entry["sha256"]}
        return {"match": all(r["match"] for r in rows.values()), "books": rows}

    def check_fingerprint(self, repo: str = REPO) -> Dict[str, object]:
        return compare_fingerprint(self.manifest["fingerprint"], fingerprint(repo))
