"""`writes(r)` — the one definition of what a rule does to an object.

`CONTRACTS/dsl_grammar_v0.2.md` said `frame persist` means "an object no firing
rule **mentions** is unchanged" and never defined `mentions`. `a0-spike`'s
expressivity ledger **X-1** pinned the hole with 376 counterexamples: the three
available readings are not equivalent, and only one of them describes the world.

* *the rule's text* — an object named anywhere in the rule. Leaves the successor
  of a mentioned-but-unassigned object undetermined; `blocked_wall`'s guard
  reads `Box.pos` and assigns nothing, so the Box's next value is unconstrained.
  Not a definition.
* *the event signature* — the event's arguments. `slid(Box, dir)` names only the
  Box, so `persist` freezes the Player across a push, and the compiled effect
  that moves him is *overridden by the frame axiom*. Wrong on 376 pairs,
  measured.
* *the compiled effect* — right on all 47,040, and, as shipped, the worst thing
  to put in a contract: it made the manual's meaning depend on a dictionary
  inside one backend.

v0.3 keeps the third reading's extension and takes the dictionary away from the
backend. `writes(r)` is fixed by the **event declaration** and by nothing else:

1. an explicit `writes { ... }` clause on the alternative in `events:`, whose
   members must be parameters of that event; failing that,
2. `DEFAULT_WRITE_SETS` below — v0.3's published table, which exists so that
   every v0.2 manual is a v0.3 manual and for no other reason. **It is closed.**
   A new event does not go in it; a new event declares.

An event in neither is an **error**. That third clause is the load-bearing one:
without it, publishing the table would only move the guess.

The backend is then *checked against* the declaration rather than being its
source — `gen_python` compares the objects its compiled effect mutates with
`WriteSets.of_rule` and raises on a mismatch. That reversal of authority is the
whole of the fix; the definition alone would be a comment.
"""

from typing import Dict, List, Optional, Sequence, Set, Tuple

from .parser.ast_nodes import (
    EventAlt, FuncCall, NameRef, RuleDecl, TheoryAST, VarRef,
)


class WritesError(Exception):
    """A rule's write set cannot be determined, or a backend disagrees with it."""


# v0.3 §"Event write sets" — the published default table, keyed by (name,
# arity), holding 0-based argument indices. Transcribed from what was
# `conflict.CLAIMED_ARGS`, which is where this repository's answer already lived
# unpublished.
#
# `stayed/1` is the single entry that is not a transcription. `CLAIMED_ARGS` had
# it claiming its argument; its compiled effect assigns nothing (`a0-spike`'s
# `gen_exec` compiles it to `pass`). Under the adopted reading an event that
# assigns nothing writes nothing, so the table says `()`. That narrows the
# `conflict` obligation, which is sound — a rule that writes no object cannot be
# the second writer of one — and it makes ledger X-3 sharper rather than duller:
# `writes {}` is now the syntactic mark of the no-op rule X-3 wants adjudicated.
DEFAULT_WRITE_SETS: Dict[Tuple[str, int], Tuple[int, ...]] = {
    ("moved", 2): (0,),
    ("jumped", 2): (0,),
    ("teleported", 2): (0,),
    ("jumped", 3): (0, 1),          # the mover and the peg it jumps over
    ("recolored", 2): (0,),
    ("vanished", 1): (0,),
    ("appeared", 1): (0,),
    ("removed", 1): (0,),
    ("stayed", 1): (),
}


class WriteSets:
    """The manual's event declarations, resolved into write sets.

    Built from the AST so that the answer is a property of the *manual*. Passed
    explicitly to everything that needs it, for the reason `Uniqueness` is: a
    checker whose verdict depends on hidden module state is not one anybody
    should believe.

    An AST-less instance falls back to `DEFAULT_WRITE_SETS` alone, which is what
    a caller holding a bare rule (a unit test, a mined candidate) gets.
    """

    def __init__(self, ast: Optional[TheoryAST] = None):
        self.declared: Dict[Tuple[str, int], Tuple[int, ...]] = {}
        self.declared_arity: Dict[str, Set[int]] = {}
        if ast is None or ast.events is None:
            return
        for decl in ast.events.events:
            for alt in decl.alternatives:
                self._add(alt)

    def _add(self, alt: EventAlt) -> None:
        key = (alt.name, len(alt.params))
        self.declared_arity.setdefault(alt.name, set()).add(len(alt.params))
        if alt.writes is None:
            return
        indices = tuple(alt.params.index(w) for w in alt.writes)
        if key in self.declared and self.declared[key] != indices:
            raise WritesError(
                "event %s/%d is declared twice with different write sets (%r "
                "and %r). One event, one meaning."
                % (alt.name, len(alt.params), self.declared[key], indices))
        self.declared[key] = indices

    # ------------------------------------------------------------------ lookup

    def indices(self, name: str, arity: int) -> Tuple[int, ...]:
        """Which argument positions this event writes. Raises if unknown."""
        key = (name, arity)
        if key in self.declared:
            return self.declared[key]
        if key in DEFAULT_WRITE_SETS:
            return DEFAULT_WRITE_SETS[key]
        raise WritesError(
            "event %s/%d has no write set: it is not in v0.3's default table "
            "and its `events:` declaration carries no `writes { ... }` clause. "
            "Add one — `event %s(%s) writes {...}` — naming every object it "
            "assigns. Guessing 'the first argument' is what cost ledger X-1 "
            "376 mispredicted transitions."
            % (name, arity, name,
               ", ".join("a%d" % i for i in range(arity)) or ""))

    def inherited_from_table(self, rules) -> List[Tuple[str, int]]:
        """Which events these rules fire whose write set came from the table.

        The table is keyed by `(name, arity)` **across worlds**, and what a rule
        writes is a per-world fact — the same objection v0.2 §Migrating makes in
        bold about copying `semantics:` values between manuals. v0.3 keeps the
        table anyway, because it is what makes every v0.2 manual a v0.3 manual,
        and pays for it here: a default that is announced is a different thing
        from a default that is silent, and the silent kind is what E-03 was
        filed about.
        """
        out = []
        for rule in rules:
            event = rule.event
            if not isinstance(event, FuncCall):
                continue
            key = (event.name, len(event.args))
            if key not in self.declared and key in DEFAULT_WRITE_SETS:
                if key not in out:
                    out.append(key)
        return sorted(out)

    def of_rule(self, rule: RuleDecl) -> Set[str]:
        """The object instances this rule's event assigns. The one definition.

        `frame persist` is exactly: every object outside the union of these over
        the firing rules keeps its value. `conflict` ranges over pairs of rules
        whose results here intersect.
        """
        event = rule.event
        if not isinstance(event, FuncCall):
            raise WritesError(
                "rule %r has no event call, so what it writes cannot be "
                "determined and neither `frame` nor `conflict` has a meaning "
                "for it" % (rule.name,))
        indices = self.indices(event.name, len(event.args))
        out: Set[str] = set()
        for index in indices:
            arg = event.args[index]
            if not isinstance(arg, NameRef):
                raise WritesError(
                    "rule %r writes argument %d of %s, which is not an object "
                    "name (%r). A write set names objects; a direction or a "
                    "number cannot be written to."
                    % (rule.name, index, event.name, arg))
            out.add(arg.name)
        return out


def written_names(rule: RuleDecl, writes: "WriteSets") -> Optional[List[str]]:
    """The names a rule's event writes, or `None` if the event has no write set.

    Split out of `of_rule` because two callers need the two halves separately.

    * `None` means the event is in neither the manual's `writes { ... }` clauses
      nor v0.3's default table. That is somebody else's error and it already has
      a better message than this function could give (v0.3 §7: the hard refusal
      belongs at the point of use, so that a manual with an unrecognised event
      is refused *for that*). Callers pass it through.
    * A raised `WritesError` means the write set resolved and one of the
      arguments it points at is not a name at all — `recolored(leftof(?s), 1)`.
      There is nothing further to learn from that manual: the sentence has no
      object in it.

    A rule variable is returned as `"?a"`, spelled with its mark. Callers see
    this only on an **ungrounded** rule — `gen_markdown` renders the AST as the
    author wrote it, while `build_ir` runs after `ground_over_instances` and
    already refuses any rule with a variable left in it. A `?a` will become an
    instance name, so it is not the defect this function is looking for, and
    treating it as one would refuse every schema in the repository.

    The list is returned in write-set order and may repeat nothing.
    """
    event = rule.event
    if not isinstance(event, FuncCall):
        return None
    try:
        indices = writes.indices(event.name, len(event.args))
    except WritesError:
        return None
    out: List[str] = []
    for index in indices:
        arg = event.args[index]
        if isinstance(arg, VarRef):
            out.append("?" + arg.name)
            continue
        if not isinstance(arg, NameRef):
            raise WritesError(
                "rule %r writes argument %d of %s, which is not an object name "
                "(%r). An event writes objects; a cell term such as "
                "`leftof(?x)` denotes a *location*, and a location is not a "
                "thing this manual owns. If the cell needs to change, something "
                "has to stand on it: seat an instance there and write the rule "
                "over that instance. See theory-compiler/runs/"
                "20260801T1200Z-R2-2-board-cell-expressivity/FINDING.md."
                % (rule.name, index, event.name, arg))
        out.append(arg.name)
    return out


def check_backend_agreement(rule: RuleDecl, mutated: Sequence[str],
                            writes: WriteSets, backend: str) -> None:
    """A backend's compiled effect must assign exactly `writes(rule)`.

    This is the clause that stops v0.3 from being a comment. The declaration is
    the authority and the compiled effect is the thing checked; before it, the
    arrow pointed the other way and `frame persist` was true only relative to a
    dictionary the manual could not see.

    Both directions are errors, and the *extra* direction is the dangerous one:
    an object the backend writes and the declaration omits is an object the
    frame axiom promises is unchanged while the code changes it, which is the
    shape of X-1's 376 with the sign flipped.
    """
    declared = writes.of_rule(rule)
    actual = set(mutated)
    if actual == declared:
        return
    extra = sorted(actual - declared)
    missing = sorted(declared - actual)
    parts = []
    if extra:
        parts.append(
            "assigns %s, which the declaration does not list — `frame persist` "
            "would promise %s unchanged while this code changes %s"
            % (", ".join(extra), " and ".join(extra),
               "them" if len(extra) > 1 else "it"))
    if missing:
        parts.append(
            "does not assign %s, which the declaration lists" % ", ".join(missing))
    raise WritesError(
        "%s's compiled effect for rule %r %s. Either the `events:` declaration "
        "or the backend is wrong; v0.3 makes the declaration the authority, so "
        "fix the backend unless the manual is claiming something false."
        % (backend, rule.name, " and ".join(parts)))


def write_sets_of(ast: TheoryAST) -> WriteSets:
    return WriteSets(ast)


__all__ = ["DEFAULT_WRITE_SETS", "WriteSets", "WritesError",
           "check_backend_agreement", "write_sets_of", "written_names"]
