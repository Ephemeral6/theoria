"""The mechanism contract.  Every family in `worldgen/mechanisms/` implements it.

A mechanism owns a set of **entity kinds**, a **slice of the state vector**, and
the answers to six questions the world asks it:

| question | method | when |
|---|---|---|
| how much state do you need? | `n_vars` / `initial_vars` | construction |
| which cells are impassable right now? | `occupied` | every free-cell test |
| which of your entities can be shoved? | `movables` | push, gravity |
| what happens if the agent moves into this cell? | `interact` | every step |
| does anything settle afterwards? | `settle` | every step, to fixpoint |
| what is the truth about you? | `truth_rules`, `invariants`, `reversibility` | ground-truth emission |

Two rules keep families independent:

* **a mechanism only ever touches its own slice.**  `View.abs(i)` translates a
  local index into the global one; writes go out as `(global_index, value)`
  pairs in an `Outcome`, never by mutating state.
* **a mechanism never inspects another's entities.**  Anything it needs about
  the rest of the world it asks the world for — `world.is_free(state, cell)`,
  `world.occupied(state)`, `world.movables(state)`.  That is why gravity can
  drop a crate it has never heard of.

`interact` returning `None` means "not mine, ask the next one"; returning an
`Outcome` ends dispatch.  Cell-sharing is forbidden by `spec.validate`, so
dispatch order can never change behaviour — `priority` exists only to make the
order deterministic for readers and diffs.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Optional, Sequence, Tuple

from ..core.spec import Entity, WorldSpec
from ..core.types import Cell, State, decode_cell, encode_cell


@dataclass(frozen=True)
class Outcome:
    """What a step does.  `agent=None` means the agent does not move."""

    agent: Optional[Cell] = None
    writes: Tuple[Tuple[int, int], ...] = ()
    # A short tag naming the ground-truth rule that fired.  The reversibility
    # analysis groups transitions by this tag, so it is not decoration: an
    # unnamed effect is a rule that cannot be checked for re-witnessability.
    rule: str = "noop"


class View:
    """A mechanism's window onto the flat state vector."""

    __slots__ = ("base", "length", "_vars")

    def __init__(self, base: int, length: int, vars_: Tuple[int, ...]):
        self.base = base
        self.length = length
        self._vars = vars_

    def abs(self, index: int) -> int:
        if not 0 <= index < self.length:
            raise IndexError("local index %d outside this mechanism's %d slots"
                             % (index, self.length))
        return self.base + index

    def get(self, index: int) -> int:
        return self._vars[self.abs(index)]

    def all(self) -> Tuple[int, ...]:
        return self._vars[self.base:self.base + self.length]

    def rebind(self, vars_: Tuple[int, ...]) -> "View":
        return View(self.base, self.length, vars_)


@dataclass
class Ctx:
    """Everything `interact` is allowed to see."""

    world: Any                 # GridWorld; use world.is_free / world.spec
    spec: WorldSpec
    state: State
    action: str
    target: Cell               # the cell the agent is trying to enter
    view: View
    mine: Tuple[Entity, ...]   # this mechanism's entities, spec order

    def index_at(self, cell: Cell) -> Optional[int]:
        """Position of my entity on `cell` within `self.mine`, or None."""
        for i, entity in enumerate(self.mine):
            if entity.cell == cell:
                return i
        return None


class Mechanism:
    """Base class.  Subclasses override what they need; the defaults are inert."""

    name: str = ""
    kinds: Tuple[str, ...] = ()
    priority: int = 50

    # --------------------------------------------------------------- state
    def n_vars(self, spec: WorldSpec, mine: Tuple[Entity, ...]) -> int:
        return 0

    def initial_vars(self, spec: WorldSpec, mine: Tuple[Entity, ...]) -> Tuple[int, ...]:
        return ()

    # -------------------------------------------------------------- queries
    def occupied(self, spec: WorldSpec, mine: Tuple[Entity, ...],
                 view: View) -> FrozenSet[Cell]:
        """Cells this mechanism currently makes impassable."""
        return frozenset()

    def no_rest(self, spec: WorldSpec, mine: Tuple[Entity, ...],
                view: View) -> FrozenSet[Cell]:
        """Cells no *object* may be left standing on, whether or not they are passable.

        A door is passable when open and a portal mouth is passable always, but a
        crate shoved onto either one is a bug with two heads: the gate's own
        colour disappears under the crate, so the frame stops determining the
        state, and a door that later closes ends up underneath a solid object.
        Both showed up as invariant violations on the first build of
        `t2-switch-push`, which is what this hook exists to prevent.

        The default is every cell this mechanism owns, which is right for every
        family whose entities do not move; `push` overrides it to empty, because
        its blocks move and their live cells are already in `occupied`.  The set
        is deliberately *static* — a collected token's cell stays off limits —
        since a rest-eligibility that changes under the agent's feet buys nothing
        the catalogue needs and costs a subtlety nobody would remember.
        """
        return frozenset(entity.cell for entity in mine)

    def movables(self, spec: WorldSpec, mine: Tuple[Entity, ...],
                 view: View) -> Tuple[Tuple[int, Cell], ...]:
        """`(global var index holding an encoded cell, current cell)` per shovable entity.

        Push and gravity both relocate things by writing an encoded cell into
        the slot named here, which is how they move entities they do not own.
        """
        return ()

    # ------------------------------------------------------------ behaviour
    def interact(self, ctx: Ctx) -> Optional[Outcome]:
        return None

    def settle(self, world: Any, state: State) -> Optional[State]:
        """Applied repeatedly after every step until no mechanism changes anything."""
        return None

    # -------------------------------------------------------------- drawing
    def render(self, spec: WorldSpec, mine: Tuple[Entity, ...], view: View,
               frame: List[List[int]]) -> None:
        return None

    # ----------------------------------------------------------- the truth
    def truth_rules(self, spec: WorldSpec, mine: Tuple[Entity, ...]) -> List[Dict[str, Any]]:
        """One dict per ground-truth rule: `name` (matching `Outcome.rule`),
        `when`, `then`, and `reversible` — the designer's claim, which
        `core/reversibility.py` then checks against the reachable graph."""
        return []

    def invariants(self, spec: WorldSpec, mine: Tuple[Entity, ...]) -> List[Dict[str, Any]]:
        """One dict per invariant: `name`, `statement`, and `check` — a callable
        `(world, state) -> bool` exercised over the whole reachable set."""
        return []

    def reversibility(self, spec: WorldSpec, mine: Tuple[Entity, ...]) -> List[Dict[str, Any]]:
        """Optional prose notes; the numbers come from the reachable graph."""
        return []


# --------------------------------------------------------------- registry

_REGISTRY: Dict[str, Mechanism] = {}


def register(mechanism: Mechanism) -> Mechanism:
    if mechanism.name in _REGISTRY:
        raise ValueError("mechanism %r registered twice" % mechanism.name)
    _REGISTRY[mechanism.name] = mechanism
    return mechanism


def registry() -> Dict[str, Mechanism]:
    return dict(_REGISTRY)


def for_kind(kind: str) -> Optional[Mechanism]:
    for mechanism in _REGISTRY.values():
        if kind in mechanism.kinds:
            return mechanism
    return None
