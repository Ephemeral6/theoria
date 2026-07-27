"""The A0 world: a self-built, fully-known micro-world for the cold-start spike.

Richer than engine-rig's Fixture A in exactly one way that matters: it contains a
**rule dependency**.  A Door is an obstacle until a Button has been pressed, so
no single-object account of the Cart's motion can explain the trajectory -- the
theory has to name a second object and a law relating them.  A low-frequency
Portal is kept from Fixture A's tradition as the thin-evidence rule.

Nothing here is ever read by the discovery pipeline.  The pipeline sees only
`artifacts/raw_trace.jsonl`, which carries frames, actions and the win flag and
nothing else.  The ground truth lives in `ground_truth.py` / `GROUND_TRUTH.md`
and is the referee's copy.

Geometry (9x9, row-major, (row, col)):

        c0 c1 c2 c3 c4 c5 c6 c7 c8
    r0   #  #  #  #  #  #  #  #  #
    r1   #  .  .  .  .  #  .  .  #
    r2   #  .  .  .  .  #  .  *  #     * = goal cell, not rendered
    r3   #  .  B  .  .  #  .  .  #     B = Button
    r4   #  .  .  .  .  D  .  .  #     D = Door
    r5   #  C  .  .  .  #  .  .  #     C = Cart start
    r6   #  .  .  .  #  #  .  .  #
    r7   #  #  #  P  #  #  .  .  #     P = Portal entry
    r8   #  #  #  #  #  #  #  #  #

Colours: 0 floor, 1 wall, 3 portal entry, 5 door (closed), 6 cart,
7 button (unpressed), 8 button (pressed).  An open door renders as floor.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

Cell = Tuple[int, int]

# ------------------------------------------------------------------ palette

FLOOR = 0
WALL = 1
PORTAL = 3
DOOR_CLOSED = 5
CART = 6
BUTTON_UP = 7
BUTTON_DOWN = 8

ACTIONS = ("UP", "DOWN", "LEFT", "RIGHT")
DELTA: Dict[str, Cell] = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}

HEIGHT = 9
WIDTH = 9

# `#` wall, `.` floor.  Objects and markers are placed separately so that the
# static layer and the object layer are never confused in the source either.
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

BUTTON_CELL: Cell = (3, 2)
DOOR_CELL: Cell = (4, 5)
PORTAL_CELL: Cell = (7, 3)
PORTAL_DEST: Cell = (1, 1)
CART_START: Cell = (5, 1)
GOAL_CELL: Cell = (2, 7)


@dataclass(frozen=True)
class WorldSpec:
    """Everything that distinguishes one A0 instance from another."""

    name: str
    button_cell: Optional[Cell] = BUTTON_CELL
    door_cell: Optional[Cell] = DOOR_CELL
    portal_cell: Optional[Cell] = PORTAL_CELL
    portal_dest: Cell = PORTAL_DEST
    cart_start: Cell = CART_START
    goal_cell: Cell = GOAL_CELL


BASE = WorldSpec(name="a0-base")

# The unsolvable variant: the Button is simply not there, so the Door can never
# open.  Constructive ground: the goal cell lies in the right room and the Door
# is the only opening in the dividing wall (the Portal leads left, not right).
NO_BUTTON = WorldSpec(name="a0-no-button", button_cell=None)


@dataclass(frozen=True)
class State:
    cart: Cell
    pressed: bool

    def key(self) -> Tuple[int, int, int]:
        return (self.cart[0], self.cart[1], int(self.pressed))


class A0World:
    """Deterministic transition function plus renderer."""

    def __init__(self, spec: WorldSpec = BASE):
        self.spec = spec
        self.walls = frozenset(
            (r, c)
            for r in range(HEIGHT)
            for c in range(WIDTH)
            if _LAYOUT[r][c] == "#"
        )

    # -------------------------------------------------------------- geometry

    def in_bounds(self, cell: Cell) -> bool:
        return 0 <= cell[0] < HEIGHT and 0 <= cell[1] < WIDTH

    def initial(self) -> State:
        return State(cart=self.spec.cart_start, pressed=False)

    def is_win(self, state: State) -> bool:
        return state.cart == self.spec.goal_cell

    # ------------------------------------------------------------ transition

    def step(self, state: State, action: str) -> State:
        """One action, one successor.  Total and deterministic by construction.

        The Button press and the Door opening happen in the *same* transition --
        the cascade question of Theoria 1.8 is answered here by fiat, and the
        answer is recorded in DECISIONS.md as D-A0-004.
        """
        dr, dc = DELTA[action]
        target = (state.cart[0] + dr, state.cart[1] + dc)

        if not self.in_bounds(target) or target in self.walls:
            return state
        if self.spec.button_cell is not None and target == self.spec.button_cell:
            if state.pressed:
                return state
            return State(cart=state.cart, pressed=True)      # press, cart stays
        if self.spec.door_cell is not None and target == self.spec.door_cell:
            if not state.pressed:
                return state
            return State(cart=target, pressed=state.pressed)
        if self.spec.portal_cell is not None and target == self.spec.portal_cell:
            return State(cart=self.spec.portal_dest, pressed=state.pressed)
        return State(cart=target, pressed=state.pressed)

    # -------------------------------------------------------------- renderer

    def render(self, state: State) -> List[List[int]]:
        """Full-frame: every pixel is either board or exactly one object."""
        frame = [[FLOOR] * WIDTH for _ in range(HEIGHT)]
        for r, c in self.walls:
            frame[r][c] = WALL
        if self.spec.portal_cell is not None:
            pr, pc = self.spec.portal_cell
            frame[pr][pc] = PORTAL
        if self.spec.door_cell is not None and not state.pressed:
            dr, dc = self.spec.door_cell
            frame[dr][dc] = DOOR_CLOSED
        if self.spec.button_cell is not None:
            br, bc = self.spec.button_cell
            frame[br][bc] = BUTTON_DOWN if state.pressed else BUTTON_UP
        cr, cc = state.cart
        frame[cr][cc] = CART
        return frame

    # --------------------------------------------------------- reachable set

    def reachable(self) -> List[State]:
        """Every state reachable from the initial one, in a deterministic order."""
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

    def passable_cells(self) -> List[Cell]:
        """Cells the Cart may legally stand on, ignoring the Door's state."""
        out = []
        for r in range(HEIGHT):
            for c in range(WIDTH):
                cell = (r, c)
                if cell in self.walls:
                    continue
                if cell == self.spec.button_cell:
                    continue
                if cell == self.spec.portal_cell:
                    continue        # entering it always bounces the Cart onward
                out.append(cell)
        return out


def frames_and_actions(world: A0World, states: Sequence[State],
                       actions: Sequence[Optional[str]]):
    return [world.render(s) for s in states], list(actions)
