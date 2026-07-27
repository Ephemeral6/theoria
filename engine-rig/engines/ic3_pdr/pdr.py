"""IC3 / PDR: the fallback that finds inductive invariants nobody handed us.

`zero_space` finds the linear conservation laws; `lp_potential` finds the ones
shaped like a potential function.  Theoria 1.10(b) gives IC3 the leftovers --
"the shapes LP and the null space cannot reach" -- and Fixture C has a concrete
one: configuration 0111 is unsolvable, and no linear pagoda proves it
(DECISIONS D-014 asserts exactly that, as a test).  The invariant that does prove
it is not a weight function at all; it is a set of states, and IC3's business is
finding a CNF description of one.

The algorithm, in the plain (non-delta) encoding:

  * frames F[0] = Init, F[1], F[2], ... where F[i] over-approximates the states
    reachable in at most i steps.  F[i] is a clause set; more clauses means
    fewer states, and F[1] is a superset of F[2] is a superset of ...
  * **block**: while some state of F[k] is bad, try to exclude it.  Look for a
    predecessor in F[k-1]; if there is one, that predecessor becomes an
    obligation one level down.  Reaching level 0 with an initial state means the
    property is genuinely false, and the obligation chain is the counterexample.
  * **generalise**: a state with no predecessor in F[k-1] is excluded by the
    clause that negates it -- then literals are dropped one at a time for as long
    as the clause stays inductive *relative to* F[k-1].  Dropping literals
    strengthens the clause, so this is where the real work happens: the engine
    stops talking about one state and starts talking about a region.
  * **propagate**: push clauses forward.  When two adjacent frames describe the
    same states, that frame is inductive, and it is the answer.

Relative induction, spelled out, because it is the one subtle thing: a clause c
is inductive relative to F[i-1] when every initial state satisfies c AND every
state that satisfies both F[i-1] and c has all its successors satisfying c.  The
"relative" matters -- on Fixture C the first clause IC3 finds (`pos3`, "position
3 always holds a peg") is *not* globally inductive, and the propagation phase is
what discovers that and refines it.

Every query is answered by enumeration (`system.states_where`), which is exact.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Set, Tuple, Union

from engines.ic3_pdr.system import (
    Clause,
    State,
    System,
    clause_key,
    cube_of,
    negate,
    satisfies,
    satisfies_all,
)

MAX_LEVELS = 64


class Ic3Error(Exception):
    """An internal invariant of the search broke -- never a property verdict."""


@dataclass
class Invariant:
    """A CNF over-approximation of the reachable states that excludes the goal."""

    clauses: Tuple[Clause, ...]
    level: int
    frame_sizes: Tuple[int, ...]
    blocked: int
    generalised_literals: int
    clauses_dropped: int = 0

    @property
    def n_clauses(self) -> int:
        return len(self.clauses)


def is_inductive(system: System, clauses: Sequence[Clause]) -> bool:
    """Does this clause set separate init from bad, and is it closed?

    A deliberate second implementation of what `check.verify` does.  The checker
    must stay independent of the search to be worth anything, so the search does
    not call it -- it carries its own copy, the same way the plan validator
    re-grounds rather than importing the planner (D-010).
    """
    if not clauses:
        return False                    # true everywhere: excludes no goal state
    inside = set(system.states_where(list(clauses)))
    if not all(state in inside for state in system.init):
        return False
    if any(state in inside for state in system.bad):
        return False
    return all(
        successor in inside
        for state in inside
        for successor in system.successors(state)
    )


def minimise(system: System, clauses: Sequence[Clause]) -> Tuple[Clause, ...]:
    """Drop clauses the invariant does not need.

    The frame IC3 converges on is inductive but not minimal -- clauses learned
    early survive propagation even after later ones subsume them.  On Fixture C's
    0111 the converged frame is `(pos3) & (!pos1 | pos2) & (pos1 | !pos2)`, and
    the first clause is redundant: what actually holds is "positions 1 and 2
    always agree".  Since the invariant is an artefact a reader adjudicates, the
    engine owes them the readable form rather than the search's scratch paper.
    """
    current = list(clauses)
    for clause in sorted(clauses, key=clause_key):
        trial = [c for c in current if c != clause]
        if is_inductive(system, trial):
            current = trial
    return tuple(sorted(current, key=clause_key))


@dataclass
class Counterexample:
    """A real path from an initial state to a bad one -- the property is false."""

    states: Tuple[State, ...]
    moves: Tuple[str, ...]

    @property
    def length(self) -> int:
        return len(self.moves)


Verdict = Union[Invariant, Counterexample]


@dataclass
class _Run:
    system: System
    frames: List[Set[Clause]] = field(default_factory=list)
    blocked: int = 0
    dropped: int = 0

    # ------------------------------------------------------------- oracles

    def states_of(self, level: int) -> List[State]:
        if level == 0:
            return list(self.system.init)
        return self.system.states_where(sorted(self.frames[level], key=clause_key))

    def inductive_relative(self, clause: Clause, level: int) -> bool:
        """init |= c, and F[level-1] & c & T implies c'."""
        if not all(satisfies(state, clause) for state in self.system.init):
            return False
        for state in self.states_of(level - 1):
            if not satisfies(state, clause):
                continue
            for successor in self.system.successors(state):
                if not satisfies(successor, clause):
                    return False
        return True

    def predecessor(self, state: State, level: int) -> Optional[State]:
        """A state of F[level-1] that steps into `state`, smallest one first."""
        for candidate in sorted(self.states_of(level - 1)):
            if state in self.system.successors(candidate):
                return candidate
        return None

    # -------------------------------------------------------- the two moves

    def generalise(self, clause: Clause, level: int) -> Clause:
        """Drop literals for as long as the clause stays relative-inductive."""
        current = clause
        for literal in sorted(clause):
            if len(current) <= 1:
                break
            trial = current - {literal}
            if self.inductive_relative(trial, level):
                current = trial
                self.dropped += 1
        return current

    def add_clause(self, clause: Clause, level: int) -> None:
        # Down to F[1] as well: a clause valid at `level` is valid at every
        # earlier one, and keeping the frames nested is what makes
        # `states_of(i) == states_of(i+1)` a sound convergence test.
        for index in range(1, level + 1):
            self.frames[index].add(clause)

    def block(self, state: State, level: int) -> Optional[Counterexample]:
        """Exclude `state` from F[level], or return the counterexample that stops us."""
        obligations: List[Tuple[int, State]] = [(level, state)]
        step_to: Dict[State, State] = {}

        while obligations:
            obligations.sort()
            index, current = obligations.pop(0)
            if current in self.system.init:
                return self._trace(current, step_to)
            if index == 0:
                raise Ic3Error("obligation at level 0 for a non-initial state")
            if not satisfies_all(current, self.frames[index]):
                continue                       # an earlier clause already excludes it
            earlier = self.predecessor(current, index)
            if earlier is not None:
                step_to[earlier] = current
                obligations.append((index - 1, earlier))
                obligations.append((index, current))
                continue
            clause = negate(cube_of(current))
            if not self.inductive_relative(clause, index):
                raise Ic3Error(
                    "a state with no predecessor in F[%d] is not blockable" % (index - 1)
                )
            self.add_clause(self.generalise(clause, index), index)
            self.blocked += 1
        return None

    def _trace(self, start: State, step_to: Dict[State, State]) -> Counterexample:
        states = [start]
        moves: List[str] = []
        current = start
        while current in step_to:
            target = step_to[current]
            label = next(
                (name for name, successor in self.system.moves(current) if successor == target),
                "?",
            )
            moves.append(label)
            states.append(target)
            current = target
        return Counterexample(states=tuple(states), moves=tuple(moves))


def ic3(system: System, max_levels: int = MAX_LEVELS) -> Verdict:
    """An inductive invariant separating init from bad, or a counterexample."""
    for state in system.init:
        if system.is_bad(state):
            return Counterexample(states=(state,), moves=())

    run = _Run(system=system, frames=[set(), set()])
    level = 1
    while level <= max_levels:
        while True:
            offending = next(
                (s for s in sorted(run.states_of(level)) if system.is_bad(s)), None
            )
            if offending is None:
                break
            counterexample = run.block(offending, level)
            if counterexample is not None:
                return counterexample

        run.frames.append(set())
        level += 1
        for index in range(1, level):
            for clause in sorted(run.frames[index], key=clause_key):
                if clause in run.frames[index + 1]:
                    continue
                if run.inductive_relative(clause, index + 1):
                    run.frames[index + 1].add(clause)
            if set(run.states_of(index)) == set(run.states_of(index + 1)):
                converged = tuple(sorted(run.frames[index + 1], key=clause_key))
                reduced = minimise(system, converged)
                return Invariant(
                    clauses=reduced,
                    level=index + 1,
                    frame_sizes=tuple(len(f) for f in run.frames),
                    blocked=run.blocked,
                    generalised_literals=run.dropped,
                    clauses_dropped=len(converged) - len(reduced),
                )

    raise Ic3Error("no verdict within %d levels" % max_levels)
