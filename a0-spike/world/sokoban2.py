"""The A0 world: a sokoban variant in which a push slides the box **two** cells.

Theoria.md Phase 1 calls A0 the first priority -- a self-built world with fully
known ground truth, zero API, zero contamination, run cold through the whole
loop: perceive -> mine rules -> adjudicate into the books -> certify -> plan ->
win, plus one conservation theorem.

The two-cell push is the design choice that makes the last item real. In ordinary
sokoban a push moves the box one cell, so the box's checkerboard colour flips and
nothing is conserved. Sliding two cells keeps the box on its own colour forever:

    (box.row + box.col) mod 2 is invariant

That law is true, provable, expressible in the frozen invariant language (which
allows mod-2 parity), and immediately useful: a level whose target square has the
opposite parity to the box is unsolvable, and the proof is one line of arithmetic
rather than a search. A0 needs exactly such a theorem, so the world is built to
have one.

Everything here is ground truth. The pipeline is not allowed to import it except
to generate frames and to check itself at the end.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

Cell = Tuple[int, int]

EMPTY = 0
PLAYER = 2
GOAL_MARK = 3          # never rendered; goals live in the problem spec, not the frame
BOX = 4
WALL = 8

DIRECTIONS = ("UP", "DOWN", "LEFT", "RIGHT")
DELTA: Dict[str, Cell] = {
    "UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1),
}

MOVE = "move"
PUSH = "push"
BLOCKED = "blocked"


@dataclass(frozen=True)
class Rules:
    """The world's dynamics, as data -- so a variant can change exactly one thing.

    Theoria.md Phase 1 layer 2: variants are produced by deterministic rewriting,
    never by rewriting the game. Each field here is one rule of the world; a
    variant flips one and leaves the rest identical, which is what makes
    "how fast does it adapt to ONE changed rule" a meaningful question.
    """

    push_distance: int = 2          # how far a pushed box travels
    require_crossing_free: bool = True   # must every cell the box crosses be free?
    walls_block_player: bool = True      # do walls stop the player walking?

    def label(self) -> str:
        return "push%d%s%s" % (
            self.push_distance,
            "" if self.require_crossing_free else "+nocross",
            "" if self.walls_block_player else "+ghost",
        )


BASE_RULES = Rules()


@dataclass(frozen=True)
class Level:
    name: str
    height: int
    width: int
    walls: Tuple[Cell, ...]
    player: Cell
    box: Cell
    target: Cell
    solvable: Optional[bool] = None      # ground truth, filled in by levels.py
    rules: "Rules" = BASE_RULES

    def parity(self, cell: Cell) -> int:
        return (cell[0] + cell[1]) % 2

    @property
    def box_parity(self) -> int:
        return self.parity(self.box)

    @property
    def target_parity(self) -> int:
        return self.parity(self.target)

    @property
    def parity_matches(self) -> bool:
        return self.box_parity == self.target_parity


@dataclass(frozen=True)
class State:
    player: Cell
    box: Cell

    def key(self) -> Tuple[Cell, Cell]:
        return (self.player, self.box)


def initial_state(level: Level) -> State:
    return State(player=level.player, box=level.box)


def in_bounds(level: Level, cell: Cell) -> bool:
    return 0 <= cell[0] < level.height and 0 <= cell[1] < level.width


def is_wall(level: Level, cell: Cell) -> bool:
    return cell in level.walls


def free(level: Level, cell: Cell, state: State) -> bool:
    """Free = on the board, not a wall, not the box. The player never blocks."""
    return in_bounds(level, cell) and not is_wall(level, cell) and cell != state.box


def _add(cell: Cell, delta: Cell, times: int = 1) -> Cell:
    return (cell[0] + delta[0] * times, cell[1] + delta[1] * times)


def step(level: Level, state: State, action: str) -> Tuple[State, str]:
    """Ground-truth transition. Returns (next state, event label).

    * target empty        -> the player walks one cell
    * target is the box   -> the box slides `push_distance` cells and the player
                             takes one, provided the cells it crosses are free
    * anything else       -> nothing happens
    """
    rules = level.rules
    delta = DELTA[action]
    target = _add(state.player, delta)

    if not in_bounds(level, target):
        return state, BLOCKED
    if is_wall(level, target) and rules.walls_block_player:
        return state, BLOCKED

    if target != state.box:
        return State(player=target, box=state.box), MOVE

    distance = rules.push_distance
    landing = _add(state.box, delta, distance)
    crossed = [_add(state.box, delta, k) for k in range(1, distance)]
    to_check = ([landing] if not rules.require_crossing_free
                else crossed + [landing])
    for cell in to_check:
        if not in_bounds(level, cell) or is_wall(level, cell):
            return state, BLOCKED
    return State(player=target, box=landing), PUSH


def render(level: Level, state: State) -> List[List[int]]:
    grid = [[EMPTY] * level.width for _ in range(level.height)]
    for (r, c) in level.walls:
        grid[r][c] = WALL
    grid[state.box[0]][state.box[1]] = BOX
    grid[state.player[0]][state.player[1]] = PLAYER
    return grid


def rollout(level: Level, actions: Sequence[str]) -> Dict[str, object]:
    """Run an action sequence and record everything about it."""
    state = initial_state(level)
    states = [state]
    events: List[str] = []
    for action in actions:
        state, event = step(level, state, action)
        states.append(state)
        events.append(event)
    return {
        "level": level.name,
        "states": states,
        "events": events,
        "actions": list(actions),
        "frames": [render(level, s) for s in states],
        "box_parities": [(s.box[0] + s.box[1]) % 2 for s in states],
    }


# --------------------------------------------------------------- ground truth

def box_parity_is_invariant(level: Level, actions: Sequence[str]) -> bool:
    """The conservation law, checked directly on a trajectory."""
    parities = set(rollout(level, actions)["box_parities"])   # type: ignore[index]
    return len(parities) == 1


def solve_bfs(level: Level, max_states: int = 200000) -> Optional[List[str]]:
    """Shortest action sequence putting the box on the target, or None.

    This is the oracle A0 checks itself against -- never the thing the pipeline
    plans with.
    """
    from collections import deque

    start = initial_state(level)
    if start.box == level.target:
        return []
    seen = {start.key()}
    queue = deque([(start, [])])
    while queue:
        state, plan = queue.popleft()
        if len(seen) > max_states:
            raise RuntimeError("state space larger than expected")
        for action in DIRECTIONS:
            nxt, event = step(level, state, action)
            if event == BLOCKED or nxt.key() in seen:
                continue
            if nxt.box == level.target:
                return plan + [action]
            seen.add(nxt.key())
            queue.append((nxt, plan + [action]))
    return None


def reachable_box_cells(level: Level) -> List[Cell]:
    """Every cell the box can ever occupy -- used to confirm the parity law bites."""
    from collections import deque

    start = initial_state(level)
    seen = {start.key()}
    boxes = {start.box}
    queue = deque([start])
    while queue:
        state = queue.popleft()
        for action in DIRECTIONS:
            nxt, event = step(level, state, action)
            if event == BLOCKED or nxt.key() in seen:
                continue
            seen.add(nxt.key())
            boxes.add(nxt.box)
            queue.append(nxt)
    return sorted(boxes)
