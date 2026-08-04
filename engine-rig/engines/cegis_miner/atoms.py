"""The guard vocabulary, and its evaluation as bitmasks over transitions.

Two things matter here beyond bookkeeping.

**Distinct atoms for extensionally equal predicates.** On Fixture A a strip that
is inside the grid is always also empty (there is only one object), so
`free`, `in_bounds` and `clear` cannot be told apart by the evidence.  They are
kept as three atoms anyway and all of them survive into the frontier, because
"the evidence does not distinguish these" is the true state of knowledge and is
exactly what a probe is for.  See DECISIONS.md D-002.

**Atoms are priced in bits.** A guard's cost is the sum of its atoms' costs, and
a position literal costs twice what a predicate costs.  Minimising atom *count*
alone would let `at(r,c)` -- the maximally specific literal, true of exactly one
transition -- win every synthesis with a single positive example.

**The action alphabet is read off the evidence, not assumed.** `DIRECTIONS` is
two different things wearing one name: a set of *geometric* directions, which
`strip_cells` needs and which every grid world has, and a guess at the world's
*action alphabet*, which only a compass-labelled world has.  A world whose
actions are `ACTION1..ACTION5` makes every `act==UP` literal identically false
and every `!act==UP` identically true, so the miner cannot see which action was
taken and `synthesize` reports that no literal separates two transitions -- a
true statement about a vocabulary that was never given the words.  Pass
`actions` to `build_vocabulary` and the `act` atoms come from the alphabet the
evidence actually contains.  Omit it and the compass is assumed, as before.
See DECISIONS.md D-E20-001.
"""

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence, Tuple, Union

DIRECTIONS = ("UP", "DOWN", "LEFT", "RIGHT")

# Strength under entailment: free(D) => in_bounds(D) and free(D) => clear(D);
# and, since the slots are single-valued, act==D => !act==D' and at(c) => !at(c').
# Negation flips the order, hence the sign flip in Atom.strength.
_RANK = {"free": 2, "in_bounds": 1, "clear": 1, "act": 1, "at": 1}

_KIND_BITS = 3      # which predicate
_NEG_BITS = 1       # negated or not
_DIR_BITS = 2       # which direction
_POS_BITS = 8       # a cell coordinate on a 12x12 board


@dataclass(frozen=True)
class Atom:
    kind: str                                  # act | free | in_bounds | clear | at
    arg: Union[str, Tuple[int, int]]
    negated: bool = False

    @property
    def name(self) -> str:
        if self.kind == "act":
            body = "act==%s" % self.arg
        elif self.kind == "at":
            body = "at(%d,%d)" % (self.arg[0], self.arg[1])
        else:
            body = "%s(strip(%s))" % (self.kind, self.arg)
        return ("!" + body) if self.negated else body

    @property
    def cost(self) -> int:
        """Description length of the literal, in bits."""
        payload = _POS_BITS if self.kind == "at" else _DIR_BITS
        return _KIND_BITS + _NEG_BITS + payload

    @property
    def strength(self) -> int:
        rank = _RANK[self.kind]
        return -rank if self.negated else rank

    def negate(self) -> "Atom":
        return Atom(self.kind, self.arg, not self.negated)

    def substitute_direction(self, direction: str, variable: str = "?dir") -> "Atom":
        """Replace a concrete direction by a variable, for rule lifting."""
        if self.kind != "at" and self.arg == direction:
            return Atom(self.kind, variable, self.negated)
        return self


# ------------------------------------------------------------------ semantics

def strip_cells(anchor: Tuple[int, int], direction: str, shape: Tuple[int, int]
                ) -> List[Tuple[int, int]]:
    r, c = anchor
    h, w = shape
    if direction == "UP":
        return [(r - 1, c + dc) for dc in range(w)]
    if direction == "DOWN":
        return [(r + h, c + dc) for dc in range(w)]
    if direction == "LEFT":
        return [(r + dr, c - 1) for dr in range(h)]
    if direction == "RIGHT":
        return [(r + dr, c + w) for dr in range(h)]
    raise ValueError(direction)


@dataclass(frozen=True)
class State:
    """Everything an atom may look at: the frame, and where the object is."""

    frame: Tuple[Tuple[int, ...], ...]
    anchor: Tuple[int, int]
    shape: Tuple[int, int]
    background: int = 0

    @property
    def height(self) -> int:
        return len(self.frame)

    @property
    def width(self) -> int:
        return len(self.frame[0])

    def in_bounds(self, cell: Tuple[int, int]) -> bool:
        return 0 <= cell[0] < self.height and 0 <= cell[1] < self.width


def evaluate(atom: Atom, state: State, action: str) -> bool:
    value = _evaluate_positive(atom.kind, atom.arg, state, action)
    return (not value) if atom.negated else value


def _evaluate_positive(kind: str, arg, state: State, action: str) -> bool:
    if kind == "act":
        return action == arg
    if kind == "at":
        return state.anchor == tuple(arg)
    cells = strip_cells(state.anchor, arg, state.shape)
    inside = [cell for cell in cells if state.in_bounds(cell)]
    if kind == "in_bounds":
        return len(inside) == len(cells)
    if kind == "clear":
        # vacuously true off-board: "nothing non-background is in the way"
        return all(state.frame[r][c] == state.background for r, c in inside)
    if kind == "free":
        return len(inside) == len(cells) and all(
            state.frame[r][c] == state.background for r, c in inside
        )
    raise ValueError(kind)


def build_vocabulary(states: Sequence[State],
                     actions: Optional[Sequence[str]] = None) -> List[Atom]:
    """Every atom the evidence could possibly need, positive and negated.

    `actions` supplies the world's action alphabet.  When it is omitted the
    compass is assumed and the result is exactly what it has always been; when
    it is given, the `act` atoms name the actions the evidence actually
    contains.  The strip predicates always range over the four geometric
    directions, because those are a fact about a grid and not about an alphabet.

    Order is deterministic and independent of the input's order: the alphabet is
    sorted, so two runs over the same evidence build the same vocabulary.
    """
    atoms: List[Atom] = []
    alphabet = sorted(set(actions)) if actions is not None else list(DIRECTIONS)
    for name in alphabet:
        atoms.append(Atom("act", name))
        atoms.append(Atom("act", name, negated=True))
    for direction in DIRECTIONS:
        for kind in ("free", "in_bounds", "clear"):
            atoms.append(Atom(kind, direction))
            atoms.append(Atom(kind, direction, negated=True))
    for anchor in sorted({s.anchor for s in states}):
        atoms.append(Atom("at", anchor))
        atoms.append(Atom("at", anchor, negated=True))
    return atoms


def atom_masks(atoms: Sequence[Atom], states: Sequence[State],
               actions: Sequence[str]) -> Dict[Atom, int]:
    """Truth table as one integer bitmask per atom -- guard evaluation is an AND."""
    masks: Dict[Atom, int] = {}
    for atom in atoms:
        mask = 0
        for i, (state, action) in enumerate(zip(states, actions)):
            if evaluate(atom, state, action):
                mask |= 1 << i
        masks[atom] = mask
    return masks


def guard_cost(guard: Sequence[Atom]) -> int:
    return sum(atom.cost for atom in guard)


def guard_strength(guard: Sequence[Atom]) -> int:
    return sum(atom.strength for atom in guard)


def guard_order_key(guard: Sequence[Atom]):
    """Total, deterministic preference over guards.

    Cheapest description first; among equals, fewest atoms; among equals, the
    logically strongest (a stronger guard fires on fewer states, so it claims
    less -- the conservative choice); ties broken by name so the output never
    depends on iteration order.
    """
    return (
        guard_cost(guard),
        len(guard),
        -guard_strength(guard),
        tuple(sorted(atom.name for atom in guard)),
    )


def atom_order_key(atom: Atom):
    return (atom.cost, -atom.strength, atom.name)
