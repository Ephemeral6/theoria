"""Turning a grounded STRIPS task into a state *type*.

A STRIPS state is a set of atoms, and over sets of atoms the deadlock theorem is
**false**: nothing stops an arbitrary atom set from holding `at(b1,c12)` and
`clear(c12)` at once, and from such a state a push can walk straight out of any
pattern. That is precisely why `deadlock_carver` needs its h² fixpoint — it has
to establish, from the action set alone, which atoms can hold together.

This module takes the other road to the same place. It reads the task's
predicate signature and, if it finds the positional one —

    at-player(?c)      exactly one thing called the player, somewhere
    at(?b, ?c)         exactly one cell per box
    clear(?c)          a cell nothing stands on

— re-presents a state as a **tuple of cells**, one slot per moving thing. In
that presentation "a box is in one place at a time" is not a fact to be derived
but the shape of the data, and `clear` is not an independent atom but a reading
of the tuple. The h² facts the producer computes are then true by construction
on this side, and the emitted Lean inherits them for free.

Two things must be checked, not assumed, and `verify` does both by exhaustion:

* **Faithfulness.** For every well-formed tuple and every ground action, the
  encoded guard must agree with `pre ⊆ atoms`, and the encoded effect must agree
  with `(atoms \\ del) ∪ add`. If it does not, the Lean development would be
  about a different system than the certificate is.
* **Adequacy.** Every state reachable in the task must be a well-formed tuple.
  Otherwise "every well-formed state containing the pattern is dead" would leave
  reachable states uncovered, which is the claim quietly narrowing.

**Degenerate tuples are outside the correspondence, and that is not glossed
over.** A tuple that puts two things in one cell has no atom-set counterpart at
all — `clear` would have to be both present and absent — so the encoding is
declared only on the well-formed ones, and the well-formedness condition travels
into the emitted theorem as a hypothesis rather than being dropped. It is not a
technicality: the closure obligation genuinely *fails* on two degenerate tuples
of the `open4far` pattern (a player standing on the box being pushed), and a
theorem that quantified over them would be false.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Sequence, Tuple

from .strips import Atom, GroundAction, StripsError, StripsTask, reachable

AT_PLAYER = "at-player"
AT = "at"
CLEAR = "clear"

State = Tuple[str, ...]          # one cell per slot, slot 0 is the player


class EncodingError(StripsError):
    """The task is not in the positional shape, or the encoding is not faithful."""


@dataclass(frozen=True)
class Guard:
    """An action's precondition, read in the encoding."""

    equals: Tuple[Tuple[int, str], ...]      # (slot, cell) the pre-state must match
    empty: Tuple[str, ...]                   # cells the pre-state must not occupy


@dataclass(frozen=True)
class Effect:
    assigns: Tuple[Tuple[int, str], ...]     # (slot, cell) the post-state takes


class PositionalEncoding:
    """Cells, slots, and the reading of each ground action in tuple terms."""

    #: Set by `verify`. `gen_lean_deadlock` refuses to emit while it is None, so
    #: the "encoding agrees with the task" link cannot be skipped by a caller who
    #: forgot it.
    verified_stats: Optional[Dict[str, int]] = None

    def __init__(self, task: StripsTask):
        self.task = task
        signature = {p: None for p in task.fluent_predicates}
        if set(signature) != {AT_PLAYER, AT, CLEAR}:
            raise EncodingError(
                "this encoding recognises the fluent signature {%s, %s, %s}; the "
                "task has {%s}. It refuses rather than approximating: an encoding "
                "that guessed at an unfamiliar predicate would be a different "
                "system than the certificate is about."
                % (AT_PLAYER, AT, CLEAR, ", ".join(task.fluent_predicates)))

        cell_types = {task.type_of(a.args[0]) for a in task.init if a.name == CLEAR}
        cell_types |= {task.type_of(a.args[0]) for a in task.init if a.name == AT_PLAYER}
        if len(cell_types) != 1:
            raise EncodingError("`clear`/`at-player` do not agree on one cell type: %s"
                                % sorted(cell_types))
        self.cell_type = cell_types.pop()
        self.cells: Tuple[str, ...] = task.objects_of(self.cell_type)

        box_types = {task.type_of(a.args[0]) for a in task.init if a.name == AT}
        if len(box_types) != 1:
            raise EncodingError("`at` does not agree on one box type: %s" % sorted(box_types))
        self.boxes: Tuple[str, ...] = task.objects_of(box_types.pop())
        self.slots: Tuple[str, ...] = ("player",) + self.boxes

        self.guards: Dict[GroundAction, Guard] = {}
        self.effects: Dict[GroundAction, Effect] = {}
        for action in task.actions:
            self.guards[action] = self._read_guard(action)
            self.effects[action] = self._read_effect(action)

    # ------------------------------------------------------------ slot lookup

    def slot_of_box(self, box: str) -> int:
        return 1 + self.boxes.index(box)

    def _slot(self, atom: Atom) -> Tuple[int, str]:
        if atom.name == AT_PLAYER:
            return 0, atom.args[0]
        if atom.name == AT:
            if atom.args[0] not in self.boxes:
                raise EncodingError("`at` mentions %r, which is not a box" % atom.args[0])
            return self.slot_of_box(atom.args[0]), atom.args[1]
        raise EncodingError("not a positional atom: %s" % atom)

    def _read_guard(self, action: GroundAction) -> Guard:
        equals: List[Tuple[int, str]] = []
        empty: List[str] = []
        for atom in sorted(action.pre):
            if atom.name == CLEAR:
                empty.append(atom.args[0])
            else:
                equals.append(self._slot(atom))
        seen = [s for s, _ in equals]
        if len(set(seen)) != len(seen):
            raise EncodingError("action %s constrains one slot twice" % action)
        return Guard(tuple(sorted(equals)), tuple(sorted(empty)))

    def _read_effect(self, action: GroundAction) -> Effect:
        assigns: List[Tuple[int, str]] = []
        for atom in sorted(action.add):
            if atom.name == CLEAR:
                continue                     # `clear` is a reading of the tuple
            assigns.append(self._slot(atom))
        seen = [s for s, _ in assigns]
        if len(set(seen)) != len(seen):
            raise EncodingError("action %s assigns one slot twice" % action)
        return Effect(tuple(sorted(assigns)))

    # ------------------------------------------------------------- the states

    def well_formed(self, state: State) -> bool:
        return len(set(state)) == len(state)

    def states(self, well_formed_only: bool = True) -> List[State]:
        product = itertools.product(self.cells, repeat=len(self.slots))
        if well_formed_only:
            return [s for s in product if self.well_formed(s)]
        return list(product)

    def atoms(self, state: State) -> FrozenSet[Atom]:
        occupied = set(state)
        out = {Atom(AT_PLAYER, (state[0],))}
        out |= {Atom(AT, (box, state[1 + i])) for i, box in enumerate(self.boxes)}
        out |= {Atom(CLEAR, (c,)) for c in self.cells if c not in occupied}
        return frozenset(out)

    def decode(self, atoms: FrozenSet[Atom]) -> Optional[State]:
        players = [a.args[0] for a in atoms if a.name == AT_PLAYER]
        placed: Dict[str, List[str]] = {}
        for atom in atoms:
            if atom.name == AT:
                placed.setdefault(atom.args[0], []).append(atom.args[1])
        if len(players) != 1:
            return None
        if sorted(placed) != sorted(self.boxes) or any(len(v) != 1 for v in placed.values()):
            return None
        state = (players[0],) + tuple(placed[b][0] for b in self.boxes)
        return state if self.atoms(state) == atoms else None

    # -------------------------------------------------------- the transitions

    def legal(self, state: State, action: GroundAction) -> bool:
        guard = self.guards[action]
        if any(state[slot] != cell for slot, cell in guard.equals):
            return False
        return all(cell not in state for cell in guard.empty)

    def apply(self, state: State, action: GroundAction) -> State:
        out = list(state)
        for slot, cell in self.effects[action].assigns:
            out[slot] = cell
        return tuple(out)

    def holds(self, state: State, pattern: Sequence[Atom]) -> bool:
        return all(atom in self.atoms(state) for atom in pattern)

    def is_goal(self, state: State) -> bool:
        return self.task.goal <= self.atoms(state)

    def initial(self) -> State:
        state = self.decode(self.task.fluent_init)
        if state is None:
            raise EncodingError(
                "the task's initial state is not a well-formed positional state")
        return state


def shortest_plan(encoding: PositionalEncoding
                  ) -> Optional[List[Tuple[State, GroundAction]]]:
    """A shortest run from the level's start to a goal, or None if there is none.

    An exhibit, not part of any proof: a conditional unsolvability theorem about
    a level that was lost from the start would be true and worthless, so the
    emitted development shows the level being won next to the pattern being
    fatal. Breadth-first over the encoded states; the actions are searched in the
    task's own order, so the plan is deterministic.
    """
    start = encoding.initial()
    if encoding.is_goal(start):
        return []
    previous: Dict[State, Tuple[State, GroundAction]] = {}
    seen = {start}
    frontier = [start]
    while frontier:
        nxt: List[State] = []
        for state in frontier:
            for action in encoding.task.actions:
                if not encoding.legal(state, action):
                    continue
                after = encoding.apply(state, action)
                if after in seen:
                    continue
                seen.add(after)
                previous[after] = (state, action)
                if encoding.is_goal(after):
                    steps: List[Tuple[State, GroundAction]] = []
                    cursor = after
                    while cursor != start:
                        before, taken = previous[cursor]
                        steps.append((before, taken))
                        cursor = before
                    return list(reversed(steps))
                nxt.append(after)
        frontier = nxt
    return None


def verify(encoding: PositionalEncoding, reachability_limit: int = 200000) -> Dict[str, int]:
    """Faithfulness and adequacy, both by exhaustion. Raises on either failure.

    **Scope, stated exactly, because an earlier version of this docstring
    overstated it.** What is checked here is the *encoding* against the *task* —
    guard against precondition, effect against add/delete, state by state and
    action by action. It says nothing about what any generator later writes into
    a file. The step from this checked encoding to emitted Lean text is a
    separate link with its own check, `gen_lean_deadlock.reread`, and the
    generator refuses to run until `verify` has set `verified_stats` here.

    The peg path's `gen_lean._check_legality` is the analogue of *that* check,
    not of this one: there `legal` is a fixed template whose meaning is known, so
    checking the predictor against it does pin the emitted text.

    Memoised on the encoding: the result is the same every time and the sweep is
    hundreds of thousands of pairs.
    """
    if getattr(encoding, "verified_stats", None) is not None:
        return encoding.verified_stats
    task = encoding.task
    checked = 0
    for state in encoding.states():
        atoms = encoding.atoms(state)
        for action in task.actions:
            checked += 1
            if encoding.legal(state, action) != action.applicable(atoms):
                raise EncodingError(
                    "the encoded guard of %s disagrees with its precondition at %s: "
                    "encoding says %s, the task says %s"
                    % (action, state, encoding.legal(state, action),
                       action.applicable(atoms)))
            if not action.applicable(atoms):
                continue
            after = encoding.decode(action.apply(atoms))
            if after is None:
                raise EncodingError(
                    "%s applied at %s leaves an atom set no tuple encodes" % (action, state))
            if after != encoding.apply(state, action):
                raise EncodingError(
                    "the encoded effect of %s disagrees at %s: encoding says %s, "
                    "the task says %s" % (action, state, encoding.apply(state, action), after))
            if not encoding.well_formed(after):
                raise EncodingError(
                    "%s applied at the well-formed state %s leaves the degenerate "
                    "state %s" % (action, state, after))

    if encoding.task.goal and not any(a.name == AT for a in encoding.task.goal):
        raise EncodingError("the goal mentions no box position, so it is not a "
                            "condition this encoding can read")

    states = reachable(task, limit=reachability_limit)
    for atoms in states:
        if encoding.decode(atoms) is None:
            raise EncodingError(
                "a reachable state is not a well-formed positional state; the "
                "well-formedness hypothesis in the emitted theorem would leave "
                "reachable states uncovered")
    encoding.verified_stats = {"encodable_states": len(encoding.states()),
                               "pairs_checked": checked,
                               "reachable_states": len(states)}
    return encoding.verified_stats
