"""Carve conditional mini unsolvability theorems out of a grounded task.

The shape, from Theoria 1.9:

    <predicate combination> AND not-goal  =>  dead

and the proof obligation behind it is small enough to discharge by enumeration,
which is what "localise the theorem machine" means here.  A pattern P -- a
conjunction of ground atoms -- is dead when

  1. **P is closed.**  Every ground action that would delete an atom of P is
     impossible in any state containing P.  Then every successor of a state
     containing P contains P.
  2. **P excludes the goal.**  No state containing P is a goal state.

Together: from any state containing P you can only reach states containing P,
and none of those is a goal.  The theorem is *conditional* -- it says nothing
about the level as a whole, only about the region P cuts out -- and that is
precisely why deadlocks are the everyday form of unsolvability while whole-level
unsolvability is rare.

Both obligations need one thing the action set does not say outright: which
atoms can hold together.  That comes from `mutex.py` and is derived, not
declared.  "Impossible in any state containing P" then means: some precondition
of the action is mutex with some atom of P.

The two proofs the sokoban fixture actually produces:

  * a box in a corner -- **no** action deletes its position at all, because
    every push out of the corner needs a pusher cell that is a wall, and
    grounding discarded those instances before the search ever saw them;
  * two boxes side by side against a wall -- pushes exist on paper, and every
    one of them needs either the cell the other box occupies to be clear or the
    player to stand where the other box is.

Only the second needs mutexes; the first falls out of grounding.  Both are
emitted the same way, because "the certificate is short" is not a reason to
report the theorem differently.
"""

from dataclasses import dataclass, field
from itertools import combinations
from typing import Callable, Dict, FrozenSet, List, Optional, Sequence, Set, Tuple

from engines.deadlock_carver.mutex import Mutexes, reachable_pairs
from engines.fd_adapter.pddl import (
    Atom,
    Domain,
    GroundAction,
    Problem,
    ground_actions,
    static_predicates,
)
from engines.fd_adapter.search import strip_static

State = FrozenSet[Atom]

# Patterns are capped at two atoms: that is exactly the width the h^2 mutexes can
# reason about, so a wider pattern would be checked with evidence that cannot see
# it. Raising this needs h^m, not a bigger loop.
MAX_PATTERN = 2


def atom_text(atom: Atom) -> str:
    """`("at", "b1", "c14")` -> `at(b1,c14)`."""
    if len(atom) == 1:
        return atom[0]
    return "%s(%s)" % (atom[0], ",".join(atom[1:]))


def pattern_text(pattern: Sequence[Atom]) -> str:
    return " AND ".join(atom_text(a) for a in pattern)


@dataclass(frozen=True)
class Blocked:
    """One deleting action, and the reason it can never fire inside the pattern."""

    action: str
    reason: str                      # "mutex_with_pattern" | "precondition_unreachable"
    pattern_atom: Optional[Atom] = None
    action_atom: Optional[Atom] = None

    def as_json(self) -> Dict[str, object]:
        out: Dict[str, object] = {"action": self.action, "reason": self.reason}
        if self.pattern_atom is not None:
            out["pattern_atom"] = atom_text(self.pattern_atom)
        if self.action_atom is not None:
            out["action_atom"] = atom_text(self.action_atom)
        return out


@dataclass
class Theorem:
    """`pattern AND not-goal => dead`, with the certificate that proves it."""

    pattern: Tuple[Atom, ...]
    blocked: Tuple[Blocked, ...]
    goal_conflict: Tuple[Atom, Atom]           # (pattern atom, goal atom)
    n_deleting_actions: int

    @property
    def size(self) -> int:
        return len(self.pattern)

    @property
    def kind(self) -> str:
        """How the closure was won -- the corner case is the degenerate one."""
        return "no_deleting_action" if self.n_deleting_actions == 0 else "deleting_actions_blocked"

    def covers(self, state: State) -> bool:
        return all(atom in state for atom in self.pattern)

    def rendering(self) -> str:
        return "%s AND not-goal => dead" % pattern_text(self.pattern)

    def as_json(self) -> Dict[str, object]:
        pattern_atom, goal_atom = self.goal_conflict
        return {
            "form": "conditional_unsolvability",
            "pattern": [list(atom) for atom in self.pattern],
            "pattern_text": pattern_text(self.pattern),
            "size": self.size,
            "closure": self.kind,
            "n_deleting_actions": self.n_deleting_actions,
            "blocked_actions": [b.as_json() for b in self.blocked],
            "goal_conflict": {
                "pattern_atom": atom_text(pattern_atom),
                "goal_atom": atom_text(goal_atom),
                "why": "mutex: the two can never hold in the same reachable state",
            },
            "claim": "every reachable state containing %s is dead" % pattern_text(self.pattern),
            "rendering": self.rendering(),
        }


@dataclass
class Task:
    """A grounded task, reduced exactly the way the search reduces it.

    Sharing `strip_static` with the planner is not a shortcut: the pruner is
    handed the search's own states, so the atoms a theorem talks about have to be
    the atoms those states contain.
    """

    domain: Domain
    problem: Problem
    actions: List[GroundAction]
    initial: State
    goal_positive: Tuple[Atom, ...]
    goal_negative: Tuple[Atom, ...]
    mutexes: Mutexes = field(default=None)     # type: ignore[assignment]

    @classmethod
    def build(cls, domain: Domain, problem: Problem) -> "Task":
        grounded = ground_actions(domain, problem)
        actions, initial, _ = strip_static(domain, problem, grounded)
        static = static_predicates(domain)
        task = cls(
            domain=domain,
            problem=problem,
            actions=actions,
            initial=initial,
            goal_positive=tuple(a for a in problem.goal_positive if a[0] not in static),
            goal_negative=tuple(a for a in problem.goal_negative if a[0] not in static),
        )
        task.mutexes = reachable_pairs(actions, initial)
        return task

    def candidate_atoms(self) -> List[Atom]:
        """Atoms a deadlock could be about.

        Restricted to the predicates the goal mentions: a pattern that cannot
        contradict the goal cannot be dead, so anything else is enumeration for
        its own sake.  Restricted further to atoms h^2 says are reachable at all,
        because a pattern no state satisfies proves nothing about any state.
        """
        wanted = {a[0] for a in self.goal_positive} | {a[0] for a in self.goal_negative}
        return sorted(
            atom for atom in self.mutexes.singles if atom[0] in wanted
        )


# ------------------------------------------------------------------ the proof

def excludes_goal(task: Task, pattern: Sequence[Atom]) -> Optional[Tuple[Atom, Atom]]:
    """The (pattern atom, goal atom) mutex that keeps this pattern off the goal."""
    for atom in pattern:
        if atom in task.goal_negative:
            return atom, atom
    pattern_atom, goal_atom = task.mutexes.conflict(pattern, task.goal_positive)
    if pattern_atom is None:
        return None
    return pattern_atom, goal_atom


def breaks(action: GroundAction, pattern: Sequence[Atom]) -> Set[Atom]:
    """Pattern atoms this action would actually remove.

    An atom that is deleted and re-added survives, so it does not break the
    pattern -- the successor function applies deletes before adds.
    """
    return (set(action.del_effects) & set(pattern)) - set(action.add_effects)


def why_blocked(task: Task, action: GroundAction, pattern: Sequence[Atom]
                ) -> Optional[Blocked]:
    """Why this action can never fire in a state containing the pattern."""
    for atom in action.pre_negative:
        if atom in pattern:
            return Blocked(
                action=action.text(), reason="mutex_with_pattern",
                pattern_atom=atom, action_atom=atom,
            )
    pattern_atom, action_atom = task.mutexes.conflict(pattern, action.pre_positive)
    if pattern_atom is not None:
        return Blocked(
            action=action.text(), reason="mutex_with_pattern",
            pattern_atom=pattern_atom, action_atom=action_atom,
        )
    if not task.mutexes.consistent(action.pre_positive):
        return Blocked(action=action.text(), reason="precondition_unreachable")
    return None


def prove(task: Task, pattern: Sequence[Atom]) -> Optional[Theorem]:
    """The theorem for this pattern, or None if it is not dead (or not a pattern)."""
    pattern = tuple(sorted(pattern))
    if not task.mutexes.consistent(pattern):
        return None                     # describes no reachable state: proves nothing
    conflict = excludes_goal(task, pattern)
    if conflict is None:
        return None                     # a goal state could contain it

    blocked: List[Blocked] = []
    deleting = 0
    for action in task.actions:
        if not breaks(action, pattern):
            continue
        deleting += 1
        reason = why_blocked(task, action, pattern)
        if reason is None:
            return None                 # this action escapes the pattern
        blocked.append(reason)

    return Theorem(
        pattern=pattern,
        blocked=tuple(blocked),
        goal_conflict=conflict,
        n_deleting_actions=deleting,
    )


def carve(task: Task, max_pattern: int = MAX_PATTERN) -> List[Theorem]:
    """Every minimal dead pattern up to `max_pattern` atoms, in a fixed order.

    Minimal: a pair whose subset is already dead is dropped, because it says
    nothing the subset did not already say and would double-count in the node
    account.
    """
    atoms = task.candidate_atoms()
    theorems: List[Theorem] = []
    dead_singletons: Set[Atom] = set()

    for atom in atoms:
        theorem = prove(task, (atom,))
        if theorem is not None:
            theorems.append(theorem)
            dead_singletons.add(atom)

    if max_pattern >= 2:
        for first, second in combinations(atoms, 2):
            if first in dead_singletons or second in dead_singletons:
                continue
            theorem = prove(task, (first, second))
            if theorem is not None:
                theorems.append(theorem)

    theorems.sort(key=lambda t: (t.size, pattern_text(t.pattern)))
    return theorems


# ----------------------------------------------------------------- the pruner

def pruner(theorems: Sequence[Theorem]) -> Callable[[State], bool]:
    """Turn the theorems into the callable `fd_adapter.search` takes.

    Indexed on the pattern's first atom so that the common case -- a state that
    matches no theorem at all -- costs one set lookup per candidate rather than a
    scan over every theorem.
    """
    index: Dict[Atom, List[Tuple[Atom, ...]]] = {}
    for theorem in theorems:
        index.setdefault(theorem.pattern[0], []).append(theorem.pattern)

    def dead(state: State) -> bool:
        for atom in state:
            for pattern in index.get(atom, ()):
                if all(other in state for other in pattern):
                    return True
        return False

    return dead
