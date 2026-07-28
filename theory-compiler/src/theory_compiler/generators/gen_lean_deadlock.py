"""A Lean development from a `deadlock_carver` conditional-unsolvability theorem.

Theoria 1.9's shape, verbatim:

    <pattern>  AND  not-goal   =>   dead

and the word that earns this emitter its own module is **conditional**. The
pagoda and CNF routes both prove a *global* statement — nothing reachable from
`s₀` is a goal. This one proves nothing whatever about `s₀`. It says: wherever
you are, if the pattern holds, you have already lost. On `sokoban-open4far` that
distinction is not academic; the level **is** solvable, and the emitted
development says so, with a plan, next to the theorem that says the pattern is
fatal. A conditional theorem whose condition never holds, or whose level was
lost anyway, would prove nothing and read like proof.

Three obligations and the induction that joins them:

    theorem dead_closed  : wf s → Pat s → legal s m → wf (step s m) ∧ Pat (step s m)
    theorem pat_no_goal  : Pat s → Goal s = false
    theorem dead         : wf r → Pat r → ReachFrom r s → Goal s = false

`wf` is the well-formedness of a state — no two things in one cell — and it is
carried rather than assumed away. It is exactly the content of the producer's h²
mutex fixpoint, and on this fixture it is load-bearing: two degenerate states
break closure for the pair pattern (see `strips_encoding`), so a theorem
quantified over all tuples would be **false**. Every reachable state is
well-formed, and `strips_encoding.verify` checks that by exhaustion, so nothing
is lost by carrying it.

Everything else in the file is derived from the grounded task, never from the
certificate: `Cell` from the objects, `Move` from the ground actions, `legal`
and `applyMove` from their preconditions and effects, `Goal` from the problem's
goal. The certificate contributes exactly one thing — `Pat`, the pattern — which
is the whole of what it is entitled to contribute.

## Proof mode

`proof="computational"` splits on the slots the pattern does **not** pin, then
on every move, then `decide`. Every leaf is closed, the axiom set is **empty**,
and the cost is `|cells|^(free slots) × |moves|` goals. That is why the split is
computed rather than hardcoded: a pattern that pins both boxes leaves one slot
free and costs a sixteenth of what an unpinned one costs. Above
`MAX_LEAN_CASES` the emitter raises rather than emitting a file that will not
elaborate — the same refusal `CertificateGapError` makes, for the same reason.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Sequence, Tuple

from ..strips import Atom, GroundAction, StripsTask
from ..strips_encoding import AT, AT_PLAYER, CLEAR, PositionalEncoding, State

#: Leaf goals `cases … <;> decide` may produce. Lean elaborates every one of
#: them separately, so this is a wall-clock budget, not a soundness one — but a
#: file that takes an hour to compile is not a file anyone checks.
MAX_LEAN_CASES = 65536

#: Leaves `closed_pinned` can close inside Lean's default heartbeat budget,
#: measured on this fixture: 1792 leaves land at ~4s, well inside it; 28672 hits
#: the ceiling at ~110s. Above this the emitter raises the budget explicitly.
_HEARTBEAT_FREE_LEAVES = 2000


def _heartbeats_for(leaves: int) -> int:
    """A budget proportional to the split, rounded to something legible."""
    return max(400000, 200000 * (leaves // 2000 + 1))


class DeadlockLeanError(Exception):
    """The development cannot be emitted honestly at this size or in this shape."""


_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_']*\Z")
_LEAN_KEYWORDS = {
    "theorem", "def", "structure", "inductive", "where", "match", "with", "fun",
    "let", "have", "show", "from", "by", "do", "if", "then", "else", "end",
    "namespace", "section", "variable", "instance", "class", "deriving", "open",
    "abbrev", "example", "mutual", "partial", "unsafe", "private", "protected",
    "at", "this", "sorry", "axiom", "attribute", "macro", "notation", "set_option",
}


def _ident(name: str, what: str) -> str:
    """Lean identifiers are generated from PDDL object names, so check them.

    A name that needed quoting or escaping would silently become a different
    name in the emitted file, and the whole point of the file is that the reader
    can match its constructors against the task by eye.
    """
    if not _IDENT.match(name) or name in _LEAN_KEYWORDS:
        raise DeadlockLeanError(
            "%s %r is not usable as a Lean identifier; this emitter will not "
            "rename the task's vocabulary behind the reader's back" % (what, name))
    return name


# --------------------------------------------------------------- reading bits

def _slot_index(encoding: PositionalEncoding, atom: Atom) -> Optional[int]:
    if atom.name == AT_PLAYER:
        return 0
    if atom.name == AT:
        return encoding.slot_of_box(atom.args[0])
    return None


def _predicate_terms(encoding: PositionalEncoding, atoms: Sequence[Atom]) -> List[str]:
    """A conjunction of atoms, in tuple terms. Deterministic order."""
    out: List[str] = []
    for atom in sorted(atoms):
        slot = _slot_index(encoding, atom)
        if slot is not None:
            out.append("s.%s == .%s" % (encoding.slots[slot], atom.args[-1]))
        elif atom.name == CLEAR:
            out.append("s.clear .%s" % atom.args[0])
        else:
            raise DeadlockLeanError("cannot read the atom %s in the positional encoding" % atom)
    return out


def _pins(encoding: PositionalEncoding, atoms: Sequence[Atom]) -> Dict[int, str]:
    """Which slots a conjunction fixes to a cell."""
    out: Dict[int, str] = {}
    for atom in sorted(atoms):
        slot = _slot_index(encoding, atom)
        if slot is None:
            continue
        if slot in out and out[slot] != atom.args[-1]:
            raise DeadlockLeanError(
                "the pattern puts %s in two cells at once (%s and %s), so it holds "
                "in no state and its theorem would be vacuous"
                % (encoding.slots[slot], out[slot], atom.args[-1]))
        out[slot] = atom.args[-1]
    return out


def _reads(encoding: PositionalEncoding, atoms: Sequence[Atom]) -> List[int]:
    """Which slots a conjunction's truth value depends on."""
    if any(a.name == CLEAR for a in atoms):
        return list(range(len(encoding.slots)))        # `clear` reads every slot
    return sorted({_slot_index(encoding, a) for a in atoms
                   if _slot_index(encoding, a) is not None})


def _move_name(action: GroundAction) -> str:
    return _ident("%s_%s" % (action.name.replace("-", "_"), "_".join(action.args)),
                  "ground action")


def _state_literal(encoding: PositionalEncoding, pinned: Dict[int, str],
                   variables: Dict[int, str]) -> str:
    parts = []
    for i in range(len(encoding.slots)):
        if i in pinned:
            parts.append("." + pinned[i])
        else:
            parts.append(variables[i])
    return "⟨%s⟩" % ", ".join(parts)


# ------------------------------------------------------------------- emission

def generate_deadlock_lean(task: StripsTask, encoding: PositionalEncoding,
                           cert, proof: str = "computational",
                           plan: Optional[Sequence[Tuple[State, GroundAction]]] = None,
                           witness: Optional[State] = None) -> str:
    """The Lean source. `cert` is a `DeadlockCertificate` whose obligations passed.

    `plan` and `witness`, when given, are the two non-vacuity exhibits: a run
    from the level's start to a goal (so the reader knows the level was winnable
    before the pattern happened), and a well-formed state the pattern accepts.
    """
    if proof != "computational":
        raise DeadlockLeanError(
            "this emitter has one proof mode, `computational`, whose axiom set is "
            "empty. There is no `algebraic` mode to fall back to: an algebraic "
            "one would cost `propext` and save nothing here, because the split "
            "is over cells rather than over arithmetic.")

    cells = [_ident(c, "cell") for c in encoding.cells]
    slots = [_ident(s, "slot") for s in encoding.slots]
    moves = list(task.actions)

    pattern = list(cert.pattern)
    pinned = _pins(encoding, pattern)
    free = [i for i in range(len(slots)) if i not in pinned]
    leaves = len(cells) ** len(free) * len(moves)
    if leaves > MAX_LEAN_CASES:
        raise DeadlockLeanError(
            "closing `dead_closed` by `decide` would take %d leaf goals "
            "(%d cell(s) ^ %d unpinned slot(s) x %d move(s)), over the budget of "
            "%d. The pattern pins %d of %d slots; a pattern that pins more is "
            "cheaper. Refusing rather than emitting a file that will not "
            "elaborate."
            % (leaves, len(cells), len(free), len(moves), MAX_LEAN_CASES,
               len(pinned), len(slots)))

    goal_atoms = sorted(task.goal)
    pat_reads = _reads(encoding, pattern)
    goal_reads = _reads(encoding, goal_atoms)
    split_for_no_goal = sorted(set(pat_reads) | set(goal_reads))
    no_goal_leaves = len(cells) ** len(split_for_no_goal)
    if no_goal_leaves > MAX_LEAN_CASES:
        raise DeadlockLeanError(
            "closing `pat_no_goal` by `decide` would take %d leaf goals, over the "
            "budget of %d" % (no_goal_leaves, MAX_LEAN_CASES))

    L: List[str] = []
    _header(L, task, encoding, cert, pattern, pinned, free, moves, leaves)
    _world(L, task, encoding, cells, slots, moves)
    _predicates(L, encoding, cert, pattern, goal_atoms)
    _theorems(L, encoding, slots, pinned, free, pat_reads, split_for_no_goal)
    _exhibits(L, encoding, plan, witness)

    L.append("#print axioms pat_pins")
    L.append("#print axioms closed_pinned")
    L.append("#print axioms dead_closed")
    L.append("#print axioms no_goal_pinned")
    L.append("#print axioms pat_no_goal")
    L.append("#print axioms dead_persists")
    L.append("#print axioms dead")
    if witness is not None:
        L.append("#print axioms pat_witness")
    if plan is not None:
        L.append("#print axioms level_is_winnable")
    L.append("")
    return "\n".join(L)


def _header(L, task, encoding, cert, pattern, pinned, free, moves, leaves) -> None:
    L.append("/-")
    L.append("  Auto-generated from a grounded STRIPS task — DO NOT EDIT.")
    L.append("")
    L.append("  A **conditional** unsolvability theorem for %s / %s:"
             % (task.domain, task.problem))
    L.append("")
    L.append("      %s  AND  not-goal  =>  dead" % cert.pattern_text)
    L.append("")
    L.append("  Conditional is the operative word. Nothing below is a claim about")
    L.append("  the level's start state; `dead` quantifies over every well-formed")
    L.append("  state the pattern accepts, reachable or not.")
    L.append("")
    L.append("  The pattern — and *only* the pattern — comes from")
    L.append("      %s" % cert.provenance)
    L.append("  produced by %s. Its two obligations were" % cert.produced_by)
    L.append("  recomputed here before emission over the whole well-formed state")
    L.append("  space; the producer's own mutex bookkeeping was read for")
    L.append("  cross-checking and believed for nothing.")
    L.append("")
    L.append("  Everything else is read off the grounded task: %d cell(s), %d"
             % (len(encoding.cells), len(moves)))
    L.append("  ground action(s), the problem's own goal.")
    L.append("")
    L.append("  `wf` — no two things share a cell — is carried as a hypothesis")
    L.append("  rather than assumed away. It is the content of the producer's h²")
    L.append("  fixpoint, and it is load-bearing: closure genuinely fails on")
    L.append("  states that put the player inside a box. Every reachable state is")
    L.append("  well-formed, checked by exhaustion on the Python side.")
    L.append("")
    L.append("  Proof mode `computational`: the split is over the %d slot(s) the"
             % len(free))
    L.append("  pattern leaves free (of %d) and then over moves — %d leaf goals,"
             % (len(encoding.slots), leaves))
    L.append("  every one closed by `decide`. Axiom set **empty**. No `sorry`,")
    L.append("  no `native_decide`.")
    if leaves > _HEARTBEAT_FREE_LEAVES:
        L.append("")
        L.append("  Lean's default heartbeat budget is sized for ordinary")
        L.append("  declarations, not for a `<;>`-chained split this wide, so the")
        L.append("  file raises it. That is a wall-clock concession and nothing")
        L.append("  more: every leaf is still closed by `decide` and the axiom set")
        L.append("  is still empty. It is stated here rather than left for whoever")
        L.append("  next runs the file to discover.")
    L.append("-/")
    L.append("")
    if leaves > _HEARTBEAT_FREE_LEAVES:
        L.append("set_option maxHeartbeats %d" % _heartbeats_for(leaves))
        L.append("")


def _world(L, task, encoding, cells, slots, moves) -> None:
    L.append("inductive Cell where")
    for cell in cells:
        L.append("  | %s" % cell)
    L.append("  deriving DecidableEq, Repr")
    L.append("")
    L.append("/-- One cell per moving thing. `clear` is a reading of this tuple,")
    L.append("    not an independent atom, which is what makes \"a cell holds at")
    L.append("    most one thing\" true by construction rather than by lemma. -/")
    L.append("structure St where")
    for slot in slots:
        L.append("  %s : Cell" % slot)
    L.append("  deriving DecidableEq, Repr")
    L.append("")
    L.append("/-- `clear c` of the STRIPS task. -/")
    L.append("def St.clear (s : St) (c : Cell) : Bool :=")
    L.append("  " + " && ".join("s.%s != c" % slot for slot in slots))
    L.append("")
    L.append("/-- Well-formed: no two things in one cell. -/")
    L.append("def wf (s : St) : Bool :=")
    pairs = [(a, b) for i, a in enumerate(slots) for b in slots[i + 1:]]
    L.append("  " + " && ".join("s.%s != s.%s" % (a, b) for a, b in pairs))
    L.append("")
    L.append("/-- The %d ground actions of the task, one constructor each. -/" % len(moves))
    L.append("inductive Move where")
    for action in moves:
        L.append("  | %s" % _move_name(action))
    L.append("  deriving DecidableEq, Repr")
    L.append("")
    L.append("def legal (s : St) (m : Move) : Bool :=")
    L.append("  match m with")
    for action in moves:
        guard = encoding.guards[action]
        terms = ["s.%s == .%s" % (encoding.slots[slot], cell)
                 for slot, cell in guard.equals]
        terms += ["s.clear .%s" % cell for cell in guard.empty]
        L.append("  | .%s => %s" % (_move_name(action), " && ".join(terms) or "true"))
    L.append("")
    L.append("def applyMove (s : St) (m : Move) : St :=")
    L.append("  match m with")
    for action in moves:
        assigns = encoding.effects[action].assigns
        body = ", ".join("%s := .%s" % (encoding.slots[slot], cell)
                         for slot, cell in assigns)
        L.append("  | .%s => %s" % (_move_name(action),
                                    "{ s with %s }" % body if body else "s"))
    L.append("")
    start = encoding.initial()
    L.append("def s0 : St := ⟨%s⟩" % ", ".join("." + c for c in start))
    L.append("")


def _predicates(L, encoding, cert, pattern, goal_atoms) -> None:
    L.append("/-- The problem's goal. -/")
    L.append("def Goal (s : St) : Bool :=")
    L.append("  " + " && ".join(_predicate_terms(encoding, goal_atoms)))
    L.append("")
    L.append("/-- The certificate's pattern: %s -/" % cert.pattern_text)
    L.append("def Pat (s : St) : Bool :=")
    L.append("  " + " && ".join(_predicate_terms(encoding, pattern)))
    L.append("")
    L.append("/-- One step of the task, from an arbitrary state rather than from `s0`. -/")
    L.append("inductive ReachFrom (r : St) : St → Prop where")
    L.append("  | refl : ReachFrom r r")
    L.append("  | step : ∀ s m, ReachFrom r s → legal s m = true → ReachFrom r (applyMove s m)")
    L.append("")


def _partial_literal(encoding, reads: Sequence[int], slots: Sequence[str]) -> str:
    """A state literal with the read slots as variables and the rest filled in.

    `decide` refuses a goal containing a free variable, so a lemma about a
    predicate that ignores some slots cannot leave those slots abstract. Filling
    them with a fixed cell is sound *because* the predicate ignores them: the
    filled statement and the abstract one reduce to the same term, so the caller
    applies the lemma at any state by definitional unfolding. `_reads` is what
    decides which slots may be filled, and it answers "all of them" the moment
    the predicate mentions `clear`.
    """
    filler = encoding.cells[0]
    return "⟨%s⟩" % ", ".join(
        slots[i] if i in reads else "." + filler for i in range(len(slots)))


def _theorems(L, encoding, slots, pinned, free, pat_reads, split_for_no_goal) -> None:
    all_slots = list(range(len(slots)))
    variables = {i: slots[i] for i in all_slots}
    literal = _state_literal(encoding, pinned, variables)

    read_names = [slots[i] for i in pat_reads]
    pat_literal = _partial_literal(encoding, pat_reads, slots)
    conclusions = " ∧ ".join("%s = .%s" % (slots[i], pinned[i]) for i in sorted(pinned))
    L.append("/-- The pattern pins %d of %d slot(s), so a state satisfying it is"
             % (len(pinned), len(slots)))
    L.append("    determined by the rest. This is what keeps the split below small. -/")
    L.append("theorem pat_pins : ∀ (%s : Cell), Pat %s = true → %s := by"
             % (" ".join(read_names), pat_literal, conclusions))
    L.append("  intro %s" % " ".join(read_names))
    L.append("  " + " <;> ".join(["cases %s" % n for n in read_names] + ["decide"]))
    L.append("")

    free_names = [slots[i] for i in free]
    binders = "(%s : Cell) " % " ".join(free_names) if free_names else ""
    L.append("/-- Closure, on the states the pattern leaves open. -/")
    L.append("theorem closed_pinned : ∀ %s(m : Move)," % binders)
    L.append("    wf %s = true → legal %s m = true →" % (literal, literal))
    L.append("    wf (applyMove %s m) = true ∧ Pat (applyMove %s m) = true := by"
             % (literal, literal))
    L.append("  intro %sm" % ("".join(n + " " for n in free_names)))
    L.append("  " + " <;> ".join(["cases %s" % n for n in free_names] + ["cases m", "decide"]))
    L.append("")

    L.append("/-- The same, with the pinning discharged. -/")
    L.append("theorem dead_closed : ∀ (s : St) (m : Move), wf s = true → Pat s = true →")
    L.append("    legal s m = true →")
    L.append("    wf (applyMove s m) = true ∧ Pat (applyMove s m) = true := by")
    L.append("  intro s m hw hp hl")
    L.append("  cases s with")
    L.append("  | mk %s =>" % " ".join(slots))
    if len(pinned) == 1:
        only = sorted(pinned)[0]
        L.append("    have h%d := pat_pins %s hp" % (only, " ".join(read_names)))
        L.append("    subst h%d" % only)
    else:
        L.append("    obtain ⟨%s⟩ := pat_pins %s hp"
                 % (", ".join("h%d" % i for i in sorted(pinned)), " ".join(read_names)))
        for i in sorted(pinned):
            L.append("    subst h%d" % i)
    L.append("    exact closed_pinned %shw hl" % "".join(n + " " for n in free_names + ["m"]))
    L.append("")

    no_goal_names = [slots[i] for i in split_for_no_goal]
    no_goal_literal = _partial_literal(encoding, split_for_no_goal, slots)
    L.append("/-- The pattern excludes the goal, on the slots the two of them read. -/")
    L.append("theorem no_goal_pinned : ∀ (%s : Cell), Pat %s = true → Goal %s = false := by"
             % (" ".join(no_goal_names), no_goal_literal, no_goal_literal))
    L.append("  intro %s" % " ".join(no_goal_names))
    L.append("  " + " <;> ".join(["cases %s" % n for n in no_goal_names] + ["decide"]))
    L.append("")
    L.append("/-- The pattern excludes the goal. -/")
    L.append("theorem pat_no_goal : ∀ (s : St), Pat s = true → Goal s = false := by")
    L.append("  intro s")
    L.append("  cases s with")
    L.append("  | mk %s => exact no_goal_pinned %s" % (" ".join(slots), " ".join(no_goal_names)))
    L.append("")

    L.append("theorem dead_persists : ∀ (r s : St), wf r = true → Pat r = true →")
    L.append("    ReachFrom r s → wf s = true ∧ Pat s = true := by")
    L.append("  intro r s hw hp h")
    L.append("  induction h with")
    L.append("  | refl => exact ⟨hw, hp⟩")
    L.append("  | step t m _ hl ih => exact dead_closed t m ih.1 ih.2 hl")
    L.append("")
    L.append("/-- The theorem. From **any** well-formed state containing the pattern,")
    L.append("    nothing reachable is a goal. -/")
    L.append("theorem dead : ∀ (r s : St), wf r = true → Pat r = true → ReachFrom r s →")
    L.append("    Goal s = false := by")
    L.append("  intro r s hw hp h")
    L.append("  exact pat_no_goal s (dead_persists r s hw hp h).2")
    L.append("")


def _exhibits(L, encoding, plan, witness) -> None:
    if witness is not None:
        literal = "⟨%s⟩" % ", ".join("." + c for c in witness)
        L.append("/-- Not vacuous: a well-formed state the pattern accepts. A theorem")
        L.append("    whose hypothesis nothing satisfies proves nothing and reads")
        L.append("    like proof. -/")
        L.append("theorem pat_witness : wf %s = true ∧ Pat %s = true := by decide"
                 % (literal, literal))
        L.append("")
    if plan is not None:
        L.append("/-- Not idle either: this level **is** winnable. Below is a run from")
        L.append("    `s0` to a goal state, so `dead` above is a statement about the")
        L.append("    pattern and not about a level that was lost from the start. -/")
        L.append("theorem level_is_winnable : ∃ s : St, ReachFrom s0 s ∧ Goal s = true := by")
        previous = "ReachFrom.refl"
        for index, (state, action) in enumerate(plan):
            after = "⟨%s⟩" % ", ".join("." + c for c in encoding.apply(state, action))
            L.append("  have h%d : ReachFrom s0 %s :=" % (index, after))
            L.append("    ReachFrom.step _ .%s %s (by decide)" % (_move_name(action), previous))
            previous = "h%d" % index
        L.append("  exact ⟨_, %s, by decide⟩" % previous)
        L.append("")
