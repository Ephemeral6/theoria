"""`GridWorld` — the transition function, the renderer, and the reachable set.

The world itself knows almost nothing.  It knows the grid, it knows the agent,
and it knows how to ask the mechanisms.  `step` is the whole of it:

    1. the target cell is out of bounds or a wall      -> nothing happens
    2. otherwise each mechanism, in priority order, is offered the target;
       the first one that claims it returns an `Outcome`
    3. no claimant                                     -> the agent walks in
    4. `settle` runs to a fixpoint (this is where gravity lives)

Everything a mechanism needs about the rest of the world it gets from
`is_free`, `occupied` and `movables`, so no mechanism imports another.

Determinism is structural rather than promised: mechanisms are ordered by
`(priority, name)`, entities keep spec order, `reachable()` walks a BFS from the
initial state and returns states sorted by `State.key()`, and no dict iteration
order reaches an output.
"""

from typing import Any, Dict, FrozenSet, List, Optional, Sequence, Tuple

from ..mechanisms.base import Ctx, Mechanism, Outcome, View, for_kind, registry
from .spec import Entity, WorldSpec, validate
from .types import ACTIONS, AGENT, FLOOR, WALL, Cell, State, decode_cell, encode_cell, shift

SETTLE_LIMIT = 256          # a settle loop longer than this is a bug, not a world


class GridWorld:
    def __init__(self, spec: WorldSpec, check: bool = True):
        if check:
            validate(spec)
        self.spec = spec
        self.walls: FrozenSet[Cell] = frozenset(
            (r, c)
            for r in range(spec.height)
            for c in range(spec.width)
            if spec.layout[r][c] == "#"
        )

        # --- bind mechanisms -------------------------------------------------
        wanted: Dict[str, Mechanism] = {}
        for kind in sorted({e.kind for e in spec.entities}):
            mechanism = for_kind(kind)
            if mechanism is None:
                raise ValueError("no mechanism owns entity kind %r" % kind)
            wanted[mechanism.name] = mechanism
        for name in spec.families:               # families with no entities (gravity)
            mechanism = registry().get(name)
            if mechanism is None:
                raise ValueError("unknown mechanism family %r" % name)
            wanted[mechanism.name] = mechanism

        self.mechanisms: Tuple[Mechanism, ...] = tuple(
            sorted(wanted.values(), key=lambda m: (m.priority, m.name))
        )
        self.entities_of: Dict[str, Tuple[Entity, ...]] = {
            m.name: tuple(e for e in spec.entities if e.kind in m.kinds)
            for m in self.mechanisms
        }

        base = 0
        self.slices: Dict[str, Tuple[int, int]] = {}
        init: List[int] = []
        for mechanism in self.mechanisms:
            mine = self.entities_of[mechanism.name]
            length = mechanism.n_vars(spec, mine)
            values = mechanism.initial_vars(spec, mine)
            if len(values) != length:
                raise ValueError("%s: initial_vars has %d entries, n_vars says %d"
                                 % (mechanism.name, len(values), length))
            self.slices[mechanism.name] = (base, length)
            init.extend(values)
            base += length
        self._initial = State(agent=spec.agent_start, vars=tuple(init))

    # ------------------------------------------------------------- plumbing

    def view(self, mechanism: Mechanism, state: State) -> View:
        base, length = self.slices[mechanism.name]
        return View(base, length, state.vars)

    def mine(self, mechanism: Mechanism) -> Tuple[Entity, ...]:
        return self.entities_of[mechanism.name]

    def in_bounds(self, cell: Cell) -> bool:
        return self.spec.in_bounds(cell)

    def occupied(self, state: State) -> FrozenSet[Cell]:
        """Every cell that is impassable right now, walls included."""
        out = set(self.walls)
        for mechanism in self.mechanisms:
            out |= mechanism.occupied(self.spec, self.mine(mechanism),
                                      self.view(mechanism, state))
        return frozenset(out)

    def no_rest(self, state: State) -> FrozenSet[Cell]:
        out = set()
        for mechanism in self.mechanisms:
            out |= mechanism.no_rest(self.spec, self.mine(mechanism),
                                     self.view(mechanism, state))
        return frozenset(out)

    def is_free(self, state: State, cell: Cell) -> bool:
        """Can an *object* be placed here?  Used by push and by gravity.

        Stricter than `can_stand`: a crate may not be parked on a door, a portal
        mouth or a token even where the agent may walk over it, because the thing
        underneath would vanish from the frame and the frame would stop
        determining the state.  See `Mechanism.no_rest`.
        """
        if not self.can_stand(state, cell):
            return False
        if cell == state.agent:
            return False
        return cell not in self.no_rest(state)

    def can_stand(self, state: State, cell: Cell) -> bool:
        """Can the *agent* end a move here?  Used by teleports.

        The agent may finish on a gate cell — that is what walking through a door
        means — so this asks only about bounds, walls and whatever is currently
        impassable.
        """
        if not self.in_bounds(cell) or cell in self.walls:
            return False
        return cell not in self.occupied(state)

    def movables(self, state: State) -> Tuple[Tuple[int, Cell], ...]:
        out: List[Tuple[int, Cell]] = []
        for mechanism in self.mechanisms:
            out.extend(mechanism.movables(self.spec, self.mine(mechanism),
                                          self.view(mechanism, state)))
        return tuple(sorted(out))

    # ------------------------------------------------------------ transition

    def initial(self) -> State:
        return self.settle(self._initial)

    def is_win(self, state: State) -> bool:
        return state.agent == self.spec.goal

    def settle(self, state: State) -> State:
        for _ in range(SETTLE_LIMIT):
            nxt = None
            for mechanism in self.mechanisms:
                nxt = mechanism.settle(self, state)
                if nxt is not None and nxt != state:
                    break
                nxt = None
            if nxt is None:
                return state
            state = nxt
        raise RuntimeError("%s: settle did not converge" % self.spec.world_id)

    def explain(self, state: State, action: str) -> Tuple[State, str]:
        """`step`, plus the name of the ground-truth rule that fired.

        The rule name is what `core/reversibility.py` groups on, so it is
        produced by the same code path that produces the state — a rule cannot
        drift away from the transition it labels.
        """
        target = shift(state.agent, action)
        if not self.in_bounds(target) or target in self.walls:
            return state, "blocked_by_wall"

        outcome: Optional[Outcome] = None
        for mechanism in self.mechanisms:
            outcome = mechanism.interact(Ctx(
                world=self,
                spec=self.spec,
                state=state,
                action=action,
                target=target,
                view=self.view(mechanism, state),
                mine=self.mine(mechanism),
            ))
            if outcome is not None:
                break

        if outcome is None:
            outcome = Outcome(agent=target, rule="walk")

        nxt = state.written(outcome.writes)
        if outcome.agent is not None:
            nxt = nxt.with_agent(outcome.agent)
        return self.settle(nxt), outcome.rule

    def step(self, state: State, action: str) -> State:
        return self.explain(state, action)[0]

    # -------------------------------------------------------------- renderer

    def render(self, state: State) -> List[List[int]]:
        spec = self.spec
        frame = [[FLOOR] * spec.width for _ in range(spec.height)]
        for r, c in self.walls:
            frame[r][c] = WALL
        for mechanism in self.mechanisms:
            mechanism.render(spec, self.mine(mechanism),
                             self.view(mechanism, state), frame)
        # The agent is painted last and therefore wins every overlap.  The goal
        # is deliberately not painted: as in cold-start-a0 (D-A0-002) the win
        # signal rides in the trace, so a reader has to induce the objective
        # rather than read it off the grid.
        frame[state.agent[0]][state.agent[1]] = AGENT
        return frame

    # --------------------------------------------------------- reachable set

    def reachable(self, limit: int = 200_000) -> List[State]:
        start = self.initial()
        seen = {start.key(): start}
        frontier = [start]
        while frontier:
            state = frontier.pop()
            for action in ACTIONS:
                nxt = self.step(state, action)
                if nxt.key() in seen:
                    continue
                if len(seen) >= limit:
                    raise RuntimeError("%s: reachable set exceeds %d states"
                                       % (self.spec.world_id, limit))
                seen[nxt.key()] = nxt
                frontier.append(nxt)
        return [seen[k] for k in sorted(seen)]

    def transitions(self, states: Optional[Sequence[State]] = None):
        """`(state, action, next_state, rule)` over the whole reachable graph."""
        for state in (self.reachable() if states is None else states):
            for action in ACTIONS:
                nxt, rule = self.explain(state, action)
                yield state, action, nxt, rule
