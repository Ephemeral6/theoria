"""A0′ — the second self-built world, designed against A0's own post-mortem.

`A0_REPORT.md` §6 named two things A0 could not test and one metric it reported
wrongly. A0′ changes exactly those three things and nothing else, so that the
comparison stays clean:

| A0 | A0′ | why |
|---|---|---|
| Button is a **latch** — pressable once, ever | Switch is a **toggle** | §6.2: every mechanism must be re-witnessable, or a probe has nothing to probe |
| every obstacle is a wall (colour 1) | a **Crate** (colour 4) is an obstacle that is not a wall | §6.2: two guards that agree on all observed evidence and disagree on a *reachable* configuration — a frontier a real action can split |
| explorer covers every state-action pair | explorer is **truncated at a fixed budget** | §6.1: with complete evidence the inner loop has nothing to repair; the revision count was 0 because nothing was missing |

Geometry (9×9, row-major):

```
      c0 c1 c2 c3 c4 c5 c6 c7 c8
 r0    #  #  #  #  #  #  #  #  #
 r1    #  .  .  .  .  #  .  .  #
 r2    #  .  .  .  K  #  .  *  #    K Crate (4), * goal (not rendered)
 r3    #  .  S  .  .  #  .  .  #    S Switch (7 off / 8 on)
 r4    #  .  .  .  .  D  #  .  #    D Door (5 closed, absent open)
 r5    #  C  .  .  .  #  .  .  #    C Cart start
 r6    #  .  .  .  #  #  .  .  #
 r7    #  #  #  P  #  #  .  .  #    P Portal (3) -> (1,1)
 r8    #  #  #  #  #  #  #  #  #
```

Mechanics, all four re-witnessable:

* push into floor → the Cart moves one cell;
* push into the Switch → the Switch toggles 7↔8 and the Door mirrors it
  (present iff the Switch shows 7); the Cart does not move;
* push onto the Portal marker → the Cart lands on (1,1);
* push into a wall, the Crate, or the closed Door → nothing happens.

The Door is the only opening in the divider and the Portal leads left, so the
right room is reachable only through the Switch. The goal cell is not rendered
and the win signal rides in the trace, as in A0 (D-A0-002).
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

Cell = Tuple[int, int]

FLOOR = 0
WALL = 1
CRATE = 4
PORTAL = 3
DOOR_CLOSED = 5
CART = 6
SWITCH_OFF = 7
SWITCH_ON = 8

ACTIONS = ("UP", "DOWN", "LEFT", "RIGHT")
DELTA: Dict[str, Cell] = {"UP": (-1, 0), "DOWN": (1, 0),
                          "LEFT": (0, -1), "RIGHT": (0, 1)}

HEIGHT = 9
WIDTH = 9

_LAYOUT = [
    "#########",
    "#....#..#",
    "#....#..#",
    "#....#..#",
    "#.......#",
    "#....#..#",
    "#...##..#",
    "###.##..#",
    "#########",
]

CRATE_CELL: Cell = (2, 4)
SWITCH_CELL: Cell = (3, 2)
DOOR_CELL: Cell = (4, 5)
PORTAL_CELL: Cell = (7, 3)
PORTAL_DEST: Cell = (1, 1)
CART_START: Cell = (5, 1)
GOAL_CELL: Cell = (2, 7)


@dataclass(frozen=True)
class WorldSpec:
    name: str
    switch_cell: Optional[Cell] = SWITCH_CELL
    door_cell: Optional[Cell] = DOOR_CELL
    crate_cell: Optional[Cell] = CRATE_CELL
    portal_cell: Optional[Cell] = PORTAL_CELL
    portal_dest: Cell = PORTAL_DEST
    cart_start: Cell = CART_START
    goal_cell: Cell = GOAL_CELL


BASE = WorldSpec(name="a0p-base")

# The unsolvable variant: no Switch, so the Door never opens.  Constructive
# ground identical to A0's, and it survives the toggle change because the Door
# still mirrors a Switch that is not there.
NO_SWITCH = WorldSpec(name="a0p-no-switch", switch_cell=None)


@dataclass(frozen=True)
class State:
    cart: Cell
    switch_on: bool

    def key(self) -> Tuple[int, int, int]:
        return (self.cart[0], self.cart[1], int(self.switch_on))


class A0PWorld:
    """Deterministic transition function plus renderer."""

    def __init__(self, spec: WorldSpec = BASE):
        self.spec = spec
        self.walls = frozenset(
            (r, c) for r in range(HEIGHT) for c in range(WIDTH)
            if _LAYOUT[r][c] == "#"
        )

    def in_bounds(self, cell: Cell) -> bool:
        return 0 <= cell[0] < HEIGHT and 0 <= cell[1] < WIDTH

    def initial(self) -> State:
        return State(cart=self.spec.cart_start, switch_on=False)

    def is_win(self, state: State) -> bool:
        return state.cart == self.spec.goal_cell

    # ------------------------------------------------------------ transition

    def step(self, state: State, action: str) -> State:
        dr, dc = DELTA[action]
        target = (state.cart[0] + dr, state.cart[1] + dc)

        if not self.in_bounds(target) or target in self.walls:
            return state
        if target == self.spec.crate_cell:
            return state
        if self.spec.switch_cell is not None and target == self.spec.switch_cell:
            # toggle, both ways, from any of the four directions
            return State(cart=state.cart, switch_on=not state.switch_on)
        if self.spec.door_cell is not None and target == self.spec.door_cell:
            if not state.switch_on:
                return state
            return State(cart=target, switch_on=state.switch_on)
        if self.spec.portal_cell is not None and target == self.spec.portal_cell:
            return State(cart=self.spec.portal_dest, switch_on=state.switch_on)
        return State(cart=target, switch_on=state.switch_on)

    # -------------------------------------------------------------- renderer

    def render(self, state: State) -> List[List[int]]:
        frame = [[FLOOR] * WIDTH for _ in range(HEIGHT)]
        for r, c in self.walls:
            frame[r][c] = WALL
        if self.spec.crate_cell is not None:
            r, c = self.spec.crate_cell
            frame[r][c] = CRATE
        if self.spec.portal_cell is not None:
            r, c = self.spec.portal_cell
            frame[r][c] = PORTAL
        if self.spec.door_cell is not None and not state.switch_on:
            r, c = self.spec.door_cell
            frame[r][c] = DOOR_CLOSED
        if self.spec.switch_cell is not None:
            r, c = self.spec.switch_cell
            frame[r][c] = SWITCH_ON if state.switch_on else SWITCH_OFF
        r, c = state.cart
        frame[r][c] = CART
        return frame

    # --------------------------------------------------------- reachable set

    def reachable(self) -> List[State]:
        start = self.initial()
        seen = {start.key(): start}
        frontier = [start]
        while frontier:
            state = frontier.pop()
            for action in ACTIONS:
                nxt = self.step(state, action)
                if nxt.key() not in seen:
                    seen[nxt.key()] = nxt
                    frontier.append(nxt)
        return [seen[k] for k in sorted(seen)]
