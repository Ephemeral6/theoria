"""Which pairs of atoms can hold together in a reachable state.

This is the h^2 reachability fixpoint (Haslum & Geffner), cut down to the binary
case and to the STRIPS subset the fd_adapter parser accepts.  It computes an
*over*-approximation of the reachable atom pairs, so the useful direction is the
negative one: a pair the fixpoint never produces genuinely never co-occurs, and
that non-membership is what every deadlock proof below rests on.

Why it is needed at all: the interesting deadlocks are not "no action can move
this box" but "every action that could move it needs a cell that the other box
is standing on".  Turning that into a proof needs one fact the action set does
not state outright -- that `clear ?c` and `at ?b ?c` cannot both hold -- and
deriving it is cheaper and more honest than declaring it.

Negative preconditions are ignored rather than approximated.  Ignoring a
precondition only lets *more* pairs into the fixpoint, so the mutexes that
survive are still sound; they are merely fewer than a fuller treatment would
find.  Erring towards fewer mutexes errs towards fewer deadlock theorems, which
is the safe direction: an unsound mutex would delete a real plan.
"""

from itertools import combinations
from typing import FrozenSet, Iterable, List, Sequence, Set, Tuple

from engines.fd_adapter.pddl import Atom, GroundAction

Pair = FrozenSet[Atom]


class Mutexes:
    """The reachable singletons and pairs, with the queries the carver asks."""

    def __init__(self, singles: Set[Atom], pairs: Set[Pair]) -> None:
        self.singles = singles
        self.pairs = pairs

    # -------------------------------------------------------------- queries

    def possible(self, atom: Atom) -> bool:
        """Could this atom ever hold in a reachable state?"""
        return atom in self.singles

    def co_possible(self, first: Atom, second: Atom) -> bool:
        """Could these two ever hold together?"""
        if first == second:
            return first in self.singles
        return frozenset((first, second)) in self.pairs

    def mutex(self, first: Atom, second: Atom) -> bool:
        return not self.co_possible(first, second)

    def consistent(self, atoms: Sequence[Atom]) -> bool:
        """Pairwise co-possible -- the strongest consistency h^2 can see."""
        return all(self.possible(a) for a in atoms) and all(
            self.co_possible(a, b) for a, b in combinations(atoms, 2)
        )

    def conflict(self, atoms: Sequence[Atom], others: Iterable[Atom]
                 ) -> Tuple[Atom, Atom]:
        """A mutex pair with one atom from each side, or (None, None)."""
        for other in others:
            for atom in atoms:
                if self.mutex(atom, other):
                    return atom, other
        return None, None            # type: ignore[return-value]

    def stats(self) -> dict:
        return {"atoms": len(self.singles), "reachable_pairs": len(self.pairs)}


def _cube_ok(atoms: Sequence[Atom], singles: Set[Atom], pairs: Set[Pair]) -> bool:
    for atom in atoms:
        if atom not in singles:
            return False
    for first, second in combinations(atoms, 2):
        if first != second and frozenset((first, second)) not in pairs:
            return False
    return True


def reachable_pairs(actions: Sequence[GroundAction], init: Iterable[Atom]) -> Mutexes:
    """The h^2 fixpoint over a grounded task.

    Grows monotonically from the initial state: an action whose preconditions are
    pairwise reachable contributes its add effects, both to each other and to
    every atom that survives its delete list.
    """
    singles: Set[Atom] = set(init)
    pairs: Set[Pair] = {
        frozenset((a, b)) for a, b in combinations(sorted(singles), 2)
    }

    changed = True
    while changed:
        changed = False
        for action in actions:
            if not _cube_ok(action.pre_positive, singles, pairs):
                continue
            adds = list(action.add_effects)
            deleted = set(action.del_effects)
            for atom in adds:
                if atom not in singles:
                    singles.add(atom)
                    changed = True
            for first, second in combinations(adds, 2):
                if first == second:
                    continue
                pair = frozenset((first, second))
                if pair not in pairs:
                    pairs.add(pair)
                    changed = True
            # An added atom also meets everything that was already true and is
            # not deleted -- provided that survivor could co-occur with the
            # preconditions in the first place.
            for survivor in sorted(singles):
                if survivor in deleted or survivor in adds:
                    continue
                if not _cube_ok(list(action.pre_positive) + [survivor], singles, pairs):
                    continue
                for atom in adds:
                    if atom == survivor:
                        continue
                    pair = frozenset((atom, survivor))
                    if pair not in pairs:
                        pairs.add(pair)
                        changed = True
    return Mutexes(singles=singles, pairs=pairs)
