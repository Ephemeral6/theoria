"""The A2 world: a pushing world whose goal room has exactly one entrance, and
that entrance is a teleport.

Built to reproduce the failure structure Theoria §1.3 describes for DC22, using
nothing from DC22 itself.  §1.3's structural claim, and all A2 borrows from it:

  * the model replays the whole history correctly;
  * it is nevertheless missing one **teleport rule**;
  * a complete search over that model proves the goal unreachable;
  * the level is in fact solvable.

The isomorphism is therefore in the *shape of the omission*, not in any geometry,
palette or trajectory.  INC-004's ruling is what permits this substitution, and
`DECISIONS.md` D-A2-001 records which upstream text was read (that paragraph of
§1.3) and which was not (any artifact of the sealed game itself, whose id this
directory deliberately does not carry — INC-004 records it, A2 does not need
it, and `tests/test_a2.py::test_no_dc22_artifact_is_present` keeps it out).

Geometry (9x9, row-major, (row, col)):

        c0 c1 c2 c3 c4 c5 c6 c7 c8
    r0   #  #  #  #  #  #  #  #  #
    r1   #  B  #  .  .  #  .  .  #     B = Button, alcove, reachable only from below
    r2   #  .  .  .  .  #  .  *  #     * = goal cell, not rendered
    r3   #  .  .  .  .  #  .  .  #
    r4   #  .  .  .  .  #  .  .  #
    r5   #  C  .  .  .  #  .  .  #     C = Cart start
    r6   #  #  .  .  D  #  .  .  #     D = Door
    r7   #  K  #  #  P  #  .  X  #     P = Portal entry, K = sealed pocket
    r8   #  #  #  #  #  #  #  #  #     X = portal exit

Three facts about this layout carry the whole spike:

1. **column c5 is solid wall from r1 to r7.**  The right room touches nothing.
   No sequence of one-cell pushes reaches it, so deleting the teleport rule makes
   the goal unreachable *and provably so* — that is the exhibit.

2. **the Portal is reachable only through the Door, and only from above.**
   (7,4)'s neighbours are (6,4) — the Door — and three walls.  So the teleport
   has exactly one firing context and the manual needs exactly one rule for it;
   and a play record that stops at the Door's threshold owes the teleport nothing.

3. **(7,1) is a sealed pocket.**  Floor, walled on all four sides, never
   occupied.  It is the world's own *true* unreachable cell, and it is what the
   repaired manual proves a genuine unreachability theorem about.  Same theorem
   shape as the exhibit, same instrument, opposite truth value — which is the
   two-layer truth regime (Theoria §1.10a) made into two artefacts you can
   diff.

Colours: 0 floor, 1 wall, 3 portal entry, 5 door (closed), 6 cart,
7 button (unpressed), 8 button (pressed).  Deliberately A0's palette: A2 is a
sibling world, and reusing the palette keeps the reused segmenter/compiler path
honest — nothing here is tuned to make the pipeline's job easier.
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

# `#` wall, `.` floor.  Objects and markers overlay this; the static layer and
# the object layer are never confused in the source either.
_LAYOUT = [
    "#########",
    "#.#..#..#",
    "#....#..#",
    "#....#..#",
    "#....#..#",
    "#....#..#",
    "##...#..#",
    "#.##.#..#",
    "#########",
]

BUTTON_CELL: Cell = (1, 1)
DOOR_CELL: Cell = (6, 4)
PORTAL_CELL: Cell = (7, 4)
PORTAL_DEST: Cell = (7, 6)
CART_START: Cell = (5, 1)
GOAL_CELL: Cell = (2, 7)
POCKET_CELL: Cell = (7, 1)


@dataclass(frozen=True)
class WorldSpec:
    """Everything that distinguishes one A2 instance from another."""

    name: str
    button_cell: Optional[Cell] = BUTTON_CELL
    door_cell: Optional[Cell] = DOOR_CELL
    portal_cell: Optional[Cell] = PORTAL_CELL
    portal_dest: Cell = PORTAL_DEST
    cart_start: Cell = CART_START
    goal_cell: Cell = GOAL_CELL


BASE = WorldSpec(name="a2-base")


@dataclass(frozen=True)
class State:
    cart: Cell
    pressed: bool

    def key(self) -> Tuple[int, int, int]:
        return (self.cart[0], self.cart[1], int(self.pressed))


class A2World:
    """Deterministic transition function plus renderer.

    Nothing in this class is ever read by the discovery pipeline.  The pipeline
    sees `artifacts/raw_trace.jsonl` and `artifacts/history_trace.jsonl`, which
    carry frames, actions and a win flag and nothing else.
    """

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

        The Button press and the Door opening happen in the *same* transition,
        as in A0: `semantics: cascade single_frame` is a fact about this world
        and the manual has to declare it (DECISIONS.md D-A2-004).
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

    def step_holed(self, state: State, action: str) -> State:
        """The same world **without** the teleport rule.

        Not a variant of the world and never used to generate a trace: it is the
        referee's copy of what the holed manual claims, so that M6 can score
        "the manual's world" against "the world" as two transition functions
        rather than as two prose paragraphs.
        """
        dr, dc = DELTA[action]
        target = (state.cart[0] + dr, state.cart[1] + dc)
        if self.spec.portal_cell is not None and target == self.spec.portal_cell:
            return state                                     # the deleted rule
        return self.step(state, action)

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

    def reachable(self, holed: bool = False) -> List[State]:
        """Every state reachable from the initial one, in a deterministic order.

        `holed=True` walks `step_holed` instead, which is how the constructive
        ground for the exhibit is checked rather than asserted.
        """
        move = self.step_holed if holed else self.step
        start = self.initial()
        seen = {start.key(): start}
        frontier = [start]
        while frontier:
            state = frontier.pop()
            for action in ACTIONS:
                nxt = move(state, action)
                if nxt.key() not in seen:
                    seen[nxt.key()] = nxt
                    frontier.append(nxt)
        return [seen[k] for k in sorted(seen)]

    def solve(self, holed: bool = False) -> Optional[List[str]]:
        """A shortest winning action sequence, or None if there is none.

        This is the referee's answer, not the manual's.  It is what "有人解出来
        了" (Theoria §1.4) means concretely: the fact that refutes a false
        unreachability theorem is a witness path, and here is where it comes
        from.
        """
        from collections import deque

        move = self.step_holed if holed else self.step
        start = self.initial()
        if self.is_win(start):
            return []
        seen = {start.key()}
        queue = deque([(start, [])])
        while queue:
            state, path = queue.popleft()
            for action in ACTIONS:
                nxt = move(state, action)
                if nxt.key() in seen:
                    continue
                seen.add(nxt.key())
                if self.is_win(nxt):
                    return path + [action]
                queue.append((nxt, path + [action]))
        return None


def frames_and_actions(world: A2World, states: Sequence[State],
                       actions: Sequence[Optional[str]]):
    return [world.render(s) for s in states], list(actions)
