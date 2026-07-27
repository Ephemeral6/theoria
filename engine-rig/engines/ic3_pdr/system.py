"""The finite transition system IC3 runs on, and its literal/clause vocabulary.

Everything here is *data*: the states, the labelled transitions, the initial and
bad sets are all enumerated up front.  That is what lets the SAT queries IC3
normally needs be answered by exhaustive enumeration instead of by a solver --
the same substitution `fd_adapter` makes for Fast Downward (DECISIONS D-009),
for the same reason, with the same consequence: correctness is unaffected and
reach is.  A system with more than a few dozen variables wants a real solver
behind `states_where`, and nothing above that function would change.

Vocabulary.  A **literal** is (variable index, required value).  A **clause** is
a frozenset of literals read as a disjunction -- dropping a literal makes a
clause *stronger*, which is the whole mechanism behind inductive generalisation.
A **cube** is a conjunction; the only cubes here are complete states.
"""

from dataclasses import dataclass
from typing import Dict, FrozenSet, Iterable, List, Optional, Sequence, Tuple

State = Tuple[bool, ...]
Literal = Tuple[int, bool]
Clause = FrozenSet[Literal]
Cube = Tuple[Literal, ...]


def satisfies(state: State, clause: Clause) -> bool:
    """A clause is a disjunction: one agreeing literal is enough."""
    return any(state[index] == value for index, value in clause)


def satisfies_all(state: State, clauses: Iterable[Clause]) -> bool:
    return all(satisfies(state, clause) for clause in clauses)


def cube_of(state: State) -> Cube:
    return tuple((index, value) for index, value in enumerate(state))


def negate(cube: Cube) -> Clause:
    """The clause excluding exactly the states that satisfy this cube."""
    return frozenset((index, not value) for index, value in cube)


def clause_key(clause: Clause) -> Tuple:
    """A total order on clauses, so every loop over a clause set is reproducible."""
    return (len(clause), tuple(sorted(clause)))


@dataclass(frozen=True)
class System:
    """A finite, fully enumerated labelled transition system."""

    name: str
    variables: Tuple[str, ...]
    states: Tuple[State, ...]
    init: Tuple[State, ...]
    bad: Tuple[State, ...]
    transitions: Dict[State, Tuple[Tuple[str, State], ...]]

    def successors(self, state: State) -> Tuple[State, ...]:
        return tuple(target for _, target in self.transitions.get(state, ()))

    def moves(self, state: State) -> Tuple[Tuple[str, State], ...]:
        return self.transitions.get(state, ())

    def is_bad(self, state: State) -> bool:
        return state in set(self.bad)

    def states_where(self, clauses: Sequence[Clause]) -> List[State]:
        """Every state satisfying all the clauses -- the enumerating SAT oracle."""
        return [s for s in self.states if satisfies_all(s, clauses)]

    # ------------------------------------------------------------ rendering

    def render_state(self, state: State) -> str:
        return "".join("1" if bit else "0" for bit in state)

    def render_literal(self, literal: Literal) -> str:
        index, value = literal
        return self.variables[index] if value else "!" + self.variables[index]

    def render_clause(self, clause: Clause) -> str:
        return "(%s)" % " | ".join(
            self.render_literal(literal) for literal in sorted(clause)
        )

    def render_cnf(self, clauses: Sequence[Clause]) -> str:
        if not clauses:
            return "true"
        return " & ".join(
            self.render_clause(c) for c in sorted(clauses, key=clause_key)
        )

    def clause_as_json(self, clause: Clause) -> List[List[object]]:
        return [
            [self.variables[index], value] for index, value in sorted(clause)
        ]


# ------------------------------------------------------------ peg solitaire

def peg_system(graph: Dict[str, object], initial: str,
               goal_states: Optional[Sequence[str]] = None,
               name: str = "peg4") -> System:
    """Fixture C as a transition system.

    The transition relation is taken over the *whole* state space, not the part
    reachable from `initial`, for the same reason `lp_potential` does: an
    inductive invariant has to be closed under moves from every state satisfying
    it, and restricting the relation to the reachable part would make the
    closure check quietly circular.
    """
    n = int(graph["n_pos"])                                # type: ignore[index]
    goals = tuple(goal_states or graph["goal_states"])     # type: ignore[index]
    variables = tuple("pos%d" % i for i in range(n))

    def to_state(text: str) -> State:
        return tuple(char == "1" for char in text)

    states = tuple(to_state(text) for text in sorted(graph["states"]))  # type: ignore[index]
    transitions: Dict[State, List[Tuple[str, State]]] = {}
    for edge in graph["edges"]:                            # type: ignore[index]
        source = to_state(edge["src_state"])
        transitions.setdefault(source, []).append(
            (str(edge["move"]), to_state(edge["dst_state"]))
        )

    return System(
        name=name,
        variables=variables,
        states=states,
        init=(to_state(initial),),
        bad=tuple(to_state(text) for text in goals),
        transitions={
            state: tuple(sorted(moves)) for state, moves in transitions.items()
        },
    )
