"""The handover package — a manual made readable by someone who was never here.

Theoria.md 1.8 gives the manual three readers: a human reads the natural-language
rendering, a machine reads the Lean, and **a fresh agent reads the source itself**.
1.11 turns that third reader into a measurement — the layered handover test, two
tiers, manual only or manual plus playbook.

The exam track can already mark such a reader.  What did not exist is the thing
being handed *over*: a directory that a fresh reader can be given in place of the
repository.  This module builds it.

--------------------------------------------------------------------------
What a package is, and the one rule that shapes it
--------------------------------------------------------------------------

**The reader has no repository.**  Everything that decides an answer is copied
in, never referenced by path.  That single rule produces most of the layout:

    README.md              the door: what this is and what to read first
    GLOSSARY.md            every name in the package, and where it comes from
    SEAL.md                what was scanned for, what was found, what it means
    MANIFEST.json          sha256 of every file, provenance, per-form status
    manual/
      MANUAL.dsl           the author's source, byte for byte (LF-normalised)
      MANUAL.md            deterministic English rendering — no model in the path
      PRIMITIVES.md        the words the rules are built from but do not define
      DOMAIN.pddl          the planning form of the manual alone
    playbook/              (tier `manual+playbook` only)
      PLAYBOOK.dsl         the author's source
      PLAYBOOK.md          deterministic English rendering
    levels/<level_id>/
      LEVEL.json           this board, as data
      BOARD.md             this board, drawn
      predictor.py         the executable form, grounded on this board
      Level.lean           the proof form, grounded on this board
      problem.pddl         the planning form, grounded on this board

**Two boards, not one.**  Three of the four co-derived forms are grounded — the
executable, the Lean and the PDDL problem all need a board — so a package that
carried one board would let a reader mistake that board's furniture for a law of
the world.  Carrying two makes the domain/problem split *visible*: what differs
between `levels/a/` and `levels/b/` is supplied by the board, and what is
identical in `manual/` is fixed by the world.  `GLOSSARY.md` states that
comparison as a table, computed rather than asserted.

**No session context.**  `context_report()` scans every content file for the
four ways a session leaks into a deliverable — a path out of the bundle, a run
id, the name of an artefact that is not here, and conversational deixis.  A hit
in normative text is `blocking` and the build refuses.  A hit inside a source
comment is a `citation`: the author's adjudication trail, which costs the reader
nothing so long as no clause *depends* on it, and which is not edited out
because a package that quietly rewrote the deliverable would be handing over a
document nobody shipped.  Both counts land in `SEAL.md` and `MANIFEST.json`.

--------------------------------------------------------------------------
What this module refuses to do
--------------------------------------------------------------------------

*It will not invent a form it cannot derive.*  A form that fails to generate is
recorded in `MANIFEST.json` under `forms` with the generator's own refusal
message, and `README.md` says which forms the reader did and did not get.  A
package silently missing its Lean would be scored as a reader's failure.

*It will not ship a fabricated board.*  `gen_pddl` used to place every object on
`cell-0-0` and ignore walls when no `ProblemSpec` was passed; this module always
passes one, and refuses to write `problem.pddl` at all if it cannot.  A false
board in a handover package is worse than a missing one: the reader cannot tell.

*It will not paraphrase.*  Every English sentence in a package comes from a
lookup table keyed by an exact DSL construct.  A construct with no entry raises
`UnrenderableClause`.  This is `gen_markdown`'s discipline and `gen_exec`'s, for
the same reason: a rendering that quietly dropped a guard would hand the reader a
weaker world, and the handover score would measure the drop instead of the
document.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .parser.theory_parser import parse_theory
from .parser.playbook_parser import parse_playbook
from .problem import ProblemSpec, from_json, check_against_theory
from .generators.gen_markdown import generate_markdown
from .generators.gen_python import generate_python
from .generators.gen_pddl import generate_pddl
from .generators.gen_lean import generate_lean

PACKAGE_FORMAT = "theoria-handover/1"

TIER_MANUAL = "manual"
TIER_MANUAL_PLAYBOOK = "manual+playbook"
TIERS = (TIER_MANUAL, TIER_MANUAL_PLAYBOOK)

#: Written by the builder itself.  `MANIFEST.json` records where the sources came
#: from in the producing repository, and `SEAL.md` quotes what the scan found; a
#: scan that read its own report would report itself.  Both exclusions are stated
#: in `SEAL.md` so a reader is never told the package was scanned more thoroughly
#: than it was.
SCAN_EXCLUDE = ("MANIFEST.json", "SEAL.md")


class HandoverError(RuntimeError):
    """The package cannot be built as specified."""


class UnrenderableClause(HandoverError):
    """A construct this module has no English for.  Never rendered as silence."""


class ContextLeak(HandoverError):
    """A file in the package depends on something outside the package."""


# =========================================================================
# inputs
# =========================================================================

@dataclass(frozen=True)
class LevelInput:
    """One board to ground the grounded forms on.

    `source` is provenance only — it is recorded in `MANIFEST.json` and reaches
    no file the reader is asked to reason from.
    """

    level_id: str
    doc: Dict[str, Any]
    source: str = ""

    def spec(self) -> ProblemSpec:
        return from_json(json.loads(json.dumps(self.doc)), default_name=self.level_id)


@dataclass(frozen=True)
class PackageSpec:
    world_id: str
    title: str
    manual_dsl: str
    levels: Tuple[LevelInput, ...]
    playbook_dsl: Optional[str] = None
    #: Free-form provenance recorded in `MANIFEST.json` and nowhere else.
    provenance: Dict[str, Any] = field(default_factory=dict)

    @property
    def tier(self) -> str:
        return TIER_MANUAL_PLAYBOOK if self.playbook_dsl else TIER_MANUAL

    def check(self) -> None:
        if not self.levels:
            raise HandoverError(
                "a package needs at least one board: the executable, Lean and "
                "PDDL-problem forms are all grounded and cannot be emitted "
                "without one")
        if len(self.levels) < 2:
            raise HandoverError(
                "a package needs at least two boards. With one, a reader cannot "
                "tell which of the names in it are the world's and which are the "
                "board's — and that distinction is half of what a manual is for")
        ids = [lv.level_id for lv in self.levels]
        if len(set(ids)) != len(ids):
            raise HandoverError("level ids must be unique; got %r" % (sorted(ids),))


# =========================================================================
# the words the rules are built from
# =========================================================================

#: Every primitive the DSL supplies, with the definition the *compiler* gives it.
#: Each entry is the behaviour of the corresponding helper in `gen_python`, in
#: words.  A manual that calls something not in this table raises: the reader
#: would otherwise be handed a guard whose central word is undefined, and would
#: correctly fail the item.
_PRIMITIVES: Dict[str, Tuple[str, str]] = {
    "free": (
        "free(c)",
        "the cell `c` is on the board, the board's own colour there is the "
        "background colour, and no object is standing on it. Written "
        "`free(X.pos)` — asking whether an object's *own* cell is a legal empty "
        "one — it excludes that object from the test and asks about the board "
        "and every *other* object."),
    "ahead": (
        "ahead(X, d)",
        "the cell one step from `X`'s cell in direction `d`."),
    "beyond": (
        "beyond(X, d)",
        "the cell two steps from `X`'s cell in direction `d`."),
    "above": ("above(X)", "the cell one step up from `X`'s cell."),
    "below": ("below(X)", "the cell one step down from `X`'s cell."),
    "leftof": ("leftof(X)", "the cell one step left from `X`'s cell."),
    "rightof": ("rightof(X)", "the cell one step right from `X`'s cell."),
    "colored": (
        "colored(c, k)",
        "the colour showing at cell `c` — the board's colour there, or the "
        "colour of whatever object is standing on it — is exactly `k`."),
    "count": (
        "count(T)  /  count(T, k)",
        "how many objects of type `T` are present; with a second argument, how "
        "many of them have colour `k`."),
    "adjacent": (
        "adjacent(a, b)",
        "cells `a` and `b` differ by exactly one step along one axis."),
}

#: Structural words that are part of the sentence, not functions of the world.
_SYNTAX_NOTES: Tuple[Tuple[str, str], ...] = (
    ("`act=<action>`",
     "the guard clause that matches the action being taken. A rule whose guard "
     "does not name the action applies whatever the action is."),
    ("`not <clause>`", "the clause does not hold."),
    ("`<a> and <b>`",
     "both hold. A guard is a conjunction and nothing else; \"either of two "
     "things is blocked\" is written as two rules, not as one guard."),
    ("`X.pos`", "the cell object `X` is standing on."),
    ("`X.pos.row` / `X.pos.col`",
     "the row and the column of that cell. Row 0 is the top row, column 0 the "
     "left column."),
    ("`forall ?v in <domain>`",
     "the rule is a schema: one rule per member of the named domain, with `?v` "
     "replaced throughout."),
    ("`mod`", "remainder after division, never negative."),
)

#: What each event *does*, keyed by (name, number of parameters).
#:
#: This is the single most load-bearing table in the module, because the manual
#: does not contain this information.  A manual declares `slid(o, p, dir)` in its
#: `events:` section and never says how far a slide goes; the distance lives in
#: the compiler's event vocabulary (`gen_python._effect`), which is closed and
#: the same for every manual of every world.  A handover package that shipped
#: the declaration without the meaning would be asking its reader to guess the
#: one number that decides every step-semantics question — so the meanings are
#: transcribed here from the effect each key compiles to, and a declared event
#: with no entry raises rather than shipping as a name with no content.
#:
#: That the meanings have to be transcribed at all is a limit of the DSL, not a
#: convenience of this module: as of v0.3 the manual has no syntax for stating
#: what its own events do.
_EVENT_SEMANTICS: Dict[Tuple[str, int], str] = {
    ("moved", 2):
        "`moved(o, d)` — object `o` moves **one** cell in direction `d`. "
        "Nothing else changes.",
    ("slid", 3):
        "`slid(o, p, d)` — object `o` travels **two** cells in direction `d`, "
        "and object `p` (the one doing the pushing) advances **one** cell in "
        "`d`, onto the cell `o` has just left. Both motions are one event and "
        "happen together.",
    ("stayed", 1):
        "`stayed(o)` — nothing moves and nothing changes. The situation after "
        "the action is identical to the situation before it.",
    ("jumped", 2):
        "`jumped(o, dest)` — object `o` is placed on the cell the landmark "
        "`dest` names. It does not travel through the cells in between; where "
        "that cell is, is supplied by the level.",
    ("teleported", 2):
        "`teleported(o, dest)` — object `o` is placed on the cell the landmark "
        "`dest` names. Same effect as `jumped(o, dest)`; which word a manual "
        "uses is the manual's business.",
    ("jumped", 3):
        "`jumped(o, over, d)` — object `o` travels **two** cells in direction "
        "`d`, and the object `over` it passed is removed from play.",
    ("recolored", 2):
        "`recolored(o, k)` — object `o`'s colour becomes `k`. It does not move.",
    ("vanished", 1):
        "`vanished(o)` — object `o` stops being present. It is no longer drawn "
        "and no longer occupies its cell.",
    ("appeared", 1):
        "`appeared(o)` — object `o` starts being present, on the cell it "
        "already holds.",
    ("removed", 1):
        "`removed(o)` — object `o` is taken out of play.",
}

_CELL_NOTE = (
    "A **cell** is written `(row, col)`. Row 0 is the top row and column 0 the "
    "left column. A **direction** moves one cell: `up` subtracts one from the "
    "row, `down` adds one, `left` subtracts one from the column, `right` adds "
    "one.")


# =========================================================================
# walking an AST without importing its whole node zoo
# =========================================================================

def _children(node: Any) -> Iterable[Any]:
    if isinstance(node, (list, tuple, set, frozenset)):
        return list(node)
    fields = getattr(node, "__dataclass_fields__", None)
    if fields:
        return [getattr(node, name) for name in fields]
    return []


def _walk(node: Any) -> Iterable[Any]:
    """Every node in an AST, by dataclass reflection.

    Reflection rather than an import list of node classes: this module then does
    not have to be edited every time the grammar grows a construct, and a new
    construct that uses an undefined primitive still trips `_primitives_used`.
    """
    stack = [node]
    while stack:
        current = stack.pop()
        if current is None or isinstance(current, (str, int, float, bool)):
            continue
        yield current
        stack.extend(_children(current))


def _event_alternatives(ast: Any) -> List[Any]:
    """Every `EventAlt` the manual declares, flattened out of its `EventDecl`s."""
    out: List[Any] = []
    events = getattr(ast, "events", None)
    for decl in (getattr(events, "events", []) or []) if events else []:
        out.extend(getattr(decl, "alternatives", []) or [])
    return out


def _declared_names(ast: Any) -> set:
    """Names this manual defines for itself.

    An event application `moved(Cart, up)` parses to the same node shape as a
    call to `free(...)`, and the difference is not in the syntax: `moved` is a
    word *this* manual coined in its `events:` section and `free` is a word the
    language supplies. Subtracting the declared names is what keeps a manual's
    own vocabulary out of the primitive table — and, in the other direction,
    keeps an undeclared word from being quietly accepted as one.
    """
    names = {alt.name for alt in _event_alternatives(ast)}
    rules = getattr(ast, "rules", None)
    for rule in (getattr(rules, "rules", []) or []) if rules else []:
        names.add(rule.name)
    return names


_CALL_IN_TEXT = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(")


def _primitives_used(ast: Any) -> List[str]:
    """Every language primitive this manual leans on.

    Two sources, because the parser keeps two representations.  Guards and
    events are parsed into `FuncCall` nodes.  An invariant is kept as the text
    the author wrote (`InvariantDecl.expr_text`), so `count(Cart) = 1` never
    becomes a node — and a primitives page assembled from nodes alone would omit
    `count` while the laws section goes on using it.
    """
    declared = _declared_names(ast)
    names = set()
    for node in _walk(ast):
        if type(node).__name__ == "FuncCall":
            name = getattr(node, "name", None)
            if isinstance(name, str) and name not in declared:
                names.add(name)
    laws = getattr(ast, "laws", None)
    for inv in (getattr(laws, "invariants", []) or []) if laws else []:
        for name in _CALL_IN_TEXT.findall(getattr(inv, "expr_text", "") or ""):
            if name not in declared:
                names.add(name)
    return sorted(names)


def _board_resolved_names(ast: Any, specs: Sequence[ProblemSpec]) -> List[str]:
    """Names the manual uses whose value only a board can supply.

    A manual that writes `jumped(Cart, portal_exit)` is naming a cell it does not
    locate.  Whether the manual *declared* it as a landmark or left it as a bare
    free name changes nothing about the world and everything about whether a
    reader of the manual alone can tell it is level data — which is why this is
    computed against the boards rather than against the declaration.
    """
    supplied = set()
    for spec in specs:
        supplied.update(spec.landmarks)
    used = set()
    for node in _walk(ast):
        if type(node).__name__ == "NameRef":
            name = getattr(node, "name", None)
            if isinstance(name, str) and name in supplied:
                used.add(name)
    return sorted(used)


# =========================================================================
# rendering: primitives, the playbook, a board
# =========================================================================

def render_primitives(ast: Any) -> str:
    """The primitives this manual actually uses, defined.

    Only the ones used: a package that listed the whole language would be
    teaching the reader constructs the manual never exercises, and the extra
    text is a place for a wrong guess to hide.
    """
    used = _primitives_used(ast)
    missing = [n for n in used if n not in _PRIMITIVES]
    if missing:
        raise UnrenderableClause(
            "the manual calls %s, and this module has no definition for %s. A "
            "package that shipped an undefined primitive would hand the reader "
            "a guard whose central word means nothing."
            % (", ".join(used), ", ".join(missing)))

    lines = ["# The words the rules are built from", "",
             "These are the primitives the manual's rules use. The manual does "
             "not restate them; they are fixed by the language the manual is "
             "written in, and they mean the same thing in every manual.", "",
             _CELL_NOTE, "", "## Functions and predicates", ""]
    for name in used:
        signature, definition = _PRIMITIVES[name]
        lines.append("- **`%s`** — %s" % (signature, definition))

    alternatives = _event_alternatives(ast)
    if alternatives:
        missing_events = [
            "%s/%d" % (alt.name, len(getattr(alt, "params", []) or []))
            for alt in alternatives
            if (alt.name, len(getattr(alt, "params", []) or []))
            not in _EVENT_SEMANTICS]
        if missing_events:
            raise UnrenderableClause(
                "the manual declares the event(s) %s and this module has no "
                "statement of what they do. The manual does not say either — "
                "an `events:` declaration is a name and an arity — so a package "
                "shipping them would be handing the reader a rule whose "
                "consequence is nowhere written down."
                % ", ".join(missing_events))
        lines += ["", "## What each event does", "",
                  "The manual's `events:` section declares the names below and "
                  "their arguments. What each one *does* is fixed by the "
                  "language, the same in every manual, and is stated here "
                  "because it is stated nowhere in the manual.", ""]
        for alt in alternatives:
            key = (alt.name, len(getattr(alt, "params", []) or []))
            lines.append("- %s" % _EVENT_SEMANTICS[key])

    lines += ["", "## Sentence shape", ""]
    for token, note in _SYNTAX_NOTES:
        lines.append("- %s — %s" % (token, note))
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


#: The four sentence forms of the playbook grammar (constraint 10), keyed by the
#: AST class the parser produces.  Dispatching on the class rather than on a
#: string field means a form the grammar grows and this table has not learned
#: raises instead of rendering as silence.
_PLAYBOOK_FORMS: Dict[str, Tuple[str, str]] = {
    "OrderStmt": (
        "Ordering",
        "Do this before that. An ordering changes how fast an answer is found "
        "and never which answers are correct."),
    "PruneStmt": (
        "Pruning",
        "A search node matching this is dead: nothing reachable from it wins. "
        "Cutting it changes nothing about which boards are winnable — it only "
        "stops work that could not have paid."),
    "HeuristicStmt": (
        "Heuristic",
        "An estimate of how much work is left, used to steer the search. "
        "`admissible` says whether it is proved never to over-estimate; "
        "`none` means it is not, so it may mislead."),
    "PreferStmt": (
        "Preference",
        "An empirical habit, carrying the measurement that justifies it. No "
        "proof — the tag says so."),
}


def _playbook_sentence(stmt: Any) -> Tuple[str, str]:
    """(form, the sentence) for one playbook statement, verbatim in its own terms."""
    kind = type(stmt).__name__
    if kind not in _PLAYBOOK_FORMS:
        raise UnrenderableClause(
            "no rendering for the playbook sentence form %r; the four forms are "
            "%s" % (kind, ", ".join(sorted(_PLAYBOOK_FORMS))))
    if kind == "OrderStmt":
        return kind, "order %s" % stmt.landmark
    if kind == "PruneStmt":
        return kind, "prune %s => dead" % " ".join(str(stmt.condition).split())
    if kind == "HeuristicStmt":
        return kind, "heuristic %s(%s)" % (stmt.name,
                                           ", ".join(stmt.params or []))
    return kind, "prefer %s" % " ".join(
        str(getattr(stmt, "body", getattr(stmt, "name", stmt))).split())


def _playbook_tags(stmt: Any) -> str:
    parts = []
    for attr in ("proof", "admissible", "winrate", "nodes", "evidence"):
        value = getattr(stmt, attr, None)
        if value not in (None, "", []):
            parts.append("%s: %s" % (attr, value))
    return ", ".join(parts)


def render_playbook(playbook_ast: Any, playbook_dsl: str) -> str:
    """playbook.dsl -> English, by table lookup over the four sentence forms.

    The forms are the whole grammar (constraint 10): ordering, pruning,
    heuristics, preferences.  There is no sentence form for a solution, so a
    playbook cannot contain one, and this renderer has nowhere to put one even
    if a file tried.
    """
    statements = list(getattr(playbook_ast, "statements", []) or [])
    lines = ["# The playbook for this world", "",
             "The manual says what the world does. This says how to win in it — "
             "and, more usefully, how to avoid work.", "",
             "Nothing here is a solution to any board. The playbook's grammar "
             "has four sentence forms — ordering, pruning, heuristics, "
             "preferences — and no form for a sequence of actions. A solution "
             "is a planner's output, not a book's content.", "",
             "Every entry is written in the manual's vocabulary and answers to "
             "the manual, not to the world: change the clause an entry rests on "
             "and the entry is void.", ""]

    if not statements:
        lines += ["This playbook is empty.", ""]
        return "\n".join(lines).rstrip() + "\n"

    by_form: Dict[str, List[Any]] = {}
    for stmt in statements:
        kind, _sentence = _playbook_sentence(stmt)
        by_form.setdefault(kind, []).append(stmt)

    for kind in sorted(by_form):
        heading, gloss = _PLAYBOOK_FORMS[kind]
        lines += ["## %s" % heading, "", gloss, ""]
        for stmt in by_form[kind]:
            _kind, sentence = _playbook_sentence(stmt)
            tags = _playbook_tags(stmt)
            lines.append("- `%s`%s" % (sentence, (" — %s" % tags) if tags else ""))
        lines.append("")

    absent = [_PLAYBOOK_FORMS[k][0] for k in sorted(_PLAYBOOK_FORMS)
              if k not in by_form]
    lines += ["## What is not in here", ""]
    if absent:
        lines += ["This playbook has no entry of these forms: %s."
                  % ", ".join(absent), ""]
    lines += ["A `prefer` entry must carry a win rate or a node count, because "
              "the grammar requires one. An empty empirical tier means nobody "
              "measured, not that nothing works.", "",
              "`playbook/PLAYBOOK.dsl` is the source these sentences were read "
              "from, comments and all.", ""]
    return "\n".join(lines).rstrip() + "\n"


_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _playbook_names(playbook_ast: Any) -> List[str]:
    """Every identifier the playbook's *sentences* use.

    Comments are not read: the parser has already dropped them, which is what
    makes this a statement about what the playbook says rather than about what
    its author wrote in the margin.
    """
    names = set()
    for stmt in getattr(playbook_ast, "statements", []) or []:
        _kind, sentence = _playbook_sentence(stmt)
        names.update(_IDENTIFIER.findall(sentence))
    return sorted(names)


BOARD_LEGEND = (
    "`.` is a cell holding the background colour. A digit is the board's own "
    "colour at that cell — the board never changes it. A capital letter is the "
    "first letter of an object's name, drawn where that object starts; where two "
    "objects would share a cell the alphabetically earlier name is drawn. `*` "
    "marks a cell a landmark names, drawn only where nothing else is. Row 0 is "
    "the top row and column 0 the left column.")


def render_board(level: LevelInput, spec: ProblemSpec) -> str:
    """One board, drawn and tabulated.

    The tables are authoritative and the drawing is a convenience: an ambiguous
    picture would turn a question about the world into a question about ASCII.
    """
    lines = ["# Board `%s`" % level.level_id, "",
             "One of the boards this world is played on. Everything on this page "
             "is supplied by *this board*; nothing on it is a law of the world. "
             "Compare it with the other board in `levels/` to see which is "
             "which.", ""]

    if spec.height is None or spec.width is None:
        lines += ["This board is not a grid; `LEVEL.json` is its whole "
                  "description.", ""]
        return "\n".join(lines).rstrip() + "\n"

    letters: Dict[Tuple[int, ...], str] = {}
    for inst in sorted(spec.instances, key=lambda i: i.name):
        if inst.present and tuple(inst.pos) not in letters:
            letters[tuple(inst.pos)] = inst.name[0].upper()
    landmark_cells = {tuple(cell) for cell in spec.landmarks.values()}

    lines += ["## The board", "", "```"]
    header = "    " + "".join(str(c % 10) for c in range(spec.width))
    lines.append(header)
    for r in range(spec.height):
        row = []
        for c in range(spec.width):
            cell = (r, c)
            colour = spec.board[r][c] if r < len(spec.board) and c < len(spec.board[r]) else spec.background
            if cell in letters:
                row.append(letters[cell])
            elif colour != spec.background:
                row.append(str(colour) if 0 <= colour <= 9 else "?")
            elif cell in landmark_cells:
                row.append("*")
            else:
                row.append(".")
        lines.append("%3d %s" % (r, "".join(row)))
    lines += ["```", "", BOARD_LEGEND, "",
              "Size: %d rows by %d columns. Background colour: %d."
              % (spec.height, spec.width, spec.background), ""]

    lines += ["## Where things start", "", "| object | type | cell | colour | present |",
              "|---|---|---|---|---|"]
    for inst in sorted(spec.instances, key=lambda i: i.name):
        lines.append("| `%s` | `%s` | %s | %s | %s |"
                     % (inst.name, inst.type, _cell_text(inst.pos),
                        "—" if inst.color is None else inst.color,
                        "yes" if inst.present else "no"))
    lines.append("")

    if spec.landmarks:
        lines += ["## What this board's landmarks name", "",
                  "| landmark | cell |", "|---|---|"]
        for name in sorted(spec.landmarks):
            lines.append("| `%s` | %s |" % (name, _cell_text(spec.landmarks[name])))
        lines.append("")
    else:
        lines += ["## Landmarks", "",
                  "This board locates no landmark.", ""]

    coincidences = [(name, inst.name)
                    for name, cell in sorted(spec.landmarks.items())
                    for inst in sorted(spec.instances, key=lambda i: i.name)
                    if inst.present and tuple(inst.pos) == tuple(cell)]
    if coincidences:
        lines += ["## Something already true on this board", "",
                  "An object starts on a cell a landmark names. Depending on "
                  "the manual's goal clause this board may already be won "
                  "before any action is taken — check the clause; this page "
                  "only reports the coincidence.", ""]
        for landmark, obj in coincidences:
            lines.append("- `%s` starts on the cell `%s` names."
                         % (obj, landmark))
        lines.append("")

    lines += ["## Goal cell", ""]
    if spec.goal_cell is not None:
        lines += ["This board's `goal_cell` field is %s. Whether the manual's "
                  "goal clause consults it is a question for the manual: a "
                  "manual whose goal clause writes a coordinate outright "
                  "ignores this field entirely."
                  % _cell_text(spec.goal_cell), ""]
    else:
        lines += ["This board supplies no `goal_cell`. That does not mean the "
                  "board has no goal — if the manual's goal clause names a "
                  "landmark or writes a coordinate outright, the goal comes "
                  "from there.", ""]
    if spec.weights:
        lines += ["## Weight vectors this board supplies", ""]
        for name in sorted(spec.weights):
            lines.append("- `%s` = %s" % (name, spec.weights[name]))
        lines.append("")
    lines += ["## Cells in play", "",
              "This board's `LEVEL.json` carries an `arena` list of %d cells. "
              "It is the board's own note of which cells are worth considering "
              "and **no rule of the manual consults it** — whether a cell can "
              "be stood on is decided by `free`, whose definition is in "
              "`manual/PRIMITIVES.md`. Treat `arena` as a convenience, not as "
              "law." % len(spec.arena), ""]
    return "\n".join(lines).rstrip() + "\n"


def _cell_text(cell: Optional[Sequence[int]]) -> str:
    if cell is None:
        return "—"
    return "(%s)" % ", ".join(str(int(v)) for v in cell)


# =========================================================================
# the glossary: every name, and where it comes from
# =========================================================================

WORLD_LAW = "world_law"
LEVEL_DATA = "level_data"
PRIMITIVE = "primitive"


def _level_observables(spec: ProblemSpec) -> Dict[str, str]:
    """What one board says, name by name, in a form two boards can be compared in."""
    out: Dict[str, str] = {
        "board_shape": "%s x %s" % (spec.height, spec.width),
        "background_colour": str(spec.background),
        "non_background_cells": str(sum(
            1 for row in spec.board for v in row if v != spec.background)),
        "arena": "%d cells" % len(spec.arena),
        "goal_cell (the board's field, which the manual's goal clause may "
        "not consult)": _cell_text(spec.goal_cell),
    }
    for name in sorted(spec.landmarks):
        out["landmark %s" % name] = _cell_text(spec.landmarks[name])
    for inst in sorted(spec.instances, key=lambda i: i.name):
        out["%s start cell" % inst.name] = _cell_text(inst.pos)
        if inst.color is not None:
            out["%s colour" % inst.name] = str(inst.color)
    for name in sorted(spec.weights):
        out["weights %s" % name] = str(spec.weights[name])
    return out


_NUMBER_IN_CLAUSE = re.compile(r"-?\d+")


def _level_constants_in_manual(manual_dsl: str) -> List[Tuple[str, str]]:
    """Numbers written into the manual's goal and laws.

    A conservation law is a fact about the world; the constant it is compared
    against is usually a fact about one board.  `a0-spike`'s manual writes
    `(Box.pos.row) mod 2 = 1`, and on a board whose Box starts on an even row
    that sentence is false as written.  This does not repair the manual — it
    surfaces the constants so a reader can see which ones are load-bearing, and
    so the defect is measured rather than tripped over.
    """
    found: List[Tuple[str, str]] = []
    for raw in manual_dsl.replace("\r\n", "\n").split("\n"):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        head = line.split(None, 1)[0]
        if head not in ("goal", "invariant"):
            continue
        if _NUMBER_IN_CLAUSE.search(line):
            found.append((head, " ".join(line.split())))
    return found


def render_glossary(ast: Any, manual_dsl: str, levels: Sequence[LevelInput],
                    specs: Sequence[ProblemSpec],
                    playbook_ast: Any = None) -> str:
    """Every name in the package, classified by where it comes from.

    The classification is *derived*, not declared.  A name the manual fixes is
    world law because it is in the manual; a name a board supplies is level data
    because it is in a board; and for level data the table prints the value on
    each board, so the claim "this varies" is evidence a reader can check rather
    than a label they have to trust.
    """
    wt = getattr(ast, "word_table", None)
    lines = ["# Glossary — every name in this package, and where it comes from",
             "",
             "Names in this world come from exactly three places. A name the "
             "**manual** fixes is the same on every board. A name a **board** "
             "supplies changes from board to board. A **primitive** belongs to "
             "the language the manual is written in and means the same in every "
             "manual of every world.", "",
             "The tables below are computed from the files in this package.",
             ""]

    # ---- world law -------------------------------------------------------
    lines += ["## Fixed by the world (from `manual/MANUAL.dsl`)", "",
              "| name | kind | what it is |", "|---|---|---|"]
    rows: List[Tuple[str, str, str]] = []
    if wt is not None:
        for obj in getattr(wt, "objects", []) or []:
            props = ", ".join("`%s`" % _prop_name(p)
                              for p in getattr(obj, "fields", []) or [])
            rows.append(("`%s`" % obj.name, "object type",
                         "a kind of thing the world contains; its observed "
                         "properties are %s" % (props or "none")))
            for prop in getattr(obj, "fields", []) or []:
                rows.append(("`%s.%s`" % (obj.name, _prop_name(prop)),
                             "property",
                             "an observation of type `%s` carried by every `%s`"
                             % (getattr(prop, "type", "?"), obj.name)))
        for dom in getattr(wt, "domains", []) or []:
            members = ", ".join("`%s`" % m for m in getattr(dom, "values", []) or [])
            rows.append(("`%s`" % dom.name, "domain",
                         "a fixed finite set of values: %s" % (members or "—")))
        for lm in getattr(wt, "landmarks", []) or []:
            rows.append(("`%s`" % lm.name, "landmark name",
                         "the world names it; **each board says which cell it "
                         "is** — see the level-data table"))
    sem = getattr(ast, "semantics", None)
    if sem is not None:
        for fname, gloss in (
                ("frame", "what happens to an object no firing rule mentions"),
                ("conflict", "how many rules may claim one object in one "
                             "transition"),
                ("cascade", "whether one action produces one frame or several")):
            value = getattr(sem, fname, None)
            if value:
                rows.append(("`%s %s`" % (fname, value), "semantics", gloss))
    for alt in _event_alternatives(ast):
        params = ", ".join(getattr(alt, "params", []) or [])
        writes = getattr(alt, "writes", None)
        rows.append(("`%s(%s)`" % (alt.name, params), "event",
                     "a kind of change the world can undergo"
                     + ("; it writes %s"
                        % (", ".join("`%s`" % w for w in writes) if writes
                           else "nothing")
                        if writes is not None else "")))
    rules = getattr(ast, "rules", None)
    for rule in (getattr(rules, "rules", []) or []) if rules else []:
        rows.append(("`%s`" % rule.name, "rule",
                     "one sentence of the form *when … then …*; see "
                     "`manual/MANUAL.md`"))
    laws = getattr(ast, "laws", None)
    if laws is not None:
        for inv in getattr(laws, "invariants", []) or []:
            rows.append(("`%s`" % inv.name, "invariant",
                         "something the manual says is true before the first "
                         "action and after every action"))
        for thm in getattr(laws, "theorems", []) or []:
            rows.append(("`%s`" % thm.name, "theorem",
                         "a consequence the manual states and cites its "
                         "evidence for"))
    if getattr(ast, "goal", None) is not None:
        rows.append(("the goal clause", "goal",
                     "what winning is; the *shape* is fixed by the world, and "
                     "any coordinate written into it is not — see the last "
                     "section"))
    for name, kind, what in rows:
        lines.append("| %s | %s | %s |" % (name, kind, what))
    lines.append("")

    # ---- level data ------------------------------------------------------
    observables = [_level_observables(s) for s in specs]
    keys = sorted({k for o in observables for k in o})
    lines += ["## Supplied by each board (from `levels/*/LEVEL.json`)", "",
              "Every row here is a name whose value this package can *show* you "
              "changing — or not — because the package carries more than one "
              "board. A row marked **differs** is level data on the evidence in "
              "this package. A row marked *same here* is level data by where it "
              "lives (a board supplies it) even though these particular boards "
              "happen to agree; two boards agreeing is not a law.", "",
              "| name | " + " | ".join("`%s`" % lv.level_id for lv in levels)
              + " | verdict |",
              "|---|" + "---|" * (len(levels) + 1)]
    for key in keys:
        values = [o.get(key, "—") for o in observables]
        verdict = "**differs**" if len(set(values)) > 1 else "*same here*"
        lines.append("| `%s` | %s | %s |" % (key, " | ".join(values), verdict))
    lines.append("")

    # ---- names the manual uses but no board-independent value exists for ---
    declared_landmarks = {lm.name for lm in (getattr(wt, "landmarks", []) or [])} \
        if wt is not None else set()
    bridge = _board_resolved_names(ast, specs)
    lines += ["## Names the manual uses that only a board can resolve", ""]
    if not bridge:
        lines += ["None. Every name the manual's clauses use is either defined "
                  "in the manual or a primitive of the language.", ""]
    else:
        lines += ["These names appear in the manual's own clauses, and the "
                  "manual does not say what they are: each board does. They are "
                  "the seam between the world and the board, and the value "
                  "column shows the seam.", "",
                  "| name | declared in the manual as a landmark? | "
                  + " | ".join("`%s`" % lv.level_id for lv in levels) + " |",
                  "|---|---|" + "---|" * len(levels)]
        for name in bridge:
            values = [_cell_text(s.landmarks.get(name)) for s in specs]
            lines.append("| `%s` | %s | %s |"
                         % (name,
                            "yes" if name in declared_landmarks
                            else "**no** — a reader of the manual alone cannot "
                                 "tell this is level data",
                            " | ".join(values)))
        lines.append("")

    # ---- primitives ------------------------------------------------------
    lines += ["## Fixed by the language (see `manual/PRIMITIVES.md`)", "",
              "| name | meaning |", "|---|---|"]
    for name in _primitives_used(ast):
        signature, definition = _PRIMITIVES[name]
        lines.append("| `%s` | %s |" % (signature, definition))
    lines.append("")

    # ---- constants inside the manual ------------------------------------
    constants = _level_constants_in_manual(manual_dsl)
    lines += ["## Numbers written into the manual", ""]
    if not constants:
        lines += ["The manual's goal clause and laws contain no numeric "
                  "constant.", ""]
    else:
        lines += ["These clauses of the manual contain a number. A law is a "
                  "fact about the world; a number it is compared against is "
                  "very often a fact about one board that has been written into "
                  "the manual by accident. This package does not repair them — "
                  "it points at them, because on a board where the number is "
                  "different the manual's sentence is false as written.", "",
                  "| section | clause |", "|---|---|"]
        for head, clause in constants:
            lines.append("| `%s` | `%s` |" % (head, clause))
        lines.append("")

    # ---- what the manual says it checked ---------------------------------
    laws = getattr(ast, "laws", None)
    claims = (list(getattr(laws, "invariants", []) or []) +
              list(getattr(laws, "theorems", []) or [])) if laws else []
    lines += ["## What the manual says it has checked", ""]
    if not claims:
        lines += ["The manual states no invariant and no theorem.", ""]
    else:
        lines += ["Each of these carries a tag saying how its author says it "
                  "was established. **A tag is a claim about evidence that is "
                  "not in this package.** Nothing here re-derives one, and a "
                  "reader should not treat `proven` or `passed` as checked.",
                  "",
                  "Where a claim can be tested against the two boards in "
                  "`levels/`, test it. A claim that speaks about how a board "
                  "starts — a parity, a distance, whether the goal is "
                  "reachable — is a claim about *some* board, and this package "
                  "carries two you can hold it against.", "",
                  "| clause | kind | what its author says |", "|---|---|---|"]
        for item in claims:
            tags = []
            for attr in ("status", "probe", "depends", "source"):
                value = getattr(item, attr, None)
                if value not in (None, "", []):
                    tags.append("%s: %s" % (attr, value))
            kind = ("invariant" if item in (getattr(laws, "invariants", []) or [])
                    else "theorem")
            lines.append("| `%s` | %s | %s |"
                         % (item.name, kind, ", ".join(tags) or "nothing"))
        lines.append("")

    if playbook_ast is not None:
        vocabulary = _manual_vocabulary(ast)
        unknown = [n for n in _playbook_names(playbook_ast)
                   if n not in vocabulary and n not in _PLAYBOOK_KEYWORDS]
        lines += ["## Names the playbook uses that the manual does not define",
                  ""]
        if not unknown:
            lines += ["None. Every name in the playbook's sentences is one the "
                      "manual defines, which is what lets a change to a manual "
                      "clause void a playbook entry.", ""]
        else:
            lines += ["A playbook answers to the manual. These names appear in "
                      "its sentences and in no declaration of the manual, so "
                      "nothing in this package says what they mean. Treat an "
                      "entry that rests on one as unverifiable from this "
                      "package rather than as a fact about the world.", "",
                      "| name |", "|---|"]
            for name in unknown:
                lines.append("| `%s` |" % name)
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


#: Words of the playbook grammar itself, not names of anything in the world.
_PLAYBOOK_KEYWORDS = frozenset({"order", "prune", "heuristic", "prefer", "dead",
                                "and", "or", "not", "true", "false"})


def _manual_vocabulary(ast: Any) -> set:
    """Every name the manual declares, plus the primitives it may lean on."""
    names = set(_declared_names(ast)) | set(_PRIMITIVES)
    wt = getattr(ast, "word_table", None)
    if wt is not None:
        for obj in getattr(wt, "objects", []) or []:
            names.add(obj.name)
            for prop in getattr(obj, "fields", []) or []:
                names.add(_prop_name(prop))
        for dom in getattr(wt, "domains", []) or []:
            names.add(dom.name)
            names.update(getattr(dom, "values", []) or [])
        for lm in getattr(wt, "landmarks", []) or []:
            names.add(lm.name)
        for decl in getattr(wt, "weights", []) or []:
            names.add(decl.name)
    laws = getattr(ast, "laws", None)
    if laws is not None:
        for item in list(getattr(laws, "invariants", []) or []) + \
                    list(getattr(laws, "theorems", []) or []):
            names.add(item.name)
    return names


def _prop_name(prop: Any) -> str:
    for attr in ("name", "field"):
        value = getattr(prop, attr, None)
        if isinstance(value, str):
            return value
    return str(prop)


# =========================================================================
# the context scan
# =========================================================================

_REPO_DIRS = ("a0-spike", "cold-start-a0", "cold-start-a2", "cold-start-a3",
              "theory-compiler", "engine-rig", "arc-recon", "exam", "monitor",
              "theoria-arm", "baseline-arms", "worldgen", "fuzzlab", "proxy",
              "CONTRACTS", "artifacts", "pipeline", "probes", "certify",
              "compile", "prime", "tools", "fixtures")

_SCAN_PATTERNS: Tuple[Tuple[str, "re.Pattern[str]"], ...] = (
    ("path_out_of_bundle",
     re.compile(r"(?:\.\./)|(?:\b(?:%s)/)" % "|".join(_REPO_DIRS))),
    ("run_id", re.compile(r"\b\d{8}T\d{6}Z\b")),
    ("artefact_not_here",
     re.compile(r"\b(?:THEORIZE_LOG|DECISIONS|PARTNER_SYNC|RUN_STATE|STATUS"
                r"|candidates\.jsonl|raw_trace|ledger\.jsonl|probes\.jsonl"
                r"|concept_accounts|dsl_grammar_v0\.\d)\b")),
    ("session_deixis",
     re.compile(r"(?:as (?:we|i) (?:discussed|said|agreed)"
                r"|earlier in (?:this|the) (?:session|conversation)"
                r"|上一轮|见上文|如前所述|前面提到)", re.I)),
)

#: A leak found inside a source comment is the author's adjudication trail.  It
#: costs the reader nothing so long as no *clause* depends on it, and the source
#: is handed over unedited on purpose — see the module docstring.
_COMMENT_PREFIX = {".dsl": "#", ".py": "#", ".pddl": ";", ".lean": "--"}


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    category: str
    severity: str       # "blocking" | "citation"
    text: str


def context_report(files: Dict[str, str]) -> List[Finding]:
    """Scan a package's content for the four ways a session leaks into it."""
    findings: List[Finding] = []
    for path in sorted(files):
        if path in SCAN_EXCLUDE:
            continue
        prefix = _COMMENT_PREFIX.get(os.path.splitext(path)[1])
        for lineno, line in enumerate(files[path].split("\n"), start=1):
            cut = line.find(prefix) if prefix else -1
            for category, pattern in _SCAN_PATTERNS:
                for match in pattern.finditer(line):
                    in_comment = cut != -1 and match.start() > cut
                    findings.append(Finding(
                        path=path, line=lineno, category=category,
                        severity="citation" if in_comment else "blocking",
                        text=line.strip()[:160]))
    return findings


def render_seal(findings: Sequence[Finding]) -> str:
    blocking = [f for f in findings if f.severity == "blocking"]
    citations = [f for f in findings if f.severity == "citation"]
    lines = ["# What this package was scanned for", "",
             "A handover package is supposed to be everything its reader gets. "
             "The build scans every file in it for the four ways a working "
             "session leaks into a document it produced:", "",
             "1. **a path out of the bundle** — a reference to a directory or "
             "file that is not here;",
             "2. **a run id** — a timestamp naming one execution nobody kept;",
             "3. **an artefact that is not here** — a log, a ledger, a status "
             "file;",
             "4. **conversational deixis** — \"as we discussed\", \"see above\".",
             "",
             "Those four and no more. It does **not** try to catch every prose "
             "mention of something that lives elsewhere: a generated file's "
             "own docstring may name the pipeline that produced it, and a "
             "source comment may name a component you do not have. Neither "
             "gives you a reference you need to follow — but do not read a "
             "clean scan as a promise that no sentence in here mentions "
             "anything outside it.", "",
             "Two files are excluded from the scan and it matters that you know "
             "which: `MANIFEST.json`, which records on purpose where these files "
             "came from in the repository that produced them, and `SEAL.md` — "
             "this file — which quotes what the scan found and would otherwise "
             "report itself. Nothing else is excluded.", "",
             "## Result", "",
             "- **blocking findings: %d.** A blocking finding is a hit in text "
             "that carries meaning — a rule, a law, a rendered sentence. The "
             "build refuses to write a package with any." % len(blocking),
             "- **citations: %d.** A citation is a hit inside a source comment: "
             "the author's record of *why* a clause was adjudicated the way it "
             "was. Those files are not here and you do not need them — no clause "
             "depends on one. The comments are handed over unedited because a "
             "package that rewrote the deliverable would be handing over a "
             "document nobody shipped." % len(citations), ""]
    if citations:
        lines += ["## The citations, in full", "",
                  "| file | line | kind |", "|---|---|---|"]
        for f in citations:
            lines.append("| `%s` | %d | %s |" % (f.path, f.line, f.category))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


# =========================================================================
# the front door
# =========================================================================

def render_readme(spec: PackageSpec, forms: Dict[str, Any],
                  levels: Sequence[LevelInput]) -> str:
    have = sorted(k for k, v in forms.items() if v.get("status") == "generated")
    missing = sorted(k for k, v in forms.items() if v.get("status") != "generated")
    lines = ["# %s" % spec.title, "",
             "This directory is a complete handover of one world's theory. It is "
             "everything you get: there is no repository behind it, no record of "
             "anyone playing this world, and no earlier conversation about it. "
             "If something is not in this directory, you do not know it.", "",
             "You have been given **%s**."
             % ("the manual and the playbook" if spec.tier == TIER_MANUAL_PLAYBOOK
                else "the manual only, and there is not supposed to be a "
                     "playbook here"),
             "", "## Read in this order", "",
             "1. `manual/MANUAL.md` — the manual in English. Mechanically "
             "rendered from `manual/MANUAL.dsl`; no model wrote a word of it.",
             "2. `manual/PRIMITIVES.md` — the handful of words the rules are "
             "built from. Short, and the rules are unreadable without it.",
             "3. `levels/` — two boards. Everything in there is supplied by a "
             "board; nothing in there is a law.",
             "4. `GLOSSARY.md` — every name in the package with where it comes "
             "from, and a table showing which names differ between the two "
             "boards.",
             ]
    if spec.tier == TIER_MANUAL_PLAYBOOK:
        lines.append("5. `playbook/PLAYBOOK.md` — how to win, and how to avoid "
                     "search. It answers to the manual, not to the world.")
    lines += ["", "`manual/MANUAL.dsl` is the manual as its author wrote it, "
              "byte for byte. Where the English rendering and the source seem to "
              "disagree, the source is the deliverable.", "",
              "## The forms", "",
              "One manual compiles to four co-derived forms — English, "
              "planning, executable, proof. The planning form comes in two "
              "files rather than one, because a planning task splits into a "
              "domain (the world) and a problem (the board), which is why the "
              "table below has five rows for four forms. Two of the rows are of "
              "the manual alone and three must be grounded on a board, which is "
              "why this package carries two boards.", "",
              "**What differs between the two boards is supplied by a board.** "
              "The converse does not hold and it matters: two boards agreeing "
              "is not a law, only a coincidence this package cannot see past. "
              "`GLOSSARY.md` marks the two cases apart rather than letting you "
              "run the inference backwards.", "",
              "| form | where | derived from | in this package? |",
              "|---|---|---|---|"]
    for label, where, derived, key in (
            ("English", "`manual/MANUAL.md`", "the manual alone", "english"),
            ("planning (domain)", "`manual/DOMAIN.pddl`", "the manual alone",
             "planning_domain"),
            ("executable", "`levels/<board>/predictor.py`",
             "the manual, on that board", "executable"),
            ("proof", "`levels/<board>/Level.lean`",
             "the manual, on that board", "proof"),
            ("planning (problem)", "`levels/<board>/problem.pddl`",
             "the manual, on that board", "planning_problem")):
        present = forms.get(key, {}).get("status") == "generated"
        lines.append("| %s | %s | %s | %s |"
                     % (label, where, derived,
                        "yes" if present else "**no — see below**"))
    lines.append("")
    if missing:
        lines += ["**Not every form is here.** The following could not be "
                  "derived from this manual, and the generator's own reason is "
                  "recorded in `MANIFEST.json` under `forms`:", ""]
        for key in missing:
            lines.append("- `%s` — %s" % (key, forms[key].get("why", "not generated")))
        lines += ["", "This is stated rather than hidden. A package quietly "
                  "missing a form would be read as the reader's failure to find "
                  "it.", ""]
    lines += ["## What is deliberately not here", "",
              "- **No worked example.** No file in this package steps a "
              "concrete board through a concrete action. Working one out is the "
              "point.",
              "- **No plan.** Not in the manual, and not in the playbook "
              "either — its grammar has no sentence form for a sequence of "
              "actions.",
              "- **No history.** No trace, no ledger, no record of how the "
              "manual was arrived at. Comments in the source cite that record; "
              "you neither have it nor need it. See `SEAL.md`.", "",
              "## Provenance", "",
              "`MANIFEST.json` carries a sha256 of every file here, and records "
              "which repository files these were copied or compiled from. That "
              "is metadata about how the package was made; you have no access to "
              "that repository and nothing in it is needed to read this one.", ""]
    lines += ["## Boards in this package", ""]
    for lv in levels:
        lines.append("- `levels/%s/`" % lv.level_id)
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


# =========================================================================
# build
# =========================================================================

def _canonical_json(doc: Any) -> str:
    return json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def check_pddl(domain: str, problem: str) -> None:
    """Refuse a PDDL pair that is not a well-formed planning task.

    The first fresh reader of the cart package found `manual/DOMAIN.pddl`
    unusable and `MANIFEST.json` calling it `generated`: two actions referred to
    a `?dest` that was in no parameter list, two had lost their preconditions
    entirely, the moving actions tested `adjacent-above` while the predicate
    block and the problem file both said `adjacent-up`, and three actions —
    the teleport, the button press, the door opening, which is the whole
    non-trivial content of that world — compiled to `(and (and))`. Had the
    reader treated the planning form as authoritative, every optimal-action
    answer would have been wrong, and the package would have scored that as the
    reader's failure.

    A form generated is not a form checked. A backend that cannot yet emit a
    sound encoding is a declared gap; one that emits an unsound encoding under a
    green status is a trap.

    The check is `strips.parse_domain` plus `strips.ground` — this track's own
    STRIPS front end, which already refuses an unbound variable, an undeclared
    predicate, a wrong arity and an empty effect, and which is the reader a
    planning form is actually for.  Nothing is re-implemented here; what is new
    is that the handover builder now *runs* it before calling a form generated.

    It refuses more than a planner would: negative preconditions are outside the
    subset it reads, so a domain using one is declared a gap rather than
    shipped.  That trade is deliberate. An over-refusal costs the reader a form
    and says so on the front page; an under-refusal costs them the answer and
    says nothing.
    """
    from . import strips

    _domain_name, _arities, _types, schemas = strips.parse_domain(domain)
    if not schemas:
        raise HandoverError("the domain declares no action at all")
    task = strips.ground(domain, problem)
    if not task.actions:
        raise HandoverError(
            "the domain and the board ground to no applicable action; the "
            "encoding and the level do not meet")


def _try(name: str, thunk) -> Tuple[Optional[str], Dict[str, Any]]:
    try:
        return thunk(), {"status": "generated"}
    except Exception as exc:                       # noqa: BLE001 -- recorded, not swallowed
        return None, {"status": "refused",
                      "why": "%s: %s" % (type(exc).__name__,
                                         " ".join(str(exc).split())[:400])}


def build_files(spec: PackageSpec) -> Tuple[Dict[str, str], Dict[str, Any]]:
    """Every file of the package, as text.  Deterministic: no clock, no RNG.

    Returns (files, manifest).  Writing is a separate step so that a caller can
    rebuild into memory and compare — which is what `tools/verify_c8.py` does to
    hold the byte-reproducibility requirement.
    """
    spec.check()
    manual_dsl = spec.manual_dsl.replace("\r\n", "\n")
    ast = parse_theory(manual_dsl)

    playbook_ast = None
    playbook_dsl = None
    if spec.playbook_dsl is not None:
        playbook_dsl = spec.playbook_dsl.replace("\r\n", "\n")
        playbook_ast = parse_playbook(playbook_dsl)

    files: Dict[str, str] = {}
    forms: Dict[str, Any] = {}
    warnings: List[str] = []

    files["manual/MANUAL.dsl"] = manual_dsl
    files["manual/PRIMITIVES.md"] = render_primitives(ast)

    text, status = _try("english", lambda: generate_markdown(ast))
    forms["english"] = status
    if text is not None:
        files["manual/MANUAL.md"] = text

    specs = []
    for level in spec.levels:
        problem = level.spec()
        warnings.extend("%s: %s" % (level.level_id, w)
                        for w in check_against_theory(problem, ast))
        specs.append(problem)

    # PDDL domain: of the manual alone, so it is generated once, from the first
    # board's geometry only to size the cell universe of the *problem* half.
    # Validated against that board before it is called generated -- see
    # `check_pddl`, and the reader report that made it necessary.
    def _domain() -> str:
        text, problem_text = generate_pddl(ast, specs[0].name,
                                           specs[0].width or 2,
                                           specs[0].height or 3,
                                           problem=specs[0])
        check_pddl(text, problem_text)
        return text

    domain, status = _try("planning_domain", _domain)
    forms["planning_domain"] = status
    if domain is not None:
        files["manual/DOMAIN.pddl"] = domain

    per_level_status: Dict[str, Dict[str, Any]] = {}
    for level, problem in zip(spec.levels, specs):
        base = "levels/%s/" % level.level_id
        files[base + "LEVEL.json"] = _canonical_json(level.doc)
        files[base + "BOARD.md"] = render_board(level, problem)
        entry: Dict[str, Any] = {}

        text, st = _try("executable", lambda p=problem: generate_python(ast, p))
        entry["executable"] = st
        if text is not None:
            files[base + "predictor.py"] = text

        text, st = _try("proof", lambda p=problem: generate_lean(ast, p))
        entry["proof"] = st
        if text is not None:
            files[base + "Level.lean"] = text

        def _problem(p=problem) -> str:
            domain_text, problem_text = generate_pddl(
                ast, p.name, p.width or 2, p.height or 3, problem=p)
            check_pddl(domain_text, problem_text)
            return problem_text

        text, st = _try("planning_problem", _problem)
        entry["planning_problem"] = st
        if text is not None:
            files[base + "problem.pddl"] = text
        per_level_status[level.level_id] = entry

    for key in ("executable", "proof", "planning_problem"):
        states = {lv.level_id: per_level_status[lv.level_id][key]
                  for lv in spec.levels}
        ok = all(s["status"] == "generated" for s in states.values())
        forms[key] = ({"status": "generated"} if ok else
                      {"status": "refused",
                       "why": "; ".join("%s: %s" % (k, v.get("why", "refused"))
                                        for k, v in sorted(states.items())
                                        if v["status"] != "generated")})

    if playbook_dsl is not None:
        files["playbook/PLAYBOOK.dsl"] = playbook_dsl
        files["playbook/PLAYBOOK.md"] = render_playbook(playbook_ast, playbook_dsl)

    files["GLOSSARY.md"] = render_glossary(ast, manual_dsl, spec.levels, specs,
                                           playbook_ast)
    files["README.md"] = render_readme(spec, forms, spec.levels)

    findings = context_report(files)
    blocking = [f for f in findings if f.severity == "blocking"]
    if blocking:
        raise ContextLeak(
            "%d blocking context leak(s); a reader of this package would need "
            "something it does not contain:\n%s"
            % (len(blocking),
               "\n".join("  %s:%d [%s] %s" % (f.path, f.line, f.category, f.text)
                         for f in blocking[:20])))
    files["SEAL.md"] = render_seal(findings)

    manifest = {
        "package_format": PACKAGE_FORMAT,
        "world_id": spec.world_id,
        "title": spec.title,
        "tier": spec.tier,
        "levels": [lv.level_id for lv in spec.levels],
        "forms": {k: forms[k] for k in sorted(forms)},
        "forms_by_level": {k: per_level_status[k] for k in sorted(per_level_status)},
        "context_scan": {
            "excluded": list(SCAN_EXCLUDE),
            "blocking": 0,
            "citations": len([f for f in findings if f.severity == "citation"]),
            "by_category": _counts(findings),
        },
        "compile_warnings": warnings,
        "provenance": spec.provenance,
        "files": {},
    }
    manifest["files"] = {path: _sha256(files[path]) for path in sorted(files)}
    files["MANIFEST.json"] = _canonical_json(manifest)
    manifest["bundle_digest"] = _sha256(
        "".join("%s %s\n" % (p, manifest["files"][p])
                for p in sorted(manifest["files"])))
    files["MANIFEST.json"] = _canonical_json(manifest)
    return files, manifest


def _counts(findings: Sequence[Finding]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for f in findings:
        key = "%s/%s" % (f.severity, f.category)
        out[key] = out.get(key, 0) + 1
    return dict(sorted(out.items()))


def write_package(spec: PackageSpec, out_dir: str) -> Dict[str, Any]:
    """Build and write.  Existing files under `out_dir` that the build no longer
    produces are removed, so a stale form from an earlier run cannot survive into
    a package that claims not to have it."""
    files, manifest = build_files(spec)
    if os.path.isdir(out_dir):
        for root, _dirs, names in os.walk(out_dir, topdown=False):
            for name in names:
                full = os.path.join(root, name)
                rel = os.path.relpath(full, out_dir).replace(os.sep, "/")
                if rel not in files:
                    os.remove(full)
            if not os.listdir(root) and os.path.abspath(root) != os.path.abspath(out_dir):
                os.rmdir(root)
    for path in sorted(files):
        full = os.path.join(out_dir, path.replace("/", os.sep))
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(files[path])
    return manifest


def read_package(out_dir: str) -> Dict[str, str]:
    files: Dict[str, str] = {}
    for root, _dirs, names in os.walk(out_dir):
        for name in sorted(names):
            full = os.path.join(root, name)
            rel = os.path.relpath(full, out_dir).replace(os.sep, "/")
            with open(full, "r", encoding="utf-8") as handle:
                files[rel] = handle.read().replace("\r\n", "\n")
    return files


# =========================================================================
# CLI
# =========================================================================

def _main(argv: Optional[Sequence[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m theory_compiler.handover",
        description="Build a self-contained handover package from a manual.")
    parser.add_argument("--theory", required=True, help="path to theory.dsl")
    parser.add_argument("--playbook", help="path to playbook.dsl (tier 2)")
    parser.add_argument("--level", action="append", default=[], metavar="ID=PATH",
                        help="a board, as `<level_id>=<problem.json>`; at least "
                             "two are required")
    parser.add_argument("--world-id", required=True)
    parser.add_argument("--title", default=None)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(list(argv) if argv is not None else None)

    levels = []
    for entry in args.level:
        if "=" not in entry:
            parser.error("--level takes `<level_id>=<path>`, got %r" % entry)
        level_id, path = entry.split("=", 1)
        with open(path, encoding="utf-8") as handle:
            levels.append(LevelInput(level_id=level_id, doc=json.load(handle),
                                     source=path))

    with open(args.theory, encoding="utf-8") as handle:
        manual = handle.read()
    playbook = None
    if args.playbook:
        with open(args.playbook, encoding="utf-8") as handle:
            playbook = handle.read()

    spec = PackageSpec(
        world_id=args.world_id,
        title=args.title or ("The %s world — handover package" % args.world_id),
        manual_dsl=manual,
        playbook_dsl=playbook,
        levels=tuple(levels),
        provenance={"manual": args.theory,
                    "playbook": args.playbook,
                    "levels": {lv.level_id: lv.source for lv in levels}},
    )
    manifest = write_package(spec, args.out)
    print("wrote %d files to %s (tier %s, digest %s)"
          % (len(manifest["files"]), args.out, manifest["tier"],
             manifest["bundle_digest"][:16]))
    for key, value in sorted(manifest["forms"].items()):
        if value["status"] != "generated":
            print("  form %-18s refused: %s" % (key, value.get("why", "")))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
