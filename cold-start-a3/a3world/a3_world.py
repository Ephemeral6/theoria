"""The A3 world — **one mechanism set, two levels**.

A3 exists to test Theoria's Claim C3 offline: *carry the two books to a second
level and the marginal cost collapses*.  Theoria §1.10a fixes what "carry" is
allowed to mean:

    说明书是 domain(跨关不变), 关卡布局是 problem(逐关实例) ——
    PDDL 本就强制这么切, C3"迁移"的严格含义就是 domain 带得走。

So the experiment is only honest if the two levels genuinely share a domain and
genuinely differ in their problem.  That is a property of the *world*, and it is
built here rather than asserted later:

* **the mechanism set is defined once**, in `step()`, and both levels are the
  same function under a different `LevelSpec`;
* **every coordinate is in the `LevelSpec`** — walls, cart start, switch, door,
  the two portal cells, the goal.  Nothing about geometry is reachable from
  `step()` except through the spec;
* the two specs share **no** cell.  Different walls, different start, different
  goal, portals in different places, switch and door in different places.

Mechanisms (the domain — identical in both levels):

1. **push** — the Cart moves one cell into a free cell; walls block.
2. **switch / door** — pushing into the Switch cell toggles it and the Cart
   stays put; the Door is present exactly while the Switch is up.  Toggle and
   door change happen in the *same* transition (`cascade single_frame`).
3. **portal pair** — pushing into portal-A puts the Cart on `exit_a`, and
   pushing into portal-B puts it on `exit_b`.  Symmetric, so both legs are
   witnessable.  The two portal cells are markers the Cart never stands on;
   the two exits are ordinary floor.
4. **goal** — the Cart standing on the goal cell wins.

**Why the exits are plain floor and not marked cells.**  The first version of
this world made each portal's exit the *other portal's cell*, so that both
landmarks could be read straight off frame 0.  It does not survive the reused
perception path, and the failure is recorded rather than designed around:
`mdl_segmenter` matches frame *t* against *t+1* only, so when the mover lands
on a cell that already hosts a static track, the cheaper script is "the
resident recolours to 6" plus "the mover vanishes" — not "the mover jumped".
The mover's track was absent from 19 of 326 frames and the miner proposed
`obj3_appear_*` / `obj3_vanish_*` rules instead of a jump.  The run is kept at
`artifacts/finding_d_a3_003/` and written up as **D-A3-003**; this is the third
segmentation gap the A0 family has found in that engine, after touching objects
and A0′'s re-identification.

The consequence is paid openly.  A portal exit is not visible in any frame, so
the transfer arm cannot derive it and is **supplied** it, along with the goal
cell, as level data.  That is what the frozen contract already says it is —
`CONTRACTS/dsl_grammar_v0.2.md`: *"Grid layout, initial state, landmark
coordinates and weight vectors are the problem, and are supplied per level."*
`a3pipeline/problem_frame.py` records, per field, whether it was derived from
the frame or supplied, and the meter reports the split, so the size of the
concession is a number in the table and not a sentence in a footnote.

**Reversibility is a design rule here, not an accident** (`monitor` finding
F-12, adopted from `cold-start-a0/prime`: *reversibility beats coverage* — an
irreversible mechanism caps what any amount of exploration can establish).  The
Switch toggles both ways, the portal works both ways, and every push is
undoable, so the whole state graph is undirected and every rule can be
re-witnessed on demand.  That is what lets level 1's sweep produce a domain
with no thin-evidence clauses, which is the precondition for testing transfer
rather than testing luck.

The goal cell is **not rendered**.  It is not discoverable from pixels and A3
does not pretend otherwise: the goal lives in the problem instance, exactly
where PDDL puts it, and is supplied per level.  See `DECISIONS.md` D-A3-002 —
what the transfer arm is given is a goal cell; what it is *not* given is a rule.

Colours are A0's and A2's where they overlap, on purpose: A3 reuses their
segmenter and compiler and a bespoke palette would make the reuse flattering.

    0 floor   1 wall   3 portal-A   4 portal-B
    5 door (present)   6 cart   7 switch up   8 switch down

Level 1 (`L1`), 9x9, row-major (row, col):

        c0 c1 c2 c3 c4 c5 c6 c7 c8
    r0   #  #  #  #  #  #  #  #  #
    r1   #  .  .  .  #  .  a  .  #    a exit_a (1,6) — plain floor
    r2   #  .  A  .  #  .  B  .  #    A portal-A (2,2), B portal-B (2,6)
    r3   #  .  b  .  #  .  .  .  #    b exit_b (3,2) — plain floor
    r4   #  S  #  .  #  .  .  .  #    S Switch (4,1), in a vertical alcove
    r5   #  .  .  .  #  #  #  .  #
    r6   #  C  .  .  #  #  #  D  #    C Cart start (6,1), D Door (6,7)
    r7   #  .  .  .  #  #  #  *  #    * goal (7,7), not rendered
    r8   #  #  #  #  #  #  #  #  #

Level 2 (`L2`), 9x9 — same mechanisms, nothing else in common:

        c0 c1 c2 c3 c4 c5 c6 c7 c8
    r0   #  #  #  #  #  #  #  #  #
    r1   #  *  .  .  #  a  B  .  #    * goal (1,1); a exit_a (1,5); B portal-B (1,6)
    r2   #  .  #  #  #  .  .  .  #
    r3   #  D  #  .  #  .  .  .  #    D Door (3,1)
    r4   #  b  .  .  #  .  .  .  #    b exit_b (4,1) — plain floor
    r5   #  A  .  .  #  .  .  .  #    A portal-A (5,1)
    r6   #  .  .  .  #  .  .  C  #    C Cart start (6,7)
    r7   #  .  .  .  #  #  S  #  #    S Switch (7,6), in a vertical alcove
    r8   #  #  #  #  #  #  #  #  #

Two properties of the pair are load-bearing and are asserted by tests rather
than by this docstring:

* **L2's winning path uses the portal leg L1's winning path does not.**  L1
  wins through A -> B; L2 wins through B -> A.  A domain mined from L1 that had
  only recorded the leg L1 needed would fail on L2, so the transfer is a real
  claim about induction, not a re-run.
* **every guard L2 needs was witnessed in L1.**  L1's portal cells have four
  free neighbours each and its Switch has two, which is a superset of what L2's
  geometry can present.  `tests/test_transfer.py` checks the containment
  directly instead of trusting the drawing.

`L2_ONEWAY` is the negative control: the same level 2 with the portal's B -> A
leg deleted.  It exists so that "the carried domain is caught when it is wrong"
is a measurement and not a hope.
"""

from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Sequence, Tuple

Cell = Tuple[int, int]

# ------------------------------------------------------------------ palette

FLOOR = 0
WALL = 1
PORTAL_A = 3
PORTAL_B = 4
DOOR_PRESENT = 5
CART = 6
SWITCH_UP = 7
SWITCH_DOWN = 8

ACTIONS: Tuple[str, ...] = ("UP", "DOWN", "LEFT", "RIGHT")
DELTA: Dict[str, Cell] = {
    "UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1),
}

HEIGHT = 9
WIDTH = 9


@dataclass(frozen=True)
class LevelSpec:
    """Everything that distinguishes one A3 level from another.

    This dataclass **is** the problem/domain cut, on the world's side of it.
    `step()` below reads nothing but a `LevelSpec`, so a mechanism cannot
    accidentally depend on a coordinate: there is no coordinate in scope.
    """

    name: str
    layout: Tuple[str, ...]
    cart_start: Cell
    switch_cell: Cell
    door_cell: Cell
    portal_a: Cell
    portal_b: Cell
    exit_a: Cell                       # where portal-A sends the Cart
    exit_b: Cell                       # where portal-B sends the Cart
    goal_cell: Cell
    portal_one_way: bool = False       # negative control 1; see L2_ONEWAY
    rewired_exit_b: Optional[Cell] = None  # negative control 2; see L2_REWIRED


L1 = LevelSpec(
    name="a3-l1",
    layout=(
        "#########",
        "#...#...#",
        "#...#...#",
        "#...#...#",
        "#.#.#...#",
        "#...###.#",
        "#...###.#",
        "#...###.#",
        "#########",
    ),
    cart_start=(6, 1),
    switch_cell=(4, 1),
    door_cell=(6, 7),
    portal_a=(2, 2),
    portal_b=(2, 6),
    exit_a=(1, 6),
    exit_b=(3, 2),
    goal_cell=(7, 7),
)


L2 = LevelSpec(
    name="a3-l2",
    layout=(
        "#########",
        "#...#...#",
        "#.###...#",
        "#.#.#...#",
        "#...#...#",
        "#...#...#",
        "#...#...#",
        "#...##.##",
        "#########",
    ),
    cart_start=(6, 7),
    switch_cell=(7, 6),
    door_cell=(3, 1),
    portal_a=(5, 1),
    portal_b=(1, 6),
    exit_a=(1, 5),
    exit_b=(4, 1),
    goal_cell=(1, 1),
)


def _variant_of_l2(name: str, **edits) -> LevelSpec:
    """A negative control is level 2 with exactly one mechanism changed.

    Spelled as an override of `L2` rather than as a second literal so that
    "only the transition function differs" is enforced by the constructor:
    every level constant is inherited, and `tests/test_negative_control.py`
    asserts the rendered first frames are byte-identical.  A negative control
    whose *pixels* differed would be a different level, and catching it would
    prove nothing about carrying a domain.
    """
    from dataclasses import replace
    return replace(L2, name=name, **edits)


#: Negative control 1 — the portal's B->A leg is deleted.  Level 2 becomes
#: unsolvable, so a manual that fails to notice does not merely mis-predict a
#: step: it certifies a win that never happened.
L2_ONEWAY = _variant_of_l2("a3-l2-oneway", portal_one_way=True)

#: Negative control 2 — the B->A leg still fires but lands somewhere else.
#: Level 2 stays solvable, so this separates "the valve detects unsolvability"
#: from "the valve detects a wrong prediction", which are not the same claim.
L2_REWIRED = _variant_of_l2("a3-l2-rewired", rewired_exit_b=(7, 1))


LEVELS: Dict[str, LevelSpec] = {
    spec.name: spec for spec in (L1, L2, L2_ONEWAY, L2_REWIRED)
}


@dataclass(frozen=True)
class State:
    cart: Cell
    pressed: bool

    def key(self) -> Tuple[int, int, int]:
        return (self.cart[0], self.cart[1], int(self.pressed))


class A3World:
    """Deterministic transition function plus renderer, for one level.

    Nothing in this class is read by the discovery pipeline.  The pipeline sees
    `artifacts/*_trace.jsonl` — frames, actions and a win flag — and, in the
    transfer arm, a single frame.  `a3pipeline` imports no world module at all;
    `tests/test_sealing.py` checks that byte-wise, as A2's tests do.
    """

    def __init__(self, spec: LevelSpec = L1):
        self.spec = spec
        self.walls: FrozenSet[Cell] = frozenset(
            (r, c)
            for r in range(HEIGHT)
            for c in range(WIDTH)
            if spec.layout[r][c] == "#"
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

        The order of the branches is the mechanism set's precedence and it is
        exhaustive over what the target cell can be: wall, switch, door,
        portal-A, portal-B, or free floor.  Every branch is reversible —
        see the module docstring on F-12.
        """
        spec = self.spec
        dr, dc = DELTA[action]
        target = (state.cart[0] + dr, state.cart[1] + dc)

        if not self.in_bounds(target) or target in self.walls:
            return state
        if target == spec.switch_cell:
            return State(cart=state.cart, pressed=not state.pressed)
        if target == spec.door_cell:
            if not state.pressed:                 # Door present -> blocked
                return state
            return State(cart=target, pressed=state.pressed)
        if target == spec.portal_a:
            return State(cart=spec.exit_a, pressed=state.pressed)
        if target == spec.portal_b:
            if spec.portal_one_way:               # negative control 1: leg deleted
                return state
            if spec.rewired_exit_b is not None:   # negative control 2: leg rewired
                return State(cart=spec.rewired_exit_b, pressed=state.pressed)
            return State(cart=spec.exit_b, pressed=state.pressed)
        return State(cart=target, pressed=state.pressed)

    # -------------------------------------------------------------- renderer

    def render(self, state: State) -> List[List[int]]:
        """Full-frame: every pixel is board, or a marker, or the Cart.

        The Cart is drawn last, so it occludes a portal cell it is standing on.
        That occlusion is real and the pipeline has to cope with it — see
        `DECISIONS.md` D-A3-003 on re-identification.  The goal cell is not
        drawn at all (D-A3-002).
        """
        spec = self.spec
        frame = [[FLOOR] * WIDTH for _ in range(HEIGHT)]
        for r, c in self.walls:
            frame[r][c] = WALL
        frame[spec.portal_a[0]][spec.portal_a[1]] = PORTAL_A
        frame[spec.portal_b[0]][spec.portal_b[1]] = PORTAL_B
        if not state.pressed:
            frame[spec.door_cell[0]][spec.door_cell[1]] = DOOR_PRESENT
        frame[spec.switch_cell[0]][spec.switch_cell[1]] = (
            SWITCH_DOWN if state.pressed else SWITCH_UP
        )
        frame[state.cart[0]][state.cart[1]] = CART
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

    def solve(self) -> Optional[List[str]]:
        """A shortest winning action sequence, or None.  The referee's answer."""
        from collections import deque

        start = self.initial()
        if self.is_win(start):
            return []
        seen = {start.key()}
        queue = deque([(start, [])])
        while queue:
            state, path = queue.popleft()
            for action in ACTIONS:
                nxt = self.step(state, action)
                if nxt.key() in seen:
                    continue
                seen.add(nxt.key())
                if self.is_win(nxt):
                    return path + [action]
                queue.append((nxt, path + [action]))
        return None

    # ------------------------------------------------- guard-coverage census

    def guard_contexts(self) -> Dict[str, int]:
        """How many reachable (state, action) pairs exercise each mechanism.

        The census is by *guard shape*, which is the unit the manual is written
        in: `push_<dir>`, `teleport_a_<dir>`, `teleport_b_<dir>`,
        `switch_<dir>`, `blocked_<dir>`.  A3's central containment check —
        "every guard L2 needs was witnessed in L1" — is a comparison of two of
        these dictionaries, so it belongs to the world and not to the report.
        """
        spec = self.spec
        census: Dict[str, int] = {}
        for state in self.reachable():
            for action in ACTIONS:
                dr, dc = DELTA[action]
                target = (state.cart[0] + dr, state.cart[1] + dc)
                low = action.lower()
                if not self.in_bounds(target) or target in self.walls:
                    key = "blocked_%s" % low
                elif target == spec.switch_cell:
                    key = "switch_%s" % low
                elif target == spec.door_cell:
                    key = ("door_open_%s" if state.pressed
                           else "door_shut_%s") % low
                elif target == spec.portal_a:
                    key = "teleport_a_%s" % low
                elif target == spec.portal_b:
                    key = "teleport_b_%s" % low
                else:
                    key = "push_%s" % low
                census[key] = census.get(key, 0) + 1
        return dict(sorted(census.items()))


def frames_and_actions(world: A3World, states: Sequence[State],
                       actions: Sequence[Optional[str]]):
    return [world.render(s) for s in states], list(actions)
